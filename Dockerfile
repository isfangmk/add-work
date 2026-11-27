# ---------- 构建阶段：用 uv 安装依赖 ----------
FROM ghcr.io/astral-sh/uv:python3.12-slim AS builder
WORKDIR /work
# 国内 pip 源，加速构建（阿里云源当前不可达，用清华源）
ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
COPY pyproject.toml uv.lock ./
# 只装依赖，不安装项目本身（源码在下面直接 COPY，无需可编辑安装）
RUN uv sync --frozen --no-dev --no-install-project

# ---------- 运行阶段：只保留虚拟环境与源码 ----------
FROM python:3.12-slim
WORKDIR /work
COPY --from=builder /work/.venv /work/.venv
# 让 entrypoint.sh 里的 python 指向虚拟环境
ENV PATH="/work/.venv/bin:$PATH"
ENV TZ=Asia/Shanghai

COPY app/  ./app
COPY frontend/build ./frontend/build
COPY main.py  .
COPY entrypoint.sh .
# funcpatch 补丁集：经 .pth 启动钩子在解释器启动时注册
COPY plugins/ ./plugins
RUN chmod +x entrypoint.sh

# 写入补丁启动钩子：把 /work 加入 sys.path，导入 plugins.bootstrap 即完成注册。
# 业务开关（REMINDER_ENABLED / WORKLOG_PUSH_ENABLED）由容器环境变量提供。
RUN printf '/work\nimport plugins.bootstrap\n' \
    > "$(python -c 'import site; print(site.getsitepackages()[0])')/_addwork_funcpatch.pth"

# 暴露端口（与代码中配置的5000端口一致）
EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
