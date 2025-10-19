#!/usr/bin/env python3
"""
Test script to verify training fix works.
Tests with a tiny dataset to ensure training starts and progresses.
"""

import os
import sys
import json
import torch
from pathlib import Path

# Force CPU
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

print("="*80)
print("🧪 TESTING TRAINING FIX - CPU MODE")
print("="*80)

# Test 1: PyTorch import
print("\n1. Testing PyTorch import...")
print(f"   PyTorch version: {torch.__version__}")
print(f"   ✅ PyTorch imported successfully")

# Test 2: CPU tensor creation
print("\n2. Testing CPU tensor creation...")
try:
    x = torch.randn(10, 10, device='cpu')
    print(f"   Tensor shape: {x.shape}")
    print(f"   Tensor device: {x.device}")
    print(f"   ✅ CPU tensor created successfully")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

# Test 3: Load tiny dataset
print("\n3. Creating tiny test dataset...")
tiny_dataset = [
    {
        "instruction": "What is the acceptance rate at Harvard?",
        "input": "",
        "output": "Harvard University has a highly competitive acceptance rate of approximately 3.4%. This makes it one of the most selective universities in the United States."
    },
    {
        "instruction": "Tell me about MIT's location",
        "input": "",
        "output": "MIT (Massachusetts Institute of Technology) is located in Cambridge, Massachusetts, just across the Charles River from Boston. The campus offers easy access to the vibrant Boston area."
    }
]

test_file = Path("data/test_tiny_dataset.json")
test_file.parent.mkdir(parents=True, exist_ok=True)
with open(test_file, 'w') as f:
    json.dump(tiny_dataset, f, indent=2)

print(f"   Created test dataset: {test_file}")
print(f"   Examples: {len(tiny_dataset)}")
print(f"   ✅ Test dataset ready")

# Test 4: Import training modules
print("\n4. Testing training module imports...")
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
    from peft import LoraConfig, get_peft_model
    from trl import SFTTrainer
    from datasets import Dataset
    print(f"   ✅ All training modules imported successfully")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 5: Load model on CPU
print("\n5. Testing model loading on CPU...")
try:
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    print(f"   Loading {model_name}...")
    
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
    print(f"   Model device: {next(model.parameters()).device}")
    
except Exception as e:
    print(f"   ❌ Model loading failed: {e}")
    sys.exit(1)

# Test 6: Apply LoRA
print("\n6. Testing LoRA configuration...")
try:
    lora_config = LoraConfig(
        r=8,  # Small rank for testing
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    
    print(f"   Trainable params: {trainable_params:,}")
    print(f"   Total params: {total_params:,}")
    print(f"   Trainable %: {100 * trainable_params / total_params:.2f}%")
    print(f"   ✅ LoRA applied successfully")
    
except Exception as e:
    print(f"   ❌ LoRA failed: {e}")
    sys.exit(1)

# Test 7: Prepare dataset
print("\n7. Preparing dataset...")
try:
    dataset = Dataset.from_list(tiny_dataset)
    train_dataset = dataset
    eval_dataset = dataset  # Use same for testing
    
    print(f"   Train examples: {len(train_dataset)}")
    print(f"   Eval examples: {len(eval_dataset)}")
    print(f"   ✅ Dataset prepared")
    
except Exception as e:
    print(f"   ❌ Dataset preparation failed: {e}")
    sys.exit(1)

# Test 8: Create trainer
print("\n8. Creating SFTTrainer...")
try:
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
    
    training_args = TrainingArguments(
        output_dir="test_output",
        max_steps=2,  # Just 2 steps for testing
        per_device_train_batch_size=1,
        learning_rate=2e-5,
        logging_steps=1,
        save_steps=10,
        eval_steps=10,
        evaluation_strategy="no",  # Disable eval for quick test
        fp16=False,
        bf16=False,
        use_cpu=True,
        no_cuda=True,
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
    
    print(f"   ✅ SFTTrainer created successfully")
    
except Exception as e:
    print(f"   ❌ Trainer creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 9: Run 1 training step
print("\n9. Testing training (1 step)...")
print("   This is the critical test - if it hangs here, MPS is still being used")
print("   Starting training...")

try:
    # Train for just 2 steps (set in TrainingArguments)
    trainer.train()
    print(f"   ✅ Training steps completed successfully!")
    print(f"   ✅ NO DEADLOCK - FIX WORKS!")

except Exception as e:
    print(f"   ❌ Training failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Cleanup
print("\n10. Cleanup...")
import shutil
if Path("test_output").exists():
    shutil.rmtree("test_output")
if test_file.exists():
    test_file.unlink()
print(f"   ✅ Cleanup complete")

print("\n" + "="*80)
print("✅ ALL TESTS PASSED - TRAINING FIX VERIFIED!")
print("="*80)
print("\n🎉 The CPU-only fix works perfectly!")
print("📝 You can now run full production training with:")
print("   python train_enhanced_model.py --dataset_path data/production_10k/production_dataset_10k.json")
print("\n⏱️  Expected training time: 4-6 hours on CPU")
print("="*80)

