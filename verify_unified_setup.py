#!/usr/bin/env python3
"""
🔍 Unified Fine-Tuning Setup Verification

This script verifies that the unified fine-tuning system is properly set up
and ready to use.
"""

import os
import sys
from pathlib import Path

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def check_file(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} NOT FOUND: {filepath}")
        return False

def check_env_var(var_name):
    """Check if environment variable is set."""
    value = os.getenv(var_name)
    if value:
        # Mask sensitive values
        if 'KEY' in var_name or 'SECRET' in var_name:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {var_name}: {masked}")
        else:
            print(f"✅ {var_name}: {value}")
        return True
    else:
        print(f"❌ {var_name}: NOT SET")
        return False

def check_python_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} NOT INSTALLED")
        return False

def main():
    """Run all verification checks."""
    print("\n" + "=" * 80)
    print("🔍 UNIFIED FINE-TUNING SETUP VERIFICATION")
    print("=" * 80)
    
    all_checks = []
    
    # Check 1: Core Files
    print_header("1. CORE FILES")
    checks = [
        check_file("unified_finetune.py", "Main script"),
        check_file("run_finetuning.sh", "Launcher script"),
        check_file("UNIFIED_FINETUNING_GUIDE.md", "User guide"),
        check_file("MIGRATION_TO_UNIFIED_FINETUNING.md", "Migration guide"),
        check_file("FINETUNING_CONSOLIDATION_SUMMARY.md", "Summary"),
        check_file("requirements-finetuning.txt", "Requirements"),
    ]
    all_checks.extend(checks)
    
    # Check 2: Old Scripts Removed
    print_header("2. OLD SCRIPTS REMOVED")
    old_scripts = [
        "bulletproof_finetune_macos.py",
        "advanced_finetune_macos.py",
        "production_finetune_FIXED.py",
        "production_finetune_integrated.py",
        "execute_bulletproof_training.sh",
        "run_advanced_finetuning.sh",
        "run_production_training.sh",
    ]
    
    removed_count = 0
    for script in old_scripts:
        if not Path(script).exists():
            print(f"✅ Removed: {script}")
            removed_count += 1
        else:
            print(f"⚠️  Still exists: {script}")
    
    all_checks.append(removed_count == len(old_scripts))
    
    # Check 3: Environment Variables
    print_header("3. ENVIRONMENT VARIABLES")
    
    # Load .env file
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file exists")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    else:
        print("❌ .env file NOT FOUND")
        all_checks.append(False)
    
    env_checks = [
        check_env_var("R2_ACCOUNT_ID"),
        check_env_var("R2_ACCESS_KEY_ID"),
        check_env_var("R2_SECRET_ACCESS_KEY"),
        check_env_var("R2_BUCKET_NAME"),
    ]
    all_checks.extend(env_checks)
    
    # Check 4: Python Dependencies
    print_header("4. PYTHON DEPENDENCIES")
    dep_checks = [
        check_python_package("torch"),
        check_python_package("transformers"),
        check_python_package("datasets"),
        check_python_package("peft"),
        check_python_package("trl"),
        check_python_package("boto3"),
        check_python_package("accelerate"),
    ]
    all_checks.extend(dep_checks)
    
    # Check 5: Directory Structure
    print_header("5. DIRECTORY STRUCTURE")
    dirs = [
        "logs/finetuning",
        "cache/training_data",
        "college_advisor_data/storage",
        "configs",
    ]
    
    for dir_path in dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"⚠️  {dir_path}/ (will be created automatically)")
    
    # Check 6: R2 Storage Module
    print_header("6. R2 STORAGE MODULE")
    try:
        from college_advisor_data.storage.r2_storage import R2StorageClient
        print("✅ R2StorageClient importable")
        all_checks.append(True)
    except ImportError as e:
        print(f"❌ Cannot import R2StorageClient: {e}")
        all_checks.append(False)
    
    # Final Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(all_checks)
    total = len(all_checks)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\nChecks Passed: {passed}/{total} ({percentage:.1f}%)")
    
    if all(all_checks):
        print("\n" + "=" * 80)
        print("✅ ALL CHECKS PASSED - SYSTEM READY FOR FINE-TUNING!")
        print("=" * 80)
        print("\nNext steps:")
        print("  1. Activate virtual environment: source venv_finetune/bin/activate")
        print("  2. Run fine-tuning: ./run_finetuning.sh")
        print("\nSee UNIFIED_FINETUNING_GUIDE.md for complete documentation.")
        print("=" * 80 + "\n")
        return 0
    else:
        print("\n" + "=" * 80)
        print("⚠️  SOME CHECKS FAILED")
        print("=" * 80)
        print("\nPlease fix the issues above before running fine-tuning.")
        print("\nCommon fixes:")
        print("  - Install dependencies: pip install -r requirements-finetuning.txt")
        print("  - Create .env file with R2 credentials")
        print("  - Ensure Python 3.8+ is installed")
        print("\nSee UNIFIED_FINETUNING_GUIDE.md for troubleshooting.")
        print("=" * 80 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
