"""Unit tests for the Job Service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from recruitment_platform.services.job_service import JobService
from recruitment_platform.models.job import Job, JobStatus, JobType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repository():
    """Provide a mocked JobRepository."""
    repo = MagicMock()
    return repo


@pytest.fixture
def job_service(mock_repository):
    """Provide a JobService backed by the mocked repository."""
    return JobService(repository=mock_repository)


@pytest.fixture
def sample_job_payload():
    """Return a valid payload for creating a job."""
    return {
        "title": "Senior Backend Engineer",
        "description": "Build and maintain scalable APIs.",
        "department": "Engineering",
        "location": "Remote",
        "employment_type": JobType.FULL_TIME,
        "salary_min": 120_000,
        "salary_max": 180_000,
        "currency": "USD",
        "hiring_manager_id": "hm-001",
        "department_id": "dept-eng",
    }


@pytest.fixture
def sample_job(sample_job_payload):
    """Return a persisted Job instance."""
    return Job(
        id="job-001",
        **sample_job_payload,
        status=JobStatus.DRAFT,
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        updated_at=datetime(2026, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def sample_jobs(sample_job_payload):
    """Return a list of multiple Job instances."""
    jobs = []
    for i in range(3):
        jobs.append(
            Job(
                id=f"job-{i:03d}",
                **{**sample_job_payload, "title": f"Role {i}"},
                status=JobStatus.OPEN if i % 2 == 0 else JobStatus.DRAFT,
                created_at=datetime(2026, 1, 1) + timedelta(days=i),
                updated_at=datetime(2026, 1, 1) + timedelta(days=i),
            )
        )
    return jobs


# ---------------------------------------------------------------------------
# Tests — create_job
# ---------------------------------------------------------------------------


class TestCreateJob:
    """Tests for JobService.create_job."""

    def test_create_job(self, job_service, mock_repository, sample_job_payload, sample_job):
        """Successfully create a job and return the persisted entity."""
        mock_repository.create.return_value = sample_job

        result = job_service.create_job(**sample_job_payload)

        mock_repository.create.assert_called_once()
        assert result is not None
        assert result.id == "job-001"
        assert result.title == "Senior Backend Engineer"
        assert result.status == JobStatus.DRAFT
        assert result.department == "Engineering"
        assert result.employment_type == JobType.FULL_TIME

    def test_create_job_sets_default_status(
        self, job_service, mock_repository, sample_job_payload, sample_job
    ):
        """Newly created jobs default to DRAFT status."""
        mock_repository.create.return_value = sample_job

        result = job_service.create_job(**sample_job_payload)

        assert result.status == JobStatus.DRAFT

    def test_create_job_persists_all_fields(
        self, job_service, mock_repository, sample_job_payload, sample_job
    ):
        """All provided fields are forwarded to the repository."""
        mock_repository.create.return_value = sample_job

        job_service.create_job(**sample_job_payload)

        call_kwargs = mock_repository.create.call_args
        persisted = call_kwargs[0][0] if call_kwargs[0] else call_kwargs[1].get("job")
        assert persisted.title == sample_job_payload["title"]
        assert persisted.description == sample_job_payload["description"]
        assert persisted.salary_min == sample_job_payload["salary_min"]
        assert persisted.salary_max == sample_job_payload["salary_max"]
        assert persisted.hiring_manager_id == sample_job_payload["hiring_manager_id"]

    def test_create_job_raises_on_repository_failure(
        self, job_service, mock_repository, sample_job_payload
    ):
        """Repository exceptions propagate to the caller."""
        mock_repository.create.side_effect = RuntimeError("DB connection lost")

        with pytest.raises(RuntimeError, match="DB connection lost"):
            job_service.create_job(**sample_job_payload)

    def test_create_job_validates_required_fields(self, job_service):
        """Missing required fields raise a ValueError."""
        with pytest.raises(ValueError):
            job_service.create_job(title="", description="No title provided")


# ---------------------------------------------------------------------------
# Tests — get_job
# ---------------------------------------------------------------------------


class TestGetJob:
    """Tests for JobService.get_job."""

    def test_get_job(self, job_service, mock_repository, sample_job):
        """Retrieve a job by its ID."""
        mock_repository.get_by_id.return_value = sample_job

        result = job_service.get_job("job-001")

        mock_repository.get_by_id.assert_called_once_with("job-001")
        assert result is not None
        assert result.id == "job-001"
        assert result.title == "Senior Backend Engineer"
        assert result.status == JobStatus.DRAFT

    def test_get_job_returns_none_when_not_found(self, job_service, mock_repository):
        """Return None when the job does not exist."""
        mock_repository.get_by_id.return_value = None

        result = job_service.get_job("nonexistent-id")

        assert result is None

    def test_get_job_raises_on_repository_failure(self, job_service, mock_repository):
        """Repository exceptions propagate to the caller."""
        mock_repository.get_by_id.side_effect = RuntimeError("DB timeout")

        with pytest.raises(RuntimeError, match="DB timeout"):
            job_service.get_job("job-001")

    def test_get_job_does_not_call_create(self, job_service, mock_repository, sample_job):
        """get_job must only read, never write."""
        mock_repository.get_by_id.return_value = sample_job

        job_service.get_job("job-001")

        mock_repository.create.assert_not_called()


# ---------------------------------------------------------------------------
# Tests — list_jobs
# ---------------------------------------------------------------------------


class TestListJobs:
    """Tests for JobService.list_jobs."""

    def test_list_jobs(self, job_service, mock_repository, sample_jobs):
        """Retrieve all jobs when no filters are applied."""
        mock_repository.list.return_value = sample_jobs

        result = job_service.list_jobs()

        mock_repository.list.assert_called_once()
        assert len(result) == 3
        assert all(isinstance(j, Job) for j in result)

    def test_list_jobs_returns_empty_list_when_no_jobs(self, job_service, mock_repository):
        """Return an empty list when no jobs exist."""
        mock_repository.list.return_value = []

        result = job_service.list_jobs()

        assert result == []

    def test_list_jobs_filters_by_status(self, job_service, mock_repository, sample_jobs):
        """Filter jobs by status."""
        open_jobs = [j for j in sample_jobs if j.status == JobStatus.OPEN]
        mock_repository.list.return_value = open_jobs

        result = job_service.list_jobs(status=JobStatus.OPEN)

        assert len(result) == 2
        assert all(j.status == JobStatus.OPEN for j in result)

    def test_list_jobs_filters_by_department(self, job_service, mock_repository, sample_jobs):
        """Filter jobs by department."""
        mock_repository.list.return_value = sample_jobs

        result = job_service.list_jobs(department="Engineering")

        assert len(result) == 3
        assert all(j.department == "Engineering" for j in result)

    def test_list_jobs_pagination(self, job_service, mock_repository, sample_jobs):
        """Respect limit and offset parameters."""
        mock_repository.list.return_value = sample_jobs[:2]

        result = job_service.list_jobs(limit=2, offset=0)

        assert len(result) == 2
        call_kwargs = mock_repository.list.call_args[1]
        assert call_kwargs.get("limit") == 2
        assert call_kwargs.get("offset") == 0

    def test_list_jobs_raises_on_repository_failure(self, job_service, mock_repository):
        """Repository exceptions propagate to the caller."""
        mock_repository.list.side_effect = RuntimeError("DB unavailable")

        with pytest.raises(RuntimeError, match="DB unavailable"):
            job_service.list_jobs()

    def test_list_jobs_returns_list_even_for_single_result(
        self, job_service, mock_repository, sample_job
    ):
        """Always return a list, even for a single result."""
        mock_repository.list.return_value = [sample_job]

        result = job_service.list_jobs()

        assert isinstance(result, list)
        assert len(result) == 1
