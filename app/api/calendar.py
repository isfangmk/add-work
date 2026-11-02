"""工时日历接口。"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AuthAppError
from app.core.logger import get_logger
from app.schemas import ApiResponse, WorkItemsRequest
from app.services.work import load_calendar_items

logger = get_logger(__name__)
router = APIRouter()


@router.post("/get-work-items-by-range", response_model=ApiResponse)
async def get_work_items_by_range(request: WorkItemsRequest) -> JSONResponse:
    try:
        results, username, _git_email = await load_calendar_items(
            settings.build_headers(request.cookie),
            request.startDate,
            request.endDate,
            request.username,
            request.gitEmail,
        )
        if results is None or username is None:
            raise AuthAppError("检查复制Cookie是否完整或已过期")

        week_items: Dict[str, list] = defaultdict(list)
        for batch in results:
            if not batch:
                continue
            for item in batch:
                week_items[item["date"]].append(item)

        return JSONResponse(ApiResponse.ok(data=dict(week_items)).model_dump())
    except AuthAppError:
        raise
    except Exception as exc:
        logger.error("获取工作项失败：%s", exc)
        raise HTTPException(status_code=500, detail=f"获取工作项失败：{exc}") from exc
