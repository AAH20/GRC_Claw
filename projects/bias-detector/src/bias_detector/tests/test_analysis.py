"""Tests for analysis endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_analyze_demographics(client: TestClient) -> None:
    """Test demographic analysis endpoint.

    Args:
        client: Test client fixture.
    """
    response = client.post(
        "/api/v1/analyze/demographics",
        json={
            "demographic_data": {
                "total_candidates": 100,
                "gender_distribution": {"male": 60, "female": 40},
                "ethnicity_distribution": {"white": 70, "asian": 20, "black": 10},
            },
            "threshold": 0.15,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "disparities" in data
    assert "overall_diversity_score" in data
    assert "underrepresented_groups" in data


def test_analyze_language(client: TestClient) -> None:
    """Test language bias detection endpoint.

    Args:
        client: Test client fixture.
    """
    response = client.post(
        "/api/v1/analyze/language",
        json={
            "text": "We are looking for a rockstar ninja who is a native english speaker.",
            "context": "job_description",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "patterns" in data
    assert "overall_bias_score" in data
    assert "biased_phrases_count" in data


def test_analyze_fairness(client: TestClient) -> None:
    """Test fairness scoring endpoint.

    Args:
        client: Test client fixture.
    """
    response = client.post(
        "/api/v1/analyze/fairness",
        json={
            "demographic_data": {
                "total_candidates": 50,
                "gender_distribution": {"male": 30, "female": 20},
            },
            "language_patterns": [],
            "hiring_decisions": [],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert "dimensions" in data
    assert "confidence" in data


def test_analyze_patterns(client: TestClient) -> None:
    """Test pattern detection endpoint.

    Args:
        client: Test client fixture.
    """
    response = client.post(
        "/api/v1/analyze/patterns",
        json={
            "hiring_decisions": [],
            "demographic_data": {"total_candidates": 0},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_analyze_recommendations(client: TestClient) -> None:
    """Test recommendations endpoint.

    Args:
        client: Test client fixture.
    """
    response = client.post(
        "/api/v1/analyze/recommendations",
        json={
            "demographic_analysis": {
                "disparities": [],
                "overall_diversity_score": 0.5,
                "underrepresented_groups": [],
            },
            "language_bias": {
                "patterns": [],
                "overall_bias_score": 0.0,
                "biased_phrases_count": 0,
            },
            "fairness_score": {
                "overall_score": 0.8,
                "dimensions": [],
                "confidence": 0.5,
            },
            "patterns": [],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_full_analysis(client: TestClient) -> None:
    """Test full analysis pipeline endpoint.

    Args:
        client: Test client fixture.
    """
    response = client.post(
        "/api/v1/analyze/full",
        json={
            "hiring_decisions": [],
            "job_descriptions": ["Looking for a software engineer"],
            "demographic_data": {
                "total_candidates": 10,
                "gender_distribution": {"male": 6, "female": 4},
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert data["status"] == "completed"
    assert "demographic_analysis" in data
    assert "language_bias" in data
    assert "fairness_score" in data
