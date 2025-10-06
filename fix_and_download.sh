#!/bin/bash

# Fix environment and download training data

set -e

echo "================================================================================"
echo "FIX ENVIRONMENT AND DOWNLOAD DATA"
echo "================================================================================"

# Check if venv exists
if [ ! -d "venv_finetune" ]; then
    echo "❌ ERROR: venv_finetune not found"
    echo "Creating it now..."
    python3 -m venv venv_finetune
fi

# Activate venv
echo ""
echo "Activating virtual environment..."
source venv_finetune/bin/activate

# Verify we're in venv
if [[ "$VIRTUAL_ENV" != *"venv_finetune"* ]]; then
    echo "❌ ERROR: Failed to activate venv"
    echo "Please run manually:"
    echo "  source venv_finetune/bin/activate"
    exit 1
fi

echo "✓ Virtual environment activated: $VIRTUAL_ENV"

# Install missing dependencies
echo ""
echo "Installing missing dependencies..."
pip install python-dotenv boto3

# Verify installation
echo ""
echo "Verifying installation..."
python -c "
import sys
print(f'Python: {sys.executable}')

try:
    import dotenv
    print('✓ python-dotenv installed')
except ImportError:
    print('❌ python-dotenv NOT installed')
    sys.exit(1)

try:
    import boto3
    print('✓ boto3 installed')
except ImportError:
    print('❌ boto3 NOT installed')
    sys.exit(1)
"

# Download training data
echo ""
echo "================================================================================"
echo "DOWNLOADING TRAINING DATA FROM R2"
echo "================================================================================"

python -c "
from college_advisor_data.storage.r2_storage import R2StorageClient

client = R2StorageClient()

print('Downloading training_data_alpaca.json...')
client.client.download_file(
    Bucket=client.bucket_name,
    Key='multi_source/training_datasets/instruction_dataset_alpaca.json',
    Filename='training_data_alpaca.json'
)

print('✓ Downloaded training_data_alpaca.json')
"

# Verify download
echo ""
echo "Verifying download..."
python -c "
import json
from pathlib import Path

file = Path('training_data_alpaca.json')
if not file.exists():
    print('❌ ERROR: File not downloaded')
    exit(1)

size_mb = file.stat().st_size / 1024 / 1024
print(f'✓ File exists: {size_mb:.2f} MB')

with open(file) as f:
    data = json.load(f)

print(f'✓ Valid JSON: {len(data)} training examples')
"

echo ""
echo "================================================================================"
echo "✓ COMPLETE"
echo "================================================================================"
echo ""
echo "Training data ready: training_data_alpaca.json"
echo ""
echo "Next step: Run fine-tuning"
echo "  python finetune_macos.py"
echo ""
echo "================================================================================"

