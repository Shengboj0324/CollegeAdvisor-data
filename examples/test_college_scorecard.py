#!/usr/bin/env python3
"""
Example script to test the College Scorecard collector.

This script demonstrates how to use the College Scorecard collector
to fetch data from the U.S. Department of Education API.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.base_collector import CollectorConfig
from collectors.government import CollegeScorecardCollector


def main():
    """Test the College Scorecard collector."""
    print("🎓 College Scorecard Collector Test")
    print("=" * 50)
    
    # Create collector configuration
    config = CollectorConfig(
        api_key="DEMO_KEY",  # Using demo key for testing
        requests_per_second=2.0,  # Be respectful to the API
        cache_enabled=True,
        cache_ttl_hours=24,
        output_format="json"
    )
    
    # Initialize collector
    collector = CollegeScorecardCollector(config)
    
    # Display source information
    source_info = collector.get_source_info()
    print(f"📊 Data Source: {source_info['name']}")
    print(f"   Provider: {source_info['provider']}")
    print(f"   Description: {source_info['description']}")
    print(f"   Total available fields: {source_info['total_fields']}")
    print(f"   Data categories: {', '.join(source_info['data_categories'])}")
    print()
    
    # Test 1: Collect basic information for a few universities
    print("🔄 Test 1: Collecting basic university information...")
    try:
        result = collector.collect(
            years=[2021],  # Most recent complete year
            states=["CA"],  # Just California for testing
            field_groups=["basic"],  # Just basic info for DEMO_KEY
            page_size=5  # Very small for DEMO_KEY rate limits
        )
        
        print(f"✅ Collection completed!")
        print(f"   Records collected: {result.total_records}")
        print(f"   Processing time: {result.processing_time:.2f} seconds")
        print(f"   API calls made: {result.api_calls}")

        if result.errors:
            print(f"⚠️  Errors: {len(result.errors)}")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"   - {error}")

        if result.data:
            print(f"\n📋 Sample data (first 2 universities):")
            for i, university in enumerate(result.data[:2]):
                print(f"   {i+1}. {university.get('school.name', 'Unknown')}")
                print(f"      Location: {university.get('school.city', 'Unknown')}, {university.get('school.state', 'Unknown')}")
                print(f"      ID: {university.get('id', 'N/A')}")
                print()
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    print()
    
    # Test 2: Show available field groups
    print("📋 Test 2: Available field groups and sample fields...")
    field_groups = collector.FIELD_GROUPS
    
    for group_name, fields in field_groups.items():
        print(f"   {group_name.upper()} ({len(fields)} fields):")
        # Show first 5 fields as examples
        for field in fields[:5]:
            print(f"     - {field}")
        if len(fields) > 5:
            print(f"     ... and {len(fields) - 5} more")
        print()
    
    # Test 3: Test caching functionality
    print("🔄 Test 3: Testing cache functionality...")
    try:
        # This should use cached data from Test 1
        start_time = datetime.now()
        result2 = collector.collect(
            years=[2021],
            states=["CA"],
            field_groups=["basic"],
            page_size=5
        )
        end_time = datetime.now()
        
        cache_duration = (end_time - start_time).total_seconds()
        print(f"✅ Cache test completed in {cache_duration:.2f} seconds")
        print(f"   Records: {result2.total_records}")
        
        if cache_duration < 2.0:  # Should be much faster with cache
            print("   ✅ Cache appears to be working (fast response)")
        else:
            print("   ⚠️  Cache may not be working (slow response)")
            
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
    
    print()
    print("🎉 College Scorecard collector test completed!")
    print("\nNext steps:")
    print("1. Try collecting data for different years or states")
    print("2. Experiment with different field groups")
    print("3. Integrate with the main data pipeline")
    print("4. Set up your own API key for higher rate limits")


if __name__ == "__main__":
    main()
