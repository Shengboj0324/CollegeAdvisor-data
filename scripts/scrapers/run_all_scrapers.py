#!/usr/bin/env python3
"""
Comprehensive Data Acquisition Orchestrator
Runs all scrapers and generates high-quality training data
"""

import logging
import sys
from pathlib import Path
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataAcquisitionOrchestrator:
    """Orchestrates all data acquisition scrapers"""
    
    def __init__(self):
        self.scrapers_dir = Path(__file__).parent
        self.results = {}
        
    def run_cds_scraper(self):
        """Run Common Data Set scraper"""
        logger.info("=" * 80)
        logger.info("RUNNING CDS SCRAPER")
        logger.info("=" * 80)
        
        try:
            from scrape_cds import CDSScraper
            scraper = CDSScraper()
            results = scraper.extract_from_local_pdfs()
            scraper.generate_summary_report()
            self.results['cds'] = len(results)
            logger.info(f"✅ CDS Scraper: {len(results)} records extracted")
        except Exception as e:
            logger.error(f"❌ CDS Scraper failed: {e}")
            self.results['cds'] = 0
            
    def run_assist_scraper(self):
        """Run ASSIST.org scraper"""
        logger.info("=" * 80)
        logger.info("RUNNING ASSIST SCRAPER")
        logger.info("=" * 80)
        
        try:
            from scrape_assist import ASSISTScraper
            scraper = ASSISTScraper()
            scraper.generate_manual_template()
            results = scraper.scrape_all_articulations()
            self.results['assist'] = len(results)
            logger.info(f"✅ ASSIST Scraper: {len(results)} records extracted")
        except Exception as e:
            logger.error(f"❌ ASSIST Scraper failed: {e}")
            self.results['assist'] = 0
            
    def run_npc_scraper(self):
        """Run Net Price Calculator scraper"""
        logger.info("=" * 80)
        logger.info("RUNNING NPC SCRAPER")
        logger.info("=" * 80)
        
        try:
            from scrape_npc import NPCScraper
            scraper = NPCScraper()
            scraper.generate_manual_template()
            # Note: Automated NPC scraping requires Selenium setup
            # For now, just generate templates
            self.results['npc'] = 0
            logger.info(f"✅ NPC Scraper: Manual template generated")
        except Exception as e:
            logger.error(f"❌ NPC Scraper failed: {e}")
            self.results['npc'] = 0
            
    def run_aid_policy_scraper(self):
        """Run financial aid policy scraper"""
        logger.info("=" * 80)
        logger.info("RUNNING AID POLICY SCRAPER")
        logger.info("=" * 80)
        
        try:
            from scrape_aid_policies import AidPolicyScraper
            scraper = AidPolicyScraper()
            results = scraper.scrape_all_policies()
            self.results['aid_policies'] = len(results)
            logger.info(f"✅ Aid Policy Scraper: {len(results)} records extracted")
        except Exception as e:
            logger.error(f"❌ Aid Policy Scraper failed: {e}")
            self.results['aid_policies'] = 0
            
    def run_major_gates_scraper(self):
        """Run major gates scraper"""
        logger.info("=" * 80)
        logger.info("RUNNING MAJOR GATES SCRAPER")
        logger.info("=" * 80)
        
        try:
            from scrape_major_gates import MajorGatesScraper
            scraper = MajorGatesScraper()
            results = scraper.scrape_all_gates()
            self.results['major_gates'] = len(results)
            logger.info(f"✅ Major Gates Scraper: {len(results)} records extracted")
        except Exception as e:
            logger.error(f"❌ Major Gates Scraper failed: {e}")
            self.results['major_gates'] = 0
            
    def generate_final_report(self):
        """Generate final acquisition report"""
        logger.info("=" * 80)
        logger.info("DATA ACQUISITION COMPLETE")
        logger.info("=" * 80)
        
        total_records = sum(self.results.values())
        
        report = f"""
# Data Acquisition Report
**Date:** {Path(__file__).stat().st_mtime}

## Summary
- **Total Records:** {total_records}

## By Source
"""
        for source, count in self.results.items():
            report += f"- **{source.upper()}:** {count} records\n"
            
        report_file = Path("DATA_ACQUISITION_REPORT.md")
        with open(report_file, 'w') as f:
            f.write(report)
            
        logger.info(f"📊 Total records acquired: {total_records}")
        logger.info(f"📄 Report saved to: {report_file}")
        
    def run_all(self):
        """Run all scrapers"""
        logger.info("🚀 Starting comprehensive data acquisition...")
        
        # Run all scrapers
        self.run_cds_scraper()
        self.run_assist_scraper()
        self.run_npc_scraper()
        self.run_aid_policy_scraper()
        self.run_major_gates_scraper()
        
        # Generate report
        self.generate_final_report()
        
        logger.info("✅ Data acquisition complete!")


def main():
    orchestrator = DataAcquisitionOrchestrator()
    orchestrator.run_all()


if __name__ == "__main__":
    main()

