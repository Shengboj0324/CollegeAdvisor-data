# 📊 COMPREHENSIVE UNIVERSITY DATA MAPPING

**Date:** 2025-10-20  
**Purpose:** Complete mapping of all university data sources in R2 bucket  
**Based on:** comprehensive_university_data_fixed.csv analysis

---

## 📁 DATA SOURCES INVENTORY

### **1. Common Data Set PDFs (106 files, ~141 MB)**
**Location:** `finetune_data/common_data_sets/`

**Coverage:** 95 universities with CDS PDFs
**Data Points Extracted:**
- Acceptance rate
- ACT scores (25th/75th percentile): Composite, English, Math
- SAT scores (25th/75th percentile): Composite, EBRW, Math
- Admits total
- Applications total
- Enrolled total
- City, State, ZIP code
- Tuition & fees
- Yield rate
- Institution name
- Source filename
- Extraction timestamp

**Universities Included:**
1. Columbia College and Columbia Engineering
2. MIT
3. ASU Campus Immersion
4. American University
5. Boston University (BU)
6. Baylor University
7. Binghamton University SUNY
8. Boston College
9. Brandeis University
10. Brigham Young University
11. Brown University
12. University of Michigan Ann Arbor
13. Princeton University
14. Carnegie Mellon University (CMU)
15. California Institute of Technology (Caltech)
16. Case Western Reserve University
17. Chapman University
18. Clemson University
19. Colorado School of Mines
20. Cornell University
21. Dartmouth College
22. Drexel University
23. Florida International University
24. George Washington University
25. Georgetown University
26. Georgia Institute of Technology
27. Gonzaga University
28. Harvard University
29. Howard University
30. Lehigh University
31. Loyola Marymount University
32. Marquette University
33. Michigan State University
34. Rutgers University New Brunswick
35. New York University (NYU)
36. North Carolina State University
37. Northwestern University
38. Pepperdine University
39. Purdue University
40. Rensselaer Polytechnic Institute (RPI)
41. Rice University
42. Rutgers University Newark
43. Santa Clara University
44. Stevens Institute of Technology
45. Stony Brook University SUNY
46. Temple University
47. Texas A&M University
48. The Ohio State University
49. Penn State University Park
50. University of Oklahoma
51. University of Texas Austin
52. University of Texas Dallas
53. Tufts University
54. Tulane University
55. UC Berkeley
56. UCLA
57. University of Pennsylvania (UPenn)
58. University of Chicago
59. University at Buffalo SUNY
60. UC Davis
61. UC Irvine
62. UC Riverside
63. UC San Diego
64. UC Santa Barbara
65. UC Santa Cruz
66. University of Connecticut
67. University of Delaware
68. University of Florida
69. University of Georgia
70. University of Iowa
71. University of Massachusetts Amherst
72. University of Miami
73. University of Minnesota Twin Cities
74. UNC Chapel Hill
75. University of Notre Dame
76. University of Oregon
77. University of Pittsburgh
78. University of Rochester
79. University of San Diego
80. University of San Francisco
81. University of South Florida
82. University of Southern California (USC)
83. University of Tennessee Knoxville
84. University of Virginia
85. University of Washington
86. University of Wisconsin Madison
87. Villanova University
88. Wake Forest University
89. Washington University in St. Louis
90. Worcester Polytechnic Institute (WPI)
91. Yeshiva University
92. Emory University
93. Stanford University
94. Yale University
95. UC Merced (XLSX)
96. University of Illinois Urbana-Champaign (XLSX)
97. New Jersey Institute of Technology (XLSX)
98. Virginia Tech (XLSX)
99. William & Mary (XLSX)

**Additional Files:**
- CDS-2024-25-Final.xlsx (consolidated data)
- cds_master_53_schools.csv
- cds_master_53_schools_filled_batch2.csv
- Data_Issues_in_University_Dataset.csv

---

### **2. Multi-Source Processed Data (6 files, ~8 MB)**
**Location:** `multi_source/`

**Files:**
1. **master_dataset.json** (3.92 MB)
   - Comprehensive processed data from all sources
   - Merged College Scorecard + IPEDS + Carnegie + CDS data

2. **expansion_report.txt** (metadata)
   - Data expansion and processing report

3. **Training Datasets:**
   - `training_datasets/instruction_dataset.jsonl` (1.64 MB)
   - `training_datasets/instruction_dataset_alpaca.json` (1.35 MB) - **7,888 examples**
   - `training_datasets/instruction_dataset_ollama.txt` (1.07 MB)
   - `training_datasets/Modelfile` (Ollama configuration)

---

### **3. Real Data (Verified Authentic) (7 files, ~13 MB)**
**Location:** `real_data/`

