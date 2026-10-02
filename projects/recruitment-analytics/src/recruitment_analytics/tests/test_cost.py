Tests for cost analysis endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestCostEndpoints:
    """Test cost analysis endpoints."""

    def test_analyze_costs(self, test_client: TestClient) -> None:
        """Test cost analysis endpoint."""
        payload = {
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "budget": 100000.0,
        }
        response = test_client.post("/api/v1/cost/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "report" in data
        assert "trends" in data
        assert data["report"]["total_cost"] > 0

    def test_get_cost_categories(self, test_client: TestClient) -> None:
        """Test cost categories endpoint."""
        response = test_client.get("/api/v1/cost/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "job_board" in data
        assert "referral" in data

"""