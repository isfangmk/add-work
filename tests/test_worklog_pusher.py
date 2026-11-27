"""工时填报结果推送补丁（addwork_patches.worklog_pusher）的单元测试。

覆盖 finish_task wrap 补丁的触发、消息格式、幂等、开关与非阻塞；
webhook 全部 mock，不访问真实网络。推送走原生 asyncio。
"""

from __future__ import annotations

import asyncio

import pytest
from addwork_patches import worklog_pusher as wp


async def _drain_pending():
    """等待当前事件循环上所有推送任务完成。"""
    while wp._pending:
        await asyncio.gather(*list(wp._pending), return_exceptions=True)
        await asyncio.sleep(0)


# --------------------------- 消息构造 ---------------------------


def test_build_message_contains_log():
    msg = wp.build_message("abc", True, ["任务开始", "处理第1个事项", "任务执行完成"])
    assert "工时填报结果" in msg
    assert "abc" in msg
    assert "成功" in msg
    assert "任务开始" in msg
    assert "处理第1个事项" in msg


def test_build_message_failure():
    msg = wp.build_message("xyz", False, ["失败"])
    assert "存在失败" in msg


# --------------------------- 异步推送与幂等 ---------------------------


@pytest.mark.asyncio
async def test_push_once_sends(monkeypatch):
    sent: list[tuple[str, str]] = []

    async def fake_send(msg, url):
        sent.append((msg, url))
        return True

    monkeypatch.setattr(wp, "send_markdown_async", fake_send)
    monkeypatch.setenv("WORKLOG_PUSH_WEBHOOK_URL", "http://mock")

    assert await wp.push_once("t1", True, ["ok"]) is True
    assert len(sent) == 1
    assert "t1" in sent[0][0]
    assert sent[0][1] == "http://mock"


@pytest.mark.asyncio
async def test_push_once_empty_message(monkeypatch):
    sent: list = []

    async def fake_send(msg, url):
        sent.append(msg)
        return True

    monkeypatch.setattr(wp, "send_markdown_async", fake_send)
    assert await wp.push_once("t1", True, []) is True
    assert len(sent) == 1


# --------------------------- wrap 补丁端到端 ---------------------------


@pytest.fixture
def patched_finish(monkeypatch):
    """每个用例独立：清空去重集合、mock 异步发送、确保开关打开。"""
    monkeypatch.setattr(wp, "_seen", set())
    sent: list[tuple[str, str]] = []

    async def fake_send(msg, url):
        sent.append((msg, url))
        return True

    monkeypatch.setattr(wp, "send_markdown_async", fake_send)
    monkeypatch.setenv("WORKLOG_PUSH_ENABLED", "true")
    return sent


@pytest.mark.asyncio
async def test_finish_task_patch_pushes_and_dedups(patched_finish):
    from app.storage import task_store as ts

    ts.init_task("t-1")
    ts.append_log("t-1", "任务开始")
    ts.append_log("t-1", "处理完成")
    ts.finish_task("t-1", True)
    await _drain_pending()

    assert len(patched_finish) == 1
    assert "任务开始" in patched_finish[0][0]

    # 同一 task 再 finish 不再推送（幂等）
    ts.finish_task("t-1", True)
    await asyncio.sleep(0.1)
    assert len(patched_finish) == 1


@pytest.mark.asyncio
async def test_finish_task_patch_disabled_no_push(monkeypatch):
    monkeypatch.setattr(wp, "_seen", set())
    sent: list = []

    async def fake_send(msg, url):
        sent.append(msg)
        return True

    monkeypatch.setattr(wp, "send_markdown_async", fake_send)
    monkeypatch.setenv("WORKLOG_PUSH_ENABLED", "false")

    from app.storage import task_store as ts

    ts.init_task("t-2")
    ts.append_log("t-2", "日志")
    ts.finish_task("t-2", True)
    await asyncio.sleep(0)
    assert sent == []


def test_finish_task_patch_keeps_original_behavior(monkeypatch):
    """wrap 补丁必须保留原 finish_task 的状态写入语义。"""
    monkeypatch.setattr(wp, "_seen", set())
    monkeypatch.setenv("WORKLOG_PUSH_ENABLED", "false")

    from app.storage import task_store as ts

    ts.init_task("t-3")
    ts.finish_task("t-3", False)
    task = ts.get_task("t-3")
    assert task is not None
    assert task["running"] is False
    assert task["success"] is False


@pytest.mark.asyncio
async def test_finish_task_patch_does_not_block_on_http(monkeypatch):
    """推送不得阻塞事件循环：即使 HTTP 很慢，finish_task 也应立即返回。"""
    monkeypatch.setattr(wp, "_seen", set())
    slow_sent: list = []

    async def slow_send(msg, url):
        await asyncio.sleep(0.3)  # 模拟慢速企业微信
        slow_sent.append(msg)

    monkeypatch.setattr(wp, "send_markdown_async", slow_send)
    monkeypatch.setenv("WORKLOG_PUSH_ENABLED", "true")

    from app.storage import task_store as ts

    ts.init_task("t-4")
    ts.append_log("t-4", "日志")
    loop = asyncio.get_running_loop()
    start = loop.time()
    ts.finish_task("t-4", True)
    elapsed = loop.time() - start

    # create_task 是 O(1)，调用方必须在 0.3s 的模拟 HTTP 耗时之前返回
    assert elapsed < 0.15, f"finish_task 阻塞了 {elapsed:.3f}s"
    assert len(wp._pending) == 1  # 推送任务已挂到事件循环
    await _drain_pending()
    assert len(slow_sent) == 1
