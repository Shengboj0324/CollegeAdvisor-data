"""Configuration management for the College Advisor data pipeline."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the data pipeline."""

    def __init__(self):
        # ChromaDB Configuration
        self.chroma_host = os.getenv("CHROMA_HOST", "localhost")
        self.chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        self.chroma_collection_name = os.getenv("CHROMA_COLLECTION_NAME", "college_advisor")
        self.chroma_cloud_host = os.getenv("CHROMA_CLOUD_HOST")
        self.chroma_cloud_api_key = os.getenv("CHROMA_CLOUD_API_KEY")

        # Embedding Configuration - LOCKED TO SENTENCE TRANSFORMERS
        # This is the canonical embedding strategy for CollegeAdvisor-data
        # API should NOT embed - data repo owns all embeddings
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.embedding_provider = "sentence_transformers"  # LOCKED - do not change
        self.embedding_dimension = 384  # all-MiniLM-L6-v2 dimension

        # Ollama Configuration
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.ollama_embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

        # Directory Configuration
        self.data_dir = Path(os.getenv("DATA_DIR", "./data"))
        self.processed_dir = Path(os.getenv("PROCESSED_DIR", "./processed"))
        self.cache_dir = Path(os.getenv("CACHE_DIR", "./cache"))

        # Processing Configuration
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "800"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "100"))
        self.batch_size = int(os.getenv("BATCH_SIZE", "100"))

        # Data Collection Configuration
        self.college_scorecard_api_key = os.getenv("COLLEGE_SCORECARD_API_KEY", "DEMO_KEY")
        self.ipeds_api_key = os.getenv("IPEDS_API_KEY")

        # Rate Limiting Configuration
        self.default_requests_per_second = float(os.getenv("DEFAULT_REQUESTS_PER_SECOND", "1.0"))
        self.default_requests_per_minute = int(os.getenv("DEFAULT_REQUESTS_PER_MINUTE", "60"))
        self.default_requests_per_hour = int(os.getenv("DEFAULT_REQUESTS_PER_HOUR", "1000"))

        # Web Scraping Configuration
        self.user_agent = os.getenv("USER_AGENT", "CollegeAdvisor-Bot/1.0")
        self.scraping_delay = float(os.getenv("SCRAPING_DELAY", "1.0"))
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))

        # Social Media API Keys
        self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")

        # Data Quality Configuration
        self.min_content_length = int(os.getenv("MIN_CONTENT_LENGTH", "50"))
        self.max_content_length = int(os.getenv("MAX_CONTENT_LENGTH", "50000"))
        self.quality_threshold = float(os.getenv("QUALITY_THRESHOLD", "0.7"))

        # Pipeline Configuration
        self.enable_real_time_processing = os.getenv("ENABLE_REAL_TIME_PROCESSING", "false").lower() == "true"
        self.enable_data_validation = os.getenv("ENABLE_DATA_VALIDATION", "true").lower() == "true"
        self.enable_synthetic_data = os.getenv("ENABLE_SYNTHETIC_DATA", "false").lower() == "true"

        # Cloudflare R2 Configuration
        self.r2_account_id = os.getenv("R2_ACCOUNT_ID")
        self.r2_access_key_id = os.getenv("R2_ACCESS_KEY_ID")
        self.r2_secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
        self.r2_bucket_name = os.getenv("R2_BUCKET_NAME", "collegeadvisor-data")

        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        log_file_path = os.getenv("LOG_FILE", "./logs/pipeline.log")
        self.log_file = Path(log_file_path) if log_file_path else None

        # Create necessary directories
        self._create_directories()

    def _create_directories(self):
        """Create necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
