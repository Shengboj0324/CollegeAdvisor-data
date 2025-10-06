#!/usr/bin/env python3
"""
Download additional data sources directly.
"""

import requests
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

output_dir = Path("data/multi_source_data")
output_dir.mkdir(parents=True, exist_ok=True)


def download_file(url: str, output_path: Path, description: str):
    """Download a file with progress."""
    logger.info(f"\nDownloading: {description}")
    logger.info(f"URL: {url}")
    logger.info(f"Output: {output_path}")
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        total_mb = total_size / 1024 / 1024
        
        logger.info(f"Size: {total_mb:.2f} MB")
        
        downloaded = 0
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        pct = downloaded / total_size * 100
                        if int(pct) % 10 == 0:
                            logger.info(f"  Progress: {pct:.0f}%")
        
        logger.info(f"✓ Downloaded: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error downloading {description}: {e}")
        return False


def main():
    """Download all additional data sources."""
    logger.info("=" * 80)
    logger.info("DOWNLOADING ADDITIONAL DATA SOURCES")
    logger.info("=" * 80)
    
    # Carnegie Classification 2025
    carnegie_url = "https://carnegieclassifications.acenet.edu/wp-content/uploads/2025/01/CCIHE2025-PublicDataFile.xlsx"
    carnegie_file = output_dir / "carnegie_2025.xlsx"
    download_file(carnegie_url, carnegie_file, "Carnegie Classification 2025")
    
    # College Scorecard Field of Study (Most Recent)
    # Note: This is a large file (~500 MB)
    fos_url = "https://ed-public-download.app.cloud.gov/downloads/Most-Recent-Cohorts-Field-of-Study.csv"
    fos_file = output_dir / "field_of_study.csv"
    
    logger.info("\n" + "=" * 80)
    logger.info("WARNING: Field of Study data is very large (~500 MB)")
    logger.info("=" * 80)
    response = input("Do you want to download it? (y/n): ")
    
    if response.lower() == 'y':
        download_file(fos_url, fos_file, "College Scorecard Field of Study")
    else:
        logger.info("Skipping Field of Study download")
    
    logger.info("\n" + "=" * 80)
    logger.info("✓ DOWNLOAD COMPLETE")
    logger.info("=" * 80)
    logger.info("\nNext step: Run scripts/expand_data_sources.py to process the data")


if __name__ == "__main__":
    main()

