#!/usr/bin/env python3
"""
🧪 ADVANCED MODEL TESTING SCRIPT
Comprehensive testing for the fine-tuned CollegeAdvisor model

Features:
- Comprehensive quality assessment
- Performance benchmarking
- Production readiness validation
- Detailed reporting
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 100)
print("🧪 ADVANCED MODEL TESTING & VALIDATION")
print("=" * 100)
print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 100)
print()

# Test configuration
class TestConfig:
    def __init__(self):
        self.model_path = "collegeadvisor_bulletproof_model"  # Match training script
        self.max_new_tokens = 200
        self.temperature = 0.7
        self.top_p = 0.9
        self.repetition_penalty = 1.1
        
        # Quality thresholds
        self.min_length = 20
        self.max_length = 500
        self.quality_threshold = 75
        self.accuracy_threshold = 96  # Match 96%+ target

config = TestConfig()

def load_model():
    """Load the fine-tuned model"""
    logger.info(f"🤖 Loading model from {config.model_path}...")
    
    try:
        from unsloth import FastLanguageModel
        
        # Load the fine-tuned model
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=config.model_path,
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
        )
        
        # Enable inference mode
        FastLanguageModel.for_inference(model)
        
        logger.info("✅ Model loaded successfully")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"❌ Error loading model: {e}")
        raise

def create_test_suite():
    """Create comprehensive test suite"""
    logger.info("📝 Creating comprehensive test suite...")
    
    test_suite = {
        "basic_knowledge": [
            "What is the admission rate at Stanford University?",
            "How much does tuition cost at Harvard University?",
            "What are the most popular majors at MIT?",
            "What GPA do I need for UC Berkeley?",
            "When are college application deadlines?",
        ],
        
        "detailed_guidance": [
            "How do I write a compelling college application essay?",
            "What extracurricular activities should I focus on for college applications?",
            "How do I prepare for the SAT exam?",
            "What should I look for when choosing a college major?",
            "How can I get financial aid for college?",
        ],
        
        "comparative_analysis": [
            "Compare the computer science programs at Stanford and MIT.",
            "What are the differences between public and private universities?",
            "Which Ivy League schools have the best pre-med programs?",
            "Compare the costs of attending college in California vs New York.",
            "What are the best colleges for engineering on the East Coast?",
        ],
        
        "specific_scenarios": [
            "I have a 3.5 GPA and want to study business. What colleges should I consider?",
            "I'm interested in environmental science and need financial aid. Any recommendations?",
            "What colleges offer good programs for first-generation college students?",
            "I want to study abroad during college. Which universities have the best programs?",
            "I'm a transfer student looking for good computer science programs. Any suggestions?",
        ],
        
        "edge_cases": [
            "What should I do if I'm waitlisted at my dream school?",
            "How do I handle college rejection letters?",
            "Can I change my major after starting college?",
            "What if I can't afford my first-choice college?",
            "How do I decide between multiple college acceptances?",
        ]
    }
    
    total_questions = sum(len(questions) for questions in test_suite.values())
    logger.info(f"✅ Created test suite with {total_questions} questions across {len(test_suite)} categories")
    
    return test_suite

def evaluate_response_quality(question: str, response: str) -> Dict[str, Any]:
    """Evaluate response quality with multiple metrics"""
    
    # Basic metrics
    word_count = len(response.split())
    char_count = len(response)
    
    # Quality scoring
    quality_score = 0
    quality_details = {}
    
    # Length check (20 points)
    if config.min_length <= char_count <= config.max_length:
        quality_score += 20
        quality_details['length'] = 'appropriate'
    else:
        quality_details['length'] = 'too_short' if char_count < config.min_length else 'too_long'
    
    # Relevance check (25 points)
    question_words = set(question.lower().split())
    response_words = set(response.lower().split())
    
    # Check for college-related terms
    college_terms = {'college', 'university', 'student', 'admission', 'tuition', 'degree', 'program', 'campus', 'academic'}
    if college_terms.intersection(response_words):
        quality_score += 15
        quality_details['domain_relevance'] = 'good'
    else:
        quality_details['domain_relevance'] = 'poor'
    
    # Check for question relevance
    if len(question_words.intersection(response_words)) >= 2:
        quality_score += 10
        quality_details['question_relevance'] = 'good'
    else:
        quality_details['question_relevance'] = 'poor'
    
    # Coherence check (20 points)
    sentences = response.split('.')
    if len(sentences) >= 2 and all(len(s.strip()) > 5 for s in sentences[:3]):
        quality_score += 20
        quality_details['coherence'] = 'good'
    else:
        quality_details['coherence'] = 'poor'
    
    # Informativeness check (20 points)
    if word_count >= 15:
        quality_score += 10
        quality_details['informativeness'] = 'good'
    else:
        quality_details['informativeness'] = 'poor'
    
    # Specificity check (10 points)
    specific_terms = {'rate', 'cost', 'requirement', 'program', 'application', 'deadline', 'scholarship'}
    if specific_terms.intersection(response_words):
        quality_score += 10
        quality_details['specificity'] = 'good'
    else:
        quality_details['specificity'] = 'poor'
    
    # Professionalism check (5 points)
    if not any(word in response.lower() for word in ['um', 'uh', 'like', 'whatever']):
        quality_score += 5
        quality_details['professionalism'] = 'good'
    else:
        quality_details['professionalism'] = 'poor'
    
    return {
        'quality_score': quality_score,
        'word_count': word_count,
        'char_count': char_count,
        'quality_details': quality_details,
        'passed': quality_score >= config.quality_threshold
    }

def run_test_category(model, tokenizer, category_name: str, questions: List[str]) -> Dict[str, Any]:
    """Run tests for a specific category"""
    logger.info(f"🧪 Testing category: {category_name} ({len(questions)} questions)")
    
    results = []
    total_time = 0
    
    for i, question in enumerate(questions, 1):
        try:
            # Format prompt - CORRECT TinyLlama format
            prompt = f"""<|user|>
{question}</s>
<|assistant|>
"""
            
            # Generate response
            start_time = time.time()
            
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=config.max_new_tokens,
                    temperature=config.temperature,
                    top_p=config.top_p,
                    repetition_penalty=config.repetition_penalty,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    do_sample=True,
                )
            
            generation_time = time.time() - start_time
            total_time += generation_time
            
            # Decode response
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract answer - CORRECT format
            if "<|assistant|>" in response:
                answer = response.split("<|assistant|>")[-1].strip()
                if "</s>" in answer:
                    answer = answer.split("</s>")[0].strip()
            else:
                answer = response
            
            # Evaluate quality
            evaluation = evaluate_response_quality(question, answer)
            
            result = {
                'question': question,
                'answer': answer,
                'generation_time': generation_time,
                'evaluation': evaluation
            }
            
            results.append(result)
            
            status = "✅ PASS" if evaluation['passed'] else "❌ FAIL"
            logger.info(f"  {i}/{len(questions)}: {status} (Quality: {evaluation['quality_score']}%)")
            
        except Exception as e:
            logger.error(f"  {i}/{len(questions)}: ❌ ERROR - {e}")
            results.append({
                'question': question,
                'answer': f"Error: {e}",
                'generation_time': 0,
                'evaluation': {'quality_score': 0, 'passed': False, 'error': str(e)}
            })
    
    # Calculate category statistics
    passed_tests = sum(1 for r in results if r['evaluation']['passed'])
    avg_quality = sum(r['evaluation']['quality_score'] for r in results) / len(results)
    avg_time = total_time / len(results)
    
    category_result = {
        'category': category_name,
        'total_questions': len(questions),
        'passed_tests': passed_tests,
        'pass_rate': (passed_tests / len(questions)) * 100,
        'avg_quality_score': avg_quality,
        'avg_generation_time': avg_time,
        'results': results
    }
    
    logger.info(f"📊 {category_name}: {passed_tests}/{len(questions)} passed ({category_result['pass_rate']:.1f}%)")
    
    return category_result

def generate_report(test_results: Dict[str, Any]) -> str:
    """Generate comprehensive test report"""
    logger.info("📄 Generating comprehensive test report...")
    
    # Calculate overall statistics
    total_questions = sum(r['total_questions'] for r in test_results.values())
    total_passed = sum(r['passed_tests'] for r in test_results.values())
    overall_pass_rate = (total_passed / total_questions) * 100
    overall_avg_quality = sum(r['avg_quality_score'] for r in test_results.values()) / len(test_results)
    overall_avg_time = sum(r['avg_generation_time'] for r in test_results.values()) / len(test_results)
    
    # Create report
    report = f"""
