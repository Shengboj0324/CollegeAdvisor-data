#!/bin/bash

# End-to-End Ingestion Script for CollegeAdvisor Data Pipeline
# This script implements the canonical ingestion flow: ingest → chunk → embed → upsert

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/venv"
DATA_DIR="$PROJECT_ROOT/data"
SEED_DIR="$DATA_DIR/seed"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        error "Virtual environment not found at $VENV_PATH"
        error "Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
}

# Activate virtual environment
activate_venv() {
    log "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
    
    # Verify activation
    if [ "$VIRTUAL_ENV" != "$VENV_PATH" ]; then
        error "Failed to activate virtual environment"
        exit 1
    fi
    
    success "Virtual environment activated"
}

# Check ChromaDB connection
check_chroma() {
    log "Checking ChromaDB connection..."
    
    # Set default environment variables if not set
    export CHROMA_HOST=${CHROMA_HOST:-localhost}
    export CHROMA_PORT=${CHROMA_PORT:-8000}
    
    # Try to connect to ChromaDB
    if ! curl -s "http://$CHROMA_HOST:$CHROMA_PORT/api/v1/heartbeat" > /dev/null; then
        warning "ChromaDB not accessible at $CHROMA_HOST:$CHROMA_PORT"
        warning "Starting local ChromaDB instance..."
        
        # Try to start ChromaDB in background
        if command -v docker &> /dev/null; then
            docker run -d --name chroma-temp -p 8000:8000 chromadb/chroma || true
            sleep 5
            
            if curl -s "http://$CHROMA_HOST:$CHROMA_PORT/api/v1/heartbeat" > /dev/null; then
                success "ChromaDB started successfully"
            else
                error "Failed to start ChromaDB. Please start it manually:"
                error "docker run -d -p 8000:8000 chromadb/chroma"
                exit 1
            fi
        else
            error "Docker not found. Please start ChromaDB manually or install Docker"
            exit 1
        fi
    else
        success "ChromaDB is accessible"
    fi
}

# Create seed data if it doesn't exist
create_sample_data() {
    if [ ! -f "$SEED_DIR/sample_colleges.csv" ]; then
        log "Creating sample seed data..."
        mkdir -p "$SEED_DIR"
        
        cat > "$SEED_DIR/sample_colleges.csv" << 'EOF'
school,name,content,location,entity_type,gpa_band,majors,interests,section,url
Stanford University,Computer Science Program,"Stanford's Computer Science program is one of the top-ranked programs in the world. The curriculum covers algorithms, systems, AI, and theory.","CA, USA",program,3.5-4.0,"Computer Science,AI,Machine Learning","technology,innovation,research",Academics,https://cs.stanford.edu
MIT,Electrical Engineering,"MIT's EECS department offers cutting-edge research opportunities in electrical engineering, computer science, and related fields.","MA, USA",program,3.5-4.0,"Electrical Engineering,Computer Science","engineering,technology,innovation",Academics,https://eecs.mit.edu
UC Berkeley,Data Science,"UC Berkeley's Data Science program combines statistics, computer science, and domain expertise to extract insights from data.","CA, USA",program,3.0-3.5,"Data Science,Statistics,Computer Science","data,analytics,research",Academics,https://data.berkeley.edu
Harvard University,Liberal Arts,"Harvard College offers a comprehensive liberal arts education with opportunities to explore diverse fields of study.","MA, USA",college,3.5-4.0,"Liberal Arts,Humanities,Sciences","education,research,leadership",General,https://college.harvard.edu
Caltech,Physics Program,"Caltech's Physics program provides rigorous training in theoretical and experimental physics with small class sizes.","CA, USA",program,3.5-4.0,"Physics,Applied Physics,Astronomy","science,research,innovation",Academics,https://pma.caltech.edu
EOF
        
        success "Sample seed data created at $SEED_DIR/sample_colleges.csv"
    fi
}

# Main ingestion function
run_ingestion() {
    local seed_file="$1"
    local doc_type="${2:-program}"
    local batch_size="${3:-100}"
    local reset_collection="${4:-false}"
    
    log "Starting end-to-end ingestion pipeline..."
    log "  Source file: $seed_file"
    log "  Document type: $doc_type"
    log "  Batch size: $batch_size"
    log "  Reset collection: $reset_collection"
    
    # Build command
    local cmd="python -m college_advisor_data.cli ingest \"$seed_file\" --doc-type \"$doc_type\" --batch-size $batch_size"
    
    if [ "$reset_collection" = "true" ]; then
        cmd="$cmd --reset-collection"
    fi
    
    # Run ingestion
    log "Executing: $cmd"
    
    if eval "$cmd"; then
        success "Ingestion completed successfully!"
        
        # Show collection stats
        log "Retrieving collection statistics..."
        python -c "
from college_advisor_data.storage.chroma_client import ChromaDBClient
client = ChromaDBClient()
stats = client.stats()
print(f'📊 Collection Statistics:')
print(f'   Total documents: {stats[\"total_documents\"]}')
print(f'   Entity types: {list(stats[\"entity_types\"].keys())}')
print(f'   Schools: {len(stats[\"schools\"])}')
print(f'   Schema compliance: {stats[\"schema_compliance\"]:.2%}')
"
    else
        error "Ingestion failed!"
        exit 1
    fi
}

# Print usage
usage() {
    echo "Usage: $0 [OPTIONS] <seed_file>"
    echo ""
    echo "Options:"
    echo "  --doc-type TYPE        Document type (college, program, summer_program, etc.) [default: program]"
    echo "  --batch-size SIZE      Batch size for processing [default: 100]"
    echo "  --reset-collection     Reset ChromaDB collection before ingestion"
    echo "  --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 data/seed/colleges.csv"
    echo "  $0 data/seed/programs.csv --doc-type program --batch-size 50"
    echo "  $0 data/seed/summer_programs.csv --doc-type summer_program --reset-collection"
    echo ""
    echo "Environment Variables:"
    echo "  CHROMA_HOST           ChromaDB host [default: localhost]"
    echo "  CHROMA_PORT           ChromaDB port [default: 8000]"
}

# Parse command line arguments
SEED_FILE=""
DOC_TYPE="program"
BATCH_SIZE="100"
RESET_COLLECTION="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --doc-type)
            DOC_TYPE="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --reset-collection)
            RESET_COLLECTION="true"
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        -*)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            if [ -z "$SEED_FILE" ]; then
                SEED_FILE="$1"
            else
                error "Multiple seed files specified"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Main execution
main() {
    log "🚀 CollegeAdvisor Data Ingestion Pipeline"
    log "========================================"
    
    # Check if seed file is provided
    if [ -z "$SEED_FILE" ]; then
        warning "No seed file provided. Using sample data..."
        create_sample_data
        SEED_FILE="$SEED_DIR/sample_colleges.csv"
    fi
    
    # Validate seed file exists
    if [ ! -f "$SEED_FILE" ]; then
        error "Seed file not found: $SEED_FILE"
        exit 1
    fi
    
    # Run checks and setup
    check_venv
    activate_venv
    check_chroma
    
    # Run ingestion
    run_ingestion "$SEED_FILE" "$DOC_TYPE" "$BATCH_SIZE" "$RESET_COLLECTION"
    
    success "🎉 End-to-end ingestion pipeline completed!"
    log "The data is now ready for API consumption."
    log "API can query ChromaDB at: http://$CHROMA_HOST:$CHROMA_PORT"
}

# Run main function
main "$@"
