"""解释器启动引导：把 add-work 补丁交给 funcpatch 管理。

.pth 中的 ``import addwork_patches.bootstrap`` 在解释器启动时执行；
这里只注册补丁与延迟钩子，不导入主分支目标模块，不改动任何主分支源码。
补丁是否生效由 funcpatch 的三层 owner 选择与 FUNC_PATCH_ENABLED 决定；
业务侧再按 REMINDER_ENABLED / WORKLOG_PUSH_ENABLED 决定是否实际动作。
"""

from __future__ import annotations

import logging

from funcpatch import SelectionConfig
from funcpatch import bootstrap as fp_bootstrap
from funcpatch.config import load_config

from . import SPECS

logger = logging.getLogger("addwork_patches.bootstrap")

_registry = None


def _config() -> SelectionConfig:
    config = load_config()
    if not config.default_owner:
        config = SelectionConfig("addwork", config.target_owners, config.enabled)
    return config


def load() -> None:
    """注册补丁并初始化 funcpatch（幂等）。"""
    global _registry
    _registry = fp_bootstrap(config=_config(), specs=list(SPECS))
    logger.info("add-work funcpatch 补丁已注册：%d 条", len(SPECS))


def unload() -> int:
    """回滚全部补丁，恢复主分支原函数。"""
    from funcpatch import shutdown

    global _registry
    count = shutdown()
    _registry = None
    return count


load()
