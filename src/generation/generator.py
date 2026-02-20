"""
End-to-end answer generation pipeline integrating retrieval, context, LLM, and citations.

Implements research Pattern 4 (End-to-End Pipeline Integration) combining:
- Hybrid retrieval (semantic + BM25)
- Citation-aware context preparation
- LLM generation with structured prompts
- Citation extraction and validation

Pipeline flow: query → retrieve_chunks → prepare_context → LLM → extract_citations → validate
"""

import logging
import re
from typing import Optional

from src.retrieval.retriever import retrieve_chunks
from src.generation.context import prepare_context_with_citations
from src.generation.prompts import SYSTEM_PROMPT, generate_user_prompt
from src.generation.providers import LLMProviderFactory

logger = logging.getLogger(__name__)


def extract_citation_ids(answer: str) -> list[int]:
    """
    Extract citation IDs from LLM answer containing [1], [2], [3] markers.

    Uses regex to find all [N] patterns where N is a number, then deduplicates
    and sorts the results.

    Args:
        answer: LLM-generated text with inline citations like "CAP theorem [1][3]"

    Returns:
        Sorted list of unique citation IDs

    Example:
        >>> extract_citation_ids("CAP theorem [1][3] and BASE [1]")
        [1, 3]
        >>> extract_citation_ids("No citations here")
        []
        >>> extract_citation_ids("Redis [10] provides [2] caching")
        [2, 10]
    """
    # Pattern matches [N] where N is one or more digits
    # Parentheses create capture group for the number
    pattern = r'\[(\d+)\]'

    # Find all matches and extract the captured groups (the numbers)
    matches = re.findall(pattern, answer)

    # Convert strings to integers
    citation_ids = [int(match) for match in matches]

    # Deduplicate and sort
    unique_ids = sorted(set(citation_ids))

    return unique_ids


def generate_answer_with_citations(
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.3
) -> dict:
    """
    Generate answer with inline citations from curated knowledge base.

    End-to-end RAG pipeline:
    1. Retrieve relevant chunks (hybrid search by default)
    2. Handle empty retrieval gracefully
    3. Prepare context with numbered citations
    4. Generate answer via LLM with structured prompts
    5. Extract and validate citations
    6. Return structured result with answer, sources, status

    Args:
        query: User's system design question
        top_k: Number of chunks to retrieve (default: 5)
        min_similarity: Minimum similarity threshold for retrieval (default: 0.3)

    Returns:
        Dict with keys:
        - answer (str): Generated answer with inline citations
        - sources (list[dict]): Cited source metadata (url, title, section, chunk_id)
        - status (str): "success" | "no_context" | "llm_error"
        - num_chunks_retrieved (int): Number of chunks retrieved (0 if empty)

    Example:
        >>> result = generate_answer_with_citations("What is the CAP theorem?")
        >>> result["status"]
        'success'
        >>> "[1]" in result["answer"]  # Has inline citations
        True
        >>> len(result["sources"]) > 0  # Has source metadata
        True
    """
    logger.info(f"Starting answer generation for query: {query[:50]}...")

    # Step 1: Retrieve chunks using hybrid search (semantic + BM25)
    logger.info(f"Retrieving chunks (top_k={top_k}, min_similarity={min_similarity}, hybrid=True)")
    chunks = retrieve_chunks(
        query=query,
        top_k=top_k,
        min_similarity=min_similarity,
        hybrid=True
    )

    # Step 2: Handle empty retrieval
    if not chunks:
        logger.warning("No relevant chunks retrieved - returning 'no_context' response")
        return {
            "answer": "I don't have relevant information in my knowledge base to answer this question.",
            "sources": [],
            "status": "no_context",
            "num_chunks_retrieved": 0
        }

    logger.info(f"Retrieved {len(chunks)} chunks")

    # Step 3: Prepare context with citations
    logger.info("Preparing context with citation markers")
    context, source_map = prepare_context_with_citations(chunks)

    # Step 4: Generate answer with LLM
    logger.info("Generating answer via LLM provider")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": generate_user_prompt(query, context)}
    ]

    try:
        provider = LLMProviderFactory()
        answer = provider.generate(messages)
        logger.info("LLM generation successful")
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return {
            "answer": f"Error generating answer: {str(e)}",
            "sources": [],
            "status": "llm_error",
            "num_chunks_retrieved": len(chunks)
        }

    # Step 5: Extract and validate citations
    logger.info("Extracting citations from answer")
    cited_ids = extract_citation_ids(answer)

    # Validate citation IDs exist in source_map
    # Filter out any invalid citations (e.g., [7] when only [1-5] exist)
    cited_sources = [
        source_map[i] for i in cited_ids
        if i in source_map
    ]

    logger.info(f"Found {len(cited_ids)} citations, {len(cited_sources)} valid")

    # Step 6: Return structured result
    return {
        "answer": answer,
        "sources": cited_sources,
        "status": "success",
        "num_chunks_retrieved": len(chunks)
    }
