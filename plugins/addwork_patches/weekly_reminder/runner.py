"""上周工时检查的调度与幂等。"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import builtin
from .config import settings

logger = logging.getLogger("addwork_patches.weekly")


def last_week_monday(today: date) -> date:
    this_monday = today - timedelta(days=today.weekday())
    return this_monday - timedelta(days=7)


_ran_weeks: set[date] = set()


async def run_check(now: datetime | None = None) -> bool:
    """执行一次上周工时检查 + 提醒；返回是否真的发送。"""
    now = now or datetime.now(ZoneInfo("Asia/Shanghai"))

    if not settings.enabled:
        logger.debug("插件未启用，跳过检查")
        return False

    if now.weekday() != settings.weekday:
        return False
    if now.hour != settings.hour:
        return False
    if now.minute < settings.minute:
        return False

    monday = last_week_monday(now.date())
    if monday in _ran_weeks:
        return False

    workdays = builtin.workdays_for_week(monday)
    if not workdays:
        logger.info("上周没有需要填工时的工作日，跳过")
        return False

    items = builtin.fetch_weekly_items(builtin.load_cookie_records(), workdays)
    missing = builtin.find_missing(items, workdays)
    if not items:
        _ran_weeks.add(monday)
        logger.info("没有可统计的工时数据，跳过本周周报")
        return False

    message = builtin.build_message(missing, items, workdays)
    if not message:
        return False

    ok = builtin.send_notification(message, settings.webhook_url)
    if ok:
        _ran_weeks.add(monday)
    return bool(ok)


async def scheduler_loop() -> None:
    """后台轮询循环：到点执行一次检查。"""
    logger.info(
        "工时提醒调度器已启动：每周%d %02d:%02d 检查上周工时",
        settings.weekday,
        settings.hour,
        settings.minute,
    )
    while True:
        try:
            await run_check()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("工时提醒检查异常")
        await asyncio.sleep(settings.check_interval_seconds)


_started = False
_start_lock = asyncio.Lock()


async def start_scheduler() -> None:
    """幂等启动周报调度线程（绑定调用方事件循环）。"""
    global _started
    async with _start_lock:
        if _started:
            return
        _started = True
        asyncio.create_task(scheduler_loop(), name="addwork-reminder")
