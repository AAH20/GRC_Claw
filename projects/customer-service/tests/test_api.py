"""Tests for customer service API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from customer_service.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Test cases for the health check endpoint."""

    def test_health_check_returns_200(self, client: TestClient) -> None:
        """Test that health check returns 200 with correct payload."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestTicketEndpoints:
    """Test cases for ticket API endpoints."""

    def test_create_ticket_returns_201(self, client: TestClient) -> None:
        """Test creating a new ticket."""
        payload = {
            "customer_id": "cust-123",
            "subject": "Test ticket",
            "content": "This is a test ticket",
            "channel": "email",
        }
        response = client.post("/api/v1/tickets", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "open"
        assert "ticket_id" in data

    def test_get_ticket_returns_200(self, client: TestClient) -> None:
        """Test retrieving a ticket by ID."""
        create_payload = {
            "customer_id": "cust-456",
            "subject": "Another ticket",
            "content": "Content here",
        }
        create_response = client.post("/api/v1/tickets", json=create_payload)
        ticket_id = create_response.json()["ticket_id"]

        response = client.get(f"/api/v1/tickets/{ticket_id}")
        assert response.status_code == 200
        assert response.json()["ticket_id"] == ticket_id

    def test_get_nonexistent_ticket_returns_404(self, client: TestClient) -> None:
        """Test that getting a non-existent ticket returns 404."""
        response = client.get("/api/v1/tickets/nonexistent-id")
        assert response.status_code == 404

    def test_triage_ticket(self, client: TestClient) -> None:
        """Test running triage on a ticket."""
        create_payload = {
            "customer_id": "cust-789",
            "subject": "Billing issue",
            "content": "I was charged twice for my subscription",
        }
        create_response = client.post("/api/v1/tickets", json=create_payload)
        ticket_id = create_response.json()["ticket_id"]

        mock_triage_result = {
            "category": "billing",
            "priority": "high",
            "confidence": 0.92,
            "intent": "duplicate_charge",
            "summary": "Customer reports duplicate charge",
            "suggested_team": "billing_team",
        }
        with patch(
            "customer_service.api.tickets.TriageAgent.run",
            new_callable=AsyncMock,
            return_value=type("Result", (), mock_triage_result)(),
        ):
            response = client.post(f"/api/v1/tickets/{ticket_id}/triage")
            assert response.status_code == 200
            data = response.json()
            assert data["category"] == "billing"
            assert data["priority"] == "high"

    def test_resolve_ticket(self, client: TestClient) -> None:
        """Test running resolution on a ticket."""
        create_payload = {
            "customer_id": "cust-101",
            "subject": "Password reset",
            "content": "I forgot my password",
        }
        create_response = client.post("/api/v1/tickets", json=create_payload)
        ticket_id = create_response.json()["ticket_id"]

        mock_resolution_result = {
            "suggestion": "Send password reset link",
            "confidence": 0.95,
            "auto_reply": "Here is your reset link",
            "escalation_recommended": False,
        }
        with patch(
            "customer_service.api.tickets.ResolutionAgent.run",
            new_callable=AsyncMock,
            return_value=type("Result", (), mock_resolution_result)(),
        ):
            response = client.post(f"/api/v1/tickets/{ticket_id}/resolve")
            assert response.status_code == 200
            data = response.json()
            assert "password reset" in data["suggestion"].lower()

    def test_escalate_ticket(self, client: TestClient) -> None:
        """Test running escalation on a ticket."""
        create_payload = {
            "customer_id": "cust-202",
            "subject": "Urgent issue",
            "content": "Service is down",
        }
        create_response = client.post("/api/v1/tickets", json=create_payload)
        ticket_id = create_response.json()["ticket_id"]

        mock_escalation_result = {
            "should_escalate": True,
            "reason": "Service outage",
            "urgency": "critical",
            "assigned_team": "sre_team",
            "context_summary": "Customer reports service outage",
        }
        with patch(
            "customer_service.api.tickets.EscalationAgent.run",
            new_callable=AsyncMock,
            return_value=type("Result", (), mock_escalation_result)(),
        ):
            response = client.post(f"/api/v1/tickets/{ticket_id}/escalate")
            assert response.status_code == 200
            data = response.json()
            assert data["should_escalate"] is True
            assert data["urgency"] == "critical"


class TestCustomerEndpoints:
    """Test cases for customer API endpoints."""

    def test_get_nonexistent_customer_returns_404(self, client: TestClient) -> None:
        """Test that getting a non-existent customer returns 404."""
        response = client.get("/api/v1/customers/nonexistent-id")
        assert response.status_code == 404

    def test_analyze_sentiment(self, client: TestClient) -> None:
        """Test sentiment analysis endpoint."""
        payload = {"text": "I love this product, it's amazing!"}
        mock_sentiment_result = {
            "overall_sentiment": "positive",
            "sentiment_score": 0.85,
            "satisfaction_level": "very_satisfied",
            "frustration_level": "none",
            "churn_risk": "none",
        }
        with patch(
            "customer_service.api.customers.SentimentAnalysisAgent.run",
            new_callable=AsyncMock,
            return_value=type("Result", (), mock_sentiment_result)(),
        ):
            response = client.post("/api/v1/customers/cust-123/sentiment", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["overall_sentiment"] == "positive"

    def test_trigger_outreach(self, client: TestClient) -> None:
        """Test proactive outreach endpoint."""
        payload = {
            "customer_data": {"name": "Acme Corp", "mrr": 5000},
            "usage_data": {"logins_last_30d": 2},
        }
        mock_outreach_result = {
            "health_score": 35.0,
            "churn_risk": "high",
            "recommended_actions": ["Schedule check-in call"],
            "outreach_message": "We miss you!",
            "engagement_level": "low",
        }
        with patch(
            "customer_service.api.customers.CustomerSuccessAgent.run",
            new_callable=AsyncMock,
            return_value=type("Result", (), mock_outreach_result)(),
        ):
            response = client.post("/api/v1/customers/cust-123/outreach", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["churn_risk"] == "high"
