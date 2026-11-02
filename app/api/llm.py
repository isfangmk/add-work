"""LLM 总结相关接口。"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.clients.llm import summarize_commits
from app.core.exceptions import ValidationAppError
from app.core.logger import get_logger
from app.schemas import ApiResponse, LLMSummaryRequest

logger = get_logger(__name__)
router = APIRouter()


@router.post("/llm-summary-by-range", response_model=ApiResponse)
async def llm_summary_by_range(request: LLMSummaryRequest) -> JSONResponse:
    try:
        logger.info(
            "LLM总结 start=%s end=%s exclude=%s",
            request.startDate,
            request.endDate,
            request.excludeDates,
        )
        raw = await summarize_commits(
            request.gitEmail,
            request.startDate,
            request.endDate,
            request.excludeDates or [],
        )
        logger.info("总结结果：%s", raw)
        if not raw:
            return JSONResponse(
                ApiResponse.ok(
                    data={},
                    msg="该日期范围内没有可用的 Git 提交记录",
                ).model_dump()
            )

        summary = json.loads(raw)
        cleaned = {
            k: (v[0] if isinstance(v, list) and v else str(v))
            for k, v in summary.items()
        }
        if not cleaned:
            return JSONResponse(
                ApiResponse.ok(
                    data={},
                    msg="该日期范围内没有可用的 Git 提交记录",
                ).model_dump()
            )
        return JSONResponse(ApiResponse.ok(data=cleaned).model_dump())
    except json.JSONDecodeError as exc:
        logger.error("JSON解析失败：%s", exc)
        raise ValidationAppError("LLM返回的JSON格式无效") from exc
    except Exception as exc:
        logger.error("LLM总结失败：%s", exc)
        raise HTTPException(status_code=500, detail=f"LLM总结失败：{exc}") from exc
