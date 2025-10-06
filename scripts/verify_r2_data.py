#!/usr/bin/env python3
"""
Verify R2 data quality and readiness for fine-tuning.
"""

import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from college_advisor_data.storage.r2_storage import R2StorageClient

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def verify_r2_bucket():
    """Verify R2 bucket and list contents."""
    logger.info("=" * 80)
    logger.info("VERIFYING R2 BUCKET CONTENTS")
    logger.info("=" * 80)
    
    try:
        client = R2StorageClient()
        
        # List all files in bucket
        logger.info(f"\nBucket: {client.bucket_name}")
        logger.info(f"Endpoint: {client.endpoint_url}\n")
        
        response = client.client.list_objects_v2(Bucket=client.bucket_name)
        
        if 'Contents' not in response:
            logger.warning("Bucket is empty!")
            return
        
        files = response['Contents']
        logger.info(f"Total files in bucket: {len(files)}\n")
        
        # Group by prefix
        prefixes = {}
        total_size = 0
        
        for obj in files:
            key = obj['Key']
            size = obj['Size']
            total_size += size
            
            prefix = key.split('/')[0] if '/' in key else 'root'
            
            if prefix not in prefixes:
                prefixes[prefix] = []
            
            prefixes[prefix].append({
                'key': key,
                'size': size,
                'size_mb': round(size / 1024 / 1024, 2)
            })
        
        # Display by category
        for prefix, items in sorted(prefixes.items()):
            logger.info(f"\n{prefix.upper()}:")
            for item in items:
                logger.info(f"  ✓ {item['key']} ({item['size_mb']} MB)")
        
        logger.info(f"\nTotal storage used: {round(total_size / 1024 / 1024, 2)} MB")
        
        # Verify critical files
        logger.info("\n" + "=" * 80)
        logger.info("CRITICAL FILES VERIFICATION")
        logger.info("=" * 80)
        
        critical_files = [
            "processed_data/institutions.json",
            "training_datasets/Modelfile",
            "training_datasets/instruction_dataset_alpaca.json",
            "training_datasets/instruction_dataset.jsonl",
            "training_datasets/instruction_dataset_ollama.txt"
        ]
        
        file_keys = [obj['Key'] for obj in files]
        
        all_present = True
        for critical_file in critical_files:
            if critical_file in file_keys:
                logger.info(f"✓ {critical_file}")
            else:
                logger.error(f"✗ MISSING: {critical_file}")
                all_present = False
        
        if all_present:
            logger.info("\n✓ All critical files present in R2!")
        else:
            logger.error("\n✗ Some critical files are missing!")
        
        return all_present
        
    except Exception as e:
        logger.error(f"Error verifying R2 bucket: {e}")
        return False


def verify_local_data():
    """Verify local training data quality."""
    logger.info("\n" + "=" * 80)
    logger.info("VERIFYING LOCAL TRAINING DATA QUALITY")
    logger.info("=" * 80)
    
    data_dir = Path("data/r2_finetuning")
    
    # Check processed institutions
    institutions_file = data_dir / "processed_institutions.json"
    if institutions_file.exists():
        with open(institutions_file, 'r') as f:
            institutions = json.load(f)
        
        logger.info(f"\n✓ Processed Institutions: {len(institutions)}")
        
        # Sample quality check
        if institutions:
            sample = institutions[0]
            logger.info(f"  Sample institution: {sample.get('name', 'N/A')}")
            logger.info(f"  Fields present: {len(sample)}")
            
            # Check important fields
            important_fields = ['name', 'city', 'state', 'admission_rate', 'student_size']
            present_fields = sum(1 for field in important_fields if sample.get(field) is not None)
            logger.info(f"  Important fields: {present_fields}/{len(important_fields)}")
    else:
        logger.error("✗ Processed institutions file not found!")
    
    # Check training datasets
    training_dir = data_dir / "training_datasets"
    
    if training_dir.exists():
        # Check Alpaca format
        alpaca_file = training_dir / "instruction_dataset_alpaca.json"
        if alpaca_file.exists():
            with open(alpaca_file, 'r') as f:
                alpaca_data = json.load(f)
            logger.info(f"\n✓ Alpaca dataset: {len(alpaca_data)} examples")
            
            if alpaca_data:
                sample = alpaca_data[0]
                logger.info(f"  Sample instruction: {sample.get('instruction', '')[:100]}...")
                logger.info(f"  Sample output: {sample.get('output', '')[:100]}...")
        
        # Check JSONL format
        jsonl_file = training_dir / "instruction_dataset.jsonl"
        if jsonl_file.exists():
            with open(jsonl_file, 'r') as f:
                jsonl_count = sum(1 for _ in f)
            logger.info(f"\n✓ JSONL dataset: {jsonl_count} examples")
        
        # Check Ollama format
        ollama_file = training_dir / "instruction_dataset_ollama.txt"
        if ollama_file.exists():
            with open(ollama_file, 'r') as f:
                ollama_content = f.read()
            logger.info(f"\n✓ Ollama dataset: {len(ollama_content)} characters")
        
        # Check Modelfile
        modelfile = training_dir / "Modelfile"
        if modelfile.exists():
            with open(modelfile, 'r') as f:
                modelfile_content = f.read()
            logger.info(f"\n✓ Modelfile present")
            logger.info(f"  Content preview:")
            for line in modelfile_content.split('\n')[:5]:
                logger.info(f"    {line}")
    else:
        logger.error("✗ Training datasets directory not found!")


def main():
    """Main verification."""
    logger.info("\n" + "=" * 80)
    logger.info("R2 DATA QUALITY VERIFICATION")
    logger.info("=" * 80)
    
    # Verify local data
    verify_local_data()
    
    # Verify R2 bucket
    r2_ok = verify_r2_bucket()
    
    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 80)
    
    if r2_ok:
        logger.info("\n✓ ALL VERIFICATIONS PASSED")
        logger.info("\nYour data is ready for fine-tuning!")
        logger.info("\nNext steps:")
        logger.info("1. cd data/r2_finetuning/training_datasets")
        logger.info("2. ollama create collegeadvisor -f Modelfile")
        logger.info("3. ollama run collegeadvisor")
    else:
        logger.error("\n✗ SOME VERIFICATIONS FAILED")
        logger.error("Please review the errors above.")


if __name__ == "__main__":
    main()

