#!/usr/bin/env python3
"""
High-Complexity Stress Test for CollegeAdvisor AI Model
Tests 10 research-heavy, policy-specific prompts requiring current data and authoritative sourcing
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List

class HighComplexityStressTester:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "collegeadvisor:latest"):
        self.base_url = base_url
        self.model = model
        self.results = []
        
    def ask_model(self, prompt: str, test_name: str, timeout: int = 300) -> Dict:
        """Ask the model a high-complexity question"""
        print(f"\n{'='*100}")
        print(f"TEST: {test_name}")
        print(f"{'='*100}")
        print(f"PROMPT:\n{prompt[:200]}...")
        print(f"{'='*100}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                answer = response.json()["response"]
                
                # Analyze response quality for high-complexity criteria
                quality_metrics = self.analyze_complexity_quality(prompt, answer)
                
                result = {
                    'test_name': test_name,
                    'prompt': prompt,
                    'answer': answer,
                    'response_time': response_time,
                    'quality_metrics': quality_metrics,
                    'answer_length': len(answer),
                    'status': 'success'
                }
                
                print(f"\n✅ Response Time: {response_time:.2f}s")
                print(f"📊 Answer Length: {len(answer)} chars")
                print(f"\n📈 QUALITY METRICS:")
                for metric, score in quality_metrics.items():
                    print(f"   {metric}: {score}")
                print(f"\nANSWER PREVIEW:\n{answer[:800]}...")
                
            else:
                result = {
                    'test_name': test_name,
                    'prompt': prompt,
                    'answer': None,
                    'response_time': response_time,
                    'quality_metrics': {},
                    'status': 'error',
                    'error': f"HTTP {response.status_code}"
                }
                print(f"\n❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            response_time = time.time() - start_time
            result = {
                'test_name': test_name,
                'prompt': prompt,
                'answer': None,
                'response_time': response_time,
                'quality_metrics': {},
                'status': 'error',
                'error': str(e)
            }
            print(f"\n❌ Error: {str(e)}")
        
        self.results.append(result)
        return result
    
    def analyze_complexity_quality(self, prompt: str, answer: str) -> Dict:
        """Analyze response quality for high-complexity criteria"""
        metrics = {}
        
        # 1. Source Citations (URLs, official references)
        url_indicators = ['http://', 'https://', '.gov', '.edu', 'StudentAid.gov', 'UCOP', 'NCAA', 'USCIS', 'ICE']
        source_count = sum(1 for indicator in url_indicators if indicator.lower() in answer.lower())
        metrics['Source_Citations'] = f"{source_count} indicators" if source_count > 0 else "❌ None found"
        
        # 2. Quantitative Data (numbers, percentages, dollar amounts)
        has_percentages = '%' in answer
        has_dollar_amounts = '$' in answer
        has_numbers = any(char.isdigit() for char in answer)
        quant_score = sum([has_percentages, has_dollar_amounts, has_numbers])
        metrics['Quantitative_Data'] = f"✅ {quant_score}/3" if quant_score >= 2 else f"⚠️ {quant_score}/3"
        
        # 3. Policy-Specific Terms
        policy_terms = ['FAFSA', 'CSS Profile', 'SAI', 'EFC', 'TAG', 'ASSIST', 'NCAA', 'NIL', 'OPT', 'STEM OPT', 
                       'CPT', 'I-20', 'F-1', 'PGWP', 'UCAS', 'Common App', 'ED', 'EA', 'REA', 'NPC', 'COA',
                       'UTMA', '529', 'AGI', 'WUE', 'WICHE', 'BS/MD', 'MCAT', 'GPA', 'residency', 'need-blind',
                       'need-aware', 'merit', 'direct admit', 'internal transfer', 'impaction']
        policy_count = sum(1 for term in policy_terms if term in answer)
        metrics['Policy_Terms'] = f"✅ {policy_count} terms" if policy_count >= 5 else f"⚠️ {policy_count} terms"
        
        # 4. Structured Output (tables, lists, comparisons)
        has_table = any(indicator in answer for indicator in ['|', '─', '━', 'vs.', 'compared to'])
        has_list = answer.count('\n-') >= 3 or answer.count('\n•') >= 3 or answer.count('\n1.') >= 3
        has_structure = has_table or has_list
        metrics['Structured_Output'] = "✅ Yes" if has_structure else "❌ No"
        
        # 5. Actionable Recommendations
        action_words = ['recommend', 'should', 'must', 'avoid', 'prioritize', 'consider', 'apply to', 
                       'focus on', 'strategy', 'plan', 'timeline', 'deadline', 'next steps']
        action_count = sum(1 for word in action_words if word.lower() in answer.lower())
        metrics['Actionable_Advice'] = f"✅ {action_count} indicators" if action_count >= 5 else f"⚠️ {action_count} indicators"
        
        # 6. Risk/Trap Warnings
        risk_terms = ['risk', 'trap', 'warning', 'caution', 'beware', 'limitation', 'restriction', 
                     'cap', 'cutoff', 'deadline', 'requirement', 'gotcha', 'fine print']
        risk_count = sum(1 for term in risk_terms if term.lower() in answer.lower())
        metrics['Risk_Warnings'] = f"✅ {risk_count} warnings" if risk_count >= 3 else f"⚠️ {risk_count} warnings"
        
        # 7. Specificity (school names, program names, specific numbers)
        school_count = sum(1 for school in ['MIT', 'Stanford', 'Harvard', 'Yale', 'Princeton', 'Columbia',
                                            'Brown', 'Cornell', 'Penn', 'Dartmouth', 'UCLA', 'Berkeley',
                                            'UCSD', 'UCSB', 'UCI', 'UW', 'Michigan', 'Georgia Tech',
                                            'UIUC', 'UT Austin', 'Purdue', 'CMU', 'Caltech', 'USC',
                                            'NYU', 'BU', 'Northeastern', 'Waterloo'] if school in answer)
        metrics['School_Specificity'] = f"✅ {school_count} schools" if school_count >= 3 else f"⚠️ {school_count} schools"
        
        # 8. Length/Depth
        word_count = len(answer.split())
        metrics['Response_Depth'] = f"✅ {word_count} words" if word_count >= 300 else f"⚠️ {word_count} words"
        
        # 9. Overall Complexity Score (0-10)
        complexity_score = 0
        if source_count > 0: complexity_score += 2
        if quant_score >= 2: complexity_score += 2
        if policy_count >= 5: complexity_score += 1.5
        if has_structure: complexity_score += 1.5
        if action_count >= 5: complexity_score += 1
        if risk_count >= 3: complexity_score += 1
        if school_count >= 3: complexity_score += 0.5
        if word_count >= 300: complexity_score += 0.5
        
        metrics['OVERALL_SCORE'] = f"{complexity_score:.1f}/10"
        
        return metrics
    
    def run_all_tests(self):
        """Run all 10 high-complexity stress tests"""
        
        print("\n" + "="*100)
        print("🚀 STARTING HIGH-COMPLEXITY STRESS TEST")
        print("="*100)
        print(f"Model: {self.model}")
        print(f"Total Tests: 10")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)
        
        # Test 1: FAFSA/CSS + SAI Net Price Stress Test
        prompt_1 = """FAFSA/CSS + SAI Net Price Stress Test (divorced + business + 529)

