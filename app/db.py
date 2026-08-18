"""SQLite 持久化。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)
_TZ = ZoneInfo("Asia/Shanghai")

_DEFAULT_WORKSPACES = [
    (
        "One-RUM",
        "VTuM6B3VeK",
        "09",
        "https://gitee.ibr.net.cn/Bonree/09/proxima/boards/8a4e4d4b-16f6-44f0-9b30-2c730476572b"
        "?component=Default&view=SVUXTVgxyp&iql=[iql]&pageIndex=1",
    ),
    (
        "One-APM",
        "PGQM3VhDkR",
        "17",
        "https://gitee.ibr.net.cn/Bonree/17/proxima/boards/60c254c3-4c55-46e7-8a91-914a5f5e01ef"
        "?component=Default&view=ljxigMMXTf&iql=[iql]&pageIndex=1",
    ),
    (
        "ONE-Meta",
        "xSSuAXE4X1",
        "16",
        "https://gitee.ibr.net.cn/Bonree/16/proxima/boards/f9d84977-8ee2-4861-aac0-38636f91fcae"
        "?component=Default&view=ynbkqxvVSi&iql=[iql]&pageIndex=1",
    ),
    (
        "Bonree-Swift-Ai",
        "SyxVCy6BOs",
        "04",
        "https://gitee.ibr.net.cn/Bonree/04/proxima/boards/13b31fcd-522d-4456-a5df-58cbb81c3008"
        "?component=Default&view=2dlBslHno0&iql=[iql]&pageIndex=1",
    ),
    (
        "One-ETL",
        "AU0gz8Tk2I",
        "14",
        "https://gitee.ibr.net.cn/Bonree/14/proxima/boards/266e7185-e099-44bc-b8a5-be7387099208"
        "?component=Default&view=0fjzzdbjX6&iql=[iql]&pageIndex=1",
    ),
    (
        "One-Pilot",
        "pgH5HDXgly",
        "12",
        "https://gitee.ibr.net.cn/Bonree/12/proxima/boards/9d719236-9dfc-46de-9de8-5b5cec7c6b7d"
        "?component=Default&view=Kbk9CUJRAE&iql=[iql]&pageIndex=1",
    ),
    (
        "ONE-Data",
        "5QMvUzUQHz",
        "02",
        "https://gitee.ibr.net.cn/Bonree/02/proxima/boards/c91bcf05-0496-4b8f-a39d-86ec8ee8eb99"
        "?component=Default&view=0lx1Sq7UAw&iql=[iql]&pageIndex=1",
    ),
]


def _now() -> str:
    return datetime.now(_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(settings.db_path)


def init_db() -> None:
    with _connect() as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS task_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                source_object_id TEXT NOT NULL,
                names TEXT NOT NULL,
                times TEXT NOT NULL,
                dates TEXT NOT NULL,
                workspace_name TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cookie_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                cookie TEXT NOT NULL,
                real_name TEXT,
                created_at TIMESTAMP NOT NULL
            );
            CREATE TABLE IF NOT EXISTS workspace_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_name TEXT NOT NULL UNIQUE,
                workspace_id TEXT NOT NULL,
                workspace_key TEXT NOT NULL,
                jump_url TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            );
            CREATE TABLE IF NOT EXISTS feedback_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                contact TEXT,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            );
            """
        )
        cur.execute("SELECT COUNT(*) FROM workspace_configs")
        if cur.fetchone()[0] == 0:
            logger.info("初始化默认 workspace 配置")
            for row in _DEFAULT_WORKSPACES:
                save_workspace_config(*row)
        cols = {
            row[1]
            for row in cur.execute("PRAGMA table_info(cookie_records)").fetchall()
        }
        if "real_name" not in cols:
            logger.info("cookie_records 增加 real_name 列")
            cur.execute("ALTER TABLE cookie_records ADD COLUMN real_name TEXT")
        conn.commit()


def get_cookie_record(username: str) -> Optional[Tuple[str, str]]:
    try:
        with _connect() as conn:
            return conn.execute(
                "SELECT username, cookie FROM cookie_records WHERE username = ? "
                "ORDER BY id DESC LIMIT 1",
                (username,),
            ).fetchone()
    except Exception as exc:
        logger.error("获取Cookie记录失败：%s", exc)
        return None


