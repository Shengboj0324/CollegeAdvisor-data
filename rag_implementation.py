"""
RAG (Retrieval-Augmented Generation) implementation for CollegeAdvisor.

This module implements the core RAG functionality that bridges ChromaDB
retrieval with Ollama generation, following the data/API contract.
"""

import json
import logging
from typing import List, Dict, Any, Optional
import requests
from pathlib import Path

# Avoid problematic imports that cause crashes
try:
    from college_advisor_data.storage.chroma_client import ChromaDBClient
    from college_advisor_data.schemas import COLLECTION_NAME, SCHEMA_VERSION
    CHROMA_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ChromaDB client not available: {e}")
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation service for college recommendations.
    
    This service implements the core RAG pattern:
    1. Retrieve relevant documents from ChromaDB
    2. Build grounded prompt with context
    3. Generate response using Ollama
    4. Format and return structured response
    """
    
    def __init__(self, 
                 chroma_host: str = "localhost",
                 chroma_port: int = 8000,
                 ollama_host: str = "http://localhost:11434",
                 collection_name: str = None):
        """
        Initialize RAG service.
        
        Args:
            chroma_host: ChromaDB server host
            chroma_port: ChromaDB server port  
            ollama_host: Ollama server URL
            collection_name: ChromaDB collection name
        """
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.ollama_host = ollama_host
        self.collection_name = collection_name or COLLECTION_NAME
        
        # Initialize clients
        self.chroma_client = None
        if CHROMA_AVAILABLE:
            try:
                self.chroma_client = ChromaDBClient(collection_name=self.collection_name)
                logger.info("ChromaDB client initialized")
            except Exception as e:
                logger.warning(f"ChromaDB client initialization failed: {e}")
        
        # Test Ollama connection
        self._test_ollama_connection()
    
    def _test_ollama_connection(self) -> bool:
        """Test connection to Ollama server."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                logger.info(f"Ollama connected with {len(models)} models")
                return True
            else:
                logger.warning(f"Ollama responded with status {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Ollama connection failed: {e}")
            return False
    
    def get_recommendations(self, 
                          query: str, 
                          profile: Optional[Dict[str, Any]] = None,
                          n_results: int = 5,
                          model: str = "llama3") -> Dict[str, Any]:
        """
        Get college recommendations using RAG.
        
        Args:
            query: User's question/query
            profile: User profile for filtering (GPA, location, etc.)
            n_results: Number of results to retrieve
            model: Ollama model to use
            
        Returns:
            Dict containing recommendations, sources, and metadata
        """
        try:
            # Step 1: Retrieve relevant documents
            retrieval_results = self._retrieve_documents(query, profile, n_results)
            
            # Step 2: Build grounded prompt
            context = self._format_context(retrieval_results)
            prompt = self._build_prompt(query, context)
            
            # Step 3: Generate response
            response_text = self._generate_response(prompt, model)
            
            # Step 4: Format response
            return self._format_response(
                query=query,
                response_text=response_text,
                retrieval_results=retrieval_results,
                model=model
            )
            
        except Exception as e:
            logger.error(f"Error in get_recommendations: {e}")
            return self._error_response(str(e))
    
    def _retrieve_documents(self, 
                           query: str, 
                           profile: Optional[Dict[str, Any]], 
                           n_results: int) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from ChromaDB."""
        
        if not self.chroma_client:
            # Fallback: return mock data for testing
            return self._get_mock_results(query, n_results)
        
        try:
            # Build filters from profile
            filters = self._build_filters(profile) if profile else None
            
            # Query ChromaDB
            results = self.chroma_client.query(
                query_text=query,
                n_results=n_results * 2,  # Get more to filter
                where=filters
            )
            
            # Format results
            formatted_results = []
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0] 
            distances = results.get("distances", [[]])[0]
            
            for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
                formatted_results.append({
                    "document": doc,
                    "metadata": meta,
                    "distance": dist,
                    "rank": i + 1
                })
            
            return formatted_results[:n_results]
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return self._get_mock_results(query, n_results)
    
    def _build_filters(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Build ChromaDB filters from user profile."""
        filters = {}
        
        if profile.get("gpa_range"):
            filters["gpa_band"] = profile["gpa_range"]
        
        if profile.get("location"):
            # Use contains for partial location matching
            filters["location"] = {"$contains": profile["location"]}
        
        if profile.get("entity_type"):
            filters["entity_type"] = profile["entity_type"]
        
        if profile.get("majors"):
            # Filter by programs/majors
            majors = profile["majors"]
            if isinstance(majors, str):
                majors = [majors]
            filters["majors"] = {"$in": majors}
        
        return filters
    
    def _format_context(self, results: List[Dict[str, Any]]) -> str:
        """Format retrieval results into context for the prompt."""
        if not results:
            return "No relevant information found."
        
        context_parts = []
        for i, result in enumerate(results[:5]):  # Use top 5 results
            doc = result.get("document", "")
            meta = result.get("metadata", {})
            
            school = meta.get("school", "Unknown Institution")
            name = meta.get("name", "Unknown Program")
            location = meta.get("location", "Unknown Location")
            
            context_parts.append(
                f"{i+1}. {school} - {name} ({location})\n   {doc[:300]}..."
            )
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the prompt for the language model."""
        return f"""You are an expert college advisor helping students find the best educational opportunities. Based on the following information about colleges and programs, provide helpful and specific recommendations.

