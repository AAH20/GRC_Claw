"""Vector store integration for semantic search."""

from __future__ import annotations

import logging
from typing import Any

from recruitment_platform.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class VectorStore(BaseIntegration):
    """Vector store for storing and searching embeddings.

    Provides persistent storage and similarity search
    for candidate and job embeddings.
    """

    def __init__(self, base_url: str, api_key: str = "") -> None:
        """Initialize the vector store.

        Args:
            base_url: Base URL for the vector store.
            api_key: API key for authentication.
        """
        super().__init__(base_url=base_url, api_key=api_key)

    async def upsert(self, collection: str, vectors: list[dict[str, Any]]) -> None:
        """Insert or update vectors in the store.

        Args:
            collection: Collection name.
            vectors: List of vector records with id, vector, and metadata.
        """
        await self.post(f"/collections/{collection}/upsert", json={"vectors": vectors})

    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors.

        Args:
            collection: Collection name.
            vector: Query vector.
            limit: Maximum results to return.

        Returns:
            List of matching records with scores.
        """
        response = await self.post(
            f"/collections/{collection}/search",
            json={"vector": vector, "limit": limit},
        )
        return response.json().get("results", [])

    async def delete(self, collection: str, ids: list[str]) -> None:
        """Delete vectors by ID.

        Args:
            collection: Collection name.
            ids: List of vector IDs to delete.
        """
        await self.post(f"/collections/{collection}/delete", json={"ids": ids})

    async def health_check(self) -> bool:
        """Check if the vector store is available.

        Returns:
            True if the service is healthy.
        """
        try:
            await self.get("/health")
            return True
        except Exception:
            return False
