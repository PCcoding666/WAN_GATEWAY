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

## 🚀 Automated Deployment (GitHub Actions)

Two workflows ship with the repository:

| Workflow | File | Trigger | What it does |
|---|---|---|---|
| **CI** | `.github/workflows/ci.yml` | every push / PR | installs deps, byte-compiles, runs `pytest`, dry-run smoke of UI + CLI + demo, builds the Docker image and boots it |
| **Deploy to production** | `.github/workflows/deploy.yml` | after CI succeeds on `main`, or manually (*Run workflow*) | builds the image, pushes it to Artifact Registry, deploys to **Cloud Run**, smoke-tests the URL |

### One-time setup

1. Create a Google Cloud project and a service account with roles **Cloud Run Admin**,
   **Artifact Registry Writer** and **Service Account User**; download its JSON key.
2. In GitHub → *Settings → Secrets and variables → Actions* add:

   | Secret | Required | Value |
   |---|---|---|
   | `GCP_PROJECT_ID` | ✅ | your project id |
   | `GCP_SA_KEY` | ✅ | the service-account JSON key |
   | `DASHSCOPE_API_KEY` | ✅ | Model Studio API key |
   | `DASHSCOPE_REGION` | – | `cn` (default) or `intl` |
   | `OSS_ACCESS_KEY_ID`, `OSS_ACCESS_KEY_SECRET`, `OSS_ENDPOINT`, `OSS_BUCKET_NAME` | – | needed for image / keyframe / reference uploads |
   | `WAN_UI_AUTH` | – | `user:password[,user2:password2]` — Gradio login gate for the UI |

   Optional *Variables*: `GCP_REGION` (default `us-central1`), `CLOUD_RUN_SERVICE` (default `wan-gateway`),
   `CLOUD_RUN_PUBLIC` (`true` to allow unauthenticated callers; default is IAM-protected).
3. Push to `main` (or run *Deploy to production* manually). Until the three required secrets
   exist the deploy job is **skipped with a notice**, so CI stays green.

**Access control.** By default the service is IAM-protected: only identities granted
`roles/run.invoker` can reach it (the workflow's smoke test uses the service account's identity
token). To open it to anyone, set the repository variable `CLOUD_RUN_PUBLIC=true` **and** set
`WAN_UI_AUTH` so the UI asks for a login — the UI spends your DashScope quota on every click.

The run summary shows the Cloud Run URL. Rollback: re-run the workflow with `image_tag`
set to an earlier commit sha (every image is tagged with its sha and `latest`).

### Local equivalent

```bash
docker build -t wan-gateway .
docker run -p 7860:7860 -e DASHSCOPE_API_KEY=sk-... wan-gateway
# or
docker compose up -d
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