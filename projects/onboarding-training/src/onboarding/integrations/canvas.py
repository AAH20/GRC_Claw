"""Canvas LMS integration client."""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from onboarding.config import get_settings
from onboarding.exceptions import LmsIntegrationError
from onboarding.models import Course, Lesson
from onboarding.utils import get_logger

logger = get_logger(__name__)


class CanvasClient:
    """Client for the Canvas LMS REST API.

    Supports course creation, lesson publishing, and status retrieval
    via the Canvas REST API v1.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.canvas.enabled:
            raise LmsIntegrationError("canvas", "Canvas integration is disabled")
        self._base_url = settings.canvas.base_url.rstrip("/")
        self._token = settings.canvas.api_token if hasattr(settings.canvas,
            "api_token") else ""
        self._timeout = settings.canvas.timeout_seconds
        self._page_size = settings.canvas.page_size

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_course(self, course: Course) -> str:
        """Create a course in Canvas.

        Args:
            course: The course to create.

        Returns:
            The Canvas course ID.

        Raises:
            LmsIntegrationError: If the API call fails.
        """
        url = f"{self._base_url}/accounts/1/courses"
        payload = {
            "course": {
                "name": course.title,
                "course_code": course.course_id,
                "description": course.description,
                "is_public": False,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    url,
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                canvas_id = str(data["id"])
                logger.info("Canvas course created",
                    canvas_id=canvas_id, title=course.title)
                return canvas_id
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Canvas API error",
                status=exc.response.status_code,
                body=exc.response.text[:500],
            )
            raise LmsIntegrationError(
                "canvas",
                f"Failed to create course: {exc.response.text[:200]}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Canvas request failed", error=str(exc))
            raise LmsIntegrationError("canvas", f"Request failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_lesson(self, canvas_course_id: str, lesson: Lesson) -> str:
        """Create a lesson (module item) in a Canvas course.

        Args:
            canvas_course_id: The Canvas course ID.
            lesson: The lesson to create.

        Returns:
            The Canvas module item ID.

        Raises:
            LmsIntegrationError: If the API call fails.
        """
        # First create a module
        module_url = f"{self._base_url}/courses/{canvas_course_id}/modules"
        module_payload = {
            "module": {
                "name": lesson.title,
                "position": lesson.order_index + 1,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                module_resp = await client.post(
                    module_url,
                    headers=self._headers(),
                    json=module_payload,
                )
                module_resp.raise_for_status()
                module_id = module_resp.json()["id"]

                # Add the lesson as a module item
                item_url = (
                    f"{self._base_url}/courses/{canvas_course_id}"
                    f"/modules/{module_id}/items"
                )
                item_payload = {
                    "module_item": {
                        "title": lesson.title,
                        "type": "Page",
                        "content": lesson.content,
                    }
                }
                item_resp = await client.post(
                    item_url,
                    headers=self._headers(),
                    json=item_payload,
                )
                item_resp.raise_for_status()
                item_id = str(item_resp.json()["id"])
                logger.info(
                    "Canvas lesson created",
                    module_id=module_id,
                    item_id=item_id,
                    title=lesson.title,
                )
                return item_id
        except httpx.HTTPStatusError as exc:
            raise LmsIntegrationError(
                "canvas",
                f"Failed to create lesson: {exc.response.text[:200]}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            raise LmsIntegrationError("canvas", f"Request failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def publish_course(self, canvas_course_id: str) -> None:
        """Publish a course in Canvas.

        Args:
            canvas_course_id: The Canvas course ID.

        Raises:
            LmsIntegrationError: If the API call fails.
        """
        url = f"{self._base_url}/courses/{canvas_course_id}"
        payload = {"course": {"event": "offer"}}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.put(url, headers=self._headers(), json=payload)
                response.raise_for_status()
                logger.info("Canvas course published", canvas_id=canvas_course_id)
        except httpx.HTTPStatusError as exc:
            raise LmsIntegrationError(
                "canvas",
                f"Failed to publish course: {exc.response.text[:200]}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            raise LmsIntegrationError("canvas", f"Request failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_course_status(self, canvas_course_id: str) -> dict[str, Any]:
        """Get the status of a Canvas course.

        Args:
            canvas_course_id: The Canvas course ID.

        Returns:
            Dict with course status information.

        Raises:
            LmsIntegrationError: If the API call fails.
        """
        url = f"{self._base_url}/courses/{canvas_course_id}"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers=self._headers())
                response.raise_for_status()
                data = response.json()
                return {
                    "status": "published"
                        if data.get("workflow_state") == "available" else "unpublished",
                    "name": data.get("name"),
                    "workflow_state": data.get("workflow_state"),
                }
        except httpx.HTTPStatusError as exc:
            raise LmsIntegrationError(
                "canvas",
                f"Failed to get course status: {exc.response.text[:200]}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            raise LmsIntegrationError("canvas", f"Request failed: {exc}") from exc

    def _headers(self) -> dict[str, str]:
        """Build request headers with authorization."""
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
