"""Assessment agent: grades learner responses and computes mastery."""

from __future__ import annotations

from typing import Any

from langchain_deepagents import create_deep_agent

from onboarding.config import get_settings
from onboarding.exceptions import AgentError
from onboarding.models import AssessmentResult, Course, Learner, Lesson
from onboarding.utils import generate_id, get_logger

logger = get_logger(__name__)


class AssessmentAgent:
    """Grades open-ended learner responses and computes mastery levels.

    Uses LangChain DeepAgents to evaluate short-answer and essay responses
    against lesson objectives and rubrics.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.assessment.enabled:
            raise AgentError("Assessment", "Agent is disabled in configuration")
        self._settings = settings
        self._agent = self._build_agent()

    def _build_agent(self) -> Any:
        """Build the underlying LangChain DeepAgent."""
        config = self._settings
        system_message = (
            "You are an expert assessment grader. Evaluate learner responses "
            "against the provided rubric and lesson objectives. Be fair, "
            "consistent, and constructive. Return a score between 0.0 and 1.0."
        )
        try:
            return create_deep_agent(
                model=config.openai_model,
                system_message=system_message,
                max_iterations=config.deepagents_max_iterations,
                temperature=0.1,
            )
        except Exception as exc:
            logger.error("Failed to build Assessment agent", error=str(exc))
            raise AgentError("Assessment",
                f"Agent initialization failed: {exc}") from exc

    async def grade_response(
        self,
        learner: Learner,
        course: Course,
        lesson: Lesson,
        question_id: str,
        response: str,
    ) -> AssessmentResult:
        """Grade a learner's response to a quiz question.

        Args:
            learner: The learner being assessed.
            course: The course containing the lesson.
            lesson: The lesson containing the question.
            question_id: The ID of the question being answered.
            response: The learner's text response.

        Returns:
            An AssessmentResult with score, pass/fail, and feedback.

        Raises:
            AgentError: If grading fails.
        """
        logger.info(
            "Grading response",
            learner_id=learner.learner_id,
            course_id=course.course_id,
            lesson_id=lesson.lesson_id,
            question_id=question_id,
        )

        question = next((q for q in lesson.quiz if q.question_id == question_id), None)
        if question is None:
            raise AgentError("Assessment",
                f"Question {question_id} not found in lesson")

        prompt = self._build_grading_prompt(lesson, question.prompt, response)

        try:
            result = await self._agent.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]}
            )
        except Exception as exc:
            logger.error("Grading failed", error=str(exc))
            raise AgentError("Assessment", f"Grading failed: {exc}") from exc

        return self._parse_result(result, learner, course, lesson)

    def _build_grading_prompt(self,
        lesson: Lesson, question: str, response: str) -> str:
        """Build the grading prompt."""
        return (
            f"Lesson: {lesson.title}\n"
            f"Lesson content summary: {lesson.content[:500]}\n\n"
            f"Question: {question}\n\n"
            f"Learner response:\n{response}\n\n"
            "Grade this response. Return JSON:\n"
            '{\n'
            '  "score": 0.0-1.0,\n'
            '  "feedback": "Constructive feedback for the learner"\n'
            "}"
        )

    def _parse_result(
        self,
        result: Any,
        learner: Learner,
        course: Course,
        lesson: Lesson,
    ) -> AssessmentResult:
        """Parse the agent output into an AssessmentResult."""
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
            raise AgentError("Assessment", f"Invalid JSON from agent: {exc}") from exc

        score = float(data.get("score", 0.0))
        passed = score >= self._settings.assessment.passing_score
        mastery = score >= self._settings.assessment.mastery_threshold

        return AssessmentResult(
            assessment_id=generate_id("assess"),
            learner_id=learner.learner_id,
            course_id=course.course_id,
            lesson_id=lesson.lesson_id,
            score=score,
            passed=passed,
            mastery_achieved=mastery,
            feedback=data.get("feedback", ""),
        )

    async def compute_mastery(
        self,
        learner: Learner,
        course: Course,
        results: list[AssessmentResult],
    ) -> float:
        """Compute overall mastery for a learner in a course.

        Args:
            learner: The learner.
            course: The course.
            results: All assessment results for this learner/course.

        Returns:
            Mastery score between 0.0 and 1.0.
        """
        if not results:
            return 0.0
        return sum(r.score for r in results) / len(results)
