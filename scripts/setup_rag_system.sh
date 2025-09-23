#!/bin/bash

# CollegeAdvisor RAG System Setup Script
# This script sets up the complete RAG system following the integration plan

set -e  # Exit on any error

echo "🚀 Setting up CollegeAdvisor RAG System"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check prerequisites
echo -e "\n${BLUE}Step 1: Checking Prerequisites${NC}"
echo "--------------------------------"

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Check pip packages
echo "Checking Python packages..."
REQUIRED_PACKAGES=("chromadb" "torch" "transformers" "datasets" "requests")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        print_status "$package"
    else
        print_error "$package - missing"
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    print_warning "Installing missing packages: ${MISSING_PACKAGES[*]}"
    pip install "${MISSING_PACKAGES[@]}"
fi

# Check Ollama
if command_exists ollama; then
    print_status "Ollama found"
    OLLAMA_MODELS=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
    if [ "$OLLAMA_MODELS" -gt 0 ]; then
        print_status "Ollama has $OLLAMA_MODELS models"
    else
        print_warning "Ollama has no models installed"
        echo "Installing llama3 model (this may take a while)..."
        ollama pull llama3 || print_warning "Failed to pull llama3 model"
    fi
else
    print_warning "Ollama not found. Please install from https://ollama.ai/download"
    print_info "After installing Ollama, run: ollama pull llama3"
fi

# Step 2: Create sample data
echo -e "\n${BLUE}Step 2: Creating Sample Data${NC}"
echo "-----------------------------"

if [ ! -f "data/sample/combined_data.json" ]; then
    print_info "Creating sample data..."
    python3 scripts/create_sample_data.py
    print_status "Sample data created"
else
    print_status "Sample data already exists"
fi

# Step 3: Start ChromaDB server
echo -e "\n${BLUE}Step 3: ChromaDB Server Setup${NC}"
echo "------------------------------"

# Check if ChromaDB server is running
if curl -s http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then
    print_status "ChromaDB server is already running"
else
    print_info "Starting ChromaDB server..."
    
    # Create chroma data directory
    mkdir -p ./chroma_data
    
    # Start ChromaDB in background
    print_info "Starting ChromaDB server in background..."
    nohup chroma run --host 0.0.0.0 --port 8000 --persist_directory ./chroma_data > chroma.log 2>&1 &
    CHROMA_PID=$!
    
    # Wait for server to start
    echo "Waiting for ChromaDB server to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then
            print_status "ChromaDB server started (PID: $CHROMA_PID)"
            echo $CHROMA_PID > chroma.pid
            break
        fi
        sleep 1
        echo -n "."
    done
    
    if ! curl -s http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then
        print_error "Failed to start ChromaDB server"
        print_info "Check chroma.log for details"
        exit 1
    fi
fi

# Step 4: Test RAG system with mock data
echo -e "\n${BLUE}Step 4: Testing RAG System${NC}"
echo "---------------------------"

print_info "Testing RAG system with mock data..."
python3 rag_implementation.py

# Step 5: Create environment file
echo -e "\n${BLUE}Step 5: Environment Configuration${NC}"
echo "----------------------------------"

if [ ! -f ".env" ]; then
    print_info "Creating .env file..."
    cat > .env << EOF
# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=college_advisor

# Ollama Configuration  
OLLAMA_HOST=http://localhost:11434

# Embedding Configuration (LOCKED for MVP)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_PROVIDER=sentence_transformers

# API Contract
COLLECTION_VERSION=college_advisor@v1.0
MODEL_VERSION=llama3:base

# Logging
LOG_LEVEL=INFO
EOF
    print_status "Environment file created"
else
    print_status "Environment file already exists"
fi

# Step 6: Summary and next steps
echo -e "\n${GREEN}🎉 RAG System Setup Complete!${NC}"
echo "=============================="

echo -e "\n${BLUE}System Status:${NC}"
echo "✅ Python packages installed"
echo "✅ Sample data created"
echo "✅ ChromaDB server running"
echo "✅ RAG implementation ready"
echo "✅ Environment configured"

if command_exists ollama; then
    echo "✅ Ollama available"
else
    echo "⚠️  Ollama needs installation"
fi

echo -e "\n${BLUE}Next Steps:${NC}"
echo "1. Ingest data into ChromaDB:"
echo "   python -m college_advisor_data.cli ingest --source data/sample/combined_data.json"
echo ""
echo "2. Test full RAG system:"
echo "   python rag_implementation.py"
echo ""
echo "3. Start developing API integration"
echo ""
echo "4. For model fine-tuning:"
echo "   python ai_training/run_sft_cpu.py --data data/training/college_qa.json --output models/college_advisor"

echo -e "\n${BLUE}Useful Commands:${NC}"
echo "• Check ChromaDB: curl http://localhost:8000/api/v1/heartbeat"
echo "• Check Ollama: ollama list"
echo "• Stop ChromaDB: kill \$(cat chroma.pid) (if exists)"
echo "• View ChromaDB logs: tail -f chroma.log"

echo -e "\n${GREEN}Ready for API integration! 🚀${NC}"
