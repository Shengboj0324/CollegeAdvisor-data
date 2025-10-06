"""
Comprehensive data collector for college admissions AI training.

This module orchestrates collection from multiple high-quality data sources
to build a comprehensive dataset for fine-tuning the CollegeAdvisor LLM.
"""

import logging
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import aiohttp
import pandas as pd

from .base_collector import BaseCollector, CollectorConfig, CollectionResult
from .government import CollegeScorecardCollector

logger = logging.getLogger(__name__)


class ComprehensiveDataCollector:
    """
    Orchestrates comprehensive data collection from multiple sources.
    
    Manages:
    - College Scorecard (complete dataset)
    - IPEDS (full institutional data)
    - Rankings data
    - Common Data Set information
    - Program-specific data
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("data/comprehensive")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            "total_institutions": 0,
            "data_sources": {},
            "collection_start": None,
            "collection_end": None,
            "errors": []
        }
    
    async def collect_all_sources(self, api_key: str = None) -> Dict[str, Any]:
        """
        Collect data from all configured sources.
        
        Args:
            api_key: College Scorecard API key
            
        Returns:
            Collection statistics and results
        """
        self.stats["collection_start"] = datetime.now().isoformat()
        logger.info("Starting comprehensive data collection...")
        
        try:
            # Collect from each source
            scorecard_data = await self._collect_college_scorecard(api_key)
            ipeds_data = await self._collect_ipeds()
            rankings_data = await self._collect_rankings()
            
            # Merge and deduplicate
            merged_data = self._merge_data_sources(
                scorecard_data,
                ipeds_data,
                rankings_data
            )
            
            # Save comprehensive dataset
            self._save_comprehensive_dataset(merged_data)
            
            self.stats["collection_end"] = datetime.now().isoformat()
            self.stats["total_institutions"] = len(merged_data)
            
            logger.info(f"Collection complete: {self.stats['total_institutions']} institutions")
            return self.stats
            
        except Exception as e:
            logger.error(f"Error in comprehensive collection: {e}")
            self.stats["errors"].append(str(e))
            raise
    
    async def _collect_college_scorecard(self, api_key: str = None) -> List[Dict]:
        """
        Collect complete College Scorecard dataset.
        
        Downloads all available institutions with comprehensive field coverage.
        """
        logger.info("Collecting College Scorecard data...")
        
        config = CollectorConfig(
            name="college_scorecard_comprehensive",
            api_key=api_key or "DEMO_KEY",
            rate_limit=10,  # requests per second
            output_dir=self.output_dir / "scorecard"
        )
        
        collector = CollegeScorecardCollector(config)
        
        # Collect all institutions with pagination
        all_institutions = []
        page = 0
        per_page = 100
        
        while True:
            try:
                result = await collector.collect_batch(
                    page=page,
                    per_page=per_page,
                    fields="all"  # Request all available fields
                )
                
                if not result.data:
                    break
                
                all_institutions.extend(result.data)
                logger.info(f"Collected {len(all_institutions)} institutions so far...")
                
                page += 1
                
                # Respect rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error collecting scorecard page {page}: {e}")
                break
        
        self.stats["data_sources"]["college_scorecard"] = len(all_institutions)
        
        # Save raw data
        output_file = self.output_dir / "scorecard" / "complete_dataset.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(all_institutions, f, indent=2)
        
        logger.info(f"College Scorecard: {len(all_institutions)} institutions collected")
        return all_institutions
    
    async def _collect_ipeds(self) -> List[Dict]:
        """
        Collect IPEDS data via Urban Institute Education Data API.
        
        Provides comprehensive institutional data including:
        - Directory information
        - Enrollment statistics
        - Completions data
        - Financial aid
        - Institutional characteristics
        """
        logger.info("Collecting IPEDS data...")
        
        base_url = "https://educationdata.urban.org/api/v1/college-university"
        
        # IPEDS endpoints to collect
        endpoints = [
            "ipeds/directory",
            "ipeds/enrollment-full-time-equivalent",
            "ipeds/completions-cip-2",
            "ipeds/institutional-characteristics",
            "ipeds/admissions-enrollment"
        ]
        
        all_data = []
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    url = f"{base_url}/{endpoint}"
                    logger.info(f"Fetching {endpoint}...")
                    
                    # Paginate through results
                    page = 1
                    while True:
                        params = {"page": page, "per_page": 1000}
                        
                        async with session.get(url, params=params) as response:
                            if response.status != 200:
                                logger.warning(f"Failed to fetch {endpoint} page {page}")
                                break
                            
                            data = await response.json()
                            results = data.get("results", [])
                            
                            if not results:
                                break
                            
                            all_data.extend(results)
                            page += 1
                            
                            await asyncio.sleep(0.2)  # Rate limiting
                
                except Exception as e:
                    logger.error(f"Error collecting IPEDS {endpoint}: {e}")
                    self.stats["errors"].append(f"IPEDS {endpoint}: {str(e)}")
        
        self.stats["data_sources"]["ipeds"] = len(all_data)
        
        # Save raw data
        output_file = self.output_dir / "ipeds" / "complete_dataset.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=2)
        
        logger.info(f"IPEDS: {len(all_data)} records collected")
        return all_data
    
    async def _collect_rankings(self) -> List[Dict]:
        """
        Collect university rankings data from multiple sources.
        
        Sources:
        - QS World University Rankings
        - Times Higher Education
        - U.S. News (where available)
        """
        logger.info("Collecting rankings data...")
        
        # Placeholder for rankings collection
        # In production, this would scrape or use APIs for rankings data
        rankings_data = []
        
        # For now, create structure for future implementation
        self.stats["data_sources"]["rankings"] = 0
        
        logger.info("Rankings collection: Placeholder (implement scraping)")
        return rankings_data
    
    def _merge_data_sources(
        self,
        scorecard: List[Dict],
        ipeds: List[Dict],
        rankings: List[Dict]
    ) -> List[Dict]:
        """
        Merge data from multiple sources into unified records.
        
        Uses UNITID and institution name for matching.
        """
        logger.info("Merging data sources...")
        
        # Convert to DataFrames for easier merging
        df_scorecard = pd.DataFrame(scorecard) if scorecard else pd.DataFrame()
        df_ipeds = pd.DataFrame(ipeds) if ipeds else pd.DataFrame()
        
        # Merge on common identifiers
        if not df_scorecard.empty and not df_ipeds.empty:
            # Merge logic here
            merged_df = df_scorecard  # Simplified for now
        else:
            merged_df = df_scorecard if not df_scorecard.empty else df_ipeds
        
        # Convert back to list of dicts
        merged_data = merged_df.to_dict('records') if not merged_df.empty else []
        
        logger.info(f"Merged {len(merged_data)} institution records")
        return merged_data
    
    def _save_comprehensive_dataset(self, data: List[Dict]):
        """Save the comprehensive merged dataset."""
        output_file = self.output_dir / "comprehensive_dataset.json"
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Also save as CSV for easier analysis
        df = pd.DataFrame(data)
        csv_file = self.output_dir / "comprehensive_dataset.csv"
        df.to_csv(csv_file, index=False)
        
        logger.info(f"Saved comprehensive dataset: {output_file}")
        logger.info(f"Saved CSV version: {csv_file}")
    
    def generate_statistics_report(self) -> str:
        """Generate a detailed statistics report."""
        report = f"""
Comprehensive Data Collection Report
=====================================
Collection Period: {self.stats.get('collection_start')} to {self.stats.get('collection_end')}
Total Institutions: {self.stats.get('total_institutions', 0)}

Data Sources:
"""
        for source, count in self.stats.get('data_sources', {}).items():
            report += f"  - {source}: {count} records\n"
        
        if self.stats.get('errors'):
            report += f"\nErrors Encountered: {len(self.stats['errors'])}\n"
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                report += f"  - {error}\n"
        
        return report


async def main():
    """Main entry point for comprehensive data collection."""
    collector = ComprehensiveDataCollector()
    
    # Run collection
    stats = await collector.collect_all_sources()
    
    # Generate report
    report = collector.generate_statistics_report()
    print(report)
    
    # Save report
    report_file = collector.output_dir / "collection_report.txt"
    with open(report_file, 'w') as f:
        f.write(report)


if __name__ == "__main__":
    asyncio.run(main())

