"""
Chunking strategies for different content types.

Provides semantic text splitting for markdown, plain text, and YouTube transcripts
using LangChain text splitters with optimized chunk sizes for RAG retrieval.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

from src.models.document import Document, Chunk


def chunk_markdown(doc: Document) -> list[Chunk]:
    """
    Chunk markdown content with header-aware splitting.

    Uses a two-stage approach:
    1. Split by markdown headers (preserving section structure)
    2. Further split large sections with RecursiveCharacterTextSplitter

    Args:
        doc: Document containing markdown content

    Returns:
        List of Chunk objects with preserved header context
    """
    # Stage 1: Split by markdown headers
    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False  # Preserve headers in chunks for context
    )

    # Split into header-based sections
    header_sections = markdown_splitter.split_text(doc.content)

    # Stage 2: Further split large sections
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=256,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )

    chunks = []
    chunk_index = 0

    for section in header_sections:
        # Get text from the section (LangChain Document object)
        section_text = section.page_content
        section_metadata = section.metadata

        # Split large sections further
        split_texts = text_splitter.split_text(section_text)

        for text in split_texts:
            # Generate unique chunk ID using raw_url (file URL, not repo URL)
            chunk_id = Chunk.generate_chunk_id(doc.raw_url, chunk_index)

            # Combine document metadata with section headers
            # Convert lists to comma-separated strings for ChromaDB compatibility
            topic_cats = doc.metadata.get("topic_categories", [])
            if isinstance(topic_cats, list):
                topic_cats = ",".join(topic_cats)

            chunk_metadata = {
                "filepath": doc.metadata.get("filepath", ""),
                "repo_name": doc.metadata.get("repo_name", ""),
                "source_type": doc.metadata.get("source_type", ""),
                "topic_categories": topic_cats,
                "section_heading": section_metadata.get("h1", section_metadata.get("h2", section_metadata.get("h3", ""))),
                "source_url": doc.raw_url,
            }

            chunk = Chunk(
                text=text,
                embedding=None,  # Populated later by embedder
                metadata=chunk_metadata,
                chunk_id=chunk_id
            )
            chunks.append(chunk)
            chunk_index += 1

    return chunks


def chunk_text(doc: Document) -> list[Chunk]:
    """
    Chunk plain text content with recursive character splitting.

    Uses hierarchical separators (paragraphs -> lines -> spaces -> characters)
    to create semantically coherent chunks.

    Args:
        doc: Document containing plain text content

    Returns:
        List of Chunk objects
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=256,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],  # Prioritize paragraph boundaries
        is_separator_regex=False,
    )

    split_texts = text_splitter.split_text(doc.content)

    chunks = []
    for chunk_index, text in enumerate(split_texts):
        chunk_id = Chunk.generate_chunk_id(doc.raw_url, chunk_index)

        # Convert lists to comma-separated strings for ChromaDB compatibility
        topic_cats = doc.metadata.get("topic_categories", [])
        if isinstance(topic_cats, list):
            topic_cats = ",".join(topic_cats)

        chunk_metadata = {
            "source_type": doc.metadata.get("source_type", ""),
            "topic_categories": topic_cats,
            "word_count": doc.metadata.get("word_count", 0),
            "source_url": doc.raw_url,
        }

        chunk = Chunk(
            text=text,
            embedding=None,
            metadata=chunk_metadata,
            chunk_id=chunk_id
        )
        chunks.append(chunk)

    return chunks


def chunk_youtube_transcript(doc: Document) -> list[Chunk]:
    """
    Chunk YouTube transcript content.

    Uses same splitting strategy as plain text (256/50) but preserves
    video-specific metadata like video_id and timestamps.

    Args:
        doc: Document containing YouTube transcript content

    Returns:
        List of Chunk objects with video metadata
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=256,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
        is_separator_regex=False,
    )

    split_texts = text_splitter.split_text(doc.content)

    chunks = []
    for chunk_index, text in enumerate(split_texts):
        chunk_id = Chunk.generate_chunk_id(doc.raw_url, chunk_index)

        # Convert lists to comma-separated strings for ChromaDB compatibility
        topic_cats = doc.metadata.get("topic_categories", [])
        if isinstance(topic_cats, list):
            topic_cats = ",".join(topic_cats)

        # Include video-specific metadata
        chunk_metadata = {
            "source_type": doc.metadata.get("source_type", ""),
            "topic_categories": topic_cats,
            "source_url": doc.raw_url,
            "video_id": doc.metadata.get("video_id", ""),
        }

        chunk = Chunk(
            text=text,
            embedding=None,
            metadata=chunk_metadata,
            chunk_id=chunk_id
        )
        chunks.append(chunk)

    return chunks
