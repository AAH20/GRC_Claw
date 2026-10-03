"""Storage integration for file and data persistence."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Storage:
    """File and data storage manager.

    Handles local and cloud storage for resumes,
    documents, and other recruitment files.
    """

    def __init__(self, base_path: str = "./storage") -> None:
        """Initialize storage.

        Args:
            base_path: Base directory for file storage.
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(__name__)

    async def save(self, file_data: bytes, filename: str, folder: str = "") -> str:
        """Save a file to storage.

        Args:
            file_data: File content as bytes.
            filename: Name of the file.
            folder: Optional subfolder.

        Returns:
            Path to the saved file.
        """
        target_dir = self.base_path / folder if folder else self.base_path
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / filename
        file_path.write_bytes(file_data)
        return str(file_path)

    async def load(self, file_path: str) -> bytes:
        """Load a file from storage.

        Args:
            file_path: Path to the file.

        Returns:
            File content as bytes.
        """
        return Path(file_path).read_bytes()

    async def delete(self, file_path: str) -> bool:
        """Delete a file from storage.

        Args:
            file_path: Path to the file.

        Returns:
            True if deleted successfully.
        """
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False

    async def list_files(self, folder: str = "") -> list[str]:
        """List files in a folder.

        Args:
            folder: Optional subfolder.

        Returns:
            List of file paths.
        """
        target_dir = self.base_path / folder if folder else self.base_path
        if not target_dir.exists():
            return []
        return [str(f) for f in target_dir.iterdir() if f.is_file()]
