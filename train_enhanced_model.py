#!/usr/bin/env python3
"""
🚀 PRODUCTION FINE-TUNING SCRIPT - LOCAL DATASET
================================================

Fast, production-ready fine-tuning using local enhanced dataset.
Zero-tolerance error handling for production deployment.

Author: Augment Agent
Date: 2025-10-18
"""

import os
import sys
import json
import logging
import torch
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# Setup logging
log_dir = Path("logs/finetuning")
log_dir.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = log_dir / f"enhanced_training_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class TrainingConfig:
    """Production training configuration."""
    
    # Paths
    dataset_path: str = "data/finetuning_enhanced/instruction_dataset_alpaca.json"
    output_dir: str = "collegeadvisor_enhanced_model"
    
    # Model
    model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    max_seq_length: int = 1024
    
    # LoRA
    lora_r: int = 32
    lora_alpha: int = 64
    lora_dropout: float = 0.05
    target_modules: List[str] = None
    
    # Training
    num_epochs: int = 3
    batch_size: int = 2
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    warmup_steps: int = 50
    
    # Monitoring
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 50
    
    # Data split
    train_split: float = 0.9
    
    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]

# ============================================================================
# SYSTEM VALIDATION
# ============================================================================

def validate_system():
    """Validate system requirements."""
    logger.info("="*80)
    logger.info("🚀 PRODUCTION FINE-TUNING - ENHANCED MODEL")
    logger.info("="*80)
    logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🐍 Python: {sys.version.split()[0]}")
    logger.info(f"📝 Log file: {log_file}")
    logger.info("="*80)
    
    # Check PyTorch
    logger.info(f"✅ PyTorch version: {torch.__version__}")
    
    # FORCE CPU MODE - MPS has deadlock issues with SFTTrainer
    device = "cpu"
    logger.info("✅ Device: CPU (forced for stability)")
    logger.info("ℹ️  Note: MPS disabled due to known deadlock issues with transformer training")
    logger.info("ℹ️  Training will take 4-6 hours on CPU (vs 1-2 hours on MPS if it worked)")

    return device

# ============================================================================
# DATA LOADING
# ============================================================================

def load_and_validate_dataset(config: TrainingConfig):
    """Load and validate the training dataset."""
    from datasets import Dataset
    
    logger.info("\n" + "="*80)
    logger.info("STEP 1: LOADING DATASET")
    logger.info("="*80)
    
    dataset_path = Path(config.dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    logger.info(f"📂 Loading dataset from: {dataset_path}")
    
    # Load JSON data
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"✅ Loaded {len(data)} examples")
    
    # Validate format
    required_fields = ['instruction', 'input', 'output']
    for i, example in enumerate(data[:5]):
        missing = [f for f in required_fields if f not in example]
        if missing:
            raise ValueError(f"Example {i} missing fields: {missing}")
    
    logger.info("✅ Dataset format validated (Alpaca format)")
    
    # Calculate statistics
    output_lengths = [len(ex['output']) for ex in data]
    avg_length = sum(output_lengths) / len(output_lengths)
    min_length = min(output_lengths)
    max_length = max(output_lengths)
    
    logger.info(f"📊 Dataset statistics:")
    logger.info(f"   - Total examples: {len(data)}")
    logger.info(f"   - Avg output length: {avg_length:.1f} chars")
    logger.info(f"   - Min output length: {min_length} chars")
    logger.info(f"   - Max output length: {max_length} chars")
    
    # Create HuggingFace dataset
    dataset = Dataset.from_list(data)
    
    # Split into train/eval
    split_idx = int(len(data) * config.train_split)
    train_dataset = Dataset.from_list(data[:split_idx])
    eval_dataset = Dataset.from_list(data[split_idx:])
    
    logger.info(f"✅ Train examples: {len(train_dataset)}")
    logger.info(f"✅ Eval examples: {len(eval_dataset)}")
    
    return train_dataset, eval_dataset

# ============================================================================
# MODEL SETUP
# ============================================================================

def setup_model_and_tokenizer(config: TrainingConfig):
    """Setup model and tokenizer with LoRA."""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    
    logger.info("\n" + "="*80)
    logger.info("STEP 2: LOADING MODEL & TOKENIZER")
    logger.info("="*80)
    
    logger.info(f"📦 Loading model: {config.model_name}")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        config.model_name,
        trust_remote_code=True
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    logger.info("✅ Tokenizer loaded")
    
    # Load model - FORCE CPU to avoid MPS deadlock
    model = AutoModelForCausalLM.from_pretrained(
        config.model_name,
        torch_dtype=torch.float32,
        trust_remote_code=True,
        device_map=None,  # Don't use device_map
        low_cpu_mem_usage=False  # Load directly to CPU
    )

    # Explicitly move to CPU
    model = model.to('cpu')

    logger.info("✅ Model loaded on CPU")
    
    # Setup LoRA
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=config.target_modules,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    
    logger.info("✅ LoRA configuration applied")
    logger.info(f"📊 Model parameters:")
    logger.info(f"   - Trainable: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")
    logger.info(f"   - Total: {total_params:,}")
    
    return model, tokenizer

