"""
Data collectors for various educational data sources.

This module contains collectors for:
- Government APIs (College Scorecard, IPEDS, Common Data Set)
- State education department APIs
- University website scrapers
- Review platform scrapers
- Summer program data sources
- Financial aid and scholarship databases
- Social media and forum content
"""

from .base_collector import BaseCollector, CollectorConfig, CollectionResult
from .government import CollegeScorecardCollector, IPEDSCollector, CommonDataSetCollector
from .state_apis import StateEducationCollector
from .web_scrapers import UniversityWebScraper, ReviewPlatformScraper
from .summer_programs import SummerProgramCollector
from .financial_aid import FinancialAidCollector
from .social_media import SocialMediaCollector, SocialMediaAuthCollector
# Enhanced authentication system collectors
from .user_auth_collector import UserAuthCollector
from .phone_verification_collector import PhoneVerificationCollector
from .security_event_collector import SecurityEventCollector
from .user_profile_collector import UserProfileCollector

__all__ = [
    "BaseCollector",
    "CollectorConfig",
    "CollectionResult",
    "CollegeScorecardCollector",
    "IPEDSCollector",
    "CommonDataSetCollector",
    "StateEducationCollector",
    "UniversityWebScraper",
    "ReviewPlatformScraper",
    "SummerProgramCollector",
    "FinancialAidCollector",
    "SocialMediaCollector",
    # Enhanced authentication collectors
    "SocialMediaAuthCollector",
    "UserAuthCollector",
    "PhoneVerificationCollector",
    "SecurityEventCollector",
    "UserProfileCollector",
]
