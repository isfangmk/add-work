"""jump_url 生成修复：wrap run_work_task，在任务执行前预热 IQL 缓存。

主分支 app/services/work.py 在 finally 中构造 jump_url 时读取
gitee.workspace_iql_cache[username + workspace_name]，而该缓存只在日历查询
(gitee.search_work_items)时写入。直接提交任务（API / MCP / 页面快速提交）
没有经过日历查询，缓存为空，导致 jump_url 不生成、日志里没有"去项目空间查看"。

缓存的值完全可由 username 推导，无需真的查询日历。本补丁在 run_work_task
执行前按 workspace_names 预热该缓存，使主分支原有 jump_url 逻辑照常工作。
不改主分支源码。
"""

from __future__ import annotations

import inspect
import logging
from typing import Any
from urllib.parse import quote

from funcpatch import PatchSpec

logger = logging.getLogger("plugins.jump_url_fix")


def _warm_iql_cache(wrapped: Any, args: tuple, kwargs: dict) -> None:
    """按本次任务的 username / workspace_names 预热 IQL 缓存。"""
    try:
        from app.clients import gitee

        bound = inspect.signature(wrapped).bind_partial(*args, **kwargs)
        username = bound.arguments.get("username")
        workspace_names = bound.arguments.get("workspace_names") or []
        if not username:
            return
        # 与主分支 gitee.py:109 写入的缓存值保持一致
        iql = quote(f"'负责人' in [\"{username}\"] order by 实际完成时间 desc", safe="")
        for name in workspace_names:
            gitee.workspace_iql_cache[f"{username}{name}"] = iql
        if workspace_names:
            logger.debug("已预热 IQL 缓存：%d 个空间", len(workspace_names))
    except Exception:
        # 预热失败不能影响任务本身，主分支会回退到无 jump_url 的原行为
        logger.exception("预热 IQL 缓存失败")


async def _run_work_task_wrapper(wrapped: Any, instance: Any, args: tuple, kwargs: dict) -> Any:
    """async wrap 协议：先预热缓存，再 await 原 run_work_task。"""
    _warm_iql_cache(wrapped, args, kwargs)
    return await wrapped(*args, **kwargs)


run_work_task_spec = PatchSpec(
    owner="addwork",
    target_module="app.services.work",
    target_attr="run_work_task",
    replacement=_run_work_task_wrapper,
    mode="wrap",
    description="任务执行前预热 IQL 缓存，修复直接提交时 jump_url 不生成",
    tags=("jump-url", "bugfix"),
)
