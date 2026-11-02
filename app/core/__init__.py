"""核心基础设施：配置、日志、异常、HTTP 客户端。"""

from app.core.config import settings
from app.core.exceptions import (
    AppError,
    AuthAppError,
    NotFoundAppError,
    TaskNotFoundError,
    ValidationAppError,
    WorkspaceNotFoundError,
)
from app.core.http_client import close_http_client, format_http_error, http_client
from app.core.logger import get_logger

__all__ = [
    "settings",
    "get_logger",
    "AppError",
    "AuthAppError",
    "NotFoundAppError",
    "TaskNotFoundError",
    "ValidationAppError",
    "WorkspaceNotFoundError",
    "http_client",
    "close_http_client",
    "format_http_error",
]
