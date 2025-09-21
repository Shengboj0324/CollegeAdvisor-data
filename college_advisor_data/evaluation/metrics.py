"""Evaluation metrics for the data pipeline and retrieval quality."""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
import json
from pathlib import Path

from ..storage.chroma_client import ChromaDBClient
from ..embedding.embedder import EmbeddingService
from ..config import config

logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """Comprehensive evaluation metrics for the data pipeline."""
    
    def __init__(self):
        self.chroma_client = ChromaDBClient()
        self.embedding_service = EmbeddingService()
    
    def evaluate_pipeline_quality(self, collection_name: str = None) -> Dict[str, Any]:
        """Evaluate overall pipeline quality."""
        logger.info("Evaluating pipeline quality")
        
        metrics = {
            "data_quality": self.evaluate_data_quality(collection_name),
            "retrieval_quality": self.evaluate_retrieval_quality(collection_name),
            "coverage_analysis": self.evaluate_coverage(collection_name),
            "embedding_quality": self.evaluate_embedding_quality(collection_name)
        }
        
        # Calculate overall score
        scores = []
        for category, category_metrics in metrics.items():
            if isinstance(category_metrics, dict) and 'score' in category_metrics:
                scores.append(category_metrics['score'])
        
        metrics['overall_score'] = np.mean(scores) if scores else 0.0
        
        return metrics
    
    def evaluate_data_quality(self, collection_name: str = None) -> Dict[str, Any]:
        """Evaluate data quality metrics."""
        try:
            stats = self.chroma_client.get_collection_stats(collection_name)
            
            if 'error' in stats:
                return {"error": stats['error'], "score": 0.0}
            
            total_docs = stats.get('total_documents', 0)
            if total_docs == 0:
                return {"error": "No documents in collection", "score": 0.0}
            
            # Sample documents for analysis
            sample_results = self.chroma_client.collection.get(
                limit=min(100, total_docs),
                include=["documents", "metadatas"]
            )
            
            quality_metrics = {
                "total_documents": total_docs,
                "document_types": stats.get('document_types', {}),
                "universities_count": len(stats.get('universities', [])),
                "subject_areas_count": len(stats.get('subject_areas', [])),
                "avg_document_length": 0,
                "metadata_completeness": 0,
                "duplicate_rate": 0
            }
            
            if sample_results['documents']:
                # Calculate average document length
                doc_lengths = [len(doc) for doc in sample_results['documents']]
                quality_metrics["avg_document_length"] = np.mean(doc_lengths)
                
                # Calculate metadata completeness
                if sample_results['metadatas']:
                    completeness_scores = []
                    for metadata in sample_results['metadatas']:
                        non_null_fields = sum(1 for v in metadata.values() if v is not None and v != '')
                        total_fields = len(metadata)
                        completeness_scores.append(non_null_fields / total_fields if total_fields > 0 else 0)
                    
                    quality_metrics["metadata_completeness"] = np.mean(completeness_scores)
                
                # Estimate duplicate rate
                doc_hashes = [hash(doc[:100]) for doc in sample_results['documents']]
                unique_hashes = len(set(doc_hashes))
                quality_metrics["duplicate_rate"] = 1 - (unique_hashes / len(doc_hashes))
            
            # Calculate quality score
            score_components = [
                min(quality_metrics["avg_document_length"] / 500, 1.0),  # Prefer docs with reasonable length
                quality_metrics["metadata_completeness"],
                1 - quality_metrics["duplicate_rate"],  # Lower duplicate rate is better
                min(quality_metrics["universities_count"] / 50, 1.0),  # Diversity bonus
                min(quality_metrics["subject_areas_count"] / 10, 1.0)  # Subject diversity bonus
            ]
            
            quality_metrics["score"] = np.mean(score_components)
            
            return quality_metrics
        
        except Exception as e:
            logger.error(f"Error evaluating data quality: {e}")
            return {"error": str(e), "score": 0.0}
    
    def evaluate_retrieval_quality(self, collection_name: str = None) -> Dict[str, Any]:
        """Evaluate retrieval quality using test queries."""
        test_queries = [
            "computer science programs at MIT",
            "summer programs for high school students",
            "engineering programs with low GPA requirements",
            "liberal arts colleges in California",
            "pre-med programs with research opportunities"
        ]
        
        retrieval_metrics = {
            "test_queries": len(test_queries),
            "successful_queries": 0,
            "avg_results_per_query": 0,
            "avg_relevance_score": 0,
            "query_results": []
        }
        
        try:
            total_results = 0
            relevance_scores = []
            
            for query in test_queries:
                try:
                    results = self.chroma_client.search(query, n_results=5, collection_name=collection_name)
                    
                    if results:
                        retrieval_metrics["successful_queries"] += 1
                        total_results += len(results)
                        
                        # Calculate relevance score based on distance
                        query_relevance = []
                        for result in results:
                            distance = result.get('distance', 1.0)
                            # Convert distance to relevance (lower distance = higher relevance)
                            relevance = max(0, 1 - distance)
                            query_relevance.append(relevance)
                        
                        avg_query_relevance = np.mean(query_relevance) if query_relevance else 0
                        relevance_scores.append(avg_query_relevance)
                        
                        retrieval_metrics["query_results"].append({
                            "query": query,
                            "results_count": len(results),
                            "avg_relevance": avg_query_relevance,
                            "top_result_distance": results[0].get('distance', 1.0) if results else 1.0
                        })
                
                except Exception as e:
                    logger.warning(f"Error with query '{query}': {e}")
                    retrieval_metrics["query_results"].append({
                        "query": query,
                        "error": str(e)
                    })
            
            retrieval_metrics["avg_results_per_query"] = (
                total_results / len(test_queries) if test_queries else 0
            )
            retrieval_metrics["avg_relevance_score"] = (
                np.mean(relevance_scores) if relevance_scores else 0
            )
            
            # Calculate retrieval score
            success_rate = retrieval_metrics["successful_queries"] / len(test_queries)
            avg_relevance = retrieval_metrics["avg_relevance_score"]
            results_coverage = min(retrieval_metrics["avg_results_per_query"] / 5, 1.0)
            
            retrieval_metrics["score"] = np.mean([success_rate, avg_relevance, results_coverage])
            
        except Exception as e:
            logger.error(f"Error evaluating retrieval quality: {e}")
            retrieval_metrics["error"] = str(e)
            retrieval_metrics["score"] = 0.0
        
        return retrieval_metrics
    
    def evaluate_coverage(self, collection_name: str = None) -> Dict[str, Any]:
        """Evaluate data coverage across different dimensions."""
        try:
            stats = self.chroma_client.get_collection_stats(collection_name)
            
            if 'error' in stats:
                return {"error": stats['error'], "score": 0.0}
            
            coverage_metrics = {
                "university_coverage": len(stats.get('universities', [])),
                "subject_area_coverage": len(stats.get('subject_areas', [])),
                "document_type_distribution": stats.get('document_types', {}),
                "geographic_coverage": 0,  # Would need location analysis
                "program_level_coverage": 0  # Would need program level analysis
            }
            
            # Analyze geographic and program level coverage from sample
            total_docs = stats.get('total_documents', 0)
            if total_docs > 0:
                sample_results = self.chroma_client.collection.get(
                    limit=min(200, total_docs),
                    include=["metadatas"]
                )
                
                if sample_results['metadatas']:
                    locations = set()
                    program_levels = set()
                    
                    for metadata in sample_results['metadatas']:
                        if metadata.get('location'):
                            locations.add(metadata['location'])
                        if metadata.get('program_type'):
                            program_levels.add(metadata['program_type'])
                    
                    coverage_metrics["geographic_coverage"] = len(locations)
                    coverage_metrics["program_level_coverage"] = len(program_levels)
            
            # Calculate coverage score
            score_components = [
                min(coverage_metrics["university_coverage"] / 100, 1.0),
                min(coverage_metrics["subject_area_coverage"] / 20, 1.0),
                min(coverage_metrics["geographic_coverage"] / 50, 1.0),
                min(coverage_metrics["program_level_coverage"] / 5, 1.0)
            ]
            
            coverage_metrics["score"] = np.mean(score_components)
            
            return coverage_metrics
        
        except Exception as e:
            logger.error(f"Error evaluating coverage: {e}")
            return {"error": str(e), "score": 0.0}
    
    def evaluate_embedding_quality(self, collection_name: str = None) -> Dict[str, Any]:
        """Evaluate embedding quality and consistency."""
        try:
            # Test embedding service health
            health_check = self.embedding_service.health_check()
            
            embedding_metrics = {
                "embedding_service_status": health_check.get("status", "unknown"),
                "embedding_dimension": health_check.get("embedding_dim", 0),
                "model_name": health_check.get("model", "unknown"),
                "consistency_score": 0,
                "semantic_coherence": 0
            }
            
            if health_check.get("status") == "healthy":
                # Test embedding consistency
                test_texts = [
                    "computer science program",
                    "computer science program",  # Duplicate for consistency test
                    "software engineering degree",
                    "programming course"
                ]
                
                try:
                    embeddings = self.embedding_service.embedder.embed_texts(test_texts)
                    
                    # Check consistency (same text should produce same embedding)
                    if len(embeddings) >= 2:
                        consistency = np.dot(embeddings[0], embeddings[1]) / (
                            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
                        )
                        embedding_metrics["consistency_score"] = float(consistency)
                    
                    # Check semantic coherence (similar texts should have similar embeddings)
                    if len(embeddings) >= 4:
                        # Compare "computer science program" with "software engineering degree"
                        similarity = np.dot(embeddings[0], embeddings[2]) / (
                            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[2])
                        )
                        embedding_metrics["semantic_coherence"] = float(similarity)
                
                except Exception as e:
                    logger.warning(f"Error testing embedding quality: {e}")
                    embedding_metrics["test_error"] = str(e)
            
            # Calculate embedding score
            score_components = []
            if embedding_metrics["embedding_service_status"] == "healthy":
                score_components.append(1.0)
            else:
                score_components.append(0.0)
            
            if embedding_metrics["consistency_score"] > 0:
                score_components.append(embedding_metrics["consistency_score"])
            
            if embedding_metrics["semantic_coherence"] > 0:
                score_components.append(min(embedding_metrics["semantic_coherence"] * 2, 1.0))
            
            embedding_metrics["score"] = np.mean(score_components) if score_components else 0.0
            
            return embedding_metrics
        
        except Exception as e:
            logger.error(f"Error evaluating embedding quality: {e}")
            return {"error": str(e), "score": 0.0}
    
    def generate_evaluation_report(self, collection_name: str = None, save_path: Path = None) -> Dict[str, Any]:
        """Generate comprehensive evaluation report."""
        logger.info("Generating evaluation report")
        
        report = {
            "evaluation_timestamp": str(np.datetime64('now')),
            "collection_name": collection_name or config.chroma_collection_name,
            "metrics": self.evaluate_pipeline_quality(collection_name),
            "recommendations": []
        }
        
        # Generate recommendations based on metrics
        metrics = report["metrics"]
        
        if metrics.get("data_quality", {}).get("score", 0) < 0.7:
            report["recommendations"].append(
                "Data quality is below threshold. Consider improving metadata completeness and reducing duplicates."
            )
        
        if metrics.get("retrieval_quality", {}).get("score", 0) < 0.7:
            report["recommendations"].append(
                "Retrieval quality needs improvement. Consider retraining embeddings or improving chunking strategy."
            )
        
        if metrics.get("coverage_analysis", {}).get("score", 0) < 0.7:
            report["recommendations"].append(
                "Data coverage is limited. Consider adding more diverse data sources."
            )
        
        if metrics.get("embedding_quality", {}).get("score", 0) < 0.7:
            report["recommendations"].append(
                "Embedding quality issues detected. Check embedding service configuration."
            )
        
        # Save report if path provided
        if save_path:
            try:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                logger.info(f"Evaluation report saved to {save_path}")
            except Exception as e:
                logger.error(f"Error saving evaluation report: {e}")
        
        return report
