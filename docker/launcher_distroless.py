import os
import sys

import django
from django.core.management import call_command
from gunicorn.app.wsgiapp import run

# 1. 配置 Django 环境
# 确保项目根目录在 Python 路径中
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AccountBooks.settings")

try:
    django.setup()

    # 2. 执行数据库迁移 (相当于 python manage.py migrate)
    print("🗄️  Checking and applying database migrations...")
    call_command("makemigrations", "accounts", interactive=False)
    call_command("migrate", interactive=False)

    # 3. 延迟导入用户模型，防止在 django.setup() 之前调用
    from django.contrib.auth import get_user_model

    User = get_user_model()
    username = os.environ.get("USERNAME", "admin")
    email = os.environ.get("EMAIL", "admin@example.com")
    password = os.environ.get("PASSWORD", "admin123")

    if not User.objects.filter(username=username).exists():
        print(f"👤 Creating superuser '{username}'...")
        User.objects.create_superuser(username, email, password)
        print(f"✅ Superuser '{username}' created.")
except Exception as e:
    print(f"⚠️  Initialization warning (this might be expected on fresh start): {e}")

# 4. 启动 Gunicorn
print("🔥 Starting Gunicorn Server via Launcher...")

# 构造原本在 CMD 中的参数
sys.argv = [
    "gunicorn",
    "AccountBooks.wsgi:application",
    "--bind",
    "0.0.0.0:8000",
    "--workers",
    "2",
    "--threads",
    "8",
    "--timeout",
    "120",
    "--access-logfile",
    "-",
    "--error-logfile",
    "-",
]
run()
