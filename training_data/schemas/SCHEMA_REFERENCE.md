# 📋 Schema Reference - CollegeAdvisor Training Data

**Purpose:** Standardized schemas for all training data to ensure consistency, citability, and freshness

---

## 🎯 **CORE PRINCIPLES**

1. **Every record MUST have metadata:** source_url, retrieved_at, last_verified
2. **Use standard IDs:** IPEDS for schools, CIP codes for programs
3. **Version everything:** Never overwrite; keep snapshots
4. **Cite everything:** No claims without citations
5. **Date everything:** effective_start, effective_end for time-bound policies

---

## 📊 **TIER 0: POLICY & RULES**

### **AidRule.jsonl**
Financial aid policy rules (FAFSA, SAI, CSS Profile)

```json
{
  "source_url": "https://studentaid.gov/help-center/answers/article/what-is-sai",
  "effective_start": "2024-07-01",
  "effective_end": null,
  "variable": "SAI",
  "definition": "Student Aid Index (SAI) is a number calculated by the FAFSA that colleges use to determine how much financial aid you're eligible to receive.",
  "formula_tex": "SAI = Parent\\_Contribution + Student\\_Contribution - Allowances",
  "worked_examples": [
    {
      "inputs": {
        "agi": 165000,
        "assets": {
          "parent_401k": 110000,
          "utma": 70000,
          "529_gp": 35000
        },
        "household": 5,
        "students_in_college": 3
      },
      "outputs": {
        "sai": 42000,
        "parent_contribution": 38000,
        "student_contribution": 14000,
        "allowances": 10000
      },
      "notes": "401k not counted; UTMA counted at 20%; grandparent 529 not counted on FAFSA (but may be on CSS)"
    }
  ],
  "retrieved_at": "2025-10-26T12:00:00Z",
  "last_verified": "2025-10-26"
}
```

**Required Fields:**
- `source_url` (string): Official source URL
- `effective_start` (date): When this rule became effective
- `effective_end` (date|null): When this rule expires (null if current)
- `variable` (string): What this rule defines (SAI, EFC, etc.)
- `definition` (string): Plain English definition
- `formula_tex` (string): LaTeX formula if applicable
- `worked_examples` (array): At least 1 worked example
- `retrieved_at` (datetime): When data was retrieved
- `last_verified` (date): When data was last verified

---

### **InstitutionAidPolicy.jsonl**
School-specific financial aid policies

```json
{
  "school_id": "uiuc",
  "school_name": "University of Illinois Urbana-Champaign",
  "ipeds_id": "145600",
  "policy_topic": "home_equity",
  "rule": "Home equity capped at 1.2x annual income for families with AGI < $200k; ignored for AGI < $100k",
  "citations": [
    "https://osfa.illinois.edu/aid/cost/net-price-calculator/"
  ],
  "exceptions": "Professional judgment may apply for unusual circumstances",
  "last_verified": "2025-10-26"
}
```

**Required Fields:**
- `school_id` (string): Internal school identifier
- `school_name` (string): Official school name
- `ipeds_id` (string): IPEDS unit ID (6-digit)
- `policy_topic` (enum): home_equity | business_equity | ncp_waiver | outside_scholarships | professional_judgment
- `rule` (string): Policy description
- `citations` (array): URLs to official policy pages
- `exceptions` (string): Any exceptions or edge cases
- `last_verified` (date): When policy was last verified

---

### **MajorGate.jsonl**
Internal transfer and admission gates for capacity-constrained majors

```json
{
  "school_id": "uw",
  "school_name": "University of Washington",
  "ipeds_id": "236948",
  "major_cip": "11.0701",
  "major_name": "Computer Science",
  "path": "direct",
  "gates": [
    {
      "metric": "prereq_gpa",
      "threshold": "3.8",
      "courses": ["CSE 142", "CSE 143"],
      "min_grade": "3.0"
    }
  ],
  "historical_selectivity": {
    "admit_rate": 0.05,
    "avg_gpa": 3.92,
    "year": 2024
  },
  "time_to_degree_risk": "high",
  "notes": "Direct admission to CS is highly competitive; pre-major path has ~5% internal transfer rate",
  "citations": [
    "https://www.cs.washington.edu/academics/ugrad/admissions"
  ],
  "last_verified": "2025-10-26"
}
```

