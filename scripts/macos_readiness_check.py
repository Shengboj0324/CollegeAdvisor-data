#!/usr/bin/env python3
"""
macOS Fine-Tuning Readiness Check

Analyzes the system for macOS-specific issues that could cause:
- Stuck processes
- Power/sleep interruptions
- Memory issues
- Data quality problems
"""

import json
import subprocess
import sys
from pathlib import Path

# Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*80}{NC}")
    print(f"{BLUE}{text}{NC}")
    print(f"{BLUE}{'='*80}{NC}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{NC}")

def print_error(text):
    print(f"{RED}❌ {text}{NC}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{NC}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{NC}")

def check_power_settings():
    """Check macOS power settings."""
    print_info("Checking power settings...")
    
    try:
        # Check battery status
        result = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True)
        output = result.stdout
        
        if 'AC Power' in output or 'AC attached' in output:
            print_success("System is plugged into AC power")
        else:
            print_error("System is running on battery")
            print_warning("Fine-tuning on battery may cause interruptions")
            print_info("Recommendation: Plug into AC power before starting")
            return False
        
        # Check sleep settings
        result = subprocess.run(['pmset', '-g'], capture_output=True, text=True)
        output = result.stdout
        
        # Look for sleep settings
        if 'sleep' in output.lower():
            print_info("Sleep settings detected - checking...")
            if 'displaysleep' in output.lower():
                print_warning("Display sleep is enabled")
                print_info("This is OK - display can sleep during training")
            
        return True
        
    except Exception as e:
        print_warning(f"Could not check power settings: {e}")
        return True

def check_numpy_compatibility():
    """Check NumPy version compatibility."""
    print_info("Checking NumPy compatibility...")
    
    try:
        import numpy as np
        version = np.__version__
        major = int(version.split('.')[0])
        
        if major >= 2:
            print_error(f"NumPy {version} detected (version 2.x)")
            print_error("NumPy 2.x is incompatible with PyTorch 2.2.0")
            print_info("Fix: pip install 'numpy<2.0'")
            return False
        else:
            print_success(f"NumPy {version} (compatible)")
            return True
            
    except Exception as e:
        print_error(f"Could not check NumPy: {e}")
        return False

def check_mps_device():
    """Check MPS device and warn about issues."""
    print_info("Checking Apple Silicon MPS device...")
    
    try:
        import torch
        
        if torch.backends.mps.is_available():
            print_warning("MPS (Apple Silicon GPU) is available")
            print_warning("MPS has known NaN gradient issues with fine-tuning")
            print_info("Recommendation: Use CPU device (--device cpu)")
            print_info("Pipeline is configured to use CPU by default")
            return True
        else:
            print_info("MPS not available - will use CPU")
            return True
            
    except Exception as e:
        print_error(f"Could not check MPS: {e}")
        return False

def check_memory_pressure():
    """Check memory pressure and swap usage."""
    print_info("Checking memory pressure...")
    
    try:
        import psutil
        
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        available_gb = mem.available / (1024**3)
        total_gb = mem.total / (1024**3)
        swap_used_gb = swap.used / (1024**3)
        
        print_info(f"Memory: {available_gb:.1f} GB available / {total_gb:.1f} GB total")
        print_info(f"Swap used: {swap_used_gb:.1f} GB")
        
        if available_gb < 3:
            print_error(f"Low memory: {available_gb:.1f} GB available")
            print_warning("Fine-tuning requires at least 3GB available")
            print_info("Close other applications before starting")
            return False
        elif available_gb < 5:
            print_warning(f"Moderate memory: {available_gb:.1f} GB available")
            print_info("Consider closing other applications")
        else:
            print_success(f"Good memory: {available_gb:.1f} GB available")
        
        if swap_used_gb > 5:
            print_warning(f"High swap usage: {swap_used_gb:.1f} GB")
            print_info("System may be under memory pressure")
        
        return True
        
    except Exception as e:
        print_error(f"Could not check memory: {e}")
        return False

def check_disk_space():
    """Check disk space for model checkpoints."""
    print_info("Checking disk space...")
    
    try:
        import psutil
        
        disk = psutil.disk_usage('.')
        free_gb = disk.free / (1024**3)
        
        print_info(f"Disk space: {free_gb:.1f} GB free")
        
        if free_gb < 5:
            print_error(f"Low disk space: {free_gb:.1f} GB")
            print_warning("Fine-tuning requires at least 5GB for checkpoints")
            return False
        elif free_gb < 10:
            print_warning(f"Moderate disk space: {free_gb:.1f} GB")
            print_info("Consider freeing up space")
        else:
            print_success(f"Good disk space: {free_gb:.1f} GB")
        
        return True
        
    except Exception as e:
        print_error(f"Could not check disk space: {e}")
        return False

