# 🚀 CollegeAdvisor-data Production Deployment Guide

This guide provides comprehensive instructions for deploying the CollegeAdvisor data pipeline and AI training system in production.

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or macOS
- **Python**: 3.9+
- **Memory**: 16GB+ RAM (32GB+ for model training)
- **Storage**: 100GB+ available space
- **GPU**: NVIDIA GPU with 8GB+ VRAM (for model training)

### Required Services
- **ChromaDB**: Vector database for embeddings
- **S3-compatible storage**: For model artifacts (AWS S3, MinIO, etc.)
- **Monitoring**: Optional (Prometheus, Grafana)

## 🔧 Installation

### 1. Clone and Setup Environment

```bash
# Clone repository
git clone <repository-url>
cd CollegeAdvisor-data

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install additional production dependencies
pip install prefect boto3 ragas unsloth
```

### 2. Environment Configuration

Create `.env` file with production settings:

```bash
# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_CLOUD_HOST=  # Optional: ChromaDB cloud endpoint
CHROMA_CLOUD_API_KEY=  # Optional: ChromaDB cloud API key

# AWS S3 Configuration (for model storage)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=collegeadvisor-models

# Embedding Configuration (LOCKED)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_PROVIDER=sentence_transformers

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/collegeadvisor.log

# Production Settings
ENVIRONMENT=production
BATCH_SIZE=100
MAX_WORKERS=4
```

### 3. Start ChromaDB

#### Option A: Docker (Recommended)
```bash
# Start ChromaDB with persistence
docker run -d \
  --name chroma-production \
  -p 8000:8000 \
  -v chroma-data:/chroma/chroma \
  chromadb/chroma:latest

# Verify connection
curl http://localhost:8000/api/v1/heartbeat
```

#### Option B: Local Installation
```bash
# Install ChromaDB
pip install chromadb

# Start ChromaDB server
chroma run --host 0.0.0.0 --port 8000 --path ./chroma_data
```

## 📊 Data Pipeline Setup

### 1. Initialize Database Schema

```bash
# Create ChromaDB collection with standardized schema
python -m college_advisor_data.cli init

# Verify schema
python -m college_advisor_data.cli health
```

### 2. Initial Data Ingestion

```bash
# Prepare seed data
mkdir -p data/seed
# Copy your CSV/JSON data files to data/seed/

# Run initial ingestion
python -m college_advisor_data.cli ingest data/seed/colleges.csv --doc-type college

# Or use the automated script
./scripts/ingest.sh data/seed/colleges.csv --doc-type college --batch-size 100
```

### 3. Verify Data Quality

```bash
# Run data quality checks
python -m college_advisor_data.cli evaluate

# Check collection statistics
python -c "
from college_advisor_data.storage.chroma_client import ChromaDBClient
client = ChromaDBClient()
stats = client.stats()
print(f'Documents: {stats[\"total_documents\"]}')
print(f'Schema compliance: {stats[\"schema_compliance\"]:.2%}')
"
```

## 🤖 AI Training Setup

### 1. Prepare Training Data

```bash
# Generate training datasets
python -m ai_training.training_pipeline generate

# Verify training data
ls -la data/training/
```

### 2. Train Initial Model

```bash
# Train Llama-3-8B with QLoRA
python -m ai_training.run_sft \
  --data data/training/training_set.jsonl \
  --output models/llama3-sft-initial \
  --epochs 3 \
  --batch-size 2

# Export to Ollama format
python -m ai_training.export_to_ollama \
  --model models/llama3-sft-initial \
  --output exports/initial \
  --name collegeadvisor-llama3-initial
```

### 3. Setup Ollama (for inference)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Import your trained model
ollama create collegeadvisor-llama3 -f exports/initial/Modelfile

# Test inference
ollama run collegeadvisor-llama3 "What are the admission requirements for Stanford?"
```

## ⚙️ Production Orchestration

### Option A: Prefect (Recommended)

```bash
# Install Prefect
pip install prefect

# Start Prefect server
prefect server start

# Deploy workflows
python orchestration/prefect_flows.py

# Start worker
prefect worker start --pool default-agent-pool
```

### Option B: Cron Jobs (Simple)

```bash
# Generate crontab entries
python orchestration/cron_scheduler.py generate-crontab

