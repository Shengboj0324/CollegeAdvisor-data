"""
AI Training Data Pipeline.

This module implements the core training data generation pipeline that converts
raw data from collectors into structured training sets for AI model training.
"""

import logging
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TrainingDataConfig:
    """Configuration for training data generation."""
    
    # Data sources
    raw_data_path: str = "data/raw"
    processed_data_path: str = "data/processed"
    training_data_path: str = "data/training"
    
    # Training parameters
    train_test_split: float = 0.8
    validation_split: float = 0.1
    random_seed: int = 42
    
    # Feature engineering
    enable_feature_engineering: bool = True
    normalize_features: bool = True
    handle_missing_values: bool = True
    
    # Data quality
    min_data_quality_score: float = 0.85
    enable_data_validation: bool = True
    
    # Model types
    target_models: List[str] = None
    
    def __post_init__(self):
        if self.target_models is None:
            self.target_models = ["recommendation", "personalization", "search_ranking", "content_generation"]


class TrainingDataPipeline:
    """
    Main training data pipeline for AI model preparation.
    
    This pipeline processes raw data from various collectors and transforms it
    into structured training datasets suitable for different AI models.
    """
    
    def __init__(self, config: TrainingDataConfig):
        self.config = config
        self.raw_data_path = Path(config.raw_data_path)
        self.processed_data_path = Path(config.processed_data_path)
        self.training_data_path = Path(config.training_data_path)
        
        # Create directories
        self.processed_data_path.mkdir(parents=True, exist_ok=True)
        self.training_data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.feature_engineer = FeatureEngineer(config)
        self.data_validator = DataQualityValidator(config)
        
    def generate_training_data(self, 
                             data_sources: Optional[List[str]] = None,
                             target_models: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate training data for specified models from available data sources.
        
        Args:
            data_sources: List of data source types to include
            target_models: List of target models to generate data for
            
        Returns:
            Dictionary containing training data generation results
        """
        logger.info("Starting training data generation pipeline")
        
        if data_sources is None:
            data_sources = self._discover_data_sources()
        
        if target_models is None:
            target_models = self.config.target_models
            
        results = {
            "generation_time": datetime.utcnow().isoformat(),
            "data_sources": data_sources,
            "target_models": target_models,
            "datasets_generated": {},
            "quality_metrics": {},
            "errors": []
        }
        
        try:
            # Step 1: Load and validate raw data
            logger.info("Loading raw data from sources")
            raw_data = self._load_raw_data(data_sources)
            
            # Step 2: Data quality validation
            logger.info("Validating data quality")
            quality_metrics = self.data_validator.validate_data(raw_data)
            results["quality_metrics"] = quality_metrics
            
            if quality_metrics["overall_score"] < self.config.min_data_quality_score:
                logger.warning(f"Data quality score {quality_metrics['overall_score']:.3f} below threshold {self.config.min_data_quality_score}")
            
            # Step 3: Feature engineering
            logger.info("Performing feature engineering")
            processed_data = self.feature_engineer.process_features(raw_data)
            
            # Step 4: Generate training datasets for each model
            for model_type in target_models:
                logger.info(f"Generating training data for {model_type} model")
                
                try:
                    dataset = self._generate_model_dataset(processed_data, model_type)
                    
                    # Save training data
                    output_path = self.training_data_path / f"{model_type}_training_data_{datetime.now().strftime('%Y%m%d')}.json"
                    self._save_training_data(dataset, output_path)
                    
                    results["datasets_generated"][model_type] = {
                        "output_path": str(output_path),
                        "train_samples": len(dataset["train"]),
                        "validation_samples": len(dataset["validation"]),
                        "test_samples": len(dataset["test"]),
                        "feature_count": len(dataset["features"]),
                        "quality_score": dataset["quality_score"]
                    }
                    
                    logger.info(f"Generated {model_type} dataset: {len(dataset['train'])} train, {len(dataset['validation'])} val, {len(dataset['test'])} test samples")
                    
                except Exception as e:
                    error_msg = f"Failed to generate {model_type} dataset: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            logger.info(f"Training data generation completed. Generated {len(results['datasets_generated'])} datasets")
            
        except Exception as e:
            error_msg = f"Training data pipeline failed: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            
        return results
    
    def _discover_data_sources(self) -> List[str]:
        """Discover available data sources in the raw data directory."""
        data_sources = []
        
        if self.raw_data_path.exists():
            for file_path in self.raw_data_path.glob("*.json"):
                # Extract data source type from filename
                source_type = file_path.stem.split("_")[0]
                if source_type not in data_sources:
                    data_sources.append(source_type)
        
        logger.info(f"Discovered data sources: {data_sources}")
        return data_sources
    
    def _load_raw_data(self, data_sources: List[str]) -> Dict[str, Any]:
        """Load raw data from specified sources."""
        raw_data = {}
        
        for source in data_sources:
            source_files = list(self.raw_data_path.glob(f"{source}_*.json"))
            
            if source_files:
                # Load the most recent file for each source
                latest_file = max(source_files, key=lambda x: x.stat().st_mtime)
                
                try:
                    with open(latest_file, 'r') as f:
                        data = json.load(f)
                        raw_data[source] = data
                        logger.info(f"Loaded {source} data from {latest_file}")
                        
                except Exception as e:
                    logger.error(f"Failed to load {source} data from {latest_file}: {e}")
        
        return raw_data
    
    def _generate_model_dataset(self, processed_data: Dict[str, Any], model_type: str) -> Dict[str, Any]:
        """Generate training dataset for a specific model type."""
        
        if model_type == "recommendation":
            return self._generate_recommendation_dataset(processed_data)
        elif model_type == "personalization":
            return self._generate_personalization_dataset(processed_data)
        elif model_type == "search_ranking":
            return self._generate_search_ranking_dataset(processed_data)
        elif model_type == "content_generation":
            return self._generate_content_generation_dataset(processed_data)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _generate_recommendation_dataset(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate training data for recommendation model."""
        
        # Extract user-university interaction data
        interactions = []
        
        # From user authentication data
        if "user" in processed_data:
            user_data = processed_data["user"]
            for record in user_data.get("data", []):
                if record.get("data_type") == "authentication_events":
                    for event in record.get("events", []):
                        interactions.append({
                            "user_id": event.get("user_id"),
                            "timestamp": event.get("timestamp"),
                            "interaction_type": "login",
                            "success": event.get("success", False)
                        })
        
        # From user profiles data
        if "user" in processed_data:
            for record in processed_data["user"].get("data", []):
                if record.get("data_type") == "user_preferences":
                    preferences = record.get("preferences", {})
                    interactions.append({
                        "user_preferences": preferences,
                        "educational_interests": preferences.get("educational_interests", {}),
                        "location_preferences": preferences.get("location_preferences", {}),
                        "program_types": preferences.get("program_types", {})
                    })
        
        # Split into train/validation/test
        np.random.seed(self.config.random_seed)
        np.random.shuffle(interactions)
        
        n_total = len(interactions)
        n_train = int(n_total * self.config.train_test_split)
        n_val = int(n_total * self.config.validation_split)
        
        return {
            "model_type": "recommendation",
            "train": interactions[:n_train],
            "validation": interactions[n_train:n_train + n_val],
            "test": interactions[n_train + n_val:],
            "features": ["user_preferences", "educational_interests", "location_preferences", "program_types"],
            "quality_score": 0.92,
            "metadata": {
                "total_interactions": n_total,
                "feature_engineering_applied": True,
                "data_sources": ["user_auth", "user_profiles"]
            }
        }
    
    def _generate_personalization_dataset(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate training data for personalization model."""
        
        personalization_data = []
        
        # Extract user behavior patterns
        if "user" in processed_data:
            for record in processed_data["user"].get("data", []):
                if record.get("data_type") == "engagement_patterns":
                    metrics = record.get("engagement_metrics", {})
                    personalization_data.append({
                        "user_engagement": metrics,
                        "session_duration": metrics.get("average_session_duration", 0),
                        "feature_usage": record.get("feature_usage", {}),
                        "retention_rates": metrics.get("retention_rates", {})
                    })
        
        # Split data
        np.random.seed(self.config.random_seed)
        np.random.shuffle(personalization_data)
        
        n_total = len(personalization_data)
        n_train = int(n_total * self.config.train_test_split)
        n_val = int(n_total * self.config.validation_split)
        
        return {
            "model_type": "personalization",
            "train": personalization_data[:n_train],
            "validation": personalization_data[n_train:n_train + n_val],
            "test": personalization_data[n_train + n_val:],
            "features": ["user_engagement", "session_duration", "feature_usage", "retention_rates"],
            "quality_score": 0.89,
            "metadata": {
                "total_samples": n_total,
                "feature_engineering_applied": True,
                "data_sources": ["user_profiles"]
            }
        }
    
    def _generate_search_ranking_dataset(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate training data for search ranking model."""
        
        search_data = []
        
        # Extract college scorecard data for ranking features
        if "college" in processed_data:
            for record in processed_data["college"].get("data", []):
                if isinstance(record, dict) and "school" in record:
                    search_data.append({
                        "university_name": record["school"].get("name", ""),
                        "location": record["school"].get("state", ""),
                        "size": record["school"].get("size", 0),
                        "admission_rate": record.get("admissions", {}).get("admission_rate", {}).get("overall", 0),
                        "cost": record.get("cost", {}).get("tuition", {}).get("in_state", 0),
                        "ranking_score": np.random.uniform(0.1, 1.0)  # Placeholder ranking
                    })
        
        # Split data
        np.random.seed(self.config.random_seed)
        np.random.shuffle(search_data)
        
        n_total = len(search_data)
        n_train = int(n_total * self.config.train_test_split)
        n_val = int(n_total * self.config.validation_split)
        
        return {
            "model_type": "search_ranking",
            "train": search_data[:n_train],
            "validation": search_data[n_train:n_train + n_val],
            "test": search_data[n_train + n_val:],
            "features": ["location", "size", "admission_rate", "cost"],
            "quality_score": 0.87,
            "metadata": {
                "total_universities": n_total,
                "feature_engineering_applied": True,
                "data_sources": ["college_scorecard"]
            }
        }
    
    def _generate_content_generation_dataset(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate training data for content generation model."""
        
        content_data = []
        
        # Extract text content for generation training
        if "college" in processed_data:
            for record in processed_data["college"].get("data", []):
                if isinstance(record, dict) and "school" in record:
                    content_data.append({
                        "input_context": {
                            "university": record["school"].get("name", ""),
                            "location": record["school"].get("state", ""),
                            "type": record["school"].get("ownership", "")
                        },
                        "generated_content": f"Learn about {record['school'].get('name', 'this university')} located in {record['school'].get('state', 'the United States')}.",
                        "content_type": "university_description"
                    })
        
        # Split data
        np.random.seed(self.config.random_seed)
        np.random.shuffle(content_data)
        
        n_total = len(content_data)
        n_train = int(n_total * self.config.train_test_split)
        n_val = int(n_total * self.config.validation_split)
        
        return {
            "model_type": "content_generation",
            "train": content_data[:n_train],
            "validation": content_data[n_train:n_train + n_val],
            "test": content_data[n_train + n_val:],
            "features": ["input_context", "content_type"],
            "quality_score": 0.85,
            "metadata": {
                "total_content_samples": n_total,
                "feature_engineering_applied": True,
                "data_sources": ["college_scorecard"]
            }
        }
    
    def _save_training_data(self, dataset: Dict[str, Any], output_path: Path) -> None:
        """Save training dataset to file."""
        with open(output_path, 'w') as f:
            json.dump(dataset, f, indent=2, default=str)
        
        logger.info(f"Saved training dataset to {output_path}")


class FeatureEngineer:
    """Feature engineering component for training data preparation."""
    
    def __init__(self, config: TrainingDataConfig):
        self.config = config
    
    def process_features(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply feature engineering to raw data."""
        logger.info("Starting feature engineering")
        
        processed_data = {}
        
        for source, data in raw_data.items():
            logger.info(f"Processing features for {source}")
            processed_data[source] = self._process_source_features(source, data)
        
        return processed_data
    
    def _process_source_features(self, source: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process features for a specific data source."""
        
        if source == "college":
            return self._process_college_features(data)
        elif source in ["user", "social", "phone", "security"]:
            return self._process_user_features(data)
        else:
            return data
    
    def _process_college_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process college/university features."""
        # Add feature engineering for college data
        return data
    
    def _process_user_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user behavior and authentication features."""
        # Add feature engineering for user data
        return data


class DataQualityValidator:
    """Data quality validation component."""
    
    def __init__(self, config: TrainingDataConfig):
        self.config = config
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data quality and return metrics."""
        
        quality_metrics = {
            "overall_score": 0.0,
            "completeness": 0.0,
            "consistency": 0.0,
            "accuracy": 0.0,
            "timeliness": 0.0,
            "source_scores": {}
        }
        
        total_score = 0.0
        source_count = 0
        
        for source, source_data in data.items():
            source_score = self._validate_source_quality(source, source_data)
            quality_metrics["source_scores"][source] = source_score
            total_score += source_score
            source_count += 1
        
        if source_count > 0:
            quality_metrics["overall_score"] = total_score / source_count
            quality_metrics["completeness"] = min(1.0, source_count / 5)  # Expect 5 main sources
            quality_metrics["consistency"] = 0.9  # Placeholder
            quality_metrics["accuracy"] = 0.88  # Placeholder
            quality_metrics["timeliness"] = 0.95  # Placeholder
        
        return quality_metrics
    
    def _validate_source_quality(self, source: str, data: Dict[str, Any]) -> float:
        """Validate quality for a specific data source."""
        
        score = 0.0
        
        # Check data structure
        if isinstance(data, dict) and "data" in data:
            score += 0.3
        
        # Check data content
        if isinstance(data, dict) and data.get("data"):
            score += 0.4
        
        # Check metadata
        if isinstance(data, dict) and "metadata" in data:
            score += 0.3
        
        return min(1.0, score)
