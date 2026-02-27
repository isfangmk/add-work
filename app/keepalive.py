"""Cookie 保活。"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from app.config import settings
from app.db import delete_cookie_record, get_all_cookie_records
from app.http_client import http_client
from app.logger import get_logger

logger = get_logger(__name__)

_active: Dict[str, Dict[str, Any]] = {}


async def _probe(cookie_str: str, *, in_loop: bool = False) -> bool:
    retries = 3 if in_loop else 1
    for attempt in range(retries):
        try:
            resp = await http_client.get(
                settings.base_url + settings.current_user_path,
                headers=settings.build_headers(cookie_str),
            )
            resp.raise_for_status()
            payload = resp.json().get("payload") or {}
            if "enterpriseCard" not in payload:
                logger.error(
                    "响应缺少 enterpriseCard (尝试 %s/%s)", attempt + 1, retries
                )
                if attempt < retries - 1:
                    await asyncio.sleep(600)
                    continue
                return False
            logger.info("保活成功：%s", payload["enterpriseCard"])
            return True
        except Exception as exc:
            logger.error("保活请求失败：%s (尝试 %s/%s)", exc, attempt + 1, retries)
            if attempt < retries - 1:
                await asyncio.sleep(10)
                continue
            return False
    return False


async def _loop(username: str, cookie_str: str) -> None:
    while True:
        try:
            logger.info("[%s] 心跳...", username)
            if await _probe(cookie_str, in_loop=True):
                logger.info("[%s] cookie 已续期", username)
            else:
                logger.error("[%s] 心跳失败，停止保活", username)
                delete_cookie_record(username)
                break
            await asyncio.sleep(settings.heartbeat_interval)
        except asyncio.CancelledError:
            logger.warning("[%s] 保活任务取消", username)
            break
        except Exception as exc:
            logger.error("[%s] 心跳异常：%s", username, exc)
            await asyncio.sleep(10)
    _active.pop(username, None)


def is_active(username: str) -> bool:
    return username in _active


async def start(username: str, cookie_str: str) -> bool:
    if not cookie_str.strip():
        logger.error("cookie 为空")
        return False

    existing = _active.get(username)
    if existing and not existing["task"].done():
        logger.warning("[%s] 已在保活中", username)
        return True

    if not await _probe(cookie_str):
        logger.error("[%s] 初始验证失败", username)
        delete_cookie_record(username)
        return False

    task = asyncio.create_task(_loop(username, cookie_str))
    _active[username] = {"task": task, "cookie_str": cookie_str}
    logger.info("[%s] 保活已启动", username)
    return True


async def restore_on_startup() -> None:
    try:
        records = get_all_cookie_records()
        logger.info("启动恢复保活，共 %s 个用户", len(records))
        for username, cookie_str in records:
            if not cookie_str.strip():
                continue
            ok = await start(username, cookie_str)
            logger.info("[%s] 恢复%s", username, "成功" if ok else "失败")
            await asyncio.sleep(10)
    except Exception as exc:
        logger.error("启动恢复保活失败：%s", exc)
