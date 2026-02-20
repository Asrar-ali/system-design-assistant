"""
Content loaders for GitHub repos, blog posts, and YouTube videos.

Provides functions to fetch raw content from different source types,
handling API authentication, rate limits, and content extraction.
"""

import os
import re
from typing import Any
import requests
from bs4 import BeautifulSoup
from github import Github, RateLimitExceededException
from youtube_transcript_api import YouTubeTranscriptApi

from src.models.source import Source, SourceType
from src.models.document import Document


def load_github_repos(sources: list[Source]) -> list[Document]:
    """
    Load markdown files from GitHub repositories.

    Args:
        sources: List of Source objects with source_type=GITHUB_REPO

    Returns:
        List of Document objects containing markdown content

    Raises:
        ValueError: If source URL is invalid or repo not found
        RateLimitExceededException: If GitHub API rate limit exceeded
    """
    documents = []

    # Initialize GitHub client with token if available
    github_token = os.getenv("GITHUB_TOKEN")
    github_client = Github(github_token) if github_token else Github()

    for source in sources:
        if source.source_type != SourceType.GITHUB_REPO:
            continue

        try:
            # Extract owner/repo from URL
            # Expected formats:
            # - https://github.com/owner/repo
            # - https://github.com/owner/repo/
            url_parts = source.url.rstrip('/').split('/')
            if len(url_parts) < 5 or 'github.com' not in source.url:
                raise ValueError(f"Invalid GitHub URL format: {source.url}")

            owner = url_parts[-2]
            repo_name = url_parts[-1]

            # Fetch repository
            repo = github_client.get_repo(f"{owner}/{repo_name}")

            # Recursively fetch markdown files
            def fetch_markdown_files(path: str = "") -> list[tuple[str, str, str]]:
                """Recursively fetch .md files from repo.

                Returns:
                    List of tuples (filepath, content, raw_url)
                """
                md_files = []
                contents = repo.get_contents(path)

                # Handle both single file and directory listings
                if not isinstance(contents, list):
                    contents = [contents]

                for content_file in contents:
                    if content_file.type == "dir":
                        # Recursively process directories
                        md_files.extend(fetch_markdown_files(content_file.path))
                    elif content_file.name.endswith('.md'):
                        # Decode markdown file content
                        file_content = content_file.decoded_content.decode('utf-8')
                        md_files.append((
                            content_file.path,
                            file_content,
                            content_file.html_url
                        ))

                return md_files

            markdown_files = fetch_markdown_files()

            # Create Document for each markdown file
            for filepath, content, raw_url in markdown_files:
                doc = Document(
                    content=content,
                    source=source,
                    metadata={
                        "filepath": filepath,
                        "repo_name": f"{owner}/{repo_name}",
                        "source_type": source.source_type.value,
                        "topic_categories": [cat.value for cat in source.topic_categories],
                    },
                    raw_url=raw_url
                )
                documents.append(doc)

        except RateLimitExceededException:
            # Re-raise rate limit errors to allow caller to handle
            raise
        except Exception as e:
            # Log error but continue processing other sources
            print(f"Error loading GitHub repo {source.url}: {str(e)}")
            continue

    return documents


def load_blog_posts(sources: list[Source]) -> list[Document]:
    """
    Load content from blog post URLs using web scraping.

    Args:
        sources: List of Source objects with source_type=BLOG_POST

    Returns:
        List of Document objects containing cleaned blog content

    Raises:
        requests.RequestException: If HTTP request fails
    """
    documents = []

    for source in sources:
        if source.source_type != SourceType.BLOG_POST:
            continue

        try:
            # Fetch HTML content
            response = requests.get(source.url, timeout=30)
            response.raise_for_status()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Try to extract article content (common HTML5 semantic tags)
            article = soup.find('article')
            if not article:
                article = soup.find('main')
            if not article:
                # Fallback to body if no article/main tag
                article = soup.find('body')

            if not article:
                print(f"Could not extract content from {source.url}")
                continue

            # Extract text and clean whitespace
            text = article.get_text(separator='\n', strip=True)
            # Collapse multiple spaces/newlines
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)

            # Validate word count (minimum 200 words for substantive content)
            word_count = len(text.split())
            if word_count < 200:
                print(f"Blog post too short ({word_count} words): {source.url}")
                continue

            # Create Document
            doc = Document(
                content=text.strip(),
                source=source,
                metadata={
                    "word_count": word_count,
                    "source_type": source.source_type.value,
                    "topic_categories": [cat.value for cat in source.topic_categories],
                },
                raw_url=source.url
            )
            documents.append(doc)

        except requests.RequestException as e:
            print(f"Error fetching blog post {source.url}: {str(e)}")
            continue
        except Exception as e:
            print(f"Error processing blog post {source.url}: {str(e)}")
            continue

    return documents


def load_youtube_videos(sources: list[Source]) -> list[Document]:
    """
    Load video transcripts from YouTube URLs.

    Args:
        sources: List of Source objects with source_type=YOUTUBE_VIDEO

    Returns:
        List of Document objects containing merged transcript paragraphs
    """
    documents = []

    for source in sources:
        if source.source_type != SourceType.YOUTUBE_VIDEO:
            continue

        try:
            # Extract video ID from URL
            # Handles:
            # - https://www.youtube.com/watch?v=VIDEO_ID
            # - https://youtu.be/VIDEO_ID
            video_id = None
            if 'youtube.com/watch?v=' in source.url:
                video_id = source.url.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in source.url:
                video_id = source.url.split('youtu.be/')[1].split('?')[0]

            if not video_id:
                print(f"Could not extract video ID from {source.url}")
                continue

            # Fetch transcript using the new API (requires instantiation)
            ytt_api = YouTubeTranscriptApi()
            fetched_transcript = ytt_api.fetch(video_id)
            # Convert to list of dicts format
            transcript = [{"text": snippet.text, "start": snippet.start, "duration": snippet.duration} for snippet in fetched_transcript]

            # Merge transcript segments into paragraphs
            # Strategy: Group by 60-second windows or sentence boundaries
            paragraphs = []
            current_paragraph = []
            current_duration = 0
            paragraph_window = 60.0  # seconds

            for segment in transcript:
                text = segment['text'].strip()
                duration = segment['duration']

                current_paragraph.append(text)
                current_duration += duration

                # Create new paragraph after 60 seconds or sentence ending
                if current_duration >= paragraph_window or text.endswith(('.', '!', '?')):
                    paragraph_text = ' '.join(current_paragraph)
                    if paragraph_text:
                        paragraphs.append(paragraph_text)
                    current_paragraph = []
                    current_duration = 0

            # Add remaining text as final paragraph
            if current_paragraph:
                paragraph_text = ' '.join(current_paragraph)
                if paragraph_text:
                    paragraphs.append(paragraph_text)

            # Combine paragraphs with double newlines
            merged_content = '\n\n'.join(paragraphs)

            # Create Document
            doc = Document(
                content=merged_content,
                source=source,
                metadata={
                    "video_id": video_id,
                    "transcript_segments": len(transcript),
                    "paragraphs": len(paragraphs),
                    "source_type": source.source_type.value,
                    "topic_categories": [cat.value for cat in source.topic_categories],
                },
                raw_url=source.url
            )
            documents.append(doc)

        except Exception as e:
            print(f"Error loading YouTube video {source.url}: {str(e)}")
            continue

    return documents
