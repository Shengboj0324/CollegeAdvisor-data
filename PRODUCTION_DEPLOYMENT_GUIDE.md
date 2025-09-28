# 🚀 CollegeAdvisor Production Deployment Guide

## 📋 Overview

This guide provides comprehensive instructions for deploying the CollegeAdvisor RAG system to production environments using Docker Compose and Kubernetes.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   API Service   │    │   ChromaDB      │
│  Load Balancer  │───▶│   (FastAPI)     │───▶│   Vector DB     │
│   Rate Limiting │    │   3 Replicas    │    │   Persistent    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │     Ollama      │              │
         └──────────────│   LLM Service   │──────────────┘
                        │   GPU Support   │
                        └─────────────────┘
```

## 🐳 Docker Compose Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 50GB+ disk space

### Quick Start
```bash
# Clone and navigate to project
cd CollegeAdvisor-data

# Deploy with one command
./deploy.sh deploy

# Check status
./deploy.sh status
```

### Manual Deployment Steps

1. **Prepare Environment**
```bash
# Create directories
mkdir -p chroma_data ssl logs

# Set permissions
chmod 755 chroma_data logs

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

2. **Deploy Services**
```bash
# Build and start all services
docker-compose build
docker-compose up -d

# Check service health
docker-compose ps
```

3. **Setup Ollama Model**
```bash
# Pull llama3 model
docker-compose exec ollama ollama pull llama3
```

4. **Ingest Data**
```bash
# Run data pipeline
docker-compose run --rm data-pipeline python simple_data_ingest.py
```

5. **Verify Deployment**
```bash
# Test API endpoints
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/recommendations/search?q=computer%20science
```

### Service Configuration

#### Core Services
- **API**: FastAPI application (port 8080)
- **ChromaDB**: Vector database (port 8000)
- **Ollama**: LLM service (port 11434)
- **Nginx**: Reverse proxy (port 80/443)

#### Optional Services
- **Redis**: Caching layer (port 6379)
- **Prometheus**: Monitoring (port 9090)
- **Grafana**: Dashboards (port 3000)

### Environment Variables
```bash
# Core Configuration
ENVIRONMENT=production
CHROMA_HOST=chromadb
CHROMA_PORT=8000
OLLAMA_HOST=ollama
OLLAMA_PORT=11434
API_HOST=0.0.0.0
API_PORT=8080

# Security (add for production)
API_SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
ALLOWED_ORIGINS=https://yourdomain.com
```

## ☸️ Kubernetes Deployment

### Prerequisites
- Kubernetes 1.20+
- kubectl configured
- Ingress controller (nginx)
- Persistent volume support

### Quick Start
```bash
# Navigate to kubernetes directory
cd kubernetes

# Deploy to cluster
./deploy-k8s.sh deploy

# Check status
./deploy-k8s.sh status
```

### Manual Kubernetes Steps

1. **Create Namespace**
```bash
kubectl apply -f namespace.yaml
```

2. **Deploy ChromaDB**
```bash
kubectl apply -f chromadb-deployment.yaml
kubectl wait --for=condition=available deployment/chromadb -n collegeadvisor
```

3. **Deploy Ollama**
```bash
kubectl apply -f ollama-deployment.yaml
kubectl wait --for=condition=available deployment/ollama -n collegeadvisor

# Pull model
kubectl exec -n collegeadvisor deployment/ollama -- ollama pull llama3
```

4. **Deploy API**
```bash
kubectl apply -f api-deployment.yaml
kubectl wait --for=condition=available deployment/collegeadvisor-api -n collegeadvisor
```

5. **Setup Ingress**
```bash
kubectl apply -f ingress.yaml
```

### Scaling Configuration

#### Horizontal Pod Autoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: collegeadvisor-api-hpa
spec:
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 70
```

#### Resource Limits
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

## 🔒 Security Configuration

### SSL/TLS Setup
```bash
# Generate SSL certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem

