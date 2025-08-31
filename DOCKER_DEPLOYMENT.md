# WAN_Gateway Docker Deployment Guide

Clean, streamlined Docker deployment for local development and Google Cloud.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop running
- `.env` file: `DASHSCOPE_API_KEY=your_key`

### Deploy in One Command
```bash
./deploy.sh deploy
```

Access: http://localhost:7860

## 📋 Commands

```bash
./deploy.sh deploy    # Build + run
./deploy.sh build     # Build only
./deploy.sh start     # Start container
./deploy.sh stop      # Stop container
./deploy.sh restart   # Restart
./deploy.sh logs      # View logs
./deploy.sh status    # Check status
./deploy.sh cleanup   # Remove all
```

## 🔧 Manual Docker

```bash
# Build
docker build -t wan-gateway .

# Run
docker run -d --name wan-gateway \
  -p 7860:7860 \
  --env DASHSCOPE_API_KEY="your_key" \
  -v $(pwd)/downloads:/app/downloads \
  wan-gateway
```

## 🐳 Docker Compose

```bash
docker-compose up -d     # Start
docker-compose logs -f   # Logs
docker-compose down      # Stop
```

## 🛠️ Configuration

- **API Key**: Set `DASHSCOPE_API_KEY` in `.env`
- **Port**: 7860 (default)
- **Volumes**: `./downloads` and `./cache`

## 🌐 Google Cloud

See `GOOGLE_CLOUD_DEPLOY.md` for cloud deployment.

## 🔍 Troubleshooting

```bash
# Check logs
./deploy.sh logs

# Test connectivity
curl http://localhost:7860/

# Verify API key
docker exec wan-gateway env | grep DASHSCOPE
```

## ✨ Features

- **Lightweight**: ~200MB image
- **Fast startup**: ~30 seconds
- **Secure**: Non-root user
- **Clean**: Single optimized Dockerfile