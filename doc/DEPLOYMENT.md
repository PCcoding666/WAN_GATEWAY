[查看中文文档](DEPLOYMENT_zh.md)

# 🚀 Wan Gateway Deployment Guide

This document provides comprehensive deployment instructions for the Wan Gateway multi-modal video generator, including local development, Docker deployment, and cloud deployment.

## 📋 Table of Contents

- [Requirements](#requirements)
- [Local Development Deployment](#local-development-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Production Environment Configuration](#production-environment-configuration)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## 🔧 Requirements

### Basic Requirements
- **Python**: 3.13+ (latest version recommended)
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Disk Space**: Minimum 5GB available space
- **Network**: Stable internet connection (for API calls)

### API Requirements
- Valid Alibaba Bailian API key
- Optional: Alibaba Cloud OSS storage configuration (for image uploads)

## 🏠 Local Development Deployment

### 1. Project Setup

```bash
# Clone the project
git clone https://github.com/PCcoding666/WAN_GATEWAY.git
cd Wan_Gateway

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import gradio; print('Gradio version:', gradio.__version__)"
```

### 3. Environment Configuration

```bash
# Copy environment variable template
cp .env.example .env

# Edit environment variables
# Use your preferred editor to edit the .env file
```

**.env file example**:
```bash
# Required configuration
DASHSCOPE_API_KEY=your_api_key_here

# Optional OSS configuration
OSS_ACCESS_KEY_ID=your_oss_access_key_id
OSS_ACCESS_KEY_SECRET=your_oss_access_key_secret
OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=wan-gateway-images

# Optional application configuration
PORT=7860
HOST=127.0.0.1
```

### 4. Run Application

```bash
# Check environment configuration
python main.py --check-env

# Start development server
python main.py

# Or use custom configuration
python main.py --host 0.0.0.0 --port 8080 --debug
```

## 🐳 Docker Deployment

### 1. Basic Docker Deployment

```bash
# Build Docker image
docker build -t wan-gateway .

# Run container
docker run -d \
  --name wan-gateway \
  -p 7860:7860 \
  -e DASHSCOPE_API_KEY=your_api_key_here \
  wan-gateway
```

### 2. Using Docker Compose

**docker-compose.yml** is included in the project:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Production-Grade Docker Deployment

```bash
# Use production deployment script
chmod +x deploy-production.sh
./deploy-production.sh

# Or manually run production-grade container
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

## ☁️ Cloud Deployment

### 1. Google Cloud Platform

```bash
# Use provided deployment script
chmod +x deploy-to-cloud.sh
./deploy-to-cloud.sh

# Or manually deploy with Cloud Run
gcloud run deploy wan-gateway \
  --image gcr.io/your-project/wan-gateway \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DASHSCOPE_API_KEY=your_api_key
```

### 2. Alibaba Cloud ECS

```bash
# On ECS instance
# 1. Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# 2. Pull and run image
sudo docker pull your-registry/wan-gateway:latest
sudo docker run -d \
  --name wan-gateway \
  -p 80:7860 \
  --restart always \
  -e DASHSCOPE_API_KEY=your_api_key \
  your-registry/wan-gateway:latest
```

### 3. AWS ECS

Deploy using AWS ECS task definition:

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

## 🔒 Production Environment Configuration

### 1. Security Configuration

```bash
# Use environment variables instead of .env files
export DASHSCOPE_API_KEY="your_secure_api_key"
export OSS_ACCESS_KEY_ID="your_secure_oss_key"
export OSS_ACCESS_KEY_SECRET="your_secure_oss_secret"

# Configure firewall (if needed)
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. Reverse Proxy Configuration (Nginx)

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
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 3. SSL Configuration

```bash
# Use Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 📊 Monitoring and Maintenance

### 1. Health Checks

```bash
# Check application status
curl http://localhost:7860/

# Check environment configuration
docker exec wan-gateway python main.py --check-env

# View container logs
docker logs wan-gateway
```

### 2. Log Management

```bash
# Configure log rotation
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

### 3. Performance Monitoring

```bash
# Monitor resource usage
docker stats wan-gateway

# Monitor application performance
# Can integrate Prometheus/Grafana or other monitoring tools
```

## ❌ Troubleshooting

### 1. Port Conflicts

```bash
# Find process using port
lsof -i :7860
# or
netstat -tlnp | grep :7860

# Use different port
python main.py --port 8080
```

### 2. Memory Issues

```bash
# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 3. API Connection Issues

```bash
# Test API connection
python -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('DASHSCOPE_API_KEY')
print(f'API Key configured: {bool(api_key)}')
"
```

### 4. Docker Related Issues

```bash
# Clean up Docker resources
docker system prune -a

# Rebuild image
docker build --no-cache -t wan-gateway .

# Check container status
docker inspect wan-gateway
```

## 🚀 Automated Deployment

### CI/CD Pipeline Example (GitHub Actions)

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
        # Add your deployment logic here
        # e.g., push to container registry, then deploy to server
        echo "Deploying to production..."
```

## 📝 Maintenance Checklist

### Daily Maintenance
- [ ] Check application logs
- [ ] Monitor resource usage
- [ ] Verify API key status
- [ ] Check disk space

### Periodic Maintenance
- [ ] Update dependencies
- [ ] Backup configuration files
- [ ] Performance optimization analysis
- [ ] Security update checks

### Emergency Response
- [ ] Prepare rollback plan
- [ ] Backup API keys
- [ ] Set up monitoring alerts
- [ ] Disaster recovery procedures

---

**Need help?** Please refer to the [main documentation](README.md) or submit an issue to the project repository.

For Chinese documentation, see the [doc](doc/) folder.