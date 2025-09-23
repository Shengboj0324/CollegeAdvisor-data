"""
Base collector class and common utilities for data collection.
"""

import logging
import time
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Iterator, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import aiohttp
from asyncio_throttle import Throttler

logger = logging.getLogger(__name__)


@dataclass
class CollectorConfig:
    """Configuration for data collectors."""
    
    # Rate limiting
    requests_per_second: float = 1.0
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    
    # Retry configuration
    max_retries: int = 3
    backoff_factor: float = 1.0
    retry_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    
    # Timeout configuration
    connect_timeout: int = 10
    read_timeout: int = 30
    
    # Caching
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    cache_dir: Optional[Path] = None
    
    # Output configuration
    output_format: str = "json"  # json, csv, parquet
    batch_size: int = 100
    
    # Authentication
    api_key: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    # Data filtering
    date_range: Optional[tuple] = None  # (start_date, end_date)
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectionResult:
    """Result of a data collection operation."""
    
    collector_name: str
    source_url: str
    total_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate collection duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_records == 0:
            return 0.0
        return self.successful_records / self.total_records


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""
    
    def __init__(self, config: CollectorConfig):
        self.config = config
        self.session = self._create_session()
        self.throttler = Throttler(rate_limit=config.requests_per_second)
        self.cache_dir = config.cache_dir or Path("./cache/collectors")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=self.config.retry_status_codes,
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update(self.config.headers)
        if self.config.api_key:
            session.headers.update({"Authorization": f"Bearer {self.config.api_key}"})
            
        return session
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key."""
        return self.cache_dir / f"{self.__class__.__name__}_{cache_key}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file is valid and not expired."""
        if not cache_path.exists() or not self.config.cache_enabled:
            return False
            
        cache_age = datetime.utcnow() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        return cache_age < timedelta(hours=self.config.cache_ttl_hours)
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Load data from cache if valid."""
        cache_path = self._get_cache_path(cache_key)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    logger.info(f"Loading from cache: {cache_key}")
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache {cache_key}: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Save data to cache."""
        if not self.config.cache_enabled:
            return
            
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug(f"Saved to cache: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_key}: {e}")
    
    async def _make_request(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make a rate-limited HTTP request."""
        async with self.throttler:
            try:
                response = self.session.get(
                    url, 
                    timeout=(self.config.connect_timeout, self.config.read_timeout),
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {url}: {e}")
                raise
    
    @abstractmethod
    def collect(self, **kwargs) -> CollectionResult:
        """Collect data from the source."""
        pass
    
    @abstractmethod
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the data source."""
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate collected data."""
        # Basic validation - subclasses should override
        return data is not None and len(data) > 0
    
    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw data to standard format."""
        # Basic transformation - subclasses should override
        return raw_data
    
    def save_results(self, result: CollectionResult, output_path: Path) -> None:
        """Save collection results to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.config.output_format == "json":
            with open(output_path.with_suffix('.json'), 'w') as f:
                json.dump(result.__dict__, f, indent=2, default=str)
        else:
            logger.warning(f"Unsupported output format: {self.config.output_format}")
