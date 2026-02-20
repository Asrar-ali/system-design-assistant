"""
Batch embedding generation using sentence-transformers.

Provides efficient embedding generation for text chunks using
the all-MiniLM-L6-v2 model (384 dimensions).
"""

from sentence_transformers import SentenceTransformer

from src.models.document import Chunk

# Try to import streamlit for production caching
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


# Module-level cache for embedding model (fallback for non-Streamlit usage)
_embedding_model = None


def load_embedding_model() -> SentenceTransformer:
    """
    Load and cache the sentence-transformers embedding model.

    Uses 'all-MiniLM-L6-v2' model which provides:
    - 384-dimensional embeddings
    - Fast inference (~700 sentences/sec on CPU)
    - Good performance on semantic similarity tasks

    Returns:
        Cached SentenceTransformer model instance

    Note:
        In Streamlit apps, uses @st.cache_resource for persistence across reruns.
        Otherwise uses module-level variable caching.
    """
    if STREAMLIT_AVAILABLE:
        # Use Streamlit's cache_resource for production deployment
        @st.cache_resource
        def _load_model():
            return SentenceTransformer('all-MiniLM-L6-v2')
        return _load_model()
    else:
        # Fallback to module-level caching for non-Streamlit usage
        global _embedding_model
        if _embedding_model is None:
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return _embedding_model


def generate_embeddings(chunks: list[Chunk], batch_size: int = 32) -> list[Chunk]:
    """
    Generate embeddings for chunks in batches.

    Processes chunks efficiently using batch encoding and updates
    each chunk's embedding field in-place.

    Args:
        chunks: List of Chunk objects to embed
        batch_size: Number of chunks to process per batch (default: 32)

    Returns:
        Same list of chunks with embedding field populated

    Note:
        Embeddings are converted from numpy arrays to Python lists
        for JSON serialization compatibility.
    """
    if not chunks:
        return chunks

    # Load model (uses cached instance)
    model = load_embedding_model()

    # Extract text from all chunks
    texts = [chunk.text for chunk in chunks]

    # Generate embeddings in batches with progress bar
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    # Populate embedding field for each chunk
    for chunk, embedding in zip(chunks, embeddings):
        # Convert numpy array to list for JSON serialization
        chunk.embedding = embedding.tolist()

    return chunks
