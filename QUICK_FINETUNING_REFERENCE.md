# Quick Finetuning Reference Card

**Last Updated:** October 17, 2025

---

## 🚀 Quick Start (3 Commands)

```bash
# 1. Verify setup
python scripts/check_finetuning_setup.py

# 2. Generate training data
python ai_training/finetuning_data_prep.py

# 3. Train!
python unified_finetune.py
```

---

## ⚠️ Critical Rules

### ❌ DON'T USE
- `ai_training/run_sft.py` - CUDA-only, won't work on macOS

### ✅ USE INSTEAD
- `unified_finetune.py` - Main training (Mac-first, HF/PEFT/Trainer)
- `ai_training/run_sft_cpu.py` - Tiny experiments only

---

## 📋 Data Contracts

### Alpaca Format (Preferred)
```json
{
  "instruction": "How do I improve my Common App essay on adversity?",
  "input": "",
  "output": "Focus on reflection over event. Show growth, decisions, outcomes..."
}
```

### Conversational JSONL
```json
{
  "messages": [
    {"role": "user", "content": "What GPA do I need for Cornell engineering?"},
    {"role": "assistant", "content": "Target 3.8+ unweighted... context on rigor..."}
  ]
}
```

---

## 🔧 Required Environment Variables

```bash
export R2_ACCOUNT_ID=your_account_id
export R2_ACCESS_KEY_ID=your_access_key
export R2_SECRET_ACCESS_KEY=your_secret_key
export PYTORCH_ENABLE_MPS_FALLBACK=1  # Already set in unified_finetune.py
```

Add to `~/.zshrc` or `~/.bash_profile` for persistence.

---

## 📦 Package Versions (macOS)

```bash
pip install transformers==4.40.2 trl<0.9.0 peft==0.11.1 accelerate==0.28.0 psutil
```

Or use:
```bash
pip install -r requirements-finetuning.txt
```

---

## 🐛 Common Errors → Quick Fixes

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: unsloth` | Don't use `run_sft.py`, use `unified_finetune.py` |
| `ImportError: Trainer` | `pip install transformers==4.40.2 peft==0.11.1` |
| `ModuleNotFoundError: psutil` | `pip install psutil` |
| `KeyError: 'instruction'` | Run `python ai_training/finetuning_data_prep.py` |
| `boto3 endpoint error` | Set R2 env vars (see above) |
| `MPS not implemented` | Already fixed with `PYTORCH_ENABLE_MPS_FALLBACK=1` |

---

## 📁 File Structure

```
CollegeAdvisor-data/
├── unified_finetune.py              # ✅ USE THIS
├── ai_training/
│   ├── finetuning_data_prep.py     # Generate data
│   ├── run_sft_cpu.py              # Tiny experiments
│   └── run_sft.py                  # ❌ IGNORE
├── scripts/
│   └── check_finetuning_setup.py   # Verify setup
└── requirements-finetuning.txt      # Install deps
```

---

## 🎯 Workflow

```
1. Set env vars → 2. Install deps → 3. Check setup → 4. Generate data → 5. Train
```

---

## 📚 Full Documentation

- **Troubleshooting:** `FINETUNING_TROUBLESHOOTING.md`
- **Setup Checker:** `python scripts/check_finetuning_setup.py`
- **Data Prep:** `python ai_training/finetuning_data_prep.py --help`

---

## 💡 Pro Tips

1. **Always run from repo root**
2. **Generate data before training**
3. **Verify setup first**
4. **Start with small batch size (1-2)**
5. **Monitor memory with Activity Monitor**

---

**Need help?** Run `python scripts/check_finetuning_setup.py` to diagnose issues.

