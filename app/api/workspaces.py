"""工作空间与迭代接口。"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.clients import gitee
from app.core.config import settings
from app.core.exceptions import AuthAppError, WorkspaceNotFoundError
from app.core.logger import get_logger
from app.schemas import (
    ApiResponse,
    FavoriteWorkspacesRequest,
    RequirementSearchRequest,
    SprintListRequest,
    UserRequest,
    WorkspaceListRequest,
)
from app.storage.db import get_favorite_workspaces, replace_favorite_workspaces

logger = get_logger(__name__)
router = APIRouter()


async def _workspace_map(
    cookie: str,
) -> Dict[str, Dict[str, str]]:
    """按登录用户拉取工作空间，返回 {workspace_name: 配置}。"""
    headers = settings.build_headers(cookie)
    workspaces = await gitee.list_workspaces(headers)
    if workspaces is None:
        raise AuthAppError("获取工作空间列表失败，请检查Cookie是否有效")
    details = await gitee.resolve_workspace_details(
        headers, [w["workspace_key"] for w in workspaces]
    )
    return {
        w["workspace_name"]: {
            "workspace_id": details.get(w["workspace_key"], {}).get("workspace_id", ""),
            "workspace_key": w["workspace_key"],
        }
        for w in workspaces
    }


@router.post("/get-workspace-list")
async def get_workspace_list(request: WorkspaceListRequest) -> JSONResponse:
    configs = await _workspace_map(request.cookie)
    data: List[Dict[str, Any]] = [
        {
            "workspace_name": name,
            "workspace_id": cfg["workspace_id"],
            "workspace_key": cfg["workspace_key"],
        }
        for name, cfg in configs.items()
    ]
    return JSONResponse(ApiResponse.ok(data=data).model_dump())


@router.post("/get-favorite-workspaces")
async def get_favorite_workspaces_api(request: UserRequest) -> JSONResponse:
    data = get_favorite_workspaces(request.username)
    return JSONResponse(ApiResponse.ok(data=data).model_dump())


@router.post("/save-favorite-workspaces")
async def save_favorite_workspaces_api(request: FavoriteWorkspacesRequest) -> JSONResponse:
    replace_favorite_workspaces(request.username, [ws.model_dump() for ws in request.workspaces])
    return JSONResponse(ApiResponse.ok(msg="关注空间已保存").model_dump())


@router.post("/get-sprint-list")
async def get_sprint_list(request: SprintListRequest) -> JSONResponse:
    try:
        headers = settings.build_headers(request.cookie)
        workspace_key = ""
        if not request.all_workspaces:
            workspaces = await gitee.list_workspaces(headers)
            if workspaces is None:
                raise AuthAppError("获取工作空间列表失败，请检查Cookie是否有效")
            workspace_key = next(
                (
                    w["workspace_key"]
                    for w in workspaces
                    if w["workspace_name"] == request.workspace_name
                ),
                "",
            )
            if not workspace_key:
                raise WorkspaceNotFoundError(request.workspace_name)
        sprints = await gitee.list_sprints(
            headers, workspace_key, all_workspaces=request.all_workspaces, keyword=request.keyword
        )
        if sprints is None:
            raise AuthAppError("获取迭代列表失败，请检查Cookie是否有效")
        return JSONResponse(ApiResponse.ok(data=sprints).model_dump())
    except (WorkspaceNotFoundError, AuthAppError):
        raise
    except Exception:
        logger.exception("获取迭代列表失败")
        raise HTTPException(status_code=500, detail="获取迭代列表失败，请稍后重试") from None


@router.post("/search-requirements")
async def search_requirements(request: RequirementSearchRequest) -> JSONResponse:
    try:
        headers = settings.build_headers(request.cookie)
        requirements = await gitee.search_requirements(headers, request.keyword, request.size)
        if requirements is None:
            raise AuthAppError("获取需求列表失败，请检查Cookie是否有效")
        return JSONResponse(ApiResponse.ok(data=requirements).model_dump())
    except AuthAppError:
        raise
    except Exception:
        logger.exception("获取需求列表失败")
        raise HTTPException(status_code=500, detail="获取需求列表失败，请稍后重试") from None
