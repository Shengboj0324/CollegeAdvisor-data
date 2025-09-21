"""Base embedding service interface and factory."""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
import hashlib
import pickle

from ..models import EmbeddingResult
from ..config import config

logger = logging.getLogger(__name__)


class BaseEmbedder(ABC):
    """Abstract base class for embedding services."""
    
    def __init__(self, model_name: str, cache_dir: Optional[Path] = None):
        self.model_name = model_name
        self.cache_dir = cache_dir or config.cache_dir / "embeddings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._embedding_dim = None
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        pass
    
    @abstractmethod
    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        pass
    
    def embed_with_cache(self, text: str, chunk_id: str) -> EmbeddingResult:
        """Generate embedding with caching support."""
        # Check cache first
        cached_result = self._load_from_cache(chunk_id)
        if cached_result:
            logger.debug(f"Using cached embedding for chunk {chunk_id}")
            return cached_result
        
        # Generate new embedding
        embedding = self.embed_single(text)
        
        result = EmbeddingResult(
            chunk_id=chunk_id,
            embedding=embedding,
            model_name=self.model_name,
            embedding_dim=len(embedding)
        )
        
        # Cache the result
        self._save_to_cache(chunk_id, result)
        
        return result
    
    def batch_embed_with_cache(self, texts: List[str], chunk_ids: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts with caching."""
        if len(texts) != len(chunk_ids):
            raise ValueError("Number of texts must match number of chunk IDs")
        
        results = []
        uncached_texts = []
        uncached_ids = []
        uncached_indices = []
        
        # Check cache for each text
        for i, (text, chunk_id) in enumerate(zip(texts, chunk_ids)):
            cached_result = self._load_from_cache(chunk_id)
            if cached_result:
                results.append(cached_result)
            else:
                results.append(None)  # Placeholder
                uncached_texts.append(text)
                uncached_ids.append(chunk_id)
                uncached_indices.append(i)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            logger.info(f"Generating embeddings for {len(uncached_texts)} uncached texts")
            embeddings = self.embed_texts(uncached_texts)
            
            # Create results and cache them
            for i, (embedding, chunk_id) in enumerate(zip(embeddings, uncached_ids)):
                result = EmbeddingResult(
                    chunk_id=chunk_id,
                    embedding=embedding,
                    model_name=self.model_name,
                    embedding_dim=len(embedding)
                )
                
                # Update results list
                original_index = uncached_indices[i]
                results[original_index] = result
                
                # Cache the result
                self._save_to_cache(chunk_id, result)
        
        return results
    
    def _get_cache_path(self, chunk_id: str) -> Path:
        """Get cache file path for a chunk ID."""
        # Create a hash of the chunk ID and model name for filename
        cache_key = f"{chunk_id}_{self.model_name}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{cache_hash}.pkl"
    
    def _load_from_cache(self, chunk_id: str) -> Optional[EmbeddingResult]:
        """Load embedding result from cache."""
        cache_path = self._get_cache_path(chunk_id)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    result = pickle.load(f)
                
                # Verify the result is for the correct model
                if result.model_name == self.model_name:
                    return result
                else:
                    # Model changed, remove old cache
                    cache_path.unlink()
            
            except Exception as e:
                logger.warning(f"Error loading cached embedding for {chunk_id}: {e}")
                # Remove corrupted cache file
                try:
                    cache_path.unlink()
                except:
                    pass
        
        return None
    
    def _save_to_cache(self, chunk_id: str, result: EmbeddingResult) -> None:
        """Save embedding result to cache."""
        cache_path = self._get_cache_path(chunk_id)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            logger.warning(f"Error caching embedding for {chunk_id}: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cached embeddings for this model."""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            logger.info(f"Cleared embedding cache for model {self.model_name}")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")


class EmbeddingService:
    """Factory and service manager for embeddings."""
    
    def __init__(self, provider: str = None, model_name: str = None):
        self.provider = provider or config.embedding_provider
        self.model_name = model_name or config.embedding_model
        self._embedder = None
    
    @property
    def embedder(self) -> BaseEmbedder:
        """Get the configured embedder instance."""
        if self._embedder is None:
            self._embedder = self._create_embedder()
        return self._embedder
    
    def _create_embedder(self) -> BaseEmbedder:
        """Create embedder based on configuration."""
        if self.provider == "sentence_transformers":
            from .sentence_transformer_embedder import SentenceTransformerEmbedder
            return SentenceTransformerEmbedder(self.model_name)
        
        elif self.provider == "ollama":
            from .ollama_embedder import OllamaEmbedder
            return OllamaEmbedder(self.model_name)
        
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")
    
    def embed_text(self, text: str, chunk_id: str) -> EmbeddingResult:
        """Generate embedding for a single text."""
        return self.embedder.embed_with_cache(text, chunk_id)
    
    def embed_batch(self, texts: List[str], chunk_ids: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts."""
        return self.embedder.batch_embed_with_cache(texts, chunk_ids)
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        return self.embedder.embedding_dimension
    
    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self.embedder.clear_cache()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the embedding service is working."""
        try:
            test_text = "This is a test sentence for health check."
            test_id = "health_check_test"
            
            result = self.embed_text(test_text, test_id)
            
            return {
                "status": "healthy",
                "provider": self.provider,
                "model": self.model_name,
                "embedding_dim": result.embedding_dim,
                "test_embedding_length": len(result.embedding)
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider,
                "model": self.model_name,
                "error": str(e)
            }
