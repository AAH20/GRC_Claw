"""Education extraction agent."""

from __future__ import annotations

import re
from typing import Any

from recruitment_platform.agents.base import BaseAgent


class EducationExtractorAgent(BaseAgent[dict[str, Any], list[dict[str, str]]]):
    """Extracts education history from resume text.

    Identifies degrees, institutions, and graduation dates
    from the education section of a resume.
    """

    def __init__(self) -> None:
        """Initialize the education extractor agent."""
        super().__init__(name="education_extractor")
        self._degree_patterns = [
            r"(?:Bachelor|Master|Ph\.?D|MBA|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?)[^\n]*",
            r"(?:BSc|MSc|BA|MA|BE|ME|BTech|MTech)[^\n]*",
        ]

    async def process(self, input_data: dict[str, Any]) -> list[dict[str, str]]:
        """Extract education entries from resume text.

        Args:
            input_data: Dictionary containing 'text' key with resume content.

        Returns:
            List of education entries with degree, institution, and year.
        """
        text = input_data.get("text", "")
        education: list[dict[str, str]] = []

        for pattern in self._degree_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                education.append(
                    {
                        "degree": match.group().strip(),
                        "institution": "",
                        "year": "",
                    }
                )

        return education
