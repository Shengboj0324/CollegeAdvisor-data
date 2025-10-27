#!/usr/bin/env python3
"""
Advanced Common Data Set (CDS) Scraper
Extracts key metrics from CDS PDFs and websites
"""

import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup
import PyPDF2
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CDSExtract:
    """Common Data Set extraction"""
    school_id: str
    school_name: str
    ipeds_id: str
    year: int
    metric: str
    value: float
    section_ref: str
    url: str
    last_verified: str


class CDSScraper:
    """Advanced CDS scraper with PDF parsing"""
    
    # Schools with CDS data
    SCHOOLS = {
        "mit": {
            "school_id": "mit",
            "school_name": "Massachusetts Institute of Technology",
            "ipeds_id": "166683",
            "cds_url": "https://ir.mit.edu/cds",
            "cds_pdf_pattern": "https://ir.mit.edu/sites/default/files/documents/CDS_{year}.pdf"
        },
        "harvard": {
            "school_id": "harvard",
            "school_name": "Harvard University",
            "ipeds_id": "166027",
            "cds_url": "https://oir.harvard.edu/fact-book/common-data-set",
            "cds_pdf_pattern": "https://oir.harvard.edu/files/huoir/files/harvard_cds_{year}.pdf"
        },
        "stanford": {
            "school_id": "stanford",
            "school_name": "Stanford University",
            "ipeds_id": "243744",
            "cds_url": "https://ucomm.stanford.edu/cds/",
            "cds_pdf_pattern": "https://ucomm.stanford.edu/wp-content/uploads/sites/15/{year}/02/CDS_{year}.pdf"
        },
    }
    
    # Metrics to extract
    METRICS = {
        "overall_admit_rate": {
            "section": "C1",
            "pattern": r"Total.*?admitted.*?(\d+)",
            "calculation": lambda admitted, applied: admitted / applied if applied > 0 else 0
        },
        "yield_rate": {
            "section": "C1",
            "pattern": r"Total.*?enrolled.*?(\d+)",
            "calculation": lambda enrolled, admitted: enrolled / admitted if admitted > 0 else 0
        },
        "percent_need_met_avg": {
            "section": "H2",
            "pattern": r"Average percent.*?need met.*?(\d+\.?\d*)%"
        },
        "avg_grant_aid": {
            "section": "H2",
            "pattern": r"Average.*?grant.*?award.*?\$(\d+,?\d*)"
        },
        "percent_receiving_aid": {
            "section": "H2",
            "pattern": r"Percent.*?receiving.*?aid.*?(\d+\.?\d*)%"
        },
    }
    
    def __init__(self, output_dir: str = "training_data/tier1_admissions", cds_dir: str = "r2_data_analysis"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / "CDSExtract.jsonl"
        self.cds_dir = Path(cds_dir)
        
    def extract_from_local_pdfs(self):
        """Extract metrics from local CDS PDFs"""
        results = []
        
        # Find all CDS PDFs in r2_data_analysis directory
        cds_files = list(self.cds_dir.glob("*CDS*.pdf")) + list(self.cds_dir.glob("*cds*.pdf"))
        
        logger.info(f"Found {len(cds_files)} CDS PDF files")
        
        for pdf_file in cds_files:
            try:
                school_name = self._extract_school_name(pdf_file.name)
                year = self._extract_year(pdf_file.name)
                
                logger.info(f"Processing {school_name} ({year})")
                
                # Extract text from PDF
                text = self._extract_pdf_text(pdf_file)
                
                # Extract metrics
                metrics = self._extract_metrics(text)
                
                # Create CDSExtract records
                for metric_name, value in metrics.items():
                    if value is not None:
                        result = CDSExtract(
                            school_id=self._normalize_school_id(school_name),
                            school_name=school_name,
                            ipeds_id=self._lookup_ipeds(school_name),
                            year=year,
                            metric=metric_name,
                            value=value,
                            section_ref=self.METRICS.get(metric_name, {}).get("section", ""),
                            url=str(pdf_file),
                            last_verified=datetime.now().strftime("%Y-%m-%d")
                        )
                        results.append(result)
                        self._save_result(result)
                        
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
                
        logger.info(f"Extracted {len(results)} CDS metrics")
        return results
        
    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF"""
        text = ""
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text()
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
        return text
        
    def _extract_metrics(self, text: str) -> Dict[str, Optional[float]]:
        """Extract metrics from CDS text"""
        metrics = {}
        
        # Extract admission rate
        admitted_match = re.search(r'Total.*?admitted.*?(\d+,?\d*)', text, re.IGNORECASE)
        applied_match = re.search(r'Total.*?applicants.*?(\d+,?\d*)', text, re.IGNORECASE)
        
        if admitted_match and applied_match:
            admitted = int(admitted_match.group(1).replace(',', ''))
            applied = int(applied_match.group(1).replace(',', ''))
            metrics['overall_admit_rate'] = round(admitted / applied, 4) if applied > 0 else None
            
        # Extract yield rate
        enrolled_match = re.search(r'Total.*?enrolled.*?(\d+,?\d*)', text, re.IGNORECASE)
        if enrolled_match and admitted_match:
            enrolled = int(enrolled_match.group(1).replace(',', ''))
            admitted = int(admitted_match.group(1).replace(',', ''))
            metrics['yield_rate'] = round(enrolled / admitted, 4) if admitted > 0 else None
            
        # Extract percent need met
        need_met_match = re.search(r'Average percent.*?need met.*?(\d+\.?\d*)%?', text, re.IGNORECASE)
        if need_met_match:
            metrics['percent_need_met_avg'] = float(need_met_match.group(1)) / 100
            
        # Extract average grant aid
        grant_match = re.search(r'Average.*?grant.*?award.*?\$(\d+,?\d*)', text, re.IGNORECASE)
        if grant_match:
            metrics['avg_grant_aid'] = int(grant_match.group(1).replace(',', ''))
            
        return metrics
        
    def _extract_school_name(self, filename: str) -> str:
        """Extract school name from filename"""
        # Remove file extension
        name = filename.replace('.pdf', '').replace('.PDF', '')
        
        # Remove common patterns
        name = re.sub(r'CDS.*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'cds.*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'common.*data.*set', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\d{4}-\d{4}', '', name)
        name = re.sub(r'\d{4}', '', name)
        name = re.sub(r'[_-]+', ' ', name)
        
        return name.strip()
        
    def _extract_year(self, filename: str) -> int:
        """Extract year from filename"""
        # Look for 4-digit year
        year_match = re.search(r'20(\d{2})', filename)
        if year_match:
            return int(f"20{year_match.group(1)}")
        return 2024  # Default to current year
        
    def _normalize_school_id(self, school_name: str) -> str:
        """Normalize school name to ID"""
        name_lower = school_name.lower()
        
        if 'mit' in name_lower or 'massachusetts institute' in name_lower:
            return 'mit'
        elif 'harvard' in name_lower:
            return 'harvard'
        elif 'stanford' in name_lower:
            return 'stanford'
        elif 'princeton' in name_lower:
            return 'princeton'
        elif 'yale' in name_lower:
            return 'yale'
        elif 'columbia' in name_lower:
            return 'columbia'
        elif 'cornell' in name_lower:
            return 'cornell'
        elif 'brown' in name_lower:
            return 'brown'
        elif 'dartmouth' in name_lower:
            return 'dartmouth'
        elif 'penn' in name_lower or 'pennsylvania' in name_lower:
            return 'upenn'
        elif 'cmu' in name_lower or 'carnegie mellon' in name_lower:
            return 'cmu'
        elif 'caltech' in name_lower or 'california institute' in name_lower:
            return 'caltech'
        elif 'duke' in name_lower:
            return 'duke'
        elif 'northwestern' in name_lower:
            return 'northwestern'
        elif 'chicago' in name_lower and 'university' in name_lower:
            return 'uchicago'
        else:
            # Generate ID from name
            return re.sub(r'[^a-z0-9]', '', name_lower)[:20]
            
    def _lookup_ipeds(self, school_name: str) -> str:
        """Lookup IPEDS ID for school"""
        # Hardcoded mapping for common schools
        ipeds_map = {
            'mit': '166683',
            'harvard': '166027',
            'stanford': '243744',
            'princeton': '186131',
            'yale': '130794',
            'columbia': '190150',
            'cornell': '190415',
            'brown': '217156',
            'dartmouth': '182670',
            'upenn': '215062',
            'cmu': '211440',
            'caltech': '110404',
            'duke': '199120',
            'northwestern': '147767',
            'uchicago': '144050',
        }
        
        school_id = self._normalize_school_id(school_name)
        return ipeds_map.get(school_id, '000000')
        
    def _save_result(self, result: CDSExtract):
        """Save result to JSONL file"""
        with open(self.output_file, 'a') as f:
            f.write(json.dumps(asdict(result)) + '\n')
            
    def generate_summary_report(self):
        """Generate summary report of extracted data"""
        if not self.output_file.exists():
            logger.warning("No CDS data extracted yet")
            return
            
        # Load all results
        results = []
        with open(self.output_file, 'r') as f:
            for line in f:
                results.append(json.loads(line))
                
        # Create summary
        df = pd.DataFrame(results)
        
        summary_file = self.output_dir / "CDS_SUMMARY.md"
        with open(summary_file, 'w') as f:
            f.write("# Common Data Set Extraction Summary\n\n")
            f.write(f"**Total Records:** {len(results)}\n")
            f.write(f"**Schools:** {df['school_name'].nunique()}\n")
            f.write(f"**Years:** {sorted(df['year'].unique())}\n\n")
            
            f.write("## Metrics Extracted\n\n")
            for metric in df['metric'].unique():
                count = len(df[df['metric'] == metric])
                f.write(f"- {metric}: {count} records\n")
                
            f.write("\n## Schools Covered\n\n")
            for school in sorted(df['school_name'].unique()):
                count = len(df[df['school_name'] == school])
                f.write(f"- {school}: {count} metrics\n")
                
        logger.info(f"Generated summary report: {summary_file}")


def main():
    scraper = CDSScraper()
    
    # Extract from local PDFs
    scraper.extract_from_local_pdfs()
    
    # Generate summary
    scraper.generate_summary_report()
    
    logger.info("CDS scraper complete")


if __name__ == "__main__":
    main()

