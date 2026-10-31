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

CI publishes every `main` build to GitHub Container Registry as
`ghcr.io/pccoding666/wan_gateway:<sha>` and `:latest`, so any Docker host can run it.

### 1. Any VM (Alibaba Cloud ECS, a VPS, your own box)

```bash
# 1. Install Docker (Alibaba Cloud Linux / CentOS shown; use apt on Debian/Ubuntu)
sudo yum install -y docker && sudo systemctl enable --now docker

# 2. Fetch the deploy helper and your settings
curl -fsSLO https://raw.githubusercontent.com/PCcoding666/WAN_GATEWAY/main/production/deploy.sh
curl -fsSL  https://raw.githubusercontent.com/PCcoding666/WAN_GATEWAY/main/.env.example -o .env
vi .env            # set DASHSCOPE_API_KEY (and WAN_UI_AUTH, OSS_* if needed)

# 3. Pull the image and (re)start the container; re-run to update, pass a sha to roll back
chmod +x deploy.sh && ./deploy.sh            # latest
./deploy.sh 4ec95d0e...                      # a specific build
```

The same steps are what the **Deploy to production** workflow runs over SSH (see below).

### 2. AWS ECS

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
| **Deploy to production** | `.github/workflows/deploy.yml` | after CI succeeds on `main`, or manually (*Run workflow*) | **stage 1** publishes the image to GHCR (`ghcr.io/pccoding666/wan_gateway:<sha>`, `:latest`); **stage 2** SSHes into your server, pulls that image, restarts the `wan-gateway` container and smoke-tests the URL |

Stage 1 needs nothing (it uses the built-in `GITHUB_TOKEN`). Stage 2 runs only when the SSH
secrets below exist; otherwise it is **skipped with a notice** and the image is still published.

### One-time setup for the server stage

1. A Linux host with Docker installed and an SSH user that can run `docker` (member of the
   `docker` group). Open the port you want to serve on (default `7860`), or put a reverse proxy
   with TLS in front of it.
2. In GitHub → *Settings → Secrets and variables → Actions* add:

   | Secret | Required | Value |
   |---|---|---|
   | `PROD_SSH_HOST` | ✅ | server hostname or IP |
   | `PROD_SSH_USER` | ✅ | SSH user |
   | `PROD_SSH_KEY` | ✅ | that user's private key (PEM) |
   | `DASHSCOPE_API_KEY` | ✅ | Model Studio API key |
   | `PROD_SSH_PORT` | – | default `22` |
   | `PROD_PORT` | – | host port to publish, default `7860` |
   | `PROD_URL` | – | public URL for the smoke test, default `http://HOST:PORT` |
   | `WAN_UI_AUTH` | recommended | `user:password[,user2:password2]` — Gradio login gate |
   | `DASHSCOPE_REGION` | – | `cn` (default) or `intl` |
   | `OSS_ACCESS_KEY_ID`, `OSS_ACCESS_KEY_SECRET`, `OSS_ENDPOINT`, `OSS_BUCKET_NAME` | – | needed for image / keyframe / reference uploads |

3. Push to `main` or run *Deploy to production* manually. The run summary shows the image
   tags and the URL.

**Access control.** The container is reachable by anyone who can reach the port, and every click
spends your DashScope quota, so set `WAN_UI_AUTH` (the UI then asks for a login) and prefer a
reverse proxy with TLS. **Rollback:** run the workflow manually with `image_tag` set to an earlier
commit sha, or `./production/deploy.sh <sha>` on the server.

**Private packages.** GHCR packages are private by default; the server stage logs in with the
workflow token, and `production/deploy.sh` run by hand needs `docker login ghcr.io` with a personal
access token that has `read:packages` — or make the package public in its GitHub settings.

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