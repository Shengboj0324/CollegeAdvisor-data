#!/usr/bin/env python3
"""
Upload all multi-source data files to R2 bucket.
"""

import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from college_advisor_data.storage.r2_storage import R2StorageClient

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def upload_all_files():
    """Upload all multi-source data files to R2."""
    
    logger.info("=" * 80)
    logger.info("UPLOADING ALL DATA TO R2 BUCKET")
    logger.info("=" * 80)
    
    # Initialize R2 client
    client = R2StorageClient()
    
    # Define files to upload
    data_dir = Path("data/multi_source_data")
    
    files_to_upload = [
        # Carnegie Classification files
        ("2025-Public-Data-File.xlsx", "source_data/carnegie/2025-Public-Data-File.xlsx"),
        ("CCIHE2021-PublicData.xlsx", "source_data/carnegie/CCIHE2021-PublicData.xlsx"),
        
        # IPEDS files
        ("IPEDS_2020-21_Final.zip", "source_data/ipeds/IPEDS_2020-21_Final.zip"),
        ("IPEDS_2021-22_Final.zip", "source_data/ipeds/IPEDS_2021-22_Final.zip"),
        ("IPEDS_2022-23_Final.zip", "source_data/ipeds/IPEDS_2022-23_Final.zip"),
        
        # College Scorecard complete data
        ("College_Scorecard_Raw_Data_05192025.zip", "source_data/scorecard/College_Scorecard_Raw_Data_05192025.zip"),
        
        # Master dataset
        ("master_dataset.json", "multi_source/master_dataset.json"),
        
        # Expansion report
        ("expansion_report.txt", "multi_source/expansion_report.txt"),
    ]
    
    # Upload training datasets
    training_dir = data_dir / "training_datasets"
    if training_dir.exists():
        for file in training_dir.iterdir():
            if file.is_file():
                files_to_upload.append(
                    (f"training_datasets/{file.name}", f"multi_source/training_datasets/{file.name}")
                )
    
    total_files = len(files_to_upload)
    uploaded = 0
    failed = 0
    total_size = 0
    
    logger.info(f"\nFound {total_files} files to upload\n")
    
    for local_path, r2_key in files_to_upload:
        local_file = data_dir / local_path if not local_path.startswith("training_datasets/") else data_dir / local_path
        
        if not local_file.exists():
            logger.warning(f"⚠ File not found: {local_file}")
            failed += 1
            continue
        
        file_size = local_file.stat().st_size
        size_mb = file_size / 1024 / 1024
        total_size += file_size
        
        logger.info(f"Uploading: {local_path}")
        logger.info(f"  Size: {size_mb:.2f} MB")
        logger.info(f"  R2 Key: {r2_key}")
        
        try:
            with open(local_file, 'rb') as f:
                client.client.put_object(
                    Bucket=client.bucket_name,
                    Key=r2_key,
                    Body=f
                )
            logger.info(f"  ✓ Uploaded successfully")
            uploaded += 1
        except Exception as e:
            logger.error(f"  ✗ Upload failed: {e}")
            failed += 1
        
        logger.info("")
    
    logger.info("=" * 80)
    logger.info("UPLOAD SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Files: {total_files}")
    logger.info(f"Uploaded: {uploaded}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total Size: {total_size / 1024 / 1024:.2f} MB")
    logger.info("")
    
    # Verify R2 bucket contents
    logger.info("=" * 80)
    logger.info("VERIFYING R2 BUCKET CONTENTS")
    logger.info("=" * 80)
    
    try:
        response = client.client.list_objects_v2(Bucket=client.bucket_name)
        
        if 'Contents' in response:
            files = response['Contents']
            logger.info(f"\nTotal Files in R2: {len(files)}")
            
            r2_total_size = 0
            for obj in sorted(files, key=lambda x: x['Key']):
                size_mb = obj['Size'] / 1024 / 1024
                r2_total_size += obj['Size']
                logger.info(f"  {obj['Key']:70s} {size_mb:8.2f} MB")
            
            logger.info(f"\nTotal R2 Size: {r2_total_size / 1024 / 1024:.2f} MB")
        else:
            logger.warning("Bucket is empty!")
    except Exception as e:
        logger.error(f"Failed to verify bucket: {e}")
    
    logger.info("\n" + "=" * 80)
    logger.info("✓ UPLOAD COMPLETE")
    logger.info("=" * 80)
    
    return uploaded, failed


if __name__ == "__main__":
    uploaded, failed = upload_all_files()
    
    if failed > 0:
        logger.error(f"\n⚠ {failed} files failed to upload")
        sys.exit(1)
    else:
        logger.info(f"\n✓ All {uploaded} files uploaded successfully")
        sys.exit(0)

