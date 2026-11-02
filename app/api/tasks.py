"""工时任务接口。"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.storage.db import get_workspace_configs
from app.core.exceptions import TaskNotFoundError, ValidationAppError, WorkspaceNotFoundError
from app.core.logger import get_logger
from app.schemas import ApiResponse, StartTaskRequest, TaskStatusResponse
from app.services.work import run_work_task
from app.storage.task_store import append_log, copy_logs, get_task, init_task, new_task_id

logger = get_logger(__name__)
router = APIRouter()


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
