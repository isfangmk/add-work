"""init_db 启动补丁：在主程序数据库初始化时拉起周报调度器。

main.py 的 lifespan 调用同步的 init_db()，此时事件循环已在运行，
因此补丁在原函数执行后把调度协程挂到当前循环；无运行循环时（如独立
脚本直接调用 init_db）只执行原逻辑，不影响主程序。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from funcpatch import PatchSpec

from . import config as _config
from .runner import start_scheduler

logger = logging.getLogger("addwork_patches.weekly")


def _enabled() -> bool:
    return bool(_config.settings.enabled)


def _init_db_wrapper(wrapped: Any, instance: Any, args: tuple, kwargs: dict) -> Any:
    """wrap 协议：先执行原 init_db，再按启用开关启动周报调度。"""
    result = wrapped(*args, **kwargs)
    if not _enabled():
        return result
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 没有运行中的事件循环（如命令行直接调 init_db），不启动调度器。
        return result
    loop.create_task(start_scheduler(), name="addwork-reminder-start")
    return result


init_db_spec = PatchSpec(
    owner="addwork",
    target_module="app.storage.db",
    target_attr="init_db",
    replacement=_init_db_wrapper,
    mode="wrap",
    enabled=_enabled,
    description="应用启动时按 REMINDER_ENABLED 拉起上周工时周报调度器",
    tags=("weekly-reminder", "startup"),
)
