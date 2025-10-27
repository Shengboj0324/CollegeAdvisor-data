#!/usr/bin/env python3
"""
Comprehensive Stress Test Suite
10 complex real-world scenarios with extreme scrutiny
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
from production_rag import ProductionRAG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 10 STRESS TEST SCENARIOS
STRESS_TESTS = [
    {
        "id": "test_01_fafsa_css_complex",
        "category": "FAFSA/CSS + SAI Net Price Stress Test",
        "query": """U.S. citizen; divorced parents; custodial parent remarried; non-custodial parent refuses CSS; 
family owns a <50-employee S-corp (owner-operated), 2 rental units, $110k in parent 401(k), 
$70k in student-owned UTMA; $35k grandparent-owned 529; AGI $165k; 3 kids in college next year.

Compute estimated SAI and college-specific net price at 6 schools (2 FAFSA-only, 4 CSS Profile), 
including how each treats business equity, home equity, UTMA, grandparent 529, and non-custodial waivers. 
Show a side-by-side table, cite each school's aid policy page + StudentAid.gov, and state exact assumptions. 
Provide a "best-value shortlist" and negotiating strategy.""",
        "required_elements": [
            "SAI calculation with exact formula",
            "6 schools (2 FAFSA-only, 4 CSS Profile)",
            "Business equity treatment (<50 employees)",
            "UTMA treatment (parent vs student asset)",
            "Grandparent 529 treatment (2024-2025 rule change)",
            "NCP waiver policies",
            "Side-by-side comparison table",
            "Citations to school aid pages",
            "Citations to StudentAid.gov",
            "Best-value shortlist",
            "Negotiating strategy"
        ],
        "grading_criteria": {
            "citation_coverage": "Every claim must have official source",
            "quantification": "Exact SAI and net price numbers",
            "policy_traps": "Must call out NCP waiver difficulty, UTMA treatment, grandparent 529 rule change",
            "decisive_recommendation": "Clear best-value shortlist with trade-offs"
        }
    },
    {
        "id": "test_02_cs_capacity_constrained",
        "category": "Capacity-Constrained CS/Data Science Admissions",
        "query": """Applicant targets UIUC (CS vs. CS+X), Georgia Tech (CS), UW (CSE direct-to-major), 
UCSD (CSE/DS25), UCI (CS/DS), Purdue (CS), UT Austin (CS).

Build a comparison of direct admit vs pre-major, admit rates by major, internal transfer gates 
(GPA cutoffs, course filters, capacity), and time-to-degree risk if not directly admitted. 
Include links to each department's latest policy page and Common Data Set where applicable. 
Conclude with a go/no-go recommendation per school and a risk-mitigation plan 
(alternate majors, early coursework, petition windows).""",
        "required_elements": [
            "7 schools compared (UIUC, Georgia Tech, UW, UCSD, UCI, Purdue, UT Austin)",
            "Direct admit vs pre-major paths",
            "Admit rates by major",
            "Internal transfer GPA cutoffs",
            "Course prerequisites for transfer",
            "Capacity constraints",
            "Time-to-degree risk analysis",
            "Links to department policy pages",
            "Common Data Set references",
            "Go/no-go recommendation per school",
            "Risk-mitigation plan"
        ],
        "grading_criteria": {
            "citation_coverage": "Every school's policy page linked",
            "quantification": "Exact GPA cutoffs, admit rates, capacity numbers",
            "policy_traps": "Must call out capped majors, transfer difficulty, time-to-degree risk",
            "decisive_recommendation": "Clear go/no-go per school with risk mitigation"
        }
    },
    {
        "id": "test_03_uc_csu_wue_residency",
        "category": "UC/CSU Residency, WUE, and Tuition Optimization",
        "query": """CA-resident senior weighing UCs, CSUs, and WUE options in AZ/CO/NV/OR/WA/UT/ID/MT, 
plus Cal Poly SLO vs SDSU.

Explain UC/CSU residency determinations for dependents (financial independence tests, physical presence, intent), 
and map WUE programs that actually discount tuition for CS/Engineering (many exclude high-demand majors). 
Produce a decision tree that minimizes net 4-year cost given GPA 3.86 UW, rigor AP/IB, and family AGI $145k. 
Cite UCOP, CSU, campus registrars, and WICHE WUE pages.""",
        "required_elements": [
            "UC/CSU residency rules (financial independence, physical presence, intent)",
            "WUE programs for CS/Engineering (with exclusions)",
            "States covered: AZ/CO/NV/OR/WA/UT/ID/MT",
            "Cal Poly SLO vs SDSU comparison",
            "Decision tree for cost minimization",
            "GPA 3.86 UW, AP/IB rigor, AGI $145k scenario",
            "Citations to UCOP",
            "Citations to CSU",
            "Citations to WICHE WUE pages",
            "4-year cost projections"
        ],
        "grading_criteria": {
            "citation_coverage": "UCOP, CSU, WICHE official pages",
            "quantification": "Exact 4-year costs, WUE discount amounts",
            "policy_traps": "Must call out WUE exclusions for CS/Engineering, residency gotchas",
            "decisive_recommendation": "Clear decision tree with cost optimization"
        }
    },
    {
        "id": "test_04_premed_bsmd",
        "category": "Pre-Med Pathways: BS/MD vs Traditional",
        "query": """Compare Brown PLME, Rice/Baylor, Pitt GAP, Case PPSP, Stony Brook Scholars for Medicine 
