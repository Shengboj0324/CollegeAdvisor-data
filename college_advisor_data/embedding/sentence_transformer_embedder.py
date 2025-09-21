"""Sentence Transformers embedding implementation."""

import logging
from typing import List
import torch

from sentence_transformers import SentenceTransformer

from .embedder import BaseEmbedder

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder(BaseEmbedder):
    """Embedding service using Sentence Transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__(model_name)
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading Sentence Transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Set device
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = self.model.to(device)
            logger.info(f"Model loaded on device: {device}")
            
        except Exception as e:
            logger.error(f"Error loading model {self.model_name}: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self.model:
            self._load_model()
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=len(texts) > 10,
                convert_to_numpy=True
            )
            
            # Convert to list of lists
            return [embedding.tolist() for embedding in embeddings]
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embeddings = self.embed_texts([text])
        return embeddings[0]
    
    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        if self._embedding_dim is None:
            if not self.model:
                self._load_model()
            self._embedding_dim = self.model.get_sentence_embedding_dimension()
        return self._embedding_dim
