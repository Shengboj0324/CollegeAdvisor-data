"""
CPU-Compatible Supervised Fine-Tuning (SFT) for CollegeAdvisor.

This script provides a CPU-compatible alternative to the GPU-based unsloth training,
using standard HuggingFace transformers for development and testing purposes.
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
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    pipeline
)

logger = logging.getLogger(__name__)


class CollegeAdvisorCPUTrainer:
    """
    CPU-compatible Supervised Fine-Tuning trainer for CollegeAdvisor.
    
    This trainer provides a fallback for systems without CUDA support,
    using standard HuggingFace transformers instead of unsloth.
    """
    
    def __init__(self, 
                 model_name: str = "microsoft/DialoGPT-medium",
                 max_seq_length: int = 512,
                 use_cpu: bool = True):
        """
        Initialize the CPU trainer.
        
        Args:
            model_name: Base model to fine-tune (CPU-friendly)
            max_seq_length: Maximum sequence length
            use_cpu: Force CPU usage
        """
        self.model_name = model_name
        self.max_seq_length = max_seq_length
        self.use_cpu = use_cpu
        self.model = None
        self.tokenizer = None
        
        # Set device
        self.device = "cpu" if use_cpu or not torch.cuda.is_available() else "cuda"
        logger.info(f"Using device: {self.device}")
    
    def load_model(self):
        """Load the base model and tokenizer for CPU training."""
        logger.info(f"Loading model: {self.model_name}")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,  # Use float32 for CPU
                device_map=None if self.use_cpu else "auto"
            )
            
            if self.use_cpu:
                self.model = self.model.to("cpu")
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def prepare_dataset(self, data: List[Dict[str, Any]]) -> Dataset:
        """
        Prepare training dataset from Q&A data.
        
        Args:
            data: List of Q&A dictionaries
            
        Returns:
            Dataset: Prepared training dataset
        """
        logger.info(f"Preparing dataset with {len(data)} examples")
        
        # Format conversations for training
        formatted_data = []
        for item in data:
            # Create conversation format
            conversation = f"Question: {item.get('question', '')}\nAnswer: {item.get('answer', '')}"
            formatted_data.append({"text": conversation})
        
        # Create dataset
        dataset = Dataset.from_list(formatted_data)
        
        # Tokenize
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                padding=True,
                max_length=self.max_seq_length,
                return_tensors="pt"
            )
        
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        return tokenized_dataset
    
    def load_training_data(self, data_path: str) -> Dataset:
        """
        Load and prepare training data from file.
        
        Args:
            data_path: Path to training data file
            
        Returns:
            Dataset: Prepared training dataset
        """
        logger.info(f"Loading training data from: {data_path}")
        
        data_file = Path(data_path)
        if not data_file.exists():
            raise FileNotFoundError(f"Training data file not found: {data_path}")
        
        # Load data based on file extension
        if data_file.suffix == '.json':
            with open(data_file, 'r') as f:
                data = json.load(f)
        elif data_file.suffix == '.jsonl':
            data = []
            with open(data_file, 'r') as f:
                for line in f:
                    data.append(json.loads(line.strip()))
        else:
            raise ValueError(f"Unsupported file format: {data_file.suffix}")
        
        return self.prepare_dataset(data)
    
    def train(self, 
              dataset: Dataset,
              output_dir: str,
              num_train_epochs: int = 3,
              per_device_train_batch_size: int = 4,
              gradient_accumulation_steps: int = 2,
              learning_rate: float = 5e-5,
              warmup_steps: int = 100,
              logging_steps: int = 10,
              save_steps: int = 500) -> Dict[str, Any]:
        """
        Train the model using standard HuggingFace Trainer.
        
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
        
        logger.info("Starting training...")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_steps=logging_steps,
            save_steps=save_steps,
            save_total_limit=3,
            prediction_loss_only=True,
            remove_unused_columns=False,
            dataloader_pin_memory=False,  # Disable for CPU
            use_cpu=self.use_cpu,
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,  # Causal LM, not masked LM
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        # Train
        train_result = trainer.train()
        
        # Save model
        trainer.save_model()
        trainer.save_state()
        
        # Save training statistics
        stats = {
            "train_loss": train_result.training_loss,
            "train_runtime": train_result.metrics["train_runtime"],
            "train_samples_per_second": train_result.metrics["train_samples_per_second"],
            "train_steps_per_second": train_result.metrics["train_steps_per_second"],
        }
        
        logger.info(f"Training completed. Final loss: {stats['train_loss']:.4f}")
        return stats


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description="CPU-compatible SFT training for CollegeAdvisor")
    parser.add_argument("--data", type=str, required=True, help="Path to training data file")
    parser.add_argument("--output", type=str, required=True, help="Output directory for model")
    parser.add_argument("--model", type=str, default="microsoft/DialoGPT-medium", help="Base model name")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Training batch size")
    parser.add_argument("--learning-rate", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--max-length", type=int, default=512, help="Maximum sequence length")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize trainer
        trainer = CollegeAdvisorCPUTrainer(
            model_name=args.model,
            max_seq_length=args.max_length
        )
        
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
        
        logger.info(f"Training completed successfully. Model saved to: {args.output}")
        logger.info(f"Training metadata saved to: {metadata_path}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
