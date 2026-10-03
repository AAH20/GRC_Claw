"""Embedding client for semantic matching."""

from __future__ import annotations

import logging
from typing import Any

from recruitment_platform.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class EmbeddingClient(BaseIntegration):
    """Client for generating and comparing text embeddings.

    Used by semantic matching agents to compute
    similarity between candidates and job descriptions.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1") -> None:
        """Initialize the embedding client.

        Args:
            api_key: API key for the embedding service.
            base_url: Base URL for the API.
        """
        super().__init__(base_url=base_url, api_key=api_key)

    async def encode(self, texts: list[str]) -> list[list[float]]:
        """Encode texts into embedding vectors.

        Args:
            texts: List of texts to encode.

        Returns:
            List of embedding vectors.
        """
        response = await self.post(
            "/embeddings",
            json={"model": "text-embedding-ada-002", "input": texts},
        )
        data = response.json()
        return [item["embedding"] for item in data["data"]]

    async def similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts.

        Args:
            text1: First text.
            text2: Second text.

        Returns:
            Cosine similarity score.
        """
        import numpy as np

        embeddings = await self.encode([text1, text2])
        vec1 = np.array(embeddings[0])
        vec2 = np.array(embeddings[1])
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

    async def health_check(self) -> bool:
        """Check if the embedding service is available.

        Returns:
            True if the service is healthy.
        """
        try:
            await self.encode(["test"])
            return True
        except Exception:
            return False