**Files:**
1. **raw_real_data.json** (7.26 MB)
   - Raw authentic data from official sources
   - College Scorecard API data
   - IPEDS data
   - Carnegie Classification data

2. **processed_real_data.json** (3.92 MB)
   - Cleaned and processed real data
   - Merged from multiple authentic sources

3. **Training Datasets:**
   - `training_datasets/instruction_dataset.jsonl` (1.64 MB)
   - `training_datasets/instruction_dataset_alpaca.json` (1.35 MB)
   - `training_datasets/instruction_dataset_ollama.txt` (1.07 MB)
   - `training_datasets/Modelfile`

---

### **4. Source Data - Carnegie Classification (2 files, ~4 MB)**
**Location:** `source_data/carnegie/`

**Files:**
1. **2025-Public-Data-File.xlsx** (2.19 MB)
   - Latest Carnegie Classification data (2025)
   - Institution classifications
   - Research activity levels
   - Enrollment profiles

2. **CCIHE2021-PublicData.xlsx** (1.71 MB)
   - 2021 Carnegie Classification data
   - Historical comparison data

**Data Points:**
- Basic Classification
- Undergraduate Profile
- Graduate Profile
- Enrollment Profile
- Undergraduate Instructional Program
- Graduate Instructional Program
- Size and Setting

---

### **5. Source Data - IPEDS (3 files, ~219 MB)**
**Location:** `source_data/ipeds/`

**Files:**
1. **IPEDS_2020-21_Final.zip** (73.32 MB)
2. **IPEDS_2021-22_Final.zip** (70.32 MB)
3. **IPEDS_2022-23_Final.zip** (75.24 MB)

**Data Categories:**
- Institutional Characteristics
- Completions (degrees awarded)
- 12-month Enrollment
- Student Financial Aid
- Graduation Rates
- Admissions
- Outcome Measures
- Student Charges (tuition/fees)
- Fall Enrollment
- Finance
- Human Resources
- Academic Libraries

---

### **6. Source Data - College Scorecard (1 file, ~394 MB)**
**Location:** `source_data/scorecard/`

**File:**
- **College_Scorecard_Raw_Data_05192025.zip** (394.3 MB)

**Data Points (1,900+ variables):**
- Admissions data
- Student demographics
- Costs (tuition, fees, living expenses)
- Financial aid
- Completion rates
- Earnings data
- Debt data
- Repayment rates
- Program-specific data
- Field of study earnings

---

### **7. Processed Data (2 files, ~0.73 MB)**
**Location:** `processed_data/`

**Files:**
1. **institutions.json** (0.73 MB)
   - Processed institution data
   - Merged from multiple sources

2. **institutions_processed.json** (minimal)
   - Processing metadata

---

### **8. Raw Data (1 file, minimal)**
**Location:** `raw_data/`

**File:**
- **college_scorecard_complete.json** (minimal)
   - Raw College Scorecard API responses

---

### **9. Legacy Training Datasets (3 files, ~0.6 MB)**
**Location:** `training_datasets/`

**Files:**
- instruction_dataset.jsonl (0.25 MB)
- instruction_dataset_alpaca.json (0.21 MB)
- instruction_dataset_ollama.txt (0.16 MB)
- Modelfile

**Note:** These are older/smaller versions. Current production datasets are in `multi_source/training_datasets/`

---

## 📊 DATA STRUCTURE ANALYSIS

### **CSV Structure (comprehensive_university_data_fixed.csv)**

**Columns (24 total):**

1. **acceptance_rate** - Admission rate (0-1 scale)
2. **act_composite_25** - ACT composite 25th percentile
3. **act_composite_75** - ACT composite 75th percentile
4. **act_english_25** - ACT English 25th percentile
5. **act_english_75** - ACT English 75th percentile
6. **act_math_25** - ACT Math 25th percentile
7. **act_math_75** - ACT Math 75th percentile
8. **admits_total** - Total students admitted
9. **applications_total** - Total applications received
10. **city** - City location
11. **enrolled_total** - Total students enrolled
12. **extracted_at** - Timestamp of data extraction
13. **institution_name** - University name
14. **sat_composite_25** - SAT composite 25th percentile
15. **sat_composite_75** - SAT composite 75th percentile
16. **sat_ebrw_25** - SAT Evidence-Based Reading & Writing 25th percentile
17. **sat_ebrw_75** - SAT Evidence-Based Reading & Writing 75th percentile
18. **sat_math_25** - SAT Math 25th percentile
19. **sat_math_75** - SAT Math 75th percentile
20. **source_filename** - PDF filename source
21. **state** - State abbreviation
22. **tuition_fees** - Annual tuition and fees
23. **yield_rate** - Enrollment yield rate (0-1 scale)
24. **zip_code** - ZIP code

