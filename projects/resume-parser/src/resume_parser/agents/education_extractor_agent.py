"""EducationExtractorAgent - Extracts education history from resumes."""

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


class EducationExtractorAgent(BaseAgent):
    """Agent specialized in extracting education history from resume text.

    Identifies degrees, institutions, dates, GPA, and honors.
    """

    def __init__(self, llm_client: BaseLLMClient, settings: Settings) -> None:
        """Initialize the education extractor agent.

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
        return "EducationExtractorAgent"

    @property
    def description(self) -> str:
        """Get the agent description.

        Returns:
            str: Agent description.
        """
        return "Extracts education history including degrees, institutions, dates, and honors"

    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent.

        Returns:
            str: System prompt.
        """
        return (
            "You are an education extraction specialist. "
            "Extract all education entries from the resume text provided. "
            "For each entry, identify: institution, degree, field_of_study, "
            "location, start_date, end_date, gpa (on 4.0 scale), and honors. "
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
        return f"""Extract all education from this resume:

---
{text}
---

Return a JSON array of education objects."""

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse the LLM response into structured education data.

        Args:
            response: Raw LLM response.

        Returns:
            dict[str, Any]: Parsed education data.
        """
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(
                r"```(?:json)?\s*\n?(.*?)\n?\s*```", response, re.DOTALL
            )
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    data = []
            else:
                data = []

        # Ensure data is a list
        if isinstance(data, dict):
            data = data.get("education", [])
        if not isinstance(data, list):
            data = []

        # Normalize education objects
        normalized: list[dict[str, Any]] = []
        for item in data:
            if isinstance(item, dict):
                normalized.append(
                    {
                        "institution": item.get("institution", item.get("school", item.get("university", "Unknown"))),
                        "degree": item.get("degree", item.get("degree_type", "Unknown")),
                        "field_of_study": item.get("field_of_study", item.get("major")),
                        "location": item.get("location"),
                        "start_date": item.get("start_date"),
                        "end_date": item.get("end_date", item.get("graduation_date")),
                        "gpa": item.get("gpa"),
                        "honors": item.get("honors", item.get("awards", [])),
                    }
                )

        return {"education": normalized}
