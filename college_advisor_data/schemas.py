"""
Standardized schemas for CollegeAdvisor data pipeline.

This module defines the canonical data contracts between the data pipeline
and the API, ensuring consistent metadata structure across all components.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
import hashlib


class EntityType(str, Enum):
    """Standardized entity types for all documents."""
    COLLEGE = "college"
    PROGRAM = "program"
    SUMMER_PROGRAM = "summer_program"
    REQUIREMENT = "requirement"
    FINANCIAL_AID = "financial_aid"
    ADMISSION_INFO = "admission_info"
    GENERAL_INFO = "general_info"


class GPABand(str, Enum):
    """Standardized GPA bands for filtering."""
    BELOW_2_5 = "0.0-2.5"
    BAND_2_5_3_0 = "2.5-3.0"
    BAND_3_0_3_5 = "3.0-3.5"
    BAND_3_5_4_0 = "3.5-4.0"
    ABOVE_4_0 = "4.0+"
    NOT_SPECIFIED = "not_specified"


class DocumentMetadata(BaseModel):
    """
    Canonical metadata schema for all documents in ChromaDB.
    
    This is the contract that the API depends on - any changes require
    a new schema version and migration strategy.
    """
    # Core identifiers
    doc_id: str = Field(..., description="Unique document identifier")
    entity_type: EntityType = Field(..., description="Type of entity")
    
    # Institution information
    school: str = Field(..., description="Institution name")
    name: str = Field(..., description="Program/entity name")
    
    # Academic filtering
    gpa_band: GPABand = Field(default=GPABand.NOT_SPECIFIED, description="GPA requirement band")
    majors: List[str] = Field(default_factory=list, description="Related majors/fields")
    interests: List[str] = Field(default_factory=list, description="Interest tags")
    
    # Geographic information
    location: str = Field(..., description="Location (State, Country format)")
    
    # Source tracking
    url: Optional[str] = Field(None, description="Source URL")
    source_id: str = Field(..., description="Source system identifier")
    
    # Content organization
    year: int = Field(default_factory=lambda: datetime.now().year, description="Academic year")
    section: str = Field(..., description="Content section/category")
    
    # Data integrity
    checksum: str = Field(..., description="Content checksum for change detection")
    
    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Last update timestamp")
    
    # Schema version
    schema_version: str = Field(default="1.0", description="Metadata schema version")


class DocumentChunk(BaseModel):
    """Document chunk for embedding and storage."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    doc_id: str = Field(..., description="Parent document ID")
    text: str = Field(..., description="Chunk text content")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    chunk_index: int = Field(..., description="Chunk position in document")
    token_count: int = Field(..., description="Approximate token count")


class CollectionSchema(BaseModel):
    """ChromaDB collection schema definition."""
    collection_name: str = Field(default="college_advisor", description="Collection name")
    schema_version: str = Field(default="1.0", description="Schema version")
    # LOCKED embedding configuration - MVP choice
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model (LOCKED)")
    embedding_dimension: int = Field(default=384, description="Embedding vector dimension (LOCKED)")
    embedding_provider: str = Field(default="sentence_transformers", description="Embedding provider (LOCKED)")
    
    # Required metadata fields for filtering
    required_fields: List[str] = Field(
        default_factory=lambda: [
            "doc_id", "entity_type", "school", "name", "location", 
            "source_id", "section", "schema_version"
        ],
        description="Required metadata fields"
    )
    
    # Indexed fields for fast filtering
    indexed_fields: List[str] = Field(
        default_factory=lambda: [
            "entity_type", "school", "gpa_band", "majors", 
            "interests", "location", "year"
        ],
        description="Fields indexed for fast filtering"
    )


