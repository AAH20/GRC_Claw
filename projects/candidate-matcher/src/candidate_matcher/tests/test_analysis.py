"""Tests for analysis endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_skills_gap_analysis(test_client: TestClient, sample_candidate, sample_job) -> None:
    """Test skills gap analysis endpoint.

    Args:
        test_client: Test client fixture.
        sample_candidate: Sample candidate fixture.
        sample_job: Sample job fixture.
    """
    response = test_client.post(
        f"/api/v1/analyze/skills-gap?candidate_id={sample_candidate.id}&job_id={sample_job.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "gap_score" in data
    assert "coverage_ratio" in data
    assert "missing_skills" in data
    assert "matching_skills" in data


def test_bias_analysis(test_client: TestClient, sample_candidate, sample_job) -> None:
    """Test bias analysis endpoint.

    Args:
        test_client: Test client fixture.
        sample_candidate: Sample candidate fixture.
        sample_job: Sample job fixture.
    """
    response = test_client.post(
        f"/api/v1/analyze/bias?candidate_id={sample_candidate.id}&job_id={sample_job.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "bias_detected" in data
    assert "bias_score" in data
    assert "recommendations" in data


def test_culture_fit_assessment(test_client: TestClient, sample_candidate, sample_job) -> None:
    """Test culture fit assessment endpoint.

    Args:
        test_client: Test client fixture.
        sample_candidate: Sample candidate fixture.
        sample_job: Sample job fixture.
    """
    response = test_client.post(
        f"/api/v1/analyze/culture-fit?candidate_id={sample_candidate.id}&job_id={sample_job.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "fit_score" in data
    assert "aligned_values" in data
    assert "summary" in data
