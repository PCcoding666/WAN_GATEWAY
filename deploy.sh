#!/bin/bash

# WAN Gateway Docker Deployment Script
# For Docker beginners - simplified version

set -e  # Exit on any error

APP_NAME="wan-gateway"
IMAGE_NAME="wan-gateway:latest"
CONTAINER_NAME="wan-gateway"
PORT="7860"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
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

# Check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        echo "Please create a .env file with your API key:"
        echo "DASHSCOPE_API_KEY=your_actual_api_key_here"
        echo ""
        echo "You can copy the example file:"
        echo "cp .env.example .env"
        echo "Then edit .env with your actual API key"
        exit 1
    fi
    
    if ! grep -q "DASHSCOPE_API_KEY=" .env || grep -q "your_api_key_here" .env; then
        print_warning "Please make sure to set your actual API key in the .env file"
        echo "Current .env content:"
        cat .env
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop first."
        exit 1
    fi
    print_status "Docker is running ✓"
}

# Build the Docker image
build_image() {
    print_status "Building Docker image..."
    if docker build -t $IMAGE_NAME .; then
        print_success "Docker image built successfully!"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Stop and remove existing container
stop_container() {
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        print_status "Stopping existing container..."
        docker stop $CONTAINER_NAME >/dev/null 2>&1 || true
    fi
    
    if docker ps -aq -f name=$CONTAINER_NAME | grep -q .; then
        print_status "Removing existing container..."
        docker rm $CONTAINER_NAME >/dev/null 2>&1 || true
    fi
}

# Start the container
start_container() {
    print_status "Starting new container..."
    
    # Create local directories if they don't exist
    mkdir -p downloads cache
    
    # Run the container
    if docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:$PORT \
        --env-file .env \
        -v "$(pwd)/downloads:/app/downloads" \
        -v "$(pwd)/cache:/app/cache" \
        --restart unless-stopped \
        $IMAGE_NAME; then
        
        print_success "Container started successfully!"
        print_status "Waiting for application to start..."
        
        # Wait for the application to be ready
        for i in {1..30}; do
            if curl -s http://localhost:$PORT >/dev/null 2>&1; then
                print_success "Application is ready!"
                print_success "🚀 Open your browser and go to: http://localhost:$PORT"
                return 0
            fi
            echo -n "."
            sleep 2
        done
        
        print_warning "Application may still be starting. Check logs with: $0 logs"
        print_status "Try opening: http://localhost:$PORT"
    else
        print_error "Failed to start container"
        exit 1
    fi
}

# Show container logs
show_logs() {
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        print_status "Showing container logs (Press Ctrl+C to exit):"
        docker logs -f $CONTAINER_NAME
    else
        print_error "Container $CONTAINER_NAME is not running"
        exit 1
    fi
}

# Show container status
show_status() {
    print_status "Container Status:"
    if docker ps -f name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q $CONTAINER_NAME; then
        docker ps -f name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        print_success "Container is running"
        print_status "Access the application at: http://localhost:$PORT"
    else
        print_warning "Container is not running"
    fi
}

# Stop the container
stop_deployment() {
    print_status "Stopping deployment..."
    stop_container
    print_success "Deployment stopped"
}

# Clean up everything
cleanup() {
    print_status "Cleaning up all resources..."
    stop_container
    
    if docker images -q $IMAGE_NAME | grep -q .; then
        print_status "Removing Docker image..."
        docker rmi $IMAGE_NAME >/dev/null 2>&1 || true
    fi
    
    print_success "Cleanup completed"
}

# Full deployment (build + run)
deploy() {
    print_status "🚀 Starting full deployment..."
    check_docker
    check_env_file
    stop_container
    build_image
    start_container
    print_success "🎉 Deployment completed successfully!"
}

# Usage help
show_help() {
    echo "WAN Gateway Docker Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy     Build and run the application (recommended for first-time setup)"
    echo "  build      Build Docker image only"
    echo "  start      Start the container (image must exist)"
    echo "  stop       Stop the running container"
    echo "  restart    Restart the container"
    echo "  logs       Show container logs"
    echo "  status     Show container status"
    echo "  cleanup    Remove container and image"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy    # Complete setup - build and run"
    echo "  $0 logs      # View application logs"
    echo "  $0 status    # Check if app is running"
    echo ""
    echo "First time setup:"
    echo "  1. Copy .env.example to .env"
    echo "  2. Edit .env with your API key"
    echo "  3. Run: $0 deploy"
    echo "  4. Open: http://localhost:7860"
}

# Main command handling
case "${1:-help}" in
    deploy)
        deploy
        ;;
    build)
        check_docker
        build_image
        ;;
    start)
        check_docker
        check_env_file
        start_container
        ;;
    stop)
        stop_deployment
        ;;
    restart)
        check_docker
        check_env_file
        stop_container
        start_container
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac