#!/usr/bin/env python3
"""
Comprehensive model inference and testing script.
Tests the trained CollegeAdvisor model with real queries.

ZERO TOLERANCE for errors - all imports validated, all errors caught.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ dotenv loaded")
except ImportError:
    logger.warning("⚠️  dotenv not available")

# Validate critical imports
try:
    import torch
    logger.info("✅ torch imported successfully")
except ImportError as e:
    logger.error(f"❌ CRITICAL: Failed to import torch: {e}")
    sys.exit(1)

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    logger.info("✅ transformers imported successfully")
except ImportError as e:
    logger.error(f"❌ CRITICAL: Failed to import transformers: {e}")
    sys.exit(1)

try:
    from peft import PeftModel, PeftConfig
    logger.info("✅ peft imported successfully")
except ImportError as e:
    logger.error(f"❌ CRITICAL: Failed to import peft: {e}")
    sys.exit(1)


class ModelInferenceTester:
    """Comprehensive model testing with zero tolerance for errors."""
    
    def __init__(self, model_path: str = "collegeadvisor_unified_model"):
        """Initialize the inference tester."""
        self.model_path = Path(model_path)
        self.model = None
        self.tokenizer = None
        self.device = self._get_device()
        self.test_results = []
        
        logger.info(f"🔧 Initializing ModelInferenceTester")
        logger.info(f"   Model path: {self.model_path}")
        logger.info(f"   Device: {self.device}")
        
        # Validate model path exists
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model path does not exist: {self.model_path}")
        
        # Validate required files exist
        required_files = [
            "adapter_config.json",
            "adapter_model.safetensors",
            "tokenizer_config.json"
        ]
        
        for file in required_files:
            file_path = self.model_path / file
            if not file_path.exists():
                raise FileNotFoundError(f"Required file missing: {file_path}")
        
        logger.info("✅ All required model files present")
    
    def _get_device(self) -> str:
        """Get the best available device."""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def load_model(self):
        """Load the fine-tuned model with comprehensive error handling."""
        logger.info("="*80)
        logger.info("LOADING MODEL")
        logger.info("="*80)
        
        try:
            # Load adapter config to get base model name
            logger.info("📂 Loading adapter config...")
            with open(self.model_path / "adapter_config.json", 'r') as f:
                adapter_config = json.load(f)
            
            base_model_name = adapter_config.get("base_model_name_or_path")
            if not base_model_name:
                raise ValueError("base_model_name_or_path not found in adapter_config.json")
            
            logger.info(f"✅ Base model: {base_model_name}")
            
            # Load tokenizer
            logger.info("📂 Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                trust_remote_code=True
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info("✅ Tokenizer loaded")
            
            # Load base model
            logger.info(f"📂 Loading base model: {base_model_name}...")
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )
            
            logger.info("✅ Base model loaded")
            
            # Load LoRA adapters
            logger.info("📂 Loading LoRA adapters...")
            self.model = PeftModel.from_pretrained(
                base_model,
                str(self.model_path)
            )
            
            # Move to device if not using device_map
            if self.device != "cuda":
                self.model = self.model.to(self.device)
            
            self.model.eval()
            
            logger.info("✅ LoRA adapters loaded")
            logger.info("="*80)
            logger.info("✅ MODEL LOADED SUCCESSFULLY")
            logger.info("="*80)
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR loading model: {e}")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error details: {str(e)}")
            raise
    
    def generate_response(
        self,
        query: str,
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True
    ) -> Dict[str, Any]:
        """Generate a response for a given query."""
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # Format the prompt (TinyLlama chat format)
            prompt = f"<|user|>\n{query}</s>\n<|assistant|>\n"
            
            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=do_sample,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract just the assistant's response
            if "<|assistant|>" in full_response:
                response = full_response.split("<|assistant|>")[-1].strip()
            else:
                response = full_response.replace(prompt, "").strip()
            
            # Calculate metrics
            response_length = len(response)
            word_count = len(response.split())
            
            return {
                "query": query,
                "response": response,
                "response_length_chars": response_length,
                "response_length_words": word_count,
                "prompt": prompt,
                "full_output": full_response,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            return {
                "query": query,
                "response": None,
                "response_length_chars": 0,
                "response_length_words": 0,
                "prompt": None,
                "full_output": None,
                "success": False,
                "error": str(e)
            }
    
    def run_test_suite(self, test_queries: List[str]) -> List[Dict[str, Any]]:
        """Run comprehensive test suite."""
        logger.info("="*80)
        logger.info(f"RUNNING TEST SUITE ({len(test_queries)} queries)")
        logger.info("="*80)
        
        results = []
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"TEST {i}/{len(test_queries)}")
            logger.info(f"{'='*80}")
            logger.info(f"Query: {query}")
            logger.info("-"*80)
            
            result = self.generate_response(query)
            
            if result["success"]:
                logger.info(f"✅ Response generated:")
                logger.info(f"   Length: {result['response_length_chars']} chars, {result['response_length_words']} words")
                logger.info(f"   Response: {result['response'][:200]}...")
            else:
                logger.error(f"❌ Failed: {result['error']}")
            
            results.append(result)
        
        self.test_results = results
        return results
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze test results and generate statistics."""
        if not self.test_results:
            logger.warning("No test results to analyze")
            return {}
        
        logger.info("\n" + "="*80)
        logger.info("ANALYZING RESULTS")
        logger.info("="*80)
        
        successful = [r for r in self.test_results if r["success"]]
        failed = [r for r in self.test_results if not r["success"]]
        
        if successful:
            char_lengths = [r["response_length_chars"] for r in successful]
            word_lengths = [r["response_length_words"] for r in successful]
            
            avg_chars = sum(char_lengths) / len(char_lengths)
            avg_words = sum(word_lengths) / len(word_lengths)
            min_chars = min(char_lengths)
            max_chars = max(char_lengths)
            min_words = min(word_lengths)
            max_words = max(word_lengths)
        else:
            avg_chars = avg_words = min_chars = max_chars = min_words = max_words = 0
        
        analysis = {
            "total_tests": len(self.test_results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.test_results) * 100,
            "avg_response_chars": avg_chars,
            "avg_response_words": avg_words,
            "min_response_chars": min_chars,
            "max_response_chars": max_chars,
            "min_response_words": min_words,
            "max_response_words": max_words
        }
        
        logger.info(f"📊 Total tests: {analysis['total_tests']}")
        logger.info(f"✅ Successful: {analysis['successful']}")
        logger.info(f"❌ Failed: {analysis['failed']}")
        logger.info(f"📈 Success rate: {analysis['success_rate']:.1f}%")
        logger.info(f"📏 Avg response: {analysis['avg_response_chars']:.0f} chars, {analysis['avg_response_words']:.0f} words")
        logger.info(f"📏 Range: {analysis['min_response_chars']}-{analysis['max_response_chars']} chars")
        
        return analysis
    
    def save_results(self, output_file: str = "model_test_results.json"):
        """Save test results to file."""
        output_path = Path(output_file)
        
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "model_path": str(self.model_path),
            "device": self.device,
            "test_results": self.test_results,
            "analysis": self.analyze_results()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to: {output_path}")
        return output_path


