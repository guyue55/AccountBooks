#!/bin/bash
# 一键格式化所有代码 (Python + Django Templates)

# 获取脚本所在目录的父目录作为项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "🚀 Starting Full Project Formatting..."
echo "=========================================="

# 1. 使用 Ruff 处理 Python 代码
# 使用 --group dev 确保 ruff 被包含在运行环境中
echo "🐍 [Python] Formatting with Ruff..."
uv run --group dev ruff format . || echo "⚠️  Ruff format encountered some issues."

echo "🛠️  [Python] Fixing Lint issues..."
uv run --group dev ruff check --fix --unsafe-fixes . || echo "⚠️  Some Lint issues require manual attention (see above)."

# 2. 使用 djlint 处理 HTML 模板
# djlint 通常在主依赖中，但也使用 --group dev 以防万一
echo "📄 [HTML] Formatting Django Templates with djlint..."
if uv run --group dev djlint --version &> /dev/null; then
    uv run --group dev djlint . --reformat
else
    echo "⚠️  djlint not found, skipping template formatting."
fi

echo "=========================================="
echo "✨ All code formatted successfully!"
echo "=========================================="
