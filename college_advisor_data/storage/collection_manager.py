"""
ChromaDB collection manager for organizing college admissions data.

Manages multiple specialized collections for different data types:
- Institutional data (colleges, universities)
- Program data (majors, departments)
- Admissions data (requirements, statistics)
- Student experiences (reviews, essays)
- Outcomes data (careers, earnings)
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from .chroma_client import ChromaDBClient
from ..schemas import DocumentChunk, DocumentMetadata

logger = logging.getLogger(__name__)


class CollectionManager:
    """
    Manages multiple ChromaDB collections for different data types.
    
    Collections:
    - institutions: College and university data
    - programs: Academic programs and majors
    - admissions: Admissions requirements and statistics
    - experiences: Student reviews and essays
    - outcomes: Career and earnings data
    - qa_pairs: Question-answer pairs for training
    """
    
    COLLECTION_SCHEMAS = {
        "institutions": {
            "description": "College and university institutional data",
            "required_fields": ["institution_name", "institution_id", "state", "type"],
            "indexed_fields": ["institution_name", "state", "type", "selectivity"]
        },
        "programs": {
            "description": "Academic programs and majors",
            "required_fields": ["program_name", "institution_id", "degree_level"],
            "indexed_fields": ["program_name", "field", "degree_level"]
        },
        "admissions": {
            "description": "Admissions requirements and statistics",
            "required_fields": ["institution_id", "admission_type"],
            "indexed_fields": ["admission_type", "selectivity", "test_optional"]
        },
        "experiences": {
            "description": "Student reviews and experiences",
            "required_fields": ["institution_id", "experience_type"],
            "indexed_fields": ["experience_type", "sentiment", "category"]
        },
        "outcomes": {
            "description": "Career outcomes and earnings data",
            "required_fields": ["institution_id", "outcome_type"],
            "indexed_fields": ["outcome_type", "field", "years_after_graduation"]
        },
        "qa_pairs": {
            "description": "Question-answer pairs for model training",
            "required_fields": ["question", "answer", "category"],
            "indexed_fields": ["category", "difficulty", "topic"]
        }
    }
    
    def __init__(self):
        self.clients = {}
        self.stats = {
            "collections_created": 0,
            "total_documents": 0,
            "collections": {}
        }
    
    def get_client(self, collection_name: str) -> ChromaDBClient:
        """
        Get or create a ChromaDB client for a specific collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            ChromaDBClient instance
        """
        if collection_name not in self.clients:
            self.clients[collection_name] = ChromaDBClient(collection_name=collection_name)
            self.clients[collection_name].get_or_create_collection()
            self.stats["collections_created"] += 1
        
        return self.clients[collection_name]
    
    def create_all_collections(self) -> Dict[str, Any]:
        """
        Create all predefined collections.
        
        Returns:
            Statistics about created collections
        """
        logger.info("Creating all ChromaDB collections...")
        
        for collection_name, schema in self.COLLECTION_SCHEMAS.items():
            try:
                client = self.get_client(collection_name)
                logger.info(f"Created collection: {collection_name}")
                self.stats["collections"][collection_name] = {
                    "created": True,
                    "description": schema["description"]
                }
            except Exception as e:
                logger.error(f"Error creating collection {collection_name}: {e}")
                self.stats["collections"][collection_name] = {
                    "created": False,
                    "error": str(e)
                }
        
        return self.stats
    
    def add_institutions(self, institutions: List[Dict[str, Any]]) -> int:
        """
        Add institutional data to the institutions collection.
        
        Args:
            institutions: List of institution records
            
        Returns:
            Number of institutions added
        """
        client = self.get_client("institutions")
        count = 0
        
        for inst in institutions:
            try:
                # Create document chunk
                chunk = DocumentChunk(
                    chunk_id=f"inst_{inst.get('id', count)}",
                    content=self._format_institution_content(inst),
                    metadata=DocumentMetadata(
                        source_type="institution",
                        institution_name=inst.get("name", "Unknown"),
                        institution_id=str(inst.get("id", "")),
                        state=inst.get("state", ""),
                        data_type="institutional_data",
                        **self._extract_institution_metadata(inst)
                    )
                )
                
                # Add to collection
                client.add_documents([chunk])
                count += 1
                
            except Exception as e:
                logger.error(f"Error adding institution {inst.get('name')}: {e}")
        
        logger.info(f"Added {count} institutions to ChromaDB")
        self.stats["total_documents"] += count
        return count
    
    def add_programs(self, programs: List[Dict[str, Any]]) -> int:
        """
        Add program data to the programs collection.
        
        Args:
            programs: List of program records
            
        Returns:
            Number of programs added
        """
        client = self.get_client("programs")
        count = 0
        
        for program in programs:
            try:
                chunk = DocumentChunk(
                    chunk_id=f"prog_{program.get('id', count)}",
                    content=self._format_program_content(program),
                    metadata=DocumentMetadata(
                        source_type="program",
                        program_name=program.get("name", "Unknown"),
                        institution_id=str(program.get("institution_id", "")),
                        data_type="program_data",
                        **self._extract_program_metadata(program)
                    )
                )
                
                client.add_documents([chunk])
                count += 1
                
            except Exception as e:
                logger.error(f"Error adding program {program.get('name')}: {e}")
        
        logger.info(f"Added {count} programs to ChromaDB")
        self.stats["total_documents"] += count
        return count
    
    def add_qa_pairs(self, qa_pairs: List[Dict[str, Any]]) -> int:
        """
        Add question-answer pairs to the qa_pairs collection.
        
        Args:
            qa_pairs: List of Q&A pairs with 'question', 'answer', 'category'
            
        Returns:
            Number of Q&A pairs added
        """
        client = self.get_client("qa_pairs")
        count = 0
        
        for qa in qa_pairs:
            try:
                # Format as instruction-response pair
                content = f"Question: {qa['question']}\n\nAnswer: {qa['answer']}"
                
                chunk = DocumentChunk(
                    chunk_id=f"qa_{count}",
                    content=content,
                    metadata=DocumentMetadata(
                        source_type="qa_pair",
                        category=qa.get("category", "general"),
                        data_type="training_data",
                        question=qa["question"],
                        answer=qa["answer"]
                    )
                )
                
                client.add_documents([chunk])
                count += 1
                
            except Exception as e:
                logger.error(f"Error adding Q&A pair: {e}")
        
        logger.info(f"Added {count} Q&A pairs to ChromaDB")
        self.stats["total_documents"] += count
        return count
    
    def load_from_json(self, json_path: Path, collection_type: str) -> int:
        """
        Load data from JSON file into appropriate collection.
        
        Args:
            json_path: Path to JSON file
            collection_type: Type of collection (institutions, programs, qa_pairs, etc.)
            
        Returns:
            Number of records added
        """
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            data = [data]
        
        if collection_type == "institutions":
            return self.add_institutions(data)
        elif collection_type == "programs":
            return self.add_programs(data)
        elif collection_type == "qa_pairs":
            return self.add_qa_pairs(data)
        else:
            logger.warning(f"Unknown collection type: {collection_type}")
            return 0
    
    def _format_institution_content(self, inst: Dict[str, Any]) -> str:
        """Format institution data as readable text for embedding."""
        parts = [
            f"Institution: {inst.get('name', 'Unknown')}",
            f"Location: {inst.get('city', '')}, {inst.get('state', '')}",
            f"Type: {inst.get('type', 'Unknown')}",
        ]
        
        if inst.get('description'):
            parts.append(f"Description: {inst['description']}")
        
        if inst.get('admission_rate'):
            parts.append(f"Admission Rate: {inst['admission_rate']}%")
        
        if inst.get('enrollment'):
            parts.append(f"Enrollment: {inst['enrollment']} students")
        
        return "\n".join(parts)
    
    def _format_program_content(self, program: Dict[str, Any]) -> str:
        """Format program data as readable text for embedding."""
        parts = [
            f"Program: {program.get('name', 'Unknown')}",
            f"Degree Level: {program.get('degree_level', 'Unknown')}",
        ]
        
        if program.get('description'):
            parts.append(f"Description: {program['description']}")
        
        if program.get('requirements'):
            parts.append(f"Requirements: {program['requirements']}")
        
        return "\n".join(parts)
    
    def _extract_institution_metadata(self, inst: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields from institution record."""
        metadata = {}
        
        # Add optional fields if present
        optional_fields = [
            'type', 'city', 'admission_rate', 'enrollment',
            'tuition', 'selectivity', 'ranking'
        ]
        
        for field in optional_fields:
            if field in inst:
                metadata[field] = str(inst[field])
        
        return metadata
    
    def _extract_program_metadata(self, program: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata fields from program record."""
        metadata = {}
        
        optional_fields = [
            'degree_level', 'field', 'department', 'credits_required'
        ]
        
        for field in optional_fields:
            if field in program:
                metadata[field] = str(program[field])
        
        return metadata
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections."""
        stats = {}
        
        for collection_name in self.COLLECTION_SCHEMAS.keys():
            if collection_name in self.clients:
                client = self.clients[collection_name]
                try:
                    count = client.collection.count()
                    stats[collection_name] = {
                        "document_count": count,
                        "status": "active"
                    }
                except Exception as e:
                    stats[collection_name] = {
                        "document_count": 0,
                        "status": "error",
                        "error": str(e)
                    }
        
        return stats
    
    def export_collection_to_json(
        self,
        collection_name: str,
        output_path: Path,
        limit: int = None
    ) -> bool:
        """
        Export a collection to JSON format.
        
        Args:
            collection_name: Name of collection to export
            output_path: Path to save JSON file
            limit: Maximum number of documents to export
            
        Returns:
            True if successful
        """
        try:
            client = self.get_client(collection_name)
            
            # Get all documents
            results = client.collection.get(limit=limit)
            
            # Format for export
            export_data = {
                "collection": collection_name,
                "exported_at": json.dumps({"timestamp": "now"}),
                "document_count": len(results.get('ids', [])),
                "documents": []
            }
            
            for i, doc_id in enumerate(results.get('ids', [])):
                export_data["documents"].append({
                    "id": doc_id,
                    "content": results['documents'][i] if 'documents' in results else None,
                    "metadata": results['metadatas'][i] if 'metadatas' in results else {}
                })
            
            # Save to file
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported {len(export_data['documents'])} documents to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting collection {collection_name}: {e}")
            return False

