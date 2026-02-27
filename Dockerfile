# 使用官方Python镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /work
# 复制项目依赖文件
COPY requirements.txt .
# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
# 复制项目所有文件到工作目录
COPY app/  ./app
COPY frontend/build ./frontend/build
COPY main.py  .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENV TZ=Asia/Shanghai
# 暴露端口（与代码中配置的5000端口一致）
EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]