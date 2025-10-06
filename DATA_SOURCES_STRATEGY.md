# Comprehensive Data Sources Strategy for CollegeAdvisor Fine-Tuning

## Research Summary

Based on intensive research, the following data sources have been identified as optimal for training a high-accuracy college admissions AI model.

## Primary Data Sources (Highest Priority)

### 1. College Scorecard (U.S. Department of Education)
**Format:** JSON, CSV via API
**Coverage:** 7,000+ institutions
**Data Quality:** Official government data, highest reliability
**Key Fields:**
- Institutional characteristics (name, location, type, size)
- Admissions data (acceptance rates, SAT/ACT scores)
- Student demographics and diversity metrics
- Costs (tuition, fees, room & board)
- Financial aid statistics
- Completion and graduation rates
- Post-graduation earnings data
- Program-level data (field of study outcomes)

**API Endpoint:** https://api.data.gov/ed/collegescorecard/v1/schools
**Status:** Already implemented in collectors/government.py
**Action:** Enhance to download complete dataset

### 2. IPEDS (Integrated Postsecondary Education Data System)
**Format:** CSV, Access Database, JSON via API
**Coverage:** All Title IV institutions (6,700+)
**Data Quality:** Comprehensive, annually updated
**Key Fields:**
- Institutional characteristics
- Enrollment data (by demographics, program, level)
- Completions (degrees/certificates awarded)
- Student financial aid
- Human resources (faculty, staff)
- Finance (revenues, expenses, endowment)
- Academic libraries
- Admissions and test scores

**API Endpoint:** https://educationdata.urban.org/documentation/
**Status:** Partially implemented
**Action:** Implement full IPEDS data download

### 3. Common Data Set (CDS)
**Format:** PDF, Excel (requires scraping/parsing)
**Coverage:** 1,000+ selective institutions
**Data Quality:** Standardized, institution-reported
**Key Fields:**
- Detailed admissions requirements
- Application deadlines and procedures
- Freshman profile (GPA, test scores, class rank)
- Transfer admission policies
- Academic offerings and special programs
- Student life information

**Source:** Individual college websites
**Status:** Not implemented
**Action:** Create CDS scraper and PDF parser

## Secondary Data Sources (High Value)

### 4. University Rankings Data
**Sources:**
- QS World University Rankings
- Times Higher Education
- U.S. News & World Report
- Forbes College Rankings

**Format:** Structured data (scrapable)
**Value:** Prestige indicators, program strengths, research output
**Action:** Implement rankings aggregator

### 5. College Admissions Essays (Successful Applications)
**Sources:**
- CollegeVine essay database
- AdmitSee successful essays
- College Essay Guy examples
- Reddit r/ApplyingToCollege

**Format:** Text, PDF
**Value:** Training data for essay evaluation and guidance
**Action:** Ethical scraping with proper attribution

### 6. Program-Specific Data
**Sources:**
- Peterson's Graduate Programs
- GradSchools.com
- Individual department websites

**Format:** Structured web data
**Value:** Detailed program requirements, specializations
**Action:** Targeted web scraping

## Tertiary Data Sources (Supplementary)

### 7. Student Reviews and Experiences
**Sources:**
- Niche.com
- College Confidential
- Unigo
- RateMyProfessors

**Format:** Text reviews, ratings
**Value:** Student perspectives, campus culture insights
**Action:** Sentiment analysis pipeline

### 8. Financial Aid and Scholarship Data
**Sources:**
- Federal Student Aid (FSA)
- Scholarship databases (Fastweb, Scholarships.com)
- Institutional financial aid pages

**Format:** Structured data, PDFs
**Value:** Financial planning guidance
**Action:** Financial aid data aggregator

### 9. Career Outcomes Data
**Sources:**
- LinkedIn Education insights
- Payscale College Salary Report
- Bureau of Labor Statistics

**Format:** Structured data
**Value:** ROI analysis, career trajectory predictions
**Action:** Outcomes data integration

## Data Quality Requirements

### Format Standards
- **JSON:** Preferred for structured institutional data
- **CSV:** Acceptable for tabular data (easily convertible)
- **PDF:** Acceptable for documents (requires OCR/parsing)
- **Text:** Acceptable for essays and reviews

### Quality Criteria
1. **Completeness:** >80% field coverage for core attributes
2. **Accuracy:** Official sources preferred, cross-validation required
3. **Recency:** Data from last 3 years prioritized
4. **Consistency:** Standardized field names and formats
5. **Volume:** Minimum 5,000 institutions for comprehensive coverage

## Data Processing Pipeline

### Stage 1: Collection
- Automated API calls for College Scorecard and IPEDS
- Scheduled web scraping for CDS and rankings
- Manual curation for essay examples

### Stage 2: Cleaning
- Standardize institution names and identifiers
- Handle missing values (imputation strategies)
- Remove duplicates and resolve conflicts
- Normalize numeric fields (scores, costs, rates)

### Stage 3: Enrichment
- Cross-reference data across sources
- Calculate derived metrics (selectivity index, value score)
- Add geographic and demographic context
- Generate embeddings for text content

### Stage 4: Validation
- Data quality checks (completeness, accuracy)
- Statistical validation (outlier detection)
- Schema compliance verification
- Sample review and spot-checking

### Stage 5: Storage
- ChromaDB for vector embeddings
- Cloudflare R2 for raw data archives
- PostgreSQL for structured data (if needed)
- JSON files for training datasets

## Fine-Tuning Dataset Composition

### Training Data Mix (Recommended)
1. **Institutional Data (40%):** College Scorecard + IPEDS
2. **Admissions Data (25%):** CDS + historical acceptance data
3. **Student Experiences (15%):** Reviews + essays
4. **Outcomes Data (10%):** Earnings + career paths
5. **Contextual Data (10%):** Rankings + program details

### Dataset Size Targets
- **Minimum:** 10,000 institution records
- **Optimal:** 25,000+ records with full enrichment
- **Text Corpus:** 1M+ tokens for language understanding
- **Q&A Pairs:** 50,000+ for instruction tuning

## Implementation Priority

### Phase 1 (Immediate - Week 1)
1. Enhance College Scorecard collector for full dataset
2. Implement IPEDS complete data download
3. Set up Cloudflare R2 integration
4. Create ChromaDB collections for each data type

### Phase 2 (Week 2)
1. Implement CDS scraper and PDF parser
2. Build rankings data aggregator
3. Create data validation pipeline
4. Generate initial training datasets

### Phase 3 (Week 3)
1. Add student review collectors
2. Implement essay database integration
3. Build data enrichment pipeline
4. Create fine-tuning dataset compiler

### Phase 4 (Week 4)
1. Outcomes data integration
2. Financial aid data aggregator
3. Final data quality validation
4. Export datasets for Ollama fine-tuning

## Success Metrics

1. **Coverage:** >90% of top 500 universities
2. **Completeness:** >85% field coverage per institution
3. **Freshness:** >80% data from last 2 years
4. **Quality Score:** >0.9 on validation metrics
5. **Volume:** >50,000 training examples for fine-tuning

## Ethical Considerations

1. Respect robots.txt and rate limits
2. Attribute data sources appropriately
3. Anonymize student data where applicable
4. Comply with FERPA and data privacy regulations
5. Use data only for educational AI purposes

