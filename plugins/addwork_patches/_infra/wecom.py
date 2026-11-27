"""企业微信消息发送：中立基础设施，不依赖任何补丁。"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger("addwork_plugins.wecom")


async def send_markdown_async(message: str, url: str) -> bool:
    """异步发送 markdown 消息到企业微信机器人，返回是否成功。"""
    if not url or not message:
        return False
    payload = {"msgtype": "markdown", "markdown": {"content": message}}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") not in (0, None):
                logger.error("企业微信返回错误：%s", data)
                return False
            logger.info("企业微信消息已发送")
            return True
    except Exception as exc:
        logger.error("企业微信消息发送失败：%s", exc)
        return False


def send_markdown(message: str, url: str) -> bool:
    """发送 markdown 消息到企业微信机器人，返回是否成功。"""
    if not url or not message:
        return False
    payload = {"msgtype": "markdown", "markdown": {"content": message}}
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") not in (0, None):
                logger.error("企业微信返回错误：%s", data)
                return False
            logger.info("企业微信消息已发送")
            return True
    except Exception as exc:
        logger.error("企业微信消息发送失败：%s", exc)
        return False
