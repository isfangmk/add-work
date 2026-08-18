# 工时管理系统

一个基于 FastAPI 和 React 开发的工时管理工具，支持从工作平台获取工作项、批量添加/更新工时，并提供 LLM 智能总结功能。

## 技术栈

- **后端**: FastAPI + Python 3.12
- **前端**: React 18 + Tailwind CSS
- **数据库**: SQLite
- **HTTP 客户端**: httpx
- **AI**: OpenAI API

## 本地部署

### 前置要求

- Python 3.12+
- Node.js 18+
- npm/yarn

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

1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

2. 创建 `.env` 文件并配置环境变量（见上方）

3. 启动后端服务

```bash
python main.py
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
npm start
```

前端开发服务器将在 `http://localhost:3000` 启动

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

## 功能特性

- 📋 获取工作项列表和迭代列表
- ⏱️ 批量添加/更新工时记录
- 🔐 Cookie 自动保活机制
- 🤖 LLM 智能总结 Git 提交记录（需配置 OpenAI）
- 📊 实时任务状态监控
- 🎨 现代化的 React 前端界面
- 🐳 支持 Docker 容器化部署
- 🔌 MCP Server（FastMCP），可供 Cursor 等客户端调用工时能力

## 项目结构

```
add-work/
├── app/                 # 后端应用目录
│   ├── config.py       # 配置文件
│   ├── db.py           # 数据库操作
│   ├── mcp.py          # FastMCP 工具
│   ├── api/            # HTTP API
│   ├── services.py     # 业务逻辑
│   └── ...
├── frontend/           # 前端应用
│   ├── src/           # 源代码
│   ├── build/         # 构建产物
│   └── package.json
├── main.py            # 应用入口
├── Dockerfile         # Docker 配置
├── entrypoint.sh      # 容器启动脚本
└── requirements.txt   # Python 依赖
```

## 端口说明

- 后端服务端口: `5000`
- 前端开发端口: `3000`
- MCP（Streamable HTTP）: `http://127.0.0.1:5000/add-work/mcp`

## MCP

与网页共用同一进程。连接用自定义 Header `X-MCP-Token`（与环境变量 `MCP_TOKEN` 一致）。

先调用 `whoami(real_name)`（企业微信中文名）。没有登录记录时引导用户打开 https://gitee.ibr.net.cn/ ，把 PRE-GW-SESSION 通过 `whoami` 的 `cookie` 再提交一次。成功后其他工具的 `account` 使用返回的 Gitee 用户名。

企业微信插件请求头示例：Key `X-MCP-Token`，Value 为 `MCP_TOKEN`。也可使用授权方式 Service token（Header 里的 Bearer）。

标准用法：`whoami` → `get_calendar` 拿 `recommended_source` → 可选 `list_sprints` / `suggest_titles` → `create_from_source`；改已有事项用 `update_item`。

## 许可证

MIT
