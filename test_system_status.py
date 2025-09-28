#!/usr/bin/env python3
"""
System Status Check - Verify all components are working
"""

import json
import requests
import subprocess
import os

def test_chromadb():
    """Test ChromaDB connection"""
    print("🔍 Testing ChromaDB...")
    try:
        response = requests.get("http://localhost:8000/api/v2/heartbeat", timeout=5)
        if response.status_code == 200:
            print("✅ ChromaDB is running and responding")
            return True
        else:
            print(f"❌ ChromaDB responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {e}")
        return False

def test_ollama():
    """Test Ollama connection and models"""
    print("🔍 Testing Ollama...")
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            models = result.stdout.strip()
            if 'llama3' in models:
                print("✅ Ollama is running with llama3 model")
                return True
            else:
                print("⚠️  Ollama is running but llama3 model not found")
                print(f"Available models:\n{models}")
                return False
        else:
            print(f"❌ Ollama command failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False

def test_sample_data():
    """Test sample data files"""
    print("🔍 Testing sample data...")
    try:
        data_files = [
            'data/sample/combined_data.json',
            'data/sample/colleges.json',
            'data/sample/programs.json',
            'data/training/college_qa.json'
        ]
        
        all_exist = True
        for file_path in data_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                print(f"✅ {file_path}: {len(data)} items")
            else:
                print(f"❌ Missing: {file_path}")
                all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"❌ Sample data test failed: {e}")
        return False

def test_python_packages():
    """Test required Python packages"""
    print("🔍 Testing Python packages...")
    try:
        packages = {
            'chromadb': 'ChromaDB client',
            'requests': 'HTTP requests',
            'transformers': 'Hugging Face transformers',
            'torch': 'PyTorch',
            'datasets': 'Hugging Face datasets'
        }
        
        all_imported = True
        for package, description in packages.items():
            try:
                __import__(package)
                print(f"✅ {package}: {description}")
            except ImportError as e:
                print(f"❌ {package}: Import failed - {e}")
                all_imported = False
        
        return all_imported
    except Exception as e:
        print(f"❌ Package test failed: {e}")
        return False

def test_environment_config():
    """Test environment configuration"""
    print("🔍 Testing environment configuration...")
    try:
        if os.path.exists('.env'):
            print("✅ .env file exists")
            with open('.env', 'r') as f:
                content = f.read()
                if 'CHROMA_HOST' in content and 'OLLAMA_HOST' in content:
                    print("✅ Environment variables configured")
                    return True
                else:
                    print("⚠️  .env file missing required variables")
                    return False
        else:
            print("⚠️  .env file not found")
            return False
    except Exception as e:
        print(f"❌ Environment config test failed: {e}")
        return False

def test_basic_ollama_generation():
    """Test basic Ollama generation"""
    print("🔍 Testing Ollama generation...")
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": "Hello, respond with just 'Hi there!'",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'response' in result:
                print(f"✅ Ollama generation working: '{result['response'][:50]}...'")
                return True
            else:
                print(f"❌ Ollama response format unexpected: {result}")
                return False
        else:
            print(f"❌ Ollama generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama generation test failed: {e}")
        return False

def main():
    """Run comprehensive system status check"""
    print("🚀 CollegeAdvisor RAG System Status Check")
    print("=" * 60)
    
    tests = [
        ("Python Packages", test_python_packages),
        ("Sample Data", test_sample_data),
        ("Environment Config", test_environment_config),
        ("ChromaDB", test_chromadb),
        ("Ollama", test_ollama),
        ("Ollama Generation", test_basic_ollama_generation)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        results[test_name] = test_func()
    
    print("\n🎯 SYSTEM STATUS SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("Ready for:")
        print("1. Data ingestion")
        print("2. Full RAG pipeline testing")
        print("3. API integration")
        print("4. Production deployment")
    else:
        print(f"\n⚠️  {total - passed} issues need attention")
        print("Check failed tests above for details")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
