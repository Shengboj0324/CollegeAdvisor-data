#!/bin/bash

################################################################################
# END-TO-END OLLAMA FINE-TUNING PIPELINE (macOS Optimized)
#
# This script runs the complete pipeline:
# 1. macOS readiness checks
# 2. Fine-tune TinyLlama with LoRA
# 3. Convert to GGUF format
# 4. Create Ollama Modelfile
# 5. Import into Ollama
# 6. Test the model
#
# macOS Optimizations:
# - Prevents system sleep during training
# - Checks power/memory/disk
# - Uses CPU device (MPS has NaN issues)
# - Validates NumPy compatibility
#
# Author: Shengbo Jiang
# Date: 2025-10-22
################################################################################

set -e  # Exit on error

# Prevent system sleep during execution
echo "🔒 Preventing system sleep during training..."
caffeinate -i -w $$ &
CAFFEINATE_PID=$!

# Cleanup on exit
cleanup() {
    echo "🔓 Re-enabling system sleep..."
    kill $CAFFEINATE_PID 2>/dev/null || true
}
trap cleanup EXIT

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
PYTHON_VERSION="3.9"
VENV_DIR="venv"
OUTPUT_DIR="./fine_tuned_model"
GGUF_DIR="./gguf_models"
MODEL_NAME="college-advisor-llama"
OLLAMA_MODEL_NAME="college-advisor:latest"

################################################################################
# PHASE 0: macOS READINESS CHECK
################################################################################

log_info "=========================================="
log_info "PHASE 0: macOS READINESS CHECK"
log_info "=========================================="

# Run macOS-specific checks
log_info "Running macOS readiness checks..."
if [ -f "scripts/macos_readiness_check.py" ]; then
    python3 scripts/macos_readiness_check.py
    if [ $? -ne 0 ]; then
        log_error "macOS readiness check failed"
        log_error "Please fix the issues above before continuing"
        exit 1
    fi
    log_success "macOS readiness check passed"
else
    log_warning "macOS readiness check script not found - skipping"
fi

################################################################################
# PHASE 1: ENVIRONMENT SETUP
################################################################################

log_info "=========================================="
log_info "PHASE 1: ENVIRONMENT SETUP"
log_info "=========================================="

# Check Python version
log_info "Checking Python version..."
PYTHON_CMD=$(which python3 || which python)
PYTHON_VER=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
log_info "Found Python $PYTHON_VER"

# Activate virtual environment
if [ ! -d "$VENV_DIR" ]; then
    log_error "Virtual environment not found at $VENV_DIR"
    log_info "Creating virtual environment..."
    $PYTHON_CMD -m venv $VENV_DIR
fi

log_info "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Install dependencies
log_info "Installing dependencies..."
if [ -f "requirements-finetuning.txt" ]; then
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements-finetuning.txt
    log_success "Dependencies installed"
else
    log_error "requirements-finetuning.txt not found"
    exit 1
fi

# Verify critical dependencies
log_info "Verifying critical dependencies..."
python3 -c "import torch; import transformers; import peft; print('✅ PyTorch, Transformers, PEFT OK')" || {
    log_error "Critical dependencies missing"
    exit 1
}

log_success "Environment setup complete"

################################################################################
# PHASE 2: DATA VALIDATION
################################################################################

log_info "=========================================="
log_info "PHASE 2: DATA VALIDATION"
log_info "=========================================="

# Check training data exists
if [ ! -f "training_data_alpaca.json" ]; then
    log_error "Training data not found: training_data_alpaca.json"
    exit 1
fi

# Validate training data
log_info "Validating training data..."
python3 -c "
import json
import sys

