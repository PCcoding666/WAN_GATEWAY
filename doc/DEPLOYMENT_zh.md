# 🚀 Wan Gateway 部署指南

这个文档提供了 Wan Gateway 多模态视频生成器的详细部署指南，包括本地开发、Docker 部署和云端部署。

## 📋 目录

- [环境要求](#环境要求)
- [本地开发部署](#本地开发部署)
- [Docker 部署](#docker-部署)
- [云端部署](#云端部署)
- [生产环境配置](#生产环境配置)
- [监控和维护](#监控和维护)
- [常见问题解决](#常见问题解决)

## 🔧 环境要求

### 基础要求
- **Python**: 3.13+ (推荐使用最新版本)
- **内存**: 最少 2GB RAM (推荐 4GB+)
- **磁盘空间**: 最少 5GB 可用空间
- **网络**: 稳定的互联网连接 (用于 API 调用)

### API 要求
- 有效的阿里巴巴百炼 API 密钥
- 可选：阿里云 OSS 存储配置 (用于图像上传)

## 🏠 本地开发部署

### 1. 项目设置

```bash
# 克隆项目
git clone https://github.com/PCcoding666/WAN_GATEWAY.git
cd Wan_Gateway

# 创建虚拟环境 (推荐)
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 验证安装
python -c "import gradio; print('Gradio version:', gradio.__version__)"
```

### 3. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
# 使用你喜欢的编辑器编辑 .env 文件
```

**.env 文件示例**:
```bash
# 必需配置
DASHSCOPE_API_KEY=your_api_key_here

# 可选 OSS 配置
OSS_ACCESS_KEY_ID=your_oss_access_key_id
OSS_ACCESS_KEY_SECRET=your_oss_access_key_secret
OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=wan-gateway-images

# 可选应用配置
PORT=7860
HOST=127.0.0.1
```

### 4. 运行应用

```bash
# 检查环境配置
python main.py --check-env

# 启动开发服务器
python main.py

# 或者使用自定义配置
python main.py --host 0.0.0.0 --port 8080 --debug
```

## 🐳 Docker 部署

### 1. 基础 Docker 部署

```bash
# 构建 Docker 镜像
docker build -t wan-gateway .

# 运行容器
docker run -d \
  --name wan-gateway \
  -p 7860:7860 \
  -e DASHSCOPE_API_KEY=your_api_key_here \
  wan-gateway
```

### 2. 使用 Docker Compose

**docker-compose.yml** 已包含在项目中:

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. 生产级 Docker 部署

```bash
# 使用生产部署脚本
chmod +x deploy-production.sh
./deploy-production.sh

# 或者手动运行生产级容器
docker run -d \
  --name wan-gateway-prod \
  -p 80:7860 \
  --restart unless-stopped \
  --memory="2g" \
  --cpus="1.0" \
  -e DASHSCOPE_API_KEY=your_api_key_here \
  -e OSS_ACCESS_KEY_ID=your_oss_key_id \
  -e OSS_ACCESS_KEY_SECRET=your_oss_secret \
  -v /var/log/wan-gateway:/app/logs \
  wan-gateway:latest
```

## ☁️ 云端部署

### 1. Google Cloud Platform

```bash
# 使用提供的部署脚本
chmod +x deploy-to-cloud.sh
./deploy-to-cloud.sh

# 或者使用 Cloud Run 手动部署
gcloud run deploy wan-gateway \
  --image gcr.io/your-project/wan-gateway \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DASHSCOPE_API_KEY=your_api_key
```

### 2. 阿里云 ECS

```bash
# 在 ECS 实例上
# 1. 安装 Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# 2. 拉取和运行镜像
sudo docker pull your-registry/wan-gateway:latest
sudo docker run -d \
  --name wan-gateway \
  -p 80:7860 \
  --restart always \
  -e DASHSCOPE_API_KEY=your_api_key \
  your-registry/wan-gateway:latest
```

### 3. AWS ECS

使用 AWS ECS 任务定义部署:

```json
{
  "family": "wan-gateway",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "wan-gateway",
      "image": "your-registry/wan-gateway:latest",
      "portMappings": [
        {
          "containerPort": 7860,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DASHSCOPE_API_KEY",
          "value": "your_api_key"
        }
      ]
    }
  ]
}
```

## 🔒 生产环境配置

### 1. 安全配置

```bash
# 使用环境变量而不是 .env 文件
export DASHSCOPE_API_KEY="your_secure_api_key"
export OSS_ACCESS_KEY_ID="your_secure_oss_key"
export OSS_ACCESS_KEY_SECRET="your_secure_oss_secret"

# 配置防火墙 (如果需要)
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. 反向代理配置 (Nginx)

**nginx.conf**:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 3. SSL 配置

```bash
# 使用 Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 📊 监控和维护

### 1. 健康检查

```bash
# 检查应用状态
curl http://localhost:7860/

# 检查环境配置
docker exec wan-gateway python main.py --check-env

# 查看容器日志
docker logs wan-gateway
```

### 2. 日志管理

```bash
# 配置日志轮转
sudo tee /etc/logrotate.d/wan-gateway <<EOF
/var/log/wan-gateway/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 0644 root root
}
EOF
```

### 3. 性能监控

```bash
# 监控资源使用
docker stats wan-gateway

# 监控应用性能
# 可以集成 Prometheus/Grafana 或其他监控工具
```

## ❌ 常见问题解决

### 1. 端口冲突

```bash
# 查找占用端口的进程
lsof -i :7860
# 或者
netstat -tlnp | grep :7860

# 使用不同端口
python main.py --port 8080
```

### 2. 内存不足

```bash
# 增加 swap 空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 3. API 连接问题

```bash
# 测试 API 连接
python -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('DASHSCOPE_API_KEY')
print(f'API Key configured: {bool(api_key)}')
"
```

### 4. Docker 相关问题

```bash
# 清理 Docker 资源
docker system prune -a

# 重新构建镜像
docker build --no-cache -t wan-gateway .

# 检查容器状态
docker inspect wan-gateway
```

## 🚀 自动化部署

### CI/CD 流水线示例 (GitHub Actions)

**.github/workflows/deploy.yml**:
```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: docker build -t wan-gateway:latest .
    
    - name: Deploy to server
      run: |
        # 这里添加你的部署逻辑
        # 例如推送到容器注册表，然后部署到服务器
        echo "Deploying to production..."
```

## 📝 维护清单

### 日常维护
- [ ] 检查应用日志
- [ ] 监控资源使用情况
- [ ] 验证 API 密钥状态
- [ ] 检查磁盘空间

### 周期性维护
- [ ] 更新依赖包
- [ ] 备份配置文件
- [ ] 性能优化分析
- [ ] 安全更新检查

### 紧急情况处理
- [ ] 准备回滚计划
- [ ] 备用 API 密钥
- [ ] 监控报警设置
- [ ] 故障恢复流程

---

**需要帮助？** 请查看 [主要文档](README.md) 或者提交 Issue 到项目仓库。