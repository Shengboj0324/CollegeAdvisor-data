"""
Embedding factory for CollegeAdvisor data pipeline.

This factory ensures we always use the canonical embedding strategy
and prevents conflicts between different embedding providers.
"""

import logging
from typing import Optional

from .sentence_transformer_embedder import SentenceTransformerEmbedder
from ..schemas import EMBEDDING_MODEL, EMBEDDING_PROVIDER

logger = logging.getLogger(__name__)


class EmbeddingFactory:
    """
    Factory for creating the canonical embedder.
    
    This factory enforces the locked embedding strategy for MVP:
    - Provider: sentence_transformers (LOCKED)
    - Model: all-MiniLM-L6-v2 (LOCKED)
    - Dimension: 384 (LOCKED)
    """
    
    _instance: Optional[SentenceTransformerEmbedder] = None
    
    @classmethod
    def get_embedder(cls, model_name: Optional[str] = None) -> SentenceTransformerEmbedder:
        """
        Get the canonical embedder instance.
        
        Args:
            model_name: Model name (ignored - locked to canonical model)
            
        Returns:
            SentenceTransformerEmbedder: The canonical embedder
        """
        if model_name and model_name != EMBEDDING_MODEL:
            logger.warning(
                f"Requested model '{model_name}' ignored. "
                f"Using locked canonical model: {EMBEDDING_MODEL}"
            )
        
        if cls._instance is None:
            logger.info(f"Creating canonical embedder: {EMBEDDING_MODEL}")
            cls._instance = SentenceTransformerEmbedder(model_name=EMBEDDING_MODEL)
            
            # Validate embedding dimension
            actual_dim = cls._instance.embedding_dimension
            expected_dim = 384  # all-MiniLM-L6-v2 dimension
            
            if actual_dim != expected_dim:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}"
                )
            
            logger.info(f"Canonical embedder ready - dimension: {actual_dim}")
        
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset the factory (for testing)."""
        cls._instance = None
    
    @classmethod
    def validate_embedding_strategy(cls) -> bool:
        """
        Validate that the embedding strategy is correctly configured.
        
        Returns:
            bool: True if strategy is valid
        """
        try:
            embedder = cls.get_embedder()
            
            # Test embedding generation
            test_text = "This is a test sentence for embedding validation."
            embedding = embedder.embed_single(test_text)
            
            # Validate embedding properties
            if not isinstance(embedding, list):
                logger.error("Embedding is not a list")
                return False
            
            if len(embedding) != 384:
                logger.error(f"Embedding dimension mismatch: {len(embedding)} != 384")
                return False
            
            if not all(isinstance(x, (int, float)) for x in embedding):
                logger.error("Embedding contains non-numeric values")
                return False
            
            logger.info("Embedding strategy validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Embedding strategy validation failed: {e}")
            return False


def get_canonical_embedder() -> SentenceTransformerEmbedder:
    """
    Convenience function to get the canonical embedder.
    
    This is the recommended way to get an embedder in the data pipeline.
    
    Returns:
        SentenceTransformerEmbedder: The canonical embedder
    """
    return EmbeddingFactory.get_embedder()


def validate_embedding_config() -> bool:
    """
    Validate the embedding configuration.
    
    Returns:
        bool: True if configuration is valid
    """
    return EmbeddingFactory.validate_embedding_strategy()


# Export the canonical embedder for easy imports
__all__ = [
    "EmbeddingFactory",
    "get_canonical_embedder", 
    "validate_embedding_config"
]