**Required Fields:**
- `school_id`, `school_name`, `ipeds_id`: School identifiers
- `major_cip` (string): CIP code (6-digit)
- `major_name` (string): Official major name
- `path` (enum): direct | pre-major | transfer
- `gates` (array): Admission requirements
  - `metric` (enum): prereq_gpa | screening_gpa | application | lottery
  - `threshold` (string): Minimum requirement
  - `courses` (array): Required courses
  - `min_grade` (string): Minimum grade
- `historical_selectivity` (object): Past admission data
- `time_to_degree_risk` (enum): low | medium | high
- `citations` (array): Official sources
- `last_verified` (date)

---

### **ResidencyRule.jsonl**
State residency determination rules

```json
{
  "system": "UC",
  "rule_name": "physical_presence",
  "rule_text": "Must be physically present in California for 366 days prior to residence determination date (typically day before instruction begins)",
  "proofs": [
    "CA driver's license or ID",
    "Voter registration",
    "Tax returns showing CA residency",
    "Utility bills",
    "Lease agreement"
  ],
  "exceptions": [
    "Active military stationed in CA",
    "Certain visa holders (refugees, asylees)"
  ],
  "examples": [
    {
      "scenario": "Student moves to CA in June 2024 for fall 2025 enrollment",
      "result": "Not eligible for CA residency until fall 2026 (need 366 days)"
    }
  ],
  "citations": [
    "https://www.ucop.edu/residency/"
  ],
  "last_verified": "2025-10-26"
}
```

**Required Fields:**
- `system` (enum): UC | CSU | state_name
- `rule_name` (string): Short identifier
- `rule_text` (string): Full rule description
- `proofs` (array): Required documentation
- `exceptions` (array): Exceptions to rule
- `examples` (array): Worked examples
- `citations` (array): Official sources
- `last_verified` (date)

---

### **WUEProgram.jsonl**
Western Undergraduate Exchange program eligibility

```json
{
  "school_id": "asu",
  "school_name": "Arizona State University",
  "ipeds_id": "104151",
  "major_cip": "11.0701",
  "major_name": "Computer Science",
  "eligible": false,
  "conditions": "CS excluded from WUE due to high demand",
  "seats_cap": null,
  "tuition_rate": null,
  "notes": "Apply for merit scholarships instead; New American University Scholarship available",
  "citations": [
    "https://students.asu.edu/wue"
  ],
  "last_verified": "2025-10-26"
}
```

**Required Fields:**
- `school_id`, `school_name`, `ipeds_id`: School identifiers
- `major_cip` (string): CIP code
- `major_name` (string): Major name
- `eligible` (boolean): Whether major qualifies for WUE
- `conditions` (string): Eligibility conditions
- `seats_cap` (number|null): Seat limit if applicable
- `tuition_rate` (number|null): WUE tuition rate (typically 150% of in-state)
- `notes` (string): Additional information
- `citations` (array): Official sources
- `last_verified` (date)

---

### **ImmigrationPolicy.jsonl**
F-1 visa, CPT, OPT, STEM OPT rules

```json
{
  "policy_area": "OPT",
  "clause": "duration",
  "requirement": "12 months for standard OPT; 24 months extension for STEM-designated degrees (CIP codes listed on STEM Designated Degree Program List)",
  "examples": [
    "CS degree (CIP 11.0701) qualifies for STEM OPT extension",
    "Total possible: 12 months standard + 24 months STEM = 36 months"
  ],
  "risk_flags": [
    "Must apply 90 days before completion, no later than 60 days after",
    "Unemployment limits: 90 days total during standard OPT, 150 days during STEM OPT"
  ],
  "citations": [
    "https://www.ice.gov/sevis/opt",
    "https://www.ice.gov/doclib/sevis/pdf/stemList.pdf"
  ],
  "last_verified": "2025-10-26"
}
```

**Required Fields:**
- `policy_area` (enum): OPT | STEM_OPT | CPT | I-20 | F-1
- `clause` (string): Specific aspect of policy
- `requirement` (string): Policy requirement
- `examples` (array): Concrete examples
- `risk_flags` (array): Common pitfalls
- `citations` (array): Official USCIS/ICE sources
- `last_verified` (date)

