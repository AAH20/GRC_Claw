"""Storage backend for persisting moderation results."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog

from content_moderation.models.schemas import ModerationResult

logger = structlog.get_logger(__name__)


class StorageBackend(ABC):
    """Abstract storage backend for moderation results."""

    @abstractmethod
    async def save(self, result: ModerationResult) -> None:
        """Save a moderation result.

        Args:
            result: Moderation result to persist.
        """
        ...

    @abstractmethod
    async def get(self, result_id: str) -> ModerationResult | None:
        """Retrieve a moderation result by ID.

        Args:
            result_id: Result identifier.

        Returns:
            Stored result or None if not found.
        """
        ...


class InMemoryStorage(StorageBackend):
    """In-memory storage backend for development and testing."""

    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self._store: dict[str, dict[str, Any]] = {}

    async def save(self, result: ModerationResult) -> None:
        """Save result to memory.

        Args:
            result: Moderation result to persist.
        """
        self._store[str(result.id)] = result.model_dump()
        logger.debug("Saved result to memory", result_id=str(result.id))

    async def get(self, result_id: str) -> ModerationResult | None:
        """Retrieve result from memory.

        Args:
            result_id: Result identifier.

        Returns:
            Stored result or None.
        """
        data = self._store.get(result_id)
        if data is None:
            return None
        return ModerationResult.model_validate(data)
