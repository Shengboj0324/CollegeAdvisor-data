

### **Task 2: Build ChromaDB Collection**

**Goal**: Create a vector database collection with embeddings for all colleges and programs.

#### Steps:

1. **Prepare Data Files**
   ```bash
   # Ensure you have structured data
   ls data/processed/
   # Expected files:
   # - colleges.csv
   # - summer_programs.csv
   # - admission_requirements.csv
   # - scholarships.csv
   ```

2. **Create Collection Builder Script**
   ```python
   # scripts/build_chroma_collection.py
   
   import chromadb
   from chromadb.config import Settings
   import pandas as pd
   import ollama
   
   # Initialize ChromaDB
   client = chromadb.Client(Settings(
       chroma_db_impl="duckdb+parquet",
       persist_directory="./chroma_data"
   ))
   
   # Create collection
   collection = client.create_collection(
       name="college_advisor@v1.0",
       metadata={"version": "1.0", "description": "College and program data"}
   )
   
   # Load data
   colleges = pd.read_csv("data/processed/colleges.csv")
   
   # Generate embeddings and add to collection
   for idx, row in colleges.iterrows():
       # Create document text
       doc_text = f"{row['name']} - {row['description']}"
       
       # Generate embedding using Ollama
       embedding = ollama.embeddings(
           model="nomic-embed-text",
           prompt=doc_text
       )
       
       # Add to collection
       collection.add(
           ids=[str(row['id'])],
           embeddings=[embedding['embedding']],
           documents=[doc_text],
           metadatas=[{
               "name": row['name'],
               "type": "college",
               "state": row['state'],
               "programs": row['programs'],
               # Add all relevant metadata
           }]
       )
   
   print(f"Added {len(colleges)} colleges to collection")
   ```

3. **Run the Builder**
   ```bash
   python scripts/build_chroma_collection.py
   ```

4. **Verify Collection**
   ```python
   # scripts/verify_collection.py
   
   import chromadb
   
   client = chromadb.Client(Settings(persist_directory="./chroma_data"))
   collection = client.get_collection("college_advisor@v1.0")
   
   # Test query
   results = collection.query(
       query_texts=["computer science programs"],
       n_results=5
   )
   
   print("Top 5 results:")
   for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
       print(f"- {metadata['name']}: {doc[:100]}...")
   ```

---

### **Task 3: Generate Embeddings**

**Goal**: Pre-generate embeddings for all data to speed up queries.

#### Steps:

1. **Install Required Packages**
   ```bash
   pip install chromadb ollama pandas numpy
   ```

2. **Generate Embeddings**
   ```bash
   # Use Ollama's embedding model
   python scripts/generate_embeddings.py \
     --model nomic-embed-text \
     --input data/processed \
     --output embeddings
   ```

3. **Verify Embeddings**
   ```bash
   # Check embedding dimensions
   python -c "
   import numpy as np
   embeddings = np.load('embeddings/colleges.npy')
   print(f'Shape: {embeddings.shape}')
   print(f'Dimension: {embeddings.shape[1]}')
   "
   ```

---

### **Task 4: Export Artifacts**

**Goal**: Package the model and data for deployment.

#### Steps:

1. **Create Artifacts Directory**
   ```bash
   mkdir -p artifacts/{chroma,models,manifests}
   ```

2. **Export ChromaDB Collection**
   ```bash
   # Copy ChromaDB data
   cp -r chroma_data artifacts/chroma/
   
   # Create metadata file
   cat > artifacts/chroma/metadata.json << EOF
   {
     "collection_name": "college_advisor@v1.0",
     "version": "1.0",
     "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
     "total_documents": $(python -c "import chromadb; print(chromadb.Client().get_collection('college_advisor@v1.0').count())")
   }
   EOF
   ```

3. **Export Ollama Model**
   ```bash
   # Save model
   ollama save collegeadvisor > artifacts/models/collegeadvisor.tar
   
   # Create model metadata
   cat > artifacts/models/metadata.json << EOF
   {
     "model_name": "collegeadvisor",
     "base_model": "llama3",
     "version": "1.0",
     "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
   }
   EOF
   ```

4. **Create Version Manifest**
   ```bash
   cat > artifacts/manifests/v1.0.json << EOF
   {
     "version": "1.0",
     "release_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
     "components": {
       "model": {
         "name": "collegeadvisor",
         "tag": "collegeadvisor:latest",
         "file": "models/collegeadvisor.tar"
       },
       "chroma_collection": {
         "name": "college_advisor@v1.0",
         "path": "chroma/",
         "document_count": 0
       }
     },
     "compatibility": {
       "api_version": "0.1.0",
       "min_ollama_version": "0.1.0",
       "min_chroma_version": "0.4.0"
     }
   }
   EOF
   ```

