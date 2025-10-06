# CollegeAdvisor-api Integration Instructions

## Overview

This document provides clear instructions for integrating the fine-tuned CollegeAdvisor model with the CollegeAdvisor-api repository.

## Prerequisites

Before proceeding, ensure you have completed in CollegeAdvisor-data repository:
- ✅ Data collection completed
- ✅ ChromaDB collections populated
- ✅ Model fine-tuned (collegeadvisor model created)
- ✅ Ollama serving the fine-tuned model

## What You Need to Do in CollegeAdvisor-api

### 1. Environment Configuration

**File to modify:** `.env` or `.env.production`

Add or update these environment variables:

```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=collegeadvisor
OLLAMA_TIMEOUT=30

# ChromaDB Configuration (if API queries ChromaDB directly)
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=college_advisor

# Embedding Configuration (must match data repo)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_PROVIDER=sentence_transformers
```

### 2. Verify Ollama is Running

Before starting the API, ensure Ollama is serving:

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Verify collegeadvisor model exists
ollama list | grep collegeadvisor
```

**Expected output:**
```
collegeadvisor:latest    ...    ...    ...
```

If model is not listed:
```bash
# In CollegeAdvisor-data repository
cd data/finetuning_prep/training_datasets
ollama create collegeadvisor -f Modelfile
```

### 3. Update API Code (If Needed)

#### Option A: If API Already Uses Ollama

No code changes needed! Just update the environment variable:
```bash
OLLAMA_MODEL=collegeadvisor
```

The API will automatically use the fine-tuned model.

#### Option B: If API Needs Ollama Integration

Add Ollama client to your API code:

**File:** `app/core/llm/ollama_client.py` (or similar)

```python
import os
import ollama
from typing import List, Dict, Any

class OllamaClient:
    def __init__(self):
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "collegeadvisor")
        self.client = ollama.Client(host=self.host)
    
    def chat(self, message: str, context: List[Dict] = None) -> str:
        """
        Send a chat message to the fine-tuned model.
        
        Args:
            message: User message
            context: Optional conversation context
            
        Returns:
            Model response
        """
        messages = context or []
        messages.append({
            "role": "user",
            "content": message
        })
        
        response = self.client.chat(
            model=self.model,
            messages=messages
        )
        
        return response['message']['content']
    
    def generate(self, prompt: str) -> str:
        """
        Generate a response from a prompt.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated text
        """
        response = self.client.generate(
            model=self.model,
            prompt=prompt
        )
        
        return response['response']
```

**File:** `app/api/v1/chat.py` (or similar)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.llm.ollama_client import OllamaClient

router = APIRouter()
ollama_client = OllamaClient()

class ChatRequest(BaseModel):
    message: str
    context: List[Dict] = []

class ChatResponse(BaseModel):
    response: str
    model: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint using fine-tuned CollegeAdvisor model.
    """
    try:
        response = ollama_client.chat(
            message=request.message,
            context=request.context
        )
        
        return ChatResponse(
            response=response,
            model=ollama_client.model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. ChromaDB Integration (Optional but Recommended)

If your API needs to query ChromaDB directly for RAG:

**File:** `app/core/retrieval/chroma_retriever.py`

```python
import os
import chromadb
from typing import List, Dict, Any

class ChromaRetriever:
    def __init__(self):
        self.host = os.getenv("CHROMA_HOST", "localhost")
        self.port = int(os.getenv("CHROMA_PORT", "8000"))
        self.collection_name = os.getenv("CHROMA_COLLECTION_NAME", "college_advisor")
        
        self.client = chromadb.HttpClient(
            host=self.host,
            port=self.port
        )
        self.collection = self.client.get_collection(self.collection_name)
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search ChromaDB for relevant documents.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        documents = []
        for i in range(len(results['ids'][0])):
            documents.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })
        
        return documents
```

**File:** `app/api/v1/search.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.core.retrieval.chroma_retriever import ChromaRetriever

router = APIRouter()
retriever = ChromaRetriever()

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    count: int

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Search endpoint using ChromaDB.
    """
    try:
        results = retriever.search(
            query=request.query,
            n_results=request.limit
        )
        
        return SearchResponse(
            results=results,
            count=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 5. RAG Integration (Recommended)

Combine ChromaDB retrieval with Ollama generation:

**File:** `app/core/rag/rag_pipeline.py`

```python
from app.core.llm.ollama_client import OllamaClient
from app.core.retrieval.chroma_retriever import ChromaRetriever
from typing import List, Dict, Any

class RAGPipeline:
    def __init__(self):
        self.llm = OllamaClient()
        self.retriever = ChromaRetriever()
    
    def query(self, question: str, n_context: int = 5) -> Dict[str, Any]:
        """
        RAG query: Retrieve relevant context and generate response.
        
        Args:
            question: User question
            n_context: Number of context documents to retrieve
            
        Returns:
            Response with sources
        """
        # Retrieve relevant documents
        context_docs = self.retriever.search(question, n_results=n_context)
        
        # Build context string
        context = "\n\n".join([
            f"Source {i+1}: {doc['content']}"
            for i, doc in enumerate(context_docs)
        ])
        
        # Build prompt with context
        prompt = f"""Based on the following information about colleges and universities, please answer the question.

