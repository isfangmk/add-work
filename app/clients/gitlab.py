"""GitLab 提交查询（按用户 Push 事件，不依赖分支名 / all=true）。"""

from __future__ import annotations

import asyncio
import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Sequence, Set, Union
from urllib.parse import quote

from app.core.config import settings
from app.core.http_client import http_client
from app.core.logger import get_logger

logger = get_logger(__name__)

_PER_PAGE = 100
_HEADERS = lambda: {"PRIVATE-TOKEN": settings.private_token}


def _api(path: str) -> str:
    base = settings.gitlab_url.rstrip("/")
    return f"{base}/api/v4{path}"


def _day_in_range(day: str, start_date: str, end_date: str) -> bool:
    return bool(day) and start_date <= day <= end_date


def _commit_item(subject: str, day: str) -> Optional[Dict[str, str]]:
    text = (subject or "").strip()
    if not text or not day:
        return None
    return {"subject": text.split("\n")[0].strip(), "date": day}


def _pick_user(users: List[Dict[str, Any]], author: str) -> Optional[Dict[str, Any]]:
    author_l = author.strip().lower()
    local = author_l.split("@", 1)[0] if "@" in author_l else author_l
    for user in users:
        fields = {
            str(user.get("email") or "").lower(),
            str(user.get("public_email") or "").lower(),
            str(user.get("username") or "").lower(),
            str(user.get("name") or "").lower(),
        }
        fields.discard("")
        if author_l in fields or local in fields:
            return user
    return users[0] if users else None


async def _resolve_user_id(author: str) -> Optional[int]:
    """用邮箱或用户名解析 GitLab user id。"""
    started = time.perf_counter()
    queries = [author]
    if "@" in author:
        local = author.split("@", 1)[0].strip()
        if local and local not in queries:
            queries.append(local)

    picked = None
    last_status = 0
    for query in queries:
        resp = await http_client.get(
            _api("/users"),
            headers=_HEADERS(),
            params={"search": query, "per_page": 20},
        )
        last_status = resp.status_code
        if resp.status_code != 200:
            logger.warning(
                "GitLab 查用户失败 query=%s status=%s body=%s",
                query,
                resp.status_code,
                (resp.text or "")[:200],
            )
            continue
        picked = _pick_user(resp.json() or [], author)
        if picked:
            break

    elapsed_ms = (time.perf_counter() - started) * 1000
    user_id = int(picked["id"]) if picked and picked.get("id") is not None else None
    if not user_id:
        logger.warning(
            "GitLab 未解析到用户 author=%s last_status=%s elapsed_ms=%.0f",
            author,
            last_status,
            elapsed_ms,
        )
        return None
    logger.info(
        "GitLab 解析用户 author=%s user_id=%s username=%s elapsed_ms=%.0f",
        author,
        user_id,
        picked.get("username"),
        elapsed_ms,
    )
    return user_id


async def _list_push_events(
    user_id: int, start_date: str, end_date: str
) -> List[Dict[str, Any]]:
    """拉取用户 pushed 事件。after/before 按日边界外扩一天，避免开区间漏边。"""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    after = (start - timedelta(days=1)).isoformat()
    before = (end + timedelta(days=1)).isoformat()

    events: List[Dict[str, Any]] = []
    page = 1
    started = time.perf_counter()
    while True:
        page_started = time.perf_counter()
        resp = await http_client.get(
            _api(f"/users/{user_id}/events"),
            headers=_HEADERS(),
            params={
                "action": "pushed",
                "after": after,
                "before": before,
                "per_page": _PER_PAGE,
                "page": page,
                "sort": "asc",
            },
        )
        page_ms = (time.perf_counter() - page_started) * 1000
        if resp.status_code != 200:
            logger.warning(
                "GitLab 事件失败 user_id=%s page=%s status=%s elapsed_ms=%.0f body=%s",
                user_id,
                page,
                resp.status_code,
                page_ms,
                (resp.text or "")[:200],
            )
            break

        batch = resp.json() or []
        logger.info(
            "GitLab 事件分页 user_id=%s page=%s status=200 raw=%s elapsed_ms=%.0f",
            user_id,
            page,
            len(batch),
            page_ms,
        )
        if not batch:
            break
        events.extend(batch)
        if len(batch) < _PER_PAGE:
            break
        page += 1

    logger.info(
        "GitLab 事件拉取完成 user_id=%s events=%s elapsed_ms=%.0f",
        user_id,
        len(events),
        (time.perf_counter() - started) * 1000,
    )
    return events


