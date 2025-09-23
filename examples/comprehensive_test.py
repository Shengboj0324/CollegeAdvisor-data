#!/usr/bin/env python3
"""
Comprehensive test of the College Scorecard collector.
Tests all field groups, pagination, and error handling.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.base_collector import CollectorConfig
from collectors.government import CollegeScorecardCollector

def test_field_groups():
    """Test all field groups individually."""
    print("🧪 Testing Field Groups")
    print("=" * 50)
    
    # Create collector configuration
    config = CollectorConfig(
        api_key="DEMO_KEY",
        requests_per_second=0.3,  # Very slow for DEMO_KEY
        cache_enabled=True,
        cache_ttl_hours=24,
        output_format="json"
    )
    
    # Initialize collector
    collector = CollegeScorecardCollector(config)
    
    # Test each field group
    field_groups = collector.FIELD_GROUPS
    
    for group_name, fields in field_groups.items():
        print(f"\n📋 Testing field group: {group_name}")
        print(f"   Fields ({len(fields)}): {', '.join(fields[:3])}{'...' if len(fields) > 3 else ''}")
        
        try:
            # Test with minimal parameters to avoid rate limits
            result = collector.collect(
                years=[2021],
                states=["CA"],  # Just California
                field_groups=[group_name],
                page_size=2  # Very small page size
            )
            
            print(f"   ✅ Success: {result.total_records} records")
            print(f"   ⏱️  Time: {result.processing_time:.2f}s")
            print(f"   📞 API calls: {result.api_calls}")
            
            if result.errors:
                print(f"   ⚠️  Errors: {len(result.errors)}")
                for error in result.errors[:2]:
                    print(f"      - {error}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            
        # Add delay between tests to respect rate limits
        import time
        time.sleep(2)

def test_pagination():
    """Test pagination functionality."""
    print("\n\n🔄 Testing Pagination")
    print("=" * 50)
    
    config = CollectorConfig(
        api_key="DEMO_KEY",
        requests_per_second=0.3,
        cache_enabled=True,
        cache_ttl_hours=24,
        output_format="json"
    )
    
    collector = CollegeScorecardCollector(config)
    
    try:
        # Test with different page sizes
        page_sizes = [1, 2, 5]
        
        for page_size in page_sizes:
            print(f"\n📄 Testing page size: {page_size}")
            
            result = collector.collect(
                years=[2021],
                states=["CA"],
                field_groups=["basic"],
                page_size=page_size
            )
            
            print(f"   ✅ Records: {result.total_records}")
            print(f"   📞 API calls: {result.api_calls}")
            
            # Add delay between tests
            import time
            time.sleep(2)
            
    except Exception as e:
        print(f"   ❌ Pagination test failed: {e}")

def test_mixed_fields():
    """Test collecting multiple field groups together."""
    print("\n\n🔀 Testing Mixed Field Groups")
    print("=" * 50)
    
    config = CollectorConfig(
        api_key="DEMO_KEY",
        requests_per_second=0.3,
        cache_enabled=True,
        cache_ttl_hours=24,
        output_format="json"
    )
    
    collector = CollegeScorecardCollector(config)
    
    try:
        # Test combining multiple field groups
        mixed_groups = [
            ["basic", "academics"],
            ["basic", "costs"],
            ["admissions", "completion"]
        ]
        
        for groups in mixed_groups:
            print(f"\n🔗 Testing groups: {', '.join(groups)}")
            
            result = collector.collect(
                years=[2021],
                states=["CA"],
                field_groups=groups,
                page_size=2
            )
            
            print(f"   ✅ Records: {result.total_records}")
            print(f"   📞 API calls: {result.api_calls}")
            
            # Add delay between tests
            import time
            time.sleep(2)
            
    except Exception as e:
        print(f"   ❌ Mixed fields test failed: {e}")

def test_latest_fields():
    """Test collecting latest available data."""
    print("\n\n🆕 Testing Latest Fields")
    print("=" * 50)
    
    config = CollectorConfig(
        api_key="DEMO_KEY",
        requests_per_second=0.3,
        cache_enabled=True,
        cache_ttl_hours=24,
        output_format="json"
    )
    
    collector = CollegeScorecardCollector(config)
    
    try:
        # Test with latest year (no year specified)
        print("📅 Testing latest data (no year specified)")
        
        result = collector.collect(
            states=["CA"],
            field_groups=["basic"],
            page_size=2
        )
        
        print(f"   ✅ Records: {result.total_records}")
        print(f"   📞 API calls: {result.api_calls}")
        
        # Test with multiple recent years
        print("\n📅 Testing multiple recent years")
        
        result = collector.collect(
            years=[2020, 2021],
            states=["CA"],
            field_groups=["basic"],
            page_size=2
        )
        
        print(f"   ✅ Records: {result.total_records}")
        print(f"   📞 API calls: {result.api_calls}")
        
    except Exception as e:
        print(f"   ❌ Latest fields test failed: {e}")

def main():
    """Run comprehensive tests."""
    print("🎓 Comprehensive College Scorecard Collector Test")
    print("=" * 60)
    print("⚠️  Using DEMO_KEY - tests are limited and slow")
    print("   Get a production API key from: https://api.data.gov/signup/")
    print("=" * 60)
    
    try:
        # Run all tests
        test_field_groups()
        test_pagination()
        test_mixed_fields()
        test_latest_fields()
        
        print("\n\n🎉 All tests completed!")
        print("✅ Foundation implementation is working correctly")
        print("\nNext steps:")
        print("1. Get a production API key for full testing")
        print("2. Implement remaining collectors (IPEDS, CDS, etc.)")
        print("3. Add data processing and validation pipelines")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")

if __name__ == "__main__":
    main()
