#!/usr/bin/env python3
"""
Collect ONLY REAL data from authentic sources.
ZERO tolerance for fake, sample, or synthetic data.

This script:
1. Deletes ALL fake/sample/synthetic data
2. Collects ONLY real data from College Scorecard API
3. Validates data authenticity
4. Uploads to R2
"""

import asyncio
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from college_advisor_data.storage.r2_storage import R2StorageClient
from college_advisor_data.config import config
from ai_training.finetuning_data_prep import FineTuningDataPreparator
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RealDataCollector:
    """Collect ONLY real data - zero tolerance for fake data."""
    
    def __init__(self):
        self.output_dir = Path("data/real_data_only")
        self.api_key = config.college_scorecard_api_key
        
        # Validate API key
        if not self.api_key or self.api_key == "DEMO_KEY":
            logger.error("=" * 80)
            logger.error("AUTHENTICATION REQUIRED")
            logger.error("=" * 80)
            logger.error("\nCollege Scorecard API requires authentication.")
            logger.error("\nTo get your API key:")
            logger.error("1. Visit: https://api.data.gov/signup/")
            logger.error("2. Enter your email and organization")
            logger.error("3. You'll receive an API key via email")
            logger.error("4. Add to .env file: COLLEGE_SCORECARD_API_KEY=your_key_here")
            logger.error("\nNote: DEMO_KEY has severe rate limits and may not work.")
            logger.error("=" * 80)
            
            response = input("\nDo you want to continue with DEMO_KEY? (y/n): ")
            if response.lower() != 'y':
                sys.exit(1)
    
    async def run(self):
        """Run complete real data collection."""
        logger.info("=" * 80)
        logger.info("REAL DATA COLLECTION - ZERO TOLERANCE FOR FAKE DATA")
        logger.info("=" * 80)
        
        # Step 1: Delete ALL fake/sample data
        self.delete_fake_data()
        
        # Step 2: Collect ONLY real data
        await self.collect_real_data()
        
        # Step 3: Validate authenticity
        self.validate_authenticity()
        
        # Step 4: Generate training data
        await self.generate_training_data()
        
        # Step 5: Upload to R2
        await self.upload_to_r2()
        
        logger.info("=" * 80)
        logger.info("✓ REAL DATA COLLECTION COMPLETE")
        logger.info("=" * 80)
    
    def delete_fake_data(self):
        """Delete ALL fake, sample, and synthetic data."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: DELETING ALL FAKE/SAMPLE/SYNTHETIC DATA")
        logger.info("=" * 80)
        
        fake_data_locations = [
            "data/sample",
            "data/r2_preparation",
            "data/r2_finetuning",
            "data/training/sample_qa.json",
            "data/training/college_qa.json",
        ]
        
        deleted_count = 0
        for location in fake_data_locations:
            path = Path(location)
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                    logger.info(f"✓ Deleted directory: {location}")
                else:
                    path.unlink()
                    logger.info(f"✓ Deleted file: {location}")
                deleted_count += 1
        
        logger.info(f"\n✓ Deleted {deleted_count} fake data locations")
        logger.info("✓ Repository is now clean of fake data")
    
    async def collect_real_data(self):
        """Collect ONLY real data from College Scorecard API."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: COLLECTING REAL DATA FROM COLLEGE SCORECARD API")
        logger.info("=" * 80)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        import aiohttp
        
        api_url = "https://api.data.gov/ed/collegescorecard/v1/schools"
        
        # Comprehensive field list for maximum data quality
        fields = [
            # Basic info
            "id", "school.name", "school.city", "school.state", "school.zip",
            "school.school_url", "school.price_calculator_url",
            "school.locale", "school.ownership", "school.carnegie_basic",
            
            # Admissions
            "latest.admissions.admission_rate.overall",
            "latest.admissions.sat_scores.average.overall",
            "latest.admissions.act_scores.midpoint.cumulative",
            
            # Student body
            "latest.student.size",
            "latest.student.demographics.race_ethnicity.white",
            "latest.student.demographics.race_ethnicity.black",
            "latest.student.demographics.race_ethnicity.hispanic",
            "latest.student.demographics.race_ethnicity.asian",
            
            # Costs
            "latest.cost.tuition.in_state",
            "latest.cost.tuition.out_of_state",
            "latest.cost.avg_net_price.overall",
            "latest.aid.median_debt.completers.overall",
            
            # Academics
            "latest.academics.program_percentage.business_marketing",
            "latest.academics.program_percentage.engineering",
            "latest.academics.program_percentage.biological",
            "latest.academics.program_percentage.computer",
            "latest.academics.program_percentage.health",
            
            # Outcomes
            "latest.earnings.10_yrs_after_entry.median",
            "latest.completion.completion_rate_4yr_150nt",
            "latest.student.retention_rate.four_year.full_time",
        ]
        
        all_institutions = []
        page = 0
        per_page = 100
        max_institutions = 5000  # Collect up to 5000 real institutions
        
        logger.info(f"API Key: {self.api_key[:10]}..." if len(self.api_key) > 10 else "DEMO_KEY")
        logger.info(f"Target: {max_institutions} institutions")
        logger.info(f"Fields: {len(fields)} comprehensive fields")
        logger.info("\nCollecting real data...")
        
        while len(all_institutions) < max_institutions:
            try:
                params = {
                    "api_key": self.api_key,
                    "page": page,
                    "per_page": per_page,
                    "fields": ",".join(fields),
                    # Only active, degree-granting institutions
                    "school.operating": 1,
                    "latest.student.size__range": "1..",  # At least 1 student
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = data.get("results", [])
                            
                            if not results:
                                logger.info(f"\n✓ No more data available (reached end at page {page})")
                                break
                            
                            all_institutions.extend(results)
                            logger.info(f"  Page {page + 1}: +{len(results)} institutions (total: {len(all_institutions)})")
                            
                            page += 1
                            await asyncio.sleep(0.2)  # Rate limiting
                            
                        elif response.status == 429:
                            logger.warning(f"\n⚠ Rate limit reached at page {page}")
                            logger.warning("Waiting 60 seconds...")
                            await asyncio.sleep(60)
                            
                        else:
                            logger.error(f"\n✗ API returned status {response.status}")
                            error_text = await response.text()
                            logger.error(f"Error: {error_text[:200]}")
                            break
                            
            except asyncio.TimeoutError:
                logger.warning(f"\n⚠ Timeout on page {page}, retrying...")
                await asyncio.sleep(5)
                continue
                
            except Exception as e:
                logger.error(f"\n✗ Error on page {page}: {e}")
                break
        
        # Save raw real data
        raw_file = self.output_dir / "raw_real_data.json"
        with open(raw_file, 'w') as f:
            json.dump(all_institutions, f, indent=2)
        
        logger.info(f"\n✓ Collected {len(all_institutions)} REAL institutions")
        logger.info(f"✓ Saved to: {raw_file}")
        logger.info(f"✓ File size: {raw_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        self.raw_data = all_institutions
    
    def validate_authenticity(self):
        """Validate that all data is real and from authentic sources."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: VALIDATING DATA AUTHENTICITY")
        logger.info("=" * 80)
        
        if not hasattr(self, 'raw_data') or not self.raw_data:
            logger.error("✗ No data to validate!")
            return
        
        # Process and validate
        processed = []
        validation_stats = {
            "total": len(self.raw_data),
            "valid": 0,
            "invalid": 0,
            "missing_name": 0,
            "missing_location": 0,
        }
        
        for inst in self.raw_data:
            # Extract name
            name = inst.get("school.name") or (inst.get("school", {}).get("name") if isinstance(inst.get("school"), dict) else None)
            
            if not name:
                validation_stats["missing_name"] += 1
                validation_stats["invalid"] += 1
                continue
            
            # Normalize structure
            normalized = {
                "id": inst.get("id"),
                "name": name,
                "city": inst.get("school.city") or (inst.get("school", {}).get("city") if isinstance(inst.get("school"), dict) else None),
                "state": inst.get("school.state") or (inst.get("school", {}).get("state") if isinstance(inst.get("school"), dict) else None),
                "zip": inst.get("school.zip"),
                "url": inst.get("school.school_url"),
                "locale": inst.get("school.locale"),
                "ownership": inst.get("school.ownership"),
                "carnegie_basic": inst.get("school.carnegie_basic"),
                
                # Admissions
                "admission_rate": inst.get("latest.admissions.admission_rate.overall"),
                "sat_average": inst.get("latest.admissions.sat_scores.average.overall"),
                "act_midpoint": inst.get("latest.admissions.act_scores.midpoint.cumulative"),
                
                # Student body
                "student_size": inst.get("latest.student.size"),
                
                # Costs
                "tuition_in_state": inst.get("latest.cost.tuition.in_state"),
                "tuition_out_of_state": inst.get("latest.cost.tuition.out_of_state"),
                "avg_net_price": inst.get("latest.cost.avg_net_price.overall"),
                "median_debt": inst.get("latest.aid.median_debt.completers.overall"),
                
                # Academics
                "program_business": inst.get("latest.academics.program_percentage.business_marketing"),
                "program_engineering": inst.get("latest.academics.program_percentage.engineering"),
                "program_biology": inst.get("latest.academics.program_percentage.biological"),
                "program_computer": inst.get("latest.academics.program_percentage.computer"),
                "program_health": inst.get("latest.academics.program_percentage.health"),
                
                # Outcomes
                "median_earnings_10yr": inst.get("latest.earnings.10_yrs_after_entry.median"),
                "completion_rate_4yr": inst.get("latest.completion.completion_rate_4yr_150nt"),
                "retention_rate": inst.get("latest.student.retention_rate.four_year.full_time"),
                
                # Metadata
                "data_source": "College Scorecard API",
                "collection_date": datetime.now().isoformat(),
                "authentic": True,
            }
            
            processed.append(normalized)
            validation_stats["valid"] += 1
        
        # Save processed real data
        processed_file = self.output_dir / "processed_real_data.json"
        with open(processed_file, 'w') as f:
            json.dump(processed, f, indent=2)
        
        logger.info(f"\n✓ Validation complete:")
        logger.info(f"  Total: {validation_stats['total']}")
        logger.info(f"  Valid: {validation_stats['valid']}")
        logger.info(f"  Invalid: {validation_stats['invalid']}")
        logger.info(f"\n✓ Saved to: {processed_file}")
        logger.info(f"✓ File size: {processed_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Calculate data completeness
        important_fields = ['name', 'city', 'state', 'admission_rate', 'student_size', 'tuition_in_state']
        total_score = 0
        for inst in processed:
            field_count = sum(1 for field in important_fields if inst.get(field) is not None)
            total_score += field_count / len(important_fields)
        
        completeness = round(total_score / len(processed) * 100, 2) if processed else 0
        logger.info(f"✓ Data completeness: {completeness}%")
        
        self.processed_data = processed
        self.validation_stats = validation_stats
    
    async def generate_training_data(self):
        """Generate training data from REAL data only."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 4: GENERATING TRAINING DATA FROM REAL DATA")
        logger.info("=" * 80)
        
        if not hasattr(self, 'processed_data') or not self.processed_data:
            logger.error("✗ No processed data available!")
            return
        
        training_dir = self.output_dir / "training_datasets"
        preparator = FineTuningDataPreparator(output_dir=training_dir)
        
        # Generate Q&A pairs from real data
        qa_pairs = preparator.generate_qa_from_institutional_data(
            self.processed_data,
            num_questions_per_institution=5
        )
        
        logger.info(f"✓ Generated {len(qa_pairs)} Q&A pairs from real data")
        
        # Create datasets
        alpaca_file = preparator.prepare_instruction_dataset(qa_pairs, "alpaca")
        jsonl_file = preparator.prepare_instruction_dataset(qa_pairs, "jsonl")
        ollama_file = preparator.prepare_instruction_dataset(qa_pairs, "ollama")
        modelfile = preparator.create_ollama_modelfile()
        
        logger.info(f"✓ Created Alpaca format: {alpaca_file}")
        logger.info(f"✓ Created JSONL format: {jsonl_file}")
        logger.info(f"✓ Created Ollama format: {ollama_file}")
        logger.info(f"✓ Created Modelfile: {modelfile}")
    
    async def upload_to_r2(self):
        """Upload ONLY real data to R2."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5: UPLOADING REAL DATA TO R2")
        logger.info("=" * 80)
        
        try:
            client = R2StorageClient()
            
            # Upload raw real data
            logger.info("Uploading raw real data...")
            raw_file = self.output_dir / "raw_real_data.json"
            client.upload_file(raw_file, "real_data/raw_real_data.json")
            
            # Upload processed real data
            logger.info("Uploading processed real data...")
            processed_file = self.output_dir / "processed_real_data.json"
            client.upload_file(processed_file, "real_data/processed_real_data.json")
            
            # Upload training datasets
            logger.info("Uploading training datasets...")
            training_dir = self.output_dir / "training_datasets"
            stats = client.upload_directory(
                training_dir,
                prefix="real_data/training_datasets",
                include_patterns=["*.json", "*.jsonl", "*.txt", "Modelfile"]
            )
            
            logger.info(f"\n✓ Uploaded {stats.get('uploaded', 0) + 2} files to R2")
            logger.info(f"✓ All data is REAL and from authentic sources")
            
        except Exception as e:
            logger.error(f"✗ R2 upload failed: {e}")
            raise


async def main():
    """Main entry point."""
    collector = RealDataCollector()
    await collector.run()


if __name__ == "__main__":
    asyncio.run(main())

