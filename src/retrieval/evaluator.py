"""
Retrieval evaluation metrics for measuring RAG pipeline quality.

Implements Precision@K and Recall@K metrics to quantify retrieval performance
on labeled test sets. These metrics enable data-driven optimization and prevent
regression when making pipeline changes.

Key Metrics:
- Precision@K: Fraction of retrieved items that are relevant (quality)
- Recall@K: Fraction of relevant items that were retrieved (coverage)

Example:
    >>> from src.retrieval.evaluator import calculate_precision_at_k, calculate_recall_at_k
    >>> retrieved = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
    >>> relevant = ['doc1', 'doc3', 'doc6']
    >>> precision = calculate_precision_at_k(retrieved, relevant, k=5)
    >>> recall = calculate_recall_at_k(retrieved, relevant, k=5)
    >>> print(f"Precision@5: {precision:.2f}, Recall@5: {recall:.2f}")
    Precision@5: 0.40, Recall@5: 0.67
"""

from typing import List, Dict
from src.retrieval.retriever import retrieve_chunks


def calculate_precision_at_k(
    retrieved_ids: List[str],
    relevant_ids: List[str],
    k: int
) -> float:
    """
    Calculate Precision@K: fraction of top-K retrieved items that are relevant.

    Precision@K measures retrieval quality by answering:
    "How many of the retrieved chunks are actually relevant?"

    Formula: Precision@K = |relevant ∩ top-K| / K

    Args:
        retrieved_ids: List of chunk IDs in ranked order (best first)
        relevant_ids: List of ground-truth relevant chunk IDs
        k: Number of top results to evaluate

    Returns:
        Precision score in range [0.0, 1.0], where:
        - 1.0 = all top-K results are relevant (perfect quality)
        - 0.0 = no top-K results are relevant (poor quality)

    Example:
        >>> retrieved = ['A', 'B', 'C', 'D', 'E']
        >>> relevant = ['A', 'C', 'F']
        >>> calculate_precision_at_k(retrieved, relevant, k=5)
        0.4  # 2 relevant in top-5 (A, C) / 5 = 0.4
    """
    if k <= 0:
        return 0.0

    # Take first K items from retrieved results
    top_k = retrieved_ids[:k]

    # Find intersection with ground-truth relevant items
    relevant_in_top_k = set(top_k) & set(relevant_ids)

    # Calculate precision: relevant items found / K
    precision = len(relevant_in_top_k) / k

    return precision


def calculate_recall_at_k(
    retrieved_ids: List[str],
    relevant_ids: List[str],
    k: int
) -> float:
    """
    Calculate Recall@K: fraction of relevant items that appear in top-K.

    Recall@K measures retrieval coverage by answering:
    "How many of the relevant chunks did we successfully retrieve?"

    Formula: Recall@K = |relevant ∩ top-K| / |relevant|

    Args:
        retrieved_ids: List of chunk IDs in ranked order (best first)
        relevant_ids: List of ground-truth relevant chunk IDs
        k: Number of top results to evaluate

    Returns:
        Recall score in range [0.0, 1.0], where:
        - 1.0 = all relevant items appear in top-K (perfect coverage)
        - 0.0 = no relevant items in top-K (poor coverage)

    Example:
        >>> retrieved = ['A', 'B', 'C', 'D', 'E']
        >>> relevant = ['A', 'C', 'F']
        >>> calculate_recall_at_k(retrieved, relevant, k=5)
        0.6667  # 2 found (A, C) / 3 total relevant = 0.67
    """
    # Handle edge case: no relevant items (avoid division by zero)
    if not relevant_ids:
        return 0.0

    if k <= 0:
        return 0.0

    # Take first K items from retrieved results
    top_k = retrieved_ids[:k]

    # Find intersection with ground-truth relevant items
    relevant_in_top_k = set(top_k) & set(relevant_ids)

    # Calculate recall: relevant items found / total relevant
    recall = len(relevant_in_top_k) / len(relevant_ids)

    return recall


