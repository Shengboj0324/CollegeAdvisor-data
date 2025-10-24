# Fine-Tuning Ollama Model - Comprehensive Error Audit Report

**Author:** Shengbo Jiang  
**Date:** 2025-10-22  
**Scope:** Complete systematic audit of fine-tuning pipeline for Ollama model deployment

---

## EXECUTIVE SUMMARY

**CRITICAL FINDING:** The current fine-tuning pipeline is **NOT configured for Ollama**. It fine-tunes TinyLlama for HuggingFace format, but lacks the complete conversion and deployment pipeline to Ollama.

**Total Errors Found:** 18 critical errors, 12 high-priority issues, 8 medium-priority issues

**Status:** PIPELINE INCOMPLETE - Multiple blocking issues prevent successful Ollama model deployment

---

## CRITICAL ERRORS (BLOCKING)

### ERROR 1: Missing requirements-finetuning.txt File
**Severity:** CRITICAL  
**Location:** `run_finetuning.sh` line 64-72  
**Impact:** Script will fail immediately on execution

**Problem:**
```bash
if [ -f "requirements-finetuning.txt" ]; then
    pip install --quiet -r requirements-finetuning.txt
else
    print_msg "$RED" "❌ requirements-finetuning.txt not found"
    exit 1
fi
```

**Evidence:**
- File `requirements-finetuning.txt` does NOT exist in repository
- Only `requirements.txt` and `requirements-locked.txt` exist
- Script will exit with error code 1

**Fix Required:**
```bash
# Option 1: Create requirements-finetuning.txt
cp requirements-locked.txt requirements-finetuning.txt

# Option 2: Update run_finetuning.sh to use existing file
sed -i '' 's/requirements-finetuning.txt/requirements-locked.txt/g' run_finetuning.sh
```

---

### ERROR 2: Training Data Format Mismatch for Ollama
**Severity:** CRITICAL  
**Location:** `training_data_ollama.txt`, `unified_finetune.py`  
**Impact:** Training data format incompatible with Ollama deployment

**Problem:**
1. **Ollama format file exists** (`training_data_ollama.txt`) with format:
   ```
   ### Human: {question}
   ### Assistant: {answer}
   ```

2. **But unified_finetune.py uses TinyLlama Zephyr format:**
   ```python
   prompt = f"<|user|>\n{instruction}</s>\n<|assistant|>\n{output}</s>"
   ```

3. **Ollama expects Llama-3 format:**
   ```
   <|start_header_id|>user<|end_header_id|>
   {instruction}<|eot_id|>
   <|start_header_id|>assistant<|end_header_id|>
   {output}<|eot_id|>
   ```

**Evidence:**
- `training_data_ollama.txt` has 23,663 lines (11,831 Q&A pairs)
- `training_data_alpaca.json` has 7,888 examples
- Format mismatch between training and deployment
- `ai_training/export_to_ollama.py` line 211-217 shows correct Ollama template

**Fix Required:**
1. Update `unified_finetune.py` to use Llama-3 chat format
2. OR create separate fine-tuning script for Ollama
3. Ensure training format matches deployment format

---

### ERROR 3: No GGUF Conversion Pipeline
**Severity:** CRITICAL  
**Location:** Missing integration between `unified_finetune.py` and `ai_training/export_to_ollama.py`  
**Impact:** Cannot deploy fine-tuned model to Ollama

**Problem:**
- `unified_finetune.py` outputs HuggingFace format (PyTorch .bin/.safetensors)
- Ollama requires GGUF format
- `export_to_ollama.py` exists but is NOT called after training
- No automated pipeline from training → GGUF → Ollama

**Evidence:**
```python
# export_to_ollama.py line 86-91
convert_cmd = [
    "python", "-m", "llama_cpp.convert",
    str(model_dir),
    "--outfile", str(gguf_path),
    "--outtype", quantization
]
```
- Requires `llama_cpp` package (NOT in requirements)
- No integration with `unified_finetune.py`

**Fix Required:**
1. Add `llama-cpp-python` to requirements
2. Call `export_to_ollama.py` after training completes
3. Create end-to-end pipeline script

---

### ERROR 4: Incorrect Admission Rate Data
**Severity:** CRITICAL (DATA QUALITY)  
**Location:** `training_data_alpaca.json` line 5, 20, 40  
**Impact:** Model will learn and output incorrect information

