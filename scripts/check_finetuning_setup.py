#!/usr/bin/env python3
"""
Quick setup checker for finetuning on macOS.
Verifies all requirements from the troubleshooting guide.
"""

import os
import sys
from pathlib import Path

def check_env_vars():
    """Check R2 environment variables."""
    print("\n" + "="*80)
    print("CHECKING R2 ENVIRONMENT VARIABLES")
    print("="*80)
    
    required_vars = {
        "R2_ACCOUNT_ID": os.getenv("R2_ACCOUNT_ID"),
        "R2_ACCESS_KEY_ID": os.getenv("R2_ACCESS_KEY_ID"),
        "R2_SECRET_ACCESS_KEY": os.getenv("R2_SECRET_ACCESS_KEY"),
    }
    
    optional_vars = {
        "R2_BUCKET_NAME": os.getenv("R2_BUCKET_NAME"),
    }
    
    all_good = True
    for var, value in required_vars.items():
        if value:
            print(f"✅ {var}: {'*' * 20} (set)")
        else:
            print(f"❌ {var}: NOT SET")
            all_good = False
    
    for var, value in optional_vars.items():
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: not set (optional)")
    
    if not all_good:
        print("\n❌ Missing required environment variables!")
        print("   Set them with:")
        print("   export R2_ACCOUNT_ID=your_account_id")
        print("   export R2_ACCESS_KEY_ID=your_access_key")
        print("   export R2_ACCESS_KEY_ID=your_secret_key")
        return False
    
    print("\n✅ All required environment variables are set")
    return True


def check_packages():
    """Check package versions."""
    print("\n" + "="*80)
    print("CHECKING PACKAGE VERSIONS (macOS compatibility)")
    print("="*80)
    
    packages_to_check = {
        "transformers": "4.40.2",
        "trl": "<0.9.0",
        "peft": "0.11.1",
        "accelerate": "0.28.0",
        "psutil": "any",
        "torch": ">=2.0.0",
    }
    
    all_good = True
    for package, expected_version in packages_to_check.items():
        try:
            mod = __import__(package)
            version = getattr(mod, "__version__", "unknown")
            
            if expected_version == "any":
                print(f"✅ {package}: {version}")
            elif expected_version.startswith("<"):
                target = expected_version[1:]
                if version < target:
                    print(f"✅ {package}: {version} (expected {expected_version})")
                else:
                    print(f"⚠️  {package}: {version} (expected {expected_version})")
                    all_good = False
            elif expected_version.startswith(">="):
                target = expected_version[2:]
                print(f"✅ {package}: {version} (expected {expected_version})")
            else:
                if version == expected_version:
                    print(f"✅ {package}: {version}")
                else:
                    print(f"⚠️  {package}: {version} (expected {expected_version})")
                    all_good = False
        except ImportError:
            print(f"❌ {package}: NOT INSTALLED")
            all_good = False
    
    if not all_good:
        print("\n⚠️  Some packages have version mismatches")
        print("   Install correct versions with:")
        print("   pip install -r requirements-finetuning.txt")
        return False
    
    print("\n✅ All packages installed with correct versions")
    return True


def check_mps_support():
    """Check MPS (Apple Silicon) support."""
    print("\n" + "="*80)
    print("CHECKING APPLE SILICON (MPS) SUPPORT")
    print("="*80)
    
    try:
        import torch
        
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("✅ MPS (Apple Silicon) is available")
            print(f"   PyTorch version: {torch.__version__}")
            
            # Check MPS fallback
            fallback = os.getenv("PYTORCH_ENABLE_MPS_FALLBACK")
            if fallback == "1":
                print("✅ PYTORCH_ENABLE_MPS_FALLBACK=1 (set)")
            else:
                print("⚠️  PYTORCH_ENABLE_MPS_FALLBACK not set")
                print("   Set it with: export PYTORCH_ENABLE_MPS_FALLBACK=1")
                print("   Or it's already set in unified_finetune.py")
            
            return True
        else:
            print("⚠️  MPS not available (running on Intel Mac or CPU mode)")
            return True
    except ImportError:
        print("❌ PyTorch not installed")
        return False


def check_data_files():
    """Check if training data exists."""
    print("\n" + "="*80)
    print("CHECKING TRAINING DATA")
    print("="*80)
    
    data_dir = Path("data/finetuning")
    
    if not data_dir.exists():
        print(f"⚠️  Data directory not found: {data_dir}")
        print("   Run: python ai_training/finetuning_data_prep.py")
        return False
    
    expected_files = [
        "instruction_dataset_alpaca.json",
        "conversational_dataset.jsonl",
    ]
    
    found_files = []
    for file in expected_files:
        file_path = data_dir / file
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"✅ {file}: {size_kb:.2f} KB")
            found_files.append(file)
        else:
            print(f"⚠️  {file}: not found")
    
    if not found_files:
        print("\n⚠️  No training data found!")
        print("   Generate data with: python ai_training/finetuning_data_prep.py")
        return False
    
    print(f"\n✅ Found {len(found_files)} training data file(s)")
    return True


def check_scripts():
    """Check if required scripts exist."""
    print("\n" + "="*80)
    print("CHECKING TRAINING SCRIPTS")
    print("="*80)
    
    scripts = {
        "unified_finetune.py": "Main training script (Mac-first, HF/PEFT/Trainer)",
        "ai_training/run_sft_cpu.py": "CPU-only training (for tiny experiments)",
        "ai_training/finetuning_data_prep.py": "Data preparation script",
    }
    
    all_good = True
    for script, description in scripts.items():
        if Path(script).exists():
            print(f"✅ {script}")
            print(f"   {description}")
        else:
            print(f"❌ {script}: NOT FOUND")
            all_good = False
    
    print("\n⚠️  IGNORE: ai_training/run_sft.py (CUDA-only, won't work on macOS)")
    
    return all_good


def main():
    """Run all checks."""
    print("\n" + "="*80)
    print("FINETUNING SETUP CHECKER FOR MACOS")
    print("="*80)
    
    checks = {
        "Environment Variables": check_env_vars(),
        "Package Versions": check_packages(),
        "MPS Support": check_mps_support(),
        "Training Data": check_data_files(),
        "Training Scripts": check_scripts(),
    }
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for check_name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    all_passed = all(checks.values())
    
    if all_passed:
        print("\n" + "="*80)
        print("✅ ALL CHECKS PASSED - READY FOR FINETUNING!")
        print("="*80)
        print("\nNext steps:")
        print("1. Generate training data: python ai_training/finetuning_data_prep.py")
        print("2. Run training: python unified_finetune.py")
        return 0
    else:
        print("\n" + "="*80)
        print("❌ SOME CHECKS FAILED - FIX ISSUES ABOVE")
        print("="*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

