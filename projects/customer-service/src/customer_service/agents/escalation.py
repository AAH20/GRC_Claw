"""Escalation Agent — Routes complex cases to human agents with context."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

from customer_service.agents.base import BaseAgent

logger = structlog.get_logger(__name__)


class EscalationResult(BaseModel):
    """Result of escalation evaluation."""

    should_escalate: bool = Field(..., description="Whether the ticket should be escalated")
    reason: str = Field(..., description="Reason for escalation")
    urgency: str = Field(..., description="Urgency level of escalation")
    assigned_team: str = Field(..., description="Team to escalate to")
    context_summary: str = Field(..., description="Summary of ticket context for human agent")
    customer_impact: str = Field(..., description="Description of customer impact")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EscalationAgent(BaseAgent):
    """Agent responsible for determining when and how to escalate tickets to human agents.

    Evaluates ticket complexity, customer sentiment, and business impact to
    make escalation decisions with full context preservation.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.1,
        escalation_threshold: float = 0.7,
    ) -> None:
        """Initialize the Escalation Agent.

        Args:
            model: The LLM model to use.
            temperature: Sampling temperature for the LLM.
            escalation_threshold: Confidence threshold for escalation.
        """
        super().__init__(name="escalation", model=model, temperature=temperature)
        self._escalation_threshold = escalation_threshold

    async def run(
        self,
        ticket_content: str,
        triage_result: dict[str, Any] | None = None,
        sentiment_result: dict[str, Any] | None = None,
        customer_context: dict[str, Any] | None = None,
    ) -> EscalationResult:
        """Evaluate whether a ticket should be escalated to a human agent.

        Args:
            ticket_content: The content of the customer ticket.
            triage_result: Optional triage classification result.
            sentiment_result: Optional sentiment analysis result.
            customer_context: Optional customer context information.

        Returns:
            EscalationResult with escalation decision and context.

        Raises:
            ValueError: If ticket_content is empty.
        """
        if not ticket_content or not ticket_content.strip():
            raise ValueError("Ticket content cannot be empty")

        logger.info("Evaluating escalation need", ticket_length=len(ticket_content))

        prompt = self._build_prompt(
            ticket_content, triage_result, sentiment_result, customer_context
        )
        response = await self._call_llm(prompt)

        result = self._parse_response(response)
        logger.info(
            "Escalation evaluation complete",
            should_escalate=result.should_escalate,
            urgency=result.urgency,
        )
        return result

    def _build_prompt(
        self,
        ticket_content: str,
        triage_result: dict[str, Any] | None,
        sentiment_result: dict[str, Any] | None,
        customer_context: dict[str, Any] | None,
    ) -> str:
        """Build the escalation evaluation prompt.

        Args:
            ticket_content: The ticket content.
            triage_result: Optional triage result.
            sentiment_result: Optional sentiment result.
            customer_context: Optional customer context.

        Returns:
            Formatted prompt string.
        """
        parts = [f"Ticket Content:\n{ticket_content}"]

        if triage_result:
            parts.append(f"Triage Classification: {triage_result}")
        if sentiment_result:
            parts.append(f"Sentiment Analysis: {sentiment_result}")
        if customer_context:
            parts.append(f"Customer Context: {customer_context}")

        return f"""Evaluate whether the following ticket should be escalated to a human agent.


{chr(10).join(parts)}

Consider:
- Complexity of the issue
- Customer sentiment and frustration level
- Business impact and potential revenue risk
- SLA breach risk
- Whether automated resolution is likely to succeed

Respond in JSON format with the following structure:
{{
    "should_escalate": <boolean>,
    "reason": "<reason for escalation>",
    "urgency": "<low|medium|high|critical>",
    "assigned_team": "<team name>",
    "context_summary": "<summary for human agent>",
    "customer_impact": "<description of customer impact>"
}}"""

    def _parse_response(self, response: str) -> EscalationResult:
        """Parse the LLM response into an EscalationResult.

        Args:
            response: Raw LLM response string.

        Returns:
            Parsed EscalationResult.

        Raises:
            ValueError: If the response cannot be parsed.
        """
        import json

        try:
            data = json.loads(response)
            return EscalationResult(**data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("Failed to parse escalation response", error=str(e), response=response)
            raise ValueError(f"Failed to parse escalation response: {e}") from e
