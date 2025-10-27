# 🎯 Data Acquisition Roadmap - CollegeAdvisor AI Model

**Purpose:** Eliminate fabrication and pass every high-complexity stress test  
**Strategy:** Feed authoritative, structured, dated, and cited policy/rule data  
**Goal:** Transform from 4.4/10 to 9+/10 on research-heavy queries

---

## 🚨 **ROOT CAUSE OF FAILURES**

The gap isn't "more data," it's **the right data in structured, source-anchored form with refresh SLAs**.

**Current Failures:**
- ❌ Zero actual URLs provided
- ❌ Fabricated numbers (SAI, selectivity rates, TCO)
- ❌ Missing current 2025 policies
- ❌ No structured output (tables, decision trees, Gantt charts)
- ❌ Generic advice without institutional specifics

**Solution:** Structured, cited, versioned data with refresh cadences

---

## 📊 **DATA TIERS & PRIORITY**

### **Tier 0: MUST-HAVE (Eliminates Fabrication)**
1. Policy & Rules (FAFSA, CSS, Transfer, Immigration, NCAA)
2. Anti-Hallucination & Citation Training Data
3. Computation Packs (SAI calculator, budget calculators)

### **Tier 1: HIGH-VALUE (Grounds Recommendations)**
1. Costs & Net Price (NPC snapshots, COA, off-campus TCO)
2. Admissions Selectivity & Outcomes (CDS, program outcomes)
3. Transfer & Articulation (ASSIST, course mappings)

### **Tier 2: NICE-TO-HAVE (Enhances Coverage)**
1. International Aid & Need Awareness
2. Deadlines & Deliverables

---

## 🎯 **PHASE 1: BUILD FIRST (IMMEDIATE PRIORITY)**

### **1. Aid Core** 🔴 CRITICAL
**Goal:** Replace fabricated SAI/NPC numbers with audited data

**Deliverables:**
- [ ] FAFSA/SAI spec pack (2024-2026)
  - Official definitions, tables, asset protections
  - Small-business treatment, multi-student adjustments
  - Edge cases (UTMA/529/grandparent 529)
  - **Target:** 50 worked examples with inputs/outputs
  
- [ ] CSS Profile institutional policies (50 schools)
  - Home equity treatment
  - Business equity treatment
  - NCP waiver policies
  - Outside scholarship stacking
  - Professional judgment criteria
  - **Target:** 50 schools × 5 policies = 250 policy records

- [ ] NPC snapshots (200 scenarios across 40 schools)
  - 6-8 canonical family profiles per school
  - AGI bands: $50k, $80k, $120k, $165k, $200k, $250k
  - Asset variations: business equity, UTMA, 529, rental property
  - **Target:** 40 schools × 5 scenarios = 200 NPC results

**Schema:**
```jsonl
// AidRule.jsonl
{"source_url":"https://studentaid.gov/...","effective_start":"2024-07-01","effective_end":null,"variable":"SAI","definition":"...","formula_tex":"...","worked_examples":[{"inputs":{"agi":165000,"assets":{"parent_401k":110000,"utma":70000,"529_gp":35000},"household":5,"students_in_college":3},"outputs":{"sai":42000},"notes":"..."}]}

// InstitutionAidPolicy.jsonl
{"school_id":"uiuc","policy_topic":"home_equity","rule":"ignored up to X; capped Y","citations":["https://..."],"exceptions":"...","last_verified":"2025-10-26"}
{"school_id":"rice","policy_topic":"ncp_waiver","rule":"case-by-case with documentation","citations":["https://..."],"last_verified":"2025-10-26"}

// NPCResult.jsonl
{"school_id":"cmu","scenario_id":"AGI165k_Scorp_UTMA_529gp","inputs":{"agi":165000,"assets":{"parent_401k":110000,"utma":70000,"529_gp":35000},"household":5,"students_in_college":3},"outputs":{"grant":35000,"scholarship":5000,"loan":5500,"work":2500,"net_price":22000},"run_date":"2025-10-26","url":"https://cmu.edu/npc"}
```

**Refresh Cadence:** Quarterly + on federal updates

---

