"""
Supervised Fine-Tuning (SFT) with QLoRA for CollegeAdvisor.

This script implements concrete SFT training using Unsloth and HuggingFace
for fine-tuning Llama-3-8B on curated Q&A data.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse

import torch
from datasets import Dataset
from transformers import TrainingArguments
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
from trl import SFTTrainer

logger = logging.getLogger(__name__)


class CollegeAdvisorSFTTrainer:
    """
    Supervised Fine-Tuning trainer for CollegeAdvisor using QLoRA.
    
    This trainer fine-tunes Llama-3-8B on educational Q&A data
    using QLoRA (4-bit quantization) for efficient training.
    """
    
    def __init__(self, 
                 model_name: str = "unsloth/llama-3-8b-bnb-4bit",
                 max_seq_length: int = 2048,
                 load_in_4bit: bool = True):
        """
        Initialize the SFT trainer.
        
        Args:
            model_name: Base model to fine-tune
            max_seq_length: Maximum sequence length
            load_in_4bit: Use 4-bit quantization
        """
        self.model_name = model_name
        self.max_seq_length = max_seq_length
        self.load_in_4bit = load_in_4bit
        self.model = None
        self.tokenizer = None
        
        # Training configuration
        self.lora_config = {
            "r": 16,
            "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj",
                             "gate_proj", "up_proj", "down_proj"],
            "lora_alpha": 16,
            "lora_dropout": 0.0,
            "bias": "none",
            "use_gradient_checkpointing": "unsloth",
            "random_state": 3407,
            "use_rslora": False,
            "loftq_config": None,
        }
    
    def load_model(self):
        """Load the base model and tokenizer with QLoRA configuration."""
        logger.info(f"Loading model: {self.model_name}")
        
        try:
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.model_name,
                max_seq_length=self.max_seq_length,
                dtype=None,  # Auto-detect
                load_in_4bit=self.load_in_4bit,
            )
            
            # Apply LoRA
            self.model = FastLanguageModel.get_peft_model(
                self.model,
                **self.lora_config
            )
            
            # Set chat template
            self.tokenizer = get_chat_template(
                self.tokenizer,
                chat_template="llama-3",
            )
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def load_training_data(self, data_path: str) -> Dataset:
        """
        Load and format training data from JSONL file.
        
        Args:
            data_path: Path to JSONL file with {instruction, input, output} format
            
        Returns:
            Dataset: Formatted training dataset
        """
        logger.info(f"Loading training data from: {data_path}")
        
        data_file = Path(data_path)
        if not data_file.exists():
            raise FileNotFoundError(f"Training data not found: {data_path}")
        
        # Load JSONL data
        training_examples = []
        with open(data_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    example = json.loads(line.strip())
                    
                    # Validate required fields
                    if not all(key in example for key in ['instruction', 'input', 'output']):
                        logger.warning(f"Line {line_num}: Missing required fields")
                        continue
                    
                    # Format as conversation
                    conversation = self._format_conversation(
                        instruction=example['instruction'],
                        input_text=example['input'],
                        output=example['output']
                    )
                    
                    training_examples.append({"text": conversation})
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Line {line_num}: Invalid JSON - {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Line {line_num}: Error processing - {e}")
                    continue
        
        if not training_examples:
            raise ValueError("No valid training examples found")
        
        logger.info(f"Loaded {len(training_examples)} training examples")
        return Dataset.from_list(training_examples)
    
    def _format_conversation(self, instruction: str, input_text: str, output: str) -> str:
        """
        Format training example as a conversation using Llama-3 chat template.
        
        Args:
            instruction: System instruction
            input_text: User input
            output: Expected output
            
        Returns:
            str: Formatted conversation
        """
        messages = [
            {
                "role": "system", 
                "content": instruction
            },
            {
                "role": "user", 
                "content": input_text
            },
            {
                "role": "assistant", 
                "content": output
            }
        ]
        
        return self.tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=False
        )
    
    def train(self, 
              dataset: Dataset,
              output_dir: str,
              num_train_epochs: int = 3,
              per_device_train_batch_size: int = 2,
              gradient_accumulation_steps: int = 4,
              learning_rate: float = 2e-4,
              warmup_steps: int = 5,
              logging_steps: int = 10,
              save_steps: int = 100) -> Dict[str, Any]:
        """
        Train the model using SFT.
        
        Args:
            dataset: Training dataset
            output_dir: Output directory for model checkpoints
            num_train_epochs: Number of training epochs
            per_device_train_batch_size: Batch size per device
            gradient_accumulation_steps: Gradient accumulation steps
            learning_rate: Learning rate
            warmup_steps: Warmup steps
            logging_steps: Logging frequency
            save_steps: Save frequency
            
        Returns:
            Dict: Training statistics
        """
        if not self.model or not self.tokenizer:
            self.load_model()
        
        logger.info("Starting SFT training...")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(output_path),
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            optim="adamw_8bit",
            learning_rate=learning_rate,
            weight_decay=0.01,
            lr_scheduler_type="linear",
            warmup_steps=warmup_steps,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=logging_steps,
            save_steps=save_steps,
            save_total_limit=2,
            dataloader_pin_memory=False,
            remove_unused_columns=False,
            report_to=None,  # Disable wandb
        )
        
        # Create trainer
        trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=dataset,
            args=training_args,
            dataset_text_field="text",
            max_seq_length=self.max_seq_length,
            dataset_num_proc=2,
        )
        
        # Train
        trainer.train()
        
        # Save final model
        trainer.save_model()
        
        # Get training stats
        train_result = trainer.state.log_history
        
        logger.info("Training completed successfully")
        
        return {
            "output_dir": str(output_path),
            "num_examples": len(dataset),
            "num_epochs": num_train_epochs,
            "final_loss": train_result[-1].get("train_loss", 0.0) if train_result else 0.0,
            "training_time": trainer.state.log_history[-1].get("train_runtime", 0.0) if train_result else 0.0
        }


def main():
    """Main training script."""
    parser = argparse.ArgumentParser(description="Fine-tune Llama-3-8B for CollegeAdvisor")
    parser.add_argument("--data", required=True, help="Path to training JSONL file")
    parser.add_argument("--output", required=True, help="Output directory for model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size per device")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--max-length", type=int, default=2048, help="Maximum sequence length")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize trainer
        trainer = CollegeAdvisorSFTTrainer(max_seq_length=args.max_length)
        
        # Load training data
        dataset = trainer.load_training_data(args.data)
        
        # Train model
        stats = trainer.train(
            dataset=dataset,
            output_dir=args.output,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size,
            learning_rate=args.learning_rate
        )
        
        # Save training metadata
        metadata = {
            "training_completed": datetime.now().isoformat(),
            "model_name": trainer.model_name,
            "training_data": args.data,
            "training_stats": stats,
            "hyperparameters": {
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "learning_rate": args.learning_rate,
                "max_length": args.max_length
            }
        }
        
        metadata_path = Path(args.output) / "training_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Training completed successfully!")
        print(f"   Model saved to: {args.output}")
        print(f"   Training examples: {stats['num_examples']}")
        print(f"   Final loss: {stats['final_loss']:.4f}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        print(f"❌ Training failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
