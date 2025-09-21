"""Data loaders for various file formats with advanced validation and error handling."""

import json
import logging
import pandas as pd
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator, Union
from pydantic import ValidationError

from ..models import Document, DocumentType, ProcessingStats
from ..config import config

logger = logging.getLogger(__name__)


class BaseLoader(ABC):
    """Abstract base class for data loaders."""
    
    def __init__(self, doc_type: DocumentType):
        self.doc_type = doc_type
        self.stats = ProcessingStats()
    
    @abstractmethod
    def load(self, source: Path) -> Iterator[Document]:
        """Load documents from source."""
        pass
    
    def validate_document(self, doc_data: Dict[str, Any]) -> Optional[Document]:
        """Validate and create Document instance."""
        try:
            # Ensure required fields
            if 'id' not in doc_data:
                doc_data['id'] = f"{self.doc_type.value}_{len(self.stats.errors) + self.stats.total_documents}"
            
            if 'title' not in doc_data:
                doc_data['title'] = doc_data.get('name', f"Document {doc_data['id']}")
            
            if 'content' not in doc_data:
                # Build content from available fields
                content_parts = []
                for field in ['description', 'summary', 'details', 'text']:
                    if field in doc_data and doc_data[field]:
                        content_parts.append(str(doc_data[field]))
                doc_data['content'] = ' '.join(content_parts) if content_parts else doc_data.get('title', '')
            
            doc_data['doc_type'] = self.doc_type
            
            return Document(**doc_data)
        
        except ValidationError as e:
            error_msg = f"Validation error for document {doc_data.get('id', 'unknown')}: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)
            return None
        except Exception as e:
            error_msg = f"Unexpected error processing document {doc_data.get('id', 'unknown')}: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)
            return None


class CSVLoader(BaseLoader):
    """Loader for CSV files with flexible schema mapping."""
    
    def __init__(self, doc_type: DocumentType, schema_mapping: Optional[Dict[str, str]] = None):
        super().__init__(doc_type)
        self.schema_mapping = schema_mapping or self._get_default_mapping()
    
    def _get_default_mapping(self) -> Dict[str, str]:
        """Get default column mapping based on document type."""
        base_mapping = {
            'id': 'id',
            'name': 'title',
            'description': 'content'
        }
        
        if self.doc_type == DocumentType.UNIVERSITY:
            return {
                **base_mapping,
                'location': 'location',
                'type': 'university_type',
                'website': 'source_url',
                'gpa_requirement': 'gpa_requirement',
                'acceptance_rate': 'acceptance_rate',
                'tuition': 'tuition',
                'programs': 'programs'
            }
        elif self.doc_type == DocumentType.SUMMER_PROGRAM:
            return {
                **base_mapping,
                'host_institution': 'university_name',
                'location': 'location',
                'duration': 'duration',
                'age_range': 'age_range',
                'subject_area': 'subject_area',
                'cost': 'cost',
                'website': 'source_url'
            }
        
        return base_mapping
    
    def load(self, source: Path) -> Iterator[Document]:
        """Load documents from CSV file."""
        try:
            logger.info(f"Loading CSV file: {source}")
            df = pd.read_csv(source)
            
            for idx, row in df.iterrows():
                try:
                    # Map columns to document fields
                    doc_data = {}
                    metadata = {}
                    
                    for csv_col, doc_field in self.schema_mapping.items():
                        if csv_col in row and pd.notna(row[csv_col]):
                            value = row[csv_col]
                            
                            # Handle special fields
                            if doc_field in ['title', 'content', 'source_url']:
                                doc_data[doc_field] = str(value)
                            elif doc_field == 'id':
                                doc_data[doc_field] = str(value)
                            else:
                                metadata[doc_field] = value
                    
                    # Add unmapped columns to metadata
                    for col in row.index:
                        if col not in self.schema_mapping and pd.notna(row[col]):
                            metadata[col] = row[col]
                    
                    doc_data['metadata'] = metadata
                    
                    document = self.validate_document(doc_data)
                    if document:
                        self.stats.total_documents += 1
                        yield document
                
                except Exception as e:
                    error_msg = f"Error processing row {idx}: {e}"
                    logger.error(error_msg)
                    self.stats.errors.append(error_msg)
        
        except Exception as e:
            error_msg = f"Error loading CSV file {source}: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)


class JSONLoader(BaseLoader):
    """Loader for JSON files with nested data support."""
    
    def load(self, source: Path) -> Iterator[Document]:
        """Load documents from JSON file."""
        try:
            logger.info(f"Loading JSON file: {source}")
            
            with open(source, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                documents = data
            elif isinstance(data, dict):
                if 'documents' in data:
                    documents = data['documents']
                elif 'data' in data:
                    documents = data['data']
                else:
                    documents = [data]
            else:
                raise ValueError(f"Unsupported JSON structure in {source}")
            
            for idx, doc_data in enumerate(documents):
                try:
                    if not isinstance(doc_data, dict):
                        self.stats.warnings.append(f"Skipping non-dict item at index {idx}")
                        continue
                    
                    document = self.validate_document(doc_data)
                    if document:
                        self.stats.total_documents += 1
                        yield document
                
                except Exception as e:
                    error_msg = f"Error processing document {idx}: {e}"
                    logger.error(error_msg)
                    self.stats.errors.append(error_msg)
        
        except Exception as e:
            error_msg = f"Error loading JSON file {source}: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)


class TextLoader(BaseLoader):
    """Loader for plain text files with intelligent parsing."""
    
    def __init__(self, doc_type: DocumentType, delimiter: str = "\n\n"):
        super().__init__(doc_type)
        self.delimiter = delimiter
    
    def load(self, source: Path) -> Iterator[Document]:
        """Load documents from text file."""
        try:
            logger.info(f"Loading text file: {source}")
            
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split content by delimiter
            sections = content.split(self.delimiter)
            
            for idx, section in enumerate(sections):
                section = section.strip()
                if not section:
                    continue
                
                try:
                    # Extract title from first line if possible
                    lines = section.split('\n')
                    title = lines[0].strip() if lines else f"Section {idx + 1}"
                    
                    doc_data = {
                        'id': f"{source.stem}_{idx + 1}",
                        'title': title,
                        'content': section,
                        'metadata': {
                            'source_file': str(source),
                            'section_index': idx
                        }
                    }
                    
                    document = self.validate_document(doc_data)
                    if document:
                        self.stats.total_documents += 1
                        yield document
                
                except Exception as e:
                    error_msg = f"Error processing section {idx}: {e}"
                    logger.error(error_msg)
                    self.stats.errors.append(error_msg)
        
        except Exception as e:
            error_msg = f"Error loading text file {source}: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)


class LoaderFactory:
    """Factory for creating appropriate loaders based on file format."""
    
    @staticmethod
    def create_loader(file_format: str, doc_type: DocumentType, **kwargs) -> BaseLoader:
        """Create appropriate loader for the given format."""
        loaders = {
            'csv': CSVLoader,
            'json': JSONLoader,
            'txt': TextLoader,
            'text': TextLoader
        }
        
        if file_format.lower() not in loaders:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        loader_class = loaders[file_format.lower()]
        return loader_class(doc_type, **kwargs)
