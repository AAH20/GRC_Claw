"""Customer Success Agent — Proactive outreach and retention risk detection."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

from customer_service.agents.base import BaseAgent

logger = structlog.get_logger(__name__)


class CustomerSuccessResult(BaseModel):
    """Result of customer success analysis."""

    health_score: float = Field(..., ge=0.0, le=100.0, description="Customer health score")
    churn_risk: str = Field(..., description="Churn risk level")
    recommended_actions: list[str] = Field(
        default_factory=list, description="Recommended proactive actions"
    )
    outreach_message: str | None = Field(None, description="Suggested outreach message")
    engagement_level: str = Field(..., description="Customer engagement level")
    satisfaction_trend: str = Field(..., description="Satisfaction trend direction")
    expansion_opportunity: bool = Field(
        False, description="Whether there is an expansion opportunity"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CustomerSuccessAgent(BaseAgent):
    """Agent responsible for proactive customer success and retention.

    Analyzes customer health, detects churn risks, and recommends
    proactive outreach actions to improve retention.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        churn_risk_threshold: float = 0.6,
    ) -> None:
        """Initialize the Customer Success Agent.

        Args:
            model: The LLM model to use.
            temperature: Sampling temperature for the LLM.
            churn_risk_threshold: Threshold for churn risk alerts.
        """
        super().__init__(name="customer_success", model=model, temperature=temperature)
        self._churn_risk_threshold = churn_risk_threshold

    async def run(
        self,
        customer_id: str,
        customer_data: dict[str, Any],
        interaction_history: list[dict[str, Any]] | None = None,
        usage_data: dict[str, Any] | None = None,
    ) -> CustomerSuccessResult:
        """Analyze customer health and recommend success actions.

        Args:
            customer_id: Unique customer identifier.
            customer_data: Customer profile and account data.
            interaction_history: Optional list of customer interactions.
            usage_data: Optional product usage data.

        Returns:
            CustomerSuccessResult with health analysis and recommendations.

        Raises:
            ValueError: If customer_id is empty.
        """
        if not customer_id or not customer_id.strip():
            raise ValueError("Customer ID cannot be empty")

        logger.info("Analyzing customer success", customer_id=customer_id)

        prompt = self._build_prompt(customer_data, interaction_history, usage_data)
        response = await self._call_llm(prompt)

        result = self._parse_response(response)
        logger.info(
            "Customer success analysis complete",
            customer_id=customer_id,
            health_score=result.health_score,
            churn_risk=result.churn_risk,
        )
        return result

    def _build_prompt(
        self,
        customer_data: dict[str, Any],
        interaction_history: list[dict[str, Any]] | None,
        usage_data: dict[str, Any] | None,
    ) -> str:
        """Build the customer success analysis prompt.

        Args:
            customer_data: Customer profile data.
            interaction_history: Optional interaction history.
            usage_data: Optional usage data.

        Returns:
            Formatted prompt string.
        """
        parts = [f"Customer Data: {customer_data}"]

        if interaction_history:
            parts.append(f"Interaction History: {interaction_history}")
        if usage_data:
            parts.append(f"Usage Data: {usage_data}")

        return f"""Analyze the following customer's health and recommend proactive success actions.

{chr(10).join(parts)}

Respond in JSON format with the following structure:
{{
    "health_score": <float between 0 and 100>,
    "churn_risk": "<none|low|medium|high|critical>",
    "recommended_actions": ["<action>"],
    "outreach_message": "<suggested outreach message or null>",
    "engagement_level": "<very_high|high|medium|low|very_low>",
    "satisfaction_trend": "<improving|stable|declining>",
    "expansion_opportunity": <boolean>
}}"""

    def _parse_response(self, response: str) -> CustomerSuccessResult:
        """Parse the LLM response into a CustomerSuccessResult.

        Args:
            response: Raw LLM response string.

        Returns:
            Parsed CustomerSuccessResult.

        Raises:
            ValueError: If the response cannot be parsed.
        """
        import json

        try:
            data = json.loads(response)
            return CustomerSuccessResult(**data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(
                "Failed to parse customer success response",
                error=str(e),
                response=response,
            )
            raise ValueError(f"Failed to parse customer success response: {e}") from e
