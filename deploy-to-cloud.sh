#!/bin/bash

# WAN Gateway Cloud Deployment Script
# Automated cloud deployment for beginners

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
APP_NAME="wan-gateway"
IMAGE_NAME="wan-gateway:latest"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    echo "Cloud Deployment Script for WAN Gateway"
    echo ""
    echo "Usage: $0 [PLATFORM] [PROJECT_ID]"
    echo ""
    echo "Platforms:"
    echo "  google     Deploy to Google Cloud Run"
    echo "  aliyun     Deploy to Alibaba Cloud"
    echo "  aws        Deploy to AWS App Runner"
    echo ""
    echo "Examples:"
    echo "  $0 google my-project-123        # Deploy to Google Cloud"
    echo "  $0 aliyun my-namespace          # Deploy to Alibaba Cloud"
    echo ""
    echo "Prerequisites:"
    echo "  - Docker image built locally"
    echo "  - Cloud CLI tools installed"
    echo "  - Valid API credentials"
}

check_prerequisites() {
    # Check if Docker image exists
    if ! docker images | grep -q "wan-gateway"; then
        print_error "Docker image 'wan-gateway' not found"
        echo "Please run: ./deploy.sh build"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_error ".env file not found"
        echo "Please create .env file with your API key"
        exit 1
    fi

    # Extract API key from .env
    API_KEY=$(grep "DASHSCOPE_API_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    if [ "$API_KEY" = "your_api_key_here" ] || [ -z "$API_KEY" ]; then
        print_error "Please set your actual API key in .env file"
        exit 1
    fi

    print_status "Prerequisites check passed ✓"
}

deploy_to_google() {
    local project_id=$1
    
    print_status "Deploying to Google Cloud Run..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud CLI not found"
        echo "Install it with: brew install google-cloud-sdk"
        exit 1
    fi

    # Authenticate and set project
    print_status "Setting up Google Cloud project..."
    gcloud config set project $project_id
    
    # Enable required services
    print_status "Enabling required services..."
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    
    # Configure Docker for GCR
    gcloud auth configure-docker --quiet
    
    # Tag and push image
    print_status "Pushing image to Google Container Registry..."
    docker tag $IMAGE_NAME gcr.io/$project_id/$APP_NAME:latest
    docker push gcr.io/$project_id/$APP_NAME:latest
    
    # Deploy to Cloud Run
    print_status "Deploying to Cloud Run..."
    gcloud run deploy $APP_NAME \
        --image gcr.io/$project_id/$APP_NAME:latest \
        --platform managed \
        --region asia-east1 \
        --allow-unauthenticated \
        --set-env-vars DASHSCOPE_API_KEY="$API_KEY" \
        --port 7860 \
        --memory 1Gi \
        --cpu 1 \
        --max-instances 10 \
        --quiet
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $APP_NAME --platform managed --region asia-east1 --format 'value(status.url)')
    
    print_success "Deployment completed!"
    print_success "Your application is available at: $SERVICE_URL"
}

deploy_to_aliyun() {
    local namespace=$1
    
    print_status "Deploying to Alibaba Cloud..."
    
    # Check if aliyun CLI is installed
    if ! command -v aliyun &> /dev/null; then
        print_error "Alibaba Cloud CLI not found"
        echo "Please install it from: https://help.aliyun.com/document_detail/121541.html"
        exit 1
    fi

    # Configure registry
    print_warning "Please make sure you have:"
    echo "1. Created a namespace in Container Registry"
    echo "2. Configured Docker login for Alibaba Cloud Registry"
    echo ""
    read -p "Press Enter to continue..."
    
    # Tag and push image
    print_status "Pushing image to Alibaba Cloud Registry..."
    docker tag $IMAGE_NAME registry.cn-hangzhou.aliyuncs.com/$namespace/$APP_NAME:latest
    docker push registry.cn-hangzhou.aliyuncs.com/$namespace/$APP_NAME:latest
    
    print_success "Image pushed successfully!"
    print_warning "Please complete deployment in Alibaba Cloud Console:"
    echo "1. Go to Container Service console"
    echo "2. Create a new application"
    echo "3. Use image: registry.cn-hangzhou.aliyuncs.com/$namespace/$APP_NAME:latest"
    echo "4. Set environment variable: DASHSCOPE_API_KEY=$API_KEY"
    echo "5. Configure port: 7860"
}

deploy_to_aws() {
    print_status "Deploying to AWS App Runner..."
    
    # Check if aws CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found"
        echo "Install it with: brew install awscli"
        exit 1
    fi

    print_warning "AWS App Runner deployment requires:"
    echo "1. ECR repository created"
    echo "2. AWS credentials configured"
    echo "3. apprunner.yaml configuration file"
    echo ""
    echo "This is more complex for beginners. Consider using Google Cloud Run instead."
}

# Main execution
case "${1:-help}" in
    google)
        if [ -z "$2" ]; then
            print_error "Project ID required for Google Cloud deployment"
            echo "Usage: $0 google PROJECT_ID"
            exit 1
        fi
        check_prerequisites
        deploy_to_google "$2"
        ;;
    aliyun)
        if [ -z "$2" ]; then
            print_error "Namespace required for Alibaba Cloud deployment"
            echo "Usage: $0 aliyun NAMESPACE"
            exit 1
        fi
        check_prerequisites
        deploy_to_aliyun "$2"
        ;;
    aws)
        check_prerequisites
        deploy_to_aws
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown platform: $1"
        echo ""
        show_help
        exit 1
        ;;
esac