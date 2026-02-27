#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting AccountBooks in PRODUCTION mode..."

# 1. Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed. Please install it first: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 2. Apply Database Migrations
echo "🗄️ Applying database migrations..."
uv run python manage.py migrate --noinput

# 3. Collect Static Files (Important for production!)
echo "🎨 Collecting static files..."
uv run python manage.py collectstatic --noinput

# 4. Start Gunicorn
# -w 1: 1 个工作进程，提供基础的高可用和负载均衡
# --threads 8: 每个进程 8 条线程，足以应对 50 人规模的并发 I/O
# --timeout 120: 避免由于 SQLite 锁等待等导致的进程强杀
echo "🔥 Starting Gunicorn Server with Optimized Config (Debug: OFF)..."
# 强制设置生产环境变量
export DJANGO_DEBUG=False

exec uv run gunicorn AccountBooks.wsgi:application \
    --workers 1 \
    --threads 8 \
    --timeout 120 \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