---

### **NCAAReg.jsonl**
NCAA recruiting and eligibility rules

```json
{
  "division": "I",
  "conference": null,
  "topic": "recruiting_visits",
  "rule_id": "13.6.7.1",
  "summary": "Prospective student-athlete may take a maximum of five expense-paid (official) visits to Division I institutions",
  "exceptions": [
    "Graduate transfers may take unlimited official visits"
  ],
  "citations": [
    "https://web3.ncaa.org/lsdbi/search/proposalView?id=105852"
  ],
  "last_verified": "2025-10-26"
}
```

**Required Fields:**
- `division` (enum): I | II | III
- `conference` (string|null): Conference name if conference-specific rule
- `topic` (string): Rule category
- `rule_id` (string): Official NCAA rule number
- `summary` (string): Plain English summary
- `exceptions` (array): Exceptions to rule
- `citations` (array): NCAA manual links
- `last_verified` (date)

---

## 📊 **TIER 0: CITATION TRAINING**

### **CitedAnswer.jsonl**
Training examples with required citations

```json
{
  "prompt": "What is MIT's CSS Profile treatment of home equity for families with AGI over $200k?",
  "answer_md": "MIT caps home equity at 1.2x annual income for families with AGI over $200k. For a family with $250k AGI and $500k home equity, only $300k (1.2 × $250k) would be assessed.\n\n**Source:** [MIT Student Financial Services - Home Equity Policy](https://sfs.mit.edu/undergraduate-students/the-cost-of-attendance/outside-awards-and-additional-funding/home-equity-policy/)\n\n**Last Verified:** 2025-10-26",
  "required_citations": [
    {
      "url": "https://sfs.mit.edu/undergraduate-students/the-cost-of-attendance/outside-awards-and-additional-funding/home-equity-policy/",
      "title": "MIT Home Equity Policy"
    }
  ],
  "last_verified": "2025-10-26"
}
```

---

### **UnanswerableExample.jsonl**
Training examples for insufficient data

```json
{
  "prompt": "What is the internal transfer GPA cutoff for CS at University of XYZ?",
  "answer_md": "I cannot verify the current internal transfer GPA cutoff for Computer Science at University of XYZ. This information is not available in my training data.\n\n**Recommended retrieval plan:**\n1. Visit the CS department website: [university-xyz.edu/cs/admissions]\n2. Contact the CS undergraduate advisor directly\n3. Check the university's internal transfer policy page\n4. Review recent Reddit/College Confidential threads for anecdotal data points\n\n**Note:** Internal transfer policies change frequently and may not be publicly published. Always verify with the department.",
  "required_citations": [],
  "last_verified": "2025-10-26"
}
```

---

### **StructuredOutputExample.jsonl**
Training examples with tables, trees, charts

```json
{
  "prompt": "Compare FAFSA-only vs CSS Profile schools for a family with $165k AGI, $110k in 401k, $70k UTMA, divorced parents.",
  "answer_md": "| School | Type | SAI/EFC | Home Equity | Business Equity | UTMA | NCP Required | Est. Net Price |\n|--------|------|---------|-------------|-----------------|------|--------------|----------------|\n| UMass Amherst | FAFSA | $42,000 | Ignored | Ignored | Counted | No | $28,000 |\n| MIT | CSS | $38,000 | Capped 1.2x | Capped | Counted | Yes | $15,000 |\n| Harvard | CSS | $35,000 | Ignored <$200k AGI | Ignored <100 emp | Counted | Yes | $12,000 |\n\n**Sources:**\n- [UMass Amherst NPC](https://www.umass.edu/umfa/net-price-calculator)\n- [MIT Financial Aid](https://sfs.mit.edu)\n- [Harvard Financial Aid](https://college.harvard.edu/financial-aid)\n\n**Last Verified:** 2025-10-26",
  "validator": {
    "type": "table",
    "required_columns": ["School", "Type", "SAI/EFC", "Est. Net Price"],
    "min_rows": 3
  },
  "last_verified": "2025-10-26"
}
```

---

## 📊 **TIER 1: COSTS & NET PRICE**

### **NPCResult.jsonl**
Net Price Calculator results for canonical scenarios

