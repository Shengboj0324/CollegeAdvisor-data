#!/usr/bin/env python3
"""
Comprehensive R2 setup with real data collection and processing.

This script:
1. Uses existing sample data as foundation
2. Collects additional data from College Scorecard
3. Processes and validates all data
4. Creates high-quality training datasets
5. Uploads everything to R2
"""

import asyncio
import sys
import logging
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from college_advisor_data.storage.r2_storage import R2StorageClient
from college_advisor_data.config import config
from ai_training.finetuning_data_prep import FineTuningDataPreparator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveR2Setup:
    """Complete R2 setup with comprehensive data preparation."""
    
    def __init__(self):
        self.output_dir = Path("data/r2_finetuning")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            "start_time": datetime.now().isoformat(),
            "stages": {},
            "data_quality": {}
        }
    
    async def run_complete_setup(self):
        """Run complete R2 setup."""
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE R2 SETUP AND DATA PREPARATION")
        logger.info("=" * 80)
        
        try:
            # Stage 1: Verify R2 bucket
            self.stage_1_verify_r2()
            
            # Stage 2: Prepare comprehensive dataset
            await self.stage_2_prepare_dataset()
            
            # Stage 3: Generate training data
            await self.stage_3_generate_training_data()
            
            # Stage 4: Upload to R2
            await self.stage_4_upload_to_r2()
            
            # Generate report
            self.generate_report()
            
            logger.info("=" * 80)
            logger.info("✓ R2 SETUP COMPLETE - DATA READY FOR FINE-TUNING")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Setup failed: {e}", exc_info=True)
            raise
    
    def stage_1_verify_r2(self):
        """Stage 1: Verify R2 bucket exists."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 1: VERIFYING R2 BUCKET")
        logger.info("=" * 80)
        
        try:
            client = R2StorageClient()
            
            # Verify bucket exists
            success = client.create_bucket()
            
            if success:
                logger.info(f"✓ R2 bucket verified: {client.bucket_name}")
                logger.info(f"  Endpoint: {client.endpoint_url}")
                
                self.stats["stages"]["r2_verification"] = {
                    "status": "success",
                    "bucket": client.bucket_name
                }
            else:
                raise Exception("Failed to verify R2 bucket")
                
        except Exception as e:
            logger.error(f"✗ R2 verification failed: {e}")
            raise
    
    async def stage_2_prepare_dataset(self):
        """Stage 2: Prepare comprehensive dataset."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 2: PREPARING COMPREHENSIVE DATASET")
        logger.info("=" * 80)
        
        try:
            # Load existing sample data
            sample_dir = Path("data/sample")
            
            all_data = []
            
            # Load colleges.json
            colleges_file = sample_dir / "colleges.json"
            if colleges_file.exists():
                with open(colleges_file, 'r') as f:
                    colleges = json.load(f)
                    all_data.extend(colleges if isinstance(colleges, list) else [colleges])
                    logger.info(f"✓ Loaded {len(colleges if isinstance(colleges, list) else [colleges])} colleges from sample data")
            
            # Load combined_data.json
            combined_file = sample_dir / "combined_data.json"
            if combined_file.exists():
                with open(combined_file, 'r') as f:
                    combined = json.load(f)
                    if isinstance(combined, dict) and "institutions" in combined:
                        all_data.extend(combined["institutions"])
                        logger.info(f"✓ Loaded {len(combined['institutions'])} institutions from combined data")
            
            # Collect additional data from College Scorecard
            logger.info("Collecting additional data from College Scorecard...")
            scorecard_data = await self._collect_scorecard_data()
            all_data.extend(scorecard_data)
            
            logger.info(f"✓ Total institutions collected: {len(all_data)}")
            
            # Process and validate
            processed_data = self._process_and_validate(all_data)
            
            # Save processed data
            processed_file = self.output_dir / "processed_institutions.json"
            with open(processed_file, 'w') as f:
                json.dump(processed_data, f, indent=2)
            
            logger.info(f"✓ Processed {len(processed_data)} valid institutions")
            logger.info(f"✓ Saved to: {processed_file}")
            
            self.stats["stages"]["dataset_preparation"] = {
                "status": "success",
                "total_collected": len(all_data),
                "valid_institutions": len(processed_data),
                "output_file": str(processed_file)
            }
            
            self.stats["data_quality"] = {
                "total_institutions": len(processed_data),
                "data_completeness": self._calculate_completeness(processed_data)
            }
            
        except Exception as e:
            logger.error(f"✗ Dataset preparation failed: {e}")
            raise
    
    async def _collect_scorecard_data(self) -> List[Dict]:
        """Collect data from College Scorecard API."""
        collected = []
        
        try:
            import aiohttp
            
            api_url = "https://api.data.gov/ed/collegescorecard/v1/schools"
            api_key = config.college_scorecard_api_key or "DEMO_KEY"
            
            # Collect multiple pages
            for page in range(10):  # Collect 10 pages = ~1000 institutions
                params = {
                    "api_key": api_key,
                    "page": page,
                    "per_page": 100,
                    "fields": "id,school.name,school.city,school.state,school.zip,school.school_url,school.price_calculator_url,latest.admissions.admission_rate.overall,latest.student.size,latest.cost.tuition.in_state,latest.cost.tuition.out_of_state,latest.academics.program_percentage.business_marketing,latest.academics.program_percentage.engineering"
                }
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(api_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                            if response.status == 200:
                                data = await response.json()
                                results = data.get("results", [])
                                
                                if not results:
                                    break
                                
                                collected.extend(results)
                                logger.info(f"  Collected page {page + 1}: {len(results)} institutions (total: {len(collected)})")
                                
                                await asyncio.sleep(0.2)  # Rate limiting
                            else:
                                logger.warning(f"  API returned status {response.status} on page {page}")
                                break
                                
                except asyncio.TimeoutError:
                    logger.warning(f"  Timeout on page {page}")
                    break
                except Exception as e:
                    logger.warning(f"  Error on page {page}: {e}")
                    break
            
            logger.info(f"✓ Collected {len(collected)} institutions from College Scorecard")
            
        except Exception as e:
            logger.warning(f"College Scorecard collection failed: {e}")
        
        return collected
    
    def _process_and_validate(self, data: List[Dict]) -> List[Dict]:
        """Process and validate institution data."""
        processed = []
        
        for inst in data:
            # Validate required fields
            name = None
            if isinstance(inst, dict):
                # Try different name field formats
                name = (inst.get("school.name") or 
                       inst.get("name") or 
                       (inst.get("school", {}).get("name") if isinstance(inst.get("school"), dict) else None))
            
            if not name:
                continue
            
            # Normalize structure
            normalized = self._normalize_institution(inst)
            
            if normalized:
                processed.append(normalized)
        
        # Remove duplicates by name
        seen_names = set()
        unique_processed = []
        
        for inst in processed:
            name = inst.get("name", "").lower()
            if name and name not in seen_names:
                seen_names.add(name)
                unique_processed.append(inst)
        
        return unique_processed
    
    def _normalize_institution(self, inst: Dict) -> Dict:
        """Normalize institution data structure."""
        normalized = {}
        
        # Extract name
        normalized["name"] = (
            inst.get("school.name") or 
            inst.get("name") or 
            (inst.get("school", {}).get("name") if isinstance(inst.get("school"), dict) else None)
        )
        
        # Extract location
        normalized["city"] = (
            inst.get("school.city") or 
            inst.get("city") or 
            (inst.get("school", {}).get("city") if isinstance(inst.get("school"), dict) else None)
        )
        
        normalized["state"] = (
            inst.get("school.state") or 
            inst.get("state") or 
            (inst.get("school", {}).get("state") if isinstance(inst.get("school"), dict) else None)
        )
        
        # Extract admissions data
        normalized["admission_rate"] = (
            inst.get("latest.admissions.admission_rate.overall") or
            inst.get("admission_rate") or
            (inst.get("latest", {}).get("admissions", {}).get("admission_rate", {}).get("overall") 
             if isinstance(inst.get("latest"), dict) else None)
        )
        
        # Extract student size
        normalized["student_size"] = (
            inst.get("latest.student.size") or
            inst.get("student_size") or
            (inst.get("latest", {}).get("student", {}).get("size") 
             if isinstance(inst.get("latest"), dict) else None)
        )
        
        # Extract tuition
        normalized["tuition_in_state"] = (
            inst.get("latest.cost.tuition.in_state") or
            inst.get("tuition_in_state") or
            (inst.get("latest", {}).get("cost", {}).get("tuition", {}).get("in_state") 
             if isinstance(inst.get("latest"), dict) else None)
        )
        
        normalized["tuition_out_of_state"] = (
            inst.get("latest.cost.tuition.out_of_state") or
            inst.get("tuition_out_of_state") or
            (inst.get("latest", {}).get("cost", {}).get("tuition", {}).get("out_of_state") 
             if isinstance(inst.get("latest"), dict) else None)
        )
        
        # Extract URL
        normalized["url"] = (
            inst.get("school.school_url") or
            inst.get("url") or
            (inst.get("school", {}).get("school_url") if isinstance(inst.get("school"), dict) else None)
        )
        
        # Add any other fields
        for key, value in inst.items():
            if key not in normalized and not isinstance(value, dict):
                normalized[key] = value
        
        return normalized
    
    def _calculate_completeness(self, data: List[Dict]) -> float:
        """Calculate data completeness score."""
        if not data:
            return 0.0
        
        important_fields = ["name", "city", "state", "admission_rate", "student_size", "tuition_in_state"]
        
        total_score = 0
        for inst in data:
            field_count = sum(1 for field in important_fields if inst.get(field) is not None)
            total_score += field_count / len(important_fields)
        
        return round(total_score / len(data) * 100, 2)
    
    async def stage_3_generate_training_data(self):
        """Stage 3: Generate training datasets."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 3: GENERATING TRAINING DATASETS")
        logger.info("=" * 80)
        
        try:
            # Load processed data
            processed_file = self.output_dir / "processed_institutions.json"
            with open(processed_file, 'r') as f:
                institutions = json.load(f)
            
            # Create training data preparator
            training_dir = self.output_dir / "training_datasets"
            preparator = FineTuningDataPreparator(output_dir=training_dir)
            
            # Generate Q&A pairs
            qa_pairs = preparator.generate_qa_from_institutional_data(
                institutions,
                num_questions_per_institution=5
            )
            
            logger.info(f"✓ Generated {len(qa_pairs)} Q&A pairs")
            
            # Create datasets in multiple formats
            alpaca_file = preparator.prepare_instruction_dataset(qa_pairs, "alpaca")
            jsonl_file = preparator.prepare_instruction_dataset(qa_pairs, "jsonl")
            ollama_file = preparator.prepare_instruction_dataset(qa_pairs, "ollama")
            modelfile = preparator.create_ollama_modelfile()
            
            logger.info(f"✓ Created Alpaca format: {alpaca_file}")
            logger.info(f"✓ Created JSONL format: {jsonl_file}")
            logger.info(f"✓ Created Ollama format: {ollama_file}")
            logger.info(f"✓ Created Modelfile: {modelfile}")
            
            self.stats["stages"]["training_data"] = {
                "status": "success",
                "qa_pairs": len(qa_pairs),
                "formats": ["alpaca", "jsonl", "ollama", "modelfile"]
            }
            
        except Exception as e:
            logger.error(f"✗ Training data generation failed: {e}")
            raise
    
    async def stage_4_upload_to_r2(self):
        """Stage 4: Upload all data to R2."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 4: UPLOADING TO CLOUDFLARE R2")
        logger.info("=" * 80)
        
        try:
            client = R2StorageClient()
            
            # Upload processed data
            logger.info("Uploading processed institutions...")
            processed_file = self.output_dir / "processed_institutions.json"
            client.upload_file(processed_file, "processed_data/institutions.json")
            
            # Upload training datasets
            logger.info("Uploading training datasets...")
            training_dir = self.output_dir / "training_datasets"
            
            stats = client.upload_directory(
                training_dir,
                prefix="training_datasets",
                include_patterns=["*.json", "*.jsonl", "*.txt", "Modelfile"]
            )
            
            logger.info(f"✓ Uploaded {stats.get('uploaded', 0)} training files to R2")
            
            self.stats["stages"]["r2_upload"] = {
                "status": "success",
                "files_uploaded": stats.get('uploaded', 0) + 1
            }
            
        except Exception as e:
            logger.error(f"✗ R2 upload failed: {e}")
            raise
    
    def generate_report(self):
        """Generate final report."""
        self.stats["end_time"] = datetime.now().isoformat()
        
        report = f"""
{'=' * 80}
R2 SETUP AND DATA PREPARATION - FINAL REPORT
{'=' * 80}

Start Time: {self.stats['start_time']}
End Time: {self.stats['end_time']}

DATA QUALITY METRICS:
  Total Institutions: {self.stats['data_quality'].get('total_institutions', 0)}
  Data Completeness: {self.stats['data_quality'].get('data_completeness', 0)}%

STAGES COMPLETED:
"""
        
        for stage_name, stage_info in self.stats['stages'].items():
            status = stage_info.get('status', 'unknown')
            symbol = "✓" if status == "success" else "✗"
            report += f"\n{symbol} {stage_name.upper()}: {status}"
            
            for key, value in stage_info.items():
                if key != "status" and not isinstance(value, dict):
                    report += f"\n    {key}: {value}"
        
        report += f"\n\n{'=' * 80}\n"
        report += "\nNEXT STEPS:\n"
        report += "1. Review training datasets in: data/r2_finetuning/training_datasets/\n"
        report += "2. Fine-tune model: cd data/r2_finetuning/training_datasets && ollama create collegeadvisor -f Modelfile\n"
        report += "3. Test model: ollama run collegeadvisor\n"
        report += "4. All data backed up to R2 bucket: collegeadvisor-finetuning-data\n"
        report += f"\n{'=' * 80}\n"
        
        # Save report
        report_file = self.output_dir / "SETUP_REPORT.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Save stats
        stats_file = self.output_dir / "setup_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
        
        print(report)
        logger.info(f"Report saved to: {report_file}")


async def main():
    """Main entry point."""
    setup = ComprehensiveR2Setup()
    await setup.run_complete_setup()


if __name__ == "__main__":
    asyncio.run(main())

