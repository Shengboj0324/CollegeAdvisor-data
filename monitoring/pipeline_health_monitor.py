#!/usr/bin/env python3
"""
Pipeline Health Monitor Service

This service monitors the health and performance of all data pipelines.
"""

import os
import sys
import yaml
import asyncio
import logging
import schedule
import time
import psutil
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from college_advisor_data.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineHealthMonitor:
    """Service for monitoring pipeline health and performance."""
    
    def __init__(self):
        self.config = Config()
        self.running = False
        self.health_history: List[Dict[str, Any]] = []
        self.last_check_time = None
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health."""
        logger.info("Checking system health...")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'system': self._check_system_resources(),
            'storage': self._check_storage_health(),
            'services': self._check_service_health(),
            'data_freshness': self._check_data_freshness(),
            'pipeline_status': self._check_pipeline_status()
        }
        
        # Calculate overall health score
        health_status['overall_score'] = self._calculate_health_score(health_status)
        health_status['status'] = self._get_health_status(health_status['overall_score'])
        
        return health_status
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Load average (Unix systems)
            try:
                load_avg = os.getloadavg()
            except:
                load_avg = [0, 0, 0]
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'load_average': {
                    '1min': load_avg[0],
                    '5min': load_avg[1],
                    '15min': load_avg[2]
                },
                'status': 'healthy' if cpu_percent < 80 and memory_percent < 85 and disk_percent < 90 else 'warning'
            }
            
        except Exception as e:
            logger.error(f"Failed to check system resources: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_storage_health(self) -> Dict[str, Any]:
        """Check data storage health."""
        try:
            storage_status = {}
            
            # Check data directories
            data_dirs = [
                'data/raw',
                'data/processed',
                'data/training',
                'logs',
                'cache'
            ]
            
            for dir_name in data_dirs:
                dir_path = project_root / dir_name
                if dir_path.exists():
                    # Count files
                    file_count = len(list(dir_path.rglob('*')))
                    
                    # Calculate directory size
                    total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                    
                    storage_status[dir_name] = {
                        'file_count': file_count,
                        'size_bytes': total_size,
                        'size_mb': round(total_size / (1024 * 1024), 2),
                        'accessible': True
                    }
                else:
                    storage_status[dir_name] = {
                        'accessible': False,
                        'error': 'Directory does not exist'
                    }
            
            # Check ChromaDB
            try:
                chroma_path = project_root / "chroma_data"
                if chroma_path.exists():
                    chroma_size = sum(f.stat().st_size for f in chroma_path.rglob('*') if f.is_file())
                    storage_status['chromadb'] = {
                        'size_bytes': chroma_size,
                        'size_mb': round(chroma_size / (1024 * 1024), 2),
                        'accessible': True
                    }
                else:
                    storage_status['chromadb'] = {'accessible': False}
            except Exception as e:
                storage_status['chromadb'] = {'accessible': False, 'error': str(e)}
            
            return {
                'directories': storage_status,
                'status': 'healthy'
            }
            
        except Exception as e:
            logger.error(f"Failed to check storage health: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_service_health(self) -> Dict[str, Any]:
        """Check external service health."""
        services_status = {}
        
        # Check ChromaDB service
        try:
            import chromadb
            client = chromadb.PersistentClient(path="./chroma_data")
            collections = client.list_collections()
            services_status['chromadb'] = {
                'status': 'healthy',
                'collections_count': len(collections),
                'response_time_ms': 0  # Placeholder
            }
        except Exception as e:
            services_status['chromadb'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Check API endpoints (if configured)
        try:
            api_config_path = project_root / "configs" / "api_config.yaml"
            if api_config_path.exists():
                import requests
                with open(api_config_path, 'r') as f:
                    api_config = yaml.safe_load(f)
                
                api_url = api_config['api_endpoints']['college_advisor_api']
                
                start_time = time.time()
                response = requests.get(f"{api_url}/health", timeout=5)
                response_time = (time.time() - start_time) * 1000
                
                services_status['api'] = {
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'status_code': response.status_code,
                    'response_time_ms': round(response_time, 2)
                }
            else:
                services_status['api'] = {'status': 'not_configured'}
                
        except Exception as e:
            services_status['api'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        return services_status
    
    def _check_data_freshness(self) -> Dict[str, Any]:
        """Check data freshness and recency."""
        freshness_status = {}
        
        try:
            # Check training data freshness
            training_dir = project_root / "data" / "training"
            if training_dir.exists():
                training_files = list(training_dir.glob("*.json"))
                if training_files:
                    latest_file = max(training_files, key=lambda f: f.stat().st_mtime)
                    age_hours = (time.time() - latest_file.stat().st_mtime) / 3600
                    
                    freshness_status['training_data'] = {
                        'latest_file': latest_file.name,
                        'age_hours': round(age_hours, 2),
                        'status': 'fresh' if age_hours < 24 else 'stale' if age_hours < 72 else 'very_stale'
                    }
                else:
                    freshness_status['training_data'] = {'status': 'no_data'}
            
            # Check raw data freshness
            raw_dir = project_root / "data" / "raw"
            if raw_dir.exists():
                raw_files = list(raw_dir.glob("*.json"))
                if raw_files:
                    latest_file = max(raw_files, key=lambda f: f.stat().st_mtime)
                    age_hours = (time.time() - latest_file.stat().st_mtime) / 3600
                    
                    freshness_status['raw_data'] = {
                        'latest_file': latest_file.name,
                        'age_hours': round(age_hours, 2),
                        'status': 'fresh' if age_hours < 6 else 'stale' if age_hours < 24 else 'very_stale'
                    }
                else:
                    freshness_status['raw_data'] = {'status': 'no_data'}
            
            return freshness_status
            
        except Exception as e:
            logger.error(f"Failed to check data freshness: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_pipeline_status(self) -> Dict[str, Any]:
        """Check pipeline execution status."""
        pipeline_status = {}
        
        try:
            # Check log files for pipeline activity
            logs_dir = project_root / "logs"
            if logs_dir.exists():
                log_files = list(logs_dir.glob("*.log"))
                
                for log_file in log_files:
                    try:
                        # Read last few lines of log file
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            last_lines = lines[-10:] if len(lines) > 10 else lines
                        
                        # Check for recent activity
                        recent_activity = any('INFO' in line or 'ERROR' in line for line in last_lines)
                        error_count = sum(1 for line in last_lines if 'ERROR' in line)
                        
                        pipeline_status[log_file.stem] = {
                            'recent_activity': recent_activity,
                            'error_count': error_count,
                            'status': 'healthy' if recent_activity and error_count == 0 else 'warning' if error_count > 0 else 'inactive'
                        }
                        
                    except Exception as e:
                        pipeline_status[log_file.stem] = {
                            'status': 'error',
                            'error': str(e)
                        }
            
            return pipeline_status
            
        except Exception as e:
            logger.error(f"Failed to check pipeline status: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _calculate_health_score(self, health_status: Dict[str, Any]) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0
        
        # System resources (30% weight)
        system = health_status.get('system', {})
        if system.get('status') == 'warning':
            score -= 15
        elif system.get('status') == 'error':
            score -= 30
        
        # Services (40% weight)
        services = health_status.get('services', {})
        unhealthy_services = sum(1 for service in services.values() 
                               if isinstance(service, dict) and service.get('status') == 'unhealthy')
        score -= unhealthy_services * 20
        
        # Data freshness (20% weight)
        freshness = health_status.get('data_freshness', {})
        stale_data = sum(1 for data in freshness.values() 
                        if isinstance(data, dict) and data.get('status') in ['stale', 'very_stale'])
        score -= stale_data * 10
        
        # Pipeline status (10% weight)
        pipelines = health_status.get('pipeline_status', {})
        inactive_pipelines = sum(1 for pipeline in pipelines.values() 
                               if isinstance(pipeline, dict) and pipeline.get('status') == 'inactive')
        score -= inactive_pipelines * 5
        
        return max(0, score)
    
    def _get_health_status(self, score: float) -> str:
        """Get health status based on score."""
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'fair'
        elif score >= 40:
            return 'poor'
        else:
            return 'critical'
    
    def start_monitoring(self):
        """Start the health monitoring service."""
        logger.info("Starting pipeline health monitoring service...")
        
        # Schedule health checks every 5 minutes
        schedule.every(5).minutes.do(self._run_health_check)
        
        self.running = True
        logger.info("Pipeline health monitoring service started")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Health monitoring service stopped by user")
        except Exception as e:
            logger.error(f"Health monitoring service error: {str(e)}")
        finally:
            self.running = False
    
    def _run_health_check(self):
        """Run health check and save results."""
        try:
            health_status = self.check_system_health()
            
            # Add to history
            self.health_history.append(health_status)
            
            # Keep only last 100 entries
            if len(self.health_history) > 100:
                self.health_history = self.health_history[-100:]
            
            # Save health report
            self._save_health_report(health_status)
            
            self.last_check_time = datetime.now()
            
            # Log health status
            score = health_status['overall_score']
            status = health_status['status']
            logger.info(f"Health check completed. Score: {score:.1f}/100 ({status})")
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
    
    def _save_health_report(self, health_status: Dict[str, Any]):
        """Save health report to file."""
        try:
            reports_dir = project_root / "logs" / "health_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = reports_dir / f"health_report_{timestamp}.json"
            
            import json
            with open(report_file, 'w') as f:
                json.dump(health_status, f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Failed to save health report: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitoring service status."""
        return {
            'running': self.running,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'health_history_count': len(self.health_history),
            'latest_health_score': self.health_history[-1]['overall_score'] if self.health_history else None,
            'next_check': schedule.next_run().isoformat() if schedule.jobs else None
        }


def main():
    """Main function to run pipeline health monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pipeline Health Monitor Service')
    parser.add_argument('--schedule', choices=['continuous', 'once'], 
                       default='continuous', help='Monitoring schedule')
    
    args = parser.parse_args()
    
    print("🏥 CollegeAdvisor Pipeline Health Monitor")
    print("=" * 50)
    
    monitor = PipelineHealthMonitor()
    
    if args.schedule == 'once':
        print("Running single health check...")
        health_status = monitor.check_system_health()
        
        print(f"\n📊 Health Score: {health_status['overall_score']:.1f}/100 ({health_status['status']})")
        print(f"System: {health_status['system']['status']}")
        print(f"Services: {len([s for s in health_status['services'].values() if isinstance(s, dict) and s.get('status') == 'healthy'])} healthy")
        
        return 0
    
    else:  # continuous
        print("Starting continuous health monitoring...")
        monitor.start_monitoring()
        return 0


if __name__ == "__main__":
    sys.exit(main())
