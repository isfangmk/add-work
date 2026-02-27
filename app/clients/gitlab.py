"""GitLab 提交查询。"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Union
from urllib.parse import quote

from app.config import settings
from app.http_client import http_client
from app.logger import get_logger

logger = get_logger(__name__)


async def _fetch_project(
    author: str,
    start_date: str,
    end_date: str,
    project_id: Union[str, int],
    since_iso: str,
    until_iso: str,
) -> List[Dict[str, str]]:
    url = (
        f"{settings.gitlab_url}/api/v4/projects/"
        f"{quote(str(project_id), safe='')}/repository/commits"
    )
    headers = {"PRIVATE-TOKEN": settings.private_token}
    result: List[Dict[str, str]] = []
    page = 1
    per_page = 100

    while True:
        resp = await http_client.get(
            url,
            headers=headers,
            params={
                "all": "true",
                "author": author,
                "since": since_iso,
                "until": until_iso,
                "per_page": per_page,
                "page": page,
            },
        )
        if resp.status_code != 200:
            logger.warning(
                "GitLab 请求失败 project=%s status=%s body=%s",
                project_id,
                resp.status_code,
                (resp.text or "")[:200],
            )
            return result

        data = resp.json()
        if not data:
            break

        for commit in data:
            day = (commit.get("authored_date") or "")[:10]
            if not day or day < start_date or day > end_date:
                continue
            subject = (commit.get("title") or commit.get("message") or "").split("\n")[0]
            result.append({"subject": subject.strip(), "date": day})

        if len(data) < per_page:
            break
        page += 1

    return result


async def fetch_commits(
    author: str,
    start_date: str,
    end_date: str,
    project_ids: Optional[Sequence[Union[str, int]]] = None,
) -> List[Dict[str, str]]:
    if not settings.private_token:
        logger.warning("PRIVATE_TOKEN 未设置")
        return []

    ids = list(project_ids or settings.project_ids)
    since_iso = f"{start_date}T00:00:00Z"
    until_iso = f"{end_date}T23:59:59Z"
    commits: List[Dict[str, str]] = []
    for pid in ids:
        commits.extend(
            await _fetch_project(author, start_date, end_date, pid, since_iso, until_iso)
        )
    return commits
