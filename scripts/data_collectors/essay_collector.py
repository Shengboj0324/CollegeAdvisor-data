#!/usr/bin/env python3
"""
📝 ESSAY COLLECTOR - COLLEGE APPLICATION ESSAYS
================================================

Collects successful college application essays from multiple sources:
- Johns Hopkins "Essays That Worked"
- CollegeVine Essay Examples
- College Essay Guy
- Shemmassian Consulting

Author: Augment Agent
Date: 2025-10-18
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.data_collectors.base_collector import BaseCollector, CollectedData
from datetime import datetime
import re

class EssayCollector(BaseCollector):
    """Collector for college application essays."""
    
    def __init__(self, output_dir: Path = None):
        if output_dir is None:
            output_dir = Path("data/collected/essays")
        
        super().__init__(
            source_name="College Essays",
            output_dir=output_dir,
            rate_limit_seconds=2.0  # Be respectful
        )
        
        # Define sources
        self.sources = {
            'jhu': {
                'name': 'Johns Hopkins Essays That Worked',
                'url': 'https://apply.jhu.edu/college-planning-guide/essays-that-worked/',
                'parser': self._parse_jhu_essays
            },
            'collegevine': {
                'name': 'CollegeVine Essay Examples',
                'url': 'https://blog.collegevine.com/common-app-essay-examples',
                'parser': self._parse_collegevine_essays
            },
            'essayguy': {
                'name': 'College Essay Guy Examples',
                'url': 'https://www.collegeessayguy.com/blog/college-essay-examples',
                'parser': self._parse_essayguy_essays
            },
            'shemmassian': {
                'name': 'Shemmassian Essay Examples',
                'url': 'https://www.shemmassianconsulting.com/blog/college-essay-examples',
                'parser': self._parse_shemmassian_essays
            }
        }
    
    def _parse_jhu_essays(self, soup) -> List[CollectedData]:
        """Parse Johns Hopkins essays."""
        essays = []
        
        try:
            # Find essay containers
            # Note: This is a template - actual selectors need to be verified
            essay_sections = soup.find_all(['div', 'article'], class_=re.compile(r'essay|content'))
            
            for section in essay_sections:
                # Extract essay text
                essay_text = section.get_text(strip=True)
                
                if len(essay_text) < 200:  # Skip if too short
                    continue
                
                # Extract title if available
                title_elem = section.find(['h1', 'h2', 'h3', 'h4'])
                title = title_elem.get_text(strip=True) if title_elem else "JHU Essay Example"
                
                # Create collected data
                data = CollectedData(
                    source="Johns Hopkins Essays That Worked",
                    url=self.sources['jhu']['url'],
                    title=title,
                    content=essay_text,
                    category="college_essay",
                    metadata={
                        'source_type': 'successful_essay',
                        'institution': 'Johns Hopkins University',
                        'essay_type': 'application_essay'
                    },
                    collected_at=datetime.now().isoformat(),
                    content_hash=self._compute_hash(essay_text)
                )
                
                essays.append(data)
        
        except Exception as e:
            self.logger.error(f"Error parsing JHU essays: {e}")
            self.stats.errors.append(f"JHU parsing error: {e}")
        
        return essays
    
    def _parse_collegevine_essays(self, soup) -> List[CollectedData]:
        """Parse CollegeVine essays."""
        essays = []
        
        try:
            # Find essay examples in blog post
            # Look for blockquotes or specific essay containers
            essay_blocks = soup.find_all(['blockquote', 'div'], class_=re.compile(r'essay|example'))
            
            for block in essay_blocks:
                essay_text = block.get_text(strip=True)
                
                if len(essay_text) < 200:
                    continue
                
                # Try to find associated title/prompt
                prev_heading = block.find_previous(['h2', 'h3', 'h4'])
                title = prev_heading.get_text(strip=True) if prev_heading else "CollegeVine Essay Example"
                
                data = CollectedData(
                    source="CollegeVine Essay Examples",
                    url=self.sources['collegevine']['url'],
                    title=title,
                    content=essay_text,
                    category="college_essay",
                    metadata={
                        'source_type': 'successful_essay',
                        'platform': 'CollegeVine',
                        'essay_type': 'common_app'
                    },
                    collected_at=datetime.now().isoformat(),
                    content_hash=self._compute_hash(essay_text)
                )
                
                essays.append(data)
        
        except Exception as e:
            self.logger.error(f"Error parsing CollegeVine essays: {e}")
            self.stats.errors.append(f"CollegeVine parsing error: {e}")
        
        return essays
    
    def _parse_essayguy_essays(self, soup) -> List[CollectedData]:
        """Parse College Essay Guy essays."""
        essays = []
        
        try:
            # Find essay content
            content_div = soup.find('div', class_=re.compile(r'content|entry|post'))
            
            if content_div:
                # Look for essay examples (often in specific formatting)
                essay_sections = content_div.find_all(['div', 'section'], class_=re.compile(r'essay|example'))
                
                for section in essay_sections:
                    essay_text = section.get_text(strip=True)
                    
                    if len(essay_text) < 200:
                        continue
                    
                    # Extract title
                    title_elem = section.find(['h2', 'h3', 'h4'])
                    title = title_elem.get_text(strip=True) if title_elem else "College Essay Guy Example"
                    
                    data = CollectedData(
                        source="College Essay Guy",
                        url=self.sources['essayguy']['url'],
                        title=title,
                        content=essay_text,
                        category="college_essay",
                        metadata={
                            'source_type': 'successful_essay',
                            'platform': 'College Essay Guy',
                            'essay_type': 'various'
                        },
                        collected_at=datetime.now().isoformat(),
                        content_hash=self._compute_hash(essay_text)
                    )
                    
                    essays.append(data)
        
        except Exception as e:
            self.logger.error(f"Error parsing Essay Guy essays: {e}")
            self.stats.errors.append(f"Essay Guy parsing error: {e}")
        
        return essays
    
    def _parse_shemmassian_essays(self, soup) -> List[CollectedData]:
        """Parse Shemmassian essays."""
        essays = []
        
        try:
            # Find essay content
            essay_blocks = soup.find_all(['div', 'section'], class_=re.compile(r'essay|example|content'))
            
            for block in essay_blocks:
                essay_text = block.get_text(strip=True)
                
                if len(essay_text) < 200:
                    continue
                
                # Extract title
                title_elem = block.find(['h2', 'h3', 'h4'])
                title = title_elem.get_text(strip=True) if title_elem else "Shemmassian Essay Example"
                
                data = CollectedData(
                    source="Shemmassian Consulting",
                    url=self.sources['shemmassian']['url'],
                    title=title,
                    content=essay_text,
                    category="college_essay",
                    metadata={
                        'source_type': 'successful_essay',
                        'platform': 'Shemmassian Consulting',
                        'essay_type': 'top_25_universities'
                    },
                    collected_at=datetime.now().isoformat(),
                    content_hash=self._compute_hash(essay_text)
                )
                
                essays.append(data)
        
        except Exception as e:
            self.logger.error(f"Error parsing Shemmassian essays: {e}")
            self.stats.errors.append(f"Shemmassian parsing error: {e}")
        
        return essays
    
    def collect(self) -> int:
        """Collect essays from all sources."""
        total_collected = 0
        
        for source_key, source_info in self.sources.items():
            self.logger.info(f"Collecting from: {source_info['name']}")
            
            try:
                # Fetch page
                html = self._fetch_url(source_info['url'])
                if not html:
                    self.logger.warning(f"Failed to fetch: {source_info['name']}")
                    continue
                
                # Parse HTML
                soup = self._parse_html(html)
                if not soup:
                    continue
                
                # Parse essays using source-specific parser
                essays = source_info['parser'](soup)
                
                self.logger.info(f"Found {len(essays)} essays from {source_info['name']}")
                self.stats.total_items += len(essays)
                
                # Validate and save each essay
                for essay in essays:
                    if self._validate_data(essay):
                        self._save_data(essay)
                        total_collected += 1
                
            except Exception as e:
                self.logger.error(f"Error collecting from {source_info['name']}: {e}")
                self.stats.errors.append(f"{source_info['name']} error: {e}")
        
        return total_collected

def main():
    """Run essay collector."""
    collector = EssayCollector()
    stats = collector.run()
    
    print(f"\n{'='*80}")
    print(f"ESSAY COLLECTION COMPLETE")
    print(f"{'='*80}")
    print(f"Total items processed: {stats.total_items}")
    print(f"Successfully collected: {stats.successful}")
    print(f"Failed: {stats.failed}")
    print(f"Skipped (duplicates): {stats.skipped}")
    print(f"Errors: {len(stats.errors)}")
    print(f"{'='*80}\n")
    
    return 0 if stats.failed == 0 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

