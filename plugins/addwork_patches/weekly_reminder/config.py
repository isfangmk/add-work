"""周报提醒配置：全部通过环境变量注入。

配置在**首次访问时**才读取，而不是模块导入时：
补丁经 .pth 在解释器启动时导入，早于主程序加载 .env，
导入时读取会拿不到 .env 里的值。
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class ReminderSettings:
    enabled: bool = False
    weekday: int = 0  # 0=周一 ... 6=周日
    hour: int = 10
    minute: int = 0
    webhook_url: str = ""
    check_interval_seconds: int = 60
    min_hours_per_day: float = 0.0
    base_url: str = "https://gitee.ibr.net.cn"
    parse_app_id: str = "Bonree"
    db_path: str = "tasks.db"

    @classmethod
    def from_env(cls) -> ReminderSettings:
        return cls(
            enabled=_bool("REMINDER_ENABLED", False),
            weekday=_int("REMINDER_WEEKDAY", 0),
            hour=_int("REMINDER_HOUR", 10),
            minute=_int("REMINDER_MINUTE", 0),
            webhook_url=os.getenv("REMINDER_WEBHOOK_URL", "").strip(),
            check_interval_seconds=_int("REMINDER_CHECK_INTERVAL", 60),
            min_hours_per_day=float(os.getenv("REMINDER_MIN_HOURS", "0")),
            base_url=os.getenv("ADDWORK_BASE_URL", "https://gitee.ibr.net.cn"),
            parse_app_id=os.getenv("ADDWORK_PARSE_APP_ID", "Bonree"),
            db_path=os.getenv("DB_PATH", "tasks.db"),
        )


class _SettingsProxy:
    """延迟读取配置的代理：首次访问时才从环境变量取值。"""

    __slots__ = ("_cached",)

    def __init__(self) -> None:
        self._cached: ReminderSettings | None = None

    def _resolve(self) -> ReminderSettings:
        if self._cached is None:
            self._cached = ReminderSettings.from_env()
        return self._cached

    def __getattr__(self, name: str):
        return getattr(self._resolve(), name)

    def refresh(self) -> ReminderSettings:
        """重新从环境变量读取（供测试与配置变更后使用）。"""
        self._cached = None
        return self._resolve()


settings = _SettingsProxy()
