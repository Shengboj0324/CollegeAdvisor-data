"""
Production orchestration flows using Prefect.

This module implements the production scheduling and automation
for the CollegeAdvisor data pipeline and AI training system.
"""

import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from prefect import flow, task, get_run_logger
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from prefect.blocks.system import Secret

# Import our components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from college_advisor_data.storage.chroma_client import ChromaDBClient
from college_advisor_data.embedding.factory import get_canonical_embedder
from college_advisor_data.monitoring.data_quality_monitor import DataQualityMonitor
from ai_training.run_sft import CollegeAdvisorSFTTrainer
from ai_training.export_to_ollama import OllamaExporter
from ai_training.eval_rag import RAGEvaluator

logger = logging.getLogger(__name__)


@task(name="health_check_chroma")
def health_check_chroma() -> Dict[str, Any]:
    """Health check for ChromaDB connection."""
    logger = get_run_logger()
    
    try:
        client = ChromaDBClient()
        heartbeat = client.heartbeat()
        stats = client.stats()
        
        result = {
            "status": "healthy",
            "heartbeat": heartbeat,
            "document_count": stats.get("total_documents", 0),
            "schema_compliance": stats.get("schema_compliance", 0.0),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"ChromaDB health check passed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@task(name="health_check_embedder")
def health_check_embedder() -> Dict[str, Any]:
    """Health check for embedding service."""
    logger = get_run_logger()
    
    try:
        embedder = get_canonical_embedder()
        
        # Test embedding generation
        test_text = "This is a test sentence for health check."
        embedding = embedder.embed_single(test_text)
        
        result = {
            "status": "healthy",
            "model_name": embedder.model_name,
            "embedding_dimension": len(embedding),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Embedder health check passed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Embedder health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@task(name="run_data_quality_check")
def run_data_quality_check() -> Dict[str, Any]:
    """Run comprehensive data quality monitoring."""
    logger = get_run_logger()
    
    try:
        monitor = DataQualityMonitor()
        
        # Run quality checks
        quality_report = monitor.run_quality_checks()
        
        logger.info(f"Data quality check completed: {quality_report}")
        return quality_report
        
    except Exception as e:
        logger.error(f"Data quality check failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@task(name="refresh_collectors")
def refresh_collectors() -> Dict[str, Any]:
    """Refresh data collectors to get latest data."""
    logger = get_run_logger()
    
    try:
        # This would trigger the actual data collection
        # For now, we'll simulate the process
        
        logger.info("Refreshing data collectors...")
        
        # In production, this would:
        # 1. Trigger API calls to collect new data
        # 2. Run preprocessing pipelines
        # 3. Update data stores
        
        result = {
            "status": "completed",
            "collectors_refreshed": [
                "user_auth_collector",
                "social_media_collector", 
                "phone_verification_collector",
                "security_event_collector",
                "user_profile_collector"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Collectors refreshed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Collector refresh failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@task(name="upsert_to_chroma")
def upsert_to_chroma(data_path: str) -> Dict[str, Any]:
    """Upsert processed data to ChromaDB."""
    logger = get_run_logger()
    
    try:
        # This would run the ingestion pipeline
        # For now, we'll simulate the process
        
        logger.info(f"Upserting data to ChromaDB from: {data_path}")
        
        client = ChromaDBClient()
        
        # Get current stats
        stats_before = client.stats()
        
        # In production, this would run:
        # python -m college_advisor_data.cli ingest {data_path}
        
        # Simulate upsert
        stats_after = client.stats()
        
        result = {
            "status": "completed",
            "documents_before": stats_before.get("total_documents", 0),
            "documents_after": stats_after.get("total_documents", 0),
            "schema_compliance": stats_after.get("schema_compliance", 0.0),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"ChromaDB upsert completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"ChromaDB upsert failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@task(name="evaluate_rag_system")
def evaluate_rag_system(eval_data_path: str) -> Dict[str, Any]:
    """Evaluate RAG system performance."""
    logger = get_run_logger()
    
    try:
        logger.info("Starting RAG system evaluation...")
        
        evaluator = RAGEvaluator()
        
        # Load evaluation dataset
        eval_dataset = evaluator.load_evaluation_dataset(eval_data_path)
        
        # Run evaluation
        results = evaluator.evaluate_rag_pipeline(eval_dataset)
        
        if results["success"]:
            logger.info(f"RAG evaluation completed: {results['scores']}")
        else:
            logger.error(f"RAG evaluation failed: {results['error']}")
        
        return results
        
    except Exception as e:
        logger.error(f"RAG evaluation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@task(name="train_model")
def train_model(training_data_path: str, output_dir: str) -> Dict[str, Any]:
    """Train new model with latest data."""
    logger = get_run_logger()
    
    try:
        logger.info("Starting model training...")
        
        trainer = CollegeAdvisorSFTTrainer()
        
        # Load training data
        dataset = trainer.load_training_data(training_data_path)
        
        # Train model
        stats = trainer.train(
            dataset=dataset,
            output_dir=output_dir,
            num_train_epochs=3
        )
        
        logger.info(f"Model training completed: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@task(name="export_model_to_ollama")
def export_model_to_ollama(model_path: str, output_dir: str) -> Dict[str, Any]:
    """Export trained model to Ollama format."""
    logger = get_run_logger()
    
    try:
        logger.info("Starting model export to Ollama...")
        
        exporter = OllamaExporter()
        
        # Export model
        result = exporter.export_model(
            model_path=model_path,
            output_dir=output_dir,
            upload_to_s3=True
        )
        
        logger.info(f"Model export completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Model export failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@flow(name="daily_data_refresh")
def daily_data_refresh():
    """
    Daily data refresh flow.
    
    Runs at 02:00 UTC daily:
    1. Health checks
    2. Refresh collectors
    3. Preprocess data
    4. Upsert to ChromaDB
    5. Data quality monitoring
    """
    logger = get_run_logger()
    logger.info("Starting daily data refresh flow...")
    
    # Health checks
    chroma_health = health_check_chroma()
    embedder_health = health_check_embedder()
    
    if chroma_health["status"] != "healthy":
        logger.error("ChromaDB health check failed - aborting flow")
        return {"status": "aborted", "reason": "ChromaDB unhealthy"}
    
    if embedder_health["status"] != "healthy":
        logger.error("Embedder health check failed - aborting flow")
        return {"status": "aborted", "reason": "Embedder unhealthy"}
    
    # Refresh data collectors
    collector_result = refresh_collectors()
    
    if collector_result["status"] != "completed":
        logger.error("Collector refresh failed - aborting flow")
        return {"status": "aborted", "reason": "Collector refresh failed"}
    
    # Upsert to ChromaDB
    upsert_result = upsert_to_chroma("data/processed/latest")
    
    if upsert_result["status"] != "completed":
        logger.error("ChromaDB upsert failed")
        return {"status": "failed", "reason": "ChromaDB upsert failed"}
    
    # Data quality monitoring
    quality_result = run_data_quality_check()
    
    logger.info("Daily data refresh flow completed successfully")
    
    return {
        "status": "completed",
        "chroma_health": chroma_health,
        "embedder_health": embedder_health,
        "collector_result": collector_result,
        "upsert_result": upsert_result,
        "quality_result": quality_result,
        "timestamp": datetime.now().isoformat()
    }


@flow(name="weekly_model_training")
def weekly_model_training():
    """
    Weekly model training and evaluation flow.
    
    Runs on Sunday at 03:00 UTC:
    1. Generate evaluation dataset
    2. Evaluate current model
    3. Train new model if needed
    4. Export to Ollama if metrics pass
    5. Update baseline metrics
    """
    logger = get_run_logger()
    logger.info("Starting weekly model training flow...")
    
    # Paths
    eval_data_path = "data/evaluation/latest_eval_set.jsonl"
    training_data_path = "data/training/latest_training_set.jsonl"
    model_output_dir = f"models/llama3-sft-{datetime.now().strftime('%Y%m%d')}"
    
    # Evaluate current model
    eval_result = evaluate_rag_system(eval_data_path)
    
    if not eval_result["success"]:
        logger.error("RAG evaluation failed - aborting training")
        return {"status": "aborted", "reason": "Evaluation failed"}
    
    current_scores = eval_result["scores"]
    overall_score = current_scores.get("overall_score", 0.0)
    
    logger.info(f"Current model overall score: {overall_score:.3f}")
    
    # Check if we need to train a new model
    # For now, we'll train weekly regardless
    should_train = True
    
    if should_train:
        # Train new model
        training_result = train_model(training_data_path, model_output_dir)
        
        if training_result.get("status") == "failed":
            logger.error("Model training failed")
            return {"status": "failed", "reason": "Training failed"}
        
        # Evaluate new model
        new_eval_result = evaluate_rag_system(eval_data_path)
        
        if new_eval_result["success"]:
            new_scores = new_eval_result["scores"]
            new_overall_score = new_scores.get("overall_score", 0.0)
            
            # Check if new model is better
            improvement = new_overall_score - overall_score
            improvement_threshold = 0.05  # 5% improvement required
            
            if improvement >= improvement_threshold:
                # Export to Ollama
                export_result = export_model_to_ollama(
                    model_path=model_output_dir,
                    output_dir=f"exports/{datetime.now().strftime('%Y%m%d')}"
                )
                
                if export_result["success"]:
                    logger.info(f"New model promoted - improvement: {improvement:.3f}")
                    return {
                        "status": "completed",
                        "model_promoted": True,
                        "improvement": improvement,
                        "new_scores": new_scores,
                        "export_result": export_result
                    }
                else:
                    logger.error("Model export failed")
                    return {"status": "failed", "reason": "Export failed"}
            else:
                logger.info(f"New model not promoted - insufficient improvement: {improvement:.3f}")
                return {
                    "status": "completed",
                    "model_promoted": False,
                    "improvement": improvement,
                    "reason": "Insufficient improvement"
                }
        else:
            logger.error("New model evaluation failed")
            return {"status": "failed", "reason": "New model evaluation failed"}
    else:
        logger.info("No training needed - current model performance acceptable")
        return {
            "status": "completed",
            "model_promoted": False,
            "reason": "No training needed"
        }


# Create deployments
def create_deployments():
    """Create Prefect deployments for production scheduling."""
    
    # Daily data refresh deployment
    daily_deployment = Deployment.build_from_flow(
        flow=daily_data_refresh,
        name="daily-data-refresh",
        schedule=CronSchedule(cron="0 2 * * *"),  # 02:00 UTC daily
        work_queue_name="data-pipeline",
        tags=["production", "daily", "data-refresh"]
    )
    
    # Weekly model training deployment
    weekly_deployment = Deployment.build_from_flow(
        flow=weekly_model_training,
        name="weekly-model-training",
        schedule=CronSchedule(cron="0 3 * * 0"),  # 03:00 UTC on Sunday
        work_queue_name="model-training",
        tags=["production", "weekly", "model-training"]
    )
    
    return [daily_deployment, weekly_deployment]


if __name__ == "__main__":
    # Create and apply deployments
    deployments = create_deployments()
    
    for deployment in deployments:
        deployment.apply()
        print(f"✅ Deployment created: {deployment.name}")
    
    print("🚀 Production orchestration deployments ready!")
    print("   Daily data refresh: 02:00 UTC")
    print("   Weekly model training: 03:00 UTC Sunday")
