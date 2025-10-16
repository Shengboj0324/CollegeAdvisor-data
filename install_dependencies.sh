#!/bin/bash

# ============================================================================
# Dependency Installation Script for Fine-Tuning Environment
# ============================================================================
# This script properly installs all dependencies in the virtual environment
# and fixes common installation issues.
#
# Usage: ./install_dependencies.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_msg() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

print_header() {
    echo ""
    echo "========================================================================"
    print_msg "$BLUE" "$@"
    echo "========================================================================"
    echo ""
}

# ============================================================================
# Step 1: Check Virtual Environment
# ============================================================================

print_header "Step 1: Checking Virtual Environment"

if [ ! -d "venv_finetune" ]; then
    print_msg "$RED" "❌ Virtual environment 'venv_finetune' not found!"
    print_msg "$YELLOW" "Creating virtual environment..."
    python3 -m venv venv_finetune
    print_msg "$GREEN" "✅ Virtual environment created"
else
    print_msg "$GREEN" "✅ Virtual environment found"
fi

# ============================================================================
# Step 2: Activate Virtual Environment
# ============================================================================

print_header "Step 2: Activating Virtual Environment"

# Activate the virtual environment
source venv_finetune/bin/activate

# Verify we're in the virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_msg "$GREEN" "✅ Virtual environment activated: $VIRTUAL_ENV"
else
    print_msg "$RED" "❌ Failed to activate virtual environment"
    exit 1
fi

# ============================================================================
# Step 3: Upgrade pip
# ============================================================================

print_header "Step 3: Upgrading pip"

python -m pip install --upgrade pip
print_msg "$GREEN" "✅ pip upgraded"

# ============================================================================
# Step 4: Install Core Dependencies
# ============================================================================

print_header "Step 4: Installing Core Dependencies"

print_msg "$YELLOW" "Installing python-dotenv, pydantic, boto3..."
pip install python-dotenv>=1.0.0 pydantic>=2.0.0 boto3>=1.28.0

print_msg "$GREEN" "✅ Core dependencies installed"

# ============================================================================
# Step 5: Install PyTorch
# ============================================================================

print_header "Step 5: Installing PyTorch"

print_msg "$YELLOW" "Installing PyTorch with MPS support for macOS..."
pip install torch>=2.0.0 torchvision>=0.15.0 torchaudio>=2.0.0

print_msg "$GREEN" "✅ PyTorch installed"

# ============================================================================
# Step 6: Install Transformers and Fine-Tuning Libraries
# ============================================================================

print_header "Step 6: Installing Transformers and Fine-Tuning Libraries"

print_msg "$YELLOW" "Installing transformers, datasets, accelerate, peft, trl..."
pip install transformers>=4.30.0 datasets>=2.14.0 accelerate>=0.20.0 peft>=0.4.0 "trl<0.9.0"

print_msg "$GREEN" "✅ Transformers and fine-tuning libraries installed"

# ============================================================================
# Step 7: Install Utilities
# ============================================================================

print_header "Step 7: Installing Utilities"

print_msg "$YELLOW" "Installing tqdm, numpy..."
pip install tqdm>=4.65.0 "numpy>=1.24.0,<2.0.0"

print_msg "$GREEN" "✅ Utilities installed"

# ============================================================================
# Step 8: Install Google API Libraries
# ============================================================================

print_header "Step 8: Installing Google API Libraries"

print_msg "$YELLOW" "Installing google-api-python-client, google-auth-oauthlib, google-auth-httplib2..."
pip install google-api-python-client>=2.0.0 google-auth-oauthlib>=0.5.0 google-auth-httplib2>=0.1.0

print_msg "$GREEN" "✅ Google API libraries installed"

# ============================================================================
# Step 9: Install Additional Dependencies (if needed)
# ============================================================================

print_header "Step 9: Installing Additional Dependencies"

print_msg "$YELLOW" "Installing psutil, requests, PyYAML..."
pip install psutil requests PyYAML

print_msg "$GREEN" "✅ Additional dependencies installed"

# ============================================================================
# Step 10: Verify Installation
# ============================================================================

print_header "Step 10: Verifying Installation"

echo "Checking critical packages..."
python -c "
import sys
errors = []

packages = [
    ('torch', 'PyTorch'),
    ('transformers', 'Transformers'),
    ('datasets', 'Datasets'),
    ('peft', 'PEFT'),
    ('trl', 'TRL'),
    ('boto3', 'Boto3'),
    ('dotenv', 'python-dotenv'),
    ('pydantic', 'Pydantic'),
    ('numpy', 'NumPy'),
    ('tqdm', 'tqdm'),
    ('googleapiclient', 'Google API Client'),
    ('google_auth_oauthlib', 'Google Auth OAuth'),
    ('google_auth_httplib2', 'Google Auth HTTP'),
]

print('Verifying packages:')
for module, name in packages:
    try:
        __import__(module)
        print(f'  ✅ {name}')
    except ImportError as e:
        print(f'  ❌ {name}: {e}')
        errors.append(name)

if errors:
    error_list = ', '.join(errors)
    print(f'\n❌ Failed to import: {error_list}')
    sys.exit(1)
else:
    print('\n✅ All packages verified successfully!')
    sys.exit(0)
"

if [ $? -eq 0 ]; then
    print_msg "$GREEN" "✅ All packages verified"
else
    print_msg "$RED" "❌ Some packages failed verification"
    exit 1
fi

# ============================================================================
# Step 11: Display Package Versions
# ============================================================================

print_header "Step 11: Package Versions"

python -c "
import torch
import transformers
import datasets
import peft
import trl
import numpy
import boto3

print(f'PyTorch: {torch.__version__}')
print(f'Transformers: {transformers.__version__}')
print(f'Datasets: {datasets.__version__}')
print(f'PEFT: {peft.__version__}')
print(f'TRL: {trl.__version__}')
print(f'NumPy: {numpy.__version__}')
print(f'Boto3: {boto3.__version__}')

# Check device availability
if torch.backends.mps.is_available():
    print(f'Device: MPS (Apple Silicon) ✅')
elif torch.cuda.is_available():
    print(f'Device: CUDA ✅')
else:
    print(f'Device: CPU')
"

# ============================================================================
# Completion
# ============================================================================

print_header "Installation Complete!"

print_msg "$GREEN" "✅ All dependencies installed successfully!"
echo ""
print_msg "$YELLOW" "To use the virtual environment:"
echo "  source venv_finetune/bin/activate"
echo ""
print_msg "$YELLOW" "To run fine-tuning:"
echo "  ./run_finetuning.sh"
echo ""
print_msg "$YELLOW" "To verify setup:"
echo "  python verify_unified_setup.py"
echo ""
print_msg "$GREEN" "Ready for fine-tuning! 🚀"
echo ""

