"""
ChromaDB client with standardized schema and production-ready operations.

This client implements the canonical data contract for CollegeAdvisor,
ensuring consistent metadata structure and reliable operations.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ..schemas import (
    DocumentMetadata, DocumentChunk, CollectionSchema,
    COLLECTION_NAME, SCHEMA_VERSION, EMBEDDING_MODEL, EMBEDDING_DIMENSION,
    REQUIRED_METADATA_FIELDS, INDEXED_METADATA_FIELDS
)
from ..config import config

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """
    Production-ready ChromaDB client with standardized schema.

    This client enforces the canonical metadata schema and provides
    reliable operations for the CollegeAdvisor data pipeline.
    """

    def __init__(self, collection_name: str = None):
        self.collection_name = collection_name or COLLECTION_NAME
        self.client = None
        self.collection = None
        self.schema = CollectionSchema()
        self._connect()

    def _connect(self):
        """Connect to ChromaDB with proper error handling and heartbeat."""
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

            # Test connection with heartbeat
            heartbeat = self.client.heartbeat()
            logger.info(f"Successfully connected to ChromaDB - heartbeat: {heartbeat}")

        except Exception as e:
            logger.error(f"Error connecting to ChromaDB: {e}")
            raise ConnectionError(f"Failed to connect to ChromaDB: {e}")

    def heartbeat(self) -> Dict[str, Any]:
        """Check ChromaDB connection health."""
        try:
            return self.client.heartbeat()
        except Exception as e:
            logger.error(f"ChromaDB heartbeat failed: {e}")
            raise
    
    def get_or_create_collection(self, collection_name: str = None) -> Any:
        """Get or create a ChromaDB collection with standardized schema."""
        collection_name = collection_name or self.collection_name

        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"Retrieved existing collection: {collection_name}")

            # Validate schema version
            collection_metadata = self.collection.metadata or {}
            if collection_metadata.get("schema_version") != SCHEMA_VERSION:
                logger.warning(f"Collection schema version mismatch: {collection_metadata.get('schema_version')} != {SCHEMA_VERSION}")

        except Exception:
            # Create new collection with schema metadata
            logger.info(f"Creating new collection: {collection_name}")
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={
                    "description": "CollegeAdvisor standardized data collection",
                    "schema_version": SCHEMA_VERSION,
                    "embedding_model": EMBEDDING_MODEL,
                    "embedding_dimension": EMBEDDING_DIMENSION,
                    "created_at": time.time()
                }
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
    
    def upsert(self,
               chunks: List[DocumentChunk],
               embeddings: List[List[float]]) -> Dict[str, Any]:
        """
        Upsert document chunks with standardized metadata schema.

        Args:
            chunks: List of DocumentChunk objects with standardized metadata
            embeddings: List of embedding vectors

        Returns:
            Dict: Upsert statistics
        """
        if not self.collection:
            self.get_or_create_collection()

        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        stats = {
            "total_chunks": len(chunks),
            "successful_chunks": 0,
            "failed_chunks": 0,
            "errors": []
        }

        batch_size = config.batch_size

        try:
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]

                # Prepare data for ChromaDB
                ids = [chunk.chunk_id for chunk in batch_chunks]
                vectors = batch_embeddings
                documents = [chunk.text for chunk in batch_chunks]
                metadatas = [self._metadata_to_dict(chunk.metadata) for chunk in batch_chunks]

                # Validate metadata before upsert
                for j, metadata in enumerate(metadatas):
                    if not self._validate_metadata(metadata):
                        error_msg = f"Invalid metadata for chunk {ids[j]}"
                        stats["errors"].append(error_msg)
                        logger.error(error_msg)
                        continue

                # Upsert batch
                self.collection.upsert(
                    ids=ids,
                    embeddings=vectors,
                    documents=documents,
                    metadatas=metadatas
                )

                stats["successful_chunks"] += len(batch_chunks)
                logger.info(f"Upserted batch {i//batch_size + 1}: {len(batch_chunks)} chunks")

                # Small delay to avoid overwhelming the database
                time.sleep(0.1)

        except Exception as e:
            error_msg = f"Error upserting chunks: {e}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
            stats["failed_chunks"] = stats["total_chunks"] - stats["successful_chunks"]
            raise

        return stats
    
    def query(self,
              query_text: str,
              n_results: int = 5,
              where: Optional[Dict] = None,
              where_document: Optional[Dict] = None,
              include: List[str] = None) -> List[Dict[str, Any]]:
        """
        Query the collection using text with standardized filtering.

        Args:
            query_text: Text query
            n_results: Number of results to return
            where: Metadata filters (e.g., {"entity_type": "college"})
            where_document: Document content filters
            include: Fields to include in results

        Returns:
            List[Dict]: Formatted query results
        """
        if not self.collection:
            self.get_or_create_collection()

        if include is None:
            include = ["documents", "metadatas", "distances"]

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=include
            )

            # Format results with standardized structure
            formatted_results = []
            if results.get('documents') and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'id': results['ids'][0][i] if results.get('ids') else None,
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                        'distance': results['distances'][0][i] if results.get('distances') else None,
                        'score': 1 - results['distances'][0][i] if results.get('distances') else None
                    }
                    formatted_results.append(result)

            return formatted_results

        except Exception as e:
            logger.error(f"Error querying collection: {e}")
            raise
    
    def query_by_embedding(self,
                          embedding: List[float],
                          n_results: int = 5,
                          where: Optional[Dict] = None,
                          where_document: Optional[Dict] = None,
                          include: List[str] = None) -> List[Dict[str, Any]]:
        """
        Query using a pre-computed embedding vector.

        Args:
            embedding: Pre-computed embedding vector
            n_results: Number of results to return
            where: Metadata filters
            where_document: Document content filters
            include: Fields to include in results

        Returns:
            List[Dict]: Formatted query results
        """
        if not self.collection:
            self.get_or_create_collection()

        if include is None:
            include = ["documents", "metadatas", "distances"]

        try:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=include
            )

            # Format results with standardized structure
            formatted_results = []
            if results.get('documents') and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'id': results['ids'][0][i] if results.get('ids') else None,
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                        'distance': results['distances'][0][i] if results.get('distances') else None,
                        'score': 1 - results['distances'][0][i] if results.get('distances') else None
                    }
                    formatted_results.append(result)

            return formatted_results

        except Exception as e:
            logger.error(f"Error querying by embedding: {e}")
            raise
    
    def count(self) -> int:
        """Get the number of documents in the collection."""
        if not self.collection:
            self.get_or_create_collection()

        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error getting collection count: {e}")
            return 0
    
    def stats(self) -> Dict[str, Any]:
        """Get detailed statistics about the collection with standardized schema."""
        if not self.collection:
            self.get_or_create_collection()

        try:
            count = self.collection.count()

            # Get sample of metadata to analyze
            sample_size = min(1000, count) if count > 0 else 0
            sample_results = self.collection.get(limit=sample_size, include=["metadatas"]) if sample_size > 0 else {"metadatas": []}

            stats = {
                "total_documents": count,
                "collection_name": self.collection_name,
                "schema_version": SCHEMA_VERSION,
                "embedding_model": EMBEDDING_MODEL,
                "sample_size": sample_size,
                "entity_types": {},
                "schools": set(),
                "locations": set(),
                "gpa_bands": {},
                "years": set(),
                "schema_compliance": 0.0
            }

            compliant_docs = 0

            if sample_results.get('metadatas'):
                for metadata in sample_results['metadatas']:
                    # Check schema compliance
                    if self._validate_metadata(metadata):
                        compliant_docs += 1

                    # Count entity types
                    entity_type = metadata.get('entity_type', 'unknown')
                    stats['entity_types'][entity_type] = stats['entity_types'].get(entity_type, 0) + 1

                    # Collect schools
                    if metadata.get('school'):
                        stats['schools'].add(metadata['school'])

                    # Collect locations
                    if metadata.get('location'):
                        stats['locations'].add(metadata['location'])

                    # Count GPA bands
                    gpa_band = metadata.get('gpa_band', 'not_specified')
                    stats['gpa_bands'][gpa_band] = stats['gpa_bands'].get(gpa_band, 0) + 1

                    # Collect years
                    if metadata.get('year'):
                        stats['years'].add(metadata['year'])

            # Calculate schema compliance
            if sample_size > 0:
                stats['schema_compliance'] = compliant_docs / sample_size

            # Convert sets to lists for JSON serialization
            stats['schools'] = sorted(list(stats['schools']))
            stats['locations'] = sorted(list(stats['locations']))
            stats['years'] = sorted(list(stats['years']))

            return stats

        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    def delete(self, ids: List[str] = None, where: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Delete documents by IDs or metadata filters.

        Args:
            ids: List of document IDs to delete
            where: Metadata filters for deletion

        Returns:
            Dict: Deletion statistics
        """
        if not self.collection:
            self.get_or_create_collection()

        if not ids and not where:
            raise ValueError("Must provide either ids or where filter")

        try:
            # Get count before deletion for stats
            if where:
                # Query to get IDs that match the filter
                results = self.collection.get(where=where, include=["metadatas"])
                ids_to_delete = results.get("ids", [])
            else:
                ids_to_delete = ids

            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete, where=where)
                logger.info(f"Deleted {len(ids_to_delete)} documents")

                return {
                    "deleted_count": len(ids_to_delete),
                    "deleted_ids": ids_to_delete[:10],  # First 10 for logging
                    "success": True
                }
            else:
                return {
                    "deleted_count": 0,
                    "deleted_ids": [],
                    "success": True,
                    "message": "No documents matched deletion criteria"
                }

        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return {
                "deleted_count": 0,
                "deleted_ids": [],
                "success": False,
                "error": str(e)
            }
    
    def get_documents(self,
                     ids: List[str] = None,
                     where: Dict[str, Any] = None,
                     limit: int = None,
                     offset: int = None,
                     include: List[str] = None) -> Dict[str, Any]:
        """
        Get documents from the collection.

        Args:
            ids: Specific document IDs to retrieve
            where: Metadata filters
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            include: Fields to include in results

        Returns:
            Dict: Retrieved documents
        """
        if not self.collection:
            self.get_or_create_collection()

        if include is None:
            include = ["documents", "metadatas"]

        try:
            results = self.collection.get(
                ids=ids,
                where=where,
                limit=limit,
                offset=offset,
                include=include
            )

            return results

        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            raise
    
    def _metadata_to_dict(self, metadata: DocumentMetadata) -> Dict[str, Any]:
        """
        Convert DocumentMetadata to dictionary for ChromaDB.

        ChromaDB has limitations on metadata types - only str, int, float, bool allowed.
        """
        result = {}

        # Convert Pydantic model to dict
        metadata_dict = metadata.dict() if hasattr(metadata, 'dict') else metadata

        for field, value in metadata_dict.items():
            if value is not None:
                if isinstance(value, (str, int, float, bool)):
                    result[field] = value
                elif isinstance(value, list):
                    # Convert lists to comma-separated strings
                    result[field] = ",".join(str(v) for v in value)
                elif hasattr(value, 'value'):  # Enum
                    result[field] = value.value
                else:
                    # Convert other types to strings
                    result[field] = str(value)

        return result

    def _validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Validate metadata against standardized schema.

        Args:
            metadata: Metadata dictionary to validate

        Returns:
            bool: True if metadata is valid
        """
        try:
            # Check required fields
            for field in REQUIRED_METADATA_FIELDS:
                if field not in metadata:
                    logger.warning(f"Missing required field: {field}")
                    return False

            # Check schema version
            if metadata.get("schema_version") != SCHEMA_VERSION:
                logger.warning(f"Schema version mismatch: {metadata.get('schema_version')} != {SCHEMA_VERSION}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating metadata: {e}")
            return False

    def create_filters(self,
                      entity_types: List[str] = None,
                      schools: List[str] = None,
                      gpa_bands: List[str] = None,
                      locations: List[str] = None,
                      years: List[int] = None,
                      majors: List[str] = None) -> Dict[str, Any]:
        """
        Create standardized metadata filters for queries.

        Args:
            entity_types: Filter by entity types
            schools: Filter by school names
            gpa_bands: Filter by GPA bands
            locations: Filter by locations
            years: Filter by years
            majors: Filter by majors (contains any)

        Returns:
            Dict: ChromaDB where filter
        """
        filters = {}

        if entity_types:
            if len(entity_types) == 1:
                filters["entity_type"] = entity_types[0]
            else:
                filters["entity_type"] = {"$in": entity_types}

        if schools:
            if len(schools) == 1:
                filters["school"] = schools[0]
            else:
                filters["school"] = {"$in": schools}

        if gpa_bands:
            if len(gpa_bands) == 1:
                filters["gpa_band"] = gpa_bands[0]
            else:
                filters["gpa_band"] = {"$in": gpa_bands}

        if locations:
            if len(locations) == 1:
                filters["location"] = locations[0]
            else:
                filters["location"] = {"$in": locations}

        if years:
            if len(years) == 1:
                filters["year"] = years[0]
            else:
                filters["year"] = {"$in": years}

        # For majors, we need to check if any of the requested majors
        # are contained in the comma-separated majors field
        if majors:
            # This is a simplified approach - in production you might want
            # more sophisticated text matching
            major_conditions = []
            for major in majors:
                major_conditions.append({"majors": {"$contains": major}})

            if len(major_conditions) == 1:
                filters.update(major_conditions[0])
            else:
                filters["$or"] = major_conditions

        return filters if filters else None
