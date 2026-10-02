"""Job posting endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from candidate_matcher.models.schemas import JobPosting

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("", response_model=JobPosting, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: Request,
    job: JobPosting,
) -> JobPosting:
    """Create a new job posting.

    Args:
        request: FastAPI request object.
        job: Job posting to create.

    Returns:
        The created job posting.
    """
    store: dict[UUID, JobPosting] = request.app.state.job_store
    store[job.id] = job
    return job


@router.get("/{job_id}", response_model=JobPosting)
async def get_job(
    request: Request,
    job_id: UUID,
) -> JobPosting:
    """Get a job posting by ID.

    Args:
        request: FastAPI request object.
        job_id: Job identifier.

    Returns:
        The job posting.

    Raises:
        HTTPException: If job not found.
    """
    store: dict[UUID, JobPosting] = request.app.state.job_store
    job = store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    return job


@router.get("", response_model=list[JobPosting])
async def list_jobs(
    request: Request,
    skip: int = 0,
    limit: int = 100,
) -> list[JobPosting]:
    """List all job postings.

    Args:
        request: FastAPI request object.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        List of job postings.
    """
    store: dict[UUID, JobPosting] = request.app.state.job_store
    jobs = list(store.values())
    return jobs[skip : skip + limit]
