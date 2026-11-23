# ---------- 构建阶段：用 uv 安装依赖 ----------
FROM ghcr.io/astral-sh/uv:python3.12-slim AS builder
WORKDIR /work
# 阿里云 pip 源，加速国内构建
ENV UV_INDEX_URL=https://pypi.aliyun.com/simple
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
RUN chmod +x entrypoint.sh

# 暴露端口（与代码中配置的5000端口一致）
EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
