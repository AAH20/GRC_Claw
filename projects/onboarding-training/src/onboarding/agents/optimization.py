"""Optimization agent: recommends content revisions from assessment data and feedback."""  # noqa: E501

from __future__ import annotations

from typing import Any

from langchain_deepagents import create_deep_agent

from onboarding.config import get_settings
from onboarding.exceptions import AgentError
from onboarding.models import AssessmentResult, Course
from onboarding.utils import get_logger

logger = get_logger(__name__)


class OptimizationAgent:
    """Analyzes assessment data and learner feedback to recommend content improvements.

    Identifies lessons with low average scores, high failure rates, or
    negative feedback trends, and suggests specific revisions.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.optimization.enabled:
            raise AgentError("Optimization", "Agent is disabled in configuration")
        self._settings = settings
        self._agent = self._build_agent()

    def _build_agent(self) -> Any:
        """Build the underlying LangChain DeepAgent."""
        config = self._settings
        system_message = (
            "You are a learning experience optimizer. Analyze assessment "
            "results and learner feedback to identify content that needs "
            "improvement. Provide specific, actionable recommendations."
        )
        try:
            return create_deep_agent(
                model=config.openai_model,
                system_message=system_message,
                max_iterations=config.deepagents_max_iterations,
                temperature=config.model_temperature,
            )
        except Exception as exc:
            logger.error("Failed to build Optimization agent", error=str(exc))
            raise AgentError("Optimization",
                f"Agent initialization failed: {exc}") from exc

    async def analyze_course(
        self,
        course: Course,
        results: list[AssessmentResult],
        min_samples: int | None = None,
    ) -> dict[str, Any]:
        """Analyze assessment data and generate optimization recommendations.

        Args:
            course: The course to analyze.
            results: All assessment results for this course.
            min_samples: Minimum results needed before recommending changes.

        Returns:
            A dict with recommendations and metrics.

        Raises:
            AgentError: If analysis fails.
        """
        threshold = min_samples or self._settings.optimization.min_feedback_samples

        if len(results) < threshold:
            logger.info(
                "Insufficient data for optimization",
                course_id=course.course_id,
                result_count=len(results),
                required=threshold,
            )
            return {
                "course_id": course.course_id,
                "sufficient_data": False,
                "result_count": len(results),
                "required_samples": threshold,
                "recommendations": [],
            }

        logger.info(
            "Analyzing course for optimization",
            course_id=course.course_id,
            result_count=len(results),
        )

        prompt = self._build_analysis_prompt(course, results)

        try:
            result = await self._agent.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]}
            )
        except Exception as exc:
            logger.error("Optimization analysis failed", error=str(exc))
            raise AgentError("Optimization", f"Analysis failed: {exc}") from exc

        return self._parse_recommendations(result, course)

    def _build_analysis_prompt(
        self,
        course: Course,
        results: list[AssessmentResult],
    ) -> str:
        """Build the analysis prompt with aggregated data."""
        # Aggregate by lesson
        lesson_stats: dict[str, dict[str, float]] = {}
        for r in results:
            if r.lesson_id not in lesson_stats:
                lesson_stats[r.lesson_id] = {"total": 0, "sum": 0.0, "failures": 0}
            lesson_stats[r.lesson_id]["total"] += 1
            lesson_stats[r.lesson_id]["sum"] += r.score
            if not r.passed:
                lesson_stats[r.lesson_id]["failures"] += 1

        stats_lines = []
        for lesson_id, stats in lesson_stats.items():
            avg = stats["sum"] / stats["total"] if stats["total"] > 0 else 0
            fail_rate = stats["failures"] / stats["total"] if stats["total"] > 0 else 0
            stats_lines.append(
                f"  - {lesson_id}: avg_score={avg:.2f}, "
                f"fail_rate={fail_rate:.2f}, n={int(stats['total'])}"
            )

        return (
            f"Course: {course.title} ({course.course_id})\n"
            f"Total assessment results: {len(results)}\n\n"
            "Per-lesson statistics:\n" + "\n".join(stats_lines) + "\n\n"
            "Identify lessons that need improvement and recommend specific "
            "content revisions. Return JSON:\n"
            '{\n'
            '  "recommendations": [\n'
            '    {\n'
            '      "lesson_id": "lesson_xxx",\n'
            '      "issue": "description of the problem",\n'
            '      "severity": "low|medium|high",\n'
            '      "suggested_action": "specific revision suggestion"\n'
            '    }\n'
            '  ]\n'
            "}"
        )

    def _parse_recommendations(self, result: Any, course: Course) -> dict[str, Any]:
        """Parse the agent output into a recommendations dict."""
        if hasattr(result, "content"):
            raw = result.content
        elif isinstance(result, dict) and "messages" in result:
            raw = result["messages"][-1].content
        else:
            raw = str(result)

        import json

        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError as exc:
            raise AgentError("Optimization", f"Invalid JSON from agent: {exc}") from exc

        return {
            "course_id": course.course_id,
            "sufficient_data": True,
            "recommendations": data.get("recommendations", []),
        }
