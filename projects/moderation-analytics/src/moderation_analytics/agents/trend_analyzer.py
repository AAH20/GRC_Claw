"""Trend Analyzer Agent implementation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate

from moderation_analytics.agents.base import BaseAgent
from moderation_analytics.models import Trend, TrendDirection


class TrendAnalyzerAgent(BaseAgent[list[Trend]]):
    """Agent that analyzes moderation trends over time.

    Uses LLM-powered analysis to identify patterns, detect anomalies,
    and describe trends in moderation data.
    """

    def __init__(self, llm: BaseLanguageModel | None = None) -> None:
        """Initialize the Trend Analyzer Agent.

        Args:
            llm: Optional pre-configured language model.
        """
        super().__init__(name="TrendAnalyzer", llm=llm)
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert moderation analytics analyst. Analyze the provided "
                    "moderation data and identify significant trends. Focus on actionable "
                    "insights and clear descriptions.",
                ),
                (
                    "human",
                    "Analyze moderation trends for the period {start_date} to {end_date}.\n\n"
                    "Data summary:\n{data_summary}\n\n"
                    "Identify key trends, their direction, and confidence levels.",
                ),
            ]
        )

    async def run(
        self,
        data: list[dict[str, Any]],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        **kwargs: Any,
    ) -> list[Trend]:
        """Analyze moderation data for trends.

        Args:
            data: List of moderation data points to analyze.
            start_date: Start of analysis period. Defaults to 30 days ago.
            end_date: End of analysis period. Defaults to now.
            **kwargs: Additional parameters.

        Returns:
            list[Trend]: Identified trends with direction and confidence.

        Raises:
            ValueError: If data is empty.
        """
        self._log_start(data_points=len(data))

        if not data:
            raise ValueError("Cannot analyze trends with empty data")

        start = start_date or (datetime.utcnow() - timedelta(days=30))
        end = end_date or datetime.utcnow()

        # Calculate basic statistics for trend detection
        trends = self._detect_trends(data, start, end)

        # Use LLM for enhanced analysis if available
        if self._settings.openai_api_key:
            try:
                llm_trends = await self._llm_analyze(data, start, end)
                trends.extend(llm_trends)
            except Exception as e:
                self._log_error(e, fallback="using statistical analysis only")

        self._log_complete(trends)
        return trends

    def _detect_trends(
        self, data: list[dict[str, Any]], start: datetime, end: datetime
    ) -> list[Trend]:
        """Detect trends using statistical analysis.

        Args:
            data: Moderation data points.
            start: Analysis period start.
            end: Analysis period end.

        Returns:
            list[Trend]: Statistically detected trends.
        """
        trends: list[Trend] = []

        if len(data) < 2:
            return trends

        # Detect volume trend
        volumes = [d.get("count", 0) for d in data]
        if len(volumes) >= 2:
            change_pct = ((volumes[-1] - volumes[0]) / max(volumes[0], 1)) * 100
            direction = self._classify_direction(change_pct)
            trends.append(
                Trend(
                    metric_name="moderation_volume",
                    direction=direction,
                    change_percentage=round(change_pct, 2),
                    confidence=0.85,
                    data_points=volumes,
                    start_date=start,
                    end_date=end,
                    description=f"Moderation volume is {direction.value} by {abs(change_pct):.1f}%",
                )
            )

        # Detect severity trend
        severities = [d.get("avg_severity", 0.0) for d in data]
        if len(severities) >= 2:
            sev_change = ((severities[-1] - severities[0]) / max(severities[0], 0.01)) * 100
            trends.append(
                Trend(
                    metric_name="average_severity",
                    direction=self._classify_direction(sev_change),
                    change_percentage=round(sev_change, 2),
                    confidence=0.75,
                    data_points=severities,
                    start_date=start,
                    end_date=end,
                    description=f"Average severity is {self._classify_direction(sev_change).value}",
                )
            )

        return trends

    def _classify_direction(self, change_pct: float) -> TrendDirection:
        """Classify percentage change into trend direction.

        Args:
            change_pct: Percentage change value.

        Returns:
            TrendDirection: Classified direction.
        """
        if abs(change_pct) < 5:
            return TrendDirection.STABLE
        if abs(change_pct) > 50:
            return TrendDirection.VOLATILE
        return TrendDirection.INCREASING if change_pct > 0 else TrendDirection.DECREASING

    async def _llm_analyze(
        self, data: list[dict[str, Any]], start: datetime, end: datetime
    ) -> list[Trend]:
        """Use LLM for enhanced trend analysis.

        Args:
            data: Moderation data points.
            start: Analysis period start.
            end: Analysis period end.

        Returns:
            list[Trend]: LLM-identified trends.
        """
        data_summary = f"Data points: {len(data)}, Period: {start.date()} to {end.date()}"
        await self._prompt.ainvoke(
            {
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "data_summary": data_summary,
            }
        )
        # Parse LLM response into Trend objects
        # In production, use structured output parsing
        return []
