#!/usr/bin/env python3
"""
Synthesis Layer for RAG System
Generates comparisons, decision frameworks, and recommendations while maintaining citations
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ComparisonRow:
    """Single row in a comparison table"""
    entity: str  # School, program, etc.
    attributes: Dict[str, Any]  # Key-value pairs
    citations: List[str]  # URLs for this row
    last_verified: str


@dataclass
class ComparisonTable:
    """Structured comparison table"""
    title: str
    headers: List[str]  # Column headers
    rows: List[ComparisonRow]
    footnotes: List[str]
    all_citations: List[str]


@dataclass
class DecisionNode:
    """Node in a decision tree"""
    question: str
    criteria: str
    yes_path: Optional['DecisionNode'] = None
    no_path: Optional['DecisionNode'] = None
    recommendation: Optional[str] = None
    citations: List[str] = None


@dataclass
class Recommendation:
    """Structured recommendation with caveats"""
    recommendation_text: str
    confidence_level: str  # "High", "Medium", "Low"
    trade_offs: List[str]
    caveats: List[str]
    supporting_facts: List[Dict[str, str]]  # fact + citation
    alternatives: List[str]


class SynthesisEngine:
    """
    Synthesis engine that generates:
    1. Comparison tables
    2. Decision frameworks
    3. Recommendations with caveats
    
    All outputs maintain citation traceability
    """
    
    def __init__(self):
        """Initialize synthesis engine"""
        logger.info("Synthesis engine initialized")
    
    def generate_comparison_table(
        self,
        entities: List[Dict],
        attributes: List[str],
        title: str
    ) -> ComparisonTable:
        """
        Generate side-by-side comparison table
        
        Args:
            entities: List of entities to compare (schools, programs, etc.)
            attributes: List of attributes to compare
            title: Table title
            
        Returns:
            ComparisonTable with citations
        """
        rows = []
        all_citations = set()
        
        for entity in entities:
            # Extract entity name
            entity_name = entity.get('school_name') or entity.get('program_name') or entity.get('name', 'Unknown')
            
            # Extract attributes
            attrs = {}
            citations = []

            for attr in attributes:
                value = entity.get(attr, 'N/A')

                # Parse JSON strings if needed
                if isinstance(value, str) and value not in ['N/A', '']:
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(value)
                        value = parsed
                    except:
                        # Not JSON, keep as string
                        pass

                attrs[attr] = value

            # Extract citations
            entity_citations = entity.get('citations', [])
            if isinstance(entity_citations, str):
                try:
                    entity_citations = json.loads(entity_citations)
                except:
                    entity_citations = [entity_citations] if entity_citations else []

            citations.extend(entity_citations)
            all_citations.update(entity_citations)
            
            # Create row
            row = ComparisonRow(
                entity=entity_name,
                attributes=attrs,
                citations=citations,
                last_verified=entity.get('last_verified', 'Unknown')
            )
            rows.append(row)
        
        return ComparisonTable(
            title=title,
            headers=['Entity'] + attributes,
            rows=rows,
            footnotes=[],
            all_citations=list(all_citations)
        )
    
    def format_comparison_table_markdown(self, table: ComparisonTable) -> str:
        """Format comparison table as markdown"""
        lines = [f"## {table.title}\n"]
        
        # Create header
        header = "| " + " | ".join(table.headers) + " |"
        separator = "|" + "|".join(["---" for _ in table.headers]) + "|"
        lines.append(header)
        lines.append(separator)
        
        # Create rows
        for row in table.rows:
            values = [row.entity]
            for header in table.headers[1:]:  # Skip 'Entity'
                value = row.attributes.get(header, 'N/A')
                # Format value
                if isinstance(value, bool):
                    value = "✅ Yes" if value else "❌ No"
                elif isinstance(value, float):
                    if 0 < value < 1:
                        value = f"{value*100:.1f}%"
                    else:
                        value = f"{value:.2f}"
                elif isinstance(value, int):
                    value = str(value)
                elif value is None:
                    value = "N/A"
                else:
                    value = str(value)
                values.append(value)
            
            row_str = "| " + " | ".join(values) + " |"
            lines.append(row_str)
        
        # Add citations
        if table.all_citations:
            lines.append("\n**Sources:**")
            for i, citation in enumerate(table.all_citations, 1):
                lines.append(f"{i}. {citation}")
        
        return "\n".join(lines)
    
    def generate_decision_framework(
        self,
        scenario: str,
        criteria: List[Dict[str, Any]],
        retrieved_data: List[Dict]
    ) -> DecisionNode:
        """
        Generate decision tree/framework
        
        Args:
            scenario: Decision scenario description
            criteria: List of decision criteria with thresholds
            retrieved_data: Retrieved data for decision making
            
        Returns:
            DecisionNode tree
        """
        # Build decision tree based on criteria
        root = DecisionNode(
            question=scenario,
            criteria="Start",
            citations=[]
        )
        
        # For now, create a simple linear decision tree
        # In production, this would be more sophisticated
        current = root
        
        for criterion in criteria:
            node = DecisionNode(
                question=criterion.get('question', ''),
                criteria=criterion.get('criteria', ''),
                citations=criterion.get('citations', [])
            )
            current.yes_path = node
            current = node
        
        return root
    
    def generate_recommendation(
        self,
        question: str,
        retrieved_data: List[Dict],
        user_context: Optional[Dict] = None
    ) -> Recommendation:
        """
        Generate recommendation with caveats and trade-offs
        
        Args:
            question: User's question
            retrieved_data: Retrieved data from RAG
            user_context: Optional user context (budget, preferences, etc.)
            
        Returns:
            Recommendation with citations and caveats
        """
        user_context = user_context or {}
        
        # Extract key facts from retrieved data
        supporting_facts = []
        all_citations = set()
        
        for data in retrieved_data:
            # Extract citations
            citations = data.get('citations', [])
            if isinstance(citations, str):
                try:
                    citations = json.loads(citations)
                except:
                    citations = [citations] if citations else []
            
            all_citations.update(citations)
            
            # Create supporting fact
            fact_text = self._extract_key_fact(data)
            if fact_text and citations:
                supporting_facts.append({
                    'fact': fact_text,
                    'citation': citations[0] if citations else 'Unknown'
                })
        
        # Generate recommendation based on data
        recommendation_text = self._synthesize_recommendation(
            question, retrieved_data, user_context
        )
        
        # Determine confidence level
        confidence = self._calculate_confidence(retrieved_data)
        
        # Generate trade-offs
        trade_offs = self._identify_trade_offs(retrieved_data, user_context)
        
        # Generate caveats
        caveats = self._generate_caveats(retrieved_data, user_context)
        
        # Generate alternatives
        alternatives = self._generate_alternatives(retrieved_data, user_context)
        
        return Recommendation(
            recommendation_text=recommendation_text,
            confidence_level=confidence,
            trade_offs=trade_offs,
            caveats=caveats,
            supporting_facts=supporting_facts[:10],  # Limit to top 10
            alternatives=alternatives
        )
    
    def format_recommendation_markdown(self, rec: Recommendation) -> str:
        """Format recommendation as markdown"""
        lines = [
            f"## Recommendation (Confidence: {rec.confidence_level})\n",
            rec.recommendation_text,
            "\n### Trade-offs:"
        ]
        
        for trade_off in rec.trade_offs:
            lines.append(f"- {trade_off}")
        
        lines.append("\n### Important Caveats:")
        for caveat in rec.caveats:
            lines.append(f"- ⚠️ {caveat}")
        
        if rec.alternatives:
            lines.append("\n### Alternative Options:")
            for alt in rec.alternatives:
                lines.append(f"- {alt}")
        
        lines.append("\n### Supporting Facts:")
        for fact in rec.supporting_facts:
            lines.append(f"- {fact['fact']}")
            lines.append(f"  - Source: {fact['citation']}")
        
        return "\n".join(lines)
    
    def _extract_key_fact(self, data: Dict) -> str:
        """Extract key fact from data record"""
        # Try different fields
        if 'rule' in data:
            return data['rule']
        elif 'requirement' in data:
            return data['requirement']
        elif 'details' in data:
            return data['details']
        elif 'notes' in data:
            return data['notes']
        else:
            # Construct from available fields
            school = data.get('school_name', '')
            topic = data.get('policy_topic') or data.get('major') or data.get('program_name', '')
            if school and topic:
                return f"{school}: {topic}"
        return ""
    
    def _synthesize_recommendation(
        self,
        question: str,
        data: List[Dict],
        context: Dict
    ) -> str:
        """Synthesize recommendation from data"""
        # This is a simplified version - in production would use more sophisticated logic
        
        # Check for budget constraints
        budget = context.get('budget', 0)
        
        # Check for specific preferences
        preferences = context.get('preferences', [])
        
        # Analyze data to find best matches
        # For now, return a template recommendation
        return (
            "Based on the official data retrieved, here is a data-driven recommendation. "
            "This recommendation is based on factual comparisons and your stated constraints, "
            "but the final decision should consider your personal circumstances and goals."
        )
    
    def _calculate_confidence(self, data: List[Dict]) -> str:
        """Calculate confidence level based on data quality"""
        if not data:
            return "Low"
        
        # Check data freshness
        current_year = datetime.now().year
        fresh_data = 0
        
        for record in data:
            last_verified = record.get('last_verified', '')
            if str(current_year) in last_verified or str(current_year - 1) in last_verified:
                fresh_data += 1
        
        freshness_ratio = fresh_data / len(data) if data else 0
        
        if freshness_ratio > 0.8 and len(data) >= 5:
            return "High"
        elif freshness_ratio > 0.5 and len(data) >= 3:
            return "Medium"
        else:
            return "Low"
    
    def _identify_trade_offs(self, data: List[Dict], context: Dict) -> List[str]:
        """Identify trade-offs from data"""
        trade_offs = []
        
        # Generic trade-offs based on common patterns
        trade_offs.append("Cost vs. Prestige: Lower-cost options may have less name recognition")
        trade_offs.append("Selectivity vs. Certainty: More selective programs have lower admit rates")
        trade_offs.append("Time vs. Flexibility: Accelerated programs offer less flexibility to change paths")
        
        return trade_offs
    
    def _generate_caveats(self, data: List[Dict], context: Dict) -> List[str]:
        """Generate caveats for recommendation"""
        caveats = [
            "This recommendation is based on current official data, which may change",
            "Individual circumstances (academic profile, extracurriculars, essays) significantly impact outcomes",
            "Financial aid packages vary by individual and are not guaranteed",
            "Admission rates and policies can change year-to-year",
            "This is a data-driven suggestion, not a guarantee of success or satisfaction"
        ]
        return caveats
    
    def _generate_alternatives(self, data: List[Dict], context: Dict) -> List[str]:
        """Generate alternative options"""
        alternatives = []
        
        # Extract alternative schools/programs from data
        for record in data:
            school = record.get('school_name')
            if school:
                alternatives.append(f"Consider {school} as an alternative option")
        
        return alternatives[:3]  # Limit to top 3

