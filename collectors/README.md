# Data Collectors

This directory contains data collectors for various educational data sources.

## Overview

The collectors are designed to gather comprehensive data about colleges, universities, summer programs, and related educational content from multiple sources including government APIs, university websites, review platforms, and social media.

## Architecture

All collectors inherit from `BaseCollector` which provides:
- Rate limiting and throttling
- Caching functionality
- Error handling and retry logic
- Standardized configuration
- Result tracking and metrics

## Available Collectors

### Government Data Sources

#### 1. College Scorecard Collector (`government.py`)
- **Source**: U.S. Department of Education College Scorecard API
- **Data**: Comprehensive institutional data including costs, graduation rates, earnings
- **Coverage**: All Title IV institutions in the United States
- **Status**: ✅ Implemented and tested

#### 2. IPEDS Collector (`government.py`)
- **Source**: Integrated Postsecondary Education Data System
- **Data**: Institutional characteristics, enrollment, completions, faculty, finance
- **Coverage**: All postsecondary institutions
- **Status**: 🚧 Planned

#### 3. Common Data Set Collector (`government.py`)
- **Source**: Various universities' Common Data Set publications
- **Data**: Standardized institutional data format
- **Coverage**: Universities that publish CDS
- **Status**: 🚧 Planned

### State Education APIs (`state_apis.py`)
- **Sources**: All 50 state education department APIs
- **Data**: State university system data
- **Coverage**: Public universities by state
- **Status**: 🚧 Planned

### Web Scrapers (`web_scrapers.py`)
- **Sources**: University websites, review platforms
- **Data**: Admission requirements, programs, reviews
- **Coverage**: Major universities and review sites
- **Status**: 🚧 Planned

### Summer Programs (`summer_programs.py`)
- **Sources**: TeenLife, Summer Discovery, academic camps
- **Data**: Summer program information
- **Coverage**: Academic and enrichment programs
- **Status**: 🚧 Planned

### Financial Aid (`financial_aid.py`)
- **Sources**: Fastweb, Scholarships.com, College Board
- **Data**: Scholarship and financial aid opportunities
- **Coverage**: National and regional aid programs
- **Status**: 🚧 Planned

### Social Media (`social_media.py`)
- **Sources**: Twitter, Reddit, YouTube, forums
- **Data**: Educational content and discussions
- **Coverage**: Major social platforms
- **Status**: 🚧 Planned

## Usage

### Basic Usage

```python
from collectors.base_collector import CollectorConfig
from collectors.government import CollegeScorecardCollector

# Create configuration
config = CollectorConfig(
    api_key="your_api_key",
    requests_per_second=1.0,
    cache_enabled=True
)

# Initialize collector
collector = CollegeScorecardCollector(config)

# Collect data
result = collector.collect(
    years=[2022, 2023],
    states=["CA", "NY"],
    field_groups=["basic", "admissions", "costs"]
)

print(f"Collected {result.total_records} records")
```

### CLI Usage

```bash
# Collect College Scorecard data
college-data collect --collector scorecard --years 2022,2023 --states CA,NY --field-groups basic,admissions

# Test collector
python examples/test_college_scorecard.py
```

### Configuration Options

```python
CollectorConfig(
    # Rate limiting
    requests_per_second=1.0,
    requests_per_minute=60,
    requests_per_hour=1000,
    
    # Retry configuration
    max_retries=3,
    backoff_factor=1.0,
    
    # Caching
    cache_enabled=True,
    cache_ttl_hours=24,
    
    # Authentication
    api_key="your_api_key",
    
    # Output
    output_format="json",
    batch_size=100
)
```

## Testing

Run the test suite:

```bash
# Run all collector tests
pytest tests/test_collectors.py -v

# Test specific collector
python examples/test_college_scorecard.py
```

## Data Quality

All collectors implement:
- Input validation
- Data transformation to standard format
- Error tracking and reporting
- Success rate monitoring
- Comprehensive logging

## Rate Limiting

Collectors respect API rate limits:
- Configurable requests per second/minute/hour
- Automatic throttling
- Exponential backoff on errors
- Respectful default settings

## Caching

Built-in caching system:
- Configurable TTL (time-to-live)
- Automatic cache invalidation
- Reduces API calls during development
- Improves performance

## Error Handling

Robust error handling:
- Automatic retries with backoff
- Detailed error logging
- Graceful degradation
- Comprehensive error reporting

## Next Steps

1. **Complete Implementation**: Finish implementing all planned collectors
2. **Enhanced Testing**: Add comprehensive test coverage
3. **Performance Optimization**: Optimize for large-scale data collection
4. **Monitoring**: Add detailed metrics and monitoring
5. **Documentation**: Complete API documentation for all collectors
