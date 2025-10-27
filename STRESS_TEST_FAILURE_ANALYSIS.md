# STRESS TEST FAILURE ANALYSIS

**Date:** 2025-10-26  
**Average Score:** 5.84/10.0  
**Status:** ❌ FAIL (Threshold: 7.0)

---

## 📊 TEST RESULTS SUMMARY

| Test | Category | Score | Status |
|------|----------|-------|--------|
| 1 | FAFSA/CSS + SAI Net Price Stress Test | 6.6/10.0 | ❌ FAIL |
| 2 | Capacity-Constrained CS/Data Science Admissions | 7.0/10.0 | ⚠️ BORDERLINE |
| 3 | UC/CSU Residency, WUE, and Tuition Optimization | 5.5/10.0 | ❌ FAIL |
| 4 | Pre-Med Pathways: BS/MD vs Traditional | 4.7/10.0 | ❌ FAIL |
| 5 | International Student — Need-Aware + Funding | 5.4/10.0 | ❌ FAIL |

---

## 🔍 ROOT CAUSE ANALYSIS

### **Problem 1: Missing Critical Data Types**

The current 1,380 records cover:
- ✅ Aid policies (69 records)
- ✅ NPC results (240 records)
- ✅ Major gates (24 records)
- ✅ SAI examples (25 records)
- ✅ ASSIST articulation (964 records)
- ✅ CDS extracts (55 records)

**But missing:**
- ❌ **International student aid policies** (need-aware vs need-blind, merit for internationals)
- ❌ **Residency determination rules** (UC/CSU, WUE eligibility)
- ❌ **BS/MD program details** (MCAT/GPA requirements, conditional guarantees)
- ❌ **Visa/immigration data** (I-20, CPT/OPT, STEM OPT)
- ❌ **Comparative cost analysis** (4-year projections, WUE discounts)
- ❌ **Admit rates by major** (CS, Engineering, Data Science)
- ❌ **Negotiating strategies** (professional judgment, appeals)

### **Problem 2: Missing Decisive Recommendations**

**Current behavior:** RAG retrieves relevant data and cites sources ✅  
**Missing:** Synthesizing data into actionable recommendations ❌

**Examples:**
- Test 1: No "best-value shortlist" or "negotiating strategy"
- Test 3: No "decision tree for cost minimization"
- Test 4: No "ROI and risk analysis"
- Test 5: No "ranked list of 12 realistic targets"

**Root cause:** RAG is designed to cite-or-abstain, not to make subjective recommendations.

### **Problem 3: Missing Comparison Tables**

**Current behavior:** RAG returns list of individual records  
**Missing:** Side-by-side comparison tables

**Examples:**
- Test 1: No "side-by-side table" of 6 schools
- Test 2: No comparison of "direct admit vs pre-major" across 7 schools
- Test 4: No comparison of BS/MD vs traditional routes

**Root cause:** RAG returns individual records, not synthesized comparisons.

---

## 📈 DATA GAPS IDENTIFIED

### **Priority 1: Critical Missing Data (Must-Have)**

1. **International Student Aid Policies (100 records)**
   - Need-aware vs need-blind status for internationals
   - Schools offering full-need to internationals (MIT, Harvard, Yale, Princeton, Amherst)
   - Schools offering large merit to internationals
   - Historical merit patterns
   - Application requirements for international aid

2. **Residency Determination Rules (50 records)**
   - UC residency rules (financial independence, physical presence, intent)
   - CSU residency rules
   - WUE eligibility by major (CS/Engineering exclusions)
   - State-by-state WUE programs (AZ/CO/NV/OR/WA/UT/ID/MT)
   - Residency appeal processes

3. **BS/MD Program Details (25 records)**
   - 5 programs: Brown PLME, Rice/Baylor, Pitt GAP, Case PPSP, Stony Brook
   - Admission selectivity
   - MCAT/GPA requirements
   - Conditional guarantees
   - Acceleration options
   - Total cost (undergrad+MD)
   - Attrition rates

