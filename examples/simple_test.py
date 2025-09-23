#!/usr/bin/env python3
"""
Simple test to verify the College Scorecard collector works.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.base_collector import CollectorConfig
from collectors.government import CollegeScorecardCollector

def main():
    """Simple test of the College Scorecard collector."""
    print("🎓 Simple College Scorecard Test")
    print("=" * 40)
    
    # Create collector configuration
    config = CollectorConfig(
        api_key="DEMO_KEY",
        requests_per_second=0.5,  # Very slow for DEMO_KEY
        cache_enabled=True,
        cache_ttl_hours=24,
        output_format="json"
    )
    
    # Initialize collector
    collector = CollegeScorecardCollector(config)
    
    # Test source info
    print("📊 Testing source info...")
    try:
        source_info = collector.get_source_info()
        print(f"✅ Source: {source_info['name']}")
        print(f"   Fields: {source_info['total_fields']}")
        print(f"   Categories: {len(source_info['data_categories'])}")
    except Exception as e:
        print(f"❌ Source info failed: {e}")
        return
    
    # Test field groups
    print("\n📋 Testing field groups...")
    try:
        field_groups = collector.FIELD_GROUPS
        print(f"✅ Found {len(field_groups)} field groups:")
        for name, fields in field_groups.items():
            print(f"   - {name}: {len(fields)} fields")
    except Exception as e:
        print(f"❌ Field groups failed: {e}")
        return
    
    print("\n🎉 Basic tests passed!")
    print("\nNote: Data collection test skipped due to DEMO_KEY rate limits.")
    print("To test data collection, get a production API key from:")
    print("https://api.data.gov/signup/")

if __name__ == "__main__":
    main()
