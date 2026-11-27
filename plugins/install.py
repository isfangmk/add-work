"""安装 / 卸载 add-work 的 funcpatch 补丁：只写 site-packages 里的 .pth，
不改动主分支任何源码。

用法（在仓库根目录）：
    .venv/Scripts/python.exe plugins/install.py             # 安装
    .venv/Scripts/python.exe plugins/install.py --uninstall # 卸载

补丁是否生效由 FUNC_PATCH_ENABLED / funcpatch.toml 选择；
业务动作是否执行由 REMINDER_ENABLED / WORKLOG_PUSH_ENABLED 控制。
"""

from __future__ import annotations

import argparse
import shutil
import site
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PTH_NAME = "_addwork_funcpatch.pth"
OLD_PTH_NAME = "_addwork_weekly_reminder.pth"


def _site_packages() -> Path:
    candidates = [Path(p) for p in site.getsitepackages()]
    for p in candidates:
        if "site-packages" in str(p) and p.exists():
            return p
    return candidates[0]


def _pth_content() -> str:
    # 补丁包名为 plugins，.pth 需把仓库根目录加入 sys.path
    repo_root = str(REPO_ROOT).replace("\\", "/")
    return f"{repo_root}\nimport plugins.bootstrap\n"


def _ensure_funcpatch() -> None:
    try:
        import funcpatch  # noqa: F401

        print(f"[OK] funcpatch 已存在: {funcpatch.__version__}")
        return
    except ImportError:
        pass
    print("[..] 未检测到 funcpatch，正在安装到当前解释器 ...")
    # uv 管理的虚拟环境没有 pip，优先用 uv；否则退回 pip。
    if shutil.which("uv"):
        subprocess.check_call(["uv", "pip", "install", "--python", sys.executable, "funcpatch"])
    else:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "funcpatch"])


def install() -> None:
    sp = _site_packages()
    _ensure_funcpatch()
    # 移除不再使用的历史启动钩子（若存在）
    (sp / OLD_PTH_NAME).unlink(missing_ok=True)
    pth = sp / PTH_NAME
    pth.write_text(_pth_content(), encoding="utf-8")
    print(f"[OK] 已写入启动钩子: {pth}")
    print("     解释器启动时将 import plugins.bootstrap")
    print()
    print("启用业务动作（在当前 shell）：")
    print("  export REMINDER_ENABLED=true       # 上周工时周报（启动时调度）")
    print("  export WORKLOG_PUSH_ENABLED=true   # 工时填报结果推送（任务完成时触发）")
    print("  # 全局关闭补丁：export FUNC_PATCH_ENABLED=false")


def uninstall() -> None:
    sp = _site_packages()
    for name in (PTH_NAME, OLD_PTH_NAME):
        pth = sp / name
        if pth.exists():
            pth.unlink()
            print(f"[OK] 已移除启动钩子: {pth}")
    print("启动钩子不存在时无需卸载")


def main() -> None:
    parser = argparse.ArgumentParser(description="安装/卸载 add-work funcpatch 补丁")
    parser.add_argument("--uninstall", action="store_true", help="卸载补丁")
    args = parser.parse_args()
    if args.uninstall:
        uninstall()
    else:
        install()


if __name__ == "__main__":
    main()
