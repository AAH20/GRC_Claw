"""ExperienceExtractorAgent - Extracts work experience from resumes."""

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


class ExperienceExtractorAgent(BaseAgent):
    """Agent specialized in extracting work experience from resume text.

    Identifies job positions, companies, dates, and achievements.
    """

    def __init__(self, llm_client: BaseLLMClient, settings: Settings) -> None:
        """Initialize the experience extractor agent.

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
        return "ExperienceExtractorAgent"

    @property
    def description(self) -> str:
        """Get the agent description.

        Returns:
            str: Agent description.
        """
        return "Extracts work experience including companies, titles, dates, and achievements"

    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent.

        Returns:
            str: System prompt.
        """
        return (
            "You are a work experience extraction specialist. "
            "Extract all work experience from the resume text provided. "
            "For each position, identify: company, title, location, start_date, "
            "end_date, is_current (true if this is the current position), "
            "description, and achievements (list of key accomplishments). "
            "Return the result as a JSON array of objects."
        )

    def _build_user_prompt(self, text: str, **kwargs: Any) -> str:
        """Build the user prompt for this agent.

        Args:
            text: Resume text to analyze.
            **kwargs: Additional context.

        Returns:
            str: User prompt.
        """
        return f"""Extract all work experience from this resume:

---
{text}
---

Return a JSON array of experience objects."""

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse the LLM response into structured experience data.

        Args:
            response: Raw LLM response.

        Returns:
            dict[str, Any]: Parsed experience data.
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
            data = data.get("experience", [])
        if not isinstance(data, list):
            data = []

        # Normalize experience objects
        normalized: list[dict[str, Any]] = []
        for item in data:
            if isinstance(item, dict):
                normalized.append(
                    {
                        "company": item.get("company", item.get("employer", "Unknown")),
                        "title": item.get("title", item.get("position", item.get("role", "Unknown"))),
                        "location": item.get("location"),
                        "start_date": item.get("start_date"),
                        "end_date": item.get("end_date"),
                        "is_current": item.get("is_current", False),
                        "description": item.get("description", item.get("summary")),
                        "achievements": item.get("achievements", item.get("accomplishments", [])),
                    }
                )

        return {"experience": normalized}
