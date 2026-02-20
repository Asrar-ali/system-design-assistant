"""
Hybrid retrieval combining BM25 keyword search with semantic vector search.

Implements BM25 retrieval and hybrid search orchestration using Reciprocal
Rank Fusion (RRF) to merge results from both retrieval methods.
"""

from typing import List, Dict, Optional

import bm25s
import Stemmer

from src.indexing.bm25_index import load_bm25_index
from src.indexing.vector_store import get_chroma_client, get_or_create_collection
from src.retrieval.fusion import reciprocal_rank_fusion


def retrieve_bm25(
    query: str,
    top_k: int = 5
) -> List[Dict]:
    """
    Retrieve chunks using BM25 keyword search.

    Args:
        query: User's natural language query
        top_k: Number of top results to retrieve (default: 5)

    Returns:
        List of result dicts, each containing:
        - chunk_id: Unique chunk identifier
        - text: Chunk text content
        - bm25_score: BM25 relevance score

        Results are sorted by bm25_score in descending order.

    Note:
        Uses same preprocessing as BM25 index building:
        - Lowercase (lower=True)
        - English stemming (Snowball stemmer)
        - Stopword removal (English stopwords)

        This prevents preprocessing mismatch (Pitfall #2).

    Example:
        >>> results = retrieve_bm25("CAP theorem", top_k=3)
        >>> results[0]['bm25_score']
        7.58
    """
    # Load BM25 index (cached after first load)
    retriever, chunk_ids = load_bm25_index()

    # Tokenize query with SAME preprocessing as index
    # CRITICAL: This must match build_bm25_index() preprocessing exactly
    stemmer = Stemmer.Stemmer('english')
    query_tokens = bm25s.tokenize(
        query,
        stopwords="en",
        stemmer=stemmer,
        lower=True
    )

    # Retrieve top_k results
    results, scores = retriever.retrieve(query_tokens, k=top_k)

    # Convert to list[dict] format
    # results is shape (1, k) for single query
    # scores is shape (1, k) for single query

    # Get chunk IDs for top-k results
    result_chunk_ids = []
    result_scores = []
    for i in range(len(results[0])):
        doc_idx = results[0][i]
        score = scores[0][i]
        chunk_id = chunk_ids[doc_idx]

        result_chunk_ids.append(chunk_id)
        result_scores.append(float(score))

    # Fetch text and metadata from ChromaDB
    # (Corpus text not saved with BM25 index)
    client = get_chroma_client()
    collection = get_or_create_collection(client)

    chroma_results = collection.get(
        ids=result_chunk_ids,
        include=['documents', 'metadatas']
    )

    # Build result list
    bm25_results = []
    for i, chunk_id in enumerate(result_chunk_ids):
        bm25_results.append({
            'chunk_id': chunk_id,
            'text': chroma_results['documents'][i],
            'metadata': chroma_results['metadatas'][i],
            'bm25_score': result_scores[i]
        })

    return bm25_results


def retrieve_hybrid(
    query: str,
    top_k: int = 5,
    metadata_filter: Optional[Dict] = None,
    min_similarity: float = 0.3
) -> List[Dict]:
    """
    Retrieve chunks using hybrid search (BM25 + semantic).

    Combines BM25 keyword search with semantic vector search using
    Reciprocal Rank Fusion (RRF) to merge results.

    Args:
        query: User's natural language query
        top_k: Number of final results to return (default: 5)
        metadata_filter: Optional metadata filter for semantic search
                        (see retriever.retrieve_chunks docs)
        min_similarity: Minimum similarity threshold for semantic results
                       (default: 0.3)

    Returns:
        List of result dicts sorted by fusion_score (descending).
        Each dict contains:
        - chunk_id: Unique chunk identifier
        - text: Chunk text content
        - metadata: Source metadata
        - fusion_score: Combined RRF score
        - similarity_score: Semantic similarity (if in vector results)
        - bm25_score: BM25 score (if in BM25 results)

    Note:
        Over-retrieves from each path (2×top_k) to provide better
        fusion coverage, then returns top_k fused results.

    Example:
        >>> results = retrieve_hybrid("CAP theorem", top_k=5)
        >>> results[0]['fusion_score']
        0.0164
        >>> 'bm25_score' in results[0]
        True
        >>> 'similarity_score' in results[0]
        True
    """
    # Over-retrieve for better fusion coverage
    # Research shows 2×top_k provides good balance (Pitfall #4)
    retrieval_k = top_k * 2

    # Path 1: BM25 keyword search
    bm25_results = retrieve_bm25(query, top_k=retrieval_k)

    # Path 2: Semantic vector search
    # Import here to avoid circular dependency
    from src.retrieval.retriever import retrieve_chunks

    # CRITICAL: Use hybrid=False to avoid infinite recursion
    vector_results = retrieve_chunks(
        query=query,
        top_k=retrieval_k,
        metadata_filter=metadata_filter,
        min_similarity=min_similarity,
        hybrid=False  # Disable hybrid to get semantic-only results
    )

    # Path 3: Fuse results using RRF
    fused_results = reciprocal_rank_fusion(
        bm25_results=bm25_results,
        vector_results=vector_results,
        k=60,  # Research-backed default
        bm25_weight=0.5,  # 50/50 balance
        vector_weight=0.5
    )

    # Enrich BM25-only results with full metadata from ChromaDB
    # (Results that only appeared in BM25 have minimal data)
    client = get_chroma_client()
    collection = get_or_create_collection(client)

    for result in fused_results:
        # If result lacks metadata, it was BM25-only - fetch from ChromaDB
        if 'metadata' not in result:
            chunk_id = result['chunk_id']
            chroma_result = collection.get(
                ids=[chunk_id],
                include=['documents', 'metadatas']
            )

            if chroma_result['ids']:
                result['text'] = chroma_result['documents'][0]
                result['metadata'] = chroma_result['metadatas'][0]

    # Return top_k fused results
    return fused_results[:top_k]
