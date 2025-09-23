# CollegeAdvisor-data Quick Start Guide

## 🚀 Getting Started

### 1. Environment Setup

```bash
# Navigate to project directory
cd CollegeAdvisor-data

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Configuration

Create a `.env` file in the project root:

```bash
# Copy example configuration
cp .env.example .env
```

Edit `.env` with your settings:

```env
# College Scorecard API (Get key from https://api.data.gov/signup/)
COLLEGE_SCORECARD_API_KEY=your_api_key_here

# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=college_advisor

# Rate Limiting (be respectful to APIs)
DEFAULT_REQUESTS_PER_SECOND=1.0
DEFAULT_REQUESTS_PER_MINUTE=60

# Data Quality
MIN_CONTENT_LENGTH=50
QUALITY_THRESHOLD=0.7
```

### 3. Test the Installation

```bash
# Check CLI is working
college-data --help

# Test basic functionality
college-data status

# Initialize if needed
college-data init
```

### 4. Collect Your First Data

#### Option A: Using Demo Key (Limited)
```bash
# Collect basic data from College Scorecard (limited by rate limits)
college-data collect --collector scorecard --field-groups basic --states CA
```

#### Option B: With Production API Key
```bash
# Collect comprehensive data
college-data collect \
  --collector scorecard \
  --years 2022,2023 \
  --states CA,NY,TX,FL \
  --field-groups basic,admissions,costs
```

### 5. Explore the Data

```bash
# Check collection status
college-data status

# Search the collected data
college-data search --query "computer science programs"

# View processed data
ls data/raw/
ls data/processed/
```

## 🔧 Development Setup

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_collectors.py -v

# Run with coverage
pytest tests/ --cov=college_advisor_data
```

### Testing Collectors

```bash
# Test College Scorecard API directly
python examples/debug_scorecard_api.py

# Test collector with sample data
python examples/test_college_scorecard.py
```

### Development Commands

```bash
# Format code
black college_advisor_data/ tests/

# Type checking
mypy college_advisor_data/

# Lint code
flake8 college_advisor_data/
```

## 📊 Data Collection Examples

### Basic University Information
```bash
college-data collect \
  --collector scorecard \
  --field-groups basic \
  --states CA \
  --output data/raw/ca_universities.json
```

### Comprehensive Data Collection
```bash
college-data collect \
  --collector scorecard \
  --years 2021,2022,2023 \
  --field-groups basic,academics,admissions,costs,aid \
  --states CA,NY,TX,FL,IL \
  --output data/raw/comprehensive_data.json
```

### Specific Program Focus
```bash
college-data collect \
  --collector scorecard \
  --field-groups academics,earnings \
  --filters "academics.program_percentage.computer>0.1"
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Rate Limit Errors
```
Error: 429 - OVER_RATE_LIMIT
```
**Solution**: 
- Get a production API key from https://api.data.gov/signup/
- Reduce `DEFAULT_REQUESTS_PER_SECOND` in `.env`
- Use caching to minimize API calls

#### 2. Import Errors
```
ModuleNotFoundError: No module named 'collectors'
```
**Solution**:
```bash
# Install in development mode
pip install -e .

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 3. ChromaDB Connection Issues
```
Connection refused to ChromaDB
```
**Solution**:
```bash
# Start ChromaDB server
chroma run --host localhost --port 8000

# Or use embedded mode (update config)
CHROMA_HOST=embedded
```

### Debug Mode

Enable verbose logging:
```bash
college-data --verbose collect --collector scorecard
```

Check logs:
```bash
tail -f logs/college_advisor.log
```

## 📚 Next Steps

### 1. Get Production API Keys
- College Scorecard: https://api.data.gov/signup/
- IPEDS: https://nces.ed.gov/ipeds/datacenter/
- Social Media APIs as needed

### 2. Explore Advanced Features
```bash
# Evaluate data quality
college-data evaluate

# Generate embeddings
college-data embed --source data/processed/

# Load into ChromaDB
college-data load --source data/processed/
```

### 3. Customize for Your Needs
- Add new collectors in `collectors/`
- Modify field mappings in `collectors/government.py`
- Extend processing pipeline in `college_advisor_data/preprocessing/`

### 4. Scale Up
- Implement additional data sources
- Set up automated pipelines
- Deploy to production environment

## 🆘 Getting Help

### Documentation
- [Implementation Status](IMPLEMENTATION_STATUS.md)
- [Collectors README](../collectors/README.md)
- [API Documentation](API_DOCUMENTATION.md)

### Support
- Check existing issues in the repository
- Create new issue with detailed description
- Include logs and error messages
- Specify your environment and configuration

### Community
- Join discussions in repository discussions
- Share your use cases and improvements
- Contribute to documentation and examples

---

**Happy data collecting! 🎓📊**
