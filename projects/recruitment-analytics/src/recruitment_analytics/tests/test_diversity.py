"""Tests for diversity analysis endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient




class TestDiversityEndpoints:
    """Test diversity analysis endpoints."""

    def test_analyze_diversity(self, test_client: TestClient) -> None:
        """Test diversity analysis endpoint."""
        payload = {
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "dimensions": ["gender", "ethnicity"],
        }
        response = test_client.post("/api/v1/diversity/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "report" in data
        assert "benchmark_comparison" in data
        assert data["report"]["gender"]["dimension"] == "gender"

    def test_get_diversity_dimensions(self, test_client: TestClient) -> None:
        """Test diversity dimensions endpoint."""
        response = test_client.get("/api/v1/diversity/dimensions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "gender" in data
        assert "ethnicity" in data

