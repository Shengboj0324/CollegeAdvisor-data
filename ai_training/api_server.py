"""
AI Training Data API Server for CollegeAdvisor-data.

This server provides REST API endpoints for AI model training data,
real-time feature serving, and model management integration.
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dataclasses import asdict
import uvicorn

from .training_pipeline import TrainingDataPipeline, TrainingDataConfig
from .feature_engineering import UserBehaviorFeatureEngineer, FeatureConfig
from .model_evaluation import ModelEvaluationFramework, EvaluationConfig
from .continuous_learning import ContinuousLearningPipeline, ContinuousLearningConfig
from .data_quality import DataQualityMonitor, DataQualityConfig
from .model_artifacts import ModelArtifactManager
from .ab_testing import ABTestingFramework

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CollegeAdvisor AI Training API",
    description="API for AI model training data and feature serving",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI training components
training_config = TrainingDataConfig()
training_pipeline = TrainingDataPipeline(training_config)

feature_config = FeatureConfig()
feature_engineer = UserBehaviorFeatureEngineer(feature_config)

evaluation_config = EvaluationConfig()
evaluation_framework = ModelEvaluationFramework(evaluation_config)

learning_config = ContinuousLearningConfig()
continuous_learning = ContinuousLearningPipeline(learning_config)

quality_config = DataQualityConfig()
quality_monitor = DataQualityMonitor(quality_config)

# Initialize model artifact manager and A/B testing
artifact_manager = ModelArtifactManager()
ab_testing = ABTestingFramework()

# Pydantic models for API requests/responses
class TrainingDataRequest(BaseModel):
    model_type: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    include_metadata: bool = True

class UserFeaturesRequest(BaseModel):
    user_id: str
    include_real_time: bool = True
    feature_types: Optional[List[str]] = None

class ModelFeedbackRequest(BaseModel):
    model_type: str
    model_version: str
    prediction_id: str
    user_feedback: str
    feedback_score: float
    metadata: Optional[Dict[str, Any]] = None

class ModelPerformanceRequest(BaseModel):
    model_type: str
    model_version: str
    metrics: Dict[str, float]
    test_results: Dict[str, Any]
    deployment_ready: bool

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "CollegeAdvisor AI Training API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "training_data": "/api/training-data/{model_type}",
            "user_features": "/api/user-features/{user_id}",
            "model_feedback": "/api/model-feedback",
            "model_performance": "/api/model-performance-metrics",
            "data_quality": "/api/data-quality/ai-training"
        }
    }

@app.get("/api/training-data/{model_type}")
async def get_training_data(
    model_type: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_metadata: bool = True
):
    """
    Get training data for specified AI model type.
    
    Args:
        model_type: Type of model (recommendation, personalization, search_ranking, content_generation)
        start_date: Start date for data filtering (YYYY-MM-DD)
        end_date: End date for data filtering (YYYY-MM-DD)
        include_metadata: Whether to include metadata in response
    """
    try:
        # Validate model type
        valid_types = ["recommendation", "personalization", "search_ranking", "content_generation"]
        if model_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model_type. Must be one of: {valid_types}"
            )
        
        # Load training data
        data_file = Path(f"data/training/{model_type}_training_data_20250922.json")
        
        if not data_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Training data not found for model type: {model_type}"
            )
        
        with open(data_file, 'r') as f:
            training_data = json.load(f)
        
        # Apply date filtering if specified
        if start_date or end_date:
            training_data = _filter_training_data_by_date(training_data, start_date, end_date)
        
        # Add metadata if requested
        if include_metadata:
            training_data["api_metadata"] = {
                "retrieved_at": datetime.now().isoformat(),
                "model_type": model_type,
                "data_quality_score": await _get_data_quality_score(model_type),
                "total_samples": len(training_data.get("train", [])) + len(training_data.get("validation", [])) + len(training_data.get("test", []))
            }
        
        return training_data
        
    except Exception as e:
        logger.error(f"Error retrieving training data for {model_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user-features/{user_id}")
async def get_user_features(
    user_id: str,
    include_real_time: bool = True,
    feature_types: Optional[str] = None
):
    """
    Get AI features for a specific user.
    
    Args:
        user_id: User identifier
        include_real_time: Whether to include real-time computed features
        feature_types: Comma-separated list of feature types to include
    """
    try:
        # Parse feature types
        requested_types = None
        if feature_types:
            requested_types = [t.strip() for t in feature_types.split(",")]
        
        # Generate mock user data for demonstration
        # In production, this would fetch from user database
        mock_user_data = {
            "user_id": user_id,
            "authentication_events": [],
            "interaction_history": [],
            "preferences": {},
            "academic_profile": {}
        }
        
        # Extract features using feature engineer
        features = feature_engineer.extract_user_features(mock_user_data)
        
        # Filter features if specific types requested
        if requested_types:
            filtered_features = {}
            for feature_type in requested_types:
                if feature_type in features:
                    filtered_features[feature_type] = features[feature_type]
            features = filtered_features
        
        # Add real-time features if requested
        if include_real_time:
            features["real_time"] = {
                "session_active": True,
                "current_timestamp": datetime.now().isoformat(),
                "online_duration": 1800,  # 30 minutes
                "recent_interactions": []
            }
        
        return {
            "user_id": user_id,
            "features": features,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "feature_version": "1.0.0",
                "include_real_time": include_real_time
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving user features for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/model-feedback")
async def submit_model_feedback(feedback: ModelFeedbackRequest):
    """
    Submit feedback for model predictions to improve training.
    
    Args:
        feedback: Model feedback data including prediction ID, user feedback, and scores
    """
    try:
        # Save feedback to continuous learning pipeline
        feedback_data = {
            "model_type": feedback.model_type,
            "model_version": feedback.model_version,
            "prediction_id": feedback.prediction_id,
            "user_feedback": feedback.user_feedback,
            "feedback_score": feedback.feedback_score,
            "metadata": feedback.metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Store feedback for continuous learning
        feedback_file = Path("data/feedback") / f"model_feedback_{datetime.now().strftime('%Y%m%d')}.json"
        feedback_file.parent.mkdir(exist_ok=True)
        
        # Append to daily feedback file
        feedback_list = []
        if feedback_file.exists():
            with open(feedback_file, 'r') as f:
                feedback_list = json.load(f)
        
        feedback_list.append(feedback_data)
        
        with open(feedback_file, 'w') as f:
            json.dump(feedback_list, f, indent=2)
        
        # Trigger continuous learning evaluation if needed
        await _evaluate_retraining_trigger(feedback.model_type, feedback_data)
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": f"{feedback.model_type}_{feedback.prediction_id}_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error submitting model feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/model-performance-metrics")
async def submit_model_performance(performance: ModelPerformanceRequest):
    """
    Submit model performance metrics for monitoring and evaluation.
    
    Args:
        performance: Model performance data including metrics and test results
    """
    try:
        # Save performance metrics
        performance_data = {
            "model_type": performance.model_type,
            "model_version": performance.model_version,
            "metrics": performance.metrics,
            "test_results": performance.test_results,
            "deployment_ready": performance.deployment_ready,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store performance data
        performance_file = Path("data/evaluation_results") / f"performance_{performance.model_type}_{datetime.now().strftime('%Y%m%d')}.json"
        performance_file.parent.mkdir(exist_ok=True)
        
        with open(performance_file, 'w') as f:
            json.dump(performance_data, f, indent=2)
        
        # Update continuous learning pipeline
        await continuous_learning.update_model_performance(
            performance.model_type,
            performance.model_version,
            performance.metrics
        )
        
        return {
            "status": "success",
            "message": "Performance metrics submitted successfully",
            "performance_id": f"{performance.model_type}_{performance.model_version}_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error submitting model performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def _filter_training_data_by_date(data: Dict[str, Any], start_date: str, end_date: str) -> Dict[str, Any]:
    """Filter training data by date range."""
    # Implementation would filter data based on timestamps
    # For now, return data as-is since our current data doesn't have timestamps
    return data

async def _get_data_quality_score(model_type: str) -> float:
    """Get data quality score for model type."""
    try:
        # Use quality monitor to assess data quality
        quality_results = quality_monitor.assess_data_quality({}, f"{model_type}_training")
        return quality_results.get("overall_score", 0.85)
    except:
        return 0.85  # Default score

async def _evaluate_retraining_trigger(model_type: str, feedback_data: Dict[str, Any]):
    """Evaluate if model retraining should be triggered based on feedback."""
    try:
        # Check if feedback indicates poor performance
        if feedback_data.get("feedback_score", 1.0) < 0.5:
            logger.warning(f"Poor feedback received for {model_type} model")
            # Could trigger retraining evaluation here
    except Exception as e:
        logger.error(f"Error evaluating retraining trigger: {str(e)}")

@app.get("/api/data-quality/ai-training")
async def get_ai_training_data_quality():
    """Get data quality metrics for AI training data."""
    try:
        # Assess quality for all model types
        model_types = ["recommendation", "personalization", "search_ranking", "content_generation"]
        quality_results = {}

        for model_type in model_types:
            # Load training data for quality assessment
            data_file = Path(f"data/training/{model_type}_training_data_20250922.json")
            if data_file.exists():
                with open(data_file, 'r') as f:
                    training_data = json.load(f)

                quality_score = quality_monitor.assess_data_quality(training_data, f"{model_type}_training")
                quality_results[model_type] = quality_score

        # Calculate overall quality metrics
        overall_quality = {
            "training_data_quality": quality_results,
            "overall_score": sum(q.get("overall_score", 0) for q in quality_results.values()) / len(quality_results) if quality_results else 0,
            "timestamp": datetime.now().isoformat(),
            "status": "healthy" if all(q.get("overall_score", 0) > 0.7 for q in quality_results.values()) else "warning"
        }

        return overall_quality

    except Exception as e:
        logger.error(f"Error retrieving AI training data quality: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evaluation-data/{model_type}")
async def get_evaluation_data(model_type: str):
    """Get evaluation datasets for model performance testing."""
    try:
        # Validate model type
        valid_types = ["recommendation", "personalization", "search_ranking", "content_generation"]
        if model_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model_type. Must be one of: {valid_types}"
            )

        # Generate evaluation data using evaluation framework
        evaluation_data = evaluation_framework.create_evaluation_dataset(model_type)

        return {
            "model_type": model_type,
            "evaluation_data": evaluation_data,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "framework_version": "1.0.0",
                "total_test_cases": len(evaluation_data.get("test_sets", []))
            }
        }

    except Exception as e:
        logger.error(f"Error retrieving evaluation data for {model_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/model-retraining-triggers")
async def get_retraining_triggers():
    """Get current model retraining triggers and status."""
    try:
        # Get retraining status from continuous learning pipeline
        triggers = await continuous_learning.get_retraining_triggers()

        return {
            "retraining_triggers": triggers,
            "timestamp": datetime.now().isoformat(),
            "active_jobs": await continuous_learning.get_active_jobs()
        }

    except Exception as e:
        logger.error(f"Error retrieving retraining triggers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/model-updates")
async def submit_model_update(model_update: Dict[str, Any]):
    """Submit model updates after retraining."""
    try:
        # Validate model update data
        required_fields = ["model_version", "model_type", "performance_metrics"]
        for field in required_fields:
            if field not in model_update:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        # Store model update information
        update_data = {
            **model_update,
            "timestamp": datetime.now().isoformat(),
            "status": "pending_deployment"
        }

        # Save to model updates directory
        updates_file = Path("data/model_updates") / f"update_{model_update['model_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        updates_file.parent.mkdir(exist_ok=True)

        with open(updates_file, 'w') as f:
            json.dump(update_data, f, indent=2)

        return {
            "status": "success",
            "message": "Model update submitted successfully",
            "update_id": updates_file.stem,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error submitting model update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Webhook endpoints
@app.post("/webhooks/user-interactions")
async def webhook_user_interactions(interaction_data: Dict[str, Any]):
    """Webhook for receiving user interaction data from CollegeAdvisor-api."""
    try:
        # Process user interaction data for training
        processed_data = {
            "user_id": interaction_data.get("user_id"),
            "interaction_type": interaction_data.get("interaction_type"),
            "timestamp": interaction_data.get("timestamp", datetime.now().isoformat()),
            "data": interaction_data.get("data", {}),
            "processed_at": datetime.now().isoformat()
        }

        # Store interaction data
        interactions_file = Path("data/user_interactions") / f"interactions_{datetime.now().strftime('%Y%m%d')}.json"
        interactions_file.parent.mkdir(exist_ok=True)

        # Append to daily interactions file
        interactions_list = []
        if interactions_file.exists():
            with open(interactions_file, 'r') as f:
                interactions_list = json.load(f)

        interactions_list.append(processed_data)

        with open(interactions_file, 'w') as f:
            json.dump(interactions_list, f, indent=2)

        return {"status": "success", "message": "User interaction data received"}

    except Exception as e:
        logger.error(f"Error processing user interaction webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/auth-events")
async def webhook_auth_events(auth_data: Dict[str, Any]):
    """Webhook for receiving authentication events from CollegeAdvisor-api."""
    try:
        # Process authentication event data
        processed_data = {
            "event_id": auth_data.get("event_id"),
            "user_id": auth_data.get("user_id"),
            "event_type": auth_data.get("event_type"),
            "timestamp": auth_data.get("timestamp", datetime.now().isoformat()),
            "success": auth_data.get("success"),
            "metadata": auth_data.get("metadata", {}),
            "processed_at": datetime.now().isoformat()
        }

        # Store auth event data
        auth_file = Path("data/auth_events") / f"auth_events_{datetime.now().strftime('%Y%m%d')}.json"
        auth_file.parent.mkdir(exist_ok=True)

        # Append to daily auth events file
        auth_list = []
        if auth_file.exists():
            with open(auth_file, 'r') as f:
                auth_list = json.load(f)

        auth_list.append(processed_data)

        with open(auth_file, 'w') as f:
            json.dump(auth_list, f, indent=2)

        return {"status": "success", "message": "Authentication event data received"}

    except Exception as e:
        logger.error(f"Error processing auth event webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Model Artifact Management Endpoints
@app.get("/api/model-artifacts/{model_type}")
async def get_model_artifacts(model_type: str):
    """Get all model artifacts for a specific model type."""
    try:
        versions = artifact_manager.get_model_versions(model_type)
        champion = artifact_manager.get_champion_model(model_type)

        return {
            "model_type": model_type,
            "versions": [asdict(v) for v in versions],
            "champion_model": asdict(champion) if champion else None,
            "total_versions": len(versions)
        }

    except Exception as e:
        logger.error(f"Error retrieving model artifacts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/model-artifacts/{model_type}/{version}")
async def get_model_artifact(model_type: str, version: str):
    """Get specific model artifact by version."""
    try:
        # Find model by version
        versions = artifact_manager.get_model_versions(model_type)
        target_artifact = None

        for v in versions:
            if v.version == version:
                # Get full artifact details
                # In a real implementation, we'd need to map version to model_id
                break

        if not target_artifact:
            raise HTTPException(status_code=404, detail=f"Model version {version} not found")

        return {"artifact": asdict(target_artifact)}

    except Exception as e:
        logger.error(f"Error retrieving model artifact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/model-deployment")
async def deploy_model(deployment_request: Dict[str, Any]):
    """Deploy a model version."""
    try:
        model_type = deployment_request.get("model_type")
        model_id = deployment_request.get("model_id")

        if not model_type or not model_id:
            raise HTTPException(status_code=400, detail="model_type and model_id required")

        success = artifact_manager.deploy_model(model_type, model_id)

        if success:
            return {"status": "success", "message": f"Model {model_id} deployed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Deployment failed")

    except Exception as e:
        logger.error(f"Error deploying model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/model-rollback")
async def rollback_model(rollback_request: Dict[str, Any]):
    """Rollback to a previous model version."""
    try:
        model_type = rollback_request.get("model_type")
        target_version = rollback_request.get("target_version")

        if not model_type or not target_version:
            raise HTTPException(status_code=400, detail="model_type and target_version required")

        success = artifact_manager.rollback_model(model_type, target_version)

        if success:
            return {"status": "success", "message": f"Rolled back to version {target_version}"}
        else:
            raise HTTPException(status_code=500, detail="Rollback failed")

    except Exception as e:
        logger.error(f"Error rolling back model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# A/B Testing Endpoints
@app.get("/api/experiments/active")
async def get_active_experiments():
    """Get all active A/B experiments."""
    try:
        experiments = ab_testing.get_active_experiments()
        return {
            "active_experiments": [asdict(exp) for exp in experiments],
            "total_active": len(experiments)
        }

    except Exception as e:
        logger.error(f"Error retrieving active experiments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/experiments")
async def create_experiment(experiment_request: Dict[str, Any]):
    """Create a new A/B experiment."""
    try:
        config = ab_testing.create_experiment(
            name=experiment_request.get("name"),
            description=experiment_request.get("description"),
            model_type=experiment_request.get("model_type"),
            champion_model_id=experiment_request.get("champion_model_id"),
            challenger_model_id=experiment_request.get("challenger_model_id"),
            traffic_split=experiment_request.get("traffic_split", 0.1),
            duration_days=experiment_request.get("duration_days", 14),
            success_metrics=experiment_request.get("success_metrics"),
            minimum_sample_size=experiment_request.get("minimum_sample_size", 1000),
            confidence_level=experiment_request.get("confidence_level", 0.95),
            metadata=experiment_request.get("metadata")
        )

        return {"experiment": asdict(config)}

    except Exception as e:
        logger.error(f"Error creating experiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/experiments/{experiment_id}/start")
async def start_experiment(experiment_id: str):
    """Start an A/B experiment."""
    try:
        success = ab_testing.start_experiment(experiment_id)

        if success:
            return {"status": "success", "message": f"Experiment {experiment_id} started"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start experiment")

    except Exception as e:
        logger.error(f"Error starting experiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/experiments/{experiment_id}/assignment/{user_id}")
async def get_experiment_assignment(experiment_id: str, user_id: str):
    """Get user assignment for an experiment."""
    try:
        variant = ab_testing.assign_user_to_variant(experiment_id, user_id)

        return {
            "experiment_id": experiment_id,
            "user_id": user_id,
            "variant": variant,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting experiment assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/experiments/results")
async def submit_experiment_result(result_data: Dict[str, Any]):
    """Submit experiment result data."""
    try:
        success = ab_testing.record_experiment_result(
            experiment_id=result_data.get("experiment_id"),
            user_id=result_data.get("user_id"),
            variant=result_data.get("variant"),
            model_id=result_data.get("model_id"),
            interaction_data=result_data.get("interaction_data", {}),
            outcome_metrics=result_data.get("outcome_metrics", {}),
            session_id=result_data.get("session_id")
        )

        if success:
            return {"status": "success", "message": "Experiment result recorded"}
        else:
            raise HTTPException(status_code=500, detail="Failed to record result")

    except Exception as e:
        logger.error(f"Error submitting experiment result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/experiments/{experiment_id}/analysis")
async def get_experiment_analysis(experiment_id: str):
    """Get statistical analysis for an experiment."""
    try:
        analysis = ab_testing.analyze_experiment(experiment_id)

        if analysis:
            return {"analysis": asdict(analysis)}
        else:
            raise HTTPException(status_code=404, detail="Analysis not available")

    except Exception as e:
        logger.error(f"Error retrieving experiment analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
