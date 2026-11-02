"""日志。"""

from __future__ import annotations

import logging
import sys
from typing import Optional


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


def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        _ColoredFormatter(
            "%(asctime)s %(levelname)s %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.propagate = False
    return logger
