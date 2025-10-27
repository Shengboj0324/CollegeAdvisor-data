#!/usr/bin/env python3
"""
Specialized Comparison Generators
Domain-specific comparison table generators for college admissions scenarios
"""

import json
import logging
from typing import Dict, List, Optional, Any
from synthesis_layer import ComparisonTable, ComparisonRow, SynthesisEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinancialAidComparator:
    """Generate financial aid comparison tables"""
    
    def __init__(self, synthesis_engine: SynthesisEngine):
        self.engine = synthesis_engine
    
    def compare_aid_policies(
        self,
        schools: List[Dict],
        scenario: Dict[str, Any]
    ) -> ComparisonTable:
        """
        Compare financial aid policies across schools
        
        Args:
            schools: List of school aid policy records
            scenario: User scenario (income, assets, etc.)
            
        Returns:
            ComparisonTable with aid policy comparison
        """
        attributes = [
            'meets_full_need',
            'home_equity_cap',
            'ncp_waiver_available',
            'outside_scholarship_policy',
            'typical_grant_aid',
            'loan_policy',
            'work_study_requirement'
        ]
        
        return self.engine.generate_comparison_table(
            entities=schools,
            attributes=attributes,
            title="Financial Aid Policy Comparison"
        )
    
    def compare_international_aid(
        self,
        schools: List[Dict]
    ) -> ComparisonTable:
        """Compare international student aid policies"""
        attributes = [
            'need_blind_international',
            'meets_full_need_international',
            'merit_available_international',
            'typical_aid_package',
            'application_deadline'
        ]
        
        return self.engine.generate_comparison_table(
            entities=schools,
            attributes=attributes,
            title="International Student Aid Comparison"
        )


class AdmissionsComparator:
    """Generate admissions comparison tables"""
    
    def __init__(self, synthesis_engine: SynthesisEngine):
        self.engine = synthesis_engine
    
    def compare_cs_admissions(
        self,
        schools: List[Dict]
    ) -> ComparisonTable:
        """Compare CS admissions across schools"""
        attributes = [
            'overall_admit_rate',
            'major_admit_rate',
            'direct_admit',
            'admission_type',
            'minimum_gpa',
            'typical_gpa',
            'notes'
        ]
        
        return self.engine.generate_comparison_table(
            entities=schools,
            attributes=attributes,
            title="Computer Science Admissions Comparison"
        )
    
    def compare_internal_transfer(
        self,
        schools: List[Dict]
    ) -> ComparisonTable:
        """Compare internal transfer rates and requirements"""
        attributes = [
            'major',
            'transfer_rate',
            'minimum_gpa',
            'typical_gpa',
            'screening_gpa',
            'transfer_type',
            'notes'
        ]
        
        return self.engine.generate_comparison_table(
            entities=schools,
            attributes=attributes,
            title="Internal Transfer Comparison"
        )


class ProgramComparator:
    """Generate program comparison tables"""
    
    def __init__(self, synthesis_engine: SynthesisEngine):
        self.engine = synthesis_engine
    
    def compare_bsmd_programs(
        self,
        programs: List[Dict]
    ) -> ComparisonTable:
        """Compare BS/MD programs"""
        attributes = [
            'program_length_years',
            'mcat_required',
            'minimum_gpa',
            'conditional_guarantee',
            'acceptance_rate',
            'total_cost',
            'attrition_rate'
        ]
        
        return self.engine.generate_comparison_table(
            entities=programs,
            attributes=attributes,
            title="BS/MD Program Comparison"
        )
    
    def compare_residency_options(
        self,
        options: List[Dict]
    ) -> ComparisonTable:
        """Compare residency and WUE options"""
        attributes = [
            'system',
            'in_state_tuition',
            'out_of_state_tuition',
            'wue_tuition',
            'wue_available',
            'savings',
            'exclusions'
        ]
        
        return self.engine.generate_comparison_table(
            entities=options,
            attributes=attributes,
            title="Residency & WUE Options Comparison"
        )


