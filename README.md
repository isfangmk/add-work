# 工时管理系统

一个基于 FastAPI 和 React 开发的工时管理工具，支持从工作平台获取工作项、批量添加/更新工时，并提供 LLM 智能总结功能。

## 技术栈

### 前端（`frontend/`）

2026 年现代前端方案，全量 TypeScript strict：

| 领域 | 选型 | 版本 |
|------|------|------|
| 构建工具 | Vite | 8.3 |
| 框架 | React | 19.3 |
| 语言 | TypeScript（strict、bundler 解析） | 5.9 |
| 样式 | Tailwind CSS v4（`@tailwindcss/vite` 插件，全部样式用工具类表达，无独立 CSS 文件） | 4.3 |
| 基础组件 | `src/components/ui/` 下的轻量组件（基于 Radix primitives + CVA），业务组件在其上用 Tailwind 组装 | — |
| 图标 | lucide-react | 1.x |
| 服务端状态 | TanStack Query v5（缓存/轮询/自动刷新） | 5.x |
| 客户端状态 | Zustand（persist middleware） | 5.x |
| 表单校验 | 组件内受控状态 + 显式校验（不引入额外表单库） | — |
| 日期 | date-fns | 4.x |
| 通知 | sonner | 2.x |
| 测试 | Vitest + @testing-library/react + user-event + jsdom | 5.x |

### 后端

| 领域 | 选型 |
|------|------|
| Web 框架 | FastAPI + Pydantic v2（Python 3.12） |
| 依赖管理 | uv（`uv.lock` 锁定）、ruff、basedpyright |
| HTTP 客户端 | httpx（AsyncClient） |
| 数据库 | SQLite |
| AI | OpenAI API（火山引擎 /doubao） |
| MCP | FastMCP（Streamable HTTP，与网页同进程） |
| 测试 | pytest（临时 DB fixture，禁止真实写入） |

## 本地部署

### 前置要求

- Python 3.12+
- Node.js 22+（Vite 8 要求；当前验证版本 v22.21.1）
- npm 10+

### 环境变量配置

在项目根目录创建 `.env` 文件，配置以下环境变量：

```env
# LLM 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
MODEL=doubao-seed-1-6-251015

# GitLab 配置
PRIVATE_TOKEN=your_gitlab_private_token_here
```

**必需环境变量说明**：

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥，用于 LLM 总结功能 | 是 |
| `OPENAI_BASE_URL` | OpenAI API 基础 URL，默认火山引擎 | 是 |
| `MODEL` | 使用的 LLM 模型名称 | 是 |
| `PRIVATE_TOKEN` | GitLab 私有令牌 | 是 |

### 后端部署

1. 安装 Python 依赖（推荐 uv，依赖由 `uv.lock` 锁定可复现）

```bash
uv sync
```

若不使用 uv，也可用 pip（依赖以 `pyproject.toml` 为准）：

```bash
pip install -r requirements.txt
```

2. 创建 `.env` 文件并配置环境变量（见上方）

3. 启动后端服务

```bash
uv run python main.py
```

服务将在 `http://127.0.0.1:5000` 启动

### 前端部署

1. 安装前端依赖

```bash
cd frontend
npm install
```

2. 开发模式运行

```bash
npm run dev
```

前端开发服务器将在 `http://localhost:5173/add-work/` 启动（Vite 8，base 为 `/add-work/`）

3. 生产构建

```bash
npm run build
```

构建产物将生成到 `frontend/build` 目录

## Docker 部署

### 构建镜像

```bash
docker build -t add-work .
```

### 运行容器

```bash
docker run -d \
  -p 5000:5000 \
  -e OPENAI_API_KEY=your_openai_api_key_here \
  -e OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 \
  -e MODEL=doubao-seed-1-6-251015 \
  -e PRIVATE_TOKEN=your_gitlab_private_token_here \
  --name add_work \
  add-work
```

### 停止容器

```bash
docker stop add_work
docker rm add_work
```

## 开发

