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
    model: str = field(
        default_factory=lambda: os.getenv("MODEL", "doubao-seed-1-6-251015")
    )

    base_url: str = "https://gitee.ibr.net.cn"
    current_user_path: str = (
        "/api/one/Bonree/rest/v1/companies/Bonree/users/current/center"
    )
    parse_app_id: str = "Bonree"

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
    sqlite_web_password: str = field(
        default_factory=lambda: os.getenv("SQLITE_WEB_PASSWORD", "")
    )

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
