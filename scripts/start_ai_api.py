#!/usr/bin/env python3
"""
Startup script for the AI Training API Server.

This script starts the FastAPI server that provides AI training data endpoints,
real-time feature serving, and model management integration.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(project_root / "logs" / "ai_api.log")
        ]
    )

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install fastapi uvicorn pydantic")
        return False

def create_directories():
    """Create required directories."""
    directories = [
        "data/model_artifacts",
        "data/ab_experiments",
        "data/user_interactions", 
        "data/auth_events",
        "data/model_updates",
        "logs"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def main():
    """Main startup function."""
    print("🚀 Starting CollegeAdvisor AI Training API Server")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create required directories
    create_directories()
    
    # Set environment variables
    os.environ.setdefault("PYTHONPATH", str(project_root))
    
    print("\n🎯 API Server Configuration:")
    print(f"   Host: 0.0.0.0")
    print(f"   Port: 8001")
    print(f"   Project Root: {project_root}")
    print(f"   Log File: {project_root}/logs/ai_api.log")
    
    print("\n📡 Available Endpoints:")
    endpoints = [
        "GET  /api/training-data/{model_type}",
        "GET  /api/user-features/{user_id}",
        "POST /api/model-feedback",
        "POST /api/model-performance-metrics",
        "GET  /api/data-quality/ai-training",
        "GET  /api/evaluation-data/{model_type}",
        "GET  /api/model-retraining-triggers",
        "POST /api/model-updates",
        "POST /webhooks/user-interactions",
        "POST /webhooks/auth-events",
        "GET  /api/model-artifacts/{model_type}",
        "POST /api/model-deployment",
        "POST /api/model-rollback",
        "GET  /api/experiments/active",
        "POST /api/experiments",
        "POST /api/experiments/{experiment_id}/start",
        "GET  /api/experiments/{experiment_id}/assignment/{user_id}",
        "POST /api/experiments/results",
        "GET  /api/experiments/{experiment_id}/analysis"
    ]
    
    for endpoint in endpoints:
        print(f"   {endpoint}")
    
    print("\n🔗 Integration URLs:")
    print("   API Documentation: http://localhost:8001/docs")
    print("   Health Check: http://localhost:8001/")
    print("   Training Data: http://localhost:8001/api/training-data/recommendation")
    
    print("\n🎉 Starting server...")
    
    try:
        # Import and run the server
        from ai_training.api_server import app
        import uvicorn
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info",
            access_log=True,
            reload=False
        )
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\n👋 AI Training API Server stopped")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        print(f"\n❌ Server error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
