#!/usr/bin/env python3
"""
Comprehensive R2 bucket data analysis.
Downloads and analyzes EVERY SINGLE FILE in the R2 bucket.

ZERO TOLERANCE for errors - validates all imports, handles all edge cases.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ dotenv imported and .env loaded")
except ImportError as e:
    logger.warning(f"⚠️  dotenv not available: {e}")

# Validate critical imports
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    logger.info("✅ boto3 imported successfully")
except ImportError as e:
    logger.error(f"❌ CRITICAL: Failed to import boto3: {e}")
    sys.exit(1)


class R2DataAnalyzer:
    """Comprehensive R2 bucket data analyzer with zero tolerance for errors."""
    
    def __init__(self):
        """Initialize R2 data analyzer."""
        logger.info("🔧 Initializing R2DataAnalyzer")
        
        # Load R2 credentials
        self.r2_account_id = os.getenv("R2_ACCOUNT_ID")
        self.r2_access_key = os.getenv("R2_ACCESS_KEY_ID")
        self.r2_secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("R2_BUCKET_NAME", "collegeadvisor-finetuning-data")
        
        # Validate credentials
        missing_vars = []
        if not self.r2_account_id:
            missing_vars.append("R2_ACCOUNT_ID")
        if not self.r2_access_key:
            missing_vars.append("R2_ACCESS_KEY_ID")
        if not self.r2_secret_key:
            missing_vars.append("R2_SECRET_ACCESS_KEY")
        
        if missing_vars:
            error_msg = f"❌ Missing R2 environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("✅ R2 credentials loaded")
        
        # Initialize S3 client
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=f'https://{self.r2_account_id}.r2.cloudflarestorage.com',
                aws_access_key_id=self.r2_access_key,
                aws_secret_access_key=self.r2_secret_key,
                region_name='auto'
            )
            logger.info("✅ R2 client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize R2 client: {e}")
            raise
        
        self.download_dir = Path("r2_data_analysis")
        self.download_dir.mkdir(exist_ok=True)
        
        self.analysis_results = {
            "files": [],
            "summary": {},
            "errors": []
        }
    
    def list_all_files(self) -> List[Dict[str, Any]]:
        """List ALL files in the R2 bucket."""
        logger.info("="*80)
        logger.info("LISTING ALL FILES IN R2 BUCKET")
        logger.info("="*80)
        
        try:
            all_files = []
            continuation_token = None
            
            while True:
                if continuation_token:
                    response = self.client.list_objects_v2(
                        Bucket=self.bucket_name,
                        ContinuationToken=continuation_token
                    )
                else:
                    response = self.client.list_objects_v2(Bucket=self.bucket_name)
                
                if 'Contents' in response:
                    for obj in response['Contents']:
                        file_info = {
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat(),
                            'size_mb': obj['Size'] / (1024 * 1024)
                        }
                        all_files.append(file_info)
                        logger.info(f"  📄 {obj['Key']} ({file_info['size_mb']:.2f} MB)")
                
                if response.get('IsTruncated'):
                    continuation_token = response.get('NextContinuationToken')
                else:
                    break
            
            logger.info(f"\n✅ Found {len(all_files)} files in R2 bucket")
            return all_files
            
        except ClientError as e:
            logger.error(f"❌ Error listing files: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise
    
    def download_file(self, key: str) -> Optional[Path]:
        """Download a single file from R2."""
        try:
            local_path = self.download_dir / key.replace('/', '_')
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📥 Downloading: {key}")
            self.client.download_file(self.bucket_name, key, str(local_path))
            logger.info(f"✅ Downloaded to: {local_path}")
            
            return local_path
            
        except Exception as e:
            logger.error(f"❌ Error downloading {key}: {e}")
            self.analysis_results["errors"].append({
                "file": key,
                "error": str(e),
                "operation": "download"
            })
            return None
    
    def analyze_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                num_records = len(data)
                
                # Analyze first record
                if num_records > 0:
                    first_record = data[0]
                    fields = list(first_record.keys()) if isinstance(first_record, dict) else []
                    
                    # Calculate average lengths
                    if fields:
                        avg_lengths = {}
                        for field in fields:
                            values = [str(record.get(field, '')) for record in data if isinstance(record, dict)]
                            if values:
                                avg_lengths[field] = sum(len(v) for v in values) / len(values)
                    else:
                        avg_lengths = {}
                    
                    return {
                        "type": "json_array",
                        "num_records": num_records,
                        "fields": fields,
                        "avg_field_lengths": avg_lengths,
                        "sample_record": first_record,
                        "success": True
                    }
                else:
                    return {
                        "type": "json_array",
                        "num_records": 0,
                        "fields": [],
                        "avg_field_lengths": {},
                        "sample_record": None,
                        "success": True
                    }
            else:
                return {
                    "type": "json_object",
                    "fields": list(data.keys()) if isinstance(data, dict) else [],
                    "success": True
                }
                
        except Exception as e:
            logger.error(f"❌ Error analyzing JSON file {file_path}: {e}")
            return {
                "type": "unknown",
                "success": False,
                "error": str(e)
            }
    
    def analyze_jsonl_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a JSONL file."""
        try:
            records = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            
            num_records = len(records)
            
            if num_records > 0:
                first_record = records[0]
                fields = list(first_record.keys()) if isinstance(first_record, dict) else []
                
                # Calculate average lengths
                avg_lengths = {}
                for field in fields:
                    values = [str(record.get(field, '')) for record in records if isinstance(record, dict)]
                    if values:
                        avg_lengths[field] = sum(len(v) for v in values) / len(values)
                
                return {
                    "type": "jsonl",
                    "num_records": num_records,
                    "fields": fields,
                    "avg_field_lengths": avg_lengths,
                    "sample_record": first_record,
                    "success": True
                }
            else:
                return {
                    "type": "jsonl",
                    "num_records": 0,
                    "fields": [],
                    "avg_field_lengths": {},
                    "sample_record": None,
                    "success": True
                }
                
        except Exception as e:
            logger.error(f"❌ Error analyzing JSONL file {file_path}: {e}")
            return {
                "type": "unknown",
                "success": False,
                "error": str(e)
            }
    
    def analyze_file(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single file."""
        key = file_info['key']
        logger.info(f"\n{'='*80}")
        logger.info(f"ANALYZING: {key}")
        logger.info(f"{'='*80}")
        
        # Download file
        local_path = self.download_file(key)
        
        if not local_path:
            return {
                "key": key,
                "success": False,
                "error": "Download failed"
            }
        
        # Determine file type and analyze
        analysis = {
            "key": key,
            "size_mb": file_info['size_mb'],
            "last_modified": file_info['last_modified']
        }
        
        if key.endswith('.json'):
            content_analysis = self.analyze_json_file(local_path)
            analysis.update(content_analysis)
        elif key.endswith('.jsonl'):
            content_analysis = self.analyze_jsonl_file(local_path)
            analysis.update(content_analysis)
        else:
            analysis.update({
                "type": "other",
                "success": True
            })
        
        return analysis
    
    def analyze_all_files(self):
        """Analyze ALL files in the R2 bucket."""
        logger.info("="*80)
        logger.info("COMPREHENSIVE R2 DATA ANALYSIS")
        logger.info("="*80)
        
        # List all files
        all_files = self.list_all_files()
        
        # Analyze each file
        for i, file_info in enumerate(all_files, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"FILE {i}/{len(all_files)}")
            logger.info(f"{'='*80}")
            
            analysis = self.analyze_file(file_info)
            self.analysis_results["files"].append(analysis)
        
        # Generate summary
        self._generate_summary()
    
    def _generate_summary(self):
        """Generate summary statistics."""
        logger.info("\n" + "="*80)
        logger.info("GENERATING SUMMARY")
        logger.info("="*80)
        
        total_files = len(self.analysis_results["files"])
        successful = [f for f in self.analysis_results["files"] if f.get("success", False)]
        failed = [f for f in self.analysis_results["files"] if not f.get("success", False)]
        
        # Count by type
        json_files = [f for f in successful if f.get("type") == "json_array"]
        jsonl_files = [f for f in successful if f.get("type") == "jsonl"]
        
        # Calculate total records
        total_records = sum(f.get("num_records", 0) for f in successful if "num_records" in f)
        
        # Calculate average field lengths across all files
        all_avg_lengths = {}
        for file in successful:
            if "avg_field_lengths" in file:
                for field, length in file["avg_field_lengths"].items():
                    if field not in all_avg_lengths:
                        all_avg_lengths[field] = []
                    all_avg_lengths[field].append(length)
        
        overall_avg_lengths = {
            field: sum(lengths) / len(lengths)
            for field, lengths in all_avg_lengths.items()
        }
        
        self.analysis_results["summary"] = {
            "total_files": total_files,
            "successful_analyses": len(successful),
            "failed_analyses": len(failed),
            "json_files": len(json_files),
            "jsonl_files": len(jsonl_files),
            "total_records": total_records,
            "overall_avg_field_lengths": overall_avg_lengths
        }
        
        logger.info(f"📊 Total files: {total_files}")
        logger.info(f"✅ Successful: {len(successful)}")
        logger.info(f"❌ Failed: {len(failed)}")
        logger.info(f"📄 JSON files: {len(json_files)}")
        logger.info(f"📄 JSONL files: {len(jsonl_files)}")
        logger.info(f"📝 Total records: {total_records}")
        logger.info(f"📏 Average field lengths:")
        for field, length in overall_avg_lengths.items():
            logger.info(f"   {field}: {length:.1f} chars")
    
    def save_analysis(self, output_file: str = "r2_comprehensive_analysis.json"):
        """Save analysis results."""
        output_path = Path(output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Analysis saved to: {output_path}")
        return output_path


def main():
    """Main execution function."""
    try:
        analyzer = R2DataAnalyzer()
        analyzer.analyze_all_files()
        analyzer.save_analysis()
        
        logger.info("\n" + "="*80)
        logger.info("✅ ANALYSIS COMPLETE")
        logger.info("="*80)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR: {e}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

