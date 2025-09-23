"""
Government data source collectors for educational institutions.

Includes:
- College Scorecard API
- IPEDS (Integrated Postsecondary Education Data System)
- Common Data Set
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Iterator
from pathlib import Path
import json
import pandas as pd

from .base_collector import BaseCollector, CollectorConfig, CollectionResult

logger = logging.getLogger(__name__)


class CollegeScorecardCollector(BaseCollector):
    """
    Collector for the U.S. Department of Education College Scorecard API.
    
    Provides comprehensive data on colleges and universities including:
    - Institutional characteristics
    - Student demographics
    - Academic programs
    - Financial aid
    - Earnings and employment outcomes
    - Costs and debt
    """
    
    BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
    
    # Comprehensive field mapping for all major data categories
    FIELD_GROUPS = {
        "basic": [
            "id", "school.name", "school.city", "school.state",
            "school.zip", "school.ownership", "school.locale",
            "school.latitude", "school.longitude"
        ],
        "academics": [
            "school.degrees_awarded.predominant", "school.degrees_awarded.highest",
            "school.main_campus", "school.online_only"
        ],
        "admissions": [
            "latest.admissions.admission_rate.overall",
            "latest.admissions.sat_scores.average.overall",
            "latest.admissions.sat_scores.25th_percentile.critical_reading",
            "latest.admissions.sat_scores.75th_percentile.critical_reading",
            "latest.admissions.sat_scores.25th_percentile.math",
            "latest.admissions.sat_scores.75th_percentile.math"
        ],
        "student_body": [
            "latest.student.size",
            "latest.student.demographics.race_ethnicity.white",
            "latest.student.demographics.race_ethnicity.black",
            "latest.student.demographics.race_ethnicity.hispanic",
            "latest.student.demographics.men",
            "latest.student.demographics.women"
        ],
        "costs": [
            "latest.cost.tuition.in_state",
            "latest.cost.tuition.out_of_state",
            "latest.cost.roomboard.oncampus",
            "latest.cost.attendance.academic_year"
        ],
        "aid": [
            "latest.aid.pell_grant_rate",
            "latest.aid.federal_loan_rate",
            "latest.aid.median_debt.completers.overall"
        ],
        "completion": [
            "latest.completion.completion_rate_4yr_100nt",
            "latest.completion.completion_rate_less_than_4yr_100nt"
        ],
        "earnings": [
            "latest.earnings.10_yrs_after_entry.median",
            "latest.earnings.6_yrs_after_entry.median"
        ]
    }
    
    def __init__(self, config: CollectorConfig):
        super().__init__(config)
        self.api_key = config.api_key or "DEMO_KEY"  # Default demo key
        
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the College Scorecard data source."""
        return {
            "name": "College Scorecard",
            "provider": "U.S. Department of Education",
            "url": "https://collegescorecard.ed.gov/",
            "api_url": self.BASE_URL,
            "description": "Official data on college costs, graduation rates, and post-college earnings",
            "update_frequency": "Annual",
            "coverage": "All Title IV institutions in the United States",
            "data_categories": list(self.FIELD_GROUPS.keys()),
            "total_fields": sum(len(fields) for fields in self.FIELD_GROUPS.values())
        }
    
    def collect(self, 
                years: Optional[List[int]] = None,
                states: Optional[List[str]] = None,
                field_groups: Optional[List[str]] = None,
                page_size: int = 100,
                **kwargs) -> CollectionResult:
        """
        Collect data from College Scorecard API.
        
        Args:
            years: List of academic years to collect (e.g., [2020, 2021])
            states: List of state abbreviations to filter by
            field_groups: List of field groups to include
            page_size: Number of records per API request
        """
        result = CollectionResult(
            collector_name=self.__class__.__name__,
            source_url=self.BASE_URL
        )
        
        try:
            # Determine which field groups to collect
            if field_groups is None:
                field_groups = list(self.FIELD_GROUPS.keys())
            
            # Build field list
            fields = []
            for group in field_groups:
                if group in self.FIELD_GROUPS:
                    fields.extend(self.FIELD_GROUPS[group])
            
            # Collect data for each year
            all_data = []
            years = years or [datetime.now().year - 1]  # Default to previous year
            total_api_calls = 0

            for year in years:
                logger.info(f"Collecting College Scorecard data for {year}")
                year_data, api_calls = self._collect_year_data(year, fields, states, page_size)
                all_data.extend(year_data)
                total_api_calls += api_calls
                result.successful_records += len(year_data)

            result.total_records = len(all_data)
            result.api_calls = total_api_calls
            result.metadata = {
                "years_collected": years,
                "field_groups": field_groups,
                "states_filter": states,
                "total_fields": len(fields)
            }
            
            # Save collected data
            if all_data:
                output_path = Path(f"data/raw/college_scorecard_{datetime.now().strftime('%Y%m%d')}.json")
                self._save_data(all_data, output_path)
                result.metadata["output_file"] = str(output_path)
            
        except Exception as e:
            error_msg = f"Collection failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        finally:
            result.end_time = datetime.utcnow()
        
        return result
    
    def _collect_year_data(self,
                          year: int,
                          fields: List[str],
                          states: Optional[List[str]],
                          page_size: int) -> tuple[List[Dict[str, Any]], int]:
        """Collect data for a specific year."""
        all_records = []
        page = 0
        api_calls = 0

        # Limit page size for DEMO_KEY to avoid rate limits
        if self.api_key == "DEMO_KEY":
            page_size = min(page_size, 20)  # Small pages for demo
            logger.warning("Using DEMO_KEY - limited to small page sizes to avoid rate limits")

        while True:
            # Check cache first
            cache_key = f"scorecard_{year}_{page}_{hash(tuple(fields))}"
            cached_data = self._load_from_cache(cache_key)

            if cached_data:
                page_data = cached_data
                logger.info(f"Using cached data for page {page}")
            else:
                # Build API request parameters
                params = {
                    "api_key": self.api_key,
                    "fields": ",".join(fields),
                    "_page": page,
                    "_per_page": page_size,
                    "school.operating": 1  # Only operating schools
                }

                # Add state filter if specified
                if states:
                    params["school.state"] = ",".join(states)

                # Make API request with rate limiting
                try:
                    logger.info(f"Requesting page {page} with {len(fields)} fields...")
                    response = self.session.get(self.BASE_URL, params=params)
                    api_calls += 1

                    if response.status_code == 429:
                        logger.error("Rate limit exceeded. Please get a production API key from https://api.data.gov/signup/")
                        break

                    response.raise_for_status()
                    page_data = response.json()

                    # Cache the response for future use
                    self._save_to_cache(cache_key, page_data)
                    logger.info(f"Successfully fetched and cached page {page}")

                except Exception as e:
                    logger.error(f"Failed to fetch page {page} for year {year}: {e}")
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        logger.error("Rate limit hit. Consider getting a production API key.")
                    break

            # Extract results
            if "results" not in page_data or not page_data["results"]:
                logger.info("No more results found")
                break

            records = page_data["results"]
            all_records.extend(records)

            logger.info(f"Collected page {page}: {len(records)} records (total: {len(all_records)})")

            # Check if we have more pages
            metadata = page_data.get("metadata", {})
            total_records = metadata.get("total", 0)
            per_page = metadata.get("per_page", page_size)
            current_page = metadata.get("page", page)

            logger.info(f"Metadata - Total: {total_records}, Per page: {per_page}, Current page: {current_page}")

            # Stop if we've reached the end
            if len(records) < page_size or (page + 1) * page_size >= total_records:
                logger.info("Reached end of data")
                break

            page += 1

            # Safety limit for DEMO_KEY
            if self.api_key == "DEMO_KEY" and page >= 2:
                logger.warning("Stopping at page 2 due to DEMO_KEY rate limits")
                break

        return all_records, api_calls
    
    def _save_data(self, data: List[Dict[str, Any]], output_path: Path) -> None:
        """Save collected data to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump({
                "metadata": {
                    "collector": self.__class__.__name__,
                    "collection_date": datetime.utcnow().isoformat(),
                    "total_records": len(data),
                    "source": self.get_source_info()
                },
                "data": data
            }, f, indent=2, default=str)
        
        logger.info(f"Saved {len(data)} records to {output_path}")


class IPEDSCollector(BaseCollector):
    """
    Collector for IPEDS (Integrated Postsecondary Education Data System) data.
    
    IPEDS is the primary source for data on colleges, universities, and technical 
    and vocational postsecondary institutions in the United States.
    """
    
    BASE_URL = "https://nces.ed.gov/ipeds/datacenter/api"
    
    def get_source_info(self) -> Dict[str, Any]:
        return {
            "name": "IPEDS",
            "provider": "National Center for Education Statistics",
            "description": "Comprehensive data on postsecondary institutions",
            "url": "https://nces.ed.gov/ipeds/"
        }
    
    def collect(self, **kwargs) -> CollectionResult:
        """Collect IPEDS data."""
        # Implementation will be added in next iteration
        result = CollectionResult(
            collector_name=self.__class__.__name__,
            source_url=self.BASE_URL
        )
        result.end_time = datetime.utcnow()
        return result


class CommonDataSetCollector(BaseCollector):
    """
    Collector for Common Data Set information from universities.
    
    The Common Data Set provides standardized data elements used by 
    publishers, guidance counselors, and others.
    """
    
    def get_source_info(self) -> Dict[str, Any]:
        return {
            "name": "Common Data Set",
            "provider": "Various Universities",
            "description": "Standardized institutional data format",
            "url": "https://commondataset.org/"
        }
    
    def collect(self, **kwargs) -> CollectionResult:
        """Collect Common Data Set information."""
        # Implementation will be added in next iteration
        result = CollectionResult(
            collector_name=self.__class__.__name__,
            source_url="https://commondataset.org/"
        )
        result.end_time = datetime.utcnow()
        return result
