#!/usr/bin/env python3
"""
Verification script for CollegeAdvisor integration setup.

This script checks all components needed for the RAG system:
1. ChromaDB connection and schema
2. Embedding service
3. Data artifacts and versioning
4. Model availability (Ollama/Unsloth)
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from college_advisor_data.config import config
from college_advisor_data.storage.chroma_client import ChromaDBClient
from college_advisor_data.schemas import COLLECTION_NAME, SCHEMA_VERSION
from college_advisor_data.embedding.embedder import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationVerifier:
    """Verifies the complete integration setup."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "artifacts": {},
            "recommendations": []
        }
    
    def check_chromadb_connection(self) -> bool:
        """Check ChromaDB connection and schema."""
        print("\n🔍 Checking ChromaDB Connection...")
        
        try:
            client = ChromaDBClient()
            
            # Test heartbeat
            heartbeat = client.client.heartbeat()
            print(f"✅ ChromaDB heartbeat: {heartbeat}")
            
            # Check collection
            collection = client.get_or_create_collection()
            count = collection.count()
            print(f"✅ Collection '{COLLECTION_NAME}' exists with {count} documents")
            
            # Check schema version
            metadata = collection.metadata or {}
            schema_version = metadata.get("schema_version", "unknown")
            print(f"✅ Schema version: {schema_version}")
            
            if schema_version != SCHEMA_VERSION:
                print(f"⚠️  Schema version mismatch: expected {SCHEMA_VERSION}, got {schema_version}")
                self.results["recommendations"].append(
                    f"Update collection schema to version {SCHEMA_VERSION}"
                )
            
            self.results["checks"]["chromadb"] = {
                "status": "success",
                "heartbeat": heartbeat,
                "collection_count": count,
                "schema_version": schema_version,
                "host": f"{config.chroma_host}:{config.chroma_port}"
            }
            
            # Record artifact info
            self.results["artifacts"]["chroma_collection"] = f"{COLLECTION_NAME}@v{schema_version}"
            
            return True
            
        except Exception as e:
            print(f"❌ ChromaDB connection failed: {e}")
            self.results["checks"]["chromadb"] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["recommendations"].append(
                "Start ChromaDB server: chroma run --host 0.0.0.0 --port 8000"
            )
            return False
    
    def check_embedding_service(self) -> bool:
        """Check embedding service functionality."""
        print("\n🔍 Checking Embedding Service...")
        
        try:
            embedder = EmbeddingService()
            
            # Test embedding
            test_text = "Computer science program at Stanford University"
            embedding = embedder.embed_text(test_text)
            
            print(f"✅ Embedding service working")
            print(f"✅ Model: {embedder.model_name}")
            print(f"✅ Dimension: {len(embedding)}")
            
            self.results["checks"]["embedding"] = {
                "status": "success",
                "model": embedder.model_name,
                "dimension": len(embedding),
                "test_embedding_length": len(embedding)
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Embedding service failed: {e}")
            self.results["checks"]["embedding"] = {
                "status": "failed",
                "error": str(e)
            }
            self.results["recommendations"].append(
                "Install sentence-transformers: pip install sentence-transformers"
            )
            return False
    
    def check_data_artifacts(self) -> bool:
        """Check for existing data artifacts."""
        print("\n🔍 Checking Data Artifacts...")
        
        # Check for processed data
        processed_dir = Path("data/processed")
        if processed_dir.exists():
            files = list(processed_dir.glob("*.json"))
            print(f"✅ Found {len(files)} processed data files")
            self.results["artifacts"]["processed_files"] = len(files)
        else:
            print("⚠️  No processed data directory found")
            self.results["recommendations"].append(
                "Run data ingestion pipeline to create processed data"
            )
        
        # Check for training data
        training_dir = Path("data/training")
        if training_dir.exists():
            files = list(training_dir.glob("*.json"))
            print(f"✅ Found {len(files)} training data files")
            self.results["artifacts"]["training_files"] = len(files)
        else:
            print("⚠️  No training data directory found")
        
        # Check for models
        models_dir = Path("models")
        if models_dir.exists():
            model_dirs = [d for d in models_dir.iterdir() if d.is_dir()]
            print(f"✅ Found {len(model_dirs)} model directories")
            self.results["artifacts"]["model_directories"] = len(model_dirs)
        else:
            print("⚠️  No models directory found")
        
        return True
    
    def check_ollama_availability(self) -> bool:
        """Check if Ollama is available."""
        print("\n🔍 Checking Ollama Availability...")
        
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                models = result.stdout.strip().split('\n')[1:]  # Skip header
                print(f"✅ Ollama available with {len(models)} models")
                print("Available models:")
                for model in models[:5]:  # Show first 5
                    print(f"  - {model}")
                
                self.results["checks"]["ollama"] = {
                    "status": "success",
                    "models": models
                }
                return True
            else:
                print("❌ Ollama command failed")
                self.results["checks"]["ollama"] = {
                    "status": "failed",
                    "error": "Command failed"
                }
                
        except FileNotFoundError:
            print("❌ Ollama not installed")
            self.results["checks"]["ollama"] = {
                "status": "not_installed",
                "error": "Ollama not found"
            }
            self.results["recommendations"].append(
                "Install Ollama: https://ollama.ai/download"
            )
            
        except Exception as e:
            print(f"❌ Ollama check failed: {e}")
            self.results["checks"]["ollama"] = {
                "status": "failed",
                "error": str(e)
            }
        
        return False
    
    def check_training_environment(self) -> bool:
        """Check training environment setup."""
        print("\n🔍 Checking Training Environment...")
        
        try:
            from ai_training.training_utils import check_training_environment
            env_info = check_training_environment()
            
            print(f"✅ Training environment: {env_info['recommended_trainer']}")
            print(f"✅ CUDA available: {env_info['cuda_available']}")
            print(f"✅ Unsloth available: {env_info['unsloth_available']}")
            
            self.results["checks"]["training"] = env_info
            
            if env_info["recommended_trainer"] == "cpu":
                self.results["recommendations"].append(
                    "Consider GPU environment for faster training"
                )
            
            return True
            
        except Exception as e:
            print(f"❌ Training environment check failed: {e}")
            self.results["checks"]["training"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    def generate_next_steps(self) -> List[str]:
        """Generate recommended next steps based on checks."""
        steps = []
        
        # Check what's missing
        chromadb_ok = self.results["checks"].get("chromadb", {}).get("status") == "success"
        embedding_ok = self.results["checks"].get("embedding", {}).get("status") == "success"
        
        if not chromadb_ok:
            steps.append("1. Start ChromaDB server: chroma run --host 0.0.0.0 --port 8000")
        
        if not embedding_ok:
            steps.append("2. Install embedding dependencies: pip install sentence-transformers")
        
        if chromadb_ok and embedding_ok:
            collection_count = self.results["checks"]["chromadb"].get("collection_count", 0)
            if collection_count == 0:
                steps.append("3. Run initial data ingestion to populate ChromaDB")
            else:
                steps.append("3. ✅ ChromaDB has data - ready for API integration")
        
        # Training recommendations
        training_status = self.results["checks"].get("training", {})
        if training_status.get("recommended_trainer") == "cpu":
            steps.append("4. For model fine-tuning, consider GPU environment")
        
        # Ollama recommendations
        ollama_status = self.results["checks"].get("ollama", {}).get("status")
        if ollama_status != "success":
            steps.append("5. Install and configure Ollama for inference")
        
        return steps
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all verification checks."""
        print("🚀 Starting CollegeAdvisor Integration Verification")
        print("=" * 60)
        
        # Run checks
        self.check_chromadb_connection()
        self.check_embedding_service()
        self.check_data_artifacts()
        self.check_ollama_availability()
        self.check_training_environment()
        
        # Generate recommendations
        next_steps = self.generate_next_steps()
        self.results["next_steps"] = next_steps
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 VERIFICATION SUMMARY")
        print("=" * 60)
        
        for check_name, check_result in self.results["checks"].items():
            status = check_result.get("status", "unknown")
            emoji = "✅" if status == "success" else "❌"
            print(f"{emoji} {check_name.upper()}: {status}")
        
        print(f"\n🎯 NEXT STEPS:")
        for step in next_steps:
            print(f"   {step}")
        
        return self.results


def main():
    """Main verification function."""
    verifier = IntegrationVerifier()
    results = verifier.run_all_checks()
    
    # Save results
    results_file = Path("verification_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    # Return exit code based on critical checks
    chromadb_ok = results["checks"].get("chromadb", {}).get("status") == "success"
    embedding_ok = results["checks"].get("embedding", {}).get("status") == "success"
    
    if chromadb_ok and embedding_ok:
        print("\n🎉 Core components are ready!")
        return 0
    else:
        print("\n⚠️  Some critical components need attention")
        return 1


if __name__ == "__main__":
    exit(main())
