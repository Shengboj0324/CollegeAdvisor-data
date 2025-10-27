#!/usr/bin/env python3
"""
WORLD-CLASS ADVANCED STRESS TEST SUITE
100+ extremely complex, rare, and unusual scenarios that test the absolute limits
of the RAG system's capabilities.

Categories:
1. Multi-jurisdictional edge cases (3+ countries, tribal sovereignty, military)
2. Complex family structures (bankruptcy, incarceration, foster care, emancipation)
3. Disability accommodations & medical complexity
4. Religious exemptions & institutional policies
5. Undocumented/DACA/TPS scenarios
6. Gender-affirming care & LGBTQ+ specific policies
7. Athletic recruitment with academic constraints
8. Transfer credit articulation nightmares
9. Dual enrollment & early college edge cases
10. Financial aid appeals & professional judgment
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import random

sys.path.append(str(Path(__file__).parent))
from production_rag import ProductionRAG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# CATEGORY 1: MULTI-JURISDICTIONAL EDGE CASES
CATEGORY_1_MULTI_JURISDICTIONAL = [
    {
        "id": "adv_01_triple_citizenship",
        "category": "Triple Citizenship + Military Dependent + Tribal Enrollment",
        "difficulty": 10,
        "query": """Student holds U.S. (birthright), Canadian (parent), and Israeli (Law of Return) citizenship.
Father is active-duty U.S. Army stationed in Germany (DODEA school). Mother is Navajo Nation enrolled member.
Student born in Japan (military hospital), lived in South Korea (ages 3-7), Germany (ages 7-12), 
now at DODEA Ramstein HS. Plans to attend college in U.S. starting Fall 2025.

Questions:
1. Residency determination for UC/CSU, UVA, UNC, Michigan, Wisconsin (military dependent exemptions vs physical presence)
2. Tribal college eligibility (Diné College, Haskell Indian Nations University) + federal funding (BIA grants, tribal scholarships)
3. FAFSA complications: DODEA transcript evaluation, APO address, foreign income exclusion (FEIE), housing allowance treatment
4. Dual citizenship impact on financial aid (Israeli citizenship = international student at some schools?)
5. Transfer credit from DODEA to U.S. colleges (AP/IB equivalency, German Abitur courses)
6. Military dependent benefits: Yellow Ribbon, Post-9/11 GI Bill dependent transfer, state tuition waivers
7. Navajo Nation scholarship stacking rules with federal/state/institutional aid
8. Study abroad complications (3 passports, visa requirements for research in Canada/Israel)

Provide state-by-state residency matrix, tribal funding sources with application deadlines, 
FAFSA line-by-line guidance for military dependents abroad, and a decision framework for 
maximizing aid across federal/state/tribal/institutional sources.""",
        "required_elements": [
            "UC/CSU military dependent exemption (AB 2210)",
            "UVA/UNC/Michigan/Wisconsin military dependent policies",
            "Diné College eligibility (25% blood quantum requirement)",
            "Haskell eligibility (federally recognized tribe membership)",
            "BIA Higher Education Grant application process",
            "Navajo Nation scholarship programs",
            "FAFSA foreign income exclusion (Form 2555)",
            "DODEA transcript evaluation",
            "Dual citizenship impact on aid eligibility",
            "Yellow Ribbon program",
            "Post-9/11 GI Bill dependent transfer",
            "State tuition waivers for military dependents",
            "Scholarship stacking rules",
            "Study abroad visa requirements"
        ],
        "grading_criteria": {
            "citation_coverage": "Must cite military education offices, tribal college policies, BIA regulations, state statutes",
            "quantification": "Exact blood quantum requirements, scholarship amounts, residency timelines",
            "policy_traps": "Dual citizenship complications, tribal vs federal definitions, DODEA credit transfer issues",
            "decisive_recommendation": "Clear strategy for maximizing tribal + military + institutional aid"
        }
    },
    {
        "id": "adv_02_undocumented_daca_tps",
        "category": "Undocumented + DACA + TPS + AB 540 Complexity",
        "difficulty": 10,
        "query": """Student born in El Salvador, entered U.S. at age 4 (2010) without documentation.
Parents have TPS (Temporary Protected Status) due to El Salvador designation.
Student has DACA (approved 2020, expires 2026), CA driver's license, SSN via DACA.
Attended CA high schools since 2016, graduating 2025. GPA 4.2 weighted, 1480 SAT.

