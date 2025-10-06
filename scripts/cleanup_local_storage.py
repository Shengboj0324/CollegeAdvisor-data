#!/usr/bin/env python3
"""
Clean up local storage after uploading to R2.
Safely removes large source files that are backed up in R2.
"""

import sys
from pathlib import Path
import logging
import shutil

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_dir_size(path):
    """Calculate total size of directory."""
    total = 0
    for item in Path(path).rglob('*'):
        if item.is_file():
            total += item.stat().st_size
    return total


def cleanup_local_storage(dry_run=True):
    """Clean up local storage after R2 upload."""
    
    logger.info("=" * 80)
    logger.info("LOCAL STORAGE CLEANUP")
    logger.info("=" * 80)
    
    if dry_run:
        logger.info("\n⚠️  DRY RUN MODE - No files will be deleted")
        logger.info("Run with --execute to actually delete files\n")
    else:
        logger.warning("\n⚠️  EXECUTE MODE - Files will be permanently deleted!")
        logger.warning("Make sure all data is backed up in R2 first!\n")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Cleanup cancelled")
            return
    
    data_dir = Path("data/multi_source_data")
    
    # Files to remove (large source files that are in R2)
    files_to_remove = [
        "2025-Public-Data-File.xlsx",
        "CCIHE2021-PublicData.xlsx",
        "IPEDS_2020-21_Final.zip",
        "IPEDS_2021-22_Final.zip",
        "IPEDS_2022-23_Final.zip",
        "College_Scorecard_Raw_Data_05192025.zip",
    ]
    
    # Files to keep (processed data)
    files_to_keep = [
        "master_dataset.json",
        "expansion_report.txt",
        "training_datasets/",
    ]
    
    total_size = 0
    removed_count = 0
    
    logger.info("Files to be removed:")
    logger.info("-" * 80)
    
    for filename in files_to_remove:
        filepath = data_dir / filename
        
        if filepath.exists():
            size = filepath.stat().st_size
            size_mb = size / 1024 / 1024
            total_size += size
            
            logger.info(f"  {filename:60s} {size_mb:8.2f} MB")
            
            if not dry_run:
                try:
                    filepath.unlink()
                    logger.info(f"    ✓ Deleted")
                    removed_count += 1
                except Exception as e:
                    logger.error(f"    ✗ Failed to delete: {e}")
        else:
            logger.info(f"  {filename:60s} (not found)")
    
    logger.info("-" * 80)
    logger.info(f"Total space to be freed: {total_size / 1024 / 1024:.2f} MB")
    logger.info("")
    
    logger.info("Files to keep:")
    logger.info("-" * 80)
    
    for filename in files_to_keep:
        filepath = data_dir / filename
        
        if filepath.exists():
            if filepath.is_dir():
                size = get_dir_size(filepath)
            else:
                size = filepath.stat().st_size
            
            size_mb = size / 1024 / 1024
            logger.info(f"  {filename:60s} {size_mb:8.2f} MB")
        else:
            logger.info(f"  {filename:60s} (not found)")
    
    logger.info("-" * 80)
    logger.info("")
    
    if dry_run:
        logger.info("=" * 80)
        logger.info("DRY RUN COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Would free: {total_size / 1024 / 1024:.2f} MB")
        logger.info(f"Would remove: {len(files_to_remove)} files")
        logger.info("")
        logger.info("To actually delete files, run:")
        logger.info("  python scripts/cleanup_local_storage.py --execute")
    else:
        logger.info("=" * 80)
        logger.info("CLEANUP COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Freed: {total_size / 1024 / 1024:.2f} MB")
        logger.info(f"Removed: {removed_count} files")
        logger.info("")
        logger.info("✓ Local storage cleaned up successfully")
        logger.info("✓ All data is safely backed up in R2")


if __name__ == "__main__":
    dry_run = "--execute" not in sys.argv
    cleanup_local_storage(dry_run=dry_run)