Context:
{context}

Question: {question}

Answer:"""
        
        # Generate response
        response = self.llm.generate(prompt)
        
        return {
            "answer": response,
            "sources": [
                {
                    "content": doc['content'],
                    "metadata": doc['metadata']
                }
                for doc in context_docs
            ]
        }
```

**File:** `app/api/v1/recommendations.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.core.rag.rag_pipeline import RAGPipeline

router = APIRouter()
rag = RAGPipeline()

class RecommendationRequest(BaseModel):
    gpa: float
    sat: int = None
    act: int = None
    interests: List[str] = []
    location_preference: str = None

class RecommendationResponse(BaseModel):
    recommendations: str
    sources: List[Dict[str, Any]]

@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Get college recommendations using RAG.
    """
    try:
        # Build query
        query = f"""I'm looking for college recommendations for a student with:
- GPA: {request.gpa}
- SAT: {request.sat if request.sat else 'Not provided'}
- ACT: {request.act if request.act else 'Not provided'}
- Interests: {', '.join(request.interests) if request.interests else 'Not specified'}
- Location preference: {request.location_preference if request.location_preference else 'No preference'}

Please recommend suitable colleges and explain why they would be a good fit."""
        
        # Get RAG response
        result = rag.query(query)
        
        return RecommendationResponse(
            recommendations=result['answer'],
            sources=result['sources']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 6. Start the API

```bash
# Install dependencies if needed
pip install ollama chromadb

# Start the API (use your existing command)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Test the Integration

**Test 1: Health Check**
```bash
curl http://localhost:8000/health
```

**Test 2: Chat Endpoint**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the admission rate at Harvard University?"
  }'
```

**Expected response:**
```json
{
  "response": "Harvard University has an admission rate of approximately 3-4%, making it one of the most selective universities in the United States...",
  "model": "collegeadvisor"
}
```

**Test 3: Search Endpoint**
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "selective universities in California",
    "limit": 5
  }'
```

**Test 4: Recommendations Endpoint**
```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "gpa": 3.8,
    "sat": 1450,
    "interests": ["computer science", "engineering"],
    "location_preference": "California"
  }'
```

## Verification Checklist

- [ ] Environment variables configured
- [ ] Ollama running and serving collegeadvisor model
- [ ] ChromaDB running (if using direct queries)
- [ ] API starts without errors
- [ ] Chat endpoint returns responses
- [ ] Search endpoint returns results (if implemented)
- [ ] Recommendations endpoint works (if implemented)
- [ ] Responses use fine-tuned model
- [ ] Response time < 10 seconds
- [ ] Responses are accurate and relevant

## Troubleshooting

### API Can't Connect to Ollama

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# If not running
ollama serve

# Check environment variable
echo $OLLAMA_HOST
```

### Model Not Found

```bash
# List available models
ollama list

# If collegeadvisor not listed, create it
cd CollegeAdvisor-data/data/finetuning_prep/training_datasets
ollama create collegeadvisor -f Modelfile
```

### ChromaDB Connection Failed

```bash
# Check ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# If not running
chroma run --path ./chroma_data --port 8000
```

### Slow Response Times

- Check Ollama is using GPU (if available)
- Reduce context window size
- Optimize ChromaDB queries
- Use caching for frequent queries

## Performance Optimization

### 1. Enable GPU Acceleration (if available)

```bash
# Run Ollama with GPU
OLLAMA_GPU=1 ollama serve
```

### 2. Implement Response Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(question: str) -> str:
    return rag.query(question)
```

### 3. Optimize ChromaDB Queries

```python
# Limit number of results
results = retriever.search(query, n_results=3)  # Instead of 10

# Use metadata filtering
results = collection.query(
    query_texts=[query],
    n_results=5,
    where={"state": "California"}  # Filter by metadata
)
```

## Next Steps

1. **Monitor Performance**
   - Track response times
   - Monitor accuracy
   - Log user queries

2. **Collect Feedback**
   - User satisfaction ratings
   - Response quality metrics
   - Error rates

3. **Iterate and Improve**
   - Refine system prompts
   - Add more training data
   - Optimize parameters

4. **Scale for Production**
   - Load balancing
   - Caching layer
   - Rate limiting
   - Monitoring and alerting

## Summary

To integrate the fine-tuned model with your API:

1. Set `OLLAMA_MODEL=collegeadvisor` in environment
2. Ensure Ollama is running with the model
3. Update API code to use Ollama client (if needed)
4. Optionally integrate ChromaDB for RAG
5. Test all endpoints
6. Monitor and optimize

The fine-tuned model will provide accurate, domain-specific responses for college admissions queries.

