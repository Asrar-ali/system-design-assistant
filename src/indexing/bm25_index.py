"""
BM25 keyword search index for hybrid retrieval.

Provides building and loading functions for BM25 index using the bm25s library.
Complements semantic search with keyword-based retrieval for technical terms
and acronyms that embeddings may miss.
"""

import json
from pathlib import Path
from typing import Tuple, Any

import bm25s
import Stemmer

from src.indexing.vector_store import get_chroma_client, get_or_create_collection

# Try to import streamlit for production caching
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


# Module-level cache for BM25 index and chunk IDs (fallback for non-Streamlit usage)
_bm25_retriever = None
_bm25_chunk_ids = None


def build_bm25_index(
    index_path: Path = None,
    chunk_ids_path: Path = None
) -> Tuple[Any, list[str]]:
    """
    Build BM25 index from all chunks in ChromaDB and persist to disk.

    Loads all chunks from the ChromaDB collection, tokenizes the corpus
    with preprocessing (lowercasing, stemming, stopword removal), builds
    BM25 index with standard parameters, and saves to disk.

    Args:
        index_path: Directory to save BM25 index files
                   (default: data/indexes/bm25_index/)
        chunk_ids_path: Path to save chunk ID mapping JSON
                       (default: data/indexes/bm25_chunk_ids.json)

    Returns:
        Tuple of (retriever, chunk_ids):
        - retriever: BM25 retriever instance
        - chunk_ids: List of ChromaDB chunk IDs in corpus order

    Note:
        Uses same preprocessing as semantic embeddings:
        - Lowercase (lower=True)
        - English stemming (Snowball stemmer)
        - Stopword removal (English stopwords)

        This prevents preprocessing mismatch between indexing and querying.

    Example:
        >>> retriever, chunk_ids = build_bm25_index()
        >>> print(f"Built index with {len(chunk_ids)} chunks")
    """
    # Default paths
    if index_path is None:
        index_path = Path(__file__).parent.parent.parent / "data" / "indexes" / "bm25_index"
    if chunk_ids_path is None:
        chunk_ids_path = Path(__file__).parent.parent.parent / "data" / "indexes" / "bm25_chunk_ids.json"

    # Create directories
    index_path.parent.mkdir(parents=True, exist_ok=True)
    chunk_ids_path.parent.mkdir(parents=True, exist_ok=True)

    # Load all chunks from ChromaDB
    print("Loading chunks from ChromaDB...")
    client = get_chroma_client()
    collection = get_or_create_collection(client)

    # Get all documents and chunk IDs
    results = collection.get(include=["documents"])
    chunk_ids = results['ids']
    documents = results['documents']

    print(f"Loaded {len(chunk_ids)} chunks from ChromaDB")

    # Tokenize corpus with preprocessing
    print("Tokenizing corpus...")
    stemmer = Stemmer.Stemmer('english')
    corpus_tokens = bm25s.tokenize(
        documents,
        stopwords="en",
        stemmer=stemmer,
        lower=True  # Case-insensitive matching
    )

    # Build BM25 index with standard parameters
    print("Building BM25 index...")
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)

    # Persist index to disk
    print(f"Saving index to {index_path}...")
    retriever.save(str(index_path))

    # Save chunk ID mapping
    print(f"Saving chunk IDs to {chunk_ids_path}...")
    with open(chunk_ids_path, 'w') as f:
        json.dump(chunk_ids, f, indent=2)

    print("✓ BM25 index build complete")

    return retriever, chunk_ids


def load_bm25_index(
    index_path: Path = None,
    chunk_ids_path: Path = None
) -> Tuple[Any, list[str]]:
    """
    Load BM25 index from disk with caching.

    Returns cached index if already loaded, otherwise loads from disk.
    Memory-maps index files for efficient loading.

    Args:
        index_path: Directory containing BM25 index files
                   (default: data/indexes/bm25_index/)
        chunk_ids_path: Path to chunk ID mapping JSON
                       (default: data/indexes/bm25_chunk_ids.json)

    Returns:
        Tuple of (retriever, chunk_ids):
        - retriever: BM25 retriever instance (cached)
        - chunk_ids: List of ChromaDB chunk IDs in corpus order (cached)

    Note:
        In Streamlit apps, uses @st.cache_resource for persistence across reruns.
        Otherwise uses module-level caching.
        Index is memory-mapped for efficient loading without full deserialization.

    Example:
        >>> retriever, chunk_ids = load_bm25_index()
        >>> # Subsequent calls return cached instance
        >>> retriever2, chunk_ids2 = load_bm25_index()
        >>> assert retriever is retriever2
    """
    if STREAMLIT_AVAILABLE:
        # Use Streamlit's cache_resource for production deployment
        @st.cache_resource
        def _load_index():
            return _load_bm25_from_disk(index_path, chunk_ids_path)
        return _load_index()
    else:
        # Fallback to module-level caching for non-Streamlit usage
        return _load_bm25_from_disk(index_path, chunk_ids_path)


def _load_bm25_from_disk(
    index_path: Path = None,
    chunk_ids_path: Path = None
) -> Tuple[Any, list[str]]:
    """Internal function to load BM25 index from disk with module-level caching."""
    global _bm25_retriever, _bm25_chunk_ids

    # Return cached if already loaded
    if _bm25_retriever is not None and _bm25_chunk_ids is not None:
        return _bm25_retriever, _bm25_chunk_ids

    # Default paths
    if index_path is None:
        index_path = Path(__file__).parent.parent.parent / "data" / "indexes" / "bm25_index"
    if chunk_ids_path is None:
        chunk_ids_path = Path(__file__).parent.parent.parent / "data" / "indexes" / "bm25_chunk_ids.json"

    # Load BM25 index
    print(f"Loading BM25 index from {index_path}...")
    _bm25_retriever = bm25s.BM25.load(str(index_path), mmap=True)

    # Load chunk IDs
    print(f"Loading chunk IDs from {chunk_ids_path}...")
    with open(chunk_ids_path, 'r') as f:
        _bm25_chunk_ids = json.load(f)

    print(f"✓ BM25 index loaded with {len(_bm25_chunk_ids)} chunks")

    return _bm25_retriever, _bm25_chunk_ids


if __name__ == "__main__":
    # Test index building and loading
    print("Testing BM25 index building...")
    retriever, chunk_ids = build_bm25_index()
    print(f"Built index with {len(chunk_ids)} chunks")

    print("\nTesting BM25 index loading...")
    retriever2, chunk_ids2 = load_bm25_index()
    print(f"Loaded index with {len(chunk_ids2)} chunks")

    # Simple retrieval test
    print("\nTesting BM25 retrieval with 'CAP theorem' query...")
    stemmer = Stemmer.Stemmer('english')
    query_tokens = bm25s.tokenize("CAP theorem", stemmer=stemmer, lower=True)
    results, scores = retriever2.retrieve(query_tokens, k=3)

    print(f"Retrieved {len(results[0])} results")
    print(f"Top score: {scores[0][0]:.2f}")
    print("✓ BM25 index test complete")
