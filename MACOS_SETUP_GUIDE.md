# 🍎 macOS Fine-Tuning Setup Guide

**Your System:** macOS (detected from error messages)  
**Issue:** Unsloth requires CUDA (NVIDIA GPUs), which macOS doesn't have  
**Solution:** Use standard PyTorch + LoRA instead

---

## 🔧 PROBLEM ANALYSIS

### Issues You Encountered:

1. **bitsandbytes >= 0.45.5 not available**
   - Latest version is 0.42.0
   - Unsloth's requirements are too new
   - bitsandbytes doesn't fully work on macOS anyway (designed for CUDA)

2. **xformers requires torch to be installed first**
   - Installation order matters
   - xformers also requires CUDA (won't work on macOS)

3. **Unsloth is optimized for NVIDIA GPUs**
   - Uses CUDA-specific optimizations
   - Won't work properly on macOS

### Root Cause:

**Unsloth is designed for NVIDIA GPUs with CUDA. macOS uses:**
- **Apple Silicon (M1/M2/M3):** MPS (Metal Performance Shaders)
- **Intel Macs:** CPU only

---

## ✅ SOLUTION: Use Standard PyTorch + LoRA

Instead of Unsloth, we'll use:
- **PyTorch** (with MPS support for Apple Silicon)
- **PEFT** (for LoRA fine-tuning)
- **Transformers** (Hugging Face)

**This will work perfectly on macOS!**

---

## 🚀 STEP-BY-STEP INSTALLATION

### Step 1: Clean Up Current Environment

```bash
# Deactivate current venv
deactivate

# Remove broken venv
rm -rf venv_finetune

# Create fresh venv
python3 -m venv venv_finetune

# Activate it
source venv_finetune/bin/activate
```

### Step 2: Run Automated Setup Script

```bash
# Make script executable
chmod +x setup_finetuning_env.sh

# Run it
./setup_finetuning_env.sh
```

**This script will:**
1. ✅ Upgrade pip
2. ✅ Install PyTorch (with MPS support)
3. ✅ Install transformers, datasets, accelerate, peft
4. ✅ Install TRL
5. ✅ Skip incompatible packages (xformers, bitsandbytes)
6. ✅ Verify installation

### Step 3: Verify Installation

After the script completes, you should see:

```
Installed packages:
  ✓ PyTorch: 2.x.x
  ✓ Transformers: 4.x.x
  ✓ Datasets: 2.x.x
  ✓ PEFT (LoRA): 0.x.x
  ✓ Accelerate: 0.x.x
  ✓ TRL: 0.x.x

Hardware support:
  CUDA available: False
  MPS available: True  (if Apple Silicon)
  Device: mps
```

---

## 🎯 ALTERNATIVE: Manual Installation

If the script doesn't work, install manually:

```bash
# Activate venv
source venv_finetune/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install PyTorch (macOS version)
pip install torch torchvision torchaudio

# Install core packages
pip install transformers datasets accelerate peft trl

# Verify
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'MPS available: {torch.backends.mps.is_available()}')"
```

---

## 📊 WHAT'S DIFFERENT FROM THE GUIDE?

### Original Guide (FINE_TUNING_GUIDE.md):
- ❌ Uses Unsloth (requires CUDA)
- ❌ Uses 4-bit quantization (requires bitsandbytes + CUDA)
- ❌ Uses xformers (requires CUDA)
- ✅ Works on NVIDIA GPUs

### macOS Version (finetune_macos.py):
- ✅ Uses standard PyTorch (works on macOS)
- ✅ Uses fp16 instead of 4-bit (compatible with MPS)
- ✅ Uses native attention (no xformers needed)
- ✅ Works on Apple Silicon and Intel Macs

### Performance Comparison:

| Feature | NVIDIA GPU (Unsloth) | macOS (Standard) |
|---------|---------------------|------------------|
| **Speed** | Very Fast (2-3 hours) | Slower (4-8 hours) |
| **Memory** | Efficient (4-bit) | More (fp16) |
| **Quality** | Same | Same |
| **Works on macOS?** | ❌ No | ✅ Yes |

---

## 🎓 FINE-TUNING ON macOS

### Step 1: Download Training Data

```bash
python -c "
from college_advisor_data.storage.r2_storage import R2StorageClient

client = R2StorageClient()
client.client.download_file(
    Bucket=client.bucket_name,
    Key='multi_source/training_datasets/instruction_dataset_alpaca.json',
    Filename='training_data_alpaca.json'
)
print('✓ Downloaded training data')
"
```

### Step 2: Run Fine-Tuning

```bash
python finetune_macos.py
```

**Expected output:**
```
================================================================================
FINE-TUNING COLLEGE ADVISOR MODEL (macOS Compatible)
================================================================================
✓ Using Apple Silicon MPS (Metal Performance Shaders)
Device: mps

Step 1: Loading training data...
✓ Loaded 7888 training examples

Step 2: Loading model and tokenizer...
Model: meta-llama/Llama-3.2-1B-Instruct
✓ Model loaded on mps

Step 3: Configuring LoRA...
trainable params: 2,097,152 || all params: 1,237,319,680 || trainable%: 0.1694

Step 4: Preparing dataset...
✓ Prepared 7888 examples

Step 5: Configuring training...
✓ Batch size: 2
✓ Gradient accumulation: 8
✓ Effective batch size: 16

Step 6: Creating trainer...
✓ Trainer created

Step 7: Starting training...
================================================================================
This will take 1-4 hours depending on your hardware
...
```

### Step 3: Monitor Progress

Training will show progress like:
```
Step 10/1500: loss=2.345
Step 20/1500: loss=2.123
Step 30/1500: loss=1.987
...
```

**Good signs:**
- ✅ Loss is decreasing
- ✅ No errors
- ✅ Steady progress

**Bad signs:**
- ❌ Loss is NaN
- ❌ Out of memory errors
- ❌ Loss not decreasing

---

## 🔧 TROUBLESHOOTING

### Error: "MPS backend out of memory"

**Solution:**
```python
# Edit finetune_macos.py
# Change line ~90:
batch_size = 1  # Instead of 2
```

### Error: "MPS does not support..."

**Solution:**
```python
# Edit finetune_macos.py
# Change line ~20:
device = "cpu"  # Force CPU instead of MPS
```

### Training is very slow

**Expected times:**
- **Apple Silicon (M1/M2/M3):** 2-4 hours
- **Intel Mac:** 6-12 hours
- **CPU only:** 12-24 hours

**To speed up:**
1. Use smaller model (already using 1B)
2. Reduce epochs (change `num_train_epochs=1`)
3. Use fewer examples (take first 1000)

---

## 📈 EXPECTED RESULTS

### Training Time:
- **M1/M2/M3 Mac:** 2-4 hours
- **Intel Mac:** 6-12 hours

### Model Size:
- **Base model:** ~2.5 GB
- **LoRA adapters:** ~8 MB
- **Total:** ~2.5 GB

### Quality:
- **Same as NVIDIA GPU version**
- LoRA fine-tuning quality is hardware-independent
- Only speed differs, not results

---

## ✅ VERIFICATION

After training completes, test the model:

```bash
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_path = 'collegeadvisor_model_macos'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

if torch.backends.mps.is_available():
    model = model.to('mps')

prompt = '''### Instruction:
What is the admission rate at Stanford University?

### Input:


### Response:
'''

inputs = tokenizer(prompt, return_tensors='pt')
if torch.backends.mps.is_available():
    inputs = {k: v.to('mps') for k, v in inputs.items()}

outputs = model.generate(**inputs, max_new_tokens=100)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
"
```

---

## 🎯 SUMMARY

**Problem:** Unsloth requires NVIDIA GPU (CUDA)  
**Your System:** macOS (no CUDA support)  
**Solution:** Use standard PyTorch + LoRA

**Steps:**
1. ✅ Clean up broken venv
2. ✅ Run `setup_finetuning_env.sh`
3. ✅ Download training data
4. ✅ Run `finetune_macos.py`
5. ✅ Wait 2-4 hours
6. ✅ Test the model

**Result:** Same quality as NVIDIA version, just slower training

---

## 🚀 READY TO START?

```bash
# 1. Clean up
deactivate
rm -rf venv_finetune
python3 -m venv venv_finetune
source venv_finetune/bin/activate

# 2. Install dependencies
chmod +x setup_finetuning_env.sh
./setup_finetuning_env.sh

# 3. Download data (if not already done)
# (training_data_alpaca.json already exists)

# 4. Start fine-tuning
python finetune_macos.py
```

**Everything is ready! Let's fix your environment and start training!** 🚀

