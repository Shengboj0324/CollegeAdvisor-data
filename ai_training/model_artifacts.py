"""
Model Artifact Management for AI Training System.

This module handles model versioning, artifact storage, and deployment management
for the CollegeAdvisor AI training pipeline.
"""

import logging
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class ModelArtifact:
    """Model artifact metadata."""
    model_id: str
    model_type: str
    version: str
    created_at: str
    performance_metrics: Dict[str, float]
    training_data_hash: str
    model_size_mb: float
    deployment_status: str  # "pending", "deployed", "retired"
    artifact_path: str
    metadata: Dict[str, Any]

@dataclass
class ModelVersion:
    """Model version information."""
    version: str
    created_at: str
    performance_score: float
    is_champion: bool
    is_challenger: bool
    deployment_date: Optional[str] = None
    retirement_date: Optional[str] = None

class ModelArtifactManager:
    """
    Manages AI model artifacts, versioning, and deployment lifecycle.
    
    This class provides functionality for:
    - Model artifact storage and retrieval
    - Version management and rollback
    - Performance tracking and comparison
    - Deployment status management
    """
    
    def __init__(self, artifacts_dir: str = "data/model_artifacts"):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each model type
        self.model_types = ["recommendation", "personalization", "search_ranking", "content_generation"]
        for model_type in self.model_types:
            (self.artifacts_dir / model_type).mkdir(exist_ok=True)
    
    def store_model_artifact(
        self,
        model_type: str,
        model_data: bytes,
        performance_metrics: Dict[str, float],
        training_data_hash: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ModelArtifact:
        """
        Store a new model artifact.
        
        Args:
            model_type: Type of model (recommendation, personalization, etc.)
            model_data: Binary model data
            performance_metrics: Model performance metrics
            training_data_hash: Hash of training data used
            metadata: Additional metadata
            
        Returns:
            ModelArtifact: Created artifact metadata
        """
        try:
            # Generate model ID and version
            timestamp = datetime.now()
            model_id = f"{model_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            version = f"v{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Create artifact directory
            artifact_dir = self.artifacts_dir / model_type / model_id
            artifact_dir.mkdir(parents=True, exist_ok=True)
            
            # Store model binary
            model_file = artifact_dir / "model.bin"
            with open(model_file, 'wb') as f:
                f.write(model_data)
            
            # Calculate model size
            model_size_mb = model_file.stat().st_size / (1024 * 1024)
            
            # Create artifact metadata
            artifact = ModelArtifact(
                model_id=model_id,
                model_type=model_type,
                version=version,
                created_at=timestamp.isoformat(),
                performance_metrics=performance_metrics,
                training_data_hash=training_data_hash,
                model_size_mb=round(model_size_mb, 2),
                deployment_status="pending",
                artifact_path=str(artifact_dir),
                metadata=metadata or {}
            )
            
            # Store artifact metadata
            metadata_file = artifact_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(asdict(artifact), f, indent=2)
            
            # Update model registry
            self._update_model_registry(artifact)
            
            logger.info(f"Stored model artifact: {model_id}")
            return artifact
            
        except Exception as e:
            logger.error(f"Error storing model artifact: {str(e)}")
            raise
    
    def get_model_artifact(self, model_type: str, model_id: str) -> Optional[ModelArtifact]:
        """
        Retrieve a specific model artifact.
        
        Args:
            model_type: Type of model
            model_id: Model identifier
            
        Returns:
            ModelArtifact: Artifact metadata or None if not found
        """
        try:
            artifact_dir = self.artifacts_dir / model_type / model_id
            metadata_file = artifact_dir / "metadata.json"
            
            if not metadata_file.exists():
                return None
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            return ModelArtifact(**metadata)
            
        except Exception as e:
            logger.error(f"Error retrieving model artifact {model_id}: {str(e)}")
            return None
    
    def get_model_versions(self, model_type: str) -> List[ModelVersion]:
        """
        Get all versions for a model type.
        
        Args:
            model_type: Type of model
            
        Returns:
            List[ModelVersion]: List of model versions
        """
        try:
            registry_file = self.artifacts_dir / f"{model_type}_registry.json"
            
            if not registry_file.exists():
                return []
            
            with open(registry_file, 'r') as f:
                registry = json.load(f)
            
            versions = []
            for artifact_data in registry.get("artifacts", []):
                # Calculate performance score (average of metrics)
                metrics = artifact_data.get("performance_metrics", {})
                performance_score = sum(metrics.values()) / len(metrics) if metrics else 0.0
                
                version = ModelVersion(
                    version=artifact_data["version"],
                    created_at=artifact_data["created_at"],
                    performance_score=performance_score,
                    is_champion=artifact_data.get("deployment_status") == "deployed",
                    is_challenger=artifact_data.get("deployment_status") == "pending",
                    deployment_date=artifact_data.get("deployment_date"),
                    retirement_date=artifact_data.get("retirement_date")
                )
                versions.append(version)
            
            # Sort by creation date (newest first)
            versions.sort(key=lambda v: v.created_at, reverse=True)
            return versions
            
        except Exception as e:
            logger.error(f"Error retrieving model versions for {model_type}: {str(e)}")
            return []
    
    def get_champion_model(self, model_type: str) -> Optional[ModelArtifact]:
        """
        Get the currently deployed (champion) model.
        
        Args:
            model_type: Type of model
            
        Returns:
            ModelArtifact: Champion model artifact or None
        """
        try:
            registry_file = self.artifacts_dir / f"{model_type}_registry.json"
            
            if not registry_file.exists():
                return None
            
            with open(registry_file, 'r') as f:
                registry = json.load(f)
            
            # Find deployed model
            for artifact_data in registry.get("artifacts", []):
                if artifact_data.get("deployment_status") == "deployed":
                    return ModelArtifact(**artifact_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving champion model for {model_type}: {str(e)}")
            return None
    
    def deploy_model(self, model_type: str, model_id: str) -> bool:
        """
        Deploy a model (make it the champion).
        
        Args:
            model_type: Type of model
            model_id: Model identifier to deploy
            
        Returns:
            bool: True if deployment successful
        """
        try:
            # Get current champion and retire it
            current_champion = self.get_champion_model(model_type)
            if current_champion:
                self._update_deployment_status(
                    model_type, 
                    current_champion.model_id, 
                    "retired",
                    retirement_date=datetime.now().isoformat()
                )
            
            # Deploy new model
            success = self._update_deployment_status(
                model_type,
                model_id,
                "deployed",
                deployment_date=datetime.now().isoformat()
            )
            
            if success:
                logger.info(f"Deployed model {model_id} for {model_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deploying model {model_id}: {str(e)}")
            return False
    
    def rollback_model(self, model_type: str, target_version: str) -> bool:
        """
        Rollback to a previous model version.
        
        Args:
            model_type: Type of model
            target_version: Version to rollback to
            
        Returns:
            bool: True if rollback successful
        """
        try:
            # Find model with target version
            registry_file = self.artifacts_dir / f"{model_type}_registry.json"
            
            if not registry_file.exists():
                return False
            
            with open(registry_file, 'r') as f:
                registry = json.load(f)
            
            target_model_id = None
            for artifact_data in registry.get("artifacts", []):
                if artifact_data["version"] == target_version:
                    target_model_id = artifact_data["model_id"]
                    break
            
            if not target_model_id:
                logger.error(f"Target version {target_version} not found for {model_type}")
                return False
            
            # Deploy target model
            return self.deploy_model(model_type, target_model_id)
            
        except Exception as e:
            logger.error(f"Error rolling back to version {target_version}: {str(e)}")
            return False
    
    def cleanup_old_artifacts(self, model_type: str, keep_versions: int = 10) -> int:
        """
        Clean up old model artifacts, keeping only the most recent versions.
        
        Args:
            model_type: Type of model
            keep_versions: Number of versions to keep
            
        Returns:
            int: Number of artifacts cleaned up
        """
        try:
            versions = self.get_model_versions(model_type)
            
            if len(versions) <= keep_versions:
                return 0
            
            # Keep deployed models and recent versions
            to_delete = []
            for version in versions[keep_versions:]:
                if not version.is_champion:  # Don't delete deployed models
                    to_delete.append(version)
            
            cleaned_count = 0
            for version in to_delete:
                # Find and delete artifact
                registry_file = self.artifacts_dir / f"{model_type}_registry.json"
                with open(registry_file, 'r') as f:
                    registry = json.load(f)
                
                for i, artifact_data in enumerate(registry.get("artifacts", [])):
                    if artifact_data["version"] == version.version:
                        # Delete artifact directory
                        artifact_dir = Path(artifact_data["artifact_path"])
                        if artifact_dir.exists():
                            shutil.rmtree(artifact_dir)
                        
                        # Remove from registry
                        registry["artifacts"].pop(i)
                        cleaned_count += 1
                        break
                
                # Update registry
                with open(registry_file, 'w') as f:
                    json.dump(registry, f, indent=2)
            
            logger.info(f"Cleaned up {cleaned_count} old artifacts for {model_type}")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up artifacts for {model_type}: {str(e)}")
            return 0
    
    def _update_model_registry(self, artifact: ModelArtifact):
        """Update the model registry with new artifact."""
        try:
            registry_file = self.artifacts_dir / f"{artifact.model_type}_registry.json"
            
            # Load existing registry
            registry = {"artifacts": []}
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    registry = json.load(f)
            
            # Add new artifact
            registry["artifacts"].append(asdict(artifact))
            registry["last_updated"] = datetime.now().isoformat()
            
            # Save registry
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating model registry: {str(e)}")
    
    def _update_deployment_status(
        self, 
        model_type: str, 
        model_id: str, 
        status: str,
        deployment_date: Optional[str] = None,
        retirement_date: Optional[str] = None
    ) -> bool:
        """Update deployment status of a model."""
        try:
            registry_file = self.artifacts_dir / f"{model_type}_registry.json"
            
            if not registry_file.exists():
                return False
            
            with open(registry_file, 'r') as f:
                registry = json.load(f)
            
            # Update artifact status
            for artifact_data in registry.get("artifacts", []):
                if artifact_data["model_id"] == model_id:
                    artifact_data["deployment_status"] = status
                    if deployment_date:
                        artifact_data["deployment_date"] = deployment_date
                    if retirement_date:
                        artifact_data["retirement_date"] = retirement_date
                    break
            else:
                return False
            
            # Save registry
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating deployment status: {str(e)}")
            return False
