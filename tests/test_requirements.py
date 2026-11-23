"""关联需求相关测试：需求搜索、写入 DataQuote01、编排透传。"""

from __future__ import annotations

import pytest

from app.clients import gitee
from app.core.http_client import http_client
from app.services import work


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_search_requirements_url_and_body(monkeypatch):
    """需求搜索走 DataQuote01 接口，body 含三空间与类型需求。"""
    captured = {}

    async def fake_post(url, headers=None, json=None):
        captured["url"] = url
        captured["body"] = json
        return _FakeResponse(
            {
                "payload": {
                    "items": [
                        {"id": "REQ1", "key": "105-1", "name": "需求一"},
                        {"id": "REQ2", "key": "", "name": "需求二"},
                    ]
                }
            }
        )

    monkeypatch.setattr(http_client, "post", fake_post)
    result = await gitee.search_requirements({}, keyword="工作流", size=10)

    assert captured["url"].endswith("/api/team/parse/api/search?from=DataQuote01")
    assert "产品中心" in captured["body"]["iql"]
    assert "26年春季正式版" in captured["body"]["iql"]
    assert "需求" in captured["body"]["iql"]
    assert "'标题' ~ '工作流'" in captured["body"]["iql"]
    assert "key = '工作流'" in captured["body"]["iql"]
    assert captured["body"]["size"] == 10
    assert captured["body"]["fromField"] == "DataQuote01"
    assert captured["body"]["refererInfo"]["workspaceId"] == "SyxVCy6BOs"
    assert result == [
        {"id": "REQ1", "key": "105-1", "name": "需求一"},
        {"id": "REQ2", "key": "", "name": "需求二"},
    ]


@pytest.mark.asyncio
async def test_search_requirements_escapes_keyword(monkeypatch):
    """关键字中的引号被转义，避免破坏 IQL。"""
    captured = {}

    async def fake_post(url, headers=None, json=None):
        captured["iql"] = json["iql"]
        return _FakeResponse({"payload": {"items": []}})

    monkeypatch.setattr(http_client, "post", fake_post)
    await gitee.search_requirements({}, keyword="a'b\"c")
    assert "a\\'b\\\"c" in captured["iql"]


@pytest.mark.asyncio
async def test_update_item_writes_data_quote(monkeypatch, real_gitee_writes):
    """update_item 带 data_quote_id 时，body 写入 DataQuote01 数组。"""
    captured = {}

    async def fake_put(url, headers=None, json=None):
        captured["body"] = json
        return _FakeResponse({})

    monkeypatch.setattr(http_client, "put", fake_put)
    ok = await gitee.update_item(
        {},
        "ITEM1",
        ["d1", "d2", "d3", "d4", "t1", "t2"],
        "2026-11-23",
        2.0,
        "事项",
        "TASK1",
        "SPRINT1",
        data_quote_id="REQ1",
    )

    assert ok is True
    assert captured["body"]["parseContext"] == {}
    assert captured["body"]["values"]["DataQuote01"] == ["REQ1"]
    assert captured["body"]["values"]["sprint"] == ["SPRINT1"]


@pytest.mark.asyncio
async def test_update_item_without_data_quote(monkeypatch, real_gitee_writes):
    """不传 data_quote_id 时 body 不含 DataQuote01（保持原行为）。"""
    captured = {}

    async def fake_put(url, headers=None, json=None):
        captured["body"] = json
        return _FakeResponse({})

    monkeypatch.setattr(http_client, "put", fake_put)
    await gitee.update_item({}, "ITEM1", ["d1"], "2026-11-23", 2.0, "事项", "TASK1")
    assert "DataQuote01" not in captured["body"]["values"]


@pytest.mark.asyncio
async def test_run_work_task_passes_data_quote_id(monkeypatch):
    """run_work_task 把每个事项的需求 id 透传给 update_item。"""
    db_module = __import__("app.storage.db", fromlist=["replace_favorite_workspaces"])
    db_module.replace_favorite_workspaces("alice", [])

    async def fake_list(headers):
        return [{"workspace_name": "One-RUM", "workspace_key": "09"}]

    async def fake_details(headers, keys):
        return {"09": {"workspace_id": "OID", "jump_url": ""}}

    async def fake_clone(*a, **k):
        return "NEWID"

    async def fake_keys(*a, **k):
        return ["k1"]

    seen = []

    async def fake_update(*a, **k):
        seen.append(k.get("data_quote_id"))
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
        ["事项A", "事项B"],
        ["S1", "S1"],
        [2.0, 1.0],
        ["2026-11-23", "2026-11-24"],
        ["One-RUM", "One-RUM"],
        "TASK1",
        data_quote_ids=["REQ1", ""],
    )
    assert seen == ["REQ1", None]


def test_start_task_request_requirement_ids():
    """StartTaskRequest 校验 requirementIds 长度并补齐空串。"""
    from app.schemas import StartTaskRequest

    base = dict(
        cookie="c",
        sourceObjectId="S",
        workspace_name="W",
        names=["a", "b"],
        sprintIds=["s1", "s2"],
        times=[1.0, 2.0],
        dates=["2026-11-23", "2026-11-24"],
    )
    # 长度不一致 → 不通过
    req = StartTaskRequest(**base, requirementIds=["REQ1"])
    assert req.lengths_match() is False

    # 长度一致 → 通过，补齐逻辑正常
    req = StartTaskRequest(**base, requirementIds=["REQ1", "REQ2"])
    assert req.lengths_match() is True
    assert req.resolved_requirement_ids() == ["REQ1", "REQ2"]

    # 不传 → 用空串补齐，长度校验不受影响
    req = StartTaskRequest(**base)
    assert req.lengths_match() is True
    assert req.resolved_requirement_ids() == ["", ""]
