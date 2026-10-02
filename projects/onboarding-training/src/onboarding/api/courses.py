"""API routes for course management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from onboarding.agents.content_creation import ContentCreationAgent
from onboarding.agents.delivery import DeliveryAgent
from onboarding.exceptions import AgentError
from onboarding.models import Course, CourseStatus, LmsProvider
from onboarding.utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])

# In-memory store for demo purposes; replace with a real database in production.
_courses: dict[str, Course] = {}


async def _get_content_agent() -> ContentCreationAgent:
    """Dependency to get the Content Creation agent."""
    try:
        return ContentCreationAgent()
    except AgentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


async def _get_delivery_agent() -> DeliveryAgent:
    """Dependency to get the Delivery agent."""
    try:
        return DeliveryAgent()
    except AgentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("", response_model=Course, status_code=status.HTTP_201_CREATED)
async def create_course(
    role: str,
    level: str = "novice",
    language: str | None = None,
    agent: ContentCreationAgent = Depends(_get_content_agent),  # noqa: B008
) -> Course:
    """Create a new onboarding course for a role.

    Args:
        role: Target job role.
        level: Learner proficiency level.
        language: Content language.
        agent: Injected Content Creation agent.

    Returns:
        The newly created course.
    """
    course = await agent.create_course(role=role, level=level, language=language)
    _courses[course.course_id] = course
    logger.info("Course created via API", course_id=course.course_id, role=role)
    return course


@router.get("/{course_id}", response_model=Course)
async def get_course(course_id: str) -> Course:
    """Get a course by ID.

    Args:
        course_id: The course identifier.

    Returns:
        The course.

    Raises:
        HTTPException: 404 if not found.
    """
    course = _courses.get(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")
    return course


@router.get("", response_model=list[Course])
async def list_courses(
    status_filter: CourseStatus | None = None,
) -> list[Course]:
    """List all courses, optionally filtered by status.

    Args:
        status_filter: Filter by course status.

    Returns:
        List of courses.
    """
    courses = list(_courses.values())
    if status_filter:
        courses = [c for c in courses if c.status == status_filter]
    return courses


@router.post("/{course_id}/deliver", response_model=Course)
async def deliver_course(
    course_id: str,
    provider: LmsProvider | None = None,
    publish: bool | None = None,
    agent: DeliveryAgent = Depends(_get_delivery_agent),  # noqa: B008
) -> Course:
    """Deliver a course to an LMS.

    Args:
        course_id: The course to deliver.
        provider: Target LMS provider.
        publish: Whether to publish immediately.
        agent: Injected Delivery agent.

    Returns:
        The updated course with LMS IDs.

    Raises:
        HTTPException: 404 if course not found.
    """
    course = _courses.get(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    updated = await agent.deliver_course(course, provider=provider, publish=publish)
    _courses[course_id] = updated
    return updated


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: str) -> None:
    """Delete a course.

    Args:
        course_id: The course to delete.

    Raises:
        HTTPException: 404 if not found.
    """
    if course_id not in _courses:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")
    del _courses[course_id]
    logger.info("Course deleted", course_id=course_id)
