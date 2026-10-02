"""Tests for marketplace analytics."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_get_analytics_report(client: TestClient) -> None:
    """Test generating analytics report."""
    # Create some data
    for i in range(3):
        client.post(
            "/api/v1/listings",
            json={
                "title": f"Analytics {i}",
                "description": f"Content {i}",
                "seller_id": "seller_1",
                "category": "test",
                "base_price": 10.0 * (i + 1),
            },
        )

    response = client.get("/api/v1/analytics/report?days=30")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["summary"]["total_listings"] >= 3


def test_get_marketplace_insights(client: TestClient) -> None:
    """Test getting marketplace insights."""
    response = client.get("/api/v1/analytics/insights?days=30")
    assert response.status_code == 200
    data = response.json()
    assert "insights" in data
    assert "recommendations" in data
