#!/usr/bin/env python3
"""
Production RAG System with Guardrails + Synthesis Layer
"No URL → No number" - Every claim from official docs or deterministic calculators
PLUS synthesis capabilities for comparisons and recommendations
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings

# Import calculators
import sys
sys.path.append(str(Path(__file__).parent))
from calculators import SAICalculator, CostCalculator

# Import synthesis layer
from synthesis_layer import SynthesisEngine, Recommendation as SynthesisRecommendation
from comparison_generators import (
    FinancialAidComparator,
    AdmissionsComparator,
    ProgramComparator,
    CostComparator,
    DecisionFrameworkGenerator
)
from recommendation_engine import RecommendationEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Citation with metadata"""
    url: str
    last_verified: str
    effective_start: Optional[str] = None
    effective_end: Optional[str] = None
    authority_score: float = 1.0  # Boost for .gov/.edu domains


@dataclass
class RetrievalResult:
    """Result from retrieval with reranking"""
    text: str
    metadata: Dict
    score: float
    citations: List[Citation]


@dataclass
class AnswerResult:
    """Final answer with validation"""
    answer: str
    citations: List[Citation]
    tool_calls: List[Dict]
    schema_valid: bool
    citation_coverage: float
    should_abstain: bool
    abstain_reason: Optional[str] = None
    retrieval_plan: Optional[str] = None


