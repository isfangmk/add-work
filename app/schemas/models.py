"""请求 / 响应 Schema（对外字段名保持兼容）。"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class LLMSummaryRequest(BaseModel):
    git_email: str
    start_date: str
    end_date: str
    exclude_dates: Optional[List[str]] = Field(default_factory=list)


class WorkspaceListRequest(BaseModel):
    cookie: str


class RequirementSearchRequest(BaseModel):
    cookie: str
    keyword: str = ""
    size: int = Field(default=20, ge=1, le=200)


class FavoriteWorkspaceItem(BaseModel):
    workspace_key: str
    workspace_name: str


class UserRequest(BaseModel):
    username: str = Field(..., min_length=1)


class FavoriteWorkspacesRequest(UserRequest):
    workspaces: List[FavoriteWorkspaceItem] = Field(default_factory=list)


class SprintListRequest(BaseModel):
    cookie: str
    workspace_name: str
    all_workspaces: bool = False
    keyword: str = ""


class WorkItemsRequest(BaseModel):
    cookie: str
    start_date: str
    end_date: str
    username: str = Field(..., min_length=1)
    git_email: Optional[str] = None


class CurrentUserRequest(BaseModel):
    cookie: str


class StartTaskRequest(BaseModel):
    username: Optional[str] = None
    cookie: str
    source_object_id: str
    workspace_name: str
    workspace_names: Optional[List[str]] = None
    names: List[str] = Field(..., min_length=1)
    sprint_ids: List[str]
    times: List[float] = Field(..., min_length=1)
    dates: List[str] = Field(..., min_length=1)
    requirement_ids: Optional[List[str]] = None
    is_update: bool = False

    @field_validator("times")
    @classmethod
    def _times_positive(cls, values: List[float]) -> List[float]:
        if not all(t > 0 for t in values):
            raise ValueError("工时须为大于 0 的有效数字")
        return values

    def resolved_workspace_names(self) -> List[str]:
        if self.workspace_names:
            return self.workspace_names
        return [self.workspace_name] * len(self.names)

    def resolved_requirement_ids(self) -> List[str]:
        if not self.requirement_ids:
            return [""] * len(self.names)
        # 长度已由 lengths_match 校验；不足时用空串补齐，保证与 names 一一对应
        return self.requirement_ids + [""] * (len(self.names) - len(self.requirement_ids))

    def lengths_match(self) -> bool:
        lengths = {len(self.names), len(self.dates), len(self.times), len(self.sprint_ids)}
        if self.workspace_names is not None:
            lengths.add(len(self.workspace_names))
        if self.requirement_ids is not None:
            lengths.add(len(self.requirement_ids))
        return len(lengths) == 1


class ApiResponse(BaseModel):
    success: bool
    msg: Optional[str] = None
    data: Optional[Any] = None

    @classmethod
    def ok(cls, data: Any = None, msg: str = "操作成功") -> "ApiResponse":
        return cls(success=True, data=data, msg=msg)

    @classmethod
    def fail(cls, msg: str) -> "ApiResponse":
        return cls(success=False, msg=msg)


class TaskStatusResponse(BaseModel):
    running: bool
    log: List[str]
    success: Optional[bool] = None


class FeedbackRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="反馈内容")
    username: Optional[str] = Field(default=None, description="用户名")
    contact: Optional[str] = Field(default=None, max_length=200, description="联系方式")
