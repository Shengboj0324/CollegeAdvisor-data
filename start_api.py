#!/usr/bin/env python3
"""
Start the CollegeAdvisor API server
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if API dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import aiohttp
        import chromadb
        print("✅ All API dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Installing API dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "api/requirements.txt"], check=True)
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False

def check_rag_services():
    """Check if RAG services are running."""
    import requests
    
    services_status = {
        "chromadb": False,
        "ollama": False
    }
    
    # Check ChromaDB
    try:
        response = requests.get("http://localhost:8000/api/v2/heartbeat", timeout=5)
        if response.status_code == 200:
            services_status["chromadb"] = True
            print("✅ ChromaDB is running")
        else:
            print("❌ ChromaDB is not responding properly")
    except Exception:
        print("❌ ChromaDB is not running")
    
    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            services_status["ollama"] = True
            print("✅ Ollama is running")
        else:
            print("❌ Ollama is not responding properly")
    except Exception:
        print("❌ Ollama is not running")
    
    return services_status

def main():
    """Main function to start the API."""
    print("🚀 Starting CollegeAdvisor API")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Cannot start API without dependencies")
        return False
    
    # Check RAG services
    print("\n🔍 Checking RAG services...")
    services = check_rag_services()
    
    if not services["chromadb"]:
        print("\n⚠️  ChromaDB is not running!")
        print("Start ChromaDB with:")
        print("   chroma run --path ./chroma_data --host 0.0.0.0 --port 8000")
        print("\nContinuing anyway (API will show degraded status)...")
    
    if not services["ollama"]:
        print("\n⚠️  Ollama is not running!")
        print("Start Ollama service and ensure llama3 model is available")
        print("\nContinuing anyway (API will show degraded status)...")
    
    # Start API server
    print("\n🌐 Starting FastAPI server...")
    print("📍 API will be available at:")
    print("   • Main API: http://localhost:8080")
    print("   • Documentation: http://localhost:8080/docs")
    print("   • Health Check: http://localhost:8080/health")
    print("   • Recommendations: http://localhost:8080/api/v1/recommendations")
    
    print("\n📊 Available Endpoints:")
    endpoints = [
        "GET  /                           - API information",
        "GET  /health                     - Health check",
        "POST /api/v1/recommendations     - Get recommendations",
        "GET  /api/v1/recommendations/search - Search colleges",
        "GET  /api/v1/status              - System status",
        "GET  /docs                       - API documentation"
    ]
    
    for endpoint in endpoints:
        print(f"   {endpoint}")
    
    print("\n🎯 Example API calls:")
    print("""
   # Health check
   curl http://localhost:8080/health
   
   # Get recommendations
   curl -X POST http://localhost:8080/api/v1/recommendations \\
     -H "Content-Type: application/json" \\
     -d '{
       "query": "What are the best computer science programs?",
       "profile": {
         "gpa_range": "3.5-4.0",
         "intended_major": "Computer Science"
       }
     }'
   
   # Search colleges
   curl "http://localhost:8080/api/v1/recommendations/search?q=computer%20science&limit=5"
    """)
    
    print("\n🚀 Starting server...")
    
    try:
        # Import and run the server
        import uvicorn
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=8080,
            log_level="info",
            reload=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 API server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
