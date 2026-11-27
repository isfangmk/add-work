"""add-work 的 funcpatch 补丁集合。"""

from __future__ import annotations

from .jump_url_fix import run_work_task_spec
from .weekly_reminder import init_db_spec
from .worklog_pusher import finish_task_spec

SPECS = [finish_task_spec, init_db_spec, run_work_task_spec]

__all__ = ["SPECS", "finish_task_spec", "init_db_spec", "run_work_task_spec"]
