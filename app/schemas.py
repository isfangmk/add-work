"""请求 / 响应 Schema（对外字段名保持兼容）。"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LLMSummaryRequest(BaseModel):
    gitEmail: str
    startDate: str
    endDate: str
    excludeDates: Optional[List[str]] = Field(default_factory=list)


class SprintListRequest(BaseModel):
    cookie: str
    workspace_name: str


class WorkItemsRequest(BaseModel):
    cookie: str
    startDate: str
    endDate: str
    username: str = Field(..., min_length=1)
    gitEmail: Optional[str] = None


class CurrentUserRequest(BaseModel):
    cookie: str


class StartTaskRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    username: Optional[str] = None
    cookie: str
    sourceObjectId: str
    workspace_name: str
    workspaceNames: Optional[List[str]] = None
    names: List[str] = Field(..., min_length=1)
    sprintIds: List[str]
    times: List[float] = Field(..., min_length=1)
    dates: List[str] = Field(..., min_length=1)
    is_update: bool = False

    @field_validator("times")
    @classmethod
    def _times_positive(cls, values: List[float]) -> List[float]:
        if not all(t > 0 for t in values):
            raise ValueError("工时须为大于 0 的有效数字")
        return values

    def resolved_workspace_names(self) -> List[str]:
        if self.workspaceNames:
            return self.workspaceNames
        return [self.workspace_name] * len(self.names)

    def lengths_match(self) -> bool:
        lengths = {len(self.names), len(self.dates), len(self.times), len(self.sprintIds)}
        if self.workspaceNames is not None:
            lengths.add(len(self.workspaceNames))
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
