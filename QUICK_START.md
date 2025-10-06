# 🚀 QUICK START - FIXED VERSION

**Your Issues:**
1. ❌ Not in virtual environment (in conda base instead)
2. ❌ Missing `python-dotenv` and `boto3` in venv
3. ❌ Unsloth won't work on macOS (needs CUDA)

**Solution:** Use the macOS-compatible method

---

## ✅ COPY-PASTE THIS (All-in-One Fix)

```bash
# 1. Go to project directory
cd /Users/jiangshengbo/Desktop/CollegeAdvisor-data

# 2. Activate venv (IMPORTANT!)
source venv_finetune/bin/activate

# 3. Verify you're in venv
echo "Python: $(which python)"

# 4. Install dependencies
pip install python-dotenv boto3

# 5. Download training data
python -c "
from college_advisor_data.storage.r2_storage import R2StorageClient
client = R2StorageClient()
client.client.download_file(
    Bucket=client.bucket_name,
    Key='multi_source/training_datasets/instruction_dataset_alpaca.json',
    Filename='training_data_alpaca.json'
)
print('✓ Downloaded')
"

# 6. Verify download
ls -lh training_data_alpaca.json

# 7. Start fine-tuning
python finetune_macos.py
```

---

## 📊 WHAT WAS FIXED

### Issue 1: Not in Virtual Environment
**Your error showed:**
```
/Users/jiangshengbo/opt/anaconda3/bin/python  ← Conda base
```

**Should be:**
```
/Users/jiangshengbo/Desktop/CollegeAdvisor-data/venv_finetune/bin/python
```

**Fix:** `source venv_finetune/bin/activate`

### Issue 2: Missing Dependencies
**Error:**
```
ModuleNotFoundError: No module named 'dotenv'
```

**Fix:** `pip install python-dotenv boto3`

### Issue 3: Unsloth Code Error
**Error in FINE_TUNING_GUIDE.md:**
```python
fp16=not torch.cuda.is_bf16_supported(),  # torch not imported!
```

**Fixed:** Added `import torch` to the guide

---

## ✅ EXPECTED OUTPUT

After running the commands, you should see:

```
Python: /Users/jiangshengbo/Desktop/CollegeAdvisor-data/venv_finetune/bin/python
Requirement already satisfied: python-dotenv in ./venv_finetune/...
Requirement already satisfied: boto3 in ./venv_finetune/...
Initialized R2 storage client for bucket: collegeadvisor-finetuning-data
✓ Downloaded
-rw-r--r--  1 user  staff   1.3M Oct  6 XX:XX training_data_alpaca.json

================================================================================
FINE-TUNING COLLEGE ADVISOR MODEL (macOS Compatible)
================================================================================
✓ Using Apple Silicon MPS
Device: mps
Step 1: Loading training data...
✓ Loaded 7888 training examples
...
```

---

## 🆘 TROUBLESHOOTING

**Still see "No module named 'dotenv'"?**
```bash
# Check if you're really in venv
which python
# Should show: .../venv_finetune/bin/python

# If not, activate again
source venv_finetune/bin/activate
```

**See "No module named 'torch'"?**
```bash
# Install PyTorch and other packages
pip install torch torchvision torchaudio transformers datasets accelerate peft trl
```

---

## 📝 SUMMARY

1. ✅ Fixed: Added `import torch` to FINE_TUNING_GUIDE.md
2. ✅ Fixed: Created proper activation instructions
3. ✅ Fixed: Added dependency installation
4. ✅ Ready: Can now download data and fine-tune

**Just copy-paste the commands above!** 🚀