# Or use Let's Encrypt with cert-manager
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.8.0/cert-manager.yaml
```

### Rate Limiting
```nginx
# In nginx.conf
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=search_limit:10m rate=5r/s;
```

### API Security
```python
# Add to API configuration
CORS_ORIGINS = ["https://yourdomain.com"]
API_KEY_REQUIRED = True
JWT_EXPIRATION = 3600
```

## 📊 Monitoring & Observability

### Prometheus Metrics
- API response times
- Request rates
- Error rates
- Resource utilization

### Grafana Dashboards
- System overview
- API performance
- ChromaDB metrics
- Ollama performance

### Health Checks
```bash
# API health
curl http://localhost:8080/health

# ChromaDB health
curl http://localhost:8000/api/v2/heartbeat

# Ollama health
curl http://localhost:11434/api/tags
```

### Log Aggregation
```bash
# View logs
docker-compose logs -f api
kubectl logs -f deployment/collegeadvisor-api -n collegeadvisor

# Centralized logging with ELK stack
# Add filebeat, logstash, elasticsearch
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build and Deploy
      run: |
        docker build -t collegeadvisor/api:${{ github.sha }} .
        docker push collegeadvisor/api:${{ github.sha }}
        kubectl set image deployment/collegeadvisor-api api=collegeadvisor/api:${{ github.sha }}
```

## 🚀 Performance Optimization

### Caching Strategy
```python
# Redis caching for API responses
@cache(expire=300)  # 5 minutes
def get_recommendations(query, profile):
    # Implementation
```

### Database Optimization
```python
# ChromaDB connection pooling
client = chromadb.HttpClient(
    host="chromadb",
    port=8000,
    settings=Settings(
        chroma_client_pool_size=10
    )
)
```

### Load Balancing
```yaml
# Multiple API replicas
replicas: 3

# Session affinity for stateful operations
sessionAffinity: ClientIP
```

## 🔧 Troubleshooting

### Common Issues

1. **ChromaDB Connection Failed**
```bash
# Check service status
docker-compose ps chromadb
kubectl get pods -n collegeadvisor

# Check logs
docker-compose logs chromadb
kubectl logs deployment/chromadb -n collegeadvisor
```

2. **Ollama Model Not Found**
```bash
# Pull model manually
docker-compose exec ollama ollama pull llama3
kubectl exec deployment/ollama -n collegeadvisor -- ollama pull llama3
```

3. **API High Response Times**
```bash
# Scale API replicas
docker-compose up -d --scale api=3
kubectl scale deployment collegeadvisor-api --replicas=5 -n collegeadvisor
```

### Performance Tuning
```bash
# Increase worker processes
uvicorn api.main:app --workers 4

# Optimize ChromaDB
export CHROMA_SERVER_CORS_ALLOW_ORIGINS="*"
export CHROMA_SERVER_GRPC_PORT=50051
```

## 📈 Scaling Guidelines

### Vertical Scaling
- **API**: 2-4 CPU cores, 4-8GB RAM per replica
- **ChromaDB**: 4-8 CPU cores, 8-16GB RAM
- **Ollama**: 8+ CPU cores, 16-32GB RAM, GPU recommended

### Horizontal Scaling
- **API**: 2-10 replicas based on load
- **ChromaDB**: Single instance (clustering in enterprise)
- **Ollama**: Single instance per model

### Storage Requirements
- **ChromaDB**: 10GB+ for vector storage
- **Ollama**: 20GB+ for model storage
- **Logs**: 5GB+ for log retention

## 🎯 Production Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database backups configured
- [ ] Monitoring setup complete
- [ ] Load testing performed

### Post-Deployment
- [ ] Health checks passing
- [ ] API endpoints responding
- [ ] Data ingestion successful
- [ ] Monitoring alerts configured
- [ ] Documentation updated

### Maintenance
- [ ] Regular backups scheduled
- [ ] Security updates applied
- [ ] Performance monitoring active
- [ ] Log rotation configured
- [ ] Disaster recovery tested

---

## 🎉 Success Metrics

### Performance Targets
- **API Response Time**: < 10 seconds for recommendations
- **Availability**: 99.9% uptime
- **Throughput**: 100+ requests/minute
- **Error Rate**: < 1%

### Monitoring Alerts
- High response times (> 15 seconds)
- Error rate spike (> 5%)
- Resource utilization (> 80%)
- Service unavailability

**🚀 Your CollegeAdvisor system is now production-ready!**
