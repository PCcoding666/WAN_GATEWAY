#!/bin/bash

# Production Deployment Script for WAN Gateway
# Supports Google Cloud Run, Google Compute Engine, and other cloud platforms

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=""
SERVICE_NAME="wan-gateway"
REGION="us-central1"
IMAGE_TAG="latest"
DEPLOYMENT_TYPE=""
DASHSCOPE_API_KEY=""

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker."
    fi
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        warning "gcloud CLI not found. Installing..."
        curl https://sdk.cloud.google.com | bash
        exec -l $SHELL
    fi
    
    success "Prerequisites check completed"
}

# Function to setup configuration
setup_config() {
    log "Setting up deployment configuration..."
    
    # Get project ID if not set
    if [ -z "$PROJECT_ID" ]; then
        read -p "Enter your Google Cloud Project ID: " PROJECT_ID
        if [ -z "$PROJECT_ID" ]; then
            error "Project ID is required"
        fi
    fi
    
    # Get API key if not set
    if [ -z "$DASHSCOPE_API_KEY" ]; then
        read -s -p "Enter your DashScope API Key: " DASHSCOPE_API_KEY
        echo
        if [ -z "$DASHSCOPE_API_KEY" ]; then
            error "DashScope API Key is required"
        fi
    fi
    
    # Choose deployment type
    if [ -z "$DEPLOYMENT_TYPE" ]; then
        echo "Choose deployment type:"
        echo "1) Google Cloud Run (Serverless - Recommended)"
        echo "2) Google Compute Engine (VM-based)"
        echo "3) Other Cloud Provider"
        read -p "Enter choice (1-3): " choice
        
        case $choice in
            1) DEPLOYMENT_TYPE="cloudrun" ;;
            2) DEPLOYMENT_TYPE="compute" ;;
            3) DEPLOYMENT_TYPE="other" ;;
            *) error "Invalid choice" ;;
        esac
    fi
    
    success "Configuration setup completed"
}

# Function to authenticate with Google Cloud
setup_gcloud() {
    log "Setting up Google Cloud authentication..."
    
    # Check if already authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log "Authenticating with Google Cloud..."
        gcloud auth login
    fi
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    log "Enabling required Google Cloud APIs..."
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable compute.googleapis.com
    
    success "Google Cloud setup completed"
}

# Function to build Docker image
build_image() {
    log "Building Docker image..."
    
    # Test local build first
    if ! docker build -t $SERVICE_NAME . ; then
        error "Docker build failed. Please check your Dockerfile and dependencies."
    fi
    
    # Tag for Google Container Registry
    docker tag $SERVICE_NAME gcr.io/$PROJECT_ID/$SERVICE_NAME:$IMAGE_TAG
    
    success "Docker image built successfully"
}

# Function to push image to registry
push_image() {
    log "Pushing image to Google Container Registry..."
    
    # Configure Docker to use gcloud as credential helper
    gcloud auth configure-docker --quiet
    
    # Push image
    if ! docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:$IMAGE_TAG ; then
        error "Failed to push image to registry"
    fi
    
    success "Image pushed to registry successfully"
}

# Function to deploy to Cloud Run
deploy_cloudrun() {
    log "Deploying to Google Cloud Run..."
    
    gcloud run deploy $SERVICE_NAME \
        --image gcr.io/$PROJECT_ID/$SERVICE_NAME:$IMAGE_TAG \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --port 7860 \
        --set-env-vars DASHSCOPE_API_KEY=$DASHSCOPE_API_KEY \
        --memory 1Gi \
        --cpu 1 \
        --max-instances 10 \
        --min-instances 0 \
        --timeout 300
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
    
    success "Deployment to Cloud Run completed!"
    echo -e "${GREEN}🌐 Your application is available at: $SERVICE_URL${NC}"
}

# Function to deploy to Compute Engine
deploy_compute() {
    log "Deploying to Google Compute Engine..."
    
    VM_NAME="$SERVICE_NAME-vm"
    
    # Create VM instance if it doesn't exist
    if ! gcloud compute instances describe $VM_NAME --zone $REGION-a &> /dev/null; then
        log "Creating VM instance..."
        gcloud compute instances create $VM_NAME \
            --image-family ubuntu-2004-lts \
            --image-project ubuntu-os-cloud \
            --machine-type e2-medium \
            --zone $REGION-a \
            --tags http-server,https-server \
            --metadata startup-script='#!/bin/bash
apt-get update
apt-get install -y docker.io
systemctl start docker
systemctl enable docker
usermod -aG docker $USER'
    fi
    
    # Wait for VM to be ready
    log "Waiting for VM to be ready..."
    sleep 30
    
    # Deploy container to VM
    gcloud compute ssh $VM_NAME --zone $REGION-a --command "
        sudo docker pull gcr.io/$PROJECT_ID/$SERVICE_NAME:$IMAGE_TAG && \
        sudo docker stop $SERVICE_NAME || true && \
        sudo docker rm $SERVICE_NAME || true && \
        sudo docker run -d \
            -p 80:7860 \
            -e DASHSCOPE_API_KEY=$DASHSCOPE_API_KEY \
            --name $SERVICE_NAME \
            --restart unless-stopped \
            gcr.io/$PROJECT_ID/$SERVICE_NAME:$IMAGE_TAG
    "
    
    # Get external IP
    EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone $REGION-a --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
    
    success "Deployment to Compute Engine completed!"
    echo -e "${GREEN}🌐 Your application is available at: http://$EXTERNAL_IP${NC}"
}

