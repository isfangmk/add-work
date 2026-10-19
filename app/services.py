"""工时业务编排。"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple

from app.clients import gitee
from app.config import settings
from app.db import (
    get_workspace_configs,
    save_task_record,
    upsert_cookie_record,
)
from app.keepalive import is_active, start as start_keepalive
from app.logger import get_logger
from app.task_store import append_log, finish_task

logger = get_logger(__name__)


async def resolve_current_user(
    cookie: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """根据 Cookie 解析当前用户，写入记录并按需启动保活。"""
    headers = settings.build_headers(cookie)
    username, git_email, real_name = await gitee.fetch_current_user(headers)
    if not username:
        return None, None, None

    cookie_str = headers["cookie"]
    upsert_cookie_record(username, cookie_str, real_name)
    if not is_active(username):
        await start_keepalive(username, cookie_str)
    return username, git_email, real_name or ""


async def load_calendar_items(
    headers: Dict[str, str],
    start_date: str,
    end_date: str,
    username: Optional[str] = None,
    git_email: Optional[str] = None,
) -> Tuple[Optional[List[Any]], Optional[str], Optional[str]]:
    """拉取日历工时（需已有 username）。"""
    if not username:
        return None, None, None

    workspaces = get_workspace_configs()
    results = await asyncio.gather(
        *[
            gitee.search_work_items(
                username,
                headers,
                name,
                cfg["workspace_key"],
                start_date,
                end_date,
            )
            for name, cfg in workspaces.items()
        ]
    )
    if None in results:
        return None, None, None
    return list(results), username, git_email


async def run_work_task(
    username: Optional[str],
    headers: Dict[str, str],
    source_object_id: str,
    names: List[str],
    sprint_ids: List[str],
    times: List[float],
    dates: List[str],
    workspace_names: List[str],
    task_id: str,
    *,
    is_update: bool = False,
) -> None:
    """后台克隆或更新事项。"""
    primary_workspace = workspace_names[0] if workspace_names else ""
    logger.info(
        "任务开始 %s",
        [
            username,
            source_object_id,
            names,
            sprint_ids,
            times,
            dates,
            workspace_names,
            task_id,
        ],
    )
    save_task_record(
        username, source_object_id, names, times, dates, primary_workspace
    )
    append_log(task_id, f"📅 任务开始执行，共处理{len(names)}个事项")

    all_ok = True
    configs = get_workspace_configs()
    jump_url = None

    try:
        if len({len(names), len(times), len(dates), len(sprint_ids), len(workspace_names)}) != 1:
            raise ValueError(
                f"名称（{len(names)}）工时（{len(times)}）日期（{len(dates)}）"
                f"迭代（{len(sprint_ids)}）工作空间（{len(workspace_names)}）长度不一致"
            )

        for idx, (name, sprint_id, hours, day, workspace_name) in enumerate(
            zip(names, sprint_ids, times, dates, workspace_names), 1
        ):
            workspace = configs.get(workspace_name)
            if not workspace:
                append_log(task_id, f"❌ 工作空间 '{workspace_name}' 不存在")
                all_ok = False
                continue

            append_log(task_id, f"\n=== 处理第{idx}/{len(names)}个事项 ===")
            append_log(
                task_id,
                f"名称：{name} | 工作空间：{workspace_name} | 目标日期：{day} "
                f"| 工时：{hours}个小时 | 迭代ID：{sprint_id}",
            )

            object_id = (
                source_object_id
                if is_update
                else await gitee.clone_item(
                    headers,
                    source_object_id,
                    name,
                    workspace["workspace_id"],
                    task_id,
                )
            )
            if not object_id:
                append_log(task_id, f"❌ 复制源事项[{source_object_id}]失败")
                all_ok = False
                continue

            keys = await gitee.resolve_field_keys(
                headers, object_id, settings.work_item_field_names, task_id
            )
            if not keys:
                append_log(task_id, "❌ 获取目标字段失败")
                all_ok = False
                continue

            if not await gitee.update_item(
                headers, object_id, keys, day, hours, name, task_id, sprint_id
            ):
                append_log(task_id, f"❌ 更新事项[{object_id}]失败")
                all_ok = False

            iql = gitee.workspace_iql_cache.get((username or "") + workspace_name, "")
            if iql:
                jump_url = workspace["jump_url"].replace("[iql]", iql)
    except Exception as exc:
        append_log(task_id, f"❌ 任务全局错误：{exc}")
        all_ok = False
    finally:
        finish_task(task_id, all_ok)
        append_log(
            task_id,
            "🎉 任务执行完成！"
            + ("所有事项处理成功" if all_ok else "部分事项处理失败（见日志）"),
        )
        if jump_url:
            append_log(
                task_id,
                "😎 去项目空间查看结果吧："
                f'<a href="{jump_url}" target="_blank" rel="noopener noreferrer">点击跳转</a>',
            )
