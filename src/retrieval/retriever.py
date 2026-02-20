"""
Semantic search retrieval using ChromaDB vector store.

Provides functions to embed user queries and retrieve relevant chunks
from the indexed knowledge base using cosine similarity.

CRITICAL: Uses same embedding model (all-MiniLM-L6-v2) as indexing pipeline
to ensure embedding space compatibility.
"""

from src.ingestion.embedder import load_embedding_model
from src.indexing.vector_store import get_chroma_client, get_or_create_collection


def embed_query(query: str) -> list[float]:
    """
    Embed user query using same model as indexed documents.

    CRITICAL: This function MUST use the same embedding model as the indexing
    pipeline (all-MiniLM-L6-v2 via load_embedding_model()). Embedding mismatch
    is the #1 cause of retrieval failures in RAG systems.

    Args:
        query: User's natural language query

    Returns:
        384-dimensional embedding vector as list of floats

    Example:
        >>> embedding = embed_query("How do you design a URL shortener?")
        >>> len(embedding)
        384
    """
    # Load cached embedding model (same as indexing)
    model = load_embedding_model()

    # Encode query to embedding vector
    # convert_to_numpy=True for efficient processing
    embedding = model.encode([query], convert_to_numpy=True)[0]

    # Convert numpy array to list for ChromaDB compatibility
    return embedding.tolist()


def query_vector_store(
    query_embedding: list[float],
    top_k: int = 5,
    metadata_filter: dict = None
) -> dict:
    """
    Query ChromaDB vector store for similar chunks.

    Args:
        query_embedding: 384-dim embedding vector from embed_query()
        top_k: Number of most similar chunks to retrieve (default: 5)
        metadata_filter: Optional metadata filter using MongoDB-style syntax.
                        Examples:
                        - {"source_type": "github"}
                        - {"source_type": {"$in": ["github", "blog"]}}
                        - {"$and": [{"source_type": "github"},
                                   {"topic_categories": {"$regex": ".*databases.*"}}]}

    Returns:
        ChromaDB results dict with keys:
        - ids: List of chunk IDs
        - documents: List of chunk text
        - metadatas: List of metadata dicts
        - distances: List of cosine distances (0=identical, 2=opposite)

    Note:
        ChromaDB uses cosine distance, not similarity. Convert with:
        similarity = 1 - distance
    """
    # Get ChromaDB client and collection
    client = get_chroma_client()
    collection = get_or_create_collection(client, name="system_design_docs")

    # Query vector store
    # where parameter uses MongoDB-style filters
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=metadata_filter
    )

    return results


def retrieve_chunks(
    query: str,
    top_k: int = 5,
    metadata_filter: dict = None,
    min_similarity: float = 0.3,
    hybrid: bool = True
) -> list[dict]:
    """
    Retrieve relevant chunks for user query.

    End-to-end retrieval pipeline: embed query → search vector store →
    convert distances to similarities → filter by threshold → rank results.

    Args:
        query: User's natural language query
        top_k: Number of chunks to retrieve (default: 5)
        metadata_filter: Optional metadata filter (see query_vector_store docs)
        min_similarity: Minimum similarity threshold for results (default: 0.3)
                       Range: -1.0 to 1.0, where 1.0 = identical
        hybrid: Enable hybrid search (BM25 + semantic) via RRF fusion (default: True)
                When False, uses semantic search only (Phase 4 behavior)

    Returns:
        List of result dicts, each containing:
        - chunk_id: Unique chunk identifier
        - text: Chunk text content
        - metadata: Source metadata (url, type, topics, etc.)
        - similarity_score: Cosine similarity (1.0 = identical, 0.0 = orthogonal)
                           (semantic-only mode)
        - fusion_score: Combined RRF score (hybrid mode)
        - bm25_score: BM25 keyword score (hybrid mode, if chunk matched)

    Results are sorted by similarity_score (semantic) or fusion_score (hybrid)
    in descending order.

    Example:
        >>> # Hybrid search (default)
        >>> results = retrieve_chunks("How do you design a URL shortener?", top_k=3)
        >>> 'fusion_score' in results[0]
        True
        >>> # Semantic-only search
        >>> results = retrieve_chunks("How do you design a URL shortener?",
        ...                          top_k=3, hybrid=False)
        >>> 'similarity_score' in results[0]
        True
    """
    # Hybrid search routing
    if hybrid:
        from src.retrieval.hybrid_retriever import retrieve_hybrid
        return retrieve_hybrid(
            query=query,
            top_k=top_k,
            metadata_filter=metadata_filter,
            min_similarity=min_similarity
        )

    # Semantic-only search path (Phase 4 behavior)
    # Step 1: Embed query
    query_embedding = embed_query(query)

    # Step 2: Query vector store
    raw_results = query_vector_store(
        query_embedding=query_embedding,
        top_k=top_k,
        metadata_filter=metadata_filter
    )

    # Step 3: Convert ChromaDB results to structured format
    # ChromaDB returns results as lists grouped by field
    chunks = []
    for i in range(len(raw_results["ids"][0])):
        chunk_id = raw_results["ids"][0][i]
        text = raw_results["documents"][0][i]
        metadata = raw_results["metadatas"][0][i]
        distance = raw_results["distances"][0][i]

        # Convert cosine distance to similarity
        # ChromaDB uses L2 distance for normalized embeddings (equivalent to cosine)
        # distance range: [0, 2] where 0 = identical
        # similarity range: [-1, 1] where 1 = identical
        similarity = 1 - distance

        # Filter by minimum similarity threshold
        if similarity >= min_similarity:
            chunks.append({
                "chunk_id": chunk_id,
                "text": text,
                "metadata": metadata,
                "similarity_score": round(similarity, 3)
            })

    # Step 4: Sort by similarity (descending)
    chunks.sort(key=lambda x: x["similarity_score"], reverse=True)

    return chunks
