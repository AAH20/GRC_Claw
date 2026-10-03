"""Contact information extraction agent."""

from __future__ import annotations

import re
from typing import Any

from recruitment_platform.agents.base import BaseAgent


class ContactExtractorAgent(BaseAgent[dict[str, Any], dict[str, str]]):
    """Extracts contact information from resume text.

    Uses regex patterns to identify email addresses, phone numbers,
    and LinkedIn profiles from unstructured resume text.
    """

    def __init__(self) -> None:
        """Initialize the contact extractor agent."""
        super().__init__(name="contact_extractor")
        self._email_pattern = re.compile(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        )
        self._phone_pattern = re.compile(
            r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"
        )
        self._linkedin_pattern = re.compile(
            r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+/?"
        )

    async def process(self, input_data: dict[str, Any]) -> dict[str, str]:
        """Extract contact information from resume text.

        Args:
            input_data: Dictionary containing 'text' key with resume content.

        Returns:
            Dictionary with extracted email, phone, and linkedin fields.
        """
        text = input_data.get("text", "")
        result: dict[str, str] = {}

        email_match = self._email_pattern.search(text)
        if email_match:
            result["email"] = email_match.group()

        phone_match = self._phone_pattern.search(text)
        if phone_match:
            result["phone"] = phone_match.group().strip()

        linkedin_match = self._linkedin_pattern.search(text)
        if linkedin_match:
            result["linkedin"] = linkedin_match.group()

        return result