def check_training_data_quality():
    """Check training data for quality issues."""
    print_info("Checking training data quality...")
    
    try:
        with open('training_data_alpaca.json', 'r') as f:
            data = json.load(f)
        
        total = len(data)
        print_info(f"Total examples: {total}")
        
        # Check for issues
        empty_outputs = 0
        very_long = 0
        admission_rate_errors = 0
        
        for i, ex in enumerate(data):
            # Empty outputs
            if not ex.get('output', '').strip():
                empty_outputs += 1
            
            # Very long examples (> 2000 chars)
            text_len = len(ex.get('instruction', '')) + len(ex.get('input', '')) + len(ex.get('output', ''))
            if text_len > 2000:
                very_long += 1
            
            # Check admission rates (should be > 1%)
            if 'admission rate' in ex.get('instruction', '').lower():
                import re
                match = re.search(r'([\d.]+)%', ex.get('output', ''))
                if match:
                    rate = float(match.group(1))
                    if rate < 1.0:
                        admission_rate_errors += 1
        
        # Report
        if empty_outputs > 0:
            print_error(f"Found {empty_outputs} examples with empty outputs")
            return False
        else:
            print_success("No empty outputs")
        
        if very_long > 0:
            print_warning(f"Found {very_long} very long examples (>2000 chars)")
            print_info("Long examples may cause memory issues")
        
        if admission_rate_errors > 0:
            print_error(f"Found {admission_rate_errors} admission rate errors (< 1%)")
            print_info("Run: python scripts/fix_admission_rates.py")
            return False
        else:
            print_success("All admission rates look correct")
        
        # Calculate average length
        total_chars = sum(
            len(ex.get('instruction', '')) + len(ex.get('input', '')) + len(ex.get('output', ''))
            for ex in data
        )
        avg_chars = total_chars // total
        print_info(f"Average example length: {avg_chars} characters")
        
        return True
        
    except FileNotFoundError:
        print_error("training_data_alpaca.json not found")
        return False
    except Exception as e:
        print_error(f"Error checking training data: {e}")
        return False

def check_process_limits():
    """Check macOS process limits."""
    print_info("Checking process limits...")
    
    try:
        # Check file descriptor limits
        result = subprocess.run(['ulimit', '-n'], shell=True, capture_output=True, text=True)
        fd_limit = result.stdout.strip()
        
        print_info(f"File descriptor limit: {fd_limit}")
        
        if fd_limit and int(fd_limit) < 1024:
            print_warning(f"Low file descriptor limit: {fd_limit}")
            print_info("May cause issues with large datasets")
        
        return True
        
    except Exception as e:
        print_warning(f"Could not check process limits: {e}")
        return True

def generate_caffeinate_command():
    """Generate caffeinate command to prevent sleep."""
    print_info("Generating anti-sleep command...")
    
    cmd = "caffeinate -i ./run_ollama_finetuning_pipeline.sh"
    
    print_success("Use this command to prevent sleep during training:")
    print(f"\n    {cmd}\n")
    print_info("The 'caffeinate -i' prefix prevents system idle sleep")
    
    return cmd

def main():
    """Run all macOS readiness checks."""
    print_header("macOS FINE-TUNING READINESS CHECK")
    
    all_passed = True
    critical_failed = False
    
    # Critical checks
    print_header("CRITICAL CHECKS")
    
    if not check_numpy_compatibility():
        all_passed = False
        critical_failed = True
    
    if not check_training_data_quality():
        all_passed = False
        critical_failed = True
    
    # Important checks
    print_header("IMPORTANT CHECKS")
    
    if not check_power_settings():
        all_passed = False
    
    if not check_memory_pressure():
        all_passed = False
    
    if not check_disk_space():
        all_passed = False
        critical_failed = True
    
    # Advisory checks
    print_header("ADVISORY CHECKS")
    
    check_mps_device()
    check_process_limits()
    
    # Recommendations
    print_header("RECOMMENDATIONS FOR macOS")
    
    print_info("1. PREVENT SLEEP:")
    generate_caffeinate_command()
    
    print_info("2. CLOSE UNNECESSARY APPS:")
    print("   - Close browsers with many tabs")
    print("   - Close Slack, Discord, etc.")
    print("   - Close IDEs if not needed")
    
    print_info("3. MONITOR PROGRESS:")
    print("   - Training will take 30-60 minutes")
    print("   - Watch for NaN warnings")
    print("   - Check Activity Monitor if stuck")
    
    print_info("4. DEVICE SELECTION:")
    print("   - Pipeline uses CPU by default (recommended)")
    print("   - MPS has NaN gradient issues")
    print("   - CPU is slower but more stable")
    
    print_info("5. BATCH SIZE:")
    print("   - Default: 2 (safe for most Macs)")
    print("   - If memory errors: reduce to 1")
    print("   - If plenty of RAM: try 4")
    
    # Summary
    print_header("READINESS SUMMARY")
    
    if critical_failed:
        print_error("CRITICAL ISSUES FOUND - MUST FIX BEFORE TRAINING")
        print_info("Fix the errors above and run this check again")
        return 1
    elif not all_passed:
        print_warning("WARNINGS FOUND - TRAINING MAY HAVE ISSUES")
        print_info("Review warnings above and address if possible")
        print_info("You can proceed but monitor closely")
        return 0
    else:
        print_success("ALL CHECKS PASSED - READY FOR TRAINING")
        print_info("\nTo start training with sleep prevention:")
        print(f"\n    caffeinate -i ./run_ollama_finetuning_pipeline.sh\n")
        return 0

if __name__ == "__main__":
    exit(main())