### **2. CS/Engineering Gates** 🔴 CRITICAL
**Goal:** Eliminate fabricated prerequisites and GPA cutoffs

**Deliverables:**
- [ ] 50 high-demand programs with internal transfer policies
  - Direct admit vs pre-major paths
  - GPA gates and weed-out courses
  - Time-to-major risk assessment
  - Historical selectivity data
  
**Target Schools:**
- UIUC (CS, CS+X)
- Georgia Tech (CS)
- UW (CSE direct-to-major)
- UCSD (CSE/DS25)
- UCI (CS/DS)
- Purdue (CS)
- UT Austin (CS)
- UCLA (CS, ECE)
- Berkeley (EECS, CS)
- Michigan (CS, CE)
- CMU (SCS)
- Cornell (CS)
- + 38 more

**Schema:**
```jsonl
// MajorGate.jsonl
{"school_id":"uw","major_cip":"11.0701","major_name":"Computer Science","path":"direct","gates":[{"metric":"prereq_gpa","threshold":"3.8","courses":["CSE 142","CSE 143"],"min_grade":"3.0"}],"historical_selectivity":{"admit_rate":0.05,"avg_gpa":3.92},"time_to_degree_risk":"high","citations":["https://www.cs.washington.edu/academics/ugrad/admissions"],"last_verified":"2025-10-26"}
{"school_id":"ucsd","major_cip":"11.0701","major_name":"Computer Science","path":"pre-major","gates":[{"metric":"screening_gpa","threshold":"3.3","courses":["CSE 8A","CSE 8B","CSE 11","CSE 12","CSE 15L","CSE 20","CSE 21"],"min_grade":"C"}],"historical_selectivity":{"admit_rate":0.15,"avg_gpa":3.65},"time_to_degree_risk":"medium","citations":["https://cse.ucsd.edu/undergraduate/admissions-current-ucsd-students"],"last_verified":"2025-10-26"}
```

**Refresh Cadence:** Termly (Fall, Winter, Spring)

---

### **3. ASSIST Sequences** 🔴 CRITICAL
**Goal:** Provide exact course plans instead of platitudes

**Deliverables:**
- [ ] Full 4-term transfer plans for target programs
  - UCSB ME
  - UCLA ECE
  - UCSD CSE
  - Cal Poly SLO ME
  - + 20 more high-demand programs

**Schema:**
```jsonl
// Articulation.jsonl
{"cc_id":"deanza","target_school_id":"ucsb","target_major":"Mechanical Engineering","target_major_cip":"14.1901","seq":[{"term":1,"courses":[{"course_cc":"MATH 1A","course_target":"MATH 3A","min_grade":"C","units":5},{"course_cc":"CHEM 1A","course_target":"CHEM 1A","min_grade":"C","units":5},{"course_cc":"ENGR 10","course_target":"ENGR 3","min_grade":"C","units":4}]},{"term":2,"courses":[{"course_cc":"MATH 1B","course_target":"MATH 3B","min_grade":"C","units":5},{"course_cc":"PHYS 4A","course_target":"PHYS 1","min_grade":"C","units":5},{"course_cc":"EWRT 1A","course_target":"Writing","min_grade":"C","units":5}]},{"term":3,"courses":[{"course_cc":"MATH 1C","course_target":"MATH 4A","min_grade":"C","units":5},{"course_cc":"PHYS 4B","course_target":"PHYS 2","min_grade":"C","units":5},{"course_cc":"ENGR 36","course_target":"ME 14","min_grade":"C","units":4}]},{"term":4,"courses":[{"course_cc":"MATH 2A","course_target":"MATH 4B","min_grade":"C","units":5},{"course_cc":"PHYS 4C","course_target":"PHYS 3","min_grade":"C","units":5},{"course_cc":"ENGR 45","course_target":"ME 15","min_grade":"C","units":4}]}],"gpa_floor":3.2,"tag_eligible":false,"notes":"ME is not TAG-eligible; highly competitive","citations":["https://assist.org"],"last_verified":"2025-10-26"}
```

**Refresh Cadence:** Termly

---

### **4. Residency/WUE Matrix** 🟡 HIGH PRIORITY
**Goal:** Ground cost optimization with actual eligibility rules

