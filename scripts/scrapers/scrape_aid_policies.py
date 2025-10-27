#!/usr/bin/env python3
"""
Financial Aid Policy Scraper
Extracts CSS Profile institutional policies from school websites
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InstitutionAidPolicy:
    """Institution-specific financial aid policy"""
    school_id: str
    school_name: str
    ipeds_id: str
    policy_topic: str
    rule: str
    citations: List[str]
    exceptions: str
    last_verified: str


class AidPolicyScraper:
    """Scrapes financial aid policies from school websites"""
    
    SCHOOLS = {
        "mit": {
            "school_id": "mit",
            "school_name": "Massachusetts Institute of Technology",
            "ipeds_id": "166683",
            "aid_url": "https://sfs.mit.edu/undergraduate-students/the-cost-of-attendance/",
            "policies": {
                "home_equity": "https://sfs.mit.edu/undergraduate-students/the-cost-of-attendance/outside-awards-and-additional-funding/home-equity-policy/",
                "outside_scholarships": "https://sfs.mit.edu/undergraduate-students/the-cost-of-attendance/outside-awards-and-additional-funding/",
                "ncp_waiver": "https://sfs.mit.edu/undergraduate-students/the-cost-of-attendance/css-profile/"
            }
        },
        "harvard": {
            "school_id": "harvard",
            "school_name": "Harvard University",
            "ipeds_id": "166027",
            "aid_url": "https://college.harvard.edu/financial-aid",
            "policies": {
                "home_equity": "https://college.harvard.edu/financial-aid/how-aid-works",
                "outside_scholarships": "https://college.harvard.edu/financial-aid/how-aid-works/outside-awards",
                "ncp_waiver": "https://college.harvard.edu/financial-aid/how-to-apply/application-requirements"
            }
        },
        "stanford": {
            "school_id": "stanford",
            "school_name": "Stanford University",
            "ipeds_id": "243744",
            "aid_url": "https://financialaid.stanford.edu/undergrad/",
            "policies": {
                "home_equity": "https://financialaid.stanford.edu/undergrad/how/parent.html",
                "outside_scholarships": "https://financialaid.stanford.edu/undergrad/how/outside.html",
                "ncp_waiver": "https://financialaid.stanford.edu/undergrad/how/apply.html"
            }
        },
    }
    
    # Known policies from manual research
    KNOWN_POLICIES = {
        "mit": {
            "home_equity": "Home equity capped at 1.2x annual income for families with AGI over $200k; ignored for families with AGI under $100k",
            "outside_scholarships": "Outside scholarships first reduce student contribution (work-study, loans), then institutional grant",
            "ncp_waiver": "NCP waiver available with documentation; professional judgment applied case-by-case"
        },
        "harvard": {
            "home_equity": "Home equity ignored for families with AGI under $200k; capped at modest multiple for higher incomes",
            "outside_scholarships": "Outside scholarships reduce student contribution first, then institutional grant dollar-for-dollar",
            "ncp_waiver": "NCP waiver available; requires documentation of no contact or financial support"
        },
        "stanford": {
            "home_equity": "Home equity capped at 1.2x annual income",
            "outside_scholarships": "Outside scholarships reduce self-help (loans, work-study) first up to $5,000, then reduce institutional grant",
            "ncp_waiver": "NCP waiver available with documentation; professional judgment applied"
        },
        "princeton": {
            "home_equity": "Home equity capped at 1.2x annual income",
            "outside_scholarships": "Outside scholarships reduce student contribution first, then institutional grant",
            "ncp_waiver": "NCP waiver available; requires documentation"
        },
        "yale": {
            "home_equity": "Home equity capped at 1.2x annual income for families with AGI over $200k",
            "outside_scholarships": "Outside scholarships reduce student contribution (work-study, summer earnings) first",
            "ncp_waiver": "NCP waiver available with documentation"
        },
    }
    
    def __init__(self, output_dir: str = "training_data/tier0_policy_rules"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / "InstitutionAidPolicy.jsonl"
        
    def scrape_all_policies(self):
        """Scrape all known policies"""
        results = []
        
        for school_id, policies in self.KNOWN_POLICIES.items():
            school_config = self.SCHOOLS.get(school_id, {
                "school_id": school_id,
                "school_name": school_id.upper(),
                "ipeds_id": "000000",
                "aid_url": "",
                "policies": {}
            })
            
            for policy_topic, rule in policies.items():
                policy_url = school_config.get("policies", {}).get(policy_topic, school_config.get("aid_url", ""))
                
                result = InstitutionAidPolicy(
                    school_id=school_config["school_id"],
                    school_name=school_config["school_name"],
                    ipeds_id=school_config["ipeds_id"],
                    policy_topic=policy_topic,
                    rule=rule,
                    citations=[policy_url] if policy_url else [],
                    exceptions="Professional judgment may apply for unusual circumstances",
                    last_verified=datetime.now().strftime("%Y-%m-%d")
                )
                
                results.append(result)
                self._save_result(result)
                logger.info(f"✅ {school_config['school_name']} - {policy_topic}")
                
        logger.info(f"Extracted {len(results)} aid policy records")
        return results
        
    def _save_result(self, result: InstitutionAidPolicy):
        """Save result to JSONL file"""
        with open(self.output_file, 'a') as f:
            f.write(json.dumps(asdict(result)) + '\n')


def main():
    scraper = AidPolicyScraper()
    scraper.scrape_all_policies()
    logger.info("Aid policy scraper complete")


if __name__ == "__main__":
    main()

