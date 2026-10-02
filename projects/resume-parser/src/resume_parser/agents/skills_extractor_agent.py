"""SkillsExtractorAgent - Extracts skills from resumes."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

import structlog

from resume_parser.agents.base import BaseAgent

if TYPE_CHECKING:
    from resume_parser.config import Settings
    from resume_parser.integrations import BaseLLMClient

logger = structlog.get_logger(__name__)


class SkillsExtractorAgent(BaseAgent):
    """Agent specialized in extracting skills from resume text.

    Identifies technical skills, soft skills, languages, and tools
    with proficiency levels and years of experience.
    """

    def __init__(self, llm_client: BaseLLMClient, settings: Settings) -> None:
        """Initialize the skills extractor agent.

        Args:
            llm_client: LLM client for generating responses.
            settings: Application settings.
        """
        super().__init__(llm_client, settings)

    @property
    def name(self) -> str:
        """Get the agent name.

        Returns:
            str: Agent name.
        """
        return "SkillsExtractorAgent"

    @property
    def description(self) -> str:
        """Get the agent description.

        Returns:
            str: Agent description.
        """
        return "Extracts technical skills, soft skills, languages, and tools with proficiency levels"

    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent.

        Returns:
            str: System prompt.
        """
        return (
            "You are a skills extraction specialist. "
            "Extract all skills from the resume text provided. "
            "Categorize each skill as one of: technical, soft, language, tool, other. "
            "For each skill, estimate proficiency (beginner, intermediate, advanced, expert) "
            "and years of experience if mentioned. "
            "Return the result as a JSON array of objects with fields: "
            "name, category, proficiency, years_experience."
        )

    def _build_user_prompt(self, text: str, **kwargs: Any) -> str:
        """Build the user prompt for this agent.

        Args:
            text: Resume text to analyze.
            **kwargs: Additional context.

        Returns:
            str: User prompt.
        """
        return f"""Extract all skills from this resume:

---
{text}
---

Return a JSON array of skill objects."""

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse the LLM response into structured skills data.

        Args:
            response: Raw LLM response.

        Returns:
            dict[str, Any]: Parsed skills data.
        """
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    data = []
            else:
                data = []

        # Ensure data is a list
        if isinstance(data, dict):
            data = data.get("skills", [])
        if not isinstance(data, list):
            data = []

        # Normalize skill objects
        normalized: list[dict[str, Any]] = []
        for item in data:
            if isinstance(item, str):
                normalized.append({"name": item, "category": "other"})
            elif isinstance(item, dict):
                normalized.append(
                    {
                        "name": item.get("name", item.get("skill", "Unknown")),
                        "category": item.get("category", "other"),
                        "proficiency": item.get("proficiency"),
                        "years_experience": item.get("years_experience"),
                    }
                )

        return {"skills": normalized}