CONTEXT INFORMATION:
{context}

STUDENT QUESTION: {query}

Please provide a helpful response that:
1. Directly addresses the student's question
2. References specific schools and programs from the context
3. Includes relevant details like location, requirements, or specializations
4. Offers practical advice for the student
5. Keeps the response focused and actionable

RESPONSE:"""
    
    def _generate_response(self, prompt: str, model: str = "llama3") -> str:
        """Generate response using Ollama."""
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return "I apologize, but I'm having trouble generating a response right now."
                
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _format_response(self, 
                        query: str,
                        response_text: str, 
                        retrieval_results: List[Dict[str, Any]],
                        model: str) -> Dict[str, Any]:
        """Format the final response."""
        
        # Extract source information
        sources = []
        for result in retrieval_results:
            meta = result.get("metadata", {})
            sources.append({
                "doc_id": meta.get("doc_id", "unknown"),
                "school": meta.get("school", "Unknown"),
                "name": meta.get("name", "Unknown"),
                "distance": result.get("distance", 1.0)
            })
        
        return {
            "query": query,
            "response": response_text,
            "sources": sources,
            "metadata": {
                "collection_version": f"{self.collection_name}@v{SCHEMA_VERSION}",
                "model_version": model,
                "n_sources": len(sources),
                "retrieval_method": "chromadb_similarity"
            }
        }
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Return error response."""
        return {
            "query": "",
            "response": f"I apologize, but I encountered an error: {error_message}",
            "sources": [],
            "metadata": {
                "error": True,
                "error_message": error_message
            }
        }
    
    def _get_mock_results(self, query: str, n_results: int) -> List[Dict[str, Any]]:
        """Return mock results for testing when ChromaDB is not available."""
        mock_data = [
            {
                "document": "Stanford University offers one of the top computer science programs in the world with strong focus on AI and machine learning.",
                "metadata": {
                    "doc_id": "stanford_cs",
                    "school": "Stanford University", 
                    "name": "Computer Science Program",
                    "location": "California, USA",
                    "gpa_band": "3.5-4.0"
                },
                "distance": 0.2,
                "rank": 1
            },
            {
                "document": "MIT's Computer Science and Artificial Intelligence Laboratory (CSAIL) is renowned for cutting-edge research in AI, robotics, and systems.",
                "metadata": {
                    "doc_id": "mit_cs",
                    "school": "Massachusetts Institute of Technology",
                    "name": "Computer Science Program", 
                    "location": "Massachusetts, USA",
                    "gpa_band": "3.5-4.0"
                },
                "distance": 0.3,
                "rank": 2
            }
        ]
        
        return mock_data[:n_results]


def test_rag_system():
    """Test the RAG system with sample queries."""
    print("🧪 Testing RAG System")
    print("=" * 30)
    
    rag = RAGService()
    
    test_queries = [
        "What are the best computer science programs for AI research?",
        "Which universities offer good CS programs with lower tuition?",
        "What should I study to prepare for computer science programs?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 50)
        
        result = rag.get_recommendations(
            query=query,
            profile={"gpa_range": "3.5-4.0"},
            n_results=3
        )
        
        print(f"Response: {result['response'][:200]}...")
        print(f"Sources: {len(result['sources'])} documents")
        
        if result.get("metadata", {}).get("error"):
            print(f"⚠️ Error: {result['metadata']['error_message']}")


if __name__ == "__main__":
    test_rag_system()
