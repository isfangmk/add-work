"""启动脚本：同时启动后端（main.py）与前端（Vite dev server）。

funcpatch 补丁通过 .pth 在解释器启动时注册，业务开关由 REMINDER_* /
WORKLOG_PUSH_* 环境变量控制。默认使用当天日期/时间，便于立即触发一次周报。

用法：
    python start_all.py            # 启动前后端
    python start_all.py --stop     # 停止
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
PY = sys.executable
# Windows 下 npx 实际是 npx.cmd，直接调用 npx 会触发 WinError 2
NPM = "npm.cmd" if sys.platform == "win32" else "npm"


def _pth_path() -> Path:
    site_dir = Path(PY).parent.parent / "Lib" / "site-packages"
    if not site_dir.is_dir():
        import site

        site_dir = Path(site.getsitepackages()[0])
    return site_dir / "_addwork_funcpatch.pth"


def start(enable_reminder: bool = False, enable_worklog: bool = True) -> None:
    now = datetime.now(ZoneInfo("Asia/Shanghai"))

    # 写入 .pth 启动钩子（插件自启动入口）；补丁包名为 plugins，
    # .pth 需把仓库根目录加入 sys.path
    pth = _pth_path()
    pth.write_text(
        f"{str(ROOT).replace(chr(92), '/')}\nimport plugins.bootstrap\n",
        encoding="utf-8",
    )
    print(f"[启动钩子] {pth}")

    env = os.environ.copy()
    if enable_reminder:
        # 调度时间设为当天当前时刻，使启动后立即命中并发送周报
        env.update(
            REMINDER_ENABLED="true",
            REMINDER_WEEKDAY=str(now.weekday()),
            REMINDER_HOUR=str(now.hour),
            REMINDER_MINUTE=str(now.minute),
        )
        print(f"[周报调度时间] 周{now.weekday() + 1} {now.hour:02d}:{now.minute:02d}（当天）")
    if enable_worklog:
        env["WORKLOG_PUSH_ENABLED"] = "true"
        print("[日志推送] 已启用")

    backend_log = ROOT / "logs" / "backend.log"
    frontend_log = ROOT / "logs" / "frontend.log"
    backend_log.parent.mkdir(exist_ok=True)
    blog = backend_log.open("w", encoding="utf-8")
    flog = frontend_log.open("w", encoding="utf-8")

    backend = subprocess.Popen(
        [PY, str(ROOT / "main.py")],
        cwd=ROOT,
        env=env,
        stdout=blog,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print(f"[后端] PID={backend.pid} 已启动 (端口 5000)，日志: {backend_log}")

    frontend = subprocess.Popen(
        [NPM, "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"],
        cwd=ROOT / "frontend",
        env=env,
        stdout=flog,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print(f"[前端] PID={frontend.pid} 已启动 (端口 5173)，日志: {frontend_log}")
    print()
    print("按 Ctrl+C 停止前后端")

    try:
        while backend.poll() is None and frontend.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for proc in (backend, frontend):
            if proc.poll() is None:
                proc.terminate()
        for proc in (backend, frontend):
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        blog.close()
        flog.close()
        # 保留启动钩子：插件安装是持久的，停止进程不应卸载插件。
        # 需要移除时执行 `python plugins/install.py --uninstall`。
        print("\n已停止前后端（启动钩子保留，可用 install.py --uninstall 卸载）")


def stop() -> None:
    _pth_path().unlink(missing_ok=True)
    print("已移除启动钩子；请根据 PID 或端口停止前后端进程")


def main() -> None:
    parser = argparse.ArgumentParser(description="启动工时系统的前后端及插件")
    parser.add_argument("--stop", action="store_true", help="移除启动钩子")
    parser.add_argument("--reminder", action="store_true", help="启用上周工时周报插件")
    parser.add_argument(
        "--no-worklog", action="store_true", help="不启用工时填报日志推送插件（默认启用）"
    )
    args = parser.parse_args()
    if args.stop:
        stop()
    else:
        start(enable_reminder=args.reminder, enable_worklog=not args.no_worklog)


if __name__ == "__main__":
    main()