Scenario: U.S. citizen; divorced parents; custodial parent remarried; non-custodial parent refuses CSS; family owns a <50-employee S-corp (owner-operated), 2 rental units, $110k in parent 401(k), $70k in student-owned UTMA; $35k grandparent-owned 529; AGI $165k; 3 kids in college next year.

Question: Compute estimated SAI and college-specific net price at 6 schools (2 FAFSA-only, 4 CSS Profile), including how each treats business equity, home equity, UTMA, grandparent 529, and non-custodial waivers. Show a side-by-side table, cite each school's aid policy page + StudentAid.gov, and state exact assumptions. Provide a "best-value shortlist" and negotiating strategy."""
        
        self.ask_model(prompt_1, "Test 1: FAFSA/CSS SAI Net Price Calculation", timeout=300)
        time.sleep(2)
        
        # Test 2: Capacity-Constrained CS Admissions
        prompt_2 = """Capacity-Constrained CS/Data Science Admissions by Institution + Internal Transfer Risk

Scenario: Applicant targets UIUC (CS vs. CS+X), Georgia Tech (CS), UW (CSE direct-to-major), UCSD (CSE/DS25), UCI (CS/DS), Purdue (CS), UT Austin (CS).

Question: Build a comparison of direct admit vs pre-major, admit rates by major, internal transfer gates (GPA cutoffs, course filters, capacity), and time-to-degree risk if not directly admitted. Include links to each department's latest policy page and Common Data Set where applicable. Conclude with a go/no-go recommendation per school and a risk-mitigation plan (alternate majors, early coursework, petition windows)."""
        
        self.ask_model(prompt_2, "Test 2: CS Admissions & Internal Transfer Risk", timeout=300)
        time.sleep(2)
        
        # Test 3: UC/CSU Residency + WUE
        prompt_3 = """UC/CSU Residency, WUE, and Tuition Optimization for a California HS Senior

Scenario: CA-resident senior weighing UCs, CSUs, and WUE options in AZ/CO/NV/OR/WA/UT/ID/MT, plus Cal Poly SLO vs SDSU.

Question: Explain UC/CSU residency determinations for dependents (financial independence tests, physical presence, intent), and map WUE programs that actually discount tuition for CS/Engineering (many exclude high-demand majors). Produce a decision tree that minimizes net 4-year cost given GPA 3.86 UW, rigor AP/IB, and family AGI $145k. Cite UCOP, CSU, campus registrars, and WICHE WUE pages."""
        
        self.ask_model(prompt_3, "Test 3: UC/CSU Residency & WUE Optimization", timeout=300)
        time.sleep(2)
        
        # Test 4: Pre-Med BS/MD vs Traditional
        prompt_4 = """Pre-Med Pathways: BS/MD vs Traditional (select programs)

Scenario: Compare Brown PLME, Rice/Baylor, Pitt GAP, Case PPSP, Stony Brook Scholars for Medicine vs traditional routes at UCLA, Michigan, UNC, UVA.

Question: For each BS/MD: admission selectivity, MCAT/GPA requirements, conditional guarantees, acceleration, required majors, linkage fine print, attrition, total cost (undergrad+MD), and in-state preference at med schools. For traditional: pre-med advising quality, committee letters, AAMC acceptance data by GPA/MCAT, in-state med school bias. Deliver a ROI and risk analysis with sources (program pages + AAMC)."""
        
        self.ask_model(prompt_4, "Test 4: BS/MD vs Traditional Pre-Med Pathways", timeout=300)
        time.sleep(2)
        
        # Test 5: International Student Need-Aware + Funding
        prompt_5 = """International Student (PRC passport, U.S. HS) — Need-Aware Admissions + Funding

Scenario: F-1 in U.S. HS; intends CS or Data Science; budget $35k/yr max.

Question: Identify need-aware vs need-blind for internationals, schools offering full-need or large merit to internationals; I-20 issuance timelines; proof-of-funds; on-campus work limits; CPT/OPT + STEM OPT extension rules. Provide a ranked list of 12 realistic targets with historical merit patterns and exact links to international aid pages and ICE/USCIS guidance. Include a visa/finance risk register."""
        
        self.ask_model(prompt_5, "Test 5: International Student Need-Aware & Funding", timeout=300)
        time.sleep(2)
        
        # Test 6: U.S. vs Canada vs U.K. CS
        prompt_6 = """U.S. vs Canada vs U.K. CS Undergrad — Immigration + Cost + Outcomes

Scenario: Student wants the fastest path to Big Tech SWE in North America.

Question: Compare total 4-year TCO (tuition, housing, visas, insurance) and post-study work rights (U.S. OPT/STEM, Canada PGWP, U.K. Graduate Route or successor policy), plus internship conversion rates and co-op models (Waterloo/Northeastern/Drexel). Provide policy citations (government/official university sites), note 2024–2026 policy shifts, and output a single best-bet recommendation with contingency routes."""
        
        self.ask_model(prompt_6, "Test 6: U.S. vs Canada vs U.K. CS Comparison", timeout=300)
        time.sleep(2)
        
        # Test 7: CC to UC/CSU Transfer
        prompt_7 = """Community College → UC/CSU Engineering Transfer (ASSIST + TAG/ADT)

Scenario: CA community college student targeting UCSB ME, UCLA ECE, UCSD CSE, Cal Poly SLO ME.

Question: Using ASSIST, map exact lower-division sequences (calc, physics, programming, circuits), GPA floors, TAG eligibility (and exclusions for engineering), ADT leverage for CSU, and realistic 2-year vs 2.5-year transfer timelines. Deliver a semester-by-semester plan with choke points (impaction, lab availability) and list all primary sources (ASSIST + campus College of Engineering pages)."""
        
        self.ask_model(prompt_7, "Test 7: CC to UC/CSU Engineering Transfer", timeout=300)
        time.sleep(2)
        
        # Test 8: NCAA Recruiting + Ivy/Patriot Aid
        prompt_8 = """NCAA Recruiting + Ivy/Patriot Aid Reality Check (NIL included)

Scenario: Top-quartile HS basketball player; interest from Ivy, Patriot, WCC; family need $20k EFC; wants strong CS.

Question: Explain Ivy/Patriot scholarship rules (no athletic scholarships in Ivy), NIL constraints for HS prospects, Official vs Unofficial visits, Likely Letters, prereads, and NLI. Compare real aid expectations using each school's NPC and Common Data Set need met % for nonresidents. Output a recruiting funnel plan, risk of over-reliance on "walk-on," and a negotiation script. Cite NCAA, league manuals, and school sites."""
        
        self.ask_model(prompt_8, "Test 8: NCAA Recruiting & Ivy/Patriot Aid", timeout=300)
        time.sleep(2)
        
        # Test 9: Housing & Total Cost Reality Audit
        prompt_9 = """Housing & Total Cost Reality Audit for Urban Campuses

Scenario: Admits to NYU, BU, Northeastern, USC, UC Berkeley; wants accurate all-in budget outside glossy COA.

Question: Build an all-in 12-month budget per campus: off-campus median rent (studio/2BR share) from reputable market data, transit pass, utilities, health insurance waivers, meal plans vs grocery, fees, and taxes. Reconcile against each school's official Cost of Attendance and explain deltas. Provide a risk analysis for housing scarcity and realistic commute times. Conclude with a ranked value vs outcome recommendation, with source links."""
        
        self.ask_model(prompt_9, "Test 9: Housing & Total Cost Reality Audit", timeout=300)
        time.sleep(2)
        
        # Test 10: Holistic School List Cross-Country
        prompt_10 = """Holistic School List + Deadlines + Deliverables Cross-Country (U.S./Canada/U.K.)

Scenario: STEM-leaning applicant; SAT 1540, 6 APs, strong research; budget $50k/yr; wants CS/HCI/DS; is open to co-ops.

Question: Produce a 15-school portfolio across U.S./Canada/U.K., bucketed (reach/target/likely), with: application platforms (Common App/Coalition/UCAS/OUAC), binding rules (ED/EA/REA), portfolio/writing supplements (e.g., CMU SCS short answers, HCI portfolios where applicable), scholarship deadlines separate from admissions, test policy nuances, UC A-G verification, predicted-grade rules (U.K.), and hard dates. Include acceptance rates by program when available, official links, and a milestones Gantt."""
        
        self.ask_model(prompt_10, "Test 10: Holistic School List Cross-Country", timeout=300)
        time.sleep(2)
        
        print("\n" + "="*100)
        print("✅ ALL HIGH-COMPLEXITY TESTS COMPLETED")
        print("="*100)
    
    def generate_report(self):
        """Generate comprehensive stress test report"""
        
        print("\n" + "="*100)
        print("📊 HIGH-COMPLEXITY STRESS TEST REPORT")
        print("="*100)
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r['status'] == 'success'])
        failed_tests = total_tests - successful_tests
        
        avg_response_time = sum(r['response_time'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        print(f"\n📈 OVERALL STATISTICS")
        print(f"{'='*100}")
        print(f"Total Tests:              {total_tests}")
        print(f"Successful Responses:     {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"Failed Responses:         {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print(f"Average Response Time:    {avg_response_time:.2f} seconds")
        
        print(f"\n📊 DETAILED TEST RESULTS")
        print(f"{'='*100}")
        
        for i, result in enumerate(self.results, 1):
            print(f"\n{i}. {result['test_name']}")
            print(f"   Status: {result['status'].upper()}")
            print(f"   Response Time: {result['response_time']:.2f}s")
            
            if result['status'] == 'success':
                print(f"   Answer Length: {result['answer_length']} chars")
                print(f"   Quality Metrics:")
                for metric, value in result['quality_metrics'].items():
                    print(f"      {metric}: {value}")
            else:
                print(f"   Error: {result.get('error', 'Unknown')}")
        
        # Save detailed results
        with open('high_complexity_stress_test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'failed_tests': failed_tests,
                    'success_rate': successful_tests/total_tests*100 if total_tests > 0 else 0,
                    'avg_response_time': avg_response_time
                },
                'all_results': self.results
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: high_complexity_stress_test_results.json")
        print(f"{'='*100}\n")

def main():
    print("\n" + "="*100)
    print("🧪 HIGH-COMPLEXITY STRESS TEST SUITE")
    print("="*100)
    print("\nThis will test the model with 10 research-heavy, policy-specific prompts")
    print("requiring current data, authoritative sourcing, and precise quantification.")
    print("\nEstimated time: 10-15 minutes")
    print("="*100)
    
    input("\nPress Enter to start testing...")
    
    tester = HighComplexityStressTester()
    
    start_time = time.time()
    tester.run_all_tests()
    total_time = time.time() - start_time
    
    print(f"\n⏱️  Total testing time: {total_time/60:.1f} minutes")
    
    tester.generate_report()

if __name__ == "__main__":
    main()

