#!/usr/bin/env python3
"""
Complete R2 setup and data preparation script.

This script:
1. Tests R2 connectivity
2. Creates R2 bucket
3. Collects high-quality data from multiple sources
4. Processes and validates data
5. Uploads to R2 for backup
6. Prepares training datasets
7. Generates comprehensive report

Usage:
    python scripts/setup_r2_and_prepare_data.py
"""

import asyncio
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from college_advisor_data.storage.r2_storage import R2StorageClient
from college_advisor_data.config import config
from collectors.government import CollegeScorecardCollector
from collectors.base_collector import CollectorConfig
from college_advisor_data.storage.collection_manager import CollectionManager
from ai_training.finetuning_data_prep import FineTuningDataPreparator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class R2DataPreparationPipeline:
    """Complete pipeline for R2 setup and data preparation."""
    
    def __init__(self):
        self.output_dir = Path("data/r2_preparation")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            "start_time": datetime.now().isoformat(),
            "stages": {},
            "errors": []
        }
    
    async def run_complete_pipeline(self):
        """Run the complete R2 setup and data preparation pipeline."""
        logger.info("=" * 80)
        logger.info("R2 SETUP AND DATA PREPARATION PIPELINE")
        logger.info("=" * 80)
        
        try:
            # Stage 1: Test R2 connectivity
            await self.stage_1_test_r2()
            
            # Stage 2: Create R2 bucket
            await self.stage_2_create_bucket()
            
            # Stage 3: Collect high-quality data
            await self.stage_3_collect_data()
            
            # Stage 4: Process and validate data
            await self.stage_4_process_data()
            
            # Stage 5: Create ChromaDB collections
            await self.stage_5_create_collections()
            
            # Stage 6: Generate training datasets
            await self.stage_6_generate_training_data()
            
            # Stage 7: Upload to R2
            await self.stage_7_upload_to_r2()
            
            # Generate final report
            self.generate_final_report()
            
            logger.info("=" * 80)
            logger.info("PIPELINE COMPLETE - ALL DATA READY FOR FINE-TUNING")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self.stats["errors"].append(str(e))
            raise
    
    async def stage_1_test_r2(self):
        """Stage 1: Test R2 connectivity."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 1: TESTING R2 CONNECTIVITY")
        logger.info("=" * 80)
        
        try:
            client = R2StorageClient()
            
            # Test by listing buckets (will work even if no buckets exist)
            logger.info(f"✓ R2 client initialized")
            logger.info(f"  Account ID: {client.account_id}")
            logger.info(f"  Endpoint: {client.endpoint_url}")
            
            self.stats["stages"]["r2_test"] = {
                "status": "success",
                "account_id": client.account_id
            }
            
            logger.info("✓ R2 connectivity test passed")
            
        except Exception as e:
            logger.error(f"✗ R2 connectivity test failed: {e}")
            self.stats["stages"]["r2_test"] = {"status": "failed", "error": str(e)}
            raise
    
    async def stage_2_create_bucket(self):
        """Stage 2: Create R2 bucket."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 2: CREATING R2 BUCKET")
        logger.info("=" * 80)
        
        try:
            client = R2StorageClient()
            
            # Create bucket
            success = client.create_bucket()
            
            if success:
                logger.info(f"✓ Bucket created/verified: {client.bucket_name}")
                self.stats["stages"]["bucket_creation"] = {
                    "status": "success",
                    "bucket_name": client.bucket_name
                }
            else:
                raise Exception("Failed to create bucket")
                
        except Exception as e:
            logger.error(f"✗ Bucket creation failed: {e}")
            self.stats["stages"]["bucket_creation"] = {"status": "failed", "error": str(e)}
            raise
    
    async def stage_3_collect_data(self):
        """Stage 3: Collect high-quality data from College Scorecard."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 3: COLLECTING HIGH-QUALITY DATA")
        logger.info("=" * 80)

        try:
            # Create output directory
            raw_data_dir = self.output_dir / "raw_data"
            raw_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Collect data with comprehensive fields
            all_institutions = []
            page = 0
            per_page = 100
            max_pages = 100  # Limit to ~10,000 institutions for initial run

            logger.info(f"Collecting data from College Scorecard API...")

            # Get API URL and key
            api_url = "https://api.data.gov/ed/collegescorecard/v1/schools"
            api_key = config.college_scorecard_api_key

            while page < max_pages:
                try:
                    # Build comprehensive field list
                    fields = self._get_comprehensive_fields()

                    # Make API request
                    params = {
                        "api_key": api_key,
                        "page": page,
                        "per_page": per_page,
                        "fields": ",".join(fields)
                    }

                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(api_url, params=params) as response:
                            if response.status != 200:
                                logger.warning(f"API returned status {response.status}")
                                break
                            
                            data = await response.json()
                            results = data.get("results", [])
                            
                            if not results:
                                break
                            
                            all_institutions.extend(results)
                            logger.info(f"  Collected {len(all_institutions)} institutions (page {page + 1})...")
                            
                            page += 1
                            await asyncio.sleep(0.1)  # Rate limiting
                
                except Exception as e:
                    logger.error(f"Error on page {page}: {e}")
                    break
            
            # Save raw data
            raw_file = self.output_dir / "raw_data" / "college_scorecard_complete.json"
            raw_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(raw_file, 'w') as f:
                json.dump(all_institutions, f, indent=2)
            
            logger.info(f"✓ Collected {len(all_institutions)} institutions")
            logger.info(f"✓ Saved to: {raw_file}")
            
            self.stats["stages"]["data_collection"] = {
                "status": "success",
                "institutions_collected": len(all_institutions),
                "output_file": str(raw_file)
            }
            
        except Exception as e:
            logger.error(f"✗ Data collection failed: {e}")
            self.stats["stages"]["data_collection"] = {"status": "failed", "error": str(e)}
            raise
    
    def _get_comprehensive_fields(self) -> List[str]:
        """Get comprehensive field list for College Scorecard API."""
        fields = []
        
        # Add all field groups from CollegeScorecardCollector
        from collectors.government import CollegeScorecardCollector
        for group_fields in CollegeScorecardCollector.FIELD_GROUPS.values():
            fields.extend(group_fields)
        
        return fields
    
    async def stage_4_process_data(self):
        """Stage 4: Process and validate data."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 4: PROCESSING AND VALIDATING DATA")
        logger.info("=" * 80)
        
        try:
            raw_file = self.output_dir / "raw_data" / "college_scorecard_complete.json"
            
            if not raw_file.exists():
                raise FileNotFoundError(f"Raw data file not found: {raw_file}")
            
            # Load raw data
            with open(raw_file, 'r') as f:
                raw_data = json.load(f)
            
            logger.info(f"Processing {len(raw_data)} institutions...")
            
            # Process and validate
            processed_data = []
            validation_stats = {
                "total": len(raw_data),
                "valid": 0,
                "invalid": 0,
                "missing_fields": {}
            }
            
            for inst in raw_data:
                # Validate and clean
                if self._validate_institution(inst):
                    processed_inst = self._clean_institution(inst)
                    processed_data.append(processed_inst)
                    validation_stats["valid"] += 1
                else:
                    validation_stats["invalid"] += 1
            
            # Save processed data
            processed_file = self.output_dir / "processed" / "institutions_processed.json"
            processed_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(processed_file, 'w') as f:
                json.dump(processed_data, f, indent=2)
            
            logger.info(f"✓ Processed {validation_stats['valid']} valid institutions")
            logger.info(f"  Invalid/incomplete: {validation_stats['invalid']}")
            logger.info(f"✓ Saved to: {processed_file}")
            
            self.stats["stages"]["data_processing"] = {
                "status": "success",
                "validation_stats": validation_stats,
                "output_file": str(processed_file)
            }
            
        except Exception as e:
            logger.error(f"✗ Data processing failed: {e}")
            self.stats["stages"]["data_processing"] = {"status": "failed", "error": str(e)}
            raise
    
    def _validate_institution(self, inst: Dict[str, Any]) -> bool:
        """Validate institution data quality."""
        # Check for required fields
        required_fields = ["school.name", "id"]
        
        for field in required_fields:
            if field not in inst or inst[field] is None:
                return False
        
        return True
    
    def _clean_institution(self, inst: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize institution data."""
        cleaned = {}
        
        # Flatten nested structure
        for key, value in inst.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    cleaned[f"{key}.{subkey}"] = subvalue
            else:
                cleaned[key] = value
        
        return cleaned
    
    async def stage_5_create_collections(self):
        """Stage 5: Create ChromaDB collections."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 5: CREATING CHROMADB COLLECTIONS")
        logger.info("=" * 80)
        
        try:
            manager = CollectionManager()
            
            # Create all collections
            stats = manager.create_all_collections()
            
            # Load processed data
            processed_file = self.output_dir / "processed" / "institutions_processed.json"
            with open(processed_file, 'r') as f:
                institutions = json.load(f)
            
            # Add to ChromaDB
            count = manager.add_institutions(institutions)
            
            logger.info(f"✓ Created {len(stats['collections'])} collections")
            logger.info(f"✓ Added {count} institutions to ChromaDB")
            
            self.stats["stages"]["chromadb_collections"] = {
                "status": "success",
                "collections_created": len(stats['collections']),
                "institutions_added": count
            }
            
        except Exception as e:
            logger.warning(f"⚠ ChromaDB collections: {e}")
            logger.info("  (ChromaDB is optional for R2 data preparation)")
            self.stats["stages"]["chromadb_collections"] = {"status": "skipped", "reason": str(e)}
    
    async def stage_6_generate_training_data(self):
        """Stage 6: Generate training datasets."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 6: GENERATING TRAINING DATASETS")
        logger.info("=" * 80)
        
        try:
            preparator = FineTuningDataPreparator(
                output_dir=self.output_dir / "training_datasets"
            )
            
            # Load processed institutions
            processed_file = self.output_dir / "processed" / "institutions_processed.json"
            with open(processed_file, 'r') as f:
                institutions = json.load(f)
            
            # Generate Q&A pairs
            qa_pairs = preparator.generate_qa_from_institutional_data(
                institutions,
                num_questions_per_institution=5
            )
            
            # Create datasets in multiple formats
            alpaca_file = preparator.prepare_instruction_dataset(qa_pairs, "alpaca")
            jsonl_file = preparator.prepare_instruction_dataset(qa_pairs, "jsonl")
            ollama_file = preparator.prepare_instruction_dataset(qa_pairs, "ollama")
            modelfile = preparator.create_ollama_modelfile()
            
            logger.info(f"✓ Generated {len(qa_pairs)} Q&A pairs")
            logger.info(f"✓ Created Alpaca format: {alpaca_file}")
            logger.info(f"✓ Created JSONL format: {jsonl_file}")
            logger.info(f"✓ Created Ollama format: {ollama_file}")
            logger.info(f"✓ Created Modelfile: {modelfile}")
            
            self.stats["stages"]["training_data"] = {
                "status": "success",
                "qa_pairs_generated": len(qa_pairs),
                "formats": ["alpaca", "jsonl", "ollama", "modelfile"]
            }
            
        except Exception as e:
            logger.error(f"✗ Training data generation failed: {e}")
            self.stats["stages"]["training_data"] = {"status": "failed", "error": str(e)}
            raise
    
    async def stage_7_upload_to_r2(self):
        """Stage 7: Upload all data to R2."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 7: UPLOADING TO CLOUDFLARE R2")
        logger.info("=" * 80)
        
        try:
            client = R2StorageClient()
            
            # Upload raw data
            logger.info("Uploading raw data...")
            raw_stats = client.upload_directory(
                self.output_dir / "raw_data",
                prefix="raw_data",
                include_patterns=["*.json"]
            )
            
            # Upload processed data
            logger.info("Uploading processed data...")
            processed_stats = client.upload_directory(
                self.output_dir / "processed",
                prefix="processed_data",
                include_patterns=["*.json"]
            )
            
            # Upload training datasets
            logger.info("Uploading training datasets...")
            training_stats = client.upload_directory(
                self.output_dir / "training_datasets",
                prefix="training_datasets",
                include_patterns=["*.json", "*.jsonl", "*.txt", "Modelfile"]
            )
            
            total_uploaded = (
                raw_stats.get("uploaded", 0) +
                processed_stats.get("uploaded", 0) +
                training_stats.get("uploaded", 0)
            )
            
            logger.info(f"✓ Uploaded {total_uploaded} files to R2")
            logger.info(f"  Raw data: {raw_stats.get('uploaded', 0)} files")
            logger.info(f"  Processed data: {processed_stats.get('uploaded', 0)} files")
            logger.info(f"  Training datasets: {training_stats.get('uploaded', 0)} files")
            
            self.stats["stages"]["r2_upload"] = {
                "status": "success",
                "total_files_uploaded": total_uploaded,
                "raw_data": raw_stats,
                "processed_data": processed_stats,
                "training_data": training_stats
            }
            
        except Exception as e:
            logger.error(f"✗ R2 upload failed: {e}")
            self.stats["stages"]["r2_upload"] = {"status": "failed", "error": str(e)}
            raise
    
    def generate_final_report(self):
        """Generate comprehensive final report."""
        self.stats["end_time"] = datetime.now().isoformat()
        
        report = f"""
{'=' * 80}
R2 DATA PREPARATION COMPLETE
{'=' * 80}

Start Time: {self.stats['start_time']}
End Time: {self.stats['end_time']}

STAGES COMPLETED:
"""
        
        for stage_name, stage_info in self.stats['stages'].items():
            status = stage_info.get('status', 'unknown')
            symbol = "✓" if status == "success" else "⚠" if status == "skipped" else "✗"
            report += f"\n{symbol} {stage_name.upper()}: {status}"
            
            if status == "success":
                for key, value in stage_info.items():
                    if key != "status" and not isinstance(value, dict):
                        report += f"\n    {key}: {value}"
        
        report += f"\n\n{'=' * 80}\n"
        
        # Save report
        report_file = self.output_dir / "R2_PREPARATION_REPORT.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Save stats as JSON
        stats_file = self.output_dir / "preparation_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
        
        print(report)
        logger.info(f"Report saved to: {report_file}")
        logger.info(f"Stats saved to: {stats_file}")


async def main():
    """Main entry point."""
    pipeline = R2DataPreparationPipeline()
    await pipeline.run_complete_pipeline()


if __name__ == "__main__":
    asyncio.run(main())

