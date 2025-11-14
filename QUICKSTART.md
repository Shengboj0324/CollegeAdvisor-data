# Quick Start Guide

**Get the CollegeAdvisor RAG System Running in 5 Minutes**

---

## Prerequisites

- Python 3.9+
- 8GB RAM minimum
- Ollama installed
- TinyLlama model downloaded

---

## Installation

### 1. Install Ollama

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Download TinyLlama

```bash
ollama pull tinyllama
```

Verify:
```bash
ollama list
# Should show: tinyllama:latest
```

---

## Local Testing

### 1. Extract Production Artifacts

```bash
cd /Users/jiangshengbo/Desktop/CollegeAdvisor-api

# Extract tarball
tar -xzf collegeadvisor-v1.0.0.tar.gz

# Verify extraction
ls -la chroma/ rag_system/
```

### 2. Start Ollama

```bash
ollama serve &
```

### 3. Test RAG System (Standalone)

```bash
cd /Users/jiangshengbo/Desktop/CollegeAdvisor-api

python -c "
import sys
sys.path.append('.')
from rag_system.production_rag import ProductionRAG

print('Initializing RAG system...')
rag = ProductionRAG()

print('Testing query...')
result = rag.query('What are UC Berkeley CS transfer requirements?')

print(f'\n✅ Answer length: {len(result.answer)} characters')
print(f'✅ Citations: {len(result.citations)}')
print(f'\nFirst 500 chars:\n{result.answer[:500]}')
"
```

**Expected Output:**
```
Initializing RAG system...
✅ Loaded 5 ChromaDB collections
✅ Loaded 1,910 documents
Testing query...
✅ Answer length: 1,234 characters
✅ Citations: 5
```

### 4. Start API Server

```bash
cd /Users/jiangshengbo/Desktop/CollegeAdvisor-api
uvicorn app.main:app --reload
```

### 5. Test API Endpoint

```bash
curl -X POST http://localhost:8000/api/mobile/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are UC Berkeley CS transfer requirements?",
    "limit": 10
  }'
```

**Expected Response:**
```json
{
  "recommendations": [
    {
      "type": "answer",
      "content": "## UC Berkeley CS Transfer Requirements...",
      "citations": [...],
      "confidence": 0.95
    }
  ]
}
```

---

## Cloud Deployment

### 1. Set Google Cloud Project

```bash
export PROJECT_ID="your-google-cloud-project-id"
gcloud config set project $PROJECT_ID
```

### 2. Build Docker Image

```bash
cd /Users/jiangshengbo/Desktop/CollegeAdvisor-api

gcloud builds submit --tag gcr.io/$PROJECT_ID/collegeadvisor-api
```

### 3. Deploy to Cloud Run

```bash
gcloud run deploy collegeadvisor-api \
  --image gcr.io/$PROJECT_ID/collegeadvisor-api \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --allow-unauthenticated
```

### 4. Get Cloud Run URL

```bash
gcloud run services describe collegeadvisor-api \
  --region us-central1 \
  --format 'value(status.url)'
```

### 5. Test Cloud Run Endpoint

```bash
export CLOUD_RUN_URL="https://collegeadvisor-api-[hash]-uc.a.run.app"

curl -X POST $CLOUD_RUN_URL/api/mobile/recommendations \
  -H "Content-Type: application/json" \
  -d '{"query": "What are UC Berkeley CS transfer requirements?"}'
```

---

## Troubleshooting

### Issue: Ollama not found
```bash
# Install Ollama
brew install ollama  # macOS
# or
curl -fsSL https://ollama.com/install.sh | sh  # Linux
```

### Issue: TinyLlama not downloaded
```bash
ollama pull tinyllama
ollama list
```

### Issue: ChromaDB collections not found
```bash
# Re-extract tarball
cd /Users/jiangshengbo/Desktop/CollegeAdvisor-api
tar -xzf collegeadvisor-v1.0.0.tar.gz

# Verify
python -c "import chromadb; client = chromadb.PersistentClient(path='./chroma/chroma_data'); print(len(client.list_collections()))"
# Should print: 5
```

### Issue: API returns 404
```bash
# Check if server is running
ps aux | grep uvicorn

# Restart server
cd /Users/jiangshengbo/Desktop/CollegeAdvisor-api
uvicorn app.main:app --reload
```

---

## Next Steps

1. **Read Architecture**: See `ARCHITECTURE.md` for technical details
2. **Review API**: See `API_REFERENCE.md` for endpoint documentation
3. **Check Evaluation**: See `EVALUATION.md` for performance metrics
4. **Deploy Production**: See `DEPLOYMENT.md` for full deployment guide

---

## Key Commands Reference

```bash
# Start Ollama
ollama serve &

# Start API (local)
uvicorn app.main:app --reload

# Test endpoint (local)
curl -X POST http://localhost:8000/api/mobile/recommendations \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question here"}'

# Deploy to Cloud Run
gcloud run deploy collegeadvisor-api \
  --image gcr.io/$PROJECT_ID/collegeadvisor-api \
  --memory 4Gi --cpu 2 --region us-central1
```

---

**Version**: 1.0.0  
**Status**: Production Ready ✅  
**Support**: See other .md files for detailed documentation

