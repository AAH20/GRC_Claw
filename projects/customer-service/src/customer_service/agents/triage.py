"""Triage Agent — Classifies incoming tickets by urgency, category, and intent."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

from customer_service.agents.base import BaseAgent

logger = structlog.get_logger(__name__)


class TriageResult(BaseModel):
    """Result of triage classification."""

    category: str = Field(..., description="Ticket category")
    priority: str = Field(..., description="Priority level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    intent: str = Field(..., description="Detected customer intent")
    summary: str = Field(..., description="Brief summary of the ticket")
    suggested_team: str = Field(..., description="Suggested team for routing")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TriageAgent(BaseAgent):
    """Agent responsible for classifying and routing incoming customer tickets.

    Uses LLM-based classification to determine ticket category, priority,
    and appropriate routing destination.
    """

    def __init__(self, model: str = "gpt-4o", temperature: float = 0.1) -> None:
        """Initialize the Triage Agent.

        Args:
            model: The LLM model to use for classification.
            temperature: Sampling temperature for the LLM.
        """
        super().__init__(name="triage", model=model, temperature=temperature)
        self._categories = ["billing", "technical", "account", "general", "complaint"]
        self._priority_levels = ["low", "medium", "high", "critical"]

    async def run(
        self, ticket_content: str, customer_context: dict[str, Any] | None = None
    ) -> TriageResult:
        """Classify a customer ticket.

        Args:
            ticket_content: The content of the customer ticket.
            customer_context: Optional customer context information.

        Returns:
            TriageResult with classification details.

        Raises:
            ValueError: If ticket_content is empty.
        """
        if not ticket_content or not ticket_content.strip():
            raise ValueError("Ticket content cannot be empty")

        logger.info("Running triage classification", ticket_length=len(ticket_content))

        prompt = self._build_prompt(ticket_content, customer_context)
        response = await self._call_llm(prompt)

        result = self._parse_response(response)
        logger.info(
            "Triage classification complete",
            category=result.category,
            priority=result.priority,
            confidence=result.confidence,
        )
        return result

    def _build_prompt(self, ticket_content: str, customer_context: dict[str, Any] | None) -> str:
        """Build the classification prompt.

        Args:
            ticket_content: The ticket content to classify.
            customer_context: Optional customer context.

        Returns:
            Formatted prompt string.
        """
        context_str = ""
        if customer_context:
            context_str = f"\nCustomer Context: {customer_context}"

        return f"""Classify the following ticket into the appropriate category and priority.


Categories: {', '.join(self._categories)}
Priority Levels: {', '.join(self._priority_levels)}

Ticket Content:
{ticket_content}
{context_str}

Respond in JSON format with the following structure:
{{
    "category": "<category>",
    "priority": "<priority>",
    "confidence": <float between 0 and 1>,
    "intent": "<detected intent>",
    "summary": "<brief summary>",
    "suggested_team": "<suggested team>"
}}"""

    def _parse_response(self, response: str) -> TriageResult:
        """Parse the LLM response into a TriageResult.

        Args:
            response: Raw LLM response string.

        Returns:
            Parsed TriageResult.

        Raises:
            ValueError: If the response cannot be parsed.
        """
        import json

        try:
            data = json.loads(response)
            return TriageResult(**data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("Failed to parse triage response", error=str(e), response=response)
            raise ValueError(f"Failed to parse triage response: {e}") from e
