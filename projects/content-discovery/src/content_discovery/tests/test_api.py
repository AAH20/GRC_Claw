"""Tests for the FastAPI application."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_health_check(test_client: TestClient) -> None:
    """Test health check endpoint.

    Args:
        test_client: Test client.
    """
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_readiness_check(test_client: TestClient) -> None:
    """Test readiness check endpoint.

    Args:
        test_client: Test client.
    """
    response = test_client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_search_endpoint(test_client: TestClient) -> None:
    """Test search endpoint.

    Args:
        test_client: Test client.
    """
    response = test_client.post(
        "/api/v1/search",
        json={
            "query": "machine learning",
            "limit": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
    assert "query" in data
    assert data["query"] == "machine learning"


def test_search_with_explanation(test_client: TestClient) -> None:
    """Test search with explanation endpoint.

    Args:
        test_client: Test client.
    """
    response = test_client.post(
        "/api/v1/search/explain",
        json={
            "query": "python programming",
            "limit": 3,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "factors" in data
    assert "confidence" in data


def test_search_suggestions(test_client: TestClient) -> None:
    """Test search suggestions endpoint.

    Args:
        test_client: Test client.
    """
    response = test_client.get("/api/v1/search/suggest?q=machine&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) <= 3


def test_recommendations_endpoint(test_client: TestClient) -> None:
    """Test recommendations endpoint.

    Args:
        test_client: Test client.
    """
    response = test_client.post(
        "/api/v1/recommendations",
        json={
            "user_id": "user_123",
            "limit": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert data["user_id"] == "user_123"


def test_user_recommendations_endpoint(test_client: TestClient) -> None:
    """Test user-specific recommendations endpoint.

    Args:
        test_client: Test client.
    """
    response = test_client.get("/api/v1/recommendations/user_456?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert data["user_id"] == "user_456"


def test_trends_endpoint(test_client: TestClient) -> None:
    """Test trends endpoint.

    Args:
        test_client: Test client.
    """
    response = test_client.post(
        "/api/v1/trends",
        json={
            "topics": ["AI", "blockchain"],
            "window_days": 7,
            "limit": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "trends" in data
    assert data["window_days"] == 7


def test_get_trends_endpoint(test_client: TestClient) -> None:
    """Test GET trends endpoint.

    Args:
        test_client: Test client.
    """
    response = test_client.get("/api/v1/trends?window_days=14&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "trends" in data
    assert data["window_days"] == 14


def test_user_profile_endpoint(test_client: TestClient) -> None:
    """Test user profile endpoint.

    Args:
        test_client: Test client.
    """
    response = test_client.get("/api/v1/users/user_789/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_789"
    assert "preferences" in data


def test_add_user_history_endpoint(test_client: TestClient) -> None:
    """Test add user history endpoint.

    Args:
        test_client: Test client.
    """
    from unittest.mock import AsyncMock, patch

    mock_client = AsyncMock()
    mock_client.add_history = AsyncMock(return_value=True)

    with patch(
        "content_discovery.api.get_user_profile",
        return_value=mock_client,
    ):
        response = test_client.post(
            "/api/v1/users/user_123/history",
            json={
                "id": "content_1",
                "title": "Test Article",
                "tags": ["python", "testing"],
                "content_type": "article",
            },
        )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_endpoint(test_client: TestClient) -> None:
    """Test metrics endpoint.

    Args:
        test_client: Test client.
    """
    response = test_client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "requests_total" in data


def test_search_validation_error(test_client: TestClient) -> None:
    """Test search endpoint validation.

    Args:
        test_client: Test client.
    """
    response = test_client.post(
        "/api/v1/search",
        json={"query": ""},  # Empty query should fail
    )
    assert response.status_code == 422


def test_recommendations_validation_error(test_client: TestClient) -> None:
    """Test recommendations endpoint validation.

    Args:
        test_client: Test client.
    """
    response = test_client.post(
        "/api/v1/recommendations",
        json={"user_id": ""},  # Empty user_id should fail
    )
    assert response.status_code == 422
