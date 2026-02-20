"""
Source metadata schema for system design content.

Defines metadata structure for all source types (GitHub repos, blog posts, YouTube videos)
to support quality validation and multi-source ingestion.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SourceType(Enum):
    """Type of content source."""
    GITHUB_REPO = "github_repo"
    BLOG_POST = "blog_post"
    YOUTUBE_VIDEO = "youtube_video"


class TopicCategory(Enum):
    """System design topic categories."""
    DATABASES = "databases"
    CACHING = "caching"
    LOAD_BALANCING = "load_balancing"
    SCALABILITY = "scalability"
    RELIABILITY = "reliability"
    DISTRIBUTED_SYSTEMS = "distributed_systems"
    API_DESIGN = "api_design"
    GENERAL = "general"
    ARCHITECTURE = "architecture"
    MICROSERVICES = "microservices"
    REAL_TIME = "real_time"
    CLOUD_ARCHITECTURE = "cloud_architecture"
    DESIGN_PATTERNS = "design_patterns"
    SEARCH = "search"
    STREAMING = "streaming"
    EVENT_DRIVEN = "event_driven"
    MESSAGE_QUEUE = "message_queue"
    RATE_LIMITING = "rate_limiting"
    WEBSOCKETS = "websockets"


class AuthorityLevel(Enum):
    """Source authority/credibility level."""
    HIGH = "high"  # FAANG blogs, academic, well-known authors
    MEDIUM = "medium"  # Professional blogs, verified engineers
    COMMUNITY = "community"  # GitHub awesome lists, curated collections


@dataclass
class Source:
    """
    Metadata for a system design content source.

    Supports multiple source types with common metadata plus type-specific fields.
    Used for manual curation and validation before ingestion.
    """
    url: str
    source_type: SourceType
    topic_categories: list[TopicCategory]
    authority_level: AuthorityLevel
    title: str
    author: str
    validated: bool = False
    validation_notes: str = ""
    curated_date: datetime | None = None
    estimated_chunks: int = 0

    # Type-specific optional fields
    github_repo_stars: int | None = None
    youtube_views: int | None = None
    blog_publication_date: datetime | None = None

    def to_dict(self) -> dict:
        """Convert Source to dictionary for JSON serialization."""
        data = {
            "url": self.url,
            "source_type": self.source_type.value,
            "topic_categories": [cat.value for cat in self.topic_categories],
            "authority_level": self.authority_level.value,
            "title": self.title,
            "author": self.author,
            "validated": self.validated,
            "validation_notes": self.validation_notes,
            "curated_date": self.curated_date.isoformat() if self.curated_date else None,
            "estimated_chunks": self.estimated_chunks,
        }

        # Add type-specific fields if present
        if self.github_repo_stars is not None:
            data["github_repo_stars"] = self.github_repo_stars
        if self.youtube_views is not None:
            data["youtube_views"] = self.youtube_views
        if self.blog_publication_date is not None:
            data["blog_publication_date"] = self.blog_publication_date.isoformat()

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Source":
        """Create Source from dictionary (JSON deserialization)."""
        # Convert string values back to enums
        source_type = SourceType(data["source_type"])
        topic_categories = [TopicCategory(cat) for cat in data["topic_categories"]]
        authority_level = AuthorityLevel(data["authority_level"])

        # Convert ISO date strings back to datetime
        curated_date = None
        if data.get("curated_date"):
            curated_date = datetime.fromisoformat(data["curated_date"])

        blog_publication_date = None
        if data.get("blog_publication_date"):
            blog_publication_date = datetime.fromisoformat(data["blog_publication_date"])

        return cls(
            url=data["url"],
            source_type=source_type,
            topic_categories=topic_categories,
            authority_level=authority_level,
            title=data["title"],
            author=data["author"],
            validated=data.get("validated", False),
            validation_notes=data.get("validation_notes", ""),
            curated_date=curated_date,
            estimated_chunks=data.get("estimated_chunks", 0),
            github_repo_stars=data.get("github_repo_stars"),
            youtube_views=data.get("youtube_views"),
            blog_publication_date=blog_publication_date,
        )
