#!/usr/bin/env python3
"""
Test training with medium dataset (100 examples) to diagnose scale issues.
"""

import os
import sys
import json
from pathlib import Path

# Set environment variables BEFORE importing torch
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

# Force spawn for multiprocessing
import multiprocessing
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass

print("="*80)
print("🧪 TESTING MEDIUM-SCALE TRAINING (100 examples)")
print("="*80)

# Load full dataset
print("\n1. Loading full dataset...")
with open("data/production_10k/production_dataset_10k.json", 'r') as f:
    full_data = json.load(f)

print(f"   Full dataset: {len(full_data)} examples")

# Take first 100 examples
medium_data = full_data[:100]
print(f"   Medium dataset: {len(medium_data)} examples")

# Save medium dataset
medium_file = Path("data/test_medium_dataset.json")
with open(medium_file, 'w') as f:
    json.dump(medium_data, f, indent=2)

print(f"   ✅ Saved to: {medium_file}")

# Now run training
print("\n2. Starting training with 100 examples...")
print("   This will help diagnose if the issue is scale-related")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer
from datasets import Dataset

print(f"\n3. Loading model...")
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token
print(f"   ✅ Tokenizer loaded")

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float32,
    device_map=None,
    low_cpu_mem_usage=False
)
model = model.to('cpu')
print(f"   ✅ Model loaded on CPU")

# Apply LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
print(f"   ✅ LoRA applied")

# Prepare dataset
print(f"\n4. Preparing dataset...")
dataset = Dataset.from_list(medium_data)
train_size = int(0.9 * len(dataset))
train_dataset = dataset.select(range(train_size))
eval_dataset = dataset.select(range(train_size, len(dataset)))

print(f"   Train: {len(train_dataset)} examples")
print(f"   Eval: {len(eval_dataset)} examples")

# Formatting function
def formatting_func(examples):
    texts = []
    if isinstance(examples['instruction'], list):
        for i in range(len(examples['instruction'])):
            text = f"<|user|>\n{examples['instruction'][i]}"
            if examples['input'][i]:
                text += f"\n{examples['input'][i]}"
            text += f"</s>\n<|assistant|>\n{examples['output'][i]}</s>"
            texts.append(text)
    else:
        text = f"<|user|>\n{examples['instruction']}"
        if examples['input']:
            text += f"\n{examples['input']}"
        text += f"</s>\n<|assistant|>\n{examples['output']}</s>"
        texts.append(text)
    return texts

# Training arguments
print(f"\n5. Creating trainer...")
training_args = TrainingArguments(
    output_dir="test_medium_output",
    max_steps=10,  # Just 10 steps
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    learning_rate=2e-5,
    logging_steps=1,
    save_steps=100,
    eval_steps=5,
    evaluation_strategy="steps",
    fp16=False,
    bf16=False,
    use_cpu=True,
    no_cuda=True,
    dataloader_num_workers=0,  # CRITICAL
    optim="adamw_torch",
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
    formatting_func=formatting_func,
    max_seq_length=512,
    packing=False,
)

print(f"   ✅ Trainer created")

# Train
print(f"\n6. Starting training (10 steps)...")
print(f"   If this hangs, the issue is NOT scale-related")
print(f"   If this works, the issue IS scale-related")

sys.stdout.flush()
sys.stderr.flush()

try:
    trainer.train()
    print(f"\n   ✅ Training completed successfully!")
    print(f"   ✅ Medium-scale training works!")
    
except Exception as e:
    print(f"\n   ❌ Training failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Cleanup
print(f"\n7. Cleanup...")
import shutil
if Path("test_medium_output").exists():
    shutil.rmtree("test_medium_output")
if medium_file.exists():
    medium_file.unlink()

print(f"\n" + "="*80)
print(f"✅ MEDIUM-SCALE TEST COMPLETE")
print(f"="*80)
print(f"\nConclusion: Training works with 100 examples")
print(f"Next: Try with larger dataset or investigate dataloader issues")

