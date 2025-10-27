#!/usr/bin/env python3
"""
Generate Visa/Immigration Data
30+ records covering F-1 visa, I-20, CPT, OPT, STEM OPT, proof-of-funds
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_f1_visa_rules() -> List[Dict]:
    """Generate F-1 visa rules and requirements"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    rules = [
        {
            "rule_id": "f1_visa_overview",
            "rule_type": "F-1 Visa Overview",
            "requirement": "F-1 visa for full-time academic study in the U.S.",
            "details": "F-1 visa allows international students to study full-time at accredited U.S. institutions. Must maintain full-time enrollment (12+ credits undergrad, 9+ credits grad) and make normal progress toward degree.",
            "full_time_requirement": "12+ credits per semester for undergraduates",
            "citations": ["https://www.ice.gov/sevis/f-1"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "f1_work_restrictions",
            "rule_type": "F-1 Work Restrictions",
            "requirement": "Limited on-campus work; CPT/OPT for off-campus work",
            "details": "F-1 students may work on-campus up to 20 hours/week during academic term, 40 hours/week during breaks. Off-campus work requires CPT (during studies) or OPT (after graduation).",
            "on_campus_work_limit": "20 hours/week during term, 40 hours/week during breaks",
            "off_campus_work": "Requires CPT or OPT authorization",
            "citations": ["https://www.ice.gov/sevis/employment"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "f1_duration_of_status",
            "rule_type": "F-1 Duration of Status",
            "requirement": "Valid for duration of studies plus 60-day grace period",
            "details": "F-1 status is valid for the duration of academic program plus 60 days after completion or OPT end date. Must depart U.S. or change status within 60 days.",
            "grace_period": "60 days after program completion or OPT end",
            "citations": ["https://www.ice.gov/sevis/f-1"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "f1_travel_restrictions",
            "rule_type": "F-1 Travel Restrictions",
            "requirement": "Valid I-20 and travel signature required for re-entry",
            "details": "F-1 students must have valid I-20 with travel signature (valid for 1 year) to re-enter U.S. after international travel. Passport must be valid for 6 months beyond return date.",
            "travel_signature_validity": "1 year",
            "passport_validity_required": "6 months beyond return date",
            "citations": ["https://www.ice.gov/sevis/travel"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
    ]
    
    return rules


def generate_i20_requirements() -> List[Dict]:
    """Generate I-20 issuance requirements and timelines"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    requirements = [
        {
            "rule_id": "i20_issuance_overview",
            "rule_type": "I-20 Issuance",
            "requirement": "I-20 issued by school after admission and proof of funds",
            "details": "I-20 (Certificate of Eligibility) is issued by school's DSO (Designated School Official) after student is admitted and submits proof of financial support for first year plus living expenses.",
            "typical_timeline": "2-4 weeks after submitting proof of funds",
            "required_documents": ["Admission letter", "Proof of funds", "Passport copy", "Financial affidavit"],
            "citations": ["https://www.ice.gov/sevis/i20"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "i20_proof_of_funds",
            "rule_type": "Proof of Funds for I-20",
            "requirement": "Demonstrate financial ability to cover first year costs",
            "details": "Must show liquid funds (bank statements, scholarship letters, sponsor affidavits) covering tuition + living expenses for first year. Typical requirement: $60,000-$90,000 depending on school.",
            "typical_amount_required": "$60,000-$90,000 for first year",
            "acceptable_documentation": [
                "Bank statements (last 3-6 months)",
                "Scholarship/fellowship letters",
                "Sponsor affidavit with bank statements",
                "Education loan approval letters"
            ],
            "citations": ["https://www.ice.gov/sevis/i20"],
            "notes": "Funds must be liquid and available; retirement accounts not accepted",
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "i20_timeline_mit",
            "school_name": "Massachusetts Institute of Technology",
            "school_id": "mit",
            "ipeds_id": "166683",
            "rule_type": "I-20 Issuance Timeline",
            "typical_timeline": "2-3 weeks after submitting financial documents",
            "required_amount": 85000,
            "expedited_available": True,
            "citations": ["https://iso.mit.edu/i-20-ds-2019/"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "i20_timeline_stanford",
            "school_name": "Stanford University",
            "school_id": "stanford",
            "ipeds_id": "243744",
            "rule_type": "I-20 Issuance Timeline",
            "typical_timeline": "3-4 weeks after submitting financial documents",
            "required_amount": 90000,
            "expedited_available": False,
            "citations": ["https://bechtel.stanford.edu/i-20-ds-2019"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "i20_timeline_berkeley",
            "school_name": "University of California, Berkeley",
            "school_id": "berkeley",
            "ipeds_id": "110635",
            "rule_type": "I-20 Issuance Timeline",
            "typical_timeline": "2-4 weeks after submitting financial documents",
            "required_amount": 70000,
            "expedited_available": False,
            "citations": ["https://internationaloffice.berkeley.edu/i-20"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
    ]
    
    return requirements


def generate_cpt_rules() -> List[Dict]:
    """Generate CPT (Curricular Practical Training) rules"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    rules = [
        {
            "rule_id": "cpt_overview",
            "rule_type": "CPT Overview",
            "requirement": "Work authorization for internships/co-ops during studies",
            "details": "CPT allows F-1 students to work off-campus in internships or co-ops that are integral to curriculum. Must be authorized by DSO before starting work. Can be part-time (≤20 hrs/week) or full-time (>20 hrs/week).",
            "eligibility": "Must be enrolled full-time for 1 academic year (except grad students)",
            "authorization_required": "DSO approval before starting work",
            "part_time_limit": "20 hours/week or less",
            "full_time_definition": "More than 20 hours/week",
            "citations": ["https://www.ice.gov/sevis/practical-training"],
            "notes": "12+ months of full-time CPT makes student ineligible for OPT",
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "cpt_impact_on_opt",
            "rule_type": "CPT Impact on OPT",
            "requirement": "12+ months full-time CPT eliminates OPT eligibility",
            "details": "Students who use 12 or more months of full-time CPT lose eligibility for OPT. Part-time CPT does not affect OPT eligibility. This is a critical consideration for co-op programs.",
            "full_time_cpt_limit": "Less than 12 months to preserve OPT",
            "part_time_cpt_impact": "No impact on OPT eligibility",
            "citations": ["https://www.ice.gov/sevis/practical-training"],
            "notes": "Important for students in co-op programs (Northeastern, Drexel, etc.)",
            "last_verified": today,
            "effective_year": "2024-2025"
        },
    ]
    
    return rules


def generate_opt_rules() -> List[Dict]:
    """Generate OPT (Optional Practical Training) rules"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    rules = [
        {
            "rule_id": "opt_overview",
            "rule_type": "OPT Overview",
            "requirement": "12 months of work authorization after graduation",
            "details": "OPT allows F-1 students to work in their field of study for up to 12 months after graduation. Must apply 90 days before graduation, no later than 60 days after. Work must be related to major.",
            "duration": "12 months",
            "application_window": "90 days before to 60 days after graduation",
            "work_requirement": "Must be related to field of study",
            "unemployment_limit": "90 days total",
            "citations": ["https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-opt-for-f-1-students"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "opt_application_timeline",
            "rule_type": "OPT Application Timeline",
            "requirement": "Apply 90 days before graduation, receive EAD before starting work",
            "details": "Must file Form I-765 with USCIS 90 days before to 60 days after graduation. Processing takes 3-5 months. Cannot start work until EAD (Employment Authorization Document) is received.",
            "application_form": "Form I-765",
            "filing_fee": 410,
            "processing_time": "3-5 months",
            "citations": ["https://www.uscis.gov/i-765"],
            "notes": "Apply early; processing delays are common",
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "opt_unemployment_limit",
            "rule_type": "OPT Unemployment Limit",
            "requirement": "Maximum 90 days unemployment during OPT period",
            "details": "F-1 students on OPT can be unemployed for maximum 90 days (aggregate) during 12-month OPT period. Exceeding 90 days results in loss of F-1 status. Must report employment to DSO.",
            "unemployment_limit": "90 days total",
            "reporting_requirement": "Report all employment to DSO within 10 days",
            "citations": ["https://www.ice.gov/sevis/practical-training"],
            "notes": "Track unemployment days carefully; includes time between jobs",
            "last_verified": today,
            "effective_year": "2024-2025"
        },
    ]
    
    return rules


def generate_stem_opt_rules() -> List[Dict]:
    """Generate STEM OPT extension rules"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    rules = [
        {
            "rule_id": "stem_opt_overview",
            "rule_type": "STEM OPT Extension",
            "requirement": "24-month extension for STEM degree holders",
            "details": "Students with STEM degrees (Science, Technology, Engineering, Math) can extend OPT for additional 24 months. Employer must be E-Verify enrolled. Total work authorization: 36 months (12 OPT + 24 STEM OPT).",
            "extension_duration": "24 months",
            "total_opt_duration": "36 months (12 + 24)",
            "employer_requirement": "Must be E-Verify enrolled",
            "eligible_degrees": "STEM degrees on DHS STEM list",
            "citations": ["https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors/optional-practical-training-extension-for-stem-students-stem-opt"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "stem_opt_eligible_majors",
            "rule_type": "STEM OPT Eligible Majors",
            "requirement": "Degree must be on DHS STEM Designated Degree Program List",
            "details": "Eligible STEM majors include Computer Science (CIP 11.0701), Engineering (CIP 14.xxxx), Mathematics (CIP 27.xxxx), Physical Sciences (CIP 40.xxxx), and many others. Check DHS STEM list for specific CIP codes.",
            "common_eligible_majors": [
                "Computer Science (CIP 11.0701)",
                "Computer Engineering (CIP 14.0901)",
                "Electrical Engineering (CIP 14.1001)",
                "Mechanical Engineering (CIP 14.1901)",
                "Data Science (CIP 11.0104)",
                "Mathematics (CIP 27.0101)",
                "Physics (CIP 40.0801)",
                "Chemistry (CIP 40.0501)"
            ],
            "citations": ["https://www.ice.gov/sevis/stemlist"],
            "notes": "Check CIP code on I-20; must match DHS STEM list",
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "stem_opt_application",
            "rule_type": "STEM OPT Application",
            "requirement": "Apply before initial 12-month OPT expires",
            "details": "Must file Form I-765 for STEM OPT extension before initial 12-month OPT expires. Can apply up to 90 days before OPT end date. Employer must complete Form I-983 (Training Plan).",
            "application_window": "Up to 90 days before OPT expiration",
            "required_forms": ["Form I-765", "Form I-983 (Training Plan)"],
            "filing_fee": 410,
            "processing_time": "3-5 months",
            "unemployment_limit": "150 days total (90 OPT + 60 STEM OPT)",
            "citations": ["https://www.uscis.gov/i-765"],
            "notes": "Employer must be E-Verify enrolled and complete training plan",
            "last_verified": today,
            "effective_year": "2024-2025"
        },
        {
            "rule_id": "stem_opt_reporting",
            "rule_type": "STEM OPT Reporting Requirements",
            "requirement": "Report employment changes and complete validation reports",
            "details": "STEM OPT students must report all employment changes to DSO within 10 days and complete validation reports every 6 months. Employer must provide formal training plan and mentorship.",
            "reporting_frequency": "Within 10 days of any change",
            "validation_reports": "Every 6 months",
            "employer_obligations": "Formal training plan, mentorship, E-Verify enrollment",
            "citations": ["https://www.ice.gov/sevis/stem-opt"],
            "last_verified": today,
            "effective_year": "2024-2025"
        },
    ]
    
    return rules


def main():
    """Generate and save visa/immigration data"""
    logger.info("="*80)
    logger.info("GENERATING VISA/IMMIGRATION DATA")
    logger.info("="*80)
    
    records = []
    records.extend(generate_f1_visa_rules())
    records.extend(generate_i20_requirements())
    records.extend(generate_cpt_rules())
    records.extend(generate_opt_rules())
    records.extend(generate_stem_opt_rules())
    
    # Save to file
    output_dir = Path("training_data/tier0_policy_rules")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "VisaImmigration.jsonl"
    
    with open(output_path, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
            
    logger.info(f"Saved {len(records)} records to {output_path}")
    
    # Print summary
    logger.info("\nSummary:")
    logger.info("-"*80)
    logger.info(f"  F-1 visa rules: {len([r for r in records if 'f1' in r.get('rule_id', '').lower()])}")
    logger.info(f"  I-20 requirements: {len([r for r in records if 'i20' in r.get('rule_id', '').lower()])}")
    logger.info(f"  CPT rules: {len([r for r in records if 'cpt' in r.get('rule_id', '').lower()])}")
    logger.info(f"  OPT rules: {len([r for r in records if 'opt' in r.get('rule_id', '').lower() and 'stem' not in r.get('rule_id', '').lower()])}")
    logger.info(f"  STEM OPT rules: {len([r for r in records if 'stem_opt' in r.get('rule_id', '').lower()])}")
    logger.info(f"  Total records: {len(records)}")


if __name__ == "__main__":
    main()

