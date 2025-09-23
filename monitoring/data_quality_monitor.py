#!/usr/bin/env python3
"""
Data Quality Monitor Service

This service continuously monitors data quality and sends alerts when issues are detected.
"""

import os
import sys
import yaml
import asyncio
import logging
import schedule
import time
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_training.data_quality import DataQualityMonitor as QualityMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataQualityMonitorService:
    """Service for continuous data quality monitoring."""
    
    def __init__(self):
        from ai_training.data_quality import DataQualityConfig
        quality_config = DataQualityConfig()
        self.monitor = QualityMonitor(quality_config)
        self.config = self._load_config()
        self.running = False
        self.last_check_time = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration."""
        config_path = project_root / "data" / "quality_monitoring_config.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default configuration
            return {
                'monitoring_schedule': '*/15 * * * *',
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
    
    def check_data_quality(self):
        """Perform data quality check."""
        logger.info("Starting data quality check...")
        
        try:
            # Get data sources to check
            data_sources = self._get_data_sources()
            
            quality_results = {}
            alerts = []
            
            for source_name, source_path in data_sources.items():
                logger.info(f"Checking quality for: {source_name}")
                
                # Load data
                data = self._load_data_source(source_path)
                if not data:
                    continue
                
                # Assess quality
                quality_result = self.monitor.assess_data_quality(data, source_name)
                quality_results[source_name] = quality_result
                
                # Check for quality issues
                issues = self._check_quality_thresholds(quality_result, source_name)
                if issues:
                    alerts.extend(issues)
            
            # Save quality results
            self._save_quality_results(quality_results)
            
            # Send alerts if necessary
            if alerts:
                self._send_alerts(alerts)
            
            self.last_check_time = datetime.now()
            logger.info(f"Data quality check completed. Found {len(alerts)} issues.")
            
        except Exception as e:
            logger.error(f"Data quality check failed: {str(e)}")
    
    def _get_data_sources(self) -> Dict[str, str]:
        """Get list of data sources to monitor."""
        data_dir = project_root / "data"
        sources = {}
        
        # Check for training data
        training_dir = data_dir / "training"
        if training_dir.exists():
            for file_path in training_dir.glob("*.json"):
                sources[f"training_{file_path.stem}"] = str(file_path)
        
        # Check for raw data
        raw_dir = data_dir / "raw"
        if raw_dir.exists():
            for file_path in raw_dir.glob("*.json"):
                sources[f"raw_{file_path.stem}"] = str(file_path)
        
        # Check for processed data
        processed_dir = data_dir / "processed"
        if processed_dir.exists():
            for file_path in processed_dir.glob("*.json"):
                sources[f"processed_{file_path.stem}"] = str(file_path)
        
        return sources
    
    def _load_data_source(self, file_path: str) -> Dict[str, Any]:
        """Load data from a source file."""
        try:
            import json
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load data from {file_path}: {str(e)}")
            return {}
    
    def _check_quality_thresholds(self, quality_result: Dict[str, Any], source_name: str) -> List[Dict[str, Any]]:
        """Check quality results against thresholds."""
        alerts = []
        thresholds = self.config['quality_thresholds']
        
        quality_scores = quality_result.get('quality_scores', {})
        
        for metric, threshold in thresholds.items():
            score = quality_scores.get(metric, 0)
            
            if score < threshold:
                alert = {
                    'type': 'quality_threshold_violation',
                    'source': source_name,
                    'metric': metric,
                    'score': score,
                    'threshold': threshold,
                    'severity': self._get_severity(score, threshold),
                    'timestamp': datetime.now().isoformat(),
                    'message': f"Quality metric '{metric}' for '{source_name}' is below threshold: {score:.3f} < {threshold}"
                }
                alerts.append(alert)
        
        return alerts
    
    def _get_severity(self, score: float, threshold: float) -> str:
        """Determine alert severity based on score deviation."""
        deviation = threshold - score
        
        if deviation > 0.2:
            return 'critical'
        elif deviation > 0.1:
            return 'high'
        elif deviation > 0.05:
            return 'medium'
        else:
            return 'low'
    
    def _save_quality_results(self, results: Dict[str, Any]):
        """Save quality results to file."""
        try:
            results_dir = project_root / "data" / "quality_reports"
            results_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = results_dir / f"quality_report_{timestamp}.json"
            
            import json
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Quality results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"Failed to save quality results: {str(e)}")
    
    def _send_alerts(self, alerts: List[Dict[str, Any]]):
        """Send quality alerts."""
        try:
            # Save alerts to file
            alerts_dir = project_root / "data" / "quality_alerts"
            alerts_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alerts_file = alerts_dir / f"quality_alerts_{timestamp}.json"
            
            import json
            with open(alerts_file, 'w') as f:
                json.dump(alerts, f, indent=2, default=str)
            
            # Log alerts
            for alert in alerts:
                severity = alert['severity'].upper()
                logger.warning(f"[{severity}] {alert['message']}")
            
            # TODO: Implement email/webhook notifications
            logger.info(f"Alerts saved to: {alerts_file}")
            
        except Exception as e:
            logger.error(f"Failed to send alerts: {str(e)}")
    
    def start_monitoring(self):
        """Start the monitoring service."""
        logger.info("Starting data quality monitoring service...")
        
        # Schedule quality checks
        schedule_pattern = self.config.get('monitoring_schedule', '*/15 * * * *')
        
        # For simplicity, run every 15 minutes
        schedule.every(15).minutes.do(self.check_data_quality)
        
        self.running = True
        logger.info("Data quality monitoring service started")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Monitoring service stopped by user")
        except Exception as e:
            logger.error(f"Monitoring service error: {str(e)}")
        finally:
            self.running = False
    
    def stop_monitoring(self):
        """Stop the monitoring service."""
        logger.info("Stopping data quality monitoring service...")
        self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitoring service status."""
        return {
            'running': self.running,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'config': self.config,
            'next_check': schedule.next_run().isoformat() if schedule.jobs else None
        }


def main():
    """Main function to run data quality monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Data Quality Monitor Service')
    parser.add_argument('--schedule', choices=['hourly', 'continuous'], 
                       default='continuous', help='Monitoring schedule')
    parser.add_argument('--check-once', action='store_true', 
                       help='Run quality check once and exit')
    
    args = parser.parse_args()
    
    print("📊 CollegeAdvisor Data Quality Monitor")
    print("=" * 50)
    
    monitor_service = DataQualityMonitorService()
    
    if args.check_once:
        print("Running single quality check...")
        monitor_service.check_data_quality()
        print("Quality check completed.")
        return 0
    
    if args.schedule == 'hourly':
        print("Starting hourly monitoring...")
        schedule.every().hour.do(monitor_service.check_data_quality)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
            return 0
    
    else:  # continuous
        print("Starting continuous monitoring...")
        monitor_service.start_monitoring()
        return 0


if __name__ == "__main__":
    sys.exit(main())
