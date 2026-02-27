# 使用最精简的官方 Python Alpine 镜像
FROM python:3.12-alpine

# 设置工作目录
WORKDIR /app

# 设置生产环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=AccountBooks.settings \
    DJANGO_DEBUG=False

# 1. 复制依赖描述文件
COPY requirements.txt .

# 2. 合并安装与清理操作（减少镜像层）
# --no-cache-dir: 防止 pip 缓存下载的包，直接解压安装
RUN pip install --no-cache-dir -r requirements.txt

# 3. 复制项目代码 (利用 .dockerignore 排除不必要的文件)
COPY . .

# 4. 初始化权限与静态资源
# 我们在构建时就完成 collectstatic，这样镜像启动后直接就是完整状态
RUN chmod +x /app/docker/docker-entrypoint.sh

# 5. 暴露端口
EXPOSE 8000

# 6. 设置入口
ENTRYPOINT ["/app/docker/docker-entrypoint.sh"]

# 7. 启动 Gunicorn
CMD ["gunicorn", "AccountBooks.wsgi:application", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "2", \
    "--threads", "8", \
    "--timeout", "120", \
    "--access-logfile", "-", \
    "--error-logfile", "-"]
