"""HTTP API 路由汇总。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api import calendar, feedback, llm, tasks, users, workspaces

router = APIRouter()
router.include_router(llm.router)
router.include_router(workspaces.router)
router.include_router(users.router)
router.include_router(calendar.router)
router.include_router(tasks.router)
router.include_router(feedback.router)
