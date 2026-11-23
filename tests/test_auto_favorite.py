"""run_work_task 自动收藏未关注空间的测试。"""

from __future__ import annotations

import pytest

from app.clients import gitee
from app.services import work
from app.storage import db


@pytest.mark.asyncio
async def test_auto_favorite_unfavorited_workspace(monkeypatch):
    """写入成功的空间若未关注，自动加入收藏。"""
    db.replace_favorite_workspaces("alice", [])

    async def fake_list(headers):
        return [{"workspace_name": "One-RUM", "workspace_key": "09"}]

    async def fake_details(headers, keys):
        return {"09": {"workspace_id": "OID", "jump_url": ""}}

    async def fake_clone(*a, **k):
        return "NEWID"

    async def fake_keys(*a, **k):
        return ["k1"]

    async def fake_update(*a, **k):
        return True

    monkeypatch.setattr(gitee, "list_workspaces", fake_list)
    monkeypatch.setattr(gitee, "resolve_workspace_details", fake_details)
    monkeypatch.setattr(gitee, "clone_item", fake_clone)
    monkeypatch.setattr(gitee, "resolve_field_keys", fake_keys)
    monkeypatch.setattr(gitee, "update_item", fake_update)

    await work.run_work_task(
        "alice",
        {},
        "SOURCE",
        ["工时事项"],
        ["S1"],
        [2.0],
        ["2026-11-23"],
        ["One-RUM"],
        "TESTTASK",
    )
    assert db.get_favorite_workspaces("alice") == [
        {"workspace_key": "09", "workspace_name": "One-RUM"}
    ]


@pytest.mark.asyncio
async def test_no_auto_favorite_on_failed_update(monkeypatch):
    """写入失败时不自动收藏。"""
    db.replace_favorite_workspaces("alice", [])

    async def fake_list(headers):
        return [{"workspace_name": "One-RUM", "workspace_key": "09"}]

    async def fake_details(headers, keys):
        return {"09": {"workspace_id": "OID", "jump_url": ""}}

    async def fake_clone(*a, **k):
        return "NEWID"

    async def fake_keys(*a, **k):
        return ["k1"]

    async def fake_update(*a, **k):
        return False

    monkeypatch.setattr(gitee, "list_workspaces", fake_list)
    monkeypatch.setattr(gitee, "resolve_workspace_details", fake_details)
    monkeypatch.setattr(gitee, "clone_item", fake_clone)
    monkeypatch.setattr(gitee, "resolve_field_keys", fake_keys)
    monkeypatch.setattr(gitee, "update_item", fake_update)

    await work.run_work_task(
        "alice",
        {},
        "SOURCE",
        ["工时事项"],
        ["S1"],
        [2.0],
        ["2026-11-23"],
        ["One-RUM"],
        "TESTTASK2",
    )
    assert db.get_favorite_workspaces("alice") == []
