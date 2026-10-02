"""ContactExtractorAgent - Extracts contact information from resumes."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

import structlog

from resume_parser.agents.base import BaseAgent
from resume_parser.utils.text_processing import extract_emails, extract_phone_numbers, extract_urls

if TYPE_CHECKING:
    from resume_parser.config import Settings
    from resume_parser.integrations import BaseLLMClient

logger = structlog.get_logger(__name__)


class ContactExtractorAgent(BaseAgent):
    """Agent specialized in extracting contact information from resume text.

    Uses both LLM analysis and regex-based extraction for robust results.
    """

    def __init__(self, llm_client: BaseLLMClient, settings: Settings) -> None:
        """Initialize the contact extractor agent.

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
        return "ContactExtractorAgent"

    @property
    def description(self) -> str:
        """Get the agent description.

        Returns:
            str: Agent description.
        """
        return "Extracts contact information including name, email, phone, address, and social links"

    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent.

        Returns:
            str: System prompt.
        """
        return (
            "You are a contact information extraction specialist. "
            "Extract all contact details from the resume text provided. "
            "Return the result as a JSON object with these fields: "
            "full_name, email, phone, address, linkedin, github, website, summary. "
            "Use null for any field that cannot be found."
        )

    def _build_user_prompt(self, text: str, **kwargs: Any) -> str:
        """Build the user prompt for this agent.

        Args:
            text: Resume text to analyze.
            **kwargs: Additional context.

        Returns:
            str: User prompt.
        """
        return f"""Extract contact information from this resume:

---
{text}
---

Return a JSON object with contact details."""

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse the LLM response into structured contact data.

        Args:
            response: Raw LLM response.

        Returns:
            dict[str, Any]: Parsed contact information.
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
                    data = {}
            else:
                data = {}

        # Supplement with regex extraction
        emails = extract_emails(response)
        phones = extract_phone_numbers(response)
        urls = extract_urls(response)

        if not data.get("email") and emails:
            data["email"] = emails[0]
        if not data.get("phone") and phones:
            data["phone"] = phones[0]
        if not data.get("linkedin"):
            linkedin_urls = [u for u in urls if "linkedin.com" in u.lower()]
            if linkedin_urls:
                data["linkedin"] = linkedin_urls[0]
        if not data.get("github"):
            github_urls = [u for u in urls if "github.com" in u.lower()]
            if github_urls:
                data["github"] = github_urls[0]
        if not data.get("website"):
            other_urls = [
                u for u in urls
                if "linkedin.com" not in u.lower() and "github.com" not in u.lower()
            ]
            if other_urls:
                data["website"] = other_urls[0]

        return data
