#!/usr/bin/env python3
"""
Simple verification script for CollegeAdvisor integration setup.
Avoids problematic imports that cause crashes.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_chromadb_server():
    """Check if ChromaDB server is running."""
    print("\n🔍 Checking ChromaDB Server...")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/api/v1/heartbeat", timeout=5)
        if response.status_code == 200:
            print("✅ ChromaDB server is running")
            return True
        else:
            print(f"❌ ChromaDB server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ ChromaDB server is not running")
        print("   Start with: chroma run --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error checking ChromaDB: {e}")
        return False

def check_ollama():
    """Check if Ollama is available."""
    print("\n🔍 Checking Ollama...")
    
    try:
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Has header + models
                models = lines[1:]
                print(f"✅ Ollama available with {len(models)} models")
                for model in models[:3]:  # Show first 3
                    print(f"   - {model.split()[0]}")
                return True
            else:
                print("✅ Ollama available but no models installed")
                print("   Install a model: ollama pull llama3")
                return True
        else:
            print("❌ Ollama command failed")
            return False
            
    except FileNotFoundError:
        print("❌ Ollama not installed")
        print("   Install from: https://ollama.ai/download")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

def check_python_packages():
    """Check required Python packages."""
    print("\n🔍 Checking Python Packages...")
    
    required_packages = [
        "chromadb",
        "sentence_transformers", 
        "transformers",
        "torch",
        "datasets"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - not installed")
            missing.append(package)
    
    if missing:
        print(f"\nInstall missing packages: pip install {' '.join(missing)}")
        return False
    
    return True

def check_data_structure():
    """Check data directory structure."""
    print("\n🔍 Checking Data Structure...")
    
    directories = [
        "data",
        "data/raw", 
        "data/processed",
        "data/training",
        "models",
        "logs"
    ]
    
    for dir_path in directories:
        path = Path(dir_path)
        if path.exists():
            files = list(path.glob("*"))
            print(f"✅ {dir_path}/ ({len(files)} files)")
        else:
            print(f"⚠️  {dir_path}/ - missing")
    
    return True

def check_config_files():
    """Check configuration files."""
    print("\n🔍 Checking Configuration...")
    
    config_files = [
        ".env",
        "college_advisor_data/config.py",
        "requirements.txt"
    ]
    
    for config_file in config_files:
        path = Path(config_file)
        if path.exists():
            print(f"✅ {config_file}")
        else:
            print(f"⚠️  {config_file} - missing")
    
    # Check environment variables
    env_vars = [
        "CHROMA_HOST",
        "CHROMA_PORT", 
        "EMBEDDING_MODEL"
    ]
    
    print("\nEnvironment variables:")
    for var in env_vars:
        value = os.getenv(var, "not set")
        print(f"   {var}: {value}")
    
    return True

def generate_next_steps(chromadb_ok, ollama_ok, packages_ok):
    """Generate next steps based on checks."""
    print("\n🎯 RECOMMENDED NEXT STEPS:")
    
    step = 1
    
    if not packages_ok:
        print(f"{step}. Install missing Python packages")
        step += 1
    
    if not chromadb_ok:
        print(f"{step}. Start ChromaDB server:")
        print("   chroma run --host 0.0.0.0 --port 8000 --persist_directory ./chroma_data")
        step += 1
    
    if not ollama_ok:
        print(f"{step}. Install and setup Ollama:")
        print("   - Download from https://ollama.ai/download")
        print("   - Install a model: ollama pull llama3")
        step += 1
    
    if chromadb_ok and packages_ok:
        print(f"{step}. Run data ingestion to populate ChromaDB:")
        print("   python -m college_advisor_data.cli ingest --help")
        step += 1
    
    if chromadb_ok and ollama_ok and packages_ok:
        print(f"{step}. Ready for API integration! 🎉")
        print("   Your RAG system components are ready")

def main():
    """Main verification function."""
    print("🚀 CollegeAdvisor Integration Verification")
    print("=" * 50)
    
    # Run checks
    packages_ok = check_python_packages()
    chromadb_ok = check_chromadb_server()
    ollama_ok = check_ollama()
    check_data_structure()
    check_config_files()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    print(f"Python Packages: {'✅' if packages_ok else '❌'}")
    print(f"ChromaDB Server: {'✅' if chromadb_ok else '❌'}")
    print(f"Ollama: {'✅' if ollama_ok else '❌'}")
    
    # Next steps
    generate_next_steps(chromadb_ok, ollama_ok, packages_ok)
    
    # Overall status
    if chromadb_ok and ollama_ok and packages_ok:
        print("\n🎉 System is ready for RAG integration!")
        return 0
    else:
        print("\n⚠️  Some components need setup")
        return 1

if __name__ == "__main__":
    exit(main())
