#!/usr/bin/env python3
"""
Test script to verify the training setup is working correctly.
"""

import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_environment():
    """Test the training environment."""
    print("="*60)
    print("TESTING COLLEGEADVISOR TRAINING ENVIRONMENT")
    print("="*60)
    
    # Test basic imports
    print("\n1. Testing basic imports...")
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__} - CUDA: {torch.cuda.is_available()}")
    except Exception as e:
        print(f"❌ PyTorch: {e}")
        return False
    
    try:
        import transformers
        print(f"✅ Transformers {transformers.__version__}")
    except Exception as e:
        print(f"❌ Transformers: {e}")
        return False
    
    try:
        from datasets import Dataset
        print("✅ Datasets library")
    except Exception as e:
        print(f"❌ Datasets: {e}")
        return False
    
    # Test unsloth (optional)
    print("\n2. Testing unsloth (optional)...")
    try:
        import unsloth
        print("✅ Unsloth available")
        unsloth_available = True
    except Exception as e:
        print(f"⚠️  Unsloth not available: {e}")
        unsloth_available = False
    
    # Test training utilities
    print("\n3. Testing training utilities...")
    try:
        from ai_training.training_utils import check_training_environment
        env_info = check_training_environment()
        print(f"✅ Training utilities - Recommended: {env_info['recommended_trainer']}")
    except Exception as e:
        print(f"❌ Training utilities: {e}")
        return False
    
    # Test data loading
    print("\n4. Testing data loading...")
    try:
        data_file = Path("data/training/sample_qa.json")
        if data_file.exists():
            with open(data_file) as f:
                data = json.load(f)
            print(f"✅ Sample data loaded: {len(data)} examples")
        else:
            print("⚠️  Sample data file not found")
    except Exception as e:
        print(f"❌ Data loading: {e}")
    
    # Test model loading (lightweight)
    print("\n5. Testing lightweight model loading...")
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
        print("✅ GPT-2 tokenizer loaded successfully")
    except Exception as e:
        print(f"❌ Model loading: {e}")
        return False
    
    print("\n" + "="*60)
    print("ENVIRONMENT TEST COMPLETED")
    print("="*60)
    
    return True

def test_cpu_trainer():
    """Test the CPU trainer initialization."""
    print("\n6. Testing CPU trainer...")
    try:
        from ai_training.run_sft_cpu import CollegeAdvisorCPUTrainer
        
        # Initialize with a very small model for testing
        trainer = CollegeAdvisorCPUTrainer(
            model_name="gpt2",  # Small model for testing
            max_seq_length=128,
            use_cpu=True
        )
        print("✅ CPU trainer initialized")
        
        # Test data preparation
        sample_data = [
            {"question": "Test question?", "answer": "Test answer."}
        ]
        dataset = trainer.prepare_dataset(sample_data)
        print(f"✅ Dataset prepared: {len(dataset)} examples")
        
        return True
        
    except Exception as e:
        print(f"❌ CPU trainer test: {e}")
        return False

def main():
    """Main test function."""
    success = True
    
    # Test environment
    if not test_environment():
        success = False
    
    # Test CPU trainer
    if not test_cpu_trainer():
        success = False
    
    print(f"\n{'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
    return success

if __name__ == "__main__":
    main()
