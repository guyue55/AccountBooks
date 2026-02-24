#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Configuration
IMAGE_NAME="accountbooks"
TAG="latest"

echo "🐳 Building Docker image: ${IMAGE_NAME}:${TAG}..."

# Check if uv is installed
if command -v uv &> /dev/null; then
    echo "📦 Syncing requirements.txt from pyproject.toml..."
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
# -f docker/Dockerfile: specify the location of Dockerfile
docker build -t ${IMAGE_NAME}:${TAG} -f docker/Dockerfile . --no-cache

echo ""
echo "🎉 Build successful!"
echo "==============================================="
echo "👉 Run the container:"
echo "   docker run -d -p 8000:8000 ${IMAGE_NAME}:${TAG}"
echo "==============================================="
