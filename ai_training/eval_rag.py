"""
RAGAS evaluation for CollegeAdvisor RAG system.

This script evaluates the RAG system using RAGAS metrics:
- Faithfulness: How grounded the answer is in the retrieved context
- Answer Correctness: Semantic similarity to ground truth
- Hit@5: Whether correct answer appears in top 5 results
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import argparse

import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_correctness,
    context_precision,
    context_recall,
    answer_relevancy
)

# Import our components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from college_advisor_data.storage.chroma_client import ChromaDBClient
from college_advisor_data.embedding.factory import get_canonical_embedder

logger = logging.getLogger(__name__)


class RAGEvaluator:
    """
    RAGAS-based evaluation for CollegeAdvisor RAG system.
    
    This evaluator tests the complete RAG pipeline:
    1. Query ChromaDB for relevant context
    2. Generate answers using the model
    3. Evaluate using RAGAS metrics
    """
    
    def __init__(self, 
                 chroma_client: ChromaDBClient = None,
                 model_endpoint: str = "http://localhost:11434/api/generate"):
        """
        Initialize the RAG evaluator.
        
        Args:
            chroma_client: ChromaDB client for retrieval
            model_endpoint: Ollama model endpoint for generation
        """
        self.chroma_client = chroma_client or ChromaDBClient()
        self.model_endpoint = model_endpoint
        self.embedder = get_canonical_embedder()
        
        # RAGAS metrics
        self.metrics = [
            faithfulness,
            answer_correctness,
            context_precision,
            context_recall,
            answer_relevancy
        ]
    
    def load_evaluation_dataset(self, data_path: str) -> Dataset:
        """
        Load evaluation dataset with questions and ground truth answers.
        
        Args:
            data_path: Path to evaluation JSONL file
            
        Returns:
            Dataset: Evaluation dataset
        """
        logger.info(f"Loading evaluation dataset: {data_path}")
        
        data_file = Path(data_path)
        if not data_file.exists():
            raise FileNotFoundError(f"Evaluation data not found: {data_path}")
        
        eval_examples = []
        with open(data_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    example = json.loads(line.strip())
                    
                    # Validate required fields
                    required_fields = ['question', 'ground_truth', 'contexts']
                    if not all(field in example for field in required_fields):
                        logger.warning(f"Line {line_num}: Missing required fields")
                        continue
                    
                    eval_examples.append(example)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Line {line_num}: Invalid JSON - {e}")
                    continue
        
        if not eval_examples:
            raise ValueError("No valid evaluation examples found")
        
        logger.info(f"Loaded {len(eval_examples)} evaluation examples")
        return Dataset.from_list(eval_examples)
    
    def retrieve_context(self, 
                        question: str, 
                        n_results: int = 5,
                        filters: Dict[str, Any] = None) -> List[str]:
        """
        Retrieve relevant context for a question.
        
        Args:
            question: User question
            n_results: Number of results to retrieve
            filters: Metadata filters
            
        Returns:
            List[str]: Retrieved context documents
        """
        try:
            # Query ChromaDB
            results = self.chroma_client.query(
                query_text=question,
                n_results=n_results,
                where=filters,
                include=["documents", "metadatas", "distances"]
            )
            
            # Extract documents
            contexts = [result["document"] for result in results]
            return contexts
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def generate_answer(self, 
                       question: str, 
                       contexts: List[str],
                       model_name: str = "collegeadvisor-llama3") -> str:
        """
        Generate answer using the fine-tuned model.
        
        Args:
            question: User question
            contexts: Retrieved context documents
            model_name: Ollama model name
            
        Returns:
            str: Generated answer
        """
        try:
            import requests
            
            # Prepare context
            context_text = "\n\n".join(contexts[:3])  # Use top 3 contexts
            
            # Create prompt
            prompt = f"""Based on the following context about colleges and academic programs, please answer the question accurately and helpfully.

Context:
{context_text}

Question: {question}

