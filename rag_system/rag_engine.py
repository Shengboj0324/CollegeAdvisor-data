#!/usr/bin/env python3
"""
RAG Engine with Tool Integration
Implements retrieval-augmented generation with deterministic calculators
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    """RAG retrieval result"""
    answer: str
    sources: List[Dict[str, str]]
    tool_calls: List[Dict[str, Any]]
    confidence: float
    should_abstain: bool
    abstain_reason: Optional[str] = None


class RAGEngine:
    """RAG engine with tool integration"""
    
    def __init__(self, chroma_path: str = "chroma_data", training_data_path: str = "training_data"):
        self.chroma_path = Path(chroma_path)
        self.training_data_path = Path(training_data_path)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create collections for different data types
        self.collections = {
            "aid_policies": self.client.get_or_create_collection("aid_policies"),
            "major_gates": self.client.get_or_create_collection("major_gates"),
            "cds_data": self.client.get_or_create_collection("cds_data"),
            "articulation": self.client.get_or_create_collection("articulation"),
            "cited_answers": self.client.get_or_create_collection("cited_answers"),
        }
        
        # Load data into collections
        self._load_all_data()
        
    def _load_all_data(self):
        """Load all training data into ChromaDB"""
        logger.info("Loading training data into ChromaDB...")
        
        # Load aid policies
        self._load_jsonl_to_collection(
            self.training_data_path / "tier0_policy_rules/InstitutionAidPolicy.jsonl",
            "aid_policies",
            id_field="school_id",
            text_fields=["school_name", "policy_topic", "rule"]
        )
        
        # Load major gates
        self._load_jsonl_to_collection(
            self.training_data_path / "tier0_policy_rules/MajorGate.jsonl",
            "major_gates",
            id_field="school_id",
            text_fields=["school_name", "major_name", "notes"]
        )
        
        # Load CDS data
        self._load_jsonl_to_collection(
            self.training_data_path / "tier1_admissions/CDSExtract.jsonl",
            "cds_data",
            id_field="school_id",
            text_fields=["school_name", "metric"]
        )
        
        # Load articulation data
        self._load_jsonl_to_collection(
            self.training_data_path / "tier1_transfer/Articulation.jsonl",
            "articulation",
            id_field="cc_id",
            text_fields=["cc_name", "target_school_name", "target_major"]
        )
        
        # Load cited answers
        self._load_jsonl_to_collection(
            self.training_data_path / "tier0_citation_training/CitedAnswer.jsonl",
            "cited_answers",
            id_field="prompt",
            text_fields=["prompt", "answer_md"]
        )
        
        logger.info("✅ All training data loaded into ChromaDB")
        
    def _load_jsonl_to_collection(self, file_path: Path, collection_name: str, id_field: str, text_fields: List[str]):
        """Load JSONL file into ChromaDB collection"""
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return
            
        collection = self.collections[collection_name]
        
        documents = []
        metadatas = []
        ids = []
        
        with open(file_path, 'r') as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON line {idx} in {file_path}: {e}")
                    continue

                # Create document text from specified fields
                doc_text = " | ".join([str(record.get(field, "")) for field in text_fields])
                documents.append(doc_text)

                # Store full record as metadata (convert lists to JSON strings for ChromaDB)
                metadata = {}
                for key, value in record.items():
                    if isinstance(value, (list, dict)):
                        metadata[key] = json.dumps(value)
                    else:
                        metadata[key] = value
                metadatas.append(metadata)

                # Generate ID
                id_value = record.get(id_field, f"{collection_name}_{idx}")
                ids.append(f"{collection_name}_{id_value}_{idx}")
                
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Loaded {len(documents)} records into {collection_name}")
            
    def query(self, question: str, n_results: int = 5) -> RAGResult:
        """Query RAG system with tool integration"""
        
        # Step 1: Retrieve relevant documents
        sources = self._retrieve_sources(question, n_results)
        
        # Step 2: Check if we have sufficient data
        if not sources:
            return RAGResult(
                answer="",
                sources=[],
                tool_calls=[],
                confidence=0.0,
                should_abstain=True,
                abstain_reason="No relevant sources found in knowledge base"
            )
            
        # Step 3: Check if question requires calculator
        tool_calls = self._identify_tool_calls(question)
        
        # Step 4: Execute tool calls if needed
        tool_results = []
        for tool_call in tool_calls:
            result = self._execute_tool(tool_call)
            tool_results.append(result)
            
        # Step 5: Generate answer with citations
        answer = self._generate_answer(question, sources, tool_results)
        
        # Step 6: Validate answer has citations
        has_citations = self._validate_citations(answer)
        
        if not has_citations:
            return RAGResult(
                answer="",
                sources=sources,
                tool_calls=tool_calls,
                confidence=0.0,
                should_abstain=True,
                abstain_reason="Cannot provide answer without verifiable citations"
            )
            
        return RAGResult(
            answer=answer,
            sources=sources,
            tool_calls=tool_calls,
            confidence=0.9 if has_citations else 0.3,
            should_abstain=False
        )
        
    def _retrieve_sources(self, question: str, n_results: int) -> List[Dict]:
        """Retrieve relevant sources from all collections"""
        all_sources = []
        
        for collection_name, collection in self.collections.items():
            try:
                results = collection.query(
                    query_texts=[question],
                    n_results=n_results
                )
                
                if results['metadatas'] and results['metadatas'][0]:
                    for metadata in results['metadatas'][0]:
                        all_sources.append({
                            "collection": collection_name,
                            "data": metadata
                        })
            except Exception as e:
                logger.error(f"Error querying {collection_name}: {e}")
                
        return all_sources[:n_results]
        
    def _identify_tool_calls(self, question: str) -> List[Dict]:
        """Identify if question requires calculator tools"""
        tool_calls = []
        
        # Check for SAI calculation keywords
        if any(keyword in question.lower() for keyword in ["sai", "student aid index", "efc", "expected family contribution", "net price"]):
            tool_calls.append({
                "tool": "sai_calculator",
                "reason": "Question requires SAI/EFC calculation"
            })
            
        # Check for cost calculation keywords
        if any(keyword in question.lower() for keyword in ["cost", "budget", "housing", "total cost"]):
            tool_calls.append({
                "tool": "cost_calculator",
                "reason": "Question requires cost calculation"
            })
            
        return tool_calls
        
    def _execute_tool(self, tool_call: Dict) -> Dict:
        """Execute tool call"""
        tool_name = tool_call["tool"]
        
        if tool_name == "sai_calculator":
            return {
                "tool": tool_name,
                "result": "SAI calculator requires specific inputs (AGI, assets, household size). Please provide these values.",
                "status": "needs_input"
            }
        elif tool_name == "cost_calculator":
            return {
                "tool": tool_name,
                "result": "Cost calculator requires specific inputs (tuition, fees, housing, etc.). Please provide these values.",
                "status": "needs_input"
            }
        else:
            return {
                "tool": tool_name,
                "result": "Unknown tool",
                "status": "error"
            }
            
    def _generate_answer(self, question: str, sources: List[Dict], tool_results: List[Dict]) -> str:
        """Generate answer with citations"""
        # This is a template - in production, you'd use the LLM here
        # For now, return a structured response with sources
        
        answer_parts = []
        
        # Add tool results if any
        if tool_results:
            answer_parts.append("**Tool Results:**\n")
            for result in tool_results:
                answer_parts.append(f"- {result['tool']}: {result['result']}\n")
            answer_parts.append("\n")
            
        # Add source-based answer
        answer_parts.append("**Based on available sources:**\n\n")
        
        for idx, source in enumerate(sources[:3], 1):
            data = source['data']
            collection = source['collection']
            
            if collection == "aid_policies":
                answer_parts.append(f"{idx}. **{data.get('school_name')}** - {data.get('policy_topic')}:\n")
                answer_parts.append(f"   {data.get('rule')}\n")
                if data.get('citations'):
                    answer_parts.append(f"   **Source:** {data['citations'][0]}\n")
                answer_parts.append(f"   **Last Verified:** {data.get('last_verified')}\n\n")
                
            elif collection == "major_gates":
                answer_parts.append(f"{idx}. **{data.get('school_name')}** - {data.get('major_name')}:\n")
                answer_parts.append(f"   {data.get('notes')}\n")
                if data.get('citations'):
                    answer_parts.append(f"   **Source:** {data['citations'][0]}\n")
                answer_parts.append(f"   **Last Verified:** {data.get('last_verified')}\n\n")
                
            elif collection == "cds_data":
                answer_parts.append(f"{idx}. **{data.get('school_name')}** ({data.get('year')}):\n")
                answer_parts.append(f"   {data.get('metric')}: {data.get('value')}\n")
                answer_parts.append(f"   **Source:** {data.get('url')}\n")
                answer_parts.append(f"   **Last Verified:** {data.get('last_verified')}\n\n")
                
        return "".join(answer_parts)
        
    def _validate_citations(self, answer: str) -> bool:
        """Validate that answer contains citations"""
        # Check for URL patterns or "Source:" mentions
        has_source = "Source:" in answer or "http" in answer
        has_verified = "Last Verified:" in answer
        
        return has_source and has_verified
        
    def get_stats(self) -> Dict:
        """Get RAG system statistics"""
        stats = {}
        
        for name, collection in self.collections.items():
            try:
                count = collection.count()
                stats[name] = count
            except:
                stats[name] = 0
                
        return stats


def main():
    """Test RAG engine"""
    rag = RAGEngine()
    
    # Print stats
    stats = rag.get_stats()
    logger.info("RAG System Statistics:")
    for collection, count in stats.items():
        logger.info(f"  {collection}: {count} records")
        
    # Test query
    test_questions = [
        "What is MIT's home equity policy?",
        "What are the internal transfer requirements for Computer Science at University of Washington?",
        "What is the admission rate at Harvard?",
    ]
    
    for question in test_questions:
        logger.info(f"\n{'='*80}")
        logger.info(f"Question: {question}")
        logger.info(f"{'='*80}")
        
        result = rag.query(question)
        
        if result.should_abstain:
            logger.info(f"❌ ABSTAIN: {result.abstain_reason}")
        else:
            logger.info(f"✅ Answer (confidence: {result.confidence}):")
            logger.info(result.answer)
            logger.info(f"\nSources: {len(result.sources)}")
            logger.info(f"Tool calls: {len(result.tool_calls)}")


if __name__ == "__main__":
    main()

