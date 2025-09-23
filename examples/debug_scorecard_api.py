#!/usr/bin/env python3
"""
Debug script to test College Scorecard API directly.
"""

import requests
import json
from pprint import pprint

def test_basic_api_call():
    """Test a basic API call to College Scorecard."""

    print("🔍 Testing College Scorecard API directly...")

    # Basic API parameters - using minimal fields to avoid rate limits
    base_url = "https://api.data.gov/ed/collegescorecard/v1/schools"
    params = {
        "api_key": "DEMO_KEY",
        "fields": "id,school.name",
        "_per_page": 2,
        "_page": 0,
        "school.operating": 1
    }
    
    print(f"📡 Making request to: {base_url}")
    print(f"📋 Parameters: {params}")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Got {len(data.get('results', []))} results")
            
            if 'results' in data and data['results']:
                print("\n📋 Sample results:")
                for i, school in enumerate(data['results'][:3]):
                    print(f"   {i+1}. {school.get('school.name', 'Unknown')} - {school.get('school.city', 'Unknown')}, {school.get('school.state', 'Unknown')}")
            
            if 'metadata' in data:
                print(f"\n📊 Metadata: {data['metadata']}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response text: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_field_variations():
    """Test different field name variations."""
    
    print("\n🔍 Testing different field variations...")
    
    base_url = "https://api.data.gov/ed/collegescorecard/v1/schools"
    
    field_tests = [
        # Test 1: Basic fields only
        {
            "name": "Basic fields",
            "fields": "id,school.name,school.city,school.state"
        },
        # Test 2: With latest prefix
        {
            "name": "Latest fields",
            "fields": "id,school.name,latest.student.size"
        },
        # Test 3: Mixed fields
        {
            "name": "Mixed fields",
            "fields": "id,school.name,school.state,latest.admissions.admission_rate.overall"
        }
    ]
    
    for test in field_tests:
        print(f"\n📋 Testing: {test['name']}")
        params = {
            "api_key": "DEMO_KEY",
            "fields": test['fields'],
            "_per_page": 2,
            "_page": 0,
            "school.operating": 1,
            "school.state": "CA"
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: {len(data.get('results', []))} results")
                if data.get('results'):
                    sample = data['results'][0]
                    print(f"   📊 Sample fields: {list(sample.keys())}")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


def test_pagination():
    """Test pagination."""
    
    print("\n🔍 Testing pagination...")
    
    base_url = "https://api.data.gov/ed/collegescorecard/v1/schools"
    params = {
        "api_key": "DEMO_KEY",
        "fields": "id,school.name",
        "_per_page": 3,
        "_page": 0,
        "school.operating": 1
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Page 0: {len(data.get('results', []))} results")
            
            if 'metadata' in data:
                metadata = data['metadata']
                print(f"📊 Total records: {metadata.get('total', 'unknown')}")
                print(f"📊 Per page: {metadata.get('per_page', 'unknown')}")
                print(f"📊 Page: {metadata.get('page', 'unknown')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_basic_api_call()
    test_field_variations()
    test_pagination()
    
    print("\n🎉 API debugging completed!")
    print("\nNext steps:")
    print("1. Check which field formats work")
    print("2. Verify pagination parameters")
    print("3. Update collector based on findings")
