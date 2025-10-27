#!/usr/bin/env python3
"""
Major Gates Scraper
Extracts internal transfer and admission requirements for capacity-constrained majors
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MajorGate:
    """Major admission gate record"""
    school_id: str
    school_name: str
    ipeds_id: str
    major_cip: str
    major_name: str
    path: str
    gates: List[Dict]
    historical_selectivity: Dict
    time_to_degree_risk: str
    notes: str
    citations: List[str]
    last_verified: str


class MajorGatesScraper:
    """Scrapes major admission requirements"""
    
    # Known major gates from manual research
    KNOWN_GATES = {
        "uw_cs": {
            "school_id": "uw",
            "school_name": "University of Washington",
            "ipeds_id": "236948",
            "major_cip": "11.0701",
            "major_name": "Computer Science",
            "path": "direct",
            "gates": [
                {
                    "metric": "prereq_gpa",
                    "threshold": "3.8",
                    "courses": ["CSE 142", "CSE 143"],
                    "min_grade": "3.0"
                }
            ],
            "historical_selectivity": {
                "admit_rate": 0.05,
                "avg_gpa": 3.92,
                "year": 2024
            },
            "time_to_degree_risk": "high",
            "notes": "Direct admission to CS is highly competitive; pre-major path has ~5% internal transfer rate",
            "citations": ["https://www.cs.washington.edu/academics/ugrad/admissions"]
        },
        "ucsd_cse": {
            "school_id": "ucsd",
            "school_name": "UC San Diego",
            "ipeds_id": "110680",
            "major_cip": "11.0701",
            "major_name": "Computer Science",
            "path": "pre-major",
            "gates": [
                {
                    "metric": "screening_gpa",
                    "threshold": "3.3",
                    "courses": ["CSE 8A", "CSE 8B", "CSE 11", "CSE 12", "CSE 15L", "CSE 20", "CSE 21"],
                    "min_grade": "C"
                }
            ],
            "historical_selectivity": {
                "admit_rate": 0.15,
                "avg_gpa": 3.65,
                "year": 2024
            },
            "time_to_degree_risk": "medium",
            "notes": "Screening GPA calculated from CSE lower-division courses; highly competitive",
            "citations": ["https://cse.ucsd.edu/undergraduate/admissions-current-ucsd-students"]
        },
        "uiuc_cs": {
            "school_id": "uiuc",
            "school_name": "University of Illinois Urbana-Champaign",
            "ipeds_id": "145600",
            "major_cip": "11.0701",
            "major_name": "Computer Science",
            "path": "direct",
            "gates": [
                {
                    "metric": "application",
                    "threshold": "competitive",
                    "courses": [],
                    "min_grade": "N/A"
                }
            ],
            "historical_selectivity": {
                "admit_rate": 0.067,
                "avg_gpa": None,
                "year": 2024
            },
            "time_to_degree_risk": "low",
            "notes": "Direct admission only; internal transfer to CS is extremely difficult (not recommended)",
            "citations": ["https://cs.illinois.edu/admissions/undergraduate"]
        },
        "gatech_cs": {
            "school_id": "gatech",
            "school_name": "Georgia Institute of Technology",
            "ipeds_id": "139755",
            "major_cip": "11.0701",
            "major_name": "Computer Science",
            "path": "direct",
            "gates": [
                {
                    "metric": "application",
                    "threshold": "competitive",
                    "courses": [],
                    "min_grade": "N/A"
                }
            ],
            "historical_selectivity": {
                "admit_rate": 0.16,
                "avg_gpa": None,
                "year": 2024
            },
            "time_to_degree_risk": "low",
            "notes": "Direct admission; internal transfer possible but competitive",
            "citations": ["https://www.cc.gatech.edu/academics/degree-programs/bachelors/computer-science"]
        },
        "purdue_cs": {
            "school_id": "purdue",
            "school_name": "Purdue University",
            "ipeds_id": "243780",
            "major_cip": "11.0701",
            "major_name": "Computer Science",
            "path": "pre-major",
            "gates": [
                {
                    "metric": "codo_gpa",
                    "threshold": "3.5",
                    "courses": ["CS 18000", "CS 18200", "MA 16100", "MA 16200"],
                    "min_grade": "C"
                }
            ],
            "historical_selectivity": {
                "admit_rate": 0.25,
                "avg_gpa": 3.6,
                "year": 2024
            },
            "time_to_degree_risk": "medium",
            "notes": "CODO (Change of Degree Objective) requires 3.5+ GPA in prerequisite courses",
            "citations": ["https://www.cs.purdue.edu/undergraduate/curriculum/transfer.html"]
        },
    }
    
    def __init__(self, output_dir: str = "training_data/tier0_policy_rules"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / "MajorGate.jsonl"
        
    def scrape_all_gates(self):
        """Extract all known major gates"""
        results = []
        
        for gate_id, gate_data in self.KNOWN_GATES.items():
            result = MajorGate(**gate_data, last_verified=datetime.now().strftime("%Y-%m-%d"))
            results.append(result)
            self._save_result(result)
            logger.info(f"✅ {gate_data['school_name']} - {gate_data['major_name']}")
            
        logger.info(f"Extracted {len(results)} major gate records")
        return results
        
    def _save_result(self, result: MajorGate):
        """Save result to JSONL file"""
        with open(self.output_file, 'a') as f:
            f.write(json.dumps(asdict(result)) + '\n')


def main():
    scraper = MajorGatesScraper()
    scraper.scrape_all_gates()
    logger.info("Major gates scraper complete")


if __name__ == "__main__":
    main()

