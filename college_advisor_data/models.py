"""Data models for the College Advisor pipeline."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class DocumentType(str, Enum):
    """Types of documents in the system."""
    UNIVERSITY = "university"
    PROGRAM = "program"
    SUMMER_PROGRAM = "summer_program"
    ADMISSION_REQUIREMENT = "admission_requirement"
    GENERAL_INFO = "general_info"


class Document(BaseModel):
    """Base document model for all ingested content."""
    
    id: str = Field(..., description="Unique identifier for the document")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Main document content")
    doc_type: DocumentType = Field(..., description="Type of document")
    source_url: Optional[str] = Field(None, description="Original source URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChunkMetadata(BaseModel):
    """Metadata for document chunks."""
    
    document_id: str = Field(..., description="ID of the parent document")
    chunk_index: int = Field(..., description="Index of this chunk within the document")
    chunk_size: int = Field(..., description="Size of the chunk in tokens")
    doc_type: DocumentType = Field(..., description="Type of the parent document")
    
    # University/Program specific metadata
    university_name: Optional[str] = Field(None, description="Name of the university")
    program_name: Optional[str] = Field(None, description="Name of the program")
    program_type: Optional[str] = Field(None, description="Type of program (undergraduate, graduate, etc.)")
    subject_area: Optional[str] = Field(None, description="Subject area or field of study")
    location: Optional[str] = Field(None, description="Geographic location")
    
    # Admission requirements
    gpa_requirement: Optional[float] = Field(None, description="Minimum GPA requirement")
    test_scores: Optional[Dict[str, Any]] = Field(None, description="Required test scores")
    
    # Summer programs
    duration: Optional[str] = Field(None, description="Program duration")
    age_range: Optional[str] = Field(None, description="Target age range")
    cost: Optional[str] = Field(None, description="Program cost information")
    
    # Additional searchable fields
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")


class EmbeddingResult(BaseModel):
    """Result of embedding generation."""
    
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    embedding: List[float] = Field(..., description="Vector embedding")
    model_name: str = Field(..., description="Name of the embedding model used")
    embedding_dim: int = Field(..., description="Dimension of the embedding vector")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessingStats(BaseModel):
    """Statistics from processing operations."""
    
    total_documents: int = 0
    total_chunks: int = 0
    total_embeddings: int = 0
    processing_time: float = 0.0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
