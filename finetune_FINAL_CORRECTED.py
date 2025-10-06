#!/usr/bin/env python3
"""
FINAL CORRECTED Fine-Tuning Script
ALL CRITICAL ISSUES FIXED:
- Correct TinyLlama Zephyr format with </s> tokens
- Proper label masking (only train on responses)
- Increased sequence length to 512
- 3 epochs for better learning
- All validation uses correct format
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
)
from datasets import Dataset
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from typing import Dict, List
import copy

print("=" * 100)
print("FINAL CORRECTED FINE-TUNING - ALL ISSUES FIXED")
print("=" * 100)
print(f"Python: {sys.version}\n")

# Configuration
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
TRAINING_DATA = "training_data_alpaca.json"
OUTPUT_DIR = "collegeadvisor_model_FINAL"
MAX_SEQ_LENGTH = 512  # Increased from 256
IGNORE_INDEX = -100  # For label masking

# FORCE CPU for stability
device = "cpu"
print(f"✓ Using CPU (stable, no NaN gradients)")
print(f"⏱️  Training will take 8-12 hours\n")

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
tokenizer.pad_token = tokenizer.eos_token  # </s>
tokenizer.padding_side = "right"

print(f"✓ EOS token: {repr(tokenizer.eos_token)}")
print(f"✓ PAD token: {repr(tokenizer.pad_token)}")

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float32,  # fp32 for CPU stability
    low_cpu_mem_usage=True,
)

print(f"✓ Model loaded\n")

# Step 3: Configure LoRA
print("Step 3: Configuring LoRA...")

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
print()

# Step 4: Prepare dataset with CORRECT TinyLlama Zephyr format
print("Step 4: Preparing dataset with CORRECT format...")

def format_example_correct(example):
    """
    CORRECT TinyLlama Zephyr format:
    <|user|>
    {instruction}</s>
    <|assistant|>
    {output}</s>
    """
    instruction = example['instruction'].strip()
    output = example['output'].strip()
    
    # CORRECT format with </s> tokens
    text = f"<|user|>\n{instruction}</s>\n<|assistant|>\n{output}</s>"
    
    return {"text": text}

# Convert and format
dataset = Dataset.from_list(data)
dataset = dataset.map(format_example_correct)

print("Sample formatted example:")
print(dataset[0]['text'][:200])
print()

# Tokenize with proper label masking
def tokenize_with_masking(examples):
    """
    Tokenize and mask labels so we only train on assistant responses.
    This prevents the model from learning to predict the instruction.
    """
    texts = examples["text"]
    
    # Tokenize full text
    model_inputs = tokenizer(
        texts,
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        padding="max_length",
        return_tensors=None,  # Return lists, not tensors
    )
    
    # Create labels (copy of input_ids)
    labels = []
    
    for i, text in enumerate(texts):
        # Find where assistant response starts
        assistant_start = text.find("<|assistant|>\n") + len("<|assistant|>\n")
        
        # Tokenize just the prefix (user part)
        prefix = text[:assistant_start]
        prefix_tokens = tokenizer(prefix, add_special_tokens=False)["input_ids"]
        prefix_len = len(prefix_tokens)
        
        # Create label: mask prefix, keep response
        label = copy.deepcopy(model_inputs["input_ids"][i])
        
        # Mask the instruction part (set to IGNORE_INDEX)
        for j in range(min(prefix_len, len(label))):
            label[j] = IGNORE_INDEX
        
        # Mask padding tokens
        for j in range(len(label)):
            if model_inputs["input_ids"][i][j] == tokenizer.pad_token_id:
                label[j] = IGNORE_INDEX
        
        labels.append(label)
    
    model_inputs["labels"] = labels
    return model_inputs

tokenized_dataset = dataset.map(
    tokenize_with_masking,
    batched=True,
    remove_columns=dataset.column_names,
    desc="Tokenizing with label masking"
)

print(f"✓ Prepared {len(tokenized_dataset)} examples with label masking\n")

# Step 5: Configure training
print("Step 5: Configuring training...")

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,  # Increased from 1 to 3
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-5,
    warmup_steps=100,  # Increased warmup
    logging_steps=10,
    save_steps=500,
    save_total_limit=3,
    fp16=False,
    bf16=False,
    optim="adamw_torch",
    max_grad_norm=1.0,
    report_to="none",
    remove_unused_columns=False,
    push_to_hub=False,
    dataloader_num_workers=0,
    logging_first_step=True,
)

print(f"✓ Epochs: {training_args.num_train_epochs}")
print(f"✓ Batch size: {training_args.per_device_train_batch_size}")
print(f"✓ Gradient accumulation: {training_args.gradient_accumulation_steps}")
print(f"✓ Effective batch size: {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps}")
print(f"✓ Learning rate: {training_args.learning_rate}")
print(f"✓ Max sequence length: {MAX_SEQ_LENGTH}")
print()

# Step 6: Create trainer with validation
print("Step 6: Creating trainer with validation...")

class ValidatingTrainer(Trainer):
    """Trainer with NaN detection and sample generation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_loss = None
        self.loss_history = []
    
    def training_step(self, model, inputs):
        loss = super().training_step(model, inputs)
        
        # Check for NaN/Inf
        if torch.isnan(loss) or torch.isinf(loss):
            print(f"\n❌ CRITICAL ERROR: Loss is {loss} at step {self.state.global_step}")
            print("Saving checkpoint before stopping...")
            self.save_model(f"{OUTPUT_DIR}/emergency_checkpoint")
            raise ValueError(f"Loss became {loss} - training stopped")
        
        # Check if loss is suspiciously low
        if self.state.global_step > 100 and loss < 0.01:
            print(f"\n⚠️  WARNING: Loss is very low ({loss:.6f}) at step {self.state.global_step}")
            print("This might indicate a problem with the data or training")
        
        self.last_loss = loss.item()
        self.loss_history.append(loss.item())
        
        return loss
    
    def log(self, logs):
        """Enhanced logging with sample generation"""
        super().log(logs)
        
        if "loss" in logs and self.state.global_step % 100 == 0:
            print(f"\n{'='*80}")
            print(f"Step {self.state.global_step}/{self.state.max_steps}")
            print(f"Loss: {logs['loss']:.4f}")
            
            # Show loss trend
            if len(self.loss_history) >= 10:
                recent_avg = sum(self.loss_history[-10:]) / 10
                print(f"Recent avg loss (last 10 steps): {recent_avg:.4f}")
            
            # Generate sample every 500 steps
            if self.state.global_step % 500 == 0 and self.state.global_step > 0:
                print("\nGenerating validation sample...")
                self.model.eval()
                
                # CORRECT format with </s>
                test_prompt = "<|user|>\nWhat is the admission rate at Stanford University?</s>\n<|assistant|>\n"
                inputs = tokenizer(test_prompt, return_tensors="pt")
                
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=80,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id,
                        eos_token_id=tokenizer.eos_token_id,
                    )
                
                response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Extract just the assistant part
                if "<|assistant|>" in response:
                    answer = response.split("<|assistant|>")[1].strip()
                else:
                    answer = response
                
                print(f"Sample response: {answer[:150]}")
                print(f"{'='*80}\n")
                
                self.model.train()

