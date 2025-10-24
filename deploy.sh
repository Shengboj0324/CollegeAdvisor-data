#!/bin/bash

# CollegeAdvisor Production Deployment Script
set -e

echo "🚀 CollegeAdvisor Production Deployment"
echo "========================================"

# Configuration
ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="collegeadvisor"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Prepare environment
prepare_environment() {
    log_info "Preparing environment..."
    
    # Create necessary directories
    mkdir -p chroma_data
    mkdir -p ssl
    mkdir -p logs
    
    # Set permissions
    chmod 755 chroma_data
    chmod 755 logs
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        log_warning ".env file not found, creating default..."
        cat > .env << EOF
# CollegeAdvisor Environment Configuration
ENVIRONMENT=${ENVIRONMENT}
CHROMA_HOST=chromadb
CHROMA_PORT=8000
OLLAMA_HOST=ollama
OLLAMA_PORT=11434
API_HOST=0.0.0.0
API_PORT=8080
EOF
    fi
    
    log_success "Environment prepared"
}

# Pull Ollama model
setup_ollama_model() {
    log_info "Setting up Ollama model..."

    # Start Ollama service temporarily to pull model
    docker-compose up -d ollama

    # Wait for Ollama to be ready
    log_info "Waiting for Ollama to be ready..."
    sleep 30

    # Check if fine-tuned model exists
    FINETUNED_MODEL="college-advisor:latest"
    if docker-compose exec ollama ollama list | grep -q "$FINETUNED_MODEL"; then
        log_success "Fine-tuned model '$FINETUNED_MODEL' found"
    else
        log_warning "Fine-tuned model not found, using base llama3"
        log_info "To use fine-tuned model, run: ./run_ollama_finetuning_pipeline.sh"

        # Pull base llama3 model as fallback
        docker-compose exec ollama ollama pull llama3
    fi

    log_success "Ollama model setup complete"
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Build and start all services
    docker-compose build
    docker-compose up -d
    
    log_success "Services deployed"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    # Wait for ChromaDB
    log_info "Waiting for ChromaDB..."
    timeout 120 bash -c 'until curl -f http://localhost:8000/api/v2/heartbeat; do sleep 5; done'
    
    # Wait for API
    log_info "Waiting for API..."
    timeout 120 bash -c 'until curl -f http://localhost:8080/health; do sleep 5; done'
    
    log_success "All services are healthy"
}

# Run data ingestion
ingest_data() {
    log_info "Running data ingestion..."
    
    # Run data pipeline
    docker-compose run --rm data-pipeline python simple_data_ingest.py
    
    log_success "Data ingestion complete"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Test API endpoints
    log_info "Testing API endpoints..."
    
    # Health check
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        return 1
    fi
    
    # Test recommendation endpoint
    if curl -X POST http://localhost:8080/api/v1/recommendations \
        -H "Content-Type: application/json" \
        -d '{"query": "test query", "max_results": 1}' > /dev/null 2>&1; then
        log_success "Recommendation endpoint working"
    else
        log_error "Recommendation endpoint failed"
        return 1
    fi
    
    log_success "Deployment verification complete"
}

# Show deployment status
show_status() {
    echo ""
    log_info "Deployment Status"
    echo "=================="
    
    docker-compose ps
    
    echo ""
    log_info "Available Endpoints"
    echo "==================="
    echo "🌐 API Server: http://localhost:8080"
    echo "📚 API Documentation: http://localhost:8080/docs"
    echo "🏥 Health Check: http://localhost:8080/health"
    echo "📊 Prometheus: http://localhost:9090"
    echo "📈 Grafana: http://localhost:3000 (admin/admin)"
    echo "🔍 ChromaDB: http://localhost:8000"
    
    echo ""
    log_info "Useful Commands"
    echo "==============="
    echo "View logs: docker-compose logs -f [service]"
    echo "Scale API: docker-compose up -d --scale api=3"
    echo "Stop all: docker-compose down"
    echo "Update: ./deploy.sh"
}

# Main deployment flow
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            prepare_environment
            deploy_services
            setup_ollama_model
            wait_for_services
            ingest_data
            verify_deployment
            show_status
            ;;
        "update")
            log_info "Updating deployment..."
            docker-compose pull
            docker-compose build
            docker-compose up -d
            wait_for_services
            verify_deployment
            show_status
            ;;
        "stop")
            log_info "Stopping services..."
            docker-compose down
            log_success "Services stopped"
            ;;
        "restart")
            log_info "Restarting services..."
            docker-compose restart
            wait_for_services
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            docker-compose logs -f ${2:-}
            ;;
        *)
            echo "Usage: $0 {deploy|update|stop|restart|status|logs [service]}"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
