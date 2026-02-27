"""LLM 总结。"""

from __future__ import annotations

import json
from typing import List, Optional

from openai import AsyncOpenAI

from app.clients.gitlab import fetch_commits
from app.config import settings
from app.http_client import http_client
from app.logger import get_logger

logger = get_logger(__name__)

_client: Optional[AsyncOpenAI] = None

_SYSTEM = """
你是智能总结专家，按以下规则处理Git提交信息：
1. 先按日期（YYYY-MM-DD）分组，同日期提交合并为1条总结
2. 总结内容：仅提炼核心功能点，不包含哈希值、作者等无关信息，简洁准确（单条不超过60字）
3. 输出格式：严格JSON字符串，key为日期（YYYY-MM-DD），value为对应总结，无其他额外内容
4. 禁止输出任何非JSON内容（如解释、注释、换行文本等），仅返回按日期降序的纯JSON字符串
""".strip()


def _get_client() -> Optional[AsyncOpenAI]:
    global _client
    if _client is not None:
        return _client
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY 未设置")
        return None
    try:
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            http_client=http_client,
        )
        return _client
    except Exception as exc:
        logger.error("初始化 LLM 客户端失败：%s", exc)
        return None


async def summarize_commits(
    author: str,
    start_date: str,
    end_date: str,
    exclude_dates: List[str],
) -> str:
    commits = await fetch_commits(author, start_date, end_date)
    exclude = set(exclude_dates)
    filtered = [c for c in commits if c.get("date") not in exclude]
    if not filtered:
        logger.warning("过滤后无提交")
        return ""

    client = _get_client()
    if not client:
        return ""

    prompt = json.dumps(filtered, ensure_ascii=False)
    logger.info("git提交信息：\n%s", prompt)
    model = settings.model
    extra_body = (
        {"thinking": {"type": "disabled"}}
        if model.startswith("doubao")
        else {"enable_thinking": False}
    )
    try:
        resp = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            model=model,
            temperature=0,
            max_tokens=500,
            extra_body=extra_body,
        )
        return resp.choices[0].message.content or ""
    except Exception as exc:
        logger.error("大模型调用失败：%s", exc)
        return ""
