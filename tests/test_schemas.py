"""请求 Schema 校验测试。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import FavoriteWorkspacesRequest, UserRequest


def test_user_request_requires_username():
    with pytest.raises(ValidationError):
        UserRequest(username="")


def test_user_request_ok():
    assert UserRequest(username="fangmingkun").username == "fangmingkun"


def test_favorite_request_defaults_to_empty():
    req = FavoriteWorkspacesRequest(username="fangmingkun")
    assert req.workspaces == []


def test_favorite_request_parses_workspaces():
    req = FavoriteWorkspacesRequest(
        username="fangmingkun",
        workspaces=[
            {"workspace_key": "09", "workspace_name": "One-RUM"},
        ],
    )
    assert len(req.workspaces) == 1
    assert req.workspaces[0].workspace_key == "09"
    assert req.workspaces[0].workspace_name == "One-RUM"


def test_favorite_request_requires_key_and_name():
    with pytest.raises(ValidationError):
        FavoriteWorkspacesRequest(username="fangmingkun", workspaces=[{"workspace_key": "09"}])
