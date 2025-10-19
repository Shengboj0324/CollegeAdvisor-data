# Finetuning Troubleshooting Guide for macOS

**Last Updated:** October 17, 2025  
**Platform:** macOS (Apple Silicon & Intel)  
**Single Source of Truth:** `unified_finetune.py` (Mac-first, HF/PEFT/Trainer)

---

## ⚠️ CRITICAL: Ignore CUDA-Centric Scripts

**DO NOT USE** `ai_training/run_sft.py` on macOS - it's CUDA-centric and will waste your time on Apple Silicon.

**USE INSTEAD:**
- ✅ `unified_finetune.py` - Main training script (Mac-first, HF/PEFT/Trainer)
- ✅ `ai_training/run_sft_cpu.py` - For tiny experiments only

---

## Data Contracts (Avoid NameError/KeyError at the Source)

### Alpaca Record (Preferred)

```json
{
  "instruction": "How do I improve my Common App essay on adversity?",
  "input": "",
  "output": "Focus on reflection over event. Show growth, decisions, outcomes..."
}
```

**Required fields:** `instruction`, `input`, `output`

### Conversational JSONL (If You Go Chat-Tuned)

```json
{
  "messages": [
    {"role": "user", "content": "What GPA do I need for Cornell engineering?"},
    {"role": "assistant", "content": "Target 3.8+ unweighted... context on rigor..."}
  ]
}
```

**Required schema:** `messages` array with `role` and `content` fields

### How to Generate Correct Format

Run `ai_training/finetuning_data_prep.py` to generate these from CDS/Q&A sources and you'll never hit schema name errors during training.

```bash
python ai_training/finetuning_data_prep.py
```

---

## Root Cause → Fix (The Errors You Hit)

### 1. ModuleNotFoundError: unsloth or bitsandbytes

**Symptom:** `ModuleNotFoundError: No module named 'unsloth'` or `bitsandbytes`

**Root Cause:** `run_sft.py` relies on CUDA-only stack

**Hard Fix:** Don't use it on macOS. Use `unified_finetune.py` or `ai_training/run_sft_cpu.py`.

---

### 2. ImportError: cannot import name 'Trainer' from transformers or TRL/PEFT mismatches

**Symptom:** 
```
ImportError: cannot import name 'Trainer' from 'transformers'
```

**Root Cause:** Incompatible package matrix (Transformers ↔ TRL ↔ PEFT)

**Hard Fix:** Pin exactly:
```bash
pip install transformers==4.40.2 trl<0.9.0 peft==0.11.1 accelerate==0.28.0
```

**Updated in:** `requirements-finetuning.txt`

---

### 3. ModuleNotFoundError: psutil (inside system checks)

**Symptom:** `ModuleNotFoundError: No module named 'psutil'`

**Root Cause:** `unified_finetune.py` uses psutil for RAM checks

**Hard Fix:** 
```bash
pip install psutil
```

**Updated in:** `requirements-finetuning.txt` (already included)

---

### 4. boto3/botocore complaints or "cannot resolve endpoint"

**Symptom:** 
```
botocore.exceptions.EndpointConnectionError: Could not connect to the endpoint URL
```

**Root Cause:** Missing/incorrect R2 env vars

**Hard Fix:** Set R2 environment variables:
```bash
export R2_ACCOUNT_ID=your_account_id
export R2_ACCESS_KEY_ID=your_access_key
export R2_SECRET_ACCESS_KEY=your_secret_key
export R2_BUCKET_NAME=collegeadvisor-finetuning-data  # optional
```

Add to `~/.zshrc` or `~/.bash_profile` for persistence.

**Verification:** Run `scripts/check_finetuning_setup.py`

---

### 5. No module named college_advisor_data / relative import failures

**Symptom:** 
```
ModuleNotFoundError: No module named 'college_advisor_data'
```

**Root Cause:** Running a script from the wrong cwd or without package context

**Hard Fix:** Run from repo root. Or add root to PYTHONPATH. Prefer:
```bash
python unified_finetune.py
```

Over direct `scripts/*.py` execution.

---

### 6. Name/key errors on dataset fields (e.g., 'instruction' KeyError)

**Symptom:** 
```
KeyError: 'instruction'
NameError: name 'instruction' is not defined
```

**Root Cause:** Input JSON/JSONL schema not matching `{instruction, input, output}`

**Hard Fix:** Use `ai_training/finetuning_data_prep.py` to generate Alpaca-schema. Validate with its formatter before training.

**Validation:** The script now includes `validate_dataset_schema()` method.

---

### 7. MPS kernel "not implemented" or slowdowns

**Symptom:** 
```
NotImplementedError: The operator 'aten::some_op' is not currently implemented for the MPS device
```

**Root Cause:** Apple Silicon missing some kernels

**Hard Fix:** Set `PYTORCH_ENABLE_MPS_FALLBACK=1`. Keep batch size small; increase gradient accumulation.

```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

**Already set in:** `unified_finetune.py` (line 37)

---

## Quick Setup Checklist

### 1. Environment Setup

```bash
# Clone/navigate to repo
cd /path/to/CollegeAdvisor-data

