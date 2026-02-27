"""Gitee / Parse API 客户端。"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote
from zoneinfo import ZoneInfo

from app.config import settings
from app.http_client import format_http_error, http_client
from app.logger import get_logger
from app.task_store import append_log

logger = get_logger(__name__)
_TZ = ZoneInfo("Asia/Shanghai")

# {username+workspace_name: quoted_iql}
workspace_iql_cache: Dict[str, str] = {}


async def fetch_current_user(
    headers: Dict[str, str],
) -> Tuple[Optional[str], Optional[str]]:
    resp = None
    try:
        resp = await http_client.get(
            settings.base_url + settings.current_user_path, headers=headers
        )
        resp.raise_for_status()
        payload = resp.json().get("payload")
        if not payload:
            return None, None
        return payload.get("displayName"), payload.get("gitEmail")
    except Exception as exc:
        logger.error(format_http_error("获取用户信息失败", exc, resp))
        return None, None


async def search_work_items(
    username: str,
    headers: Dict[str, str],
    workspace_name: str,
    workspace_key: str,
    start_date: str,
    end_date: str,
) -> Optional[List[Dict[str, Any]]]:
    resp = None
    try:
        iql = (
            f"('实际完成时间' >= '{start_date}' and '实际完成时间' <= '{end_date}' "
            f"and '负责人' in [\"{username}\"] ) and (所属空间 = '{workspace_name}') "
            f"order by 实际完成时间 desc"
        )
        workspace_iql_cache[username + workspace_name] = quote(
            f"'负责人' in [\"{username}\"] order by 实际完成时间 desc",
            safe="",
        )
        body = {
            "iql": iql,
            "size": 10,
            "from": 0,
            "execFieldBehaviors": True,
            "fields": [
                "ancestors",
                "assignee",
                "createdAt",
                "createdBy",
                "earlyWarning",
                "field019",
                "field028",
                "field027",
                "Bozq53g7",
                "Lkb66aTo",
                "id",
                "itemType",
                "key",
                "rowId",
                "sprint",
                "workspace",
            ],
            "refererInfo": {"workspaceKey": workspace_key},
        }
        logger.info("search body: %s", json.dumps(body, ensure_ascii=False))
        resp = await http_client.post(
            f"{settings.base_url}/api/team/parse/api/search",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        items: List[Dict[str, Any]] = []
        for item in resp.json()["payload"]["items"]:
            sprint = item["values"]["sprint"][0]
            items.append(
                {
                    "object_id": item["objectId"],
                    "name": item["name"],
                    "sprint": sprint["name"],
                    "sprint_id": sprint["objectId"],
                    "time": item["values"]["field019"],
                    "date": datetime.fromtimestamp(
                        item["values"]["Lkb66aTo"] / 1000, _TZ
                    ).strftime("%Y-%m-%d"),
                    "workspace_name": workspace_name,
                }
            )
        return items
    except Exception as exc:
        logger.error(format_http_error("搜索事项列表失败", exc, resp))
        return None


async def list_sprints(
    headers: Dict[str, str],
    workspace_key: str,
    workspace_id: str,
) -> Optional[List[Dict[str, Any]]]:
    """拉取空间下未完成的迭代列表。"""
    resp = None
    body = {
        "where": {
            "workspace": {
                "$inQuery": {
                    "where": {
                        "$or": [
                            {"key": workspace_key},
                            {"objectId": workspace_id},
                        ]
                    },
                    "className": "Workspace",
                }
            },
            "completed": False,
        },
        "include": "workspace",
        "order": "-createdAt",
    }
    try:
        resp = await http_client.post(
            f"{settings.base_url}/api/team/parse/api/apps/schema/Sprint",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        return [
            {"object_id": item["objectId"], "name": item["name"]}
            for item in resp.json()["results"]
        ]
    except Exception as exc:
        logger.error(format_http_error("获取迭代列表失败", exc, resp))
        return None


async def clone_item(
    headers: Dict[str, str],
    source_object_id: str,
    name: str,
    workspace_id: str,
    task_id: str,
) -> Optional[str]:
    resp = None
    try:
        resp = await http_client.post(
            f"{settings.base_url}/api/team/parse/api/items/clone",
            headers=headers,
            json={
                "objectId": source_object_id,
                "workspace": workspace_id,
                "name": name,
                "includeStatus": True,
                "includeDescendant": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if "objectId" not in data:
            raise ValueError("响应数据中未包含objectId字段")
        append_log(task_id, f"✅ 复制事项成功，新事项ID：{data['objectId']}")
        return data["objectId"]
    except Exception as exc:
        append_log(task_id, format_http_error(f"❌ 复制事项[{name}]失败", exc, resp))
        return None


async def resolve_field_keys(
    headers: Dict[str, str],
    object_id: str,
    field_names: List[str],
    task_id: str,
) -> List[str]:
    if not object_id:
        append_log(task_id, "❌ 获取字段key失败：object_id为空")
        return []
    resp = None
    try:
        resp = await http_client.get(
            f"{settings.base_url}/api/team/parse/api/items/{object_id}?screen=view",
            headers=headers,
        )
        resp.raise_for_status()
        field_map = {
            f.get("name"): f.get("key") for f in resp.json().get("fields", [])
        }
        keys: List[str] = []
        for name in field_names:
            if name not in field_map:
                missing = [n for n in field_names if n not in field_map]
                raise ValueError(f"字段不存在：{name}（缺失：{set(missing)}）")
            keys.append(field_map[name])
        append_log(task_id, f"✅ 获取字段key成功：{dict(zip(field_names, keys))}")
        return keys
    except Exception as exc:
        append_log(task_id, format_http_error("❌ 获取字段key失败", exc, resp))
        return []


async def update_item(
    headers: Dict[str, str],
    object_id: str,
    target_keys: List[str],
    date: str,
    time: float,
    name: str,
    task_id: str,
    sprint_id: Optional[str] = None,
) -> bool:
    if not object_id or not target_keys or not time:
        append_log(
            task_id,
            "❌ 更新事项失败：事项id[object_id]，目标字段[target_keys] 或工时[time]为空",
        )
        return False
    try:
        ts = int(datetime.strptime(date, "%Y-%m-%d").timestamp() * 1000)
    except ValueError as exc:
        append_log(task_id, f"❌ 日期格式错误[{date}]：{exc}（正确格式：2025-10-14）")
        return False

    body: Dict[str, Any] = {"values": {"__screen_type": "view"}}
    if name:
        body["name"] = name
    for i, key in enumerate(target_keys):
        body["values"][key] = ts if i < 4 else time
    if sprint_id:
        body["values"]["sprint"] = [sprint_id]

    resp = None
    try:
        resp = await http_client.put(
            f"{settings.base_url}/api/team/parse/api/v2/items/{object_id}?detail=true",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        msg = f"✅ 更新事项[{object_id}]成功，目标日期：{date} | 工时：{time}个小时"
        if sprint_id:
            msg += f" | 迭代ID：{sprint_id}"
        append_log(task_id, msg)
        return True
    except Exception as exc:
        append_log(
            task_id, format_http_error(f"❌ 更新事项[{object_id}]失败", exc, resp)
        )
        return False
