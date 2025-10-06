#!/usr/bin/env python3
"""
🧪 ADVANCED MODEL TESTING & VALIDATION SCRIPT
==============================================

Comprehensive testing suite for the fine-tuned CollegeAdvisor model.
Tests for accuracy, response quality, and production readiness.

Features:
- ✅ Comprehensive accuracy testing
- ✅ Response quality analysis
- ✅ Benchmark comparisons
- ✅ Production readiness validation
- ✅ Performance metrics
- ✅ Detailed reporting
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("=" * 80)
print("🧪 ADVANCED MODEL TESTING & VALIDATION")
print("=" * 80)


class ModelTester:
    """Comprehensive model testing and validation."""
    
    def __init__(self, model_dir: str = "collegeadvisor_model_advanced"):
        self.model_dir = Path(model_dir)
        self.model = None
        self.tokenizer = None
        self.device = self._detect_device()
        self.test_results = {}
        
    def _detect_device(self) -> str:
        """Detect the best available device."""
        try:
            import torch
            
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        except ImportError:
            return "cpu"
    
    def load_model(self) -> bool:
        """Load the fine-tuned model."""
        print("\n🤖 LOADING MODEL")
        print("-" * 40)
        
        if not self.model_dir.exists():
            print(f"❌ Model directory not found: {self.model_dir}")
            return False
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            print(f"📁 Model directory: {self.model_dir}")
            print(f"🖥️  Device: {self.device}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
            print("✅ Tokenizer loaded")
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_dir,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                device_map="auto" if self.device != "mps" else None,
        low_cpu_mem_usage=True
    )
    
            # Move to device if needed
            if self.device == "mps":
                self.model = self.model.to(self.device)
            
            print("✅ Model loaded successfully")
            return True
            
except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def create_test_dataset(self) -> List[Dict[str, str]]:
        """Create comprehensive test dataset."""
        return [
            # Basic factual questions
            {
                "question": "What is the admission rate at Stanford University?",
                "expected_keywords": ["stanford", "admission", "rate", "%"],
                "category": "factual"
            },
            {
                "question": "How much does it cost to attend MIT?",
                "expected_keywords": ["mit", "tuition", "cost", "$"],
                "category": "factual"
            },
            {
                "question": "What are the requirements for UC Berkeley?",
                "expected_keywords": ["berkeley", "requirements", "gpa", "sat"],
                "category": "requirements"
            },
            
            # Program-specific questions
            {
                "question": "Tell me about Harvard's computer science program.",
                "expected_keywords": ["harvard", "computer science", "program"],
                "category": "programs"
            },
            {
                "question": "What engineering programs does Carnegie Mellon offer?",
                "expected_keywords": ["carnegie mellon", "engineering", "programs"],
                "category": "programs"
            },
            {
                "question": "Which universities have the best business schools?",
                "expected_keywords": ["business", "schools", "universities"],
                "category": "rankings"
            },
            
            # Comparative questions
            {
                "question": "Compare Harvard and Yale universities.",
                "expected_keywords": ["harvard", "yale", "compare"],
                "category": "comparison"
            },
            {
                "question": "What's the difference between public and private universities?",
                "expected_keywords": ["public", "private", "universities", "difference"],
                "category": "comparison"
            },
            
            # Advice questions
            {
                "question": "What should I study to prepare for medical school?",
                "expected_keywords": ["medical school", "study", "prepare"],
                "category": "advice"
            },
            {
                "question": "How can I improve my chances of getting into a top university?",
                "expected_keywords": ["improve", "chances", "university"],
                "category": "advice"
            },
            
            # Complex questions
            {
                "question": "I have a 3.7 GPA and want to study computer science in California. What are my options?",
                "expected_keywords": ["3.7", "gpa", "computer science", "california"],
                "category": "personalized"
            },
            {
                "question": "What are some affordable universities with good engineering programs?",
                "expected_keywords": ["affordable", "universities", "engineering"],
                "category": "personalized"
            },
            
            # Edge cases
            {
                "question": "What is the capital of France?",
                "expected_keywords": [],  # Should decline to answer
                "category": "out_of_scope"
            },
            {
                "question": "Tell me about quantum physics.",
                "expected_keywords": [],  # Should decline to answer
                "category": "out_of_scope"
            }
        ]
    
    def generate_response(self, question: str, max_tokens: int = 200) -> Tuple[str, float]:
        """Generate response and measure response time."""
        try:
            import torch
            
            # Format as chat
            messages = [{"role": "user", "content": question}]
            
            # Apply chat template if available
            if hasattr(self.tokenizer, 'apply_chat_template'):
                prompt = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            else:
                prompt = f"User: {question}\nAssistant:"
            
            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=1024
            )
            
            # Move to device
            if self.device != "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate
            start_time = time.time()
    
    with torch.no_grad():
                outputs = self.model.generate(
            **inputs,
                    max_new_tokens=max_tokens,
                    temperature=0.7,
            do_sample=True,
            top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            response_time = time.time() - start_time
            
            # Decode response
            response = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            ).strip()
            
            return response, response_time
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error: {e}", 0.0
    
    def evaluate_response_quality(self, question: str, response: str, expected_keywords: List[str], category: str) -> Dict[str, Any]:
        """Evaluate the quality of a response."""
        metrics = {
            "length": len(response),
            "word_count": len(response.split()),
            "keyword_score": 0.0,
            "relevance_score": 0.0,
            "quality_score": 0.0,
            "issues": []
        }
        
        # Check for basic issues
        if len(response) < 20:
            metrics["issues"].append("Too short")
        
        if "I don't know" in response.lower() or "I'm not sure" in response.lower():
            if category != "out_of_scope":
                metrics["issues"].append("Claims ignorance inappropriately")
        
        if "error" in response.lower():
            metrics["issues"].append("Contains error message")
        
        # Keyword matching
        if expected_keywords:
            response_lower = response.lower()
            matched_keywords = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
            metrics["keyword_score"] = matched_keywords / len(expected_keywords)
        else:
            # For out-of-scope questions, check if it appropriately declines
            if category == "out_of_scope":
                decline_phrases = ["college", "university", "can't help", "not my expertise"]
                if any(phrase in response.lower() for phrase in decline_phrases):
                    metrics["keyword_score"] = 1.0
                else:
                    metrics["keyword_score"] = 0.0
        
        # Relevance score (simple heuristic)
        question_words = set(question.lower().split())
        response_words = set(response.lower().split())
        common_words = question_words.intersection(response_words)
        metrics["relevance_score"] = len(common_words) / len(question_words) if question_words else 0.0
        
        # Overall quality score
        metrics["quality_score"] = (
            metrics["keyword_score"] * 0.4 +
            metrics["relevance_score"] * 0.3 +
            (1.0 if not metrics["issues"] else 0.5) * 0.3
        )
        
        return metrics
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        print("\n🧪 RUNNING COMPREHENSIVE TESTS")
        print("-" * 40)
        
        test_dataset = self.create_test_dataset()
        results = {
            "total_tests": len(test_dataset),
            "passed_tests": 0,
            "failed_tests": 0,
            "response_times": [],
            "quality_scores": [],
            "category_scores": {},
            "detailed_results": []
        }
        
        print(f"📊 Running {len(test_dataset)} test cases...")
        
        for i, test_case in enumerate(test_dataset, 1):
            print(f"\n📝 Test {i}/{len(test_dataset)}: {test_case['category'].upper()}")
            print(f"❓ Question: {test_case['question']}")
            
            # Generate response
            response, response_time = self.generate_response(test_case['question'])
            results["response_times"].append(response_time)
            
            print(f"🤖 Response: {response[:100]}{'...' if len(response) > 100 else ''}")
            print(f"⏱️  Response time: {response_time:.2f}s")
            
            # Evaluate quality
            quality_metrics = self.evaluate_response_quality(
                test_case['question'],
                response,
                test_case['expected_keywords'],
                test_case['category']
            )
            
            results["quality_scores"].append(quality_metrics["quality_score"])
            
            # Category tracking
            category = test_case['category']
            if category not in results["category_scores"]:
                results["category_scores"][category] = []
            results["category_scores"][category].append(quality_metrics["quality_score"])
            
            # Pass/fail determination
            passed = quality_metrics["quality_score"] >= 0.6 and not quality_metrics["issues"]
            if passed:
                results["passed_tests"] += 1
                print("✅ PASSED")
    else:
                results["failed_tests"] += 1
                print(f"❌ FAILED: {', '.join(quality_metrics['issues']) if quality_metrics['issues'] else 'Low quality score'}")
            
            # Store detailed results
            results["detailed_results"].append({
                "question": test_case['question'],
                "response": response,
                "category": category,
                "response_time": response_time,
                "quality_metrics": quality_metrics,
                "passed": passed
            })
        
        return results
    
    def calculate_final_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final performance metrics."""
        metrics = {
            "accuracy": results["passed_tests"] / results["total_tests"],
            "avg_response_time": statistics.mean(results["response_times"]),
            "avg_quality_score": statistics.mean(results["quality_scores"]),
            "response_time_std": statistics.stdev(results["response_times"]) if len(results["response_times"]) > 1 else 0,
            "category_performance": {}
        }
        
        # Category performance
        for category, scores in results["category_scores"].items():
            metrics["category_performance"][category] = {
                "avg_score": statistics.mean(scores),
                "count": len(scores),
                "pass_rate": sum(1 for score in scores if score >= 0.6) / len(scores)
            }
        
        return metrics
    
    def generate_report(self, results: Dict[str, Any], metrics: Dict[str, Any]) -> None:
        """Generate detailed test report."""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        # Overall metrics
        print(f"\n🎯 OVERALL PERFORMANCE")
        print(f"   Accuracy: {metrics['accuracy']:.1%}")
        print(f"   Quality Score: {metrics['avg_quality_score']:.3f}")
        print(f"   Tests Passed: {results['passed_tests']}/{results['total_tests']}")
        print(f"   Average Response Time: {metrics['avg_response_time']:.2f}s")
        
        # Target achievement
        target_accuracy = 0.95
        if metrics['accuracy'] >= target_accuracy:
            print(f"✅ TARGET ACHIEVED: {metrics['accuracy']:.1%} >= {target_accuracy:.1%}")
    else:
            print(f"❌ TARGET MISSED: {metrics['accuracy']:.1%} < {target_accuracy:.1%}")
        
        # Category breakdown
        print(f"\n📋 CATEGORY PERFORMANCE")
        for category, perf in metrics["category_performance"].items():
            print(f"   {category.upper()}: {perf['avg_score']:.3f} ({perf['pass_rate']:.1%} pass rate)")
        
        # Performance analysis
        print(f"\n⚡ PERFORMANCE ANALYSIS")
        if metrics['avg_response_time'] < 2.0:
            print("✅ Response time: Excellent (< 2s)")
        elif metrics['avg_response_time'] < 5.0:
            print("✅ Response time: Good (< 5s)")
        else:
            print("⚠️  Response time: Could be improved (> 5s)")
        
        # Quality analysis
        if metrics['avg_quality_score'] >= 0.8:
            print("✅ Response quality: Excellent")
        elif metrics['avg_quality_score'] >= 0.6:
            print("✅ Response quality: Good")
    else:
            print("⚠️  Response quality: Needs improvement")
        
        # Failed tests analysis
        if results["failed_tests"] > 0:
            print(f"\n❌ FAILED TESTS ANALYSIS")
            failed_tests = [r for r in results["detailed_results"] if not r["passed"]]
            
            for test in failed_tests[:3]:  # Show first 3 failures
                print(f"   Question: {test['question']}")
                print(f"   Issues: {', '.join(test['quality_metrics']['issues'])}")
                print(f"   Quality Score: {test['quality_metrics']['quality_score']:.3f}")