def generate_doc_id(entity_type: str, school: str, name: str, year: int = None) -> str:
    """
    Generate standardized document ID.
    
    Args:
        entity_type: Type of entity
        school: Institution name
        name: Program/entity name
        year: Academic year (optional)
        
    Returns:
        str: Standardized document ID
    """
    # Normalize inputs
    entity_clean = entity_type.lower().replace(" ", "_")
    school_clean = school.lower().replace(" ", "_").replace(".", "")
    name_clean = name.lower().replace(" ", "_").replace(".", "")
    
    # Create base ID
    if year:
        doc_id = f"{entity_clean}_{school_clean}_{name_clean}_{year}"
    else:
        doc_id = f"{entity_clean}_{school_clean}_{name_clean}"
    
    # Truncate if too long and add hash for uniqueness
    if len(doc_id) > 100:
        hash_suffix = hashlib.md5(doc_id.encode()).hexdigest()[:8]
        doc_id = doc_id[:90] + "_" + hash_suffix
    
    return doc_id


def generate_chunk_id(doc_id: str, chunk_index: int) -> str:
    """
    Generate standardized chunk ID.
    
    Args:
        doc_id: Parent document ID
        chunk_index: Chunk position
        
    Returns:
        str: Standardized chunk ID
    """
    return f"{doc_id}_chunk_{chunk_index:04d}"


def generate_source_id(source_type: str, external_id: str) -> str:
    """
    Generate standardized source ID.
    
    Args:
        source_type: Source system type (scorecard, ipeds, etc.)
        external_id: External system identifier
        
    Returns:
        str: Standardized source ID
    """
    return f"{source_type}:{external_id}"


def calculate_content_checksum(content: str) -> str:
    """
    Calculate content checksum for change detection.
    
    Args:
        content: Text content
        
    Returns:
        str: SHA256 checksum
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def create_document_metadata(
    entity_type: EntityType,
    school: str,
    name: str,
    location: str,
    source_type: str,
    external_id: str,
    section: str,
    content: str,
    gpa_band: GPABand = GPABand.NOT_SPECIFIED,
    majors: List[str] = None,
    interests: List[str] = None,
    url: str = None,
    year: int = None
) -> DocumentMetadata:
    """
    Create standardized document metadata.
    
    Args:
        entity_type: Type of entity
        school: Institution name
        name: Program/entity name
        location: Geographic location
        source_type: Source system type
        external_id: External system ID
        section: Content section
        content: Text content for checksum
        gpa_band: GPA requirement band
        majors: Related majors
        interests: Interest tags
        url: Source URL
        year: Academic year
        
    Returns:
        DocumentMetadata: Standardized metadata
    """
    if year is None:
        year = datetime.now().year
    
    if majors is None:
        majors = []
    
    if interests is None:
        interests = []
    
    doc_id = generate_doc_id(entity_type.value, school, name, year)
    source_id = generate_source_id(source_type, external_id)
    checksum = calculate_content_checksum(content)
    
    return DocumentMetadata(
        doc_id=doc_id,
        entity_type=entity_type,
        school=school,
        name=name,
        gpa_band=gpa_band,
        majors=majors,
        interests=interests,
        location=location,
        url=url,
        source_id=source_id,
        year=year,
        section=section,
        checksum=checksum
    )


# Schema validation functions
def validate_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Validate metadata against schema.
    
    Args:
        metadata: Metadata dictionary
        
    Returns:
        bool: True if valid
    """
    try:
        DocumentMetadata(**metadata)
        return True
    except Exception:
        return False


def migrate_metadata_v1_to_v2(old_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate metadata from v1 to v2 schema.
    
    Args:
        old_metadata: Old metadata format
        
    Returns:
        Dict: Migrated metadata
    """
    # Placeholder for future schema migrations
    return old_metadata


# Export schema constants for API contract
COLLECTION_NAME = "college_advisor"
SCHEMA_VERSION = "1.0"

# EMBEDDING STRATEGY - LOCKED FOR MVP
# The data repo owns all embeddings - API should NOT embed
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # LOCKED - MVP choice
EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 dimension
EMBEDDING_PROVIDER = "sentence_transformers"  # LOCKED - data repo owns embeddings

# Required fields that API can depend on
REQUIRED_METADATA_FIELDS = [
    "doc_id", "entity_type", "school", "name", "location", 
    "source_id", "section", "schema_version"
]

# Indexed fields for API filtering
INDEXED_METADATA_FIELDS = [
    "entity_type", "school", "gpa_band", "majors", 
    "interests", "location", "year"
]
