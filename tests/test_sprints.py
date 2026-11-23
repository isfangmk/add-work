"""迭代列表测试：当前空间过滤、全空间、关键词搜索。"""

from __future__ import annotations

import pytest

from app.clients import gitee
from app.core.http_client import http_client


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_list_sprints_default_current_workspace(monkeypatch):
    """默认只当前空间，where 带 workspace key，无 keyword。"""
    captured = {}

    async def fake_post(url, headers=None, json=None):
        captured["body"] = json
        return _FakeResponse(
            {"results": [{"objectId": "S1", "name": "迭代一", "workspace": {"name": "WS"}}]}
        )

    monkeypatch.setattr(http_client, "post", fake_post)
    result = await gitee.list_sprints({}, "04")

    where = captured["body"]["where"]
    assert where["workspace"]["$inQuery"]["where"] == {"key": "04"}
    assert "name" not in where
    assert captured["body"]["limit"] == 100
    assert result == [{"object_id": "S1", "name": "迭代一", "workspace_name": "WS"}]


@pytest.mark.asyncio
async def test_list_sprints_all_workspaces(monkeypatch):
    """all_workspaces=True 时 where 用空 + limit 9999。"""
    captured = {}

    async def fake_post(url, headers=None, json=None):
        captured["body"] = json
        return _FakeResponse({"results": []})

    monkeypatch.setattr(http_client, "post", fake_post)
    await gitee.list_sprints({}, "04", all_workspaces=True)

    in_query = captured["body"]["where"]["workspace"]["$inQuery"]
    assert in_query["where"] == {}
    assert in_query["limit"] == 9999


@pytest.mark.asyncio
async def test_list_sprints_keyword_escaped(monkeypatch):
    """keyword 用 $regex 且转义正则元字符。"""
    captured = {}

    async def fake_post(url, headers=None, json=None):
        captured["body"] = json
        return _FakeResponse({"results": []})

    monkeypatch.setattr(http_client, "post", fake_post)
    await gitee.list_sprints({}, "04", keyword="V4.0")

    name = captured["body"]["where"]["name"]
    assert name["$regex"] == r"V4\.0"
    assert name["$options"] == "i"