4. **Visa/Immigration Data (30 records)**
   - I-20 issuance timelines
   - Proof-of-funds requirements
   - On-campus work limits (20 hrs/week)
   - CPT rules
   - OPT rules (12 months)
   - STEM OPT extension (24 months)
   - F-1 visa restrictions

5. **Admit Rates by Major (100 records)**
   - CS admit rates at top 50 schools
   - Engineering admit rates
   - Data Science admit rates
   - Direct admit vs pre-major rates
   - Internal transfer rates

### **Priority 2: Enhanced Existing Data (Should-Have)**

6. **Expanded NPC Results (200 more records)**
   - Add 20 more schools (total 60 schools)
   - Add international student scenarios
   - Add divorced parent scenarios with NCP refusal
   - Add S-corp/business owner scenarios

7. **Expanded Aid Policies (100 more records)**
   - Add negotiating strategies
   - Add professional judgment policies
   - Add appeal processes
   - Add merit scholarship policies

8. **Cost Comparison Data (50 records)**
   - 4-year total cost projections
   - WUE discount amounts
   - In-state vs out-of-state comparisons
   - Living cost differentials (urban vs rural)

### **Priority 3: Synthesis Capabilities (Nice-to-Have)**

9. **Decision Trees (10 records)**
   - Cost minimization decision trees
   - Major selection decision trees
   - School selection decision trees

10. **Comparison Templates (20 records)**
    - Side-by-side school comparisons
    - BS/MD vs traditional comparisons
    - Direct admit vs pre-major comparisons

---

## 🎯 ACTION PLAN

### **Phase 1: Critical Data Expansion (Priority 1)**

**Target:** Add 305 records (1,380 → 1,685)

1. ✅ Create `scripts/data_expansion/generate_international_aid.py`
   - 100 records: international aid policies for top 100 schools

2. ✅ Create `scripts/data_expansion/generate_residency_rules.py`
   - 50 records: UC/CSU/WUE residency rules

3. ✅ Create `scripts/data_expansion/generate_bsmd_programs.py`
   - 25 records: BS/MD program details

4. ✅ Create `scripts/data_expansion/generate_visa_immigration.py`
   - 30 records: F-1 visa, I-20, CPT/OPT rules

5. ✅ Create `scripts/data_expansion/generate_admit_rates.py`
   - 100 records: admit rates by major for top 50 schools

### **Phase 2: Enhanced Existing Data (Priority 2)**

**Target:** Add 350 records (1,685 → 2,035)

6. ✅ Expand NPC results (240 → 440)
7. ✅ Expand aid policies (69 → 169)
8. ✅ Add cost comparison data (0 → 50)

### **Phase 3: Re-test and Iterate**

9. ✅ Re-run stress tests
10. ✅ If score < 9.0, identify new gaps and expand further
11. ✅ Repeat until score ≥ 9.0

---

## 🎊 SUCCESS CRITERIA

**Hard Gates (Must Pass):**
- ✅ Citations coverage ≥ 90%
- ✅ Fabricated-number rate ≤ 2%
- ✅ Structure validity ≥ 95%
- ✅ Abstain correctness ≥ 95%

**Stress Test Gates (Must Pass):**
- ❌ Average score ≥ 9.0 (currently 5.84)
- ❌ All tests ≥ 7.0 (currently 4 of 5 fail)
- ❌ Required elements coverage ≥ 80% (currently ~40%)
- ❌ Decisive recommendations in 100% of tests (currently 20%)

---

## 📝 NEXT STEPS

1. **Immediate:** Create 5 data expansion scripts (Priority 1)
2. **Short-term:** Generate 305 new records
3. **Medium-term:** Expand existing data (Priority 2)
4. **Long-term:** Re-test until 9.0+ score achieved

**Estimated timeline:** 2-3 iterations to reach 9.0+ score
**Estimated final record count:** 2,000-2,500 records