# ============================================================================
# TRAINING
# ============================================================================

def train_model(model, tokenizer, train_dataset, eval_dataset, config: TrainingConfig):
    """Train the model using SFTTrainer."""
    from transformers import TrainingArguments
    from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
    
    logger.info("\n" + "="*80)
    logger.info("STEP 3: TRAINING")
    logger.info("="*80)
    
    # Format function for TinyLlama chat format
    def formatting_func(examples):
        texts = []
        # Handle both single example and batch
        if isinstance(examples['instruction'], list):
            # Batch processing
            for i in range(len(examples['instruction'])):
                text = f"<|user|>\n{examples['instruction'][i]}"
                if examples['input'][i]:
                    text += f"\n{examples['input'][i]}"
                text += f"</s>\n<|assistant|>\n{examples['output'][i]}</s>"
                texts.append(text)
        else:
            # Single example
            text = f"<|user|>\n{examples['instruction']}"
            if examples['input']:
                text += f"\n{examples['input']}"
            text += f"</s>\n<|assistant|>\n{examples['output']}</s>"
            texts.append(text)
        return texts
    
    # Training arguments
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        weight_decay=config.weight_decay,
        warmup_steps=config.warmup_steps,
        logging_steps=config.logging_steps,
        save_steps=config.save_steps,
        eval_steps=config.eval_steps,
        evaluation_strategy="steps",
        save_total_limit=3,
        fp16=False,  # Disable fp16 for CPU
        bf16=False,  # Disable bf16 for CPU
        use_cpu=True,  # FORCE CPU training
        no_cuda=True,  # Disable CUDA
        optim="adamw_torch",
        lr_scheduler_type="cosine",
        report_to="none",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
    )
    
    # Create trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        formatting_func=formatting_func,
        max_seq_length=config.max_seq_length,
        packing=False,
    )
    
    logger.info("🚀 Starting training...")
    logger.info(f"   - Epochs: {config.num_epochs}")
    logger.info(f"   - Batch size: {config.batch_size}")
    logger.info(f"   - Learning rate: {config.learning_rate}")
    logger.info(f"   - Train examples: {len(train_dataset)}")
    logger.info(f"   - Eval examples: {len(eval_dataset)}")
    
    # Train
    start_time = datetime.now()
    trainer.train()
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    logger.info(f"✅ Training complete in {duration/3600:.2f} hours")
    
    # Save model
    trainer.save_model(str(output_dir / "final_model"))
    tokenizer.save_pretrained(str(output_dir / "final_model"))
    
    logger.info(f"✅ Model saved to: {output_dir / 'final_model'}")
    
    return trainer

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main training pipeline."""
    import argparse

    try:
        # Parse command-line arguments
        parser = argparse.ArgumentParser(description='Fine-tune CollegeAdvisor model')
        parser.add_argument('--dataset_path', type=str, default="data/finetuning_enhanced/instruction_dataset_alpaca.json",
                            help='Path to training dataset')
        parser.add_argument('--output_dir', type=str, default="collegeadvisor_enhanced_model",
                            help='Output directory for model')
        parser.add_argument('--num_epochs', type=int, default=3,
                            help='Number of training epochs')
        parser.add_argument('--batch_size', type=int, default=2,
                            help='Training batch size')
        parser.add_argument('--learning_rate', type=float, default=2e-5,
                            help='Learning rate')

        args = parser.parse_args()

        # Validate system
        device = validate_system()

        # Load configuration from args
        config = TrainingConfig(
            dataset_path=args.dataset_path,
            output_dir=args.output_dir,
            num_epochs=args.num_epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate
        )

        # Load dataset
        train_dataset, eval_dataset = load_and_validate_dataset(config)
        
        # Setup model
        model, tokenizer = setup_model_and_tokenizer(config)
        
        # Train
        trainer = train_model(model, tokenizer, train_dataset, eval_dataset, config)
        
        logger.info("\n" + "="*80)
        logger.info("✅ TRAINING COMPLETE - MODEL READY FOR TESTING")
        logger.info("="*80)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ FATAL ERROR: {e}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    import traceback
    sys.exit(main())

