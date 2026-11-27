# add-work 补丁集（funcpatch 实现）

三个独立业务补丁，通过 [funcpatch](../../funcpatch/) 以 `PatchSpec` 方式挂接到主分支函数。
**主分支 `app/` 与 `main.py` 一行不改**；补丁在解释器启动时经 `.pth` 延迟注册，
目标模块首次导入时由 funcpatch 应用。

| 补丁 | owner | patch 目标 | 业务动作 |
|---|---|---|---|
| `weekly_reminder` | `addwork` | `app.storage.db:init_db`（wrap） | 应用启动时按 `REMINDER_ENABLED` 拉起周报调度：每周检查上周工时（排除周末+节假日），发企业微信明细周报。 |
| `worklog_pusher` | `addwork` | `app.storage.task_store:finish_task`（wrap） | 页面/MCP 任务完成写入状态时，把该任务执行日志推送企业微信。事件驱动，无轮询。 |
| `jump_url_fix` | `addwork` | `app.services.work:run_work_task`（async wrap） | 任务执行前预热 IQL 缓存，修复直接提交任务时“去项目空间查看结果”链接不生成。 |

三个补丁互不依赖：企业微信发送在公共层 `plugins/_infra/wecom.py`，各自独立调用；
禁用任一补丁不影响另一个。每个目标只有一个 owner 生效，由 funcpatch 进程级占用表保证。

---

## 安装 / 加载

```bash
# 安装：写入 .pth 启动钩子（不碰任何源码）；funcpatch 缺失时自动安装
.venv/Scripts/python.exe plugins/install.py

# 启用业务动作（不设置即不动作，零副作用）
export REMINDER_ENABLED=true        # 上周工时周报
export WORKLOG_PUSH_ENABLED=true    # 工时填报日志推送

# 正常启动主程序（启动命令不变）
python main.py

# 或用一体化脚本（自动设置当天调度时间便于立即触发周报）
python start_all.py --reminder

# 卸载：移除 .pth
.venv/Scripts/python.exe plugins/install.py --uninstall
```

三层开关，互不干扰：

| 开关 | 作用 |
|---|---|
| 未执行 `install.py` | 补丁完全不存在，零影响 |
| `FUNC_PATCH_ENABLED=false` | funcpatch 全局关闭，所有补丁不应用（走主分支原实现） |
| `funcpatch.toml` / `FUNC_PATCH_OWNER` | 选择哪个 owner 的补丁生效（单目标单 owner） |
| `REMINDER_ENABLED` / `WORKLOG_PUSH_ENABLED` | 补丁已应用，但业务动作是否实际执行 |

---

## 配置项（环境变量）

### 周报 `weekly_reminder`

| 变量 | 默认 | 说明 |
|---|---|---|
| `REMINDER_ENABLED` | `false` | 是否执行周报检查 |
| `REMINDER_WEEKDAY` | `0` | 检查星期（0=周一） |
| `REMINDER_HOUR` / `REMINDER_MINUTE` | `10` / `0` | 检查时间（Asia/Shanghai） |
| `REMINDER_WEBHOOK_URL` | 空（不推送） | 通知地址 |
| `REMINDER_CHECK_INTERVAL` | `60` | 调度轮询间隔（秒） |
| `REMINDER_MIN_HOURS` | `0` | 当天工时 > 该值才算填过 |
| `DB_PATH` | `tasks.db` | 读取 cookie_records |
| `ADDWORK_BASE_URL` | `https://gitee.ibr.net.cn` | Gitee base url |
| `ADDWORK_PARSE_APP_ID` | `Bonree` | parse application id |

节假日：可选依赖 `chinese_calendar`；未安装时用 `weekly_reminder/cal.py` 内置 2025/2026 节假日表兜底。

### 日志推送 `worklog_pusher`

| 变量 | 默认 | 说明 |
|---|---|---|
| `WORKLOG_PUSH_ENABLED` | `false` | 是否执行推送 |
| `WORKLOG_PUSH_WEBHOOK_URL` | 空（不推送） | 推送地址（可与周报不同） |

数据源：`app.storage.task_store.TASK_STATUS`。任务完成（`finish_task`）时按 `task_id` 幂等去重推送；先标记已处理再发送，失败不重试。

---

## 为什么是 two PatchSpec 而不是轮询

- `finish_task` 是任务完成的唯一信号点（主分支 `run_work_task` 在 `finally` 中调用它），
  wrap 补丁在该点同步读取日志并推送，比每 3 秒轮询 `TASK_STATUS` 更及时、无延迟、无空转。
- `init_db` 在主程序 lifespan 启动时被调用且已有运行中的事件循环，
  wrap 补丁在此刻把周报调度协程挂到主循环，无需主分支加任何"插座"调用。
- 两者均用 `mode="wrap"`，先调用原函数再执行补丁逻辑，主分支行为完全保留。

---

## 文件结构

```
plugins/
├── README.md                      本说明
├── install.py                     安装/卸载 .pth 启动钩子
├── __init__.py                    SPECS = 全部补丁声明
├── bootstrap.py                   .pth 引导：funcpatch bootstrap / shutdown
├── _infra/wecom.py                企业微信发送（公共基础设施）
├── worklog_pusher/                finish_task wrap 补丁 + 异步推送逻辑
│   └── __init__.py
├── jump_url_fix/                  run_work_task async wrap 补丁 + IQL 缓存预热
│   └── __init__.py
└── weekly_reminder/               init_db wrap 补丁 + 周报调度
    ├── __init__.py
    ├── config.py                  环境变量配置
    ├── cal.py                     工作日/节假日计算
    ├── builtin.py                 周报业务逻辑（查询/汇总/消息）
    └── runner.py                  调度与幂等
```

补丁的业务开关与配置见项目根目录 `.env.example`。
