#!/usr/bin/env python3
"""
🔧 BASE DATA COLLECTOR - PRODUCTION FRAMEWORK
==============================================

Zero-tolerance error handling framework for all data collectors.
All collectors inherit from this base class.

Author: Augment Agent
Date: 2025-10-18
"""

import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
import hashlib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class CollectedData:
    """Standard format for collected data."""
    source: str
    url: str
    title: str
    content: str
    category: str
    metadata: Dict[str, Any]
    collected_at: str
    content_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CollectionStats:
    """Statistics for collection run."""
    source_name: str
    start_time: str
    end_time: Optional[str] = None
    total_items: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class BaseCollector(ABC):
    """
    Base class for all data collectors.
    
    Provides:
    - Error handling
    - Rate limiting
    - Deduplication
    - Progress tracking
    - Data validation
    """
    
    def __init__(
        self,
        source_name: str,
        output_dir: Path,
        rate_limit_seconds: float = 1.0,
        max_retries: int = 3
    ):
        """
        Initialize collector.
        
        Args:
            source_name: Name of the data source
            output_dir: Directory to save collected data
            rate_limit_seconds: Seconds to wait between requests
            max_retries: Maximum number of retries for failed requests
        """
        self.source_name = source_name
        self.output_dir = Path(output_dir)
        self.rate_limit_seconds = rate_limit_seconds
        self.max_retries = max_retries
        
        # Setup logging
        self.logger = logging.getLogger(f"collector.{source_name}")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize stats
        self.stats = CollectionStats(
            source_name=source_name,
            start_time=datetime.now().isoformat()
        )
        
        # Track seen content (deduplication)
        self.seen_hashes = set()
        
        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def _compute_hash(self, content: str) -> str:
        """Compute hash of content for deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _is_duplicate(self, content: str) -> bool:
        """Check if content has been seen before."""
        content_hash = self._compute_hash(content)
        if content_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(content_hash)
        return False
    
    def _rate_limit(self):
        """Apply rate limiting."""
        time.sleep(self.rate_limit_seconds)
    
    def _fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch URL with retries and error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    self.stats.errors.append(f"Failed to fetch {url}: {e}")
                    return None
        return None
    
    def _parse_html(self, html: str) -> Optional[BeautifulSoup]:
        """
        Parse HTML with error handling.
        
        Args:
            html: HTML content
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            self.logger.error(f"Failed to parse HTML: {e}")
            self.stats.errors.append(f"HTML parsing error: {e}")
            return None
    
    def _validate_data(self, data: CollectedData) -> bool:
        """
        Validate collected data.
        
        Args:
            data: Collected data to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not data.content or len(data.content) < 100:
            self.logger.warning(f"Content too short: {len(data.content)} chars")
            return False
        
        if not data.title:
            self.logger.warning("Missing title")
            return False
        
        # Check for duplicates
        if self._is_duplicate(data.content):
            self.logger.info(f"Duplicate content skipped: {data.title}")
            self.stats.skipped += 1
            return False
        
        return True
    
    def _save_data(self, data: CollectedData):
        """
        Save collected data to file.
        
        Args:
            data: Data to save
        """
        try:
            # Create filename from hash
            filename = f"{data.content_hash[:16]}.json"
            filepath = self.output_dir / filename
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved: {data.title}")
            self.stats.successful += 1
            
        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
            self.stats.errors.append(f"Save error: {e}")
            self.stats.failed += 1
    
    def _save_stats(self):
        """Save collection statistics."""
        try:
            self.stats.end_time = datetime.now().isoformat()
            stats_file = self.output_dir / "collection_stats.json"
            
            with open(stats_file, 'w') as f:
                json.dump(self.stats.to_dict(), f, indent=2)
            
            self.logger.info(f"Stats saved to: {stats_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save stats: {e}")
    
    @abstractmethod
    def collect(self) -> int:
        """
        Collect data from source.
        
        Must be implemented by subclasses.
        
        Returns:
            Number of items successfully collected
        """
        pass
    
    def run(self) -> CollectionStats:
        """
        Run the collector.
        
        Returns:
            Collection statistics
        """
        self.logger.info(f"="*80)
        self.logger.info(f"Starting collection: {self.source_name}")
        self.logger.info(f"="*80)
        
        try:
            # Run collection
            collected = self.collect()
            
            # Save stats
            self._save_stats()
            
            # Log summary
            self.logger.info(f"="*80)
            self.logger.info(f"Collection complete: {self.source_name}")
            self.logger.info(f"Total items: {self.stats.total_items}")
            self.logger.info(f"Successful: {self.stats.successful}")
            self.logger.info(f"Failed: {self.stats.failed}")
            self.logger.info(f"Skipped: {self.stats.skipped}")
            self.logger.info(f"="*80)
            
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Collection failed: {e}")
            self.stats.errors.append(f"Fatal error: {e}")
            self._save_stats()
            raise

