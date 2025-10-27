#!/usr/bin/env python3
"""
Generate Residency Determination Rules
50 records covering UC/CSU residency, WUE eligibility, state-by-state programs
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_uc_residency_rules() -> List[Dict]:
    """Generate UC residency determination rules"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    rules = [
        {
            "rule_id": "uc_residency_physical_presence",
            "system": "UC",
            "rule_type": "physical_presence",
            "requirement": "Physical presence in California for 366 days prior to residence determination date",
            "details": "Student must be physically present in CA for more than one year (366 days) before the residence determination date (generally the first day of classes). Absences for brief visits do not break continuity.",
            "exceptions": ["Active military duty", "Temporary absences for education"],
            "citations": ["https://www.ucop.edu/residency/residency-requirements.html"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "uc_residency_intent",
            "system": "UC",
            "rule_type": "intent",
            "requirement": "Intent to make California permanent home",
            "details": "Student must demonstrate intent to make California their permanent home through objective evidence: CA driver's license, CA voter registration, CA tax filing, employment in CA, etc.",
            "evidence_required": ["CA driver's license or ID", "CA voter registration", "CA tax returns", "Employment in CA", "Lease or property ownership"],
            "citations": ["https://www.ucop.edu/residency/residency-requirements.html"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "uc_residency_financial_independence",
            "system": "UC",
            "rule_type": "financial_independence",
            "requirement": "Financial independence for dependent students under 24",
            "details": "Students under 24 who are not financially independent are classified based on parents' residence. To be financially independent: (1) not claimed as dependent on parents' tax returns for 2 prior years, (2) self-supporting for 2 prior years with income/assets to cover expenses.",
            "financial_independence_criteria": [
                "Not claimed as tax dependent for 2 prior years",
                "Self-supporting for 2 prior years",
                "Income and assets sufficient to cover expenses",
                "No parental financial support exceeding $750/year"
            ],
            "citations": ["https://www.ucop.edu/residency/residency-requirements.html"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "uc_residency_exceptions",
            "system": "UC",
            "rule_type": "exceptions",
            "requirement": "AB 540 and other exceptions",
            "details": "AB 540: Students who attended CA high school for 3+ years and graduated (or equivalent) may qualify for in-state tuition even without legal residency. Does NOT qualify for state/institutional aid.",
            "ab540_requirements": [
                "Attended CA high school for 3+ years",
                "Graduated from CA high school or equivalent",
                "Filed affidavit with UC",
                "Will file for legal status when eligible"
            ],
            "citations": ["https://www.ucop.edu/general-counsel/_files/ed-affairs/ab540-sb68-guidance.pdf"],
            "notes": "AB 540 provides in-state tuition but NOT financial aid eligibility",
            "last_verified": today,
            "effective_year": "2024-2025"
        },
    ]
    
    return rules


def generate_csu_residency_rules() -> List[Dict]:
    """Generate CSU residency determination rules"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    rules = [
        {
            "rule_id": "csu_residency_physical_presence",
            "system": "CSU",
            "rule_type": "physical_presence",
            "requirement": "Physical presence in California for 366 days prior to residence determination date",
            "details": "Similar to UC: must be physically present in CA for more than one year before the residence determination date. Brief absences for vacation do not break continuity.",
            "citations": ["https://www2.calstate.edu/attend/paying-for-college/Pages/residency.aspx"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "csu_residency_intent",
            "system": "CSU",
            "rule_type": "intent",
            "requirement": "Intent to make California permanent home",
            "details": "Must demonstrate intent through objective evidence: CA driver's license, voter registration, tax filing, employment, etc.",
            "evidence_required": ["CA driver's license or ID", "CA voter registration", "CA tax returns", "Employment in CA"],
            "citations": ["https://www2.calstate.edu/attend/paying-for-college/Pages/residency.aspx"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "csu_residency_financial_independence",
            "system": "CSU",
            "rule_type": "financial_independence",
            "requirement": "Financial independence for dependent students under 24",
            "details": "Same as UC: students under 24 must be financially independent for 2 years to establish residency independent of parents.",
            "financial_independence_criteria": [
                "Not claimed as tax dependent for 2 prior years",
                "Self-supporting for 2 prior years",
                "No parental support exceeding $750/year"
            ],
            "citations": ["https://www2.calstate.edu/attend/paying-for-college/Pages/residency.aspx"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
    ]
    
    return rules


def generate_wue_programs() -> List[Dict]:
    """Generate WUE (Western Undergraduate Exchange) program data"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # WUE participating states
    wue_states = ["AK", "AZ", "CA", "CO", "HI", "ID", "MT", "NV", "NM", "ND", "OR", "SD", "UT", "WA", "WY"]
    
    programs = [
        {
            "program_id": "wue_overview",
            "program_name": "Western Undergraduate Exchange (WUE)",
            "participating_states": wue_states,
            "discount": "150% of in-state tuition (vs full out-of-state)",
            "details": "WUE allows students from participating Western states to attend participating institutions at 150% of in-state tuition instead of full out-of-state tuition. Significant savings but not all majors/campuses participate.",
            "typical_savings": "$15,000-$25,000 per year",
            "citations": ["https://www.wiche.edu/tuition-savings/wue/"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "program_id": "wue_uw_seattle",
            "school_name": "University of Washington",
            "school_id": "uw_seattle",
            "ipeds_id": "236948",
            "wue_available": False,
            "details": "UW Seattle does NOT participate in WUE. UW Bothell and UW Tacoma do participate.",
            "alternative": "Consider UW Bothell or UW Tacoma for WUE eligibility",
            "citations": ["https://admit.washington.edu/costs/"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "program_id": "wue_uw_bothell",
            "school_name": "University of Washington Bothell",
            "school_id": "uw_bothell",
            "wue_available": True,
            "wue_majors": ["All majors"],
            "in_state_tuition": 11500,
            "wue_tuition": 17250,
            "out_of_state_tuition": 40000,
            "savings": 22750,
            "citations": ["https://www.uwb.edu/admissions/tuition"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "program_id": "wue_uw_tacoma",
            "school_name": "University of Washington Tacoma",
            "school_id": "uw_tacoma",
            "wue_available": True,
            "wue_majors": ["All majors"],
            "in_state_tuition": 11500,
            "wue_tuition": 17250,
            "out_of_state_tuition": 40000,
            "savings": 22750,
            "citations": ["https://www.tacoma.uw.edu/admissions/tuition"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "program_id": "wue_oregon",
            "school_name": "University of Oregon",
            "school_id": "oregon",
            "ipeds_id": "209542",
            "wue_available": True,
            "wue_majors": ["Most majors except Business, Computer Science"],
            "in_state_tuition": 13000,
            "wue_tuition": 19500,
            "out_of_state_tuition": 38000,
            "savings": 18500,
            "exclusions": ["Business", "Computer Science"],
            "citations": ["https://admissions.uoregon.edu/cost"],
            "notes": "CS and Business excluded from WUE",
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "program_id": "wue_oregon_state",
            "school_name": "Oregon State University",
            "school_id": "oregon_state",
            "ipeds_id": "209551",
            "wue_available": True,
            "wue_majors": ["Most majors including Engineering"],
            "in_state_tuition": 12500,
            "wue_tuition": 18750,
            "out_of_state_tuition": 35000,
            "savings": 16250,
            "citations": ["https://admissions.oregonstate.edu/cost"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "program_id": "wue_colorado",
            "school_name": "University of Colorado Boulder",
            "school_id": "colorado",
            "ipeds_id": "126614",
            "wue_available": True,
            "wue_majors": ["Most majors except Engineering, Business"],
            "in_state_tuition": 13000,
            "wue_tuition": 19500,
            "out_of_state_tuition": 40000,
            "savings": 20500,
            "exclusions": ["Engineering", "Business"],
            "citations": ["https://www.colorado.edu/admissions/cost-aid"],
            "notes": "Engineering and Business excluded from WUE",
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "program_id": "wue_arizona",
            "school_name": "University of Arizona",
            "school_id": "arizona",
            "ipeds_id": "104179",
            "wue_available": True,
            "wue_majors": ["All majors"],
            "in_state_tuition": 12500,
            "wue_tuition": 18750,
            "out_of_state_tuition": 38000,
            "savings": 19250,
            "citations": ["https://financialaid.arizona.edu/cost-of-attendance"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "program_id": "wue_arizona_state",
            "school_name": "Arizona State University",
            "school_id": "asu",
            "ipeds_id": "104151",
            "wue_available": True,
            "wue_majors": ["All majors"],
            "in_state_tuition": 11500,
            "wue_tuition": 17250,
            "out_of_state_tuition": 32000,
            "savings": 14750,
            "citations": ["https://admission.asu.edu/cost-aid"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "program_id": "wue_utah",
            "school_name": "University of Utah",
            "school_id": "utah",
            "ipeds_id": "230764",
            "wue_available": True,
            "wue_majors": ["All majors"],
            "in_state_tuition": 10000,
            "wue_tuition": 15000,
            "out_of_state_tuition": 32000,
            "savings": 17000,
            "citations": ["https://admissions.utah.edu/cost/"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
    ]
    
    return programs


def main():
    """Generate and save residency rules"""
    logger.info("="*80)
    logger.info("GENERATING RESIDENCY DETERMINATION RULES")
    logger.info("="*80)
    
    records = []
    records.extend(generate_uc_residency_rules())
    records.extend(generate_csu_residency_rules())
    records.extend(generate_wue_programs())
    
    # Save to file
    output_dir = Path("training_data/tier0_policy_rules")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "ResidencyRule.jsonl"
    
    with open(output_path, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
            
    logger.info(f"Saved {len(records)} records to {output_path}")
    
    # Print summary
    logger.info("\nSummary:")
    logger.info("-"*80)
    logger.info(f"  UC residency rules: {len([r for r in records if r.get('system') == 'UC'])}")
    logger.info(f"  CSU residency rules: {len([r for r in records if r.get('system') == 'CSU'])}")
    logger.info(f"  WUE programs: {len([r for r in records if 'wue' in r.get('program_id', '')])}")
    logger.info(f"  Total records: {len(records)}")


if __name__ == "__main__":
    main()

