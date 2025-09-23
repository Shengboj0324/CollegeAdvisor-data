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
from .social_media import SocialMediaCollector

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
]
