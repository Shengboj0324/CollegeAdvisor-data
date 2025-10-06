#!/usr/bin/env python3
"""
Comprehensive fine-tuning preparation script.

This script orchestrates the complete data preparation pipeline:
1. Collect comprehensive data from all sources
2. Process and clean the data
3. Create ChromaDB collections
4. Generate training datasets
5. Upload to Cloudflare R2
6. Prepare Ollama fine-tuning files

Usage:
    python scripts/prepare_finetuning.py --full
    python scripts/prepare_finetuning.py --collect-only
    python scripts/prepare_finetuning.py --process-only
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.comprehensive_data_collector import ComprehensiveDataCollector
from college_advisor_data.storage.collection_manager import CollectionManager
from college_advisor_data.storage.r2_storage import R2StorageClient
from ai_training.finetuning_data_prep import FineTuningDataPreparator, prepare_complete_finetuning_dataset
from college_advisor_data.ingestion.pipeline import DataPipeline
from college_advisor_data.config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FineTuningPreparationOrchestrator:
    """
    Orchestrates the complete fine-tuning preparation process.
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("data/finetuning_prep")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            "start_time": datetime.now().isoformat(),
            "stages_completed": [],
            "errors": []
        }
    
    async def run_full_pipeline(self, api_key: str = None):
        """Run the complete fine-tuning preparation pipeline."""
        logger.info("=" * 80)
        logger.info("STARTING COMPREHENSIVE FINE-TUNING PREPARATION PIPELINE")
        logger.info("=" * 80)
        
        try:
            # Stage 1: Data Collection
            await self.stage_1_collect_data(api_key)
            
            # Stage 2: Data Processing
            await self.stage_2_process_data()
            
            # Stage 3: ChromaDB Population
            await self.stage_3_populate_chromadb()
            
            # Stage 4: Generate Training Datasets
            await self.stage_4_generate_training_data()
            
            # Stage 5: Upload to R2
            await self.stage_5_upload_to_r2()
            
            # Stage 6: Create Ollama Files
            await self.stage_6_create_ollama_files()
            
            # Generate final report
            self.generate_final_report()
            
            logger.info("=" * 80)
            logger.info("FINE-TUNING PREPARATION COMPLETE")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self.stats["errors"].append(str(e))
            raise
    
    async def stage_1_collect_data(self, api_key: str = None):
        """Stage 1: Collect comprehensive data from all sources."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 1: DATA COLLECTION")
        logger.info("=" * 80)
        
        try:
            collector = ComprehensiveDataCollector(
                output_dir=self.output_dir / "raw_data"
            )
            
            stats = await collector.collect_all_sources(api_key)
            
            self.stats["collection_stats"] = stats
            self.stats["stages_completed"].append("data_collection")
            
            logger.info(f"✓ Data collection complete: {stats['total_institutions']} institutions")
            
        except Exception as e:
            logger.error(f"✗ Data collection failed: {e}")
            self.stats["errors"].append(f"Stage 1: {str(e)}")
            raise
    
    async def stage_2_process_data(self):
        """Stage 2: Process and clean collected data."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 2: DATA PROCESSING")
        logger.info("=" * 80)
        
        try:
            # Initialize data pipeline
            pipeline = DataPipeline()
            
            # Process comprehensive dataset
            raw_data_file = self.output_dir / "raw_data" / "comprehensive_dataset.json"
            
            if raw_data_file.exists():
                logger.info(f"Processing {raw_data_file}...")
                
                # Run processing pipeline
                result = await pipeline.process_file(
                    raw_data_file,
                    output_dir=self.output_dir / "processed"
                )
                
                self.stats["processing_stats"] = result
                self.stats["stages_completed"].append("data_processing")
                
                logger.info("✓ Data processing complete")
            else:
                logger.warning(f"Raw data file not found: {raw_data_file}")
                
        except Exception as e:
            logger.error(f"✗ Data processing failed: {e}")
            self.stats["errors"].append(f"Stage 2: {str(e)}")
            raise
    
    async def stage_3_populate_chromadb(self):
        """Stage 3: Populate ChromaDB collections."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 3: CHROMADB POPULATION")
        logger.info("=" * 80)
        
        try:
            manager = CollectionManager()
            
            # Create all collections
            collection_stats = manager.create_all_collections()
            
            # Load processed data into collections
            processed_file = self.output_dir / "processed" / "comprehensive_dataset.json"
            
            if processed_file.exists():
                with open(processed_file, 'r') as f:
                    data = json.load(f)
                
                # Add institutions
                institutions_added = manager.add_institutions(data)
                
                logger.info(f"✓ Added {institutions_added} institutions to ChromaDB")
            
            self.stats["chromadb_stats"] = manager.get_collection_stats()
            self.stats["stages_completed"].append("chromadb_population")
            
            logger.info("✓ ChromaDB population complete")
            
        except Exception as e:
            logger.error(f"✗ ChromaDB population failed: {e}")
            self.stats["errors"].append(f"Stage 3: {str(e)}")
            raise
    
    async def stage_4_generate_training_data(self):
        """Stage 4: Generate training datasets for fine-tuning."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 4: TRAINING DATA GENERATION")
        logger.info("=" * 80)
        
        try:
            institutions_file = self.output_dir / "processed" / "comprehensive_dataset.json"
            
            if institutions_file.exists():
                datasets = prepare_complete_finetuning_dataset(
                    institutions_file=institutions_file,
                    output_dir=self.output_dir / "training_datasets"
                )
                
                self.stats["training_datasets"] = {
                    name: str(path) for name, path in datasets.items()
                }
                self.stats["stages_completed"].append("training_data_generation")
                
                logger.info(f"✓ Generated {len(datasets)} training datasets")
            else:
                logger.warning(f"Processed data file not found: {institutions_file}")
                
        except Exception as e:
            logger.error(f"✗ Training data generation failed: {e}")
            self.stats["errors"].append(f"Stage 4: {str(e)}")
            raise
    
    async def stage_5_upload_to_r2(self):
        """Stage 5: Upload datasets to Cloudflare R2."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 5: CLOUDFLARE R2 UPLOAD")
        logger.info("=" * 80)
        
        try:
            # Check if R2 credentials are configured
            if not all([
                config.__dict__.get("r2_account_id"),
                config.__dict__.get("r2_access_key_id"),
                config.__dict__.get("r2_secret_access_key")
            ]):
                logger.warning("R2 credentials not configured. Skipping upload.")
                logger.info("To enable R2 upload, set: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")
                return
            
            client = R2StorageClient()
            
            # Create bucket if needed
            client.create_bucket()
            
            # Upload training datasets
            training_dir = self.output_dir / "training_datasets"
            if training_dir.exists():
                upload_stats = client.upload_directory(
                    training_dir,
                    prefix="finetuning/training_datasets",
                    include_patterns=["*.json", "*.jsonl", "*.txt", "Modelfile"]
                )
                
                self.stats["r2_upload_stats"] = upload_stats
                self.stats["stages_completed"].append("r2_upload")
                
                logger.info(f"✓ Uploaded {upload_stats['uploaded']} files to R2")
            
        except Exception as e:
            logger.warning(f"R2 upload skipped or failed: {e}")
            # Don't raise - R2 upload is optional
    
    async def stage_6_create_ollama_files(self):
        """Stage 6: Create Ollama-specific files for fine-tuning."""
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 6: OLLAMA FILE CREATION")
        logger.info("=" * 80)
        
        try:
            # Create instructions file
            instructions = self._create_ollama_instructions()
            
            instructions_file = self.output_dir / "OLLAMA_FINETUNING_INSTRUCTIONS.md"
            with open(instructions_file, 'w') as f:
                f.write(instructions)
            
            self.stats["stages_completed"].append("ollama_files")
            
            logger.info(f"✓ Created Ollama instructions: {instructions_file}")
            
        except Exception as e:
            logger.error(f"✗ Ollama file creation failed: {e}")
            self.stats["errors"].append(f"Stage 6: {str(e)}")
            raise
    
    def _create_ollama_instructions(self) -> str:
        """Create instructions for Ollama fine-tuning."""
        return """# Ollama Fine-Tuning Instructions

