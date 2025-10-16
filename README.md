# 🎓 CollegeAdvisor Data Pipeline & Fine-Tuning

A production-ready data pipeline and fine-tuning system for college admissions AI assistance.

---

## 🚀 Quick Start - Fine-Tuning

### One-Command Fine-Tuning

```bash
# 1. Activate virtual environment
source venv_finetune/bin/activate

# 2. Run fine-tuning
./run_finetuning.sh
```

That's it! The script will:
- ✅ Validate your system
- ✅ Download training data from R2
- ✅ Process and validate data
- ✅ Train the model
- ✅ Save checkpoints and final model

**See:** [`UNIFIED_FINETUNING_GUIDE.md`](UNIFIED_FINETUNING_GUIDE.md) for complete documentation.

---

## 📋 Table of Contents

- [Fine-Tuning](#fine-tuning)
- [Data Pipeline](#data-pipeline)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Support](#support)

---

## 🎯 Fine-Tuning

### Unified Fine-Tuning System

We've consolidated **14 different scripts** into a **single, production-ready solution**:

**Main Script:** `unified_finetune.py`
**Launcher:** `run_finetuning.sh`
**Documentation:** `UNIFIED_FINETUNING_GUIDE.md`

### Features

- ✅ **Automatic R2 Data Fetching** - Downloads training data with integrity verification
- ✅ **Comprehensive Validation** - Pre-flight checks for dependencies, disk space, memory
- ✅ **MacBook Optimized** - Works on Apple Silicon (MPS) and Intel (CPU)
- ✅ **Robust Error Handling** - Extensive error checking with clear messages
- ✅ **Memory Efficient** - Optimized for MacBook hardware constraints
- ✅ **Checkpoint Support** - Automatic saving with resume capability
- ✅ **Real-time Monitoring** - Progress tracking with detailed logging

### Quick Commands

```bash
# Run fine-tuning
./run_finetuning.sh

# Or run directly
python unified_finetune.py
```

### Documentation

- **[Unified Fine-Tuning Guide](UNIFIED_FINETUNING_GUIDE.md)** - Complete usage guide
- **[Migration Guide](MIGRATION_TO_UNIFIED_FINETUNING.md)** - Migrating from old scripts
- **[Consolidation Summary](FINETUNING_CONSOLIDATION_SUMMARY.md)** - Technical details

---

## 📊 Data Pipeline

### Overview

Production-ready data collection and processing pipeline with:
- Multiple data source collectors
- Real-time quality monitoring
- Automated pipelines
- R2 cloud storage integration

### Data Sources

1. **Government APIs**
   - College Scorecard API
   - IPEDS Data
   - State Education APIs

2. **Institutional Data**
   - Carnegie Classification
   - University websites
   - Financial aid databases

3. **Social Media**
   - Reddit discussions
   - Twitter mentions
   - YouTube content

4. **User Data** (Production)
   - Authentication events
   - User profiles
   - Interaction data

### Data Collection

```bash
# Collect from all sources
python -m college_advisor_data.cli collect-all

# Collect from specific source
python -m college_advisor_data.cli collect --source scorecard
```

### Data Quality Monitoring

```bash
# Run quality checks
python monitoring/data_quality_monitor.py

# View quality reports
ls data/quality_reports/
```

---

## 📁 Project Structure

```
CollegeAdvisor-data/
├── unified_finetune.py              # 🎯 Main fine-tuning script
├── run_finetuning.sh                # 🚀 Fine-tuning launcher
├── UNIFIED_FINETUNING_GUIDE.md      # 📖 Complete guide
│
├── college_advisor_data/            # Core data pipeline
│   ├── ingestion/                   # Data ingestion
│   ├── preprocessing/               # Data processing
│   ├── embedding/                   # Vector embeddings
│   ├── storage/                     # R2 storage client
│   └── evaluation/                  # Quality evaluation
│
├── collectors/                      # Data collectors
│   ├── government.py               # Government APIs
│   ├── web_scrapers.py             # Web scraping
│   ├── social_media.py             # Social media
│   └── financial_aid.py            # Financial aid data
│
├── ai_training/                     # AI training modules
│   ├── finetuning_data_prep.py     # Data preparation
│   ├── training_pipeline.py        # Training pipeline
│   ├── continuous_learning.py      # Continuous learning
│   └── data_quality.py             # Quality monitoring
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
│   ├── training/                   # Training datasets
│   └── quality_reports/            # Quality reports
│
└── logs/                           # Logs
    ├── finetuning/                 # Fine-tuning logs
    └── pipeline.log                # Pipeline logs
```

---

## 🔧 Installation

### Prerequisites

- Python 3.8+
- 8GB+ RAM (16GB recommended)
- 10GB+ free disk space

### Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd CollegeAdvisor-data

# 2. Create virtual environment
python3 -m venv venv_finetune
source venv_finetune/bin/activate

# 3. Install dependencies
pip install -r requirements-finetuning.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### R2 Configuration

Ensure your `.env` file contains:

```bash
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=collegeadvisor-finetuning-data
COLLEGE_SCORECARD_API_KEY=your_api_key
```

---

## ⚙️ Configuration

### Fine-Tuning Configuration

Edit `unified_finetune.py` - `FineTuningConfig` class:

```python
@dataclass
class FineTuningConfig:
    # Model
    model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    max_seq_length: int = 1024

    # LoRA
    lora_r: int = 32
    lora_alpha: int = 64

    # Training
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 2
    learning_rate: float = 2e-5
```

### Pipeline Configuration

- **API Config:** `configs/api_config.yaml`
- **Database Config:** `configs/database_config.yaml`
- **Quality Monitoring:** `data/quality_monitoring_config.yaml`

---

## 📚 Documentation

### Fine-Tuning

- **[Unified Fine-Tuning Guide](UNIFIED_FINETUNING_GUIDE.md)** - Complete usage guide
- **[Migration Guide](MIGRATION_TO_UNIFIED_FINETUNING.md)** - Migrating from old scripts
- **[Consolidation Summary](FINETUNING_CONSOLIDATION_SUMMARY.md)** - Technical overview

### Data Pipeline

- **[Quick Start](QUICK_START.md)** - Getting started
- **[Production Deployment](PRODUCTION_DEPLOYMENT_GUIDE.md)** - Production setup
- **[Data Expansion Strategy](DATA_EXPANSION_STRATEGY.md)** - Expanding data sources

### API & Integration

- **[API Integration](API_INTEGRATION_INSTRUCTIONS.md)** - API setup
- **[R2 Setup](R2_SETUP_COMPLETE.md)** - R2 configuration

---

## 🆘 Support

### Troubleshooting

1. **Check logs:** `logs/finetuning/unified_finetune_*.log`
2. **Review guides:** See documentation links above
3. **Verify setup:** Run system validation in the script

### Common Issues

**Issue: R2 credentials not found**
```bash
# Check .env file
cat .env | grep R2_
```

**Issue: Out of memory**
```python
# Reduce batch size in FineTuningConfig
per_device_train_batch_size = 1
gradient_accumulation_steps = 16
```

**Issue: Dependencies missing**
```bash
# Reinstall dependencies
pip install -r requirements-finetuning.txt
```

---

## 🎯 Next Steps

1. **Run Fine-Tuning**
   ```bash
   ./run_finetuning.sh
   ```

2. **Test Your Model**
   - See testing section in `UNIFIED_FINETUNING_GUIDE.md`

3. **Deploy to Production**
   - See `PRODUCTION_DEPLOYMENT_GUIDE.md`

4. **Expand Data Sources**
   - See `DATA_EXPANSION_STRATEGY.md`

---

## 📊 Status

- ✅ **Fine-Tuning:** Production Ready
- ✅ **Data Pipeline:** Production Ready
- ✅ **R2 Integration:** Complete
- ✅ **Quality Monitoring:** Active
- ✅ **Documentation:** Complete

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built with:
- HuggingFace Transformers
- PyTorch
- PEFT (Parameter-Efficient Fine-Tuning)
- Cloudflare R2
- ChromaDB

---

**Ready to fine-tune? Run:** `./run_finetuning.sh`
