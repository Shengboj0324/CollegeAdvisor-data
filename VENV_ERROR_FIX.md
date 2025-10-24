# Virtual Environment Error Fix

**Error:** `OSError: [Errno 2] No such file or directory: '.../typing_extensions-4.14.1.dist-info/METADATA'`

**Cause:** Corrupted virtual environment packages

**Status:** ✅ FIX AVAILABLE

---

## Quick Fix

```bash
./fix_venv.sh
```

This will:
1. Remove corrupted virtual environment
2. Create fresh venv
3. Install all dependencies
4. Verify installation

**Time:** 5-10 minutes

---

## Manual Fix (Alternative)

If the script doesn't work, do this manually:

```bash
# 1. Deactivate current venv (if active)
deactivate

# 2. Remove corrupted venv
rm -rf venv

# 3. Create fresh venv
python3 -m venv venv

# 4. Activate new venv
source venv/bin/activate

# 5. Upgrade pip
pip install --upgrade pip

# 6. Install dependencies
pip install -r requirements-finetuning.txt

# 7. Verify
python3 -c "import torch, transformers, peft; print('✅ All packages OK')"
```

---

## After Fix

Once the venv is fixed, run the pipeline:

```bash
./run_ollama_finetuning_pipeline.sh
```

The pipeline now includes:
- ✅ Automatic corrupted venv detection
- ✅ Auto-recreation if corrupted
- ✅ Dependency verification

---

## Why This Happened

Virtual environments can become corrupted when:
- Packages are updated outside the venv
- System Python is upgraded
- Disk errors during installation
- Interrupted pip installations

The fix script prevents this from blocking your training.

---

## Verification

After running `./fix_venv.sh`, you should see:

```
✅ PyTorch 2.2.0
✅ Transformers 4.40.2
✅ PEFT 0.10.0
✅ NumPy 1.26.4
```

If all show ✅, you're ready to train!

