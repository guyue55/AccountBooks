#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting AccountBooks in PRODUCTION mode..."

# 1. Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed. Please install it first: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 2. Collect Static Files (Important for production!)
echo "🎨 Collecting static files..."
uv run python manage.py collectstatic --noinput

# 3. Start Gunicorn
# -w 4: 4 worker processes
# --threads 2: Each worker uses 2 threads (better concurrency)
# --timeout 120: Avoid aggressive kills during local dev lag
echo "🔥 Starting Gunicorn Server with Optimized Config..."
exec uv run gunicorn AccountBooks.wsgi:application \
    --workers 1 \
    --threads 8 \
    --timeout 120 \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
