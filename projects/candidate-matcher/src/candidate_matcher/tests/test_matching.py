"""Tests for matching endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from candidate_matcher.models.schemas import MatchRequest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_match_candidates(test_client: TestClient, sample_job, sample_candidate) -> None:
    """Test matching candidates to a job.

    Args:
        test_client: Test client fixture.
        sample_job: Sample job fixture.
        sample_candidate: Sample candidate fixture.
    """
    request = MatchRequest(
        job_id=sample_job.id,
        candidate_ids=[sample_candidate.id],
        top_k=10,
        include_explanation=False,
    )
    response = test_client.post("/api/v1/match", json=request.model_dump(mode="json"))
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) > 0
    result = results[0]
    assert "overall_score" in result
    assert "semantic_score" in result
    assert "skills_score" in result
    assert "rank" in result


def test_match_candidates_not_found(test_client: TestClient) -> None:
    """Test matching with non-existent job.

    Args:
        test_client: Test client fixture.
    """
    from uuid import uuid4

    request = MatchRequest(job_id=uuid4(), top_k=10)
    response = test_client.post("/api/v1/match", json=request.model_dump(mode="json"))
    assert response.status_code == 404


def test_batch_match(test_client: TestClient, sample_job, sample_candidate) -> None:
    """Test batch matching.

    Args:
        test_client: Test client fixture.
        sample_job: Sample job fixture.
        sample_candidate: Sample candidate fixture.
    """
    from candidate_matcher.models.schemas import BatchMatchRequest

    request = BatchMatchRequest(
        job_id=sample_job.id,
        candidate_ids=[sample_candidate.id],
    )
    response = test_client.post("/api/v1/match/batch", json=request.model_dump(mode="json"))
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_candidates" in data
    assert data["total_candidates"] == 1
