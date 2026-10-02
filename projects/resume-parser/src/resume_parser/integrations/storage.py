"""Storage backends for parsed resumes."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import structlog

from resume_parser.models import ParsedResume

logger = structlog.get_logger(__name__)


class BaseStorage(ABC):
    """Abstract base class for resume storage backends."""

    @abstractmethod
    async def save(self, resume: ParsedResume) -> None:
        """Save a parsed resume.

        Args:
            resume: The parsed resume to save.
        """
        ...

    @abstractmethod
    async def get(self, resume_id: str) -> ParsedResume | None:
        """Retrieve a parsed resume by ID.

        Args:
            resume_id: The resume identifier.

        Returns:
            ParsedResume | None: The parsed resume or None if not found.
        """
        ...

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[ParsedResume]:
        """List all parsed resumes.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            list[ParsedResume]: List of parsed resumes.
        """
        ...

    @abstractmethod
    async def delete(self, resume_id: str) -> bool:
        """Delete a parsed resume.

        Args:
            resume_id: The resume identifier.

        Returns:
            bool: True if deleted, False if not found.
        """
        ...

    @abstractmethod
    async def exists(self, resume_id: str) -> bool:
        """Check if a resume exists.

        Args:
            resume_id: The resume identifier.

        Returns:
            bool: True if exists.
        """
        ...


class LocalFileStorage(BaseStorage):
    """Local filesystem storage backend."""

    def __init__(self, base_path: Path) -> None:
        """Initialize local file storage.

        Args:
            base_path: Base directory for storing resumes.
        """
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, resume_id: str) -> Path:
        """Get the file path for a resume ID.

        Args:
            resume_id: The resume identifier.

        Returns:
            Path: File path.
        """
        return self._base_path / f"{resume_id}.json"

    async def save(self, resume: ParsedResume) -> None:
        """Save a parsed resume to local file.

        Args:
            resume: The parsed resume to save.
        """
        file_path = self._get_file_path(resume.id)
        data = resume.model_dump(mode="json")
        file_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.info("resume_saved", resume_id=resume.id, path=str(file_path))

    async def get(self, resume_id: str) -> ParsedResume | None:
        """Retrieve a parsed resume from local file.

        Args:
            resume_id: The resume identifier.

        Returns:
            ParsedResume | None: The parsed resume or None if not found.
        """
        file_path = self._get_file_path(resume_id)
        if not file_path.exists():
            return None
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return ParsedResume.model_validate(data)

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[ParsedResume]:
        """List all parsed resumes from local storage.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            list[ParsedResume]: List of parsed resumes.
        """
        files = sorted(self._base_path.glob("*.json"))
        results: list[ParsedResume] = []
        for f in files[offset : offset + limit]:
            data = json.loads(f.read_text(encoding="utf-8"))
            results.append(ParsedResume.model_validate(data))
        return results

    async def delete(self, resume_id: str) -> bool:
        """Delete a parsed resume from local storage.

        Args:
            resume_id: The resume identifier.

        Returns:
            bool: True if deleted, False if not found.
        """
        file_path = self._get_file_path(resume_id)
        if not file_path.exists():
            return False
        file_path.unlink()
        logger.info("resume_deleted", resume_id=resume_id)
        return True

    async def exists(self, resume_id: str) -> bool:
        """Check if a resume exists in local storage.

        Args:
            resume_id: The resume identifier.

        Returns:
            bool: True if exists.
        """
        return self._get_file_path(resume_id).exists()


class InMemoryStorage(BaseStorage):
    """In-memory storage backend for testing."""

    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self._storage: dict[str, ParsedResume] = {}

    async def save(self, resume: ParsedResume) -> None:
        """Save a parsed resume in memory.

        Args:
            resume: The parsed resume to save.
        """
        self._storage[resume.id] = resume

    async def get(self, resume_id: str) -> ParsedResume | None:
        """Retrieve a parsed resume from memory.

        Args:
            resume_id: The resume identifier.

        Returns:
            ParsedResume | None: The parsed resume or None if not found.
        """
        return self._storage.get(resume_id)

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[ParsedResume]:
        """List all parsed resumes from memory.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            list[ParsedResume]: List of parsed resumes.
        """
        items = list(self._storage.values())
        return items[offset : offset + limit]

    async def delete(self, resume_id: str) -> bool:
        """Delete a parsed resume from memory.

        Args:
            resume_id: The resume identifier.

        Returns:
            bool: True if deleted, False if not found.
        """
        if resume_id not in self._storage:
            return False
        del self._storage[resume_id]
        return True

    async def exists(self, resume_id: str) -> bool:
        """Check if a resume exists in memory.

        Args:
            resume_id: The resume identifier.

        Returns:
            bool: True if exists.
        """
        return resume_id in self._storage

    def clear(self) -> None:
        """Clear all stored resumes."""
        self._storage.clear()


def create_storage(backend: str, path: Path | None = None) -> BaseStorage:
    """Factory function to create a storage backend.

    Args:
        backend: Storage backend type ('local' or 'memory').
        path: Base path for local storage.

    Returns:
        BaseStorage: Configured storage backend.

    Raises:
        ValueError: If backend type is not supported.
    """
    if backend == "local":
        return LocalFileStorage(path or Path("./data/resumes"))
    elif backend == "memory":
        return InMemoryStorage()
    else:
        raise ValueError(f"Unsupported storage backend: {backend}")
