"""
Test Enhanced Response Generator

This script tests the new enhanced response generator to ensure it produces
high-quality 200-500 word responses before running on the full dataset.

Zero-tolerance testing:
- Validates all imports
- Tests all response types
- Checks quality metrics
- Provides detailed output

Author: Augment Agent
Date: October 18, 2025
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate imports with zero tolerance
try:
    from ai_training.enhanced_response_generator import EnhancedResponseGenerator, ResponseQuality
    logger.info("✅ EnhancedResponseGenerator imported successfully")
except ImportError as e:
    logger.error(f"❌ CRITICAL: Failed to import EnhancedResponseGenerator: {e}")
    sys.exit(1)

try:
    import json
    logger.info("✅ json imported successfully")
except ImportError as e:
    logger.error(f"❌ CRITICAL: Failed to import json: {e}")
    sys.exit(1)


def test_acceptance_rate_response():
    """Test acceptance rate response generation."""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Acceptance Rate Response")
    logger.info("="*80)
    
    generator = EnhancedResponseGenerator(min_words=200, max_words=500)
    
    # Test case: Cornell University
    response = generator.generate_acceptance_rate_response(
        university="Cornell University",
        acceptance_rate=7.5,
        additional_context={"enrollment": 15000, "sat_average": 1480}
    )
    
    quality = generator.validate_response_quality(response)
    
    logger.info(f"\n📊 Quality Metrics:")
    logger.info(f"   Characters: {quality.char_count}")
    logger.info(f"   Words: {quality.word_count}")
    logger.info(f"   Has Context: {quality.has_context}")
    logger.info(f"   Has Advice: {quality.has_advice}")
    logger.info(f"   Has Action Items: {quality.has_action_items}")
    logger.info(f"   Valid: {quality.is_valid}")
    
    if not quality.is_valid:
        logger.error(f"   Error: {quality.error_message}")
        return False
    
    logger.info(f"\n📝 Sample Response (first 300 chars):")
    logger.info(f"   {response[:300]}...")
    
    return True


def test_enrollment_response():
    """Test enrollment response generation."""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Enrollment Response")
    logger.info("="*80)
    
    generator = EnhancedResponseGenerator(min_words=200, max_words=500)
    
    # Test case: MIT
    response = generator.generate_enrollment_response(
        university="MIT",
        enrollment=11520,
        additional_context={}
    )
    
    quality = generator.validate_response_quality(response)
    
    logger.info(f"\n📊 Quality Metrics:")
    logger.info(f"   Characters: {quality.char_count}")
    logger.info(f"   Words: {quality.word_count}")
    logger.info(f"   Valid: {quality.is_valid}")
    
    if not quality.is_valid:
        logger.error(f"   Error: {quality.error_message}")
        return False
    
    logger.info(f"\n📝 Sample Response (first 300 chars):")
    logger.info(f"   {response[:300]}...")
    
    return True


def test_sat_score_response():
    """Test SAT score response generation."""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: SAT Score Response")
    logger.info("="*80)
    
    generator = EnhancedResponseGenerator(min_words=200, max_words=500)
    
    # Test case: Harvard
    response = generator.generate_sat_score_response(
        university="Harvard University",
        sat_average=1520,
        additional_context={}
    )
    
    quality = generator.validate_response_quality(response)
    
    logger.info(f"\n📊 Quality Metrics:")
    logger.info(f"   Characters: {quality.char_count}")
    logger.info(f"   Words: {quality.word_count}")
    logger.info(f"   Valid: {quality.is_valid}")
    
    if not quality.is_valid:
        logger.error(f"   Error: {quality.error_message}")
        return False
    
    logger.info(f"\n📝 Sample Response (first 300 chars):")
    logger.info(f"   {response[:300]}...")
    
    return True


def test_location_response():
    """Test location response generation."""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Location Response")
    logger.info("="*80)
    
    generator = EnhancedResponseGenerator(min_words=200, max_words=500)
    
    # Test case: Stanford
    response = generator.generate_location_response(
        university="Stanford University",
        city="Stanford",
        state="CA",
        additional_context={}
    )
    
    quality = generator.validate_response_quality(response)
    
    logger.info(f"\n📊 Quality Metrics:")
    logger.info(f"   Characters: {quality.char_count}")
    logger.info(f"   Words: {quality.word_count}")
    logger.info(f"   Valid: {quality.is_valid}")
    
    if not quality.is_valid:
        logger.error(f"   Error: {quality.error_message}")
        return False
    
    logger.info(f"\n📝 Sample Response (first 300 chars):")
    logger.info(f"   {response[:300]}...")
    
    return True


def test_tuition_response():
    """Test tuition response generation."""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Tuition Response")
    logger.info("="*80)
    
    generator = EnhancedResponseGenerator(min_words=200, max_words=500)
    
    # Test case: NYU
    response = generator.generate_tuition_response(
        university="New York University",
        tuition=58168,
        additional_context={}
    )
    
    quality = generator.validate_response_quality(response)
    
    logger.info(f"\n📊 Quality Metrics:")
    logger.info(f"   Characters: {quality.char_count}")
    logger.info(f"   Words: {quality.word_count}")
    logger.info(f"   Valid: {quality.is_valid}")
    
    if not quality.is_valid:
        logger.error(f"   Error: {quality.error_message}")
        return False
    
    logger.info(f"\n📝 Sample Response (first 300 chars):")
    logger.info(f"   {response[:300]}...")
    
    return True


def save_sample_responses():
    """Generate and save sample responses for manual review."""
    logger.info("\n" + "="*80)
    logger.info("GENERATING SAMPLE RESPONSES FOR MANUAL REVIEW")
    logger.info("="*80)
    
    generator = EnhancedResponseGenerator(min_words=200, max_words=500)
    
    samples = []
    
    # Sample 1: Cornell acceptance rate
    samples.append({
        "question": "What are my chances of getting into Cornell University?",
        "response": generator.generate_acceptance_rate_response(
            "Cornell University", 7.5, {}
        ),
        "type": "acceptance_rate"
    })
    
    # Sample 2: MIT enrollment
    samples.append({
        "question": "What's it like to attend MIT? How big is the student body?",
        "response": generator.generate_enrollment_response(
            "MIT", 11520, {}
        ),
        "type": "enrollment"
    })
    
    # Sample 3: Harvard SAT
    samples.append({
        "question": "How competitive is Harvard University for standardized testing?",
        "response": generator.generate_sat_score_response(
            "Harvard University", 1520, {}
        ),
        "type": "sat_score"
    })
    
    # Save to file
    output_file = Path("sample_enhanced_responses.json")
    with open(output_file, 'w') as f:
        json.dump(samples, f, indent=2)
    
    logger.info(f"\n✅ Saved {len(samples)} sample responses to: {output_file}")
    logger.info(f"\n📋 Please review these samples manually to ensure quality!")
    
    return output_file


def main():
    """Run all tests."""
    logger.info("\n" + "="*80)
    logger.info("ENHANCED RESPONSE GENERATOR TEST SUITE")
    logger.info("="*80)
    
    tests = [
        ("Acceptance Rate Response", test_acceptance_rate_response),
        ("Enrollment Response", test_enrollment_response),
        ("SAT Score Response", test_sat_score_response),
        ("Location Response", test_location_response),
        ("Tuition Response", test_tuition_response),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
            results[test_name] = False
    
    # Generate sample responses
    try:
        sample_file = save_sample_responses()
    except Exception as e:
        logger.error(f"❌ Failed to generate sample responses: {e}")
        sample_file = None
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n" + "="*80)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("="*80)
        logger.info("\nThe enhanced response generator is ready to use.")
        logger.info(f"Review sample responses in: {sample_file}")
        logger.info("\nNext step: Run the full data generation pipeline")
        return 0
    else:
        logger.error("\n" + "="*80)
        logger.error("❌ SOME TESTS FAILED")
        logger.error("="*80)
        logger.error("\nFix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

