#!/bin/bash

# Complete installation and fine-tuning script
# Fixes ALL issues

set -e

echo "================================================================================"
echo "COMPLETE SETUP - FIXING ALL ISSUES"
echo "================================================================================"

# Activate venv
source venv_finetune/bin/activate

# Upgrade pip
echo ""
echo "Step 1: Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install packages in correct order with correct versions
echo ""
echo "Step 2: Installing core packages (Python 3.9 compatible)..."

# Install numpy first (MUST be <2.0)
pip install "numpy<2.0.0,>=1.24.0"

# Install PyTorch
pip install torch torchvision torchaudio

# Install transformers (version compatible with Python 3.9)
pip install "transformers<4.41.0"

# Install other packages
pip install "datasets>=2.14.0"
pip install "accelerate>=0.20.0"
pip install "peft>=0.4.0"
pip install "trl<0.9.0"

# Install project dependencies
pip install python-dotenv pydantic boto3

# Install utilities
pip install tqdm

echo ""
echo "Step 3: Verifying installation..."
python -c "
import sys
print(f'Python: {sys.version}')

import numpy
print(f'✓ NumPy: {numpy.__version__}')
assert numpy.__version__.startswith('1.'), 'NumPy must be 1.x'

import torch
print(f'✓ PyTorch: {torch.__version__}')
print(f'✓ MPS available: {torch.backends.mps.is_available()}')

import transformers
print(f'✓ Transformers: {transformers.__version__}')

import peft
print(f'✓ PEFT: {peft.__version__}')

import trl
print(f'✓ TRL: {trl.__version__}')

print('\n✅ All packages installed correctly')
"

echo ""
echo "Step 4: Downloading training data..."
python -c "
from college_advisor_data.storage.r2_storage import R2StorageClient
client = R2StorageClient()
client.client.download_file(
    Bucket=client.bucket_name,
    Key='multi_source/training_datasets/instruction_dataset_alpaca.json',
    Filename='training_data_alpaca.json'
)
print('✓ Downloaded training data')
"

echo ""
echo "================================================================================"
echo "✅ SETUP COMPLETE - STARTING FINE-TUNING"
echo "================================================================================"

# Run fine-tuning
python finetune_macos.py