# Install cron jobs
crontab orchestration/crontab.txt

# Verify cron jobs
crontab -l
```

## 📈 Monitoring and Maintenance

### 1. Health Monitoring

```bash
# Setup health check endpoint
python -m college_advisor_data.cli health

# Monitor logs
tail -f logs/collegeadvisor.log

# Check ChromaDB status
curl http://localhost:8000/api/v1/heartbeat
```

### 2. Data Quality Monitoring

```bash
# Daily quality checks
python -m college_advisor_data.cli evaluate

# Monitor schema compliance
python -c "
from college_advisor_data.storage.chroma_client import ChromaDBClient
client = ChromaDBClient()
stats = client.stats()
if stats['schema_compliance'] < 0.95:
    print('WARNING: Schema compliance below 95%')
"
```

### 3. Model Performance Monitoring

```bash
# Weekly model evaluation
python -m ai_training.eval_rag \
  --eval-data data/evaluation/eval_set.jsonl \
  --model collegeadvisor-llama3 \
  --output evaluation_results \
  --baseline evaluation_results/baseline.json
```

## 🔄 Production Workflows

### Daily Data Refresh (02:00 UTC)
1. Health checks (ChromaDB, embedder)
2. Refresh data collectors
3. Preprocess new data
4. Upsert to ChromaDB
5. Data quality monitoring
6. Alert on failures

### Weekly Model Training (03:00 UTC Sunday)
1. Generate evaluation dataset
2. Evaluate current model performance
3. Train new model if needed
4. Evaluate new model
5. Export to Ollama if metrics improve by ≥5%
6. Update baseline metrics

## 🚨 Troubleshooting

### Common Issues

#### ChromaDB Connection Failed
```bash
# Check if ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# Restart ChromaDB
docker restart chroma-production

# Check logs
docker logs chroma-production
```

#### Embedding Generation Slow
```bash
# Check GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Monitor GPU usage
nvidia-smi

# Reduce batch size if memory issues
export BATCH_SIZE=50
```

#### Model Training Out of Memory
```bash
# Use gradient checkpointing
export GRADIENT_CHECKPOINTING=true

# Reduce batch size
export TRAIN_BATCH_SIZE=1

# Use CPU offloading
export CPU_OFFLOAD=true
```

### Log Locations
- **Application logs**: `logs/collegeadvisor.log`
- **Orchestration logs**: `logs/orchestration/`
- **Workflow results**: `logs/workflow_results/`
- **Training logs**: `logs/training/`

## 🔐 Security Considerations

### 1. API Keys and Secrets
- Store sensitive credentials in environment variables
- Use AWS IAM roles for S3 access
- Rotate API keys regularly

### 2. Network Security
- Restrict ChromaDB access to internal network
- Use HTTPS for all external communications
- Implement proper firewall rules

### 3. Data Privacy
- Ensure compliance with data protection regulations
- Implement data retention policies
- Secure model artifacts in S3

## 📊 Performance Optimization

### 1. ChromaDB Optimization
- Use SSD storage for ChromaDB data
- Monitor collection size and performance
- Consider sharding for large datasets

### 2. Embedding Performance
- Use GPU acceleration when available
- Batch embedding generation
- Cache embeddings when possible

### 3. Model Training Optimization
- Use mixed precision training (fp16/bf16)
- Implement gradient accumulation
- Use efficient attention mechanisms

## 🎯 Success Metrics

### Data Pipeline Health
- **Uptime**: >99.5%
- **Data freshness**: <24 hours
- **Schema compliance**: >95%
- **Processing latency**: <1 hour

### AI Model Performance
- **Faithfulness**: >0.8
- **Answer correctness**: >0.75
- **Hit@5**: >0.9
- **Response time**: <2 seconds

### System Performance
- **Memory usage**: <80%
- **Disk usage**: <85%
- **CPU usage**: <70% (average)
- **GPU utilization**: >80% (during training)

---

## 🆘 Support

For production support:
1. Check logs in `logs/` directory
2. Run health checks: `python -m college_advisor_data.cli health`
3. Monitor system resources
4. Review workflow results in `logs/workflow_results/`

**The CollegeAdvisor-data system is now production-ready! 🚀**
