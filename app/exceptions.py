"""业务异常。"""

from fastapi import HTTPException, status


class AppError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class ValidationAppError(AppError):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class NotFoundAppError(AppError):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class AuthAppError(AppError):
    def __init__(self, detail: str = "Cookie无效或已过期"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class WorkspaceNotFoundError(NotFoundAppError):
    def __init__(self, workspace_name: str):
        super().__init__(detail=f"工作空间 '{workspace_name}' 不存在")


class TaskNotFoundError(NotFoundAppError):
    def __init__(self, task_id: str):
        super().__init__(detail=f"任务ID '{task_id}' 不存在")
