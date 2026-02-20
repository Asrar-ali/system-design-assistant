"""
Orchestrates complete ingestion pipeline from source JSON files to ChromaDB.

Integrates loaders, chunkers, and embedder into a single cohesive pipeline
with incremental ingestion to avoid re-processing already-embedded content.
"""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

from src.models.source import Source, SourceType
from src.models.document import Document, Chunk
from src.ingestion.loaders import load_github_repos, load_blog_posts, load_youtube_videos
from src.ingestion.chunkers import chunk_markdown, chunk_text, chunk_youtube_transcript
from src.ingestion.embedder import generate_embeddings
from src.indexing.vector_store import get_chroma_client, get_or_create_collection


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """
    Metrics tracking for ingestion pipeline execution.

    Tracks counts at each pipeline stage plus elapsed time and errors.
    """
    sources_processed: int
    chunks_created: int
    chunks_embedded: int
    chunks_stored: int
    time_elapsed: float
    errors: list[str]


def ingest_sources(
    source_files: list[str],
    collection_name: str = "system_design_docs",
    batch_size: int = 500
) -> IngestionResult:
    """
    Orchestrate complete ingestion pipeline from source JSON files to ChromaDB.

    Pipeline stages:
        0. Load sources from JSON files
        1. Load raw content (with incremental processing to skip already-ingested sources)
        2. Chunk documents based on source type
        3. Generate embeddings in batches
        4. Store to ChromaDB in efficient batches
        5. Return metrics

    Args:
        source_files: List of paths to source JSON files
                     (e.g., ["data/sources/github_sources.json", ...])
        collection_name: ChromaDB collection name (default: "system_design_docs")
        batch_size: Number of chunks per batch for storage (default: 500)

    Returns:
        IngestionResult with metrics for each pipeline stage

    Example:
        >>> result = ingest_sources([
        ...     "data/sources/github_sources.json",
        ...     "data/sources/blog_sources.json",
        ...     "data/sources/youtube_sources.json"
        ... ])
        >>> print(f"Processed {result.sources_processed} sources")
        >>> print(f"Created {result.chunks_created} chunks")
    """
    start_time = time.time()
    errors = []

    # Stage 0: Load sources from JSON files
    logger.info("Stage 0: Loading sources from JSON files...")
    all_sources = []

    for source_file in source_files:
        try:
            with open(source_file, 'r') as f:
                sources_data = json.load(f)
                for source_dict in sources_data:
                    source = Source.from_dict(source_dict)
                    all_sources.append(source)
            logger.info(f"  Loaded {len(sources_data)} sources from {source_file}")
        except Exception as e:
            error_msg = f"Error loading {source_file}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            continue

    if not all_sources:
        logger.error("No sources loaded from any file. Aborting pipeline.")
        return IngestionResult(
            sources_processed=0,
            chunks_created=0,
            chunks_embedded=0,
            chunks_stored=0,
            time_elapsed=time.time() - start_time,
            errors=errors
        )

    logger.info(f"Total sources loaded: {len(all_sources)}")

    # Get ChromaDB client and collection for incremental processing check
    client = get_chroma_client()
    collection = get_or_create_collection(client, name=collection_name)

    # Check for existing chunks to enable incremental processing
    logger.info("Checking for existing chunks in ChromaDB...")
    try:
        existing_data = collection.get()
        existing_ids = set(existing_data.get("ids", []))
        logger.info(f"  Found {len(existing_ids)} existing chunks")

        # Extract unique source URLs from existing chunk IDs
        # Chunk IDs format: {source_url_hash}_{chunk_index}
        existing_source_hashes = set()
        for chunk_id in existing_ids:
            source_hash = chunk_id.split('_')[0]
            existing_source_hashes.add(source_hash)

        # Filter sources: only process sources not yet ingested
        import hashlib
        filtered_sources = []
        for source in all_sources:
            url_hash = hashlib.md5(source.url.encode()).hexdigest()[:8]
            if url_hash not in existing_source_hashes:
                filtered_sources.append(source)

        sources_to_process = filtered_sources
        skipped_count = len(all_sources) - len(filtered_sources)
        if skipped_count > 0:
            logger.info(f"  Skipping {skipped_count} already-ingested sources")
    except Exception as e:
        logger.warning(f"Could not check existing chunks: {e}. Processing all sources.")
        sources_to_process = all_sources

    if not sources_to_process:
        logger.info("No new sources to process. All sources already ingested.")
        return IngestionResult(
            sources_processed=0,
            chunks_created=0,
            chunks_embedded=0,
            chunks_stored=0,
            time_elapsed=time.time() - start_time,
            errors=errors
        )

    logger.info(f"Processing {len(sources_to_process)} new sources...")

    # Group sources by type for routing to appropriate loaders
    github_sources = [s for s in sources_to_process if s.source_type == SourceType.GITHUB_REPO]
    blog_sources = [s for s in sources_to_process if s.source_type == SourceType.BLOG_POST]
    youtube_sources = [s for s in sources_to_process if s.source_type == SourceType.YOUTUBE_VIDEO]

    # Stage 1: Load raw content
    logger.info("Stage 1: Loading raw content...")
    all_documents = []

    if github_sources:
        logger.info(f"  Loading {len(github_sources)} GitHub repos...")
        try:
            github_docs = load_github_repos(github_sources)
            all_documents.extend(github_docs)
            logger.info(f"    Loaded {len(github_docs)} documents from GitHub")
        except Exception as e:
            error_msg = f"Error loading GitHub repos: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    if blog_sources:
        logger.info(f"  Loading {len(blog_sources)} blog posts...")
        try:
            blog_docs = load_blog_posts(blog_sources)
            all_documents.extend(blog_docs)
            logger.info(f"    Loaded {len(blog_docs)} documents from blogs")
        except Exception as e:
            error_msg = f"Error loading blog posts: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    if youtube_sources:
        logger.info(f"  Loading {len(youtube_sources)} YouTube videos...")
        try:
            youtube_docs = load_youtube_videos(youtube_sources)
            all_documents.extend(youtube_docs)
            logger.info(f"    Loaded {len(youtube_docs)} documents from YouTube")
        except Exception as e:
            error_msg = f"Error loading YouTube videos: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    if not all_documents:
        logger.warning("No documents loaded from any source. Check errors.")
        return IngestionResult(
            sources_processed=len(sources_to_process),
            chunks_created=0,
            chunks_embedded=0,
            chunks_stored=0,
            time_elapsed=time.time() - start_time,
            errors=errors
        )

    logger.info(f"Total documents loaded: {len(all_documents)}")

    # Stage 2: Chunk documents
    logger.info("Stage 2: Chunking documents...")
    all_chunks = []

    for doc in all_documents:
        try:
            # Route to appropriate chunker based on source type
            if doc.source.source_type == SourceType.GITHUB_REPO:
                chunks = chunk_markdown(doc)
            elif doc.source.source_type == SourceType.BLOG_POST:
                chunks = chunk_text(doc)
            elif doc.source.source_type == SourceType.YOUTUBE_VIDEO:
                chunks = chunk_youtube_transcript(doc)
            else:
                logger.warning(f"Unknown source type: {doc.source.source_type}")
                continue

            all_chunks.extend(chunks)
        except Exception as e:
            error_msg = f"Error chunking document from {doc.source.url}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            continue

    if not all_chunks:
        logger.warning("No chunks created. Check chunking errors.")
        return IngestionResult(
            sources_processed=len(sources_to_process),
            chunks_created=0,
            chunks_embedded=0,
            chunks_stored=0,
            time_elapsed=time.time() - start_time,
            errors=errors
        )

    logger.info(f"Total chunks created: {len(all_chunks)}")

    # Stage 3: Generate embeddings
    logger.info("Stage 3: Generating embeddings...")
    try:
        embedded_chunks = generate_embeddings(all_chunks, batch_size=32)
        logger.info(f"  Generated embeddings for {len(embedded_chunks)} chunks")
    except Exception as e:
        error_msg = f"Error generating embeddings: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        return IngestionResult(
            sources_processed=len(sources_to_process),
            chunks_created=len(all_chunks),
            chunks_embedded=0,
            chunks_stored=0,
            time_elapsed=time.time() - start_time,
            errors=errors
        )

    # Stage 4: Store to ChromaDB in batches
    logger.info(f"Stage 4: Storing chunks to ChromaDB (batch_size={batch_size})...")
    chunks_stored = 0

    for i in range(0, len(embedded_chunks), batch_size):
        batch = embedded_chunks[i:i + batch_size]

        try:
            # Prepare batch data for ChromaDB
            ids = [chunk.chunk_id for chunk in batch]
            documents = [chunk.text for chunk in batch]
            embeddings = [chunk.embedding for chunk in batch]
            metadatas = [chunk.metadata for chunk in batch]

            # Add to ChromaDB collection
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

            chunks_stored += len(batch)

            # Progress tracking: log every 500 chunks
            if chunks_stored % 500 == 0 or chunks_stored == len(embedded_chunks):
                logger.info(f"  Stored {chunks_stored}/{len(embedded_chunks)} chunks")

        except Exception as e:
            error_msg = f"Error storing batch {i}-{i+len(batch)}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            continue

    # Stage 5: Return metrics
    time_elapsed = time.time() - start_time

    result = IngestionResult(
        sources_processed=len(sources_to_process),
        chunks_created=len(all_chunks),
        chunks_embedded=len(embedded_chunks),
        chunks_stored=chunks_stored,
        time_elapsed=time_elapsed,
        errors=errors
    )

    logger.info(f"Pipeline complete in {time_elapsed:.2f}s")
    logger.info(f"  Sources processed: {result.sources_processed}")
    logger.info(f"  Chunks created: {result.chunks_created}")
    logger.info(f"  Chunks embedded: {result.chunks_embedded}")
    logger.info(f"  Chunks stored: {result.chunks_stored}")
    if errors:
        logger.warning(f"  Errors encountered: {len(errors)}")

    return result
