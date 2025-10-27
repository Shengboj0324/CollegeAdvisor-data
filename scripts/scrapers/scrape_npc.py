#!/usr/bin/env python3
"""
Advanced Net Price Calculator (NPC) Scraper
Automates NPC runs for canonical family scenarios across multiple schools
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FamilyScenario:
    """Canonical family financial scenario"""
    scenario_id: str
    agi: int
    assets: Dict[str, int]
    household: int
    students_in_college: int
    parent_marital_status: str
    ncp_contribution: int
    description: str


@dataclass
class NPCResult:
    """Net Price Calculator result"""
    school_id: str
    school_name: str
    ipeds_id: str
    scenario_id: str
    inputs: Dict
    outputs: Dict
    run_date: str
    url: str
    notes: str
    last_verified: str


class NPCScraper:
    """Advanced NPC scraper with multi-school support"""
    
    # Canonical scenarios to test
    SCENARIOS = [
        FamilyScenario(
            scenario_id="AGI50k_Basic",
            agi=50000,
            assets={"parent_401k": 30000, "savings": 5000},
            household=4,
            students_in_college=1,
            parent_marital_status="married",
            ncp_contribution=0,
            description="Low-income, basic assets"
        ),
        FamilyScenario(
            scenario_id="AGI80k_Moderate",
            agi=80000,
            assets={"parent_401k": 60000, "savings": 15000, "529": 20000},
            household=4,
            students_in_college=1,
            parent_marital_status="married",
            ncp_contribution=0,
            description="Middle-income, moderate savings"
        ),
        FamilyScenario(
            scenario_id="AGI120k_TwoKids",
            agi=120000,
            assets={"parent_401k": 90000, "savings": 25000, "529": 40000},
            household=5,
            students_in_college=2,
            parent_marital_status="married",
            ncp_contribution=0,
            description="Upper-middle income, 2 in college"
        ),
        FamilyScenario(
            scenario_id="AGI165k_Scorp_UTMA_529gp",
            agi=165000,
            assets={
                "parent_401k": 110000,
                "utma": 70000,
                "529_gp": 35000,
                "business_equity": 200000,
                "home_equity": 300000
            },
            household=5,
            students_in_college=3,
            parent_marital_status="divorced",
            ncp_contribution=0,
            description="High-income, complex assets, divorced"
        ),
        FamilyScenario(
            scenario_id="AGI200k_HighAssets",
            agi=200000,
            assets={
                "parent_401k": 150000,
                "savings": 50000,
                "529": 80000,
                "home_equity": 400000,
                "rental_property": 250000
            },
            household=4,
            students_in_college=1,
            parent_marital_status="married",
            ncp_contribution=0,
            description="High-income, high assets"
        ),
    ]
    
    # School NPC configurations
    SCHOOLS = {
        "mit": {
            "school_id": "mit",
            "school_name": "Massachusetts Institute of Technology",
            "ipeds_id": "166683",
            "npc_url": "https://npc.collegeboard.org/app/mit",
            "npc_type": "collegeboard"
        },
        "harvard": {
            "school_id": "harvard",
            "school_name": "Harvard University",
            "ipeds_id": "166027",
            "npc_url": "https://college.harvard.edu/financial-aid/net-price-calculator",
            "npc_type": "custom"
        },
        "stanford": {
            "school_id": "stanford",
            "school_name": "Stanford University",
            "ipeds_id": "243744",
            "npc_url": "https://financialaid.stanford.edu/undergrad/how/calculator/",
            "npc_type": "custom"
        },
        "cmu": {
            "school_id": "cmu",
            "school_name": "Carnegie Mellon University",
            "ipeds_id": "211440",
            "npc_url": "https://www.cmu.edu/sfs/financial-aid/net-price-calculator/index.html",
            "npc_type": "collegeboard"
        },
        "umass": {
            "school_id": "umass",
            "school_name": "University of Massachusetts Amherst",
            "ipeds_id": "166629",
            "npc_url": "https://www.umass.edu/umfa/net-price-calculator",
            "npc_type": "custom"
        },
    }
    
    def __init__(self, output_dir: str = "training_data/tier1_costs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / "NPCResult.jsonl"
        self.driver = None
        
    def init_driver(self):
        """Initialize Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        
    def close_driver(self):
        """Close WebDriver"""
        if self.driver:
            self.driver.quit()
            
    def scrape_collegeboard_npc(self, school_config: Dict, scenario: FamilyScenario) -> Optional[NPCResult]:
        """Scrape College Board NPC (used by many schools)"""
        try:
            logger.info(f"Scraping {school_config['school_name']} for scenario {scenario.scenario_id}")
            
            self.driver.get(school_config['npc_url'])
            time.sleep(2)
            
            # Fill in family information
            # Note: This is a template - actual field IDs vary by school
            # You'll need to inspect each school's NPC form
            
            # AGI
            agi_field = self.driver.find_element(By.ID, "agi")
            agi_field.clear()
            agi_field.send_keys(str(scenario.agi))
            
            # Household size
            household_field = self.driver.find_element(By.ID, "household_size")
            household_field.clear()
            household_field.send_keys(str(scenario.household))
            
            # Students in college
            students_field = self.driver.find_element(By.ID, "students_in_college")
            students_field.clear()
            students_field.send_keys(str(scenario.students_in_college))
            
            # Assets (varies by NPC)
            if "parent_401k" in scenario.assets:
                # 401k typically not counted
                pass
            
            if "savings" in scenario.assets:
                savings_field = self.driver.find_element(By.ID, "parent_savings")
                savings_field.clear()
                savings_field.send_keys(str(scenario.assets["savings"]))
            
            # Submit form
            submit_button = self.driver.find_element(By.ID, "submit")
            submit_button.click()
            
            # Wait for results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "npc-results"))
            )
            
            # Parse results
            grant = self._extract_number(self.driver, "grant_amount")
            scholarship = self._extract_number(self.driver, "scholarship_amount")
            loan = self._extract_number(self.driver, "loan_amount")
            work = self._extract_number(self.driver, "work_study_amount")
            net_price = self._extract_number(self.driver, "net_price")
            coa = self._extract_number(self.driver, "cost_of_attendance")
            
            result = NPCResult(
                school_id=school_config['school_id'],
                school_name=school_config['school_name'],
                ipeds_id=school_config['ipeds_id'],
                scenario_id=scenario.scenario_id,
                inputs={
                    "agi": scenario.agi,
                    "assets": scenario.assets,
                    "household": scenario.household,
                    "students_in_college": scenario.students_in_college,
                    "parent_marital_status": scenario.parent_marital_status,
                    "ncp_contribution": scenario.ncp_contribution
                },
                outputs={
                    "grant": grant,
                    "scholarship": scholarship,
                    "loan": loan,
                    "work": work,
                    "net_price": net_price,
                    "coa": coa
                },
                run_date=datetime.now().strftime("%Y-%m-%d"),
                url=school_config['npc_url'],
                notes=scenario.description,
                last_verified=datetime.now().strftime("%Y-%m-%d")
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error scraping {school_config['school_name']}: {e}")
            return None
            
    def _extract_number(self, driver, element_id: str) -> int:
        """Extract numeric value from element"""
        try:
            element = driver.find_element(By.ID, element_id)
            text = element.text.replace('$', '').replace(',', '').strip()
            return int(text)
        except:
            return 0
            
    def scrape_all_schools(self):
        """Scrape all schools for all scenarios"""
        self.init_driver()
        results = []
        
        try:
            for school_id, school_config in self.SCHOOLS.items():
                for scenario in self.SCENARIOS:
                    if school_config['npc_type'] == 'collegeboard':
                        result = self.scrape_collegeboard_npc(school_config, scenario)
                        if result:
                            results.append(result)
                            self._save_result(result)
                    
                    # Rate limiting
                    time.sleep(3)
                    
        finally:
            self.close_driver()
            
        logger.info(f"Scraped {len(results)} NPC results")
        return results
        
    def _save_result(self, result: NPCResult):
        """Save result to JSONL file"""
        with open(self.output_file, 'a') as f:
            f.write(json.dumps(asdict(result)) + '\n')
            
    def generate_manual_template(self):
        """Generate template for manual NPC runs"""
        template_file = self.output_dir / "NPC_MANUAL_TEMPLATE.md"
        
        with open(template_file, 'w') as f:
            f.write("# Manual NPC Run Template\n\n")
            f.write("For schools with custom NPCs that can't be automated, use this template:\n\n")
            
            for scenario in self.SCENARIOS:
                f.write(f"## Scenario: {scenario.scenario_id}\n")
                f.write(f"**Description:** {scenario.description}\n\n")
                f.write(f"**Inputs:**\n")
                f.write(f"- AGI: ${scenario.agi:,}\n")
                f.write(f"- Household: {scenario.household}\n")
                f.write(f"- Students in college: {scenario.students_in_college}\n")
                f.write(f"- Marital status: {scenario.parent_marital_status}\n")
                f.write(f"- Assets:\n")
                for asset, value in scenario.assets.items():
                    f.write(f"  - {asset}: ${value:,}\n")
                f.write("\n")
                f.write("**Results to record:**\n")
                f.write("- Grant: $______\n")
                f.write("- Scholarship: $______\n")
                f.write("- Loan: $______\n")
                f.write("- Work-study: $______\n")
                f.write("- Net Price: $______\n")
                f.write("- COA: $______\n")
                f.write("\n---\n\n")
                
        logger.info(f"Generated manual template: {template_file}")


def main():
    scraper = NPCScraper()
    
    # Generate manual template
    scraper.generate_manual_template()
    
    # Uncomment to run automated scraping (requires Selenium setup)
    # scraper.scrape_all_schools()
    
    logger.info("NPC scraper setup complete")


if __name__ == "__main__":
    main()

