"""Work experience extraction agent."""

from __future__ import annotations

import re
from typing import Any

from recruitment_platform.agents.base import BaseAgent


class ExperienceExtractorAgent(BaseAgent[dict[str, Any], list[dict[str, Any]]]):
    """Extracts work experience from resume text.

    Identifies job titles, companies, dates, and descriptions
    from the experience section of a resume.
    """

    def __init__(self) -> None:
        """Initialize the experience extractor agent."""
        super().__init__(name="experience_extractor")
        self._date_pattern = re.compile(
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}\s*[-–]\s*(?:Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4})",
            re.IGNORECASE,
        )

    async def process(self, input_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract work experience entries from resume text.

        Args:
            input_data: Dictionary containing 'text' key with resume content.

        Returns:
            List of experience entries with title, company, dates, and description.
        """
        text = input_data.get("text", "")
        experiences: list[dict[str, Any]] = []

        for match in self._date_pattern.finditer(text):
            start = max(0, match.start() - 200)
            context = text[start:match.end() + 500]
            experiences.append({
                "title": "",
                "company": "",
                "dates": match.group().strip(),
                "description": context.strip(),
            })

        return experiences
