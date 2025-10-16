#!/bin/bash
#
# 🚀 UNIFIED FINE-TUNING LAUNCHER
# ================================
# 
# This script provides a simple, reliable way to run fine-tuning on MacBook.
# It handles environment setup, validation, and execution.
#
# Usage:
#   ./run_finetuning.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_msg() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

print_msg "$BLUE" "================================================================================"
print_msg "$BLUE" "🚀 UNIFIED FINE-TUNING LAUNCHER"
print_msg "$BLUE" "================================================================================"
echo

# Step 1: Check Python
print_msg "$YELLOW" "📋 Step 1: Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_msg "$RED" "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_msg "$GREEN" "✅ Python $PYTHON_VERSION found"
echo

# Step 2: Check/Create Virtual Environment
print_msg "$YELLOW" "📋 Step 2: Setting up virtual environment..."
if [ ! -d "venv_finetune" ]; then
    print_msg "$YELLOW" "Creating virtual environment..."
    python3 -m venv venv_finetune
    print_msg "$GREEN" "✅ Virtual environment created"
else
    print_msg "$GREEN" "✅ Virtual environment exists"
fi
echo

# Step 3: Activate Virtual Environment
print_msg "$YELLOW" "📋 Step 3: Activating virtual environment..."
source venv_finetune/bin/activate
print_msg "$GREEN" "✅ Virtual environment activated"
echo

# Step 4: Install/Update Dependencies
print_msg "$YELLOW" "📋 Step 4: Checking dependencies..."
if [ -f "requirements-finetuning.txt" ]; then
    print_msg "$YELLOW" "Installing/updating dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements-finetuning.txt
    print_msg "$GREEN" "✅ Dependencies installed"
else
    print_msg "$RED" "❌ requirements-finetuning.txt not found"
    exit 1
fi
echo

# Step 5: Check .env file
print_msg "$YELLOW" "📋 Step 5: Checking R2 credentials..."
if [ ! -f ".env" ]; then
    print_msg "$RED" "❌ .env file not found"
    print_msg "$YELLOW" "Please create .env file with R2 credentials:"
    print_msg "$YELLOW" "  R2_ACCOUNT_ID=your_account_id"
    print_msg "$YELLOW" "  R2_ACCESS_KEY_ID=your_access_key"
    print_msg "$YELLOW" "  R2_SECRET_ACCESS_KEY=your_secret_key"
    print_msg "$YELLOW" "  R2_BUCKET_NAME=collegeadvisor-finetuning-data"
    exit 1
fi

# Check if R2 credentials are set
if ! grep -q "R2_ACCOUNT_ID" .env || ! grep -q "R2_ACCESS_KEY_ID" .env; then
    print_msg "$RED" "❌ R2 credentials not found in .env file"
    exit 1
fi

print_msg "$GREEN" "✅ R2 credentials found"
echo

# Step 6: Check unified script
print_msg "$YELLOW" "📋 Step 6: Checking unified fine-tuning script..."
if [ ! -f "unified_finetune.py" ]; then
    print_msg "$RED" "❌ unified_finetune.py not found"
    exit 1
fi
print_msg "$GREEN" "✅ Unified script found"
echo

# Step 7: Run Fine-Tuning
print_msg "$BLUE" "================================================================================"
print_msg "$GREEN" "🚀 STARTING FINE-TUNING"
print_msg "$BLUE" "================================================================================"
echo
print_msg "$YELLOW" "⏱️  Estimated time: 1-4 hours (depending on your MacBook)"
print_msg "$YELLOW" "📝 Logs will be saved to: logs/finetuning/"
print_msg "$YELLOW" "📁 Model will be saved to: collegeadvisor_unified_model/"
echo
print_msg "$YELLOW" "Press Ctrl+C to cancel..."
sleep 2
echo

# Run the unified fine-tuning script
python3 unified_finetune.py

# Check exit code
if [ $? -eq 0 ]; then
    echo
    print_msg "$BLUE" "================================================================================"
    print_msg "$GREEN" "✅ FINE-TUNING COMPLETED SUCCESSFULLY!"
    print_msg "$BLUE" "================================================================================"
    echo
    print_msg "$GREEN" "📁 Model saved to: collegeadvisor_unified_model/"
    print_msg "$GREEN" "📝 Check logs in: logs/finetuning/"
    echo
    print_msg "$YELLOW" "Next steps:"
    print_msg "$YELLOW" "  1. Test your model (see UNIFIED_FINETUNING_GUIDE.md)"
    print_msg "$YELLOW" "  2. Deploy to production (see PRODUCTION_DEPLOYMENT_GUIDE.md)"
    echo
else
    echo
    print_msg "$BLUE" "================================================================================"
    print_msg "$RED" "❌ FINE-TUNING FAILED"
    print_msg "$BLUE" "================================================================================"
    echo
    print_msg "$YELLOW" "Please check the logs in: logs/finetuning/"
    print_msg "$YELLOW" "See UNIFIED_FINETUNING_GUIDE.md for troubleshooting"
    echo
    exit 1
fi
