"""Tests for source tracking endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient




class TestSourceEndpoints:
    """Test source tracking endpoints."""

    def test_analyze_sources(self, test_client: TestClient) -> None:
        """Test source analysis endpoint."""
        payload = {
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
        }
        response = test_client.post("/api/v1/source/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert "top_performing" in data
        assert "underperforming" in data
        assert "insights" in data

    def test_get_source_types(self, test_client: TestClient) -> None:
        """Test source types endpoint."""
        response = test_client.get("/api/v1/source/types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "referral" in data
        assert "linkedin" in data

