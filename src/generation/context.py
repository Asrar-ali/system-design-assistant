"""
Citation-aware context preparation for answer generation.

Implements research Pattern 1 (Citation-Aware Context Injection) by adding
numbered source markers [1], [2], [3] to chunks and building source metadata
map for citation resolution.
"""


def prepare_context_with_citations(chunks: list[dict]) -> tuple[str, dict]:
    """
    Prepare context string with numbered citations and source metadata map.

    Takes retrieval results (list of chunk dicts) and injects numbered citation
    markers for LLM to reference. Builds parallel source map for resolving
    citations back to original sources.

    IMPORTANT: Input is list[dict] from retrieve_chunks(), NOT list[Chunk] objects.
    Retrieval pipeline returns dicts with keys: chunk_id, text, metadata, similarity_score.

    Args:
        chunks: List of chunk dicts from retrieve_chunks() with keys:
                - chunk_id (str): Unique chunk identifier
                - text (str): Chunk text content
                - metadata (dict): Source metadata with keys:
                  - source_url (str): Original source URL
                  - source_title (str): Source title/name
                  - section_header (str): Section within source
                - similarity_score or fusion_score (float): Relevance score

    Returns:
        Tuple of (context_string, source_map):
        - context_string: Chunks with injected [1], [2], [3] markers
        - source_map: Dict mapping citation numbers to source metadata
          {
              1: {"source_url": "...", "title": "...", "section": "...", "chunk_id": "..."},
              2: {"source_url": "...", "title": "...", "section": "...", "chunk_id": "..."},
              ...
          }

    Example:
        >>> chunks = [
        ...     {
        ...         "chunk_id": "abc123",
        ...         "text": "CAP theorem states...",
        ...         "metadata": {
        ...             "source_url": "https://github.com/example/repo",
        ...             "source_title": "System Design Primer",
        ...             "section_header": "Database Theory"
        ...         },
        ...         "similarity_score": 0.85
        ...     }
        ... ]
        >>> context, source_map = prepare_context_with_citations(chunks)
        >>> "[1]" in context
        True
        >>> 1 in source_map
        True
        >>> source_map[1]["title"]
        'System Design Primer'
    """
    # Handle empty chunks list
    if not chunks:
        return "", {}

    context_parts = []
    source_map = {}

    # Inject numbered citation markers starting at 1 (user-friendly)
    for idx, chunk in enumerate(chunks, start=1):
        # Access dict keys, NOT object attributes
        # retrieve_chunks() returns dicts, not Chunk objects
        chunk_text = chunk.get("text", "")

        # Inject citation number before chunk text
        context_parts.append(f"[{idx}] {chunk_text}")

        # Build source metadata map from chunk dict
        # Use .get() with defaults for graceful missing metadata handling
        metadata = chunk.get("metadata", {})

        # Derive title from available metadata:
        # - repo_name for GitHub repos (e.g., "donnemartin/system-design-primer")
        # - source_title if explicitly set
        # - Fall back to "Unknown Source"
        title = (
            metadata.get("source_title") or
            metadata.get("repo_name") or
            "Unknown Source"
        )

        source_map[idx] = {
            "source_url": metadata.get("source_url"),
            "title": title,
            "section": metadata.get("section_heading", "") or metadata.get("section_header", ""),
            "chunk_id": chunk.get("chunk_id")
        }

    # Join chunks with double newline for readability
    context = "\n\n".join(context_parts)

    return context, source_map