**Deliverables:**
- [ ] UC/CSU residency rules
  - Physical presence requirements
  - Financial independence tests
  - Dependent criteria
  - Leave-of-absence traps
  
- [ ] WUE eligibility by major (top 30 WUE schools)
  - Which majors actually qualify
  - CS/CE exclusions (common)
  - Seat caps

**Schema:**
```jsonl
// ResidencyRule.jsonl
{"system":"UC","rule_name":"physical_presence","rule_text":"Must be physically present in California for 366 days prior to residence determination date","proofs":["CA driver's license","voter registration","tax returns"],"exceptions":["Active military","certain visa holders"],"examples":[{"scenario":"Student moves to CA in June 2024 for fall 2025","result":"Not eligible until fall 2026"}],"citations":["https://www.ucop.edu/residency/"],"last_verified":"2025-10-26"}

// WUEProgram.jsonl
{"school_id":"asu","major_cip":"11.0701","major_name":"Computer Science","eligible":false,"conditions":"CS excluded from WUE due to high demand","seats_cap":null,"notes":"Apply for merit scholarships instead","citations":["https://students.asu.edu/wue"],"last_verified":"2025-10-26"}
{"school_id":"unr","major_cip":"14.0801","major_name":"Civil Engineering","eligible":true,"conditions":"Must maintain 3.0 GPA","seats_cap":50,"notes":"Limited seats; apply early","citations":["https://www.unr.edu/wue"],"last_verified":"2025-10-26"}
```

**Refresh Cadence:** Annual

---

### **5. Citation Corpus** 🔴 CRITICAL
**Goal:** Force model to anchor claims or abstain

**Deliverables:**
- [ ] 250 "cite-or-abstain" exemplars with validators
  - Prompts requiring URLs to official pages
  - Gold answers with explicit links + last_verified
  - Math steps where applicable
  
- [ ] 50 "unanswerable/insufficient-data" exemplars
  - Model learns to say "cannot verify; here's the retrieval plan"
  
- [ ] 100 structured-output exemplars
  - Tables (side-by-side comparisons)
  - Decision trees (cost optimization, school selection)
  - Gantt charts (application timelines)
  - With validators (e.g., rows=schools provided, all required fields present)

**Schema:**
```jsonl
// CitedAnswer.jsonl
{"prompt":"What is MIT's CSS Profile treatment of home equity for families with AGI over $200k?","answer_md":"MIT caps home equity at 1.2x annual income for families with AGI over $200k. For a family with $250k AGI and $500k home equity, only $300k (1.2 × $250k) would be assessed.\n\n**Source:** [MIT Student Financial Services - Home Equity Policy](https://sfs.mit.edu/undergraduate-students/the-cost-of-attendance/outside-awards-and-additional-funding/home-equity-policy/)\n\n**Last Verified:** 2025-10-26","required_citations":[{"url":"https://sfs.mit.edu/undergraduate-students/the-cost-of-attendance/outside-awards-and-additional-funding/home-equity-policy/","title":"MIT Home Equity Policy"}],"last_verified":"2025-10-26"}

// UnanswerableExample.jsonl
{"prompt":"What is the internal transfer GPA cutoff for CS at University of XYZ?","answer_md":"I cannot verify the current internal transfer GPA cutoff for Computer Science at University of XYZ. This information is not available in my training data.\n\n**Recommended retrieval plan:**\n1. Visit the CS department website: [university-xyz.edu/cs/admissions]\n2. Contact the CS undergraduate advisor directly\n3. Check the university's internal transfer policy page\n4. Review recent Reddit/College Confidential threads for anecdotal data points\n\n**Note:** Internal transfer policies change frequently and may not be publicly published. Always verify with the department.","required_citations":[],"last_verified":"2025-10-26"}

// StructuredOutputExample.jsonl
{"prompt":"Compare FAFSA-only vs CSS Profile schools for a family with $165k AGI, $110k in 401k, $70k UTMA, divorced parents.","answer_md":"| School | Type | SAI/EFC | Home Equity | Business Equity | UTMA | NCP Required | Est. Net Price |\n|--------|------|---------|-------------|-----------------|------|--------------|----------------|\n| UMass Amherst | FAFSA | $42,000 | Ignored | Ignored | Counted | No | $28,000 |\n| MIT | CSS | $38,000 | Capped 1.2x | Capped | Counted | Yes | $15,000 |\n| Harvard | CSS | $35,000 | Ignored <$200k AGI | Ignored <100 emp | Counted | Yes | $12,000 |\n\n**Sources:**\n- [UMass Amherst NPC](https://www.umass.edu/umfa/net-price-calculator)\n- [MIT Financial Aid](https://sfs.mit.edu)\n- [Harvard Financial Aid](https://college.harvard.edu/financial-aid)\n\n**Last Verified:** 2025-10-26","validator":{"type":"table","required_columns":["School","Type","SAI/EFC","Est. Net Price"],"min_rows":3},"last_verified":"2025-10-26"}
```

