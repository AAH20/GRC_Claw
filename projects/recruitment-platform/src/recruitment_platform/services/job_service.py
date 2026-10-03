"""Job service for recruitment platform."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


class JobServiceError(Exception):
    """Base exception for job service errors."""


class JobNotFoundError(JobServiceError):
    """Raised when a job is not found."""


class JobValidationError(JobServiceError):
    """Raised when job data fails validation."""


@dataclass
class Job:
    """Represents a job posting."""

    id: str
    title: str
    description: str
    company: str
    location: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    employment_type: str = "full-time"
    status: str = "open"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# In-memory store for demonstration
_jobs: Dict[str, Job] = {}


def _validate_job_data(data: Dict[str, Any]) -> None:
    """Validate job data before creation.

    Args:
        data: Dictionary containing job fields.

    Raises:
        JobValidationError: If required fields are missing or invalid.
    """
    required_fields = ["title", "description", "company", "location"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        raise JobValidationError(
            f"Missing required fields: {', '.join(missing)}"
        )

    if data.get("salary_min") is not None and data.get("salary_max") is not None:
        if data["salary_min"] > data["salary_max"]:
            raise JobValidationError("salary_min cannot exceed salary_max")

    valid_types = {"full-time", "part-time", "contract", "internship", "temporary"}
    if data.get("employment_type", "full-time") not in valid_types:
        raise JobValidationError(
            f"employment_type must be one of: {', '.join(valid_types)}"
        )


def create_job(data: Dict[str, Any]) -> Job:
    """Create a new job posting with validation.

    Args:
        data: Dictionary containing job fields (title, description, company,
              location, salary_min, salary_max, employment_type, tags, etc.).

    Returns:
        The created Job instance.

    Raises:
        JobValidationError: If required fields are missing or data is invalid.
    """
    _validate_job_data(data)

    job_id = str(uuid.uuid4())
    now = datetime.utcnow()

    job = Job(
        id=job_id,
        title=data["title"],
        description=data["description"],
        company=data["company"],
        location=data["location"],
        salary_min=data.get("salary_min"),
        salary_max=data.get("salary_max"),
        employment_type=data.get("employment_type", "full-time"),
        status=data.get("status", "open"),
        created_at=now,
        updated_at=now,
        tags=data.get("tags", []),
        metadata=data.get("metadata", {}),
    )

    _jobs[job_id] = job
    return job


def get_job(job_id: str) -> Job:
    """Retrieve a job by its ID.

    Args:
        job_id: The unique identifier of the job.

    Returns:
        The Job instance.

    Raises:
        JobNotFoundError: If no job exists with the given ID.
    """
    job = _jobs.get(job_id)
    if job is None:
        raise JobNotFoundError(f"Job with id '{job_id}' not found")
    return job


def list_jobs(
    filters: Optional[Dict[str, Any]] = None,
    pagination: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """List jobs with optional filtering and pagination.

    Args:
        filters: Optional filter criteria (company, location, status,
                 employment_type, tags).
        pagination: Optional pagination params (page, per_page).

    Returns:
        Dictionary with 'jobs' list, 'total' count, 'page', and 'per_page'.
    """
    filters = filters or {}
    pagination = pagination or {}

    page = max(1, pagination.get("page", 1))
    per_page = min(100, max(1, pagination.get("per_page", 20)))

    results: List[Job] = list(_jobs.values())

    # Apply filters
    if filters.get("company"):
        results = [j for j in results if j.company.lower() == filters["company"].lower()]
    if filters.get("location"):
        results = [j for j in results if j.location.lower() == filters["location"].lower()]
    if filters.get("status"):
        results = [j for j in results if j.status == filters["status"]]
    if filters.get("employment_type"):
        results = [j for j in results if j.employment_type == filters["employment_type"]]
    if filters.get("tags"):
        tag_set = set(filters["tags"])
        results = [j for j in results if tag_set.issubset(set(j.tags))]

    total = len(results)

    # Apply pagination
    start = (page - 1) * per_page
    end = start + per_page
    paginated = results[start:end]

    return {
        "jobs": paginated,
        "total": total,
        "page": page,
        "per_page": per_page,
    }
