#!/usr/bin/env python3
"""
Recommendation Engine
Generates data-driven recommendations with caveats, trade-offs, and alternatives
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from synthesis_layer import Recommendation, SynthesisEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generate recommendations based on retrieved data and user context
    All recommendations include:
    - Supporting facts with citations
    - Trade-offs
    - Caveats
    - Alternatives
    - Confidence level
    """
    
    def __init__(self, synthesis_engine: SynthesisEngine):
        self.engine = synthesis_engine
    
    def recommend_school_list(
        self,
        all_schools: List[Dict],
        user_profile: Dict[str, Any],
        target_count: int = 12
    ) -> Recommendation:
        """
        Recommend a balanced school list
        
        Args:
            all_schools: All available schools with data
            user_profile: User's academic profile, budget, preferences
            target_count: Target number of schools (default: 12)
            
        Returns:
            Recommendation with school list
        """
        # Extract user profile
        gpa = user_profile.get('gpa', 0)
        budget = user_profile.get('budget', 0)
        major = user_profile.get('major', '')
        income = user_profile.get('family_income', 0)
        
        # Score schools based on fit
        scored_schools = []
        for school in all_schools:
            score = self._calculate_fit_score(school, user_profile)
            scored_schools.append((school, score))
        
        # Sort by score
        scored_schools.sort(key=lambda x: x[1], reverse=True)
        
        # Select balanced list (reach, target, safety)
        selected = self._select_balanced_list(scored_schools, user_profile, target_count)
        
        # Generate recommendation text
        rec_text = self._format_school_list_recommendation(selected, user_profile)
        
        # Extract supporting facts
        supporting_facts = []
        for school, category in selected:
            school_name = school.get('school_name', 'Unknown')
            admit_rate = school.get('major_admit_rate') or school.get('overall_admit_rate', 0)
            
            citations = school.get('citations', [])
            if isinstance(citations, str):
                try:
                    citations = json.loads(citations)
                except:
                    citations = [citations] if citations else []
            
            fact = f"{school_name}: {admit_rate*100:.1f}% admit rate ({category})"
            if citations:
                supporting_facts.append({
                    'fact': fact,
                    'citation': citations[0]
                })
        
        # Generate trade-offs
        trade_offs = [
            f"Reach schools (< 10% admit): Higher prestige but lower acceptance probability",
            f"Target schools (10-30% admit): Balanced selectivity and fit",
            f"Safety schools (> 30% admit): Higher acceptance probability but may sacrifice some preferences",
            f"Budget constraint (${budget:,}/year): May limit options at some schools"
        ]
        
        # Generate caveats
        caveats = [
            "Admission rates vary by major and applicant pool",
            "Financial aid packages are estimates until official offers received",
            "This list is based on statistical fit, not guaranteed outcomes",
            "Visit campuses and research culture fit before finalizing",
            "Application deadlines and requirements vary by school"
        ]
        
        # Generate alternatives
        alternatives = []
        if len(scored_schools) > target_count:
            for school, score in scored_schools[target_count:target_count+3]:
                name = school.get('school_name', 'Unknown')
                alternatives.append(f"{name} (fit score: {score:.2f})")
        
        # Calculate confidence
        confidence = "High" if len(all_schools) >= 20 else "Medium"
        
        return Recommendation(
            recommendation_text=rec_text,
            confidence_level=confidence,
            trade_offs=trade_offs,
            caveats=caveats,
            supporting_facts=supporting_facts,
            alternatives=alternatives
        )
    
    def recommend_financial_strategy(
        self,
        schools: List[Dict],
        scenario: Dict[str, Any]
    ) -> Recommendation:
        """Recommend financial aid strategy"""
        
        # Extract scenario
        income = scenario.get('income', 0)
        assets = scenario.get('assets', 0)
        divorced = scenario.get('divorced_parents', False)
        
        # Categorize schools by aid generosity
        meets_full_need = [s for s in schools if s.get('meets_full_need', False)]
        no_loan = [s for s in schools if 'no-loan' in str(s.get('loan_policy', '')).lower()]
        ncp_waiver = [s for s in schools if s.get('ncp_waiver_available', False)]
        
        # Generate recommendation
        rec_lines = [
            "## Financial Aid Strategy Recommendation\n",
            f"Based on your family income (${income:,}) and circumstances, here is a data-driven strategy:\n"
        ]
        
        rec_lines.append("### Priority 1: Schools Meeting Full Need")
        rec_lines.append(f"Apply to **{len(meets_full_need)} schools** that meet 100% of demonstrated need:")
        for school in meets_full_need[:8]:
            name = school.get('school_name', 'Unknown')
            rec_lines.append(f"- {name}")
        
        if divorced and ncp_waiver:
            rec_lines.append("\n### Priority 2: Non-Custodial Parent Waiver")
            rec_lines.append(f"Given divorced parents, prioritize **{len(ncp_waiver)} schools** offering NCP waiver:")
            for school in ncp_waiver[:5]:
                name = school.get('school_name', 'Unknown')
                rec_lines.append(f"- {name}")
        
        rec_lines.append("\n### Priority 3: No-Loan Schools")
        rec_lines.append(f"Consider **{len(no_loan)} schools** with no-loan policies:")
        for school in no_loan[:5]:
            name = school.get('school_name', 'Unknown')
            rec_lines.append(f"- {name}")
        
        rec_lines.append("\n### Action Items:")
        rec_lines.append("1. Run Net Price Calculators for all target schools")
        rec_lines.append("2. Gather financial documents (tax returns, W-2s, asset statements)")
        rec_lines.append("3. Complete FAFSA and CSS Profile by deadlines")
        rec_lines.append("4. Request NCP waiver documentation if applicable")
        rec_lines.append("5. Compare aid offers in April and negotiate if needed")
        
        rec_text = "\n".join(rec_lines)
        
        # Supporting facts
        supporting_facts = []
        for school in meets_full_need[:5]:
            name = school.get('school_name', 'Unknown')
            citations = school.get('citations', [])
            if isinstance(citations, str):
                try:
                    citations = json.loads(citations)
                except:
                    citations = [citations] if citations else []
            
            if citations:
                supporting_facts.append({
                    'fact': f"{name} meets 100% of demonstrated need",
                    'citation': citations[0]
                })
        
        # Trade-offs
        trade_offs = [
            "Schools meeting full need are often highly selective",
            "CSS Profile schools may assess assets differently than FAFSA",
            "Home equity treatment varies significantly by school",
            "Outside scholarships may reduce institutional aid at some schools"
        ]
        
        # Caveats
        caveats = [
            "Net Price Calculator estimates are not guaranteed aid offers",
            "Aid packages can vary significantly even among similar schools",
            "Special circumstances (medical expenses, job loss) may affect aid",
            "Merit scholarships may have GPA requirements to maintain",
            "Aid policies can change year-to-year"
        ]
        
        # Alternatives
        alternatives = [
            "Consider in-state public universities for lower base cost",
            "Explore merit scholarship programs at less selective schools",
            "Look into work-study and campus employment opportunities"
        ]
        
        return Recommendation(
            recommendation_text=rec_text,
            confidence_level="High",
            trade_offs=trade_offs,
            caveats=caveats,
            supporting_facts=supporting_facts,
            alternatives=alternatives
        )
    
    def recommend_cs_pathway(
        self,
        schools: List[Dict],
        user_profile: Dict[str, Any]
    ) -> Recommendation:
        """Recommend CS admission pathway"""
        
        gpa = user_profile.get('gpa', 0)
        risk_tolerance = user_profile.get('risk_tolerance', 'medium')
        
        # Categorize schools
        direct_admit = [s for s in schools if s.get('direct_admit', False)]
        pre_major = [s for s in schools if not s.get('direct_admit', False)]
        
        # Generate recommendation based on risk tolerance
        rec_lines = ["## CS Admission Pathway Recommendation\n"]
        
        if risk_tolerance == 'low':
            rec_lines.append("**Given your low risk tolerance, prioritize DIRECT ADMIT programs:**\n")
            rec_lines.append(f"**{len(direct_admit)} Direct Admit Schools:**")
            for school in direct_admit[:8]:
                name = school.get('school_name', 'Unknown')
                rate = school.get('major_admit_rate', 0)
                rec_lines.append(f"- {name}: {rate*100:.1f}% admit rate")
            
            rec_lines.append("\n⚠️ **AVOID pre-major schools** with competitive internal transfer:")
            for school in pre_major[:3]:
                name = school.get('school_name', 'Unknown')
                transfer_rate = school.get('transfer_rate', 0)
                rec_lines.append(f"- {name}: Only {transfer_rate*100:.1f}% internal transfer rate")
        
        else:
            rec_lines.append("**Balanced approach with mix of direct admit and pre-major:**\n")
            rec_lines.append(f"**Direct Admit (60% of list):** {len(direct_admit[:7])} schools")
            for school in direct_admit[:7]:
                name = school.get('school_name', 'Unknown')
                rec_lines.append(f"- {name}")
            
            rec_lines.append(f"\n**Pre-Major (40% of list):** {len(pre_major[:5])} schools")
            rec_lines.append("(Only if you're confident in maintaining high GPA)")
            for school in pre_major[:5]:
                name = school.get('school_name', 'Unknown')
                gpa_req = school.get('typical_gpa', 0)
                rec_lines.append(f"- {name} (typical GPA: {gpa_req:.2f})")
        
        rec_text = "\n".join(rec_lines)
        
        # Supporting facts
        supporting_facts = []
        for school in direct_admit[:5]:
            name = school.get('school_name', 'Unknown')
            rate = school.get('major_admit_rate', 0)
            citations = school.get('citations', [])
            if isinstance(citations, str):
                try:
                    citations = json.loads(citations)
                except:
                    citations = [citations] if citations else []
            
            if citations:
                supporting_facts.append({
                    'fact': f"{name}: {rate*100:.1f}% CS admit rate (direct admit)",
                    'citation': citations[0]
                })
        
        # Trade-offs
        trade_offs = [
            "Direct admit: Guaranteed CS major but often more competitive admission",
            "Pre-major: Easier initial admission but risky internal transfer (5-30% rates)",
            "Highly selective programs: Better outcomes but lower acceptance probability",
            "Less selective programs: Higher acceptance but may sacrifice some opportunities"
        ]
        
        # Caveats
        caveats = [
            "Internal transfer rates can change year-to-year",
            "GPA requirements are minimums; actual competitive GPAs are often higher",
            "Some schools allow major changes; others lock you into your admitted major",
            "CS program quality varies significantly even among similar-ranked schools"
        ]
        
        # Alternatives
        alternatives = [
            "Consider CS+X programs (often less competitive than pure CS)",
            "Look into Data Science or Information Science as alternative majors",
            "Explore liberal arts colleges with strong CS programs (less competitive)"
        ]
        
        return Recommendation(
            recommendation_text=rec_text,
            confidence_level="High",
            trade_offs=trade_offs,
            caveats=caveats,
            supporting_facts=supporting_facts,
            alternatives=alternatives
        )
    
    def _calculate_fit_score(self, school: Dict, profile: Dict) -> float:
        """Calculate fit score for school based on user profile"""
        score = 0.0
        
        # Admit rate fit (higher score for target range)
        admit_rate = school.get('major_admit_rate') or school.get('overall_admit_rate', 0)
        gpa = profile.get('gpa', 0)
        
        if admit_rate > 0.30:
            score += 0.3  # Safety
        elif 0.10 <= admit_rate <= 0.30:
            score += 0.5  # Target
        else:
            score += 0.2  # Reach
        
        # Budget fit
        budget = profile.get('budget', 0)
        net_price = school.get('net_price', school.get('tuition', 0))
        
        if net_price <= budget:
            score += 0.3
        elif net_price <= budget * 1.2:
            score += 0.2
        else:
            score += 0.1
        
        # Major fit
        major = profile.get('major', '').lower()
        school_major = school.get('major', '').lower()
        
        if major and major in school_major:
            score += 0.2
        
        return score
    
    def _select_balanced_list(
        self,
        scored_schools: List[Tuple[Dict, float]],
        profile: Dict,
        target_count: int
    ) -> List[Tuple[Dict, str]]:
        """Select balanced list of reach/target/safety schools"""
        
        # Categorize by admit rate
        reach = []
        target = []
        safety = []
        
        for school, score in scored_schools:
            admit_rate = school.get('major_admit_rate') or school.get('overall_admit_rate', 0)
            
            if admit_rate < 0.10:
                reach.append((school, score))
            elif admit_rate < 0.30:
                target.append((school, score))
            else:
                safety.append((school, score))
        
        # Select balanced distribution (2-3-2 or 3-4-3 depending on target_count)
        if target_count <= 8:
            reach_count = 2
            target_count_num = 3
            safety_count = 2
        else:
            reach_count = 3
            target_count_num = 5
            safety_count = 3
        
        selected = []
        selected.extend([(s, "Reach") for s, _ in reach[:reach_count]])
        selected.extend([(s, "Target") for s, _ in target[:target_count_num]])
        selected.extend([(s, "Safety") for s, _ in safety[:safety_count]])
        
        return selected
    
    def _format_school_list_recommendation(
        self,
        selected: List[Tuple[Dict, str]],
        profile: Dict
    ) -> str:
        """Format school list recommendation"""
        
        lines = ["## Recommended School List\n"]
        lines.append(f"Based on your profile (GPA: {profile.get('gpa', 0):.2f}, Budget: ${profile.get('budget', 0):,}/year):\n")
        
        # Group by category
        reach = [s for s, cat in selected if cat == "Reach"]
        target = [s for s, cat in selected if cat == "Target"]
        safety = [s for s, cat in selected if cat == "Safety"]
        
        lines.append(f"### Reach Schools ({len(reach)})")
        for school in reach:
            name = school.get('school_name', 'Unknown')
            rate = school.get('major_admit_rate') or school.get('overall_admit_rate', 0)
            lines.append(f"- {name} ({rate*100:.1f}% admit rate)")
        
        lines.append(f"\n### Target Schools ({len(target)})")
        for school in target:
            name = school.get('school_name', 'Unknown')
            rate = school.get('major_admit_rate') or school.get('overall_admit_rate', 0)
            lines.append(f"- {name} ({rate*100:.1f}% admit rate)")
        
        lines.append(f"\n### Safety Schools ({len(safety)})")
        for school in safety:
            name = school.get('school_name', 'Unknown')
            rate = school.get('major_admit_rate') or school.get('overall_admit_rate', 0)
            lines.append(f"- {name} ({rate*100:.1f}% admit rate)")
        
        return "\n".join(lines)

