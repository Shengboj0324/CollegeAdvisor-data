#!/usr/bin/env python3
"""
Connection Verification Script for CollegeAdvisor Data Pipeline

This script verifies all database and service connections are working properly.
"""

import os
import sys
import yaml
import asyncio
import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from college_advisor_data.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConnectionVerifier:
    """Verifies all system connections and dependencies."""
    
    def __init__(self):
        self.config = Config()
        self.results: List[Tuple[str, bool, str]] = []
    
    def verify_postgresql_connection(self) -> Tuple[bool, str]:
        """Verify PostgreSQL database connection."""
        try:
            import psycopg2
            from psycopg2 import sql
            
            # Load database config
            db_config_path = project_root / "configs" / "database_config.yaml"
            if db_config_path.exists():
                with open(db_config_path, 'r') as f:
                    db_config = yaml.safe_load(f)
                    
                analytics_db = db_config['databases']['analytics_db']
                
                # Expand environment variables with defaults
                host = os.getenv('DB_HOST', 'localhost')
                port = int(os.getenv('DB_PORT', '5432'))
                database = os.getenv('DB_NAME', 'college_advisor_analytics')
                username = os.getenv('DB_USERNAME', 'analytics_user')
                password = os.getenv('DB_PASSWORD', 'your_password')
                
                # Test connection
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=username,
                    password=password,
                    connect_timeout=10
                )
                
                # Test basic query
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                
                conn.close()
                return True, f"PostgreSQL connected successfully. Version: {version[:50]}..."
            else:
                return False, "Database config file not found"
                
        except ImportError:
            return False, "psycopg2 not installed. Run: pip install psycopg2-binary"
        except Exception as e:
            return False, f"PostgreSQL connection failed: {str(e)}"
    
    def verify_chromadb_connection(self) -> Tuple[bool, str]:
        """Verify ChromaDB connection."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Try to connect to ChromaDB
            try:
                # First try HTTP client (if server is running)
                client = chromadb.HttpClient(host="localhost", port=8000)
                client.heartbeat()
                return True, "ChromaDB HTTP server connected successfully"
            except:
                # Fall back to persistent client
                client = chromadb.PersistentClient(path="./chroma_data")
                collections = client.list_collections()
                return True, f"ChromaDB persistent client connected. Collections: {len(collections)}"
                
        except ImportError:
            return False, "chromadb not installed. Run: pip install chromadb"
        except Exception as e:
            return False, f"ChromaDB connection failed: {str(e)}"
    
    def verify_redis_connection(self) -> Tuple[bool, str]:
        """Verify Redis connection."""
        try:
            import redis
            
            # Load database config
            db_config_path = project_root / "configs" / "database_config.yaml"
            if db_config_path.exists():
                with open(db_config_path, 'r') as f:
                    db_config = yaml.safe_load(f)
                    
                redis_config = db_config['databases']['redis_cache']
                
                # Expand environment variables with defaults
                host = os.getenv('REDIS_HOST', 'localhost')
                port = int(os.getenv('REDIS_PORT', '6379'))
                db = int(os.getenv('REDIS_DB', '0'))
                password = os.getenv('REDIS_PASSWORD', '') or None
                
                # Test connection
                r = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                
                # Test basic operations
                r.ping()
                info = r.info()
                
                return True, f"Redis connected successfully. Version: {info.get('redis_version', 'unknown')}"
            else:
                return False, "Database config file not found"
                
        except ImportError:
            return False, "redis not installed. Run: pip install redis"
        except Exception as e:
            return False, f"Redis connection failed: {str(e)}"
    
    def verify_mongodb_connection(self) -> Tuple[bool, str]:
        """Verify MongoDB connection."""
        try:
            from pymongo import MongoClient
            
            # Load database config
            db_config_path = project_root / "configs" / "database_config.yaml"
            if db_config_path.exists():
                with open(db_config_path, 'r') as f:
                    db_config = yaml.safe_load(f)
                    
                mongo_config = db_config['databases']['mongodb']
                
                # Expand environment variables with defaults
                host = os.getenv('MONGO_HOST', 'localhost')
                port = int(os.getenv('MONGO_PORT', '27017'))
                database = os.getenv('MONGO_DB', 'college_advisor_docs')
                username = os.getenv('MONGO_USERNAME', '') or None
                password = os.getenv('MONGO_PASSWORD', '') or None
                
                # Build connection string
                if username and password:
                    uri = f"mongodb://{username}:{password}@{host}:{port}/{database}"
                else:
                    uri = f"mongodb://{host}:{port}/{database}"
                
                # Test connection
                client = MongoClient(
                    uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000
                )
                
                # Test basic operations
                server_info = client.server_info()
                
                return True, f"MongoDB connected successfully. Version: {server_info.get('version', 'unknown')}"
            else:
                return False, "Database config file not found"
                
        except ImportError:
            return False, "pymongo not installed. Run: pip install pymongo"
        except Exception as e:
            return False, f"MongoDB connection failed: {str(e)}"
    
    def verify_api_endpoints(self) -> Tuple[bool, str]:
        """Verify API endpoint connectivity."""
        try:
            import requests
            
            # Load API config
            api_config_path = project_root / "configs" / "api_config.yaml"
            if api_config_path.exists():
                with open(api_config_path, 'r') as f:
                    api_config = yaml.safe_load(f)
                    
                base_url = api_config['api_endpoints']['college_advisor_api']
                
                # Test basic connectivity
                response = requests.get(f"{base_url}/health", timeout=10)
                
                if response.status_code == 200:
                    return True, f"API endpoint {base_url} is accessible"
                else:
                    return False, f"API endpoint returned status {response.status_code}"
            else:
                return False, "API config file not found"
                
        except ImportError:
            return False, "requests not installed. Run: pip install requests"
        except requests.exceptions.ConnectionError:
            return False, "API endpoint is not accessible (connection refused)"
        except Exception as e:
            return False, f"API endpoint verification failed: {str(e)}"
    
    def verify_file_permissions(self) -> Tuple[bool, str]:
        """Verify file system permissions."""
        try:
            # Check data directories
            data_dirs = [
                "data/raw",
                "data/processed", 
                "data/training",
                "logs",
                "cache"
            ]
            
            issues = []
            for dir_path in data_dirs:
                full_path = project_root / dir_path
                if not full_path.exists():
                    full_path.mkdir(parents=True, exist_ok=True)
                
                # Test write permissions
                test_file = full_path / "test_write.tmp"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                except Exception as e:
                    issues.append(f"{dir_path}: {str(e)}")
            
            if issues:
                return False, f"Permission issues: {'; '.join(issues)}"
            else:
                return True, "All file permissions verified"
                
        except Exception as e:
            return False, f"File permission check failed: {str(e)}"
    
    def run_all_verifications(self) -> Dict[str, Any]:
        """Run all connection verifications."""
        logger.info("Starting connection verification...")
        
        verifications = [
            ("PostgreSQL Database", self.verify_postgresql_connection),
            ("ChromaDB Vector Store", self.verify_chromadb_connection),
            ("Redis Cache", self.verify_redis_connection),
            ("MongoDB Document Store", self.verify_mongodb_connection),
            ("API Endpoints", self.verify_api_endpoints),
            ("File Permissions", self.verify_file_permissions),
        ]
        
        results = {}
        all_passed = True
        
        for name, verification_func in verifications:
            logger.info(f"Verifying {name}...")
            try:
                success, message = verification_func()
                results[name] = {
                    "status": "PASS" if success else "FAIL",
                    "message": message
                }
                
                if success:
                    logger.info(f"✅ {name}: {message}")
                else:
                    logger.error(f"❌ {name}: {message}")
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"❌ {name}: Verification failed with exception: {str(e)}")
                results[name] = {
                    "status": "ERROR",
                    "message": f"Verification failed: {str(e)}"
                }
                all_passed = False
        
        results["overall_status"] = "PASS" if all_passed else "FAIL"
        return results


def main():
    """Main function to run connection verification."""
    print("🔍 CollegeAdvisor Data Pipeline - Connection Verification")
    print("=" * 60)
    
    verifier = ConnectionVerifier()
    results = verifier.run_all_verifications()
    
    print("\n📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    for service, result in results.items():
        if service == "overall_status":
            continue
            
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"{status_icon} {service}: {result['status']}")
        print(f"   {result['message']}")
        print()
    
    overall_status = results["overall_status"]
    if overall_status == "PASS":
        print("🎉 All connections verified successfully!")
        return 0
    else:
        print("⚠️  Some connections failed verification. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