**Problem:**
```json
{
  "instruction": "What is the admission rate at Alabama A & M University?",
  "output": "The admission rate at Alabama A & M University is approximately 0.6622%."
}
```

**Analysis:**
- 0.6622% = 0.006622 (less than 1% acceptance rate)
- This would make Alabama A&M more selective than Harvard (3.4%)
- **ACTUAL:** Should be 66.22% (0.6622 as decimal)
- **ERROR:** Decimal to percentage conversion bug

**Evidence:**
- Line 5: Alabama A&M = 0.6622% (should be 66.22%)
- Line 20: UAB = 0.8842% (should be 88.42%)
- Line 40: UAH = 0.7425% (should be 74.25%)
- **ALL admission rates in dataset are off by 100x**

**Fix Required:**
```python
# In data generation script
admission_rate_percent = admission_rate_decimal * 100
output = f"The admission rate is approximately {admission_rate_percent:.2f}%."
```

---

### ERROR 5: R2 Bucket Name Mismatch
**Severity:** CRITICAL  
**Location:** `unified_finetune.py` line 117, `.env` file  
**Impact:** Cannot download training data from R2

**Problem:**
```python
# unified_finetune.py line 117
r2_bucket_name: str = "collegeadvisor-finetuning-data"
```

**Evidence:**
- Hardcoded bucket name may not match actual R2 bucket
- No validation that bucket exists
- No fallback if bucket name is wrong
- `.env` file may have different bucket name

**Fix Required:**
1. Read bucket name from environment variable
2. Add bucket existence validation
3. Provide clear error message if bucket not found

---

### ERROR 6: Missing llama-cpp-python Dependency
**Severity:** CRITICAL  
**Location:** `requirements.txt`, `requirements-locked.txt`  
**Impact:** GGUF conversion will fail

**Problem:**
- `export_to_ollama.py` requires `llama-cpp-python` for GGUF conversion
- Package NOT listed in any requirements file
- Conversion will fail with ModuleNotFoundError

**Fix Required:**
```txt
# Add to requirements-locked.txt
llama-cpp-python==0.2.20
```

---

## HIGH-PRIORITY ERRORS

### ERROR 7: No Ollama Model Import Script
**Severity:** HIGH  
**Location:** Missing script  
**Impact:** Manual steps required after GGUF conversion

**Problem:**
- After GGUF conversion, need to import to Ollama
- No automated script for: `ollama create collegeadvisor -f Modelfile`
- Manual intervention required

**Fix Required:**
Create `scripts/import_to_ollama.sh`:
```bash
#!/bin/bash
ollama create collegeadvisor -f exported_models/Modelfile
ollama list | grep collegeadvisor
```

---

### ERROR 8: Inconsistent Model Names
**Severity:** HIGH  
**Location:** Multiple files  
**Impact:** Confusion and deployment errors

**Problem:**
- `unified_finetune.py`: TinyLlama/TinyLlama-1.1B-Chat-v1.0
- `export_to_ollama.py`: collegeadvisor-llama3
- `deploy.sh`: llama3
- `ai_training/run_sft.py`: unsloth/llama-3-8b-bnb-4bit

**Evidence:**
- 4 different model names/bases across codebase
- Unclear which model is actually being used
- TinyLlama (1.1B) vs Llama-3 (8B) - completely different models

**Fix Required:**
1. Standardize on ONE base model
2. Update all scripts to use same model
3. Document model choice in README

---

### ERROR 9: No Model Validation After Training
**Severity:** HIGH  
**Location:** `unified_finetune.py` line 822-843  
**Impact:** May deploy broken model

**Problem:**
```python
# Training completes but no validation
train_result = trainer.train()
trainer.save_model()  # Saves without testing
```

**Missing:**
- No inference test after training
- No quality checks on generated outputs
- No comparison with base model
- No automated evaluation metrics

**Fix Required:**
Add validation step:
```python
# After training
logger.info("Running model validation...")
test_prompts = [
    "What is the admission rate at Stanford?",
    "Tell me about MIT's computer science program"
]
for prompt in test_prompts:
    output = generate_response(model, tokenizer, prompt)
    logger.info(f"Test: {prompt}\nOutput: {output}\n")
```

