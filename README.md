# CollegeAdvisor-data

**Data ingestion, processing, and embedding pipeline for the College Advisor AI app**

This repository handles the complete data pipeline for college and summer program information, from raw data ingestion to vector embeddings stored in ChromaDB.

## 🎯 Project Overview

Part of a 3-repository AI College Application Assessment App:
- **CollegeAdvisor-data** (this repo) - Data pipeline and ChromaDB management
- **CollegeAdvisor-backend** - API server with Ollama integration
- **CollegeAdvisor-ios** - SwiftUI iOS application

## 🏗️ Architecture

```
Raw Data → Preprocessing → Chunking → Embedding → ChromaDB
    ↓           ↓            ↓          ↓          ↓
  CSV/JSON   Normalize    800-token   Vector    Search
  Scraping   Clean text   chunks      embed     Ready
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone and navigate to repository
cd CollegeAdvisor-data

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Initialize pipeline
college-data init
```

### 2. Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Basic Usage

```bash
# Ingest sample data
college-data ingest --source data/seed/universities_sample.csv --doc-type university

# Load into ChromaDB
college-data load

# Search the database
college-data search --query "computer science programs"

# Check status
college-data status
```

## 📁 Repository Structure

```
CollegeAdvisor-data/
├── college_advisor_data/          # Main package
│   ├── ingestion/                 # Data loading and ingestion
│   ├── preprocessing/             # Text cleaning and chunking
│   ├── embedding/                 # Vector embedding generation
│   ├── storage/                   # ChromaDB integration
│   ├── evaluation/                # Pipeline evaluation
│   ├── config.py                  # Configuration management
│   ├── models.py                  # Data models
│   └── cli.py                     # Command-line interface
├── data/
│   ├── raw/                       # Raw input data
│   ├── processed/                 # Processed data
│   └── seed/                      # Sample/seed data
├── tests/                         # Unit tests
├── logs/                          # Log files
├── cache/                         # Temporary cache
├── requirements.txt               # Dependencies
├── pyproject.toml                 # Project configuration
└── README.md                      # This file
```