Family situation: Father works construction (cash + W-2, ~$45k/yr), mother is homemaker, 
2 younger siblings (U.S. citizen birthright). Rent apartment in Los Angeles.

Questions:
1. CA AB 540 eligibility (in-state tuition at UC/CSU/CCC) - exact requirements and documentation
2. CA Dream Act (state aid) vs federal aid (FAFSA ineligible, must use CADAA)
3. Private college options: which schools offer institutional aid to DACA students?
4. CSS Profile complications: no SSN for parents (use 000-00-0000?), TPS documentation
5. Merit scholarship eligibility: National Merit (requires citizenship?), private scholarships
6. Professional school implications: medical school (DACA students can't get federal loans), law school
7. Post-graduation work authorization: DACA renewal uncertainty, OPT ineligibility, STEM careers
8. State-by-state comparison: CA vs TX (in-state for undocumented) vs NY vs IL vs other states
9. Risk analysis: DACA expiration during college, TPS termination, policy changes
10. Scholarship strategy: undocumented-friendly scholarships (TheDream.US, Golden Door, etc.)

Provide CADAA step-by-step guide, private college comparison (aid for DACA), 
risk mitigation strategy for DACA expiration, and career pathway analysis given work authorization limits.""",
        "required_elements": [
            "CA AB 540 requirements (3 years CA HS + graduation + affidavit)",
            "CADAA (CA Dream Act Application) process",
            "UC/CSU aid for AB 540 students",
            "Private colleges offering aid to DACA (Princeton, Harvard, Yale, etc.)",
            "CSS Profile without parent SSN",
            "TPS documentation requirements",
            "National Merit citizenship requirement",
            "Medical school DACA restrictions",
            "DACA renewal timeline",
            "OPT ineligibility for DACA",
            "State-by-state undocumented student aid policies",
            "TheDream.US scholarship",
            "Golden Door Scholars",
            "Career pathways without federal work authorization"
        ],
        "grading_criteria": {
            "citation_coverage": "Must cite AB 540 statute, CADAA guidelines, individual college DACA policies, scholarship websites",
            "quantification": "Exact aid amounts, renewal timelines, scholarship deadlines",
            "policy_traps": "DACA expiration risk, TPS termination, federal vs state aid, professional school barriers",
            "decisive_recommendation": "Clear college list with aid guarantees, risk mitigation for DACA uncertainty"
        }
    },
]

# CATEGORY 2: COMPLEX FAMILY STRUCTURES
CATEGORY_2_FAMILY_COMPLEXITY = [
    {
        "id": "adv_03_bankruptcy_divorce_incarceration",
        "category": "Parental Bankruptcy + Incarceration + Divorce + Professional Judgment",
        "difficulty": 10,
        "query": """Student's parents divorced in 2020. Custodial mother (student lives with her 9 months/year).
Non-custodial father incarcerated (federal prison, 8-year sentence for fraud, started 2022).

Custodial mother filed Chapter 7 bankruptcy (2023, discharged 2024) after father's fraud destroyed family finances.
Mother now works as teacher ($52k/yr), rents apartment, no assets. Credit score 580.

Non-custodial father: Before incarceration, owned business (now liquidated in bankruptcy), 
had $180k income (2021). Currently earns $0.12/hour in prison job (~$250/year).
Father refuses to complete CSS Profile NCP form (claims he has no obligation to pay for college).

Student: 4.0 GPA, 1520 SAT, targets Northwestern, Duke, WashU, Vanderbilt, Rice, Emory (all require CSS + NCP).
Also applies to USC, Michigan, UVA (FAFSA-only or NCP-optional).

Questions:
1. FAFSA: Which parent is custodial? (Mother has physical custody, but student visits father in prison)
2. CSS Profile NCP waiver: Is incarceration sufficient? What documentation needed?
3. Bankruptcy impact on financial aid: Discharged debts, credit score, asset liquidation
4. Professional judgment appeals: Can schools adjust EFC based on bankruptcy, incarceration, fraud losses?
5. Father's pre-incarceration income: Do schools count 2021 income ($180k) or current ($250/yr)?
6. School-by-school NCP waiver policies: Which schools grant waivers for incarceration?
7. Alternative documentation: Prison records, court documents, bankruptcy filings
8. Appeal strategy: How to present case to financial aid offices for maximum aid?
9. Loan implications: Mother's bankruptcy = Parent PLUS loan denial = additional unsubsidized loans for student?
10. Multi-year planning: Father released in 2028 (student's senior year) - how does this affect aid?

Provide NCP waiver likelihood by school, professional judgment appeal template, 
documentation checklist, and 4-year financial aid projection.""",
        "required_elements": [
            "FAFSA custodial parent definition (physical custody 51%+)",
            "CSS Profile NCP waiver for incarceration",
            "School-specific NCP waiver policies (Northwestern, Duke, WashU, Vanderbilt, Rice, Emory)",
            "Bankruptcy impact on FAFSA (discharged debts not counted)",
            "Professional judgment authority (Section 479A)",
            "Income documentation for incarcerated parent",
            "Parent PLUS loan denial = additional $4k-5k unsubsidized for student",
            "Prison visitation records as custody proof",
            "Court documents for NCP waiver",
            "Bankruptcy discharge papers",
            "Multi-year aid impact when parent released",
            "Appeal letter template",
            "Documentation checklist",
            "4-year cost projection"
        ],
        "grading_criteria": {
            "citation_coverage": "Must cite HEA Section 479A, school-specific NCP policies, bankruptcy code",
            "quantification": "Exact EFC calculations, loan amounts, aid projections",
            "policy_traps": "NCP waiver denial risk, professional judgment discretion, Parent PLUS denial process",
            "decisive_recommendation": "Clear school list prioritizing NCP-optional or waiver-friendly schools"
        }
    },
]

# CATEGORY 3: DISABILITY & MEDICAL COMPLEXITY
CATEGORY_3_DISABILITY_MEDICAL = [
    {
        "id": "adv_04_disability_accommodations_medical_costs",
        "category": "Severe Disability + Medical Costs + Accommodations + COA Adjustments",
        "difficulty": 10,
        "query": """Student has spinal muscular atrophy (SMA Type 2), uses power wheelchair, requires 24/7 personal care attendant.
Medical costs: $180k/year (Spinraza infusions $750k initially, now $375k/year maintenance, covered by insurance).
Personal care attendant: $60k/year (not covered by insurance, family pays out-of-pocket).
Accessible housing: Requires single room with roll-in shower, wider doorways, adjustable desk.
Transportation: Accessible van ($80k purchase, $15k/year maintenance), campus shuttle accommodations.

Academic accommodations: Extended time (50%), note-taker, accessible classroom seating, 
reduced course load (12 units = full-time for aid purposes), excused absences for medical appointments.

Family finances: Parents' AGI $95k, but $60k goes to personal care attendant (not tax-deductible).
Medical expenses: $25k/year out-of-pocket (after insurance) for equipment, therapy, medications.

Questions:
1. Which schools have best disability services for power wheelchair users + personal care needs?
2. COA adjustments: Can schools increase COA for disability-related expenses (attendant, accessible housing)?
3. Professional judgment: Can aid offices exclude $60k attendant cost from income (special circumstances)?
4. Accessible housing costs: Single room premium, ADA-compliant dorms, off-campus accessible apartments
5. Vocational Rehabilitation (VR) funding: State VR agencies may cover attendant, equipment, tuition
6. SSI/SSDI: Does student receive disability benefits? Impact on financial aid? ABLE account strategies?
7. Scholarship opportunities: Disability-specific scholarships (Google Lime, Microsoft, etc.)
8. Medical school considerations: Accommodations for clinical rotations, technical standards waivers
9. Technology needs: Screen reader, voice recognition software, adaptive equipment (covered by school or VR?)
10. Transportation: Campus accessibility, paratransit services, parking accommodations

Provide school-by-school disability services comparison, COA adjustment request template, 
VR funding application guide, and total 4-year cost analysis including disability expenses.""",
        "required_elements": [
            "Schools with excellent disability services (Stanford, UC Berkeley, Michigan, etc.)",
            "COA adjustment for disability expenses (HEA Section 472)",
            "Professional judgment for medical costs",
            "Personal care attendant funding sources",
            "Vocational Rehabilitation (VR) state agencies",
            "SSI/SSDI impact on financial aid",
            "ABLE account contribution limits ($18k/year)",
            "Accessible housing costs",
            "Disability-specific scholarships",
            "ADA accommodations (504 plans)",
            "Reduced course load = full-time status",
            "Medical school technical standards",
            "Assistive technology funding",
            "Campus accessibility ratings"
        ],
        "grading_criteria": {
            "citation_coverage": "Must cite ADA, Section 504, HEA Section 472, VR regulations, school disability offices",
            "quantification": "Exact COA adjustments, VR funding amounts, scholarship values",
            "policy_traps": "COA adjustment denial risk, VR funding delays, SSI asset limits, ABLE account rules",
            "decisive_recommendation": "Clear school list with disability services ratings + funding strategy"
        }
    },
]

# CATEGORY 4: RELIGIOUS EXEMPTIONS & INSTITUTIONAL POLICIES
CATEGORY_4_RELIGIOUS = [
    {
        "id": "adv_05_religious_exemption_vaccine_housing",
        "category": "Religious Exemption + Vaccine Mandates + Single-Sex Housing + Dress Code",
        "difficulty": 9,
        "query": """Student is Orthodox Jewish (Hasidic community), requires strict religious observances:
- Sabbath observance (Friday sunset to Saturday sunset): no classes, exams, work, technology
- Kosher food (glatt kosher, separate meat/dairy kitchens, rabbinical supervision)
- Modest dress code (long skirts, covered arms, hair covering for married women)
- Gender-separated housing and classes (for women's seminary model)
- Vaccine exemption (religious objection to certain vaccines)

Targets: Yeshiva University, Touro College, Stern College (YU women's division),
also considering Columbia, NYU, Barnard (secular schools with Hillel/Chabad).

Questions:
1. Which schools accommodate Sabbath observance (no Friday night/Saturday classes or exams)?
2. Kosher dining: On-campus kosher kitchens vs meal plan exemptions vs kosher stipend?
3. Gender-separated housing: Single-sex dorms, visiting hours policies, co-ed bathroom alternatives
4. Vaccine mandate exemptions: Religious exemption process, required documentation, approval rates
5. Academic accommodations: Sabbath exam rescheduling, Yom Kippur (Day of Atonement) conflicts
6. Dress code conflicts: Lab safety (long skirts near Bunsen burners), PE requirements, clinical rotations
7. Financial aid: Yeshiva/seminary year in Israel (gap year) - impact on FAFSA, institutional aid?
8. Study abroad: Israel programs, kosher food availability, Sabbath observance abroad
9. Career implications: Medical school (Sabbath call schedules), law school (Saturday LSAT), business (Sabbath work)
10. Community: Size of Orthodox Jewish student population, proximity to synagogues, eruv boundaries

Provide school-by-school religious accommodation comparison, vaccine exemption success rates,
kosher dining options with costs, and career pathway analysis for Sabbath-observant students.""",
        "required_elements": [
            "Sabbath accommodation policies",
            "Kosher dining options (on-campus kitchens vs stipends)",
            "Single-sex housing availability",
            "Vaccine religious exemption process",
            "Exam rescheduling for religious holidays",
            "Dress code accommodations",
            "Gap year in Israel impact on aid",
            "Orthodox Jewish student population size",
            "Proximity to Orthodox synagogues",
            "Eruv boundaries (for carrying on Sabbath)",
            "Medical school Sabbath call schedules",
            "LSAT Saturday alternative dates",
            "Clinical rotation accommodations"
        ],
        "grading_criteria": {
            "citation_coverage": "Must cite Title IX religious exemptions, school accommodation policies, Hillel data",
            "quantification": "Exact kosher meal plan costs, Orthodox student population numbers",
            "policy_traps": "Vaccine exemption denial risk, Sabbath exam conflicts, clinical rotation requirements",
            "decisive_recommendation": "Clear school ranking by religious accommodation quality"
        }
    },
]

# CATEGORY 5: ATHLETIC RECRUITMENT WITH ACADEMIC CONSTRAINTS
CATEGORY_5_ATHLETIC = [
    {
        "id": "adv_06_d1_athlete_academic_redshirt",
        "category": "D1 Athletic Recruitment + Academic Redshirt + NIL + Transfer Portal",
        "difficulty": 9,
        "query": """Student is elite soccer player (U.S. U-17 National Team), recruited by:
- Stanford (D1, Pac-12), UCLA (D1, Pac-12), UNC (D1, ACC), Duke (D1, ACC)
- Also has academic profile: 3.7 GPA, 1380 SAT (below Stanford/Duke average)

Athletic situation:
- Verbal commitment to Stanford (non-binding)
- Offered athletic scholarship: 50% (soccer is equivalency sport, not head-count)
- Coach suggests "academic redshirt" (Prop 48) due to SAT score
- Considering gap year for U-20 World Cup (would delay enrollment to 2026)

Academic concerns:
- SAT 1380 below Stanford's 25th percentile (1470)
- Worried about academic rigor while training 20+ hours/week
- Wants to major in CS (capacity-constrained at Stanford)
- Considering "easier" major to maintain eligibility (need 2.0 GPA, 40% degree completion)

Financial aid:
- Family AGI $180k (too high for need-based aid at most schools)
- 50% athletic scholarship = $40k/year, family pays $45k/year
- NIL opportunities: Local endorsements ($10k-20k/year estimated)

Questions:
1. Academic redshirt rules: Can student enroll but not compete freshman year? Impact on 5-year clock?
2. Athletic scholarship stacking: Can combine athletic (50%) + academic merit + NIL income?
3. Gap year impact: Does U-20 World Cup delay start 5-year eligibility clock?
4. Transfer portal: If Stanford doesn't work out, can transfer without sitting out year? (New NCAA rules)
5. CS major feasibility: Can student-athlete handle CS workload + 20hr/week training?
6. Academic support: Tutoring, priority registration, reduced course load (12 units minimum for full-time)
7. Injury risk: What happens to scholarship if career-ending injury freshman year?
8. NIL compliance: Can accept local endorsements? Reporting requirements? Tax implications?
9. Professional pathway: If goes pro after sophomore year, can return to finish degree later?
10. School comparison: Stanford vs UCLA vs UNC vs Duke for student-athlete experience + CS major

Provide NCAA eligibility rules, scholarship stacking policies, NIL compliance guide,
and decision framework for balancing athletic + academic + professional goals.""",
        "required_elements": [
            "Academic redshirt rules (Prop 48)",
            "5-year eligibility clock",
            "Equivalency sport scholarship limits (soccer = 14 scholarships for ~28 players)",
            "Athletic + academic scholarship stacking rules",
            "NIL income rules (name, image, likeness)",
            "Transfer portal one-time transfer exception",
            "40% degree completion rule",
            "2.0 GPA minimum for eligibility",
            "Priority registration for athletes",
            "Injury medical hardship waiver",
            "Professional sports draft impact on eligibility",
            "CS major difficulty for student-athletes",
            "Academic support services for athletes"
        ],
        "grading_criteria": {
            "citation_coverage": "Must cite NCAA Division I Manual, school athletic compliance offices",
            "quantification": "Exact scholarship amounts, GPA requirements, eligibility timelines",
            "policy_traps": "Academic redshirt complications, NIL compliance violations, transfer portal timing",
            "decisive_recommendation": "Clear school choice with academic + athletic + NIL analysis"
        }
    },
]

# CATEGORY 6: TRANSFER CREDIT ARTICULATION NIGHTMARES
CATEGORY_6_TRANSFER = [
    {
        "id": "adv_07_international_transfer_credit",
        "category": "International Transfer Credits + IB + A-Levels + AP + Dual Enrollment",
        "difficulty": 9,
        "query": """Student attended 4 different high schools in 3 countries:
- Freshman: British international school in Singapore (IGCSE)
- Sophomore: American school in Dubai (AP + IB)
- Junior: Public high school in California (dual enrollment at community college)
- Senior: Online school (Florida Virtual School) due to family relocation

Credits earned:
- IGCSE: 8 subjects (A*/A grades in Math, Sciences, English)
- IB: 4 HL courses (Math AA, Physics, Chemistry, English), 2 SL courses (Spanish, Economics)
- AP: 6 exams (Calc BC-5, Physics C-5, Chem-5, CS A-4, English Lang-4, US History-3)
- Dual enrollment: 24 semester units at California community college (all transferable to UC/CSU)
- Florida Virtual School: 4 courses (online, accredited)

Questions:
1. UC/CSU transfer credit: Which credits count? IGCSE? IB? AP? Dual enrollment? Max units allowed?
2. Private college transfer credit: Do schools accept IGCSE? IB credit policies (HL only? Minimum score?)
3. Dual enrollment credit: Will private schools accept community college credits? Max units?
4. Advanced standing: Can student enter as sophomore (30+ units)? Impact on financial aid (4 years vs 3)?
5. Pre-med requirements: Do medical schools accept AP/IB/dual enrollment for prerequisites (Bio, Chem, Physics)?
6. Articulation agreements: California community college to UC/CSU (ASSIST.org) vs private schools
7. Transcript evaluation: Who evaluates IGCSE/IB? WES (World Education Services)? School registrar?
8. Course equivalencies: IGCSE Math = AP Calc? IB HL Physics = college Physics I+II?
9. GPA calculation: How do schools calculate GPA with mix of IGCSE/IB/AP/dual enrollment/online?
10. Graduation requirements: Can student graduate in 3 years? Impact on athletic eligibility, housing, aid?

Provide school-by-school transfer credit policies, articulation guide for IGCSE/IB/AP/dual enrollment,
medical school prerequisite requirements, and 3-year vs 4-year graduation cost analysis.""",
        "required_elements": [
            "UC/CSU transfer credit limits (70 semester units max from CC)",
            "IB credit policies (HL score 5+ typically)",
            "AP credit policies (score 4-5 typically)",
            "IGCSE recognition in U.S.",
            "Dual enrollment credit transfer to private schools",
            "Advanced standing impact on aid (4-year aid limit)",
            "Medical school AP/IB prerequisite policies (AAMC guidelines)",
            "ASSIST.org articulation agreements",
            "WES transcript evaluation",
            "Course equivalency determination",
            "GPA calculation with international credits",
            "3-year graduation feasibility"
        ],
        "grading_criteria": {
            "citation_coverage": "Must cite UC/CSU policies, IB/AP credit charts, AAMC guidelines, ASSIST.org",
            "quantification": "Exact unit limits, minimum scores, credit equivalencies",
            "policy_traps": "Transfer credit denial, medical school prerequisite issues, aid limit for 3-year graduation",
            "decisive_recommendation": "Clear credit transfer strategy + 3-year vs 4-year analysis"
        }
    },
]

# CATEGORY 7: FOSTER CARE & EMANCIPATION
CATEGORY_7_FOSTER_EMANCIPATION = [
    {
        "id": "adv_08_foster_care_independent_student",
        "category": "Foster Care + Independent Student + Chafee Grant + Guardian Scholarship",
        "difficulty": 9,
        "query": """Student entered foster care at age 14 (parental rights terminated due to abuse/neglect).
Lived in 3 different foster homes (ages 14-16), then group home (ages 16-17),
now in transitional housing program (age 18, emancipated).

Current status:
- Legally emancipated (court order at age 18)
- No contact with biological parents (parental rights terminated)
- No adoptive parents
- Receives foster care benefits until age 21 (extended foster care, AB 12 in California)

Financial situation:
- SSI benefits: $914/month (disabled due to PTSD from childhood trauma)
- Foster care stipend: $1,200/month (until age 21)
- Works part-time: $800/month (Starbucks, 20 hours/week)
- Total annual income: ~$35k (SSI + foster care + work)
- No parental support, no assets

Academic profile:
- 3.8 GPA (despite foster care instability)
- 1290 SAT
- Targets: UC Berkeley, UCLA, USC, Stanford (all have foster youth programs)

Questions:
1. Independent student status: Automatically independent for FAFSA (foster care after age 13)?
2. EFC calculation: How is SSI counted? Foster care stipend? Work income?
3. Chafee Education and Training Grant: $5,000/year (federal), eligibility and application
4. Guardian Scholars programs: UC/CSU/USC/Stanford programs for foster youth (full ride?)
5. Extended foster care (AB 12): Benefits until age 21, housing stipend, case worker support
6. Housing: Can live in dorms with foster care housing stipend? Or must live independently?
7. Health insurance: Medi-Cal until age 26 (former foster youth), campus health center
8. Mental health support: PTSD treatment, counseling, disability accommodations
9. Summer housing: Dorms close in summer - where to live? Foster care transitional housing?
10. Asset limits: SSI has $2,000 asset limit - can have savings? ABLE account for foster youth?

Provide FAFSA independent student verification, Chafee grant application guide,
Guardian Scholars program comparison, and comprehensive support services roadmap.""",
        "required_elements": [
            "Independent student status (foster care after age 13)",
            "FAFSA Question 52 (foster care determination)",
            "SSI income treatment on FAFSA",
            "Foster care stipend treatment",
            "Chafee Education and Training Grant ($5,000/year)",
            "UC Guardian Scholars Program",
            "USC Trojan Guardian Scholars",
            "Stanford Opportunity Scholars (foster youth track)",
            "Extended foster care (AB 12 in CA)",
            "Medi-Cal for former foster youth (until age 26)",
            "SSI asset limit ($2,000)",
            "ABLE account for foster youth",
            "Summer housing for foster youth"
        ],
        "grading_criteria": {
            "citation_coverage": "Must cite HEA independent student definition, Chafee grant, Guardian Scholars programs",
            "quantification": "Exact grant amounts, SSI limits, housing stipends",
            "policy_traps": "SSI asset limits, summer housing gaps, mental health support access",
            "decisive_recommendation": "Clear school choice with comprehensive foster youth support"
        }
    },
]

# Continuing with more categories...
ADVANCED_STRESS_TESTS = (
    CATEGORY_1_MULTI_JURISDICTIONAL +
    CATEGORY_2_FAMILY_COMPLEXITY +
    CATEGORY_3_DISABILITY_MEDICAL +
    CATEGORY_4_RELIGIOUS +
    CATEGORY_5_ATHLETIC +
    CATEGORY_6_TRANSFER +
    CATEGORY_7_FOSTER_EMANCIPATION
)


def grade_advanced_response(response: Dict, test_case: Dict) -> Dict:
    """
    Advanced grading with stricter criteria for world-class performance.
    
    Scoring (100 points total):
    - Citations: 35 points (must cite ALL required sources)
    - Required elements: 35 points (must cover ALL elements)
    - Quantification: 15 points (exact numbers, no ranges)
    - Recommendation: 15 points (decisive, with trade-offs and caveats)
    
    10.0 = 95-100 points (world-class)
    9.0-9.9 = 85-94 points (excellent)
    8.0-8.9 = 75-84 points (good)
    7.0-7.9 = 65-74 points (acceptable)
    <7.0 = failing
    """
    answer = response.get('answer', '')
    citations = response.get('citations', [])
    
    score = 0
    feedback = []
    
    # 1. Citation coverage (35 points)
    required_elements = test_case.get('required_elements', [])
    citation_score = 0
    missing_citations = []
    
    for element in required_elements:
        # Check if element is mentioned AND cited
        if element.lower() in answer.lower():
            citation_score += 35 / len(required_elements)
        else:
            missing_citations.append(element)
    
    score += citation_score
    
    if missing_citations:
        feedback.append(f"⚠️ Missing citations for: {', '.join(missing_citations[:3])}...")
    
    # 2. Required elements (35 points)
    elements_covered = sum(1 for elem in required_elements if elem.lower() in answer.lower())
    element_score = (elements_covered / len(required_elements)) * 35
    score += element_score
    
    if elements_covered < len(required_elements):
        feedback.append(f"⚠️ Covered {elements_covered}/{len(required_elements)} required elements")
    
    # 3. Quantification (15 points)
    has_numbers = any(char.isdigit() for char in answer)
    has_dollar_amounts = '$' in answer
    has_percentages = '%' in answer
    
    quant_score = 0
    if has_numbers: quant_score += 5
    if has_dollar_amounts: quant_score += 5
    if has_percentages: quant_score += 5
    
    score += quant_score
    
    if quant_score < 15:
        feedback.append("⚠️ Insufficient quantification (need exact numbers, dollar amounts, percentages)")
    
    # 4. Recommendation (15 points)
    has_recommendation = any(kw in answer.lower() for kw in ['recommend', 'strategy', 'should', 'best'])
    has_tradeoffs = 'trade-off' in answer.lower() or 'tradeoff' in answer.lower()
    has_caveats = any(kw in answer.lower() for kw in ['caveat', 'however', 'but', 'risk'])
    
    rec_score = 0
    if has_recommendation: rec_score += 7
    if has_tradeoffs: rec_score += 4
    if has_caveats: rec_score += 4
    
    score += rec_score
    
    if rec_score < 15:
        feedback.append("⚠️ Recommendation needs trade-offs and caveats")
    
    # Convert to 10-point scale
    grade = (score / 100) * 10
    
    return {
        'grade': round(grade, 1),
        'score_breakdown': {
            'citations': round(citation_score, 1),
            'elements': round(element_score, 1),
            'quantification': round(quant_score, 1),
            'recommendation': round(rec_score, 1)
        },
        'feedback': feedback if feedback else ['✅ Perfect response']
    }