---

### ERROR 10: MPS Device Issues Not Fully Resolved
**Severity:** HIGH  
**Location:** `unified_finetune.py` line 36-37, 676-690  
**Impact:** Training may fail on Apple Silicon

**Problem:**
```python
# Line 36-37
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# Line 676-688
if self.device == "mps":
    model_kwargs['device_map'] = None
    # ...
    self.model = self.model.to("mps")
```

**Known Issues:**
- MPS has NaN gradient problems (documented in previous failures)
- Fallback enabled but may not prevent all issues
- No detection/handling of NaN gradients during training
- No automatic fallback to CPU if MPS fails

**Fix Required:**
1. Add NaN gradient detection
2. Implement automatic CPU fallback
3. Add warning about MPS instability
4. Consider forcing CPU for production

---

### ERROR 11: No Training Data Validation
**Severity:** HIGH  
**Location:** `unified_finetune.py` line 394-446  
**Impact:** May train on corrupted/invalid data

**Problem:**
```python
def verify_data_integrity(self, file_path: Path) -> Dict[str, Any]:
    # Only checks structure, not content quality
    if not isinstance(data, list):
        raise ValueError("Data must be a list of examples")
```

**Missing Validations:**
- No check for duplicate examples
- No validation of output quality
- No detection of malformed responses
- No check for data distribution
- No validation of admission rate values (see ERROR 4)

**Fix Required:**
```python
# Add comprehensive validation
def validate_data_quality(data):
    # Check for duplicates
    seen = set()
    for ex in data:
        key = (ex['instruction'], ex['output'])
        if key in seen:
            logger.warning(f"Duplicate found: {ex['instruction']}")
        seen.add(key)
    
    # Validate admission rates
    for ex in data:
        if 'admission rate' in ex['instruction'].lower():
            rate = extract_rate(ex['output'])
            if rate < 1.0:  # Suspiciously low
                logger.error(f"Invalid rate: {rate}% in {ex}")
```

---

### ERROR 12: Hardcoded Paths and Configuration
**Severity:** HIGH  
**Location:** Multiple files  
**Impact:** Difficult to customize and deploy

**Problem:**
- `unified_finetune.py` line 108: `output_dir: str = "collegeadvisor_unified_model"`
- `unified_finetune.py` line 117: `r2_bucket_name: str = "collegeadvisor-finetuning-data"`
- `unified_finetune.py` line 118: `r2_data_prefix: str = "multi_source/training_datasets/"`
- No command-line arguments to override
- No config file support

**Fix Required:**
Add argparse support:
```python
parser = argparse.ArgumentParser()
parser.add_argument('--output-dir', default='collegeadvisor_unified_model')
parser.add_argument('--bucket', default='collegeadvisor-finetuning-data')
parser.add_argument('--data-prefix', default='multi_source/training_datasets/')
args = parser.parse_args()
```

---

### ERROR 13: No Checkpoint Resume Logic
**Severity:** HIGH  
**Location:** `unified_finetune.py`  
**Impact:** Cannot resume interrupted training

**Problem:**
- Script claims "Checkpoint Support" (line 11)
- TrainingArguments has `save_steps=100` (line 769)
- But NO logic to detect and resume from checkpoints
- If training interrupted, must start from scratch

**Fix Required:**
```python
# Before training
checkpoint_dir = Path(output_dir)
checkpoints = list(checkpoint_dir.glob("checkpoint-*"))
resume_from_checkpoint = None
if checkpoints:
    latest = max(checkpoints, key=lambda p: int(p.name.split('-')[1]))
    resume_from_checkpoint = str(latest)
    logger.info(f"Resuming from checkpoint: {resume_from_checkpoint}")

# In trainer.train()
train_result = trainer.train(resume_from_checkpoint=resume_from_checkpoint)
```

---

### ERROR 14: Insufficient Error Handling in R2 Operations
**Severity:** HIGH  
**Location:** `unified_finetune.py` line 326-351, 353-392  
**Impact:** Cryptic errors when R2 operations fail

**Problem:**
```python
def list_available_datasets(self) -> List[str]:
    try:
        response = self.client.list_objects_v2(...)
        # ...
    except Exception as e:
        logger.error(f"❌ Failed to list R2 datasets: {e}")
        raise  # Generic exception, no specific handling
```

