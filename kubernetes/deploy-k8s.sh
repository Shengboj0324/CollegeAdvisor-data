#!/bin/bash

# Kubernetes Deployment Script for CollegeAdvisor
set -e

echo "🚀 CollegeAdvisor Kubernetes Deployment"
echo "======================================="

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
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "kubectl cannot connect to cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Deploy namespace
deploy_namespace() {
    log_info "Creating namespace..."
    kubectl apply -f namespace.yaml
    log_success "Namespace created"
}

# Deploy ChromaDB
deploy_chromadb() {
    log_info "Deploying ChromaDB..."
    kubectl apply -f chromadb-deployment.yaml
    
    log_info "Waiting for ChromaDB to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/chromadb -n collegeadvisor
    log_success "ChromaDB deployed"
}

# Deploy Ollama
deploy_ollama() {
    log_info "Deploying Ollama..."
    kubectl apply -f ollama-deployment.yaml
    
    log_info "Waiting for Ollama to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/ollama -n collegeadvisor
    
    # Pull llama3 model
    log_info "Pulling llama3 model..."
    kubectl exec -n collegeadvisor deployment/ollama -- ollama pull llama3
    
    log_success "Ollama deployed"
}

# Deploy API
deploy_api() {
    log_info "Deploying API..."
    kubectl apply -f api-deployment.yaml
    
    log_info "Waiting for API to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/collegeadvisor-api -n collegeadvisor
    log_success "API deployed"
}

# Deploy ingress
deploy_ingress() {
    log_info "Deploying ingress..."
    kubectl apply -f ingress.yaml
    log_success "Ingress deployed"
}

# Run data ingestion
ingest_data() {
    log_info "Running data ingestion..."
    
    # Create a job for data ingestion
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: data-ingestion
  namespace: collegeadvisor
spec:
  template:
    spec:
      containers:
      - name: data-pipeline
        image: collegeadvisor/data:latest
        env:
        - name: CHROMA_HOST
          value: "chromadb-service"
        - name: CHROMA_PORT
          value: "8000"
        command: ["python", "simple_data_ingest.py"]
      restartPolicy: Never
  backoffLimit: 3
EOF
    
    kubectl wait --for=condition=complete --timeout=300s job/data-ingestion -n collegeadvisor
    log_success "Data ingestion complete"
}

# Show status
show_status() {
    echo ""
    log_info "Deployment Status"
    echo "=================="
    
    kubectl get all -n collegeadvisor
    
    echo ""
    log_info "Service Endpoints"
    echo "================="
    kubectl get services -n collegeadvisor
    
    echo ""
    log_info "Ingress Information"
    echo "==================="
    kubectl get ingress -n collegeadvisor
}

# Main deployment flow
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            deploy_namespace
            deploy_chromadb
            deploy_ollama
            deploy_api
            deploy_ingress
            ingest_data
            show_status
            ;;
        "update")
            log_info "Updating deployment..."
            kubectl apply -f .
            show_status
            ;;
        "delete")
            log_warning "Deleting deployment..."
            kubectl delete namespace collegeadvisor
            log_success "Deployment deleted"
            ;;
        "status")
            show_status
            ;;
        "logs")
            kubectl logs -f deployment/${2:-collegeadvisor-api} -n collegeadvisor
            ;;
        *)
            echo "Usage: $0 {deploy|update|delete|status|logs [deployment]}"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
