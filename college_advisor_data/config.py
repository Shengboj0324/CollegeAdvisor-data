"""Configuration management for the College Advisor data pipeline."""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Configuration settings for the data pipeline."""
    
    # ChromaDB Configuration
    chroma_host: str = Field(default="localhost", env="CHROMA_HOST")
    chroma_port: int = Field(default=8000, env="CHROMA_PORT")
    chroma_collection_name: str = Field(default="college_advisor", env="CHROMA_COLLECTION_NAME")
    chroma_cloud_host: Optional[str] = Field(default=None, env="CHROMA_CLOUD_HOST")
    chroma_cloud_api_key: Optional[str] = Field(default=None, env="CHROMA_CLOUD_API_KEY")
    
    # Embedding Configuration
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    embedding_provider: str = Field(default="sentence_transformers", env="EMBEDDING_PROVIDER")
    
    # Ollama Configuration
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    ollama_embedding_model: str = Field(default="nomic-embed-text", env="OLLAMA_EMBEDDING_MODEL")
    
    # Directory Configuration
    data_dir: Path = Field(default=Path("./data"), env="DATA_DIR")
    processed_dir: Path = Field(default=Path("./processed"), env="PROCESSED_DIR")
    cache_dir: Path = Field(default=Path("./cache"), env="CACHE_DIR")
    
    # Processing Configuration
    chunk_size: int = Field(default=800, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, env="CHUNK_OVERLAP")
    batch_size: int = Field(default=100, env="BATCH_SIZE")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[Path] = Field(default=Path("./logs/pipeline.log"), env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __post_init__(self):
        """Create necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
