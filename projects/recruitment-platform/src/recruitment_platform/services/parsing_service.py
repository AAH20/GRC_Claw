"""Resume parsing service."""

from __future__ import annotations

import logging
from typing import Any

from recruitment_platform.agents.resume_parser.resume_parser_agent import ResumeParserAgent

logger = logging.getLogger(__name__)


class ParsingService:
    """Service for parsing resumes.

    Orchestrates the resume parsing pipeline and provides
    a high-level interface for resume processing.
    """

    def __init__(self) -> None:
        """Initialize the parsing service."""
        self._parser = ResumeParserAgent()
        self._logger = logging.getLogger(__name__)

    async def parse(self, text: str) -> dict[str, Any]:
        """Parse resume text into structured data.

        Args:
            text: Raw resume text.

        Returns:
            Structured resume data.
        """
        return await self._parser.process({"text": text})

    async def parse_file(self, file_path: str) -> dict[str, Any]:
        """Parse a resume file.

        Args:
            file_path: Path to the resume file.

        Returns:
            Structured resume data.
        """
        from recruitment_platform.integrations.file_parsers import FileParser

        parser = FileParser()
        text = await parser.parse(file_path)
        return await self.parse(text)
