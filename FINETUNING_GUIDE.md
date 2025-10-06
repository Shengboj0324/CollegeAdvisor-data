# CollegeAdvisor Fine-Tuning Guide

## Overview

This guide provides comprehensive instructions for preparing and fine-tuning the CollegeAdvisor LLM using Ollama and ChromaDB.

## Prerequisites

### Required Software
- Python 3.9+
- Ollama installed and running
- ChromaDB server running (or cloud instance)
- Sufficient disk space (50GB+ recommended)
- 16GB+ RAM recommended

### Required API Keys
- College Scorecard API key (get from https://api.data.gov/signup/)
- Cloudflare R2 credentials (optional, for data backup)

## Setup Instructions

### 1. Environment Configuration

Copy the environment template and configure:

```bash
cp .env.finetuning.example .env
```

Edit `.env` and set:
- `COLLEGE_SCORECARD_API_KEY`: Your API key
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`: R2 credentials (optional)
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)
- `CHROMA_HOST`, `CHROMA_PORT`: ChromaDB connection details

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Required Services

**Start ChromaDB:**
```bash
chroma run --path ./chroma_data --port 8000
```

**Start Ollama:**
```bash
ollama serve
```

**Pull base model:**
```bash
ollama pull llama3
```

## Data Preparation Pipeline

### Phase 1: Test System Readiness

Run comprehensive readiness tests:

```bash
python scripts/test_finetuning_readiness.py
```

This will test:
- Configuration settings
- ChromaDB connectivity
- Embedding generation
- Data processing pipeline
- Ollama connectivity
- R2 storage (optional)
- Training data generation
- Data quality

**Expected Output:**
```
Tests Passed: 8-9
Tests Failed: 0
Warnings: 0-1 (R2 is optional)

✓ ALL CRITICAL TESTS PASSED - SYSTEM READY FOR FINE-TUNING
```

### Phase 2: Collect Comprehensive Data

Run the full data collection pipeline:

```bash
python scripts/prepare_finetuning.py --full --api-key YOUR_API_KEY
```

This will:
1. Collect data from College Scorecard (7,000+ institutions)
2. Collect data from IPEDS via Urban Institute API
3. Process and clean all collected data
4. Create ChromaDB collections
5. Generate training datasets in multiple formats
6. Upload to R2 (if configured)
7. Create Ollama Modelfile

**Expected Duration:** 2-4 hours depending on network speed

**Output Location:** `data/finetuning_prep/`

### Phase 3: Verify Data Quality

Check the preparation report:

```bash
cat data/finetuning_prep/PREPARATION_REPORT.txt
```

Verify:
- Total institutions collected (target: 5,000+)
- ChromaDB documents added
- Training datasets generated
- No critical errors

## Fine-Tuning Process

### Option 1: Basic Fine-Tuning (Recommended for Start)

Create a custom model with system prompt:

```bash
cd data/finetuning_prep/training_datasets
ollama create collegeadvisor -f Modelfile
```

Test the model:

```bash
ollama run collegeadvisor "What is the admission rate at Harvard University?"
```

### Option 2: Advanced Fine-Tuning with Training Data

For more advanced fine-tuning, use the instruction dataset:

```bash
# Create model with training data
ollama create collegeadvisor-tuned -f Modelfile --training-data instruction_dataset_ollama.txt
```

### Option 3: Custom Fine-Tuning Parameters

Edit the Modelfile to adjust parameters:

```
FROM llama3

SYSTEM """Your custom system prompt here"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096
```

Then create the model:

```bash
ollama create collegeadvisor-custom -f Modelfile
```

## ChromaDB Collections

The system creates specialized collections:

### Collections Created

1. **institutions** - College and university data
   - Institutional characteristics
   - Admissions statistics
   - Costs and financial aid
   - Student demographics

2. **programs** - Academic programs and majors
   - Program descriptions
   - Degree requirements
   - Field of study data

3. **admissions** - Admissions requirements
   - Test score ranges
   - GPA requirements
   - Application deadlines

4. **experiences** - Student reviews and experiences
   - Campus culture
   - Student satisfaction
   - Quality of life

5. **outcomes** - Career outcomes
   - Post-graduation earnings
   - Employment rates
   - Career trajectories

6. **qa_pairs** - Training Q&A pairs
   - Instruction tuning data
   - Domain-specific knowledge

### Querying Collections

```python
from college_advisor_data.storage.collection_manager import CollectionManager

manager = CollectionManager()
client = manager.get_client("institutions")

# Search for institutions
results = client.search(
    query_text="selective universities in California",
    n_results=10
)
```

## Training Datasets Generated

### 1. Alpaca Format (`instruction_dataset_alpaca.json`)
Standard instruction tuning format:
```json
{
  "instruction": "What is the admission rate at Harvard?",
  "input": "",
  "output": "Harvard has an admission rate of approximately 3-4%."
}
```

### 2. JSONL Format (`instruction_dataset.jsonl`)
Line-delimited JSON for streaming:
```json
{"prompt": "What is...", "completion": "Harvard has..."}
```

### 3. Ollama Format (`instruction_dataset_ollama.txt`)
Conversational format for Ollama:
```
### Human: What is the admission rate at Harvard?
### Assistant: Harvard has an admission rate of approximately 3-4%.
```

### 4. Modelfile (`Modelfile`)
Ollama model configuration with system prompt and parameters.

## Integration with CollegeAdvisor-api

### 1. Ensure Ollama is Running

```bash
ollama serve
```

### 2. Verify Model is Available

```bash
ollama list
```

You should see `collegeadvisor` in the list.

### 3. Configure API to Use Fine-Tuned Model

In CollegeAdvisor-api repository, set environment variable:

```bash
export OLLAMA_MODEL=collegeadvisor
```

Or in `.env` file:
```
OLLAMA_MODEL=collegeadvisor
```

### 4. Test API Integration

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the admission requirements for Stanford?"}'
```

## Data Sources

### Primary Sources (Implemented)

1. **College Scorecard**
   - Coverage: 7,000+ institutions
   - Data: Admissions, costs, outcomes
   - Update: Annual
   - Quality: Official government data

2. **IPEDS (Integrated Postsecondary Education Data System)**
   - Coverage: 6,700+ institutions
   - Data: Comprehensive institutional data
   - Update: Annual
   - Quality: Federal reporting data

### Secondary Sources (Planned)

3. **Common Data Set (CDS)**
   - Coverage: 1,000+ selective institutions
   - Data: Detailed admissions requirements
   - Update: Annual
   - Quality: Institution-reported

4. **University Rankings**
   - Sources: QS, THE, US News
   - Data: Prestige indicators
   - Update: Annual

## Monitoring and Validation

### Check ChromaDB Collections

```python
from college_advisor_data.storage.collection_manager import CollectionManager

manager = CollectionManager()
stats = manager.get_collection_stats()
print(stats)
```

### Export Collection for Review

```python
manager.export_collection_to_json(
    "institutions",
    Path("data/exports/institutions_export.json"),
    limit=100
)
```

### Test Model Quality

Create a test script:

```python
import ollama

questions = [
    "What is the admission rate at MIT?",
    "Tell me about Stanford's computer science program",
    "What are the costs of attending Harvard?",
]

for question in questions:
    response = ollama.chat(model='collegeadvisor', messages=[
        {'role': 'user', 'content': question}
    ])
    print(f"Q: {question}")
    print(f"A: {response['message']['content']}\n")
```

## Troubleshooting

### ChromaDB Connection Issues

```bash
# Check if ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# Restart ChromaDB
chroma run --path ./chroma_data --port 8000
```

### Ollama Issues

```bash
# Check Ollama status
ollama list

# Restart Ollama
killall ollama
ollama serve
```

### Data Collection Failures

```bash
# Run with verbose logging
LOG_LEVEL=DEBUG python scripts/prepare_finetuning.py --collect-only
```

### Memory Issues

If you encounter memory issues:
- Reduce batch size in config: `BATCH_SIZE=50`
- Process data in smaller chunks
- Use a machine with more RAM

## Performance Optimization

### Embedding Generation

Use GPU acceleration if available:
```python
# In config
EMBEDDING_DEVICE=cuda  # or 'mps' for Mac
```

### ChromaDB Performance

```bash
# Use persistent storage
chroma run --path ./chroma_data --port 8000
```

### Ollama Performance

```bash
# Use GPU acceleration
ollama run collegeadvisor --gpu
```

## Next Steps

After successful fine-tuning:

1. **Evaluate Model Performance**
   - Test with diverse queries
   - Compare with base model
   - Measure accuracy and relevance

2. **Iterate on Training Data**
   - Add more Q&A pairs
   - Include domain-specific knowledge
   - Refine system prompts

3. **Deploy to Production**
   - Export model for API use
   - Set up monitoring
   - Configure auto-scaling

4. **Continuous Improvement**
   - Collect user feedback
   - Retrain periodically
   - Update with new data sources

## Support and Resources

- **Documentation**: See PRODUCTION_DEPLOYMENT_GUIDE.md
- **API Integration**: See CollegeAdvisor-api repository
- **Data Sources**: See DATA_SOURCES_STRATEGY.md
- **Issues**: Check logs in `logs/pipeline.log`

## Success Criteria

Your system is ready for production when:

✅ All readiness tests pass
✅ 5,000+ institutions in ChromaDB
✅ Training datasets generated successfully
✅ Fine-tuned model responds accurately
✅ API integration working
✅ Response time < 10 seconds
✅ Accuracy > 90% on test queries

