"""
Document ingestion pipeline.

Orchestrates loading, chunking, embedding, and storing documents from curated sources.
"""

from .pipeline import ingest_sources, IngestionResult

__all__ = ["ingest_sources", "IngestionResult"]
