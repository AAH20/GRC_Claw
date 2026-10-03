"""Application service for managing job applications."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ApplicationStatus(str, Enum):
    """Valid application statuses."""

    PENDING = "pending"
    REVIEWING = "viewing"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApplicationError(Exception):
    """Base exception for application service errors."""


class ValidationError(ApplicationError):
    """Raised when application data fails validation."""


class ApplicationNotFoundError(ApplicationError):
    """Raised when an application is not found."""


class InvalidStatusError(ApplicationError):
    """Raised when an invalid status is provided."""


@dataclass
class Application:
    """Represents a job application."""

    id: str
    job_id: str
    candidate_id: str
    status: ApplicationStatus = ApplicationStatus.PENDING
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PaginationParams:
    """Pagination parameters."""

    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValidationError("Page must be >= 1")
        if self.page_size < 1 or self.page_size > 100:
            raise ValidationError("Page size must be between 1 and 100")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass
class ApplicationFilters:
    """Filters for listing applications."""

    job_id: Optional[str] = None
    candidate_id: Optional[str] = None
    status: Optional[ApplicationStatus] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class ApplicationService:
    """Service for managing job applications."""

    def __init__(self, repository: Any) -> None:
        """Initialize with a repository for persistence.

        Args:
            repository: An object with create, update, get, and list methods.
        """
        self._repo = repository

    def create_application(self, data: Dict[str, Any]) -> Application:
        """Create a new job application with validation.

        Args:
            data: Dictionary containing application data.
                Required keys: job_id, candidate_id
                Optional keys: cover_letter, resume_url, metadata

        Returns:
            The created Application instance.

        Raises:
            ValidationError: If required fields are missing or invalid.
        """
        if not isinstance(data, dict):
            raise ValidationError("Application data must be a dictionary")

        job_id = data.get("job_id")
        candidate_id = data.get("candidate_id")

        if not job_id or not isinstance(job_id, str):
            raise ValidationError("job_id is required and must be a string")

        if not candidate_id or not isinstance(candidate_id, str):
            raise ValidationError("candidate_id is required and must be a string")

        cover_letter = data.get("cover_letter")
        if cover_letter is not None and not isinstance(cover_letter, str):
            raise ValidationError("cover_letter must be a string if provided")

        resume_url = data.get("resume_url")
        if resume_url is not None and not isinstance(resume_url, str):
            raise ValidationError("resume_url must be a string if provided")

        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValidationError("metadata must be a dictionary if provided")

        application = Application(
            id="",
            job_id=job_id,
            candidate_id=candidate_id,
            cover_letter=cover_letter,
            resume_url=resume_url,
            metadata=metadata,
        )

        try:
            result = self._repo.create(application)
            logger.info("Created application for job=%s candidate=%s", job_id, candidate_id)
            return result
        except Exception as exc:
            logger.error("Failed to create application: %s", exc)
            raise ApplicationError(f"Failed to create application: {exc}") from exc

    def update_application_status(
        self, application_id: str, status: str
    ) -> Application:
        """Update the status of an existing application.

        Args:
            application_id: The unique identifier of the application.
            status: The new status value.

        Returns:
            The updated Application instance.

        Raises:
            ValidationError: If application_id or status is invalid.
            ApplicationNotFoundError: If the application does not exist.
            InvalidStatusError: If the status value is not valid.
        """
        if not application_id or not isinstance(application_id, str):
            raise ValidationError("application_id is required and must be a string")

        if not status or not isinstance(status, str):
            raise ValidationError("status is required and must be a string")

        try:
            new_status = ApplicationStatus(status.lower())
        except ValueError:
            valid = [s.value for s in ApplicationStatus]
            raise InvalidStatusError(
                f"Invalid status '{status}'. Valid statuses: {valid}"
            )

        try:
            application = self._repo.get(application_id)
        except Exception as exc:
            logger.error("Failed to fetch application %s: %s", application_id, exc)
            raise ApplicationNotFoundError(
                f"Application '{application_id}' not found"
            ) from exc

        if application is None:
            raise ApplicationNotFoundError(
                f"Application '{application_id}' not found"
            )

        application.status = new_status
        application.updated_at = datetime.utcnow()

        try:
            result = self._repo.update(application)
            logger.info("Updated application %s status to %s", application_id, new_status.value)
            return result
        except Exception as exc:
            logger.error("Failed to update application %s: %s", application_id, exc)
            raise ApplicationError(f"Failed to update application: {exc}") from exc

    def list_applications(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List applications with optional filtering and pagination.

        Args:
            filters: Optional filter criteria (job_id, candidate_id, status,
                created_after, created_before).
            pagination: Optional pagination params (page, page_size).

        Returns:
            Dictionary with 'items', 'total', 'page', 'page_size' keys.

        Raises:
            ValidationError: If filter or pagination params are invalid.
        """
        filters = filters or {}
        pagination = pagination or {}

        app_filters = ApplicationFilters(
            job_id=filters.get("job_id"),
            candidate_id=filters.get("candidate_id"),
            status=ApplicationStatus(filters["status"]) if filters.get("status") else None,
            created_after=filters.get("created_after"),
            created_before=filters.get("created_before"),
        )

        page = pagination.get("page", 1)
        page_size = pagination.get("page_size", 20)
        params = PaginationParams(page=page, page_size=page_size)

        try:
            items, total = self._repo.list(
                filters=app_filters,
                offset=params.offset,
                limit=params.page_size,
            )
        except Exception as exc:
            logger.error("Failed to list applications: %s", exc)
            raise ApplicationError(f"Failed to list applications: {exc}") from exc

        return {
            "items": items,
            "total": total,
            "page": params.page,
            "page_size": params.page_size,
        }
