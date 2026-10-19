"""工时工具 MCP Server（FastMCP）。"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Annotated, Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext
from pydantic import Field

load_dotenv()

from app.clients import gitee  # noqa: E402
from app.clients.llm import summarize_commits as llm_summarize_commits  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import get_cookie_record, get_cookie_record_by_real_name, get_workspace_configs, update_cookie_real_name  # noqa: E402
from app.logger import get_logger  # noqa: E402
from app.services import load_calendar_items, resolve_current_user, run_work_task  # noqa: E402
from app.task_store import copy_logs, get_task, init_task, new_task_id  # noqa: E402

logger = get_logger(__name__)
_TZ = ZoneInfo("Asia/Shanghai")

_ACCOUNT_DESC = (
    "Gitee 用户名，如 fangmingkun。由 whoami 返回，禁止编造或使用他人账号"
)
_GITEE_LOGIN_URL = "https://gitee.ibr.net.cn/"

mcp = FastMCP(
    name="add-work",
    instructions=(
        "添加工时工具。"
        "连接 Header 使用 X-MCP-Token 认证。"
        "企业微信会注入用户中文名。先调用 whoami(real_name=中文名)。"
        "若尚未登录：引导用户打开 https://gitee.ibr.net.cn/ 登录，"
        "把 PRE-GW-SESSION Cookie 再通过 whoami 的 cookie 参数提交"
        "（值类似 17eca8db2ef64b54a9f1b753919fb1d6）。"
        "whoami 成功后得到 Gitee 用户名，后续 get_calendar / list_workspaces / "
        "list_sprints / suggest_titles / create_from_source / update_item 的 account "
        "使用该 Gitee 用户名。禁止编造账号。"
        "流程：whoami → get_calendar 看周历并使用 recommended_source；"
        "需要换工作空间时 list_workspaces，默认用源事项的 workspace_name；"
        "换空间或改迭代时 list_sprints；可选 suggest_titles；"
        "create_from_source 克隆源事项写入新工时（可按事项指定不同工作空间）；"
        "改已有事项用 update_item。"
        "用户粘贴企业微信「智能总结」生成的每日工作事项时："
        "提炼成工时事项名称，精简、客观，一般不超过 50 个字，不要整段粘贴原文。"
        "不要自己编造 object_id，必须从日历拷贝。"
    ),
)


class McpToolLogMiddleware(Middleware):
    async def on_list_tools(self, context: MiddlewareContext, call_next):
        logger.info("MCP list_tools")
        return await call_next(context)

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        name = getattr(context.message, "name", "") or ""
        args = getattr(context.message, "arguments", None) or {}
        account = ""
        if isinstance(args, dict):
            account = str(args.get("account") or args.get("real_name") or "")
            args = dict(args)
            if args.get("cookie"):
                args["cookie"] = "***"
        try:
            payload = json.dumps(args, ensure_ascii=False, default=str)
        except TypeError:
            payload = str(args)
        if len(payload) > 2000:
            payload = payload[:2000] + "..."
        logger.info("MCP tool start name=%s account=%s args=%s", name, account, payload)
        started = time.perf_counter()
        try:
            result = await call_next(context)
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.info(
                "MCP tool done name=%s account=%s elapsed_ms=%.0f",
                name,
                account,
                elapsed_ms,
            )
            return result
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.error(
                "MCP tool fail name=%s account=%s elapsed_ms=%.0f err=%s",
                name,
                account,
                elapsed_ms,
                exc,
            )
            raise


def _ok(data: Any = None, msg: str = "操作成功") -> Dict[str, Any]:
    return {"success": True, "msg": msg, "data": data}


def _fail(msg: str) -> Dict[str, Any]:
    return {"success": False, "msg": msg, "data": None}


def mcp_token_from_headers(headers: Dict[str, str]) -> str:
    """从连接 Header 取出 MCP Token（X-MCP-Token 或 Authorization: Bearer）。"""
    lowered = {str(k).lower(): str(v).strip() for k, v in headers.items()}
    token = lowered.get("x-mcp-token") or ""
    auth = lowered.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    return token


def _gitee_cookie_guide(reason: str) -> str:
    return (
        f"{reason}请先打开 {_GITEE_LOGIN_URL} 登录，"
        "然后将 PRE-GW-SESSION 的 Cookie 值再调用 whoami。"
        "Cookie 值类似 17eca8db2ef64b54a9f1b753919fb1d6"
        "（参数 real_name 为中文名，cookie 为该值）。"
    )


async def _require_user(account: str) -> Tuple[Optional[Dict[str, Any]], str, str, str]:
    name = (account or "").strip()
    if not name:
        return (
            _fail("缺少 account：请先调用 whoami 获取 Gitee 用户名"),
            "",
            "",
            "",
        )
    record = get_cookie_record(name)
    if not record:
        return (
            _fail(_gitee_cookie_guide(f"未找到账号 {name} 的登录记录，")),
            "",
            "",
            "",
        )
    cookie = record[1]
    username, git_email, _real_name = await resolve_current_user(cookie)
    if not username:
        return (
            _fail(_gitee_cookie_guide("登录已过期，")),
            "",
            "",
            "",
        )
    return None, cookie, username, git_email or ""


def _week_range(offset: int = 0) -> Tuple[date, date, str]:
    today = datetime.now(_TZ).date()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    sunday = monday + timedelta(days=6)
    if offset == 0:
        label = "本周"
    elif offset < 0:
        label = f"{abs(offset)}周前"
    else:
        label = f"{offset}周后"
    return monday, sunday, label


def _group_days(results: List[Any]) -> Dict[str, list]:
    week_items: Dict[str, list] = defaultdict(list)
    for batch in results:
        if not batch:
            continue
        for item in batch:
            week_items[item["date"]].append(item)
    return dict(week_items)


def _pick_source(days: Dict[str, list]) -> Optional[Dict[str, Any]]:
    dates = sorted(day for day, items in days.items() if items)
    if not dates:
        return None
    item = days[dates[-1]][-1]
    return {
        "object_id": item["object_id"],
        "name": item.get("name"),
        "workspace_name": item.get("workspace_name"),
        "sprint_id": item.get("sprint_id"),
        "sprint": item.get("sprint"),
        "time": item.get("time"),
        "date": item.get("date"),
    }


async def _run_task(
    username: str,
    cookie: str,
    object_id: str,
    workspace_names: List[str],
    names: List[str],
    sprint_ids: List[str],
    times: List[float],
    dates: List[str],
    *,
    is_update: bool,
) -> Dict[str, Any]:
    task_id = new_task_id()
    init_task(task_id)
    await run_work_task(
        username,
        settings.build_headers(cookie),
        object_id,
        names,
        sprint_ids,
        times,
        dates,
        workspace_names,
        task_id,
        is_update=is_update,
    )
    task = get_task(task_id) or {}
    return _ok(
        {
            "taskId": task_id,
            "success": task.get("success"),
            "log": copy_logs(task_id),
        },
        msg="任务执行完成" if task.get("success") else "任务结束，存在失败（见 log）",
    )


@mcp.tool
async def whoami(
    real_name: Annotated[str, Field(description="企业微信注入的中文姓名")],
    cookie: Annotated[
        Optional[str],
        Field(
            description=(
                "可选。Gitee 的 PRE-GW-SESSION Cookie 值，"
                "类似 17eca8db2ef64b54a9f1b753919fb1d6"
            )
        ),
    ] = None,
) -> Dict[str, Any]:
    """用中文名识别用户。无登录记录时引导去 Gitee 登录并提交 Cookie，校验成功后保活并返回 Gitee 用户名、中文名、邮箱。"""
    cn = (real_name or "").strip()
    if not cn:
        return _fail("缺少中文姓名")

    raw_cookie = (cookie or "").strip()
    if raw_cookie:
        username, git_email, card = await resolve_current_user(raw_cookie)
        if not username:
            return _fail(_gitee_cookie_guide("Cookie 无效或已过期，"))
        bound_name = cn or card
        update_cookie_real_name(username, bound_name)
        return _ok(
            {
                "username": username,
                "real_name": bound_name,
                "gitEmail": git_email or "",
            }
        )

    record = get_cookie_record_by_real_name(cn)
    if not record:
        return _fail(_gitee_cookie_guide(f"未找到中文名 {cn} 的登录记录，"))
    stored_user, stored_cookie = record
    username, git_email, card = await resolve_current_user(stored_cookie)
    if not username:
        return _fail(_gitee_cookie_guide("登录已过期，"))
    update_cookie_real_name(username, cn)
    return _ok(
        {
            "username": username or stored_user,
            "real_name": cn or card,
            "gitEmail": git_email or "",
        }
    )


@mcp.tool
async def get_calendar(
    account: Annotated[str, Field(description=_ACCOUNT_DESC)],
    week_offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """查看工时周历。week_offset=0 为本周，-1 为上周。返回 days 与 recommended_source。"""
    err, cookie, username, git_email = await _require_user(account)
    if err:
        return err

    if start_date and end_date:
        start, end, label = start_date, end_date, f"{start_date} ~ {end_date}"
    else:
        monday, sunday, label = _week_range(week_offset)
        start, end = monday.isoformat(), sunday.isoformat()

    results, name, _email = await load_calendar_items(
        settings.build_headers(cookie),
        start,
        end,
        username,
        git_email,
    )
    if results is None or name is None:
        return _fail(_gitee_cookie_guide("登录已过期，"))

    days = _group_days(results)
    return _ok(
        {
            "user": {"username": username, "gitEmail": git_email},
            "week": {"start": start, "end": end, "label": label},
            "days": days,
            "recommended_source": _pick_source(days),
        }
    )


@mcp.tool
async def list_workspaces() -> Dict[str, Any]:
    """列出可选工作空间名称（与网页下拉一致）。create_from_source 默认用源事项空间，换空间时从本列表选。"""
    configs = get_workspace_configs()
    data = [
        {
            "workspace_name": name,
            "workspace_id": cfg["workspace_id"],
            "workspace_key": cfg["workspace_key"],
        }
        for name, cfg in configs.items()
    ]
    return _ok(data)


@mcp.tool
async def list_sprints(
    account: Annotated[str, Field(description=_ACCOUNT_DESC)],
    workspace_name: Annotated[
        str,
        Field(
            description=(
                "工作空间名称。默认用源事项的 workspace_name；"
                "换空间时从 list_workspaces 或日历事项拷贝"
            )
        ),
    ],
) -> Dict[str, Any]:
    """列出指定工作空间的未完成迭代。"""
    workspace = get_workspace_configs().get(workspace_name)
    if not workspace:
        return _fail(f"工作空间 '{workspace_name}' 不存在")
    err, cookie, _user, _email = await _require_user(account)
    if err:
        return err
    sprints = await gitee.list_sprints(
        settings.build_headers(cookie),
        workspace["workspace_key"],
        workspace["workspace_id"],
    )
    if sprints is None:
        return _fail(_gitee_cookie_guide("获取迭代列表失败，"))
    return _ok(sprints)


@mcp.tool
async def suggest_titles(
    account: Annotated[str, Field(description=_ACCOUNT_DESC)],
    start_date: str,
    end_date: str,
    exclude_dates: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """按当前账号 Git 提交生成每日事项名称（日期 -> 文本）。不写 Gitee。"""
    err, _cookie, _user, git_email = await _require_user(account)
    if err:
        return err
    if not git_email:
        return _fail("当前用户没有 gitEmail，无法拉取提交")
    raw = await llm_summarize_commits(
        git_email, start_date, end_date, exclude_dates or []
    )
    if not raw:
        return _ok({}, msg="该区间没有可用提交或 LLM 未配置")
    try:
        summary = json.loads(raw)
    except json.JSONDecodeError:
        return _fail("LLM 返回的 JSON 无效")
    cleaned = {
        k: (v[0] if isinstance(v, list) and v else str(v))
        for k, v in summary.items()
    }
    return _ok(cleaned)


@mcp.tool
async def create_from_source(
    account: Annotated[str, Field(description=_ACCOUNT_DESC)],
    source_object_id: Annotated[
        str,
        Field(description="源事项 ID。从 get_calendar 的 recommended_source.object_id 或 days 里某条 object_id 拷贝"),
    ],
    workspace_name: Annotated[
        str,
        Field(
            description=(
                "默认工作空间。通常从 recommended_source.workspace_name 拷贝；"
                "也可从 list_workspaces 选择。各事项未单独指定时都用此值"
            )
        ),
    ],
    names: Annotated[
        List[str],
        Field(
            description=(
                '待创建的事项名称列表，例如 ["接口联调", "修缺陷"]。'
                "由智能总结改写时须精简，一般不超过 50 个字，不要整段粘贴原文"
            )
        ),
    ],
    hours: Annotated[
        List[float],
        Field(description="各事项工时（小时），与 names 一一对应，均须大于 0"),
    ],
    dates: Annotated[
        List[str],
        Field(description="各事项日期 YYYY-MM-DD，与 names 一一对应"),
    ],
    sprint_ids: Annotated[
        List[str],
        Field(description="各事项迭代 ID，与 names 一一对应。从 recommended_source.sprint_id 或 list_sprints 拷贝"),
    ],
    workspace_names: Annotated[
        Optional[List[str]],
        Field(
            description=(
                "可选。各事项工作空间，与 names 一一对应。"
                "不传则全部使用 workspace_name；换空间时从 list_workspaces 拷贝"
            )
        ),
    ] = None,
) -> Dict[str, Any]:
    """克隆源事项并创建新工时。names、hours、dates、sprint_ids 长度必须相同；可选按事项指定工作空间。"""
    if not names or not hours or not dates or not sprint_ids:
        return _fail("names、hours、dates、sprint_ids 不能为空")
    lengths = {len(names), len(hours), len(dates), len(sprint_ids)}
    if workspace_names is not None:
        lengths.add(len(workspace_names))
    if len(lengths) != 1:
        return _fail("names、hours、dates、sprint_ids（及 workspace_names）长度必须相同")
    if any(h <= 0 for h in hours):
        return _fail("工时须为大于 0 的数字")

    default_ws = (workspace_name or "").strip()
    resolved_workspaces = [
        (w or "").strip() or default_ws
        for w in (workspace_names if workspace_names is not None else [default_ws] * len(names))
    ]
    configs = get_workspace_configs()
    for ws in resolved_workspaces:
        if not ws:
            return _fail("缺少工作空间：请传 workspace_name 或 workspace_names")
        if ws not in configs:
            return _fail(f"工作空间 '{ws}' 不存在，请先调用 list_workspaces")

    clean_names = [n.strip() for n in names]
    clean_dates = [d.strip() for d in dates]
    resolved_sprints = [sid.strip() for sid in sprint_ids]
    if not all(clean_names) or not all(clean_dates):
        return _fail("每条事项都需要 name 和 date")
    if not all(resolved_sprints):
        return _fail("每条事项都需要 sprint_ids 中的迭代 ID")

    err, cookie, username, _email = await _require_user(account)
    if err:
        return err
    return await _run_task(
        username,
        cookie,
        source_object_id.strip(),
        resolved_workspaces,
        clean_names,
        resolved_sprints,
        [float(h) for h in hours],
        clean_dates,
        is_update=False,
    )


@mcp.tool
async def update_item(
    account: Annotated[str, Field(description=_ACCOUNT_DESC)],
    object_id: Annotated[str, Field(description="要更新的事项 ID，从 get_calendar 的 days 里拷贝")],
    workspace_name: Annotated[
        str,
        Field(description="该事项所在空间，从 days 里拷贝；一般不要改到其他空间"),
    ],
    name: Annotated[str, Field(description="事项名称。精简，一般不超过 50 个字")],
    hours: Annotated[float, Field(description="工时（小时），须大于 0")],
    date: Annotated[str, Field(description="日期 YYYY-MM-DD")],
    sprint_id: Annotated[str, Field(description="迭代 ID")],
) -> Dict[str, Any]:
    """更新已有工时事项，不克隆。"""
    ws = (workspace_name or "").strip()
    if ws not in get_workspace_configs():
        return _fail(f"工作空间 '{ws}' 不存在，请先调用 list_workspaces")
    if hours <= 0:
        return _fail("工时须为大于 0 的数字")
    if not (object_id and name.strip() and date.strip()):
        return _fail("object_id、name、date 不能为空")
    if not (sprint_id or "").strip():
        return _fail("缺少 sprint_id")

    err, cookie, username, _email = await _require_user(account)
    if err:
        return err
    return await _run_task(
        username,
        cookie,
        object_id,
        [ws],
        [name.strip()],
        [sprint_id.strip()],
        [float(hours)],
        [date.strip()],
        is_update=True,
    )


mcp.add_middleware(McpToolLogMiddleware())
mcp_http_app = mcp.http_app(path="/")


if __name__ == "__main__":
    from app.db import init_db

    init_db()
    mcp.run()
