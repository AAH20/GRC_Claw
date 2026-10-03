"""Skill extraction agent for assessments."""

from __future__ import annotations

from typing import Any

from recruitment_platform.agents.base import BaseAgent


class SkillExtractor(BaseAgent[dict[str, Any], list[str]]):
    """Extracts skills from assessment responses.

    Identifies demonstrated skills from candidate
    assessment answers and work samples.
    """

    def __init__(self) -> None:
        """Initialize the skill extractor."""
        super().__init__(name="skill_extractor")

    async def process(self, input_data: dict[str, Any]) -> list[str]:
        """Extract skills from assessment data.

        Args:
            input_data: Dictionary with 'responses' and 'work_samples'.

        Returns:
            List of identified skills.
        """
        return []
