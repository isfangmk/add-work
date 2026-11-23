"""关注空间数据库 CRUD 测试。"""

from __future__ import annotations

from app.storage import db


def test_empty_favorites_for_new_user():
    assert db.get_favorite_workspaces("new_user") == []


def test_replace_favorites():
    workspaces = [
        {"workspace_key": "09", "workspace_name": "One-RUM"},
        {"workspace_key": "17", "workspace_name": "One-APM"},
    ]
    db.replace_favorite_workspaces("alice", workspaces)
    assert db.get_favorite_workspaces("alice") == workspaces


def test_replace_overwrites_existing():
    db.replace_favorite_workspaces("alice", [{"workspace_key": "09", "workspace_name": "One-RUM"}])
    db.replace_favorite_workspaces("alice", [{"workspace_key": "16", "workspace_name": "ONE-Meta"}])
    result = db.get_favorite_workspaces("alice")
    assert len(result) == 1
    assert result[0]["workspace_key"] == "16"


def test_add_favorite_is_idempotent():
    db.replace_favorite_workspaces("bob", [])
    assert db.add_favorite_workspace("bob", "09", "One-RUM") is True
    assert db.add_favorite_workspace("bob", "09", "One-RUM") is False
    assert len(db.get_favorite_workspaces("bob")) == 1


def test_add_favorite_appends():
    db.replace_favorite_workspaces("bob", [])
    db.add_favorite_workspace("bob", "09", "One-RUM")
    db.add_favorite_workspace("bob", "17", "One-APM")
    assert [w["workspace_key"] for w in db.get_favorite_workspaces("bob")] == ["09", "17"]


def test_add_favorite_rejects_empty():
    assert db.add_favorite_workspace("bob", "", "One-RUM") is False
    assert db.add_favorite_workspace("bob", "09", "") is False


def test_favorites_are_per_user():
    db.replace_favorite_workspaces("alice", [{"workspace_key": "09", "workspace_name": "RUM"}])
    db.replace_favorite_workspaces("bob", [{"workspace_key": "17", "workspace_name": "APM"}])
    assert [w["workspace_key"] for w in db.get_favorite_workspaces("alice")] == ["09"]
    assert [w["workspace_key"] for w in db.get_favorite_workspaces("bob")] == ["17"]
