"""Application configuration loaded from environment variables.

This module provides centralized configuration management with:
- Fail-fast validation for required settings (GROQ_API_KEY)
- Type conversion for int/Path settings
- Sensible defaults for optional settings
- Clear error messages guiding users to fix configuration

Usage:
    from src.config import settings

    # Validate configuration on startup
    settings.validate()

    # Access settings
    api_key = settings.groq_api_key
    chunk_size = settings.chunk_size
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    @property
    def groq_api_key(self) -> str:
        """Required: Groq API key for LLM inference.

        Raises:
            ValueError: If GROQ_API_KEY is not set in environment
        """
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError(
                "GROQ_API_KEY is required. "
                "Copy .env.example to .env and add your API key from groq.com"
            )
        return key

    @property
    def chroma_path(self) -> Path:
        """Path to ChromaDB persistent storage.

        Default: ./chroma_db
        """
        return Path(os.getenv("CHROMA_PATH", "./chroma_db"))

    @property
    def chunk_size(self) -> int:
        """Text chunk size in tokens.

        Default: 512 tokens (recommended range: 400-512)
        """
        return int(os.getenv("CHUNK_SIZE", "512"))

    @property
    def chunk_overlap(self) -> int:
        """Chunk overlap in tokens.

        Default: 100 tokens (~15% of chunk_size)
        """
        return int(os.getenv("CHUNK_OVERLAP", "100"))

    @property
    def top_k(self) -> int:
        """Number of chunks to retrieve for each query.

        Default: 5 chunks
        """
        return int(os.getenv("TOP_K", "5"))

    @property
    def embedding_model(self) -> str:
        """Sentence transformer model for embeddings.

        Default: all-MiniLM-L6-v2 (384 dim, fast, good quality)
        """
        return os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    @property
    def ollama_host(self) -> str:
        """Ollama API host (fallback LLM).

        Default: http://localhost:11434
        """
        return os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def validate(self) -> None:
        """Validate all required settings.

        Raises:
            ValueError: If required settings are missing
        """
        # Trigger validation by accessing required properties
        _ = self.groq_api_key

        # Print configuration summary
        print("✓ Configuration loaded")
        print(f"  Chroma path: {self.chroma_path}")
        print(f"  Chunk size: {self.chunk_size}")
        print(f"  Top-K: {self.top_k}")


# Singleton instance
settings = Settings()