# Create virtual environment (if not exists)
python3 -m venv venv_finetune
source venv_finetune/bin/activate

# Install dependencies with correct versions
pip install -r requirements-finetuning.txt
```

### 2. Set Environment Variables

```bash
# Add to ~/.zshrc or ~/.bash_profile
export R2_ACCOUNT_ID=your_account_id
export R2_ACCESS_KEY_ID=your_access_key
export R2_SECRET_ACCESS_KEY=your_secret_key
export R2_BUCKET_NAME=collegeadvisor-finetuning-data
export PYTORCH_ENABLE_MPS_FALLBACK=1

# Reload shell
source ~/.zshrc  # or source ~/.bash_profile
```

### 3. Verify Setup

```bash
python scripts/check_finetuning_setup.py
```

This will check:
- ✅ R2 environment variables
- ✅ Package versions (transformers, peft, trl, accelerate, psutil)
- ✅ MPS support and fallback setting
- ✅ Training data files
- ✅ Training scripts

### 4. Generate Training Data

```bash
python ai_training/finetuning_data_prep.py
```

This generates:
- `data/finetuning/instruction_dataset_alpaca.json` - Alpaca format
- `data/finetuning/conversational_dataset.jsonl` - Chat format
- `data/finetuning/preparation_stats.json` - Statistics

### 5. Run Training

```bash
python unified_finetune.py
```

---

## Package Version Matrix (macOS Compatible)

| Package | Version | Reason |
|---------|---------|--------|
| transformers | ==4.40.2 | Exact pin for compatibility |
| trl | <0.9.0 | Avoid breaking changes |
| peft | ==0.11.1 | Exact pin for compatibility |
| accelerate | ==0.28.0 | Exact pin for compatibility |
| psutil | >=5.9.0 | System checks |
| torch | >=2.0.0 | MPS support |

**Install command:**
```bash
pip install transformers==4.40.2 trl<0.9.0 peft==0.11.1 accelerate==0.28.0 psutil
```

---

## Common Errors and Solutions

### Error: "CUDA not available"
**Solution:** This is expected on macOS. The script will use MPS (Apple Silicon) or CPU.

### Error: "Out of memory"
**Solution:** Reduce batch size in config:
```python
per_device_train_batch_size: int = 1  # Reduce from 2
gradient_accumulation_steps: int = 16  # Increase from 8
```

### Error: "Dataset is empty"
**Solution:** Generate training data first:
```bash
python ai_training/finetuning_data_prep.py
```

### Error: "Missing required fields in data"
**Solution:** Your data doesn't match the Alpaca schema. Regenerate with `finetuning_data_prep.py`.

---

## File Structure

```
CollegeAdvisor-data/
├── unified_finetune.py              # ✅ Main training script (USE THIS)
├── ai_training/
│   ├── finetuning_data_prep.py     # ✅ Data preparation
│   ├── run_sft_cpu.py              # ✅ CPU-only (tiny experiments)
│   └── run_sft.py                  # ❌ IGNORE (CUDA-only)
├── scripts/
│   └── check_finetuning_setup.py   # ✅ Setup verification
├── requirements-finetuning.txt      # ✅ macOS-compatible deps
└── data/
    └── finetuning/                  # Generated training data
        ├── instruction_dataset_alpaca.json
        └── conversational_dataset.jsonl
```

---

## Best Practices

1. **Always run from repo root:** `python unified_finetune.py`
2. **Generate data first:** `python ai_training/finetuning_data_prep.py`
3. **Verify setup:** `python scripts/check_finetuning_setup.py`
4. **Use exact package versions:** `pip install -r requirements-finetuning.txt`
5. **Set MPS fallback:** Already done in `unified_finetune.py`
6. **Keep batch size small:** Start with 1-2, increase gradient accumulation
7. **Monitor memory:** Use Activity Monitor to watch RAM usage

---

## Getting Help

If you encounter issues:

1. Run the setup checker:
   ```bash
   python scripts/check_finetuning_setup.py
   ```

2. Check the logs:
   ```bash
   tail -f logs/finetuning/unified_finetune_*.log
   ```

3. Verify data schema:
   ```bash
   python -c "from ai_training.finetuning_data_prep import FineTuningDataPreparator; \
              prep = FineTuningDataPreparator(); \
              prep.validate_dataset_schema('data/finetuning/instruction_dataset_alpaca.json', 'alpaca')"
   ```

---

## Summary

✅ **DO:**
- Use `unified_finetune.py` for training
- Pin package versions exactly
- Generate data with `finetuning_data_prep.py`
- Set R2 environment variables
- Enable MPS fallback (already done)
- Run from repo root

❌ **DON'T:**
- Use `ai_training/run_sft.py` on macOS
- Mix package versions
- Skip data validation
- Run scripts from wrong directory
- Forget to set environment variables

---

**Ready to train?**

```bash
# 1. Verify setup
python scripts/check_finetuning_setup.py

# 2. Generate data
python ai_training/finetuning_data_prep.py

# 3. Train!
python unified_finetune.py
```

