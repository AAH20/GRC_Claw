"""Escalation Analyzer Agent - detects patterns and provides insights."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from escalation_workflow.agents.base import BaseAgent
from escalation_workflow.models.analysis import (EscalationAnalysis,
                                                 EscalationPattern,
                                                 TrendReport)
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from escalation_workflow.models.escalation import Escalation


class EscalationAnalyzerInput(BaseModel):
    """Input schema for the escalation analyzer agent."""

    escalations: list[Escalation]
    analysis_type: str = "single"
    time_range_days: int = 30
    context: dict[str, Any] = Field(default_factory=dict)


class EscalationAnalyzerAgent(BaseAgent[EscalationAnalyzerInput, EscalationAnalysis]):
    """Agent that analyzes escalations for patterns and insights.

    Uses LLM reasoning to detect recurring patterns, assess risks,
    and provide actionable recommendations.
    """

    SYSTEM_PROMPT = """You are an expert escalation analyst. Analyze the provided escalations
to identify patterns, assess risks, and provide insights.

Look for:
- Recurring issues and root causes
- Seasonal or time-based patterns
- Dependency-related escalations
- Capacity and resource constraints
- Configuration and deployment issues

Provide actionable recommendations for prevention and improvement."""

    async def run(self, input_data: EscalationAnalyzerInput) -> EscalationAnalysis:
        """Analyze escalations for patterns and insights.

        Args:
            input_data: Escalations and analysis parameters.

        Returns:
            EscalationAnalysis: Analysis results with patterns and recommendations.
        """
        self.logger.info(
            "Analyzing escalations",
            count=len(input_data.escalations),
            analysis_type=input_data.analysis_type,
        )

        escalations = input_data.escalations
        escalation_summaries = [
            f"- {e.title} ({e.priority}, {e.category}, {e.status})"
            for e in escalations[:10]
        ]

        user_content = f"""
Analysis Type: {input_data.analysis_type}
Time Range: {input_data.time_range_days} days
Number of Escalations: {len(escalations)}

Recent Escalations:
{chr(10).join(escalation_summaries)}

Context: {input_data.context}

Provide:
1. Pattern analysis (recurring, seasonal, dependency, capacity, configuration, external)
2. Risk assessment (0.0-1.0)
3. Impact assessment
4. Actionable recommendations
5. Related escalation IDs if applicable
"""

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        try:
            response = await self.model.ainvoke(messages)
            return self._parse_analysis(response.content, escalations)
        except Exception as exc:
            self.logger.error("Analysis failed", error=str(exc))
            return self._fallback_analysis(escalations)

    def _parse_analysis(
        self, content: str, escalations: list[Escalation]
    ) -> EscalationAnalysis:
        """Parse LLM response into an EscalationAnalysis.

        Args:
            content: Raw LLM response content.
            escalations: The escalations that were analyzed.

        Returns:
            EscalationAnalysis: Parsed analysis result.
        """
        content_lower = content.lower()
        patterns: list[EscalationPattern] = []

        pattern_keywords = {
            EscalationPattern.RECURRING: ["recurring", "repeated", "frequent"],
            EscalationPattern.SEASONAL: ["seasonal", "periodic", "time-based"],
            EscalationPattern.DEPENDENCY: ["dependency", "dependent", "upstream"],
            EscalationPattern.CAPACITY: ["capacity", "resource", "overload"],
            EscalationPattern.CONFIGURATION: ["configuration", "config", "deployment"],
            EscalationPattern.EXTERNAL: ["external", "third-party", "vendor"],
        }

        for pattern, keywords in pattern_keywords.items():
            if any(kw in content_lower for kw in keywords):
                patterns.append(pattern)

        return EscalationAnalysis(
            escalation_id=escalations[0].id if escalations else None,
            analysis_type="batch" if len(escalations) > 1 else "single",
            summary=content,
            patterns=patterns or [EscalationPattern.RECURRING],
            risk_score=0.5,
            impact_assessment="Moderate impact detected",
            recommendations=[
                "Review escalation patterns",
                "Implement preventive measures",
            ],
            related_escalations=[e.id for e in escalations[1:5]],
        )

    def _fallback_analysis(self, escalations: list[Escalation]) -> EscalationAnalysis:
        """Provide fallback analysis when LLM fails.

        Args:
            escalations: The escalations that were analyzed.

        Returns:
            EscalationAnalysis: Default analysis result.
        """
        return EscalationAnalysis(
            escalation_id=escalations[0].id if escalations else None,
            analysis_type="batch" if len(escalations) > 1 else "single",
            summary="Analysis unavailable due to LLM failure",
            patterns=[],
            risk_score=0.0,
            impact_assessment="Unknown",
            recommendations=["Retry analysis", "Check system logs"],
        )

    async def generate_trend_report(
        self, escalations: list[Escalation], days: int = 30
    ) -> TrendReport:
        """Generate a trend report from escalation data.

        Args:
            escalations: List of escalations to analyze.
            days: Number of days for the trend period.

        Returns:
            TrendReport: Computed trend report.
        """
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        start = now - timedelta(days=days)

        total = len(escalations)
        resolved = sum(1 for e in escalations if e.status.value == "resolved")
        breached = sum(1 for e in escalations if e.status.value == "closed")

        categories: dict[str, int] = {}
        priorities: dict[str, int] = {}
        for e in escalations:
            categories[e.category] = categories.get(e.category, 0) + 1
            priorities[e.priority] = priorities.get(e.priority, 0) + 1

        return TrendReport(
            period_start=start,
            period_end=now,
            total_escalations=total,
            resolved_count=resolved,
            breached_count=breached,
            avg_resolution_minutes=0.0,
            top_categories=dict(
                sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
            priority_distribution=priorities,
        )
