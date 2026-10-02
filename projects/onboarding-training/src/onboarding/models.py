"""Shared domain models for the Onboarding & Training platform."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Return the current UTC time."""
    return datetime.now(UTC)


class CourseStatus(StrEnum):
    """Lifecycle status of a course."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LearnerLevel(StrEnum):
    """Proficiency level of a learner."""

    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LmsProvider(StrEnum):
    """Supported LMS providers."""

    CANVAS = "canvas"
    MOODLE = "moodle"
    SCORM = "scorm"


class QuizQuestion(BaseModel):
    """A single quiz question within a lesson."""

    question_id: str
    prompt: str
    question_type: Literal["multiple_choice", "true_false", "short_answer", "essay"]
    options: list[str] = Field(default_factory=list)
    correct_answer: str | None = None
    points: int = Field(default=1, ge=1, le=100)


class Lesson(BaseModel):
    """A lesson within a course."""

    lesson_id: str
    title: str
    content: str
    order_index: int = Field(ge=0)
    estimated_minutes: int = Field(default=15, ge=1, le=300)
    quiz: list[QuizQuestion] = Field(default_factory=list)


class Course(BaseModel):
    """An onboarding course."""

    course_id: str
    title: str
    description: str
    role_target: str
    lessons: list[Lesson] = Field(default_factory=list)
    status: CourseStatus = CourseStatus.DRAFT
    lms_provider: LmsProvider = LmsProvider.CANVAS
    lms_course_id: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Learner(BaseModel):
    """A learner enrolled in onboarding."""

    learner_id: str
    email: str
    full_name: str
    role: str
    level: LearnerLevel = LearnerLevel.NOVICE
    enrolled_course_ids: list[str] = Field(default_factory=list)
    lms_user_id: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class AssessmentResult(BaseModel):
    """Result of grading a learner's response."""

    assessment_id: str
    learner_id: str
    course_id: str
    lesson_id: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    mastery_achieved: bool
    feedback: str
    graded_at: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CohortMetrics(BaseModel):
    """Aggregated metrics for a cohort."""

    cohort_id: str
    total_learners: int = Field(ge=0)
    active_learners: int = Field(ge=0)
    completion_rate: float = Field(ge=0.0, le=1.0)
    average_score: float = Field(ge=0.0, le=1.0)
    average_time_minutes: float = Field(ge=0.0)
    period_start: datetime
    period_end: datetime
    alerts: list[str] = Field(default_factory=list)