**Data Quality Issues Noted:**
- Many missing values (empty cells)
- Some institutions have 0.0 acceptance rates (data extraction errors)
- Inconsistent institution naming
- Some city/state/zip data missing
- Some tuition data missing

---

## 🎯 COMPREHENSIVE DATA MAPPING STRUCTURE

### **Proposed Excel Structure:**

**Sheet 1: University Overview**
- Institution ID (unique)
- Institution Name (standardized)
- City
- State
- ZIP Code
- Website
- Type (Public/Private)
- Carnegie Classification
- Data Sources Available (checkboxes)

**Sheet 2: Admissions Data**
- Institution ID
- Acceptance Rate
- Applications Total
- Admits Total
- Enrolled Total
- Yield Rate
- SAT Composite 25th/75th
- SAT EBRW 25th/75th
- SAT Math 25th/75th
- ACT Composite 25th/75th
- ACT English 25th/75th
- ACT Math 25th/75th
- Data Year
- Source

**Sheet 3: Costs & Financial Aid**
- Institution ID
- Tuition & Fees (In-State)
- Tuition & Fees (Out-of-State)
- Room & Board
- Books & Supplies
- Total Cost of Attendance
- Average Net Price
- % Receiving Financial Aid
- Average Grant Aid
- Average Loan Amount
- Data Year
- Source

**Sheet 4: Enrollment & Demographics**
- Institution ID
- Total Enrollment
- Undergraduate Enrollment
- Graduate Enrollment
- Full-Time Enrollment
- Part-Time Enrollment
- % Female
- % Male
- % White
- % Black/African American
- % Hispanic/Latino
- % Asian
- % International
- Data Year
- Source

**Sheet 5: Academic Programs**
- Institution ID
- Total Degrees Offered
- Most Popular Majors (top 10)
- STEM Programs Count
- Business Programs Count
- Liberal Arts Programs Count
- Professional Programs Count
- Data Year
- Source

**Sheet 6: Outcomes**
- Institution ID
- 4-Year Graduation Rate
- 6-Year Graduation Rate
- Retention Rate (1st to 2nd year)
- Median Earnings (10 years after entry)
- Employment Rate
- Graduate School Enrollment Rate
- Loan Default Rate
- Loan Repayment Rate
- Data Year
- Source

**Sheet 7: Faculty & Resources**
- Institution ID
- Student-to-Faculty Ratio
- % Faculty Full-Time
- % Faculty with Terminal Degree
- Average Class Size
- Library Holdings
- Research Expenditures
- Endowment Size
- Data Year
- Source

**Sheet 8: CDS PDF Mapping**
- Institution ID
- Institution Name
- PDF Filename
- PDF Location in R2
- Extraction Date
- Data Completeness Score
- Notes

**Sheet 9: Data Sources Reference**
- Source ID
- Source Name
- Source Type (API/File/PDF)
- Location in R2
- File Size
- Last Updated
- Coverage (# of institutions)
- Data Points Available
- Quality Rating

**Sheet 10: Data Quality Issues**
- Institution ID
- Field Name
- Issue Type (Missing/Invalid/Inconsistent)
- Current Value
- Expected Value
- Priority (High/Medium/Low)
- Status (Open/In Progress/Resolved)
- Notes

---

## 📈 STATISTICS

**Total Data Volume:** ~641.65 MB

**Breakdown:**
- College Scorecard: 394.3 MB (61.4%)
- IPEDS (3 years): 218.88 MB (34.1%)
- CDS PDFs: ~141 MB (2.2%)
- Processed/Training Data: ~15 MB (2.3%)

**Universities Covered:**
- CDS PDFs: 99 universities
- College Scorecard: ~7,000+ institutions
- IPEDS: ~6,500+ institutions
- Carnegie: ~4,000+ institutions

**Training Data:**
- 7,888 instruction-response pairs (Alpaca format)
- Covers admission rates, tuition, locations, programs, demographics

---

## 🔄 DATA FLOW

```
Source Data (Raw)
├── College Scorecard API → raw_real_data.json
├── IPEDS ZIP files → extracted tables
├── Carnegie XLSX → classification data
└── CDS PDFs → extracted fields

↓ Processing

Processed Data
├── master_dataset.json (merged all sources)
├── processed_real_data.json (cleaned)
└── institutions.json (structured)

↓ Training Data Generation

Training Datasets
├── instruction_dataset_alpaca.json (7,888 examples)
├── instruction_dataset.jsonl (JSONL format)
└── instruction_dataset_ollama.txt (Ollama format)
```

---

**This mapping will be converted to Excel format with all sheets and data properly structured.**

