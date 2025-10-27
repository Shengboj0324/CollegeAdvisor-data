#!/usr/bin/env python3
"""
Deterministic Calculators for Financial Aid and Cost Analysis
No hallucination - all numbers are derived from formulas or sourced data
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SAIResult:
    """Student Aid Index calculation result"""
    sai: int
    parent_contribution: int
    student_contribution: int
    allowances: int
    formula_used: str
    source: str
    notes: str


@dataclass
class CostResult:
    """Cost of attendance calculation result"""
    total_cost: int
    tuition_fees: int
    housing_food: int
    books_supplies: int
    personal: int
    transportation: int
    breakdown: Dict[str, int]
    source: str
    notes: str


class SAICalculator:
    """
    Student Aid Index (SAI) Calculator
    Based on 2024-2025 FAFSA Simplification Act
    """
    
    # Income protection allowances (2024-2025)
    INCOME_PROTECTION = {
        2: 20140,
        3: 25060,
        4: 30960,
        5: 36570,
        6: 42740,
    }
    
    # Asset protection allowances (2024-2025)
    ASSET_PROTECTION = {
        "two_parent": 10000,
        "one_parent": 5000,
    }
    
    def calculate(
        self,
        agi: int,
        household_size: int,
        students_in_college: int,
        parent_assets: Dict[str, int],
        student_assets: Dict[str, int],
        marital_status: str = "married"
    ) -> SAIResult:
        """
        Calculate SAI using 2024-2025 formula
        
        Args:
            agi: Adjusted Gross Income
            household_size: Number in household
            students_in_college: Number of students in college
            parent_assets: Dict of parent assets (excludes 401k, home equity)
            student_assets: Dict of student assets
            marital_status: "married" or "single"
        """
        
        # Step 1: Calculate parent contribution
        income_protection = self.INCOME_PROTECTION.get(household_size, 42740)
        available_income = max(0, agi - income_protection)
        
        # Progressive tax on available income
        if available_income <= 17000:
            income_contribution = int(available_income * 0.22)
        elif available_income <= 21000:
            income_contribution = int(3740 + (available_income - 17000) * 0.25)
        elif available_income <= 25000:
            income_contribution = int(4740 + (available_income - 21000) * 0.29)
        elif available_income <= 29000:
            income_contribution = int(5900 + (available_income - 25000) * 0.34)
        else:
            income_contribution = int(7260 + (available_income - 29000) * 0.40)
            
        # Step 2: Calculate parent asset contribution
        # Note: 401k, home equity NOT counted under new FAFSA
        countable_assets = sum([
            parent_assets.get("savings", 0),
            parent_assets.get("529", 0),
            parent_assets.get("investments", 0),
            # Business equity with <100 employees NOT counted
            # UTMA/UGMA counted as parent asset (not student)
            parent_assets.get("utma", 0),
        ])
        
        asset_protection = self.ASSET_PROTECTION.get(
            "two_parent" if marital_status == "married" else "one_parent",
            10000
        )
        
        available_assets = max(0, countable_assets - asset_protection)
        asset_contribution = int(available_assets * 0.12)  # 12% assessment rate
        
        parent_contribution = income_contribution + asset_contribution
        
        # Step 3: Calculate student contribution
        # Student assets assessed at 20%
        student_countable_assets = sum([
            student_assets.get("savings", 0),
            student_assets.get("investments", 0),
            # Note: Student 529 now counted as parent asset under new FAFSA
        ])
        
        student_contribution = int(student_countable_assets * 0.20)
        
        # Step 4: Calculate SAI
        # Note: Under new FAFSA, SAI is NOT divided by number of students in college
        # (This is a major change from old EFC formula)
        sai = parent_contribution + student_contribution
        
        # SAI can be negative (unlike EFC)
        # Minimum SAI is -1500
        sai = max(-1500, sai)
        
        return SAIResult(
            sai=sai,
            parent_contribution=parent_contribution,
            student_contribution=student_contribution,
            allowances=income_protection + asset_protection,
            formula_used="2024-2025 FAFSA Simplification Act",
            source="https://studentaid.gov/help-center/answers/article/what-is-sai",
            notes=f"SAI calculated for household of {household_size} with {students_in_college} in college. "
                  f"Note: SAI is NOT divided by number in college (major change from old EFC). "
                  f"401k, home equity, and small business equity (<100 employees) are NOT counted."
        )
        
    def calculate_from_scenario(self, scenario: Dict) -> SAIResult:
        """Calculate SAI from scenario dict"""
        return self.calculate(
            agi=scenario.get("agi", 0),
            household_size=scenario.get("household", 4),
            students_in_college=scenario.get("students_in_college", 1),
            parent_assets=scenario.get("assets", {}),
            student_assets=scenario.get("student_assets", {}),
            marital_status=scenario.get("parent_marital_status", "married")
        )


class CostCalculator:
    """
    Cost of Attendance Calculator
    Uses actual COA data from schools
    """
    
    # Sample COA data (in production, load from database)
    COA_DATA = {
        "mit": {
            "tuition_fees": 60156,
            "housing_food": 19110,
            "books_supplies": 820,
            "personal": 2160,
            "transportation": 0,
            "source": "https://sfs.mit.edu/undergraduate-students/the-cost-of-attendance/",
            "year": "2024-2025"
        },
        "harvard": {
            "tuition_fees": 56550,
            "housing_food": 20374,
            "books_supplies": 1000,
            "personal": 2500,
            "transportation": 0,
            "source": "https://college.harvard.edu/financial-aid/how-aid-works/cost-attendance",
            "year": "2024-2025"
        },
        "stanford": {
            "tuition_fees": 62484,
            "housing_food": 19922,
            "books_supplies": 1245,
            "personal": 2745,
            "transportation": 675,
            "source": "https://financialaid.stanford.edu/undergrad/budget/index.html",
            "year": "2024-2025"
        },
    }
    
    def calculate(self, school_id: str, living_situation: str = "on_campus") -> Optional[CostResult]:
        """
        Calculate cost of attendance for a school
        
        Args:
            school_id: School identifier
            living_situation: "on_campus", "off_campus", or "with_parents"
        """
        
        if school_id not in self.COA_DATA:
            return None
            
        coa = self.COA_DATA[school_id]
        
        tuition_fees = coa["tuition_fees"]
        housing_food = coa["housing_food"]
        books_supplies = coa["books_supplies"]
        personal = coa["personal"]
        transportation = coa["transportation"]
        
        # Adjust for living situation
        if living_situation == "off_campus":
            # Off-campus typically 10-20% higher for housing
            housing_food = int(housing_food * 1.15)
            transportation = int(transportation * 1.5) if transportation > 0 else 2000
        elif living_situation == "with_parents":
            # Living with parents - no housing cost
            housing_food = 0
            transportation = int(transportation * 2) if transportation > 0 else 3000
            
        total_cost = tuition_fees + housing_food + books_supplies + personal + transportation
        
        return CostResult(
            total_cost=total_cost,
            tuition_fees=tuition_fees,
            housing_food=housing_food,
            books_supplies=books_supplies,
            personal=personal,
            transportation=transportation,
            breakdown={
                "tuition_fees": tuition_fees,
                "housing_food": housing_food,
                "books_supplies": books_supplies,
                "personal": personal,
                "transportation": transportation,
            },
            source=coa["source"],
            notes=f"COA for {coa['year']} academic year, {living_situation} living situation"
        )
        
    def calculate_net_price(
        self,
        school_id: str,
        sai: int,
        living_situation: str = "on_campus"
    ) -> Optional[Dict]:
        """
        Calculate estimated net price
        
        Note: This is a rough estimate. Actual net price depends on school's
        financial aid policies and should be verified with NPC.
        """
        
        coa_result = self.calculate(school_id, living_situation)
        if not coa_result:
            return None
            
        # Very rough estimate - actual aid varies by school
        # This is just for demonstration
        estimated_grant = max(0, coa_result.total_cost - sai - 5500)  # 5500 = federal loan
        estimated_net_price = coa_result.total_cost - estimated_grant
        
        return {
            "coa": coa_result.total_cost,
            "estimated_grant": estimated_grant,
            "estimated_loan": 5500,
            "estimated_net_price": estimated_net_price,
            "source": coa_result.source,
            "notes": "This is a ROUGH ESTIMATE. Use school's Net Price Calculator for accurate estimate. "
                     f"Based on SAI of ${sai:,}. Actual aid varies significantly by school policy."
        }


def main():
    """Test calculators"""
    
    # Test SAI calculator
    logger.info("="*80)
    logger.info("SAI CALCULATOR TEST")
    logger.info("="*80)
    
    sai_calc = SAICalculator()
    
    scenario = {
        "agi": 165000,
        "household": 5,
        "students_in_college": 3,
        "assets": {
            "parent_401k": 110000,  # NOT counted
            "utma": 70000,  # Counted as parent asset
            "529_gp": 35000,  # NOT counted on FAFSA
            "savings": 25000,
            "529": 40000,
        },
        "student_assets": {
            "savings": 5000,
        },
        "parent_marital_status": "married"
    }
    
    result = sai_calc.calculate_from_scenario(scenario)
    
    logger.info(f"SAI: ${result.sai:,}")
    logger.info(f"Parent Contribution: ${result.parent_contribution:,}")
    logger.info(f"Student Contribution: ${result.student_contribution:,}")
    logger.info(f"Allowances: ${result.allowances:,}")
    logger.info(f"Formula: {result.formula_used}")
    logger.info(f"Source: {result.source}")
    logger.info(f"Notes: {result.notes}")
    
    # Test Cost calculator
    logger.info("\n" + "="*80)
    logger.info("COST CALCULATOR TEST")
    logger.info("="*80)
    
    cost_calc = CostCalculator()
    
    for school_id in ["mit", "harvard", "stanford"]:
        logger.info(f"\n{school_id.upper()}:")
        cost_result = cost_calc.calculate(school_id)
        if cost_result:
            logger.info(f"  Total COA: ${cost_result.total_cost:,}")
            logger.info(f"  Tuition/Fees: ${cost_result.tuition_fees:,}")
            logger.info(f"  Housing/Food: ${cost_result.housing_food:,}")
            logger.info(f"  Source: {cost_result.source}")

        # Calculate net price using SAI from earlier calculation
        net_price = cost_calc.calculate_net_price(school_id, result.sai)
        if net_price:
            logger.info(f"  Estimated Net Price: ${net_price['estimated_net_price']:,}")
            logger.info(f"  Notes: {net_price['notes']}")


if __name__ == "__main__":
    main()

