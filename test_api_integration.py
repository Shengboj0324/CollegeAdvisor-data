#!/usr/bin/env python3
"""
Test API integration with RAG service
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.rag_client import RAGClient
from api.models import RecommendationRequest, UserProfile

async def test_rag_client():
    """Test the RAG client directly."""
    print("🧪 Testing RAG Client Integration")
    print("=" * 50)
    
    client = RAGClient()
    
    # Test 1: Health check
    print("1. Testing health check...")
    health = await client.health_check()
    print(f"   Health status: {health}")
    
    # Test 2: Simple recommendation
    print("\n2. Testing simple recommendation...")
    result = await client.get_recommendations(
        query="What are the best computer science programs?",
        n_results=3
    )
    
    if "error" in result:
        print(f"   ❌ Error: {result['error']}")
    else:
        print(f"   ✅ Response: {result['response'][:100]}...")
        print(f"   ✅ Sources: {len(result['sources'])} documents")
    
    # Test 3: Recommendation with profile
    print("\n3. Testing recommendation with profile...")
    profile = {
        "gpa_range": "3.5-4.0",
        "intended_major": "Computer Science",
        "location_preference": "California"
    }
    
    result = await client.get_recommendations(
        query="Which universities should I consider for AI research?",
        profile=profile,
        n_results=3
    )
    
    if "error" in result:
        print(f"   ❌ Error: {result['error']}")
    else:
        print(f"   ✅ Response: {result['response'][:100]}...")
        print(f"   ✅ Sources: {len(result['sources'])} documents")
        print(f"   ✅ Profile applied: {result['metadata']['profile_applied']}")
    
    return health["status"] == "healthy"

def test_api_models():
    """Test API models and validation."""
    print("\n🧪 Testing API Models")
    print("=" * 50)
    
    try:
        # Test UserProfile
        profile = UserProfile(
            gpa_range="3.5-4.0",
            intended_major="Computer Science",
            academic_interests=["AI", "Machine Learning"],
            location_preference="California",
            budget_max=60000
        )
        print("✅ UserProfile model works")
        
        # Test RecommendationRequest
        request = RecommendationRequest(
            query="What are the best CS programs?",
            profile=profile,
            max_results=5
        )
        print("✅ RecommendationRequest model works")
        print(f"   Query: {request.query}")
        print(f"   Profile: {request.profile.intended_major}")
        print(f"   Max results: {request.max_results}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

async def test_api_endpoints_simulation():
    """Simulate API endpoint calls."""
    print("\n🧪 Simulating API Endpoint Calls")
    print("=" * 50)
    
    try:
        # Simulate the main recommendation endpoint logic
        client = RAGClient()
        
        # Create a request
        profile = UserProfile(
            gpa_range="3.5-4.0",
            intended_major="Computer Science",
            location_preference="California"
        )
        
        request = RecommendationRequest(
            query="What are the best computer science programs for someone interested in AI?",
            profile=profile,
            max_results=3
        )
        
        print(f"📝 Request: {request.query}")
        print(f"📊 Profile: GPA {request.profile.gpa_range}, Major {request.profile.intended_major}")
        
        # Call RAG service (simulating the API endpoint)
        rag_result = await client.get_recommendations(
            query=request.query,
            profile=request.profile.model_dump() if request.profile else None,
            n_results=request.max_results
        )
        
        if "error" in rag_result:
            print(f"❌ RAG service error: {rag_result['error']}")
            return False
        
        # Simulate response formatting
        response_data = {
            "query": request.query,
            "recommendations": rag_result["response"],
            "sources": rag_result["sources"],
            "metadata": {
                "model": rag_result.get("model", "llama3"),
                "retrieval_count": len(rag_result["sources"]),
                "processing_time": rag_result.get("processing_time", 0)
            },
            "profile_used": request.profile.model_dump()
        }
        
        print("✅ API endpoint simulation successful")
        print(f"   Response length: {len(response_data['recommendations'])} chars")
        print(f"   Sources found: {len(response_data['sources'])}")
        print(f"   Processing time: {response_data['metadata']['processing_time']:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ API simulation failed: {e}")
        return False

async def main():
    """Run all integration tests."""
    print("🚀 API Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("RAG Client", test_rag_client()),
        ("API Models", test_api_models()),
        ("API Endpoints Simulation", test_api_endpoints_simulation())
    ]
    
    results = []
    for test_name, test_coro in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n🎯 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ RAG client working")
        print("✅ API models validated")
        print("✅ Endpoint simulation successful")
        print("\nReady to start the API server!")
        print("Run: python start_api.py")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("Check the error messages above")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
