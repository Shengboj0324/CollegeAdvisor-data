"""ChromaDB client with cloud support and advanced operations."""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ..models import EmbeddingResult, ProcessingStats, ChunkMetadata
from ..config import config

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """Advanced ChromaDB client with cloud support and batch operations."""
    
    def __init__(self, collection_name: str = None):
        self.collection_name = collection_name or config.chroma_collection_name
        self.client = None
        self.collection = None
        self._connect()
    
    def _connect(self):
        """Connect to ChromaDB (local or cloud)."""
        try:
            if config.chroma_cloud_host and config.chroma_cloud_api_key:
                # Cloud connection
                logger.info(f"Connecting to ChromaDB cloud: {config.chroma_cloud_host}")
                self.client = chromadb.HttpClient(
                    host=config.chroma_cloud_host,
                    port=443,
                    ssl=True,
                    headers={"Authorization": f"Bearer {config.chroma_cloud_api_key}"}
                )
            else:
                # Local connection
                logger.info(f"Connecting to local ChromaDB: {config.chroma_host}:{config.chroma_port}")
                self.client = chromadb.HttpClient(
                    host=config.chroma_host,
                    port=config.chroma_port
                )
            
            # Test connection
            self.client.heartbeat()
            logger.info("Successfully connected to ChromaDB")
            
        except Exception as e:
            logger.error(f"Error connecting to ChromaDB: {e}")
            raise
    
    def get_or_create_collection(self, collection_name: str = None) -> Any:
        """Get or create a ChromaDB collection."""
        collection_name = collection_name or self.collection_name
        
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"Retrieved existing collection: {collection_name}")
        
        except Exception:
            # Create new collection
            logger.info(f"Creating new collection: {collection_name}")
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "College Advisor data collection"}
            )
        
        return self.collection
    
    def reset_collection(self, collection_name: str = None) -> None:
        """Delete and recreate a collection."""
        collection_name = collection_name or self.collection_name
        
        try:
            # Delete existing collection
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Could not delete collection {collection_name}: {e}")
        
        # Create new collection
        self.get_or_create_collection(collection_name)
    
    def upsert_embeddings(self, 
                         embeddings: List[EmbeddingResult], 
                         chunks: List[str],
                         metadatas: List[ChunkMetadata]) -> ProcessingStats:
        """Upsert embeddings into ChromaDB with batch processing."""
        if not self.collection:
            self.get_or_create_collection()
        
        stats = ProcessingStats()
        batch_size = config.batch_size
        
        try:
            for i in range(0, len(embeddings), batch_size):
                batch_embeddings = embeddings[i:i + batch_size]
                batch_chunks = chunks[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                
                # Prepare data for ChromaDB
                ids = [emb.chunk_id for emb in batch_embeddings]
                vectors = [emb.embedding for emb in batch_embeddings]
                documents = batch_chunks
                metadata_dicts = [self._metadata_to_dict(meta) for meta in batch_metadatas]
                
                # Upsert batch
                self.collection.upsert(
                    ids=ids,
                    embeddings=vectors,
                    documents=documents,
                    metadatas=metadata_dicts
                )
                
                stats.total_embeddings += len(batch_embeddings)
                logger.info(f"Upserted batch {i//batch_size + 1}: {len(batch_embeddings)} embeddings")
                
                # Small delay to avoid overwhelming the database
                time.sleep(0.1)
        
        except Exception as e:
            error_msg = f"Error upserting embeddings: {e}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
            raise
        
        return stats
    
    def search(self, 
               query: str, 
               n_results: int = 5,
               where: Optional[Dict] = None,
               collection_name: str = None) -> List[Dict[str, Any]]:
        """Search the collection using text query."""
        if not self.collection:
            self.get_or_create_collection(collection_name)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    }
                    formatted_results.append(result)
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching collection: {e}")
            raise
    
    def search_by_embedding(self,
                           embedding: List[float],
                           n_results: int = 5,
                           where: Optional[Dict] = None,
                           collection_name: str = None) -> List[Dict[str, Any]]:
        """Search using a pre-computed embedding."""
        if not self.collection:
            self.get_or_create_collection(collection_name)
        
        try:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    }
                    formatted_results.append(result)
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching by embedding: {e}")
            raise
    
    def get_collection_count(self, collection_name: str = None) -> int:
        """Get the number of documents in the collection."""
        if not self.collection:
            self.get_or_create_collection(collection_name)
        
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error getting collection count: {e}")
            return 0
    
    def get_collection_stats(self, collection_name: str = None) -> Dict[str, Any]:
        """Get detailed statistics about the collection."""
        if not self.collection:
            self.get_or_create_collection(collection_name)
        
        try:
            count = self.collection.count()
            
            # Get sample of metadata to analyze
            sample_results = self.collection.get(limit=min(100, count), include=["metadatas"])
            
            stats = {
                "total_documents": count,
                "collection_name": collection_name or self.collection_name,
                "document_types": {},
                "universities": set(),
                "subject_areas": set()
            }
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    # Count document types
                    doc_type = metadata.get('doc_type', 'unknown')
                    stats['document_types'][doc_type] = stats['document_types'].get(doc_type, 0) + 1
                    
                    # Collect universities
                    if metadata.get('university_name'):
                        stats['universities'].add(metadata['university_name'])
                    
                    # Collect subject areas
                    if metadata.get('subject_area'):
                        stats['subject_areas'].add(metadata['subject_area'])
            
            # Convert sets to lists for JSON serialization
            stats['universities'] = list(stats['universities'])
            stats['subject_areas'] = list(stats['subject_areas'])
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents by their IDs."""
        if not self.collection:
            self.get_or_create_collection()
        
        try:
            self.collection.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise
    
    def load_processed_data(self, collection_name: str = None) -> ProcessingStats:
        """Load processed data from the processed directory."""
        processed_dir = config.processed_dir
        stats = ProcessingStats()
        
        if not processed_dir.exists():
            logger.warning(f"Processed directory does not exist: {processed_dir}")
            return stats
        
        # Find processed files
        processed_files = list(processed_dir.glob("*.json"))
        if not processed_files:
            logger.warning(f"No processed files found in {processed_dir}")
            return stats
        
        logger.info(f"Loading {len(processed_files)} processed files")
        
        for file_path in processed_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract embeddings, chunks, and metadata
                embeddings = [EmbeddingResult(**emb) for emb in data.get('embeddings', [])]
                chunks = data.get('chunks', [])
                metadatas = [ChunkMetadata(**meta) for meta in data.get('metadatas', [])]
                
                if embeddings and chunks and metadatas:
                    file_stats = self.upsert_embeddings(embeddings, chunks, metadatas)
                    stats.total_embeddings += file_stats.total_embeddings
                    stats.errors.extend(file_stats.errors)
                
            except Exception as e:
                error_msg = f"Error loading file {file_path}: {e}"
                logger.error(error_msg)
                stats.errors.append(error_msg)
        
        return stats
    
    def _metadata_to_dict(self, metadata: ChunkMetadata) -> Dict[str, Any]:
        """Convert ChunkMetadata to dictionary for ChromaDB."""
        # ChromaDB has limitations on metadata types
        result = {}
        
        for field, value in metadata.dict().items():
            if value is not None:
                if isinstance(value, (str, int, float, bool)):
                    result[field] = value
                elif isinstance(value, list):
                    # Convert lists to comma-separated strings
                    result[field] = ",".join(str(v) for v in value)
                else:
                    # Convert other types to strings
                    result[field] = str(value)
        
        return result
