"""Ollama embedding implementation."""

import logging
import requests
from typing import List, Dict, Any
import time

from .embedder import BaseEmbedder
from ..config import config

logger = logging.getLogger(__name__)


class OllamaEmbedder(BaseEmbedder):
    """Embedding service using Ollama."""
    
    def __init__(self, model_name: str = "nomic-embed-text"):
        super().__init__(model_name)
        self.base_url = config.ollama_host.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        self._check_model_availability()
    
    def _check_model_availability(self):
        """Check if the model is available in Ollama."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            models = response.json().get('models', [])
            available_models = [model['name'] for model in models]
            
            if self.model_name not in available_models:
                logger.warning(f"Model {self.model_name} not found in Ollama. Available models: {available_models}")
                logger.info(f"Attempting to pull model {self.model_name}")
                self._pull_model()
            else:
                logger.info(f"Model {self.model_name} is available in Ollama")
        
        except Exception as e:
            logger.error(f"Error checking Ollama model availability: {e}")
            raise
    
    def _pull_model(self):
        """Pull the model if it's not available."""
        try:
            logger.info(f"Pulling model {self.model_name} from Ollama...")
            
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model_name},
                stream=True
            )
            response.raise_for_status()
            
            # Wait for pull to complete
            for line in response.iter_lines():
                if line:
                    data = line.decode('utf-8')
                    if '"status":"success"' in data:
                        logger.info(f"Successfully pulled model {self.model_name}")
                        return
            
        except Exception as e:
            logger.error(f"Error pulling model {self.model_name}: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        
        for i, text in enumerate(texts):
            try:
                embedding = self._generate_embedding(text)
                embeddings.append(embedding)
                
                # Add small delay to avoid overwhelming Ollama
                if i > 0 and i % 10 == 0:
                    time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error generating embedding for text {i}: {e}")
                # Return zero vector as fallback
                if embeddings:
                    zero_embedding = [0.0] * len(embeddings[0])
                else:
                    zero_embedding = [0.0] * 384  # Default dimension
                embeddings.append(zero_embedding)
        
        return embeddings
    
    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self._generate_embedding(text)
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama API."""
        try:
            payload = {
                "model": self.model_name,
                "prompt": text
            }
            
            response = self.session.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            embedding = result.get('embedding')
            
            if not embedding:
                raise ValueError(f"No embedding returned from Ollama for model {self.model_name}")
            
            return embedding
        
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error generating embedding: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        if self._embedding_dim is None:
            # Generate a test embedding to determine dimension
            try:
                test_embedding = self._generate_embedding("test")
                self._embedding_dim = len(test_embedding)
            except Exception as e:
                logger.warning(f"Could not determine embedding dimension: {e}")
                # Default dimensions for common models
                model_dims = {
                    "nomic-embed-text": 768,
                    "mxbai-embed-large": 1024,
                    "all-minilm": 384
                }
                
                for model_key, dim in model_dims.items():
                    if model_key in self.model_name.lower():
                        self._embedding_dim = dim
                        break
                else:
                    self._embedding_dim = 768  # Default fallback
                
                logger.info(f"Using default dimension {self._embedding_dim} for model {self.model_name}")
        
        return self._embedding_dim
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Ollama service is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            # Try generating a test embedding
            test_embedding = self._generate_embedding("health check")
            
            return {
                "status": "healthy",
                "ollama_url": self.base_url,
                "model": self.model_name,
                "embedding_dim": len(test_embedding)
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "ollama_url": self.base_url,
                "model": self.model_name,
                "error": str(e)
            }
