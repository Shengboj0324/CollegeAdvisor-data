"""
A/B Testing Framework for AI Model Evaluation.

This module provides comprehensive A/B testing capabilities for comparing
AI model performance and making data-driven deployment decisions.
"""

import logging
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

logger = logging.getLogger(__name__)

class ExperimentStatus(str, Enum):
    """Experiment status values."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ExperimentType(str, Enum):
    """Experiment type values."""
    MODEL_COMPARISON = "model_comparison"
    FEATURE_TEST = "feature_test"
    ALGORITHM_TEST = "algorithm_test"
    PARAMETER_TUNING = "parameter_tuning"

@dataclass
class ExperimentConfig:
    """A/B experiment configuration."""
    experiment_id: str
    name: str
    description: str
    experiment_type: ExperimentType
    model_type: str
    champion_model_id: str
    challenger_model_id: str
    traffic_split: float  # Percentage for challenger (0.0 to 1.0)
    start_date: str
    end_date: str
    success_metrics: List[str]
    minimum_sample_size: int
    confidence_level: float
    status: ExperimentStatus
    metadata: Dict[str, Any]

@dataclass
class ExperimentResult:
    """A/B experiment result data."""
    user_id: str
    experiment_id: str
    variant: str  # "champion" or "challenger"
    model_id: str
    timestamp: str
    interaction_data: Dict[str, Any]
    outcome_metrics: Dict[str, float]
    session_id: str

@dataclass
class ExperimentAnalysis:
    """A/B experiment statistical analysis."""
    experiment_id: str
    champion_metrics: Dict[str, float]
    challenger_metrics: Dict[str, float]
    statistical_significance: Dict[str, bool]
    confidence_intervals: Dict[str, Tuple[float, float]]
    sample_sizes: Dict[str, int]
    recommendation: str  # "deploy_challenger", "keep_champion", "continue_test"
    analysis_date: str

class ABTestingFramework:
    """
    Comprehensive A/B testing framework for AI model evaluation.
    
    This framework provides:
    - Experiment design and configuration
    - Traffic splitting and user assignment
    - Result collection and analysis
    - Statistical significance testing
    - Automated decision recommendations
    """
    
    def __init__(self, experiments_dir: str = "data/ab_experiments"):
        self.experiments_dir = Path(experiments_dir)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.experiments_dir / "configs").mkdir(exist_ok=True)
        (self.experiments_dir / "results").mkdir(exist_ok=True)
        (self.experiments_dir / "analyses").mkdir(exist_ok=True)
    
    def create_experiment(
        self,
        name: str,
        description: str,
        model_type: str,
        champion_model_id: str,
        challenger_model_id: str,
        traffic_split: float = 0.1,
        duration_days: int = 14,
        success_metrics: Optional[List[str]] = None,
        minimum_sample_size: int = 1000,
        confidence_level: float = 0.95,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExperimentConfig:
        """
        Create a new A/B experiment.
        
        Args:
            name: Experiment name
            description: Experiment description
            model_type: Type of model being tested
            champion_model_id: Current production model ID
            challenger_model_id: New model ID to test
            traffic_split: Percentage of traffic for challenger (0.0 to 1.0)
            duration_days: Experiment duration in days
            success_metrics: List of metrics to optimize
            minimum_sample_size: Minimum sample size per variant
            confidence_level: Statistical confidence level
            metadata: Additional experiment metadata
            
        Returns:
            ExperimentConfig: Created experiment configuration
        """
        try:
            # Generate experiment ID
            timestamp = datetime.now()
            experiment_id = f"exp_{model_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Set default success metrics
            if success_metrics is None:
                success_metrics = ["accuracy", "user_satisfaction", "response_time"]
            
            # Calculate experiment dates
            start_date = timestamp.isoformat()
            end_date = (timestamp + timedelta(days=duration_days)).isoformat()
            
            # Create experiment configuration
            config = ExperimentConfig(
                experiment_id=experiment_id,
                name=name,
                description=description,
                experiment_type=ExperimentType.MODEL_COMPARISON,
                model_type=model_type,
                champion_model_id=champion_model_id,
                challenger_model_id=challenger_model_id,
                traffic_split=traffic_split,
                start_date=start_date,
                end_date=end_date,
                success_metrics=success_metrics,
                minimum_sample_size=minimum_sample_size,
                confidence_level=confidence_level,
                status=ExperimentStatus.DRAFT,
                metadata=metadata or {}
            )
            
            # Save experiment configuration
            config_file = self.experiments_dir / "configs" / f"{experiment_id}.json"
            with open(config_file, 'w') as f:
                json.dump(asdict(config), f, indent=2)
            
            logger.info(f"Created A/B experiment: {experiment_id}")
            return config
            
        except Exception as e:
            logger.error(f"Error creating A/B experiment: {str(e)}")
            raise
    
    def start_experiment(self, experiment_id: str) -> bool:
        """
        Start an A/B experiment.
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            bool: True if experiment started successfully
        """
        try:
            config = self.get_experiment_config(experiment_id)
            if not config:
                return False
            
            # Update status to active
            config.status = ExperimentStatus.ACTIVE
            config.start_date = datetime.now().isoformat()
            
            # Save updated configuration
            config_file = self.experiments_dir / "configs" / f"{experiment_id}.json"
            with open(config_file, 'w') as f:
                json.dump(asdict(config), f, indent=2)
            
            logger.info(f"Started A/B experiment: {experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting experiment {experiment_id}: {str(e)}")
            return False
    
    def assign_user_to_variant(self, experiment_id: str, user_id: str) -> Optional[str]:
        """
        Assign a user to an experiment variant.
        
        Args:
            experiment_id: Experiment identifier
            user_id: User identifier
            
        Returns:
            str: Assigned variant ("champion" or "challenger") or None if experiment not active
        """
        try:
            config = self.get_experiment_config(experiment_id)
            if not config or config.status != ExperimentStatus.ACTIVE:
                return None
            
            # Check if experiment is within date range
            now = datetime.now()
            start_date = datetime.fromisoformat(config.start_date.replace('Z', '+00:00').replace('+00:00', ''))
            end_date = datetime.fromisoformat(config.end_date.replace('Z', '+00:00').replace('+00:00', ''))
            
            if now < start_date or now > end_date:
                return None
            
            # Use consistent hash-based assignment
            hash_input = f"{experiment_id}_{user_id}"
            hash_value = hash(hash_input) % 100
            
            # Assign based on traffic split
            if hash_value < (config.traffic_split * 100):
                return "challenger"
            else:
                return "champion"
                
        except Exception as e:
            logger.error(f"Error assigning user to variant: {str(e)}")
            return None
    
    def record_experiment_result(
        self,
        experiment_id: str,
        user_id: str,
        variant: str,
        model_id: str,
        interaction_data: Dict[str, Any],
        outcome_metrics: Dict[str, float],
        session_id: str
    ) -> bool:
        """
        Record an experiment result.
        
        Args:
            experiment_id: Experiment identifier
            user_id: User identifier
            variant: Experiment variant ("champion" or "challenger")
            model_id: Model ID used for prediction
            interaction_data: User interaction data
            outcome_metrics: Measured outcome metrics
            session_id: Session identifier
            
        Returns:
            bool: True if result recorded successfully
        """
        try:
            # Create result record
            result = ExperimentResult(
                user_id=user_id,
                experiment_id=experiment_id,
                variant=variant,
                model_id=model_id,
                timestamp=datetime.now().isoformat(),
                interaction_data=interaction_data,
                outcome_metrics=outcome_metrics,
                session_id=session_id
            )
            
            # Save result to daily file
            date_str = datetime.now().strftime('%Y%m%d')
            results_file = self.experiments_dir / "results" / f"{experiment_id}_{date_str}.json"
            
            # Append to results file
            results_list = []
            if results_file.exists():
                with open(results_file, 'r') as f:
                    results_list = json.load(f)
            
            results_list.append(asdict(result))
            
            with open(results_file, 'w') as f:
                json.dump(results_list, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording experiment result: {str(e)}")
            return False
    
    def analyze_experiment(self, experiment_id: str) -> Optional[ExperimentAnalysis]:
        """
        Analyze experiment results and provide statistical analysis.
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            ExperimentAnalysis: Statistical analysis results
        """
        try:
            config = self.get_experiment_config(experiment_id)
            if not config:
                return None
            
            # Load all results for experiment
            results = self._load_experiment_results(experiment_id)
            
            if not results:
                return None
            
            # Separate results by variant
            champion_results = [r for r in results if r["variant"] == "champion"]
            challenger_results = [r for r in results if r["variant"] == "challenger"]
            
            # Calculate metrics for each variant
            champion_metrics = self._calculate_variant_metrics(champion_results, config.success_metrics)
            challenger_metrics = self._calculate_variant_metrics(challenger_results, config.success_metrics)
            
            # Perform statistical significance testing
            significance = self._test_statistical_significance(
                champion_results, 
                challenger_results, 
                config.success_metrics,
                config.confidence_level
            )
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(
                champion_metrics,
                challenger_metrics,
                config.confidence_level
            )
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                champion_metrics,
                challenger_metrics,
                significance,
                len(champion_results),
                len(challenger_results),
                config.minimum_sample_size
            )
            
            # Create analysis
            analysis = ExperimentAnalysis(
                experiment_id=experiment_id,
                champion_metrics=champion_metrics,
                challenger_metrics=challenger_metrics,
                statistical_significance=significance,
                confidence_intervals=confidence_intervals,
                sample_sizes={"champion": len(champion_results), "challenger": len(challenger_results)},
                recommendation=recommendation,
                analysis_date=datetime.now().isoformat()
            )
            
            # Save analysis
            analysis_file = self.experiments_dir / "analyses" / f"{experiment_id}_analysis.json"
            with open(analysis_file, 'w') as f:
                json.dump(asdict(analysis), f, indent=2)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing experiment {experiment_id}: {str(e)}")
            return None
    
    def get_experiment_config(self, experiment_id: str) -> Optional[ExperimentConfig]:
        """Get experiment configuration."""
        try:
            config_file = self.experiments_dir / "configs" / f"{experiment_id}.json"
            
            if not config_file.exists():
                return None
            
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            return ExperimentConfig(**config_data)
            
        except Exception as e:
            logger.error(f"Error loading experiment config {experiment_id}: {str(e)}")
            return None
    
    def get_active_experiments(self) -> List[ExperimentConfig]:
        """Get all active experiments."""
        try:
            active_experiments = []
            config_dir = self.experiments_dir / "configs"
            
            for config_file in config_dir.glob("*.json"):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                config = ExperimentConfig(**config_data)
                if config.status == ExperimentStatus.ACTIVE:
                    active_experiments.append(config)
            
            return active_experiments
            
        except Exception as e:
            logger.error(f"Error loading active experiments: {str(e)}")
            return []
    
    def _load_experiment_results(self, experiment_id: str) -> List[Dict[str, Any]]:
        """Load all results for an experiment."""
        try:
            results = []
            results_dir = self.experiments_dir / "results"
            
            for results_file in results_dir.glob(f"{experiment_id}_*.json"):
                with open(results_file, 'r') as f:
                    daily_results = json.load(f)
                    results.extend(daily_results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error loading experiment results: {str(e)}")
            return []
    
    def _calculate_variant_metrics(self, results: List[Dict[str, Any]], success_metrics: List[str]) -> Dict[str, float]:
        """Calculate aggregated metrics for a variant."""
        try:
            if not results:
                return {}
            
            metrics = {}
            
            for metric in success_metrics:
                values = []
                for result in results:
                    if metric in result.get("outcome_metrics", {}):
                        values.append(result["outcome_metrics"][metric])
                
                if values:
                    metrics[metric] = statistics.mean(values)
                    metrics[f"{metric}_std"] = statistics.stdev(values) if len(values) > 1 else 0.0
                    metrics[f"{metric}_count"] = len(values)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating variant metrics: {str(e)}")
            return {}
    
    def _test_statistical_significance(
        self, 
        champion_results: List[Dict[str, Any]], 
        challenger_results: List[Dict[str, Any]],
        success_metrics: List[str],
        confidence_level: float
    ) -> Dict[str, bool]:
        """Test statistical significance between variants."""
        try:
            significance = {}
            
            for metric in success_metrics:
                champion_values = [r["outcome_metrics"].get(metric, 0) for r in champion_results if metric in r.get("outcome_metrics", {})]
                challenger_values = [r["outcome_metrics"].get(metric, 0) for r in challenger_results if metric in r.get("outcome_metrics", {})]
                
                if len(champion_values) > 10 and len(challenger_values) > 10:
                    # Simple t-test approximation (in production, use scipy.stats)
                    champion_mean = statistics.mean(champion_values)
                    challenger_mean = statistics.mean(challenger_values)
                    
                    # Calculate effect size (simplified)
                    effect_size = abs(challenger_mean - champion_mean) / max(champion_mean, 0.001)
                    
                    # Simple significance test (effect size > 5% and sufficient samples)
                    significance[metric] = effect_size > 0.05 and len(champion_values) > 100 and len(challenger_values) > 100
                else:
                    significance[metric] = False
            
            return significance
            
        except Exception as e:
            logger.error(f"Error testing statistical significance: {str(e)}")
            return {}
    
    def _calculate_confidence_intervals(
        self,
        champion_metrics: Dict[str, float],
        challenger_metrics: Dict[str, float],
        confidence_level: float
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for metric differences."""
        try:
            intervals = {}
            
            for metric in champion_metrics:
                if metric.endswith("_std") or metric.endswith("_count"):
                    continue
                
                champion_value = champion_metrics.get(metric, 0)
                challenger_value = challenger_metrics.get(metric, 0)
                
                # Simple confidence interval calculation
                diff = challenger_value - champion_value
                margin = abs(diff) * 0.1  # Simplified margin of error
                
                intervals[metric] = (diff - margin, diff + margin)
            
            return intervals
            
        except Exception as e:
            logger.error(f"Error calculating confidence intervals: {str(e)}")
            return {}
    
    def _generate_recommendation(
        self,
        champion_metrics: Dict[str, float],
        challenger_metrics: Dict[str, float],
        significance: Dict[str, bool],
        champion_sample_size: int,
        challenger_sample_size: int,
        minimum_sample_size: int
    ) -> str:
        """Generate deployment recommendation based on analysis."""
        try:
            # Check if we have sufficient sample size
            if champion_sample_size < minimum_sample_size or challenger_sample_size < minimum_sample_size:
                return "continue_test"
            
            # Count significant improvements
            significant_improvements = 0
            significant_degradations = 0
            
            for metric, is_significant in significance.items():
                if is_significant:
                    champion_value = champion_metrics.get(metric, 0)
                    challenger_value = challenger_metrics.get(metric, 0)
                    
                    if challenger_value > champion_value:
                        significant_improvements += 1
                    else:
                        significant_degradations += 1
            
            # Make recommendation
            if significant_improvements > significant_degradations and significant_improvements > 0:
                return "deploy_challenger"
            elif significant_degradations > 0:
                return "keep_champion"
            else:
                return "continue_test"
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {str(e)}")
            return "continue_test"
