#!/bin/bash

################################################################################
# Virtual Environment Fix Script
#
# Fixes corrupted virtual environment by recreating it
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

VENV_DIR="venv"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Virtual Environment Fix${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if venv exists
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}⚠️  Found existing virtual environment${NC}"
    echo -e "${BLUE}[1/5] Checking for corruption...${NC}"
    
    # Try to activate and check pip
    if source $VENV_DIR/bin/activate 2>/dev/null && pip --version &>/dev/null; then
        echo -e "${GREEN}✅ Virtual environment appears healthy${NC}"
        deactivate
        
        echo ""
        echo -e "${BLUE}Do you want to recreate it anyway? (y/N)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}✅ Keeping existing virtual environment${NC}"
            exit 0
        fi
    else
        echo -e "${RED}❌ Virtual environment is corrupted${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}[2/5] Removing corrupted virtual environment...${NC}"
    deactivate 2>/dev/null || true
    rm -rf $VENV_DIR
    echo -e "${GREEN}✅ Removed${NC}"
else
    echo -e "${BLUE}[1/5] No existing virtual environment found${NC}"
    echo -e "${BLUE}[2/5] Skipping removal${NC}"
fi

echo ""
echo -e "${BLUE}[3/5] Creating fresh virtual environment...${NC}"
python3 -m venv $VENV_DIR

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${RED}❌ Failed to create virtual environment${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}[4/5] Activating virtual environment...${NC}"
source $VENV_DIR/bin/activate

echo ""
echo -e "${BLUE}[5/5] Installing dependencies...${NC}"
echo -e "${YELLOW}This may take 5-10 minutes...${NC}"
echo ""

# Upgrade pip first
pip install --upgrade pip

# Install dependencies
if [ -f "requirements-finetuning.txt" ]; then
    pip install -r requirements-finetuning.txt
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
    else
        echo ""
        echo -e "${RED}❌ Dependency installation failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ requirements-finetuning.txt not found${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verifying Installation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verify critical packages
echo -e "${BLUE}Checking PyTorch...${NC}"
python3 -c "import torch; print(f'✅ PyTorch {torch.__version__}')" || echo -e "${RED}❌ PyTorch not found${NC}"

echo -e "${BLUE}Checking Transformers...${NC}"
python3 -c "import transformers; print(f'✅ Transformers {transformers.__version__}')" || echo -e "${RED}❌ Transformers not found${NC}"

echo -e "${BLUE}Checking PEFT...${NC}"
python3 -c "import peft; print(f'✅ PEFT {peft.__version__}')" || echo -e "${RED}❌ PEFT not found${NC}"

echo -e "${BLUE}Checking NumPy...${NC}"
python3 -c "import numpy; print(f'✅ NumPy {numpy.__version__}')" || echo -e "${RED}❌ NumPy not found${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ VIRTUAL ENVIRONMENT READY${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. The virtual environment is now active"
echo -e "  2. Run the pipeline:"
echo -e "     ${YELLOW}./run_ollama_finetuning_pipeline.sh${NC}"
echo ""
echo -e "${YELLOW}Note: You're currently in the venv. To deactivate:${NC}"
echo -e "     ${YELLOW}deactivate${NC}"
echo ""