# Function to test deployment
test_deployment() {
    log "Testing deployment..."
    
    case $DEPLOYMENT_TYPE in
        "cloudrun")
            SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
            ;;
        "compute")
            EXTERNAL_IP=$(gcloud compute instances describe $SERVICE_NAME-vm --zone $REGION-a --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
            SERVICE_URL="http://$EXTERNAL_IP"
            ;;
        *)
            warning "Skipping automated testing for other cloud providers"
            return
            ;;
    esac
    
    # Test with curl
    if command -v curl &> /dev/null; then
        log "Testing application accessibility..."
        if curl -s -o /dev/null -w "%{http_code}" $SERVICE_URL | grep -q "200\|302"; then
            success "Application is accessible and responding"
        else
            warning "Application may not be fully ready yet. Please check manually: $SERVICE_URL"
        fi
    fi
}

# Function to show deployment summary
show_summary() {
    echo
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}     DEPLOYMENT SUMMARY${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo -e "Project ID: ${BLUE}$PROJECT_ID${NC}"
    echo -e "Service Name: ${BLUE}$SERVICE_NAME${NC}"
    echo -e "Deployment Type: ${BLUE}$DEPLOYMENT_TYPE${NC}"
    echo -e "Region: ${BLUE}$REGION${NC}"
    echo -e "Image: ${BLUE}gcr.io/$PROJECT_ID/$SERVICE_NAME:$IMAGE_TAG${NC}"
    
    case $DEPLOYMENT_TYPE in
        "cloudrun")
            SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)" 2>/dev/null || echo "Check Cloud Console")
            echo -e "Service URL: ${BLUE}$SERVICE_URL${NC}"
            echo
            echo -e "${YELLOW}Management Commands:${NC}"
            echo "View logs: gcloud run services logs read $SERVICE_NAME --region $REGION"
            echo "Update service: gcloud run services replace-traffic $SERVICE_NAME --to-latest --region $REGION"
            echo "Delete service: gcloud run services delete $SERVICE_NAME --region $REGION"
            ;;
        "compute")
            EXTERNAL_IP=$(gcloud compute instances describe $SERVICE_NAME-vm --zone $REGION-a --format="value(networkInterfaces[0].accessConfigs[0].natIP)" 2>/dev/null || echo "Check Console")
            echo -e "VM External IP: ${BLUE}$EXTERNAL_IP${NC}"
            echo -e "Application URL: ${BLUE}http://$EXTERNAL_IP${NC}"
            echo
            echo -e "${YELLOW}Management Commands:${NC}"
            echo "SSH to VM: gcloud compute ssh $SERVICE_NAME-vm --zone $REGION-a"
            echo "View container logs: gcloud compute ssh $SERVICE_NAME-vm --zone $REGION-a --command 'sudo docker logs $SERVICE_NAME'"
            echo "Stop VM: gcloud compute instances stop $SERVICE_NAME-vm --zone $REGION-a"
            ;;
    esac
    
    echo -e "${GREEN}============================================${NC}"
}

# Main execution flow
main() {
    echo -e "${BLUE}"
    echo "██╗    ██╗ █████╗ ███╗   ██╗     ██████╗  █████╗ ████████╗███████╗██╗    ██╗ █████╗ ██╗   ██╗"
    echo "██║    ██║██╔══██╗████╗  ██║    ██╔════╝ ██╔══██╗╚══██╔══╝██╔════╝██║    ██║██╔══██╗╚██╗ ██╔╝"
    echo "██║ █╗ ██║███████║██╔██╗ ██║    ██║  ███╗███████║   ██║   █████╗  ██║ █╗ ██║███████║ ╚████╔╝ "
    echo "██║███╗██║██╔══██║██║╚██╗██║    ██║   ██║██╔══██║   ██║   ██╔══╝  ██║███╗██║██╔══██║  ╚██╔╝  "
    echo "╚███╔███╔╝██║  ██║██║ ╚████║    ╚██████╔╝██║  ██║   ██║   ███████╗╚███╔███╔╝██║  ██║   ██║   "
    echo " ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═══╝     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝   "
    echo -e "${NC}"
    echo -e "${BLUE}                          Production Cloud Deployment Script${NC}"
    echo
    
    check_prerequisites
    setup_config
    
    if [[ "$DEPLOYMENT_TYPE" == "cloudrun" || "$DEPLOYMENT_TYPE" == "compute" ]]; then
        setup_gcloud
    fi
    
    build_image
    
    if [[ "$DEPLOYMENT_TYPE" == "cloudrun" || "$DEPLOYMENT_TYPE" == "compute" ]]; then
        push_image
    fi
    
    case $DEPLOYMENT_TYPE in
        "cloudrun")
            deploy_cloudrun
            ;;
        "compute")
            deploy_compute
            ;;
        "other")
            success "Image built and ready for deployment to other cloud providers"
            echo "Image name: $SERVICE_NAME:$IMAGE_TAG"
            echo "For deployment instructions, see CLOUD_MIGRATION_SOP.md"
            ;;
    esac
    
    test_deployment
    show_summary
    
    success "🎉 Deployment completed successfully!"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --api-key)
            DASHSCOPE_API_KEY="$2"
            shift 2
            ;;
        --deployment-type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --project-id PROJECT_ID     Google Cloud Project ID"
            echo "  --api-key API_KEY           DashScope API Key"
            echo "  --deployment-type TYPE      Deployment type (cloudrun|compute|other)"
            echo "  --region REGION             Deployment region (default: us-central1)"
            echo "  --help                      Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Run main function
main