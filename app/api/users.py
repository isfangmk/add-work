"""用户相关接口。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.exceptions import AuthAppError
from app.core.logger import get_logger
from app.schemas import ApiResponse, CurrentUserRequest
from app.services.work import resolve_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.post("/get-current-user", response_model=ApiResponse)
async def get_current_user(request: CurrentUserRequest) -> JSONResponse:
    try:
        username, git_email, _real_name = await resolve_current_user(request.cookie)
        if not username:
            raise AuthAppError("检查复制Cookie是否完整或已过期")
        return JSONResponse(
            ApiResponse.ok(
                data={"username": username, "gitEmail": git_email or ""}
            ).model_dump()
        )
    except AuthAppError:
        raise
    except Exception as exc:
        logger.error("获取当前用户失败：%s", exc)
        raise HTTPException(status_code=500, detail=f"获取当前用户失败：{exc}") from exc
