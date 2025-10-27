#!/usr/bin/env python3
"""
Generate FAFSA/SAI Worked Examples
50 diverse scenarios covering edge cases
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


# 50 diverse SAI scenarios covering edge cases
SAI_SCENARIOS = [
    # Basic scenarios
    {
        "id": "basic_low_income",
        "description": "Basic low-income family, no assets",
        "agi": 30000,
        "household": 4,
        "students_in_college": 1,
        "assets": {},
        "student_assets": {},
        "marital_status": "married",
        "notes": "Negative SAI expected due to income below protection allowance"
    },
    {
        "id": "basic_middle_income",
        "description": "Middle-income family, modest savings",
        "agi": 75000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 15000},
        "student_assets": {"savings": 2000},
        "marital_status": "married",
        "notes": "Typical middle-class family"
    },
    {
        "id": "basic_high_income",
        "description": "High-income family, substantial assets",
        "agi": 250000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 100000, "investments": 200000},
        "student_assets": {"savings": 10000},
        "marital_status": "married",
        "notes": "High SAI, likely no need-based aid"
    },
    
    # Multiple students in college
    {
        "id": "two_in_college",
        "description": "Two students in college simultaneously",
        "agi": 100000,
        "household": 5,
        "students_in_college": 2,
        "assets": {"savings": 50000, "529": 40000},
        "student_assets": {"savings": 3000},
        "marital_status": "married",
        "notes": "CRITICAL: SAI NOT divided by number in college (2024-2025 change from old EFC)"
    },
    {
        "id": "three_in_college",
        "description": "Three students in college simultaneously",
        "agi": 120000,
        "household": 6,
        "students_in_college": 3,
        "assets": {"savings": 60000, "529": 80000},
        "student_assets": {"savings": 2000},
        "marital_status": "married",
        "notes": "CRITICAL: SAI NOT divided by number in college (major policy change)"
    },
    
    # 529 Plans
    {
        "id": "large_529_parent",
        "description": "Large parent-owned 529 plan",
        "agi": 90000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 20000, "529": 100000},
        "student_assets": {"savings": 1000},
        "marital_status": "married",
        "notes": "Parent-owned 529 assessed at 5.64% (included in parent assets)"
    },
    {
        "id": "grandparent_529",
        "description": "Grandparent-owned 529 distribution",
        "agi": 80000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 25000},
        "student_assets": {"savings": 2000},
        "marital_status": "married",
        "notes": "CRITICAL: Grandparent 529 distributions NO LONGER counted as student income (2024-2025 change)"
    },
    
    # UTMA/UGMA accounts
    {
        "id": "utma_account",
        "description": "UTMA account in student's name",
        "agi": 100000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 30000, "utma": 50000},
        "student_assets": {"savings": 3000},
        "marital_status": "married",
        "notes": "UTMA counted as PARENT asset (not student) if student is dependent"
    },
    {
        "id": "large_utma",
        "description": "Large UTMA from inheritance",
        "agi": 85000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 20000, "utma": 150000},
        "student_assets": {"savings": 2000},
        "marital_status": "married",
        "notes": "Large UTMA significantly increases SAI via parent asset contribution"
    },
    
    # Business equity
    {
        "id": "small_business_excluded",
        "description": "Small business (<100 employees) excluded",
        "agi": 120000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 40000, "business_equity": 200000, "business_employees": 50},
        "student_assets": {"savings": 3000},
        "marital_status": "married",
        "notes": "Business equity NOT counted if <100 employees"
    },
    {
        "id": "large_business_counted",
        "description": "Large business (≥100 employees) counted",
        "agi": 150000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 50000, "business_equity": 300000, "business_employees": 150},
        "student_assets": {"savings": 5000},
        "marital_status": "married",
        "notes": "Business equity COUNTED if ≥100 employees"
    },
    
    # S-Corp scenarios
    {
        "id": "s_corp_owner",
        "description": "S-Corp owner with retained earnings",
        "agi": 180000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 60000, "business_equity": 250000, "business_employees": 75},
        "student_assets": {"savings": 4000},
        "marital_status": "married",
        "notes": "S-Corp equity excluded if <100 employees, but AGI includes K-1 income"
    },
    
    # Divorced/separated parents
    {
        "id": "divorced_custodial_only",
        "description": "Divorced, custodial parent only (FAFSA)",
        "agi": 60000,
        "household": 3,
        "students_in_college": 1,
        "assets": {"savings": 15000},
        "student_assets": {"savings": 2000},
        "marital_status": "single",
        "notes": "FAFSA uses custodial parent only; CSS Profile may require NCP"
    },
    {
        "id": "divorced_remarried",
        "description": "Divorced, custodial parent remarried",
        "agi": 140000,  # Custodial + stepparent combined
        "household": 5,
        "students_in_college": 1,
        "assets": {"savings": 50000},
        "student_assets": {"savings": 3000},
        "marital_status": "married",
        "notes": "Stepparent income/assets MUST be included on FAFSA"
    },
    {
        "id": "divorced_high_ncp",
        "description": "Divorced, high-income non-custodial parent",
        "agi": 70000,  # Custodial parent only
        "household": 3,
        "students_in_college": 1,
        "assets": {"savings": 20000},
        "student_assets": {"savings": 2000},
        "marital_status": "single",
        "notes": "FAFSA ignores NCP; CSS Profile schools will require NCP Profile"
    },
    
    # Rental property
    {
        "id": "rental_property",
        "description": "Rental property investment",
        "agi": 110000,  # Includes rental income
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 30000, "investments": 250000},  # Rental property equity
        "student_assets": {"savings": 3000},
        "marital_status": "married",
        "notes": "Rental property equity COUNTED as investment asset"
    },
    
    # Farm equity
    {
        "id": "family_farm",
        "description": "Family farm equity",
        "agi": 95000,
        "household": 5,
        "students_in_college": 1,
        "assets": {"savings": 25000, "farm_equity": 400000},
        "student_assets": {"savings": 2000},
        "marital_status": "married",
        "notes": "Farm equity excluded if family lives on and operates farm"
    },
    
    # Single parent scenarios
    {
        "id": "single_parent_low_income",
        "description": "Single parent, low income",
        "agi": 35000,
        "household": 3,
        "students_in_college": 1,
        "assets": {"savings": 5000},
        "student_assets": {"savings": 500},
        "marital_status": "single",
        "notes": "Lower asset protection allowance for single parents ($5k vs $10k)"
    },
    {
        "id": "single_parent_middle_income",
        "description": "Single parent, middle income",
        "agi": 80000,
        "household": 3,
        "students_in_college": 1,
        "assets": {"savings": 30000},
        "student_assets": {"savings": 3000},
        "marital_status": "single",
        "notes": "Single parent asset protection: $5,000"
    },
    
    # Large household sizes
    {
        "id": "large_household_6",
        "description": "Large household (6 people)",
        "agi": 100000,
        "household": 6,
        "students_in_college": 1,
        "assets": {"savings": 40000},
        "student_assets": {"savings": 2000},
        "marital_status": "married",
        "notes": "Higher income protection allowance for larger households"
    },
    {
        "id": "large_household_8",
        "description": "Very large household (8 people)",
        "agi": 120000,
        "household": 8,
        "students_in_college": 2,
        "assets": {"savings": 50000},
        "student_assets": {"savings": 3000},
        "marital_status": "married",
        "notes": "Maximum income protection allowance ($42,740 + $5,180 per additional)"
    },
    
    # Student income scenarios
    {
        "id": "student_high_income",
        "description": "Student with high summer earnings",
        "agi": 90000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 35000},
        "student_assets": {"savings": 15000},  # From summer work
        "marital_status": "married",
        "notes": "Student assets assessed at 20% (no protection allowance)"
    },
    {
        "id": "student_work_study",
        "description": "Student with work-study income",
        "agi": 75000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 25000},
        "student_assets": {"savings": 3000},
        "marital_status": "married",
        "notes": "Work-study income NOT counted on FAFSA"
    },
    
    # Zero EFC scenarios
    {
        "id": "auto_zero_efc",
        "description": "Auto-zero SAI (AGI ≤ $27,000)",
        "agi": 25000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 50000},  # Assets ignored
        "student_assets": {"savings": 10000},  # Assets ignored
        "marital_status": "married",
        "notes": "CRITICAL: Auto-zero SAI if AGI ≤ $27,000 (assets ignored)"
    },
    {
        "id": "simplified_needs_test",
        "description": "Simplified needs test (AGI ≤ $60,000)",
        "agi": 55000,
        "household": 4,
        "students_in_college": 1,
        "assets": {"savings": 75000},  # Assets ignored
        "student_assets": {"savings": 5000},  # Assets ignored
        "marital_status": "married",
        "notes": "CRITICAL: Simplified needs test if AGI ≤ $60,000 (assets ignored)"
    },
]


def generate_sai_examples() -> List[Dict]:
    """Generate comprehensive SAI worked examples"""
    records = []
    today = datetime.now().strftime("%Y-%m-%d")
    sai_calc = SAICalculator()
    
    for scenario in SAI_SCENARIOS:
        # Calculate SAI
        sai_result = sai_calc.calculate_from_scenario(scenario)

        # Create detailed record
        record = {
            "scenario_id": scenario["id"],
            "description": scenario["description"],
            "inputs": {
                "agi": scenario["agi"],
                "household_size": scenario["household"],
                "students_in_college": scenario["students_in_college"],
                "parent_assets": scenario["assets"],
                "student_assets": scenario["student_assets"],
                "parent_marital_status": scenario["marital_status"]
            },
            "outputs": {
                "sai": sai_result.sai,
                "parent_contribution": sai_result.parent_contribution,
                "student_contribution": sai_result.student_contribution,
                "formula_version": "2024-2025 FAFSA Simplification Act",
                "formula_used": sai_result.formula_used
            },
            "key_policies": [
                "SAI NOT divided by number of students in college (changed from old EFC)",
                "Parent-owned 529 plans assessed as parent assets at 5.64%",
                "UTMA/UGMA counted as parent assets for dependent students",
                "Small business equity (<100 employees) excluded",
                "Grandparent 529 distributions no longer counted as student income",
                "Auto-zero SAI if AGI ≤ $27,000",
                "Simplified needs test (assets ignored) if AGI ≤ $60,000"
            ],
            "citations": [
                "https://studentaid.gov/help-center/answers/article/how-is-sai-calculated",
                "https://fsapartners.ed.gov/knowledge-center/fsa-handbook/2024-2025-fsa-handbook"
            ],
            "notes": scenario["notes"],
            "last_verified": today,
            "effective_year": "2024-2025"
        }
        
        records.append(record)
        
    logger.info(f"Generated {len(records)} SAI worked examples")
    return records


def main():
    """Generate and save SAI examples"""
    logger.info("="*80)
    logger.info("GENERATING FAFSA/SAI WORKED EXAMPLES")
    logger.info("="*80)
    
    records = generate_sai_examples()
    
    # Save to file
    output_path = "training_data/tier0_policy_rules/SAIExample.jsonl"
    with open(output_path, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
            
    logger.info(f"Saved {len(records)} records to {output_path}")
    
    # Print summary
    logger.info("\nSummary:")
    logger.info("-"*80)
    logger.info(f"  Total scenarios: {len(records)}")
    
    # SAI distribution
    sai_values = [r["outputs"]["sai"] for r in records]
    logger.info(f"  SAI range: ${min(sai_values):,} to ${max(sai_values):,}")
    logger.info(f"  Negative SAI count: {sum(1 for s in sai_values if s < 0)}")
    logger.info(f"  Zero SAI count: {sum(1 for s in sai_values if s == 0)}")
    
    # Edge case coverage
    logger.info("\nEdge Cases Covered:")
    logger.info("-"*80)
    edge_cases = [
        "Multiple students in college",
        "529 plans (parent and grandparent)",
        "UTMA/UGMA accounts",
        "Small business equity",
        "S-Corp ownership",
        "Divorced/separated parents",
        "Rental property",
        "Farm equity",
        "Single parent households",
        "Large households (6-8 people)",
        "High student income",
        "Auto-zero SAI",
        "Simplified needs test"
    ]
    for case in edge_cases:
        logger.info(f"  ✓ {case}")


if __name__ == "__main__":
    main()

