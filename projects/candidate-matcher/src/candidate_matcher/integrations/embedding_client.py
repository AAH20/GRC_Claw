"""Embedding client integration for semantic similarity."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from candidate_matcher.config.exceptions import EmbeddingError
from candidate_matcher.config.logging_config import get_logger
from candidate_matcher.config.settings import Settings, get_settings

logger = get_logger(__name__)


class BaseEmbeddingClient(ABC):
    """Abstract base class for embedding clients."""

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        ...

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.
        """
        ...


class LangChainEmbeddingClient(BaseEmbeddingClient):
    """Embedding client backed by LangChain embeddings."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """Initialize the embedding client.

        Args:
            settings: Application settings. Uses global settings if not provided.
        """
        self._settings = settings or get_settings()
        self._embeddings = self._create_embeddings()

    def _create_embeddings(self) -> Embeddings:
        """Create the LangChain embeddings instance.

        Returns:
            Configured embeddings instance.

        Raises:
            EmbeddingError: If creation fails.
        """
        try:
            return OpenAIEmbeddings(
                model=self._settings.embedding_model,
                dimensions=self._settings.embedding_dimensions,
                api_key=self._settings.openai_api_key or None,
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to create embedding model: {e}") from e

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        try:
            embeddings = await self._embeddings.aembed_documents(texts)
            return [list(map(float, emb)) for emb in embeddings]
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e))
            raise EmbeddingError(f"Embedding generation failed: {e}") from e

    async def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        try:
            embedding = await self._embeddings.aembed_query(text)
            return list(map(float, embedding))
        except Exception as e:
            logger.error("query_embedding_failed", error=str(e))
            raise EmbeddingError(f"Query embedding failed: {e}") from e


class MockEmbeddingClient(BaseEmbeddingClient):
    """Mock embedding client for testing and development."""

    def __init__(self, dimensions: int = 1536) -> None:
        """Initialize the mock client.

        Args:
            dimensions: Dimensionality of mock embeddings.
        """
        self._dimensions = dimensions
        self._counter = 0

    def _generate_deterministic_embedding(self, text: str) -> list[float]:
        """Generate a deterministic mock embedding based on text hash.

        Args:
            text: Input text.

        Returns:
            A deterministic embedding vector.
        """
        import hashlib

        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))
        embedding = np.random.randn(self._dimensions).tolist()
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = (np.array(embedding) / norm).tolist()
        return embedding

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate mock embeddings for texts.

        Args:
            texts: List of text strings.

        Returns:
            List of mock embedding vectors.
        """
        return [self._generate_deterministic_embedding(text) for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        """Generate mock embedding for a query.

        Args:
            text: Text to embed.

        Returns:
            Mock embedding vector.
        """
        return self._generate_deterministic_embedding(text)


def create_embedding_client(settings: Optional[Settings] = None) -> BaseEmbeddingClient:
    """Factory function to create an embedding client.

    Args:
        settings: Application settings. Uses global settings if not provided.

    Returns:
        An embedding client instance.
    """
    settings = settings or get_settings()
    if settings.llm_provider == "mock":
        return MockEmbeddingClient(dimensions=settings.embedding_dimensions)
    return LangChainEmbeddingClient(settings)
