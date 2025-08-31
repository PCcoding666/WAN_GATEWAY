# Cloud Migration SOP (Standard Operating Procedure)
## WAN Gateway Docker Application Deployment

### 📋 Overview
This document provides a step-by-step procedure for migrating your locally developed Docker application to cloud servers. Multiple deployment options are covered to suit different requirements and budgets.

---

## 🎯 Pre-Deployment Checklist

### 1. Local Verification
- [ ] Docker builds successfully locally: `docker build -t wan-gateway .`
- [ ] Application runs correctly in Docker: `./deploy-clean.sh start`
- [ ] All environment variables are properly configured
- [ ] API keys and secrets are ready for production

### 2. Production Readiness
- [ ] Remove development-specific configurations
- [ ] Secure API keys (use environment variables, not hardcoded)
- [ ] Configure proper logging for production
- [ ] Test with production-like data volumes

### 3. Cloud Account Setup
- [ ] Cloud platform account active (Google Cloud, AWS, Azure, etc.)
- [ ] Billing configured and limits set
- [ ] Required APIs/services enabled
- [ ] Access permissions configured

---

## 🚀 Deployment Options

### Option A: Google Cloud Run (Recommended - Serverless)

#### Step 1: Setup Google Cloud
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize and authenticate
gcloud init
gcloud auth login

# Set project and enable services
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### Step 2: Build and Push Image
```bash
# Build for production
docker build -t wan-gateway .

# Tag for Google Container Registry
docker tag wan-gateway gcr.io/YOUR_PROJECT_ID/wan-gateway:latest

# Push to registry
docker push gcr.io/YOUR_PROJECT_ID/wan-gateway:latest
```

#### Step 3: Deploy to Cloud Run
```bash
gcloud run deploy wan-gateway \
    --image gcr.io/YOUR_PROJECT_ID/wan-gateway:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 7860 \
    --set-env-vars DASHSCOPE_API_KEY=YOUR_API_KEY \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0
```

#### Benefits:
- ✅ Pay only for actual usage
- ✅ Automatic scaling (0 to N instances)
- ✅ No server management
- ✅ HTTPS by default

---

### Option B: Google Compute Engine (VM-based)

#### Step 1: Create VM Instance
```bash
gcloud compute instances create wan-gateway-vm \
    --image-family ubuntu-2004-lts \
    --image-project ubuntu-os-cloud \
    --machine-type e2-medium \
    --zone us-central1-a \
    --tags http-server,https-server
```

#### Step 2: Setup VM Environment
```bash
# SSH into VM
gcloud compute ssh wan-gateway-vm --zone us-central1-a

# Install Docker
sudo apt update
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

#### Step 3: Deploy Application
```bash
# Pull and run your image
docker pull gcr.io/YOUR_PROJECT_ID/wan-gateway:latest
docker run -d \
    -p 80:7860 \
    -e DASHSCOPE_API_KEY=YOUR_API_KEY \
    --name wan-gateway \
    --restart unless-stopped \
    gcr.io/YOUR_PROJECT_ID/wan-gateway:latest
```

#### Benefits:
- ✅ Full control over environment
- ✅ Predictable costs
- ✅ Can run multiple services
- ✅ Persistent storage options

---

### Option C: Other Cloud Providers

#### AWS (Amazon Web Services)
```bash
# AWS ECR + ECS/Fargate
aws ecr create-repository --repository-name wan-gateway
docker tag wan-gateway:latest AWS_ACCOUNT.dkr.ecr.region.amazonaws.com/wan-gateway:latest
docker push AWS_ACCOUNT.dkr.ecr.region.amazonaws.com/wan-gateway:latest
```

#### Azure Container Instances
```bash
# Azure Container Registry + Container Instances
az acr create --resource-group myResourceGroup --name myRegistry --sku Basic
az acr build --registry myRegistry --image wan-gateway:latest .
az container create --resource-group myResourceGroup --name wan-gateway --image myRegistry.azurecr.io/wan-gateway:latest
```

#### DigitalOcean App Platform
```bash
# Use doctl CLI or web interface
doctl apps create-deployment myapp --config app.yaml
```

---

## 🔧 Production Configuration

### Environment Variables Setup
Create a production environment file:
```bash
# .env.production
DASHSCOPE_API_KEY=your_production_api_key
PORT=7860
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Security Best Practices
1. **API Key Management**
   - Use cloud secret managers (Google Secret Manager, AWS Secrets Manager)
   - Never commit API keys to code
   - Rotate keys regularly

2. **Network Security**
   - Configure firewall rules
   - Use HTTPS only
   - Implement rate limiting

3. **Container Security**
   - Use non-root user (already configured)
   - Regular security updates
   - Scan images for vulnerabilities

### Monitoring and Logging
```bash
# Google Cloud Logging
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wan-gateway"

# Health check endpoint (add to your app)
curl https://your-app-url.run.app/health
```

---

## 📊 Cost Optimization

### Google Cloud Run
- **Free Tier**: 2 million requests/month
- **Pricing**: ~$0.40 per million requests
- **Memory**: $0.0025/GB/hour
- **CPU**: $0.0025/vCPU/hour

### Optimization Tips
1. Set appropriate memory limits (start with 512MB, scale up if needed)
2. Configure min-instances only if needed for cold start performance
3. Use request timeout settings
4. Monitor usage with billing alerts

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Build Failures
```bash
# Check build logs
docker build -t wan-gateway . --no-cache

# Test locally first
docker run -p 7860:7860 wan-gateway
```

#### 2. Cloud Run Deployment Issues
```bash
# Check deployment logs
gcloud run services logs read wan-gateway --region us-central1

# Test with minimal configuration
gcloud run deploy wan-gateway --image gcr.io/PROJECT/wan-gateway --platform managed
```

#### 3. Network Issues
```bash
# Test connectivity
curl -v https://your-service-url

# Check firewall rules
gcloud compute firewall-rules list
```

---

## 📝 Quick Deployment Script

Create `deploy-production.sh`:
```bash
#!/bin/bash
set -e

# Configuration
PROJECT_ID="your-project-id"
SERVICE_NAME="wan-gateway"
REGION="us-central1"
IMAGE_TAG="latest"

echo "🚀 Starting production deployment..."

# Build and push
echo "📦 Building Docker image..."
docker build -t $SERVICE_NAME .

echo "🏷️ Tagging for Google Container Registry..."
docker tag $SERVICE_NAME gcr.io/$PROJECT_ID/$SERVICE_NAME:$IMAGE_TAG

echo "📤 Pushing to container registry..."
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:$IMAGE_TAG

echo "🌟 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:$IMAGE_TAG \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 7860 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10

echo "✅ Deployment complete!"
echo "🌐 Your application is available at:"
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
```

---

## 📋 Post-Deployment Checklist

- [ ] Application accessible via public URL
- [ ] Health checks passing
- [ ] Logs showing normal operation
- [ ] Environment variables properly set
- [ ] Performance monitoring configured
- [ ] Backup and disaster recovery plan in place
- [ ] Cost monitoring alerts configured
- [ ] Security scanning completed

---

## 📞 Support and Next Steps

1. **Monitor Performance**: Set up alerts for response time, error rates
2. **Scale Planning**: Configure auto-scaling based on usage patterns
3. **CI/CD Setup**: Automate deployments with GitHub Actions or Cloud Build
4. **Domain Setup**: Configure custom domain if needed
5. **SSL/TLS**: Ensure HTTPS is properly configured

For issues or questions, refer to:
- Google Cloud Run Documentation
- Application logs and monitoring dashboards
- Cloud provider support channels