"""Vector store integration for candidate and job embeddings."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from candidate_matcher.config.exceptions import VectorStoreError
from candidate_matcher.config.logging_config import get_logger
from candidate_matcher.config.settings import Settings, get_settings

logger = get_logger(__name__)


class BaseVectorStore(ABC):
    """Abstract base class for vector store clients."""

    @abstractmethod
    async def upsert(
        self,
        collection: str,
        id: str,
        vector: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Insert or update a vector in the store.

        Args:
            collection: Collection name.
            id: Unique identifier for the vector.
            vector: Embedding vector.
            metadata: Associated metadata.
        """
        ...

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors.

        Args:
            collection: Collection name.
            query_vector: Query embedding vector.
            top_k: Number of results to return.
            filters: Optional metadata filters.

        Returns:
            List of matching vectors with scores and metadata.
        """
        ...

    @abstractmethod
    async def delete(self, collection: str, id: str) -> None:
        """Delete a vector from the store.

        Args:
            collection: Collection name.
            id: Vector identifier to delete.
        """
        ...


class InMemoryVectorStore(BaseVectorStore):
    """In-memory vector store for development and testing."""

    def __init__(self) -> None:
        """Initialize the in-memory store."""
        self._collections: dict[str, dict[str, dict[str, Any]]] = {}

    async def upsert(
        self,
        collection: str,
        id: str,
        vector: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Insert or update a vector.

        Args:
            collection: Collection name.
            id: Unique identifier.
            vector: Embedding vector.
            metadata: Associated metadata.
        """
        if collection not in self._collections:
            self._collections[collection] = {}
        self._collections[collection][id] = {
            "id": id,
            "vector": vector,
            "metadata": metadata,
        }

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors using cosine similarity.

        Args:
            collection: Collection name.
            query_vector: Query embedding vector.
            top_k: Number of results.
            filters: Optional metadata filters.

        Returns:
            List of matching vectors with scores.
        """
        import numpy as np

        if collection not in self._collections:
            return []

        query_arr = np.array(query_vector)
        results: list[dict[str, Any]] = []

        for item in self._collections[collection].values():
            if filters:
                match = all(
                    item["metadata"].get(k) == v for k, v in filters.items()
                )
                if not match:
                    continue

            vec_arr = np.array(item["vector"])
            similarity = float(
                np.dot(query_arr, vec_arr)
                / (np.linalg.norm(query_arr) * np.linalg.norm(vec_arr) + 1e-10)
            )
            results.append({
                "id": item["id"],
                "score": similarity,
                "metadata": item["metadata"],
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def delete(self, collection: str, id: str) -> None:
        """Delete a vector.

        Args:
            collection: Collection name.
            id: Vector identifier.
        """
        if collection in self._collections:
            self._collections[collection].pop(id, None)

    async def clear(self) -> None:
        """Clear all collections."""
        self._collections.clear()


class QdrantVectorStore(BaseVectorStore):
    """Qdrant vector store client."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the Qdrant client.

        Args:
            settings: Application settings.
        """
        self._settings = settings or get_settings()
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create the Qdrant client.

        Returns:
            Qdrant client instance.

        Raises:
            VectorStoreError: If client creation fails.
        """
        if self._client is None:
            try:
                from qdrant_client import QdrantClient

                self._client = QdrantClient(url=self._settings.vector_store_url)
            except Exception as e:
                raise VectorStoreError(f"Failed to create Qdrant client: {e}") from e
        return self._client

    async def upsert(
        self,
        collection: str,
        id: str,
        vector: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Insert or update a vector in Qdrant.

        Args:
            collection: Collection name.
            id: Unique identifier.
            vector: Embedding vector.
            metadata: Associated metadata.
        """
        try:
            client = self._get_client()
            client.upsert(
                collection_name=collection,
                points=[{"id": id, "vector": vector, "payload": metadata}],
            )
        except Exception as e:
            logger.error("qdrant_upsert_failed", error=str(e))
            raise VectorStoreError(f"Qdrant upsert failed: {e}") from e

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors in Qdrant.

        Args:
            collection: Collection name.
            query_vector: Query embedding vector.
            top_k: Number of results.
            filters: Optional metadata filters.

        Returns:
            List of matching vectors with scores.
        """
        try:
            client = self._get_client()
            results = client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=top_k,
                query_filter=filters,
            )
            return [
                {
                    "id": str(r.id),
                    "score": r.score,
                    "metadata": r.payload or {},
                }
                for r in results
            ]
        except Exception as e:
            logger.error("qdrant_search_failed", error=str(e))
            raise VectorStoreError(f"Qdrant search failed: {e}") from e

    async def delete(self, collection: str, id: str) -> None:
        """Delete a vector from Qdrant.

        Args:
            collection: Collection name.
            id: Vector identifier.
        """
        try:
            client = self._get_client()
            client.delete(collection_name=collection, points_selector=[id])
        except Exception as e:
            logger.error("qdrant_delete_failed", error=str(e))
            raise VectorStoreError(f"Qdrant delete failed: {e}") from e


def create_vector_store(settings: Settings | None = None) -> BaseVectorStore:
    """Factory function to create a vector store client.

    Args:
        settings: Application settings. Uses global settings if not provided.

    Returns:
        A vector store client instance.
    """
    settings = settings or get_settings()
    if settings.environment == "development" and settings.llm_provider == "mock":
        return InMemoryVectorStore()
    return QdrantVectorStore(settings)
