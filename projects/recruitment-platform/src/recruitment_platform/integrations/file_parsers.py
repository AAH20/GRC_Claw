"""File parsing integrations for resume processing."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FileParser:
    """Parse various file formats into text.

    Supports PDF, DOCX, TXT, and other common formats.
    """

    def __init__(self) -> None:
        """Initialize the file parser."""
        self._logger = logging.getLogger(__name__)

    async def parse(self, file_path: str) -> str:
        """Parse a file and extract text content.

        Args:
            file_path: Path to the file to parse.

        Returns:
            Extracted text content.

        Raises:
            ValueError: If the file format is not supported.
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return await self._parse_pdf(path)
        elif suffix == ".docx":
            return await self._parse_docx(path)
        elif suffix == ".txt":
            return await self._parse_txt(path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    async def _parse_pdf(self, path: Path) -> str:
        """Parse a PDF file.

        Args:
            path: Path to the PDF file.

        Returns:
            Extracted text.
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(path))
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            self._logger.warning("PyMuPDF not installed, using fallback")
            return ""

    async def _parse_docx(self, path: Path) -> str:
        """Parse a DOCX file.

        Args:
            path: Path to the DOCX file.

        Returns:
            Extracted text.
        """
        try:
            from docx import Document

            doc = Document(str(path))
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            self._logger.warning("python-docx not installed, using fallback")
            return ""

    async def _parse_txt(self, path: Path) -> str:
        """Parse a plain text file.

        Args:
            path: Path to the text file.

        Returns:
            File content.
        """
        return path.read_text(encoding="utf-8")
