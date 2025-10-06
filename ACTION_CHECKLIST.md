# Fine-Tuning Action Checklist

## Immediate Actions (CollegeAdvisor-data Repository)

### Step 1: Environment Setup (5 minutes)

```bash
# Copy environment template
cp .env.finetuning.example .env

# Edit .env and set these required values:
# - COLLEGE_SCORECARD_API_KEY=your_key_here
# - CHROMA_HOST=localhost
# - CHROMA_PORT=8000
# - OLLAMA_HOST=http://localhost:11434

# Optional (for backup):
# - R2_ACCOUNT_ID=your_account_id
# - R2_ACCESS_KEY_ID=your_access_key
# - R2_SECRET_ACCESS_KEY=your_secret_key
```

### Step 2: Start Required Services (5 minutes)

**Terminal 1 - ChromaDB:**
```bash
chroma run --path ./chroma_data --port 8000
```

**Terminal 2 - Ollama:**
```bash
ollama serve
```

**Terminal 3 - Pull Base Model:**
```bash
ollama pull llama3
```

### Step 3: Run Readiness Tests (5 minutes)

```bash
python scripts/test_finetuning_readiness.py
```

**Expected Output:**
```
Tests Passed: 8-9
Tests Failed: 0
Warnings: 0-1 (R2 is optional)

✓ ALL CRITICAL TESTS PASSED - SYSTEM READY FOR FINE-TUNING
```

**If tests fail:**
- Check that ChromaDB is running (Terminal 1)
- Check that Ollama is running (Terminal 2)
- Verify .env configuration
- Check logs in `data/finetuning_readiness_report.json`

### Step 4: Collect and Prepare Data (2-4 hours)

```bash
# Get your College Scorecard API key from: https://api.data.gov/signup/
# Then run:

python scripts/prepare_finetuning.py --full --api-key YOUR_API_KEY
```

**This will:**
- Collect 5,000-7,000 institutions from College Scorecard
- Collect comprehensive data from IPEDS
- Process and clean all data
- Create 6 ChromaDB collections
- Generate training datasets in 3 formats
- Upload to R2 (if configured)
- Create Ollama Modelfile

**Monitor progress:**
- Watch terminal output for stage completion
- Check `data/finetuning_prep/PREPARATION_REPORT.txt` when done

**Expected output location:**
```
data/finetuning_prep/
├── raw_data/
│   ├── scorecard/complete_dataset.json
│   ├── ipeds/complete_dataset.json
│   └── comprehensive_dataset.json
├── processed/
│   └── comprehensive_dataset.json
├── training_datasets/
│   ├── instruction_dataset_alpaca.json
│   ├── instruction_dataset.jsonl
│   ├── instruction_dataset_ollama.txt
│   └── Modelfile
├── PREPARATION_REPORT.txt
└── preparation_stats.json
```

### Step 5: Fine-Tune Model (10 minutes)

```bash
cd data/finetuning_prep/training_datasets
ollama create collegeadvisor -f Modelfile
```

**Expected output:**
```
transferring model data
creating model layer
writing manifest
success
```

### Step 6: Test Fine-Tuned Model (5 minutes)

```bash
ollama run collegeadvisor "What is the admission rate at Harvard University?"
```

**Expected:** Accurate response about Harvard's admission rate (~3-4%)

**Test more queries:**
```bash
ollama run collegeadvisor "Tell me about Stanford's computer science program"
ollama run collegeadvisor "What are the costs of attending MIT?"
ollama run collegeadvisor "Compare UCLA and UC Berkeley"
```

### Step 7: Verify ChromaDB Collections (5 minutes)

```python
# Run in Python
from college_advisor_data.storage.collection_manager import CollectionManager

manager = CollectionManager()
stats = manager.get_collection_stats()

for collection, info in stats.items():
    print(f"{collection}: {info['document_count']} documents")
```

**Expected:**
```
institutions: 5000+ documents
programs: 1000+ documents
qa_pairs: 10000+ documents
```

## Actions in CollegeAdvisor-api Repository

### Step 1: Configure API to Use Fine-Tuned Model (2 minutes)

```bash
# In CollegeAdvisor-api/.env
OLLAMA_MODEL=collegeadvisor
OLLAMA_HOST=http://localhost:11434
```

