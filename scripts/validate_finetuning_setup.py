#!/usr/bin/env python3
"""
Comprehensive validation script for fine-tuning setup.

Validates:
- Python environment
- Dependencies
- Training data
- Model files
- R2 connectivity
- System resources
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_header(text: str):
    """Print section header."""
    print(f"\n{BLUE}{'='*80}{NC}")
    print(f"{BLUE}{text}{NC}")
    print(f"{BLUE}{'='*80}{NC}\n")

def print_success(text: str):
    """Print success message."""
    print(f"{GREEN}✅ {text}{NC}")

def print_error(text: str):
    """Print error message."""
    print(f"{RED}❌ {text}{NC}")

def print_warning(text: str):
    """Print warning message."""
    print(f"{YELLOW}⚠️  {text}{NC}")

def print_info(text: str):
    """Print info message."""
    print(f"{BLUE}ℹ️  {text}{NC}")

def check_python_version() -> Tuple[bool, str]:
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)"

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check required dependencies."""
    required = [
        'torch',
        'transformers',
        'peft',
        'accelerate',
        'datasets',
        'trl',
        'boto3',
        'python-dotenv',
        'pydantic',
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    return len(missing) == 0, missing

def check_training_data() -> Tuple[bool, Dict]:
    """Check training data files."""
    results = {}
    
    # Check Alpaca format
    alpaca_file = Path('training_data_alpaca.json')
    if alpaca_file.exists():
        try:
            with open(alpaca_file, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                results['alpaca'] = {'status': 'error', 'message': 'Not a list'}
            elif len(data) == 0:
                results['alpaca'] = {'status': 'error', 'message': 'Empty dataset'}
            else:
                # Check format
                example = data[0]
                required_keys = ['instruction', 'input', 'output']
                missing_keys = [k for k in required_keys if k not in example]
                
                if missing_keys:
                    results['alpaca'] = {'status': 'error', 'message': f'Missing keys: {missing_keys}'}
                else:
                    # Check for admission rate errors
                    admission_errors = 0
                    for ex in data[:100]:  # Sample first 100
                        if 'admission rate' in ex.get('instruction', '').lower():
                            output = ex.get('output', '')
                            # Look for rates < 1% (likely error)
                            import re
                            match = re.search(r'([\d.]+)%', output)
                            if match:
                                rate = float(match.group(1))
                                if rate < 1.0:
                                    admission_errors += 1
                    
                    results['alpaca'] = {
                        'status': 'ok',
                        'examples': len(data),
                        'admission_errors': admission_errors,
                        'file_size': alpaca_file.stat().st_size / (1024*1024)  # MB
                    }
        except Exception as e:
            results['alpaca'] = {'status': 'error', 'message': str(e)}
    else:
        results['alpaca'] = {'status': 'missing'}
    
    # Check Ollama format
    ollama_file = Path('training_data_ollama.txt')
    if ollama_file.exists():
        try:
            with open(ollama_file, 'r') as f:
                lines = f.readlines()
            
            results['ollama'] = {
                'status': 'ok',
                'lines': len(lines),
                'file_size': ollama_file.stat().st_size / (1024*1024)  # MB
            }
        except Exception as e:
            results['ollama'] = {'status': 'error', 'message': str(e)}
    else:
        results['ollama'] = {'status': 'missing'}
    
    # Overall status
    has_valid_data = any(
        r.get('status') == 'ok' for r in results.values()
    )
    
    return has_valid_data, results

def check_r2_connectivity() -> Tuple[bool, str]:
    """Check R2 connectivity."""
    try:
        import boto3
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        # Check environment variables
        required_vars = ['R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET_NAME']
        missing_vars = [v for v in required_vars if not os.getenv(v)]
        
        if missing_vars:
            return False, f"Missing env vars: {missing_vars}"
        
        # Try to connect
        s3_client = boto3.client(
            's3',
            endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
            aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
            region_name='auto'
        )
        
        # Test connection
        s3_client.head_bucket(Bucket=os.getenv('R2_BUCKET_NAME'))
        
        return True, "Connected"
        
    except Exception as e:
        return False, str(e)

def check_system_resources() -> Dict:
    """Check system resources."""
    import psutil
    
    # Memory
    mem = psutil.virtual_memory()
    mem_gb = mem.total / (1024**3)
    mem_available_gb = mem.available / (1024**3)
    
    # Disk
    disk = psutil.disk_usage('.')
    disk_free_gb = disk.free / (1024**3)
    
    # CPU
    cpu_count = psutil.cpu_count()
    
    return {
        'memory_total_gb': round(mem_gb, 2),
        'memory_available_gb': round(mem_available_gb, 2),
        'disk_free_gb': round(disk_free_gb, 2),
        'cpu_count': cpu_count,
        'memory_ok': mem_available_gb >= 4,  # Need at least 4GB
        'disk_ok': disk_free_gb >= 10,  # Need at least 10GB
    }

def check_ollama() -> Tuple[bool, str]:
    """Check if Ollama is installed and running."""
    try:
        # Check if ollama command exists
        result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "Ollama not installed"
        
        # Check if Ollama is running
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            return True, "Running"
        else:
            return False, "Not running"
    except Exception as e:
        return False, f"Not running ({str(e)})"

def main():
    """Run all validations."""
    print_header("FINE-TUNING SETUP VALIDATION")
    
    all_passed = True
    
    # 1. Python version
    print_info("Checking Python version...")
    passed, msg = check_python_version()
    if passed:
        print_success(msg)
    else:
        print_error(msg)
        all_passed = False
    
    # 2. Dependencies
    print_info("Checking dependencies...")
    passed, missing = check_dependencies()
    if passed:
        print_success("All dependencies installed")
    else:
        print_error(f"Missing dependencies: {', '.join(missing)}")
        print_info("Install with: pip install -r requirements-finetuning.txt")
        all_passed = False
    
    # 3. Training data
    print_info("Checking training data...")
    passed, results = check_training_data()
    
    for format_name, result in results.items():
        status = result.get('status')
        if status == 'ok':
            examples = result.get('examples', result.get('lines', 0))
            size_mb = result.get('file_size', 0)
            print_success(f"{format_name.upper()}: {examples} examples, {size_mb:.2f} MB")
            
            # Check for admission rate errors
            if 'admission_errors' in result and result['admission_errors'] > 0:
                print_warning(f"Found {result['admission_errors']} potential admission rate errors (< 1%)")
                print_info("Run: python scripts/fix_admission_rates.py")
        elif status == 'missing':
            print_warning(f"{format_name.upper()}: File not found")
        else:
            print_error(f"{format_name.upper()}: {result.get('message', 'Error')}")
    
    if not passed:
        all_passed = False
    
    # 4. R2 connectivity
    print_info("Checking R2 connectivity...")
    passed, msg = check_r2_connectivity()
    if passed:
        print_success(f"R2: {msg}")
    else:
        print_warning(f"R2: {msg}")
        print_info("R2 is optional if using local data (--local_data flag)")
    
    # 5. System resources
    print_info("Checking system resources...")
    resources = check_system_resources()
    print_info(f"Memory: {resources['memory_available_gb']:.1f} GB available / {resources['memory_total_gb']:.1f} GB total")
    print_info(f"Disk: {resources['disk_free_gb']:.1f} GB free")
    print_info(f"CPU: {resources['cpu_count']} cores")
    
    if not resources['memory_ok']:
        print_warning("Low memory - may need to reduce batch size")
    if not resources['disk_ok']:
        print_warning("Low disk space - may not have enough for model checkpoints")
    
    # 6. Ollama
    print_info("Checking Ollama...")
    passed, msg = check_ollama()
    if passed:
        print_success(f"Ollama: {msg}")
    else:
        print_warning(f"Ollama: {msg}")
        print_info("Ollama is needed for final model deployment")
        print_info("Install: brew install ollama")
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    if all_passed:
        print_success("All critical checks passed!")
        print_info("\nYou can now run fine-tuning:")
        print_info("  ./run_ollama_finetuning_pipeline.sh")
        print_info("  OR")
        print_info("  python unified_finetune.py --local_data training_data_alpaca.json")
        return 0
    else:
        print_error("Some checks failed - please fix issues before fine-tuning")
        return 1

if __name__ == "__main__":
    exit(main())

