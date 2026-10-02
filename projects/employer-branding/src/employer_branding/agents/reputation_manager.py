"""Reputation Manager Agent for monitoring and managing employer reputation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from employer_branding.agents.base import BaseAgent
from employer_branding.models import (
    ReputationAnalysisRequest,
    ReputationLevel,
    ReputationScore,
    ReviewSource,
)


class ReputationManagerAgent(BaseAgent[ReputationScore]):
    """Agent that monitors and manages employer reputation.

    Aggregates review data from multiple sources, calculates reputation
    scores, identifies trends, and provides actionable recommendations
    for reputation improvement.
    """

    def __init__(self) -> None:
        """Initialize the reputation manager agent."""
        super().__init__()
        self._prompt_template = self._build_prompt_template()

    def _build_prompt_template(self) -> ChatPromptTemplate:
        """Build the prompt template for reputation analysis.

        Returns:
            Configured ChatPromptTemplate.
        """
        system_message = """You are an expert employer reputation analyst.
Analyze the provided review data and return a JSON object with:
{
    "overall_score": float between 0 and 100,
    "reputation_level": "excellent|good|average|poor|critical",
    "rating": float between 0 and 5,
    "category_scores": {"category": float},
    "trend": "improving|stable|declining",
    "recommendations": ["actionable recommendation strings"]
}

Base your analysis on review ratings, sentiment distribution, common themes,
and industry benchmarks. Be objective and data-driven."""

        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            HumanMessage(content="{input}"),
        ])

    async def run(self, request: ReputationAnalysisRequest) -> ReputationScore:
        """Analyze and score employer reputation.

        Args:
            request: Reputation analysis request with company and options.

        Returns:
            ReputationScore with detailed scoring and recommendations.

        Raises:
            ValueError: If request parameters are invalid.
            RuntimeError: If analysis fails.
        """
        self.logger.info(
            "analyzing_reputation",
            company=request.company_name,
            sources=[s.value for s in request.sources],
            period_days=request.period_days,
        )

        try:
            # In production, this would fetch real review data
            review_summary = self._summarize_reviews(request)

            prompt = self._build_analysis_prompt(request, review_summary)
            response = await self._model.ainvoke(prompt)
            raw_content = response.content if hasattr(response, "content") else str(response)

            parsed = self._parse_response(raw_content)

            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=request.period_days)

            score = ReputationScore(
                company_name=request.company_name,
                overall_score=parsed["overall_score"],
                reputation_level=ReputationLevel(parsed["reputation_level"]),
                rating=parsed["rating"],
                review_count=parsed.get("review_count", 0),
                positive_percentage=parsed.get("positive_percentage", 0.0),
                negative_percentage=parsed.get("negative_percentage", 0.0),
                neutral_percentage=parsed.get("neutral_percentage", 0.0),
                category_scores=parsed.get("category_scores", {}),
                trend=parsed.get("trend", "stable"),
                period_start=period_start,
                period_end=period_end,
                recommendations=parsed.get("recommendations", []),
            )

            self.logger.info(
                "reputation_analyzed",
                score_id=str(score.id),
                overall_score=score.overall_score,
                level=score.reputation_level.value,
            )
            return score

        except Exception as exc:
            self.logger.error("reputation_analysis_failed", error=str(exc))
            raise RuntimeError(f"Failed to analyze reputation: {exc}") from exc

    def _summarize_reviews(self, request: ReputationAnalysisRequest) -> str:
        """Summarize review data for the company.

        In production, this would fetch from review APIs.
        For now, returns a placeholder summary.

        Args:
            request: Reputation analysis request.

        Returns:
            Summary string of review data.
        """
        sources_str = ", ".join(s.value for s in request.sources)
        return (
            f"Review data for {request.company_name} from sources: {sources_str} "
            f"over the past {request.period_days} days. "
            f"Include ratings, pros/cons, and recommendation rates."
        )

    def _build_analysis_prompt(
        self, request: ReputationAnalysisRequest, review_summary: str
    ) -> str:
        """Build the analysis prompt.

        Args:
            request: Reputation analysis request.
            review_summary: Summary of review data.

        Returns:
            Formatted prompt string.
        """
        parts = [
            f"Analyze employer reputation for: {request.company_name}",
            f"Analysis period: {request.period_days} days",
            f"\nReview Summary:\n{review_summary}",
        ]

        if request.include_recommendations:
            parts.append("\nProvide actionable recommendations for improvement.")

        return "\n".join(parts)

    def _parse_response(self, raw_content: str) -> dict[str, Any]:
        """Parse the LLM response into a structured dictionary.

        Args:
            raw_content: Raw response content from the model.

        Returns:
            Parsed dictionary with reputation data.

        Raises:
            ValueError: If response cannot be parsed.
        """
        import json

        content = raw_content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse reputation analysis response: {exc}") from exc

        required = ["overall_score", "reputation_level", "rating"]
        for field in required:
            if field not in parsed:
                raise ValueError(f"Missing required field in response: {field}")

        return parsed
