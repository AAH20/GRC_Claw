"""Resolution Agent — Generates resolution suggestions and auto-replies."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

from customer_service.agents.base import BaseAgent

logger = structlog.get_logger(__name__)


class ResolutionResult(BaseModel):
    """Result of resolution generation."""

    suggestion: str = Field(..., description="Resolution suggestion")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    auto_reply: str | None = Field(None, description="Suggested auto-reply message")
    related_articles: list[str] = Field(default_factory=list, description="Related help articles")
    escalation_recommended: bool = Field(False, description="Whether escalation is recommended")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ResolutionAgent(BaseAgent):
    """Agent responsible for generating resolution suggestions for customer tickets.

    Analyzes ticket content and customer context to propose solutions,
    draft auto-replies, and recommend escalation when needed.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        auto_reply_enabled: bool = False,
        confidence_threshold: float = 0.85,
    ) -> None:
        """Initialize the Resolution Agent.

        Args:
            model: The LLM model to use.
            temperature: Sampling temperature for the LLM.
            auto_reply_enabled: Whether to generate auto-reply messages.
            confidence_threshold: Minimum confidence for auto-resolution.
        """
        super().__init__(name="resolution", model=model, temperature=temperature)
        self._auto_reply_enabled = auto_reply_enabled
        self._confidence_threshold = confidence_threshold

    async def run(
        self,
        ticket_content: str,
        triage_result: dict[str, Any] | None = None,
        customer_context: dict[str, Any] | None = None,
    ) -> ResolutionResult:
        """Generate a resolution suggestion for a customer ticket.

        Args:
            ticket_content: The content of the customer ticket.
            triage_result: Optional triage classification result.
            customer_context: Optional customer context information.

        Returns:
            ResolutionResult with resolution details.

        Raises:
            ValueError: If ticket_content is empty.
        """
        if not ticket_content or not ticket_content.strip():
            raise ValueError("Ticket content cannot be empty")

        logger.info("Generating resolution suggestion", ticket_length=len(ticket_content))

        prompt = self._build_prompt(ticket_content, triage_result, customer_context)
        response = await self._call_llm(prompt)

        result = self._parse_response(response)
        logger.info(
            "Resolution generated",
            confidence=result.confidence,
            escalation_recommended=result.escalation_recommended,
        )
        return result

    def _build_prompt(
        self,
        ticket_content: str,
        triage_result: dict[str, Any] | None,
        customer_context: dict[str, Any] | None,
    ) -> str:
        """Build the resolution prompt.

        Args:
            ticket_content: The ticket content.
            triage_result: Optional triage result.
            customer_context: Optional customer context.

        Returns:
            Formatted prompt string.
        """
        parts = [f"Ticket Content:\n{ticket_content}"]

        if triage_result:
            parts.append(f"Triage Classification: {triage_result}")
        if customer_context:
            parts.append(f"Customer Context: {customer_context}")

        auto_reply_instruction = ""
        if self._auto_reply_enabled:
            auto_reply_instruction = '\n"auto_reply": "<suggested auto-reply message or null>",'

        return f"""Generate a resolution suggestion for the following customer ticket.

{chr(10).join(parts)}

Respond in JSON format with the following structure:
{{
    "suggestion": "<resolution suggestion>",
    "confidence": <float between 0 and 1>,{auto_reply_instruction}
    "related_articles": ["<article_id>"],
    "escalation_recommended": <boolean>
}}"""

    def _parse_response(self, response: str) -> ResolutionResult:
        """Parse the LLM response into a ResolutionResult.

        Args:
            response: Raw LLM response string.

        Returns:
            Parsed ResolutionResult.

        Raises:
            ValueError: If the response cannot be parsed.
        """
        import json

        try:
            data = json.loads(response)
            return ResolutionResult(**data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("Failed to parse resolution response", error=str(e), response=response)
            raise ValueError(f"Failed to parse resolution response: {e}") from e
