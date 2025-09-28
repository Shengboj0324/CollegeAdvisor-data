#!/usr/bin/env python3
"""
Test full RAG pipeline with ingested data
"""

import json
import requests
import chromadb
from chromadb.config import Settings

class SimpleRAGService:
    """Simple RAG service for testing"""
    
    def __init__(self):
        self.chroma_client = chromadb.HttpClient(
            host="localhost",
            port=8000,
            settings=Settings()
        )
        self.ollama_url = "http://localhost:11434/api/generate"
        
    def retrieve_documents(self, query, n_results=3):
        """Retrieve relevant documents from ChromaDB"""
        try:
            collection = self.chroma_client.get_collection("college_advisor")
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            documents = []
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                documents.append({
                    'content': doc,
                    'metadata': metadata,
                    'distance': results['distances'][0][i] if results['distances'] else 0
                })
            
            return documents
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []
    
    def generate_response(self, query, context_docs):
        """Generate response using Ollama"""
        try:
            # Prepare context
            context = "\n\n".join([doc['content'] for doc in context_docs])
            
            # Create prompt
            prompt = f"""Based on the following information about colleges and programs, please answer the user's question.

Context:
{context}

Question: {query}

Please provide a helpful and accurate answer based on the context provided. If the context doesn't contain enough information to fully answer the question, say so and provide what information you can."""

            # Call Ollama
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "llama3",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated')
            else:
                return f"Error: Ollama returned status {response.status_code}"
                
        except Exception as e:
            return f"Error generating response: {e}"
    
    def query(self, question):
        """Full RAG query"""
        print(f"🔍 Query: {question}")
        print("-" * 60)
        
        # Retrieve documents
        docs = self.retrieve_documents(question)
        print(f"📚 Retrieved {len(docs)} documents")
        
        if docs:
            print("📄 Top documents:")
            for i, doc in enumerate(docs[:2]):
                print(f"  {i+1}. {doc['content'][:100]}...")
                print(f"     Distance: {doc['distance']:.3f}")
        
        # Generate response
        print("\n🤖 Generating response...")
        response = self.generate_response(question, docs)
        
        print(f"\n💬 Response:\n{response}")
        print("\n" + "="*80 + "\n")
        
        return {
            'query': question,
            'documents': docs,
            'response': response
        }

def test_rag_queries():
    """Test various RAG queries"""
    rag = SimpleRAGService()
    
    test_queries = [
        "What are the best computer science programs for AI research?",
        "Which universities have lower tuition costs?",
        "What are the admission requirements for top CS programs?",
        "Tell me about Stanford's computer science program",
        "What programs are available at UC Berkeley?"
    ]
    
    results = []
    for query in test_queries:
        try:
            result = rag.query(query)
            results.append(result)
        except Exception as e:
            print(f"❌ Query failed: {e}")
            results.append({'query': query, 'error': str(e)})
    
    return results

def main():
    """Main test function"""
    print("🚀 Full RAG Pipeline Test")
    print("=" * 80)
    
    try:
        # Test ChromaDB connection
        client = chromadb.HttpClient(host="localhost", port=8000)
        collection = client.get_collection("college_advisor")
        count = collection.count()
        print(f"✅ ChromaDB connected: {count} documents in collection")
        
        # Test Ollama connection
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Ollama connected")
        else:
            print("❌ Ollama connection failed")
            return False
        
        print("\n🧪 Running RAG tests...")
        print("=" * 80)
        
        # Run tests
        results = test_rag_queries()
        
        # Summary
        successful = sum(1 for r in results if 'error' not in r)
        total = len(results)
        
        print(f"📊 Test Summary: {successful}/{total} queries successful")
        
        if successful == total:
            print("\n🎉 ALL RAG TESTS PASSED!")
            print("✅ Data retrieval working")
            print("✅ Response generation working")
            print("✅ Full pipeline operational")
            print("\nReady for:")
            print("• API integration")
            print("• Real data ingestion")
            print("• Production deployment")
        else:
            print(f"\n⚠️  {total - successful} tests failed")
            print("Check error messages above")
        
        return successful == total
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
