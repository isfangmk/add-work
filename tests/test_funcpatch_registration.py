"""funcpatch 注册与引导的端到端测试。

验证 .pth 引导后补丁确实应用到主分支函数，且全局开关生效。
测试进程由 pytest 启动，.pth 的 import 行会在解释器启动时执行，
因此这里直接检查已注册的状态。
"""

from __future__ import annotations

from funcpatch import get_registry, is_patched

from plugins import SPECS, finish_task_spec, init_db_spec, run_work_task_spec


def test_specs_registered():
    assert finish_task_spec in SPECS
    assert init_db_spec in SPECS
    assert run_work_task_spec in SPECS
    assert {s.target for s in SPECS} == {
        "app.storage.task_store:finish_task",
        "app.storage.db:init_db",
        "app.services.work:run_work_task",
    }


def test_all_specs_are_wrap_mode():
    assert all(s.mode == "wrap" for s in SPECS)
    assert all(s.owner == "addwork" for s in SPECS)


def test_third_spec_targets_async_work_task():
    import inspect

    assert inspect.iscoroutinefunction(run_work_task_spec.replacement)


def test_registry_applied_to_main_branch_functions():
    reg = get_registry()
    assert reg is not None
    assert is_patched("app.storage.task_store:finish_task")
    assert is_patched("app.storage.db:init_db")
    assert all(reg.is_applied(s.target) for s in SPECS)


def test_original_functions_recoverable():
    reg = get_registry()
    assert reg is not None
    for spec in SPECS:
        original = reg.get_original(spec.target)
        assert original is not None
        assert callable(original)
