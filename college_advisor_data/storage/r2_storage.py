"""
Cloudflare R2 storage integration for CollegeAdvisor data pipeline.

Provides efficient, cost-effective object storage for:
- Raw data archives
- Processed datasets
- Model artifacts
- Training data backups
"""

import logging
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

logger = logging.getLogger(__name__)


class R2StorageClient:
    """
    Cloudflare R2 storage client using S3-compatible API.
    
    R2 provides zero egress fees and S3-compatible interface,
    making it ideal for storing large datasets and model artifacts.
    """
    
    def __init__(
        self,
        account_id: str = None,
        access_key_id: str = None,
        secret_access_key: str = None,
        bucket_name: str = None
    ):
        """
        Initialize R2 storage client.
        
        Args:
            account_id: Cloudflare account ID
            access_key_id: R2 access key ID
            secret_access_key: R2 secret access key
            bucket_name: Default bucket name
        """
        self.account_id = account_id or os.getenv("R2_ACCOUNT_ID")
        self.access_key_id = access_key_id or os.getenv("R2_ACCESS_KEY_ID")
        self.secret_access_key = secret_access_key or os.getenv("R2_SECRET_ACCESS_KEY")
        self.bucket_name = bucket_name or os.getenv("R2_BUCKET_NAME", "collegeadvisor-data")
        
        if not all([self.account_id, self.access_key_id, self.secret_access_key]):
            raise ValueError("R2 credentials not provided. Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")
        
        # Initialize S3 client for R2
        self.endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"

        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name='auto',  # R2 uses 'auto' as region
            config=Config(
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'adaptive'}
            )
        )
        
        logger.info(f"Initialized R2 storage client for bucket: {self.bucket_name}")
    
    def create_bucket(self, bucket_name: str = None) -> bool:
        """
        Create a new R2 bucket.

        Args:
            bucket_name: Name of bucket to create (uses default if not provided)

        Returns:
            True if successful, False otherwise
        """
        bucket = bucket_name or self.bucket_name

        try:
            # R2 doesn't use LocationConstraint - just create bucket without it
            self.client.create_bucket(Bucket=bucket)
            logger.info(f"Created R2 bucket: {bucket}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['BucketAlreadyOwnedByYou', 'BucketAlreadyExists']:
                logger.info(f"Bucket {bucket} already exists")
                return True
            else:
                logger.error(f"Error creating bucket {bucket}: {e}")
                return False
    
    def upload_file(
        self,
        file_path: Union[str, Path],
        object_key: str = None,
        bucket_name: str = None,
        metadata: Dict[str, str] = None
    ) -> bool:
        """
        Upload a file to R2 storage.
        
        Args:
            file_path: Local file path to upload
            object_key: Key (path) in R2 bucket (uses filename if not provided)
            bucket_name: Target bucket (uses default if not provided)
            metadata: Optional metadata to attach to object
            
        Returns:
            True if successful, False otherwise
        """
        file_path = Path(file_path)
        bucket = bucket_name or self.bucket_name
        key = object_key or file_path.name
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.client.upload_file(
                str(file_path),
                bucket,
                key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Uploaded {file_path} to R2://{bucket}/{key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error uploading {file_path}: {e}")
            return False
    
    def upload_directory(
        self,
        directory_path: Union[str, Path],
        prefix: str = "",
        bucket_name: str = None,
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """
        Upload an entire directory to R2 storage.
        
        Args:
            directory_path: Local directory to upload
            prefix: Prefix to add to all object keys
            bucket_name: Target bucket
            include_patterns: File patterns to include (e.g., ['*.json', '*.csv'])
            exclude_patterns: File patterns to exclude
            
        Returns:
            Statistics about the upload
        """
        directory_path = Path(directory_path)
        bucket = bucket_name or self.bucket_name
        
        if not directory_path.is_dir():
            logger.error(f"Directory not found: {directory_path}")
            return {"success": False, "error": "Directory not found"}
        
        stats = {
            "total_files": 0,
            "uploaded": 0,
            "failed": 0,
            "total_size": 0,
            "start_time": datetime.now().isoformat()
        }
        
        # Get all files in directory
        files = list(directory_path.rglob("*"))
        
        for file_path in files:
            if not file_path.is_file():
                continue
            
            # Apply filters
            if include_patterns and not any(file_path.match(p) for p in include_patterns):
                continue
            if exclude_patterns and any(file_path.match(p) for p in exclude_patterns):
                continue
            
            stats["total_files"] += 1
            stats["total_size"] += file_path.stat().st_size
            
            # Calculate relative path for object key
            relative_path = file_path.relative_to(directory_path)
            object_key = f"{prefix}/{relative_path}" if prefix else str(relative_path)
            
            # Upload file
            if self.upload_file(file_path, object_key, bucket):
                stats["uploaded"] += 1
            else:
                stats["failed"] += 1
        
        stats["end_time"] = datetime.now().isoformat()
        logger.info(f"Directory upload complete: {stats['uploaded']}/{stats['total_files']} files")
        
        return stats
    
    def download_file(
        self,
        object_key: str,
        local_path: Union[str, Path],
        bucket_name: str = None
    ) -> bool:
        """
        Download a file from R2 storage.
        
        Args:
            object_key: Key of object in R2
            local_path: Local path to save file
            bucket_name: Source bucket
            
        Returns:
            True if successful, False otherwise
        """
        bucket = bucket_name or self.bucket_name
        local_path = Path(local_path)
        
        # Create parent directory if needed
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self.client.download_file(bucket, object_key, str(local_path))
            logger.info(f"Downloaded R2://{bucket}/{object_key} to {local_path}")
            return True
            
        except ClientError as e:
            logger.error(f"Error downloading {object_key}: {e}")
            return False
    
    def list_objects(
        self,
        prefix: str = "",
        bucket_name: str = None,
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        List objects in R2 bucket.
        
        Args:
            prefix: Filter objects by prefix
            bucket_name: Bucket to list
            max_keys: Maximum number of keys to return
            
        Returns:
            List of object metadata
        """
        bucket = bucket_name or self.bucket_name
        
        try:
            response = self.client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            objects = response.get('Contents', [])
            logger.info(f"Listed {len(objects)} objects in R2://{bucket}/{prefix}")
            
            return objects
            
        except ClientError as e:
            logger.error(f"Error listing objects: {e}")
            return []
    
    def delete_object(self, object_key: str, bucket_name: str = None) -> bool:
        """
        Delete an object from R2 storage.
        
        Args:
            object_key: Key of object to delete
            bucket_name: Bucket containing object
            
        Returns:
            True if successful, False otherwise
        """
        bucket = bucket_name or self.bucket_name
        
        try:
            self.client.delete_object(Bucket=bucket, Key=object_key)
            logger.info(f"Deleted R2://{bucket}/{object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting {object_key}: {e}")
            return False
    
    def get_object_metadata(
        self,
        object_key: str,
        bucket_name: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an object.
        
        Args:
            object_key: Key of object
            bucket_name: Bucket containing object
            
        Returns:
            Object metadata or None if not found
        """
        bucket = bucket_name or self.bucket_name
        
        try:
            response = self.client.head_object(Bucket=bucket, Key=object_key)
            return {
                "size": response.get('ContentLength'),
                "last_modified": response.get('LastModified'),
                "content_type": response.get('ContentType'),
                "metadata": response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"Error getting metadata for {object_key}: {e}")
            return None
    
    def archive_dataset(
        self,
        dataset_path: Union[str, Path],
        dataset_name: str,
        version: str = None
    ) -> bool:
        """
        Archive a dataset to R2 with versioning.
        
        Args:
            dataset_path: Path to dataset file or directory
            dataset_name: Name of dataset
            version: Version identifier (uses timestamp if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        dataset_path = Path(dataset_path)
        version = version or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        prefix = f"datasets/{dataset_name}/{version}"
        
        metadata = {
            "dataset_name": dataset_name,
            "version": version,
            "archived_at": datetime.now().isoformat()
        }
        
        if dataset_path.is_file():
            object_key = f"{prefix}/{dataset_path.name}"
            return self.upload_file(dataset_path, object_key, metadata=metadata)
        elif dataset_path.is_dir():
            stats = self.upload_directory(dataset_path, prefix)
            return stats.get("uploaded", 0) > 0
        else:
            logger.error(f"Invalid dataset path: {dataset_path}")
            return False


# Convenience functions for common operations

def upload_training_data(data_path: Union[str, Path], version: str = None) -> bool:
    """Upload training data to R2."""
    client = R2StorageClient()
    return client.archive_dataset(data_path, "training_data", version)


def upload_model_artifacts(artifacts_path: Union[str, Path], model_name: str, version: str = None) -> bool:
    """Upload model artifacts to R2."""
    client = R2StorageClient()
    return client.archive_dataset(artifacts_path, f"models/{model_name}", version)


def backup_raw_data(data_dir: Union[str, Path] = "data/raw") -> bool:
    """Backup raw data directory to R2."""
    client = R2StorageClient()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return client.archive_dataset(data_dir, "raw_data_backup", timestamp)

