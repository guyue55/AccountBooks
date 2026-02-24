#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "🗄️  Checking database migrations..."
python manage.py migrate

echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if env vars are provided or use defaults (admin/admin123)
# We check if the user exists first to avoid errors on restart
echo "👤 Checking superuser..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('USERNAME', 'admin')
email = os.environ.get('EMAIL', 'admin@example.com')
password = os.environ.get('PASSWORD', 'admin123')

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser '{username}'...")
    User.objects.create_superuser(username, email, password)
    print(f"✅ Superuser '{username}' created.")
else:
    print(f"ℹ️  Superuser '{username}' already exists.")
EOF

echo "🔥 Starting Server..."
# Execute the passed command (e.g., gunicorn)
exec "$@"