trainer = ValidatingTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

print("✓ Trainer created\n")

# Step 7: Train
print("Step 7: Starting training...")
print("=" * 100)
print("TRAINING IN PROGRESS")
print("=" * 100)
print("⏱️  Estimated time: 8-12 hours on CPU")
print("✓ Loss monitored for NaN/Inf")
print("✓ Samples generated every 500 steps")
print("✓ Training on responses only (instructions masked)")
print("=" * 100)
print()

try:
    trainer.train()
    print("\n✓ Training completed successfully!")
except Exception as e:
    print(f"\n❌ Training failed: {e}")
    import traceback
    traceback.print_exc()
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
    "How much does tuition cost at Harvard University?",
    "What are the most popular majors at MIT?",
]

print("\nTesting fine-tuned model:\n")

for question in test_questions:
    # CORRECT format
    prompt = f"<|user|>\n{question}</s>\n<|assistant|>\n"
    inputs = tokenizer(prompt, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract answer
    if "<|assistant|>" in response:
        answer = response.split("<|assistant|>")[1].strip()
    else:
        answer = response
    
    print(f"Q: {question}")
    print(f"A: {answer}")
    print()

print("=" * 100)
print("✓ FINE-TUNING COMPLETE")
print("=" * 100)
print(f"\nModel saved to: {OUTPUT_DIR}")
print("\nNext step:")
print(f"  python test_FINAL_CORRECTED.py")
print("\n" + "=" * 100)

