"""Intelligent text chunking with semantic boundary detection and token management."""

import logging
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

from ..models import Document, ChunkMetadata, DocumentType
from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    content: str
    start_pos: int
    end_pos: int
    token_count: int
    sentence_count: int
    metadata: ChunkMetadata


class TextChunker:
    """Advanced text chunker with semantic boundary detection."""
    
    def __init__(self, 
                 chunk_size: int = None, 
                 overlap_size: int = None,
                 min_chunk_size: int = 100,
                 max_chunk_size: int = 1200):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Target chunk size in tokens
            overlap_size: Overlap between chunks in tokens
            min_chunk_size: Minimum chunk size in tokens
            max_chunk_size: Maximum chunk size in tokens
        """
        self.chunk_size = chunk_size or config.chunk_size
        self.overlap_size = overlap_size or config.chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Sentence boundary patterns
        self.strong_boundaries = [
            r'\n\n+',  # Paragraph breaks
            r'\n\s*[-•*]\s+',  # List items
            r'\n\s*\d+\.\s+',  # Numbered lists
            r'\n\s*[A-Z][^.]*:\s*',  # Section headers
        ]
        
        # Weak boundaries (prefer but not required)
        self.weak_boundaries = [
            r'\.\s+[A-Z]',  # Sentence endings
            r';\s+',  # Semicolons
            r':\s+',  # Colons
        ]
    
    def chunk_document(self, document: Document) -> List[TextChunk]:
        """
        Chunk a document into semantically coherent pieces.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of text chunks with metadata
        """
        text = document.content
        if not text.strip():
            return []
        
        # First, try to split by strong boundaries
        chunks = self._split_by_boundaries(text, document)
        
        # If chunks are too large, split further
        final_chunks = []
        for chunk in chunks:
            if chunk.token_count > self.max_chunk_size:
                sub_chunks = self._split_large_chunk(chunk, document)
                final_chunks.extend(sub_chunks)
            elif chunk.token_count >= self.min_chunk_size:
                final_chunks.append(chunk)
            else:
                # Try to merge small chunks
                if final_chunks and final_chunks[-1].token_count + chunk.token_count <= self.max_chunk_size:
                    final_chunks[-1] = self._merge_chunks(final_chunks[-1], chunk, document)
                else:
                    final_chunks.append(chunk)
        
        # Add overlap between chunks
        overlapped_chunks = self._add_overlap(final_chunks, text, document)
        
        # Update chunk indices
        for i, chunk in enumerate(overlapped_chunks):
            chunk.metadata.chunk_index = i
        
        return overlapped_chunks
    
    def _split_by_boundaries(self, text: str, document: Document) -> List[TextChunk]:
        """Split text by semantic boundaries."""
        chunks = []
        
        # Try strong boundaries first
        for pattern in self.strong_boundaries:
            if re.search(pattern, text):
                parts = re.split(pattern, text)
                if len(parts) > 1:
                    current_pos = 0
                    for part in parts:
                        if part.strip():
                            chunk = self._create_chunk(
                                part.strip(), 
                                current_pos, 
                                current_pos + len(part), 
                                document,
                                len(chunks)
                            )
                            if chunk.token_count >= self.min_chunk_size:
                                chunks.append(chunk)
                        current_pos += len(part)
                    return chunks
        
        # If no strong boundaries, split by sentences
        sentences = sent_tokenize(text)
        if len(sentences) <= 1:
            # Single sentence or no sentences, return as single chunk
            return [self._create_chunk(text, 0, len(text), document, 0)]
        
        current_chunk = ""
        current_tokens = 0
        start_pos = 0
        
        for sentence in sentences:
            sentence_tokens = len(word_tokenize(sentence))
            
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Create chunk from current content
                chunk = self._create_chunk(
                    current_chunk.strip(), 
                    start_pos, 
                    start_pos + len(current_chunk), 
                    document,
                    len(chunks)
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk = sentence
                current_tokens = sentence_tokens
                start_pos = text.find(sentence, start_pos)
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    start_pos = text.find(sentence)
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk.strip():
            chunk = self._create_chunk(
                current_chunk.strip(), 
                start_pos, 
                start_pos + len(current_chunk), 
                document,
                len(chunks)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_large_chunk(self, chunk: TextChunk, document: Document) -> List[TextChunk]:
        """Split a chunk that's too large."""
        text = chunk.content
        sentences = sent_tokenize(text)
        
        if len(sentences) <= 1:
            # Can't split further, return as is
            return [chunk]
        
        sub_chunks = []
        current_chunk = ""
        current_tokens = 0
        start_pos = 0
        
        for sentence in sentences:
            sentence_tokens = len(word_tokenize(sentence))
            
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Create sub-chunk
                sub_chunk = self._create_chunk(
                    current_chunk.strip(),
                    chunk.start_pos + start_pos,
                    chunk.start_pos + start_pos + len(current_chunk),
                    document,
                    chunk.metadata.chunk_index
                )
                sub_chunks.append(sub_chunk)
                
                # Start new chunk
                current_chunk = sentence
                current_tokens = sentence_tokens
                start_pos = text.find(sentence, start_pos)
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    start_pos = text.find(sentence)
                current_tokens += sentence_tokens
        
        # Add final sub-chunk
        if current_chunk.strip():
            sub_chunk = self._create_chunk(
                current_chunk.strip(),
                chunk.start_pos + start_pos,
                chunk.start_pos + start_pos + len(current_chunk),
                document,
                chunk.metadata.chunk_index
            )
            sub_chunks.append(sub_chunk)
        
        return sub_chunks
    
    def _merge_chunks(self, chunk1: TextChunk, chunk2: TextChunk, document: Document) -> TextChunk:
        """Merge two adjacent chunks."""
        merged_content = chunk1.content + " " + chunk2.content
        merged_tokens = chunk1.token_count + chunk2.token_count
        merged_sentences = chunk1.sentence_count + chunk2.sentence_count
        
        # Create new metadata
        metadata = ChunkMetadata(
            document_id=document.id,
            chunk_index=chunk1.metadata.chunk_index,
            chunk_size=merged_tokens,
            doc_type=document.doc_type,
            **self._extract_metadata_from_document(document)
        )
        
        return TextChunk(
            content=merged_content,
            start_pos=chunk1.start_pos,
            end_pos=chunk2.end_pos,
            token_count=merged_tokens,
            sentence_count=merged_sentences,
            metadata=metadata
        )
    
    def _add_overlap(self, chunks: List[TextChunk], full_text: str, document: Document) -> List[TextChunk]:
        """Add overlap between adjacent chunks."""
        if len(chunks) <= 1 or self.overlap_size <= 0:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            content = chunk.content
            
            # Add overlap from previous chunk
            if i > 0:
                prev_chunk = chunks[i - 1]
                overlap_text = self._get_overlap_text(prev_chunk.content, self.overlap_size, from_end=True)
                if overlap_text:
                    content = overlap_text + " " + content
            
            # Add overlap from next chunk
            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                overlap_text = self._get_overlap_text(next_chunk.content, self.overlap_size, from_end=False)
                if overlap_text:
                    content = content + " " + overlap_text
            
            # Create new chunk with overlap
            new_chunk = TextChunk(
                content=content,
                start_pos=chunk.start_pos,
                end_pos=chunk.end_pos,
                token_count=len(word_tokenize(content)),
                sentence_count=len(sent_tokenize(content)),
                metadata=chunk.metadata
            )
            
            overlapped_chunks.append(new_chunk)
        
        return overlapped_chunks
    
    def _get_overlap_text(self, text: str, overlap_tokens: int, from_end: bool = True) -> str:
        """Extract overlap text from beginning or end of chunk."""
        tokens = word_tokenize(text)
        
        if len(tokens) <= overlap_tokens:
            return text
        
        if from_end:
            overlap_tokens_list = tokens[-overlap_tokens:]
        else:
            overlap_tokens_list = tokens[:overlap_tokens]
        
        return " ".join(overlap_tokens_list)
    
    def _create_chunk(self, content: str, start_pos: int, end_pos: int, 
                     document: Document, chunk_index: int) -> TextChunk:
        """Create a TextChunk with metadata."""
        tokens = word_tokenize(content)
        sentences = sent_tokenize(content)
        
        metadata = ChunkMetadata(
            document_id=document.id,
            chunk_index=chunk_index,
            chunk_size=len(tokens),
            doc_type=document.doc_type,
            **self._extract_metadata_from_document(document)
        )
        
        return TextChunk(
            content=content,
            start_pos=start_pos,
            end_pos=end_pos,
            token_count=len(tokens),
            sentence_count=len(sentences),
            metadata=metadata
        )
    
    def _extract_metadata_from_document(self, document: Document) -> Dict:
        """Extract relevant metadata from document for chunks."""
        metadata = {}
        doc_metadata = document.metadata or {}
        
        # Map document metadata to chunk metadata fields
        field_mapping = {
            'university_name': ['university_name', 'name', 'institution'],
            'program_name': ['program_name', 'program', 'title'],
            'location': ['location', 'city', 'state'],
            'subject_area': ['subject_area', 'field', 'discipline'],
            'gpa_requirement': ['gpa_requirement', 'gpa', 'min_gpa'],
            'duration': ['duration', 'length'],
            'age_range': ['age_range', 'ages'],
            'cost': ['cost', 'tuition', 'price', 'fee']
        }
        
        for chunk_field, doc_fields in field_mapping.items():
            for doc_field in doc_fields:
                if doc_field in doc_metadata:
                    metadata[chunk_field] = doc_metadata[doc_field]
                    break
        
        return metadata