def get_cookie_record_by_real_name(real_name: str) -> Optional[Tuple[str, str]]:
    name = (real_name or "").strip()
    if not name:
        return None
    try:
        with _connect() as conn:
            return conn.execute(
                "SELECT username, cookie FROM cookie_records WHERE real_name = ? "
                "ORDER BY id DESC LIMIT 1",
                (name,),
            ).fetchone()
    except Exception as exc:
        logger.error("按中文名获取Cookie记录失败：%s", exc)
        return None


def upsert_cookie_record(
    username: str, cookie: str, real_name: Optional[str] = None
) -> None:
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT id FROM cookie_records WHERE username = ? ORDER BY id DESC LIMIT 1",
                (username,),
            ).fetchone()
            if row:
                conn.execute(
                    """
                    UPDATE cookie_records
                    SET cookie = ?, real_name = CASE
                        WHEN ? != '' THEN ? ELSE real_name END
                    WHERE id = ?
                    """,
                    (cookie, real_name or "", real_name or "", row[0]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO cookie_records (username, cookie, real_name, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (username, cookie, real_name or "", _now()),
                )
            conn.commit()
    except Exception as exc:
        logger.error("保存Cookie记录失败：%s", exc)


def save_cookie_record(
    username: str, cookie: str, real_name: Optional[str] = None
) -> None:
    upsert_cookie_record(username, cookie, real_name)


def update_cookie_real_name(username: str, real_name: str) -> None:
    name = (real_name or "").strip()
    if not name:
        return
    try:
        with _connect() as conn:
            conn.execute(
                "UPDATE cookie_records SET real_name = ? WHERE username = ?",
                (name, username),
            )
            conn.commit()
    except Exception as exc:
        logger.error("更新Cookie中文名失败：%s", exc)


def get_all_cookie_records() -> List[Tuple[str, str]]:
    try:
        with _connect() as conn:
            return conn.execute("SELECT username, cookie FROM cookie_records").fetchall()
    except Exception as exc:
        logger.error("获取所有Cookie记录失败：%s", exc)
        return []


def delete_cookie_record(username: str) -> None:
    try:
        with _connect() as conn:
            conn.execute("DELETE FROM cookie_records WHERE username = ?", (username,))
            conn.commit()
    except Exception as exc:
        logger.error("删除Cookie记录失败：%s", exc)


def save_task_record(
    username: str,
    source_object_id: str,
    names: List[str],
    times: List[float],
    dates: List[str],
    workspace_name: str,
) -> None:
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO task_records
                    (username, source_object_id, names, times, dates, workspace_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    source_object_id,
                    json.dumps(names, ensure_ascii=False),
                    json.dumps(times, ensure_ascii=False),
                    json.dumps(dates, ensure_ascii=False),
                    workspace_name,
                    _now(),
                ),
            )
            conn.commit()
    except Exception as exc:
        logger.error("保存任务记录失败：%s", exc)


def get_workspace_configs() -> Dict[str, Dict[str, str]]:
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT workspace_name, workspace_id, workspace_key, jump_url FROM workspace_configs"
            ).fetchall()
        return {
            name: {
                "workspace_id": wid,
                "workspace_key": wkey,
                "jump_url": jump,
            }
            for name, wid, wkey, jump in rows
        }
    except Exception as exc:
        logger.error("获取workspace配置失败：%s", exc)
        return {}


def get_workspace_key_by_name(workspace_name: str) -> Optional[str]:
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT workspace_key FROM workspace_configs WHERE workspace_name = ?",
                (workspace_name,),
            ).fetchone()
        return row[0] if row else None
    except Exception as exc:
        logger.error("获取workspace key失败：%s", exc)
        return None


def save_workspace_config(
    workspace_name: str,
    workspace_id: str,
    workspace_key: str,
    jump_url: str,
) -> bool:
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO workspace_configs
                    (workspace_name, workspace_id, workspace_key, jump_url, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (workspace_name, workspace_id, workspace_key, jump_url, _now()),
            )
            conn.commit()
        return True
    except Exception as exc:
        logger.error("保存workspace配置失败：%s", exc)
        return False


def save_feedback(
    content: str,
    username: Optional[str] = None,
    contact: Optional[str] = None,
) -> Optional[int]:
    """保存用户反馈，成功返回记录 id。"""
    try:
        with _connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO feedback_records (username, contact, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (username or "", contact or "", content, _now()),
            )
            conn.commit()
            return cur.lastrowid
    except Exception as exc:
        logger.error("保存反馈失败：%s", exc)
        return None
