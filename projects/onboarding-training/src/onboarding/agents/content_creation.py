"""Content Creation agent: generates onboarding course content using LangChain DeepAgents."""  # noqa: E501

from __future__ import annotations

from typing import Any

from langchain_deepagents import create_deep_agent

from onboarding.config import get_settings
from onboarding.exceptions import AgentError
from onboarding.models import Course, Lesson, QuizQuestion
from onboarding.utils import generate_id, get_logger

logger = get_logger(__name__)


class ContentCreationAgent:
    """Generates personalized onboarding course outlines, lessons, and quizzes.

    Uses LangChain DeepAgents with the grc-marketing-core toolkit to produce
    role-specific training content.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.content_creation.enabled:
            raise AgentError("ContentCreation", "Agent is disabled in configuration")
        self._settings = settings
        self._agent = self._build_agent()

    def _build_agent(self) -> Any:
        """Build the underlying LangChain DeepAgent."""
        config = self._settings
        system_message = (
            "You are an expert onboarding content creator. Generate structured "
            "course outlines, lesson content, and quiz questions tailored to the "
            "learner's role and proficiency level. Output valid JSON matching "
            "the expected schema."
        )
        try:
            return create_deep_agent(
                model=config.openai_model,
                system_message=system_message,
                max_iterations=config.deepagents_max_iterations,
                temperature=config.model_temperature,
            )
        except Exception as exc:
            logger.error("Failed to build ContentCreation agent", error=str(exc))
            raise AgentError("ContentCreation",
                f"Agent initialization failed: {exc}") from exc

    async def create_course(
        self,
        role: str,
        level: str = "novice",
        language: str | None = None,
        max_lessons: int | None = None,
    ) -> Course:
        """Create a complete onboarding course for a given role.

        Args:
            role: The target job role (e.g. "sales_rep", "engineer").
            level: Learner proficiency level.
            language: Content language (defaults to config).
            max_lessons: Maximum number of lessons (defaults to config).

        Returns:
            A fully generated Course model.

        Raises:
            AgentError: If content generation fails.
        """
        lang = language or self._settings.content_creation.default_language
        lesson_cap = (
            max_lessons or self._settings.content_creation.max_lessons_per_course
        )

        logger.info(
            "Creating course",
            role=role,
            level=level,
            language=lang,
            max_lessons=lesson_cap,
        )

        prompt = self._build_prompt(role, level, lang, lesson_cap)

        try:
            result = await self._agent.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]}
            )
        except Exception as exc:
            logger.error("Content creation failed", error=str(exc), role=role)
            raise AgentError("ContentCreation",
                f"Course generation failed: {exc}") from exc

        return self._parse_course(result, role)

    def _build_prompt(self,
        role: str, level: str, language: str, max_lessons: int) -> str:
        """Build the content generation prompt."""
        return (
            f"Create an onboarding course for a {role} at the {level} level.\n"
            f"Language: {language}\n"
            f"Maximum lessons: {max_lessons}\n\n"
            "Return a JSON object with this structure:\n"
            '{\n'
            '  "title": "Course title",\n'
            '  "description": "Course description",\n'
            '  "lessons": [\n'
            '    {\n'
            '      "title": "Lesson title",\n'
            '      "content": "Lesson body text (markdown)",\n'
            '      "estimated_minutes": 15,\n'
            '      "quiz": [\n'
            '        {\n'
            '          "prompt": "Question text",\n'
            '          "question_type": "multiple_choice",\n'
            '          "options": ["A", "B", "C", "D"],\n'
            '          "correct_answer": "A",\n'
            '          "points": 1\n'
            '        }\n'
            '      ]\n'
            '    }\n'
            '  ]\n'
            "}"
        )

    def _parse_course(self, result: Any, role: str) -> Course:
        """Parse the agent output into a Course model."""
        # Extract the last message content from the agent result
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
            raise AgentError("ContentCreation",
                f"Invalid JSON from agent: {exc}") from exc

        lessons: list[Lesson] = []
        for idx, lesson_data in enumerate(data.get("lessons", [])):
            quiz_items: list[QuizQuestion] = []
            for q_idx, q in enumerate(lesson_data.get("quiz", [])):
                quiz_items.append(
                    QuizQuestion(
                        question_id=generate_id(f"q{q_idx}"),
                        prompt=q["prompt"],
                        question_type=q.get("question_type", "multiple_choice"),
                        options=q.get("options", []),
                        correct_answer=q.get("correct_answer"),
                        points=q.get("points", 1),
                    )
                )
            lessons.append(
                Lesson(
                    lesson_id=generate_id("lesson"),
                    title=lesson_data["title"],
                    content=lesson_data["content"],
                    order_index=idx,
                    estimated_minutes=lesson_data.get("estimated_minutes", 15),
                    quiz=quiz_items,
                )
            )

        return Course(
            course_id=generate_id("course"),
            title=data.get("title", f"Onboarding: {role}"),
            description=data.get("description", ""),
            role_target=role,
            lessons=lessons,
        )
