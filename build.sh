#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Default configuration
IMAGE_NAME="accountbooks"
CONTAINER_NAME="accountbooks"
TAG="latest"
DOCKERFILE="docker/Dockerfile"

# Check for arguments
if [ "$1" == "--distroless" ]; then
    DOCKERFILE="docker/Dockerfile.distroless"
    TAG="${TAG}-distroless"
    CONTAINER_NAME="${CONTAINER_NAME}-distroless"
else
    echo "🐳 请选择要构建的镜像类型 (Select Image Type):"
    echo "   1) 标准镜像 (Standard)      - docker/Dockerfile"
    echo "   2) Distroless 镜像          - docker/Dockerfile.distroless"
    read -p "👉 您的选择 [默认 1]: " choice
    echo ""

    if [[ "$choice" == "2" ]]; then
        DOCKERFILE="docker/Dockerfile.distroless"
        TAG="${TAG}-distroless"
        CONTAINER_NAME="${CONTAINER_NAME}-distroless"
    else
        echo "✅ 使用默认选项: 1 (Standard)"
    fi
fi

echo "🐳 Building Docker image: ${IMAGE_NAME}:${TAG} using ${DOCKERFILE}..."

# Check if uv is installed
if command -v uv &> /dev/null; then
    echo "📦 Syncing requirements.txt from pyproject.toml..."
    # 默认只编译项目核心依赖，不包含 dev 组
    uv pip compile pyproject.toml -o requirements.txt
else
    echo "⚠️  'uv' not found. Skipping requirements.txt sync. Make sure it's up to date!"
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: 'docker' is not installed."
    exit 1
fi

# Build the image
# --no-cache: ensure we get the latest updates
# 
# 🌐 [单平台构建] 默认：仅为当前宿主机架构编译
docker build -t ${IMAGE_NAME}:${TAG} -f ${DOCKERFILE} . --no-cache

# 🌐 [多平台跨平台构建] 如果您想在本地直接编译 AMD64 + ARM64 并推送到远端仓库：
# 请使用下方命令（需安装 docker buildx，且由于普通本地 Docker 引擎没法同时容纳双架构，往往需要跟上 --push 直接推上云）
# docker buildx build --platform linux/amd64,linux/arm64 -t ${IMAGE_NAME}:${TAG} -f ${DOCKERFILE} . --no-cache
echo ""
echo "🎉 Build successful!"
echo "==============================================="
echo "👉 Run the container:"
echo "   docker run -d --name ${CONTAINER_NAME} -p 8000:8000 ${IMAGE_NAME}:${TAG}"
echo ""
echo "💡 Tip: Use './build.sh --distroless' to build a distroless image."
echo "==============================================="
