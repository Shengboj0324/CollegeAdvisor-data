"""Main ingestion pipeline orchestrating the complete data processing workflow."""

import logging
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import Document, DocumentType, ProcessingStats
from ..config import config
from .loaders import LoaderFactory
from ..preprocessing.preprocessor import TextPreprocessor
from ..preprocessing.chunker import TextChunker
from ..embedding.embedder import EmbeddingService
from ..storage.chroma_client import ChromaDBClient

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Complete data ingestion and processing pipeline."""
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.chunker = TextChunker()
        self.embedding_service = EmbeddingService()
        self.chroma_client = ChromaDBClient()
        self.stats = ProcessingStats()
    
    def ingest_from_file(self, 
                        source_path: Path, 
                        file_format: str, 
                        doc_type: str,
                        save_processed: bool = True) -> ProcessingStats:
        """
        Complete ingestion pipeline from file to ChromaDB.
        
        Args:
            source_path: Path to source data file
            file_format: Format of the source file (csv, json, txt)
            doc_type: Type of documents (university, program, summer_program)
            save_processed: Whether to save processed data to disk
            
        Returns:
            Processing statistics
        """
        start_time = time.time()
        logger.info(f"Starting ingestion pipeline for {source_path}")
        
        try:
            # Step 1: Load documents
            documents = self._load_documents(source_path, file_format, doc_type)
            if not documents:
                logger.warning("No documents loaded")
                return self.stats
            
            # Step 2: Process documents
            processed_data = self._process_documents(documents)
            if not processed_data:
                logger.warning("No documents processed successfully")
                return self.stats
            
            # Step 3: Save processed data if requested
            if save_processed:
                self._save_processed_data(processed_data, source_path)
            
            # Step 4: Load into ChromaDB
            self._load_to_chromadb(processed_data)
            
            # Update final statistics
            self.stats.processing_time = time.time() - start_time
            logger.info(f"Pipeline completed in {self.stats.processing_time:.2f} seconds")
            
            return self.stats
        
        except Exception as e:
            error_msg = f"Pipeline failed: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)
            self.stats.processing_time = time.time() - start_time
            return self.stats
    
    def _load_documents(self, source_path: Path, file_format: str, doc_type: str) -> List[Document]:
        """Load documents from source file."""
        logger.info(f"Loading documents from {source_path}")
        
        try:
            doc_type_enum = DocumentType(doc_type)
            loader = LoaderFactory.create_loader(file_format, doc_type_enum)
            
            documents = list(loader.load(source_path))
            
            # Update statistics
            self.stats.total_documents = len(documents)
            self.stats.errors.extend(loader.stats.errors)
            self.stats.warnings.extend(loader.stats.warnings)
            
            logger.info(f"Loaded {len(documents)} documents")
            return documents
        
        except Exception as e:
            error_msg = f"Error loading documents: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)
            return []
    
    def _process_documents(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Process documents through preprocessing, chunking, and embedding."""
        logger.info(f"Processing {len(documents)} documents")
        
        processed_data = []
        
        for i, document in enumerate(documents):
            try:
                logger.debug(f"Processing document {i+1}/{len(documents)}: {document.id}")
                
                # Step 1: Preprocess text
                preprocessing_result = self.preprocessor.preprocess(document)
                
                # Step 2: Create chunks
                chunks = self.chunker.chunk_document(document)
                if not chunks:
                    logger.warning(f"No chunks created for document {document.id}")
                    continue
                
                # Step 3: Generate embeddings
                chunk_texts = [chunk.content for chunk in chunks]
                chunk_ids = [f"{document.id}_chunk_{chunk.metadata.chunk_index}" for chunk in chunks]
                
                embeddings = self.embedding_service.embed_batch(chunk_texts, chunk_ids)
                
                # Step 4: Enhance metadata with preprocessing results
                for chunk, embedding in zip(chunks, embeddings):
                    # Add keywords and entities to metadata
                    chunk.metadata.keywords = preprocessing_result.keywords
                    
                    # Add extracted entities
                    if preprocessing_result.entities:
                        for entity_type, values in preprocessing_result.entities.items():
                            if entity_type == 'gpa' and values:
                                try:
                                    chunk.metadata.gpa_requirement = float(values[0])
                                except (ValueError, IndexError):
                                    pass
                
                # Store processed data
                doc_data = {
                    'document': document.dict(),
                    'preprocessing': preprocessing_result.__dict__,
                    'chunks': [chunk.content for chunk in chunks],
                    'metadatas': [chunk.metadata.dict() for chunk in chunks],
                    'embeddings': [embedding.dict() for embedding in embeddings]
                }
                
                processed_data.append(doc_data)
                self.stats.total_chunks += len(chunks)
                self.stats.total_embeddings += len(embeddings)
                
            except Exception as e:
                error_msg = f"Error processing document {document.id}: {e}"
                logger.error(error_msg)
                self.stats.errors.append(error_msg)
        
        logger.info(f"Successfully processed {len(processed_data)} documents")
        return processed_data
    
    def _save_processed_data(self, processed_data: List[Dict[str, Any]], source_path: Path) -> None:
        """Save processed data to disk."""
        try:
            # Create processed directory if it doesn't exist
            config.processed_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{source_path.stem}_processed_{timestamp}.json"
            output_path = config.processed_dir / output_filename
            
            # Prepare data for saving
            save_data = {
                'metadata': {
                    'source_file': str(source_path),
                    'processed_at': datetime.now().isoformat(),
                    'total_documents': len(processed_data),
                    'total_chunks': self.stats.total_chunks,
                    'total_embeddings': self.stats.total_embeddings
                },
                'documents': processed_data
            }
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved processed data to {output_path}")
        
        except Exception as e:
            error_msg = f"Error saving processed data: {e}"
            logger.error(error_msg)
            self.stats.warnings.append(error_msg)
    
    def _load_to_chromadb(self, processed_data: List[Dict[str, Any]]) -> None:
        """Load processed data into ChromaDB."""
        logger.info("Loading data into ChromaDB")
        
        try:
            # Prepare data for ChromaDB
            all_embeddings = []
            all_chunks = []
            all_metadatas = []
            
            for doc_data in processed_data:
                embeddings = doc_data['embeddings']
                chunks = doc_data['chunks']
                metadatas = doc_data['metadatas']
                
                # Convert to proper objects
                from ..models import EmbeddingResult, ChunkMetadata
                
                for emb_dict, chunk, meta_dict in zip(embeddings, chunks, metadatas):
                    all_embeddings.append(EmbeddingResult(**emb_dict))
                    all_chunks.append(chunk)
                    all_metadatas.append(ChunkMetadata(**meta_dict))
            
            # Upsert to ChromaDB
            chroma_stats = self.chroma_client.upsert_embeddings(
                all_embeddings, 
                all_chunks, 
                all_metadatas
            )
            
            # Update statistics
            self.stats.errors.extend(chroma_stats.errors)
            
            logger.info(f"Successfully loaded {chroma_stats.total_embeddings} embeddings to ChromaDB")
        
        except Exception as e:
            error_msg = f"Error loading to ChromaDB: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    def process_directory(self, 
                         source_dir: Path, 
                         file_pattern: str = "*.csv",
                         doc_type: str = "university") -> ProcessingStats:
        """Process all files in a directory."""
        logger.info(f"Processing directory: {source_dir}")
        
        files = list(source_dir.glob(file_pattern))
        if not files:
            logger.warning(f"No files found matching pattern {file_pattern} in {source_dir}")
            return self.stats
        
        total_stats = ProcessingStats()
        
        for file_path in files:
            try:
                file_format = file_path.suffix[1:]  # Remove the dot
                file_stats = self.ingest_from_file(file_path, file_format, doc_type)
                
                # Aggregate statistics
                total_stats.total_documents += file_stats.total_documents
                total_stats.total_chunks += file_stats.total_chunks
                total_stats.total_embeddings += file_stats.total_embeddings
                total_stats.processing_time += file_stats.processing_time
                total_stats.errors.extend(file_stats.errors)
                total_stats.warnings.extend(file_stats.warnings)
                
            except Exception as e:
                error_msg = f"Error processing file {file_path}: {e}"
                logger.error(error_msg)
                total_stats.errors.append(error_msg)
        
        return total_stats
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of all pipeline components."""
        health_status = {
            "pipeline": "healthy",
            "components": {}
        }
        
        try:
            # Check embedding service
            health_status["components"]["embedding"] = self.embedding_service.health_check()
            
            # Check ChromaDB
            try:
                count = self.chroma_client.get_collection_count()
                health_status["components"]["chromadb"] = {
                    "status": "healthy",
                    "document_count": count
                }
            except Exception as e:
                health_status["components"]["chromadb"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # Check if any component is unhealthy
            for component, status in health_status["components"].items():
                if status.get("status") != "healthy":
                    health_status["pipeline"] = "unhealthy"
                    break
        
        except Exception as e:
            health_status["pipeline"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