# 🧪 ADVANCED MODEL TESTING REPORT
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Model:** {config.model_path}

## 📊 OVERALL RESULTS
- **Total Questions:** {total_questions}
- **Questions Passed:** {total_passed}
- **Overall Pass Rate:** {overall_pass_rate:.1f}%
- **Average Quality Score:** {overall_avg_quality:.1f}%
- **Average Generation Time:** {overall_avg_time:.3f}s

## 🎯 ACCURACY ASSESSMENT
"""
    
    if overall_pass_rate >= config.accuracy_threshold:
        report += f"✅ **TARGET ACHIEVED:** {overall_pass_rate:.1f}% ≥ {config.accuracy_threshold}% threshold\n"
        report += "🚀 **STATUS:** Model ready for production deployment\n\n"
    else:
        report += f"❌ **TARGET MISSED:** {overall_pass_rate:.1f}% < {config.accuracy_threshold}% threshold\n"
        report += "🔧 **STATUS:** Model needs additional training\n\n"
    
    # Category breakdown
    report += "## 📋 CATEGORY BREAKDOWN\n\n"
    
    for category, results in test_results.items():
        status = "✅" if results['pass_rate'] >= 80 else "⚠️" if results['pass_rate'] >= 60 else "❌"
        report += f"### {status} {category.replace('_', ' ').title()}\n"
        report += f"- **Pass Rate:** {results['pass_rate']:.1f}%\n"
        report += f"- **Quality Score:** {results['avg_quality_score']:.1f}%\n"
        report += f"- **Avg Time:** {results['avg_generation_time']:.3f}s\n\n"
    
    # Recommendations
    report += "## 💡 RECOMMENDATIONS\n\n"
    
    if overall_pass_rate >= config.accuracy_threshold:
        report += "✅ **Model Performance:** Excellent - ready for deployment\n"
        report += "🚀 **Next Steps:** Deploy to production environment\n"
        report += "📊 **Monitoring:** Set up performance monitoring in production\n"
    elif overall_pass_rate >= 80:
        report += "⚠️ **Model Performance:** Good but below target\n"
        report += "🔧 **Suggestions:** Fine-tune hyperparameters or add more training data\n"
        report += "🧪 **Testing:** Run additional validation tests\n"
    else:
        report += "❌ **Model Performance:** Needs significant improvement\n"
        report += "🔄 **Action Required:** Retrain with improved data and parameters\n"
        report += "📚 **Data:** Consider expanding training dataset\n"
    
    return report

def main():
    """Main testing function"""
    try:
        # Check if model exists
        if not Path(config.model_path).exists():
            logger.error(f"❌ Model not found at {config.model_path}")
            logger.error("Please run the training script first!")
            return False
        
        # Load model
        import torch
        model, tokenizer = load_model()
        
        # Create test suite
        test_suite = create_test_suite()
        
        # Run tests for each category
        test_results = {}
        
        for category_name, questions in test_suite.items():
            category_result = run_test_category(model, tokenizer, category_name, questions)
            test_results[category_name] = category_result
        
        # Generate and save report
        report = generate_report(test_results)
        
        # Save detailed results
        results_file = Path(config.model_path) / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'config': config.__dict__,
                'test_results': test_results,
                'overall_pass_rate': sum(r['passed_tests'] for r in test_results.values()) / sum(r['total_questions'] for r in test_results.values()) * 100
            }, f, indent=2)
        
        # Save report
        report_file = Path(config.model_path) / "test_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Print summary
        total_questions = sum(r['total_questions'] for r in test_results.values())
        total_passed = sum(r['passed_tests'] for r in test_results.values())
        overall_pass_rate = (total_passed / total_questions) * 100
        
        print("\n" + "=" * 100)
        print("📊 TESTING COMPLETED")
        print("=" * 100)
        print(f"🎯 Overall Accuracy: {overall_pass_rate:.1f}%")
        print(f"✅ Questions Passed: {total_passed}/{total_questions}")
        
        if overall_pass_rate >= config.accuracy_threshold:
            print("🎉 TARGET ACHIEVED: 95%+ accuracy!")
            print("🚀 Model ready for production!")
            success = True
        else:
            print(f"❌ Target missed: {overall_pass_rate:.1f}% < {config.accuracy_threshold}%")
            print("🔧 Model needs additional training")
            success = False
        
        print(f"📄 Detailed report: {report_file}")
        print("=" * 100)
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Testing failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

