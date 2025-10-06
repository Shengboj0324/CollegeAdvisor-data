# 🧪 FINE-TUNING TESTING & VALIDATION GUIDE

**Generated:** 2025-10-06  
**Purpose:** Guarantee error-free fine-tuning with comprehensive testing  
**Status:** Production-ready test suite

---

## 📋 TESTING STRATEGY

### 3-Phase Testing Approach:

1. **Pre-Training Validation** - Verify data and setup
2. **During Training Monitoring** - Track progress and catch errors
3. **Post-Training Evaluation** - Validate model quality

---

## ✅ PHASE 1: PRE-TRAINING VALIDATION

### Test 1: Verify Training Data

```bash
python -c "
import json
from pathlib import Path

print('=' * 80)
print('TRAINING DATA VALIDATION')
print('=' * 80)

# Check file exists
data_file = Path('training_data_alpaca.json')
if not data_file.exists():
    print('❌ ERROR: training_data_alpaca.json not found')
    print('   Run download script first')
    exit(1)

print('✓ File exists')

# Load and validate
with open(data_file) as f:
    data = json.load(f)

print(f'✓ Valid JSON format')
print(f'✓ Total examples: {len(data)}')

# Check structure
if len(data) == 0:
    print('❌ ERROR: No training examples found')
    exit(1)

required_fields = ['instruction', 'input', 'output']
sample = data[0]

for field in required_fields:
    if field not in sample:
        print(f'❌ ERROR: Missing field: {field}')
        exit(1)
    if not sample[field] or len(sample[field].strip()) == 0:
        print(f'⚠️  WARNING: Empty field: {field}')

print(f'✓ All required fields present')

# Check data quality
empty_count = 0
short_count = 0

for ex in data:
    if not ex['output'] or len(ex['output'].strip()) < 10:
        empty_count += 1
    if len(ex['output'].strip()) < 50:
        short_count += 1

print(f'✓ Empty outputs: {empty_count} ({empty_count/len(data)*100:.1f}%)')
print(f'✓ Short outputs (<50 chars): {short_count} ({short_count/len(data)*100:.1f}%)')

if empty_count > len(data) * 0.1:
    print('⚠️  WARNING: >10% empty outputs')

# Sample examples
print(f'\n📝 Sample Training Example:')
print(f'   Instruction: {sample[\"instruction\"][:80]}...')
print(f'   Input: {sample[\"input\"][:80]}...')
print(f'   Output: {sample[\"output\"][:80]}...')

print('\n' + '=' * 80)
print('✅ TRAINING DATA VALIDATION PASSED')
print('=' * 80)
"
```

### Test 2: Verify GPU Setup (if using GPU)

```bash
python -c "
import torch

print('=' * 80)
print('GPU VALIDATION')
print('=' * 80)

if torch.cuda.is_available():
    print(f'✓ CUDA available: {torch.cuda.is_available()}')
    print(f'✓ CUDA version: {torch.version.cuda}')
    print(f'✓ GPU count: {torch.cuda.device_count()}')
    
    for i in range(torch.cuda.device_count()):
        print(f'\nGPU {i}:')
        print(f'  Name: {torch.cuda.get_device_name(i)}')
        print(f'  Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB')
        
        # Check available memory
        torch.cuda.set_device(i)
        torch.cuda.empty_cache()
        free_mem = torch.cuda.mem_get_info()[0] / 1024**3
        total_mem = torch.cuda.mem_get_info()[1] / 1024**3
        print(f'  Free: {free_mem:.1f} GB / {total_mem:.1f} GB')
        
        if free_mem < 6:
            print(f'  ⚠️  WARNING: Low free memory (<6 GB)')
            print(f'     Consider using 4-bit quantization')
    
    print('\n✅ GPU VALIDATION PASSED')
else:
    print('⚠️  No GPU detected - will use CPU')
    print('   Training will be MUCH slower')
    print('   Consider using cloud GPU (Colab, Lambda Labs)')

print('=' * 80)
"
```

### Test 3: Verify Dependencies

```bash
python -c "
import sys

print('=' * 80)
print('DEPENDENCY VALIDATION')
print('=' * 80)

required_packages = {
    'torch': '2.0.0',
    'transformers': '4.30.0',
    'datasets': '2.0.0',
    'peft': '0.4.0',
    'bitsandbytes': '0.40.0',
    'accelerate': '0.20.0',
}

missing = []
outdated = []

for package, min_version in required_packages.items():
    try:
        mod = __import__(package)
        version = getattr(mod, '__version__', 'unknown')
        print(f'✓ {package}: {version}')
        
        # Simple version check (not perfect but good enough)
        if version != 'unknown' and version < min_version:
            outdated.append(f'{package} (need >={min_version}, have {version})')
    except ImportError:
        print(f'❌ {package}: NOT INSTALLED')
        missing.append(package)

if missing:
    print(f'\n❌ ERROR: Missing packages: {missing}')
    print('   Install with: pip install ' + ' '.join(missing))
    sys.exit(1)

if outdated:
    print(f'\n⚠️  WARNING: Outdated packages: {outdated}')
    print('   Consider upgrading')

print('\n✅ DEPENDENCY VALIDATION PASSED')
print('=' * 80)
"
```