class CostComparator:
    """Generate cost comparison tables"""
    
    def __init__(self, synthesis_engine: SynthesisEngine):
        self.engine = synthesis_engine
    
    def compare_net_prices(
        self,
        schools: List[Dict],
        income_bracket: int
    ) -> ComparisonTable:
        """Compare net prices across schools for income bracket"""
        
        # Filter NPC results for income bracket
        filtered = []
        for school in schools:
            family_income = school.get('family_income', 0)
            if abs(family_income - income_bracket) < 20000:  # Within $20k
                filtered.append(school)
        
        attributes = [
            'family_income',
            'expected_family_contribution',
            'total_grant_aid',
            'net_price',
            'loan_amount',
            'work_study'
        ]
        
        return self.engine.generate_comparison_table(
            entities=filtered if filtered else schools,
            attributes=attributes,
            title=f"Net Price Comparison (Income: ${income_bracket:,})"
        )
    
    def compare_four_year_costs(
        self,
        schools: List[Dict],
        scenario: Dict[str, Any]
    ) -> str:
        """Generate 4-year cost projection comparison"""
        
        lines = ["## 4-Year Cost Projection\n"]
        
        for school in schools:
            school_name = school.get('school_name', 'Unknown')
            
            # Extract costs
            tuition = school.get('tuition', 0)
            room_board = school.get('room_board', 0)
            fees = school.get('fees', 0)
            
            # Calculate 4-year total
            annual_cost = tuition + room_board + fees
            four_year_cost = annual_cost * 4
            
            # Apply aid if available
            grant_aid = school.get('total_grant_aid', 0)
            net_annual = annual_cost - grant_aid
            net_four_year = net_annual * 4
            
            lines.append(f"### {school_name}")
            lines.append(f"- **Annual Cost:** ${annual_cost:,}")
            lines.append(f"- **Annual Grant Aid:** ${grant_aid:,}")
            lines.append(f"- **Net Annual Cost:** ${net_annual:,}")
            lines.append(f"- **4-Year Total:** ${net_four_year:,}")
            lines.append("")
        
        return "\n".join(lines)