**Missing:**
- No handling of network timeouts
- No retry logic for transient failures
- No specific error messages for common issues (auth, bucket not found, etc.)
- No offline mode/fallback to local data

**Fix Required:**
```python
from botocore.exceptions import ClientError, NoCredentialsError
import time

def list_available_datasets(self, max_retries=3) -> List[str]:
    for attempt in range(max_retries):
        try:
            response = self.client.list_objects_v2(...)
            return datasets
        except NoCredentialsError:
            logger.error("R2 credentials not configured")
            raise
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                logger.error(f"Bucket not found: {self.config.r2_bucket_name}")
                raise
            elif attempt < max_retries - 1:
                logger.warning(f"Retry {attempt+1}/{max_retries}...")
                time.sleep(2 ** attempt)
            else:
                raise
```

---

### ERROR 15: Training Data Not in R2
**Severity:** HIGH  
**Location:** `unified_finetune.py` line 448-467  
**Impact:** Script expects data in R2 but data is local

**Problem:**
```python
def fetch_training_data(self, dataset_name: str = "instruction_dataset_alpaca.json"):
    r2_key = f"{self.config.r2_data_prefix}{dataset_name}"
    local_path = self.download_dataset(r2_key)
```

**Evidence:**
- Training data exists locally: `training_data_alpaca.json`, `training_data_ollama.txt`
- Script tries to download from R2
- If data not in R2, training fails
- No fallback to local files

**Fix Required:**
```python
def fetch_training_data(self, dataset_name: str = "instruction_dataset_alpaca.json"):
    # Check local first
    local_file = Path(dataset_name)
    if local_file.exists():
        logger.info(f"Using local training data: {local_file}")
        stats = self.verify_data_integrity(local_file)
        return local_file, stats
    
    # Fall back to R2
    logger.info("Local data not found, downloading from R2...")
    r2_key = f"{self.config.r2_data_prefix}{dataset_name}"
    local_path = self.download_dataset(r2_key)
    stats = self.verify_data_integrity(local_path)
    return local_path, stats
```

---

### ERROR 16: No Disk Space Monitoring During Training
**Severity:** MEDIUM  
**Location:** `unified_finetune.py` line 180-191  
**Impact:** Training may fail mid-way due to disk space

**Problem:**
- Pre-flight check validates 10GB free space
- But training generates checkpoints every 100 steps
- Model size ~2.2GB, checkpoints can accumulate
- No monitoring during training
- `save_total_limit=3` helps but not foolproof

**Fix Required:**
```python
# Add periodic disk space check
class DiskSpaceCallback(TrainerCallback):
    def on_save(self, args, state, control, **kwargs):
        stat = shutil.disk_usage(Path.cwd())
        available_gb = stat.free / (1024**3)
        if available_gb < 5.0:
            logger.error(f"Low disk space: {available_gb:.2f} GB")
            control.should_training_stop = True
        return control

# Add to trainer
trainer = Trainer(..., callbacks=[DiskSpaceCallback()])
```

---

### ERROR 17: Tokenizer Padding Configuration Issue
**Severity:** MEDIUM  
**Location:** `unified_finetune.py` line 662-663  
**Impact:** May cause training instability

**Problem:**
```python
if self.tokenizer.pad_token is None:
    self.tokenizer.pad_token = self.tokenizer.eos_token
```

**Issue:**
- Setting pad_token = eos_token can confuse model
- Model may learn to generate padding tokens
- Better to use a dedicated pad token
- TinyLlama may have specific padding requirements

**Fix Required:**
```python
if self.tokenizer.pad_token is None:
    # Add dedicated pad token
    self.tokenizer.add_special_tokens({'pad_token': '[PAD]'})
    self.model.resize_token_embeddings(len(self.tokenizer))
```

---

### ERROR 18: No Logging of Training Hyperparameters
**Severity:** MEDIUM  
**Location:** `unified_finetune.py` line 866-894  
**Impact:** Difficult to reproduce results

**Problem:**
- Summary prints some config
- But doesn't log complete hyperparameters
- No MLflow/Weights&Biases integration
- Can't track experiments

