#!/usr/bin/env python3
"""
Simple data ingestion without embedding model dependencies
"""

import json
import chromadb
from chromadb.config import Settings

def ingest_sample_data():
    """Ingest sample data into ChromaDB"""
    print("🔄 Starting simple data ingestion...")
    
    try:
        # Connect to ChromaDB
        client = chromadb.HttpClient(
            host="localhost",
            port=8000,
            settings=Settings(allow_reset=True)
        )
        
        # Reset collection if it exists
        try:
            client.delete_collection("college_advisor")
            print("✅ Deleted existing collection")
        except Exception as e:
            print(f"ℹ️  No existing collection to delete: {e}")
        
        # Create new collection with default embedding function
        collection = client.create_collection(
            name="college_advisor",
            metadata={"schema_version": "1.0", "description": "College advisor data"}
        )
        
        # Load sample data
        with open('data/sample/combined_data.json', 'r') as f:
            data = json.load(f)
        
        print(f"📊 Loaded {len(data)} items from sample data")
        
        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for i, item in enumerate(data):
            # Create document text
            if item.get('type') == 'university':
                doc_text = f"University: {item['name']}\n"
                doc_text += f"Location: {item['location']}\n"
                doc_text += f"Description: {item['description']}\n"
                doc_text += f"Tuition: ${item['tuition']:,}\n"
                doc_text += f"Acceptance Rate: {item['acceptance_rate']*100:.1f}%\n"
                doc_text += f"Programs: {', '.join(item['programs'])}"
            elif item.get('type') == 'program':
                doc_text = f"Program: {item['name']}\n"
                doc_text += f"University: {item.get('university', 'N/A')}\n"
                doc_text += f"Description: {item['description']}\n"
                doc_text += f"Duration: {item.get('duration', 'N/A')}\n"
                if 'requirements' in item:
                    doc_text += f"Requirements: {', '.join(item['requirements'])}"
            else:
                # Handle other types or malformed data
                doc_text = f"Name: {item.get('name', 'Unknown')}\n"
                doc_text += f"Type: {item.get('type', 'Unknown')}\n"
                doc_text += f"Description: {item.get('description', str(item))}"

            documents.append(doc_text)
            metadatas.append({
                "type": item.get('type', 'unknown'),
                "name": item.get('name', f'item_{i}'),
                "source": "sample_data"
            })
            ids.append(f"doc_{i}")
        
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ Successfully ingested {len(documents)} documents")
        
        # Test query
        print("\n🔍 Testing query...")
        results = collection.query(
            query_texts=["computer science programs"],
            n_results=3
        )
        
        print(f"Found {len(results['documents'][0])} relevant documents:")
        for i, doc in enumerate(results['documents'][0]):
            print(f"  {i+1}. {doc[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Data ingestion failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Simple Data Ingestion for CollegeAdvisor")
    print("=" * 50)
    
    success = ingest_sample_data()
    
    if success:
        print("\n🎉 Data ingestion completed successfully!")
        print("Next steps:")
        print("1. Test full RAG pipeline")
        print("2. Integrate with API repo")
        print("3. Replace with real data")
    else:
        print("\n❌ Data ingestion failed")
        print("Check the error messages above")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
