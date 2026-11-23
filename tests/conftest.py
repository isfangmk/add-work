"""pytest 全局 fixture：把数据库指向临时文件，并禁止真实写入工时。"""

from __future__ import annotations

import dataclasses

import pytest

from app.clients import gitee
from app.core import config
from app.storage import db

# 保存真实写入函数，供需要测试其 body 拼装的用例显式恢复（底层 HTTP 会被用例 mock，不会联网）
_REAL_CLONE_ITEM = gitee.clone_item
_REAL_UPDATE_ITEM = gitee.update_item


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """每个测试使用独立的临时 SQLite 库，绝不触碰真实 tasks.db。"""
    db_file = tmp_path / "test.db"
    # settings 是 frozen dataclass，用 replace 造临时副本，只改 db_path
    test_settings = dataclasses.replace(config.settings, db_path=str(db_file))
    monkeypatch.setattr(db, "settings", test_settings)
    db.init_db()
    return db_file


@pytest.fixture(autouse=True)
def block_work_writes(monkeypatch):
    """兜底保险：禁止真实写入工时（clone_item / update_item）。

    只读查询（搜索事项、列空间、列迭代、解析字段、用户信息）放行，
    因为读取不会污染线上数据。测试用例若确需覆盖写入路径，
    自行 monkeypatch 这两个函数即可（测试的 mock 会覆盖这里的兜底）。
    """

    async def forbidden(*args, **kwargs):
        raise AssertionError("测试中禁止真实写入工时，请先 mock gitee.clone_item / update_item")

    monkeypatch.setattr(gitee, "clone_item", forbidden)
    monkeypatch.setattr(gitee, "update_item", forbidden)


@pytest.fixture
def real_gitee_writes(monkeypatch):
    """显式恢复真实写入函数，用于测试其请求体拼装（用例必须自行 mock http_client）。"""
    monkeypatch.setattr(gitee, "clone_item", _REAL_CLONE_ITEM)
    monkeypatch.setattr(gitee, "update_item", _REAL_UPDATE_ITEM)
