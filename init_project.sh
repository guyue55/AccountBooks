#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting AccountBooks initialization..."

# 1. Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed. Please install it first: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 2. Install dependencies
echo "📦 Installing dependencies..."
uv sync

# 3. Apply migrations
echo "🗄️  Applying database migrations..."
uv run python manage.py migrate

echo "🎨 Collecting static files..."
uv run python manage.py collectstatic --noinput

# 4. Create default superuser
echo "👤 Checking/Creating superuser (admin)..."
cat <<EOF > create_superuser_temp.py
import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AccountBooks.settings")
django.setup()

User = get_user_model()
USERNAME = "admin"
PASSWORD = "admin123"
EMAIL = "admin@example.com"

if not User.objects.filter(username=USERNAME).exists():
    print(f"Creating superuser '{USERNAME}'...")
    User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
    print(f"✅ Superuser '{USERNAME}' created successfully.")
else:
    print(f"ℹ️  Superuser '{USERNAME}' already exists. Skipping creation.")
EOF

uv run python create_superuser_temp.py
rm create_superuser_temp.py

# 5. Success message
echo ""
echo "🎉 Initialization complete! You are ready to go."
echo "==============================================="
echo "👉 Run the server:"
echo "   uv run python manage.py runserver"
echo ""
echo "👉 Login to Admin Panel:"
echo "   URL: http://127.0.0.1:8000/admin/"
echo "   User: admin"
echo "   Pass: admin123"
echo "==============================================="
