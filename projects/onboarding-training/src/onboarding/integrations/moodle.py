"""Moodle LMS integration client."""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from onboarding.config import get_settings
from onboarding.exceptions import LmsIntegrationError
from onboarding.models import Course, Lesson
from onboarding.utils import get_logger

logger = get_logger(__name__)


class MoodleClient:
    """Client for the Moodle Web Services API.

    Supports course creation, lesson publishing, and status retrieval
    via the Moodle REST web service protocol.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.moodle.enabled:
            raise LmsIntegrationError("moodle", "Moodle integration is disabled")
        self._base_url = settings.moodle.base_url.rstrip("/")
        self._ws_endpoint = settings.moodle.webservice_endpoint
        self._token = settings.moodle.ws_token if hasattr(settings.moodle,
            "ws_token") else ""
        self._timeout = settings.moodle.timeout_seconds

    def _ws_url(self) -> str:
        """Build the full web service URL."""
        return f"{self._base_url}{self._ws_endpoint}"

    def _params(self,
        wsfunction: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build request parameters for a web service call."""
        params: dict[str, Any] = {
            "wstoken": self._token,
            "wsfunction": wsfunction,
            "moodlewsrestformat": "json",
        }
        if extra:
            params.update(extra)
        return params

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_course(self, course: Course) -> str:
        """Create a course in Moodle.

        Args:
            course: The course to create.

        Returns:
            The Moodle course ID.

        Raises:
            LmsIntegrationError: If the API call fails.
        """
        params = self._params(
            "core_course_create_courses",
            {
                "courses[0][fullname]": course.title,
                "courses[0][shortname]": course.course_id,
                "courses[0][summary]": course.description,
                "courses[0][visible]": 1,
            },
        )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._ws_url(), data=params)
                response.raise_for_status()
                data = response.json()

                if isinstance(data, list) and len(data) > 0:
                    moodle_id = str(data[0]["id"])
                    logger.info("Moodle course created",
                        moodle_id=moodle_id, title=course.title)
                    return moodle_id
                elif isinstance(data, dict) and "exception" in data:
                    raise LmsIntegrationError("moodle",
                        data.get("message", "Unknown error"))
                else:
                    raise LmsIntegrationError("moodle", f"Unexpected response: {data}")
        except httpx.HTTPStatusError as exc:
            raise LmsIntegrationError(
                "moodle",
                f"Failed to create course: {exc.response.text[:200]}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            raise LmsIntegrationError("moodle", f"Request failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_lesson(self, moodle_course_id: str, lesson: Lesson) -> str:
        """Create a lesson (label/resource) in a Moodle course.

        Args:
            moodle_course_id: The Moodle course ID.
            lesson: The lesson to create.

        Returns:
            The Moodle activity ID.

        Raises:
            LmsIntegrationError: If the API call fails.
        """
        params = self._params(
            "core_course_create_modules",
            {
                "modules[0][course]": moodle_course_id,
                "modules[0][module]": 1,  # Label module type
                "modules[0][instance]": 0,
                "modules[0][section]": lesson.order_index,
                "modules[0][title]": lesson.title,
                "modules[0][content]": lesson.content,
            },
        )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._ws_url(), data=params)
                response.raise_for_status()
                data = response.json()

                if isinstance(data, list) and len(data) > 0:
                    activity_id = str(data[0].get("id", ""))
                    logger.info("Moodle lesson created",
                        activity_id=activity_id, title=lesson.title)
                    return activity_id
                elif isinstance(data, dict) and "exception" in data:
                    raise LmsIntegrationError("moodle",
                        data.get("message", "Unknown error"))
                else:
                    raise LmsIntegrationError("moodle", f"Unexpected response: {data}")
        except httpx.HTTPStatusError as exc:
            raise LmsIntegrationError(
                "moodle",
                f"Failed to create lesson: {exc.response.text[:200]}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            raise LmsIntegrationError("moodle", f"Request failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def publish_course(self, moodle_course_id: str) -> None:
        """Publish (make visible) a Moodle course.

        Args:
            moodle_course_id: The Moodle course ID.

        Raises:
            LmsIntegrationError: If the API call fails.
        """
        params = self._params(
            "core_course_update_courses",
            {"courses[0][id]": moodle_course_id, "courses[0][visible]": 1},
        )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._ws_url(), data=params)
                response.raise_for_status()
                logger.info("Moodle course published", moodle_id=moodle_course_id)
        except httpx.HTTPStatusError as exc:
            raise LmsIntegrationError(
                "moodle",
                f"Failed to publish course: {exc.response.text[:200]}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            raise LmsIntegrationError("moodle", f"Request failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_course_status(self, moodle_course_id: str) -> dict[str, Any]:
        """Get the status of a Moodle course.

        Args:
            moodle_course_id: The Moodle course ID.

        Returns:
            Dict with course status information.

        Raises:
            LmsIntegrationError: If the API call fails.
        """
        params = self._params(
            "core_course_get_courses",
            {"options[ids][0]": moodle_course_id},
        )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._ws_url(), data=params)
                response.raise_for_status()
                data = response.json()

                if isinstance(data, list) and len(data) > 0:
                    course_data = data[0]
                    return {
                        "status": "published"
                            if course_data.get("visible") == 1 else "unpublished",
                        "name": course_data.get("fullname"),
                        "visible": course_data.get("visible"),
                    }
                elif isinstance(data, dict) and "exception" in data:
                    raise LmsIntegrationError("moodle",
                        data.get("message", "Unknown error"))
                else:
                    raise LmsIntegrationError("moodle", f"Unexpected response: {data}")
        except httpx.HTTPStatusError as exc:
            raise LmsIntegrationError(
                "moodle",
                f"Failed to get course status: {exc.response.text[:200]}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            raise LmsIntegrationError("moodle", f"Request failed: {exc}") from exc