def evaluate_retrieval(
    test_set: List[Dict],
    top_k: int = 5,
    min_similarity: float = 0.5,
    hybrid: bool = True
) -> Dict:
    """
    Evaluate retrieval performance on labeled test set.

    Runs retrieval on each test question and calculates aggregate Precision@K
    and Recall@K metrics. Returns both aggregate statistics and per-query
    breakdown for debugging.

    Args:
        test_set: List of test questions with structure:
            [
                {
                    "question": "How do you design a URL shortener?",
                    "relevant_chunk_ids": ["chunk1", "chunk2", ...],
                    "topic": "distributed_systems",
                    "difficulty": "medium",
                    "query_type": "design"
                },
                ...
            ]
        top_k: Number of results to retrieve per query (default: 5)
        min_similarity: Minimum similarity threshold for retrieval (default: 0.5)
        hybrid: Enable hybrid search (BM25 + semantic) via RRF fusion (default: True)
                When False, uses semantic search only

    Returns:
        Evaluation results dict with structure:
        {
            "retrieval_mode": str,    # "hybrid" or "semantic"
            "precision_at_k": float,  # Mean precision across all queries
            "recall_at_k": float,     # Mean recall across all queries
            "num_queries": int,       # Number of queries evaluated
            "top_k": int,             # K value used
            "min_similarity": float,  # Similarity threshold used
            "per_query_results": [    # Per-query breakdown
                {
                    "question": str,
                    "topic": str,
                    "difficulty": str,
                    "precision": float,
                    "recall": float,
                    "num_retrieved": int,
                    "num_relevant": int,
                    "relevant_in_top_k": int
                },
                ...
            ]
        }

    Example:
        >>> test_set = [
        ...     {
        ...         "question": "What is consistent hashing?",
        ...         "relevant_chunk_ids": ["chunk1", "chunk2"],
        ...         "topic": "distributed_systems",
        ...         "difficulty": "medium",
        ...         "query_type": "concept"
        ...     }
        ... ]
        >>> results = evaluate_retrieval(test_set, top_k=5)
        >>> print(f"Precision@5: {results['precision_at_k']:.3f}")
        >>> print(f"Recall@5: {results['recall_at_k']:.3f}")
    """
    precision_scores = []
    recall_scores = []
    per_query_results = []

    for test_case in test_set:
        question = test_case["question"]
        relevant_ids = test_case["relevant_chunk_ids"]
        topic = test_case.get("topic", "unknown")
        difficulty = test_case.get("difficulty", "unknown")

        # Retrieve chunks for this query
        retrieved_chunks = retrieve_chunks(
            query=question,
            top_k=top_k,
            min_similarity=min_similarity,
            hybrid=hybrid
        )

        # Extract chunk IDs from retrieved results
        retrieved_ids = [chunk["chunk_id"] for chunk in retrieved_chunks]

        # Calculate precision and recall
        precision = calculate_precision_at_k(retrieved_ids, relevant_ids, k=top_k)
        recall = calculate_recall_at_k(retrieved_ids, relevant_ids, k=top_k)

        # Track scores
        precision_scores.append(precision)
        recall_scores.append(recall)

        # Calculate additional stats for debugging
        relevant_in_top_k = len(set(retrieved_ids[:top_k]) & set(relevant_ids))

        # Store per-query result
        per_query_results.append({
            "question": question,
            "topic": topic,
            "difficulty": difficulty,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "num_retrieved": len(retrieved_ids),
            "num_relevant": len(relevant_ids),
            "relevant_in_top_k": relevant_in_top_k
        })

    # Calculate aggregate metrics
    precision_at_k = sum(precision_scores) / len(precision_scores) if precision_scores else 0.0
    recall_at_k = sum(recall_scores) / len(recall_scores) if recall_scores else 0.0

    return {
        "retrieval_mode": "hybrid" if hybrid else "semantic",
        "precision_at_k": round(precision_at_k, 3),
        "recall_at_k": round(recall_at_k, 3),
        "num_queries": len(test_set),
        "top_k": top_k,
        "min_similarity": min_similarity,
        "per_query_results": per_query_results
    }


def format_evaluation_results(results: Dict) -> str:
    """
    Format evaluation results for human-readable display.

    Args:
        results: Evaluation results dict from evaluate_retrieval()

    Returns:
        Formatted string with aggregate metrics and worst-performing queries

    Example:
        >>> results = evaluate_retrieval(test_set)
        >>> print(format_evaluation_results(results))
        === Retrieval Evaluation Results ===
        Precision@5: 0.720 (72.0% of top-5 results are relevant)
        Recall@5: 0.650 (65.0% of relevant items retrieved)
        Queries evaluated: 30
        ...
    """
    output_lines = []

    # Header
    output_lines.append("=" * 60)
    output_lines.append("RETRIEVAL EVALUATION RESULTS")
    output_lines.append("=" * 60)

    # Aggregate metrics
    retrieval_mode = results.get("retrieval_mode", "unknown")
    precision = results["precision_at_k"]
    recall = results["recall_at_k"]
    num_queries = results["num_queries"]
    top_k = results["top_k"]

    output_lines.append("")
    output_lines.append(f"Retrieval Mode: {retrieval_mode}")
    output_lines.append("")
    output_lines.append("Aggregate Metrics:")
    output_lines.append(f"  Precision@{top_k}: {precision:.3f} ({precision*100:.1f}% of top-{top_k} results are relevant)")
    output_lines.append(f"  Recall@{top_k}: {recall:.3f} ({recall*100:.1f}% of relevant items retrieved)")
    output_lines.append(f"  Queries evaluated: {num_queries}")
    output_lines.append("")

    # Target comparison
    precision_target = 0.70
    recall_target = 0.60

    precision_status = "PASS ✓" if precision >= precision_target else "FAIL ✗"
    recall_status = "PASS ✓" if recall >= recall_target else "FAIL ✗"

    output_lines.append("Target Comparison:")
    output_lines.append(f"  Precision@{top_k} >= {precision_target:.2f}: {precision:.3f} — {precision_status}")
    output_lines.append(f"  Recall@{top_k} >= {recall_target:.2f}: {recall:.3f} — {recall_status}")
    output_lines.append("")

    # Worst-performing queries (sorted by precision ascending)
    per_query = results.get("per_query_results", [])
    worst_queries = sorted(per_query, key=lambda x: x["precision"])[:5]

    output_lines.append("Worst-Performing Queries (by precision):")
    output_lines.append("-" * 60)
    for i, query_result in enumerate(worst_queries, 1):
        output_lines.append(f"{i}. {query_result['question']}")
        output_lines.append(f"   Precision: {query_result['precision']:.3f}, Recall: {query_result['recall']:.3f}")
        output_lines.append(f"   Topic: {query_result['topic']}, Difficulty: {query_result['difficulty']}")
        output_lines.append(f"   Retrieved: {query_result['num_retrieved']}, Relevant: {query_result['num_relevant']}")
        output_lines.append("")

    output_lines.append("=" * 60)

    return "\n".join(output_lines)
