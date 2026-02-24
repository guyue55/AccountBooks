# Stage 1: 构建阶段 (Builder)
# 使用官方 Python 3.12 精简版作为基础镜像
FROM python:3.12-slim-bookworm AS builder

# 如果遇到 403 Forbidden，可以尝试更换镜像源，或者检查 Docker Hub 网络连接
# 或者尝试使用: FROM public.ecr.aws/docker/library/python:3.12-slim-bookworm

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 创建虚拟环境
RUN python -m venv /opt/venv
# 将虚拟环境加入 PATH
ENV PATH="/opt/venv/bin:$PATH"

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
# --no-cache-dir: 减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Stage 2: 运行阶段 (Runner)
FROM python:3.12-alpine AS runner

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# 安装运行时必需的系统库，并立即清理缓存以减小体积
# # 这一步合并了 install 和 clean，避免 apt 缓存被提交到镜像层
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制构建好的虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制项目代码 (利用 .dockerignore 排除不必要文件)
COPY . .

# 复制并设置入口脚本
COPY docker/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 暴露端口
EXPOSE 8000

# 设置入口点
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# 启动命令
CMD ["gunicorn", "AccountBooks.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-"]
