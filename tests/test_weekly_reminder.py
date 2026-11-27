"""周报补丁（plugins.weekly_reminder）的单元测试。

只测补丁自身逻辑：工作日计算、缺失判定、消息构造、调度门控与幂等、
通知请求体。不访问真实网络，不依赖 .pth。
"""

from __future__ import annotations

import importlib
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from plugins.weekly_reminder import builtin, cal, config, runner

# --------------------------- 工作日计算 ---------------------------


def test_is_workday_excludes_weekend():
    assert cal.is_workday(date(2026, 11, 21)) is False  # 周六
    assert cal.is_workday(date(2026, 11, 22)) is False  # 周日
    assert cal.is_workday(date(2026, 11, 23)) is True  # 周一


def test_workdays_for_week_excludes_national_holiday():
    workdays = builtin.workdays_for_week(date(2026, 9, 28))
    assert date(2026, 9, 28) in workdays
    assert date(2026, 9, 30) in workdays
    assert date(2026, 10, 1) not in workdays  # 国庆
    assert date(2026, 10, 3) not in workdays  # 周六+假期


def test_last_week_workdays_returns_monday_and_days():
    monday, days = cal.last_week_workdays(date(2026, 11, 26))
    assert monday == date(2026, 11, 16)
    assert all(d.weekday() < 5 for d in days)
    assert date(2026, 11, 16) in days
    assert date(2026, 11, 21) not in days


# --------------------------- 缺失判定与消息 ---------------------------


def test_find_missing_and_build_message():
    workdays = [date(2026, 11, 16), date(2026, 11, 17), date(2026, 11, 18)]
    items = {"alice": {"2026-11-16": 8.0, "2026-11-17": 8.0}}

    missing = builtin.find_missing(items, workdays)
    assert missing == {"alice": ["2026-11-18"]}

    message = builtin.build_message(missing, items, workdays)
    assert "alice" in message
    assert "2026-11-18" in message
    assert "❌未填" in message
    assert "✅" in message


def test_find_missing_respects_min_hours(monkeypatch):
    monkeypatch.setattr(
        builtin,
        "settings",
        config.ReminderSettings(min_hours_per_day=2.0),
    )
    workdays = [date(2026, 11, 16)]
    missing = builtin.find_missing({"bob": {"2026-11-16": 1.0}}, workdays)
    assert missing == {"bob": ["2026-11-16"]}


def test_build_message_empty_returns_empty():
    assert builtin.build_message({}, {}, []) == ""


# --------------------------- 调度门控与幂等 ---------------------------


class _Harness:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []
        self.cookie_records: list = []

    def fetch(self, cookie_records, workdays):
        return {"u": {d.isoformat(): 8.0 for d in workdays[:-1]}}

    def find(self, items, workdays):
        return {"u": [workdays[-1].isoformat()]}

    def build(self, missing, items, workdays):
        return "MISSING:" + ",".join(k for k in missing)

    def send(self, message, url):
        self.sent.append((message, url))
        return True


@pytest.mark.asyncio
async def test_run_check_gating_and_idempotency(monkeypatch):
    h = _Harness()
    # 2026-11-26 是周四（weekday=3），配置需匹配
    monkeypatch.setattr(runner, "settings", config.ReminderSettings(enabled=True, weekday=3))
    monkeypatch.setattr(runner, "_ran_weeks", set())
    monkeypatch.setattr(builtin, "load_cookie_records", lambda: h.cookie_records)
    monkeypatch.setattr(builtin, "fetch_weekly_items", h.fetch)
    monkeypatch.setattr(builtin, "find_missing", h.find)
    monkeypatch.setattr(builtin, "build_message", h.build)
    monkeypatch.setattr(builtin, "send_notification", h.send)

    now = datetime(2026, 11, 26, 10, 5, tzinfo=ZoneInfo("Asia/Shanghai"))  # 周四
    assert await runner.run_check(now) is True
    assert len(h.sent) == 1

    assert await runner.run_check(now) is False  # 同周幂等
    assert len(h.sent) == 1

    wrong_day = datetime(2026, 11, 27, 10, 5, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert await runner.run_check(wrong_day) is False

    early = datetime(2026, 11, 26, 9, 59, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert await runner.run_check(early) is False


@pytest.mark.asyncio
async def test_run_check_skips_when_no_data(monkeypatch):
    h = _Harness()
    monkeypatch.setattr(runner, "settings", config.ReminderSettings(enabled=True))
    monkeypatch.setattr(runner, "_ran_weeks", set())
    monkeypatch.setattr(builtin, "load_cookie_records", lambda: [])
    monkeypatch.setattr(builtin, "fetch_weekly_items", lambda c, w: {})
    monkeypatch.setattr(builtin, "send_notification", h.send)

    now = datetime(2026, 11, 26, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert await runner.run_check(now) is False
    assert h.sent == []


@pytest.mark.asyncio
async def test_run_check_disabled(monkeypatch):
    h = _Harness()
    monkeypatch.setattr(runner, "settings", config.ReminderSettings(enabled=False))
    monkeypatch.setattr(builtin, "send_notification", h.send)
    now = datetime(2026, 11, 23, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert await runner.run_check(now) is False
    assert h.sent == []


# --------------------------- 通知请求体 ---------------------------


def test_send_notification_payload(monkeypatch):
    captured: dict = {}

    class _FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"errcode": 0, "errmsg": "ok"}

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json):
            captured["url"] = url
            captured["json"] = json
            return _FakeResponse()

    import plugins.wecom as wecom

    monkeypatch.setattr(wecom.httpx, "Client", lambda **kwargs: _FakeClient())
    assert builtin.send_notification(message="hello", url="http://mock/webhook") is True
    assert captured["url"] == "http://mock/webhook"
    assert captured["json"]["msgtype"] == "markdown"
    assert captured["json"]["markdown"]["content"] == "hello"


def test_env_config(monkeypatch):
    monkeypatch.setenv("REMINDER_ENABLED", "true")
    monkeypatch.setenv("REMINDER_WEEKDAY", "3")
    monkeypatch.setenv("REMINDER_HOUR", "19")
    monkeypatch.setenv("REMINDER_MINUTE", "30")
    reloaded = importlib.reload(config)
    try:
        assert reloaded.settings.enabled is True
        assert reloaded.settings.weekday == 3
        assert reloaded.settings.hour == 19
        assert reloaded.settings.minute == 30
    finally:
        for key in ("REMINDER_ENABLED", "REMINDER_WEEKDAY", "REMINDER_HOUR", "REMINDER_MINUTE"):
            monkeypatch.delenv(key, raising=False)
        importlib.reload(config)


def test_settings_are_read_lazily_not_at_import(monkeypatch):
    """配置必须延迟到首次访问时读取。

    补丁经 .pth 在解释器启动时导入，此时主程序还没加载 .env，
    导入时读取会拿不到 .env 里的值。
    """
    monkeypatch.delenv("REMINDER_WEBHOOK_URL", raising=False)
    reloaded = importlib.reload(config)
    try:
        assert reloaded.settings.webhook_url == ""
        monkeypatch.setenv("REMINDER_WEBHOOK_URL", "https://example.test/webhook")
        # 不重新导入模块，仅刷新缓存即可拿到新值
        assert reloaded.settings.refresh().webhook_url == "https://example.test/webhook"
        assert reloaded.settings.webhook_url == "https://example.test/webhook"
    finally:
        monkeypatch.delenv("REMINDER_WEBHOOK_URL", raising=False)
        importlib.reload(config)
