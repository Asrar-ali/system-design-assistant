"""
Document and chunk models for processing pipeline.

Defines data structures for raw documents and chunked text segments,
enabling type-safe processing from ingestion through embedding.
"""

from dataclasses import dataclass
import hashlib
from src.models.source import Source


@dataclass
class Document:
    """
    Represents raw content from a source before chunking.

    Used to store extracted content with full metadata for downstream
    processing in the chunking pipeline.
    """
    content: str
    source: Source
    metadata: dict
    raw_url: str

    def to_dict(self) -> dict:
        """Convert Document to dictionary for JSON serialization."""
        return {
            "content": self.content,
            "source": self.source.to_dict(),
            "metadata": self.metadata,
            "raw_url": self.raw_url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        """Create Document from dictionary (JSON deserialization)."""
        return cls(
            content=data["content"],
            source=Source.from_dict(data["source"]),
            metadata=data.get("metadata", {}),
            raw_url=data["raw_url"],
        )


@dataclass
class Chunk:
    """
    Represents a semantically chunked text segment ready for embedding.

    Contains text, optional embedding vector, metadata for retrieval,
    and a unique identifier for deduplication and tracking.

    Metadata fields:
        - source_url: Original source URL
        - source_type: Type of source (github_repo, blog_post, youtube_video)
        - topic_categories: List of topic category values
        - section_heading: Markdown section heading (for GitHub README content)
        - timestamp: Video timestamp (for YouTube content)
    """
    text: str
    embedding: list[float] | None
    metadata: dict
    chunk_id: str

    def to_dict(self) -> dict:
        """Convert Chunk to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "chunk_id": self.chunk_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        """Create Chunk from dictionary (JSON deserialization)."""
        return cls(
            text=data["text"],
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
            chunk_id=data["chunk_id"],
        )

    @staticmethod
    def generate_chunk_id(source_url: str, chunk_index: int) -> str:
        """
        Generate unique chunk identifier using hash-based approach.

        Args:
            source_url: URL of the source document
            chunk_index: Sequential index of chunk within document

        Returns:
            Unique chunk ID in format: {source_url_hash}_{chunk_index}

        Example:
            >>> Chunk.generate_chunk_id("https://github.com/donnemartin/system-design-primer", 0)
            'a3f5b8c9_0'
        """
        # Hash source URL to create shorter, consistent identifier
        url_hash = hashlib.md5(source_url.encode()).hexdigest()[:8]
        return f"{url_hash}_{chunk_index}"
