"""日志：项目自身日志与 uvicorn 访问日志统一格式。"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict, Optional

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def new_formatter() -> logging.Formatter:
    return _ColoredFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)


class _ColoredFormatter(logging.Formatter):
    _COLORS = {
        "DEBUG": "\033[96m",
        "INFO": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "CRITICAL": "\033[95m\033[1m",
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        level = record.levelname
        color = self._COLORS.get(level)
        if color:
            record.levelname = f"{color}[{level}]{self._RESET}"
        try:
            return super().format(record)
        finally:
            record.levelname = level


def _handler_config() -> Dict[str, Any]:
    return {
        "class": "logging.StreamHandler",
        "stream": "ext://sys.stdout",
        "formatter": "app",
    }


def uvicorn_log_config() -> Dict[str, Any]:
    """供 uvicorn.run(log_config=...) 使用，统一 uvicorn 日志与项目日志格式。"""
    formatter = {"app": {"()": "app.core.logger.new_formatter"}}
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatter,
        "handlers": {"app": _handler_config()},
        "loggers": {
            "uvicorn": {"handlers": ["app"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["app"], "level": "INFO", "propagate": False},
            # 访问日志由应用中间件输出（含耗时），关闭 uvicorn 原生 access 避免重复
            "uvicorn.access": {"handlers": ["app"], "level": "WARNING", "propagate": False},
        },
        # uvicorn 默认 logger（含 access）走上面的配置
        "root": {"handlers": ["app"], "level": "INFO"},
    }


def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(new_formatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger
