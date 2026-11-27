"""工时填报结果推送：以 funcpatch wrap 补丁挂接 finish_task。

主分支 run_work_task 是 async 函数，在 finally 中调用 finish_task(task_id, success)。
本补丁包裹该同步函数，推送走原生 asyncio：从当前事件循环取 running loop，
用 create_task 调度异步协程，不阻塞事件循环。
任务 id 先标记已处理再发送，失败不重试，避免刷屏。
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from funcpatch import PatchSpec

from ._infra.wecom import send_markdown_async

logger = logging.getLogger("addwork_patches.worklog")

_TRUE_VALUES = {"1", "true", "yes", "on"}

# 已推送的任务 id（进程内去重）。
_seen: set[str] = set()
# 运行中的推送任务，保持强引用防止被 GC；完成后自动移除。
_pending: set[asyncio.Task] = set()


def _enabled() -> bool:
    raw = os.getenv("WORKLOG_PUSH_ENABLED", "")
    return raw.strip().lower() in _TRUE_VALUES


def webhook_url() -> str:
    """推送地址：取环境变量，未配置时返回空串（不推送）。"""
    return os.getenv("WORKLOG_PUSH_WEBHOOK_URL", "").strip()


def build_message(task_id: str, success: bool, log: list[str]) -> str:
    """构造单条任务的执行日志推送文本。"""
    lines = [
        "**工时填报结果**",
        f"任务：{task_id}",
        f"状态：{'✅ 成功' if success else '❌ 存在失败'}",
        "",
    ]
    lines.extend(f"> {line}" for line in log)
    return "\n".join(lines)


async def push_once(task_id: str, success: bool, log: list[str]) -> bool:
    """异步推送一条已完成任务；返回是否成功发送。"""
    message = build_message(task_id, success, log)
    if not message:
        return False
    ok = await send_markdown_async(message, webhook_url())
    if ok:
        logger.info("任务日志已推送：%s", task_id)
    else:
        logger.warning("任务日志推送失败：%s", task_id)
    return ok


def _task_log(task_id: str) -> list[str]:
    """从 task_store 读取日志副本（内存操作，不阻塞）。"""
    from app.storage.task_store import TASK_STATUS, copy_logs

    if task_id not in TASK_STATUS:
        return []
    return list(copy_logs(task_id) or TASK_STATUS[task_id].get("log", []))


async def _push_async(task_id: str, success: bool) -> None:
    """异步发送：稍等主分支写完收尾日志，再读日志并推送。"""
    await asyncio.sleep(0.05)
    try:
        await push_once(task_id, success, _task_log(task_id))
    except Exception:
        logger.exception("工时填报结果推送异常：task_id=%s", task_id)


def _schedule_push(task_id: str, success: bool) -> None:
    """在当前事件循环上调度推送；无运行循环时回退到 asyncio.run。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 命令行直接调用 finish_task 等无 loop 场景，保证推送仍能完成。
        asyncio.run(_push_async(task_id, success))
        return
    task = loop.create_task(_push_async(task_id, success), name=f"worklog-push-{task_id}")
    _pending.add(task)
    task.add_done_callback(_pending.discard)


def _finish_task_wrapper(wrapped: Any, instance: Any, args: tuple, kwargs: dict) -> Any:
    """wrap 协议：先调用原 finish_task，再把异步推送挂到当前事件循环。"""
    result = wrapped(*args, **kwargs)
    try:
        if not _enabled():
            return result
        task_id = kwargs.get("task_id", args[0] if args else "")
        success = kwargs.get("success", args[1] if len(args) > 1 else None)
        if not task_id or success is None or task_id in _seen:
            return result
        _seen.add(task_id)  # 先标记，发送失败不重试，避免刷屏
        _schedule_push(str(task_id), bool(success))
    except Exception:
        logger.exception(
            "工时填报结果推送调度异常：task_id=%s", kwargs.get("task_id", args[0] if args else "")
        )
    return result


finish_task_spec = PatchSpec(
    owner="addwork",
    target_module="app.storage.task_store",
    target_attr="finish_task",
    replacement=_finish_task_wrapper,
    mode="wrap",
    enabled=_enabled,
    description="任务完成并写入状态后，异步推送工时填报结果到企业微信",
    tags=("worklog", "wecom"),
)
