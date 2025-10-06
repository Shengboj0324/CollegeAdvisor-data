#!/usr/bin/env python3
"""
Fine-tune LLM on macOS (Apple Silicon or Intel)
Compatible with MPS (Metal Performance Shaders) and CPU
"""

import json
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import os

print("=" * 80)
print("FINE-TUNING COLLEGE ADVISOR MODEL (macOS Compatible)")
print("=" * 80)

# Configuration
MODEL_NAME = "meta-llama/Llama-3.2-1B-Instruct"  # Smaller model for macOS
TRAINING_DATA = "training_data_alpaca.json"
OUTPUT_DIR = "collegeadvisor_model_macos"
MAX_SEQ_LENGTH = 512  # Reduced for memory efficiency

# Detect device
if torch.cuda.is_available():
    device = "cuda"
    print("✓ Using CUDA GPU")
elif torch.backends.mps.is_available():
    device = "mps"
    print("✓ Using Apple Silicon MPS (Metal Performance Shaders)")
else:
    device = "cpu"
    print("⚠️  Using CPU (this will be slow)")

print(f"Device: {device}")
print()

# Step 1: Load training data
print("Step 1: Loading training data...")
if not os.path.exists(TRAINING_DATA):
    print(f"❌ ERROR: {TRAINING_DATA} not found")
    print("Please download it first:")
    print("  python -c \"from college_advisor_data.storage.r2_storage import R2StorageClient; ...")
    exit(1)

with open(TRAINING_DATA) as f:
    data = json.load(f)

print(f"✓ Loaded {len(data)} training examples")

# Step 2: Load model and tokenizer
print("\nStep 2: Loading model and tokenizer...")
print(f"Model: {MODEL_NAME}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# Load model with appropriate settings for macOS
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if device != "cpu" else torch.float32,
    device_map={"": device} if device != "mps" else None,  # MPS doesn't support device_map
    low_cpu_mem_usage=True,
)

# Move to MPS if available
if device == "mps":
    model = model.to(device)

print(f"✓ Model loaded on {device}")

# Step 3: Configure LoRA
print("\nStep 3: Configuring LoRA...")

lora_config = LoraConfig(
    r=8,  # Reduced rank for faster training
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Step 4: Prepare dataset
print("\nStep 4: Preparing dataset...")

def format_instruction(example):
    """Format example as instruction-following prompt."""
    text = f"""### Instruction:
{example['instruction']}

### Input:
{example['input']}

### Response:
{example['output']}"""
    return {"text": text}

# Convert to HuggingFace dataset
dataset = Dataset.from_list(data)
dataset = dataset.map(format_instruction)

# Tokenize
def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        padding="max_length",
    )

tokenized_dataset = dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=dataset.column_names
)

print(f"✓ Prepared {len(tokenized_dataset)} examples")

# Step 5: Configure training
print("\nStep 5: Configuring training...")

# Adjust batch size based on device
if device == "cuda":
    batch_size = 4
    gradient_accumulation = 4
elif device == "mps":
    batch_size = 2
    gradient_accumulation = 8
else:  # CPU
    batch_size = 1
    gradient_accumulation = 16

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=batch_size,
    gradient_accumulation_steps=gradient_accumulation,
    learning_rate=2e-4,
    warmup_steps=10,
    logging_steps=10,
    save_steps=100,
    save_total_limit=2,
    fp16=False,  # MPS doesn't support fp16 training yet
    bf16=False,
    optim="adamw_torch",  # Use PyTorch optimizer (compatible with MPS)
    report_to="none",  # Disable wandb
    remove_unused_columns=False,
    push_to_hub=False,
)

print(f"✓ Batch size: {batch_size}")
print(f"✓ Gradient accumulation: {gradient_accumulation}")
print(f"✓ Effective batch size: {batch_size * gradient_accumulation}")

# Step 6: Create trainer
print("\nStep 6: Creating trainer...")

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)

print("✓ Trainer created")

# Step 7: Train
print("\nStep 7: Starting training...")
print("=" * 80)
print("This will take 1-4 hours depending on your hardware")
print("You can monitor progress in the output below")
print("=" * 80)
print()

try:
    trainer.train()
    print("\n✓ Training completed successfully!")
except Exception as e:
    print(f"\n❌ Training failed: {e}")
    print("\nTroubleshooting:")
    print("  1. If out of memory: Reduce batch_size in the script")
    print("  2. If MPS error: Try setting device='cpu' in the script")
    print("  3. Check the error message above for details")
    exit(1)

# Step 8: Save model
print("\nStep 8: Saving model...")
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"✓ Model saved to: {OUTPUT_DIR}")

# Step 9: Test the model
print("\nStep 9: Testing the model...")

test_prompt = """### Instruction:
What is the admission rate at Stanford University?

### Input:


### Response:
"""

inputs = tokenizer(test_prompt, return_tensors="pt")
if device != "cpu":
    inputs = {k: v.to(device) for k, v in inputs.items()}

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=100,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("\nTest Question: What is the admission rate at Stanford University?")
print(f"Model Response:\n{response}")

print("\n" + "=" * 80)
print("✓ FINE-TUNING COMPLETE")
print("=" * 80)
print(f"\nModel saved to: {OUTPUT_DIR}")
print("\nNext steps:")
print("  1. Test the model with: python test_model_macos.py")
print("  2. Convert to GGUF for Ollama (optional)")
print("  3. Deploy the model")
print("\n" + "=" * 80)

