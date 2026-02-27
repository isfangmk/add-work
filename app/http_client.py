"""共享 HTTP 客户端。"""

from __future__ import annotations

import httpx

from app.config import settings

http_client = httpx.AsyncClient(timeout=settings.http_timeout)


async def close_http_client() -> None:
    await http_client.aclose()


def format_http_error(prefix: str, exc: Exception, response=None) -> str:
    msg = f"{prefix}：{exc}"
    if response is not None:
        try:
            msg += f"\n响应内容：{response.text}"
        except Exception:
            pass
    return msg