**Refresh Cadence:** Quarterly

---

## 📊 **PHASE 2: EXPAND COVERAGE**

### **6. Costs & Net Price** 🟡 HIGH PRIORITY

**Deliverables:**
- [ ] COA deltas (100 schools)
  - Tuition/fees breakdown
  - Health insurance (waivable vs mandatory)
  - Mandatory fees (technology, recreation, etc.)
  - Fine print (course fees, lab fees, parking)

- [ ] Off-campus TCO (50 urban campuses)
  - Median rents (studio, 1BR, 2BR share)
  - Utilities (electric, gas, water, internet)
  - Transit pass (monthly/annual)
  - Taxes (if applicable)
  - 12-month budget (not just 9-month COA)

**Schema:**
```jsonl
// COAItem.jsonl
{"school_id":"nyu","item":"tuition","amount":60438,"term":"2025-26","notes":"Does not include course fees","url":"https://www.nyu.edu/students/student-information-and-resources/bills-payments-and-refunds/tuition-and-fees.html","last_verified":"2025-10-26"}
{"school_id":"nyu","item":"health_insurance","amount":4710,"term":"2025-26","notes":"Waivable with proof of comparable coverage","url":"https://www.nyu.edu/students/health-and-wellness/student-health-center/insurance.html","last_verified":"2025-10-26"}

// CityCost.jsonl
{"campus_id":"nyu_washington_square","housing_type":"studio","monthly_cost":2800,"data_source":"Zillow median rent, Greenwich Village","observed_date":"2025-10-26","url":"https://www.zillow.com/greenwich-village-new-york-ny/"}
{"campus_id":"nyu_washington_square","housing_type":"2BR_share","monthly_cost":1600,"data_source":"Zillow median rent, Greenwich Village, divided by 2","observed_date":"2025-10-26","url":"https://www.zillow.com/greenwich-village-new-york-ny/"}
```

**Refresh Cadence:** Quarterly

---

### **7. Admissions Selectivity & Outcomes** 🟡 HIGH PRIORITY

**Deliverables:**
- [ ] Common Data Set extraction (100 schools)
  - Overall admit rate
  - Program/college-level admit (if available)
  - Yield
  - % need met
  - Nonresident aid availability
  - Testing policy

- [ ] Program outcomes (50 programs)
  - Employment rate at 6 months
  - Median starting compensation
  - Co-op participation (Waterloo, Northeastern, Drexel, etc.)
  - Time-to-job

**Schema:**
```jsonl
// CDSExtract.jsonl
{"school_id":"mit","year":2024,"metric":"overall_admit_rate","value":0.039,"section_ref":"C1","url":"https://ir.mit.edu/cds","last_verified":"2025-10-26"}
{"school_id":"mit","metric":"percent_need_met_avg","value":1.00,"section_ref":"H2","url":"https://ir.mit.edu/cds","last_verified":"2025-10-26"}

// OutcomeStat.jsonl
{"school_id":"waterloo","program":"Computer Science","stat":"employment_rate_6mo","value":0.98,"cohort_year":2024,"url":"https://uwaterloo.ca/co-operative-education/why-co-op/co-op-earnings/hourly-earnings-information-jan-dec-2024","last_verified":"2025-10-26"}
{"school_id":"northeastern","program":"Computer Science","stat":"median_starting_comp","value":95000,"cohort_year":2024,"url":"https://careers.northeastern.edu/outcomes/","last_verified":"2025-10-26"}
```

