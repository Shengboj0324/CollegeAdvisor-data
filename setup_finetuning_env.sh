#!/bin/bash

# Fine-tuning Environment Setup Script
# Handles all dependency issues for macOS

set -e  # Exit on error

echo "================================================================================"
echo "FINE-TUNING ENVIRONMENT SETUP"
echo "================================================================================"

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ ERROR: Not in a virtual environment"
    echo "Please activate your venv first:"
    echo "  source venv_finetune/bin/activate"
    exit 1
fi

echo "✓ Virtual environment detected: $VIRTUAL_ENV"

# Step 1: Upgrade pip
echo ""
echo "Step 1: Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel

# Step 2: Install PyTorch first (required for other packages)
echo ""
echo "Step 2: Installing PyTorch..."
echo "Detecting system..."

# Check if CUDA is available (unlikely on macOS, but check anyway)
if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA GPU detected - installing CUDA version"
    pip install torch torchvision torchaudio
else
    echo "✓ No NVIDIA GPU - installing CPU/MPS version for macOS"
    # For macOS with Apple Silicon (M1/M2/M3), use MPS backend
    pip install torch torchvision torchaudio
fi

# Step 3: Install core dependencies
echo ""
echo "Step 3: Installing core dependencies..."
pip install transformers datasets accelerate peft

# Step 4: Install bitsandbytes (with macOS compatibility)
echo ""
echo "Step 4: Installing bitsandbytes..."
# bitsandbytes 0.42.0 is the latest available, not 0.45.5
# On macOS, bitsandbytes may not work properly (it's designed for CUDA)
if [[ $(uname -m) == "arm64" ]]; then
    echo "⚠️  WARNING: Apple Silicon detected"
    echo "   bitsandbytes doesn't fully support macOS/Apple Silicon"
    echo "   Installing anyway, but 4-bit quantization may not work"
    echo "   You'll need to use fp16 or fp32 instead"
fi

pip install bitsandbytes==0.42.0 || {
    echo "⚠️  bitsandbytes installation failed (expected on macOS)"
    echo "   Continuing without it - you'll use fp16/fp32 instead of 4-bit"
}

# Step 5: Install TRL (Transformer Reinforcement Learning)
echo ""
echo "Step 5: Installing TRL..."
pip install "trl<0.9.0"

# Step 6: Skip xformers on macOS (it requires CUDA)
echo ""
echo "Step 6: Checking xformers compatibility..."
if [[ $(uname) == "Darwin" ]]; then
    echo "⚠️  macOS detected - skipping xformers (requires CUDA)"
    echo "   This is fine - PyTorch will use native attention instead"
else
    echo "Installing xformers..."
    pip install xformers || {
        echo "⚠️  xformers installation failed"
        echo "   Continuing without it - will use slower attention"
    }
fi

# Step 7: Install Unsloth (alternative approach for macOS)
echo ""
echo "Step 7: Installing Unsloth..."

# On macOS, we can't use the full Unsloth with all optimizations
# We'll use a simpler approach
echo "⚠️  Note: Full Unsloth optimizations require CUDA"
echo "   Installing base Unsloth for macOS compatibility..."

pip install git+https://github.com/unslothai/unsloth.git || {
    echo "⚠️  Full Unsloth installation failed"
    echo "   This is expected on macOS - we'll use standard fine-tuning instead"
}

# Step 8: Verify installation
echo ""
echo "================================================================================"
echo "VERIFYING INSTALLATION"
echo "================================================================================"

python -c "
import sys
print('Python version:', sys.version)
print()

packages = {
    'torch': 'PyTorch',
    'transformers': 'Transformers',
    'datasets': 'Datasets',
    'peft': 'PEFT (LoRA)',
    'accelerate': 'Accelerate',
    'trl': 'TRL',
}

print('Installed packages:')
for package, name in packages.items():
    try:
        mod = __import__(package)
        version = getattr(mod, '__version__', 'unknown')
        print(f'  ✓ {name}: {version}')
    except ImportError:
        print(f'  ✗ {name}: NOT INSTALLED')

print()

# Check for GPU/MPS
import torch
print('Hardware support:')
print(f'  CUDA available: {torch.cuda.is_available()}')
print(f'  MPS available: {torch.backends.mps.is_available()}')
print(f'  Device: {\"cuda\" if torch.cuda.is_available() else \"mps\" if torch.backends.mps.is_available() else \"cpu\"}')

# Check bitsandbytes
try:
    import bitsandbytes
    print(f'  ✓ bitsandbytes: {bitsandbytes.__version__}')
except:
    print(f'  ✗ bitsandbytes: Not available (expected on macOS)')
"

echo ""
echo "================================================================================"
echo "✓ INSTALLATION COMPLETE"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Review the verification output above"
echo "  2. If on macOS, you'll use fp16 instead of 4-bit quantization"
echo "  3. Run: python finetune_macos.py (we'll create this next)"
echo ""
echo "================================================================================"

