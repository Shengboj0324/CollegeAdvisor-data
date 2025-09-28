"""
RAG Client for connecting to the RAG service from the data pipeline
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
import aiohttp
import requests
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class RAGClient:
    """Client for interacting with the RAG service."""
    
    def __init__(self, 
                 chroma_host: str = "localhost",
                 chroma_port: int = 8000,
                 ollama_host: str = "localhost",
                 ollama_port: int = 11434,
                 collection_name: str = "college_advisor"):
        """
        Initialize RAG client.
        
        Args:
            chroma_host: ChromaDB host
            chroma_port: ChromaDB port
            ollama_host: Ollama host
            ollama_port: Ollama port
            collection_name: ChromaDB collection name
        """
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.ollama_host = ollama_host
        self.ollama_port = ollama_port
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port,
            settings=Settings()
        )
        
        # URLs
        self.chroma_url = f"http://{chroma_host}:{chroma_port}"
        self.ollama_url = f"http://{ollama_host}:{ollama_port}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of RAG service components."""
        health_status = {
            "status": "healthy",
            "chromadb": "unknown",
            "ollama": "unknown",
            "collection": "unknown"
        }
        
        try:
            # Check ChromaDB
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.chroma_url}/api/v2/heartbeat", timeout=5) as response:
                    if response.status == 200:
                        health_status["chromadb"] = "healthy"
                    else:
                        health_status["chromadb"] = "unhealthy"
                        health_status["status"] = "degraded"
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            health_status["chromadb"] = "unhealthy"
            health_status["status"] = "degraded"
        
        try:
            # Check Ollama
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags", timeout=5) as response:
                    if response.status == 200:
                        health_status["ollama"] = "healthy"
                    else:
                        health_status["ollama"] = "unhealthy"
                        health_status["status"] = "degraded"
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            health_status["ollama"] = "unhealthy"
            health_status["status"] = "degraded"
        
        try:
            # Check collection
            collection = self.chroma_client.get_collection(self.collection_name)
            count = collection.count()
            health_status["collection"] = f"healthy ({count} documents)"
        except Exception as e:
            logger.error(f"Collection health check failed: {e}")
            health_status["collection"] = "unhealthy"
            health_status["status"] = "degraded"
        
        return health_status
    
    def _retrieve_documents(self,
                          query: str,
                          profile: Optional[Dict[str, Any]] = None,
                          n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from ChromaDB."""
        try:
            collection = self.chroma_client.get_collection(self.collection_name)

            # For now, skip filtering due to ChromaDB query syntax complexity
            # The sample data doesn't have consistent metadata structure for filtering
            # In production, we'd need to standardize metadata fields
            where_clause = None

            # Note: ChromaDB filtering requires exact field matches and specific operators
            # For MVP, we'll rely on semantic search without metadata filtering

            # Query collection
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
            
            # Format results
            documents = []
            for i in range(len(results['documents'][0])):
                doc = {
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'relevance_score': 1.0 - results['distances'][0][i] if results['distances'] else 0.0,
                    'document_id': results['ids'][0][i] if results['ids'] else f"doc_{i}"
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            return []
    
    async def _generate_response(self, 
                               prompt: str, 
                               model: str = "llama3") -> str:
        """Generate response using Ollama."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                }
                
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "").strip()
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return "I apologize, but I'm having trouble generating a response right now."
                        
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _build_prompt(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """Build prompt for the LLM."""
        context = "\n\n".join([doc['content'] for doc in documents])
        
        prompt = f"""You are a helpful college advisor assistant. Based on the following \
information about colleges and programs, please provide personalized recommendations \
to answer the user's question.

CONTEXT:
{context}

USER QUESTION: {query}

Please provide a helpful, accurate, and personalized response based on the context \
provided. Include specific details about colleges, programs, requirements, and costs \
when relevant. If the context doesn't contain enough information to fully answer the \
question, acknowledge this and provide what information you can.

RESPONSE:"""
        
        return prompt
    
    async def get_recommendations(self, 
                                query: str,
                                profile: Optional[Dict[str, Any]] = None,
                                n_results: int = 5,
                                filters: Optional[Dict[str, Any]] = None,
                                model: str = "llama3") -> Dict[str, Any]:
        """
        Get college recommendations using RAG.
        
        Args:
            query: User's question/query
            profile: User profile for filtering
            n_results: Number of results to retrieve
            filters: Additional filters
            model: Ollama model to use
            
        Returns:
            Dict containing recommendations, sources, and metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Retrieve relevant documents
            documents = self._retrieve_documents(query, profile, n_results)
            
            if not documents:
                return {
                    "error": "No relevant documents found",
                    "query": query,
                    "sources": [],
                    "response": "I apologize, but I couldn't find relevant information to answer your question."
                }
            
            # Step 2: Build prompt
            prompt = self._build_prompt(query, documents)
            
            # Step 3: Generate response
            response_text = await self._generate_response(prompt, model)
            
            # Step 4: Format response
            processing_time = time.time() - start_time
            
            return {
                "query": query,
                "response": response_text,
                "sources": documents,
                "model": model,
                "processing_time": processing_time,
                "metadata": {
                    "retrieval_count": len(documents),
                    "model_used": model,
                    "profile_applied": profile is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Error in get_recommendations: {e}")
            return {
                "error": str(e),
                "query": query,
                "sources": [],
                "response": f"I apologize, but I encountered an error: {str(e)}"
            }
