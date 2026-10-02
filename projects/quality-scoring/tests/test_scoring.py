"""Tests for scoring API endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from quality_scoring.models.schemas import ContentType, ScoreDimension


def test_score_content(client: TestClient, sample_content_input) -> None:
    """Test full content scoring endpoint."""
    response = client.post(
        "/api/v1/score",
        json={
            "content": sample_content_input.model_dump(),
            "include_benchmark": False,
            "include_improvements": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    score = data["score"]
    assert "overall_score" in score
    assert "dimensions" in score
    assert len(score["dimensions"]) == 4


def test_score_readability(client: TestClient, sample_content_input) -> None:
    """Test readability scoring endpoint."""
    response = client.post(
        "/api/v1/score/readability",
        json=sample_content_input.model_dump(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dimension"] == "readability"
    assert 0 <= data["score"] <= 100


def test_score_originality(client: TestClient, sample_content_input) -> None:
    """Test originality scoring endpoint."""
    response = client.post(
        "/api/v1/score/originality",
        json=sample_content_input.model_dump(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dimension"] == "originality"
    assert 0 <= data["score"] <= 100


def test_score_engagement(client: TestClient, sample_content_input) -> None:
    """Test engagement scoring endpoint."""
    response = client.post(
        "/api/v1/score/engagement",
        json=sample_content_input.model_dump(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dimension"] == "engagement"
    assert 0 <= data["score"] <= 100


def test_score_seo(client: TestClient, sample_content_input) -> None:
    """Test SEO scoring endpoint."""
    response = client.post(
        "/api/v1/score/seo",
        json=sample_content_input.model_dump(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dimension"] == "seo"
    assert 0 <= data["score"] <= 100


def test_score_with_benchmark(client: TestClient, sample_content_input) -> None:
    """Test scoring with benchmark comparison."""
    response = client.post(
        "/api/v1/score",
        json={
            "content": sample_content_input.model_dump(),
            "include_benchmark": True,
            "include_improvements": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "benchmark" in data
    assert data["benchmark"] is not None


def test_score_with_improvements(client: TestClient, sample_content_input) -> None:
    """Test scoring with improvement suggestions."""
    response = client.post(
        "/api/v1/score",
        json={
            "content": sample_content_input.model_dump(),
            "include_benchmark": False,
            "include_improvements": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "improvements" in data
    assert data["improvements"] is not None


def test_score_specific_dimensions(client: TestClient, sample_content_input) -> None:
    """Test scoring with specific dimensions only."""
    response = client.post(
        "/api/v1/score",
        json={
            "content": sample_content_input.model_dump(),
            "dimensions": ["readability", "seo"],
            "include_benchmark": False,
            "include_improvements": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["score"]["dimensions"]) == 2


def test_score_content_too_short(client: TestClient) -> None:
    """Test scoring with too-short content."""
    response = client.post(
        "/api/v1/score",
        json={
            "content": {
                "content": "Short.",
                "content_type": "article",
            },
            "include_benchmark": False,
            "include_improvements": False,
        },
    )
    assert response.status_code == 400


def test_batch_score(client: TestClient, sample_content_input) -> None:
    """Test batch scoring endpoint."""
    response = client.post(
        "/api/v1/batch/score",
        json={
            "items": [
                sample_content_input.model_dump(),
                sample_content_input.model_dump(),
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 2
    assert data["successful"] == 2
    assert data["failed"] == 0
    assert len(data["results"]) == 2