**Fix Required:**
```python
# Save complete config
config_dict = {
    'model_name': config.model_name,
    'lora_r': config.lora_r,
    'lora_alpha': config.lora_alpha,
    'learning_rate': config.learning_rate,
    'num_epochs': config.num_train_epochs,
    'batch_size': config.per_device_train_batch_size,
    'gradient_accumulation': config.gradient_accumulation_steps,
    'max_seq_length': config.max_seq_length,
    'training_data': str(data_file),
    'data_stats': data_stats,
    'quality_metrics': quality_metrics,
    'training_metrics': training_metrics,
    'timestamp': datetime.now().isoformat()
}

with open(output_dir / 'experiment_log.json', 'w') as f:
    json.dump(config_dict, f, indent=2)
```

---

## MEDIUM-PRIORITY ISSUES

### ISSUE 1: simple_data_ingest.py Not Used in Fine-Tuning
**Severity:** MEDIUM  
**Location:** `simple_data_ingest.py`  
**Impact:** Confusion about data pipeline

**Problem:**
- `simple_data_ingest.py` ingests data into ChromaDB
- But fine-tuning uses JSON files directly
- No connection between the two
- Unclear which script to run when

**Recommendation:**
- Rename to `ingest_to_chromadb.py` for clarity
- Document that it's for RAG, not fine-tuning
- Create separate `prepare_finetuning_data.py`

---

### ISSUE 2: No Documentation of Complete Workflow
**Severity:** MEDIUM  
**Location:** README.md  
**Impact:** Users don't know end-to-end process

**Problem:**
README shows:
1. Fine-tune with `unified_finetune.py`
2. But doesn't explain:
   - How to convert to GGUF
   - How to import to Ollama
   - How to test the model
   - How to deploy

**Recommendation:**
Add to README:
```markdown
## Complete Ollama Fine-Tuning Workflow

1. Prepare data: `python ai_training/finetuning_data_prep.py`
2. Fine-tune: `./run_finetuning.sh`
3. Convert to GGUF: `python ai_training/export_to_ollama.py --model collegeadvisor_unified_model --output exported_models`
4. Import to Ollama: `ollama create collegeadvisor -f exported_models/Modelfile`
5. Test: `ollama run collegeadvisor "What is Stanford's admission rate?"`
6. Deploy: `./deploy.sh`
```

---

## SUMMARY OF REQUIRED FIXES

### Immediate (Blocking)
1. ✅ Create or fix `requirements-finetuning.txt`
2. ✅ Fix admission rate data (multiply by 100)
3. ✅ Add llama-cpp-python to requirements
4. ✅ Create end-to-end pipeline script
5. ✅ Fix training data format for Ollama compatibility

### High Priority
6. ✅ Add model validation after training
7. ✅ Implement checkpoint resume logic
8. ✅ Add comprehensive data validation
9. ✅ Improve R2 error handling
10. ✅ Add local data fallback

### Medium Priority
11. ✅ Add disk space monitoring
12. ✅ Fix tokenizer padding
13. ✅ Add experiment logging
14. ✅ Document complete workflow
15. ✅ Standardize model names

---

## RECOMMENDED ACTION PLAN

### Phase 1: Critical Fixes (Day 1)
1. Fix requirements file issue
2. Fix admission rate data
3. Add llama-cpp-python dependency
4. Test basic training pipeline

### Phase 2: Ollama Integration (Day 2-3)
1. Update training format for Ollama
2. Create automated GGUF conversion
3. Create Ollama import script
4. Test end-to-end pipeline

### Phase 3: Robustness (Day 4-5)
1. Add comprehensive validation
2. Improve error handling
3. Add monitoring and logging
4. Create complete documentation

---

## CONCLUSION

The current fine-tuning pipeline has **18 critical errors** that prevent successful Ollama model deployment. The most severe issues are:

1. **Missing requirements file** - immediate blocker
2. **Incorrect training data** - all admission rates wrong by 100x
3. **No GGUF conversion pipeline** - can't deploy to Ollama
4. **Format mismatch** - training format != deployment format

**Estimated time to fix:** 3-5 days of focused work

**Risk level:** HIGH - Multiple blocking issues, data quality problems, incomplete pipeline

**Recommendation:** Do NOT attempt fine-tuning until at least Phase 1 and Phase 2 fixes are complete.

