"""Tests for funnel analysis endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient




class TestFunnelEndpoints:
    """Test funnel analysis endpoints."""

    def test_analyze_funnel(self, test_client: TestClient) -> None:
        """Test funnel analysis endpoint."""
        payload = {
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "department": "Engineering",
        }
        response = test_client.post("/api/v1/funnel/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "funnel" in data
        assert "insights" in data
        assert "recommendations" in data
        assert data["funnel"]["department"] == "Engineering"

    def test_get_funnel_stages(self, test_client: TestClient) -> None:
        """Test funnel stages endpoint."""
        response = test_client.get("/api/v1/funnel/stages")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "applied" in data
        assert "hired" in data

    def test_analyze_funnel_invalid_dates(self, test_client: TestClient) -> None:
        """Test funnel analysis with invalid date range."""
        payload = {
            "start_date": "2024-03-31",
            "end_date": "2024-01-01",
        }
        response = test_client.post("/api/v1/funnel/analyze", json=payload)
        assert response.status_code == 422

