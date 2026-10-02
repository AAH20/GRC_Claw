"""Tests for candidate and job endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_create_candidate(test_client: TestClient, sample_candidate) -> None:
    """Test creating a candidate.

    Args:
        test_client: Test client fixture.
        sample_candidate: Sample candidate fixture.
    """
    response = test_client.post(
        "/api/v1/candidates",
        json=sample_candidate.model_dump(mode="json"),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_candidate.name
    assert data["id"] == str(sample_candidate.id)


def test_get_candidate(test_client: TestClient, sample_candidate) -> None:
    """Test getting a candidate by ID.

    Args:
        test_client: Test client fixture.
        sample_candidate: Sample candidate fixture.
    """
    response = test_client.get(f"/api/v1/candidates/{sample_candidate.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_candidate.id)
    assert data["name"] == sample_candidate.name


def test_get_candidate_not_found(test_client: TestClient) -> None:
    """Test getting a non-existent candidate.

    Args:
        test_client: Test client fixture.
    """
    from uuid import uuid4

    response = test_client.get(f"/api/v1/candidates/{uuid4()}")
    assert response.status_code == 404


def test_list_candidates(test_client: TestClient, sample_candidate) -> None:  # noqa: ARG001
    """Test listing candidates.

    Args:
        test_client: Test client fixture.
        sample_candidate: Sample candidate fixture.
    """
    response = test_client.get("/api/v1/candidates")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_create_job(test_client: TestClient, sample_job) -> None:
    """Test creating a job posting.

    Args:
        test_client: Test client fixture.
        sample_job: Sample job fixture.
    """
    response = test_client.post(
        "/api/v1/jobs",
        json=sample_job.model_dump(mode="json"),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_job.title
    assert data["id"] == str(sample_job.id)


def test_get_job(test_client: TestClient, sample_job) -> None:
    """Test getting a job by ID.

    Args:
        test_client: Test client fixture.
        sample_job: Sample job fixture.
    """
    response = test_client.get(f"/api/v1/jobs/{sample_job.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_job.id)
    assert data["title"] == sample_job.title


def test_get_job_not_found(test_client: TestClient) -> None:
    """Test getting a non-existent job.

    Args:
        test_client: Test client fixture.
    """
    from uuid import uuid4

    response = test_client.get(f"/api/v1/jobs/{uuid4()}")
    assert response.status_code == 404