try:
    with open('training_data_alpaca.json', 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print('❌ Training data must be a list')
        sys.exit(1)
    
    if len(data) == 0:
        print('❌ Training data is empty')
        sys.exit(1)
    
    # Check first example
    example = data[0]
    required_keys = ['instruction', 'input', 'output']
    for key in required_keys:
        if key not in example:
            print(f'❌ Missing required key: {key}')
            sys.exit(1)
    
    print(f'✅ Training data validated: {len(data)} examples')
    
except Exception as e:
    print(f'❌ Error validating training data: {e}')
    sys.exit(1)
" || exit 1

log_success "Data validation complete"

################################################################################
# PHASE 3: FINE-TUNING
################################################################################

log_info "=========================================="
log_info "PHASE 3: FINE-TUNING WITH LoRA"
log_info "=========================================="

log_info "Starting fine-tuning process..."
log_warning "This may take 30-60 minutes depending on your hardware"

python3 unified_finetune.py \
    --output_dir "$OUTPUT_DIR" \
    --num_epochs 3 \
    --batch_size 2 \
    --learning_rate 2e-5 \
    --max_seq_length 1024 \
    --lora_r 32 \
    --lora_alpha 64 \
    --lora_dropout 0.05 \
    --device cpu \
    --save_steps 100 \
    --logging_steps 10

if [ $? -ne 0 ]; then
    log_error "Fine-tuning failed"
    exit 1
fi

log_success "Fine-tuning complete"

# Verify model output
if [ ! -d "$OUTPUT_DIR" ]; then
    log_error "Output directory not found: $OUTPUT_DIR"
    exit 1
fi

log_info "Checking for model files..."
if [ ! -f "$OUTPUT_DIR/adapter_config.json" ]; then
    log_error "LoRA adapter not found"
    exit 1
fi

log_success "Model files verified"

################################################################################
# PHASE 4: GGUF CONVERSION
################################################################################

log_info "=========================================="
log_info "PHASE 4: GGUF CONVERSION FOR OLLAMA"
log_info "=========================================="

log_info "Converting model to GGUF format..."
mkdir -p "$GGUF_DIR"

python3 ai_training/export_to_ollama.py \
    --model_path "$OUTPUT_DIR" \
    --output_dir "$GGUF_DIR" \
    --model_name "$MODEL_NAME" \
    --quantization "q4_k_m"

if [ $? -ne 0 ]; then
    log_error "GGUF conversion failed"
    exit 1
fi

log_success "GGUF conversion complete"

# Find GGUF file
GGUF_FILE=$(find "$GGUF_DIR" -name "*.gguf" | head -n 1)
if [ -z "$GGUF_FILE" ]; then
    log_error "GGUF file not found in $GGUF_DIR"
    exit 1
fi

log_info "GGUF file: $GGUF_FILE"

################################################################################
# PHASE 5: OLLAMA IMPORT
################################################################################

log_info "=========================================="
log_info "PHASE 5: OLLAMA MODEL IMPORT"
log_info "=========================================="

# Check if Ollama is running
log_info "Checking Ollama service..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log_error "Ollama is not running. Please start Ollama first:"
    log_error "  brew services start ollama"
    log_error "  OR"
    log_error "  ollama serve"
    exit 1
fi

log_success "Ollama is running"

# Create Modelfile
MODELFILE_PATH="$GGUF_DIR/Modelfile"
log_info "Creating Modelfile..."

cat > "$MODELFILE_PATH" << EOF
FROM $GGUF_FILE

TEMPLATE """{{{{ if .System }}}}<|start_header_id|>system<|end_header_id|>

{{{{ .System }}}}<|eot_id|>{{{{ end }}}}{{{{ if .Prompt }}}}<|start_header_id|>user<|end_header_id|>

{{{{ .Prompt }}}}<|eot_id|>{{{{ end }}}}<|start_header_id|>assistant<|end_header_id|>

{{{{ .Response }}}}<|eot_id|>"""

PARAMETER stop "<|start_header_id|>"
PARAMETER stop "<|end_header_id|>"
PARAMETER stop "<|eot_id|>"
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40

SYSTEM """You are a knowledgeable college admissions advisor. You provide accurate, helpful information about universities, admission requirements, and the college application process. Base your responses on factual data."""
EOF

log_success "Modelfile created: $MODELFILE_PATH"

# Import model into Ollama
log_info "Importing model into Ollama as '$OLLAMA_MODEL_NAME'..."
ollama create "$OLLAMA_MODEL_NAME" -f "$MODELFILE_PATH"

if [ $? -ne 0 ]; then
    log_error "Failed to import model into Ollama"
    exit 1
fi

log_success "Model imported into Ollama"

################################################################################
# PHASE 6: MODEL TESTING
################################################################################

log_info "=========================================="
log_info "PHASE 6: MODEL TESTING"
log_info "=========================================="

log_info "Testing model with sample queries..."

# Test query 1
log_info "Test 1: Admission rate query"
RESPONSE=$(ollama run "$OLLAMA_MODEL_NAME" "What is the admission rate at Stanford University?" 2>&1)
echo "$RESPONSE"

# Test query 2
log_info "Test 2: General college question"
RESPONSE=$(ollama run "$OLLAMA_MODEL_NAME" "What factors should I consider when choosing a college?" 2>&1)
echo "$RESPONSE"

log_success "Model testing complete"

################################################################################
# COMPLETION
################################################################################

log_success "=========================================="
log_success "PIPELINE COMPLETE!"
log_success "=========================================="

echo ""
log_info "Summary:"
log_info "  - Fine-tuned model: $OUTPUT_DIR"
log_info "  - GGUF model: $GGUF_FILE"
log_info "  - Ollama model: $OLLAMA_MODEL_NAME"
echo ""
log_info "To use the model:"
log_info "  ollama run $OLLAMA_MODEL_NAME"
echo ""
log_info "To list all models:"
log_info "  ollama list"
echo ""
log_info "To remove the model:"
log_info "  ollama rm $OLLAMA_MODEL_NAME"
echo ""

log_success "All phases completed successfully!"

