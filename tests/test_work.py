"""工时编排逻辑测试：日历按关注空间过滤、失败容错、自动收藏。"""

from __future__ import annotations

import pytest

from app.clients import gitee
from app.services import work
from app.storage import db

ALL_WORKSPACES = [
    {"workspace_name": "One-RUM", "workspace_key": "09"},
    {"workspace_name": "One-APM", "workspace_key": "17"},
    {"workspace_name": "ONE-Meta", "workspace_key": "16"},
]


@pytest.fixture
def mock_workspaces(monkeypatch):
    async def fake_list(headers):
        return [dict(w) for w in ALL_WORKSPACES]

    monkeypatch.setattr(gitee, "list_workspaces", fake_list)


@pytest.mark.asyncio
async def test_empty_favorites_skips_all_queries(mock_workspaces, monkeypatch):
    """没有关注空间时不发起任何工时查询。"""
    called = []

    async def fake_search(*args, **kwargs):
        called.append(args)
        return []

    monkeypatch.setattr(gitee, "search_work_items", fake_search)
    batches, username, _ = await work.load_calendar_items(
        {}, "2026-11-16", "2026-11-22", "alice", "a@x.com"
    )
    assert batches == []
    assert called == []
    assert username == "alice"


@pytest.mark.asyncio
async def test_only_favorite_workspaces_are_queried(mock_workspaces, monkeypatch):
    """只查询已关注且用户可见的空间。"""
    db.replace_favorite_workspaces("alice", [{"workspace_key": "09", "workspace_name": "One-RUM"}])
    queried = []

    async def fake_search(username, headers, name, key, start, end):
        queried.append((name, key))
        return [{"date": "2026-11-16", "name": f"{name}工时"}]

    monkeypatch.setattr(gitee, "search_work_items", fake_search)
    batches, _user, _email = await work.load_calendar_items({}, "2026-11-16", "2026-11-22", "alice")
    assert queried == [("One-RUM", "09")]
    assert len(batches) == 1
    assert batches[0][0]["name"] == "One-RUM工时"


@pytest.mark.asyncio
async def test_failed_workspace_is_skipped(mock_workspaces, monkeypatch):
    """单个空间查询失败只跳过它，不影响其他空间。"""
    db.replace_favorite_workspaces(
        "alice",
        [
            {"workspace_key": "09", "workspace_name": "One-RUM"},
            {"workspace_key": "17", "workspace_name": "One-APM"},
        ],
    )

    async def fake_search(username, headers, name, key, start, end):
        if key == "09":
            raise RuntimeError("boom")
        return [{"date": "2026-11-16", "name": "ok"}]

    monkeypatch.setattr(gitee, "search_work_items", fake_search)
    batches, _user, _email = await work.load_calendar_items({}, "2026-11-16", "2026-11-22", "alice")
    assert len(batches) == 1
    assert batches[0][0]["name"] == "ok"


@pytest.mark.asyncio
async def test_workspace_not_visible_is_not_queried(mock_workspaces, monkeypatch):
    """收藏了但当前用户不可见的空间不查询。"""
    db.replace_favorite_workspaces(
        "alice", [{"workspace_key": "white-list-x", "workspace_name": "不存在空间"}]
    )
    queried = []

    async def fake_search(*args, **kwargs):
        queried.append(args)
        return []

    monkeypatch.setattr(gitee, "search_work_items", fake_search)
    batches, _user, _email = await work.load_calendar_items({}, "2026-11-16", "2026-11-22", "alice")
    assert queried == []
    assert batches == []