def get_comprehensive_test_queries() -> List[str]:
    """Get comprehensive list of test queries covering different scenarios."""
    return [
        # Basic factual queries
        "What is Cornell's acceptance rate?",
        "How many students attend MIT?",
        "What is the average SAT score for Harvard?",
        
        # Comparison queries
        "Compare Cornell and MIT for engineering",
        "Which is better for computer science: Stanford or Berkeley?",
        
        # Advisory queries (should require detailed responses)
        "How do I improve my Common App essay on adversity?",
        "What extracurriculars should I do for Ivy League admissions?",
        "How can I demonstrate leadership in my college application?",
        
        # Specific program queries
        "Tell me about Cornell's engineering program",
        "What makes MIT's computer science program unique?",
        
        # Admissions strategy
        "What are my chances of getting into Cornell with a 3.8 GPA?",
        "Should I apply Early Decision or Regular Decision?",
        
        # Essay and application help
        "How do I write a compelling Why Cornell essay?",
        "What should I include in my activities list?",
        
        # Financial aid
        "How much does Cornell cost per year?",
        "What financial aid does MIT offer?",
    ]


def main():
    """Main execution function."""
    logger.info("="*80)
    logger.info("COMPREHENSIVE MODEL INFERENCE TEST")
    logger.info("="*80)
    
    try:
        # Initialize tester
        tester = ModelInferenceTester()
        
        # Load model
        tester.load_model()
        
        # Get test queries
        test_queries = get_comprehensive_test_queries()
        
        # Run tests
        results = tester.run_test_suite(test_queries)
        
        # Analyze and save
        analysis = tester.analyze_results()
        output_file = tester.save_results()
        
        logger.info("\n" + "="*80)
        logger.info("✅ TESTING COMPLETE")
        logger.info("="*80)
        logger.info(f"Results saved to: {output_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        import traceback
        logger.error(f"   Traceback:\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

