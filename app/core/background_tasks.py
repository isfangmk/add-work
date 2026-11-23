"""后台任务追踪：保存 task 强引用，避免被事件循环 GC，异常时记录日志。"""

from __future__ import annotations

import asyncio
from typing import Coroutine, Set

from app.core.logger import get_logger

logger = get_logger(__name__)

_background_tasks: Set[asyncio.Task] = set()


def spawn(coro: Coroutine, *, name: str = "") -> asyncio.Task:
    """创建后台任务并保持强引用，完成时自动移除并可观察异常。"""
    task = asyncio.create_task(coro, name=name or None)

    def _done(done: asyncio.Task) -> None:
        _background_tasks.discard(done)
        if done.cancelled():
            return
        exc = done.exception()
        if exc is not None:
            logger.exception("后台任务[%s]异常：%s", done.get_name(), exc, exc_info=exc)

    task.add_done_callback(_done)
    _background_tasks.add(task)
    return task
