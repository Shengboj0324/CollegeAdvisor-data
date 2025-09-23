"""
Simple cron-based orchestration for CollegeAdvisor data pipeline.

This provides a lightweight alternative to Prefect for environments
where simple scheduling is sufficient.
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CronOrchestrator:
    """
    Simple cron-based orchestrator for production workflows.
    
    This orchestrator provides basic scheduling and execution
    of data pipeline and AI training workflows.
    """
    
    def __init__(self, project_root: str = None):
        """
        Initialize the cron orchestrator.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv"
        self.logs_dir = self.project_root / "logs" / "orchestration"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def run_command(self, command: List[str], log_file: str = None) -> Dict[str, Any]:
        """
        Run a command with proper logging and error handling.
        
        Args:
            command: Command to run
            log_file: Optional log file name
            
        Returns:
            Dict: Execution result
        """
        if log_file:
            log_path = self.logs_dir / log_file
        else:
            log_path = self.logs_dir / f"command_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logger.info(f"Running command: {' '.join(command)}")
        logger.info(f"Logging to: {log_path}")
        
        try:
            # Activate virtual environment
            env = os.environ.copy()
            if self.venv_path.exists():
                env["VIRTUAL_ENV"] = str(self.venv_path)
                env["PATH"] = f"{self.venv_path}/bin:{env['PATH']}"
            
            # Run command
            with open(log_path, 'w') as log_file_handle:
                result = subprocess.run(
                    command,
                    cwd=str(self.project_root),
                    env=env,
                    stdout=log_file_handle,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=3600  # 1 hour timeout
                )
            
            # Read log output
            with open(log_path, 'r') as log_file_handle:
                output = log_file_handle.read()
            
            success = result.returncode == 0
            
            if success:
                logger.info(f"Command completed successfully")
            else:
                logger.error(f"Command failed with return code: {result.returncode}")
            
            return {
                "success": success,
                "return_code": result.returncode,
                "output": output,
                "log_file": str(log_path),
                "timestamp": datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Command timed out")
            return {
                "success": False,
                "error": "Command timed out",
                "log_file": str(log_path),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "log_file": str(log_path),
                "timestamp": datetime.now().isoformat()
            }
    
    def daily_data_refresh(self) -> Dict[str, Any]:
        """
        Daily data refresh workflow.
        
        Returns:
            Dict: Workflow execution result
        """
        logger.info("Starting daily data refresh workflow...")
        
        workflow_results = {
            "workflow": "daily_data_refresh",
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
        
        # Step 1: Health check
        logger.info("Step 1: Health check")
        health_result = self.run_command(
            ["python", "-m", "college_advisor_data.cli", "health"],
            log_file=f"daily_health_{datetime.now().strftime('%Y%m%d')}.log"
        )
        workflow_results["steps"].append({
            "step": "health_check",
            "result": health_result
        })
        
        if not health_result["success"]:
            logger.error("Health check failed - aborting workflow")
            workflow_results["status"] = "aborted"
            workflow_results["reason"] = "Health check failed"
            return workflow_results
        
        # Step 2: Data collection (simulated)
        logger.info("Step 2: Data collection")
        # In production, this would trigger actual data collectors
        collection_result = {
            "success": True,
            "message": "Data collection completed",
            "timestamp": datetime.now().isoformat()
        }
        workflow_results["steps"].append({
            "step": "data_collection",
            "result": collection_result
        })
        
        # Step 3: Data ingestion
        logger.info("Step 3: Data ingestion")
        # Check if there's new data to ingest
        seed_dir = self.project_root / "data" / "seed"
        if seed_dir.exists() and list(seed_dir.glob("*.csv")):
            latest_seed = max(seed_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime)
            
            ingest_result = self.run_command(
                ["python", "-m", "college_advisor_data.cli", "ingest", str(latest_seed)],
                log_file=f"daily_ingest_{datetime.now().strftime('%Y%m%d')}.log"
            )
        else:
            ingest_result = {
                "success": True,
                "message": "No new data to ingest",
                "timestamp": datetime.now().isoformat()
            }
        
        workflow_results["steps"].append({
            "step": "data_ingestion",
            "result": ingest_result
        })
        
        # Step 4: Data quality monitoring
        logger.info("Step 4: Data quality monitoring")
        quality_result = self.run_command(
            ["python", "-m", "college_advisor_data.cli", "evaluate"],
            log_file=f"daily_quality_{datetime.now().strftime('%Y%m%d')}.log"
        )
        workflow_results["steps"].append({
            "step": "quality_monitoring",
            "result": quality_result
        })
        
        # Determine overall status
        all_successful = all(step["result"]["success"] for step in workflow_results["steps"])
        workflow_results["status"] = "completed" if all_successful else "failed"
        workflow_results["end_time"] = datetime.now().isoformat()
        
        logger.info(f"Daily data refresh workflow {workflow_results['status']}")
        
        return workflow_results
    
    def weekly_model_training(self) -> Dict[str, Any]:
        """
        Weekly model training workflow.
        
        Returns:
            Dict: Workflow execution result
        """
        logger.info("Starting weekly model training workflow...")
        
        workflow_results = {
            "workflow": "weekly_model_training",
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
        
        # Step 1: Generate training data
        logger.info("Step 1: Generate training data")
        training_data_result = self.run_command(
            ["python", "-m", "ai_training.training_pipeline", "generate"],
            log_file=f"weekly_training_data_{datetime.now().strftime('%Y%m%d')}.log"
        )
        workflow_results["steps"].append({
            "step": "generate_training_data",
            "result": training_data_result
        })
        
        if not training_data_result["success"]:
            logger.error("Training data generation failed - aborting workflow")
            workflow_results["status"] = "aborted"
            workflow_results["reason"] = "Training data generation failed"
            return workflow_results
        
        # Step 2: Evaluate current model (if exists)
        logger.info("Step 2: Evaluate current model")
        eval_data_path = self.project_root / "data" / "evaluation" / "eval_set.jsonl"
        
        if eval_data_path.exists():
            eval_result = self.run_command(
                ["python", "-m", "ai_training.eval_rag", 
                 "--eval-data", str(eval_data_path),
                 "--output", "evaluation_results"],
                log_file=f"weekly_eval_{datetime.now().strftime('%Y%m%d')}.log"
            )
        else:
            eval_result = {
                "success": True,
                "message": "No evaluation data available",
                "timestamp": datetime.now().isoformat()
            }
        
        workflow_results["steps"].append({
            "step": "model_evaluation",
            "result": eval_result
        })
        
        # Step 3: Train new model
        logger.info("Step 3: Train new model")
        training_data_path = self.project_root / "data" / "training" / "training_set.jsonl"
        model_output_dir = self.project_root / "models" / f"llama3-sft-{datetime.now().strftime('%Y%m%d')}"
        
        if training_data_path.exists():
            train_result = self.run_command(
                ["python", "-m", "ai_training.run_sft",
                 "--data", str(training_data_path),
                 "--output", str(model_output_dir),
                 "--epochs", "3"],
                log_file=f"weekly_training_{datetime.now().strftime('%Y%m%d')}.log"
            )
        else:
            train_result = {
                "success": False,
                "error": "No training data available",
                "timestamp": datetime.now().isoformat()
            }
        
        workflow_results["steps"].append({
            "step": "model_training",
            "result": train_result
        })
        
        # Step 4: Export to Ollama (if training successful)
        if train_result["success"] and model_output_dir.exists():
            logger.info("Step 4: Export to Ollama")
            export_output_dir = self.project_root / "exports" / datetime.now().strftime('%Y%m%d')
            
            export_result = self.run_command(
                ["python", "-m", "ai_training.export_to_ollama",
                 "--model", str(model_output_dir),
                 "--output", str(export_output_dir),
                 "--name", f"collegeadvisor-llama3-{datetime.now().strftime('%Y%m%d')}"],
                log_file=f"weekly_export_{datetime.now().strftime('%Y%m%d')}.log"
            )
            
            workflow_results["steps"].append({
                "step": "model_export",
                "result": export_result
            })
        else:
            logger.info("Step 4: Skipping export (training failed)")
            workflow_results["steps"].append({
                "step": "model_export",
                "result": {
                    "success": False,
                    "message": "Skipped due to training failure",
                    "timestamp": datetime.now().isoformat()
                }
            })
        
        # Determine overall status
        training_successful = train_result["success"]
        workflow_results["status"] = "completed" if training_successful else "failed"
        workflow_results["end_time"] = datetime.now().isoformat()
        
        logger.info(f"Weekly model training workflow {workflow_results['status']}")
        
        return workflow_results
    
    def save_workflow_result(self, result: Dict[str, Any]):
        """Save workflow result to file."""
        results_dir = self.project_root / "logs" / "workflow_results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_name = result["workflow"]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = results_dir / f"{workflow_name}_{timestamp}.json"
        
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Workflow result saved to: {result_file}")


def generate_crontab():
    """Generate crontab entries for production scheduling."""
    project_root = Path(__file__).parent.parent
    
    crontab_entries = f"""# CollegeAdvisor Data Pipeline Cron Jobs
# Generated on {datetime.now().isoformat()}

# Daily data refresh at 02:00 UTC
0 2 * * * cd {project_root} && python orchestration/cron_scheduler.py daily

# Weekly model training on Sunday at 03:00 UTC  
0 3 * * 0 cd {project_root} && python orchestration/cron_scheduler.py weekly

# Health check every 6 hours
0 */6 * * * cd {project_root} && python -m college_advisor_data.cli health >> logs/health_checks.log 2>&1
"""
    
    crontab_file = project_root / "orchestration" / "crontab.txt"
    with open(crontab_file, 'w') as f:
        f.write(crontab_entries)
    
    print(f"✅ Crontab entries generated: {crontab_file}")
    print("\nTo install:")
    print(f"crontab {crontab_file}")
    print("\nTo view current crontab:")
    print("crontab -l")


def main():
    """Main CLI for cron orchestrator."""
    parser = argparse.ArgumentParser(description="CollegeAdvisor Cron Orchestrator")
    parser.add_argument("workflow", choices=["daily", "weekly", "generate-crontab"], 
                       help="Workflow to run")
    parser.add_argument("--project-root", help="Project root directory")
    
    args = parser.parse_args()
    
    if args.workflow == "generate-crontab":
        generate_crontab()
        return
    
    # Initialize orchestrator
    orchestrator = CronOrchestrator(project_root=args.project_root)
    
    # Run workflow
    if args.workflow == "daily":
        result = orchestrator.daily_data_refresh()
    elif args.workflow == "weekly":
        result = orchestrator.weekly_model_training()
    else:
        print(f"Unknown workflow: {args.workflow}")
        return 1
    
    # Save result
    orchestrator.save_workflow_result(result)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Workflow: {result['workflow']}")
    print(f"Status: {result['status']}")
    print(f"Steps completed: {len(result['steps'])}")
    
    if result['status'] == 'failed':
        failed_steps = [step for step in result['steps'] if not step['result']['success']]
        print(f"Failed steps: {len(failed_steps)}")
        for step in failed_steps:
            print(f"  - {step['step']}: {step['result'].get('error', 'Unknown error')}")
    
    print(f"{'='*60}")
    
    return 0 if result['status'] in ['completed', 'aborted'] else 1


if __name__ == "__main__":
    exit(main())