### Step 2: Verify Ollama is Running (1 minute)

```bash
# Check Ollama is serving
curl http://localhost:11434/api/tags

# Verify collegeadvisor model exists
ollama list | grep collegeadvisor
```

### Step 3: Start API Server (2 minutes)

```bash
# Follow your existing API startup process
# Example:
cd CollegeAdvisor-api
python -m uvicorn app.main:app --reload
```

### Step 4: Test API Integration (5 minutes)

```bash
# Test chat endpoint
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the admission requirements for Stanford University?"
  }'
```

**Expected:** JSON response with accurate Stanford admissions information

**Test more endpoints:**
```bash
# Test search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "selective universities in California",
    "limit": 10
  }'

# Test recommendations
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "gpa": 3.8,
    "sat": 1450,
    "interests": ["computer science", "engineering"]
  }'
```

## Verification Checklist

### Data Pipeline ✓
- [ ] ChromaDB running on port 8000
- [ ] Ollama running on port 11434
- [ ] All readiness tests pass
- [ ] Data collection completed successfully
- [ ] 5,000+ institutions collected
- [ ] ChromaDB collections populated
- [ ] Training datasets generated

### Fine-Tuning ✓
- [ ] Modelfile created
- [ ] Model fine-tuned (collegeadvisor)
- [ ] Model responds to test queries
- [ ] Responses are accurate
- [ ] Response time < 10 seconds

### API Integration ✓
- [ ] API configured to use collegeadvisor model
- [ ] API starts without errors
- [ ] Chat endpoint works
- [ ] Search endpoint works
- [ ] Recommendations endpoint works
- [ ] Responses use fine-tuned model

### Production Readiness ✓
- [ ] Data backed up (R2 or local)
- [ ] Model exported/saved
- [ ] Documentation reviewed
- [ ] Performance benchmarks met
- [ ] Error handling tested

## Troubleshooting Quick Reference

### ChromaDB Not Connecting
```bash
# Check if running
curl http://localhost:8000/api/v1/heartbeat

# If not running, start it
chroma run --path ./chroma_data --port 8000
```

### Ollama Not Found
```bash
# Check if running
ollama list

# If not running, start it
ollama serve

# Check model exists
ollama list | grep collegeadvisor
```

### Data Collection Fails
```bash
# Verify API key
echo $COLLEGE_SCORECARD_API_KEY

# Run with debug logging
LOG_LEVEL=DEBUG python scripts/prepare_finetuning.py --collect-only --api-key YOUR_KEY
```

### Model Not Responding
```bash
# Recreate model
cd data/finetuning_prep/training_datasets
ollama create collegeadvisor -f Modelfile --force

# Test again
ollama run collegeadvisor "test query"
```

### API Returns Errors
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check model is available
ollama list

# Restart API server
# (use your API restart command)
```

## Time Estimates

| Task | Estimated Time |
|------|----------------|
| Environment setup | 5 minutes |
| Start services | 5 minutes |
| Readiness tests | 5 minutes |
| Data collection | 2-4 hours |
| Fine-tuning | 10 minutes |
| Testing model | 5 minutes |
| API configuration | 2 minutes |
| API testing | 5 minutes |
| **Total** | **3-5 hours** |

## Success Criteria

You're ready for production when:

✅ All readiness tests pass
✅ 5,000+ institutions in ChromaDB
✅ Training datasets generated
✅ Model fine-tuned successfully
✅ Model responds accurately
✅ API integration working
✅ Response time < 10 seconds
✅ No errors in logs

## Next Steps After Success

1. **Monitor Performance**
   - Track response times
   - Monitor accuracy
   - Collect user feedback

2. **Iterate on Data**
   - Add more institutions
   - Include more Q&A pairs
   - Expand to additional data sources

3. **Optimize Model**
   - Adjust parameters
   - Refine system prompt
   - Test different base models

4. **Deploy to Production**
   - Set up monitoring
   - Configure backups
   - Implement auto-scaling

## Support

- **Documentation**: See FINETUNING_GUIDE.md
- **Data Sources**: See DATA_SOURCES_STRATEGY.md
- **Implementation**: See IMPLEMENTATION_SUMMARY.md
- **Logs**: Check `logs/pipeline.log`
- **Reports**: Check `data/finetuning_prep/PREPARATION_REPORT.txt`

