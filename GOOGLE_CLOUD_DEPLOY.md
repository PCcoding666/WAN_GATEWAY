# Google Cloud Run Deployment Configuration

## Prerequisites
1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Initialize gcloud: `gcloud init`
3. Enable Cloud Run API: `gcloud services enable run.googleapis.com`
4. Set your project: `gcloud config set project YOUR_PROJECT_ID`

## Build and Deploy Commands

### 1. Build for Google Cloud
```bash
# Build the Docker image
docker build -t wan-gateway .

# Tag for Google Container Registry
docker tag wan-gateway gcr.io/YOUR_PROJECT_ID/wan-gateway

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/wan-gateway
```

### 2. Deploy to Cloud Run
```bash
# Deploy with environment variable
gcloud run deploy wan-gateway \
    --image gcr.io/YOUR_PROJECT_ID/wan-gateway \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 7860 \
    --set-env-vars DASHSCOPE_API_KEY=YOUR_API_KEY_HERE \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10
```

### 3. One-line deployment script
```bash
# Quick deployment (replace YOUR_PROJECT_ID and YOUR_API_KEY)
PROJECT_ID="your-project-id"
API_KEY="your-dashscope-api-key"

docker build -t wan-gateway . && \
docker tag wan-gateway gcr.io/$PROJECT_ID/wan-gateway && \
docker push gcr.io/$PROJECT_ID/wan-gateway && \
gcloud run deploy wan-gateway \
    --image gcr.io/$PROJECT_ID/wan-gateway \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 7860 \
    --set-env-vars DASHSCOPE_API_KEY=$API_KEY \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10
```

## Environment Variables
- `DASHSCOPE_API_KEY`: Your Alibaba DashScope API key (required)
- `PORT`: Application port (default: 7860)

## Resource Configuration
- Memory: 2Gi (adjustable based on needs)
- CPU: 1 vCPU (adjustable based on needs)
- Max instances: 10 (adjustable based on expected traffic)

## Cost Optimization
- Cloud Run charges only for actual usage
- Configure appropriate max instances to control costs
- Consider setting up auto-scaling policies

## Monitoring
- View logs: `gcloud run services logs read wan-gateway --region us-central1`
- View service details: `gcloud run services describe wan-gateway --region us-central1`