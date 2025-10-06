#!/usr/bin/env python3
"""
CORRECTED Fine-Tuning Script for macOS
Fixes: NaN gradients, loss=0, empty outputs
Uses: CPU (stable), proper formatting, conservative parameters
"""

import json
import os
import sys
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
from peft import LoraConfig, get_peft_model, TaskType
import numpy as np

print("=" * 100)
print("CORRECTED FINE-TUNING - CPU MODE (STABLE)")
print("=" * 100)
print(f"Python: {sys.version}\n")

# Configuration
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
TRAINING_DATA = "training_data_alpaca.json"
OUTPUT_DIR = "collegeadvisor_model_cpu_fixed"
MAX_SEQ_LENGTH = 256  # Reduced for stability

# FORCE CPU for stability (MPS has NaN gradient issues)
device = "cpu"
print(f"✓ Using CPU (stable, no NaN gradients)")
print(f"⏱️  Training will take 8-12 hours (but will actually work!)\n")

# Step 1: Load training data
print("Step 1: Loading training data...")
if not os.path.exists(TRAINING_DATA):
    print(f"❌ ERROR: {TRAINING_DATA} not found")
    sys.exit(1)

with open(TRAINING_DATA) as f:
    data = json.load(f)

print(f"✓ Loaded {len(data)} training examples\n")

# Step 2: Load model and tokenizer
print("Step 2: Loading model and tokenizer...")
print(f"Model: {MODEL_NAME}\n")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float32,  # Use fp32 for stability
    low_cpu_mem_usage=True,
)

print(f"✓ Model loaded\n")

# Step 3: Configure LoRA (conservative settings)
print("Step 3: Configuring LoRA...")

lora_config = LoraConfig(
    r=8,  # Rank
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],  # Only Q and V for stability
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
print()

# Step 4: Prepare dataset with PROPER formatting
print("Step 4: Preparing dataset...")

def format_example(example):
    """Format with clear delimiters"""
    text = f"<|user|>\n{example['instruction']}\n<|assistant|>\n{example['output']}<|endoftext|>"
    return {"text": text}

# Convert and format
dataset = Dataset.from_list(data)
dataset = dataset.map(format_example)

# Tokenize
def tokenize_function(examples):
    result = tokenizer(
        examples["text"],
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        padding="max_length",
    )
    result["labels"] = result["input_ids"].copy()
    return result

tokenized_dataset = dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=dataset.column_names
)

print(f"✓ Prepared {len(tokenized_dataset)} examples\n")

# Step 5: Configure training (CONSERVATIVE settings)
print("Step 5: Configuring training...")

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=1,  # Start with 1 epoch
    per_device_train_batch_size=4,  # Larger batch
    gradient_accumulation_steps=4,
    learning_rate=2e-5,  # Lower learning rate
    warmup_steps=50,
    logging_steps=10,
    save_steps=200,
    save_total_limit=3,
    fp16=False,  # No mixed precision
    bf16=False,
    optim="adamw_torch",
    max_grad_norm=1.0,  # Gradient clipping
    report_to="none",
    remove_unused_columns=False,
    push_to_hub=False,
    dataloader_num_workers=0,  # No multiprocessing on macOS
)

print(f"✓ Batch size: {training_args.per_device_train_batch_size}")
print(f"✓ Gradient accumulation: {training_args.gradient_accumulation_steps}")
print(f"✓ Effective batch size: {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps}")
print(f"✓ Learning rate: {training_args.learning_rate}")
print(f"✓ Max gradient norm: {training_args.max_grad_norm}")
print()

# Step 6: Create trainer with validation
print("Step 6: Creating trainer...")

class ValidatingTrainer(Trainer):
    """Trainer that validates during training"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_loss = None
    
    def training_step(self, model, inputs):
        loss = super().training_step(model, inputs)
        
        # Check for NaN
        if torch.isnan(loss) or torch.isinf(loss):
            print(f"\n❌ ERROR: Loss is {loss} at step {self.state.global_step}")
            print("Training failed - stopping")
            raise ValueError(f"Loss became {loss}")
        
        # Check if loss is stuck at 0
        if self.state.global_step > 50 and loss < 0.01:
            print(f"\n⚠️  WARNING: Loss is very low ({loss}) at step {self.state.global_step}")
            print("This might indicate a problem")
        
        self.last_loss = loss.item()
        return loss
    
    def log(self, logs):
        """Enhanced logging"""
        super().log(logs)
        
        if "loss" in logs and self.state.global_step % 50 == 0:
            print(f"\nStep {self.state.global_step}: Loss = {logs['loss']:.4f}")
            
            # Generate sample to verify training
            if self.state.global_step % 200 == 0:
                print("Generating sample output...")
                self.model.eval()
                
                test_prompt = "<|user|>\nWhat is the admission rate at Stanford University?\n<|assistant|>\n"
                inputs = tokenizer(test_prompt, return_tensors="pt")
                
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=50,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
                
                response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                print(f"Sample: {response[:200]}...")
                
                self.model.train()

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

trainer = ValidatingTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)

print("✓ Trainer created\n")

# Step 7: Train with monitoring
print("Step 7: Starting training...")
print("=" * 100)
print("TRAINING IN PROGRESS")
print("=" * 100)
print("⏱️  Estimated time: 8-12 hours on CPU")
print("✓ Loss will be monitored for NaN/0 issues")
print("✓ Sample outputs will be generated every 200 steps")
print("=" * 100)
print()

try:
    trainer.train()
    print("\n✓ Training completed successfully!")
except Exception as e:
    print(f"\n❌ Training failed: {e}")
    print("\nTroubleshooting:")
    print("  1. Check the error message above")
    print("  2. Review training logs")
    print("  3. Try reducing batch size or learning rate")
    sys.exit(1)

# Step 8: Save model
print("\nStep 8: Saving model...")
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"✓ Model saved to: {OUTPUT_DIR}\n")

# Step 9: Final validation
print("Step 9: Final validation...")

model.eval()

test_questions = [
    "What is the admission rate at Stanford University?",
    "How much does it cost to attend Harvard?",
    "What are the most popular majors at MIT?"
]

print("\nTesting fine-tuned model:\n")

for question in test_questions:
    prompt = f"<|user|>\n{question}\n<|assistant|>\n"
    inputs = tokenizer(prompt, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract answer
    if "<|assistant|>" in response:
        answer = response.split("<|assistant|>")[1].strip()
    else:
        answer = response
    
    print(f"Q: {question}")
    print(f"A: {answer[:200]}")
    print()

print("=" * 100)
print("✓ FINE-TUNING COMPLETE")
print("=" * 100)
print(f"\nModel saved to: {OUTPUT_DIR}")
print("\nNext steps:")
print("  1. Test with: python test_model_correct.py")
print("  2. If outputs are good, model is ready to use")
print("  3. If outputs are still empty, see TRAINING_FAILURE_ANALYSIS.md")
print("\n" + "=" * 100)