class DecisionFrameworkGenerator:
    """Generate decision frameworks and trees"""
    
    def __init__(self, synthesis_engine: SynthesisEngine):
        self.engine = synthesis_engine
    
    def generate_cs_admission_framework(
        self,
        schools: List[Dict],
        user_profile: Dict[str, Any]
    ) -> str:
        """Generate decision framework for CS admissions"""
        
        lines = ["## CS Admissions Decision Framework\n"]
        
        # Extract user profile
        gpa = user_profile.get('gpa', 0)
        budget = user_profile.get('budget', 0)
        
        lines.append("### Step 1: Direct Admit vs Pre-Major")
        lines.append("**Question:** Do you want guaranteed CS major access?")
        lines.append("")
        
        # Categorize schools
        direct_admit = [s for s in schools if s.get('direct_admit', False)]
        pre_major = [s for s in schools if not s.get('direct_admit', False)]
        
        lines.append("**Direct Admit Schools (Guaranteed CS):**")
        for school in direct_admit[:5]:
            name = school.get('school_name', 'Unknown')
            rate = school.get('major_admit_rate', 0)
            lines.append(f"- {name}: {rate*100:.1f}% admit rate")
        
        lines.append("\n**Pre-Major Schools (Competitive Internal Transfer):**")
        for school in pre_major[:5]:
            name = school.get('school_name', 'Unknown')
            transfer_rate = school.get('transfer_rate', 0)
            lines.append(f"- {name}: {transfer_rate*100:.1f}% internal transfer rate")
        
        lines.append("\n### Step 2: Selectivity vs Certainty")
        lines.append("**Question:** What is your risk tolerance?")
        lines.append("")
        
        # Categorize by admit rate
        highly_selective = [s for s in schools if s.get('major_admit_rate', 1) < 0.10]
        moderately_selective = [s for s in schools if 0.10 <= s.get('major_admit_rate', 1) < 0.30]
        accessible = [s for s in schools if s.get('major_admit_rate', 1) >= 0.30]
        
        lines.append(f"- **Reach (< 10% admit):** {len(highly_selective)} schools")
        lines.append(f"- **Target (10-30% admit):** {len(moderately_selective)} schools")
        lines.append(f"- **Safety (> 30% admit):** {len(accessible)} schools")
        
        lines.append("\n### Step 3: Cost Optimization")
        lines.append(f"**Your Budget:** ${budget:,}/year")
        lines.append("")
        lines.append("Consider:")
        lines.append("- In-state public universities (lowest cost)")
        lines.append("- Private universities with strong aid (if income < $150k)")
        lines.append("- WUE programs (150% of in-state tuition)")
        
        lines.append("\n### Recommended Strategy:")
        lines.append("1. **2-3 Reach schools** (< 10% admit, direct admit preferred)")
        lines.append("2. **3-4 Target schools** (10-30% admit, mix of direct/pre-major)")
        lines.append("3. **2-3 Safety schools** (> 30% admit, direct admit required)")
        
        return "\n".join(lines)
    
    def generate_financial_aid_framework(
        self,
        schools: List[Dict],
        scenario: Dict[str, Any]
    ) -> str:
        """Generate financial aid decision framework"""
        
        lines = ["## Financial Aid Decision Framework\n"]
        
        # Extract scenario
        income = scenario.get('income', 0)
        assets = scenario.get('assets', 0)
        divorced = scenario.get('divorced_parents', False)
        
        lines.append("### Step 1: Identify Aid-Friendly Schools")
        lines.append("")
        
        # Categorize schools
        meets_full_need = [s for s in schools if s.get('meets_full_need', False)]
        no_loan = [s for s in schools if 'no-loan' in str(s.get('loan_policy', '')).lower()]
        
        lines.append(f"**Schools Meeting Full Need:** {len(meets_full_need)}")
        for school in meets_full_need[:5]:
            name = school.get('school_name', 'Unknown')
            lines.append(f"- {name}")
        
        lines.append(f"\n**No-Loan Schools:** {len(no_loan)}")
        for school in no_loan[:5]:
            name = school.get('school_name', 'Unknown')
            lines.append(f"- {name}")
        
        if divorced:
            lines.append("\n### Step 2: Non-Custodial Parent Waiver")
            lines.append("**Your situation:** Divorced parents")
            lines.append("")
            
            ncp_waiver = [s for s in schools if s.get('ncp_waiver_available', False)]
            lines.append(f"**Schools offering NCP waiver:** {len(ncp_waiver)}")
            for school in ncp_waiver[:5]:
                name = school.get('school_name', 'Unknown')
                lines.append(f"- {name}")
        
        lines.append("\n### Step 3: Home Equity Treatment")
        lines.append(f"**Your income:** ${income:,}")
        lines.append("")
        
        # Schools with favorable home equity treatment
        favorable_he = [s for s in schools if s.get('home_equity_cap')]
        lines.append(f"**Schools capping home equity:** {len(favorable_he)}")
        for school in favorable_he[:5]:
            name = school.get('school_name', 'Unknown')
            cap = school.get('home_equity_cap', 'Unknown')
            lines.append(f"- {name}: {cap}")
        
        lines.append("\n### Recommended Strategy:")
        lines.append("1. Apply to schools meeting full need")
        lines.append("2. Prioritize schools with NCP waiver (if applicable)")
        lines.append("3. Target schools with favorable home equity treatment")
        lines.append("4. Run NPCs for all schools to compare offers")
        lines.append("5. Apply to 8-12 schools to maximize aid comparison")
        
        return "\n".join(lines)
    
    def generate_international_student_framework(
        self,
        schools: List[Dict],
        budget: int
    ) -> str:
        """Generate framework for international students"""
        
        lines = ["## International Student Decision Framework\n"]
        
        lines.append(f"**Your Budget:** ${budget:,}/year")
        lines.append("")
        
        # Categorize schools
        need_blind = [s for s in schools if s.get('need_blind_international', False)]
        meets_need = [s for s in schools if s.get('meets_full_need_international', False)]
        merit = [s for s in schools if s.get('merit_available_international', False)]
        
        lines.append("### Step 1: Need-Blind vs Need-Aware")
        lines.append("")
        lines.append(f"**Need-Blind for Internationals:** {len(need_blind)} schools")
        lines.append("(Admission decision not affected by financial need)")
        for school in need_blind:
            name = school.get('school_name', 'Unknown')
            lines.append(f"- {name}")
        
        lines.append(f"\n**Need-Aware (but meet full need if admitted):** {len(meets_need)} schools")
        for school in meets_need[:10]:
            if school not in need_blind:
                name = school.get('school_name', 'Unknown')
                lines.append(f"- {name}")
        
        lines.append("\n### Step 2: Merit Scholarships")
        lines.append(f"**Schools offering merit to internationals:** {len(merit)}")
        for school in merit[:10]:
            name = school.get('school_name', 'Unknown')
            lines.append(f"- {name}")
        
        lines.append("\n### Step 3: Budget Reality Check")
        if budget < 35000:
            lines.append("⚠️ **Budget < $35k/year:** Focus on need-blind schools and large merit scholarships")
        elif budget < 50000:
            lines.append("**Budget $35-50k/year:** Mix of need-based and merit schools")
        else:
            lines.append("**Budget > $50k/year:** More flexibility, consider all options")
        
        lines.append("\n### Recommended Strategy:")
        lines.append("1. **Apply to all need-blind schools** (best chance with aid)")
        lines.append("2. **Apply to 5-7 need-aware schools** that meet full need")
        lines.append("3. **Apply to 3-5 merit scholarship schools** (backup options)")
        lines.append("4. **Verify I-20 timelines** (2-4 weeks after acceptance)")
        lines.append("5. **Plan for proof of funds** (required for I-20)")
        
        return "\n".join(lines)