**Refresh Cadence:** Annual

---

### **8. Immigration Policies** 🟡 HIGH PRIORITY

**Deliverables:**
- [ ] F-1/CPT/OPT/STEM OPT rules
  - Durations (12 months OPT, 24 months STEM OPT)
  - Hours (20 hrs/week during term, 40 hrs/week during breaks)
  - Employer/role constraints
  - Grace periods (60 days post-completion)
  - School-level DSO nuances

**Schema:**
```jsonl
// ImmigrationPolicy.jsonl
{"policy_area":"OPT","clause":"duration","requirement":"12 months for standard OPT, 24 months extension for STEM-designated degrees","examples":["CS degree (CIP 11.0701) qualifies for STEM OPT"],"risk_flags":["Must apply 90 days before completion, no later than 60 days after"],"citations":["https://www.ice.gov/sevis/opt"],"last_verified":"2025-10-26"}
{"policy_area":"CPT","clause":"work_hours","requirement":"Part-time CPT: ≤20 hrs/week during term; Full-time CPT: >20 hrs/week (only during breaks unless program requires)","examples":["Co-op programs typically use full-time CPT"],"risk_flags":["12+ months full-time CPT makes you ineligible for OPT"],"citations":["https://www.ice.gov/sevis/practical-training"],"last_verified":"2025-10-26"}
```

**Refresh Cadence:** Quarterly

---

### **9. NCAA/Recruiting Rules** 🟢 MEDIUM PRIORITY

**Deliverables:**
- [ ] NCAA Division I/II/III rules
  - Official vs Unofficial visits
  - Likely Letters (Ivy)
  - NIL constraints for HS prospects
  - Amateurism rules
  - Conference-level quirks (Ivy, Patriot no athletic scholarships)

**Schema:**
```jsonl
// NCAAReg.jsonl
{"division":"I","topic":"recruiting_visits","rule_id":"13.6.7.1","summary":"Prospective student-athlete may take a maximum of five expense-paid visits","exceptions":["Graduate transfers may take unlimited official visits"],"citations":["https://web3.ncaa.org/lsdbi/search/proposalView?id=105852"],"last_verified":"2025-10-26"}
{"division":"I","conference":"Ivy","topic":"athletic_scholarships","rule_id":"Ivy_Agreement","summary":"Ivy League schools do not offer athletic scholarships; all aid is need-based","exceptions":[],"citations":["https://ivyleague.com/sports/2021/6/10/information-psa-index"],"last_verified":"2025-10-26"}
```

**Refresh Cadence:** Annual + mid-year bulletins

---

## 🔄 **DATA GOVERNANCE & REFRESH SLAs**

### **Metadata Requirements**
Every document chunk MUST carry:
```json
{
  "source_url": "https://...",
  "page_title": "...",
  "retrieved_at": "2025-10-26T12:00:00Z",
  "effective_start": "2024-07-01",
  "effective_end": null,
  "jurisdiction": "federal|state|institutional",
  "school_id": "mit",
  "last_verified": "2025-10-26"
}
```

### **Recency Ranking**
- Prefer `effective_end` is `null` OR `retrieved_at` ≤ 120 days for volatile domains
- Flag stale data (>120 days) with warnings

### **Versioning**
- Keep snapshots; never overwrite
- Allow longitudinal comparisons (e.g., "MIT's aid policy changed in 2024 from X to Y")

---

## 🛠️ **ACQUISITION TACTICS**

### **1. Prioritize Official Sources**
- Federal: StudentAid.gov, USCIS, ICE, NCAA
- State: UCOP, CSU, ASSIST.org, WICHE
- Institutional: School financial aid pages, department pages, Common Data Sets

### **2. Respect robots.txt and TOS**
- If scraping, check robots.txt
- Prefer downloadable PDFs/CSVs for stability
- Use official APIs where available

### **3. Normalize IDs**
- `school_id`: IPEDS unit ID (6-digit)
- `program`: CIP codes (6-digit)
- `major_slug`: Internal slug for joins

