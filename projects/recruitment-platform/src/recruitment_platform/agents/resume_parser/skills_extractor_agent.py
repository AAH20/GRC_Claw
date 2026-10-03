"""Skills extraction agent."""

from __future__ import annotations

import re
from typing import Any

from recruitment_platform.agents.base import BaseAgent


class SkillsExtractorAgent(BaseAgent[dict[str, Any], list[str]]):
    """Extracts skills from resume text.

    Matches text against a comprehensive skill taxonomy
    to identify technical and soft skills.
    """

    def __init__(self) -> None:
        """Initialize the skills extractor agent."""
        super().__init__(name="skills_extractor")
        self._skill_keywords = {
            "python",
            "java",
            "javascript",
            "typescript",
            "go",
            "rust",
            "sql",
            "nosql",
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "machine learning",
            "deep learning",
            "nlp",
            "computer vision",
            "react",
            "angular",
            "vue",
            "node",
            "django",
            "flask",
            "fastapi",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "elasticsearch",
            "git",
            "ci/cd",
            "terraform",
            "ansible",
            "linux",
        }

    async def process(self, input_data: dict[str, Any]) -> list[str]:
        """Extract skills from resume text.

        Args:
            input_data: Dictionary containing 'text' key with resume content.

        Returns:
            List of identified skills.
        """
        text = input_data.get("text", "").lower()
        found_skills: list[str] = []

        for skill in self._skill_keywords:
            if re.search(rf"\b{re.escape(skill)}\b", text):
                found_skills.append(skill)

        return found_skills
