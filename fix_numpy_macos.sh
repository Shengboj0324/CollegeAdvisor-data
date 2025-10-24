#!/bin/bash

################################################################################
# NumPy Compatibility Fix for macOS
#
# Fixes NumPy 2.x incompatibility with PyTorch 2.2.0
# 
# Author: Shengbo Jiang
# Date: 2025-10-22
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}NumPy Compatibility Fix for macOS${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check current NumPy version
echo -e "${BLUE}[1/4] Checking current NumPy version...${NC}"
NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)" 2>&1)

if [[ $NUMPY_VERSION == *"2."* ]]; then
    echo -e "${RED}❌ NumPy $NUMPY_VERSION detected (incompatible)${NC}"
    echo -e "${YELLOW}⚠️  NumPy 2.x is incompatible with PyTorch 2.2.0${NC}"
    NEEDS_FIX=true
elif [[ $NUMPY_VERSION == *"1."* ]]; then
    echo -e "${GREEN}✅ NumPy $NUMPY_VERSION (compatible)${NC}"
    NEEDS_FIX=false
else
    echo -e "${RED}❌ Could not determine NumPy version${NC}"
    echo -e "${YELLOW}Error: $NUMPY_VERSION${NC}"
    exit 1
fi

echo ""

# Fix if needed
if [ "$NEEDS_FIX" = true ]; then
    echo -e "${BLUE}[2/4] Uninstalling NumPy 2.x...${NC}"
    pip uninstall -y numpy
    
    echo ""
    echo -e "${BLUE}[3/4] Installing NumPy 1.x...${NC}"
    pip install 'numpy<2.0,>=1.24.0'
    
    echo ""
    echo -e "${BLUE}[4/4] Verifying installation...${NC}"
    NEW_VERSION=$(python3 -c "import numpy; print(numpy.__version__)" 2>&1)
    
    if [[ $NEW_VERSION == *"1."* ]]; then
        echo -e "${GREEN}✅ NumPy $NEW_VERSION installed successfully${NC}"
    else
        echo -e "${RED}❌ Installation failed${NC}"
        echo -e "${YELLOW}Error: $NEW_VERSION${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}[2/4] No fix needed${NC}"
    echo -e "${BLUE}[3/4] Skipping installation${NC}"
    echo -e "${BLUE}[4/4] Verification${NC}"
    echo -e "${GREEN}✅ NumPy version is already compatible${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing PyTorch Compatibility${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test PyTorch
echo -e "${BLUE}Testing PyTorch import...${NC}"
PYTORCH_TEST=$(python3 -c "import torch; print(f'PyTorch {torch.__version__} - OK')" 2>&1)

if [[ $PYTORCH_TEST == *"OK"* ]]; then
    echo -e "${GREEN}✅ $PYTORCH_TEST${NC}"
else
    echo -e "${RED}❌ PyTorch import failed${NC}"
    echo -e "${YELLOW}Error: $PYTORCH_TEST${NC}"
    exit 1
fi

# Test MPS
echo -e "${BLUE}Testing MPS availability...${NC}"
MPS_TEST=$(python3 -c "import torch; print('MPS available' if torch.backends.mps.is_available() else 'MPS not available')" 2>&1)

if [[ $MPS_TEST == *"available"* ]]; then
    echo -e "${GREEN}✅ $MPS_TEST${NC}"
else
    echo -e "${YELLOW}⚠️  $MPS_TEST${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ FIX COMPLETE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Run readiness check:"
echo -e "     ${YELLOW}python3 scripts/macos_readiness_check.py${NC}"
echo ""
echo -e "  2. Start fine-tuning:"
echo -e "     ${YELLOW}./run_ollama_finetuning_pipeline.sh${NC}"
echo ""

