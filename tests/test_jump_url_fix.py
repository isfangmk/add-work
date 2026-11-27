"""jump_url 修复补丁的单元测试。

验证 wrap run_work_task 后：协程身份不变、IQL 缓存按 username+workspace 预热、
预热值与主分支 gitee.py 的写入逻辑一致、预热失败不影响任务本身。
"""

from __future__ import annotations

import inspect
from urllib.parse import quote

import pytest
from addwork_patches import jump_url_fix


def _expected_iql(username: str) -> str:
    return quote(f"'负责人' in [\"{username}\"] order by 实际完成时间 desc", safe="")


def test_spec_targets_run_work_task():
    spec = jump_url_fix.run_work_task_spec
    assert spec.target == "app.services.work:run_work_task"
    assert spec.mode == "wrap"
    assert spec.owner == "addwork"


def test_wrapper_is_coroutine_function():
    """async wrap 必须保持 iscoroutinefunction，否则 FastAPI/调用方会出错。"""
    assert inspect.iscoroutinefunction(jump_url_fix._run_work_task_wrapper)


@pytest.mark.asyncio
async def test_warm_cache_populates_expected_keys(monkeypatch):
    from app.clients import gitee

    monkeypatch.setattr(gitee, "workspace_iql_cache", {})

    # 用一个假的原函数，只提供签名供 bind_partial 提取参数
    async def fake_work_task(
        username,
        headers,
        source_object_id,
        names,
        sprint_ids,
        times,
        dates,
        workspace_names,
        task_id,
        *,
        is_update=False,
        data_quote_ids=None,
    ):
        return "ok"

    result = await jump_url_fix._run_work_task_wrapper(
        fake_work_task,
        None,
        ("fangmingkun", {}, "src", ["n1", "n2"], [], [], [], ["空间A", "空间B"], "t1"),
        {},
    )
    assert result == "ok"

    cache = gitee.workspace_iql_cache
    assert cache["fangmingkun空间A"] == _expected_iql("fangmingkun")
    assert cache["fangmingkun空间B"] == _expected_iql("fangmingkun")


@pytest.mark.asyncio
async def test_warm_cache_failure_does_not_break_task(monkeypatch):
    """预热抛异常时不能影响原任务执行。"""

    def broken_bind(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(inspect, "signature", broken_bind)

    async def fake_work_task():
        return "still-ok"

    result = await jump_url_fix._run_work_task_wrapper(fake_work_task, None, (), {})
    assert result == "still-ok"
