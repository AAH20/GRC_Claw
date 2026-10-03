"""Storage integrations for compliance data persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class Storage:
    """File-based storage for compliance data.

    Provides simple JSON file persistence for development and testing.
    Replace with database-backed storage for production use.
    """

    def __init__(self, data_dir: str = "./data") -> None:
        """Initialize storage with data directory.

        Args:
            data_dir: Directory for data files.
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, collection: str) -> Path:
        """Get file path for a collection.

        Args:
            collection: Collection name.

        Returns:
            File path for the collection.
        """
        return self.data_dir / f"{collection}.json"

    def save(self, collection: str, data: Any) -> None:
        """Save data to a collection.

        Args:
            collection: Collection name.
            data: Data to save.
        """
        file_path = self._get_file_path(collection)
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, default=str, indent=2)
            logger.info("Data saved", collection=collection)
        except Exception as exc:
            logger.error("Failed to save data", collection=collection, error=str(exc))
            raise

    def load(self, collection: str) -> Any | None:
        """Load data from a collection.

        Args:
            collection: Collection name.

        Returns:
            Loaded data or None if not found.
        """
        file_path = self._get_file_path(collection)
        if not file_path.exists():
            return None
        try:
            with open(file_path) as f:
                return json.load(f)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load data", collection=collection, error=str(exc))
            return None

    def append(self, collection: str, item: Any) -> None:
        """Append an item to a collection.

        Args:
            collection: Collection name.
            item: Item to append.
        """
        existing = self.load(collection) or []
        if not isinstance(existing, list):
            existing = [existing]
        existing.append(item)
        self.save(collection, existing)

    def clear(self, collection: str) -> None:
        """Clear a collection.

        Args:
            collection: Collection name.
        """
        file_path = self._get_file_path(collection)
        if file_path.exists():
            file_path.unlink()
            logger.info("Collection cleared", collection=collection)
