"""Performance Analytics agent: cohort dashboards, trends, and alerting."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from langchain_deepagents import create_deep_agent

from onboarding.config import get_settings
from onboarding.exceptions import AgentError
from onboarding.models import AssessmentResult, CohortMetrics, Course, Learner
from onboarding.utils import get_logger

logger = get_logger(__name__)


class PerformanceAnalyticsAgent:
    """Generates cohort-level performance dashboards, trends, and alerts.

    Aggregates completion rates, engagement metrics, and assessment scores
    across learner cohorts to surface actionable insights.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.performance_analytics.enabled:
            raise AgentError("PerformanceAnalytics",
                "Agent is disabled in configuration")
        self._settings = settings
        self._agent = self._build_agent()

    def _build_agent(self) -> Any:
        """Build the underlying LangChain DeepAgent."""
        config = self._settings
        system_message = (
            "You are a learning analytics expert. Analyze cohort performance "
            "data to identify trends, at-risk learners, and actionable insights. "
            "Focus on completion rates, engagement patterns, and score distributions."
        )
        try:
            return create_deep_agent(
                model=config.openai_model,
                system_message=system_message,
                max_iterations=config.deepagents_max_iterations,
                temperature=config.model_temperature,
            )
        except Exception as exc:
            logger.error("Failed to build PerformanceAnalytics agent", error=str(exc))
            raise AgentError("PerformanceAnalytics",
                f"Agent initialization failed: {exc}") from exc

    async def generate_cohort_report(
        self,
        cohort_id: str,
        learners: list[Learner],
        courses: list[Course],
        results: list[AssessmentResult],
        lookback_days: int | None = None,
    ) -> CohortMetrics:
        """Generate a performance report for a cohort.

        Args:
            cohort_id: Identifier for the cohort.
            learners: All learners in the cohort.
            courses: All courses assigned to the cohort.
            results: All assessment results for the cohort.
            lookback_days: Analysis period (defaults to config).

        Returns:
            Aggregated CohortMetrics with alerts.

        Raises:
            AgentError: If report generation fails.
        """
        days = (
            lookback_days or self._settings.performance_analytics.default_lookback_days
        )
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        logger.info(
            "Generating cohort report",
            cohort_id=cohort_id,
            learner_count=len(learners),
            lookback_days=days,
        )

        # Compute base metrics
        total = len(learners)
        active = len({r.learner_id for r in results})
        completion = active / total if total > 0 else 0.0
        avg_score = (
            sum(r.score for r in results) / len(results) if results else 0.0
        )

        # Estimate time from lesson data
        total_minutes = sum(
            lesson.estimated_minutes
            for course in courses
            for lesson in course.lessons
        )
        avg_time = total_minutes / total if total > 0 else 0.0

        # Generate alerts
        alerts = self._generate_alerts(completion, avg_score, total, active)

        metrics = CohortMetrics(
            cohort_id=cohort_id,
            total_learners=total,
            active_learners=active,
            completion_rate=completion,
            average_score=avg_score,
            average_time_minutes=avg_time,
            period_start=start_date,
            period_end=end_date,
            alerts=alerts,
        )

        # Use the agent for deeper insights
        insights = await self._generate_insights(metrics, learners, results)
        if insights:
            metrics.alerts.extend(insights.get("additional_alerts", []))

        return metrics

    def _generate_alerts(
        self,
        completion: float,
        avg_score: float,
        total: int,
        active: int,
    ) -> list[str]:
        """Generate alert strings based on metric thresholds."""
        alerts: list[str] = []
        threshold = self._settings.performance_analytics.alert_completion_threshold

        if completion < threshold:
            alerts.append(
                f"LOW_COMPLETION: {completion:.0%} completion rate "
                f"(threshold: {threshold:.0%})"
            )
        if avg_score < 0.6:
            alerts.append(
                f"LOW_AVG_SCORE: {avg_score:.0%} average score across cohort"
            )
        if total > 0 and active / total < 0.5:
            alerts.append(
                f"LOW_ENGAGEMENT: only {active}/{total} learners active"
            )
        return alerts

    async def _generate_insights(
        self,
        metrics: CohortMetrics,
        learners: list[Learner],
        results: list[AssessmentResult],
    ) -> dict[str, Any]:
        """Use the agent to generate deeper insights from the data."""
        prompt = (
            f"Cohort metrics:\n"
            f"  Total learners: {metrics.total_learners}\n"
            f"  Active learners: {metrics.active_learners}\n"
            f"  Completion rate: {metrics.completion_rate:.0%}\n"
            f"  Average score: {metrics.average_score:.0%}\n"
            f"  Average time: {metrics.average_time_minutes:.0f} minutes\n\n"
            f"Existing alerts: {metrics.alerts}\n\n"
            "Provide additional insights and recommendations. Return JSON:\n"
            '{\n'
            '  "additional_alerts": ["alert string"],\n'
            '  "insights": ["insight string"]\n'
            "}"
        )

        try:
            result = await self._agent.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]}
            )
        except Exception as exc:
            logger.warning("Insight generation failed", error=str(exc))
            return {}

        if hasattr(result, "content"):
            raw = result.content
        elif isinstance(result, dict) and "messages" in result:
            raw = result["messages"][-1].content
        else:
            raw = str(result)

        import json

        try:
            return json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            return {}
