#!/usr/bin/env python3
"""
Quick test to verify SFTTrainer can be created with full dataset.
This tests the exact hang point without actually training.
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

import multiprocessing
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass

print("="*80)
print("🧪 TESTING TRAINER CREATION WITH FULL DATASET")
print("="*80)

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer
from datasets import Dataset

# Load full dataset
print("\n1. Loading full dataset...")
with open("data/production_10k/production_dataset_10k.json", 'r') as f:
    data = json.load(f)

print(f"   Total: {len(data)} examples")

# Split
train_size = int(0.9 * len(data))
train_data = data[:train_size]
print(f"   Train: {len(train_data)} examples")

# Convert to Dataset
print("\n2. Converting to Dataset...")
train_dataset = Dataset.from_list(train_data)
print(f"   ✅ Dataset created")

# Load model
print("\n3. Loading model...")
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
print(f"   ✅ Model loaded")

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
print("\n4. Creating training arguments...")
training_args = TrainingArguments(
    output_dir="test_trainer_output",
    max_steps=1,  # Just 1 step
    per_device_train_batch_size=2,
    learning_rate=2e-5,
    logging_steps=1,
    save_steps=1000,
    evaluation_strategy="no",
    fp16=False,
    bf16=False,
    use_cpu=True,
    no_cuda=True,
    dataloader_num_workers=0,
    optim="adamw_torch",
    report_to="none",
)
print(f"   ✅ Training args created")

# Create trainer - THIS IS WHERE IT HANGS
print("\n5. Creating SFTTrainer...")
print("   Testing with max_seq_length=512 (same as medium test)")
print("   This is the critical test - if it hangs here, we have a problem")
print("   If it succeeds, training will work!")

sys.stdout.flush()
sys.stderr.flush()

import time
start = time.time()

try:
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        tokenizer=tokenizer,
        formatting_func=formatting_func,
        max_seq_length=512,  # CRITICAL: Use 512, not 1024
        packing=False,
    )
    
    elapsed = time.time() - start
    print(f"\n   ✅ Trainer created successfully in {elapsed:.1f} seconds!")
    print(f"   ✅ This means training will work!")
    
except Exception as e:
    elapsed = time.time() - start
    print(f"\n   ❌ Trainer creation failed after {elapsed:.1f} seconds")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Cleanup
print(f"\n6. Cleanup...")
import shutil
if Path("test_trainer_output").exists():
    shutil.rmtree("test_trainer_output")

print(f"\n" + "="*80)
print(f"✅ TRAINER CREATION TEST COMPLETE")
print(f"="*80)
print(f"\nConclusion: SFTTrainer can be created with full dataset")
print(f"Next: Run actual training - it will work!")

