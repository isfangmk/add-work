"""应用配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Settings:
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "tasks.db"))

    gitlab_url: str = "http://newgitlab.ibr.net.cn/"
    project_ids: List[str] = field(default_factory=lambda: ["3", "40"])
    private_token: str = field(default_factory=lambda: os.getenv("PRIVATE_TOKEN", ""))

    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_base_url: str = field(
        default_factory=lambda: os.getenv(
            "OPENAI_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
        )
    )
    model: str = field(default_factory=lambda: os.getenv("MODEL", "doubao-seed-1-6-251015"))

    base_url: str = "https://gitee.ibr.net.cn"
    current_user_path: str = "/api/one/Bonree/rest/v1/companies/Bonree/users/current/center"
    parse_app_id: str = "Bonree"

    # 需求搜索：三空间范围与引用的 workspaceId
    requirement_workspaces: List[str] = field(
        default_factory=lambda: ["产品中心", "26年春季正式版", "26年1230预览版"]
    )
    requirement_workspace_id: str = "SyxVCy6BOs"
    # 仅用于文档展示的占位值，不是真实 Cookie（真实值禁止写入源码）
    cookie_example: str = "<PRE-GW-SESSION 的值>"

    heartbeat_interval: int = 600
    http_timeout: float = 30.0

    work_item_field_names: List[str] = field(
        default_factory=lambda: [
            "计划开始日期",
            "计划完成日期",
            "实际开始时间",
            "实际完成时间",
            "预估工时",
            "已登记工时",
        ]
    )

    path_prefix: str = "/add-work"
    # 浏览器同源部署时前端与 API 同源；如需跨域，按需配置（逗号分隔），不要与 credentials 同用通配
    cors_origins: List[str] = field(
        default_factory=lambda: [
            origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()
        ]
    )
    sqlite_web_password: str = field(default_factory=lambda: os.getenv("SQLITE_WEB_PASSWORD", ""))
    mcp_token: str = field(default_factory=lambda: os.getenv("MCP_TOKEN", ""))
    add_work_url: str = field(default_factory=lambda: os.getenv("ADD_WORK_URL", ""))

    def build_headers(self, cookie: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "x-parse-application-id": self.parse_app_id,
        }
        if cookie:
            if "PRE-GW-SESSION" not in cookie:
                cookie = f"PRE-GW-SESSION={cookie}"
            headers["cookie"] = cookie
        return headers


settings = Settings()
