"""
Reciprocal Rank Fusion (RRF) for hybrid search result merging.

Combines BM25 keyword search results with semantic vector search results
using rank-based fusion. Avoids score normalization issues by using ranks only.

Research-backed default: k=60 (from RRF paper by Cormack et al.)
"""

from typing import List, Dict, Optional


def reciprocal_rank_fusion(
    bm25_results: List[Dict],
    vector_results: List[Dict],
    k: int = 60,
    bm25_weight: float = 0.5,
    vector_weight: float = 0.5
) -> List[Dict]:
    """
    Merge BM25 and vector search results using Reciprocal Rank Fusion.

    RRF combines rankings from different retrieval methods without normalizing
    scores. Each result's contribution is weighted by its rank position using
    the formula: weight / (k + rank)

    This approach:
    - Avoids score scale mismatch between BM25 and cosine similarity
    - Doesn't penalize items appearing in only one result list
    - Uses research-validated default k=60

    Args:
        bm25_results: List of dicts with 'chunk_id' and 'bm25_score' fields
        vector_results: List of dicts with 'chunk_id' and 'similarity_score' fields
        k: RRF constant (default: 60, per research)
        bm25_weight: Weight for BM25 ranking contribution (default: 0.5)
        vector_weight: Weight for vector ranking contribution (default: 0.5)

    Returns:
        List of result dicts sorted by fusion_score in descending order.
        Each dict contains all fields from vector_results plus:
        - fusion_score: Combined RRF score
        - bm25_score: BM25 score if chunk appeared in BM25 results

    Example:
        >>> bm25_results = [
        ...     {'chunk_id': 'A', 'bm25_score': 15.3},
        ...     {'chunk_id': 'B', 'bm25_score': 12.1}
        ... ]
        >>> vector_results = [
        ...     {'chunk_id': 'B', 'similarity_score': 0.85, 'text': 'chunk B'},
        ...     {'chunk_id': 'C', 'similarity_score': 0.72, 'text': 'chunk C'}
        ... ]
        >>> fused = reciprocal_rank_fusion(bm25_results, vector_results)
        >>> fused[0]['chunk_id']
        'B'  # B appears in both lists, highest fusion score
    """
    # Build rank mappings (1-indexed)
    # If chunk doesn't appear in a list, rank is None
    bm25_ranks = {
        result['chunk_id']: rank + 1
        for rank, result in enumerate(bm25_results)
    }

    vector_ranks = {
        result['chunk_id']: rank + 1
        for rank, result in enumerate(vector_results)
    }

    # Build lookup for full chunk data from vector results
    # Vector results have complete metadata from ChromaDB
    vector_data = {
        result['chunk_id']: result
        for result in vector_results
    }

    # Build lookup for BM25 scores
    bm25_scores = {
        result['chunk_id']: result['bm25_score']
        for result in bm25_results
    }

    # Collect all unique chunk IDs
    all_chunk_ids = set(bm25_ranks.keys()) | set(vector_ranks.keys())

    # Calculate RRF scores
    fused_results = []
    for chunk_id in all_chunk_ids:
        # Get ranks (None if not present in that result list)
        bm25_rank = bm25_ranks.get(chunk_id)
        vector_rank = vector_ranks.get(chunk_id)

        # Calculate RRF score
        # If rank is None, contribution is 0
        bm25_contribution = bm25_weight / (k + bm25_rank) if bm25_rank else 0
        vector_contribution = vector_weight / (k + vector_rank) if vector_rank else 0
        fusion_score = bm25_contribution + vector_contribution

        # Build result dict
        # Start with vector data if available, otherwise create minimal dict
        if chunk_id in vector_data:
            result = vector_data[chunk_id].copy()
        else:
            # Chunk only in BM25 results, need to fetch from ChromaDB
            # For now, create minimal dict (will be enriched by hybrid_retriever)
            result = {'chunk_id': chunk_id}

        # Add fusion metadata
        result['fusion_score'] = round(fusion_score, 4)

        # Add BM25 score if present
        if chunk_id in bm25_scores:
            result['bm25_score'] = bm25_scores[chunk_id]

        fused_results.append(result)

    # Sort by fusion score (descending)
    fused_results.sort(key=lambda x: x['fusion_score'], reverse=True)

    return fused_results
