"""Delivery agent: orchestrates publishing and scheduling of content across LMS platforms."""  # noqa: E501

from __future__ import annotations

from typing import Any

from langchain_deepagents import create_deep_agent

from onboarding.config import get_settings
from onboarding.exceptions import AgentError, LmsIntegrationError
from onboarding.integrations.canvas import CanvasClient
from onboarding.integrations.moodle import MoodleClient
from onboarding.integrations.scorm import ScormClient
from onboarding.models import Course, LmsProvider
from onboarding.utils import get_logger

logger = get_logger(__name__)


class DeliveryAgent:
    """Orchestrates the delivery of courses to LMS platforms.

    Handles publishing, scheduling, and status tracking across Canvas,
    Moodle, and SCORM providers.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.delivery.enabled:
            raise AgentError("Delivery", "Agent is disabled in configuration")
        self._settings = settings
        self._agent = self._build_agent()
        self._clients: dict[LmsProvider, Any] = {}

    def _build_agent(self) -> Any:
        """Build the underlying LangChain DeepAgent."""
        config = self._settings
        system_message = (
            "You are an LMS delivery orchestrator. Given a course and target "
            "LMS provider, determine the optimal delivery strategy including "
            "publishing order, scheduling, and enrollment rules."
        )
        try:
            return create_deep_agent(
                model=config.openai_model,
                system_message=system_message,
                max_iterations=config.deepagents_max_iterations,
                temperature=config.model_temperature,
            )
        except Exception as exc:
            logger.error("Failed to build Delivery agent", error=str(exc))
            raise AgentError("Delivery", f"Agent initialization failed: {exc}") from exc

    def _get_client(self, provider: LmsProvider) -> Any:
        """Get or create an LMS client for the given provider."""
        if provider not in self._clients:
            if provider == LmsProvider.CANVAS:
                self._clients[provider] = CanvasClient()
            elif provider == LmsProvider.MOODLE:
                self._clients[provider] = MoodleClient()
            elif provider == LmsProvider.SCORM:
                self._clients[provider] = ScormClient()
        return self._clients[provider]

    async def deliver_course(
        self,
        course: Course,
        provider: LmsProvider | None = None,
        publish: bool | None = None,
    ) -> Course:
        """Deliver a course to the specified LMS provider.

        Args:
            course: The course to deliver.
            provider: Target LMS (defaults to course.lms_provider or config).
            publish: Whether to publish immediately (defaults to config).

        Returns:
            The updated Course with LMS IDs populated.

        Raises:
            AgentError: If delivery fails.
            LmsIntegrationError: If the LMS API call fails.
        """
        target = (
            provider
            or course.lms_provider
            or LmsProvider(self._settings.delivery.default_lms)
        )
        should_publish = (
            publish if publish is not None else self._settings.delivery.publish_draft
        )

        logger.info(
            "Delivering course",
            course_id=course.course_id,
            provider=target.value,
            publish=should_publish,
        )

        client = self._get_client(target)

        try:
            lms_course_id = await client.create_course(course)
            course.lms_course_id = lms_course_id

            for lesson in course.lessons:
                await client.create_lesson(course.lms_course_id, lesson)

            if should_publish:
                await client.publish_course(lms_course_id)

            course.status = "published" if should_publish else "draft"
            logger.info(
                "Course delivered successfully",
                course_id=course.course_id,
                lms_course_id=lms_course_id,
            )
            return course

        except LmsIntegrationError:
            raise
        except Exception as exc:
            logger.error(
                "Course delivery failed",
                course_id=course.course_id,
                error=str(exc),
            )
            raise AgentError("Delivery", f"Failed to deliver course: {exc}") from exc

    async def get_delivery_status(self, course: Course) -> dict[str, Any]:
        """Get the delivery status of a course from its LMS.

        Args:
            course: The course to check.

        Returns:
            A dict with status information from the LMS.
        """
        if not course.lms_course_id:
            return {"status": "not_delivered", "provider": course.lms_provider.value}

        client = self._get_client(course.lms_provider)
        try:
            return await client.get_course_status(course.lms_course_id)
        except Exception as exc:
            logger.error(
                "Failed to get delivery status",
                course_id=course.course_id,
                error=str(exc),
            )
            raise AgentError("Delivery", f"Status check failed: {exc}") from exc
