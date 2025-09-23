# 🚀 CollegeAdvisor Integration - Next Steps

Based on your current setup and the integration plan, here are the concrete next steps to implement the RAG system.

## ✅ Current Status

**Ready Components:**
- ✅ ChromaDB client implementation with proper schema
- ✅ Embedding service (sentence-transformers)
- ✅ PyTorch, Transformers, Datasets
- ✅ Ollama available
- ✅ Unsloth installed (CPU limitations noted)
- ✅ Training infrastructure (CPU-compatible)

**Needs Setup:**
- ❌ ChromaDB server not running
- ⚠️ No data in ChromaDB yet
- ⚠️ No fine-tuned model yet

## 🎯 Step-by-Step Implementation

### **Step 1: Start ChromaDB Server**

```bash
# Create persistent directory
mkdir -p ./chroma_data

# Start ChromaDB server
chroma run --host 0.0.0.0 --port 8000 --persist_directory ./chroma_data
```

**Verification:**
```bash
curl http://localhost:8000/api/v1/heartbeat
# Should return: {"nanosecond heartbeat": <timestamp>}
```

### **Step 2: Ingest Initial Data**

You have a complete ingestion pipeline. Let's use it:

```bash
# Check if you have sample data
ls data/raw/

# If you have CSV data, run ingestion
python -m college_advisor_data.cli ingest \
  --source data/raw/colleges.csv \
  --format csv \
  --type university

# Or create sample data and ingest
python scripts/create_sample_data.py
python -m college_advisor_data.cli ingest \
  --source data/sample/colleges.json \
  --format json \
  --type university
```

### **Step 3: Verify ChromaDB Population**

```python
from college_advisor_data.storage.chroma_client import ChromaDBClient

client = ChromaDBClient()
collection = client.get_or_create_collection()
print(f"Collection has {collection.count()} documents")

# Test query
results = client.query("computer science programs", n_results=3)
print("Sample results:", results)
```

### **Step 4: Create API Contract Implementation**

Based on your architecture, create the API contract:

```python
# File: contracts/api_contract.py
from typing import List, Dict, Any
from pydantic import BaseModel

class RecommendationRequest(BaseModel):
    query: str
    profile: Dict[str, Any] = {}
    n_results: int = 5

class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    sources: List[str]
    collection_version: str
    model_version: str

# Environment contract
CHROMA_COLLECTION = "college_advisor@v1.0"
MODEL_TAG = "llama3:base"  # Will upgrade to fine-tuned later
```

### **Step 5: Implement RAG Endpoint Logic**

```python
# File: rag_implementation.py
from college_advisor_data.storage.chroma_client import ChromaDBClient
import requests
import json

class RAGService:
    def __init__(self):
        self.chroma_client = ChromaDBClient()
        self.ollama_host = "http://localhost:11434"
        
    def get_recommendations(self, query: str, profile: Dict = None) -> Dict:
        # Step 1: Retrieve relevant documents
        filters = self._build_filters(profile) if profile else None
        results = self.chroma_client.query(
            query_text=query,
            n_results=8,
            where=filters
        )
        
        # Step 2: Build grounded prompt
        context = self._format_context(results)
        prompt = self._build_prompt(query, context)
        
        # Step 3: Generate response
        response = self._call_ollama(prompt)
        
        # Step 4: Format response
        return {
            "recommendations": self._parse_response(response),
            "sources": [r.get("doc_id") for r in results],
            "collection_version": "college_advisor@v1.0",
            "model_version": "llama3:base"
        }
    
    def _build_filters(self, profile: Dict) -> Dict:
        filters = {}
        if profile.get("gpa_range"):
            filters["gpa_band"] = profile["gpa_range"]
        if profile.get("location"):
            filters["location"] = {"$contains": profile["location"]}
        return filters
    
    def _format_context(self, results: List[Dict]) -> str:
        context_parts = []
        for i, result in enumerate(results[:5]):  # Top 5 results
            doc = result.get("documents", [""])[0]
            meta = result.get("metadatas", [{}])[0]
            school = meta.get("school", "Unknown")
            context_parts.append(f"{i+1}. {school}: {doc}")
        return "\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str) -> str:
        return f"""You are an expert college advisor. Based on the following information about colleges and programs, provide helpful recommendations.

CONTEXT:
{context}

QUESTION: {query}

Provide a helpful response with specific recommendations based on the context above. Include school names and relevant details."""

    def _call_ollama(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": "llama3",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2}
                },
                timeout=30
            )
            return response.json().get("response", "")
        except Exception as e:
            return f"Error generating response: {e}"
    
    def _parse_response(self, response: str) -> List[Dict]:
        # For now, return as single recommendation
        # Later: parse structured JSON response
        return [{"text": response, "confidence": 0.8}]
```

### **Step 6: Test End-to-End RAG**

```python
# File: test_rag.py
from rag_implementation import RAGService

def test_rag_system():
    rag = RAGService()
    
    # Test query
    result = rag.get_recommendations(
        query="What are some good computer science programs?",
        profile={"gpa_range": "3.5-4.0"}
    )
    
    print("RAG Response:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_rag_system()
```

### **Step 7: Model Fine-tuning (Optional)**

Since you have unsloth installed but CUDA limitations:

```bash
# For CPU training (development)
python ai_training/run_sft_cpu.py \
  --data data/training/college_qa.json \
  --output models/college_advisor_cpu \
  --epochs 1 \
  --batch-size 1

# For GPU training (production - when available)
python ai_training/run_sft.py \
  --data data/training/college_qa.json \
  --output models/college_advisor_gpu \
  --epochs 3 \
  --batch-size 4
```

## 🔧 Environment Configuration

Create/update your `.env` file:

```bash
# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=college_advisor

# Ollama
OLLAMA_HOST=http://localhost:11434

# Embedding (locked for MVP)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_PROVIDER=sentence_transformers

# API Contract
COLLECTION_VERSION=college_advisor@v1.0
MODEL_VERSION=llama3:base
```

## 📋 Verification Checklist

- [ ] ChromaDB server running on port 8000
- [ ] Data ingested into ChromaDB collection
- [ ] Ollama running with llama3 model
- [ ] RAG service can query ChromaDB
- [ ] RAG service can call Ollama
- [ ] End-to-end test returns recommendations

## 🚀 Ready for API Integration

Once these steps are complete, you'll have:

1. **Artifact A**: ChromaDB collection `college_advisor@v1.0` with embedded data
2. **Artifact B**: Ollama model `llama3:base` (upgradeable to fine-tuned)
3. **RAG Service**: Complete retrieval + generation pipeline
4. **API Contract**: Clear interface for the API repo to consume

The API repo can then implement the `/recommendations` endpoint using your RAG service as a dependency.

## 🎯 Next Phase: API Integration

After completing these steps, the API repo should:

1. Import your RAG service
2. Implement FastAPI endpoint
3. Add authentication, rate limiting, logging
4. Deploy as stateless service
5. Point iOS app to the API

This follows the "Data writes, API reads" principle perfectly! 🎉
