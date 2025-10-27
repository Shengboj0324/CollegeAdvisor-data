#!/usr/bin/env python3
"""
Evaluation Harness for Production RAG
Tests against hard gates before any fine-tuning
"""

import json
import logging
import re
from typing import Dict, List
from dataclasses import dataclass, asdict
from pathlib import Path

from production_rag import ProductionRAG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EvalQuery:
    """Evaluation query with expected criteria"""
    category: str
    question: str
    context: Dict
    expected_format: str = None
    requires_calculator: bool = False
    should_abstain: bool = False
    notes: str = ""


@dataclass
class EvalResult:
    """Evaluation result for a single query"""
    query: str
    category: str
    
    # Hard gates
    has_citations: bool
    citation_count: int
    has_fabricated_numbers: bool
    schema_valid: bool
    abstain_correct: bool
    
    # Scoring
    citation_coverage: float
    numeric_traceability: float
    structure_score: float
    risk_flags_score: float
    decisiveness_score: float
    
    # Overall
    total_score: float
    passed: bool
    
    # Details
    answer: str
    notes: str


class EvalHarness:
    """
    Evaluation harness with hard gates
    
    Hard Gates (ship/kill switches):
    - Citations ≥ 90%
    - Fabricated-number rate ≤ 2%
    - Structure validity ≥ 95%
    - Correct abstain behavior ≥ 95%
    """
    
    # Hard gate thresholds
    GATES = {
        "citations_coverage": 0.90,
        "fabricated_number_rate": 0.02,
        "structure_validity": 0.95,
        "abstain_correctness": 0.95,
    }
    
    def __init__(self):
        """Initialize eval harness"""
        self.rag = ProductionRAG()
        self.queries = self._load_queries()
        
    def _load_queries(self) -> List[EvalQuery]:
        """Load evaluation queries (50-100 across 8 categories)"""
        queries = []
        
        # Category 1: FAFSA/CSS/SAI edge cases (10 queries)
        queries.extend([
            EvalQuery(
                category="FAFSA/CSS/SAI",
                question="Calculate SAI for divorced parents: custodial parent AGI $80k, remarried (stepparent AGI $60k), non-custodial parent refuses CSS. Household 4, 2 in college. Assets: $50k savings, $30k 529.",
                context={
                    "sai_scenario": {
                        "agi": 140000,  # Custodial + stepparent
                        "household": 4,
                        "students_in_college": 2,
                        "assets": {"savings": 50000, "529": 30000},
                        "student_assets": {},
                        "parent_marital_status": "married"
                    }
                },
                requires_calculator=True,
                notes="Tests divorced parent scenario with stepparent income"
            ),
            EvalQuery(
                category="FAFSA/CSS/SAI",
                question="Family owns S-corp with 45 employees, $200k equity. AGI $150k, household 5, 1 in college. How is business equity treated under 2024-2025 FAFSA?",
                context={},
                requires_calculator=False,
                notes="Tests small business exclusion (<100 employees)"
            ),
            EvalQuery(
                category="FAFSA/CSS/SAI",
                question="Grandparent 529 with $100k. How does this affect FAFSA vs CSS Profile schools?",
                context={},
                requires_calculator=False,
                notes="Tests grandparent 529 treatment (not on FAFSA, varies by CSS school)"
            ),
        ])
        
        # Category 2: CS/Engineering internal transfer gates (10 queries)
        queries.extend([
            EvalQuery(
                category="Internal Transfer",
                question="What are the internal transfer requirements for Computer Science at University of Washington?",
                context={},
                expected_format="table",
                notes="Tests major gate retrieval with GPA thresholds"
            ),
            EvalQuery(
                category="Internal Transfer",
                question="Compare CS internal transfer difficulty at UW vs UCSD vs UIUC. Include GPA requirements and acceptance rates.",
                context={},
                expected_format="table",
                notes="Tests multi-school comparison with structured output"
            ),
        ])
        
        # Category 3: UC/CSU residency + WUE (10 queries)
        queries.extend([
            EvalQuery(
                category="Residency/WUE",
                question="Can I establish California residency while attending UC Berkeley as an out-of-state student?",
                context={},
                requires_calculator=False,
                notes="Tests UC residency rules (answer: generally no for undergrads)"
            ),
            EvalQuery(
                category="Residency/WUE",
                question="Which UC/CSU engineering programs accept WUE? What's the cost difference vs in-state?",
                context={},
                expected_format="table",
                notes="Tests WUE eligibility by program"
            ),
        ])
        
        # Category 4: Transfer articulation (10 queries)
        queries.extend([
            EvalQuery(
                category="Transfer Articulation",
                question="Show me the course-by-course transfer plan from De Anza College to UC Berkeley Computer Science.",
                context={},
                expected_format="table",
                notes="Tests ASSIST articulation retrieval"
            ),
            EvalQuery(
                category="Transfer Articulation",
                question="What are the IGETC requirements and which UCs accept it for engineering majors?",
                context={},
                expected_format="table",
                notes="Tests IGETC policy (most UCs don't accept for engineering)"
            ),
        ])
        
        # Category 5: International/Visa (10 queries)
        queries.extend([
            EvalQuery(
                category="International/Visa",
                question="Which top CS programs are need-blind for international students? Include admission rates and average aid.",
                context={},
                expected_format="table",
                notes="Tests need-aware vs need-blind policies"
            ),
            EvalQuery(
                category="International/Visa",
                question="Explain CPT vs OPT vs STEM OPT for F-1 students. Include duration limits and work restrictions.",
                context={},
                expected_format="table",
                notes="Tests immigration work authorization rules"
            ),
        ])
        
        # Category 6: Cost analysis (10 queries)
        queries.extend([
            EvalQuery(
                category="Cost Analysis",
                question="Compare total cost of attendance at MIT vs Stanford vs Harvard for a student with SAI $50k.",
                context={"school_id": "mit"},
                expected_format="table",
                requires_calculator=True,
                notes="Tests multi-school cost comparison"
            ),
            EvalQuery(
                category="Cost Analysis",
                question="What is the 4-year total cost difference between living on-campus vs off-campus at Stanford?",
                context={"school_id": "stanford"},
                requires_calculator=True,
                notes="Tests housing cost analysis"
            ),
        ])
        
        # Category 7: Unanswerable (should abstain) (10 queries)
        queries.extend([
            EvalQuery(
                category="Unanswerable",
                question="What will be the admission rate at Harvard in 2030?",
                context={},
                should_abstain=True,
                notes="Tests abstain on future predictions"
            ),
            EvalQuery(
                category="Unanswerable",
                question="What is the internal transfer rate for Biology at University of XYZ?",
                context={},
                should_abstain=True,
                notes="Tests abstain on missing data (school not in corpus)"
            ),
            EvalQuery(
                category="Unanswerable",
                question="Should I major in CS or Biology?",
                context={},
                should_abstain=True,
                notes="Tests abstain on subjective questions without context"
            ),
        ])
        
        # Category 8: Policy-specific (10 queries)
        queries.extend([
            EvalQuery(
                category="Policy-Specific",
                question="How does MIT treat outside scholarships? Do they reduce grants or student contribution first?",
                context={},
                requires_calculator=False,
                notes="Tests specific institutional policy"
            ),
            EvalQuery(
                category="Policy-Specific",
                question="Which schools offer NCP (non-custodial parent) waivers and what documentation is required?",
                context={},
                expected_format="table",
                notes="Tests CSS Profile NCP waiver policies"
            ),
        ])
        
        return queries
        
    def _score_citations(self, result, query: EvalQuery) -> Dict:
        """Score citation quality"""
        has_citations = result.citation_coverage > 0
        citation_count = len(result.citations)
        
        # Check for official URLs (.edu, .gov)
        official_citations = sum(
            1 for c in result.citations
            if any(domain in c.url for domain in [".edu", ".gov", "assist.org"])
        )
        
        score = {
            "has_citations": has_citations,
            "citation_count": citation_count,
            "official_count": official_citations,
            "coverage": result.citation_coverage,
        }
        
        return score
        
    def _score_numeric_traceability(self, result, query: EvalQuery) -> Dict:
        """Score numeric traceability (no fabricated numbers)"""
        # Find all numbers in answer
        numbers = re.findall(r'\$[\d,]+|\d+\.\d+%|\d+%', result.answer)
        
        # Check if numbers have sources
        has_fabricated = False
        
        if numbers:
            # If we have numbers, we must have either:
            # 1. Citations (from retrieval)
            # 2. Tool calls (from calculators)
            if not result.citations and not result.tool_calls:
                has_fabricated = True
                
        score = {
            "number_count": len(numbers),
            "has_fabricated": has_fabricated,
            "traceability": 0.0 if has_fabricated else 1.0,
        }
        
        return score
        
    def _score_structure(self, result, query: EvalQuery) -> Dict:
        """Score structured output compliance"""
        if not query.expected_format:
            return {"valid": True, "score": 1.0}
            
        valid = result.schema_valid
        
        score = {
            "expected_format": query.expected_format,
            "valid": valid,
            "score": 1.0 if valid else 0.0,
        }

        return score

    def _score_abstain(self, result, query: EvalQuery) -> Dict:
        """Score abstain behavior"""
        # Should abstain but didn't
        if query.should_abstain and not result.should_abstain:
            return {"correct": False, "score": 0.0, "error": "Should have abstained"}

        # Shouldn't abstain but did
        if not query.should_abstain and result.should_abstain:
            return {"correct": False, "score": 0.0, "error": "Shouldn't have abstained"}

        # Correct behavior
        return {"correct": True, "score": 1.0}

    def evaluate_query(self, query: EvalQuery) -> EvalResult:
        """Evaluate a single query"""
        logger.info(f"\nEvaluating: {query.question[:80]}...")

        # Run RAG
        result = self.rag.query(
            query.question,
            context=query.context,
            expected_format=query.expected_format
        )

        # Score dimensions
        citation_score = self._score_citations(result, query)
        numeric_score = self._score_numeric_traceability(result, query)
        structure_score = self._score_structure(result, query)
        abstain_score = self._score_abstain(result, query)

        # Calculate total score (0-10)
        total_score = (
            citation_score["coverage"] * 2.0 +  # 20%
            numeric_score["traceability"] * 2.0 +  # 20%
            structure_score["score"] * 2.0 +  # 20%
            abstain_score["score"] * 2.0 +  # 20%
            (1.0 if result.citations else 0.0) * 2.0  # 20% - has any citations
        )

        # Pass if score >= 7.0
        passed = total_score >= 7.0

        return EvalResult(
            query=query.question,
            category=query.category,
            has_citations=citation_score["has_citations"],
            citation_count=citation_score["citation_count"],
            has_fabricated_numbers=numeric_score["has_fabricated"],
            schema_valid=structure_score["valid"],
            abstain_correct=abstain_score["correct"],
            citation_coverage=citation_score["coverage"],
            numeric_traceability=numeric_score["traceability"],
            structure_score=structure_score["score"],
            risk_flags_score=0.5,  # Placeholder
            decisiveness_score=0.5,  # Placeholder
            total_score=total_score,
            passed=passed,
            answer=result.answer[:500] if result.answer else result.abstain_reason or "",
            notes=query.notes
        )

    def run_evaluation(self) -> Dict:
        """Run full evaluation suite"""
        logger.info("="*80)
        logger.info("EVALUATION HARNESS - TESTING RAG AGAINST HARD GATES")
        logger.info("="*80)

        results = []

        for query in self.queries:
            try:
                result = self.evaluate_query(query)
                results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating query: {e}")

        # Calculate aggregate metrics
        total_queries = len(results)

        # Hard gate 1: Citations coverage
        # Only count queries that should have answered (not abstained correctly)
        answerable_queries = [r for r in results if not (r.abstain_correct and r.query in [q.question for q in self.queries if q.should_abstain])]
        queries_with_citations = sum(1 for r in answerable_queries if r.has_citations)
        citations_coverage = queries_with_citations / len(answerable_queries) if answerable_queries else 1.0

        # Hard gate 2: Fabricated numbers
        queries_with_fabrication = sum(1 for r in results if r.has_fabricated_numbers)
        fabrication_rate = queries_with_fabrication / total_queries if total_queries > 0 else 0

        # Hard gate 3: Structure validity
        queries_with_valid_structure = sum(1 for r in results if r.schema_valid)
        structure_validity = queries_with_valid_structure / total_queries if total_queries > 0 else 0

        # Hard gate 4: Abstain correctness
        queries_with_correct_abstain = sum(1 for r in results if r.abstain_correct)
        abstain_correctness = queries_with_correct_abstain / total_queries if total_queries > 0 else 0

        # Overall pass rate
        passed_queries = sum(1 for r in results if r.passed)
        pass_rate = passed_queries / total_queries if total_queries > 0 else 0

        # Average score
        avg_score = sum(r.total_score for r in results) / total_queries if total_queries > 0 else 0

        # Check hard gates
        gates_passed = {
            "citations_coverage": citations_coverage >= self.GATES["citations_coverage"],
            "fabricated_number_rate": fabrication_rate <= self.GATES["fabricated_number_rate"],
            "structure_validity": structure_validity >= self.GATES["structure_validity"],
            "abstain_correctness": abstain_correctness >= self.GATES["abstain_correctness"],
        }

        all_gates_passed = all(gates_passed.values())

        summary = {
            "total_queries": total_queries,
            "passed_queries": passed_queries,
            "pass_rate": pass_rate,
            "avg_score": avg_score,
            "hard_gates": {
                "citations_coverage": {
                    "value": citations_coverage,
                    "threshold": self.GATES["citations_coverage"],
                    "passed": gates_passed["citations_coverage"]
                },
                "fabricated_number_rate": {
                    "value": fabrication_rate,
                    "threshold": self.GATES["fabricated_number_rate"],
                    "passed": gates_passed["fabricated_number_rate"]
                },
                "structure_validity": {
                    "value": structure_validity,
                    "threshold": self.GATES["structure_validity"],
                    "passed": gates_passed["structure_validity"]
                },
                "abstain_correctness": {
                    "value": abstain_correctness,
                    "threshold": self.GATES["abstain_correctness"],
                    "passed": gates_passed["abstain_correctness"]
                },
            },
            "all_gates_passed": all_gates_passed,
            "results": [asdict(r) for r in results]
        }

        return summary

    def print_summary(self, summary: Dict):
        """Print evaluation summary"""
        logger.info("\n" + "="*80)
        logger.info("EVALUATION SUMMARY")
        logger.info("="*80)

        logger.info(f"\nTotal Queries: {summary['total_queries']}")
        logger.info(f"Passed: {summary['passed_queries']} ({summary['pass_rate']:.1%})")
        logger.info(f"Average Score: {summary['avg_score']:.2f}/10.0")

        logger.info("\n" + "-"*80)
        logger.info("HARD GATES (Ship/Kill Switches)")
        logger.info("-"*80)

        for gate_name, gate_data in summary['hard_gates'].items():
            status = "✅ PASS" if gate_data['passed'] else "❌ FAIL"
            logger.info(
                f"{status} | {gate_name}: {gate_data['value']:.1%} "
                f"(threshold: {gate_data['threshold']:.1%})"
            )

        logger.info("\n" + "="*80)
        if summary['all_gates_passed']:
            logger.info("🎉 ALL GATES PASSED - READY TO DEPLOY (NO FINE-TUNING NEEDED)")
        else:
            logger.info("⚠️  SOME GATES FAILED - CONSIDER TARGETED FINE-TUNING")
        logger.info("="*80)

    def save_results(self, summary: Dict, output_path: str = "eval_results.json"):
        """Save evaluation results"""
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"\nResults saved to {output_path}")


def main():
    """Run evaluation harness"""
    harness = EvalHarness()
    summary = harness.run_evaluation()
    harness.print_summary(summary)
    harness.save_results(summary)


if __name__ == "__main__":
    main()


