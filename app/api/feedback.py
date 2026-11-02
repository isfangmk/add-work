"""用户反馈接口。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.storage.db import save_feedback
from app.core.exceptions import ValidationAppError
from app.core.logger import get_logger
from app.schemas import ApiResponse, FeedbackRequest

logger = get_logger(__name__)
router = APIRouter()


@router.post("/feedback", response_model=ApiResponse)
async def submit_feedback(request: FeedbackRequest) -> JSONResponse:
    content = (request.content or "").strip()
    if not content:
        raise ValidationAppError("反馈内容不能为空")

    feedback_id = save_feedback(
        content=content,
        username=(request.username or "").strip() or None,
        contact=(request.contact or "").strip() or None,
    )
    if feedback_id is None:
        raise HTTPException(status_code=500, detail="反馈保存失败，请稍后重试")

    logger.info(
        "收到反馈 id=%s username=%s contact=%s",
        feedback_id,
        request.username,
        request.contact,
    )
    return JSONResponse(
        ApiResponse.ok(
            data={"id": feedback_id}, msg="反馈已提交，感谢你的建议"
        ).model_dump()
    )