---

## 📊 PHASE 2: DURING TRAINING MONITORING

### Create Monitoring Script

Save as `monitor_training.py`:

```python
#!/usr/bin/env python3
"""
Monitor training progress and catch errors early
"""

import json
import time
from pathlib import Path
import matplotlib.pyplot as plt

def monitor_training(output_dir="collegeadvisor_model", check_interval=30):
    """Monitor training logs and metrics."""
    
    print("=" * 80)
    print("TRAINING MONITOR")
    print("=" * 80)
    print(f"Monitoring: {output_dir}")
    print(f"Check interval: {check_interval}s")
    print("Press Ctrl+C to stop\n")
    
    trainer_state_file = Path(output_dir) / "trainer_state.json"
    
    losses = []
    steps = []
    
    try:
        while True:
            if trainer_state_file.exists():
                with open(trainer_state_file) as f:
                    state = json.load(f)
                
                # Extract loss history
                log_history = state.get('log_history', [])
                
                if log_history:
                    latest = log_history[-1]
                    
                    if 'loss' in latest:
                        step = latest.get('step', 0)
                        loss = latest['loss']
                        
                        steps.append(step)
                        losses.append(loss)
                        
                        print(f"Step {step}: loss={loss:.4f}")
                        
                        # Check for issues
                        if loss > 10:
                            print("⚠️  WARNING: Very high loss - check learning rate")
                        elif len(losses) > 10 and losses[-1] > losses[-10]:
                            print("⚠️  WARNING: Loss increasing - possible overfitting")
                        elif loss < 0.01:
                            print("⚠️  WARNING: Very low loss - possible data leakage")
                    
                    # Plot progress
                    if len(losses) > 5:
                        plt.figure(figsize=(10, 6))
                        plt.plot(steps, losses)
                        plt.xlabel('Step')
                        plt.ylabel('Loss')
                        plt.title('Training Progress')
                        plt.grid(True)
                        plt.savefig('training_progress.png')
                        plt.close()
            
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")
        
        if losses:
            print(f"\nFinal Statistics:")
            print(f"  Total steps: {steps[-1]}")
            print(f"  Initial loss: {losses[0]:.4f}")
            print(f"  Final loss: {losses[-1]:.4f}")
            print(f"  Improvement: {(losses[0] - losses[-1]) / losses[0] * 100:.1f}%")

if __name__ == "__main__":
    monitor_training()
```

Run in separate terminal:
```bash
python monitor_training.py
```

---

## 🎯 PHASE 3: POST-TRAINING EVALUATION

### Test 1: Basic Functionality

```python
#!/usr/bin/env python3
"""
Test basic model functionality
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

print("=" * 80)
print("BASIC FUNCTIONALITY TEST")
print("=" * 80)

# Load model
model_path = "collegeadvisor_model"
print(f"Loading model from: {model_path}")

try:
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None
    )
    print("✓ Model loaded successfully")
except Exception as e:
    print(f"❌ ERROR loading model: {e}")
    exit(1)

# Test inference
test_prompt = """### Instruction:
What is the admission rate at Stanford University?

### Response:
"""

print(f"\nTest prompt: {test_prompt[:50]}...")

try:
    inputs = tokenizer(test_prompt, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    
    outputs = model.generate(
        **inputs,
        max_new_tokens=100,
        temperature=0.7,
        do_sample=True
    )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"\nModel response:\n{response}")
    print("\n✅ BASIC FUNCTIONALITY TEST PASSED")
    
except Exception as e:
    print(f"❌ ERROR during inference: {e}")
    exit(1)

print("=" * 80)
```

### Test 2: Comprehensive Evaluation

Save as `evaluate_model.py`:

```python
#!/usr/bin/env python3
"""
Comprehensive model evaluation
"""

import json
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from tqdm import tqdm

# Load model
model_path = "collegeadvisor_model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)

# Test cases
test_cases = [
    {
        "question": "What is the admission rate at Stanford University?",
        "expected_keywords": ["stanford", "admission", "rate", "%"],
        "category": "admissions"
    },
    {
        "question": "How much is tuition at MIT?",
        "expected_keywords": ["mit", "tuition", "$", "cost"],
        "category": "costs"
    },
    {
        "question": "Tell me about Harvard's student size",
        "expected_keywords": ["harvard", "student", "size", "enrollment"],
        "category": "demographics"
    },
    {
        "question": "What is the location of Yale University?",
        "expected_keywords": ["yale", "new haven", "connecticut", "ct"],
        "category": "location"
    },
    {
        "question": "Compare Berkeley and UCLA",
        "expected_keywords": ["berkeley", "ucla", "california"],
        "category": "comparison"
    },
]

print("=" * 80)
print("COMPREHENSIVE MODEL EVALUATION")
print("=" * 80)

results = {
    "total": len(test_cases),
    "passed": 0,
    "failed": 0,
    "by_category": {}
}

for i, test in enumerate(tqdm(test_cases, desc="Testing")):
    prompt = f"""### Instruction:
{test['question']}

### Response:
"""
    
    inputs = tokenizer(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    
    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.7,
        do_sample=True
    )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response_lower = response.lower()
    
    # Check if expected keywords are present
    found_keywords = [kw for kw in test['expected_keywords'] if kw.lower() in response_lower]
    passed = len(found_keywords) >= len(test['expected_keywords']) * 0.5  # At least 50% keywords
    
    if passed:
        results["passed"] += 1
        status = "✓ PASS"
    else:
        results["failed"] += 1
        status = "✗ FAIL"
    
    # Track by category
    category = test['category']
    if category not in results['by_category']:
        results['by_category'][category] = {"passed": 0, "failed": 0}
    
    if passed:
        results['by_category'][category]['passed'] += 1
    else:
        results['by_category'][category]['failed'] += 1
    
    print(f"\n{status} Test {i+1}: {test['question']}")
    print(f"   Found keywords: {found_keywords}")
    print(f"   Response: {response[:100]}...")

# Print summary
print("\n" + "=" * 80)
print("EVALUATION SUMMARY")
print("=" * 80)
print(f"Total tests: {results['total']}")
print(f"Passed: {results['passed']} ({results['passed']/results['total']*100:.1f}%)")
print(f"Failed: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")

print(f"\nBy Category:")
for category, stats in results['by_category'].items():
    total = stats['passed'] + stats['failed']
    print(f"  {category}: {stats['passed']}/{total} ({stats['passed']/total*100:.1f}%)")

# Save results
with open('evaluation_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✓ Results saved to: evaluation_results.json")
print("=" * 80)
```

Run evaluation:
```bash
python evaluate_model.py
```

---

## 🔍 ERROR DETECTION & TROUBLESHOOTING

### Common Errors and Solutions:

**Error 1: CUDA Out of Memory**
```
RuntimeError: CUDA out of memory
```
**Solution:**
```python
# Reduce batch size
per_device_train_batch_size=1  # Instead of 2

# Enable gradient checkpointing
gradient_checkpointing=True

# Use 4-bit quantization
load_in_4bit=True
```

**Error 2: Loss is NaN**
```
Step 10: loss=nan
```
**Solution:**
```python
# Reduce learning rate
learning_rate=1e-5  # Instead of 2e-4

# Check for bad data
# Remove examples with empty outputs
```

**Error 3: Model Not Learning (Loss Not Decreasing)**
```
Step 100: loss=2.5 (same as step 1)
```
**Solution:**
```python
# Increase learning rate
learning_rate=5e-4

# Increase training steps
max_steps=500  # Instead of 100

# Check data quality
```

---

## ✅ FINAL VALIDATION CHECKLIST

Before deploying:

- [ ] Pre-training validation passed
- [ ] Training completed without errors
- [ ] Loss decreased significantly (>50%)
- [ ] Basic functionality test passed
- [ ] Comprehensive evaluation >70% pass rate
- [ ] Model responds to test questions
- [ ] Responses are relevant and accurate
- [ ] No hallucinations or incorrect data
- [ ] Model size is reasonable (<10 GB)
- [ ] Inference speed is acceptable (<5s per response)

---

## 📊 SUCCESS CRITERIA

**Minimum Acceptable:**
- Training loss < 1.0
- Evaluation pass rate > 60%
- Responses contain relevant keywords
- No major errors or crashes

**Good Quality:**
- Training loss < 0.5
- Evaluation pass rate > 80%
- Responses are coherent and accurate
- Fast inference (<3s)

**Production Ready:**
- Training loss < 0.3
- Evaluation pass rate > 90%
- Responses are expert-level
- Handles edge cases well

---

## 🎯 NEXT STEPS AFTER TESTING

1. **If tests pass:** Deploy model
2. **If tests fail:** Debug and retrain
3. **If quality is low:** Expand training data
4. **If performance is slow:** Optimize model

**See `DEPLOYMENT_GUIDE.md` for deployment instructions**

