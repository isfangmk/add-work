"""Gitee / Parse API 客户端。"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.http_client import format_http_error, http_client
from app.core.logger import get_logger
from app.storage.task_store import append_log

logger = get_logger(__name__)
_TZ = ZoneInfo("Asia/Shanghai")

# {username+workspace_name: quoted_iql}
workspace_iql_cache: Dict[str, str] = {}

# {需求 id: {id, key, name}} 惰性缓存：命中直接用，未命中才查详情并回填
_requirement_cache: Dict[str, Dict[str, str]] = {}
_requirement_pending: Set[str] = set()


def _requirement_from_item(requirement_id: str, item: Dict[str, Any]) -> Dict[str, str]:
    return {
        "id": requirement_id,
        "key": item.get("key") or "",
        "name": item.get("name") or "",
    }


async def fetch_requirement(
    headers: Dict[str, str], requirement_id: str
) -> Optional[Dict[str, str]]:
    """取需求 {id, key, name}：命中缓存直接返回，未命中查详情回填（并发去重）。"""
    cached = _requirement_cache.get(requirement_id)
    if cached:
        return cached
    # 并发去重：同一 id 只发一次详情请求，其余等待其回填
    if requirement_id in _requirement_pending:
        for _ in range(50):  # 最多等 ~5s
            cached = _requirement_cache.get(requirement_id)
            if cached:
                return cached
            await asyncio.sleep(0.1)
        return None
    _requirement_pending.add(requirement_id)
    try:
        resp = await http_client.get(
            f"{settings.base_url}/api/team/parse/api/items/{quote(requirement_id, safe='')}"
            "?detail=true",
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        item = data.get("item") or data
        result = _requirement_from_item(requirement_id, item)
        _requirement_cache[requirement_id] = result
        return result
    except Exception as exc:
        logger.error(format_http_error(f"获取需求详情失败 id={requirement_id}", exc))
        return None
    finally:
        _requirement_pending.discard(requirement_id)


async def fetch_current_user(
    headers: Dict[str, str],
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    resp = None
    try:
        resp = await http_client.get(
            settings.base_url + settings.current_user_path, headers=headers
        )
        resp.raise_for_status()
        payload = resp.json().get("payload")
        if not payload:
            return None, None, None
        return (
            payload.get("displayName"),
            payload.get("gitEmail"),
            payload.get("enterpriseCard"),
        )
    except Exception as exc:
        logger.error(format_http_error("获取用户信息失败", exc, resp))
        return None, None, None


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
                "DataQuote01",
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
        requirement_ids: Set[str] = set()
        for item in resp.json()["payload"]["items"]:
            sprint = item["values"]["sprint"][0]
            # 关联需求：列表接口返回 id 字符串数组，详情接口可能返回对象，统一取第一个 id
            data_quote = item["values"].get("DataQuote01") or []
            first_quote = data_quote[0] if data_quote else None
            requirement_id = (
                first_quote.get("value") or first_quote.get("objectId")
                if isinstance(first_quote, dict)
                else first_quote
            ) or ""
            if requirement_id:
                requirement_ids.add(requirement_id)
            items.append(
                {
                    "object_id": item["objectId"],
                    "name": item["name"],
                    "sprint": sprint["name"],
                    "sprint_id": sprint["objectId"],
                    "time": item["values"]["field019"],
                    "date": datetime.fromtimestamp(item["values"]["Lkb66aTo"] / 1000, _TZ).strftime(
                        "%Y-%m-%d"
                    ),
                    "workspace_name": workspace_name,
                    "requirement_id": requirement_id,
                    "requirement_name": "",
                    "requirement_key": "",
                }
            )

        # 惰性缓存补全需求名称：并发查（未命中才请求详情，命中直接用缓存）
        if requirement_ids:
            details = await asyncio.gather(
                *[fetch_requirement(headers, rid) for rid in requirement_ids]
            )
            id_to_req = {d["id"]: d for d in details if d}
            for item in items:
                req = id_to_req.get(item["requirement_id"])
                if req:
                    item["requirement_name"] = req["name"]
                    item["requirement_key"] = req["key"]
        return items
    except Exception as exc:
        logger.error(format_http_error("搜索事项列表失败", exc, resp))
        return None


async def search_requirements(
    headers: Dict[str, str],
    keyword: str = "",
    size: int = 20,
) -> Optional[List[Dict[str, Any]]]:
    """按关键字搜索需求（服务端 IQL 模糊匹配标题或编号），不拉全量。

    实测该接口仅支持 '标题' ~ 'kw' 与 key = 'kw'，不支持名称字段的 contains/like。
    关键字为空时 '标题' ~ '' 等价于不过滤。
    """
    resp = None
    try:
        kw = (keyword or "").strip().replace("'", "\\'").replace('"', '\\"')
        spaces = ",".join(f'"{name}"' for name in settings.requirement_workspaces)
        iql = (
            f"('所属空间' in [{spaces}] "
            "and '类型' in [\"需求\"] "
            f"and ('标题' ~ '{kw}' or key = '{kw}')) order by  创建时间 desc"
        )
        body = {
            "iql": iql,
            "size": size,
            "from": 0,
            "extraSearchField": "",
            "fromField": "DataQuote01",
            "fields": ["name", "key", "status", "itemType", "id"],
            "refererInfo": {"workspaceId": settings.requirement_workspace_id},
        }
        resp = await http_client.post(
            settings.base_url + "/api/team/parse/api/search?from=DataQuote01",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        items = resp.json()["payload"]["items"]
        return [
            {
                "id": item["id"],
                "key": item.get("key", ""),
                "name": item.get("name", ""),
            }
            for item in items
            if item.get("id")
        ]
    except Exception as exc:
        logger.error(format_http_error("获取需求列表失败", exc, resp))
        return None


def _jump_url(workspace_key: str, board_key: str, view_id: str) -> str:
    return (
        f"{settings.base_url}/{settings.parse_app_id}/{workspace_key}/proxima"
        f"/boards/{board_key}?component=Default&view={view_id}&iql=[iql]&pageIndex=1"
    )


def _fallback_jump_url(workspace_key: str) -> str:
    return f"{settings.base_url}/{settings.parse_app_id}/{workspace_key}/proxima/all/boards"


async def list_workspaces(
    headers: Dict[str, str],
) -> Optional[List[Dict[str, str]]]:
    """拉取当前用户可见的全部工作空间。"""
    resp = None
    try:
        resp = await http_client.post(
            f"{settings.base_url}/api/one/{settings.parse_app_id}/rest/v2"
            f"/companies/{settings.parse_app_id}/projects/v2"
            "?name=&tags=&_limit=100&_offset=0&view=CARD",
            headers=headers,
            json={"customs": []},
        )
        resp.raise_for_status()
        return [
            {"workspace_name": item["name"], "workspace_key": item["uuid"]}
            for item in resp.json()
            if item.get("name") and item.get("uuid")
        ]
    except Exception as exc:
        logger.error(format_http_error("获取工作空间列表失败", exc, resp))
        return None


async def resolve_workspace_details(
    headers: Dict[str, str],
    workspace_keys: List[str],
) -> Dict[str, Dict[str, str]]:
    """按 workspace_key 批量解析 workspace_id 与 jump_url。

    jump_url 取空间的 All items 看板默认视图拼模板，
    解析不到看板时退化为空间看板列表页。
    """
    keys = list(dict.fromkeys(k for k in workspace_keys if k))
    details: Dict[str, Dict[str, str]] = {
        key: {"workspace_id": "", "jump_url": _fallback_jump_url(key)} for key in keys
    }
    if not keys:
        return details
    resp = None
    try:
        # Workspace 类反查 objectId（clone_item 需要）
        resp = await http_client.post(
            f"{settings.base_url}/api/team/parse/api/apps/schema/Workspace",
            headers=headers,
            json={"where": {"key": {"$in": keys}}, "limit": len(keys)},
        )
        resp.raise_for_status()
        rows = resp.json().get("results", [])
        oid_to_key = {row["objectId"]: row["key"] for row in rows}
        for row in rows:
            details[row["key"]]["workspace_id"] = row["objectId"]

        # 各空间的 All items 看板
        resp = await http_client.post(
            f"{settings.base_url}/api/team/parse/api/apps/schema/Board",
            headers=headers,
            json={
                "where": {
                    "name": "All items",
                    "workspace": {
                        "$inQuery": {
                            "where": {"key": {"$in": keys}},
                            "className": "Workspace",
                        }
                    },
                },
                "include": "workspace",
                "limit": len(keys),
            },
        )
        resp.raise_for_status()
        boards = resp.json().get("results", [])

        # 看板的默认视图
        view_ids = [view["objectId"] for board in boards for view in board.get("views", [])]
        default_views: Dict[str, str] = {}
        if view_ids:
            resp = await http_client.post(
                f"{settings.base_url}/api/team/parse/api/apps/schema/View",
                headers=headers,
                json={
                    "where": {"key": "default", "objectId": {"$in": view_ids}},
                    "limit": len(view_ids),
                },
            )
            resp.raise_for_status()
            default_views = {
                view["objectId"]: view["objectId"] for view in resp.json().get("results", [])
            }

        for board in boards:
            workspace_ref = board.get("workspace") or {}
            key = workspace_ref.get("key") or oid_to_key.get(workspace_ref.get("objectId", ""), "")
            if not key or key not in details:
                continue
            view_id = next(
                (
                    default_views[view["objectId"]]
                    for view in board.get("views", [])
                    if view.get("objectId") in default_views
                ),
                "",
            )
            if view_id:
                details[key]["jump_url"] = _jump_url(key, board["key"], view_id)
        return details
    except Exception as exc:
        logger.error(format_http_error("解析工作空间详情失败", exc, resp))
        return details


async def list_sprints(
    headers: Dict[str, str],
    workspace_key: str,
    all_workspaces: bool = False,
    keyword: str = "",
) -> Optional[List[Dict[str, Any]]]:
    """拉取迭代列表。默认只当前空间未完成迭代；all_workspaces=True 拉全空间最近100条。keyword 按名称过滤。"""
    resp = None
    where_workspace = (
        {"$inQuery": {"where": {}, "limit": 9999, "className": "Workspace"}}
        if all_workspaces
        else {"$inQuery": {"where": {"key": workspace_key}, "className": "Workspace"}}
    )
    where: Dict[str, Any] = {
        "workspace": where_workspace,
        "completed": False,
    }
    kw = (keyword or "").strip()
    if kw:
        # 转义正则元字符，避免用户输入破坏查询；大小写不敏感
        where["name"] = {"$regex": re.escape(kw), "$options": "i"}
    body = {
        "where": where,
        "include": "workspace",
        "order": "-createdAt",
        "limit": 100,
    }
    try:
        resp = await http_client.post(
            f"{settings.base_url}/api/team/parse/api/apps/schema/Sprint",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        return [
            {
                "object_id": item["objectId"],
                "name": item["name"],
                "workspace_name": (item.get("workspace") or {}).get("name", "")
                if isinstance(item.get("workspace"), dict)
                else "",
            }
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
        field_map = {f.get("name"): f.get("key") for f in resp.json().get("fields", [])}
        keys: List[str] = []
        for name in field_names:
            if name not in field_map:
                missing = [n for n in field_names if n not in field_map]
                raise ValueError(f"字段不存在：{name}（缺失：{set(missing)}）")
            keys.append(field_map[name])
        append_log(task_id, f"✅ 获取字段key成功：{dict(zip(field_names, keys, strict=True))}")
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
    data_quote_id: Optional[str] = None,
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

    body: Dict[str, Any] = {"parseContext": {}, "values": {"__screen_type": "view"}}
    if name:
        body["name"] = name
    for i, key in enumerate(target_keys):
        body["values"][key] = ts if i < 4 else time
    if sprint_id:
        body["values"]["sprint"] = [sprint_id]
    if data_quote_id:
        body["values"]["DataQuote01"] = [data_quote_id]

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
        if data_quote_id:
            msg += f" | 关联需求：{data_quote_id}"
        append_log(task_id, msg)
        return True
    except Exception as exc:
        append_log(task_id, format_http_error(f"❌ 更新事项[{object_id}]失败", exc, resp))
        return False
