"""Tests for CRM Enhancer API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from crm_enhancer.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "crm-enhancer"


class TestContactEndpoints:
    """Tests for contact API endpoints."""

    def test_enrich_contact_success(self, client: TestClient) -> None:
        """Test successful contact enrichment."""
        response = client.post(
            "/api/v1/contacts/enrich",
            json={
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "company": "Acme Inc",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["contact"]["email"] == "john.doe@example.com"
        assert data["company_domain"] == "example.com"
        assert data["confidence_score"] > 0.0

    def test_enrich_contact_invalid_email(self, client: TestClient) -> None:
        """Test contact enrichment with invalid email."""
        response = client.post(
            "/api/v1/contacts/enrich",
            json={"email": "invalid-email"},
        )
        assert response.status_code == 400

    def test_enrich_contact_missing_email(self, client: TestClient) -> None:
        """Test contact enrichment with missing email."""
        response = client.post(
            "/api/v1/contacts/enrich",
            json={"first_name": "John"},
        )
        assert response.status_code == 422


class TestDealEndpoints:
    """Tests for deal API endpoints."""

    def test_score_deal_success(self, client: TestClient) -> None:
        """Test successful deal scoring."""
        response = client.post(
            "/api/v1/deals/score",
            json={
                "deal_id": "deal_001",
                "title": "Test Deal",
                "value": 50000.0,
                "stage": "proposal_price_quote",
                "contact_email": "buyer@example.com",
                "company": "Test Corp",
                "days_in_stage": 10,
                "activities_count": 5,
                "last_activity_days": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deal_id"] == "deal_001"
        assert 0 <= data["total_score"] <= 100
        assert data["priority"] in ["low", "medium", "high"]
        assert len(data["factors"]) == 5

    def test_score_deal_negative_value(self, client: TestClient) -> None:
        """Test deal scoring with negative value."""
        response = client.post(
            "/api/v1/deals/score",
            json={
                "deal_id": "deal_002",
                "title": "Bad Deal",
                "value": -1000.0,
                "stage": "prospecting",
                "contact_email": "test@example.com",
            },
        )
        assert response.status_code == 400

    def test_score_deal_missing_fields(self, client: TestClient) -> None:
        """Test deal scoring with missing required fields."""
        response = client.post(
            "/api/v1/deals/score",
            json={"title": "Incomplete"},
        )
        assert response.status_code == 422

    def test_list_deals(self, client: TestClient) -> None:
        """Test listing deals."""
        response = client.get("/api/v1/deals/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_deal_not_implemented(self, client: TestClient) -> None:
        """Test getting a single deal returns 501."""
        response = client.get("/api/v1/deals/deal_001")
        assert response.status_code == 501


class TestMetricsEndpoint:
    """Tests for metrics endpoint."""

    def test_metrics_endpoint(self, client: TestClient) -> None:
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
