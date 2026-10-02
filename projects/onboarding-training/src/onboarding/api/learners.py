"""API routes for learner management."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from onboarding.models import AssessmentResult, Learner, LearnerLevel
from onboarding.utils import generate_id, get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/learners", tags=["learners"])

# In-memory store for demo purposes; replace with a real database in production.
_learners: dict[str, Learner] = {}
_assessments: dict[str, list[AssessmentResult]] = {}


@router.post("", response_model=Learner, status_code=status.HTTP_201_CREATED)
async def create_learner(
    email: str,
    full_name: str,
    role: str,
    level: LearnerLevel = LearnerLevel.NOVICE,
) -> Learner:
    """Register a new learner.

    Args:
        email: Learner email address.
        full_name: Learner full name.
        role: Learner job role.
        level: Proficiency level.

    Returns:
        The newly created learner.
    """
    learner = Learner(
        learner_id=generate_id("learner"),
        email=email,
        full_name=full_name,
        role=role,
        level=level,
    )
    _learners[learner.learner_id] = learner
    _assessments[learner.learner_id] = []
    logger.info("Learner created", learner_id=learner.learner_id, email=email)
    return learner


@router.get("/{learner_id}", response_model=Learner)
async def get_learner(learner_id: str) -> Learner:
    """Get a learner by ID.

    Args:
        learner_id: The learner identifier.

    Returns:
        The learner.

    Raises:
        HTTPException: 404 if not found.
    """
    learner = _learners.get(learner_id)
    if learner is None:
        raise HTTPException(status_code=404, detail=f"Learner {learner_id} not found")
    return learner


@router.get("", response_model=list[Learner])
async def list_learners(role: str | None = None) -> list[Learner]:
    """List all learners, optionally filtered by role.

    Args:
        role: Filter by job role.

    Returns:
        List of learners.
    """
    learners = list(_learners.values())
    if role:
        learners = [learner for learner in learners if learner.role == role]
    return learners


@router.post("/{learner_id}/enroll", response_model=Learner)
async def enroll_learner(learner_id: str, course_id: str) -> Learner:
    """Enroll a learner in a course.

    Args:
        learner_id: The learner to enroll.
        course_id: The course to enroll in.

    Returns:
        The updated learner.

    Raises:
        HTTPException: 404 if learner not found.
    """
    learner = _learners.get(learner_id)
    if learner is None:
        raise HTTPException(status_code=404, detail=f"Learner {learner_id} not found")

    if course_id not in learner.enrolled_course_ids:
        learner.enrolled_course_ids.append(course_id)
        logger.info("Learner enrolled", learner_id=learner_id, course_id=course_id)
    return learner


@router.get("/{learner_id}/assessments", response_model=list[AssessmentResult])
async def get_learner_assessments(learner_id: str) -> list[AssessmentResult]:
    """Get all assessment results for a learner.

    Args:
        learner_id: The learner identifier.

    Returns:
        List of assessment results.

    Raises:
        HTTPException: 404 if learner not found.
    """
    if learner_id not in _learners:
        raise HTTPException(status_code=404, detail=f"Learner {learner_id} not found")
    return _assessments.get(learner_id, [])


@router.get("/{learner_id}/progress")
async def get_learner_progress(learner_id: str) -> dict:
    """Get progress summary for a learner.

    Args:
        learner_id: The learner identifier.

    Returns:
        Progress summary with completion percentage and scores.

    Raises:
        HTTPException: 404 if learner not found.
    """
    if learner_id not in _learners:
        raise HTTPException(status_code=404, detail=f"Learner {learner_id} not found")

    results = _assessments.get(learner_id, [])
    learner = _learners[learner_id]

    total_courses = len(learner.enrolled_course_ids)
    completed_courses = len({r.course_id for r in results if r.passed})
    avg_score = sum(r.score for r in results) / len(results) if results else 0.0

    return {
        "learner_id": learner_id,
        "enrolled_courses": total_courses,
        "completed_courses": completed_courses,
        "completion_rate": completed_courses / total_courses
            if total_courses > 0 else 0.0,
        "average_score": avg_score,
        "total_assessments": len(results),
    }
