#!/usr/bin/env python3
"""
Simple RAG System Test - Direct ChromaDB Integration
"""

import json
import requests
import chromadb
from sentence_transformers import SentenceTransformer

def test_chromadb_connection():
    """Test ChromaDB connection"""
    print("🔍 Testing ChromaDB connection...")
    try:
        response = requests.get("http://localhost:8000/api/v2/heartbeat")
        if response.status_code == 200:
            print("✅ ChromaDB is running")
            return True
        else:
            print(f"❌ ChromaDB heartbeat failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {e}")
        return False

def test_embedding_model():
    """Test embedding model"""
    print("🔍 Testing embedding model...")
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        test_text = "This is a test sentence."
        embedding = model.encode([test_text])
        print(f"✅ Embedding model working (dimension: {len(embedding[0])})")
        return model
    except Exception as e:
        print(f"❌ Embedding model failed: {e}")
        return None

def test_data_ingestion():
    """Test direct data ingestion to ChromaDB"""
    print("🔍 Testing data ingestion...")
    try:
        # Connect to ChromaDB
        client = chromadb.HttpClient(host="localhost", port=8000)
        
        # Create or get collection
        collection_name = "college_advisor_test"
        try:
            collection = client.get_collection(collection_name)
            print(f"✅ Found existing collection: {collection_name}")
        except:
            collection = client.create_collection(collection_name)
            print(f"✅ Created new collection: {collection_name}")
        
        # Load sample data
        with open('data/sample/combined_data.json', 'r') as f:
            data = json.load(f)
        
        # Initialize embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Prepare data for ingestion
        documents = []
        metadatas = []
        ids = []
        
        for i, item in enumerate(data):
            # Create document text
            if item.get('type') == 'college':
                doc_text = f"College: {item['name']}. Location: {item['location']}. Description: {item['description']}"
            elif item.get('type') == 'program':
                doc_text = f"Program: {item['name']}. College: {item['college']}. Description: {item['description']}"
            else:
                doc_text = str(item)
            
            documents.append(doc_text)
            metadatas.append({
                'type': item.get('type', 'unknown'),
                'name': item.get('name', f'item_{i}'),
                'source': 'sample_data'
            })
            ids.append(f"doc_{i}")
        
        # Generate embeddings
        print(f"📊 Generating embeddings for {len(documents)} documents...")
        embeddings = model.encode(documents).tolist()
        
        # Upsert to ChromaDB
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids
        )
        
        print(f"✅ Successfully ingested {len(documents)} documents")
        return collection, model
        
    except Exception as e:
        print(f"❌ Data ingestion failed: {e}")
        return None, None

def test_retrieval(collection, model):
    """Test retrieval functionality"""
    print("🔍 Testing retrieval...")
    try:
        query = "Tell me about Stanford University"
        query_embedding = model.encode([query]).tolist()
        
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=3
        )
        
        print(f"✅ Retrieved {len(results['documents'][0])} results for query: '{query}'")
        for i, doc in enumerate(results['documents'][0]):
            print(f"   {i+1}. {doc[:100]}...")
        
        return results
        
    except Exception as e:
        print(f"❌ Retrieval failed: {e}")
        return None

def test_ollama_connection():
    """Test Ollama connection"""
    print("🔍 Testing Ollama connection...")
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running with {len(models)} models")
            for model in models:
                print(f"   - {model['name']}")
            return len(models) > 0
        else:
            print(f"❌ Ollama connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        return False

def main():
    """Run comprehensive RAG system test"""
    print("🚀 Simple RAG System Test")
    print("=" * 50)
    
    # Test 1: ChromaDB
    if not test_chromadb_connection():
        print("❌ Cannot proceed without ChromaDB")
        return
    
    # Test 2: Embedding Model
    model = test_embedding_model()
    if not model:
        print("❌ Cannot proceed without embedding model")
        return
    
    # Test 3: Data Ingestion
    collection, model = test_data_ingestion()
    if not collection:
        print("❌ Cannot proceed without data ingestion")
        return
    
    # Test 4: Retrieval
    results = test_retrieval(collection, model)
    if not results:
        print("❌ Retrieval test failed")
        return
    
    # Test 5: Ollama (optional)
    ollama_available = test_ollama_connection()
    
    print("\n🎉 RAG System Test Summary")
    print("=" * 50)
    print("✅ ChromaDB: Connected and working")
    print("✅ Embeddings: Model loaded and working")
    print("✅ Data Ingestion: Sample data loaded")
    print("✅ Retrieval: Query processing working")
    print(f"{'✅' if ollama_available else '⚠️ '} Ollama: {'Available' if ollama_available else 'Not available (setup script still running)'}")
    
    print("\n🎯 Next Steps:")
    if not ollama_available:
        print("1. Wait for setup script to complete Ollama model download")
        print("2. Test full RAG pipeline with generation")
    else:
        print("1. Ready for full RAG pipeline testing")
    print("2. Replace sample data with real college data")
    print("3. Integrate with API repository")
    print("4. Deploy to production")

if __name__ == "__main__":
    main()