Answer:"""
            
            # Call Ollama API
            response = requests.post(
                self.model_endpoint,
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_ctx": 2048
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Model API error: {response.status_code}")
                return "Error generating answer"
                
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "Error generating answer"
    
    def evaluate_rag_pipeline(self, 
                             eval_dataset: Dataset,
                             model_name: str = "collegeadvisor-llama3",
                             n_contexts: int = 5) -> Dict[str, Any]:
        """
        Evaluate the complete RAG pipeline using RAGAS.
        
        Args:
            eval_dataset: Evaluation dataset
            model_name: Ollama model name
            n_contexts: Number of contexts to retrieve
            
        Returns:
            Dict: Evaluation results
        """
        logger.info("Starting RAG pipeline evaluation...")
        
        # Prepare evaluation data
        questions = []
        ground_truths = []
        answers = []
        contexts = []
        
        for i, example in enumerate(eval_dataset):
            try:
                question = example["question"]
                ground_truth = example["ground_truth"]
                
                logger.info(f"Processing example {i+1}/{len(eval_dataset)}: {question[:50]}...")
                
                # Retrieve context
                retrieved_contexts = self.retrieve_context(
                    question=question,
                    n_results=n_contexts
                )
                
                # Generate answer
                generated_answer = self.generate_answer(
                    question=question,
                    contexts=retrieved_contexts,
                    model_name=model_name
                )
                
                # Store results
                questions.append(question)
                ground_truths.append(ground_truth)
                answers.append(generated_answer)
                contexts.append(retrieved_contexts)
                
            except Exception as e:
                logger.error(f"Error processing example {i}: {e}")
                continue
        
        if not questions:
            raise ValueError("No examples processed successfully")
        
        # Create RAGAS dataset
        ragas_dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths
        })
        
        # Run RAGAS evaluation
        logger.info("Running RAGAS evaluation...")
        try:
            results = evaluate(
                dataset=ragas_dataset,
                metrics=self.metrics
            )
            
            # Extract scores
            scores = {
                "faithfulness": results["faithfulness"],
                "answer_correctness": results["answer_correctness"],
                "context_precision": results["context_precision"],
                "context_recall": results["context_recall"],
                "answer_relevancy": results["answer_relevancy"]
            }
            
            # Calculate Hit@5 manually
            hit_at_5 = self._calculate_hit_at_k(
                questions=questions,
                ground_truths=ground_truths,
                contexts=contexts,
                k=5
            )
            scores["hit_at_5"] = hit_at_5
            
            # Calculate overall score
            overall_score = sum(scores.values()) / len(scores)
            scores["overall_score"] = overall_score
            
            logger.info("RAGAS evaluation completed")
            
            return {
                "success": True,
                "num_examples": len(questions),
                "scores": scores,
                "detailed_results": results.to_pandas().to_dict('records'),
                "evaluation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "num_examples": len(questions)
            }
    
    def _calculate_hit_at_k(self, 
                           questions: List[str],
                           ground_truths: List[str], 
                           contexts: List[List[str]],
                           k: int = 5) -> float:
        """
        Calculate Hit@K metric.
        
        Args:
            questions: List of questions
            ground_truths: List of ground truth answers
            contexts: List of retrieved contexts for each question
            k: Number of top results to consider
            
        Returns:
            float: Hit@K score
        """
        hits = 0
        total = len(questions)
        
        for i in range(total):
            ground_truth = ground_truths[i].lower()
            question_contexts = contexts[i][:k]
            
            # Check if any context contains relevant information
            for context in question_contexts:
                if any(word in context.lower() for word in ground_truth.split() if len(word) > 3):
                    hits += 1
                    break
        
        return hits / total if total > 0 else 0.0
    
    def compare_with_baseline(self, 
                             current_scores: Dict[str, float],
                             baseline_path: str,
                             improvement_threshold: float = 0.05) -> Dict[str, Any]:
        """
        Compare current scores with baseline.
        
        Args:
            current_scores: Current evaluation scores
            baseline_path: Path to baseline scores JSON
            improvement_threshold: Minimum improvement required
            
        Returns:
            Dict: Comparison results
        """
        baseline_file = Path(baseline_path)
        
        if not baseline_file.exists():
            logger.warning(f"Baseline file not found: {baseline_path}")
            return {
                "baseline_available": False,
                "should_promote": True,  # Promote if no baseline
                "message": "No baseline available - promoting model"
            }
        
        try:
            with open(baseline_file, 'r') as f:
                baseline_scores = json.load(f)
            
            # Compare scores
            improvements = {}
            for metric, current_score in current_scores.items():
                baseline_score = baseline_scores.get(metric, 0.0)
                improvement = current_score - baseline_score
                improvements[metric] = {
                    "current": current_score,
                    "baseline": baseline_score,
                    "improvement": improvement,
                    "improvement_pct": (improvement / baseline_score * 100) if baseline_score > 0 else 0
                }
            
            # Check if overall improvement meets threshold
            overall_improvement = improvements.get("overall_score", {}).get("improvement", 0)
            should_promote = overall_improvement >= improvement_threshold
            
            return {
                "baseline_available": True,
                "should_promote": should_promote,
                "improvement_threshold": improvement_threshold,
                "overall_improvement": overall_improvement,
                "improvements": improvements,
                "message": f"Model {'promoted' if should_promote else 'not promoted'} - improvement: {overall_improvement:.3f}"
            }
            
        except Exception as e:
            logger.error(f"Error comparing with baseline: {e}")
            return {
                "baseline_available": False,
                "should_promote": False,
                "error": str(e)
            }


def main():
    """Main evaluation script."""
    parser = argparse.ArgumentParser(description="Evaluate RAG system with RAGAS")
    parser.add_argument("--eval-data", required=True, help="Path to evaluation JSONL file")
    parser.add_argument("--model", default="collegeadvisor-llama3", help="Ollama model name")
    parser.add_argument("--output", required=True, help="Output directory for results")
    parser.add_argument("--baseline", help="Path to baseline scores JSON")
    parser.add_argument("--threshold", type=float, default=0.05, help="Improvement threshold for promotion")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize evaluator
        evaluator = RAGEvaluator()
        
        # Load evaluation dataset
        eval_dataset = evaluator.load_evaluation_dataset(args.eval_data)
        
        # Run evaluation
        results = evaluator.evaluate_rag_pipeline(
            eval_dataset=eval_dataset,
            model_name=args.model
        )
        
        if not results["success"]:
            print(f"❌ Evaluation failed: {results['error']}")
            return 1
        
        # Save results
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_path = output_dir / "evaluation_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Compare with baseline if provided
        comparison = None
        if args.baseline:
            comparison = evaluator.compare_with_baseline(
                current_scores=results["scores"],
                baseline_path=args.baseline,
                improvement_threshold=args.threshold
            )
            
            comparison_path = output_dir / "baseline_comparison.json"
            with open(comparison_path, 'w') as f:
                json.dump(comparison, f, indent=2)
        
        # Print results
        print(f"✅ Evaluation completed successfully!")
        print(f"   Examples evaluated: {results['num_examples']}")
        print(f"   Results saved to: {results_path}")
        
        scores = results["scores"]
        print(f"\n📊 RAGAS Scores:")
        print(f"   Faithfulness: {scores['faithfulness']:.3f}")
        print(f"   Answer Correctness: {scores['answer_correctness']:.3f}")
        print(f"   Context Precision: {scores['context_precision']:.3f}")
        print(f"   Context Recall: {scores['context_recall']:.3f}")
        print(f"   Answer Relevancy: {scores['answer_relevancy']:.3f}")
        print(f"   Hit@5: {scores['hit_at_5']:.3f}")
        print(f"   Overall Score: {scores['overall_score']:.3f}")
        
        if comparison:
            print(f"\n🔄 Baseline Comparison:")
            print(f"   {comparison['message']}")
            if comparison.get("overall_improvement"):
                print(f"   Overall improvement: {comparison['overall_improvement']:.3f}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        print(f"❌ Evaluation failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
