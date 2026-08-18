"""FastAPI 应用入口。"""

from __future__ import annotations

import asyncio
import hashlib
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from app.api import router  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import init_db  # noqa: E402
from app.exceptions import AppError  # noqa: E402
from app.http_client import close_http_client  # noqa: E402
from app.keepalive import restore_on_startup  # noqa: E402
from app.logger import get_logger  # noqa: E402
from app.mcp import mcp_http_app, mcp_token_from_headers  # noqa: E402
from app.schemas import ApiResponse  # noqa: E402
from sqlite_web.sqlite_web import app as sqlite_web_app  # noqa: E402
from sqlite_web.sqlite_web import initialize_app as init_sqlite_web  # noqa: E402
from starlette.middleware.wsgi import WSGIMiddleware  # noqa: E402

logger = get_logger(__name__)

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    BASE_DIR = Path(__file__).resolve().parent

PREFIX = settings.path_prefix


@asynccontextmanager
async def app_lifespan(_app: FastAPI):
    init_db()
    asyncio.create_task(restore_on_startup())
    yield
    await close_http_client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with app_lifespan(app):
        async with mcp_http_app.lifespan(app):
            yield


app = FastAPI(title="添加工时工具", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# English SQLite browser: https://github.com/coleifer/sqlite-web
_db_path = Path(settings.db_path)
if not _db_path.is_absolute():
    _db_path = BASE_DIR / _db_path
_sqlite_password = settings.sqlite_web_password
init_sqlite_web([str(_db_path)], read_only=False, password=_sqlite_password or None)
if _sqlite_password:
    _key = b"sqlite-web-" + str(_db_path).encode("utf8") + _sqlite_password.encode("utf8")
    sqlite_web_app.secret_key = hashlib.sha256(_key).hexdigest()
else:
    logger.warning("SQLITE_WEB_PASSWORD 未配置，/sqlite 可匿名访问")
app.mount(f"{PREFIX}/sqlite", WSGIMiddleware(sqlite_web_app))
app.mount(f"{PREFIX}/mcp", mcp_http_app)

_MCP_PATH = f"{PREFIX}/mcp"


@app.middleware("http")
async def mcp_http_middleware(request: Request, call_next):
    # MCP Streamable HTTP 客户端通常不跟随 307，把无尾斜杠改写到挂载路径内部。
    path = request.scope.get("path", "")
    if path == _MCP_PATH:
        request.scope["path"] = _MCP_PATH + "/"
        raw = request.scope.get("raw_path")
        if isinstance(raw, (bytes, bytearray)):
            request.scope["raw_path"] = raw.rstrip(b"/") + b"/"

    if not request.scope.get("path", "").startswith(_MCP_PATH):
        return await call_next(request)
    expected = settings.mcp_token
    if not expected:
        return JSONResponse(
            {"error": "unauthorized", "msg": "服务未配置 MCP_TOKEN"},
            status_code=401,
        )
    if mcp_token_from_headers(dict(request.headers)) != expected:
        return JSONResponse(
            {"error": "unauthorized", "msg": "缺少或错误的 X-MCP-Token"},
            status_code=401,
        )
    return await call_next(request)


@app.get("/")
async def root_redirect():
    return RedirectResponse(url=f"{PREFIX}/", status_code=302)


static_dir = BASE_DIR / "frontend" / "build" / "static"
if static_dir.is_dir():
    app.mount(f"{PREFIX}/static", StaticFiles(directory=static_dir, html=True), name="static")


@app.get(PREFIX)
@app.get(f"{PREFIX}/")
async def spa_index():
    index = BASE_DIR / "frontend" / "build" / "index.html"
    if index.is_file():
        return FileResponse(index)
    raise HTTPException(status_code=404, detail="index.html不存在")


app.include_router(router, prefix=PREFIX)


@app.exception_handler(AppError)
async def handle_app_error(_request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.fail(exc.detail).model_dump(),
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("服务已启动: http://127.0.0.1:5000")
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False, log_level="info")
    except KeyboardInterrupt:
        logger.info("服务已停止")
