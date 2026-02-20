"""Document indexing and embedding module.

Handles:
- Embedding generation with sentence-transformers
- ChromaDB vector store management
- Index persistence and loading
"""
from .vector_store import get_chroma_client, get_or_create_collection

__all__ = ["get_chroma_client", "get_or_create_collection"]
