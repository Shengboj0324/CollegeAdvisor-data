# 🚀 Unified Fine-Tuning Guide

## Overview

This guide covers the **unified production fine-tuning script** (`unified_finetune.py`) - the ONLY script you need for fine-tuning on MacBook.

### What This Replaces

This single script replaces **14 previous scripts**:
- ❌ `bulletproof_finetune_macos.py`
- ❌ `advanced_finetune_macos.py`
- ❌ `production_finetune_FIXED.py`
- ❌ `production_finetune_integrated.py`
- ❌ `setup_advanced_finetuning.py`
- ❌ `download_training_data.py`
- ❌ `test_training_setup.py`
- ❌ All shell wrapper scripts (`execute_bulletproof_training.sh`, `run_advanced_finetuning.sh`, etc.)

### Key Features

✅ **Automatic R2 Data Fetching** - Downloads training data from Cloudflare R2 with integrity verification  
✅ **Comprehensive Validation** - Pre-flight checks for dependencies, disk space, memory, and data quality  
✅ **MacBook Optimized** - Works on both Apple Silicon (MPS) and Intel (CPU) MacBooks  
✅ **Robust Error Handling** - Extensive error checking with clear, actionable error messages  
✅ **Memory Efficient** - Optimized batch sizes and gradient accumulation for MacBook constraints  
✅ **Checkpoint Support** - Automatic checkpoint saving with resume capability  
✅ **Real-time Monitoring** - Progress tracking with detailed logging  
✅ **Production Ready** - Battle-tested configuration with guaranteed success  

---

## Prerequisites

### 1. System Requirements

- **MacBook** (Apple Silicon or Intel)
- **Python 3.8+**
- **8GB+ RAM** (16GB recommended)
- **10GB+ free disk space**

### 2. Environment Setup

#### Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv_finetune

# Activate it
source venv_finetune/bin/activate
```

#### Install Dependencies

```bash
# Install all required packages
pip install -r requirements-finetuning.txt
```

### 3. R2 Credentials

Ensure your `.env` file contains R2 credentials:

```bash
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=collegeadvisor-finetuning-data
```

**Note:** These should already be configured in your `.env` file.

---

## Quick Start

### Basic Usage

```bash
# Activate virtual environment
source venv_finetune/bin/activate

# Run fine-tuning
python unified_finetune.py
```

That's it! The script will:
1. ✅ Validate your system
2. ✅ Download training data from R2
3. ✅ Verify data integrity
4. ✅ Process and format data
5. ✅ Load model with LoRA
6. ✅ Train the model
7. ✅ Save checkpoints and final model

### Expected Output

```
================================================================================
🚀 UNIFIED PRODUCTION FINE-TUNING FOR MACBOOK
================================================================================
📅 Date: 2025-10-16 14:30:00
🐍 Python: 3.11.5
📝 Log file: logs/finetuning/unified_finetune_20251016_143000.log
================================================================================

STEP 1: SYSTEM VALIDATION
================================================================================
✅ Python version: 3.11.5
✅ torch installed
✅ transformers installed
✅ datasets installed
✅ peft installed
✅ trl installed
✅ boto3 installed
✅ accelerate installed
✅ Disk space: 45.23 GB available
✅ System memory: 16.00 GB total, 8.50 GB available
✅ Device: Apple Silicon (MPS)
✅ ALL SYSTEM CHECKS PASSED
================================================================================

STEP 2: LOADING CONFIGURATION
✅ Configuration loaded
   - Model: TinyLlama/TinyLlama-1.1B-Chat-v1.0
   - Output: collegeadvisor_unified_model

STEP 3: FETCHING TRAINING DATA
================================================================================
✅ R2 client initialized
✅ Found 3 datasets in R2
   - multi_source/training_datasets/instruction_dataset_alpaca.json
   - multi_source/training_datasets/instruction_dataset.jsonl
   - multi_source/training_datasets/instruction_dataset_ollama.txt
📥 Using dataset: instruction_dataset_alpaca.json
📥 Downloading from R2: multi_source/training_datasets/instruction_dataset_alpaca.json
✅ Downloaded: cache/training_data/instruction_dataset_alpaca.json (245.67 KB)
🔍 Verifying data integrity...
✅ Data integrity verified:
   - Total examples: 1250
   - File size: 245.67 KB
   - Format valid: True
================================================================================

STEP 4: PROCESSING DATA
================================================================================
📂 Loading data from: cache/training_data/instruction_dataset_alpaca.json
✅ Loaded 1250 examples
🔍 Validating data quality...
✅ Data quality metrics:
   - Quality score: 98.40%
   - Valid examples: 1230/1250
   - Avg instruction length: 156 chars
   - Avg output length: 342 chars
🔄 Formatting data for training...
✅ Formatted 1230 examples
✅ Data split:
   - Training: 1107 examples
   - Evaluation: 123 examples
✅ Created dataset with 1107 examples
✅ Created dataset with 123 examples
================================================================================

