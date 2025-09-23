"""
Data Quality Monitoring for AI Model Reliability.

This module implements comprehensive data validation, quality metrics, and
monitoring systems to ensure AI model reliability and performance.
"""

import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
import warnings
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


@dataclass
class DataQualityConfig:
    """Configuration for data quality monitoring."""
    
    # Quality thresholds
    min_completeness: float = 0.95
    min_consistency: float = 0.90
    min_accuracy: float = 0.85
    min_timeliness: float = 0.90
    min_validity: float = 0.95
    
    # Anomaly detection
    contamination_rate: float = 0.1
    outlier_threshold: float = 3.0
    drift_threshold: float = 0.05
    
    # Monitoring settings
    quality_check_interval_hours: int = 6
    alert_threshold: float = 0.80
    historical_window_days: int = 30
    
    # Data validation rules
    required_fields: List[str] = field(default_factory=list)
    field_types: Dict[str, str] = field(default_factory=dict)
    value_ranges: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    categorical_values: Dict[str, List[str]] = field(default_factory=dict)


class DataQualityMonitor:
    """
    Comprehensive data quality monitoring system for AI model reliability.
    
    This system validates data quality, detects anomalies, monitors data drift,
    and provides alerts when data quality issues could impact model performance.
    """
    
    def __init__(self, config: DataQualityConfig):
        self.config = config
        self.quality_history = {}
        self.baseline_statistics = {}
        self.anomaly_detectors = {}
        
        # Setup directories
        self.quality_reports_path = Path("data/quality_reports")
        self.alerts_path = Path("data/quality_alerts")
        self.baselines_path = Path("data/quality_baselines")
        
        for path in [self.quality_reports_path, self.alerts_path, self.baselines_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def assess_data_quality(self, data: Dict[str, Any], data_source: str) -> Dict[str, Any]:
        """
        Perform comprehensive data quality assessment.
        
        Args:
            data: Data to assess
            data_source: Source identifier for the data
            
        Returns:
            Dictionary containing quality assessment results
        """
        logger.info(f"Assessing data quality for {data_source}")
        
        quality_report = {
            "data_source": data_source,
            "assessment_time": datetime.utcnow().isoformat(),
            "sample_count": 0,
            "quality_dimensions": {},
            "overall_score": 0.0,
            "issues_detected": [],
            "recommendations": [],
            "alerts": []
        }
        
        try:
            # Convert data to DataFrame for analysis
            df = self._prepare_dataframe(data)
            quality_report["sample_count"] = len(df)
            
            if len(df) == 0:
                quality_report["issues_detected"].append("No data available for assessment")
                return quality_report
            
            # Assess quality dimensions
            quality_report["quality_dimensions"]["completeness"] = self._assess_completeness(df)
            quality_report["quality_dimensions"]["consistency"] = self._assess_consistency(df)
            quality_report["quality_dimensions"]["accuracy"] = self._assess_accuracy(df, data_source)
            quality_report["quality_dimensions"]["timeliness"] = self._assess_timeliness(df)
            quality_report["quality_dimensions"]["validity"] = self._assess_validity(df)
            quality_report["quality_dimensions"]["uniqueness"] = self._assess_uniqueness(df)
            
            # Detect anomalies
            anomalies = self._detect_anomalies(df, data_source)
            quality_report["anomalies"] = anomalies
            
            # Detect data drift
            drift_analysis = self._detect_data_drift(df, data_source)
            quality_report["drift_analysis"] = drift_analysis
            
            # Calculate overall quality score
            quality_report["overall_score"] = self._calculate_overall_score(quality_report["quality_dimensions"])
            
            # Generate issues and recommendations
            quality_report["issues_detected"] = self._identify_issues(quality_report)
            quality_report["recommendations"] = self._generate_recommendations(quality_report)
            
            # Check for alerts
            quality_report["alerts"] = self._check_quality_alerts(quality_report)
            
            # Update quality history
            self._update_quality_history(data_source, quality_report)
            
            # Save quality report
            self._save_quality_report(quality_report)
            
            logger.info(f"Data quality assessment completed for {data_source}. Overall score: {quality_report['overall_score']:.3f}")
            
        except Exception as e:
            logger.error(f"Data quality assessment failed for {data_source}: {e}")
            quality_report["errors"] = [str(e)]
        
        return quality_report
    
    def _prepare_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare DataFrame from input data."""
        
        if isinstance(data, dict) and "data" in data:
            data_list = data["data"]
        elif isinstance(data, list):
            data_list = data
        else:
            data_list = [data]
        
        # Flatten nested data structures
        flattened_data = []
        for item in data_list:
            if isinstance(item, dict):
                flattened_item = self._flatten_dict(item)
                flattened_data.append(flattened_item)
        
        return pd.DataFrame(flattened_data) if flattened_data else pd.DataFrame()
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                # Handle list of dictionaries by taking the first item
                items.extend(self._flatten_dict(v[0], new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _assess_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data completeness."""
        
        completeness = {
            "overall_completeness": 0.0,
            "field_completeness": {},
            "missing_data_patterns": {},
            "score": 0.0
        }
        
        if len(df) == 0:
            return completeness
        
        # Calculate field-level completeness
        for column in df.columns:
            non_null_count = df[column].notna().sum()
            field_completeness = non_null_count / len(df)
            completeness["field_completeness"][column] = field_completeness
        
        # Overall completeness
        completeness["overall_completeness"] = np.mean(list(completeness["field_completeness"].values()))
        
        # Missing data patterns
        missing_patterns = df.isnull().sum().to_dict()
        completeness["missing_data_patterns"] = {k: v for k, v in missing_patterns.items() if v > 0}
        
        # Score based on threshold
        completeness["score"] = min(1.0, completeness["overall_completeness"] / self.config.min_completeness)
        
        return completeness
    
    def _assess_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data consistency."""
        
        consistency = {
            "format_consistency": {},
            "value_consistency": {},
            "schema_consistency": {},
            "score": 0.0
        }
        
        if len(df) == 0:
            return consistency
        
        # Format consistency (data types)
        for column in df.columns:
            if df[column].notna().sum() > 0:
                # Check if all non-null values have consistent types
                non_null_values = df[column].dropna()
                if len(non_null_values) > 0:
                    first_type = type(non_null_values.iloc[0])
                    consistent_types = all(isinstance(val, first_type) for val in non_null_values)
                    consistency["format_consistency"][column] = consistent_types
        
        # Value consistency (for categorical fields)
        for column in df.select_dtypes(include=['object']).columns:
            unique_values = df[column].dropna().unique()
            if len(unique_values) > 0:
                # Check for case inconsistencies
                lower_values = [str(v).lower() for v in unique_values]
                case_consistent = len(set(lower_values)) == len(unique_values)
                consistency["value_consistency"][column] = case_consistent
        
        # Schema consistency
        expected_columns = self.config.required_fields
        if expected_columns:
            missing_columns = set(expected_columns) - set(df.columns)
            extra_columns = set(df.columns) - set(expected_columns)
            consistency["schema_consistency"] = {
                "missing_columns": list(missing_columns),
                "extra_columns": list(extra_columns),
                "schema_match": len(missing_columns) == 0
            }
        
        # Calculate overall consistency score
        format_scores = list(consistency["format_consistency"].values())
        value_scores = list(consistency["value_consistency"].values())
        all_scores = format_scores + value_scores
        
        if all_scores:
            consistency["score"] = sum(all_scores) / len(all_scores)
        else:
            consistency["score"] = 1.0
        
        return consistency
    
    def _assess_accuracy(self, df: pd.DataFrame, data_source: str) -> Dict[str, Any]:
        """Assess data accuracy."""
        
        accuracy = {
            "range_violations": {},
            "format_violations": {},
            "business_rule_violations": {},
            "score": 0.0
        }
        
        if len(df) == 0:
            return accuracy
        
        # Check value ranges
        for column, (min_val, max_val) in self.config.value_ranges.items():
            if column in df.columns:
                numeric_col = pd.to_numeric(df[column], errors='coerce')
                violations = ((numeric_col < min_val) | (numeric_col > max_val)).sum()
                accuracy["range_violations"][column] = violations
        
        # Check categorical values
        for column, valid_values in self.config.categorical_values.items():
            if column in df.columns:
                invalid_values = ~df[column].isin(valid_values + [None, np.nan])
                violations = invalid_values.sum()
                accuracy["format_violations"][column] = violations
        
        # Business rule validations (example rules)
        if "user_id" in df.columns:
            # User IDs should be unique
            duplicate_users = df["user_id"].duplicated().sum()
            accuracy["business_rule_violations"]["duplicate_user_ids"] = duplicate_users
        
        # Calculate accuracy score
        total_violations = sum(accuracy["range_violations"].values()) + \
                          sum(accuracy["format_violations"].values()) + \
                          sum(accuracy["business_rule_violations"].values())
        
        if len(df) > 0:
            accuracy_rate = 1 - (total_violations / len(df))
            accuracy["score"] = max(0.0, accuracy_rate)
        else:
            accuracy["score"] = 1.0
        
        return accuracy
    
    def _assess_timeliness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data timeliness."""
        
        timeliness = {
            "data_freshness": {},
            "update_frequency": {},
            "score": 0.0
        }
        
        # Look for timestamp columns
        timestamp_columns = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
        
        if timestamp_columns:
            for col in timestamp_columns:
                try:
                    # Convert to datetime
                    timestamps = pd.to_datetime(df[col], errors='coerce')
                    valid_timestamps = timestamps.dropna()
                    
                    if len(valid_timestamps) > 0:
                        latest_timestamp = valid_timestamps.max()
                        current_time = pd.Timestamp.now()
                        
                        # Calculate data freshness (hours since latest data)
                        hours_since_latest = (current_time - latest_timestamp).total_seconds() / 3600
                        timeliness["data_freshness"][col] = hours_since_latest
                        
                        # Calculate update frequency
                        if len(valid_timestamps) > 1:
                            time_diffs = valid_timestamps.diff().dropna()
                            avg_update_interval = time_diffs.mean().total_seconds() / 3600
                            timeliness["update_frequency"][col] = avg_update_interval
                
                except Exception as e:
                    logger.warning(f"Error processing timestamp column {col}: {e}")
        
        # Calculate timeliness score
        if timeliness["data_freshness"]:
            # Score based on data freshness (fresher data gets higher score)
            freshness_scores = []
            for hours_old in timeliness["data_freshness"].values():
                # Score decreases as data gets older
                freshness_score = max(0.0, 1.0 - (hours_old / 168))  # 1 week = 168 hours
                freshness_scores.append(freshness_score)
            
            timeliness["score"] = np.mean(freshness_scores)
        else:
            timeliness["score"] = 0.5  # Neutral score if no timestamp data
        
        return timeliness
    
    def _assess_validity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data validity."""
        
        validity = {
            "format_validity": {},
            "domain_validity": {},
            "referential_integrity": {},
            "score": 0.0
        }
        
        if len(df) == 0:
            return validity
        
        # Format validity checks
        for column in df.columns:
            if column in self.config.field_types:
                expected_type = self.config.field_types[column]
                
                if expected_type == "email":
                    # Simple email validation
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    valid_emails = df[column].astype(str).str.match(email_pattern, na=False)
                    validity["format_validity"][column] = valid_emails.sum() / len(df)
                
                elif expected_type == "url":
                    # Simple URL validation
                    url_pattern = r'^https?://.+'
                    valid_urls = df[column].astype(str).str.match(url_pattern, na=False)
                    validity["format_validity"][column] = valid_urls.sum() / len(df)
                
                elif expected_type == "numeric":
                    # Numeric validation
                    numeric_values = pd.to_numeric(df[column], errors='coerce')
                    valid_numeric = numeric_values.notna()
                    validity["format_validity"][column] = valid_numeric.sum() / len(df)
        
        # Domain validity (business logic)
        # Example: Check if percentages are between 0 and 1
        percentage_columns = [col for col in df.columns if 'rate' in col.lower() or 'percentage' in col.lower()]
        for col in percentage_columns:
            if col in df.columns:
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                valid_percentages = ((numeric_col >= 0) & (numeric_col <= 1)).sum()
                validity["domain_validity"][col] = valid_percentages / len(df)
        
        # Calculate overall validity score
        all_validity_scores = list(validity["format_validity"].values()) + \
                             list(validity["domain_validity"].values())
        
        if all_validity_scores:
            validity["score"] = np.mean(all_validity_scores)
        else:
            validity["score"] = 1.0
        
        return validity
    
    def _assess_uniqueness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data uniqueness."""
        
        uniqueness = {
            "duplicate_records": 0,
            "duplicate_rate": 0.0,
            "field_uniqueness": {},
            "score": 0.0
        }
        
        if len(df) == 0:
            return uniqueness
        
        # Overall duplicate records
        duplicate_records = df.duplicated().sum()
        uniqueness["duplicate_records"] = duplicate_records
        uniqueness["duplicate_rate"] = duplicate_records / len(df)
        
        # Field-level uniqueness
        for column in df.columns:
            unique_values = df[column].nunique()
            total_values = df[column].notna().sum()
            if total_values > 0:
                uniqueness_ratio = unique_values / total_values
                uniqueness["field_uniqueness"][column] = uniqueness_ratio
        
        # Calculate uniqueness score
        uniqueness["score"] = 1.0 - uniqueness["duplicate_rate"]
        
        return uniqueness
    
    def _detect_anomalies(self, df: pd.DataFrame, data_source: str) -> Dict[str, Any]:
        """Detect anomalies in the data."""
        
        anomalies = {
            "statistical_outliers": {},
            "isolation_forest_anomalies": {},
            "anomaly_count": 0,
            "anomaly_rate": 0.0
        }
        
        if len(df) < 10:  # Need minimum data for anomaly detection
            return anomalies
        
        # Statistical outlier detection for numeric columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if df[column].notna().sum() > 5:
                values = df[column].dropna()
                z_scores = np.abs(stats.zscore(values))
                outliers = z_scores > self.config.outlier_threshold
                anomalies["statistical_outliers"][column] = outliers.sum()
        
        # Isolation Forest for multivariate anomaly detection
        if len(numeric_columns) >= 2:
            try:
                numeric_data = df[numeric_columns].dropna()
                if len(numeric_data) >= 10:
                    # Initialize or get existing anomaly detector
                    detector_key = f"{data_source}_isolation_forest"
                    if detector_key not in self.anomaly_detectors:
                        self.anomaly_detectors[detector_key] = IsolationForest(
                            contamination=self.config.contamination_rate,
                            random_state=42
                        )
                        # Fit on the data
                        self.anomaly_detectors[detector_key].fit(numeric_data)
                    
                    # Predict anomalies
                    anomaly_predictions = self.anomaly_detectors[detector_key].predict(numeric_data)
                    anomaly_count = (anomaly_predictions == -1).sum()
                    anomalies["isolation_forest_anomalies"]["count"] = anomaly_count
                    anomalies["isolation_forest_anomalies"]["rate"] = anomaly_count / len(numeric_data)
            
            except Exception as e:
                logger.warning(f"Isolation forest anomaly detection failed: {e}")
        
        # Calculate total anomaly metrics
        total_outliers = sum(anomalies["statistical_outliers"].values())
        isolation_anomalies = anomalies["isolation_forest_anomalies"].get("count", 0)
        
        anomalies["anomaly_count"] = total_outliers + isolation_anomalies
        anomalies["anomaly_rate"] = anomalies["anomaly_count"] / len(df) if len(df) > 0 else 0.0
        
        return anomalies
    
    def _detect_data_drift(self, df: pd.DataFrame, data_source: str) -> Dict[str, Any]:
        """Detect data drift compared to baseline."""
        
        drift_analysis = {
            "drift_detected": False,
            "drift_score": 0.0,
            "drifted_features": [],
            "statistical_tests": {}
        }
        
        # Load baseline statistics
        baseline_key = f"{data_source}_baseline"
        if baseline_key not in self.baseline_statistics:
            # Create baseline from current data
            self.baseline_statistics[baseline_key] = self._create_baseline_statistics(df)
            self._save_baseline_statistics(baseline_key, self.baseline_statistics[baseline_key])
            return drift_analysis
        
        baseline = self.baseline_statistics[baseline_key]
        
        # Compare current data with baseline
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        drift_scores = []
        
        for column in numeric_columns:
            if column in baseline and df[column].notna().sum() > 5:
                current_values = df[column].dropna()
                baseline_mean = baseline[column]["mean"]
                baseline_std = baseline[column]["std"]
                
                # Calculate drift using statistical tests
                try:
                    # Kolmogorov-Smirnov test for distribution drift
                    baseline_sample = np.random.normal(baseline_mean, baseline_std, len(current_values))
                    ks_statistic, p_value = stats.ks_2samp(current_values, baseline_sample)
                    
                    drift_analysis["statistical_tests"][column] = {
                        "ks_statistic": ks_statistic,
                        "p_value": p_value,
                        "drift_detected": p_value < 0.05
                    }
                    
                    if p_value < 0.05:
                        drift_analysis["drifted_features"].append(column)
                        drift_scores.append(ks_statistic)
                
                except Exception as e:
                    logger.warning(f"Drift detection failed for column {column}: {e}")
        
        # Calculate overall drift score
        if drift_scores:
            drift_analysis["drift_score"] = np.mean(drift_scores)
            drift_analysis["drift_detected"] = drift_analysis["drift_score"] > self.config.drift_threshold
        
        return drift_analysis
    
    def _create_baseline_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create baseline statistics for drift detection."""
        
        baseline = {}
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if df[column].notna().sum() > 0:
                values = df[column].dropna()
                baseline[column] = {
                    "mean": float(values.mean()),
                    "std": float(values.std()),
                    "min": float(values.min()),
                    "max": float(values.max()),
                    "median": float(values.median()),
                    "count": len(values)
                }
        
        return baseline
    
    def _calculate_overall_score(self, quality_dimensions: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall quality score."""
        
        dimension_weights = {
            "completeness": 0.25,
            "consistency": 0.20,
            "accuracy": 0.25,
            "timeliness": 0.15,
            "validity": 0.10,
            "uniqueness": 0.05
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for dimension, weight in dimension_weights.items():
            if dimension in quality_dimensions:
                score = quality_dimensions[dimension].get("score", 0.0)
                weighted_score += score * weight
                total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _identify_issues(self, quality_report: Dict[str, Any]) -> List[str]:
        """Identify data quality issues."""
        
        issues = []
        dimensions = quality_report["quality_dimensions"]
        
        # Check each dimension against thresholds
        if dimensions.get("completeness", {}).get("score", 1.0) < self.config.min_completeness:
            issues.append("Data completeness below threshold")
        
        if dimensions.get("consistency", {}).get("score", 1.0) < self.config.min_consistency:
            issues.append("Data consistency issues detected")
        
        if dimensions.get("accuracy", {}).get("score", 1.0) < self.config.min_accuracy:
            issues.append("Data accuracy problems found")
        
        if dimensions.get("timeliness", {}).get("score", 1.0) < self.config.min_timeliness:
            issues.append("Data timeliness concerns")
        
        if dimensions.get("validity", {}).get("score", 1.0) < self.config.min_validity:
            issues.append("Data validity violations")
        
        # Check anomalies
        anomaly_rate = quality_report.get("anomalies", {}).get("anomaly_rate", 0.0)
        if anomaly_rate > 0.1:  # More than 10% anomalies
            issues.append(f"High anomaly rate detected: {anomaly_rate:.2%}")
        
        # Check drift
        if quality_report.get("drift_analysis", {}).get("drift_detected", False):
            issues.append("Data drift detected")
        
        return issues
    
    def _generate_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations for quality improvement."""
        
        recommendations = []
        issues = quality_report["issues_detected"]
        
        if "Data completeness below threshold" in issues:
            recommendations.append("Investigate data collection processes and fix missing data sources")
        
        if "Data consistency issues detected" in issues:
            recommendations.append("Standardize data formats and implement validation rules")
        
        if "Data accuracy problems found" in issues:
            recommendations.append("Review data validation rules and implement additional accuracy checks")
        
        if "Data timeliness concerns" in issues:
            recommendations.append("Optimize data collection frequency and reduce processing delays")
        
        if "Data validity violations" in issues:
            recommendations.append("Implement stricter input validation and data cleaning procedures")
        
        if any("anomaly rate" in issue for issue in issues):
            recommendations.append("Investigate anomalous data points and improve anomaly detection")
        
        if "Data drift detected" in issues:
            recommendations.append("Update baseline statistics and consider model retraining")
        
        return recommendations
    
    def _check_quality_alerts(self, quality_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for quality alerts that require immediate attention."""
        
        alerts = []
        overall_score = quality_report["overall_score"]
        
        if overall_score < self.config.alert_threshold:
            alerts.append({
                "alert_type": "quality_degradation",
                "severity": "high" if overall_score < 0.7 else "medium",
                "message": f"Overall data quality score dropped to {overall_score:.3f}",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check for critical issues
        if quality_report.get("drift_analysis", {}).get("drift_detected", False):
            alerts.append({
                "alert_type": "data_drift",
                "severity": "high",
                "message": "Significant data drift detected",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        anomaly_rate = quality_report.get("anomalies", {}).get("anomaly_rate", 0.0)
        if anomaly_rate > 0.2:  # More than 20% anomalies
            alerts.append({
                "alert_type": "high_anomaly_rate",
                "severity": "critical",
                "message": f"Anomaly rate exceeded 20%: {anomaly_rate:.2%}",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return alerts
    
    def _update_quality_history(self, data_source: str, quality_report: Dict[str, Any]) -> None:
        """Update quality history for trend analysis."""
        
        if data_source not in self.quality_history:
            self.quality_history[data_source] = []
        
        history_entry = {
            "timestamp": quality_report["assessment_time"],
            "overall_score": quality_report["overall_score"],
            "sample_count": quality_report["sample_count"],
            "issues_count": len(quality_report["issues_detected"]),
            "alerts_count": len(quality_report["alerts"])
        }
        
        self.quality_history[data_source].append(history_entry)
        
        # Keep only recent history
        cutoff_time = datetime.utcnow() - timedelta(days=self.config.historical_window_days)
        self.quality_history[data_source] = [
            entry for entry in self.quality_history[data_source]
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
    
    def _save_quality_report(self, quality_report: Dict[str, Any]) -> None:
        """Save quality report to file."""
        
        data_source = quality_report["data_source"]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.quality_reports_path / f"{data_source}_quality_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(quality_report, f, indent=2, default=str)
        
        # Save alerts separately if any
        if quality_report["alerts"]:
            alert_file = self.alerts_path / f"{data_source}_alerts_{timestamp}.json"
            with open(alert_file, 'w') as f:
                json.dump(quality_report["alerts"], f, indent=2, default=str)
    
    def _save_baseline_statistics(self, baseline_key: str, baseline_stats: Dict[str, Any]) -> None:
        """Save baseline statistics for drift detection."""
        
        baseline_file = self.baselines_path / f"{baseline_key}.json"
        with open(baseline_file, 'w') as f:
            json.dump(baseline_stats, f, indent=2, default=str)
    
    def get_quality_summary(self, data_source: Optional[str] = None) -> Dict[str, Any]:
        """Get quality summary for monitoring dashboard."""
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "data_sources": [],
            "overall_health": "unknown",
            "active_alerts": 0,
            "quality_trends": {}
        }
        
        if data_source:
            sources = [data_source] if data_source in self.quality_history else []
        else:
            sources = list(self.quality_history.keys())
        
        summary["data_sources"] = sources
        
        # Calculate overall health
        recent_scores = []
        total_alerts = 0
        
        for source in sources:
            history = self.quality_history[source]
            if history:
                latest_entry = history[-1]
                recent_scores.append(latest_entry["overall_score"])
                total_alerts += latest_entry["alerts_count"]
                
                # Calculate trend
                if len(history) >= 2:
                    recent_avg = np.mean([entry["overall_score"] for entry in history[-3:]])
                    older_avg = np.mean([entry["overall_score"] for entry in history[-6:-3]]) if len(history) >= 6 else recent_avg
                    trend = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"
                    summary["quality_trends"][source] = trend
        
        if recent_scores:
            avg_score = np.mean(recent_scores)
            if avg_score >= 0.9:
                summary["overall_health"] = "excellent"
            elif avg_score >= 0.8:
                summary["overall_health"] = "good"
            elif avg_score >= 0.7:
                summary["overall_health"] = "fair"
            else:
                summary["overall_health"] = "poor"
        
        summary["active_alerts"] = total_alerts
        
        return summary
