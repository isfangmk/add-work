"""工时日历接口。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AuthAppError
from app.core.logger import get_logger
from app.schemas import ApiResponse, WorkItemsRequest
from app.services.work import group_items_by_date, load_calendar_items

logger = get_logger(__name__)
router = APIRouter()


@router.post("/get-work-items-by-range")
async def get_work_items_by_range(request: WorkItemsRequest) -> JSONResponse:
    try:
        results, username, _git_email = await load_calendar_items(
            settings.build_headers(request.cookie),
            request.start_date,
            request.end_date,
            request.username,
            request.git_email,
        )
        if results is None or username is None:
            raise AuthAppError("检查复制Cookie是否完整或已过期")

        return JSONResponse(ApiResponse.ok(data=group_items_by_date(results)).model_dump())
    except AuthAppError:
        raise
    except Exception:
        logger.exception("获取工作项失败")
        raise HTTPException(status_code=500, detail="获取工作项失败，请稍后重试") from None
