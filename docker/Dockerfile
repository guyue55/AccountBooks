# Stage 1: 构建阶段 (Builder)
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# 设置环境变量，防止生成 .pyc 并禁用 pip 缓存（由 Docker 缓存层管理）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# # 安装构建依赖 (如果后续有处理图片的库如 Pillow, 可以在这里加 libjpeg-dev 等)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装依赖
COPY requirements.txt .
# 构建时默认不指定国内源，由构建逻辑自行处理，或保持灵活
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: 运行阶段 (Runner)
FROM python:3.12-alpine AS runner

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=AccountBooks.settings \
    DJANGO_DEBUG=False

# 从 builder 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制项目代码 (利用 .dockerignore 排除不必要文件)
COPY . .

# 修正入口脚本权限
RUN chmod +x /app/docker/docker-entrypoint.sh

# 预收集静态文件（WhiteNoise 需要）
RUN python manage.py collectstatic --noinput

# 暴露端口
EXPOSE 8000

# 默认使用 docker 目录下的入口脚本
ENTRYPOINT ["/app/docker/docker-entrypoint.sh"]

# 启动命令 (使用更精确的参数配置)
CMD ["gunicorn", "AccountBooks.wsgi:application", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "2", \
    "--threads", "8", \
    "--timeout", "120", \
    "--access-logfile", "-", \
    "--error-logfile", "-"]
