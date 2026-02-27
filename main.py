"""FastAPI 应用入口。"""

from __future__ import annotations

import asyncio
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
from app.schemas import ApiResponse  # noqa: E402

logger = get_logger(__name__)

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    BASE_DIR = Path(__file__).resolve().parent

PREFIX = settings.path_prefix


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    asyncio.create_task(restore_on_startup())
    yield
    await close_http_client()


app = FastAPI(title="添加工时工具", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


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
