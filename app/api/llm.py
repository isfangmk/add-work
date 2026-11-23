"""LLM 总结相关接口。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.clients.llm import summarize_commits
from app.core.logger import get_logger
from app.schemas import ApiResponse, LLMSummaryRequest

logger = get_logger(__name__)
router = APIRouter()


@router.post("/llm-summary-by-range")
async def llm_summary_by_range(request: LLMSummaryRequest) -> JSONResponse:
    try:
        logger.info(
            "LLM总结 start=%s end=%s exclude=%s",
            request.start_date,
            request.end_date,
            request.exclude_dates,
        )
        summary = await summarize_commits(
            request.git_email,
            request.start_date,
            request.end_date,
            request.exclude_dates or [],
        )
        if not summary:
            return JSONResponse(
                ApiResponse.ok(
                    data={},
                    msg="该日期范围内没有可用的 Git 提交记录",
                ).model_dump()
            )
        return JSONResponse(ApiResponse.ok(data=summary).model_dump())
    except Exception:
        logger.exception("LLM总结失败")
        raise HTTPException(status_code=500, detail="LLM总结失败，请稍后重试") from None
