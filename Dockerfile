# 单阶段构建：pip 安装依赖后拷入源码
FROM python:3.12-slim
WORKDIR /work

# 阿里云 pip 源，加速构建
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_INDEX_URL=${PIP_INDEX_URL} \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai

# 先装依赖，利用镜像层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
