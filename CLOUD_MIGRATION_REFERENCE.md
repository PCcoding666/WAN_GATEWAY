# Quick Reference: Cloud Migration Commands

## 🚀 One-Command Deployment

### Interactive Deployment (Recommended)
```bash
./deploy-production.sh
```

### Automated Deployment
```bash
./deploy-production.sh \
    --project-id "your-project-id" \
    --api-key "your-dashscope-api-key" \
    --deployment-type "cloudrun" \
    --region "us-central1"
```

---

## 📋 Common Commands

### Google Cloud Run
```bash
# Deploy
gcloud run deploy wan-gateway \
    --image gcr.io/PROJECT_ID/wan-gateway:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated

# View logs
gcloud run services logs read wan-gateway --region us-central1

# Update traffic
gcloud run services replace-traffic wan-gateway --to-latest --region us-central1

# Delete service
gcloud run services delete wan-gateway --region us-central1
```

### Google Compute Engine
```bash
# Create VM
gcloud compute instances create wan-gateway-vm \
    --image-family ubuntu-2004-lts \
    --image-project ubuntu-os-cloud \
    --machine-type e2-medium \
    --zone us-central1-a

# SSH to VM
gcloud compute ssh wan-gateway-vm --zone us-central1-a

# Stop VM
gcloud compute instances stop wan-gateway-vm --zone us-central1-a
```

### Docker Registry
```bash
# Build and push
docker build -t wan-gateway .
docker tag wan-gateway gcr.io/PROJECT_ID/wan-gateway:latest
docker push gcr.io/PROJECT_ID/wan-gateway:latest

# Pull and run locally
docker pull gcr.io/PROJECT_ID/wan-gateway:latest
docker run -p 7860:7860 -e DASHSCOPE_API_KEY=your_key gcr.io/PROJECT_ID/wan-gateway:latest
```

---

## 🔧 Configuration Files

### Environment Variables (.env.production)
```
DASHSCOPE_API_KEY=your_production_api_key
PORT=7860
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Cloud Run Service Configuration (service.yaml)
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: wan-gateway
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        autoscaling.knative.dev/minScale: "0"
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/wan-gateway:latest
        ports:
        - containerPort: 7860
        env:
        - name: DASHSCOPE_API_KEY
          value: "your_api_key"
        resources:
          limits:
            memory: 1Gi
            cpu: 1000m
```

---

## 🚨 Troubleshooting

### Build Issues
```bash
# Clean build
docker system prune -f
docker build --no-cache -t wan-gateway .

# Test locally
docker run -p 7860:7860 wan-gateway
curl http://localhost:7860
```

### Deployment Issues
```bash
# Check gcloud configuration
gcloud config list
gcloud auth list

# Test registry access
gcloud auth configure-docker
docker push gcr.io/PROJECT_ID/test

# Check service status
gcloud run services describe wan-gateway --region us-central1
```

### Network Issues
```bash
# Test public access
curl -v https://your-service-url.run.app

# Check firewall rules
gcloud compute firewall-rules list

# Test from VM
gcloud compute ssh your-vm --command "curl -v http://localhost:7860"
```

---

## 💰 Cost Monitoring

### Set Billing Alerts
```bash
# Create budget
gcloud billing budgets create \
    --billing-account BILLING_ACCOUNT_ID \
    --display-name "WAN Gateway Budget" \
    --budget-amount 50 \
    --threshold-rule percent=50 \
    --threshold-rule percent=90
```

### Resource Limits
```bash
# Cloud Run
gcloud run services update wan-gateway \
    --max-instances 5 \
    --region us-central1

# Compute Engine
gcloud compute instances set-scheduling wan-gateway-vm \
    --preemptible \
    --zone us-central1-a
```

---

## 📊 Monitoring

### Application Health
```bash
# Add to your application
curl https://your-service-url.run.app/health

# View metrics
gcloud run services describe wan-gateway --region us-central1
```

### Performance Monitoring
```bash
# Enable monitoring
gcloud services enable monitoring.googleapis.com

# View metrics in console
open https://console.cloud.google.com/monitoring
```

---

## 🔄 CI/CD Integration

### GitHub Actions (.github/workflows/deploy.yml)
```yaml
name: Deploy to Google Cloud Run
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: google-github-actions/setup-gcloud@master
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: ${{ secrets.GCP_PROJECT_ID }}
    - run: gcloud auth configure-docker
    - run: docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/wan-gateway .
    - run: docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/wan-gateway
    - run: gcloud run deploy wan-gateway --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/wan-gateway --region us-central1
```

---

## 📱 Management URLs

- **Google Cloud Console**: https://console.cloud.google.com
- **Cloud Run Services**: https://console.cloud.google.com/run
- **Container Registry**: https://console.cloud.google.com/gcr
- **Compute Engine**: https://console.cloud.google.com/compute
- **Billing**: https://console.cloud.google.com/billing