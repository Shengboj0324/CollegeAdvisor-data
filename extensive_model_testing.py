#!/usr/bin/env python3
"""
Extensive Model Quality Testing Suite
Tests 60-100 complex questions across multiple categories
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

class ExtensiveModelTester:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "collegeadvisor:latest"):
        self.base_url = base_url
        self.model = model
        self.results = []
        self.categories = {
            'essay_writing': [],
            'admission_analysis': [],
            'data_driven': [],
            'personalized_advice': [],
            'trends_analysis': [],
            'strategic_planning': [],
            'financial_aid': [],
            'program_specific': [],
            'comparative_analysis': [],
            'critical_thinking': []
        }
        
    def ask_model(self, question: str, category: str) -> Dict:
        """Ask the model a question and record results"""
        print(f"\n{'='*80}")
        print(f"Category: {category.upper()}")
        print(f"Question: {question[:100]}...")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": question,
                    "stream": False
                },
                timeout=180
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                answer = response.json()["response"]
                
                # Analyze response quality
                quality_score = self.analyze_quality(question, answer)
                
                result = {
                    'category': category,
                    'question': question,
                    'answer': answer,
                    'response_time': response_time,
                    'quality_score': quality_score,
                    'answer_length': len(answer),
                    'status': 'success'
                }
                
                print(f"\n✅ Response Time: {response_time:.2f}s")
                print(f"📊 Quality Score: {quality_score}/10")
                print(f"📝 Answer Length: {len(answer)} chars")
                print(f"\nAnswer Preview:\n{answer[:500]}...")
                
            else:
                result = {
                    'category': category,
                    'question': question,
                    'answer': None,
                    'response_time': response_time,
                    'quality_score': 0,
                    'status': 'error',
                    'error': f"HTTP {response.status_code}"
                }
                print(f"\n❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            response_time = time.time() - start_time
            result = {
                'category': category,
                'question': question,
                'answer': None,
                'response_time': response_time,
                'quality_score': 0,
                'status': 'error',
                'error': str(e)
            }
            print(f"\n❌ Error: {str(e)}")
        
        self.results.append(result)
        self.categories[category].append(result)
        
        return result
    
    def analyze_quality(self, question: str, answer: str) -> float:
        """Analyze response quality (0-10 scale)"""
        score = 0.0
        
        # Length check (not too short, not too long)
        if 100 < len(answer) < 3000:
            score += 2.0
        elif 50 < len(answer) < 5000:
            score += 1.0
        
        # Specificity check (contains numbers, percentages, specific terms)
        if any(char.isdigit() for char in answer):
            score += 1.5
        if '%' in answer:
            score += 0.5
        
        # Structure check (contains multiple sentences)
        sentences = answer.count('.') + answer.count('!') + answer.count('?')
        if sentences >= 3:
            score += 1.5
        
        # Detail check (contains specific keywords)
        detail_keywords = ['specific', 'example', 'such as', 'including', 'for instance', 
                          'particularly', 'especially', 'typically', 'generally']
        if any(keyword in answer.lower() for keyword in detail_keywords):
            score += 1.5
        
        # Analytical depth (contains reasoning words)
        analytical_keywords = ['because', 'therefore', 'however', 'although', 'while',
                              'consider', 'analyze', 'compare', 'contrast', 'evaluate']
        if any(keyword in answer.lower() for keyword in analytical_keywords):
            score += 1.5
        
        # Actionable advice (contains action verbs)
        action_keywords = ['should', 'recommend', 'suggest', 'focus', 'emphasize',
                          'highlight', 'demonstrate', 'showcase', 'develop']
        if any(keyword in answer.lower() for keyword in action_keywords):
            score += 1.5
        
        return min(score, 10.0)
    
    def run_all_tests(self):
        """Run all 60-100 test questions"""
        
        print("\n" + "="*80)
        print("🚀 STARTING EXTENSIVE MODEL QUALITY TESTING")
        print("="*80)
        print(f"Model: {self.model}")
        print(f"Total Questions: 80")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Category 1: Essay Writing (15 questions)
        essay_questions = [
            "How should I structure my Common App personal statement? What are the key elements that admissions officers look for?",
            "What makes a compelling college essay opening? Give me specific examples of effective hooks.",
            "Should I write about overcoming adversity in my college essay? What are the pros and cons?",
            "How can I make my college essay stand out when writing about a common topic like sports or volunteering?",
            "What's the ideal tone for a college essay - formal, casual, or somewhere in between? How do I find my authentic voice?",
            "How do I write about my academic interests without sounding too technical or boring?",
            "What are common mistakes students make in their college essays that I should avoid?",
            "How personal should I get in my college essay? Where's the line between vulnerability and oversharing?",
            "Should I use humor in my college essay? What are the risks and benefits?",
            "How do I write a strong 'Why This College' essay that goes beyond generic praise?",
            "What's the best way to show intellectual curiosity in my college essays?",
            "How can I effectively write about failure or setbacks in my application essays?",
            "Should I mention mental health challenges in my college essay? How do I approach this sensitively?",
            "How do I write compelling supplemental essays when I'm applying to 15+ schools?",
            "What role should my cultural background or identity play in my college essays?"
        ]
        
        for q in essay_questions:
            self.ask_model(q, 'essay_writing')
            time.sleep(1)
        
        # Category 2: Admission Analysis (15 questions)
        admission_questions = [
            "What percentage chance do I have of getting into Harvard with a 4.0 GPA, 1580 SAT, and strong extracurriculars?",
            "How much does being a legacy student actually improve admission chances at Ivy League schools?",
            "What's the acceptance rate for early decision vs regular decision at Stanford? How much does applying early help?",
            "If I'm applying to MIT for computer science, what are the typical stats of admitted students in this major?",
            "How do admission rates differ between in-state and out-of-state applicants at UC Berkeley?",
            "What percentage of students get off the waitlist at top 20 universities? Is it worth staying on?",
            "How competitive is admission to Wharton School of Business compared to other Penn schools?",
            "What are my chances at Yale with a 3.85 GPA but exceptional research experience and publications?",
            "How does demonstrated interest affect admission chances at different types of schools?",
            "What's the admission rate for international students at top US universities compared to domestic students?",
            "How much do standardized test scores matter in test-optional admissions? Should I still submit a 1450 SAT?",
            "What percentage of admitted students at Princeton have perfect GPAs? Can I get in with a 3.9?",
            "How competitive is transfer admission to Columbia compared to freshman admission?",
            "What are the admission statistics for recruited athletes vs non-athletes at Ivy League schools?",
            "How does applying for financial aid affect admission chances at need-aware universities?"
        ]
        
        for q in admission_questions:
            self.ask_model(q, 'admission_analysis')
            time.sleep(1)
        
        # Category 3: Data-Driven Questions (10 questions)
        data_questions = [
            "What has been the trend in Ivy League admission rates over the past 10 years? Show me the data.",
            "How have average SAT scores of admitted students at top 20 schools changed from 2015 to 2024?",
            "What percentage of students at MIT are STEM majors vs humanities majors? How has this changed over time?",
            "Compare the yield rates (percentage of admitted students who enroll) at Harvard, Stanford, and MIT.",
            "What's the average financial aid package at Princeton vs Yale vs Harvard for students from families making under $75k?",
            "How many students apply early action vs regular decision at top universities? What are the trends?",
            "What percentage of students at elite universities come from the top 1% income bracket?",
            "How do graduation rates compare between Ivy League schools and top public universities?",
            "What's the average class size at liberal arts colleges vs large research universities?",
            "How have international student enrollment numbers changed at US universities over the past 5 years?"
        ]
        
        for q in data_questions:
            self.ask_model(q, 'data_driven')
            time.sleep(1)
        
        # Category 4: Personalized Advice (10 questions)
        personalized_questions = [
            "I'm a first-gen student with 3.7 GPA, 1380 SAT, strong community service. What schools should I target?",
            "I want to study neuroscience and eventually go to med school. Which undergrad programs should I consider?",
            "I'm interested in both computer science and business. Should I apply to dual degree programs or choose one?",
            "I'm a recruited athlete with decent academics (3.5 GPA). How should I balance athletic and academic fit?",
            "I'm passionate about environmental science but my school doesn't offer many related courses. How do I show this interest?",
            "I'm a homeschooled student applying to college. What additional materials should I prepare?",
            "I want to study film/cinema but my parents want me to pursue something 'practical'. How do I navigate this?",
            "I'm a transfer student from community college. What do top universities look for in transfer applicants?",
            "I'm taking a gap year before college. How do I make it productive and strengthen my application?",
            "I'm interested in women's colleges. What are the unique advantages and how do I decide if they're right for me?"
        ]
        
        for q in personalized_questions:
            self.ask_model(q, 'personalized_advice')
            time.sleep(1)
        
        # Category 5: Trends Analysis (8 questions)
        trends_questions = [
            "How has the test-optional movement changed college admissions? What are the long-term implications?",
            "What impact has the Supreme Court decision on affirmative action had on college admissions?",
            "How are universities adapting their admissions processes in response to AI and ChatGPT?",
            "What's the trend in early decision applications? Are more students applying early?",
            "How has the pandemic affected college admissions policies and what changes are permanent?",
            "What's the trend in demonstrated interest - are more schools tracking it or moving away from it?",
            "How are holistic admissions practices evolving at top universities?",
            "What's the future of standardized testing in college admissions?"
        ]
        
        for q in trends_questions:
            self.ask_model(q, 'trends_analysis')
            time.sleep(1)
        
        # Category 6: Strategic Planning (8 questions)
        strategic_questions = [
            "Should I apply to more reach schools or target schools? What's the ideal balance in my college list?",
            "Is it better to be well-rounded or highly specialized (spiked) in my extracurriculars?",
            "Should I retake a 1520 SAT to try for a perfect score? Is the improvement worth it?",
            "How do I decide between applying early decision vs early action vs regular decision?",
            "Should I take 5 AP classes senior year or focus on depth in my extracurriculars?",
            "Is it worth applying to Ivy League schools if my stats are slightly below average?",
            "Should I apply to my state flagship as a safety even if I want to go out of state?",
            "How many colleges should I apply to? What's too many and what's too few?"
        ]
        
        for q in strategic_questions:
            self.ask_model(q, 'strategic_planning')
            time.sleep(1)
        
        # Category 7: Financial Aid (7 questions)
        financial_questions = [
            "What's the difference between need-blind, need-aware, and need-based admissions?",
            "Which top universities offer the best financial aid packages for middle-class families?",
            "How do I negotiate financial aid offers? Is it possible to get more aid after admission?",
            "What are the best merit scholarship programs at top universities?",
            "Should I apply for outside scholarships or focus on schools with good institutional aid?",
            "How does CSS Profile differ from FAFSA and which schools require which?",
            "What are full-ride scholarship programs and how competitive are they?"
        ]
        
        for q in financial_questions:
            self.ask_model(q, 'financial_aid')
            time.sleep(1)
        
        # Category 8: Program-Specific (7 questions)
        program_questions = [
            "What are the best undergraduate business programs and how do their admissions differ?",
            "Compare engineering programs at MIT, Stanford, Caltech, and Carnegie Mellon. What makes each unique?",
            "What should I know about applying to direct-admit nursing programs?",
            "How competitive are BS/MD programs and what do they look for in applicants?",
            "What are the differences between liberal arts colleges and research universities for pre-med students?",
            "Which schools have the best undergraduate research opportunities in biology?",
            "What are the top programs for international relations and how do I prepare for them?"
        ]
        
        for q in program_questions:
            self.ask_model(q, 'program_specific')
            time.sleep(1)
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80)
        
    def generate_report(self):
        """Generate comprehensive test report"""
        
        print("\n" + "="*80)
        print("📊 EXTENSIVE MODEL QUALITY TEST REPORT")
        print("="*80)
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r['status'] == 'success'])
        failed_tests = total_tests - successful_tests
        
        avg_response_time = sum(r['response_time'] for r in self.results) / total_tests
        avg_quality_score = sum(r['quality_score'] for r in self.results if r['status'] == 'success') / successful_tests if successful_tests > 0 else 0
        avg_answer_length = sum(r.get('answer_length', 0) for r in self.results if r['status'] == 'success') / successful_tests if successful_tests > 0 else 0
        
        print(f"\n📈 OVERALL STATISTICS")
        print(f"{'='*80}")
        print(f"Total Questions Asked:        {total_tests}")
        print(f"Successful Responses:         {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"Failed Responses:             {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print(f"Average Response Time:        {avg_response_time:.2f} seconds")
        print(f"Average Quality Score:        {avg_quality_score:.2f}/10")
        print(f"Average Answer Length:        {avg_answer_length:.0f} characters")
        
        print(f"\n📊 CATEGORY BREAKDOWN")
        print(f"{'='*80}")
        
        for category, results in self.categories.items():
            if results:
                cat_success = len([r for r in results if r['status'] == 'success'])
                cat_avg_quality = sum(r['quality_score'] for r in results if r['status'] == 'success') / cat_success if cat_success > 0 else 0
                cat_avg_time = sum(r['response_time'] for r in results) / len(results)
                
                print(f"\n{category.upper().replace('_', ' ')}")
                print(f"  Questions:        {len(results)}")
                print(f"  Success Rate:     {cat_success/len(results)*100:.1f}%")
                print(f"  Avg Quality:      {cat_avg_quality:.2f}/10")
                print(f"  Avg Time:         {cat_avg_time:.2f}s")
        
        # Quality distribution
        print(f"\n📊 QUALITY SCORE DISTRIBUTION")
        print(f"{'='*80}")
        
        quality_ranges = {
            '9-10 (Excellent)': 0,
            '7-8.9 (Good)': 0,
            '5-6.9 (Fair)': 0,
            '3-4.9 (Poor)': 0,
            '0-2.9 (Very Poor)': 0
        }
        
        for result in self.results:
            if result['status'] == 'success':
                score = result['quality_score']
                if score >= 9:
                    quality_ranges['9-10 (Excellent)'] += 1
                elif score >= 7:
                    quality_ranges['7-8.9 (Good)'] += 1
                elif score >= 5:
                    quality_ranges['5-6.9 (Fair)'] += 1
                elif score >= 3:
                    quality_ranges['3-4.9 (Poor)'] += 1
                else:
                    quality_ranges['0-2.9 (Very Poor)'] += 1
        
        for range_name, count in quality_ranges.items():
            percentage = (count / successful_tests * 100) if successful_tests > 0 else 0
            bar = '█' * int(percentage / 2)
            print(f"{range_name:20} {count:3d} ({percentage:5.1f}%) {bar}")
        
        # Response time distribution
        print(f"\n⏱️  RESPONSE TIME DISTRIBUTION")
        print(f"{'='*80}")
        
        time_ranges = {
            '0-1s (Very Fast)': 0,
            '1-2s (Fast)': 0,
            '2-5s (Normal)': 0,
            '5-10s (Slow)': 0,
            '10s+ (Very Slow)': 0
        }
        
        for result in self.results:
            time_val = result['response_time']
            if time_val < 1:
                time_ranges['0-1s (Very Fast)'] += 1
            elif time_val < 2:
                time_ranges['1-2s (Fast)'] += 1
            elif time_val < 5:
                time_ranges['2-5s (Normal)'] += 1
            elif time_val < 10:
                time_ranges['5-10s (Slow)'] += 1
            else:
                time_ranges['10s+ (Very Slow)'] += 1
        
        for range_name, count in time_ranges.items():
            percentage = (count / total_tests * 100)
            bar = '█' * int(percentage / 2)
            print(f"{range_name:20} {count:3d} ({percentage:5.1f}%) {bar}")
        
        # Best and worst responses
        print(f"\n🏆 TOP 5 HIGHEST QUALITY RESPONSES")
        print(f"{'='*80}")
        
        sorted_by_quality = sorted([r for r in self.results if r['status'] == 'success'], 
                                   key=lambda x: x['quality_score'], reverse=True)[:5]
        
        for i, result in enumerate(sorted_by_quality, 1):
            print(f"\n{i}. Quality: {result['quality_score']:.1f}/10 | Category: {result['category']}")
            print(f"   Q: {result['question'][:80]}...")
            print(f"   A: {result['answer'][:150]}...")
        
        print(f"\n⚠️  BOTTOM 5 LOWEST QUALITY RESPONSES")
        print(f"{'='*80}")
        
        sorted_by_quality_low = sorted([r for r in self.results if r['status'] == 'success'], 
                                       key=lambda x: x['quality_score'])[:5]
        
        for i, result in enumerate(sorted_by_quality_low, 1):
            print(f"\n{i}. Quality: {result['quality_score']:.1f}/10 | Category: {result['category']}")
            print(f"   Q: {result['question'][:80]}...")
            print(f"   A: {result['answer'][:150]}...")
        
        # Final verdict
        print(f"\n{'='*80}")
        print(f"🎯 FINAL VERDICT")
        print(f"{'='*80}")
        
        if avg_quality_score >= 8:
            verdict = "✅ EXCELLENT - Production ready with high quality responses"
        elif avg_quality_score >= 6:
            verdict = "✅ GOOD - Production ready with acceptable quality"
        elif avg_quality_score >= 4:
            verdict = "⚠️  FAIR - May need improvement before production"
        else:
            verdict = "❌ POOR - Needs significant improvement"
        
        print(f"\nOverall Quality: {avg_quality_score:.2f}/10")
        print(f"Verdict: {verdict}")
        print(f"\nSuccess Rate: {successful_tests/total_tests*100:.1f}%")
        print(f"Average Response Time: {avg_response_time:.2f}s")
        
        if successful_tests/total_tests >= 0.95 and avg_quality_score >= 6:
            print(f"\n🎉 MODEL PASSES EXTENSIVE QUALITY TESTING!")
        else:
            print(f"\n⚠️  MODEL NEEDS IMPROVEMENT")
        
        print(f"\n{'='*80}")
        
        # Save detailed results to JSON
        with open('extensive_test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'failed_tests': failed_tests,
                    'success_rate': successful_tests/total_tests*100,
                    'avg_response_time': avg_response_time,
                    'avg_quality_score': avg_quality_score,
                    'avg_answer_length': avg_answer_length,
                    'verdict': verdict
                },
                'category_breakdown': {
                    cat: {
                        'count': len(results),
                        'success_rate': len([r for r in results if r['status'] == 'success'])/len(results)*100,
                        'avg_quality': sum(r['quality_score'] for r in results if r['status'] == 'success') / len([r for r in results if r['status'] == 'success']) if len([r for r in results if r['status'] == 'success']) > 0 else 0,
                        'avg_time': sum(r['response_time'] for r in results) / len(results)
                    }
                    for cat, results in self.categories.items() if results
                },
                'all_results': self.results
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: extensive_test_results.json")
        print(f"{'='*80}\n")

def main():
    print("\n" + "="*80)
    print("🧪 EXTENSIVE MODEL QUALITY TESTING SUITE")
    print("="*80)
    print("\nThis will test the model with 80 complex questions across 8 categories:")
    print("  1. Essay Writing (15 questions)")
    print("  2. Admission Analysis (15 questions)")
    print("  3. Data-Driven Questions (10 questions)")
    print("  4. Personalized Advice (10 questions)")
    print("  5. Trends Analysis (8 questions)")
    print("  6. Strategic Planning (8 questions)")
    print("  7. Financial Aid (7 questions)")
    print("  8. Program-Specific (7 questions)")
    print("\nEstimated time: 15-20 minutes")
    print("="*80)
    
    input("\nPress Enter to start testing...")
    
    tester = ExtensiveModelTester()
    
    start_time = time.time()
    tester.run_all_tests()
    total_time = time.time() - start_time
    
    print(f"\n⏱️  Total testing time: {total_time/60:.1f} minutes")
    
    tester.generate_report()

if __name__ == "__main__":
    main()