```json
{
  "school_id": "cmu",
  "school_name": "Carnegie Mellon University",
  "ipeds_id": "211440",
  "scenario_id": "AGI165k_Scorp_UTMA_529gp",
  "inputs": {
    "agi": 165000,
    "assets": {
      "parent_401k": 110000,
      "utma": 70000,
      "529_gp": 35000,
      "business_equity": 200000,
      "home_equity": 300000
    },
    "household": 5,
    "students_in_college": 3,
    "parent_marital_status": "divorced",
    "ncp_contribution": 0
  },
  "outputs": {
    "grant": 35000,
    "scholarship": 5000,
    "loan": 5500,
    "work": 2500,
    "net_price": 22000,
    "coa": 70000
  },
  "run_date": "2025-10-26",
  "url": "https://www.cmu.edu/sfs/financial-aid/net-price-calculator/index.html",
  "notes": "Business equity capped; home equity capped at 1.2x income",
  "last_verified": "2025-10-26"
}
```

---

### **COAItem.jsonl**
Cost of Attendance line items

```json
{
  "school_id": "nyu",
  "school_name": "New York University",
  "ipeds_id": "193900",
  "item": "tuition",
  "amount": 60438,
  "term": "2025-26",
  "notes": "Does not include course fees (varies by major)",
  "url": "https://www.nyu.edu/students/student-information-and-resources/bills-payments-and-refunds/tuition-and-fees.html",
  "last_verified": "2025-10-26"
}
```

---

### **CityCost.jsonl**
Off-campus housing and living costs

```json
{
  "campus_id": "nyu_washington_square",
  "school_id": "nyu",
  "housing_type": "studio",
  "monthly_cost": 2800,
  "data_source": "Zillow median rent, Greenwich Village",
  "observed_date": "2025-10-26",
  "url": "https://www.zillow.com/greenwich-village-new-york-ny/",
  "notes": "Median for 1-bedroom studio within 1 mile of campus"
}
```

---

## 📊 **TIER 1: ADMISSIONS & OUTCOMES**

### **CDSExtract.jsonl**
Common Data Set extractions

```json
{
  "school_id": "mit",
  "school_name": "Massachusetts Institute of Technology",
  "ipeds_id": "166683",
  "year": 2024,
  "metric": "overall_admit_rate",
  "value": 0.039,
  "section_ref": "C1",
  "url": "https://ir.mit.edu/cds",
  "last_verified": "2025-10-26"
}
```

---

### **Articulation.jsonl**
Community college transfer articulation

```json
{
  "cc_id": "deanza",
  "cc_name": "De Anza College",
  "target_school_id": "ucsb",
  "target_school_name": "UC Santa Barbara",
  "target_major": "Mechanical Engineering",
  "target_major_cip": "14.1901",
  "seq": [
    {
      "term": 1,
      "courses": [
        {
          "course_cc": "MATH 1A",
          "course_target": "MATH 3A",
          "min_grade": "C",
          "units": 5
        }
      ]
    }
  ],
  "gpa_floor": 3.2,
  "tag_eligible": false,
  "notes": "ME is not TAG-eligible; highly competitive",
  "citations": ["https://assist.org"],
  "last_verified": "2025-10-26"
}
```

---

## 🔄 **METADATA STANDARDS**

### **All Records Must Include:**
```json
{
  "last_verified": "2025-10-26",
  "retrieved_at": "2025-10-26T12:00:00Z",
  "citations": ["https://..."],
  "notes": "Additional context"
}
```

### **School Identifiers:**
```json
{
  "school_id": "mit",
  "school_name": "Massachusetts Institute of Technology",
  "ipeds_id": "166683"
}
```

### **Program Identifiers:**
```json
{
  "major_cip": "11.0701",
  "major_name": "Computer Science"
}
```

---

## ✅ **VALIDATION CHECKLIST**

Before loading any record:
- [ ] All required fields present
- [ ] `citations` array has at least 1 URL
- [ ] `last_verified` is within 120 days for volatile data
- [ ] School IDs match IPEDS database
- [ ] CIP codes are valid 6-digit codes
- [ ] Dates in ISO 8601 format (YYYY-MM-DD)
- [ ] URLs are accessible (200 status)

---

**This schema reference ensures all training data is structured, cited, versioned, and verifiable.** 🎯