后端用 [uv](https://docs.astral.sh/uv/) 管理依赖，前端用 npm；`Makefile` 提供统一入口。

```bash
make install        # 后端 uv sync + 前端 npm install
make lint           # 后端 ruff check + format --check + basedpyright，前端 tsc 类型检查
make format         # ruff format 格式化后端代码
make test           # 后端 pytest + 前端 tsc 类型检查
make typecheck      # 仅前端 tsc --noEmit
make build          # 前端 build + Docker 镜像构建
```

等价的原生命令：

| 用途 | 命令 |
|------|------|
| 安装后端依赖 | `uv sync` |
| 后端静态检查 | `uv run ruff check . && uv run ruff format --check .` |
| 后端类型检查 | `uv run basedpyright` |
| 后端格式化 | `uv run ruff format .` |
| 后端测试 | `uv run pytest -q` |
| 前端类型检查 | `cd frontend && npm run typecheck` |
| 前端测试 | `cd frontend && npm run test`（Vitest，不调用真实 API） |
| 前端测试（监听模式） | `cd frontend && npm run test:watch` |
| 前端构建 | `cd frontend && npm run build` |

测试安全：pytest 会自动把数据库指向临时文件（`tests/conftest.py`），并通过兜底 fixture 禁止真实写入工时（`gitee.clone_item` / `gitee.update_item`）；搜索等只读查询不受影响。

## 功能特性

- 📋 获取工作项列表和迭代列表
- ⏱️ 批量添加/更新工时记录
- 🔐 Cookie 自动保活机制
- 🤖 LLM 智能总结 Git 提交记录（需配置 OpenAI）
- 📊 实时任务状态监控
- 🎨 现代化的 React 前端界面
- 🐳 支持 Docker 容器化部署
- 🔌 MCP Server（FastMCP），可供 Cursor 等客户端调用工时能力

### 关于直接提交任务缺少“去项目空间查看结果”链接

`app/services/work.py` 的任务完成日志中，只有满足 `gitee.workspace_iql_cache` 有缓存
且工作空间解析出 `jump_url` 时，才会输出“😎 去项目空间查看结果吧”。该缓存此前只在
日历工时查询（`gitee.search_work_items`）时写入，因此通过 API / MCP / 页面直接提交任务、
没有先打开日历页时，链接不会生成。

此问题由 funcpatch 补丁修复（不改主分支源码）：`plugins/addwork_patches/jump_url_fix.py`
以 wrap 方式挂接 `run_work_task`，在任务执行前按 `username + workspace_names` 预热 IQL 缓存，
使主分支原有 `jump_url` 逻辑照常工作。详见 `plugins/README.md`。

## 项目结构

```
add-work/
├── app/
│   ├── api/            # HTTP 路由
│   ├── clients/        # 外部系统客户端（Gitee / GitLab / LLM）
│   ├── core/           # 配置、日志、异常、HTTP 客户端
│   ├── mcp/            # FastMCP 工具
│   ├── schemas/        # 请求/响应模型
│   ├── services/       # 业务编排与 Cookie 保活
│   └── storage/        # SQLite 与任务状态
├── frontend/
├── plugins/             # funcpatch 补丁集（周报 / 日志推送 / 跳转链接修复）
├── tests/              # pytest 单元测试
├── main.py
├── start_all.py        # 一键启动前后端（并装载补丁）
├── Dockerfile
├── entrypoint.sh
├── pyproject.toml      # 后端依赖 + ruff/pytest 配置
├── uv.lock             # 依赖锁定文件
├── Makefile            # 统一命令入口
└── requirements.txt    # pip 兼容用（权威依赖见 pyproject.toml）
```

## 端口说明

- 后端服务端口: `5000`
- 前端开发端口: `3000`
- MCP（Streamable HTTP）: `http://127.0.0.1:5000/add-work/mcp`

## MCP

与网页共用同一进程。连接用自定义 Header `X-MCP-Token`（与环境变量 `MCP_TOKEN` 一致）。

先调用 `whoami(real_name)`（企业微信中文名）。没有登录记录时引导用户打开 https://gitee.ibr.net.cn/ ，把 PRE-GW-SESSION 通过 `whoami` 的 `cookie` 再提交一次。成功后其他工具的 `account` 使用返回的 Gitee 用户名。

企业微信插件请求头示例：Key `X-MCP-Token`，Value 为 `MCP_TOKEN`。也可使用授权方式 Service token（Header 里的 Bearer）。

标准用法：`whoami` → `get_calendar` 拿 `recommended_source` → 可选 `list_workspaces` / `list_sprints` / `suggest_titles` → `create_from_source`（默认源事项工作空间，可用 `workspace_names` 按事项指定）；改已有事项用 `update_item`。

## 许可证

MIT
