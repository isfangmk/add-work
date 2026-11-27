"""funcpatch 注册与引导的端到端测试。

验证 .pth 引导后补丁确实应用到主分支函数，且全局开关生效。
测试进程由 pytest 启动，.pth 的 import 行会在解释器启动时执行，
因此这里直接检查已注册的状态。
"""

from __future__ import annotations

from funcpatch import get_registry, is_patched

from plugins.bootstrap import SPECS, finish_task_spec, init_db_spec, run_work_task_spec


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


def test_package_init_does_not_import_patches():
    """包初始化不得导入补丁。

    Python 导入 ``plugins.<子包>`` 前会先执行 ``plugins/__init__.py``，
    若在此处导入全部补丁，单独引入一个补丁就会连带加载其余补丁。
    """
    import ast
    import pathlib

    init_src = pathlib.Path(__file__).resolve().parent.parent / "plugins" / "__init__.py"
    tree = ast.parse(init_src.read_text(encoding="utf-8"))

    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            # __future__ 之类的特殊导入不算业务依赖
            if node.module == "__future__":
                continue
            imported.extend(
                f"{node.module or '.' * node.level}.{alias.name}" for alias in node.names
            )

    assert imported == [], f"plugins/__init__.py 不应导入补丁，实际导入了：{imported}"