async def _commits_from_compare(
    project_id: Union[str, int],
    commit_from: str,
    commit_to: str,
    author: str,
    start_date: str,
    end_date: str,
) -> List[Dict[str, str]]:
    started = time.perf_counter()
    resp = await http_client.get(
        _api(f"/projects/{quote(str(project_id), safe='')}/repository/compare"),
        headers=_HEADERS(),
        params={"from": commit_from, "to": commit_to},
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    if resp.status_code != 200:
        logger.warning(
            "GitLab compare 失败 project=%s status=%s elapsed_ms=%.0f",
            project_id,
            resp.status_code,
            elapsed_ms,
        )
        return []

    author_l = author.strip().lower()
    local = author_l.split("@", 1)[0] if "@" in author_l else author_l
    result: List[Dict[str, str]] = []
    for commit in resp.json().get("commits") or []:
        email = str(commit.get("author_email") or "").lower()
        name = str(commit.get("author_name") or "").lower()
        if author_l and email != author_l and author_l not in email and local not in email:
            if author_l not in name and local not in name:
                continue
        day = (commit.get("authored_date") or commit.get("created_at") or "")[:10]
        if not _day_in_range(day, start_date, end_date):
            continue
        item = _commit_item(
            commit.get("title") or commit.get("message") or "", day
        )
        if item:
            result.append(item)
    logger.info(
        "GitLab compare 完成 project=%s from=%s to=%s count=%s elapsed_ms=%.0f",
        project_id,
        commit_from[:8],
        commit_to[:8],
        len(result),
        elapsed_ms,
    )
    return result


async def _commits_from_push_event(
    event: Dict[str, Any],
    author: str,
    start_date: str,
    end_date: str,
    allowed_projects: Set[str],
) -> List[Dict[str, str]]:
    project_id = event.get("project_id")
    if project_id is None or str(project_id) not in allowed_projects:
        return []

    push = event.get("push_data") or {}
    if not isinstance(push, dict):
        return []

    event_day = (event.get("created_at") or "")[:10]
    title = (push.get("commit_title") or "").strip()
    commit_from = (push.get("commit_from") or "").strip()
    commit_to = (push.get("commit_to") or "").strip()
    commit_count = int(push.get("commit_count") or 0)

    # 单提交或缺少 from：直接用事件标题
    if commit_count <= 1 or not commit_from or not commit_to or commit_from == commit_to:
        day = event_day
        if not _day_in_range(day, start_date, end_date):
            return []
        item = _commit_item(title, day)
        return [item] if item else []

    return await _commits_from_compare(
        project_id, commit_from, commit_to, author, start_date, end_date
    )


async def fetch_commits(
    author: str,
    start_date: str,
    end_date: str,
    project_ids: Optional[Sequence[Union[str, int]]] = None,
) -> List[Dict[str, str]]:
    if not settings.private_token:
        logger.warning("PRIVATE_TOKEN 未设置")
        return []

    author = (author or "").strip()
    if not author:
        logger.warning("GitLab author 为空")
        return []

    allowed = {str(pid) for pid in (project_ids or settings.project_ids)}
    started = time.perf_counter()
    logger.info(
        "GitLab 拉取开始(事件) author=%s range=%s~%s projects=%s",
        author,
        start_date,
        end_date,
        sorted(allowed),
    )

    user_id = await _resolve_user_id(author)
    if not user_id:
        logger.warning("GitLab 未找到用户 author=%s", author)
        return []

    events = await _list_push_events(user_id, start_date, end_date)
    batches = await asyncio.gather(
        *[
            _commits_from_push_event(ev, author, start_date, end_date, allowed)
            for ev in events
        ]
    )

    # 按 subject+date 去重，保持稳定顺序
    seen: Set[tuple] = set()
    commits: List[Dict[str, str]] = []
    for batch in batches:
        for item in batch:
            key = (item["date"], item["subject"])
            if key in seen:
                continue
            seen.add(key)
            commits.append(item)

    commits.sort(key=lambda x: x["date"], reverse=True)
    logger.info(
        "GitLab 拉取完成(事件) author=%s range=%s~%s count=%s events=%s elapsed_ms=%.0f",
        author,
        start_date,
        end_date,
        len(commits),
        len(events),
        (time.perf_counter() - started) * 1000,
    )
    return commits
