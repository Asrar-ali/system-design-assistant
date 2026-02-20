"""
LLM Provider Factory with Groq primary and Ollama fallback.

Implements primary-backup fallback pattern for reliable LLM access:
- Groq (primary): Fast cloud inference with llama-3.3-70b-versatile
- Ollama (backup): Local inference fallback with llama3.2

Configuration:
- Groq: Requires GROQ_API_KEY environment variable
- Ollama: Uses OpenAI-compatible API at localhost:11434
"""

import logging
import os
from typing import Optional

from groq import Groq
from groq import RateLimitError, APIConnectionError, InternalServerError
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """
    LLM provider factory with automatic failover from Groq to Ollama.

    Usage:
        factory = LLMProviderFactory()
        response = factory.generate([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain load balancing"}
        ])
    """

    def __init__(self):
        """Initialize both Groq and Ollama clients."""
        self.groq_client = self._init_groq()
        self.ollama_client = self._init_ollama()

    def _init_groq(self) -> Optional[Groq]:
        """
        Initialize Groq client if API key is available.

        Returns:
            Groq client if GROQ_API_KEY is set, None otherwise
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.info("GROQ_API_KEY not found - Groq provider not configured")
            return None

        logger.info("Groq provider configured with llama-3.3-70b-versatile")
        return Groq(api_key=api_key)

    def _init_ollama(self) -> OpenAI:
        """
        Initialize Ollama client using OpenAI-compatible API.

        Returns:
            OpenAI client configured for Ollama at localhost:11434
        """
        logger.info("Ollama provider configured with llama3.2 at localhost:11434")
        return OpenAI(
            base_url="http://localhost:11434/v1/",
            api_key="ollama"  # Dummy key, Ollama doesn't require authentication
        )

    def generate(self, messages: list[dict], max_retries: int = 2) -> str:
        """
        Generate chat completion with automatic Groq → Ollama fallback.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_retries: Maximum retry attempts for each provider (default: 2)

        Returns:
            Generated text response from LLM

        Raises:
            Exception: If both Groq and Ollama fail

        Example:
            >>> factory = LLMProviderFactory()
            >>> messages = [
            ...     {"role": "system", "content": "You are a technical expert."},
            ...     {"role": "user", "content": "What is sharding?"}
            ... ]
            >>> response = factory.generate(messages)
        """
        # Try Groq first if configured
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.3,  # Low hallucination, factual answers
                    max_tokens=1024   # Sufficient for structured answers
                )
                return response.choices[0].message.content

            except (RateLimitError, APIConnectionError, InternalServerError) as e:
                logger.warning(
                    f"Groq provider failed ({e.__class__.__name__}), "
                    "falling back to Ollama"
                )
                # Continue to Ollama fallback below

        # Fallback to Ollama
        try:
            response = self.ollama_client.chat.completions.create(
                model="llama3.2",
                messages=messages,
                temperature=0.3,  # Match Groq temperature
                max_tokens=1024
            )
            logger.info("Using Ollama fallback provider")
            return response.choices[0].message.content

        except Exception as e:
            # Both providers failed
            error_msg = (
                "Both Groq and Ollama providers failed. "
                "Ensure Ollama is running (ollama serve) and llama3.2 model is pulled "
                "(ollama pull llama3.2)"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
