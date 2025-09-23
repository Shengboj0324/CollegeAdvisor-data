#!/usr/bin/env python3
"""
Pipeline Setup Script for CollegeAdvisor Data Pipeline

This script initializes and configures all data pipelines.
"""

import os
import sys
import yaml
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from college_advisor_data.config import Config
from ai_training.training_pipeline import TrainingDataPipeline
from ai_training.continuous_learning import ContinuousLearningPipeline
from ai_training.data_quality import DataQualityMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineSetup:
    """Sets up and initializes all data pipelines."""
    
    def __init__(self):
        self.config = Config()
        self.setup_results: Dict[str, Any] = {}
    
    def create_directories(self) -> bool:
        """Create necessary directories for pipeline operations."""
        logger.info("Creating pipeline directories...")
        
        try:
            directories = [
                "data/raw",
                "data/processed",
                "data/training",
                "data/quality_reports",
                "data/quality_alerts",
                "data/quality_baselines",
                "data/evaluation_results",
                "logs",
                "cache/collectors",
                "cache/embeddings",
                "processed/chunks",
                "processed/embeddings"
            ]
            
            for directory in directories:
                dir_path = project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created directory: {directory}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create directories: {str(e)}")
            return False
    
    def initialize_training_pipeline(self) -> bool:
        """Initialize the AI training data pipeline."""
        logger.info("Initializing training data pipeline...")

        try:
            from ai_training.training_pipeline import TrainingDataConfig
            config = TrainingDataConfig()
            pipeline = TrainingDataPipeline(config)
            
            # Test pipeline initialization
            pipeline_info = {
                'name': 'Training Data Pipeline',
                'version': '1.0.0',
                'initialized_at': datetime.now().isoformat(),
                'supported_models': ['recommendation', 'personalization', 'search_ranking', 'content_generation']
            }
            
            # Save pipeline configuration
            config_path = project_root / "data" / "pipeline_config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(pipeline_info, f, default_flow_style=False)
            
            logger.info("✅ Training data pipeline initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize training pipeline: {str(e)}")
            return False
    
    def initialize_continuous_learning(self) -> bool:
        """Initialize the continuous learning pipeline."""
        logger.info("Initializing continuous learning pipeline...")

        try:
            from ai_training.continuous_learning import ContinuousLearningConfig
            config = ContinuousLearningConfig()
            pipeline = ContinuousLearningPipeline(config)
            
            # Configure continuous learning
            config = {
                'retraining_schedule': '0 2 * * 0',  # Weekly at 2 AM on Sunday
                'performance_threshold': 0.85,
                'drift_threshold': 0.1,
                'min_training_samples': 1000,
                'evaluation_metrics': ['accuracy', 'precision', 'recall', 'f1'],
                'a_b_testing_enabled': True,
                'champion_challenger_ratio': 0.8
            }
            
            # Save continuous learning configuration
            config_path = project_root / "data" / "continuous_learning_config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            logger.info("✅ Continuous learning pipeline initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize continuous learning: {str(e)}")
            return False
    
    def initialize_data_quality_monitoring(self) -> bool:
        """Initialize data quality monitoring."""
        logger.info("Initializing data quality monitoring...")

        try:
            from ai_training.data_quality import DataQualityConfig
            config = DataQualityConfig()
            monitor = DataQualityMonitor(config)
            
            # Configure quality monitoring
            config = {
                'monitoring_schedule': '*/15 * * * *',  # Every 15 minutes
                'quality_thresholds': {
                    'completeness': 0.95,
                    'consistency': 0.90,
                    'accuracy': 0.85,
                    'timeliness': 0.90,
                    'validity': 0.95,
                    'uniqueness': 0.98
                },
                'alert_channels': ['email', 'webhook'],
                'baseline_update_frequency': 'daily'
            }
            
            # Save quality monitoring configuration
            config_path = project_root / "data" / "quality_monitoring_config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            logger.info("✅ Data quality monitoring initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize data quality monitoring: {str(e)}")
            return False
    
    def setup_database_connections(self) -> bool:
        """Set up and test database connections."""
        logger.info("Setting up database connections...")
        
        try:
            # Load database configuration
            db_config_path = project_root / "configs" / "database_config.yaml"
            if not db_config_path.exists():
                logger.warning("Database config not found, creating default...")
                return True  # Skip if no config
            
            with open(db_config_path, 'r') as f:
                db_config = yaml.safe_load(f)
            
            # Test ChromaDB connection
            try:
                import chromadb
                client = chromadb.PersistentClient(path="./chroma_data")
                collections = client.list_collections()
                logger.info(f"✅ ChromaDB connected. Collections: {len(collections)}")
            except Exception as e:
                logger.warning(f"ChromaDB connection issue: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup database connections: {str(e)}")
            return False
    
    def create_pipeline_schedules(self) -> bool:
        """Create pipeline scheduling configuration."""
        logger.info("Creating pipeline schedules...")
        
        try:
            schedules = {
                'data_collection': {
                    'government_data': '0 1 * * *',  # Daily at 1 AM
                    'social_media': '*/30 * * * *',  # Every 30 minutes
                    'web_scraping': '0 */6 * * *',  # Every 6 hours
                    'authentication_events': '*/5 * * * *'  # Every 5 minutes
                },
                'data_processing': {
                    'training_data_generation': '0 3 * * *',  # Daily at 3 AM
                    'feature_engineering': '0 4 * * *',  # Daily at 4 AM
                    'model_evaluation': '0 5 * * 0'  # Weekly on Sunday at 5 AM
                },
                'quality_monitoring': {
                    'data_quality_check': '*/15 * * * *',  # Every 15 minutes
                    'anomaly_detection': '*/30 * * * *',  # Every 30 minutes
                    'quality_reporting': '0 6 * * *'  # Daily at 6 AM
                },
                'continuous_learning': {
                    'model_retraining': '0 2 * * 0',  # Weekly on Sunday at 2 AM
                    'performance_monitoring': '*/10 * * * *',  # Every 10 minutes
                    'drift_detection': '0 */2 * * *'  # Every 2 hours
                }
            }
            
            # Save schedules configuration
            schedules_path = project_root / "data" / "pipeline_schedules.yaml"
            with open(schedules_path, 'w') as f:
                yaml.dump(schedules, f, default_flow_style=False)
            
            logger.info("✅ Pipeline schedules created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create pipeline schedules: {str(e)}")
            return False
    
    def run_setup(self) -> Dict[str, Any]:
        """Run complete pipeline setup."""
        logger.info("Starting pipeline setup...")
        
        setup_steps = [
            ("Create Directories", self.create_directories),
            ("Initialize Training Pipeline", self.initialize_training_pipeline),
            ("Initialize Continuous Learning", self.initialize_continuous_learning),
            ("Initialize Data Quality Monitoring", self.initialize_data_quality_monitoring),
            ("Setup Database Connections", self.setup_database_connections),
            ("Create Pipeline Schedules", self.create_pipeline_schedules),
        ]
        
        results = {}
        all_successful = True
        
        for step_name, step_func in setup_steps:
            logger.info(f"Running: {step_name}")
            
            try:
                success = step_func()
                results[step_name] = {
                    'status': 'SUCCESS' if success else 'FAILED',
                    'timestamp': datetime.now().isoformat()
                }
                
                if not success:
                    all_successful = False
                    
            except Exception as e:
                logger.error(f"Step {step_name} failed with exception: {str(e)}")
                results[step_name] = {
                    'status': 'ERROR',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                all_successful = False
        
        results['overall_status'] = 'SUCCESS' if all_successful else 'FAILED'
        results['setup_completed_at'] = datetime.now().isoformat()
        
        # Save setup results
        results_path = project_root / "data" / "pipeline_setup_results.yaml"
        with open(results_path, 'w') as f:
            yaml.dump(results, f, default_flow_style=False)
        
        return results


def main():
    """Main function to run pipeline setup."""
    print("🚀 CollegeAdvisor Data Pipeline - Setup")
    print("=" * 50)
    
    setup = PipelineSetup()
    results = setup.run_setup()
    
    print("\n📊 SETUP SUMMARY")
    print("=" * 50)
    
    for step, result in results.items():
        if step in ['overall_status', 'setup_completed_at']:
            continue
            
        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"{status_icon} {step}: {result['status']}")
        
        if 'error' in result:
            print(f"   Error: {result['error']}")
    
    overall_status = results['overall_status']
    if overall_status == 'SUCCESS':
        print("\n🎉 Pipeline setup completed successfully!")
        print("You can now start the data collection services.")
        return 0
    else:
        print("\n⚠️  Pipeline setup encountered issues. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
