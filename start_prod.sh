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
# -w 4: 4 worker processes (adjust based on CPU cores, 2-4 x cores recommended)
# -b 0.0.0.0:8000: Bind to all interfaces on port 8000
# --access-logfile -: Log access to stdout
# --error-logfile -: Log errors to stdout
echo "🔥 Starting Gunicorn Server..."
exec uv run gunicorn AccountBooks.wsgi:application \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
