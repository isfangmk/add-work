"""工时业务编排。"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from app.clients import gitee
from app.core.config import settings
from app.core.logger import get_logger
from app.services.keepalive import is_active
from app.services.keepalive import start as start_keepalive
from app.storage.db import (
    add_favorite_workspace,
    get_favorite_workspaces,
    save_task_record,
    upsert_cookie_record,
)
from app.storage.task_store import append_log, finish_task

logger = get_logger(__name__)


def group_items_by_date(results: List[Any]) -> Dict[str, List[Any]]:
    """把 [[item,...], ...] 结果按日期分组（日历接口与 MCP 共用）。"""
    grouped: Dict[str, List[Any]] = defaultdict(list)
    for batch in results:
        if not batch:
            continue
        for item in batch:
            grouped[item["date"]].append(item)
    return dict(grouped)


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
    """拉取日历工时（只从用户关注的空间读取，需已有 username）。"""
    if not username:
        return None, None, None

    favorites = get_favorite_workspaces(username)
    if not favorites:
        # 没有关注空间时返回空结果，不发任何查询
        return [], username, git_email

    workspaces = await gitee.list_workspaces(headers)
    if workspaces is None:
        return None, None, None
    # 只保留当前用户可见且已关注的空间
    fav_keys = {f["workspace_key"] for f in favorites}
    targets = [ws for ws in workspaces if ws["workspace_key"] in fav_keys]

    results = await asyncio.gather(
        *[
            gitee.search_work_items(
                username,
                headers,
                ws["workspace_name"],
                ws["workspace_key"],
                start_date,
                end_date,
            )
            for ws in targets
        ],
        return_exceptions=True,
    )
    # 单个空间失败只记日志、跳过，不影响整体日历；保持 [[item,...], ...] 结构
    batches: List[List[Any]] = []
    for ws, result in zip(targets, results, strict=True):
        if isinstance(result, BaseException):
            logger.warning("空间[%s]工时查询失败，已跳过：%s", ws["workspace_name"], result)
            continue
        if result is None:
            logger.warning("空间[%s]工时查询返回空，已跳过", ws["workspace_name"])
            continue
        batches.append(result)
    return batches, username, git_email


async def run_work_task(
    username: str,
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
    data_quote_ids: Optional[List[str]] = None,
) -> None:
    """后台克隆或更新事项。"""
    requirement_ids = data_quote_ids or [""] * len(names)
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
    save_task_record(username, source_object_id, names, times, dates, primary_workspace)
    append_log(task_id, f"📅 任务开始执行，共处理{len(names)}个事项")

    all_ok = True
    jump_url = None

    try:
        if (
            len(
                {
                    len(names),
                    len(times),
                    len(dates),
                    len(sprint_ids),
                    len(workspace_names),
                    len(requirement_ids),
                }
            )
            != 1
        ):
            raise ValueError(
                f"名称（{len(names)}）工时（{len(times)}）日期（{len(dates)}）"
                f"迭代（{len(sprint_ids)}）工作空间（{len(workspace_names)}）"
                f"关联需求（{len(requirement_ids)}）长度不一致"
            )

        workspaces = await gitee.list_workspaces(headers)
        if workspaces is None:
            raise ValueError("获取工作空间列表失败，请检查Cookie是否有效")
        name_to_key = {w["workspace_name"]: w["workspace_key"] for w in workspaces}
        details = await gitee.resolve_workspace_details(
            headers, [name_to_key[n] for n in workspace_names if n in name_to_key]
        )
        # 当前关注空间 key（用于写入成功后自动收藏未关注的空间）
        fav_keys = {f["workspace_key"] for f in get_favorite_workspaces(username)}

        for idx, (name, sprint_id, hours, day, workspace_name, data_quote_id) in enumerate(
            zip(
                names,
                sprint_ids,
                times,
                dates,
                workspace_names,
                requirement_ids,
                strict=True,
            ),
            1,
        ):
            workspace_key = name_to_key.get(workspace_name)
            if not workspace_key:
                append_log(task_id, f"❌ 工作空间 '{workspace_name}' 不存在")
                all_ok = False
                continue
            workspace = details.get(workspace_key, {})

            append_log(task_id, f"\n=== 处理第{idx}/{len(names)}个事项 ===")
            append_log(
                task_id,
                f"名称：{name} | 工作空间：{workspace_name} | 目标日期：{day} "
                f"| 工时：{hours}个小时 | 迭代ID：{sprint_id}",
            )

            if not is_update and not workspace.get("workspace_id"):
                append_log(task_id, f"❌ 工作空间 '{workspace_name}' 解析失败，无法复制事项")
                all_ok = False
                continue

            object_id = (
                source_object_id
                if is_update
                else await gitee.clone_item(
                    headers,
                    source_object_id,
                    name,
                    workspace.get("workspace_id", ""),
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
                headers,
                object_id,
                keys,
                day,
                hours,
                name,
                task_id,
                sprint_id,
                data_quote_id=data_quote_id or None,
            ):
                append_log(task_id, f"❌ 更新事项[{object_id}]失败")
                all_ok = False
            elif username and workspace_key and workspace_key not in fav_keys:
                # 写入成功且该空间未关注 → 自动收藏，方便下次日历直接显示
                if add_favorite_workspace(username, workspace_key, workspace_name):
                    fav_keys.add(workspace_key)
                    append_log(
                        task_id,
                        f"⭐ 已自动关注空间「{workspace_name}」（检测到该空间有新工时）",
                    )

            iql = gitee.workspace_iql_cache.get(username + workspace_name, "")
            if iql and workspace.get("jump_url"):
                jump_url = workspace["jump_url"].replace("[iql]", iql)
    except Exception as exc:
        append_log(task_id, f"❌ 任务全局错误：{exc}")
        all_ok = False
    finally:
        finish_task(task_id, all_ok)
        append_log(
            task_id,
            "🎉 任务执行完成！" + ("所有事项处理成功" if all_ok else "部分事项处理失败（见日志）"),
        )
        if jump_url:
            append_log(task_id, f"😎 去项目空间查看结果吧：{jump_url}")
