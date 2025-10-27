"""
Run Brutal Edge-Case Tests
Tests the RAG system against 20 extreme scenarios designed to break weak systems
"""

import sys
import json
import logging
from datetime import datetime

sys.path.append('rag_system')

from production_rag import ProductionRAG
from brutal_edge_case_tests import BRUTAL_EDGE_CASES, grade_brutal_edge_case

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


def run_brutal_tests():
    """Run all 20 brutal edge-case tests"""
    
    logger.info("=" * 80)
    logger.info("BRUTAL EDGE-CASE TEST SUITE")
    logger.info("20 scenarios designed to break weak college counseling AIs")
    logger.info("=" * 80)
    logger.info("")
    
    # Initialize RAG
    rag = ProductionRAG()
    
    results = []
    
    for i, test in enumerate(BRUTAL_EDGE_CASES, 1):
        logger.info("=" * 80)
        logger.info(f"TEST {i}/20: {test['category']}")
        logger.info(f"Difficulty: {test['difficulty']}/10")
        logger.info("=" * 80)
        logger.info("")
        
        # Query the RAG
        result = rag.query(test['query'])
        
        # Grade the response
        grading = grade_brutal_edge_case(
            {'answer': result.answer, 'citations': result.citations},
            test
        )
        
        # Log results
        logger.info(f"GRADE: {grading['grade']}/10.0")
        logger.info(f"Breakdown: Citations={grading['score_breakdown']['citations']}/40, "
                   f"Elements={grading['score_breakdown']['elements']}/40, "
                   f"Abstain={grading['score_breakdown']['abstain']}/10, "
                   f"Special={grading['score_breakdown']['special']}/10")
        logger.info(f"Covered {grading['covered_elements']}/{grading['total_elements']} required elements")
        
        if grading['feedback']:
            for fb in grading['feedback'][:3]:  # Show first 3 issues
                logger.info(f"  {fb}")
        
        logger.info("")
        
        # Store result
        results.append({
            'test_id': test['id'],
            'category': test['category'],
            'difficulty': test['difficulty'],
            'grading': grading,
            'answer_preview': result.answer[:200] + '...' if len(result.answer) > 200 else result.answer,
            'citation_count': len(result.citations)
        })
    
    # Summary
    logger.info("=" * 80)
    logger.info("BRUTAL EDGE-CASE TEST SUMMARY")
    logger.info("=" * 80)
    
    grades = [r['grading']['grade'] for r in results]
    avg_grade = sum(grades) / len(grades)
    
    perfect = sum(1 for g in grades if g >= 9.5)
    excellent = sum(1 for g in grades if g >= 9.0)
    good = sum(1 for g in grades if g >= 8.0)
    passing = sum(1 for g in grades if g >= 7.0)
    failing = sum(1 for g in grades if g < 7.0)
    
    logger.info(f"Total Tests: {len(results)}")
    logger.info(f"Average Grade: {avg_grade:.1f}/10.0")
    logger.info(f"Perfect (≥9.5): {perfect}")
    logger.info(f"Excellent (≥9.0): {excellent}")
    logger.info(f"Good (≥8.0): {good}")
    logger.info(f"Passing (≥7.0): {passing}")
    logger.info(f"Failing (<7.0): {failing}")
    logger.info(f"Pass Rate: {(passing/len(results))*100:.1f}%")
    logger.info("=" * 80)
    
    # Status determination
    if avg_grade >= 9.0 and failing == 0:
        status = "✅ PRODUCTION-READY - OUTSTANDING PERFORMANCE"
    elif avg_grade >= 8.0 and failing <= 2:
        status = "⚠️ NEAR-READY - MINOR GAPS REMAIN"
    elif avg_grade >= 7.0:
        status = "⚠️ NEEDS IMPROVEMENT - SIGNIFICANT GAPS"
    else:
        status = "❌ NOT READY - MAJOR FAILURES"
    
    logger.info(f"STATUS: {status}")
    logger.info("")
    
    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': len(results),
        'average_grade': round(avg_grade, 2),
        'perfect_count': perfect,
        'excellent_count': excellent,
        'good_count': good,
        'passing_count': passing,
        'failing_count': failing,
        'pass_rate': round((passing/len(results))*100, 1),
        'status': status,
        'results': results
    }
    
    with open('brutal_edge_case_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    logger.info("Results saved to brutal_edge_case_results.json")
    logger.info("")
    
    # Detailed failure analysis
    if failing > 0:
        logger.info("=" * 80)
        logger.info("FAILURE ANALYSIS")
        logger.info("=" * 80)
        
        for r in results:
            if r['grading']['grade'] < 7.0:
                logger.info(f"\n❌ FAILED: {r['category']}")
                logger.info(f"   Grade: {r['grading']['grade']}/10.0")
                logger.info(f"   Elements: {r['grading']['covered_elements']}/{r['grading']['total_elements']}")
                for fb in r['grading']['feedback'][:5]:
                    logger.info(f"   {fb}")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST SUITE COMPLETE")
    logger.info("=" * 80)
    
    return output


if __name__ == '__main__':
    results = run_brutal_tests()
    
    # Exit with error code if not production-ready
    if results['failing_count'] > 0 or results['average_grade'] < 9.0:
        sys.exit(1)
    else:
        sys.exit(0)