---

### **Task 5: Sync with CollegeAdvisor-api**

**Goal**: Make the artifacts available to the API.

#### Option A: Local Development

```bash
# Copy ChromaDB data to API repository
cp -r artifacts/chroma/* ~/Desktop/CollegeAdvisor-api/chroma_data/

# Ollama model is already available locally (no copy needed)
# Just ensure it's running: ollama serve
```

#### Option B: Cloud Deployment

```bash
# 1. Deploy ChromaDB to Cloud Run
gcloud run deploy chromadb \
  --image chromadb/chroma:latest \
  --region us-west1 \
  --allow-unauthenticated \
  --set-env-vars PERSIST_DIRECTORY=/data \
  --add-volume name=chroma-data,type=cloud-storage,bucket=collegeadvisor-chroma \
  --add-volume-mount volume=chroma-data,mount-path=/data

# 2. Upload ChromaDB data to Cloud Storage
gsutil -m cp -r artifacts/chroma/* gs://collegeadvisor-chroma/

# 3. Deploy Ollama to Cloud Run (requires custom image)
# Build custom image with model
docker build -t gcr.io/YOUR_PROJECT/ollama-collegeadvisor:v1.0 .
docker push gcr.io/YOUR_PROJECT/ollama-collegeadvisor:v1.0

gcloud run deploy ollama \
  --image gcr.io/YOUR_PROJECT/ollama-collegeadvisor:v1.0 \
  --region us-west1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2

# 4. Update API environment variables
gcloud run services update collegeadvisor-api \
  --region us-west1 \
  --update-env-vars \
    CHROMA_HOST=https://chromadb-xxx.run.app,\
    CHROMA_PORT=443,\
    OLLAMA_HOST=https://ollama-xxx.run.app,\
    OLLAMA_PORT=443,\
    MODEL_TAG=collegeadvisor,\
    CHROMA_COLLECTION=college_advisor@v1.0
```

---

### **Task 6: Test Integration**

**Goal**: Verify everything works end-to-end.

#### Steps:

1. **Test Locally**
   ```bash
   cd ~/Desktop/CollegeAdvisor-api
   
   # Start services
   ollama serve &
   docker-compose up -d chromadb
   
   # Start API
   uvicorn app.main:app --reload
   
   # Test recommendation endpoint
   curl -X POST http://localhost:8000/recommendations \
     -H "Authorization: Bearer dev-token-change-in-production" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "I want to study computer science in California",
       "max_results": 5,
       "include_reasoning": true
     }' | jq
   ```

2. **Verify Response**
   - Should return structured recommendations
   - Should include reasoning
   - Should have high confidence scores
   - Should match user query

---

## 📊 Success Criteria

- [ ] Ollama model `collegeadvisor` created and tested
- [ ] ChromaDB collection `college_advisor@v1.0` built with embeddings
- [ ] All data files processed and loaded
- [ ] Artifacts exported and versioned
- [ ] Integration tested locally
- [ ] (Optional) Deployed to Cloud Run
- [ ] API returns relevant recommendations with reasoning

---

## 🚀 Quick Start Commands

```bash
# 1. Fine-tune model
ollama create collegeadvisor -f Modelfile

# 2. Build ChromaDB collection
python scripts/build_chroma_collection.py

# 3. Verify
ollama list | grep collegeadvisor
python scripts/verify_collection.py

# 4. Sync to API (local)
cp -r chroma_data/* ~/Desktop/CollegeAdvisor-api/chroma_data/

# 5. Test
cd ~/Desktop/CollegeAdvisor-api
uvicorn app.main:app --reload
```

---

## 📝 Notes

- The API is already configured to use `collegeadvisor` model
- ChromaDB collection should be named `college_advisor@v1.0`
- Use `nomic-embed-text` for embeddings (384 dimensions)
- Ensure data quality before building collection
- Version all artifacts for rollback capability

---

## 🆘 Troubleshooting

**Model not found**:
```bash
ollama list
ollama pull llama3
ollama create collegeadvisor -f Modelfile
```

**ChromaDB connection failed**:
```bash
docker-compose up -d chromadb
curl http://localhost:8001/api/v1/heartbeat
```

**Empty recommendations**:
- Check if collection has data: `collection.count()`
- Verify embeddings are generated correctly
- Test query directly on ChromaDB

---

## ✅ Completion Checklist

When you complete these tasks, the full system will be operational:

- ✅ CollegeAdvisor-api: Backend API (DONE)
- ⏳ CollegeAdvisor-data: AI Training & Data (TODO)
- ⏳ iOS App: Frontend (Separate project)

**After completing these tasks, return to CollegeAdvisor-api and test the full integration!**

