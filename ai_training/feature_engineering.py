"""
User Behavior Feature Engineering for AI Model Training.

This module implements advanced feature extraction from user interactions,
authentication patterns, and personalization data to create rich features
for AI model training and personalization.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """Configuration for feature engineering."""
    
    # Temporal features
    time_window_days: int = 30
    session_timeout_minutes: int = 30
    
    # Behavioral features
    min_interactions: int = 5
    engagement_percentiles: List[float] = None
    
    # Text features
    max_text_features: int = 1000
    min_text_frequency: int = 2
    
    # Normalization
    normalize_numerical: bool = True
    handle_outliers: bool = True
    outlier_threshold: float = 3.0
    
    def __post_init__(self):
        if self.engagement_percentiles is None:
            self.engagement_percentiles = [0.25, 0.5, 0.75, 0.9, 0.95]


class UserBehaviorFeatureEngineer:
    """
    Advanced feature engineering for user behavior analysis and AI personalization.
    
    This class extracts meaningful features from user authentication data,
    interaction patterns, and behavioral signals for AI model training.
    """
    
    def __init__(self, config: FeatureConfig):
        self.config = config
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=config.max_text_features,
            min_df=config.min_text_frequency,
            stop_words='english'
        )
        
    def extract_user_features(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract comprehensive user behavior features.
        
        Args:
            user_data: Raw user data from collectors
            
        Returns:
            Dictionary of extracted features
        """
        logger.info("Extracting user behavior features")
        
        features = {
            "authentication_features": {},
            "engagement_features": {},
            "preference_features": {},
            "temporal_features": {},
            "behavioral_patterns": {},
            "personalization_signals": {}
        }
        
        try:
            # Extract authentication behavior features
            if "user_auth" in user_data:
                features["authentication_features"] = self._extract_auth_features(user_data["user_auth"])
            
            # Extract engagement and interaction features
            if "user_profiles" in user_data:
                features["engagement_features"] = self._extract_engagement_features(user_data["user_profiles"])
            
            # Extract preference and interest features
            if "user_profiles" in user_data:
                features["preference_features"] = self._extract_preference_features(user_data["user_profiles"])
            
            # Extract temporal behavior patterns
            features["temporal_features"] = self._extract_temporal_features(user_data)
            
            # Extract advanced behavioral patterns
            features["behavioral_patterns"] = self._extract_behavioral_patterns(user_data)
            
            # Extract personalization signals
            features["personalization_signals"] = self._extract_personalization_signals(user_data)
            
            logger.info(f"Extracted {len(features)} feature categories")
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            
        return features
    
    def _extract_auth_features(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract authentication behavior features."""
        
        auth_features = {
            "login_frequency": 0.0,
            "success_rate": 0.0,
            "preferred_auth_methods": [],
            "device_diversity": 0.0,
            "security_score": 0.0,
            "mfa_usage": 0.0,
            "session_patterns": {}
        }
        
        try:
            data = auth_data.get("data", [])
            
            for record in data:
                if record.get("data_type") == "authentication_events":
                    events = record.get("events", [])
                    
                    if events:
                        # Calculate success rate
                        successful_logins = sum(1 for event in events if event.get("success", False))
                        auth_features["success_rate"] = successful_logins / len(events)
                        
                        # Extract authentication methods
                        methods = [event.get("authentication_method", "") for event in events]
                        auth_features["preferred_auth_methods"] = list(set(methods))
                        
                        # Calculate device diversity
                        devices = [event.get("device_type", "") for event in events]
                        auth_features["device_diversity"] = len(set(devices)) / len(devices) if devices else 0
                
                elif record.get("data_type") == "authentication_method_analytics":
                    analytics = record.get("analytics", {})
                    
                    # MFA usage
                    mfa_stats = analytics.get("mfa_usage", {})
                    auth_features["mfa_usage"] = mfa_stats.get("enabled_users_percentage", 0.0)
                    
                    # Security score based on method preferences
                    method_security = {
                        "email_password": 0.6,
                        "phone_verification": 0.8,
                        "social_signin": 0.7,
                        "mfa": 1.0
                    }
                    
                    methods_used = analytics.get("method_usage", {})
                    weighted_security = sum(
                        method_security.get(method, 0.5) * usage 
                        for method, usage in methods_used.items()
                    )
                    auth_features["security_score"] = weighted_security
        
        except Exception as e:
            logger.error(f"Authentication feature extraction failed: {e}")
        
        return auth_features
    
    def _extract_engagement_features(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user engagement and interaction features."""
        
        engagement_features = {
            "session_duration_avg": 0.0,
            "session_frequency": 0.0,
            "feature_adoption_rate": 0.0,
            "retention_score": 0.0,
            "engagement_depth": 0.0,
            "platform_preference": "",
            "usage_patterns": {}
        }
        
        try:
            data = profile_data.get("data", [])
            
            for record in data:
                if record.get("data_type") == "engagement_patterns":
                    metrics = record.get("engagement_metrics", {})
                    
                    # Session metrics
                    engagement_features["session_duration_avg"] = metrics.get("average_session_duration", 0.0)
                    engagement_features["session_frequency"] = metrics.get("sessions_per_user", 0.0)
                    
                    # Retention metrics
                    retention_rates = metrics.get("retention_rates", {})
                    if retention_rates:
                        # Calculate weighted retention score
                        weights = {"day_1": 0.1, "day_7": 0.3, "day_30": 0.6}
                        retention_score = sum(
                            weights.get(period, 0.0) * rate 
                            for period, rate in retention_rates.items()
                        )
                        engagement_features["retention_score"] = retention_score
                    
                    # Feature usage analysis
                    feature_usage = record.get("feature_usage", {})
                    if feature_usage:
                        engagement_features["feature_adoption_rate"] = np.mean(list(feature_usage.values()))
                        engagement_features["usage_patterns"] = feature_usage
                
                elif record.get("data_type") == "platform_usage":
                    platform_breakdown = record.get("platform_breakdown", {})
                    
                    # Determine platform preference
                    if platform_breakdown:
                        preferred_platform = max(platform_breakdown.keys(), 
                                               key=lambda x: platform_breakdown[x].get("engagement_time", 0))
                        engagement_features["platform_preference"] = preferred_platform
                    
                    # Calculate engagement depth
                    ios_metrics = platform_breakdown.get("ios", {})
                    engagement_features["engagement_depth"] = ios_metrics.get("engagement_time", 0.0)
        
        except Exception as e:
            logger.error(f"Engagement feature extraction failed: {e}")
        
        return engagement_features
    
    def _extract_preference_features(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user preference and interest features."""
        
        preference_features = {
            "educational_interests": {},
            "location_preferences": {},
            "program_type_preferences": {},
            "preference_diversity": 0.0,
            "preference_strength": 0.0,
            "goal_clarity": 0.0
        }
        
        try:
            data = profile_data.get("data", [])
            
            for record in data:
                if record.get("data_type") == "user_preferences":
                    preferences = record.get("preferences", {})
                    
                    # Extract preference categories
                    preference_features["educational_interests"] = preferences.get("educational_interests", {})
                    preference_features["location_preferences"] = preferences.get("location_preferences", {})
                    preference_features["program_type_preferences"] = preferences.get("program_types", {})
                    
                    # Calculate preference diversity (entropy-like measure)
                    all_prefs = []
                    for pref_category in preferences.values():
                        if isinstance(pref_category, dict):
                            all_prefs.extend(pref_category.values())
                    
                    if all_prefs:
                        # Normalize preferences
                        total = sum(all_prefs)
                        normalized_prefs = [p / total for p in all_prefs if total > 0]
                        
                        # Calculate diversity (higher = more diverse interests)
                        preference_features["preference_diversity"] = -sum(
                            p * np.log(p + 1e-10) for p in normalized_prefs
                        )
                        
                        # Calculate preference strength (how concentrated preferences are)
                        preference_features["preference_strength"] = max(normalized_prefs) if normalized_prefs else 0.0
                
                elif record.get("data_type") == "educational_goals":
                    goals = record.get("goals_analytics", {})
                    
                    # Calculate goal clarity based on profile completion
                    completion_metrics = record.get("goal_completion", {})
                    preference_features["goal_clarity"] = completion_metrics.get("average_profile_completion", 0.0)
        
        except Exception as e:
            logger.error(f"Preference feature extraction failed: {e}")
        
        return preference_features
    
    def _extract_temporal_features(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract temporal behavior patterns."""
        
        temporal_features = {
            "activity_time_patterns": {},
            "weekly_patterns": {},
            "seasonal_patterns": {},
            "recency_score": 0.0,
            "consistency_score": 0.0
        }
        
        try:
            # Extract timestamps from various data sources
            timestamps = []
            
            for source, data in user_data.items():
                if isinstance(data, dict) and "data" in data:
                    for record in data["data"]:
                        if isinstance(record, dict):
                            # Look for timestamp fields
                            for key, value in record.items():
                                if "timestamp" in key.lower() or "time" in key.lower():
                                    if isinstance(value, str):
                                        try:
                                            ts = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                            timestamps.append(ts)
                                        except:
                                            pass
            
            if timestamps:
                # Calculate recency score (how recent is the latest activity)
                latest_activity = max(timestamps)
                days_since_activity = (datetime.now() - latest_activity.replace(tzinfo=None)).days
                temporal_features["recency_score"] = max(0, 1 - days_since_activity / 30)
                
                # Analyze time patterns
                hours = [ts.hour for ts in timestamps]
                weekdays = [ts.weekday() for ts in timestamps]
                
                # Activity time patterns (hourly distribution)
                hour_counts = np.bincount(hours, minlength=24)
                temporal_features["activity_time_patterns"] = {
                    f"hour_{i}": count / len(hours) for i, count in enumerate(hour_counts)
                }
                
                # Weekly patterns
                weekday_counts = np.bincount(weekdays, minlength=7)
                temporal_features["weekly_patterns"] = {
                    f"weekday_{i}": count / len(weekdays) for i, count in enumerate(weekday_counts)
                }
                
                # Calculate consistency score (how regular is the activity)
                if len(timestamps) > 1:
                    time_diffs = [(timestamps[i] - timestamps[i-1]).total_seconds() / 3600 
                                 for i in range(1, len(timestamps))]
                    consistency = 1 / (1 + np.std(time_diffs)) if time_diffs else 0
                    temporal_features["consistency_score"] = min(1.0, consistency)
        
        except Exception as e:
            logger.error(f"Temporal feature extraction failed: {e}")
        
        return temporal_features
    
    def _extract_behavioral_patterns(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract advanced behavioral patterns and user segments."""
        
        behavioral_features = {
            "user_segment": "",
            "exploration_score": 0.0,
            "decision_speed": 0.0,
            "social_influence": 0.0,
            "risk_tolerance": 0.0,
            "information_seeking": 0.0
        }
        
        try:
            # Analyze social authentication patterns
            if "social_auth" in user_data:
                social_data = user_data["social_auth"].get("data", [])
                
                for record in social_data:
                    if record.get("data_type") == "oauth_usage_stats":
                        providers = record.get("providers", {})
                        
                        # Social influence score based on social auth usage
                        total_usage = sum(provider.get("usage_percentage", 0) for provider in providers.values())
                        behavioral_features["social_influence"] = min(1.0, total_usage)
            
            # Analyze security behavior for risk tolerance
            if "security_events" in user_data:
                security_data = user_data["security_events"].get("data", [])
                
                for record in security_data:
                    if record.get("data_type") == "failed_login_attempts":
                        metrics = record.get("metrics", {})
                        
                        # Risk tolerance based on security behavior
                        failure_rate = metrics.get("total_failed_attempts", 0) / max(1, metrics.get("unique_users_affected", 1))
                        behavioral_features["risk_tolerance"] = max(0, 1 - failure_rate / 10)
            
            # Analyze exploration behavior from user profiles
            if "user_profiles" in user_data:
                profile_data = user_data["user_profiles"].get("data", [])
                
                for record in profile_data:
                    if record.get("data_type") == "user_preferences":
                        preferences = record.get("preferences", {})
                        
                        # Exploration score based on preference diversity
                        all_categories = len([cat for cat in preferences.values() if isinstance(cat, dict)])
                        behavioral_features["exploration_score"] = min(1.0, all_categories / 5)
                    
                    elif record.get("data_type") == "engagement_patterns":
                        feature_usage = record.get("feature_usage", {})
                        
                        # Information seeking based on feature usage
                        info_features = ["university_search", "program_comparison", "recommendation_engine"]
                        info_usage = np.mean([feature_usage.get(feature, 0) for feature in info_features])
                        behavioral_features["information_seeking"] = info_usage
            
            # Determine user segment based on behavioral patterns
            behavioral_features["user_segment"] = self._classify_user_segment(behavioral_features)
        
        except Exception as e:
            logger.error(f"Behavioral pattern extraction failed: {e}")
        
        return behavioral_features
    
    def _extract_personalization_signals(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract signals for AI personalization."""
        
        personalization_signals = {
            "recommendation_receptivity": 0.0,
            "content_preferences": {},
            "interaction_style": "",
            "personalization_effectiveness": 0.0,
            "feature_affinity": {},
            "learning_style": ""
        }
        
        try:
            # Analyze recommendation effectiveness
            if "user_profiles" in user_data:
                profile_data = user_data["user_profiles"].get("data", [])
                
                for record in profile_data:
                    if record.get("data_type") == "personalization_metrics":
                        rec_performance = record.get("recommendation_performance", {})
                        
                        # Recommendation receptivity
                        ctr = rec_performance.get("click_through_rate", 0)
                        conversion = rec_performance.get("conversion_rate", 0)
                        satisfaction = rec_performance.get("user_satisfaction", 0) / 5.0  # Normalize to 0-1
                        
                        personalization_signals["recommendation_receptivity"] = np.mean([ctr, conversion, satisfaction])
                        personalization_signals["personalization_effectiveness"] = rec_performance.get("recommendation_accuracy", 0)
                        
                        # Feature affinity analysis
                        features = record.get("personalization_features", {})
                        for feature_name, feature_data in features.items():
                            effectiveness = feature_data.get("effectiveness", 0)
                            usage = feature_data.get("usage_rate", 0)
                            personalization_signals["feature_affinity"][feature_name] = np.mean([effectiveness, usage])
            
            # Determine interaction style and learning preferences
            personalization_signals["interaction_style"] = self._classify_interaction_style(user_data)
            personalization_signals["learning_style"] = self._classify_learning_style(user_data)
        
        except Exception as e:
            logger.error(f"Personalization signal extraction failed: {e}")
        
        return personalization_signals
    
    def _classify_user_segment(self, behavioral_features: Dict[str, Any]) -> str:
        """Classify user into behavioral segments."""
        
        exploration = behavioral_features.get("exploration_score", 0)
        social_influence = behavioral_features.get("social_influence", 0)
        info_seeking = behavioral_features.get("information_seeking", 0)
        
        if exploration > 0.7 and info_seeking > 0.6:
            return "explorer"
        elif social_influence > 0.6:
            return "social_follower"
        elif info_seeking > 0.8:
            return "researcher"
        elif exploration < 0.3 and info_seeking < 0.4:
            return "casual_browser"
        else:
            return "balanced_user"
    
    def _classify_interaction_style(self, user_data: Dict[str, Any]) -> str:
        """Classify user interaction style."""
        
        # Analyze engagement patterns to determine interaction style
        try:
            if "user_profiles" in user_data:
                for record in user_data["user_profiles"].get("data", []):
                    if record.get("data_type") == "engagement_patterns":
                        metrics = record.get("engagement_metrics", {})
                        session_duration = metrics.get("average_session_duration", 0)
                        sessions_per_user = metrics.get("sessions_per_user", 0)
                        
                        if session_duration > 20 and sessions_per_user < 3:
                            return "deep_diver"
                        elif session_duration < 10 and sessions_per_user > 5:
                            return "quick_scanner"
                        else:
                            return "balanced_explorer"
        except:
            pass
        
        return "unknown"
    
    def _classify_learning_style(self, user_data: Dict[str, Any]) -> str:
        """Classify user learning style preferences."""
        
        # Analyze feature usage to infer learning style
        try:
            if "user_profiles" in user_data:
                for record in user_data["user_profiles"].get("data", []):
                    if record.get("data_type") == "engagement_patterns":
                        feature_usage = record.get("feature_usage", {})
                        
                        comparison_usage = feature_usage.get("program_comparison", 0)
                        search_usage = feature_usage.get("university_search", 0)
                        recommendation_usage = feature_usage.get("recommendation_engine", 0)
                        
                        if comparison_usage > 0.7:
                            return "analytical"
                        elif recommendation_usage > 0.7:
                            return "guided"
                        elif search_usage > 0.8:
                            return "self_directed"
                        else:
                            return "mixed"
        except:
            pass
        
        return "unknown"
