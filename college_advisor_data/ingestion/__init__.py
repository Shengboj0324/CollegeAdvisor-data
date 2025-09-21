"""Data ingestion module for College Advisor pipeline."""

from .pipeline import IngestionPipeline
from .loaders import CSVLoader, JSONLoader, TextLoader

__all__ = ["IngestionPipeline", "CSVLoader", "JSONLoader", "TextLoader"]
