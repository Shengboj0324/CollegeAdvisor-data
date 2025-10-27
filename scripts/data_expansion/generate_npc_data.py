#!/usr/bin/env python3
"""
Generate NPC (Net Price Calculator) Data
200+ scenarios across 40 schools with canonical family profiles
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add parent directory to path for calculator import
sys.path.append(str(Path(__file__).parent.parent.parent / "rag_system"))
from calculators import SAICalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Top 40 schools for NPC data
NPC_SCHOOLS = [
    {"id": "mit", "name": "Massachusetts Institute of Technology", "ipeds": "166683", "meets_full_need": True, "need_blind": True},
    {"id": "harvard", "name": "Harvard University", "ipeds": "166027", "meets_full_need": True, "need_blind": True},
    {"id": "stanford", "name": "Stanford University", "ipeds": "243744", "meets_full_need": True, "need_blind": True},
    {"id": "yale", "name": "Yale University", "ipeds": "130794", "meets_full_need": True, "need_blind": True},
    {"id": "princeton", "name": "Princeton University", "ipeds": "186131", "meets_full_need": True, "need_blind": True},
    {"id": "caltech", "name": "California Institute of Technology", "ipeds": "110404", "meets_full_need": True, "need_blind": True},
    {"id": "columbia", "name": "Columbia University", "ipeds": "190150", "meets_full_need": True, "need_blind": True},
    {"id": "penn", "name": "University of Pennsylvania", "ipeds": "215062", "meets_full_need": True, "need_blind": True},
    {"id": "brown", "name": "Brown University", "ipeds": "217156", "meets_full_need": True, "need_blind": True},
    {"id": "dartmouth", "name": "Dartmouth College", "ipeds": "182670", "meets_full_need": True, "need_blind": True},
    {"id": "cornell", "name": "Cornell University", "ipeds": "190415", "meets_full_need": True, "need_blind": True},
    {"id": "duke", "name": "Duke University", "ipeds": "198419", "meets_full_need": True, "need_blind": True},
    {"id": "northwestern", "name": "Northwestern University", "ipeds": "147767", "meets_full_need": True, "need_blind": True},
    {"id": "uchicago", "name": "University of Chicago", "ipeds": "144050", "meets_full_need": True, "need_blind": True},
    {"id": "jhu", "name": "Johns Hopkins University", "ipeds": "162928", "meets_full_need": True, "need_blind": True},
    {"id": "rice", "name": "Rice University", "ipeds": "227757", "meets_full_need": True, "need_blind": True},
    {"id": "vanderbilt", "name": "Vanderbilt University", "ipeds": "221999", "meets_full_need": True, "need_blind": True},
    {"id": "wustl", "name": "Washington University in St. Louis", "ipeds": "179867", "meets_full_need": True, "need_blind": True},
    {"id": "notre_dame", "name": "University of Notre Dame", "ipeds": "152080", "meets_full_need": True, "need_blind": True},
    {"id": "emory", "name": "Emory University", "ipeds": "139658", "meets_full_need": True, "need_blind": True},
    {"id": "cmu", "name": "Carnegie Mellon University", "ipeds": "211440", "meets_full_need": True, "need_blind": False},
    {"id": "georgetown", "name": "Georgetown University", "ipeds": "131496", "meets_full_need": True, "need_blind": False},
    {"id": "usc", "name": "University of Southern California", "ipeds": "123961", "meets_full_need": True, "need_blind": False},
    {"id": "nyu", "name": "New York University", "ipeds": "193900", "meets_full_need": False, "need_blind": False},
    {"id": "tufts", "name": "Tufts University", "ipeds": "168148", "meets_full_need": True, "need_blind": True},
    {"id": "bc", "name": "Boston College", "ipeds": "164988", "meets_full_need": True, "need_blind": False},
    {"id": "umich", "name": "University of Michigan", "ipeds": "170976", "meets_full_need": True, "need_blind": False},
    {"id": "uva", "name": "University of Virginia", "ipeds": "234076", "meets_full_need": True, "need_blind": False},
    {"id": "unc", "name": "University of North Carolina at Chapel Hill", "ipeds": "199120", "meets_full_need": True, "need_blind": False},
    {"id": "gatech", "name": "Georgia Institute of Technology", "ipeds": "139755", "meets_full_need": False, "need_blind": True},
    {"id": "berkeley", "name": "University of California, Berkeley", "ipeds": "110635", "meets_full_need": False, "need_blind": True},
    {"id": "ucla", "name": "University of California, Los Angeles", "ipeds": "110662", "meets_full_need": False, "need_blind": True},
    {"id": "ucsd", "name": "University of California, San Diego", "ipeds": "110680", "meets_full_need": False, "need_blind": True},
    {"id": "ucsb", "name": "University of California, Santa Barbara", "ipeds": "110705", "meets_full_need": False, "need_blind": True},
    {"id": "uci", "name": "University of California, Irvine", "ipeds": "110653", "meets_full_need": False, "need_blind": True},
    {"id": "ucd", "name": "University of California, Davis", "ipeds": "110644", "meets_full_need": False, "need_blind": True},
    {"id": "uw", "name": "University of Washington", "ipeds": "236948", "meets_full_need": False, "need_blind": True},
    {"id": "uiuc", "name": "University of Illinois Urbana-Champaign", "ipeds": "145637", "meets_full_need": False, "need_blind": True},
    {"id": "wisc", "name": "University of Wisconsin-Madison", "ipeds": "240444", "meets_full_need": False, "need_blind": True},
    {"id": "purdue", "name": "Purdue University", "ipeds": "243780", "meets_full_need": False, "need_blind": True},
]


# Canonical family scenarios (6 scenarios per school)
CANONICAL_SCENARIOS = [
    {
        "id": "low_income_simple",
        "description": "Low income, simple assets",
        "agi": 50000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 5000, "529": 0},
        "student_assets": {"savings": 1000},
        "parent_marital_status": "married"
    },
    {
        "id": "middle_income_simple",
        "description": "Middle income, simple assets",
        "agi": 80000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 20000, "529": 15000},
        "student_assets": {"savings": 3000},
        "parent_marital_status": "married"
    },
    {
        "id": "upper_middle_simple",
        "description": "Upper middle income, simple assets",
        "agi": 120000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 50000, "529": 40000},
        "student_assets": {"savings": 5000},
        "parent_marital_status": "married"
    },
    {
        "id": "high_income_complex",
        "description": "High income with business equity and UTMA",
        "agi": 165000,
        "household": 5,
        "students_in_college": 3,
        "assets": {"savings": 25000, "529": 40000, "utma": 70000},
        "student_assets": {"savings": 5000},
        "parent_marital_status": "married"
    },
    {
        "id": "very_high_income",
        "description": "Very high income, substantial assets",
        "agi": 200000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 100000, "529": 80000, "investments": 50000},
        "student_assets": {"savings": 10000},
        "parent_marital_status": "married"
    },
    {
        "id": "divorced_parents",
        "description": "Divorced parents, custodial parent remarried",
        "agi": 140000,  # Custodial + stepparent
        "household": 4,
        "students_in_college": 2,
        "assets": {"savings": 50000, "529": 30000},
        "student_assets": {"savings": 2000},
        "parent_marital_status": "married"
    },
]


# Estimated grant formulas by school type
def estimate_grant(school_id: str, sai: int, coa: int, meets_full_need: bool) -> Dict:
    """
    Estimate grant aid based on school policy
    This is a simplified model - actual NPCs are more complex
    """
    need = max(0, coa - sai)
    
    if meets_full_need:
        # Schools that meet 100% of need
        grant = need
        loan = 5500  # Federal student loan
        work_study = 2500
        net_price = sai + loan + work_study
    else:
        # Schools that don't meet full need
        # Typically meet 70-90% of need
        grant = int(need * 0.80)
        loan = 5500
        work_study = 2000
        gap = need - grant
        net_price = sai + gap + loan + work_study
        
    return {
        "grant": grant,
        "scholarship": 0,  # Merit scholarships separate
        "loan": loan,
        "work_study": work_study,
        "net_price": net_price,
        "need": need,
        "gap": max(0, need - grant)
    }


# COA data for schools
COA_DATA = {
    "mit": 82246,
    "harvard": 80424,
    "stanford": 87071,
    "yale": 83880,
    "princeton": 79540,
    "caltech": 84270,
    "columbia": 89680,
    "penn": 87948,
    "brown": 85566,
    "dartmouth": 84012,
    "cornell": 84568,
    "duke": 84517,
    "northwestern": 86934,
    "uchicago": 87963,
    "jhu": 84410,
    "rice": 72950,
    "vanderbilt": 83096,
    "wustl": 84248,
    "notre_dame": 81693,
    "emory": 79532,
    "cmu": 83494,
    "georgetown": 84896,
    "usc": 87256,
    "nyu": 86248,
    "tufts": 84270,
    "bc": 82296,
    "umich": 76000,  # In-state
    "uva": 72000,  # In-state
    "unc": 68000,  # In-state
    "gatech": 32000,  # In-state
    "berkeley": 38000,  # In-state
    "ucla": 38000,  # In-state
    "ucsd": 37000,  # In-state
    "ucsb": 37000,  # In-state
    "uci": 37000,  # In-state
    "ucd": 37000,  # In-state
    "uw": 35000,  # In-state
    "uiuc": 36000,  # In-state
    "wisc": 32000,  # In-state
    "purdue": 28000,  # In-state
}


def generate_npc_data() -> List[Dict]:
    """Generate NPC data for all schools and scenarios"""
    records = []
    today = datetime.now().strftime("%Y-%m-%d")
    sai_calc = SAICalculator()
    
    for school in NPC_SCHOOLS:
        school_id = school["id"]
        coa = COA_DATA.get(school_id, 80000)  # Default COA
        
        for scenario in CANONICAL_SCENARIOS:
            # Calculate SAI
            sai_result = sai_calc.calculate_from_scenario(scenario)
            sai = sai_result.sai
            
            # Estimate grant aid
            aid_estimate = estimate_grant(
                school_id,
                sai,
                coa,
                school["meets_full_need"]
            )
            
            # Create record
            record = {
                "school_id": school_id,
                "school_name": school["name"],
                "ipeds_id": school["ipeds"],
                "scenario_id": scenario["id"],
                "scenario_description": scenario["description"],
                "inputs": {
                    "agi": scenario["agi"],
                    "household": scenario["household"],
                    "students_in_college": scenario["students_in_college"],
                    "assets": scenario["assets"],
                    "student_assets": scenario["student_assets"],
                    "parent_marital_status": scenario["parent_marital_status"]
                },
                "outputs": {
                    "sai": sai,
                    "coa": coa,
                    "grant": aid_estimate["grant"],
                    "scholarship": aid_estimate["scholarship"],
                    "loan": aid_estimate["loan"],
                    "work_study": aid_estimate["work_study"],
                    "net_price": aid_estimate["net_price"],
                    "need": aid_estimate["need"],
                    "gap": aid_estimate["gap"]
                },
                "run_date": today,
                "url": f"https://{school_id}.edu/npc",
                "notes": f"Estimated NPC result for {scenario['description']}. Actual results may vary. Use official NPC for accurate estimates.",
                "meets_full_need": school["meets_full_need"],
                "need_blind": school["need_blind"]
            }
            
            records.append(record)
            
    logger.info(f"Generated {len(records)} NPC records")
    return records


def main():
    """Generate and save NPC data"""
    logger.info("="*80)
    logger.info("GENERATING NPC DATA FOR 40 SCHOOLS × 6 SCENARIOS")
    logger.info("="*80)
    
    records = generate_npc_data()
    
    # Save to file
    output_path = "training_data/tier1_costs/NPCResult.jsonl"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
            
    logger.info(f"Saved {len(records)} records to {output_path}")
    
    # Print summary
    logger.info("\nSummary:")
    logger.info("-"*80)
    logger.info(f"  Schools: {len(NPC_SCHOOLS)}")
    logger.info(f"  Scenarios per school: {len(CANONICAL_SCENARIOS)}")
    logger.info(f"  Total records: {len(records)}")
    logger.info(f"  Schools meeting full need: {sum(1 for s in NPC_SCHOOLS if s['meets_full_need'])}")
    logger.info(f"  Need-blind schools: {sum(1 for s in NPC_SCHOOLS if s['need_blind'])}")


if __name__ == "__main__":
    main()

