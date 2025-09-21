"""
College Advisor Data Pipeline

A comprehensive data ingestion, processing, and embedding pipeline for the College Advisor AI app.
Handles university programs, summer camps, and admissions data with ChromaDB integration.
"""

__version__ = "0.1.0"
__author__ = "College Advisor Team"

from .config import Config
from .models import Document, ChunkMetadata, EmbeddingResult

__all__ = ["Config", "Document", "ChunkMetadata", "EmbeddingResult"]
