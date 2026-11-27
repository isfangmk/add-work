"""上周工时周报的业务逻辑。

刻意不复用 app.core.http_client（绑定主程序事件循环的 AsyncClient，跨线程复用有风险），
在本补丁自己的调度线程里自建客户端与直读 SQLite。
"""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import threading
from datetime import date, timedelta
from typing import Any, Dict, List, Tuple

import httpx

from . import cal
from .config import settings

logger = logging.getLogger("plugins.weekly_reminder")


def _resolve_db_path() -> str:
    if os.path.isabs(settings.db_path):
        return settings.db_path
    # 本文件位于 plugins/weekly_reminder/，上三级为项目根
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(repo_root, settings.db_path)


def workdays_for_week(monday: date) -> List[date]:
    """返回 monday 所在周（自然周）的工作日。"""
    days = [monday + timedelta(days=i) for i in range(7)]
    return [d for d in days if cal.is_workday(d)]


def load_cookie_records() -> List[Tuple[str, str]]:
    """读取 (username, cookie)：优先复用主程序 DB 模块，失败则直读 SQLite。"""
    try:
        from app.storage.db import get_all_cookie_records

        return [tuple(r) for r in get_all_cookie_records()]  # type: ignore[misc]
    except Exception as exc:
        logger.debug("复用主程序 DB 失败(%s)，改为直读 SQLite", exc)
    db_path = _resolve_db_path()
    if not os.path.isfile(db_path):
        logger.warning("数据库文件不存在：%s", db_path)
        return []
    try:
        with sqlite3.connect(db_path) as conn:
            return [
                (row[0], row[1])
                for row in conn.execute("SELECT username, cookie FROM cookie_records").fetchall()
            ]
    except Exception as exc:
        logger.error("读取 cookie_records 失败：%s", exc)
        return []


def _run_async(coro):  # type: ignore[no-untyped-def]
    """在独立线程的新事件循环里运行协程，避免与调用方已有 loop 冲突。"""
    box: Dict[str, Any] = {}

    def target() -> None:
        try:
            box["value"] = asyncio.run(coro)
        except BaseException as exc:
            box["error"] = exc

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join()
    if "error" in box:
        raise box["error"]
    return box.get("value")


def _headers(cookie: str) -> Dict[str, str]:
    if "PRE-GW-SESSION" not in cookie:
        cookie = f"PRE-GW-SESSION={cookie}"
    return {
        "Content-Type": "application/json",
        "x-parse-application-id": settings.parse_app_id,
        "cookie": cookie,
    }


async def _fetch_one(
    client: httpx.AsyncClient,
    username: str,
    cookie: str,
    start_date: str,
    end_date: str,
) -> Dict[str, float]:
    """拉取单个用户在日期区间内的工时，按日期汇总小时数。"""
    iql = (
        f"('实际完成时间' >= '{start_date}' and '实际完成时间' <= '{end_date}' "
        f"and '负责人' in [\"{username}\"] ) order by 实际完成时间 desc"
    )
    body = {
        "iql": iql,
        "size": 100,
        "from": 0,
        "execFieldBehaviors": True,
        "fields": ["id", "name", "field019", "Lkb66aTo", "assignee"],
    }
    by_date: Dict[str, float] = {}
    try:
        resp = await client.post(
            f"{settings.base_url}/api/team/parse/api/search", headers=_headers(cookie), json=body
        )
        resp.raise_for_status()
        for item in resp.json().get("payload", {}).get("items", []):
            values = item.get("values", {})
            raw_date = values.get("Lkb66aTo")
            hours = values.get("field019") or 0
            if not raw_date:
                continue
            day = date.fromtimestamp(raw_date / 1000).isoformat()
            try:
                by_date[day] = by_date.get(day, 0.0) + float(hours)
            except (TypeError, ValueError):
                pass
    except Exception as exc:
        logger.warning("用户[%s]工时查询失败：%s", username, exc)
    return by_date


def fetch_weekly_items(
    cookie_records: List[Any], workdays: List[date]
) -> Dict[str, Dict[str, float]]:
    if not cookie_records or not workdays:
        return {}
    start_date, end_date = workdays[0].isoformat(), workdays[-1].isoformat()

    async def _all() -> Dict[str, Dict[str, float]]:
        result: Dict[str, Dict[str, float]] = {}
        async with httpx.AsyncClient(timeout=30.0) as client:
            for username, cookie in cookie_records:
                result[username] = await _fetch_one(
                    client, str(username), str(cookie), start_date, end_date
                )
        return result

    return _run_async(_all())


def find_missing(items: Dict[str, Dict[str, float]], workdays: List[date]) -> Dict[str, List[str]]:
    missing: Dict[str, List[str]] = {}
    day_strs = [d.isoformat() for d in workdays]
    for username in items:
        hours_by_day = items.get(username) or {}
        absent = [d for d in day_strs if hours_by_day.get(d, 0.0) <= settings.min_hours_per_day]
        if absent:
            missing[username] = absent
    return missing


def build_message(
    missing: Dict[str, List[str]],
    items: Dict[str, Dict[str, float]] | None = None,
    workdays: List[date] | None = None,
) -> str:
    """逐日列出"已填/未填"明细。"""
    items = items or {}
    workdays = workdays or []
    day_strs = [d.isoformat() for d in workdays]

    if not items and not missing:
        return ""

    lines = ["**上周工时填报周报**", ""]
    has_missing = False

    for username in sorted(set(items) | set(missing)):
        hours_by_day = items.get(username, {}) or {}
        real_name = _real_name(username)
        who = real_name if real_name else username

        details: List[str] = []
        absent: List[str] = []
        for d in day_strs:
            hours = hours_by_day.get(d, 0.0)
            if hours and hours > settings.min_hours_per_day:
                details.append(f"{d} ✅{_fmt_hours(hours)}h")
            else:
                details.append(f"{d} ❌未填")
                absent.append(d)
        if absent:
            has_missing = True

        lines.append(f"**{who}（{username}）**")
        lines.append("　" + "｜".join(details))
        lines.append("")

    if has_missing:
        lines += ["请未填的同事尽快补齐，谢谢。"]
    else:
        lines += ["上周工时已全部填报，👍"]

    first = day_strs[0] if day_strs else ""
    last = day_strs[-1] if day_strs else ""
    lines += ["", f"> 统计口径：上周工作日（{first} ~ {last}），已排除周末与节假日"]
    return "\n".join(lines)


def _fmt_hours(hours: float) -> str:
    return str(int(hours)) if float(hours).is_integer() else f"{hours:g}"


def _real_name(username: str) -> str:
    try:
        with sqlite3.connect(_resolve_db_path()) as conn:
            row = conn.execute(
                "SELECT real_name FROM cookie_records WHERE username = ? ORDER BY id DESC LIMIT 1",
                (username,),
            ).fetchone()
            return str(row[0]) if row and row[0] else ""
    except Exception:
        return ""


def send_notification(message: str, url: str) -> bool:
    from .._infra.wecom import send_markdown

    ok = send_markdown(message, url)
    if ok:
        logger.info("工时周报已发送")
    return ok
