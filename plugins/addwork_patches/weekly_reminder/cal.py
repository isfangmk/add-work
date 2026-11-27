"""工作日计算：排除周末与中国法定节假日。

优先用 chinese_calendar；未安装时用内置节假日表兜底。
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

logger = logging.getLogger("addwork_patches.weekly")

try:
    from chinese_calendar import is_holiday as _is_holiday

    _HAS_CALENDAR = True
except ImportError:
    _HAS_CALENDAR = False

_BUILTIN_HOLIDAYS: frozenset[date] = (
    frozenset(
        date.fromisoformat(s)
        for s in [
            # 2025
            "2025-01-01",
            "2025-01-28",
            "2025-01-29",
            "2025-01-30",
            "2025-01-31",
            "2025-02-01",
            "2025-02-02",
            "2025-02-03",
            "2025-02-04",
            "2025-04-04",
            "2025-04-05",
            "2025-04-06",
            "2025-05-01",
            "2025-05-02",
            "2025-05-03",
            "2025-05-04",
            "2025-05-05",
            "2025-05-31",
            "2025-06-01",
            "2025-06-02",
            "2025-10-01",
            "2025-10-02",
            "2025-10-03",
            "2025-10-04",
            "2025-10-05",
            "2025-10-06",
            "2025-10-07",
            "2025-10-08",
            # 2026
            "2026-01-01",
            "2026-01-02",
            "2026-01-03",
            "2026-02-16",
            "2026-02-17",
            "2026-02-18",
            "2026-02-19",
            "2026-02-20",
            "2026-02-21",
            "2026-02-22",
            "2026-02-23",
            "2026-04-04",
            "2026-04-05",
            "2026-04-06",
            "2026-05-01",
            "2026-05-02",
            "2026-05-03",
            "2026-05-04",
            "2026-05-05",
            "2026-06-19",
            "2026-06-20",
            "2026-06-21",
            "2026-09-25",
            "2026-09-26",
            "2026-09-27",
            "2026-10-01",
            "2026-10-02",
            "2026-10-03",
            "2026-10-04",
            "2026-10-05",
            "2026-10-06",
            "2026-10-07",
        ]
    )
    if not _HAS_CALENDAR
    else frozenset()
)


def is_workday(day: date) -> bool:
    """是否是需要填工时的工作日（排除周末 + 节假日）。"""
    if day.weekday() >= 5:
        return False
    if _HAS_CALENDAR:
        try:
            return not _is_holiday(day)
        except Exception as exc:
            logger.warning("节假日库查询失败(%s)，回退内置表", day, exc)
    return day not in _BUILTIN_HOLIDAYS


def last_week_workdays(today: date) -> tuple[date, list[date]]:
    """返回 (上周一, 上周所有工作日)。"""
    this_monday = today - timedelta(days=today.weekday())
    last_monday = this_monday - timedelta(days=7)
    days = [last_monday + timedelta(days=i) for i in range(7)]
    return last_monday, [d for d in days if is_workday(d)]