### **4. ETL Pipeline**
```
HTML → Markdown → Chunk (1-2k tokens) + Metadata
     ↓
Extract tables to CSV alongside raw text
     ↓
Validate schema + required fields
     ↓
Load to training corpus with versioning
```

---

## 📁 **DIRECTORY STRUCTURE**

```
CollegeAdvisor-data/
├── training_data/
│   ├── tier0_policy_rules/
│   │   ├── AidRule.jsonl
│   │   ├── InstitutionAidPolicy.jsonl
│   │   ├── MajorGate.jsonl
│   │   ├── ResidencyRule.jsonl
│   │   ├── WUEProgram.jsonl
│   │   ├── ImmigrationPolicy.jsonl
│   │   └── NCAAReg.jsonl
│   ├── tier0_citation_training/
│   │   ├── CitedAnswer.jsonl
│   │   ├── UnanswerableExample.jsonl
│   │   └── StructuredOutputExample.jsonl
│   ├── tier0_computation/
│   │   ├── SAICalculatorTestVectors.jsonl
│   │   └── HousingBudgetCalculator.jsonl
│   ├── tier1_costs/
│   │   ├── NPCResult.jsonl
│   │   ├── COAItem.jsonl
│   │   └── CityCost.jsonl
│   ├── tier1_admissions/
│   │   ├── CDSExtract.jsonl
│   │   └── OutcomeStat.jsonl
│   ├── tier1_transfer/
│   │   └── Articulation.jsonl
│   └── tier2_international/
│       ├── IntlAidMatrix.jsonl
│       └── Deadline.jsonl
├── scripts/
│   ├── scrapers/
│   │   ├── scrape_npc.py
│   │   ├── scrape_cds.py
│   │   ├── scrape_assist.py
│   │   └── scrape_aid_policies.py
│   ├── validators/
│   │   ├── validate_schema.py
│   │   └── check_freshness.py
│   └── etl/
│       ├── html_to_markdown.py
│       ├── extract_tables.py
│       └── chunk_and_metadata.py
└── docs/
    ├── DATA_ACQUISITION_ROADMAP.md (this file)
    └── SCHEMA_REFERENCE.md
```

---

## 🎯 **SUCCESS METRICS**

### **Phase 1 Complete When:**
- [ ] 50 worked SAI examples with inputs/outputs
- [ ] 250 CSS Profile policy records (50 schools × 5 policies)
- [ ] 200 NPC results (40 schools × 5 scenarios)
- [ ] 50 CS/Engineering gate records with citations
- [ ] 24 ASSIST transfer sequences (4 programs × 6 CCs)
- [ ] 30 WUE eligibility records
- [ ] 250 cite-or-abstain exemplars
- [ ] 50 unanswerable exemplars
- [ ] 100 structured-output exemplars

### **Re-test High-Complexity Queries:**
Run the same 10 stress tests and target:
- **Source Citations:** 8+/10 responses with actual URLs
- **Quantitative Data:** 9+/10 responses with precise, sourced numbers
- **Policy Specificity:** 8+/10 responses with current policy details
- **Structured Output:** 8+/10 responses with tables/trees/charts
- **Overall Quality:** 8.5+/10 average (up from 4.4/10)

---

## 🚀 **NEXT STEPS**

1. **Create schema files** (copy examples above to `.jsonl` files)
2. **Build scrapers** for Phase 1 data sources
3. **Validate & load** first 100 records per schema
4. **Re-train model** with new data
5. **Re-run stress tests** and measure improvement
6. **Iterate** based on remaining gaps

---

## 📞 **QUESTIONS TO RESOLVE**

1. **Training format:** Do you want JSONL for fine-tuning or Markdown for RAG?
2. **Refresh automation:** Should we build automated scrapers with scheduling?
3. **Validation:** Do you want schema validators before loading?
4. **Versioning:** Git-based or database-based versioning?

---

**This roadmap will transform your model from 4.4/10 to 9+/10 on high-complexity queries by eliminating fabrication and grounding every claim in authoritative, cited, versioned data.** 🎯