## Prerequisites
- Ollama installed and running
- Training datasets prepared (in training_datasets/)
- Sufficient disk space for model storage

## Fine-Tuning Steps

### 1. Create Custom Model from Modelfile

```bash
cd data/finetuning_prep/training_datasets
ollama create collegeadvisor -f Modelfile
```

### 2. Test the Model

```bash
ollama run collegeadvisor "What is the admission rate at Harvard?"
```

### 3. Further Fine-Tuning (Optional)

For more advanced fine-tuning with training data:

```bash
# Use the instruction dataset
ollama create collegeadvisor-tuned -f Modelfile --training-data instruction_dataset_ollama.txt
```

### 4. Export Model for API Use

```bash
# Export to GGUF format
ollama export collegeadvisor collegeadvisor.gguf

# Or push to Ollama registry
ollama push collegeadvisor
```

## Integration with CollegeAdvisor-api

1. Ensure Ollama is running: `ollama serve`
2. In CollegeAdvisor-api, set environment variable:
   ```
   OLLAMA_MODEL=collegeadvisor
   ```
3. The API will automatically use the fine-tuned model

## Monitoring Performance

Test the model with various queries:
- Institutional information
- Admissions requirements
- Program details
- Financial aid questions

Compare responses with base model to verify improvements.
"""
    
    def generate_final_report(self):
        """Generate comprehensive final report."""
        self.stats["end_time"] = datetime.now().isoformat()
        
        report = f"""
{'=' * 80}
FINE-TUNING PREPARATION REPORT
{'=' * 80}

Start Time: {self.stats['start_time']}
End Time: {self.stats['end_time']}

Stages Completed:
"""
        for stage in self.stats['stages_completed']:
            report += f"  ✓ {stage}\n"
        
        if self.stats.get('errors'):
            report += f"\nErrors Encountered: {len(self.stats['errors'])}\n"
            for error in self.stats['errors']:
                report += f"  ✗ {error}\n"
        
        report += f"\n{'=' * 80}\n"
        
        # Save report
        report_file = self.output_dir / "PREPARATION_REPORT.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Save stats as JSON
        stats_file = self.output_dir / "preparation_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
        
        print(report)
        logger.info(f"Report saved to: {report_file}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Prepare data for fine-tuning")
    parser.add_argument("--full", action="store_true", help="Run full pipeline")
    parser.add_argument("--collect-only", action="store_true", help="Only collect data")
    parser.add_argument("--process-only", action="store_true", help="Only process data")
    parser.add_argument("--api-key", help="College Scorecard API key")
    parser.add_argument("--output-dir", help="Output directory", default="data/finetuning_prep")
    
    args = parser.parse_args()
    
    orchestrator = FineTuningPreparationOrchestrator(
        output_dir=Path(args.output_dir)
    )
    
    if args.full or (not args.collect_only and not args.process_only):
        await orchestrator.run_full_pipeline(args.api_key)
    elif args.collect_only:
        await orchestrator.stage_1_collect_data(args.api_key)
    elif args.process_only:
        await orchestrator.stage_2_process_data()


if __name__ == "__main__":
    asyncio.run(main())

