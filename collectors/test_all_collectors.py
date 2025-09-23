#!/usr/bin/env python3
"""
Comprehensive Collector Testing Script

This script tests all data collectors to ensure they're working properly.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.base_collector import BaseCollector
from collectors.government import CollegeScorecardCollector
from collectors.social_media import SocialMediaCollector
from collectors.financial_aid import FinancialAidCollector
from collectors.summer_programs import SummerProgramCollector
from collectors.web_scrapers import WebScrapingCollector
from collectors.user_auth_collector import UserAuthCollector
from collectors.phone_verification_collector import PhoneVerificationCollector
from collectors.security_event_collector import SecurityEventCollector
from collectors.user_profile_collector import UserProfileCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelLevel)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CollectorTester:
    """Tests all data collectors comprehensively."""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.test_start_time = datetime.now()
    
    def test_government_collectors(self) -> Dict[str, Any]:
        """Test government data collectors."""
        logger.info("Testing Government Data Collectors...")
        
        results = {}
        
        # Test College Scorecard Collector
        try:
            collector = CollegeScorecardCollector()
            
            # Test basic functionality
            source_info = collector.get_source_info()
            assert source_info['name'] == 'College Scorecard API'
            
            # Test data collection (limited sample)
            collection_result = collector.collect(
                years=[2022],
                states=['CA'],
                max_records=10
            )
            
            results['college_scorecard'] = {
                'status': 'PASS',
                'records_collected': collection_result.total_records,
                'success_rate': collection_result.success_rate,
                'message': f"Collected {collection_result.total_records} records"
            }
            
        except Exception as e:
            results['college_scorecard'] = {
                'status': 'FAIL',
                'error': str(e),
                'message': f"College Scorecard test failed: {str(e)}"
            }
        
        return results
    
    def test_social_media_collectors(self) -> Dict[str, Any]:
        """Test social media data collectors."""
        logger.info("Testing Social Media Collectors...")
        
        results = {}
        
        try:
            collector = SocialMediaCollector()
            
            # Test initialization
            source_info = collector.get_source_info()
            assert 'Social Media' in source_info['name']
            
            # Test data collection (mock mode)
            collection_result = collector.collect(
                platforms=['twitter', 'reddit'],
                keywords=['college', 'university'],
                max_posts=5
            )
            
            results['social_media'] = {
                'status': 'PASS',
                'records_collected': collection_result.total_records,
                'message': f"Social media collector working. Collected {collection_result.total_records} records"
            }
            
        except Exception as e:
            results['social_media'] = {
                'status': 'FAIL',
                'error': str(e),
                'message': f"Social media test failed: {str(e)}"
            }
        
        return results
    
    def test_authentication_collectors(self) -> Dict[str, Any]:
        """Test authentication data collectors."""
        logger.info("Testing Authentication Collectors...")
        
        results = {}
        
        # Test User Auth Collector
        try:
            collector = UserAuthCollector()
            
            # Test data generation
            collection_result = collector.collect(num_events=10)
            
            results['user_auth'] = {
                'status': 'PASS',
                'records_collected': collection_result.total_records,
                'message': f"User auth collector working. Generated {collection_result.total_records} events"
            }
            
        except Exception as e:
            results['user_auth'] = {
                'status': 'FAIL',
                'error': str(e),
                'message': f"User auth test failed: {str(e)}"
            }
        
        # Test Phone Verification Collector
        try:
            collector = PhoneVerificationCollector()
            
            collection_result = collector.collect(num_events=10)
            
            results['phone_verification'] = {
                'status': 'PASS',
                'records_collected': collection_result.total_records,
                'message': f"Phone verification collector working. Generated {collection_result.total_records} events"
            }
            
        except Exception as e:
            results['phone_verification'] = {
                'status': 'FAIL',
                'error': str(e),
                'message': f"Phone verification test failed: {str(e)}"
            }
        
        # Test Security Event Collector
        try:
            collector = SecurityEventCollector()
            
            collection_result = collector.collect(num_events=10)
            
            results['security_events'] = {
                'status': 'PASS',
                'records_collected': collection_result.total_records,
                'message': f"Security event collector working. Generated {collection_result.total_records} events"
            }
            
        except Exception as e:
            results['security_events'] = {
                'status': 'FAIL',
                'error': str(e),
                'message': f"Security event test failed: {str(e)}"
            }
        
        # Test User Profile Collector
        try:
            collector = UserProfileCollector()
            
            collection_result = collector.collect(num_profiles=10)
            
            results['user_profiles'] = {
                'status': 'PASS',
                'records_collected': collection_result.total_records,
                'message': f"User profile collector working. Generated {collection_result.total_records} profiles"
            }
            
        except Exception as e:
            results['user_profiles'] = {
                'status': 'FAIL',
                'error': str(e),
                'message': f"User profile test failed: {str(e)}"
            }
        
        return results
    
    def test_web_scrapers(self) -> Dict[str, Any]:
        """Test web scraping collectors."""
        logger.info("Testing Web Scraping Collectors...")
        
        results = {}
        
        try:
            collector = WebScrapingCollector()
            
            # Test basic functionality
            source_info = collector.get_source_info()
            
            # Test data collection (limited)
            collection_result = collector.collect(
                urls=['https://example.com'],
                max_pages=1
            )
            
            results['web_scraping'] = {
                'status': 'PASS',
                'records_collected': collection_result.total_records,
                'message': f"Web scraping collector working. Processed {collection_result.total_records} pages"
            }
            
        except Exception as e:
            results['web_scraping'] = {
                'status': 'FAIL',
                'error': str(e),
                'message': f"Web scraping test failed: {str(e)}"
            }
        
        return results
    
    def test_financial_aid_collectors(self) -> Dict[str, Any]:
        """Test financial aid data collectors."""
        logger.info("Testing Financial Aid Collectors...")
        
        results = {}
        
        try:
            collector = FinancialAidCollector()
            
            # Test data collection
            collection_result = collector.collect(
                aid_types=['grants', 'scholarships'],
                max_records=10
            )
            
            results['financial_aid'] = {
                'status': 'PASS',
                'records_collected': collection_result.total_records,
                'message': f"Financial aid collector working. Collected {collection_result.total_records} records"
            }
            
        except Exception as e:
            results['financial_aid'] = {
                'status': 'FAIL',
                'error': str(e),
                'message': f"Financial aid test failed: {str(e)}"
            }
        
        return results
    
    def test_summer_programs_collectors(self) -> Dict[str, Any]:
        """Test summer programs collectors."""
        logger.info("Testing Summer Programs Collectors...")
        
        results = {}
        
        try:
            collector = SummerProgramCollector()
            
            # Test data collection
            collection_result = collector.collect(
                program_types=['academic', 'research'],
                max_records=10
            )
            
            results['summer_programs'] = {
                'status': 'PASS',
                'records_collected': collection_result.total_records,
                'message': f"Summer programs collector working. Collected {collection_result.total_records} records"
            }
            
        except Exception as e:
            results['summer_programs'] = {
                'status': 'FAIL',
                'error': str(e),
                'message': f"Summer programs test failed: {str(e)}"
            }
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all collector tests."""
        logger.info("Starting comprehensive collector testing...")
        
        all_results = {}
        
        # Run all test categories
        test_categories = [
            ("Government Collectors", self.test_government_collectors),
            ("Social Media Collectors", self.test_social_media_collectors),
            ("Authentication Collectors", self.test_authentication_collectors),
            ("Web Scraping Collectors", self.test_web_scrapers),
            ("Financial Aid Collectors", self.test_financial_aid_collectors),
            ("Summer Programs Collectors", self.test_summer_programs_collectors),
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for category_name, test_func in test_categories:
            logger.info(f"Running {category_name}...")
            
            try:
                category_results = test_func()
                all_results[category_name] = category_results
                
                # Count results
                for test_name, result in category_results.items():
                    total_tests += 1
                    if result['status'] == 'PASS':
                        passed_tests += 1
                        
            except Exception as e:
                logger.error(f"Category {category_name} failed: {str(e)}")
                all_results[category_name] = {
                    'error': str(e),
                    'status': 'CATEGORY_FAIL'
                }
        
        # Calculate overall statistics
        test_duration = (datetime.now() - self.test_start_time).total_seconds()
        
        all_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'test_duration': test_duration,
            'overall_status': 'PASS' if passed_tests == total_tests else 'FAIL'
        }
        
        return all_results


def main():
    """Main function to run collector tests."""
    print("🧪 CollegeAdvisor Data Pipeline - Collector Testing")
    print("=" * 60)
    
    tester = CollectorTester()
    results = tester.run_all_tests()
    
    print("\n📊 COLLECTOR TEST SUMMARY")
    print("=" * 60)
    
    # Print category results
    for category, category_results in results.items():
        if category == 'summary':
            continue
            
        print(f"\n📂 {category}")
        print("-" * 40)
        
        if 'error' in category_results:
            print(f"❌ Category failed: {category_results['error']}")
            continue
        
        for test_name, result in category_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_icon} {test_name}: {result['status']}")
            print(f"   {result['message']}")
    
    # Print overall summary
    summary = results['summary']
    print(f"\n🎯 OVERALL RESULTS")
    print("=" * 60)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Test Duration: {summary['test_duration']:.2f} seconds")
    
    if summary['overall_status'] == 'PASS':
        print("\n🎉 All collector tests passed!")
        return 0
    else:
        print("\n⚠️  Some collector tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