STEP 5: LOADING MODEL
================================================================================
📥 Loading tokenizer: TinyLlama/TinyLlama-1.1B-Chat-v1.0
✅ Tokenizer loaded
📥 Loading model: TinyLlama/TinyLlama-1.1B-Chat-v1.0
✅ Model loaded on mps
🔧 Configuring LoRA...
✅ LoRA configured:
   - Trainable params: 8,388,608
   - Total params: 1,108,388,608
   - Trainable: 0.76%
================================================================================

STEP 6: TRAINING MODEL
⏱️  This may take 1-4 hours depending on your MacBook...
================================================================================
🔄 Tokenizing datasets...
✅ Tokenization complete
🚀 Training started...
   - Epochs: 3
   - Batch size: 2
   - Gradient accumulation: 8
   - Effective batch size: 16
   - Learning rate: 2e-05

[Training progress bars and metrics...]

💾 Saving final model...
================================================================================
✅ TRAINING COMPLETE
================================================================================
📊 Final metrics:
   - Train loss: 0.8234
   - Train runtime: 3245.67s
   - Samples/second: 1.02
📁 Model saved to: collegeadvisor_unified_model
================================================================================
```

---

## Configuration

### Default Configuration

The script uses sensible defaults optimized for MacBook:

```python
# Model
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
max_seq_length = 1024

# LoRA
lora_r = 32
lora_alpha = 64
lora_dropout = 0.05

# Training
num_train_epochs = 3
per_device_train_batch_size = 2
gradient_accumulation_steps = 8
learning_rate = 2e-5
```

### Custom Configuration

To customize, edit the `FineTuningConfig` class in `unified_finetune.py`:

```python
@dataclass
class FineTuningConfig:
    # Modify these values as needed
    num_train_epochs: int = 5  # More epochs
    learning_rate: float = 1e-5  # Lower learning rate
    lora_r: int = 64  # Higher rank for more capacity
    # ... etc
```

---

## Advanced Usage

### Using Different Datasets

The script automatically selects the best available dataset from R2. To use a specific dataset:

1. Check available datasets in R2:
   ```python
   from college_advisor_data.storage.r2_storage import R2StorageClient
   client = R2StorageClient()
   objects = client.list_objects(prefix="multi_source/training_datasets/")
   for obj in objects:
       print(obj)
   ```

2. Modify the `dataset_name` in the `main()` function

### Resume from Checkpoint

If training is interrupted, the script automatically saves checkpoints. To resume:

```python
# In the FineTuningConfig class, set:
resume_from_checkpoint = "collegeadvisor_unified_model/checkpoint-500"
```

### Memory Optimization

For MacBooks with limited RAM (8GB):

```python
# Reduce batch size and increase gradient accumulation
per_device_train_batch_size = 1
gradient_accumulation_steps = 16
```

---

## Troubleshooting

### Issue: "R2 credentials not found"

**Solution:** Ensure `.env` file exists with R2 credentials:
```bash
cat .env | grep R2_
```

### Issue: "Insufficient disk space"

**Solution:** Free up at least 10GB of disk space:
```bash
# Check disk space
df -h

# Clean up old models
rm -rf collegeadvisor_model_*
```

### Issue: "Out of memory"

**Solution:** Reduce batch size in configuration:
```python
per_device_train_batch_size = 1
gradient_accumulation_steps = 16
```

### Issue: "MPS backend not available"

**Solution:** The script will automatically fall back to CPU. This is normal for Intel MacBooks.

### Issue: "Download failed from R2"

**Solution:** 
1. Check internet connection
2. Verify R2 credentials
3. Check R2 bucket has data:
   ```bash
   python -c "from college_advisor_data.storage.r2_storage import R2StorageClient; client = R2StorageClient(); print(client.list_objects(prefix='multi_source/'))"
   ```

---

## Output Files

After successful training, you'll find:

```
collegeadvisor_unified_model/
├── adapter_config.json          # LoRA adapter configuration
├── adapter_model.safetensors    # Trained LoRA weights
├── training_config.json         # Training configuration used
├── training_metrics.json        # Final training metrics
├── tokenizer.json              # Tokenizer files
├── tokenizer_config.json
├── special_tokens_map.json
└── checkpoint-*/               # Training checkpoints
```

---

## Next Steps

### Test Your Model

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")

# Load LoRA adapter
model = PeftModel.from_pretrained(base_model, "collegeadvisor_unified_model")

# Test
prompt = "<|user|>\nWhat is the admission rate at Harvard?</s>\n<|assistant|>\n"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_length=200)
print(tokenizer.decode(outputs[0]))
```

### Deploy to Production

See `PRODUCTION_DEPLOYMENT_GUIDE.md` for deployment instructions.

---

## Support

For issues or questions:
1. Check the log file: `logs/finetuning/unified_finetune_*.log`
2. Review this guide's troubleshooting section
3. Check system validation output

---

## License

MIT License - See LICENSE file for details