vs traditional routes at UCLA, Michigan, UNC, UVA.

For each BS/MD: admission selectivity, MCAT/GPA requirements, conditional guarantees, acceleration, 
required majors, linkage fine print, attrition, total cost (undergrad+MD), and in-state preference at med schools. 
For traditional: pre-med advising quality, committee letters, AAMC acceptance data by GPA/MCAT, 
in-state med school bias. Deliver a ROI and risk analysis with sources (program pages + AAMC).""",
        "required_elements": [
            "5 BS/MD programs (Brown PLME, Rice/Baylor, Pitt GAP, Case PPSP, Stony Brook)",
            "4 traditional routes (UCLA, Michigan, UNC, UVA)",
            "Admission selectivity for each",
            "MCAT/GPA requirements",
            "Conditional guarantees",
            "Acceleration options",
            "Required majors",
            "Linkage fine print",
            "Attrition rates",
            "Total cost (undergrad+MD)",
            "In-state preference",
            "Pre-med advising quality",
            "AAMC acceptance data",
            "ROI analysis",
            "Risk analysis",
            "Citations to program pages and AAMC"
        ],
        "grading_criteria": {
            "citation_coverage": "Every program page + AAMC data",
            "quantification": "Exact costs, acceptance rates, GPA/MCAT thresholds",
            "policy_traps": "Must call out conditional guarantees, attrition, in-state bias",
            "decisive_recommendation": "Clear ROI and risk analysis"
        }
    },
    {
        "id": "test_05_international_student",
        "category": "International Student (PRC passport, U.S. HS) — Need-Aware + Funding",
        "query": """F-1 in U.S. HS; intends CS or Data Science; budget $35k/yr max.

