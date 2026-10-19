"""HTTP API（路径与响应结构保持兼容）。"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.clients.llm import summarize_commits
from app.config import settings
from app.db import get_workspace_configs, save_feedback
from app.exceptions import (
    AuthAppError,
    TaskNotFoundError,
    ValidationAppError,
    WorkspaceNotFoundError,
)
from app.logger import get_logger
from app.schemas import (
    ApiResponse,
    CurrentUserRequest,
    FeedbackRequest,
    LLMSummaryRequest,
    SprintListRequest,
    StartTaskRequest,
    TaskStatusResponse,
    WorkItemsRequest,
)
from app.services import load_calendar_items, resolve_current_user, run_work_task
from app.clients import gitee
from app.task_store import (
    append_log,
    copy_logs,
    get_task,
    init_task,
    new_task_id,
)

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
            return JSONResponse(ApiResponse.ok(data={}).model_dump())

        summary = json.loads(raw)
        cleaned = {
            k: (v[0] if isinstance(v, list) and v else str(v))
            for k, v in summary.items()
        }
        return JSONResponse(ApiResponse.ok(data=cleaned).model_dump())
    except json.JSONDecodeError as exc:
        logger.error("JSON解析失败：%s", exc)
        raise ValidationAppError("LLM返回的JSON格式无效") from exc
    except Exception as exc:
        logger.error("LLM总结失败：%s", exc)
        raise HTTPException(status_code=500, detail=f"LLM总结失败：{exc}") from exc


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


@router.post("/start-task", response_model=ApiResponse)
async def start_task(request: StartTaskRequest) -> JSONResponse:
    try:
        if not request.lengths_match():
            raise ValidationAppError("名称、工时、日期、迭代、工作空间列表长度不一致")

        workspace_names = request.resolved_workspace_names()
        configs = get_workspace_configs()
        for name in workspace_names:
            if name not in configs:
                raise WorkspaceNotFoundError(name)

        task_id = new_task_id()
        init_task(task_id)
        append_log(task_id, "📋 任务已创建，准备执行...")

        asyncio.create_task(
            run_work_task(
                request.username,
                settings.build_headers(request.cookie),
                request.sourceObjectId,
                request.names,
                request.sprintIds,
                request.times,
                request.dates,
                workspace_names,
                task_id,
                is_update=request.is_update,
            )
        )
        return JSONResponse(
            ApiResponse.ok(data={"taskId": task_id}, msg="任务已启动").model_dump()
        )
    except (ValidationAppError, WorkspaceNotFoundError):
        raise
    except Exception as exc:
        logger.error("启动任务失败：%s", exc)
        raise HTTPException(status_code=500, detail=f"启动任务失败：{exc}") from exc


@router.get("/task-status", response_model=TaskStatusResponse)
async def task_status(task_id: str) -> JSONResponse:
    task = get_task(task_id)
    if task is None:
        raise TaskNotFoundError(task_id)
    return JSONResponse(
        TaskStatusResponse(
            running=task["running"],
            log=copy_logs(task_id),
            success=task.get("success"),
        ).model_dump()
    )


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
        ApiResponse.ok(data={"id": feedback_id}, msg="反馈已提交，感谢你的建议").model_dump()
    )