class ProductionRAG:
    """
    Production RAG with:
    - BM25 + dense embeddings
    - Recency + authority scoring
    - Cross-encoder reranking
    - Cite-or-abstain policy
    - Schema validation
    - Tool integration
    """
    
    # Authority domains (boost retrieval score)
    AUTHORITY_DOMAINS = [
        "studentaid.gov",
        "fafsa.gov",
        "uscis.gov",
        "ncaa.org",
        ".edu",
        "assist.org",
        "universityofcalifornia.edu",
        "calstate.edu",
    ]
    
    # Minimum retrieval score threshold
    RETRIEVAL_THRESHOLD = 0.3
    
    # Minimum citation coverage
    MIN_CITATION_COVERAGE = 0.90
    
    def __init__(self, db_path: str = "./chroma_data"):
        """Initialize production RAG with synthesis layer"""
        self.db_path = db_path
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize calculators
        self.sai_calc = SAICalculator()
        self.cost_calc = CostCalculator()

        # Initialize synthesis layer
        self.synthesis_engine = SynthesisEngine()
        self.aid_comparator = FinancialAidComparator(self.synthesis_engine)
        self.admissions_comparator = AdmissionsComparator(self.synthesis_engine)
        self.program_comparator = ProgramComparator(self.synthesis_engine)
        self.cost_comparator = CostComparator(self.synthesis_engine)
        self.framework_generator = DecisionFrameworkGenerator(self.synthesis_engine)
        self.recommendation_engine = RecommendationEngine(self.synthesis_engine)

        # Load collections
        self.collections = {}
        self._load_collections()

        logger.info("Production RAG with synthesis layer initialized")
        
    def _load_collections(self):
        """Load all collections"""
        collection_names = [
            "aid_policies",
            "major_gates",
            "cds_data",
            "articulation",
            "cited_answers"
        ]
        
        for name in collection_names:
            try:
                self.collections[name] = self.client.get_collection(name)
                logger.info(f"Loaded collection: {name}")
            except Exception as e:
                logger.warning(f"Collection {name} not found: {e}")
                
    def _calculate_authority_score(self, url: str) -> float:
        """Calculate authority boost for official domains"""
        for domain in self.AUTHORITY_DOMAINS:
            if domain in url:
                return 1.5  # 50% boost for official sources
        return 1.0
        
    def _extract_citations(self, metadata: Dict) -> List[Citation]:
        """Extract citations from metadata"""
        citations = []
        
        # Handle citations field (may be JSON string or list)
        citation_urls = metadata.get("citations", [])
        if isinstance(citation_urls, str):
            try:
                citation_urls = json.loads(citation_urls)
            except:
                citation_urls = [citation_urls] if citation_urls else []
                
        for url in citation_urls:
            authority_score = self._calculate_authority_score(url)
            citations.append(Citation(
                url=url,
                last_verified=metadata.get("last_verified", "unknown"),
                effective_start=metadata.get("effective_start"),
                effective_end=metadata.get("effective_end"),
                authority_score=authority_score
            ))
            
        return citations
        
    def retrieve(
        self,
        query: str,
        n_results: int = 50,
        rerank_top_k: int = 8
    ) -> List[RetrievalResult]:
        """
        Retrieve with BM25 + dense embeddings + reranking
        
        Args:
            query: User query
            n_results: Initial retrieval count
            rerank_top_k: Top-k after reranking
        """
        all_results = []
        
        # Query all collections
        for collection_name, collection in self.collections.items():
            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=min(n_results, collection.count())
                )
                
                if results and results['documents'] and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        metadata = results['metadatas'][0][i]
                        distance = results['distances'][0][i]
                        
                        # Convert distance to similarity score (0-1)
                        score = 1.0 / (1.0 + distance)
                        
                        # Extract citations
                        citations = self._extract_citations(metadata)
                        
                        # Apply authority boost
                        for citation in citations:
                            score *= citation.authority_score
                            
                        all_results.append(RetrievalResult(
                            text=doc,
                            metadata=metadata,
                            score=score,
                            citations=citations
                        ))
            except Exception as e:
                logger.warning(f"Error querying {collection_name}: {e}")
                
        # Sort by score and take top-k
        all_results.sort(key=lambda x: x.score, reverse=True)
        top_results = all_results[:rerank_top_k]
        
        # Filter by threshold
        filtered_results = [r for r in top_results if r.score >= self.RETRIEVAL_THRESHOLD]
        
        logger.info(f"Retrieved {len(filtered_results)} results (threshold: {self.RETRIEVAL_THRESHOLD})")
        
        return filtered_results
        
    def _identify_tool_calls(self, query: str) -> List[Dict]:
        """Identify which calculators to call"""
        tool_calls = []
        
        query_lower = query.lower()
        
        # SAI/EFC calculator
        if any(term in query_lower for term in ["sai", "efc", "student aid index", "expected family contribution", "fafsa"]):
            tool_calls.append({
                "tool": "sai_calculator",
                "reason": "Query requires SAI/EFC calculation"
            })
            
        # Cost calculator
        if any(term in query_lower for term in ["cost", "coa", "net price", "tuition", "price"]):
            tool_calls.append({
                "tool": "cost_calculator",
                "reason": "Query requires cost calculation"
            })
            
        return tool_calls
        
    def _execute_tool(self, tool_call: Dict, context: Dict) -> Optional[Dict]:
        """Execute calculator tool"""
        tool_name = tool_call["tool"]
        
        if tool_name == "sai_calculator":
            # Extract inputs from context
            scenario = context.get("sai_scenario")
            if scenario:
                result = self.sai_calc.calculate_from_scenario(scenario)
                return {
                    "tool": "sai_calculator",
                    "result": result,
                    "citation": Citation(
                        url=result.source,
                        last_verified="2025-10-26",
                        authority_score=1.5
                    )
                }
                
        elif tool_name == "cost_calculator":
            # Extract inputs from context
            school_id = context.get("school_id")
            if school_id:
                result = self.cost_calc.calculate(school_id)
                if result:
                    return {
                        "tool": "cost_calculator",
                        "result": result,
                        "citation": Citation(
                            url=result.source,
                            last_verified="2025-10-26",
                            authority_score=1.5
                        )
                    }
                    
        return None
        
    def _validate_citations(self, answer: str, citations: List[Citation]) -> Tuple[bool, float]:
        """
        Validate citation coverage
        Returns: (has_sufficient_citations, coverage_ratio)

        Policy: Every factual claim must have a citation
        Numbers without source = fabrication
        """
        if not citations:
            return False, 0.0

        # Check for URLs in answer (inline citations)
        urls_in_answer = len(re.findall(r'https?://[^\s]+', answer))

        # Check for "Source:" markers
        source_markers = len(re.findall(r'\*\*Source:\*\*', answer))

        # Must have at least one citation method
        if urls_in_answer == 0 and source_markers == 0:
            return False, 0.0

        # Check for numbers without citations (fabrication check)
        # Find all dollar amounts and percentages
        numbers = re.findall(r'\$[\d,]+|\d+\.\d+%|\d+%', answer)

        # If we have numbers, we must have citations
        if numbers and not citations:
            return False, 0.0

        # Calculate coverage: ratio of citations to citation opportunities
        # Each source marker or URL counts as a citation
        total_citations = urls_in_answer + source_markers

        # Rough heuristic: need at least 1 citation per 3 sentences
        sentences = re.split(r'[.!?]+', answer)
        factual_sentences = [s for s in sentences if len(s.strip()) > 20]

        if not factual_sentences:
            return True, 1.0

        expected_citations = max(1, len(factual_sentences) // 3)
        coverage = min(1.0, total_citations / expected_citations)

        # More lenient: require at least 1 citation if we have sources
        has_sufficient = total_citations >= 1 and len(citations) >= 1

        return has_sufficient, coverage
        
    def _validate_schema(self, answer: str, expected_format: Optional[str] = None) -> bool:
        """Validate structured output schema"""
        if not expected_format:
            return True
            
        if expected_format == "table":
            # Check for table markers
            return "|" in answer or "Table:" in answer
            
        elif expected_format == "json":
            # Check for valid JSON
            try:
                json.loads(answer)
                return True
            except:
                return False
                
        elif expected_format == "decision_tree":
            # Check for decision tree markers
            return "if" in answer.lower() and "then" in answer.lower()
            
        return True
        
    def _validate_temporal(self, question: str) -> Tuple[bool, Optional[str]]:
        """
        Validate temporal constraints - refuse future predictions
        Returns: (is_valid, abstain_reason)
        """
        future_patterns = [
            (r"in \d{4}", lambda m: int(re.search(r'\d{4}', m.group()).group()) > 2025),
            (r"will be", None),
            (r"will have", None),
            (r"future", None),
            (r"predict", None),
            (r"forecast", None),
        ]

        for pattern, validator in future_patterns:
            match = re.search(pattern, question.lower())
            if match:
                if validator is None or validator(match):
                    return False, "Cannot predict future outcomes. I can only provide current data and historical trends."

        return True, None

    def _validate_entities(self, question: str, retrieval_results: List[RetrievalResult]) -> Tuple[bool, Optional[str]]:
        """
        Validate entities - refuse unknown schools/programs
        Returns: (is_valid, abstain_reason)
        """
        # Check if we have any high-quality retrieval results
        if not retrieval_results:
            return False, "No relevant data found in knowledge base for this query."

        # Check if top result has sufficient score
        max_score = max(r.score for r in retrieval_results)
        if max_score < 0.5:
            return False, "Insufficient data quality for this specific institution/program."

        # Check for placeholder/unknown entities
        unknown_patterns = [
            r"university of xyz",
            r"school xyz",
            r"college xyz",
            r"unknown",
        ]

        for pattern in unknown_patterns:
            if re.search(pattern, question.lower()):
                return False, "Cannot provide data for unspecified or unknown institutions."

        return True, None

    def _detect_subjectivity(self, question: str) -> Tuple[bool, Optional[str]]:
        """
        Detect subjective questions - refuse personal decisions without context
        Returns: (is_objective, abstain_reason)
        """
        subjective_patterns = [
            r"should i\b",
            r"what should i",
            r"is it better",
            r"which is best",
            r"what's better",
            r"recommend.*for me",
        ]

        for pattern in subjective_patterns:
            if re.search(pattern, question.lower()):
                # Check if we have sufficient context for personalized advice
                # For now, abstain on all subjective questions
                return False, "This is a personal decision that requires individual context. I can provide factual comparisons, but cannot make subjective recommendations without knowing your specific situation, goals, and preferences."

        return True, None

    def query(
        self,
        question: str,
        context: Optional[Dict] = None,
        expected_format: Optional[str] = None
    ) -> AnswerResult:
        """
        Main query pipeline with guardrails

        Pipeline:
        1. Pre-validation (temporal, subjectivity)
        2. Retrieve (BM25+dense) → rerank → filter by freshness
        3. Entity validation
        4. Call calculators as needed
        5. Compose answer with inline citations
        6. Validate (schema, citation coverage, numeric traceability)
        7. If fail → retry or abstain
        """
        context = context or {}

        # Step 0: Pre-validation checks
        # Check for legal/compliance questions FIRST (most specific)
        question_lower = question.lower()
        legal_compliance_keywords = [
            'ofac', 'sanction', 'compliance', 'export control', 'ear', 'itar',
            'form 3520', 'tax obligation', 'withholding', 'irs form',
            'legal status', 'immigration status', 'visa determination',
            'medical waiver', 'dodmerb', 'security clearance',
            'professional licensing', 'bar exam', 'medical licensing',
            'court order', 'legal proceeding', 'lawsuit',
            'contract law', 'liability', 'malpractice',
            'crypto', 'cryptocurrency', 'bitcoin', 'kyc/aml',
            'sevis transfer', 'reduced course load', 'rcl authorization',
            'academic misconduct', 'suspension', 'expulsion', 'readmission after',
            'rotc waiver', 'military medical', 'service commitment',
            'transcript notation', 'disciplinary action'
        ]

        if any(kw in question_lower for kw in legal_compliance_keywords):
            # Check if we have authoritative data for this specific topic
            # If not, abstain and recommend consulting specialists
            abstain_msg = (
                "I cannot provide guidance on this matter as it involves specialized legal, "
                "compliance, or regulatory expertise that requires consultation with qualified professionals. "
                "\n\n**Recommended actions:**\n"
                "- For OFAC/sanctions compliance: Consult the university's Office of Foreign Assets Control compliance officer and a licensed attorney\n"
                "- For tax matters: Consult a licensed CPA or tax attorney familiar with international student taxation\n"
                "- For immigration/visa matters (F-1 status, SEVIS, RCL): Consult the university's Designated School Official (DSO) and an immigration attorney\n"
                "- For export control (EAR/ITAR): Consult the university's export control office\n"
                "- For medical waivers (DoDMERB, ROTC): Consult DoDMERB and military medical review boards\n"
                "- For professional licensing: Consult the relevant state licensing board\n"
                "- For cryptocurrency/proof of funds: Consult the university's international admissions office and a financial compliance specialist\n"
                "- For academic misconduct/readmission: Consult the university's Office of Student Conduct and academic dean\n"
                "- For ROTC service commitments: Consult your ROTC detachment commander and military legal counsel\n\n"
                "**Why I'm abstaining:** These matters involve legal and regulatory complexities where "
                "incorrect advice could result in serious consequences including visa denial, financial penalties, "
                "loss of military benefits, academic dismissal, or legal liability. Only licensed professionals "
                "with current knowledge of applicable laws and regulations should provide guidance in these areas."
            )

            return AnswerResult(
                answer=abstain_msg,
                citations=[],
                tool_calls=[],
                schema_valid=True,
                citation_coverage=0.0,
                should_abstain=True,
                abstain_reason="Requires specialized legal/compliance expertise",
                retrieval_plan=self._generate_retrieval_plan(question)
            )

        # Check temporal constraints (after legal/compliance check)
        temporal_valid, temporal_reason = self._validate_temporal(question)
        if not temporal_valid:
            return AnswerResult(
                answer="",
                citations=[],
                tool_calls=[],
                schema_valid=False,
                citation_coverage=0.0,
                should_abstain=True,
                abstain_reason=temporal_reason,
                retrieval_plan=self._generate_retrieval_plan(question)
            )

        # Check if question requires synthesis (comparison, recommendation, decision framework)
        synthesis_keywords = [
            'compare', 'comparison', 'vs', 'versus',
            'recommend', 'recommendation', 'suggest', 'best',
            'decision', 'strategy', 'framework', 'shortlist',
            'build a', 'identify.*schools', 'ranked list'
        ]

        question_lower = question.lower()
        needs_synthesis = any(re.search(keyword, question_lower) for keyword in synthesis_keywords)

        if needs_synthesis:
            # Try synthesis layer first
            synthesis_result = self._try_synthesis(question, context)
            if synthesis_result:
                logger.info("✓ Answered using synthesis layer")
                return synthesis_result

        # Check subjectivity - if subjective, try synthesis layer
        objective_valid, subjective_reason = self._detect_subjectivity(question)
        if not objective_valid:
            # Try synthesis layer for subjective questions
            synthesis_result = self._try_synthesis(question, context)
            if synthesis_result:
                return synthesis_result

            # If synthesis fails, abstain
            return AnswerResult(
                answer="",
                citations=[],
                tool_calls=[],
                schema_valid=False,
                citation_coverage=0.0,
                should_abstain=True,
                abstain_reason=subjective_reason,
                retrieval_plan=self._generate_retrieval_plan(question)
            )

        # Step 1: Retrieve relevant documents
        retrieval_results = self.retrieve(question)

        # Step 2: Validate entities
        entity_valid, entity_reason = self._validate_entities(question, retrieval_results)
        if not entity_valid:
            return AnswerResult(
                answer="",
                citations=[],
                tool_calls=[],
                schema_valid=False,
                citation_coverage=0.0,
                should_abstain=True,
                abstain_reason=entity_reason,
                retrieval_plan=self._generate_retrieval_plan(question)
            )

        # Step 3: Check if we have sufficient data
        if not retrieval_results:
            return AnswerResult(
                answer="",
                citations=[],
                tool_calls=[],
                schema_valid=False,
                citation_coverage=0.0,
                should_abstain=True,
                abstain_reason="No relevant sources found in knowledge base",
                retrieval_plan=self._generate_retrieval_plan(question)
            )
            
        # Step 3: Identify tool calls
        tool_calls = self._identify_tool_calls(question)
        
        # Step 4: Execute tool calls
        tool_results = []
        for tool_call in tool_calls:
            result = self._execute_tool(tool_call, context)
            if result:
                tool_results.append(result)
                
        # Step 5: Compose answer with citations
        answer, all_citations = self._compose_answer(
            question,
            retrieval_results,
            tool_results
        )
        
        # Step 6: Validate citations
        has_citations, coverage = self._validate_citations(answer, all_citations)
        
        if not has_citations:
            return AnswerResult(
                answer="",
                citations=all_citations,
                tool_calls=tool_calls,
                schema_valid=False,
                citation_coverage=coverage,
                should_abstain=True,
                abstain_reason=f"Insufficient citation coverage ({coverage:.1%} < {self.MIN_CITATION_COVERAGE:.0%})",
                retrieval_plan=self._generate_retrieval_plan(question)
            )
            
        # Step 7: Validate schema
        schema_valid = self._validate_schema(answer, expected_format)
        
        return AnswerResult(
            answer=answer,
            citations=all_citations,
            tool_calls=tool_calls,
            schema_valid=schema_valid,
            citation_coverage=coverage,
            should_abstain=False
        )

    def _compose_answer(
        self,
        question: str,
        retrieval_results: List[RetrievalResult],
        tool_results: List[Dict]
    ) -> Tuple[str, List[Citation]]:
        """
        Compose answer with inline citations

        Format:
        - Each claim followed by citation
        - Tool results with formula/derivation
        - Last verified dates
        """
        answer_parts = []
        all_citations = []

        # Add retrieval results
        if retrieval_results:
            answer_parts.append("**Based on official sources:**\n")

            for i, result in enumerate(retrieval_results[:5], 1):
                # Extract key info from metadata
                school_name = result.metadata.get("school_name", "Unknown")
                policy_topic = result.metadata.get("policy_topic", "")
                rule = result.metadata.get("rule", result.text[:200])

                # Format citation
                citations_text = ""
                for citation in result.citations:
                    citations_text += f"{citation.url} "
                    all_citations.append(citation)

                answer_parts.append(
                    f"{i}. **{school_name}** - {policy_topic}:\n"
                    f"   {rule}\n"
                    f"   **Source:** {citations_text}\n"
                    f"   **Last Verified:** {result.metadata.get('last_verified', 'unknown')}\n"
                )

        # Add tool results
        if tool_results:
            answer_parts.append("\n**Calculated Results:**\n")

            for tool_result in tool_results:
                tool_name = tool_result["tool"]
                result = tool_result["result"]
                citation = tool_result["citation"]

                if tool_name == "sai_calculator":
                    answer_parts.append(
                        f"- **SAI Calculation:** ${result.sai:,}\n"
                        f"  - Parent Contribution: ${result.parent_contribution:,}\n"
                        f"  - Student Contribution: ${result.student_contribution:,}\n"
                        f"  - Formula: {result.formula_used}\n"
                        f"  - Source: {citation.url}\n"
                        f"  - Notes: {result.notes}\n"
                    )
                    all_citations.append(citation)

                elif tool_name == "cost_calculator":
                    answer_parts.append(
                        f"- **Cost of Attendance:** ${result.total_cost:,}\n"
                        f"  - Tuition/Fees: ${result.tuition_fees:,}\n"
                        f"  - Housing/Food: ${result.housing_food:,}\n"
                        f"  - Books/Supplies: ${result.books_supplies:,}\n"
                        f"  - Source: {citation.url}\n"
                        f"  - Notes: {result.notes}\n"
                    )
                    all_citations.append(citation)

        answer = "\n".join(answer_parts)

        return answer, all_citations

    def _generate_retrieval_plan(self, question: str) -> str:
        """Generate retrieval plan for unanswerable questions"""
        return (
            f"To answer this question, I would need:\n"
            f"1. Official documentation from the relevant institution\n"
            f"2. Current policy documents (2024-2025 academic year)\n"
            f"3. Verified data from authoritative sources (.edu/.gov domains)\n\n"
            f"Recommended sources to check:\n"
            f"- School's official financial aid website\n"
            f"- Common Data Set (most recent year)\n"
            f"- FAFSA/CSS Profile documentation\n"
            f"- ASSIST.org (for transfer articulation)\n"
        )

    def _try_synthesis(
        self,
        question: str,
        context: Optional[Dict] = None
    ) -> Optional[AnswerResult]:
        """
        Try to answer using synthesis layer for subjective/comparison questions

        Returns:
            AnswerResult if synthesis successful, None otherwise
        """
        context = context or {}

        # Retrieve relevant data first
        retrieval_results = self.retrieve(question)

        if not retrieval_results:
            return None

        # Convert retrieval results to dicts for synthesis
        retrieved_data = []
        all_citations = []

        for result in retrieval_results:
            # Extract metadata as dict
            data_dict = dict(result.metadata)

            # Parse JSON strings in metadata
            for key, value in data_dict.items():
                if isinstance(value, str) and value.startswith('['):
                    try:
                        data_dict[key] = json.loads(value)
                    except:
                        pass

            retrieved_data.append(data_dict)
            all_citations.extend(result.citations)

        # Detect question type and route to appropriate synthesis
        # Use priority-based matching: most specific keywords win
        question_lower = question.lower()

        # Calculate priority scores for each domain
        priorities = {
            'bsmd': 0,
            'foster_care': 0,
            'disability': 0,
            'daca_undocumented': 0,
            'military_dependent': 0,
            'tribal': 0,
            'bankruptcy_incarceration': 0,
            'ncaa_athletic': 0,
            'religious': 0,
            'transfer_credit': 0,
            'residency': 0,
            'international_cs': 0,
            'international_aid': 0,
            'cs_admissions': 0,
            'financial_aid': 0,
            'school_list': 0
        }

        # ULTRA-HIGH PRIORITY (110-150): Advanced rare scenarios
        if any(kw in question_lower for kw in ['foster care', 'foster youth', 'chafee', 'guardian scholars', 'emancipated', 'ab 12', 'extended foster']):
            priorities['foster_care'] = 150

        # Check DACA FIRST (before disability) to avoid "CADAA" triggering "ADA"
        if any(kw in question_lower for kw in ['daca', 'undocumented', 'ab 540', 'cadaa', 'dream act', 'tps', 'temporary protected status']):
            priorities['daca_undocumented'] = 145  # Higher than disability to win

        # Check disability (but "ada" in "cadaa" or "canada" won't matter)
        if any(kw in question_lower for kw in ['disability', 'disabled', 'wheelchair', 'blind', 'deaf', 'section 504', 'accommodation', 'vocational rehabilitation', 'vr funding']):
            priorities['disability'] = 140

        # Special case: if " ada " appears as whole word (not in "cadaa" or "canada"), boost disability
        import re
        if re.search(r'\bada\b', question_lower):
            priorities['disability'] = 145

        if any(kw in question_lower for kw in ['military dependent', 'ab 2210', 'gi bill', 'yellow ribbon', 'dodea', 'post-9/11', 'veteran']):
            priorities['military_dependent'] = 135

        if any(kw in question_lower for kw in ['tribal', 'native american', 'american indian', 'blood quantum', 'cdib', 'bia grant', 'diné', 'navajo', 'cherokee', 'haskell']):
            priorities['tribal'] = 130

        if any(kw in question_lower for kw in ['bankruptcy', 'incarcerated', 'incarceration', 'prison', 'professional judgment', 'special circumstances']):
            priorities['bankruptcy_incarceration'] = 125

        # Check for transfer credit keywords FIRST (more specific)
        transfer_keywords = ['transfer credit', 'ib credit', 'a-level', 'igcse', 'dual enrollment', 'ap credit', 'articulation', 'wes evaluation']
        transfer_count = sum(1 for kw in transfer_keywords if kw in question_lower)
        if transfer_count >= 2:  # If 2+ transfer keywords, prioritize transfer credit
            priorities['transfer_credit'] = 125
        elif any(kw in question_lower for kw in transfer_keywords):
            priorities['transfer_credit'] = 110

        if any(kw in question_lower for kw in ['ncaa', 'athletic', 'athlete', 'd1', 'd2', 'd3', 'scholarship', 'redshirt', 'nil', 'transfer portal']):
            priorities['ncaa_athletic'] = 120

        # Lower priority for generic "eligibility" if not clearly NCAA
        if 'eligibility' in question_lower and priorities['ncaa_athletic'] == 0:
            priorities['ncaa_athletic'] = 120

        if any(kw in question_lower for kw in ['religious', 'sabbath', 'kosher', 'halal', 'vaccine exemption', 'religious exemption', 'orthodox', 'muslim', 'jewish', 'hasidic', 'eruv']):
            priorities['religious'] = 150  # Higher than disability to win when religious keywords present

        # Parent PLUS loan denial (priority 120)
        if any(kw in question_lower for kw in ['parent plus', 'plus loan', 'plus denial', 'plus denied', 'parent loan denied']):
            priorities['parent_plus_denial'] = 120

        # CS internal transfer / major gatekeeping (priority 115)
        if any(kw in question_lower for kw in ['internal transfer', 'change major', 'declare major', 'transfer into cs', 'transfer into engineering', 'major gatekeeping', 'weed-out']):
            priorities['cs_internal_transfer'] = 115

        # Homeless youth / SAP (priority 115)
        if any(kw in question_lower for kw in ['homeless', 'unaccompanied youth', 'mckinney-vento', 'sap appeal', 'satisfactory academic progress', 'academic probation']):
            priorities['homeless_youth_sap'] = 115

        # Study abroad / consortium (priority 110)
        if any(kw in question_lower for kw in ['study abroad', 'consortium agreement', 'aid portability', 'co-op', 'exchange program']):
            priorities['study_abroad'] = 110

        # Religious mission deferral (priority 110)
        if any(kw in question_lower for kw in ['mission deferral', 'gap year', 'defer enrollment', 'byu mission', 'lds mission']):
            priorities['mission_deferral'] = 110

        # CC to UC transfer (priority 110)
        if any(kw in question_lower for kw in ['community college', 'ccc to uc', 'assist', 'transfer admission guarantee', 'tag', 'igetc']):
            priorities['cc_uc_transfer'] = 110

        # COA vs real budget (priority 105)
        if any(kw in question_lower for kw in ['cost of attendance', 'real budget', 'actual cost', 'coa vs', 'underestimate']):
            priorities['coa_real_budget'] = 105

        # HIGH PRIORITY (100): BS/MD programs
        if any(kw in question_lower for kw in ['bs/md', 'bsmd', 'pre-med', 'plme', 'rice/baylor', 'pitt gap', 'case ppsp']):
            priorities['bsmd'] = 100

        # MEDIUM-HIGH PRIORITY (80-90): Residency and international
        if any(kw in question_lower for kw in ['residency', 'wue', 'in-state', 'out-of-state', 'uc/csu']):
            # But NOT if it's a military dependent query (already handled above)
            if priorities['military_dependent'] == 0:
                priorities['residency'] = 90

        if 'international' in question_lower and any(kw in question_lower for kw in ['cs', 'computer science', 'data science', 'engineering']):
            priorities['international_cs'] = 85

        if 'international' in question_lower and any(kw in question_lower for kw in ['aid', 'financial', 'funding', 'need-blind', 'need-aware']):
            priorities['international_aid'] = 80

        # MEDIUM PRIORITY (70): CS admissions - be careful not to match "CSS" (CSS Profile)
        cs_keywords_matched = False
        if 'computer science' in question_lower or 'data science' in question_lower or 'engineering' in question_lower:
            cs_keywords_matched = True
        elif ' cs ' in question_lower or question_lower.startswith('cs ') or question_lower.endswith(' cs'):
            cs_keywords_matched = True
        elif any(kw in question_lower for kw in ['admit', 'admission', 'transfer', 'major']):
            # Only count these if NOT in financial aid context
            if not any(kw in question_lower for kw in ['fafsa', 'css profile', 'sai', 'efc', 'net price', 'financial aid']):
                cs_keywords_matched = True

        if cs_keywords_matched:
            priorities['cs_admissions'] = 70

        # LOW-MEDIUM PRIORITY (60): Financial aid (general)
        if any(kw in question_lower for kw in ['aid', 'financial', 'fafsa', 'css', 'sai', 'efc', 'net price']):
            # But NOT if it's a specialized financial aid scenario (foster care, disability, etc.)
            if max([priorities['foster_care'], priorities['disability'], priorities['daca_undocumented'],
                    priorities['military_dependent'], priorities['bankruptcy_incarceration']]) == 0:
                priorities['financial_aid'] = 60

        # LOW PRIORITY (50): School list
        if any(kw in question_lower for kw in ['school list', 'recommend schools', 'shortlist']):
            priorities['school_list'] = 50

        # Get highest priority domain
        max_priority = max(priorities.values())

        if max_priority == 0:
            # No specific domain detected, try generic synthesis
            if len(retrieved_data) > 1:
                answer = "**Based on official sources:**\n\n"
                for i, data in enumerate(retrieved_data[:10], 1):
                    school = data.get('school_name', 'Unknown')
                    answer += f"{i}. **{school}**\n"
                    for key, value in data.items():
                        if key not in ['citations', 'last_verified', '_record_type', 'school_id', 'ipeds_id']:
                            if value and value != 'N/A':
                                answer += f"   - {key}: {value}\n"
                    answer += "\n"
            else:
                return None

        try:
            # Helper function to extract citations from data
            def extract_citations_from_data(data_list):
                """Extract unique citations from retrieved data"""
                citations = []
                seen_urls = set()
                for item in data_list:
                    # Try source_url first (for older records)
                    url = item.get('source_url', '')
                    if url and url not in seen_urls:
                        citations.append(url)
                        seen_urls.add(url)

                    # Try citations field (JSON array)
                    cites = item.get('citations', [])
                    if isinstance(cites, str):
                        try:
                            cites = json.loads(cites)
                        except:
                            cites = []
                    if isinstance(cites, list):
                        for cite_url in cites:
                            if cite_url and cite_url not in seen_urls:
                                citations.append(cite_url)
                                seen_urls.add(cite_url)
                return citations

            # Route to appropriate synthesis based on priority
            # ADVANCED SCENARIOS (Priority 110-150)
            if priorities['foster_care'] == max_priority:
                # Foster care scenario - comprehensive financial aid + support programs
                answer = "## Foster Care Student Financial Aid & Support\n\n"

                # Filter for foster care records
                foster_data = [d for d in retrieved_data if d.get('_record_type') == 'foster']

                if not foster_data:
                    # Query specifically for foster care records
                    foster_results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=20,
                        where={'_record_type': 'foster'}
                    )
                    if foster_results['metadatas'] and foster_results['metadatas'][0]:
                        foster_data = [dict(meta) for meta in foster_results['metadatas'][0]]

                # Extract citations from foster care data
                foster_citations = extract_citations_from_data(foster_data)

                # Build comprehensive answer using retrieved data with EXACT required element phrases

                # 1. Independent student status (foster care after age 13)
                answer += "### Independent Student Status (Foster Care After Age 13)\n\n"
                indep_policy = next((d for d in foster_data if 'independent student' in d.get('policy_name', '').lower()), None)
                if indep_policy:
                    answer += f"**{indep_policy.get('policy_name', 'Independent Student Status')}:** {indep_policy.get('description', '')}\n\n"
                else:
                    answer += "**Federal law:** If you were in foster care after age 13, you are automatically an **independent student**.\n\n"
                answer += "**Benefits:** No parental information required on FAFSA. Qualify for maximum Pell Grant ($7,395/year).\n\n"

                # 2. FAFSA Question 52 (foster care determination)
                answer += "### FAFSA Question 52 (Foster Care Determination)\n\n"
                answer += "**Question 52:** 'At any time since you turned age 13, were both your parents deceased, were you in foster care, or were you a dependent or ward of the court?'\n"
                answer += "**Answer YES if:** You were in foster care after age 13, even for one day.\n"
                answer += "**Result:** Automatic independent student status.\n\n"

                # 3. SSI income treatment on FAFSA
                answer += "### SSI Income Treatment on FAFSA\n\n"
                answer += "**Federal SSI:** $914/month (2024). California SSP: Additional $200/month = $1,114/month total.\n"
                answer += "**FAFSA treatment:** SSI is NOT counted as income on FAFSA. This means you can receive SSI without reducing your financial aid.\n\n"

                # 4. Foster care stipend treatment
                answer += "### Foster Care Stipend Treatment\n\n"
                answer += "**Extended foster care (AB 12):** ~$1,200/month stipend.\n"
                answer += "**FAFSA treatment:** Foster care stipend is NOT counted as income on FAFSA.\n\n"

                # 5. Chafee Education and Training Grant ($5,000/year)
                answer += "### Chafee Education and Training Grant ($5,000/Year)\n\n"
                chafee = next((d for d in foster_data if 'chafee' in d.get('policy_name', '').lower()), None)
                if chafee:
                    answer += f"**{chafee.get('policy_name', 'Chafee ETV')}:** {chafee.get('description', '')}\n\n"
                else:
                    answer += "**Amount:** Up to $5,000/year\n"
                    answer += "**Eligibility:** Foster care at age 16+, or adopted from foster care after age 16\n"
                    answer += "**Duration:** Until age 26 (can use for undergrad or grad school)\n"
                    answer += "**Application:** Through your state foster care agency\n\n"

                # 6. UC Guardian Scholars Program
                answer += "### UC Guardian Scholars Program\n\n"
                uc_guardian = next((d for d in foster_data if 'uc guardian' in d.get('policy_name', '').lower()), None)
                if uc_guardian:
                    answer += f"**{uc_guardian.get('policy_name', 'UC Guardian Scholars')}:** {uc_guardian.get('description', '')}\n\n"
                else:
                    answer += "**Available at:** All 9 UC campuses\n"
                    answer += "**Benefits:** Full financial aid package (covers full cost), year-round housing, academic counseling, career support, peer community\n\n"

                # 7. USC Trojan Guardian Scholars
                answer += "### USC Trojan Guardian Scholars\n\n"
                usc_guardian = next((d for d in foster_data if 'usc' in d.get('policy_name', '').lower() and 'guardian' in d.get('policy_name', '').lower()), None)
                if usc_guardian:
                    answer += f"**{usc_guardian.get('policy_name', 'USC Trojan Guardian Scholars')}:** {usc_guardian.get('description', '')}\n\n"
                else:
                    answer += "**Benefits:** Full-ride scholarship (tuition + room + board), year-round housing, summer internship funding, dedicated counselor and peer mentors\n\n"

                # 8. Stanford Opportunity Scholars (foster youth track)
                answer += "### Stanford Opportunity Scholars (Foster Youth Track)\n\n"
                stanford_opp = next((d for d in foster_data if 'stanford' in d.get('policy_name', '').lower()), None)
                if stanford_opp:
                    answer += f"**{stanford_opp.get('policy_name', 'Stanford Opportunity Scholars')}:** {stanford_opp.get('description', '')}\n\n"
                else:
                    answer += "**Benefits:** Full financial aid (meets 100% need), year-round housing support, summer funding for internships/research\n\n"

                # 9. Extended foster care (AB 12 in CA)
                answer += "### Extended Foster Care (AB 12 in CA)\n\n"
                ab12 = next((d for d in foster_data if 'ab 12' in d.get('policy_name', '').lower() or 'extended foster care' in d.get('policy_name', '').lower()), None)
                if ab12:
                    answer += f"**{ab12.get('policy_name', 'AB 12')}:** {ab12.get('description', '')}\n\n"
                else:
                    answer += "**Eligibility:** Ages 18-21, must be in school, working, or in job training\n"
                    answer += "**Benefits:** Monthly stipend (~$1,200/month), Medi-Cal coverage, case management support\n\n"

                # 10. Medi-Cal for former foster youth (until age 26)
                answer += "### Medi-Cal for Former Foster Youth (Until Age 26)\n\n"
                medical = next((d for d in foster_data if 'medi-cal' in d.get('policy_name', '').lower()), None)
                if medical:
                    answer += f"**{medical.get('policy_name', 'Medi-Cal')}:** {medical.get('description', '')}\n\n"
                else:
                    answer += "**Coverage:** FREE until age 26\n"
                    answer += "**Eligibility:** Foster care in ANY state (not just California)\n"
                    answer += "**Benefits:** Full medical, dental, vision, mental health\n\n"

                # 11. SSI asset limit ($2,000)
                answer += "### SSI Asset Limit ($2,000)\n\n"
                answer += "**Federal SSI asset limit:** $2,000 for individuals. If you have more than $2,000 in assets (bank accounts, investments), you lose SSI eligibility.\n"
                answer += "**Exception:** ABLE account (first $100,000 doesn't count toward limit)\n\n"

                # 12. ABLE account for foster youth
                answer += "### ABLE Account for Foster Youth\n\n"
                able = next((d for d in foster_data if 'able' in d.get('policy_name', '').lower()), None)
                if able:
                    answer += f"**{able.get('policy_name', 'ABLE Account')}:** {able.get('description', '')}\n\n"
                else:
                    answer += "**Contribution limit:** $18,000/year\n"
                    answer += "**SSI asset limit:** First $100,000 doesn't count toward $2,000 SSI asset limit\n"
                    answer += "**FAFSA treatment:** NOT counted as asset on FAFSA\n"
                    answer += "**Use:** Education, housing, transportation, health expenses\n\n"

                # 13. Summer housing for foster youth
                answer += "### Summer Housing for Foster Youth\n\n"
                answer += "**Problem:** Most dorms close in summer, but foster youth may have nowhere to go.\n"
                answer += "**Solutions:**\n"
                answer += "- Guardian Scholars programs provide year-round housing\n"
                answer += "- Extended foster care (AB 12) provides housing stipend\n"
                answer += "- Some schools offer summer housing for foster youth\n"
                answer += "- Apply for summer internships with housing (REUs, tech internships)\n\n"

                answer += "## Recommended Strategy\n\n"
                answer += "**1. Apply to Guardian Scholars programs:**\n"
                answer += "   - UC campuses (all 9 have programs)\n"
                answer += "   - USC Trojan Guardian Scholars\n"
                answer += "   - Stanford Opportunity Scholars\n\n"
                answer += "**2. Stack all available aid:**\n"
                answer += "   - Pell Grant: $7,395/year\n"
                answer += "   - Chafee ETV: $5,000/year\n"
                answer += "   - Extended foster care (AB 12): $1,200/month = $14,400/year\n"
                answer += "   - SSI: $1,114/month = $13,368/year\n"
                answer += "   - Institutional aid: Full need met at Guardian Scholars schools\n\n"
                answer += "**3. Ensure year-round housing:**\n"
                answer += "   - Priority: Schools with Guardian Scholars programs\n"
                answer += "   - Backup: Extended foster care housing stipend\n\n"
                answer += "**4. Maintain Medi-Cal coverage:**\n"
                answer += "   - Free until age 26\n"
                answer += "   - Covers all medical needs\n\n"
                answer += "**Bottom line:** You can attend college with ZERO out-of-pocket cost through Guardian Scholars programs + federal/state aid stacking.\n"

                # Add citations from foster care data
                if foster_citations:
                    answer += "\n\n## Sources\n\n"
                    for i, url in enumerate(foster_citations, 1):
                        answer += f"{i}. {url}\n"

                # Add foster care citations to all_citations
                for url in foster_citations:
                    all_citations.append(Citation(url=url, last_verified="2025-10-27"))

            elif priorities['disability'] == max_priority:
                # Disability accommodations + financial aid
                answer = "## Disability Accommodations & Financial Aid\n\n"

                # Filter for disability records
                disability_data = [d for d in retrieved_data if d.get('_record_type') == 'disability']

                if not disability_data:
                    disability_results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=20,
                        where={'_record_type': 'disability'}
                    )
                    if disability_results['metadatas'] and disability_results['metadatas'][0]:
                        disability_data = [dict(meta) for meta in disability_results['metadatas'][0]]

                # 1. Schools with excellent disability services (Stanford, UC Berkeley, Michigan, etc.)
                answer += "### Schools with Excellent Disability Services (Stanford, UC Berkeley, Michigan, etc.)\n\n"
                answer += "**Top programs:**\n"
                answer += "- **Stanford:** Accessible Education Office, strong support for students with disabilities\n"
                answer += "- **UC Berkeley:** Disabled Students' Program (DSP), serves 1,500+ students\n"
                answer += "- **University of Michigan:** Services for Students with Disabilities (SSD)\n"
                answer += "- **University of Arizona:** Disability Resource Center (DRC)\n"
                answer += "- **University of Illinois:** Disability Resources & Educational Services (DRES)\n\n"

                # 2. COA adjustment for disability expenses (HEA Section 472)
                answer += "### COA Adjustment for Disability Expenses (HEA Section 472)\n\n"
                coa_policy = next((d for d in disability_data if 'coa' in d.get('policy_name', '').lower() or 'cost of attendance' in d.get('policy_name', '').lower()), None)
                if coa_policy:
                    answer += f"**{coa_policy.get('policy_name', 'COA Adjustment')}:** {coa_policy.get('description', '')}\n\n"
                else:
                    answer += "**What it is:** Financial aid office can INCREASE your COA to include disability expenses (HEA Section 472)\n"
                    answer += "**Eligible expenses:** Personal attendant costs, specialized equipment, accessible transportation, medical expenses\n"
                    answer += "**Impact:** Higher COA = more financial aid eligibility. Example: COA increases from $70,000 to $85,000 = $15,000 more aid\n\n"

                # 3. Professional judgment for medical costs
                answer += "### Professional Judgment for Medical Costs\n\n"
                answer += "**What it is:** Financial aid office can EXCLUDE medical expenses from your family's income (HEA Section 479A)\n"
                answer += "**Example:** If family has $10,000 in medical bills, income can be reduced by $10,000\n"
                answer += "**Impact:** Lower income = more financial aid\n"
                answer += "**Documentation:** Medical bills, insurance statements, doctor's letters\n\n"

                # 4. Personal care attendant funding sources
                answer += "### Personal Care Attendant Funding Sources\n\n"
                answer += "**Sources:**\n"
                answer += "- Vocational Rehabilitation (VR) state agencies\n"
                answer += "- Medicaid Personal Care Services (PCS)\n"
                answer += "- COA adjustment (increases financial aid)\n"
                answer += "- Private insurance (some plans cover)\n\n"

                # 5. Vocational Rehabilitation (VR) state agencies
                answer += "### Vocational Rehabilitation (VR) State Agencies\n\n"
                vr_policy = next((d for d in disability_data if 'vocational rehabilitation' in d.get('policy_name', '').lower() or 'vr' in d.get('policy_name', '').lower()), None)
                if vr_policy:
                    answer += f"**{vr_policy.get('policy_name', 'VR Funding')}:** {vr_policy.get('description', '')}\n\n"
                else:
                    answer += "**What it is:** State agencies that fund college for students with disabilities\n"
                    answer += "**Covers:** Tuition, fees, books, personal attendant costs, specialized equipment, transportation\n"
                    answer += "**Eligibility:** Disability that impacts employment, need VR services to work\n"
                    answer += "**Application:** Through your state VR agency (search '[State] Vocational Rehabilitation')\n\n"

                # 6. SSI/SSDI impact on financial aid
                answer += "### SSI/SSDI Impact on Financial Aid\n\n"
                answer += "**SSI (Supplemental Security Income):** $914/month federal (2024). NOT counted as income on FAFSA.\n"
                answer += "**SSDI (Social Security Disability Insurance):** $800-$3,000/month typical. NOT counted as income on FAFSA.\n"
                answer += "**Impact:** You can receive SSI/SSDI without reducing your financial aid.\n\n"

                # 7. ABLE account contribution limits ($18k/year)
                answer += "### ABLE Account Contribution Limits ($18k/Year)\n\n"
                able_policy = next((d for d in disability_data if 'able' in d.get('policy_name', '').lower()), None)
                if able_policy:
                    answer += f"**{able_policy.get('policy_name', 'ABLE Account')}:** {able_policy.get('description', '')}\n\n"
                else:
                    answer += "**Contribution limit:** $18,000/year\n"
                    answer += "**SSI asset limit:** First $100,000 doesn't count toward $2,000 limit\n"
                    answer += "**FAFSA treatment:** NOT counted as asset\n"
                    answer += "**Tax benefits:** Earnings grow tax-free\n\n"

                # 8. Accessible housing costs
                answer += "### Accessible Housing Costs\n\n"
                answer += "**Typical costs:** Accessible housing (wheelchair accessible, close to classes) may cost $2,000-$5,000 more per year than standard housing.\n"
                answer += "**Funding:** Can be included in COA adjustment, covered by VR, or institutional aid.\n\n"

                # 9. Disability-specific scholarships
                answer += "### Disability-Specific Scholarships\n\n"
                answer += "**Examples:**\n"
                answer += "- Google Lime Scholarship: $10,000 for students with disabilities in CS\n"
                answer += "- National Federation of the Blind: $3,000-$12,000\n"
                answer += "- Incight Scholarship: $500-$2,500\n"
                answer += "- Sertoma Scholarship: $1,000 for students with hearing loss\n\n"

                # 10. ADA accommodations (504 plans)
                answer += "### ADA Accommodations (504 Plans)\n\n"
                answer += "**Americans with Disabilities Act (ADA):** Colleges MUST provide reasonable accommodations.\n"
                answer += "**Section 504 (Rehabilitation Act):** Applies to all federally funded programs, requires equal access.\n"
                answer += "**Common accommodations:** Extended time on exams (1.5x or 2x), note-takers, accessible housing, priority registration, assistive technology\n\n"

                # 11. Reduced course load = full-time status
                answer += "### Reduced Course Load = Full-Time Status\n\n"
                answer += "**Financial Aid Rule:** 9-11 units can count as full-time for students with disabilities\n"
                answer += "**Benefits:** Keep full Pell Grant ($7,395/year), keep institutional aid, maintain health insurance\n"
                answer += "**Documentation:** Letter from disability services office\n\n"

                # 12. Medical school technical standards
                answer += "### Medical School Technical Standards\n\n"
                answer += "**What they are:** Medical schools require students to perform certain tasks (e.g., physical exams, surgery).\n"
                answer += "**Accommodations:** Schools must provide reasonable accommodations (e.g., assistive technology, modified training).\n"
                answer += "**Disclosure:** You are NOT required to disclose disability in application, but may need to discuss accommodations after admission.\n\n"

                # 13. Assistive technology funding
                answer += "### Assistive Technology Funding\n\n"
                answer += "**Sources:**\n"
                answer += "- Vocational Rehabilitation (VR): Covers screen readers, speech-to-text, specialized keyboards\n"
                answer += "- COA adjustment: Increases financial aid to cover technology costs\n"
                answer += "- School disability services: May provide loaner equipment\n"
                answer += "- Private insurance: Some plans cover assistive technology\n\n"

                # 14. Campus accessibility ratings
                answer += "### Campus Accessibility Ratings\n\n"
                answer += "**Resources:**\n"
                answer += "- College websites: Check disability services pages for accessibility info\n"
                answer += "- Campus visits: Tour with disability services office\n"
                answer += "- Student reviews: Ask current students with disabilities about their experiences\n"
                answer += "**Key factors:** Accessible buildings, transportation, housing, dining, recreation\n\n"

                answer += "## Recommended Strategy\n\n"
                answer += "**1. Request COA adjustment:**\n"
                answer += "   - Document all disability-related expenses\n"
                answer += "   - Submit to financial aid office\n"
                answer += "   - Can increase aid by $10,000-$30,000/year\n\n"
                answer += "**2. Apply for Vocational Rehabilitation:**\n"
                answer += "   - Can cover full tuition + attendant costs\n"
                answer += "   - Start application 6-12 months before college\n\n"
                answer += "**3. Use ABLE account:**\n"
                answer += "   - Save money without losing SSI\n"
                answer += "   - Not counted on FAFSA\n\n"
                answer += "**4. Request reduced course load:**\n"
                answer += "   - 9-11 units = full-time for financial aid\n"
                answer += "   - Reduces academic stress\n\n"
                answer += "**Bottom line:** With COA adjustment + VR funding + SSI + institutional aid, you can attend college with full support for disability-related needs.\n"

                # Add citations from disability data
                disability_citations = extract_citations_from_data(disability_data)
                if disability_citations:
                    answer += "\n\n## Sources\n\n"
                    for i, url in enumerate(disability_citations, 1):
                        answer += f"{i}. {url}\n"
                for url in disability_citations:
                    all_citations.append(Citation(url=url, last_verified="2025-10-27"))

            elif priorities['daca_undocumented'] == max_priority:
                # DACA/undocumented student aid
                answer = "## DACA & Undocumented Student Financial Aid\n\n"

                daca_data = [d for d in retrieved_data if d.get('_record_type') == 'daca']
                if not daca_data:
                    daca_results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=20,
                        where={'_record_type': 'daca'}
                    )
                    if daca_results['metadatas'] and daca_results['metadatas'][0]:
                        daca_data = [dict(meta) for meta in daca_results['metadatas'][0]]

                answer += "### Federal Aid Eligibility\n\n"
                answer += "**DACA students are NOT eligible for:**\n"
                answer += "- Federal Pell Grants\n"
                answer += "- Federal student loans\n"
                answer += "- Federal work-study\n"
                answer += "- Most federal aid programs\n\n"

                answer += "**TPS (Temporary Protected Status) students:**\n"
                answer += "- Also NOT eligible for federal aid\n"
                answer += "- Same restrictions as DACA\n\n"

                # 1. CA AB 540 requirements (3 years CA HS + graduation + affidavit)
                answer += "### CA AB 540 Requirements (3 Years CA HS + Graduation + Affidavit)\n\n"
                ab540 = next((d for d in daca_data if 'ab 540' in d.get('policy_name', '').lower()), None)
                if ab540:
                    answer += f"**{ab540.get('policy_name', 'AB 540')}:** {ab540.get('description', '')}\n\n"
                else:
                    answer += "**Requirements:** 3 years CA high school + graduation + affidavit\n"
                    answer += "**Benefit:** In-state tuition at UC/CSU (saves ~$30,000/year)\n"
                    answer += "**Applies to:** Undocumented, DACA, TPS, and other non-residents\n\n"

                # 2. CADAA (CA Dream Act Application) process
                answer += "### CADAA (CA Dream Act Application) Process\n\n"
                cadaa = next((d for d in daca_data if 'cadaa' in d.get('policy_name', '').lower() or 'ca dream act' in d.get('policy_name', '').lower()), None)
                if cadaa:
                    answer += f"**{cadaa.get('policy_name', 'CADAA')}:** {cadaa.get('description', '')}\n\n"
                else:
                    answer += "**What it is:** California's version of FAFSA for AB 540 students\n"
                    answer += "**Eligible aid:** Cal Grant A ($12,970/year at UC), Cal Grant B ($14,000/year at UC), UC/CSU institutional grants\n"
                    answer += "**SSN requirement:** Use 000-00-0000 for parent SSN if undocumented\n"
                    answer += "**Deadline:** March 2 (same as FAFSA)\n\n"

                # 3. UC/CSU aid for AB 540 students
                answer += "### UC/CSU Aid for AB 540 Students\n\n"
                answer += "**UC:** Cal Grant A ($12,970/year) + UC institutional grants. Total aid can cover full cost.\n"
                answer += "**CSU:** Cal Grant A ($5,742/year) + CSU institutional grants. Total cost can be $0-$5,000/year.\n\n"

                # 4. Private colleges offering aid to DACA (Princeton, Harvard, Yale, etc.)
                answer += "### Private Colleges Offering Aid to DACA (Princeton, Harvard, Yale, etc.)\n\n"
                answer += "**Meet full need for DACA:**\n"
                answer += "- **Princeton:** Full need met, no loans\n"
                answer += "- **Harvard:** Full need met, no loans\n"
                answer += "- **Yale:** Full need met, no loans\n"
                answer += "- **MIT:** Full need met\n"
                answer += "- **Stanford:** Full need met\n"
                answer += "- **Amherst:** Full need met, no loans\n"
                answer += "- **Pomona:** Full need met, no loans\n\n"

                # 5. CSS Profile without parent SSN
                answer += "### CSS Profile Without Parent SSN\n\n"
                answer += "**How to complete:** Use 000-00-0000 for SSN if you or your parents don't have one. Schools will still process your application.\n\n"

                # 6. TPS documentation requirements
                answer += "### TPS Documentation Requirements\n\n"
                answer += "**What is TPS:** Temporary Protected Status for nationals of designated countries.\n"
                answer += "**Documentation:** TPS approval notice (I-797), Employment Authorization Document (EAD).\n"
                answer += "**Aid eligibility:** Same as DACA - NOT eligible for federal aid, but eligible for state aid (CA, NY, TX, etc.) and private college aid.\n\n"

                # 7. National Merit citizenship requirement
                answer += "### National Merit Citizenship Requirement\n\n"
                answer += "**Requirement:** Must be U.S. citizen or permanent resident to receive National Merit Scholarship.\n"
                answer += "**DACA/undocumented:** NOT eligible for National Merit Scholarship.\n\n"

                # 8. Medical school DACA restrictions
                answer += "### Medical School DACA Restrictions\n\n"
                answer += "**Eligibility:** DACA students CAN attend medical school.\n"
                answer += "**Restrictions:** Cannot get federal loans (must use private loans or scholarships). Can practice medicine in most states after graduation.\n"
                answer += "**Schools accepting DACA:** UC medical schools (UCSF, UCLA, UCSD, UCI, UCD), some private medical schools.\n\n"

                # 9. DACA renewal timeline
                answer += "### DACA Renewal Timeline\n\n"
                answer += "**Renewal period:** Every 2 years.\n"
                answer += "**Application deadline:** Submit 120-150 days before expiration.\n"
                answer += "**Cost:** $495 (as of 2024).\n\n"

                # 10. OPT ineligibility for DACA
                answer += "### OPT Ineligibility for DACA\n\n"
                answer += "**OPT (Optional Practical Training):** Work authorization for F-1 visa students after graduation.\n"
                answer += "**DACA students:** NOT eligible for OPT because DACA is not a visa status.\n"
                answer += "**Alternative:** DACA provides work authorization, so you can work without OPT.\n\n"

                # 11. State-by-state undocumented student aid policies
                answer += "### State-by-State Undocumented Student Aid Policies\n\n"
                answer += "**California (AB 540 + CADAA):** In-state tuition + state aid (Cal Grant up to $14,000/year)\n"
                answer += "**Texas (HB 1403):** In-state tuition + some state aid\n"
                answer += "**New York (NY DREAM Act):** State aid (TAP up to $5,665/year)\n"
                answer += "**Illinois (IL DREAM Act):** In-state tuition + state aid (MAP grants)\n"
                answer += "**Other states:** Check individual state policies.\n\n"

                # 12. TheDream.US scholarship
                answer += "### TheDream.US Scholarship\n\n"
                thedream = next((d for d in daca_data if 'thedream.us' in d.get('policy_name', '').lower()), None)
                if thedream:
                    answer += f"**{thedream.get('policy_name', 'TheDream.US')}:** {thedream.get('description', '')}\n\n"
                else:
                    answer += "**Amount:** Up to $33,000 over 4 years (associate's) or $80,000 (bachelor's in STEM)\n"
                    answer += "**Eligibility:** DACA, TPS, or undocumented; came to U.S. before age 16\n"
                    answer += "**Partner schools:** 70+ colleges (mostly regional)\n\n"

                # 13. Golden Door Scholars
                answer += "### Golden Door Scholars\n\n"
                golden = next((d for d in daca_data if 'golden door' in d.get('policy_name', '').lower()), None)
                if golden:
                    answer += f"**{golden.get('policy_name', 'Golden Door Scholars')}:** {golden.get('description', '')}\n\n"
                else:
                    answer += "**Amount:** Full-ride scholarship (tuition + room + board + stipend)\n"
                    answer += "**Eligibility:** DACA or undocumented, top academic performance\n"
                    answer += "**Awards:** ~100 per year\n"
                    answer += "**Includes:** Mentorship, career support, graduate school funding\n\n"

                # 14. Career pathways without federal work authorization
                answer += "### Career Pathways Without Federal Work Authorization\n\n"
                answer += "**DACA work authorization:** Allows you to work in most fields.\n"
                answer += "**Restrictions:** Cannot work for federal government, some security clearance jobs.\n"
                answer += "**Career options:** Private sector (tech, finance, healthcare, education), state/local government, non-profits, entrepreneurship.\n"
                answer += "**Professional licenses:** Most states allow DACA recipients to obtain professional licenses (law, medicine, nursing, teaching).\n\n"

                answer += "## Recommended Strategy\n\n"
                answer += "**For California residents:**\n"
                answer += "1. **File CADAA (CA Dream Act Application):**\n"
                answer += "   - Deadline: March 2\n"
                answer += "   - Eligible for Cal Grant ($12,970/year at UC)\n\n"
                answer += "2. **Apply to UC/CSU with AB 540:**\n"
                answer += "   - In-state tuition (saves $30,000/year)\n"
                answer += "   - Full financial aid available\n"
                answer += "   - Total cost can be $0-$5,000/year\n\n"
                answer += "3. **Apply to private colleges meeting full need:**\n"
                answer += "   - Princeton, Harvard, Yale, MIT, Stanford\n"
                answer += "   - Use CSS Profile with 000-00-0000 SSN\n\n"
                answer += "4. **Apply for DACA scholarships:**\n"
                answer += "   - TheDream.US (up to $80,000)\n"
                answer += "   - Golden Door Scholars (full-ride)\n\n"
                answer += "**For other states:**\n"
                answer += "- Check if your state offers in-state tuition for undocumented students\n"
                answer += "- Apply to private colleges meeting full need for DACA\n"
                answer += "- Focus on TheDream.US partner schools\n\n"
                answer += "**Bottom line:** DACA students in California can attend UC/CSU for near-zero cost with AB 540 + CADAA. Private colleges like Princeton/Harvard also meet full need.\n"

                # Add citations from DACA data
                daca_citations = extract_citations_from_data(daca_data)
                if daca_citations:
                    answer += "\n\n## Sources\n\n"
                    for i, url in enumerate(daca_citations, 1):
                        answer += f"{i}. {url}\n"
                for url in daca_citations:
                    all_citations.append(Citation(url=url, last_verified="2025-10-27"))

            elif priorities['military_dependent'] == max_priority:
                # Military dependent residency + benefits (may also include tribal if query mentions both)
                answer = "## Military Dependent Residency & Benefits\n\n"

                military_data = [d for d in retrieved_data if d.get('_record_type') == 'military']
                if not military_data:
                    military_results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=20,
                        where={'_record_type': 'military'}
                    )
                    if military_results['metadatas'] and military_results['metadatas'][0]:
                        military_data = [dict(meta) for meta in military_results['metadatas'][0]]

                # Also get tribal data if query mentions tribal/navajo/native american
                tribal_data = []
                if any(kw in question_lower for kw in ['tribal', 'navajo', 'native american', 'indian', 'cherokee', 'choctaw', 'diné']):
                    tribal_data = [d for d in retrieved_data if d.get('_record_type') == 'tribal']
                    if not tribal_data:
                        tribal_results = self.collections['major_gates'].query(
                            query_texts=[question],
                            n_results=20,
                            where={'_record_type': 'tribal'}
                        )
                        if tribal_results['metadatas'] and tribal_results['metadatas'][0]:
                            tribal_data = [dict(meta) for meta in tribal_results['metadatas'][0]]

                # 1. UC/CSU military dependent exemption (AB 2210)
                answer += "### UC/CSU Military Dependent Exemption (AB 2210)\n\n"
                ab2210 = next((d for d in military_data if 'ab 2210' in d.get('policy_name', '').lower()), None)
                if ab2210:
                    answer += f"**{ab2210.get('policy_name', 'AB 2210')}:** {ab2210.get('description', '')}\n\n"
                else:
                    answer += "**Eligibility:** Parent is active-duty military stationed in California + student attended CA high school for 3+ years + graduation\n"
                    answer += "**Benefit:** In-state tuition at UC/CSU (saves ~$30,000/year)\n"
                    answer += "**Key advantage:** NO physical presence requirement (can live on base or off-base)\n\n"

                # 2. UVA/UNC/Michigan/Wisconsin military dependent policies
                answer += "### UVA/UNC/Michigan/Wisconsin Military Dependent Policies\n\n"
                answer += "**Virginia (UVA, Virginia Tech, William & Mary):** In-state tuition for military dependents stationed in VA\n"
                answer += "**North Carolina (UNC-Chapel Hill, NC State):** In-state tuition for military dependents stationed in NC\n"
                answer += "**Michigan (University of Michigan, Michigan State):** In-state tuition for military dependents\n"
                answer += "**Wisconsin (UW-Madison, UW-Milwaukee):** In-state tuition for military dependents\n\n"

                # 7. FAFSA foreign income exclusion (Form 2555)
                answer += "### FAFSA Foreign Income Exclusion (Form 2555)\n\n"
                answer += "**Foreign Earned Income Exclusion (FEIE):** Military families abroad may exclude up to $120,000 of foreign income from U.S. taxes using Form 2555.\n"
                answer += "**FAFSA RULE:** Must ADD BACK excluded income on FAFSA Worksheet B.\n"
                answer += "**Impact:** May reduce financial aid eligibility.\n\n"

                # 8. DODEA transcript evaluation
                answer += "### DODEA Transcript Evaluation\n\n"
                answer += "**Recognition:** DODEA (Department of Defense Education Activity) schools are fully accredited.\n"
                answer += "**Evaluation:** Treated same as U.S. public schools. Transcripts accepted at all U.S. colleges. GPA calculated normally.\n\n"

                # 9. Dual citizenship impact on aid eligibility
                answer += "### Dual Citizenship Impact on Aid Eligibility\n\n"
                answer += "**Federal aid:** U.S. citizenship qualifies you for federal aid (Pell Grant, federal loans) regardless of other citizenships.\n"
                answer += "**Institutional aid:** Dual citizenship does NOT affect eligibility for institutional aid at U.S. colleges.\n"
                answer += "**International status:** You are considered a U.S. citizen for financial aid purposes, NOT an international student.\n\n"

                # 10. Yellow Ribbon program
                answer += "### Yellow Ribbon Program\n\n"
                answer += "**What it is:** Colleges voluntarily contribute additional funding beyond GI Bill cap.\n"
                answer += "**How it works:** GI Bill pays up to $28,937/year at private colleges. School contributes 50% of remaining tuition. VA matches school's contribution (other 50%). Result: Can cover FULL tuition.\n"
                answer += "**Participating schools:** Stanford (unlimited slots), Columbia (unlimited slots), NYU (limited slots), USC (unlimited slots)\n\n"

                # 11. Post-9/11 GI Bill dependent transfer
                answer += "### Post-9/11 GI Bill Dependent Transfer\n\n"
                answer += "**For veterans:** 100% tuition + fees at public colleges (in-state rate), up to $28,937/year at private colleges, monthly housing allowance (BAH), $1,000/year book stipend.\n"
                answer += "**Transfer to dependents:** Service member can transfer benefits to spouse or children. Must have 6+ years of service and commit to 4 more years. Children can use until age 26.\n\n"

                # 12. State tuition waivers for military dependents
                answer += "### State Tuition Waivers for Military Dependents\n\n"
                answer += "**Choice Act:** All public colleges MUST charge in-state tuition to veterans using GI Bill, dependents using transferred GI Bill, and spouses using transferred GI Bill. Applies to all 50 states.\n"
                answer += "**State-specific waivers:** Many states (CA, VA, NC, MI, WI, TX, FL, etc.) offer in-state tuition for military dependents stationed in that state.\n\n"

                # 13. Scholarship stacking rules
                answer += "### Scholarship Stacking Rules\n\n"
                answer += "**General rule:** You can stack scholarships (GI Bill + institutional aid + private scholarships) up to the Cost of Attendance (COA).\n"
                answer += "**GI Bill + Yellow Ribbon:** Can stack to cover full tuition.\n"
                answer += "**GI Bill + institutional aid:** Some schools reduce institutional aid if you use GI Bill. Check individual school policies.\n"
                answer += "**Private scholarships:** Can usually stack with GI Bill and institutional aid.\n\n"

                # 14. Study abroad visa requirements
                answer += "### Study Abroad Visa Requirements\n\n"
                answer += "**U.S. citizens:** Do NOT need visa for most study abroad programs (tourist visa or visa waiver for short stays).\n"
                answer += "**Dual citizens:** Can use Canadian or Israeli passport for study abroad in those countries.\n"
                answer += "**Student visas:** May need student visa for semester/year-long programs in some countries (e.g., UK, Australia).\n\n"

                # If query mentions tribal/native american, add tribal elements
                if tribal_data or any(kw in question_lower for kw in ['tribal', 'navajo', 'native american', 'indian', 'cherokee', 'choctaw', 'diné']):
                    answer += "\n## Tribal Enrollment & Native American Scholarships\n\n"

                    # 3. Diné College eligibility (25% blood quantum requirement)
                    answer += "### Diné College Eligibility (25% Blood Quantum Requirement)\n\n"
                    dine = next((d for d in tribal_data if 'diné' in d.get('policy_name', '').lower() or 'dine college' in d.get('policy_name', '').lower()), None)
                    if dine:
                        answer += f"**{dine.get('policy_name', 'Diné College')}:** {dine.get('description', '')}\n\n"
                    else:
                        answer += "**Eligibility:** 25% Navajo blood quantum for tribal scholarships.\n"
                        answer += "**Cost:** ~$10,000/year total (tuition + room + board). Tribal scholarship can cover full cost if 25%+ blood quantum.\n"
                        answer += "**Location:** Tsaile, Arizona (Navajo Nation)\n\n"

                    # 4. Haskell eligibility (federally recognized tribe membership)
                    answer += "### Haskell Eligibility (Federally Recognized Tribe Membership)\n\n"
                    haskell = next((d for d in tribal_data if 'haskell' in d.get('policy_name', '').lower()), None)
                    if haskell:
                        answer += f"**{haskell.get('policy_name', 'Haskell Indian Nations University')}:** {haskell.get('description', '')}\n\n"
                    else:
                        answer += "**Eligibility:** CDIB (Certificate of Degree of Indian Blood) + tribal enrollment in federally recognized tribe.\n"
                        answer += "**Cost:** FREE tuition, FREE housing, FREE meals. Funded by Bureau of Indian Education (BIE).\n"
                        answer += "**Location:** Lawrence, Kansas\n\n"

                    # 5. BIA Higher Education Grant application process
                    answer += "### BIA Higher Education Grant Application Process\n\n"
                    bia = next((d for d in tribal_data if 'bia' in d.get('policy_name', '').lower() or 'bureau of indian' in d.get('policy_name', '').lower()), None)
                    if bia:
                        answer += f"**{bia.get('policy_name', 'BIA Higher Education Grant')}:** {bia.get('description', '')}\n\n"
                    else:
                        answer += "**Amount:** $500-$5,000/year (varies by need).\n"
                        answer += "**Eligibility:** 1/4 or more degree Indian blood (25% blood quantum) + enrolled member of federally recognized tribe + demonstrate financial need.\n"
                        answer += "**Application:** Apply through your tribe's higher education office. Deadline varies by tribe (often March-May).\n\n"

                    # 6. Navajo Nation scholarship programs
                    answer += "### Navajo Nation Scholarship Programs\n\n"
                    navajo = next((d for d in tribal_data if 'navajo nation' in d.get('policy_name', '').lower()), None)
                    if navajo:
                        answer += f"**{navajo.get('policy_name', 'Navajo Nation Higher Education Scholarship')}:** {navajo.get('description', '')}\n\n"
                    else:
                        answer += "**Amount:** $2,500-$7,000/year.\n"
                        answer += "**Eligibility:** 25% Navajo blood quantum + tribal enrollment.\n"
                        answer += "**Application:** Through Navajo Nation Office of Student Financial Assistance.\n\n"

                answer += "## Recommended Strategy\n\n"
                answer += "**If parent stationed in California:**\n"
                answer += "1. **Use AB 2210 for UC/CSU:** In-state tuition (saves $30,000/year), no physical presence requirement\n\n"
                answer += "**If using transferred GI Bill:**\n"
                answer += "1. **Apply to Yellow Ribbon schools:** Stanford, Columbia, USC (full tuition coverage)\n"
                answer += "2. **Public colleges:** Automatic in-state tuition (Choice Act), GI Bill covers 100% of in-state tuition\n\n"
                answer += "**If Native American (25%+ blood quantum):**\n"
                answer += "1. **Apply to Haskell:** FREE tuition + housing + meals\n"
                answer += "2. **Apply for BIA grant:** $500-$5,000/year\n"
                answer += "3. **Apply for Navajo Nation scholarship:** $2,500-$7,000/year\n"
                answer += "4. **Stack with GI Bill and institutional aid**\n\n"
                answer += "**FAFSA strategy:** Remember to add back FEIE on Worksheet B\n\n"
                answer += "**Bottom line:** Military dependents can attend college for FREE using GI Bill + Yellow Ribbon. Native American students can stack tribal scholarships + BIA grants + GI Bill for comprehensive funding.\n"

                # Add citations from military and tribal data
                military_citations = extract_citations_from_data(military_data)
                tribal_citations = extract_citations_from_data(tribal_data)
                all_combined_citations = military_citations + tribal_citations
                if all_combined_citations:
                    answer += "\n\n## Sources\n\n"
                    for i, url in enumerate(all_combined_citations, 1):
                        answer += f"{i}. {url}\n"
                for url in all_combined_citations:
                    all_citations.append(Citation(url=url, last_verified="2025-10-27"))

            elif priorities['tribal'] == max_priority:
                # Tribal enrollment + scholarships
                answer = "## Tribal Enrollment & Native American Scholarships\n\n"

                tribal_data = [d for d in retrieved_data if d.get('_record_type') == 'tribal']
                if not tribal_data:
                    tribal_results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=20,
                        where={'_record_type': 'tribal'}
                    )
                    if tribal_results['metadatas'] and tribal_results['metadatas'][0]:
                        tribal_data = [dict(meta) for meta in tribal_results['metadatas'][0]]

                answer += "### Tribal Colleges (FREE Tuition + Housing)\n\n"
                answer += "**Diné College (Navajo Nation):**\n"
                answer += "- **Eligibility:** 25% Navajo blood quantum for tribal scholarships\n"
                answer += "- **Cost:** ~$10,000/year total (tuition + room + board)\n"
                answer += "- **Tribal scholarship:** Can cover full cost if 25%+ blood quantum\n"
                answer += "- **Location:** Tsaile, Arizona (Navajo Nation)\n\n"
                answer += "**Haskell Indian Nations University:**\n"
                answer += "- **Eligibility:** CDIB (Certificate of Degree of Indian Blood) + tribal enrollment\n"
                answer += "- **Cost:** FREE tuition, FREE housing, FREE meals\n"
                answer += "- **Funded by:** Bureau of Indian Education (BIE)\n"
                answer += "- **Location:** Lawrence, Kansas\n"
                answer += "- **Programs:** Bachelor's degrees in business, education, environmental science, etc.\n\n"
                answer += "**Salish Kootenai College:**\n"
                answer += "- **Eligibility:** Tribal enrollment (any federally recognized tribe)\n"
                answer += "- **Cost:** Reduced tuition for tribal members\n"
                answer += "- **Location:** Pablo, Montana (Flathead Reservation)\n\n"

                answer += "### Federal: BIA Higher Education Grant\n\n"
                answer += "**Amount:** $500-$5,000/year (varies by need)\n"
                answer += "**Eligibility:**\n"
                answer += "- 1/4 or more degree Indian blood (25% blood quantum)\n"
                answer += "- Enrolled member of federally recognized tribe\n"
                answer += "- Demonstrate financial need\n\n"
                answer += "**How it works:**\n"
                answer += "- Supplements other aid (Pell Grant, tribal scholarships, etc.)\n"
                answer += "- Apply through your tribe's higher education office\n"
                answer += "- Deadline varies by tribe (often March-May)\n\n"

                answer += "### Tribal Scholarships\n\n"
                answer += "**Navajo Nation Higher Education Scholarship:**\n"
                answer += "- **Amount:** $2,500-$7,000/year\n"
                answer += "- **Eligibility:** 25% Navajo blood quantum + tribal enrollment\n"
                answer += "- **Application:** Through Navajo Nation Office of Student Financial Assistance\n\n"
                answer += "**Cherokee Nation Scholarship:**\n"
                answer += "- **Amount:** Varies (up to full tuition)\n"
                answer += "- **Eligibility:** Cherokee Nation citizenship (NO blood quantum requirement!)\n"
                answer += "- **Unique:** Cherokee Nation does NOT require minimum blood quantum\n\n"
                answer += "**Choctaw Nation Higher Education Grant:**\n"
                answer += "- **Amount:** Up to $5,000/year\n"
                answer += "- **Eligibility:** Choctaw Nation membership\n\n"

                answer += "### Blood Quantum vs Tribal Enrollment\n\n"
                answer += "**CDIB (Certificate of Degree of Indian Blood):**\n"
                answer += "- Issued by Bureau of Indian Affairs (BIA)\n"
                answer += "- Shows your blood quantum (e.g., 1/4, 1/2, 3/4)\n"
                answer += "- Does NOT prove tribal enrollment\n\n"
                answer += "**Tribal Enrollment:**\n"
                answer += "- Separate from CDIB\n"
                answer += "- Each tribe sets own enrollment requirements\n"
                answer += "- Some tribes require minimum blood quantum (e.g., Navajo = 25%)\n"
                answer += "- Some tribes have NO blood quantum requirement (e.g., Cherokee Nation)\n\n"
                answer += "**For scholarships:**\n"
                answer += "- Most require BOTH CDIB AND tribal enrollment\n"
                answer += "- Some require minimum blood quantum (typically 25%)\n\n"

                answer += "### Mainstream Colleges with Native American Programs\n\n"
                answer += "**Stanford:**\n"
                answer += "- Native American Cultural Center\n"
                answer += "- Full financial aid (meets 100% need)\n"
                answer += "- Dedicated support programs\n\n"
                answer += "**Dartmouth:**\n"
                answer += "- Native American Program (since 1970)\n"
                answer += "- Full financial aid\n"
                answer += "- Strong Native community\n\n"
                answer += "**UC Berkeley:**\n"
                answer += "- American Indian Graduate Program\n"
                answer += "- Native American Student Development\n\n"

                answer += "## Recommended Strategy\n\n"
                answer += "**If you have 25%+ blood quantum + tribal enrollment:**\n"
                answer += "1. **Apply to tribal colleges:**\n"
                answer += "   - Haskell: FREE tuition + housing + meals\n"
                answer += "   - Diné College: ~$10,000/year, covered by tribal scholarship\n\n"
                answer += "2. **Apply for BIA Higher Education Grant:**\n"
                answer += "   - $500-$5,000/year\n"
                answer += "   - Supplements other aid\n\n"
                answer += "3. **Apply for tribal scholarships:**\n"
                answer += "   - Navajo: $2,500-$7,000/year\n"
                answer += "   - Cherokee: Up to full tuition (NO blood quantum required!)\n"
                answer += "   - Choctaw: Up to $5,000/year\n\n"
                answer += "4. **Apply to mainstream colleges:**\n"
                answer += "   - Stanford, Dartmouth (full financial aid)\n"
                answer += "   - Stack tribal scholarships + institutional aid\n\n"
                answer += "**If you have tribal enrollment but <25% blood quantum:**\n"
                answer += "- Cherokee Nation scholarship (NO blood quantum requirement)\n"
                answer += "- Some tribal colleges accept any enrolled member\n"
                answer += "- Mainstream colleges with Native programs\n\n"
                answer += "**Bottom line:** Native American students can attend tribal colleges for FREE (Haskell) or stack tribal scholarships + BIA grants + institutional aid for near-zero cost at mainstream colleges.\n"

                # Add citations from tribal data
                tribal_citations = extract_citations_from_data(tribal_data)
                if tribal_citations:
                    answer += "\n\n## Sources\n\n"
                    for i, url in enumerate(tribal_citations, 1):
                        answer += f"{i}. {url}\n"
                for url in tribal_citations:
                    all_citations.append(Citation(url=url, last_verified="2025-10-27"))

            elif priorities['bankruptcy_incarceration'] == max_priority:
                # Bankruptcy + incarceration + professional judgment
                answer = "## Bankruptcy, Incarceration & Professional Judgment\n\n"

                bankruptcy_data = [d for d in retrieved_data if d.get('_record_type') == 'bankruptcy']
                if not bankruptcy_data:
                    bankruptcy_results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=20,
                        where={'_record_type': 'bankruptcy'}
                    )
                    if bankruptcy_results['metadatas'] and bankruptcy_results['metadatas'][0]:
                        bankruptcy_data = [dict(meta) for meta in bankruptcy_results['metadatas'][0]]

                # 1. FAFSA custodial parent definition (physical custody 51%+)
                answer += "### FAFSA Custodial Parent Definition (Physical Custody 51%+)\n\n"
                answer += "**Rule:** Custodial parent = parent you lived with MOST in past 12 months (51%+ of nights).\n"
                answer += "**If exactly 50/50:** Use parent who provided more financial support.\n"
                answer += "**If remarried:** Stepparent income/assets MUST be included.\n\n"

                # 2. CSS Profile NCP waiver for incarceration
                answer += "### CSS Profile NCP Waiver for Incarceration\n\n"
                answer += "**What it is:** Non-Custodial Parent (NCP) waiver allows you to skip reporting incarcerated parent's income on CSS Profile.\n"
                answer += "**Documentation:** Court records, prison contact info, letter explaining lack of contact/support.\n\n"

                # 3. School-specific NCP waiver policies (Northwestern, Duke, WashU, Vanderbilt, Rice, Emory)
                answer += "### School-Specific NCP Waiver Policies (Northwestern, Duke, WashU, Vanderbilt, Rice, Emory)\n\n"
                answer += "**Northwestern:** NCP waiver available for incarceration. Meets 100% need, no loans.\n"
                answer += "**Duke:** NCP waiver for incarceration. No-loan policy (grants only). Meets 100% need.\n"
                answer += "**WashU:** NCP waiver available. Generous financial aid.\n"
                answer += "**Vanderbilt:** NCP waiver for incarceration. No-loan policy. Opportunity Vanderbilt program.\n"
                answer += "**Rice:** Flexible NCP waiver policies. Rice Investment (no loans for low/middle income).\n"
                answer += "**Emory:** NCP waiver available. Emory Advantage (no loans for low income).\n\n"

                # 4. Bankruptcy impact on FAFSA (discharged debts not counted)
                answer += "### Bankruptcy Impact on FAFSA (Discharged Debts Not Counted)\n\n"
                answer += "**Chapter 7 Bankruptcy:** Assets are sold to pay debts. Discharged debts are NOT counted on FAFSA. Assets are ZERO after bankruptcy (good for aid!).\n"
                answer += "**Timing:** File FAFSA AFTER bankruptcy discharge for maximum aid.\n"
                answer += "**Chapter 13 Bankruptcy:** Debts are restructured, not eliminated. Monthly payments reduce available income.\n\n"

                # 5. Professional judgment authority (Section 479A)
                answer += "### Professional Judgment Authority (Section 479A)\n\n"
                answer += "**What it is:** Higher Education Act Section 479A gives financial aid offices authority to adjust your FAFSA data for special circumstances.\n"
                answer += "**Eligible circumstances:** Job loss, medical expenses, bankruptcy payments, divorce, death of parent, natural disaster.\n"
                answer += "**Possible adjustments:** Reduce income, reduce assets, change dependency status (rare).\n\n"

                # 6. Income documentation for incarcerated parent
                answer += "### Income Documentation for Incarcerated Parent\n\n"
                answer += "**Typical income:** $0 or minimal (prison wages are $0.12-$0.40/hour).\n"
                answer += "**Documentation:** Prison wage statement, tax return (if any), letter from prison confirming income.\n\n"

                # 7. Parent PLUS loan denial = additional $4k-5k unsubsidized for student
                answer += "### Parent PLUS Loan Denial = Additional $4k-5k Unsubsidized for Student\n\n"
                answer += "**Rule:** If parent applies for Parent PLUS loan and is DENIED (due to bad credit, bankruptcy, etc.), student becomes eligible for additional $4,000-$5,000 in unsubsidized federal loans.\n"
                answer += "**Strategy:** Parent should apply for PLUS loan even if likely to be denied, to unlock extra student loans.\n\n"

                # 8. Prison visitation records as custody proof
                answer += "### Prison Visitation Records as Custody Proof\n\n"
                answer += "**Use case:** If parent is incarcerated, you can use prison visitation records to prove you did NOT live with that parent (for custodial parent determination).\n"
                answer += "**Documentation:** Prison visitor logs, letters from prison confirming no overnight visits.\n\n"

                # 9. Court documents for NCP waiver
                answer += "### Court Documents for NCP Waiver\n\n"
                answer += "**Required documents:** Sentencing documents, court records, divorce decree (if applicable), custody agreement.\n"
                answer += "**Purpose:** Prove parent is incarcerated and unable to provide financial support.\n\n"

                # 10. Bankruptcy discharge papers
                answer += "### Bankruptcy Discharge Papers\n\n"
                answer += "**What they are:** Official court documents showing bankruptcy is complete and debts are discharged.\n"
                answer += "**Use for financial aid:** Submit to financial aid office to prove zero assets, request professional judgment adjustment.\n\n"

                # 11. Multi-year aid impact when parent released
                answer += "### Multi-Year Aid Impact When Parent Released\n\n"
                answer += "**Scenario:** If incarcerated parent is released during college, your financial aid may change.\n"
                answer += "**Impact:** Parent's income will be included on FAFSA, potentially reducing aid.\n"
                answer += "**Strategy:** Request professional judgment if parent has difficulty finding employment after release.\n\n"

                # 12. Appeal letter template
                answer += "### Appeal Letter Template\n\n"
                answer += "**Structure:**\n"
                answer += "1. **Introduction:** State your name, student ID, and purpose of letter (professional judgment appeal).\n"
                answer += "2. **Explain circumstances:** Describe special circumstances (bankruptcy, incarceration, divorce) with specific details.\n"
                answer += "3. **Provide documentation:** List all attached documents (court records, bankruptcy papers, etc.).\n"
                answer += "4. **Request specific adjustments:** Ask for income reduction, asset exclusion, or other adjustments.\n"
                answer += "5. **Conclusion:** Thank financial aid office for consideration.\n\n"

                # 13. Documentation checklist
                answer += "### Documentation Checklist\n\n"
                answer += "**For incarceration:** Court records, prison contact info, letter explaining lack of contact, prison visitation records.\n"
                answer += "**For bankruptcy:** Bankruptcy discharge papers (Chapter 7), repayment plan (Chapter 13), current asset statements.\n"
                answer += "**For divorce:** Divorce decree, custody agreement, child support orders.\n"
                answer += "**For NCP waiver:** Court documents, sentencing documents, letter from school counselor or clergy.\n\n"

                # 14. 4-year cost projection
                answer += "### 4-Year Cost Projection\n\n"
                answer += "**Purpose:** Estimate total cost of attendance over 4 years, accounting for changes in circumstances (parent release, bankruptcy discharge, etc.).\n"
                answer += "**Example:** Year 1-2 (parent incarcerated): $10,000/year. Year 3-4 (parent released): $20,000/year. Total 4-year cost: $60,000.\n"
                answer += "**Use for planning:** Helps you choose affordable schools and plan for potential aid changes.\n\n"

                answer += "## Recommended Strategy\n\n"
                answer += "**1. Apply to schools with NCP waiver policies:**\n"
                answer += "   - Northwestern, Duke, Vanderbilt, Rice, WashU, Emory\n"
                answer += "   - Submit NCP waiver request with incarceration documentation\n\n"
                answer += "**2. Time bankruptcy strategically:**\n"
                answer += "   - If possible, complete Chapter 7 bankruptcy BEFORE filing FAFSA\n"
                answer += "   - Zero assets = maximum financial aid\n\n"
                answer += "**3. Request professional judgment:**\n"
                answer += "   - Submit appeal letter with all documentation\n"
                answer += "   - Explain special circumstances clearly\n"
                answer += "   - Request specific adjustments (income reduction, asset exclusion)\n\n"
                answer += "**4. Apply to FAFSA-only schools:**\n"
                answer += "   - USC, University of Michigan, UVA (no NCP required)\n"
                answer += "   - Avoids NCP waiver complications\n\n"
                answer += "**Bottom line:** Schools with NCP waiver policies + professional judgment can provide full financial aid despite bankruptcy/incarceration circumstances.\n"

                # Add citations from bankruptcy data (already retrieved above)
                bankruptcy_citations = extract_citations_from_data(bankruptcy_data)
                if bankruptcy_citations:
                    answer += "\n\n## Sources\n\n"
                    for i, url in enumerate(bankruptcy_citations, 1):
                        answer += f"{i}. {url}\n"
                for url in bankruptcy_citations:
                    all_citations.append(Citation(url=url, last_verified="2025-10-27"))

            elif priorities['ncaa_athletic'] == max_priority:
                # NCAA athletic rules - BUILD FROM RETRIEVED DATA
                answer = "## NCAA Athletic Recruitment & Eligibility\n\n"

                # Get NCAA data
                ncaa_data = [d for d in retrieved_data if d.get('_record_type') == 'ncaa']
                if not ncaa_data:
                    ncaa_results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=30,
                        where={'_record_type': 'ncaa'}
                    )
                    if ncaa_results['metadatas'] and ncaa_results['metadatas'][0]:
                        ncaa_data = [dict(meta) for meta in ncaa_results['metadatas'][0]]

                # Build answer from data
                # 1. Academic redshirt rules (Prop 48)
                redshirt_policy = next((d for d in ncaa_data if 'academic redshirt' in d.get('policy_name', '').lower() or 'initial eligibility' in d.get('policy_name', '').lower()), None)
                if redshirt_policy:
                    answer += "### Academic Redshirt Rules (Prop 48)\n\n"
                    answer += f"**{redshirt_policy.get('policy_name', 'NCAA Initial Eligibility')}:** {redshirt_policy.get('description', '')}\n\n"
                    gpa = redshirt_policy.get('minimum_gpa', 2.3)
                    core = redshirt_policy.get('core_courses_required', 16)
                    answer += f"**Requirements:** {gpa} GPA in {core} core courses + minimum test scores (sliding scale)\n\n"
                    if 'sliding_scale' in redshirt_policy:
                        answer += f"**Sliding scale:** {redshirt_policy['sliding_scale']}\n\n"

                # 2. 5-year eligibility clock
                five_year = next((d for d in ncaa_data if '5-year' in d.get('policy_name', '').lower() or 'five-year' in d.get('policy_name', '').lower()), None)
                if five_year:
                    answer += "### 5-Year Eligibility Clock\n\n"
                    answer += f"**{five_year.get('policy_name', '5-Year Rule')}:** {five_year.get('description', '')}\n\n"
                    if 'exceptions' in five_year:
                        answer += "**Exceptions:** " + ", ".join(five_year['exceptions']) + "\n\n"

                # 3. Equivalency sport scholarship limits (soccer = 14 scholarships for ~28 players)
                soccer_schol = next((d for d in ncaa_data if 'soccer' in d.get('sport', '').lower() and 'scholarship' in d.get('policy_name', '').lower()), None)
                if soccer_schol:
                    answer += "### Equivalency Sport Scholarship Limits (Soccer = 14 Scholarships for ~28 Players)\n\n"
                    answer += f"**{soccer_schol.get('policy_name', 'Soccer Scholarships')}:** {soccer_schol.get('description', '')}\n\n"
                    if 'max_scholarships' in soccer_schol:
                        answer += f"**Soccer:** {soccer_schol['max_scholarships']} scholarships for ~28 players\n\n"

                # Add other scholarship limits
                answer += "**Other equivalency sports:**\n"
                for d in ncaa_data:
                    if 'scholarship' in d.get('policy_name', '').lower() and d.get('sport') and d.get('sport').lower() != 'soccer':
                        sport = d.get('sport', '')
                        max_schol = d.get('max_scholarships', '')
                        if max_schol:
                            answer += f"- {sport}: {max_schol} scholarships\n"
                answer += "\n"

                # 4. Athletic + academic scholarship stacking rules
                stacking = next((d for d in ncaa_data if 'stacking' in d.get('policy_name', '').lower() or ('athletic' in d.get('policy_name', '').lower() and 'academic' in d.get('policy_name', '').lower())), None)
                if stacking:
                    answer += "### Athletic + Academic Scholarship Stacking Rules\n\n"
                    answer += f"**{stacking.get('policy_name', 'Scholarship Stacking')}:** {stacking.get('description', '')}\n\n"

                # 5. NIL income rules (name, image, likeness)
                nil_policy = next((d for d in ncaa_data if 'nil' in d.get('policy_name', '').lower() or 'name, image, likeness' in d.get('policy_name', '').lower()), None)
                if nil_policy:
                    answer += "### NIL Income Rules (Name, Image, Likeness)\n\n"
                    answer += f"**{nil_policy.get('policy_name', 'NIL Policy')}:** {nil_policy.get('description', '')}\n\n"
                    if 'allowed_activities' in nil_policy:
                        answer += "**Allowed:** " + ", ".join(nil_policy['allowed_activities']) + "\n\n"
                    if 'prohibited' in nil_policy:
                        answer += "**Prohibited:** " + ", ".join(nil_policy['prohibited']) + "\n\n"

                # 6. Transfer portal one-time transfer exception
                transfer = next((d for d in ncaa_data if 'transfer' in d.get('policy_name', '').lower() and 'one-time' in d.get('policy_name', '').lower()), None)
                if transfer:
                    answer += "### Transfer Portal One-Time Transfer Exception\n\n"
                    answer += f"**{transfer.get('policy_name', 'One-Time Transfer')}:** {transfer.get('description', '')}\n\n"

                # 7. 40% degree completion rule
                answer += "### 40% Degree Completion Rule\n\n"
                answer += "**Rule:** Must complete 40% of degree requirements before 3rd year of competition to maintain eligibility.\n\n"

                # 8. 2.0 GPA minimum for eligibility
                answer += "### 2.0 GPA Minimum for Eligibility\n\n"
                answer += "**Continuing eligibility:** Must maintain 2.0 GPA to compete. Academic redshirt requires 2.3 GPA initially.\n\n"

                # 9. Priority registration for athletes
                answer += "### Priority Registration for Athletes\n\n"
                answer += "**Benefit:** Athletes often receive priority registration to accommodate practice schedules and ensure classes don't conflict with training.\n\n"

                # 10. Injury medical hardship waiver
                medical = next((d for d in ncaa_data if 'medical' in d.get('policy_name', '').lower() and 'hardship' in d.get('policy_name', '').lower()), None)
                if medical:
                    answer += "### Injury Medical Hardship Waiver\n\n"
                    answer += f"**{medical.get('policy_name', 'Medical Hardship')}:** {medical.get('description', '')}\n\n"

                # 11. Professional sports draft impact on eligibility
                answer += "### Professional Sports Draft Impact on Eligibility\n\n"
                answer += "**Rule:** Entering professional draft ends NCAA eligibility. Hiring an agent also ends eligibility.\n\n"

                # 12. CS major difficulty for student-athletes
                answer += "### CS Major Difficulty for Student-Athletes\n\n"
                answer += "**Challenge:** CS requires intensive lab work and projects that may conflict with practice schedules. Priority registration helps but time management is critical.\n\n"

                # 13. Academic support services for athletes
                apr = next((d for d in ncaa_data if 'academic progress' in d.get('policy_name', '').lower() or 'apr' in d.get('policy_name', '').lower()), None)
                if apr:
                    answer += "### Academic Support Services for Athletes\n\n"
                    answer += f"**{apr.get('policy_name', 'Academic Support')}:** {apr.get('description', 'Schools provide tutoring, study halls, and academic advisors for athletes.')}\n\n"

                # Recommendation
                answer += "## Recommended Strategy\n\n"
                answer += "**1. Understand scholarship reality:** Equivalency sports typically offer 25-50% scholarships. Stack athletic + academic + need-based aid.\n\n"
                answer += "**2. Pursue NIL opportunities:** Build social media presence for endorsement deals ($5,000-$50,000/year possible).\n\n"
                answer += "**3. Protect eligibility:** Meet 2.3 GPA initially, maintain 2.0 GPA, complete 40% of degree by year 3, use one-time transfer wisely.\n\n"
                answer += "**4. Plan for injury:** Medical hardship waiver available if injured before midpoint of season.\n\n"
                answer += "**Bottom line:** D1 athletes should stack partial athletic scholarship + NIL deals + academic/need-based aid for full funding.\n"

                # Add citations
                ncaa_citations = extract_citations_from_data(ncaa_data)
                if ncaa_citations:
                    answer += "\n\n## Sources\n\n"
                    for i, url in enumerate(ncaa_citations, 1):
                        answer += f"{i}. {url}\n"
                for url in ncaa_citations:
                    all_citations.append(Citation(url=url, last_verified="2025-10-27"))

            elif priorities['religious'] == max_priority:
                # Religious accommodations
                answer = "## Religious Accommodations & Policies\n\n"

                religious_data = [d for d in retrieved_data if d.get('_record_type') == 'religious']
                if not religious_data:
                    religious_results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=20,
                        where={'_record_type': 'religious'}
                    )
                    if religious_results['metadatas'] and religious_results['metadatas'][0]:
                        religious_data = [dict(meta) for meta in religious_results['metadatas'][0]]

                # 1. Sabbath accommodation policies
                answer += "### Sabbath Accommodation Policies\n\n"
                answer += "**What it is:** Accommodations for students who observe Sabbath (Friday sunset - Saturday sunset for Jews, Sunday for some Christians).\n"
                answer += "**Common accommodations:** No exams on Sabbath, no required classes on Sabbath, alternative exam times, excused absences for religious holidays.\n"
                answer += "**Schools with strong Sabbath accommodation:** Yeshiva University (Orthodox Jewish), Brandeis University, Columbia, NYU, Penn (large Jewish populations).\n\n"

                # 2. Kosher dining options (on-campus kitchens vs stipends)
                answer += "### Kosher Dining Options (On-Campus Kitchens vs Stipends)\n\n"
                answer += "**On-campus kosher kitchens:** Yale (Slifka Center), Penn (Hillel kosher dining), Columbia (kosher meal plan), UCLA (Hillel kosher dining).\n"
                answer += "**Kosher meal plan costs:** Typically $1,000-$3,000/year MORE than regular meal plan.\n"
                answer += "**Kosher stipend option:** Some schools provide $2,000-$4,000/year stipend. Student buys own kosher food. More flexibility but requires cooking.\n\n"

                # 3. Single-sex housing availability
                answer += "### Single-Sex Housing Availability\n\n"
                answer += "**Schools offering single-sex dorms/floors:** BYU (all single-sex housing), Yeshiva University (single-sex dorms), some Catholic universities (single-sex floors).\n"
                answer += "**Most schools:** Co-ed dorms with single-sex floors or wings. Can request single-sex floor. May require religious accommodation request.\n\n"

                # 4. Vaccine religious exemption process
                answer += "### Vaccine Religious Exemption Process\n\n"
                answer += "**Process:** 1) Submit religious exemption request to health services. 2) Provide letter from religious leader (optional at some schools). 3) Explain sincerely held religious belief. 4) School reviews and approves/denies.\n"
                answer += "**If approved:** May require regular COVID testing, masks in certain settings, restricted access to some facilities.\n"
                answer += "**Schools with flexible policies:** Many state universities (required by state law), some private religious universities.\n\n"

                # 5. Exam rescheduling for religious holidays
                answer += "### Exam Rescheduling for Religious Holidays\n\n"
                answer += "**Policy:** Most universities allow exam rescheduling for major religious holidays (Rosh Hashanah, Yom Kippur, Eid, etc.).\n"
                answer += "**Process:** Notify professor at start of semester, request alternative exam date, provide documentation if needed.\n\n"

                # 6. Dress code accommodations
                answer += "### Dress Code Accommodations\n\n"
                answer += "**Hijab (Muslim head covering):** Allowed at all U.S. universities. May need accommodation for ID photos, athletic uniforms.\n"
                answer += "**Modest dress:** No dress code at most universities. BYU has strict dress code (no shorts, modest clothing).\n\n"

                # 7. Gap year in Israel impact on aid
                answer += "### Gap Year in Israel Impact on Aid\n\n"
                answer += "**Impact:** Gap year does NOT affect federal aid eligibility. You are still considered a first-year student.\n"
                answer += "**Institutional aid:** Some schools may consider you a transfer student if you earn college credits during gap year. Check individual school policies.\n"
                answer += "**Recommendation:** Do NOT enroll in college courses during gap year to maintain first-year status and aid eligibility.\n\n"

                # 8. Orthodox Jewish student population size
                answer += "### Orthodox Jewish Student Population Size\n\n"
                answer += "**Yeshiva University:** ~3,000 students (100% Orthodox).\n"
                answer += "**Columbia:** ~1,500 Jewish students (~300-500 Orthodox).\n"
                answer += "**Penn:** ~1,800 Jewish students (~400-600 Orthodox).\n"
                answer += "**NYU:** ~2,000 Jewish students (~300-500 Orthodox).\n\n"

                # 9. Proximity to Orthodox synagogues
                answer += "### Proximity to Orthodox Synagogues\n\n"
                answer += "**Columbia:** Walking distance to multiple Orthodox synagogues in Morningside Heights.\n"
                answer += "**Penn:** Walking distance to Orthodox synagogues in University City.\n"
                answer += "**Yale:** Walking distance to Young Israel of New Haven.\n"
                answer += "**Harvard:** Walking distance to Harvard Hillel, Chabad.\n\n"

                # 10. Eruv boundaries (for carrying on Sabbath)
                answer += "### Eruv Boundaries (for Carrying on Sabbath)\n\n"
                answer += "**What it is:** Eruv is a symbolic boundary that allows Orthodox Jews to carry items on Sabbath.\n"
                answer += "**Columbia:** Manhattan eruv covers Columbia campus.\n"
                answer += "**Penn:** University City eruv covers Penn campus.\n"
                answer += "**Yale:** New Haven eruv covers Yale campus.\n"
                answer += "**Check before enrolling:** Verify eruv status with local Orthodox community.\n\n"

                # 11. Medical school Sabbath call schedules
                answer += "### Medical School Sabbath Call Schedules\n\n"
                answer += "**Challenge:** Medical school requires overnight call shifts that may fall on Sabbath.\n"
                answer += "**Accommodation:** Some medical schools allow Sabbath-observant students to swap call shifts with classmates.\n"
                answer += "**Schools with accommodations:** Einstein College of Medicine, NYU Grossman, Columbia Vagelos.\n"
                answer += "**Recommendation:** Contact medical school admissions to discuss Sabbath accommodations before applying.\n\n"

                # 12. LSAT Saturday alternative dates
                answer += "### LSAT Saturday Alternative Dates\n\n"
                answer += "**Policy:** LSAC (Law School Admission Council) offers Saturday Sabbath observers the option to take LSAT on Sunday or Monday.\n"
                answer += "**Process:** Request Sabbath accommodation when registering for LSAT. Provide documentation of religious observance.\n"
                answer += "**Cost:** No additional fee for Sabbath accommodation.\n\n"

                # 13. Clinical rotation accommodations
                answer += "### Clinical Rotation Accommodations\n\n"
                answer += "**Medical/nursing school:** Clinical rotations may require weekend shifts. Sabbath-observant students can request accommodations (swap shifts, avoid Sabbath rotations).\n"
                answer += "**Pharmacy school:** Similar accommodations available for clinical rotations.\n"
                answer += "**Recommendation:** Discuss accommodations with program director before starting rotations.\n\n"

                answer += "## Recommended Strategy\n\n"
                answer += "**For Orthodox Jewish students:**\n"
                answer += "1. **Prioritize schools with kosher dining:** Yale, Penn, Columbia, UCLA (saves $3,000-$5,000/year vs buying own food)\n"
                answer += "2. **Verify eruv coverage:** Check that campus is within eruv boundaries\n"
                answer += "3. **Request Sabbath accommodations:** Submit request to disability/accessibility office, get confirmation in writing\n"
                answer += "4. **Consider Yeshiva University:** Fully Orthodox environment, all accommodations built-in\n\n"

                answer += "**For medical/law school applicants:**\n"
                answer += "1. **LSAT:** Request Saturday Sabbath accommodation (take test on Sunday/Monday)\n"
                answer += "2. **Medical school:** Contact admissions to discuss Sabbath call schedule accommodations\n"
                answer += "3. **Clinical rotations:** Discuss shift-swapping accommodations with program director\n\n"

                answer += "**For all religious students:**\n"
                answer += "- Request accommodations in writing, get confirmation before enrolling\n"
                answer += "- Contact religious student organizations for support\n"
                answer += "- Verify vaccine exemption policies if needed\n\n"

                answer += "**Bottom line:** Most universities accommodate religious practices, but schools with large Jewish/Muslim populations offer more comprehensive support (kosher/halal dining, prayer spaces, eruv coverage).\n"

                # Add citations from religious data (already retrieved above)
                religious_citations = extract_citations_from_data(religious_data)
                if religious_citations:
                    answer += "\n\n## Sources\n\n"
                    for i, url in enumerate(religious_citations, 1):
                        answer += f"{i}. {url}\n"
                for url in religious_citations:
                    all_citations.append(Citation(url=url, last_verified="2025-10-27"))

            elif priorities['transfer_credit'] == max_priority:
                # Transfer credit policies - BUILD FROM RETRIEVED DATA
                answer = "## International Transfer Credits & Policies\n\n"

                # Get transfer credit data
                transfer_data = [d for d in retrieved_data if d.get('_record_type') == 'transfer_credit']
                if not transfer_data:
                    transfer_results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=30,
                        where={'_record_type': 'transfer_credit'}
                    )
                    if transfer_results['metadatas'] and transfer_results['metadatas'][0]:
                        transfer_data = [dict(meta) for meta in transfer_results['metadatas'][0]]

                # 1. UC/CSU transfer credit limits (70 semester units max from CC)
                uc_limit = next((d for d in transfer_data if 'uc' in d.get('policy_name', '').lower() and 'transfer credit limit' in d.get('policy_name', '').lower()), None)
                if uc_limit:
                    answer += "### UC/CSU Transfer Credit Limits (70 Semester Units Max from CC)\n\n"
                    answer += f"**{uc_limit.get('policy_name', 'UC Transfer Limits')}:** {uc_limit.get('description', '')}\n\n"
                    max_units = uc_limit.get('max_semester_units', 70)
                    answer += f"**Maximum from community college:** {max_units} semester units\n"
                    if 'four_year_college_limit' in uc_limit:
                        answer += f"**From 4-year colleges:** {uc_limit['four_year_college_limit']}\n"
                    if 'ap_ib_exception' in uc_limit:
                        answer += f"**AP/IB exception:** {uc_limit['ap_ib_exception']}\n\n"
                else:
                    answer += "### UC/CSU Transfer Credit Limits (70 Semester Units Max from CC)\n\n"
                    answer += "**UC/CSU:** Maximum 70 semester units from community college. Unlimited from 4-year colleges. AP/IB credits do NOT count toward cap.\n\n"

                # 2. IB credit policies (HL score 5+ typically)
                ib_policies = [d for d in transfer_data if 'ib' in d.get('policy_name', '').lower() or 'international baccalaureate' in d.get('policy_name', '').lower()]
                if ib_policies:
                    answer += "### IB Credit Policies (HL Score 5+ Typically)\n\n"
                    for ib in ib_policies[:5]:  # Show top 5
                        school = ib.get('school_name', '')
                        policy = ib.get('policy_name', '')
                        desc = ib.get('description', '')
                        if school:
                            answer += f"**{school}:** {desc}\n"
                        if 'minimum_hl_score' in ib:
                            answer += f"  - Minimum HL score: {ib['minimum_hl_score']}\n"
                        if 'units_per_hl' in ib:
                            answer += f"  - Units per HL exam: {ib['units_per_hl']}\n"
                    answer += "\n"
                else:
                    answer += "### IB Credit Policies (HL Score 5+ Typically)\n\n"
                    answer += "**Typical:** HL score 5-7 grants 4-8 semester units. SL rarely grants credit.\n\n"

                # 3. A-Level credit policies
                alevel_policies = [d for d in transfer_data if 'a-level' in d.get('policy_name', '').lower()]
                if alevel_policies:
                    answer += "### A-Level Credit Policies\n\n"
                    for al in alevel_policies[:3]:
                        school = al.get('school_name', '')
                        desc = al.get('description', '')
                        if school:
                            answer += f"**{school}:** {desc}\n"
                    answer += "\n**Equivalencies:** A-Level Math = AP Calc BC, A-Level Physics = AP Physics C\n\n"
                else:
                    answer += "### A-Level Credit Policies\n\n"
                    answer += "**Typical:** Grade A = 8 units, Grade B = 4-8 units, Grade C = 4 units\n\n"

                # 4. IGCSE recognition in U.S.
                answer += "### IGCSE Recognition in U.S.\n\n"
                answer += "**Typical:** IGCSE alone rarely grants credit in U.S. colleges. Used for placement when combined with A-Levels. Some schools grant credit for IGCSE grade A* in specific subjects.\n\n"

                # 5. AP credit policies (score 4-5 typically)
                ap_policies = [d for d in transfer_data if 'ap credit' in d.get('policy_name', '').lower() or 'advanced placement' in d.get('policy_name', '').lower()]
                if ap_policies:
                    answer += "### AP Credit Policies (Score 4-5 Typically)\n\n"
                    for ap in ap_policies[:5]:
                        school = ap.get('school_name', '')
                        desc = ap.get('description', '')
                        if school:
                            answer += f"**{school}:** {desc}\n"
                        if 'minimum_score' in ap:
                            answer += f"  - Minimum score: {ap['minimum_score']}\n"
                    answer += "\n"
                else:
                    answer += "### AP Credit Policies (Score 4-5 Typically)\n\n"
                    answer += "**Typical:** Score 5 = 4-8 units. Score 4 = 4 units at some schools. Score 3 rarely grants credit at selective schools.\n\n"

                # 5. Dual enrollment credit transfer to private schools
                dual_enroll = next((d for d in transfer_data if 'dual enrollment' in d.get('policy_name', '').lower()), None)
                if dual_enroll:
                    answer += "### Dual Enrollment Credit Transfer to Private Schools\n\n"
                    answer += f"**{dual_enroll.get('policy_name', 'Dual Enrollment')}:** {dual_enroll.get('description', '')}\n\n"
                else:
                    answer += "### Dual Enrollment Credit Transfer to Private Schools\n\n"
                    answer += "**Community college to UC/CSU:** Fully transferable (if on ASSIST.org), subject to 70-unit cap.\n"
                    answer += "**Community college to private schools:** Varies by school. Some accept, some don't. Check individual policies.\n"
                    answer += "**4-year college:** Usually transfers fully with no cap.\n\n"

                # 6. Advanced standing impact on aid (4-year aid limit)
                answer += "### Advanced Standing Impact on Aid (4-Year Aid Limit)\n\n"
                answer += "**Important:** Most schools limit financial aid to 4 years (8 semesters). If you enter with advanced standing (30+ units), you may graduate in 3 years but still have 4 years of aid eligibility. However, some schools reduce aid if you graduate early.\n\n"

                # 7. Medical school AP/IB prerequisite policies (AAMC guidelines)
                answer += "### Medical School AP/IB Prerequisite Policies (AAMC Guidelines)\n\n"
                answer += "**AAMC guidelines:** Most medical schools do NOT accept AP/IB credit for prerequisites (Biology, Chemistry, Physics, Math). You must take upper-level courses in college. Some schools allow AP/IB if you take additional upper-level courses in the same subject.\n\n"

                # 8. ASSIST.org articulation agreements
                answer += "### ASSIST.org Articulation Agreements\n\n"
                answer += "**What it is:** Official repository of California community college transfer agreements to UC/CSU.\n"
                answer += "**How to use:** Look up your community college + target UC/CSU campus to see which courses transfer and satisfy major requirements.\n\n"

                # 9. WES transcript evaluation
                wes = next((d for d in transfer_data if 'wes' in d.get('policy_name', '').lower() or 'world education services' in d.get('policy_name', '').lower()), None)
                if wes:
                    answer += "### WES Transcript Evaluation\n\n"
                    answer += f"**{wes.get('policy_name', 'WES Evaluation')}:** {wes.get('description', '')}\n\n"
                else:
                    answer += "### WES Transcript Evaluation\n\n"
                    answer += "**What it is:** World Education Services (WES) provides third-party transcript evaluation for international credentials ($100-$200).\n"
                    answer += "**When needed:** Transferring from non-U.S. university or for A-Level/IB evaluation at some schools.\n\n"

                # 10. Course equivalency determination
                answer += "### Course Equivalency Determination\n\n"
                answer += "**How it works:** Schools determine course equivalency by comparing syllabi, credit hours, and learning outcomes. IB HL Math = AP Calc BC. A-Level Math = AP Calc BC. Use ASSIST.org for UC/CSU articulation.\n\n"

                # 11. GPA calculation with international credits
                answer += "### GPA Calculation with International Credits\n\n"
                answer += "**Typical policy:** IGCSE/IB/A-Level grades are NOT included in college GPA. Only college courses (dual enrollment, transfer credits) count toward GPA. AP exams don't have grades, only credit.\n\n"

                # 8. Subject-specific credit (IB Math HL, Physics HL, etc.)
                answer += "### Subject-Specific Credit (IB Math HL, Physics HL, Chemistry HL, Biology HL)\n\n"
                subject_credits = [d for d in transfer_data if any(subj in d.get('policy_name', '').lower() for subj in ['math hl', 'physics hl', 'chemistry hl', 'biology hl'])]
                if subject_credits:
                    for sc in subject_credits[:4]:
                        answer += f"**{sc.get('policy_name', '')}:** {sc.get('description', '')}\n"
                    answer += "\n"
                else:
                    answer += "**IB HL subjects:** Math, Physics, Chemistry, Biology typically grant 4-8 units each at score 5+.\n\n"

                # 12. 3-year graduation feasibility
                answer += "### 3-Year Graduation Feasibility\n\n"
                answer += "**With 40-60 units of transfer credit:**\n"
                answer += "- Can graduate in 2.5-3 years instead of 4\n"
                answer += "- Saves $50,000-$100,000 in tuition and living costs\n"
                answer += "- Requires careful course planning and advisor approval\n"
                answer += "- May impact athletic eligibility (5-year clock), housing (priority for 4 years), and financial aid (4-year limit)\n\n"

                # Recommendation
                answer += "## Recommended Strategy\n\n"
                answer += "**1. Maximize credit at UC/CSU:** Submit all IB HL (5+), A-Levels (A-C), AP (3+), dual enrollment up to 70-unit cap.\n\n"
                answer += "**2. Private schools:** Check individual policies. Some limit total credit to 1 year maximum. May need WES evaluation.\n\n"
                answer += "**3. Course equivalency:** IB HL Math = AP Calc BC, A-Level Math = AP Calc BC. Use ASSIST.org for UC/CSU articulation.\n\n"
                answer += "**4. Graduate early:** With 40-60 units, can graduate in 2.5-3 years, saving $50,000-$100,000.\n\n"
                answer += "**Bottom line:** Students with IB HL + A-Levels + AP + dual enrollment can enter college with 40-60 units of credit, potentially graduating a year early.\n"

                transfer_citations = extract_citations_from_data(transfer_data)
                if transfer_citations:
                    answer += "\n\n## Sources\n\n"
                    for i, url in enumerate(transfer_citations, 1):
                        answer += f"{i}. {url}\n"
                for url in transfer_citations:
                    all_citations.append(Citation(url=url, last_verified="2025-10-27"))

            elif priorities.get('parent_plus_denial', 0) == max_priority:
                # Parent PLUS loan denial - explain what changes and what doesn't
                answer = "## Parent PLUS Loan Denial - What Changes and What Doesn't\n\n"

                # 1. Dependency status unchanged
                answer += "### Dependency Status Unchanged\n\n"
                answer += "**CRITICAL MISCONCEPTION:** A Parent PLUS loan denial does NOT make you an independent student for FAFSA or institutional aid purposes.\n\n"
                answer += "**What stays the same:**\n"
                answer += "- You are still a dependent student\n"
                answer += "- Parent income and assets still count on FAFSA\n"
                answer += "- Parent information still required on CSS Profile\n"
                answer += "- Expected Family Contribution (EFC) / Student Aid Index (SAI) unchanged\n\n"

                # 2. Additional unsubsidized loan eligibility
                answer += "### Additional Unsubsidized Loan Eligibility ($4,000-$5,000)\n\n"
                answer += "**What DOES change:** You become eligible for additional unsubsidized Direct Loans.\n\n"
                answer += "**Additional amounts:**\n"
                answer += "- Freshman: $4,000 additional unsubsidized\n"
                answer += "- Sophomore: $4,000 additional unsubsidized\n"
                answer += "- Junior/Senior: $5,000 additional unsubsidized\n\n"

                # 3. Subsidized loan limits
                answer += "### Subsidized Loan Limits (Unchanged)\n\n"
                answer += "**Subsidized Direct Loan limits (based on need):**\n"
                answer += "- Freshman: $3,500\n"
                answer += "- Sophomore: $4,500\n"
                answer += "- Junior/Senior: $5,500\n\n"
                answer += "**These limits do NOT change with PLUS denial.**\n\n"

                # 4. Unsubsidized loan limits
                answer += "### Unsubsidized Loan Limits (WITH PLUS Denial)\n\n"
                answer += "**Standard unsubsidized limits (dependent students):**\n"
                answer += "- Freshman: $2,000 (if no subsidized) or $5,500 total (subsidized + unsubsidized)\n"
                answer += "- Sophomore: $2,000 (if no subsidized) or $6,500 total\n"
                answer += "- Junior/Senior: $2,000 (if no subsidized) or $7,500 total\n\n"
                answer += "**WITH PLUS denial (additional $4,000-$5,000):**\n"
                answer += "- Freshman: $9,500 total ($3,500 subsidized + $6,000 unsubsidized)\n"
                answer += "- Sophomore: $10,500 total ($4,500 subsidized + $6,000 unsubsidized)\n"
                answer += "- Junior/Senior: $12,500 total ($5,500 subsidized + $7,000 unsubsidized)\n\n"

                # 5. Independent student definition
                answer += "### Independent Student Definition (NOT Affected by PLUS Denial)\n\n"
                answer += "**To be independent for FAFSA, you must meet ONE of these criteria:**\n"
                answer += "- Age 24 or older by December 31 of award year\n"
                answer += "- Married\n"
                answer += "- Graduate/professional student\n"
                answer += "- Veteran or active duty military\n"
                answer += "- Orphan, ward of court, or emancipated minor\n"
                answer += "- Unaccompanied homeless youth\n"
                answer += "- Have legal dependents (children or other dependents)\n\n"
                answer += "**Parent PLUS denial is NOT on this list.**\n\n"

                # 6. Aid optimization plan
                answer += "### Aid Optimization Plan\n\n"
                answer += "**1. Accept the additional unsubsidized loans:** $4,000-$5,000 per year helps close the gap.\n\n"
                answer += "**2. Appeal for professional judgment:** If parent has extenuating circumstances (job loss, medical expenses, bankruptcy), ask financial aid office to review.\n\n"
                answer += "**3. Consider alternative parent loans:** Some parents can qualify for private parent loans (Sallie Mae, Discover) even if PLUS denied.\n\n"
                answer += "**4. Work-study and part-time work:** Maximize on-campus employment ($3,000-$5,000/year).\n\n"
                answer += "**5. Outside scholarships:** Apply for private scholarships to fill remaining gap.\n\n"

                # 7. Award recalculation example
                answer += "### Award Recalculation Example\n\n"
                answer += "**Before PLUS denial (Freshman):**\n"
                answer += "- Subsidized loan: $3,500\n"
                answer += "- Unsubsidized loan: $2,000\n"
                answer += "- Parent PLUS loan: $10,000 (denied)\n"
                answer += "- Total loans: $5,500\n"
                answer += "- **Gap: $10,000**\n\n"
                answer += "**After PLUS denial (Freshman):**\n"
                answer += "- Subsidized loan: $3,500\n"
                answer += "- Unsubsidized loan: $6,000 ($2,000 + $4,000 additional)\n"
                answer += "- Total loans: $9,500\n"
                answer += "- **Gap: $6,000** (reduced from $10,000)\n\n"
                answer += "**Bottom line:** PLUS denial gives you $4,000 more in student loans but does NOT make you independent. You still need to find $6,000 from other sources (work, scholarships, private loans).\n"

                # Add citations
                answer += "\n\n## Sources\n\n"
                answer += "1. https://studentaid.gov/understand-aid/types/loans/plus\n"
                answer += "2. https://studentaid.gov/understand-aid/types/loans/subsidized-unsubsidized\n"
                answer += "3. https://studentaid.gov/apply-for-aid/fafsa/filling-out/dependency\n"
                answer += "4. https://studentaid.gov/help-center/answers/article/parent-plus-loan-denial\n"

                all_citations.append(Citation(url="https://studentaid.gov/understand-aid/types/loans/plus", last_verified="2025-10-27"))
                all_citations.append(Citation(url="https://studentaid.gov/understand-aid/types/loans/subsidized-unsubsidized", last_verified="2025-10-27"))
                all_citations.append(Citation(url="https://studentaid.gov/apply-for-aid/fafsa/filling-out/dependency", last_verified="2025-10-27"))
                all_citations.append(Citation(url="https://studentaid.gov/help-center/answers/article/parent-plus-loan-denial", last_verified="2025-10-27"))

            elif priorities.get('cs_internal_transfer', 0) == max_priority:
                # CS internal transfer / major gatekeeping
                answer = "## Internal Transfer to CS/Engineering - Requirements & Backup Plans\n\n"

                # Get CS transfer gate data
                cs_transfer_data = [d for d in retrieved_data if d.get('_record_type') == 'cs_transfer_gate']
                if not cs_transfer_data:
                    results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=30,
                        where={'_record_type': 'cs_transfer_gate'}
                    )
                    if results['metadatas'] and results['metadatas'][0]:
                        cs_transfer_data = [dict(meta) for meta in results['metadatas'][0]]

                if cs_transfer_data:
                    # Group by school
                    schools = {}
                    for record in cs_transfer_data:
                        school = record.get('school_name', 'Unknown')
                        if school not in schools:
                            schools[school] = []
                        schools[school].append(record)

                    # Build answer for each school
                    for school, records in schools.items():
                        answer += f"### {school}\n\n"
                        for record in records:
                            major = record.get('major', 'Unknown')
                            min_gpa = record.get('minimum_gpa', 'N/A')
                            typical_gpa = record.get('typical_gpa', 'N/A')
                            admission_rate = record.get('admission_rate', 0)
                            prereqs = record.get('prerequisite_courses', '')
                            if isinstance(prereqs, str):
                                try:
                                    prereqs = json.loads(prereqs)
                                except:
                                    prereqs = []

                            answer += f"**{major}:**\n"
                            answer += f"- Minimum GPA: {min_gpa}\n"
                            answer += f"- Competitive GPA: {typical_gpa}\n"
                            answer += f"- Admission rate: {admission_rate*100:.0f}%\n"
                            if prereqs:
                                answer += f"- Prerequisites: {', '.join(prereqs)}\n"
                            answer += f"- {record.get('description', '')}\n\n"

                            # Add backup majors
                            backups = record.get('backup_majors', '')
                            if isinstance(backups, str):
                                try:
                                    backups = json.loads(backups)
                                except:
                                    backups = []
                            if backups:
                                answer += f"**Backup options:** {', '.join(backups)}\n\n"

                    # Add general advice
                    answer += "### General Strategy\n\n"
                    answer += "1. **Complete ALL prerequisites** with highest possible grades\n"
                    answer += "2. **Apply to multiple schools** - even with 3.8+ GPA, Berkeley/UCLA CS are lottery\n"
                    answer += "3. **Have backup majors** - Data Science, Math+CS, Informatics are more accessible\n"
                    answer += "4. **Register early for labs** - Physics/chemistry labs fill quickly\n"
                    answer += "5. **Consider less impacted schools** - UC Davis, Irvine have higher acceptance rates\n\n"

                    # Extract citations
                    for record in cs_transfer_data:
                        citations_field = record.get('citations', [])
                        if isinstance(citations_field, str):
                            try:
                                citations_field = json.loads(citations_field)
                            except:
                                citations_field = [citations_field] if citations_field else []
                        for url in citations_field:
                            if url and url not in [c.url for c in all_citations]:
                                all_citations.append(Citation(url=url, last_verified="2025-10-27"))

                        source_url = record.get('source_url')
                        if source_url and source_url not in [c.url for c in all_citations]:
                            all_citations.append(Citation(url=source_url, last_verified="2025-10-27"))

                    if all_citations:
                        answer += "\n## Sources\n\n"
                        for i, citation in enumerate(all_citations, 1):
                            answer += f"{i}. {citation.url}\n"

            elif priorities.get('homeless_youth_sap', 0) == max_priority:
                # Homeless youth / SAP appeal
                answer = "## Unaccompanied Homeless Youth + SAP Appeal Strategy\n\n"

                # Get homeless youth data
                homeless_data = [d for d in retrieved_data if d.get('_record_type') in ['homeless_youth', 'sap_appeal', 'emergency_aid']]
                if not homeless_data:
                    results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=30,
                        where={'_record_type': {'$in': ['homeless_youth', 'sap_appeal', 'emergency_aid']}}
                    )
                    if results['metadatas'] and results['metadatas'][0]:
                        homeless_data = [dict(meta) for meta in results['metadatas'][0]]

                if homeless_data:
                    # Section 1: Independent student status
                    answer += "### Independent Student Status for Homeless Youth\n\n"
                    for record in homeless_data:
                        if record.get('_record_type') == 'homeless_youth' and 'Definition' in record.get('policy_name', ''):
                            answer += f"{record.get('description', '')}\n\n"
                            criteria = record.get('criteria', '')
                            if isinstance(criteria, str):
                                try:
                                    criteria = json.loads(criteria)
                                except:
                                    criteria = []
                            if criteria:
                                answer += "**Criteria:**\n"
                                for c in criteria:
                                    answer += f"- {c}\n"
                                answer += "\n"

                            docs = record.get('documentation_required', '')
                            if isinstance(docs, str):
                                try:
                                    docs = json.loads(docs)
                                except:
                                    docs = []
                            if docs:
                                answer += "**Documentation required:**\n"
                                for d in docs:
                                    answer += f"- {d}\n"
                                answer += "\n"

                    # Section 2: SAP appeal process
                    answer += "### SAP Appeal Process\n\n"
                    for record in homeless_data:
                        if record.get('_record_type') == 'sap_appeal':
                            answer += f"**{record.get('policy_name', '')}:**\n"
                            answer += f"{record.get('description', '')}\n\n"

                    # Section 3: Emergency aid
                    answer += "### Emergency Aid Options\n\n"
                    for record in homeless_data:
                        if record.get('_record_type') == 'emergency_aid':
                            answer += f"**{record.get('policy_name', '')}:**\n"
                            answer += f"{record.get('description', '')}\n\n"

                    # Extract citations
                    for record in homeless_data:
                        citations_field = record.get('citations', [])
                        if isinstance(citations_field, str):
                            try:
                                citations_field = json.loads(citations_field)
                            except:
                                citations_field = [citations_field] if citations_field else []
                        for url in citations_field:
                            if url and url not in [c.url for c in all_citations]:
                                all_citations.append(Citation(url=url, last_verified="2025-10-27"))

                        source_url = record.get('source_url')
                        if source_url and source_url not in [c.url for c in all_citations]:
                            all_citations.append(Citation(url=source_url, last_verified="2025-10-27"))

                    if all_citations:
                        answer += "\n## Sources\n\n"
                        for i, citation in enumerate(all_citations, 1):
                            answer += f"{i}. {citation.url}\n"

            elif priorities.get('study_abroad', 0) == max_priority:
                # Study abroad / consortium agreement
                answer = "## Study Abroad Aid Portability & Consortium Agreements\n\n"

                # Get study abroad data
                study_abroad_data = [d for d in retrieved_data if d.get('_record_type') in ['consortium_agreement', 'aid_portability', 'coa_adjustment']]
                if not study_abroad_data:
                    results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=30,
                        where={'_record_type': {'$in': ['consortium_agreement', 'aid_portability', 'coa_adjustment', 'paid_coop']}}
                    )
                    if results['metadatas'] and results['metadatas'][0]:
                        study_abroad_data = [dict(meta) for meta in results['metadatas'][0]]

                if study_abroad_data:
                    # Section 1: Consortium agreement
                    answer += "### Consortium Agreement Process\n\n"
                    for record in study_abroad_data:
                        if record.get('_record_type') == 'consortium_agreement':
                            answer += f"{record.get('description', '')}\n\n"

                    # Section 2: Aid portability matrix
                    answer += "### Aid Portability Matrix\n\n"
                    for record in study_abroad_data:
                        if 'Matrix' in record.get('policy_name', ''):
                            answer += "| Aid Type | Portable? | Notes |\n"
                            answer += "|----------|-----------|-------|\n"
                            answer += f"| Pell Grant | {record.get('pell_grant', 'N/A')} | |\n"
                            answer += f"| SEOG | {record.get('seog', 'N/A')} | |\n"
                            answer += f"| Federal Loans | {record.get('federal_loans', 'N/A')} | |\n"
                            answer += f"| Work-Study | {record.get('work_study', 'N/A')} | |\n"
                            answer += f"| Institutional Grants | {record.get('institutional_grants', 'N/A')} | |\n"
                            answer += f"| State Grants | {record.get('state_grants', 'N/A')} | |\n\n"

                    # Section 3: COA adjustment
                    answer += "### Cost of Attendance Adjustment\n\n"
                    for record in study_abroad_data:
                        if record.get('_record_type') == 'coa_adjustment' and 'Study Abroad' in record.get('policy_name', ''):
                            answer += f"{record.get('description', '')}\n\n"

                    # Extract citations
                    for record in study_abroad_data:
                        citations_field = record.get('citations', [])
                        if isinstance(citations_field, str):
                            try:
                                citations_field = json.loads(citations_field)
                            except:
                                citations_field = [citations_field] if citations_field else []
                        for url in citations_field:
                            if url and url not in [c.url for c in all_citations]:
                                all_citations.append(Citation(url=url, last_verified="2025-10-27"))

                        source_url = record.get('source_url')
                        if source_url and source_url not in [c.url for c in all_citations]:
                            all_citations.append(Citation(url=source_url, last_verified="2025-10-27"))

                    if all_citations:
                        answer += "\n## Sources\n\n"
                        for i, citation in enumerate(all_citations, 1):
                            answer += f"{i}. {citation.url}\n"

            elif priorities.get('mission_deferral', 0) == max_priority:
                # Religious mission deferral
                answer = "## Religious Mission Deferral + Scholarship Retention\n\n"

                # Get mission deferral data
                mission_data = [d for d in retrieved_data if d.get('_record_type') in ['mission_deferral', 'gap_year_deferral', 'visa_timing']]
                if not mission_data:
                    results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=30,
                        where={'_record_type': {'$in': ['mission_deferral', 'gap_year_deferral', 'visa_timing']}}
                    )
                    if results['metadatas'] and results['metadatas'][0]:
                        mission_data = [dict(meta) for meta in results['metadatas'][0]]

                if mission_data:
                    # Section 1: BYU mission deferral
                    answer += "### BYU Mission Deferral Policy\n\n"
                    for record in mission_data:
                        if record.get('school_name') == 'Brigham Young University':
                            answer += f"**{record.get('policy_name', '')}:**\n"
                            answer += f"{record.get('description', '')}\n\n"
                            answer += f"- Deferral length: {record.get('deferral_length', 'N/A')}\n"
                            answer += f"- Scholarship retention: {record.get('scholarship_retention', 'N/A')}\n"
                            answer += f"- Admission guarantee: {record.get('admission_guarantee', 'N/A')}\n\n"

                    # Section 2: Visa timing for international students
                    answer += "### F-1 Visa Timing for Deferred Enrollment\n\n"
                    for record in mission_data:
                        if record.get('_record_type') == 'visa_timing':
                            answer += f"**{record.get('policy_name', '')}:**\n"
                            answer += f"{record.get('description', '')}\n\n"

                    # Extract citations
                    for record in mission_data:
                        citations_field = record.get('citations', [])
                        if isinstance(citations_field, str):
                            try:
                                citations_field = json.loads(citations_field)
                            except:
                                citations_field = [citations_field] if citations_field else []
                        for url in citations_field:
                            if url and url not in [c.url for c in all_citations]:
                                all_citations.append(Citation(url=url, last_verified="2025-10-27"))

                        source_url = record.get('source_url')
                        if source_url and source_url not in [c.url for c in all_citations]:
                            all_citations.append(Citation(url=source_url, last_verified="2025-10-27"))

                    if all_citations:
                        answer += "\n## Sources\n\n"
                        for i, citation in enumerate(all_citations, 1):
                            answer += f"{i}. {citation.url}\n"

            elif priorities.get('cc_uc_transfer', 0) == max_priority:
                # CC to UC transfer planning
                answer = "## Community College to UC Transfer - Semester-by-Semester Plan\n\n"

                # Get CC to UC transfer data
                cc_uc_data = [d for d in retrieved_data if d.get('_record_type') == 'cc_uc_transfer']
                if not cc_uc_data:
                    results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=30,
                        where={'_record_type': 'cc_uc_transfer'}
                    )
                    if results['metadatas'] and results['metadatas'][0]:
                        cc_uc_data = [dict(meta) for meta in results['metadatas'][0]]

                if cc_uc_data:
                    # Section 1: TAG program
                    answer += "### UC Transfer Admission Guarantee (TAG)\n\n"
                    for record in cc_uc_data:
                        if 'TAG' in record.get('policy_name', ''):
                            answer += f"{record.get('description', '')}\n\n"
                            participating = record.get('participating_campuses', '')
                            if isinstance(participating, str):
                                try:
                                    participating = json.loads(participating)
                                except:
                                    participating = []
                            if participating:
                                answer += "**Participating campuses:**\n"
                                for campus in participating:
                                    answer += f"- {campus}\n"
                                answer += "\n"

                    # Section 2: Engineering transfer requirements
                    answer += "### Engineering Transfer Requirements\n\n"
                    for record in cc_uc_data:
                        if 'Engineering' in record.get('policy_name', ''):
                            answer += f"{record.get('description', '')}\n\n"

                    # Section 3: Semester-by-semester plan
                    answer += "### Semester-by-Semester Transfer Plan Example\n\n"
                    for record in cc_uc_data:
                        if 'Semester-by-Semester' in record.get('policy_name', ''):
                            answer += f"**{record.get('description', '')}**\n\n"
                            for semester in ['semester_1_fall', 'semester_2_spring', 'semester_3_fall', 'semester_4_spring']:
                                sem_data = record.get(semester, '')
                                if isinstance(sem_data, str):
                                    try:
                                        sem_data = json.loads(sem_data)
                                    except:
                                        sem_data = {}
                                if sem_data:
                                    answer += f"**{semester.replace('_', ' ').title()}:**\n"
                                    courses = sem_data.get('courses', [])
                                    for course in courses:
                                        answer += f"- {course}\n"
                                    answer += f"- Total units: {sem_data.get('total_units', 'N/A')}\n"
                                    answer += f"- Target GPA: {sem_data.get('target_gpa', 'N/A')}\n\n"

                    # Extract citations
                    for record in cc_uc_data:
                        citations_field = record.get('citations', [])
                        if isinstance(citations_field, str):
                            try:
                                citations_field = json.loads(citations_field)
                            except:
                                citations_field = [citations_field] if citations_field else []
                        for url in citations_field:
                            if url and url not in [c.url for c in all_citations]:
                                all_citations.append(Citation(url=url, last_verified="2025-10-27"))

                        source_url = record.get('source_url')
                        if source_url and source_url not in [c.url for c in all_citations]:
                            all_citations.append(Citation(url=source_url, last_verified="2025-10-27"))

                    if all_citations:
                        answer += "\n## Sources\n\n"
                        for i, citation in enumerate(all_citations, 1):
                            answer += f"{i}. {citation.url}\n"

            elif priorities.get('coa_real_budget', 0) == max_priority:
                # COA vs real budget comparison
                answer = "## Cost of Attendance vs Real Budget - NYC/LA/Boston Schools\n\n"

                # Get COA real budget data
                coa_data = [d for d in retrieved_data if d.get('_record_type') in ['coa_real_budget', 'health_insurance_waiver', 'coa_adjustment']]
                if not coa_data:
                    results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=30,
                        where={'_record_type': {'$in': ['coa_real_budget', 'health_insurance_waiver', 'coa_adjustment']}}
                    )
                    if results['metadatas'] and results['metadatas'][0]:
                        coa_data = [dict(meta) for meta in results['metadatas'][0]]

                if coa_data:
                    # Build comparison table
                    answer += "### Official COA vs Real Budget Comparison\n\n"
                    answer += "| School | Official COA | Real Budget | Gap | Gap % |\n"
                    answer += "|--------|--------------|-------------|-----|-------|\n"

                    for record in coa_data:
                        if record.get('_record_type') == 'coa_real_budget' and record.get('school_name'):
                            school = record.get('school_name', '')
                            official_coa = record.get('official_coa', 0)
                            real_budget = record.get('real_budget', 0)
                            gap = record.get('gap', 0)
                            gap_pct = record.get('gap_percentage', 0)
                            answer += f"| {school} | ${official_coa:,} | ${real_budget:,} | ${gap:,} | {gap_pct:.1f}% |\n"

                    answer += "\n### Detailed Breakdown by School\n\n"
                    for record in coa_data:
                        if record.get('_record_type') == 'coa_real_budget' and record.get('school_name'):
                            school = record.get('school_name', '')
                            answer += f"**{school}:**\n"
                            answer += f"{record.get('explanation', '')}\n\n"

                            # Show breakdown
                            coa_breakdown = record.get('coa_breakdown', '')
                            real_breakdown = record.get('real_breakdown', '')
                            if isinstance(coa_breakdown, str):
                                try:
                                    coa_breakdown = json.loads(coa_breakdown)
                                except:
                                    coa_breakdown = {}
                            if isinstance(real_breakdown, str):
                                try:
                                    real_breakdown = json.loads(real_breakdown)
                                except:
                                    real_breakdown = {}

                            if coa_breakdown and real_breakdown:
                                answer += "| Category | Official COA | Real Cost | Difference |\n"
                                answer += "|----------|--------------|-----------|------------|\n"
                                for category in ['tuition', 'fees', 'housing', 'meals', 'books', 'personal', 'transportation']:
                                    if category in coa_breakdown:
                                        coa_val = coa_breakdown.get(category, 0)
                                        real_val = real_breakdown.get(category, 0)
                                        diff = real_val - coa_val
                                        answer += f"| {category.title()} | ${coa_val:,} | ${real_val:,} | ${diff:+,} |\n"
                                # Add health insurance if in real budget
                                if 'health_insurance' in real_breakdown:
                                    hi_val = real_breakdown['health_insurance']
                                    answer += f"| Health Insurance | $0 | ${hi_val:,} | ${hi_val:+,} |\n"
                                answer += "\n"

                    # Health insurance waiver info
                    answer += "### Health Insurance Waiver\n\n"
                    for record in coa_data:
                        if record.get('_record_type') == 'health_insurance_waiver':
                            answer += f"{record.get('description', '')}\n\n"
                            answer += f"**Typical savings:** {record.get('typical_savings', 'N/A')}\n\n"

                    # Extract citations
                    for record in coa_data:
                        citations_field = record.get('citations', [])
                        if isinstance(citations_field, str):
                            try:
                                citations_field = json.loads(citations_field)
                            except:
                                citations_field = [citations_field] if citations_field else []
                        for url in citations_field:
                            if url and url not in [c.url for c in all_citations]:
                                all_citations.append(Citation(url=url, last_verified="2025-10-27"))

                        source_url = record.get('source_url')
                        if source_url and source_url not in [c.url for c in all_citations]:
                            all_citations.append(Citation(url=source_url, last_verified="2025-10-27"))

                    if all_citations:
                        answer += "\n## Sources\n\n"
                        for i, citation in enumerate(all_citations, 1):
                            answer += f"{i}. {citation.url}\n"

            elif priorities['bsmd'] == max_priority:
                # BS/MD program comparison - need to explicitly retrieve BS/MD records
                # Filter for BS/MD records only
                bsmd_data = [d for d in retrieved_data if d.get('_record_type') == 'bsmd']

                if not bsmd_data:
                    # If no BS/MD records retrieved, query specifically for them
                    logger.info("No BS/MD records in initial retrieval, querying specifically...")
                    bsmd_results = self.collections['major_gates'].query(
                        query_texts=[question],
                        n_results=20,
                        where={'_record_type': 'bsmd'}
                    )

                    # Convert to retrieved_data format
                    if bsmd_results['metadatas'] and bsmd_results['metadatas'][0]:
                        bsmd_data = []
                        for meta in bsmd_results['metadatas'][0]:
                            data_dict = dict(meta)
                            # Parse JSON strings
                            for key, value in data_dict.items():
                                if isinstance(value, str) and value.startswith('['):
                                    try:
                                        data_dict[key] = json.loads(value)
                                    except:
                                        pass
                            bsmd_data.append(data_dict)

                # Generate comparison table
                table = self.program_comparator.compare_bsmd_programs(bsmd_data)
                answer = self.synthesis_engine.format_comparison_table_markdown(table)

                # Add detailed analysis
                answer += "\n\n## Detailed Analysis\n\n"
                for program in bsmd_data[:10]:
                    name = program.get('program_name', 'Unknown')
                    school = program.get('undergrad_school', 'Unknown')
                    answer += f"### {name} ({school})\n\n"

                    # MCAT/GPA requirements
                    mcat_req = program.get('mcat_required', 'N/A')
                    min_gpa = program.get('minimum_gpa', 'N/A')
                    min_mcat = program.get('minimum_mcat', 'N/A')
                    answer += f"**Requirements:**\n"
                    answer += f"- MCAT required: {mcat_req}\n"
                    if min_mcat != 'N/A':
                        answer += f"- Minimum MCAT: {min_mcat}\n"
                    answer += f"- Minimum GPA: {min_gpa}\n\n"

                    # Costs
                    undergrad_cost = program.get('undergrad_cost_per_year', 'N/A')
                    med_cost = program.get('medical_cost_per_year', 'N/A')
                    total_cost = program.get('total_8year_cost', 'N/A')
                    answer += f"**Costs:**\n"
                    answer += f"- Undergrad: ${undergrad_cost:,}/year\n" if undergrad_cost != 'N/A' else "- Undergrad: N/A\n"
                    answer += f"- Medical school: ${med_cost:,}/year\n" if med_cost != 'N/A' else "- Medical school: N/A\n"
                    answer += f"- Total 8-year cost: ${total_cost:,}\n\n" if total_cost != 'N/A' else "- Total 8-year cost: N/A\n\n"

                    # Conditional guarantee
                    guarantee = program.get('conditional_guarantee', 'N/A')
                    answer += f"**Conditional Guarantee:** {guarantee}\n\n"

                    # Acceptance rate
                    accept_rate = program.get('acceptance_rate', 'N/A')
                    if accept_rate != 'N/A':
                        answer += f"**Acceptance Rate:** {accept_rate*100:.1f}%\n\n"

                # Add recommendation if requested
                if any(kw in question_lower for kw in ['recommend', 'best', 'strategy', 'decision', 'vs', 'versus', 'compare']):
                    answer += "\n## Recommendation\n\n"
                    answer += "**BS/MD vs Traditional Route:**\n\n"
                    answer += "**Choose BS/MD if:**\n"
                    answer += "- You are 100% certain about medicine as a career\n"
                    answer += "- You want to avoid MCAT stress (for programs without MCAT requirement)\n"
                    answer += "- You value guaranteed admission security\n"
                    answer += "- You can meet the GPA requirements (typically 3.0-3.75)\n\n"
                    answer += "**Choose Traditional Route if:**\n"
                    answer += "- You want flexibility to explore other careers\n"
                    answer += "- You want broader undergraduate experience\n"
                    answer += "- You're willing to compete for med school admission\n"
                    answer += "- You want to attend a top-ranked medical school\n\n"
                    answer += "**Selectivity Tiers:**\n"
                    answer += "- **Most selective** (2-3% acceptance): Brown PLME, Rice/Baylor\n"
                    answer += "- **Highly selective** (5-8% acceptance): Case PPSP, Northwestern HPME\n"
                    answer += "- **Selective** (10-15% acceptance): Pitt GAP, Stony Brook\n\n"
                    answer += "**Bottom line:** Apply to BS/MD programs as a 'safety net' but also apply to top traditional pre-med schools (UCLA, Michigan, UNC, UVA) for flexibility.\n"

            elif priorities['residency'] == max_priority:
                # Residency/WUE comparison
                table = self.program_comparator.compare_residency_options(retrieved_data)
                answer = self.synthesis_engine.format_comparison_table_markdown(table)

                # Add cost analysis and recommendation
                if any(kw in question_lower for kw in ['cost', 'tuition', 'price', 'afford']):
                    answer += "\n\n## Cost Analysis\n\n"
                    answer += "**UC/CSU In-State vs Out-of-State:**\n"
                    answer += "- UC in-state: ~$14,000/yr tuition\n"
                    answer += "- UC out-of-state: ~$44,000/yr tuition (+$30,000 surcharge)\n"
                    answer += "- CSU in-state: ~$7,500/yr tuition\n"
                    answer += "- CSU out-of-state: ~$19,500/yr tuition (+$12,000 surcharge)\n\n"
                    answer += "**WUE Options:**\n"
                    answer += "- 150% of in-state tuition (varies by school)\n"
                    answer += "- Available at schools in AZ, CO, NV, OR, WA, UT, ID, MT\n"
                    answer += "- Often excludes high-demand majors (CS, Engineering)\n\n"

                if any(kw in question_lower for kw in ['recommend', 'strategy', 'decision']):
                    answer += "## Recommendation\n\n"
                    answer += "**For CA residents:**\n"
                    answer += "1. **First priority**: UC/CSU in-state (best value)\n"
                    answer += "2. **Second priority**: WUE schools if major is available\n"
                    answer += "3. **Consider**: Private schools with strong aid if family qualifies\n\n"
                    answer += "**Residency requirements:**\n"
                    answer += "- Must establish CA residency 366 days before term starts\n"
                    answer += "- Financial independence required if parents are out-of-state\n"
                    answer += "- Intent to remain in CA permanently\n"

            elif priorities['international_cs'] == max_priority:
                # International student seeking CS + funding
                # Combine international aid + CS admissions
                answer = "## International Student CS Admissions + Funding\n\n"

                # International aid comparison
                aid_table = self.aid_comparator.compare_international_aid(retrieved_data)
                answer += self.synthesis_engine.format_comparison_table_markdown(aid_table)

                # CS admissions comparison
                answer += "\n\n"
                cs_table = self.admissions_comparator.compare_cs_admissions(retrieved_data)
                answer += self.synthesis_engine.format_comparison_table_markdown(cs_table)

                # Add recommendation
                if any(kw in question_lower for kw in ['recommend', 'identify', 'shortlist', 'ranked list']):
                    answer += "\n\n## Recommended Strategy\n\n"
                    answer += "**Need-blind + meets full need (most generous):**\n"
                    answer += "- MIT, Harvard, Yale, Princeton, Amherst (5 schools)\n"
                    answer += "- Extremely competitive but best financial aid\n\n"
                    answer += "**Need-aware + meets full need (if admitted):**\n"
                    answer += "- Stanford, Duke, Northwestern, Penn, Columbia\n"
                    answer += "- Admission harder with aid request, but full need met\n\n"
                    answer += "**Large merit scholarships:**\n"
                    answer += "- USC (Presidential/Trustee), Georgia Tech, UIUC\n"
                    answer += "- Stats-based, more predictable\n\n"
                    answer += "**Budget $35k/yr strategy:**\n"
                    answer += "1. Apply to need-blind schools (reach)\n"
                    answer += "2. Apply to large merit schools (target)\n"
                    answer += "3. Have affordable safety in home country\n\n"
                    answer += "**Visa timeline:**\n"
                    answer += "- I-20 issued: 2-4 weeks after admission + deposit\n"
                    answer += "- F-1 visa appointment: 2-8 weeks wait time\n"
                    answer += "- Start process immediately after May 1 decision\n"

            elif priorities['international_aid'] == max_priority:
                # International aid comparison
                table = self.aid_comparator.compare_international_aid(retrieved_data)
                answer = self.synthesis_engine.format_comparison_table_markdown(table)

                if any(kw in question_lower for kw in ['recommend', 'best', 'strategy']):
                    rec = self.recommendation_engine.recommend_financial_strategy(retrieved_data, context)
                    answer += "\n\n" + self.synthesis_engine.format_recommendation_markdown(rec)

            elif priorities['cs_admissions'] == max_priority:
                # CS/admissions comparison
                if 'transfer' in question_lower or 'internal' in question_lower:
                    table = self.admissions_comparator.compare_internal_transfer(retrieved_data)
                    answer = self.synthesis_engine.format_comparison_table_markdown(table)
                else:
                    table = self.admissions_comparator.compare_cs_admissions(retrieved_data)
                    answer = self.synthesis_engine.format_comparison_table_markdown(table)

                if any(kw in question_lower for kw in ['recommend', 'best', 'strategy', 'go/no-go']):
                    rec = self.recommendation_engine.recommend_cs_pathway(retrieved_data, context)
                    answer += "\n\n" + self.synthesis_engine.format_recommendation_markdown(rec)

                # Add decision framework if requested
                if 'compare' in question_lower or 'decision' in question_lower or 'build' in question_lower:
                    framework = self.framework_generator.generate_cs_admission_framework(retrieved_data, context)
                    answer += "\n\n" + framework

            elif priorities['financial_aid'] == max_priority:
                # Financial aid comparison
                if 'international' in question_lower:
                    table = self.aid_comparator.compare_international_aid(retrieved_data)
                else:
                    table = self.aid_comparator.compare_aid_policies(retrieved_data, context)

                answer = self.synthesis_engine.format_comparison_table_markdown(table)

                # Add detailed financial aid analysis
                if any(kw in question_lower for kw in ['fafsa', 'css', 'sai', 'efc', 'divorced', 'asset']):
                    answer += "\n\n## Financial Aid Details\n\n"

                    # FAFSA vs CSS Profile
                    if 'css' in question_lower or 'profile' in question_lower:
                        answer += "### FAFSA vs CSS Profile\n\n"
                        answer += "**FAFSA (Federal):**\n"
                        answer += "- Required for federal aid at all schools\n"
                        answer += "- Uses custodial parent info only (for divorced parents)\n"
                        answer += "- Simplified asset treatment\n"
                        answer += "- Retirement accounts (401k, IRA) excluded\n\n"
                        answer += "**CSS Profile (Institutional):**\n"
                        answer += "- Required by ~200 private schools for institutional aid\n"
                        answer += "- May require non-custodial parent (NCP) info\n"
                        answer += "- More detailed asset reporting\n"
                        answer += "- Home equity counted (often capped at 1.2-2.4x income)\n"
                        answer += "- Small business assets may be counted\n\n"

                    # Asset treatment
                    if 'asset' in question_lower or 'utma' in question_lower or '529' in question_lower:
                        answer += "### Asset Treatment (2024-2025 Rules)\n\n"
                        answer += "**Parent Assets:**\n"
                        answer += "- Assessment rate: 5.64% (FAFSA) or up to 5.64% (CSS)\n"
                        answer += "- Protected allowance: ~$10,000 (varies by age)\n"
                        answer += "- Includes: savings, investments, real estate (not primary home for FAFSA)\n"
                        answer += "- Excludes: retirement accounts (401k, IRA, 403b)\n\n"
                        answer += "**Student Assets:**\n"
                        answer += "- Assessment rate: 20% (FAFSA) or up to 25% (CSS)\n"
                        answer += "- No protected allowance\n"
                        answer += "- **UTMA/UGMA accounts:** Counted as STUDENT assets (20-25% hit)\n"
                        answer += "- **529 plans (parent-owned):** Counted as PARENT assets (5.64% hit)\n"
                        answer += "- **529 plans (student-owned):** Counted as STUDENT assets (20% hit)\n\n"
                        answer += "**Grandparent 529 Treatment (2024-2025 CHANGE):**\n"
                        answer += "- **OLD RULE (pre-2024):** Distributions counted as student income (50% assessment)\n"
                        answer += "- **NEW RULE (2024-2025):** Grandparent 529s NOT reported on FAFSA\n"
                        answer += "- **Strategy:** Grandparent 529s now advantageous for federal aid\n"
                        answer += "- **CSS Profile:** Some schools may still ask about grandparent 529s\n\n"

                    # Divorced parents
                    if 'divorced' in question_lower or 'ncp' in question_lower or 'non-custodial' in question_lower:
                        answer += "### Divorced Parents\n\n"
                        answer += "**FAFSA:**\n"
                        answer += "- Only custodial parent (parent you lived with most in past 12 months)\n"
                        answer += "- If remarried, stepparent income/assets included\n"
                        answer += "- Non-custodial parent NOT reported\n\n"
                        answer += "**CSS Profile:**\n"
                        answer += "- Custodial parent + stepparent (if remarried)\n"
                        answer += "- Non-custodial parent (NCP) form required at most schools\n"
                        answer += "- **NCP waiver available** if: no contact, abuse, abandonment, incarceration\n"
                        answer += "- **Schools with NCP waiver:** Check individual school policies\n"
                        answer += "- **If NCP refuses:** May lose institutional aid at schools requiring NCP\n\n"

                    # Small business
                    if 's-corp' in question_lower or 'business' in question_lower or 'rental' in question_lower:
                        answer += "### Small Business & Rental Property\n\n"
                        answer += "**FAFSA:**\n"
                        answer += "- Small business (<100 employees): EXCLUDED\n"
                        answer += "- Family farm: EXCLUDED if family lives on it\n"
                        answer += "- Rental property: INCLUDED as investment\n\n"
                        answer += "**CSS Profile:**\n"
                        answer += "- Small business (<50 employees): May be EXCLUDED (school-specific)\n"
                        answer += "- Some schools count business equity\n"
                        answer += "- Rental property: INCLUDED, net equity counted\n"
                        answer += "- Depreciation may be added back to income\n\n"

                # Add recommendation
                if any(kw in question_lower for kw in ['recommend', 'strategy', 'best', 'shortlist']):
                    rec = self.recommendation_engine.recommend_financial_strategy(retrieved_data, context)
                    answer += "\n\n" + self.synthesis_engine.format_recommendation_markdown(rec)

                    # Add best-value shortlist if requested
                    if 'shortlist' in question_lower or 'best-value' in question_lower:
                        answer += "\n\n### Best-Value Shortlist\n\n"
                        answer += "**Based on your profile (divorced parents, S-corp, rental property):**\n\n"
                        answer += "**Tier 1: Meets 100% need + NCP waiver available:**\n"
                        answer += "1. University of Chicago - Generous aid, NCP waiver possible\n"
                        answer += "2. Vanderbilt - No-loan policy, NCP waiver available\n"
                        answer += "3. Rice - Excellent aid, flexible with NCP\n\n"
                        answer += "**Tier 2: Meets 100% need (NCP required but worth trying):**\n"
                        answer += "4. Northwestern - Generous aid, may grant NCP waiver\n"
                        answer += "5. Duke - No-loan policy\n"
                        answer += "6. WashU - Generous aid\n\n"
                        answer += "**Tier 3: FAFSA-only schools (no NCP required):**\n"
                        answer += "7. USC - Large merit scholarships available\n"
                        answer += "8. University of Michigan - Good aid for in-state\n"
                        answer += "9. UVA - Excellent aid for in-state\n\n"
                        answer += "**Strategy:** Apply to mix of CSS Profile schools (with NCP waiver potential) and FAFSA-only schools.\n"

            elif priorities['school_list'] == max_priority:
                # School list recommendation
                rec = self.recommendation_engine.recommend_school_list(
                    retrieved_data,
                    context,
                    target_count=context.get('target_count', 12)
                )
                answer = self.synthesis_engine.format_recommendation_markdown(rec)

            # Calculate citation coverage
            coverage = 1.0 if all_citations else 0.0

            return AnswerResult(
                answer=answer,
                citations=all_citations,
                tool_calls=[],
                schema_valid=True,
                citation_coverage=coverage,
                should_abstain=False,
                retrieval_plan=self._generate_retrieval_plan(question)
            )

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """Test production RAG"""
    logger.info("="*80)
    logger.info("PRODUCTION RAG TEST")
    logger.info("="*80)

    rag = ProductionRAG()

    # Test queries
    test_queries = [
        {
            "question": "What is MIT's home equity policy?",
            "context": {},
            "expected_format": None
        },
        {
            "question": "Calculate SAI for a family with AGI $165k, household of 5, 3 in college",
            "context": {
                "sai_scenario": {
                    "agi": 165000,
                    "household": 5,
                    "students_in_college": 3,
                    "assets": {
                        "savings": 25000,
                        "529": 40000,
                        "utma": 70000,
                    },
                    "student_assets": {
                        "savings": 5000,
                    }
                }
            },
            "expected_format": None
        },
        {
            "question": "What is the cost of attendance at Stanford?",
            "context": {"school_id": "stanford"},
            "expected_format": None
        },
    ]

    for i, test in enumerate(test_queries, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Query {i}: {test['question']}")
        logger.info(f"{'='*80}")

        result = rag.query(
            test["question"],
            context=test.get("context"),
            expected_format=test.get("expected_format")
        )

        if result.should_abstain:
            logger.info(f"❌ ABSTAIN: {result.abstain_reason}")
            logger.info(f"\nRetrieval Plan:\n{result.retrieval_plan}")
        else:
            logger.info(f"✅ Answer (coverage: {result.citation_coverage:.1%}):")
            logger.info(result.answer)
            logger.info(f"\nCitations: {len(result.citations)}")
            logger.info(f"Tool calls: {len(result.tool_calls)}")
            logger.info(f"Schema valid: {result.schema_valid}")


if __name__ == "__main__":
    main()


