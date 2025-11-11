#!/bin/bash

# Docker 测试脚本
# 用于测试 Wan Gateway 应用的 Docker 部署

set -e  # 遇到错误时退出

echo "🐳 开始 Docker 测试..."

# 检查 Docker 是否运行
echo "🔍 检查 Docker 状态..."
if ! docker info &> /dev/null; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi
echo "✅ Docker 运行正常"

# 停止并删除现有容器（如果存在）
echo "🧹 清理现有容器..."
if docker ps -a --format '{{.Names}}' | grep -q '^wan-gateway$'; then
    docker stop wan-gateway >/dev/null 2>&1 || true
    docker rm wan-gateway >/dev/null 2>&1 || true
    echo "✅ 已清理现有容器"
fi

# 构建 Docker 镜像（如果不存在）
echo "🏗️ 检查 Docker 镜像..."
if ! docker images | grep -q 'wan-gateway.*latest'; then
    echo "🔨 构建 Docker 镜像..."
    docker build -t wan-gateway .
    echo "✅ Docker 镜像构建完成"
else
    echo "✅ Docker 镜像已存在"
fi

# 启动容器
echo "🚀 启动容器..."
docker-compose up -d
echo "✅ 容器已启动"

# 等待应用启动
echo "⏳ 等待应用启动..."
sleep 10

# 检查容器状态
echo "🔍 检查容器状态..."
if docker ps | grep -q wan-gateway; then
    echo "✅ 容器正在运行"
else
    echo "❌ 容器未运行"
    docker logs wan-gateway
    exit 1
fi

# 检查应用是否响应
echo "🔍 检查应用响应..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:7860 | grep -q "200"; then
    echo "✅ 应用正常响应"
else
    echo "❌ 应用未响应"
    docker logs wan-gateway
    exit 1
fi

echo "🎉 Docker 测试完成！"
echo "🌐 访问地址: http://localhost:7860"
echo "⏹️  要停止测试，请运行: docker-compose down"