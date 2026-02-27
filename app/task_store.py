"""进程内异步任务状态。"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from app.logger import get_logger

logger = get_logger(__name__)

# {task_id: {"running": bool, "log": list[str], "success": bool|None}}
TASK_STATUS: Dict[str, Dict[str, Any]] = {}


def new_task_id() -> str:
    return str(uuid.uuid4())


def init_task(task_id: str) -> None:
    TASK_STATUS[task_id] = {"running": True, "log": [], "success": None}


def append_log(task_id: str, message: str) -> None:
    if task_id not in TASK_STATUS:
        init_task(task_id)
    TASK_STATUS[task_id]["log"].append(message)
    logger.info("TaskLog[%s]: %s", task_id, message)


def finish_task(task_id: str, success: bool) -> None:
    TASK_STATUS[task_id]["running"] = False
    TASK_STATUS[task_id]["success"] = success


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    return TASK_STATUS.get(task_id)


def copy_logs(task_id: str) -> List[str]:
    return TASK_STATUS[task_id]["log"].copy()
