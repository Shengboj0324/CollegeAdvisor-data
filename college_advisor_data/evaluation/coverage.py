"""Coverage analysis for data completeness and distribution."""

import logging
import numpy as np
from typing import Dict, List, Any, Set, Tuple
from collections import Counter, defaultdict
import re

from ..storage.chroma_client import ChromaDBClient
from ..config import config

logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """Analyze data coverage across multiple dimensions."""
    
    def __init__(self):
        self.chroma_client = ChromaDBClient()
    
    def analyze_comprehensive_coverage(self, collection_name: str = None) -> Dict[str, Any]:
        """Perform comprehensive coverage analysis."""
        logger.info("Analyzing comprehensive data coverage")
        
        analysis = {
            "university_coverage": self.analyze_university_coverage(collection_name),
            "geographic_coverage": self.analyze_geographic_coverage(collection_name),
            "subject_coverage": self.analyze_subject_coverage(collection_name),
            "program_level_coverage": self.analyze_program_level_coverage(collection_name),
            "temporal_coverage": self.analyze_temporal_coverage(collection_name),
            "admission_requirements_coverage": self.analyze_admission_coverage(collection_name)
        }
        
        # Calculate overall coverage score
        scores = []
        for category, category_analysis in analysis.items():
            if isinstance(category_analysis, dict) and 'coverage_score' in category_analysis:
                scores.append(category_analysis['coverage_score'])
        
        analysis['overall_coverage_score'] = np.mean(scores) if scores else 0.0
        
        return analysis
    
    def analyze_university_coverage(self, collection_name: str = None) -> Dict[str, Any]:
        """Analyze coverage of universities and institutions."""
        try:
            # Get all documents with metadata
            total_docs = self.chroma_client.get_collection_count(collection_name)
            if total_docs == 0:
                return {"error": "No documents in collection", "coverage_score": 0.0}
            
            # Sample documents for analysis
            sample_size = min(1000, total_docs)
            sample_results = self.chroma_client.collection.get(
                limit=sample_size,
                include=["metadatas", "documents"]
            )
            
            universities = set()
            university_types = Counter()
            programs_per_university = defaultdict(set)
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    uni_name = metadata.get('university_name')
                    if uni_name:
                        universities.add(uni_name)
                        
                        # Track university types
                        uni_type = metadata.get('university_type', 'unknown')
                        university_types[uni_type] += 1
                        
                        # Track programs per university
                        program = metadata.get('program_name')
                        if program:
                            programs_per_university[uni_name].add(program)
            
            # Calculate metrics
            avg_programs_per_uni = np.mean([len(programs) for programs in programs_per_university.values()]) if programs_per_university else 0
            
            # Estimate coverage based on known major universities (simplified)
            major_universities = {
                'MIT', 'Stanford', 'Harvard', 'UC Berkeley', 'Carnegie Mellon',
                'Caltech', 'Princeton', 'Yale', 'Columbia', 'University of Chicago'
            }
            
            major_uni_coverage = len(universities.intersection(major_universities)) / len(major_universities)
            
            coverage_analysis = {
                "total_universities": len(universities),
                "university_types": dict(university_types),
                "avg_programs_per_university": avg_programs_per_uni,
                "major_university_coverage": major_uni_coverage,
                "sample_size": sample_size,
                "coverage_score": min(len(universities) / 100, 1.0) * 0.7 + major_uni_coverage * 0.3
            }
            
            return coverage_analysis
        
        except Exception as e:
            logger.error(f"Error analyzing university coverage: {e}")
            return {"error": str(e), "coverage_score": 0.0}
    
    def analyze_geographic_coverage(self, collection_name: str = None) -> Dict[str, Any]:
        """Analyze geographic distribution of institutions."""
        try:
            total_docs = self.chroma_client.get_collection_count(collection_name)
            sample_size = min(1000, total_docs)
            
            sample_results = self.chroma_client.collection.get(
                limit=sample_size,
                include=["metadatas"]
            )
            
            states = set()
            cities = set()
            regions = defaultdict(int)
            
            # US state abbreviations for region mapping
            state_regions = {
                'CA': 'West', 'OR': 'West', 'WA': 'West', 'NV': 'West', 'AZ': 'West',
                'TX': 'South', 'FL': 'South', 'GA': 'South', 'NC': 'South', 'VA': 'South',
                'NY': 'Northeast', 'MA': 'Northeast', 'CT': 'Northeast', 'PA': 'Northeast',
                'IL': 'Midwest', 'OH': 'Midwest', 'MI': 'Midwest', 'IN': 'Midwest'
            }
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    location = metadata.get('location', '')
                    if location:
                        # Extract state from location string
                        state_match = re.search(r'\b([A-Z]{2})\b', location)
                        if state_match:
                            state = state_match.group(1)
                            states.add(state)
                            region = state_regions.get(state, 'Other')
                            regions[region] += 1
                        
                        # Extract city
                        city_match = re.search(r'^([^,]+)', location)
                        if city_match:
                            cities.add(city_match.group(1).strip())
            
            # Calculate coverage score
            state_coverage = min(len(states) / 50, 1.0)  # 50 US states
            region_balance = 1 - np.std(list(regions.values())) / np.mean(list(regions.values())) if regions else 0
            region_balance = max(0, min(region_balance, 1))
            
            coverage_analysis = {
                "states_covered": len(states),
                "cities_covered": len(cities),
                "regional_distribution": dict(regions),
                "state_coverage_percentage": len(states) / 50 * 100,
                "regional_balance_score": region_balance,
                "coverage_score": (state_coverage * 0.7 + region_balance * 0.3)
            }
            
            return coverage_analysis
        
        except Exception as e:
            logger.error(f"Error analyzing geographic coverage: {e}")
            return {"error": str(e), "coverage_score": 0.0}
    
    def analyze_subject_coverage(self, collection_name: str = None) -> Dict[str, Any]:
        """Analyze coverage of academic subjects and fields."""
        try:
            total_docs = self.chroma_client.get_collection_count(collection_name)
            sample_size = min(1000, total_docs)
            
            sample_results = self.chroma_client.collection.get(
                limit=sample_size,
                include=["metadatas", "documents"]
            )
            
            subject_areas = Counter()
            stem_fields = set()
            liberal_arts_fields = set()
            
            # Define major subject categories
            stem_keywords = {
                'computer science', 'engineering', 'mathematics', 'physics', 'chemistry',
                'biology', 'statistics', 'data science', 'artificial intelligence'
            }
            
            liberal_arts_keywords = {
                'english', 'history', 'philosophy', 'art', 'literature', 'music',
                'theater', 'languages', 'anthropology', 'sociology'
            }
            
            if sample_results['metadatas'] and sample_results['documents']:
                for metadata, document in zip(sample_results['metadatas'], sample_results['documents']):
                    # Extract from metadata
                    subject = metadata.get('subject_area')
                    if subject:
                        subject_areas[subject.lower()] += 1
                    
                    # Extract from document content
                    content_lower = document.lower()
                    
                    for stem_field in stem_keywords:
                        if stem_field in content_lower:
                            stem_fields.add(stem_field)
                    
                    for liberal_field in liberal_arts_keywords:
                        if liberal_field in content_lower:
                            liberal_arts_fields.add(liberal_field)
            
            # Calculate coverage metrics
            total_subjects = len(subject_areas)
            stem_coverage = len(stem_fields) / len(stem_keywords)
            liberal_arts_coverage = len(liberal_arts_fields) / len(liberal_arts_keywords)
            
            coverage_analysis = {
                "total_subject_areas": total_subjects,
                "subject_distribution": dict(subject_areas.most_common(20)),
                "stem_fields_covered": len(stem_fields),
                "liberal_arts_fields_covered": len(liberal_arts_fields),
                "stem_coverage_percentage": stem_coverage * 100,
                "liberal_arts_coverage_percentage": liberal_arts_coverage * 100,
                "coverage_score": (stem_coverage + liberal_arts_coverage) / 2
            }
            
            return coverage_analysis
        
        except Exception as e:
            logger.error(f"Error analyzing subject coverage: {e}")
            return {"error": str(e), "coverage_score": 0.0}
    
    def analyze_program_level_coverage(self, collection_name: str = None) -> Dict[str, Any]:
        """Analyze coverage of different program levels."""
        try:
            total_docs = self.chroma_client.get_collection_count(collection_name)
            sample_size = min(1000, total_docs)
            
            sample_results = self.chroma_client.collection.get(
                limit=sample_size,
                include=["metadatas", "documents"]
            )
            
            program_levels = Counter()
            degree_types = Counter()
            
            # Keywords for different program levels
            level_keywords = {
                'undergraduate': ['undergraduate', 'bachelor', 'bs', 'ba', 'bsc'],
                'graduate': ['graduate', 'master', 'ms', 'ma', 'msc', 'phd', 'doctorate'],
                'summer_program': ['summer program', 'summer camp', 'internship'],
                'certificate': ['certificate', 'certification', 'diploma']
            }
            
            if sample_results['metadatas'] and sample_results['documents']:
                for metadata, document in zip(sample_results['metadatas'], sample_results['documents']):
                    # Extract from metadata
                    program_type = metadata.get('program_type')
                    if program_type:
                        program_levels[program_type.lower()] += 1
                    
                    # Extract from document content
                    content_lower = document.lower()
                    
                    for level, keywords in level_keywords.items():
                        for keyword in keywords:
                            if keyword in content_lower:
                                program_levels[level] += 1
                                break
            
            # Calculate coverage score
            expected_levels = ['undergraduate', 'graduate', 'summer_program', 'certificate']
            covered_levels = sum(1 for level in expected_levels if program_levels.get(level, 0) > 0)
            level_coverage = covered_levels / len(expected_levels)
            
            coverage_analysis = {
                "program_level_distribution": dict(program_levels),
                "levels_covered": covered_levels,
                "total_expected_levels": len(expected_levels),
                "level_coverage_percentage": level_coverage * 100,
                "coverage_score": level_coverage
            }
            
            return coverage_analysis
        
        except Exception as e:
            logger.error(f"Error analyzing program level coverage: {e}")
            return {"error": str(e), "coverage_score": 0.0}
    
    def analyze_temporal_coverage(self, collection_name: str = None) -> Dict[str, Any]:
        """Analyze temporal aspects of the data."""
        try:
            total_docs = self.chroma_client.get_collection_count(collection_name)
            sample_size = min(1000, total_docs)
            
            sample_results = self.chroma_client.collection.get(
                limit=sample_size,
                include=["metadatas", "documents"]
            )
            
            years_mentioned = set()
            deadlines = []
            durations = Counter()
            
            if sample_results['metadatas'] and sample_results['documents']:
                for metadata, document in zip(sample_results['metadatas'], sample_results['documents']):
                    # Extract years from content
                    year_matches = re.findall(r'\b(20\d{2})\b', document)
                    years_mentioned.update(year_matches)
                    
                    # Extract duration information
                    duration = metadata.get('duration')
                    if duration:
                        durations[duration] += 1
                    
                    # Look for deadline patterns
                    deadline_patterns = [
                        r'deadline[:\s]+([a-z]+ \d{1,2})',
                        r'apply by[:\s]+([a-z]+ \d{1,2})',
                        r'due[:\s]+([a-z]+ \d{1,2})'
                    ]
                    
                    for pattern in deadline_patterns:
                        matches = re.findall(pattern, document.lower())
                        deadlines.extend(matches)
            
            # Calculate temporal coverage
            current_year = 2024
            recent_years = [str(year) for year in range(current_year - 2, current_year + 3)]
            recent_coverage = len(years_mentioned.intersection(recent_years)) / len(recent_years)
            
            coverage_analysis = {
                "years_mentioned": sorted(list(years_mentioned)),
                "recent_year_coverage": recent_coverage,
                "deadline_mentions": len(deadlines),
                "duration_distribution": dict(durations),
                "coverage_score": recent_coverage
            }
            
            return coverage_analysis
        
        except Exception as e:
            logger.error(f"Error analyzing temporal coverage: {e}")
            return {"error": str(e), "coverage_score": 0.0}
    
    def analyze_admission_coverage(self, collection_name: str = None) -> Dict[str, Any]:
        """Analyze coverage of admission requirements information."""
        try:
            total_docs = self.chroma_client.get_collection_count(collection_name)
            sample_size = min(1000, total_docs)
            
            sample_results = self.chroma_client.collection.get(
                limit=sample_size,
                include=["metadatas", "documents"]
            )
            
            gpa_mentions = 0
            sat_mentions = 0
            act_mentions = 0
            essay_mentions = 0
            recommendation_mentions = 0
            
            admission_keywords = {
                'gpa': ['gpa', 'grade point average'],
                'sat': ['sat', 'sat score'],
                'act': ['act', 'act score'],
                'essay': ['essay', 'personal statement', 'statement of purpose'],
                'recommendation': ['recommendation', 'letter of recommendation', 'reference']
            }
            
            if sample_results['documents']:
                for document in sample_results['documents']:
                    content_lower = document.lower()
                    
                    for category, keywords in admission_keywords.items():
                        for keyword in keywords:
                            if keyword in content_lower:
                                if category == 'gpa':
                                    gpa_mentions += 1
                                elif category == 'sat':
                                    sat_mentions += 1
                                elif category == 'act':
                                    act_mentions += 1
                                elif category == 'essay':
                                    essay_mentions += 1
                                elif category == 'recommendation':
                                    recommendation_mentions += 1
                                break
            
            total_samples = len(sample_results['documents']) if sample_results['documents'] else 1
            
            coverage_analysis = {
                "gpa_coverage": gpa_mentions / total_samples,
                "sat_coverage": sat_mentions / total_samples,
                "act_coverage": act_mentions / total_samples,
                "essay_coverage": essay_mentions / total_samples,
                "recommendation_coverage": recommendation_mentions / total_samples,
                "total_samples": total_samples
            }
            
            # Calculate overall admission coverage score
            coverage_scores = [
                coverage_analysis["gpa_coverage"],
                coverage_analysis["sat_coverage"],
                coverage_analysis["act_coverage"],
                coverage_analysis["essay_coverage"],
                coverage_analysis["recommendation_coverage"]
            ]
            
            coverage_analysis["coverage_score"] = np.mean(coverage_scores)
            
            return coverage_analysis
        
        except Exception as e:
            logger.error(f"Error analyzing admission coverage: {e}")
            return {"error": str(e), "coverage_score": 0.0}
