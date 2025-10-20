# CollegeAdvisor Data Pipeline & Fine-Tuning System

**Author:** Shengbo Jiang  
**Date:** 10/15/2025

A production-grade data pipeline and model fine-tuning system for college admissions information retrieval and question answering.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Data Pipeline](#data-pipeline)
- [Fine-Tuning System](#fine-tuning-system)
- [Technical Implementation](#technical-implementation)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)

---

## Overview

This system implements a complete data pipeline and fine-tuning infrastructure for college admissions AI assistance. It integrates multiple authoritative data sources, processes them into structured formats, and fine-tunes language models for domain-specific question answering.

### Key Components

1. Multi-Source Data Collection: Aggregates data from College Scorecard API, IPEDS, Carnegie Classification, and Common Data Set PDFs
2. Data Processing Pipeline: Transforms raw data into training-ready instruction-response pairs
3. Fine-Tuning System: LoRA-based parameter-efficient fine-tuning for TinyLlama models
4. RAG Integration: Retrieval-augmented generation using ChromaDB vector store
5. Production API: FastAPI-based REST API with Docker deployment

---

## Architecture

### System Design

```
Data Sources → Collection → Processing → Storage (R2) → Fine-Tuning → Deployment
     ↓            ↓            ↓             ↓              ↓            ↓
  APIs/PDFs   Collectors   Processors   Cloudflare    LoRA/PEFT    Docker/K8s
```

### Data Flow

1. Collection: Automated collectors fetch data from APIs and parse PDFs
2. Validation: Schema validation and quality checks
3. Processing: Normalization, deduplication, enrichment
4. Storage: Dual storage in R2 (raw) and ChromaDB (embeddings)
5. Training Data Generation: Conversion to instruction-response format

---

## Data Pipeline

### Data Sources

**1. College Scorecard API**
- Source: U.S. Department of Education
- Coverage: 7,000+ institutions
- Variables: 1,900+ data points per institution
- Data: Admissions, costs, financial aid, outcomes, earnings, debt

**2. IPEDS (Integrated Postsecondary Education Data System)**
- Source: National Center for Education Statistics
- Coverage: 6,500+ institutions
- Data: Institutional characteristics, enrollment, completions, finance, human resources

**3. Carnegie Classification**
- Source: Indiana University Center for Postsecondary Research
- Coverage: 4,000+ institutions
- Data: Basic classification, research activity, enrollment profiles

**4. Common Data Set (CDS) PDFs**
- Source: Individual universities
- Coverage: 99 universities (manually collected)
- Data: Standardized admissions, enrollment, test scores, costs

### Collection Architecture

```
collectors/
├── base_collector.py          # Abstract base class
├── comprehensive_data_collector.py  # Main orchestrator
├── government.py              # College Scorecard, IPEDS
└── web_scrapers.py           # CDS PDF extraction
```

Implementation:
- Asynchronous HTTP requests for API efficiency
- PDF parsing using PyPDF2 and pdfplumber
- Rate limiting and retry logic
- Caching layer to minimize API calls

### Data Processing

Pipeline Stages:

1. Extraction: Raw data retrieval from sources
2. Validation: Schema validation using Pydantic models
3. Normalization: Standardize field names, units, formats
4. Enrichment: Cross-reference data across sources
5. Deduplication: Merge records by UNITID/OPEID
6. Quality Checks: Completeness, consistency, accuracy metrics

Output Formats:
- master_dataset.json: Merged data from all sources (3.92 MB)
- processed_real_data.json: Cleaned and validated (3.92 MB)
- institutions.json: Structured institution records (0.73 MB)

### Training Data Generation

Instruction-Response Pair Generation:

```
Input:
{
  "institution": "Stanford University",
  "admission_rate": 0.0361,
  "sat_composite_25": 1470
}

Output:
{
  "instruction": "What is the admission rate at Stanford University?",
  "input": "",
  "output": "The admission rate at Stanford University is approximately 3.61%."
}
```

Categories:
- Admissions (acceptance rates, requirements)
- Costs (tuition, fees, financial aid)
- Location (city, state, setting)
- Demographics (enrollment, diversity)
- Academics (programs, majors, faculty)
- Outcomes (graduation rates, earnings)

Dataset Statistics:
- Total examples: 7,888
- Average response length: 62 characters
- Format: Alpaca JSON, JSONL, Ollama text

---

## Fine-Tuning System

### Model Architecture

Base Model: TinyLlama/TinyLlama-1.1B-Chat-v1.0
- Parameters: 1.1 billion
- Architecture: Llama 2 with optimizations
- Context length: 2048 tokens
- Training: Pre-trained on 3 trillion tokens

Fine-Tuning Method: LoRA (Low-Rank Adaptation)
- Technique: Parameter-efficient fine-tuning
- Trainable parameters: ~0.5% of total
- Memory efficiency: Fits on consumer hardware
- Inference: Merge adapters or load separately

### LoRA Configuration

```python
lora_config = LoraConfig(
    r=8,                    # Rank of update matrices
    lora_alpha=16,          # Scaling factor
    target_modules=["q_proj", "v_proj"],  # Attention layers
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)
```

Rationale:
- Low rank (r=8) prevents overfitting on small dataset
- Target q_proj and v_proj for attention mechanism tuning
- Alpha=16 provides 2x scaling for stability

### Training Configuration

Hyperparameters:
```python
training_args = TrainingArguments(
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,  # Effective batch size: 16
    learning_rate=2e-5,
    warmup_steps=100,
    max_grad_norm=1.0,
    fp16=False,  # CPU training
    optim="adamw_torch",
    logging_steps=10,
    save_steps=500,
)
```

Training Process:
1. Load base model and tokenizer
2. Apply LoRA adapters
3. Tokenize with label masking (train only on responses)
4. Train for 3 epochs (~1,479 steps)
5. Save adapter weights and configuration

Label Masking Implementation:
```python
# Mask instruction tokens with -100 (ignored in loss)
prefix = "<|user|>\n{instruction}</s>\n<|assistant|>\n"
prefix_tokens = tokenizer(prefix)["input_ids"]
labels[:len(prefix_tokens)] = -100  # Ignore in loss calculation
```

### Format Specification

TinyLlama Zephyr Format:
```
<|user|>
{instruction}</s>
<|assistant|>
{output}</s>
```

Critical Details:
- Use </s> as EOS token (not <|endoftext|>)
- Include </s> after both user and assistant messages
- No system message in this format

### Execution

Quick Start:
```bash
source venv_finetune/bin/activate
./run_finetuning.sh
```

Script: unified_finetune.py
- Automatic data download from R2
- Format validation and preprocessing
- Training with progress logging
- Checkpoint saving every 500 steps
- Final model export

Output:
- Adapter weights: adapter_model.safetensors
- Configuration: adapter_config.json
- Tokenizer: tokenizer.json, tokenizer_config.json
- Training metrics: training_args.bin

---

## Technical Implementation

### Innovations

1. Multi-Source Data Integration
   - Unified schema across heterogeneous sources
   - Conflict resolution using source priority
   - Cross-validation between datasets

2. Label Masking for Instruction Tuning
   - Prevents model from learning instruction patterns
   - Focuses training on response generation
   - Improves output quality and reduces repetition

3. Efficient Fine-Tuning
   - LoRA reduces trainable parameters by 99.5%
   - CPU-compatible training (no GPU required)
   - Gradient accumulation for larger effective batch size

4. Production-Ready Pipeline
   - Automated data collection and refresh
   - Error handling and retry logic
   - Comprehensive logging and monitoring
   - Docker containerization for deployment

### Technology Stack

Data Collection:
- Python 3.9+
- aiohttp (async HTTP)
- PyPDF2, pdfplumber (PDF parsing)
- Pydantic (validation)

Fine-Tuning:
- PyTorch 2.2.2
- Transformers 4.40.2
- PEFT 0.10.0 (LoRA)
- Datasets 2.18.0

Storage:
- Cloudflare R2 (object storage)
- ChromaDB (vector database)
- PostgreSQL (structured data)

Deployment:
- FastAPI (REST API)
- Docker, Docker Compose
- Kubernetes (optional)
- Nginx (reverse proxy)

### Performance Metrics

Data Pipeline:
- Collection time: ~2 hours for full refresh
- Processing throughput: ~1,000 institutions/minute
- Storage: 641.65 MB total

Fine-Tuning:
- Training time: 8-12 hours (CPU)
- Memory usage: ~8 GB RAM
- Model size: 2.2 GB (base) + 17 MB (adapters)

Inference:
- Latency: ~200ms per query (with RAG)
- Throughput: ~5 queries/second
- Memory: ~4 GB RAM

---

## Installation

### Prerequisites

- Python 3.9+
- 8 GB RAM minimum
- 50 GB disk space
- Virtual environment tool (venv, conda)

### Setup

1. Clone Repository
```bash
git clone <repository-url>
cd CollegeAdvisor-data
```

2. Create Virtual Environment
```bash
python3.9 -m venv venv_finetune
source venv_finetune/bin/activate
```

3. Install Dependencies
```bash
pip install -r requirements-locked.txt
```

4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required Environment Variables:
- R2_ACCOUNT_ID: Cloudflare R2 account ID
- R2_ACCESS_KEY_ID: R2 access key
- R2_SECRET_ACCESS_KEY: R2 secret key
- R2_BUCKET_NAME: Bucket name
- COLLEGE_SCORECARD_API_KEY: Department of Education API key

---

## Usage

### Fine-Tuning

Single Command:
```bash
source venv_finetune/bin/activate
./run_finetuning.sh
```

Manual Execution:
```bash
python unified_finetune.py
```

Output Location: collegeadvisor_unified_model/

### Data Collection

Full Pipeline:
```bash
python simple_data_ingest.py
```

Specific Collectors:
```python
from collectors import ComprehensiveDataCollector

collector = ComprehensiveDataCollector()
scorecard_data = collector.collect_scorecard()
ipeds_data = collector.collect_ipeds()
```

### API Deployment

Docker Compose:
```bash
./deploy.sh deploy
```

Manual Start:
```bash
python start_api.py
```

API Endpoints:
- GET /health: Health check
- POST /recommend: Get college recommendations
- POST /query: RAG-based question answering

---

## Project Structure

```
CollegeAdvisor-data/
├── unified_finetune.py              # Main fine-tuning script
├── run_finetuning.sh                # Fine-tuning launcher
├── simple_data_ingest.py            # Data ingestion
├── start_api.py                     # API server launcher
├── deploy.sh                        # Deployment script
│
├── college_advisor_data/            # Core data pipeline
│   ├── ingestion/                   # Data ingestion modules
│   ├── preprocessing/               # Data processing
│   ├── embedding/                   # Vector embeddings
│   ├── storage/                     # R2 storage client
│   └── evaluation/                  # Quality evaluation
│
├── collectors/                      # Data collectors
│   ├── base_collector.py           # Abstract base class
│   ├── comprehensive_data_collector.py
│   ├── government.py               # Government APIs
│   └── web_scrapers.py             # CDS PDF extraction
│
├── ai_training/                     # AI training modules
│   ├── finetuning_data_prep.py     # Data preparation
│   ├── training_pipeline.py        # Training orchestration
│   └── model_evaluation.py         # Model evaluation
│
├── api/                            # REST API
│   ├── main.py                     # FastAPI application
│   ├── rag_client.py               # RAG integration
│   └── models.py                   # Pydantic models
│
├── monitoring/                      # Monitoring & alerts
│   ├── data_quality_monitor.py     # Quality monitoring
│   └── pipeline_health_monitor.py  # Pipeline health
│
├── configs/                         # Configuration files
│   ├── api_config.yaml             # API endpoints
│   └── database_config.yaml        # Database config
│
├── data/                           # Data storage
│   ├── raw/                        # Raw data
│   ├── processed/                  # Processed data
│   └── training/                   # Training datasets
│
├── docker-compose.yml              # Docker orchestration
├── Dockerfile.api                  # API container
├── Dockerfile.data                 # Data pipeline container
│
├── requirements.txt                # Python dependencies
├── requirements-locked.txt         # Locked versions
│
├── README.md                       # This file
├── PRODUCTION_DEPLOYMENT_GUIDE.md  # Deployment guide
└── DATA_MAPPING_SUMMARY.md         # Data mapping reference
```

---

## License

This project is proprietary software developed by Shengbo Jiang.

