#!/usr/bin/env python3
"""
Comprehensive testing script for fine-tuning readiness.

Tests all components required for successful fine-tuning:
1. Data collection infrastructure
2. ChromaDB connectivity and collections
3. Data processing pipeline
4. Ollama connectivity
5. R2 storage (optional)
6. Training data generation

Provides detailed diagnostics and recommendations.
"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from college_advisor_data.config import config
from college_advisor_data.storage.chroma_client import ChromaDBClient
from college_advisor_data.storage.collection_manager import CollectionManager
from college_advisor_data.embedding.factory import EmbeddingFactory
from ai_training.finetuning_data_prep import FineTuningDataPreparator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FineTuningReadinessTest:
    """
    Comprehensive testing suite for fine-tuning readiness.
    """
    
    def __init__(self):
        self.results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "warnings": 0,
            "test_details": {}
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all readiness tests."""
        logger.info("=" * 80)
        logger.info("FINE-TUNING READINESS TEST SUITE")
        logger.info("=" * 80)
        
        # Test 1: Configuration
        await self.test_configuration()
        
        # Test 2: ChromaDB Connectivity
        await self.test_chromadb_connectivity()
        
        # Test 3: ChromaDB Collections
        await self.test_chromadb_collections()
        
        # Test 4: Embedding Generation
        await self.test_embedding_generation()
        
        # Test 5: Data Processing
        await self.test_data_processing()
        
        # Test 6: Ollama Connectivity
        await self.test_ollama_connectivity()
        
        # Test 7: R2 Storage (Optional)
        await self.test_r2_storage()
        
        # Test 8: Training Data Generation
        await self.test_training_data_generation()
        
        # Test 9: Data Quality
        await self.test_data_quality()
        
        # Generate report
        self.generate_report()
        
        return self.results
    
    async def test_configuration(self):
        """Test configuration settings."""
        logger.info("\n[TEST 1] Configuration Settings")
        logger.info("-" * 80)
        
        try:
            # Check critical settings
            checks = {
                "ChromaDB Host": config.chroma_host,
                "ChromaDB Port": config.chroma_port,
                "Embedding Model": config.embedding_model,
                "Ollama Host": config.ollama_host,
                "Data Directory": config.data_dir.exists()
            }
            
            all_passed = True
            for check_name, check_value in checks.items():
                status = "✓" if check_value else "✗"
                logger.info(f"  {status} {check_name}: {check_value}")
                if not check_value:
                    all_passed = False
            
            if all_passed:
                self._record_pass("configuration")
            else:
                self._record_fail("configuration", "Some configuration values missing")
                
        except Exception as e:
            self._record_fail("configuration", str(e))
    
    async def test_chromadb_connectivity(self):
        """Test ChromaDB connection."""
        logger.info("\n[TEST 2] ChromaDB Connectivity")
        logger.info("-" * 80)
        
        try:
            client = ChromaDBClient()
            heartbeat = client.heartbeat()
            
            logger.info(f"  ✓ ChromaDB connection successful")
            logger.info(f"  ✓ Heartbeat: {heartbeat}")
            
            self._record_pass("chromadb_connectivity")
            
        except Exception as e:
            logger.error(f"  ✗ ChromaDB connection failed: {e}")
            self._record_fail("chromadb_connectivity", str(e))
    
    async def test_chromadb_collections(self):
        """Test ChromaDB collection creation and management."""
        logger.info("\n[TEST 3] ChromaDB Collections")
        logger.info("-" * 80)
        
        try:
            manager = CollectionManager()
            
            # Create test collection
            test_client = manager.get_client("test_collection")
            
            # Test adding a document
            from college_advisor_data.schemas import DocumentChunk, DocumentMetadata
            
            test_chunk = DocumentChunk(
                chunk_id="test_001",
                content="This is a test document for fine-tuning readiness.",
                metadata=DocumentMetadata(
                    source_type="test",
                    data_type="test_data"
                )
            )
            
            test_client.add_documents([test_chunk])
            
            # Verify document was added
            count = test_client.collection.count()
            
            logger.info(f"  ✓ Collection created successfully")
            logger.info(f"  ✓ Document added successfully (count: {count})")
            
            # Clean up test collection
            test_client.client.delete_collection("test_collection")
            logger.info(f"  ✓ Test collection cleaned up")
            
            self._record_pass("chromadb_collections")
            
        except Exception as e:
            logger.error(f"  ✗ ChromaDB collections test failed: {e}")
            self._record_fail("chromadb_collections", str(e))
    
    async def test_embedding_generation(self):
        """Test embedding generation."""
        logger.info("\n[TEST 4] Embedding Generation")
        logger.info("-" * 80)
        
        try:
            embedder = EmbeddingFactory.create_embedder()
            
            # Test embedding generation
            test_texts = [
                "Harvard University is located in Cambridge, Massachusetts.",
                "Stanford University has a highly selective admissions process."
            ]
            
            embeddings = embedder.embed_documents(test_texts)
            
            logger.info(f"  ✓ Embedder created: {type(embedder).__name__}")
            logger.info(f"  ✓ Generated {len(embeddings)} embeddings")
            logger.info(f"  ✓ Embedding dimension: {len(embeddings[0])}")
            
            self._record_pass("embedding_generation")
            
        except Exception as e:
            logger.error(f"  ✗ Embedding generation failed: {e}")
            self._record_fail("embedding_generation", str(e))
    
    async def test_data_processing(self):
        """Test data processing pipeline."""
        logger.info("\n[TEST 5] Data Processing Pipeline")
        logger.info("-" * 80)
        
        try:
            from college_advisor_data.preprocessing.preprocessor import TextPreprocessor
            from college_advisor_data.preprocessing.chunker import TextChunker
            
            # Test preprocessor
            preprocessor = TextPreprocessor()
            test_text = "Harvard University, located in Cambridge, MA, is one of the top universities."
            processed = preprocessor.preprocess(test_text)
            
            logger.info(f"  ✓ Text preprocessor working")
            
            # Test chunker
            chunker = TextChunker()
            chunks = chunker.chunk_text(test_text * 100)  # Create longer text
            
            logger.info(f"  ✓ Text chunker working ({len(chunks)} chunks created)")
            
            self._record_pass("data_processing")
            
        except Exception as e:
            logger.error(f"  ✗ Data processing test failed: {e}")
            self._record_fail("data_processing", str(e))
    
    async def test_ollama_connectivity(self):
        """Test Ollama connectivity."""
        logger.info("\n[TEST 6] Ollama Connectivity")
        logger.info("-" * 80)
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Test Ollama API
                async with session.get(f"{config.ollama_host}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("models", [])
                        
                        logger.info(f"  ✓ Ollama connection successful")
                        logger.info(f"  ✓ Available models: {len(models)}")
                        
                        for model in models[:5]:  # Show first 5 models
                            logger.info(f"    - {model.get('name')}")
                        
                        self._record_pass("ollama_connectivity")
                    else:
                        raise Exception(f"Ollama API returned status {response.status}")
                        
        except Exception as e:
            logger.warning(f"  ⚠ Ollama connection failed: {e}")
            logger.warning(f"  ⚠ Make sure Ollama is running: ollama serve")
            self._record_warning("ollama_connectivity", str(e))
    
    async def test_r2_storage(self):
        """Test R2 storage connectivity (optional)."""
        logger.info("\n[TEST 7] Cloudflare R2 Storage (Optional)")
        logger.info("-" * 80)
        
        try:
            if not all([config.r2_account_id, config.r2_access_key_id, config.r2_secret_access_key]):
                logger.info("  ⚠ R2 credentials not configured (optional)")
                logger.info("  ℹ To enable R2: Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")
                self._record_warning("r2_storage", "Not configured")
                return
            
            from college_advisor_data.storage.r2_storage import R2StorageClient
            
            client = R2StorageClient()
            
            # Test bucket access
            objects = client.list_objects(max_keys=1)
            
            logger.info(f"  ✓ R2 connection successful")
            logger.info(f"  ✓ Bucket accessible: {client.bucket_name}")
            
            self._record_pass("r2_storage")
            
        except Exception as e:
            logger.warning(f"  ⚠ R2 storage test failed: {e}")
            self._record_warning("r2_storage", str(e))
    
    async def test_training_data_generation(self):
        """Test training data generation."""
        logger.info("\n[TEST 8] Training Data Generation")
        logger.info("-" * 80)
        
        try:
            preparator = FineTuningDataPreparator(
                output_dir=Path("data/test_finetuning")
            )
            
            # Create test Q&A pairs
            test_qa = [
                {
                    "question": "What is the admission rate at Harvard?",
                    "answer": "Harvard has an admission rate of approximately 3-4%.",
                    "category": "admissions"
                },
                {
                    "question": "Where is Stanford located?",
                    "answer": "Stanford University is located in Stanford, California.",
                    "category": "location"
                }
            ]
            
            # Test different formats
            alpaca_file = preparator.prepare_instruction_dataset(test_qa, "alpaca")
            jsonl_file = preparator.prepare_instruction_dataset(test_qa, "jsonl")
            ollama_file = preparator.prepare_instruction_dataset(test_qa, "ollama")
            
            logger.info(f"  ✓ Alpaca format generated: {alpaca_file}")
            logger.info(f"  ✓ JSONL format generated: {jsonl_file}")
            logger.info(f"  ✓ Ollama format generated: {ollama_file}")
            
            # Test Modelfile creation
            modelfile = preparator.create_ollama_modelfile()
            logger.info(f"  ✓ Modelfile created: {modelfile}")
            
            self._record_pass("training_data_generation")
            
        except Exception as e:
            logger.error(f"  ✗ Training data generation failed: {e}")
            self._record_fail("training_data_generation", str(e))
    
    async def test_data_quality(self):
        """Test data quality and completeness."""
        logger.info("\n[TEST 9] Data Quality")
        logger.info("-" * 80)
        
        try:
            # Check for existing data
            data_dir = Path("data")
            
            checks = {
                "Raw data directory": (data_dir / "raw").exists(),
                "Processed data directory": (data_dir / "processed").exists(),
                "Training data directory": (data_dir / "training").exists(),
                "Sample data available": (data_dir / "sample").exists()
            }
            
            all_passed = True
            for check_name, check_result in checks.items():
                status = "✓" if check_result else "⚠"
                logger.info(f"  {status} {check_name}")
                if not check_result:
                    all_passed = False
            
            if all_passed:
                self._record_pass("data_quality")
            else:
                self._record_warning("data_quality", "Some data directories missing")
                
        except Exception as e:
            logger.error(f"  ✗ Data quality test failed: {e}")
            self._record_fail("data_quality", str(e))
    
    def _record_pass(self, test_name: str):
        """Record a passed test."""
        self.results["tests_passed"] += 1
        self.results["test_details"][test_name] = {"status": "PASS"}
    
    def _record_fail(self, test_name: str, error: str):
        """Record a failed test."""
        self.results["tests_failed"] += 1
        self.results["test_details"][test_name] = {"status": "FAIL", "error": error}
    
    def _record_warning(self, test_name: str, message: str):
        """Record a warning."""
        self.results["warnings"] += 1
        self.results["test_details"][test_name] = {"status": "WARNING", "message": message}
    
    def generate_report(self):
        """Generate final test report."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"Tests Passed: {self.results['tests_passed']}")
        logger.info(f"Tests Failed: {self.results['tests_failed']}")
        logger.info(f"Warnings: {self.results['warnings']}")
        
        if self.results["tests_failed"] == 0:
            logger.info("\n✓ ALL CRITICAL TESTS PASSED - SYSTEM READY FOR FINE-TUNING")
        else:
            logger.warning("\n✗ SOME TESTS FAILED - REVIEW ERRORS BEFORE PROCEEDING")
        
        # Save detailed report
        report_file = Path("data/finetuning_readiness_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\nDetailed report saved to: {report_file}")
        logger.info("=" * 80)


async def main():
    """Main entry point."""
    tester = FineTuningReadinessTest()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["tests_failed"] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())

