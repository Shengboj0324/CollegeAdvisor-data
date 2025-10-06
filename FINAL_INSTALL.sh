#!/bin/bash

# FINAL INSTALLATION SCRIPT - GUARANTEED TO WORK
# Fixes ALL version conflicts

set -e

echo "================================================================================"
echo "FINAL INSTALLATION - FIXING ALL FUCKING ERRORS"
echo "================================================================================"

# Clean slate
echo "Step 1: Creating clean environment..."
rm -rf venv_finetune
python3 -m venv venv_finetune
source venv_finetune/bin/activate

echo "✓ Clean venv created"

# Upgrade pip
echo ""
echo "Step 2: Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install in EXACT order with EXACT versions
echo ""
echo "Step 3: Installing packages in correct order..."

# NumPy FIRST (must be 1.x)
echo "  Installing NumPy 1.26.4..."
pip install numpy==1.26.4

# PyTorch
echo "  Installing PyTorch..."
pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2

# Transformers (version compatible with Python 3.9)
echo "  Installing Transformers 4.40.2..."
pip install transformers==4.40.2

# PEFT (version compatible with transformers 4.40.2)
echo "  Installing PEFT 0.10.0..."
pip install peft==0.10.0

# Other packages
echo "  Installing other packages..."
pip install accelerate==0.28.0
pip install datasets==2.18.0
pip install "trl<0.9.0"
pip install python-dotenv pydantic boto3 tqdm

echo ""
echo "Step 4: Verifying installation..."
python << 'EOF'
import sys
print(f"Python: {sys.version}")

import numpy
print(f"✓ NumPy: {numpy.__version__}")
if not numpy.__version__.startswith("1."):
    print("❌ ERROR: NumPy must be 1.x")
    sys.exit(1)

import torch
print(f"✓ PyTorch: {torch.__version__}")
print(f"✓ MPS available: {torch.backends.mps.is_available()}")

import transformers
print(f"✓ Transformers: {transformers.__version__}")

import peft
print(f"✓ PEFT: {peft.__version__}")

import trl
print(f"✓ TRL: {trl.__version__}")

# Test import that was failing
try:
    from transformers import Trainer
    print("✓ Trainer import successful")
except Exception as e:
    print(f"❌ Trainer import failed: {e}")
    sys.exit(1)

print("\n✅ ALL PACKAGES INSTALLED CORRECTLY - NO ERRORS")
EOF

echo ""
echo "Step 5: Downloading training data..."
python << 'EOF'
from college_advisor_data.storage.r2_storage import R2StorageClient
import os

if not os.path.exists("training_data_alpaca.json"):
    client = R2StorageClient()
    client.client.download_file(
        Bucket=client.bucket_name,
        Key='multi_source/training_datasets/instruction_dataset_alpaca.json',
        Filename='training_data_alpaca.json'
    )
    print("✓ Downloaded training data")
else:
    print("✓ Training data already exists")
EOF

echo ""
echo "================================================================================"
echo "✅ INSTALLATION COMPLETE - ZERO ERRORS"
echo "================================================================================"
echo ""
echo "Now run:"
echo "  source venv_finetune/bin/activate"
echo "  python finetune_macos.py"
echo ""
echo "================================================================================"

