"""Moderator Performance Agent implementation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate

from moderation_analytics.agents.base import BaseAgent
from moderation_analytics.models import ModeratorPerformance


class ModeratorPerformanceAgent(BaseAgent[list[ModeratorPerformance]]):
    """Agent that evaluates moderator performance.

    Analyzes accuracy, response time, consistency, and provides
    actionable feedback for moderator improvement.
    """

    def __init__(self, llm: BaseLanguageModel | None = None) -> None:
        """Initialize the Moderator Performance Agent.

        Args:
            llm: Optional pre-configured language model.
        """
        super().__init__(name="ModeratorPerformance", llm=llm)
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert in evaluating moderator performance. Provide fair, "
                    "data-driven assessments with constructive feedback.",
                ),
                (
                    "human",
                    "Evaluate the following moderator performance data:\n\n{performance_data}\n\n"
                    "Provide detailed performance analysis with strengths, weaknesses, "
                    "and recommendations.",
                ),
            ]
        )

    async def run(
        self,
        moderator_data: list[dict[str, Any]],
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        **kwargs: Any,
    ) -> list[ModeratorPerformance]:
        """Evaluate moderator performance.

        Args:
            moderator_data: List of moderator performance data.
            period_start: Evaluation period start. Defaults to 30 days ago.
            period_end: Evaluation period end. Defaults to now.
            **kwargs: Additional parameters.

        Returns:
            list[ModeratorPerformance]: Performance evaluations for each moderator.

        Raises:
            ValueError: If moderator_data is empty.
        """
        self._log_start(moderator_count=len(moderator_data))

        if not moderator_data:
            raise ValueError("Cannot evaluate performance with empty moderator data")

        start = period_start or (datetime.utcnow() - timedelta(days=30))
        end = period_end or datetime.utcnow()

        results: list[ModeratorPerformance] = []
        for mod_data in moderator_data:
            performance = self._calculate_performance(mod_data, start, end)
            results.append(performance)

        # Use LLM for qualitative analysis
        if self._settings.openai_api_key:
            try:
                await self._enhance_with_llm(results, moderator_data)
            except Exception as e:
                self._log_error(e, fallback="using quantitative analysis only")

        self._log_complete(results)
        return results

    def _calculate_performance(
        self, data: dict[str, Any], start: datetime, end: datetime
    ) -> ModeratorPerformance:
        """Calculate performance metrics for a single moderator.

        Args:
            data: Raw moderator data.
            start: Evaluation period start.
            end: Evaluation period end.

        Returns:
            ModeratorPerformance: Calculated performance metrics.
        """
        total = data.get("total_reviews", 0)
        correct = data.get("correct_decisions", 0)
        escalated = data.get("escalations", 0)

        accuracy = correct / total if total > 0 else 0.0
        escalation_rate = escalated / total if total > 0 else 0.0

        return ModeratorPerformance(
            moderator_id=str(data.get("moderator_id", "unknown")),
            moderator_name=str(data.get("moderator_name", "Unknown")),
            total_reviews=total,
            accuracy=round(accuracy, 4),
            average_response_time_seconds=float(data.get("avg_response_time", 0.0)),
            consistency_score=float(data.get("consistency_score", 0.0)),
            escalation_rate=round(escalation_rate, 4),
            period_start=start,
            period_end=end,
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            recommendations=data.get("recommendations", []),
        )

    async def _enhance_with_llm(
        self, results: list[ModeratorPerformance], raw_data: list[dict[str, Any]]
    ) -> None:
        """Enhance performance results with LLM qualitative analysis.

        Args:
            results: Performance results to enhance in-place.
            raw_data: Raw moderator data for LLM context.
        """
        # In production, use structured output to parse LLM response
        pass
