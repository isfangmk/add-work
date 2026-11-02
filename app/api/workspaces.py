"""工作空间与迭代接口。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.clients import gitee
from app.core.config import settings
from app.storage.db import get_workspace_configs
from app.core.exceptions import AuthAppError, WorkspaceNotFoundError
from app.core.logger import get_logger
from app.schemas import ApiResponse, SprintListRequest

logger = get_logger(__name__)
router = APIRouter()


@router.get("/get-workspace-list", response_model=ApiResponse)
async def get_workspace_list() -> JSONResponse:
    configs = get_workspace_configs()
    data = [
        {
            "workspace_name": name,
            "workspace_id": cfg["workspace_id"],
            "workspace_key": cfg["workspace_key"],
        }
        for name, cfg in configs.items()
    ]
    return JSONResponse(ApiResponse.ok(data=data).model_dump())


@router.post("/get-sprint-list", response_model=ApiResponse)
async def get_sprint_list(request: SprintListRequest) -> JSONResponse:
    try:
        workspace = get_workspace_configs().get(request.workspace_name)
        if not workspace:
            raise WorkspaceNotFoundError(request.workspace_name)

        sprints = await gitee.list_sprints(
            settings.build_headers(request.cookie),
            workspace["workspace_key"],
            workspace["workspace_id"],
        )
        if sprints is None:
            raise AuthAppError("获取迭代列表失败，请检查Cookie是否有效")
        return JSONResponse(ApiResponse.ok(data=sprints).model_dump())
    except (WorkspaceNotFoundError, AuthAppError):
        raise
    except Exception as exc:
        logger.error("获取迭代列表失败：%s", exc)
        raise HTTPException(status_code=500, detail=f"获取迭代列表失败：{exc}") from exc
