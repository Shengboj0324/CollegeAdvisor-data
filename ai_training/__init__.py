"""
AI Training Module for CollegeAdvisor Data Pipeline.

This module provides comprehensive AI training infrastructure including:
- Training data pipeline for model preparation
- User behavior feature engineering
- Model evaluation framework
- Continuous learning pipeline
- Data quality monitoring

The AI training system transforms raw data into structured training sets,
implements advanced feature engineering, provides model evaluation capabilities,
and ensures continuous improvement through automated retraining pipelines.
"""

from .training_pipeline import TrainingDataPipeline, TrainingDataConfig
from .feature_engineering import UserBehaviorFeatureEngineer, FeatureConfig
from .model_evaluation import ModelEvaluationFramework, EvaluationConfig
from .continuous_learning import ContinuousLearningPipeline, ContinuousLearningConfig
from .data_quality import DataQualityMonitor, DataQualityConfig

__all__ = [
    # Training pipeline
    "TrainingDataPipeline",
    "TrainingDataConfig",
    
    # Feature engineering
    "UserBehaviorFeatureEngineer", 
    "FeatureConfig",
    
    # Model evaluation
    "ModelEvaluationFramework",
    "EvaluationConfig",
    
    # Continuous learning
    "ContinuousLearningPipeline",
    "ContinuousLearningConfig",
    
    # Data quality
    "DataQualityMonitor",
    "DataQualityConfig",
]

# Version information
__version__ = "1.0.0"
__author__ = "CollegeAdvisor AI Team"
__description__ = "AI Training Infrastructure for Educational Data Platform"