print()

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        
        if metrics['accuracy'] < 0.9:
            print("   • Consider additional training epochs")
            print("   • Review training data quality")
            print("   • Adjust learning rate or LoRA parameters")
        
        if metrics['avg_response_time'] > 3.0:
            print("   • Consider model quantization for faster inference")
            print("   • Optimize generation parameters")
        
        low_performing_categories = [
            cat for cat, perf in metrics["category_performance"].items()
            if perf['avg_score'] < 0.7
        ]
        
        if low_performing_categories:
            print(f"   • Focus on improving: {', '.join(low_performing_categories)}")
        
        # Production readiness
        print(f"\n🚀 PRODUCTION READINESS")
        
        production_ready = (
            metrics['accuracy'] >= 0.85 and
            metrics['avg_quality_score'] >= 0.7 and
            metrics['avg_response_time'] <= 5.0
        )
        
        if production_ready:
            print("✅ Model is PRODUCTION READY!")
            print("   • High accuracy and quality scores")
            print("   • Acceptable response times")
            print("   • Ready for deployment")
        else:
            print("⚠️  Model needs improvement before production")
            print("   • Review failed tests and recommendations")
            print("   • Consider additional training")
        
        print("\n" + "=" * 80)
    
    def save_results(self, results: Dict[str, Any], metrics: Dict[str, Any]) -> None:
        """Save test results to file."""
        report_data = {
            "test_date": datetime.now().isoformat(),
            "model_dir": str(self.model_dir),
            "device": self.device,
            "results": results,
            "metrics": metrics
        }
        
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"📄 Detailed report saved to: {report_file}")
    
    def run_full_validation(self) -> bool:
        """Run the complete validation suite."""
        print("🚀 STARTING FULL MODEL VALIDATION")
        print("=" * 80)
        
        # Load model
        if not self.load_model():
            return False
        
        # Run tests
        results = self.run_comprehensive_tests()
        
        # Calculate metrics
        metrics = self.calculate_final_metrics(results)
        
        # Generate report
        self.generate_report(results, metrics)
        
        # Save results
        self.save_results(results, metrics)
        
        # Return success based on target achievement
        return metrics['accuracy'] >= 0.85  # Minimum production threshold


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test fine-tuned CollegeAdvisor model")
    parser.add_argument(
        "--model-dir",
        default="collegeadvisor_model_advanced",
        help="Path to the fine-tuned model directory"
    )
    
    args = parser.parse_args()
    
    try:
        tester = ModelTester(args.model_dir)
        success = tester.run_full_validation()
        
        if success:
            print("\n🎉 MODEL VALIDATION SUCCESSFUL!")
            print("Your CollegeAdvisor model is ready for production!")
        else:
            print("\n⚠️  MODEL NEEDS IMPROVEMENT")
            print("Review the test report and consider additional training.")
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)