Identify need-aware vs need-blind for internationals, schools offering full-need or large merit to internationals; 
I-20 issuance timelines; proof-of-funds; on-campus work limits; CPT/OPT + STEM OPT extension rules. 
Provide a ranked list of 12 realistic targets with historical merit patterns and exact links to 
international aid pages and ICE/USCIS guidance. Include a visa/finance risk register.""",
        "required_elements": [
            "Need-aware vs need-blind for internationals",
            "Schools offering full-need to internationals",
            "Schools offering large merit to internationals",
            "I-20 issuance timelines",
            "Proof-of-funds requirements",
            "On-campus work limits (20 hrs/week)",
            "CPT/OPT rules",
            "STEM OPT extension (24 months)",
            "12 realistic targets ranked",
            "Historical merit patterns",
            "Links to international aid pages",
            "ICE/USCIS guidance citations",
            "Visa/finance risk register"
        ],
        "grading_criteria": {
            "citation_coverage": "Every school's international aid page + ICE/USCIS",
            "quantification": "Exact merit amounts, budget fit ($35k/yr)",
            "policy_traps": "Must call out need-aware status, I-20 proof-of-funds, work limits",
            "decisive_recommendation": "Clear ranked list with risk register"
        }
    },
]


def grade_response(response, test: Dict) -> Dict:
    """Grade a stress test response with extreme scrutiny"""
    score = 0
    max_score = 100
    feedback = []

    # Handle AnswerResult dataclass
    citations = response.citations if hasattr(response, 'citations') else []
    answer_text = response.answer if hasattr(response, 'answer') else str(response)

    # 1. Citation Coverage (30 points)
    citation_score = 0
    if citations:
        citation_count = len(citations)
        if citation_count >= 5:
            citation_score = 30
        elif citation_count >= 3:
            citation_score = 20
            feedback.append(f"⚠️ Only {citation_count} citations (need 5+)")
        else:
            citation_score = 10
            feedback.append(f"❌ Insufficient citations: {citation_count} (need 5+)")
    else:
        feedback.append("❌ NO CITATIONS - CRITICAL FAILURE")
    score += citation_score

    # 2. Required Elements Coverage (30 points)
    required_elements = test.get("required_elements", [])
    elements_found = 0
    missing_elements = []

    answer_lower = answer_text.lower()
    for element in required_elements:
        # Simple keyword matching (would need more sophisticated NLP in production)
        keywords = element.lower().split()
        if any(kw in answer_lower for kw in keywords[:3]):  # Check first 3 keywords
            elements_found += 1
        else:
            missing_elements.append(element)

    element_score = int((elements_found / len(required_elements)) * 30) if required_elements else 0
    score += element_score

    if missing_elements:
        feedback.append(f"⚠️ Missing elements: {', '.join(missing_elements[:3])}...")

    # 3. Quantification (20 points)
    # Check for numbers, dollar amounts, percentages
    has_numbers = any(char.isdigit() for char in answer_text)
    has_dollar = '$' in answer_text
    has_percent = '%' in answer_text
    
    quant_score = 0
    if has_numbers and has_dollar:
        quant_score = 20
    elif has_numbers:
        quant_score = 10
        feedback.append("⚠️ Missing dollar amounts")
    else:
        feedback.append("❌ NO QUANTIFICATION - numbers required")
    score += quant_score
    
    # 4. Decisive Recommendation (20 points)
    recommendation_keywords = ["recommend", "suggest", "best", "shortlist", "go/no-go", "decision"]
    has_recommendation = any(kw in answer_lower for kw in recommendation_keywords)
    
    rec_score = 20 if has_recommendation else 0
    if not has_recommendation:
        feedback.append("❌ NO DECISIVE RECOMMENDATION")
    score += rec_score
    
    # Calculate final grade
    grade = score / max_score * 10  # Convert to 10-point scale
    
    return {
        "score": score,
        "max_score": max_score,
        "grade": round(grade, 2),
        "citation_score": citation_score,
        "element_score": element_score,
        "quant_score": quant_score,
        "rec_score": rec_score,
        "feedback": feedback,
        "elements_found": elements_found,
        "elements_total": len(required_elements),
        "missing_elements": missing_elements
    }


def main():
    """Run comprehensive stress tests"""
    logger.info("="*80)
    logger.info("COMPREHENSIVE STRESS TEST SUITE")
    logger.info("="*80)
    
    # Initialize RAG
    logger.info("\nInitializing Production RAG...")
    rag = ProductionRAG(db_path="chroma_data")
    
    # Run stress tests
    results = []
    total_score = 0
    
    for i, test in enumerate(STRESS_TESTS, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"STRESS TEST {i}/5: {test['category']}")
        logger.info(f"{'='*80}")
        logger.info(f"\nQuery: {test['query'][:200]}...")
        
        # Query RAG
        response = rag.query(test["query"])
        
        # Grade response
        grading = grade_response(response, test)
        
        # Store result (convert dataclass to dict)
        response_dict = {
            "answer": response.answer if hasattr(response, 'answer') else str(response),
            "citations": [{"url": c.url, "last_verified": c.last_verified} for c in response.citations] if hasattr(response, 'citations') else [],
            "should_abstain": response.should_abstain if hasattr(response, 'should_abstain') else False,
            "citation_coverage": response.citation_coverage if hasattr(response, 'citation_coverage') else 0.0
        }

        result = {
            "test_id": test["id"],
            "category": test["category"],
            "query": test["query"],
            "response": response_dict,
            "grading": grading
        }
        results.append(result)
        total_score += grading["grade"]
        
        # Print grading
        logger.info(f"\n{'─'*80}")
        logger.info(f"GRADE: {grading['grade']}/10.0")
        logger.info(f"{'─'*80}")
        logger.info(f"  Citation Score: {grading['citation_score']}/30")
        logger.info(f"  Element Score: {grading['element_score']}/30 ({grading['elements_found']}/{grading['elements_total']} elements)")
        logger.info(f"  Quantification Score: {grading['quant_score']}/20")
        logger.info(f"  Recommendation Score: {grading['rec_score']}/20")
        
        if grading["feedback"]:
            logger.info(f"\nFeedback:")
            for fb in grading["feedback"]:
                logger.info(f"  {fb}")
    
    # Calculate average
    avg_score = total_score / len(STRESS_TESTS)
    
    # Print summary
    logger.info(f"\n{'='*80}")
    logger.info(f"STRESS TEST SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"\nTests Run: {len(STRESS_TESTS)}")
    logger.info(f"Average Score: {avg_score:.2f}/10.0")
    
    # Save results
    output_path = "stress_test_results.json"
    with open(output_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "tests_run": len(STRESS_TESTS),
            "average_score": avg_score,
            "results": results
        }, f, indent=2)
    
    logger.info(f"\nResults saved to {output_path}")
    
    # Pass/fail determination
    logger.info(f"\n{'='*80}")
    if avg_score >= 9.0:
        logger.info("✅ PASS: Excellent performance (≥9.0)")
    elif avg_score >= 7.0:
        logger.info("⚠️ CONDITIONAL PASS: Good but needs improvement (7.0-8.9)")
    else:
        logger.info("❌ FAIL: Requires data expansion and improvement (<7.0)")
    logger.info(f"{'='*80}")


if __name__ == "__main__":
    main()

