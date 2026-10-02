"""Sentiment Analysis Agent — Analyzes customer sentiment and satisfaction signals."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

from customer_service.agents.base import BaseAgent

logger = structlog.get_logger(__name__)


class SentimentResult(BaseModel):
    """Result of sentiment analysis."""

    overall_sentiment: str = Field(..., description="Overall sentiment classification")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score from -1 to 1")
    satisfaction_level: str = Field(..., description="Customer satisfaction level")
    frustration_level: str = Field(..., description="Detected frustration level")
    key_phrases: list[str] = Field(
        default_factory=list, description="Key sentiment phrases detected"
    )
    urgency_indicators: list[str] = Field(
        default_factory=list, description="Urgency indicators detected"
    )
    churn_risk: str = Field(..., description="Churn risk assessment")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SentimentAnalysisAgent(BaseAgent):
    """Agent responsible for analyzing customer sentiment in tickets and interactions.

    Detects emotional signals, satisfaction levels, frustration indicators,
    and churn risk from customer communications.
    """

    def __init__(self, model: str = "gpt-4o", temperature: float = 0.1) -> None:
        """Initialize the Sentiment Analysis Agent.

        Args:
            model: The LLM model to use.
            temperature: Sampling temperature for the LLM.
        """
        super().__init__(name="sentiment_analysis", model=model, temperature=temperature)

    async def run(
        self,
        text: str,
        interaction_history: list[dict[str, Any]] | None = None,
    ) -> SentimentResult:
        """Analyze sentiment in customer communication.

        Args:
            text: The customer communication text to analyze.
            interaction_history: Optional list of previous interactions.

        Returns:
            SentimentResult with sentiment analysis details.

        Raises:
            ValueError: If text is empty.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        logger.info("Analyzing sentiment", text_length=len(text))

        prompt = self._build_prompt(text, interaction_history)
        response = await self._call_llm(prompt)

        result = self._parse_response(response)
        logger.info(
            "Sentiment analysis complete",
            sentiment=result.overall_sentiment,
            score=result.sentiment_score,
            churn_risk=result.churn_risk,
        )
        return result

    def _build_prompt(
        self,
        text: str,
        interaction_history: list[dict[str, Any]] | None,
    ) -> str:
        """Build the sentiment analysis prompt.

        Args:
            text: The customer communication text.
            interaction_history: Optional interaction history.

        Returns:
            Formatted prompt string.
        """
        history_str = ""
        if interaction_history:
            history_str = f"\nInteraction History: {interaction_history}"

        return f"""Analyze the sentiment of the following customer communication.

Communication:
{text}
{history_str}

Respond in JSON format with the following structure:
{{
    "overall_sentiment": "<positive|neutral|negative|mixed>",
    "sentiment_score": <float between -1 and 1>,
    "satisfaction_level": "<very_satisfied|satisfied|neutral|dissatisfied|very_dissatisfied>",
    "frustration_level": "<none|low|medium|high|extreme>",
    "key_phrases": ["<phrase>"],
    "urgency_indicators": ["<indicator>"],
    "churn_risk": "<none|low|medium|high|critical>"
}}"""

    def _parse_response(self, response: str) -> SentimentResult:
        """Parse the LLM response into a SentimentResult.

        Args:
            response: Raw LLM response string.

        Returns:
            Parsed SentimentResult.

        Raises:
            ValueError: If the response cannot be parsed.
        """
        import json

        try:
            data = json.loads(response)
            return SentimentResult(**data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("Failed to parse sentiment response", error=str(e), response=response)
            raise ValueError(f"Failed to parse sentiment response: {e}") from e
