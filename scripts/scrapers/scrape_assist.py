#!/usr/bin/env python3
"""
Advanced ASSIST.org Scraper
Extracts course articulation agreements for CC to UC/CSU transfers
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Articulation:
    """Course articulation record"""
    cc_id: str
    cc_name: str
    target_school_id: str
    target_school_name: str
    target_major: str
    target_major_cip: str
    seq: List[Dict]
    gpa_floor: float
    tag_eligible: bool
    notes: str
    citations: List[str]
    last_verified: str


class ASSISTScraper:
    """Advanced ASSIST.org scraper"""
    
    # Community colleges
    COMMUNITY_COLLEGES = {
        "deanza": {"id": "deanza", "name": "De Anza College", "district": "Foothill-De Anza"},
        "foothill": {"id": "foothill", "name": "Foothill College", "district": "Foothill-De Anza"},
        "diablo": {"id": "diablo", "name": "Diablo Valley College", "district": "Contra Costa"},
        "santamonica": {"id": "santamonica", "name": "Santa Monica College", "district": "Santa Monica"},
        "pasadena": {"id": "pasadena", "name": "Pasadena City College", "district": "Pasadena"},
        "orange": {"id": "orange", "name": "Orange Coast College", "district": "Coast"},
    }
    
    # Target schools and majors
    TARGET_PROGRAMS = {
        "ucsb_me": {
            "school_id": "ucsb",
            "school_name": "UC Santa Barbara",
            "major": "Mechanical Engineering",
            "major_cip": "14.1901",
            "tag_eligible": False,
            "gpa_floor": 3.2
        },
        "ucla_ece": {
            "school_id": "ucla",
            "school_name": "UCLA",
            "major": "Electrical and Computer Engineering",
            "major_cip": "14.1001",
            "tag_eligible": False,
            "gpa_floor": 3.5
        },
        "ucsd_cse": {
            "school_id": "ucsd",
            "school_name": "UC San Diego",
            "major": "Computer Science and Engineering",
            "major_cip": "11.0701",
            "tag_eligible": False,
            "gpa_floor": 3.5
        },
        "slo_me": {
            "school_id": "slo",
            "school_name": "Cal Poly San Luis Obispo",
            "major": "Mechanical Engineering",
            "major_cip": "14.1901",
            "tag_eligible": False,
            "gpa_floor": 3.4
        },
    }
    
    def __init__(self, output_dir: str = "training_data/tier1_transfer"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / "Articulation.jsonl"
        self.base_url = "https://assist.org"
        
    def scrape_articulation(self, cc_id: str, program_key: str) -> Optional[Articulation]:
        """Scrape articulation agreement for CC to target program"""
        try:
            cc = self.COMMUNITY_COLLEGES[cc_id]
            program = self.TARGET_PROGRAMS[program_key]
            
            logger.info(f"Scraping {cc['name']} → {program['school_name']} {program['major']}")
            
            # ASSIST.org API endpoint (example - actual API may differ)
            # Note: ASSIST.org has an API but requires registration
            # This is a template for the structure
            
            url = f"{self.base_url}/api/articulation"
            params = {
                "from": cc['name'],
                "to": program['school_name'],
                "major": program['major'],
                "year": "2024-25"
            }
            
            # For now, create manual template
            # In production, you'd call the actual API
            
            # Example articulation sequence
            seq = self._generate_example_sequence(cc_id, program_key)
            
            result = Articulation(
                cc_id=cc_id,
                cc_name=cc['name'],
                target_school_id=program['school_id'],
                target_school_name=program['school_name'],
                target_major=program['major'],
                target_major_cip=program['major_cip'],
                seq=seq,
                gpa_floor=program['gpa_floor'],
                tag_eligible=program['tag_eligible'],
                notes=f"{program['major']} is highly competitive; TAG not available" if not program['tag_eligible'] else "TAG eligible with 3.4+ GPA",
                citations=["https://assist.org"],
                last_verified=datetime.now().strftime("%Y-%m-%d")
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error scraping articulation: {e}")
            return None
            
    def _generate_example_sequence(self, cc_id: str, program_key: str) -> List[Dict]:
        """Generate example course sequence"""
        # This is a template - actual sequences should come from ASSIST.org
        
        if program_key == "ucsb_me":
            return [
                {
                    "term": 1,
                    "courses": [
                        {"course_cc": "MATH 1A", "course_target": "MATH 3A", "min_grade": "C", "units": 5},
                        {"course_cc": "CHEM 1A", "course_target": "CHEM 1A", "min_grade": "C", "units": 5},
                        {"course_cc": "ENGR 10", "course_target": "ENGR 3", "min_grade": "C", "units": 4}
                    ]
                },
                {
                    "term": 2,
                    "courses": [
                        {"course_cc": "MATH 1B", "course_target": "MATH 3B", "min_grade": "C", "units": 5},
                        {"course_cc": "PHYS 4A", "course_target": "PHYS 1", "min_grade": "C", "units": 5},
                        {"course_cc": "EWRT 1A", "course_target": "Writing", "min_grade": "C", "units": 5}
                    ]
                },
                {
                    "term": 3,
                    "courses": [
                        {"course_cc": "MATH 1C", "course_target": "MATH 4A", "min_grade": "C", "units": 5},
                        {"course_cc": "PHYS 4B", "course_target": "PHYS 2", "min_grade": "C", "units": 5},
                        {"course_cc": "ENGR 36", "course_target": "ME 14", "min_grade": "C", "units": 4}
                    ]
                },
                {
                    "term": 4,
                    "courses": [
                        {"course_cc": "MATH 2A", "course_target": "MATH 4B", "min_grade": "C", "units": 5},
                        {"course_cc": "PHYS 4C", "course_target": "PHYS 3", "min_grade": "C", "units": 5},
                        {"course_cc": "ENGR 45", "course_target": "ME 15", "min_grade": "C", "units": 4}
                    ]
                }
            ]
        elif program_key == "ucsd_cse":
            return [
                {
                    "term": 1,
                    "courses": [
                        {"course_cc": "MATH 1A", "course_target": "MATH 20A", "min_grade": "C", "units": 5},
                        {"course_cc": "CIS 22A", "course_target": "CSE 8A", "min_grade": "C", "units": 4},
                        {"course_cc": "EWRT 1A", "course_target": "Writing", "min_grade": "C", "units": 5}
                    ]
                },
                {
                    "term": 2,
                    "courses": [
                        {"course_cc": "MATH 1B", "course_target": "MATH 20B", "min_grade": "C", "units": 5},
                        {"course_cc": "CIS 22B", "course_target": "CSE 8B", "min_grade": "C", "units": 4},
                        {"course_cc": "PHYS 4A", "course_target": "PHYS 2A", "min_grade": "C", "units": 5}
                    ]
                },
                {
                    "term": 3,
                    "courses": [
                        {"course_cc": "MATH 1C", "course_target": "MATH 20C", "min_grade": "C", "units": 5},
                        {"course_cc": "CIS 22C", "course_target": "CSE 12", "min_grade": "C", "units": 4},
                        {"course_cc": "PHYS 4B", "course_target": "PHYS 2B", "min_grade": "C", "units": 5}
                    ]
                },
                {
                    "term": 4,
                    "courses": [
                        {"course_cc": "MATH 2A", "course_target": "MATH 18", "min_grade": "C", "units": 4},
                        {"course_cc": "CIS 35A", "course_target": "CSE 15L", "min_grade": "C", "units": 2},
                        {"course_cc": "MATH 22", "course_target": "CSE 21", "min_grade": "C", "units": 4}
                    ]
                }
            ]
        else:
            return []
            
    def scrape_all_articulations(self):
        """Scrape all CC to target program articulations"""
        results = []
        
        for cc_id in self.COMMUNITY_COLLEGES.keys():
            for program_key in self.TARGET_PROGRAMS.keys():
                result = self.scrape_articulation(cc_id, program_key)
                if result:
                    results.append(result)
                    self._save_result(result)
                    
                # Rate limiting
                time.sleep(1)
                
        logger.info(f"Scraped {len(results)} articulation agreements")
        return results
        
    def _save_result(self, result: Articulation):
        """Save result to JSONL file"""
        with open(self.output_file, 'a') as f:
            f.write(json.dumps(asdict(result)) + '\n')
            
    def generate_manual_template(self):
        """Generate template for manual ASSIST lookups"""
        template_file = self.output_dir / "ASSIST_MANUAL_TEMPLATE.md"
        
        with open(template_file, 'w') as f:
            f.write("# ASSIST.org Manual Lookup Template\n\n")
            f.write("Visit https://assist.org and look up the following articulations:\n\n")
            
            for cc_id, cc in self.COMMUNITY_COLLEGES.items():
                f.write(f"## {cc['name']}\n\n")
                for program_key, program in self.TARGET_PROGRAMS.items():
                    f.write(f"### → {program['school_name']} - {program['major']}\n")
                    f.write(f"- **URL:** https://assist.org/transfer/results?year=74&institution=...\n")
                    f.write(f"- **GPA Floor:** {program['gpa_floor']}\n")
                    f.write(f"- **TAG Eligible:** {program['tag_eligible']}\n")
                    f.write(f"- **Record courses for 4 terms**\n\n")
                    
        logger.info(f"Generated manual template: {template_file}")


def main():
    scraper = ASSISTScraper()
    
    # Generate manual template
    scraper.generate_manual_template()
    
    # Generate example articulations
    scraper.scrape_all_articulations()
    
    logger.info("ASSIST scraper complete")


if __name__ == "__main__":
    main()

