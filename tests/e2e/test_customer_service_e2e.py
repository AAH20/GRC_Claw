"""E2E tests for the full Customer Service workflow.

Tests the complete lifecycle of customer service through the
Customer Service API: ticket management, triage, resolution,
escalation, sentiment analysis, and proactive outreach.
"""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import (
    assert_health_check,
    assert_response_error,
    assert_response_success,
    generate_unique_id,
)


class TestCustomerServiceE2E:
    """End-to-end test suite for customer service workflow."""

    def test_health_check(self, customer_service_client: TestClient) -> None:
        """Verify the Customer Service service is healthy.

        Args:
            customer_service_client: Test client for the Customer Service API.
        """
        assert_health_check(customer_service_client)

    def test_ticket_lifecycle_full_workflow(
        self,
        customer_service_client: TestClient,
        sample_ticket_data: dict[str, Any],
    ) -> None:
        """Test the complete ticket lifecycle workflow.

        Steps:
            1. Create a new ticket.
            2. Verify the ticket was created.
            3. Retrieve the ticket by ID.
            4. Run triage classification.
            5. Generate resolution suggestion.
            6. Evaluate escalation.

        Args:
            customer_service_client: Test client for the Customer Service API.
            sample_ticket_data: Sample ticket creation payload.
        """
        # Step 1: Create ticket
        create_response = customer_service_client.post(
            "/api/v1/tickets", json=sample_ticket_data
        )
        created = assert_response_success(create_response, expected_status=201)

        ticket_id = created["ticket_id"]
        assert ticket_id is not None
        assert created["status"] == "open"
        assert created["message"] == "Ticket created successfully"

        # Step 2: Retrieve ticket by ID
        get_response = customer_service_client.get(
            f"/api/v1/tickets/{ticket_id}"
        )
        retrieved = assert_response_success(get_response)
        assert retrieved["ticket_id"] == ticket_id
        assert retrieved["customer_id"] == sample_ticket_data["customer_id"]
        assert retrieved["subject"] == sample_ticket_data["subject"]
        assert retrieved["status"] == "open"

        # Step 3: Run triage
        triage_response = customer_service_client.post(
            f"/api/v1/tickets/{ticket_id}/triage"
        )
        triage = assert_response_success(triage_response)
        assert "category" in triage
        assert "priority" in triage
        assert "confidence" in triage
        assert "intent" in triage
        assert "summary" in triage
        assert "suggested_team" in triage

        # Step 4: Generate resolution
        resolution_response = customer_service_client.post(
            f"/api/v1/tickets/{ticket_id}/resolve"
        )
        resolution = assert_response_success(resolution_response)
        assert "suggestion" in resolution
        assert "confidence" in resolution
        assert "auto_reply" in resolution
        assert "escalation_recommended" in resolution

        # Step 5: Evaluate escalation
        escalation_response = customer_service_client.post(
            f"/api/v1/tickets/{ticket_id}/escalate"
        )
        escalation = assert_response_success(escalation_response)
        assert "should_escalate" in escalation
        assert "reason" in escalation
        assert "urgency" in escalation
        assert "assigned_team" in escalation
        assert "context_summary" in escalation

    def test_sentiment_analysis_workflow(
        self, customer_service_client: TestClient
    ) -> None:
        """Test the sentiment analysis workflow.

        Args:
            customer_service_client: Test client for the Customer Service API.
        """
        customer_id = generate_unique_id("cust")

        sentiment_request: dict[str, Any] = {
            "text": "I am extremely frustrated with the recent update. "
            "The dashboard keeps crashing and I cannot access my data. "
            "This is unacceptable for a paid service.",
            "interaction_history": [
                {"date": "2026-09-15", "type": "complaint", "resolved": False},
                {"date": "2026-09-20", "type": "support_ticket", "resolved": False},
            ],
        }
        response = customer_service_client.post(
            f"/api/v1/customers/{customer_id}/sentiment", json=sentiment_request
        )
        result = assert_response_success(response)

        assert "overall_sentiment" in result
        assert "sentiment_score" in result
        assert "satisfaction_level" in result
        assert "frustration_level" in result
        assert "churn_risk" in result

    def test_proactive_outreach_workflow(
        self, customer_service_client: TestClient
    ) -> None:
        """Test the proactive customer success outreach workflow.

        Args:
            customer_service_client: Test client for the Customer Service API.
        """
        customer_id = generate_unique_id("cust")

        outreach_request: dict[str, Any] = {
            "customer_data": {
                "name": "Test Customer",
                "tier": "enterprise",
                "contract_value": 100000.0,
                "tenure_months": 18,
            },
            "interaction_history": [
                {"date": "2026-09-01", "type": "login", "count": 5},
                {"date": "2026-09-15", "type": "support_ticket", "resolved": True},
            ],
            "usage_data": {
                "last_login_days": 15,
                "feature_adoption_rate": 0.3,
                "active_users": 8,
            },
        }
        response = customer_service_client.post(
            f"/api/v1/customers/{customer_id}/outreach", json=outreach_request
        )
        result = assert_response_success(response)

        assert "health_score" in result
        assert "churn_risk" in result
        assert "recommended_actions" in result
        assert "outreach_message" in result
        assert "engagement_level" in result

    def test_ticket_creation_validation_error(
        self, customer_service_client: TestClient
    ) -> None:
        """Test that ticket creation validates required fields.

        Args:
            customer_service_client: Test client for the Customer Service API.
        """
        invalid_data: dict[str, Any] = {
            "customer_id": "",
            "subject": "",
            "content": "",
        }
        response = customer_service_client.post(
            "/api/v1/tickets", json=invalid_data
        )
        assert_response_error(response, expected_status=422)

    def test_ticket_not_found_error(
        self, customer_service_client: TestClient
    ) -> None:
        """Test that accessing a non-existent ticket returns 404.

        Args:
            customer_service_client: Test client for the Customer Service API.
        """
        fake_id = "nonexistent-ticket-id"
        response = customer_service_client.get(f"/api/v1/tickets/{fake_id}")
        assert_response_error(response, expected_status=404)

    def test_ticket_triage_not_found(
        self, customer_service_client: TestClient
    ) -> None:
        """Test that triaging a non-existent ticket returns 404.

        Args:
            customer_service_client: Test client for the Customer Service API.
        """
        fake_id = "nonexistent-ticket-id"
        response = customer_service_client.post(
            f"/api/v1/tickets/{fake_id}/triage"
        )
        assert_response_error(response, expected_status=404)

    def test_ticket_resolution_not_found(
        self, customer_service_client: TestClient
    ) -> None:
        """Test that resolving a non-existent ticket returns 404.

        Args:
            customer_service_client: Test client for the Customer Service API.
        """
        fake_id = "nonexistent-ticket-id"
        response = customer_service_client.post(
            f"/api/v1/tickets/{fake_id}/resolve"
        )
        assert_response_error(response, expected_status=404)

    def test_ticket_escalation_not_found(
        self, customer_service_client: TestClient
    ) -> None:
        """Test that escalating a non-existent ticket returns 404.

        Args:
            customer_service_client: Test client for the Customer Service API.
        """
        fake_id = "nonexistent-ticket-id"
        response = customer_service_client.post(
            f"/api/v1/tickets/{fake_id}/escalate"
        )
        assert_response_error(response, expected_status=404)

    def test_customer_not_found_error(
        self, customer_service_client: TestClient
    ) -> None:
        """Test that accessing a non-existent customer returns 404.

        Args:
            customer_service_client: Test client for the Customer Service API.
        """
        fake_id = "nonexistent-customer-id"
        response = customer_service_client.get(f"/api/v1/customers/{fake_id}")
        assert_response_error(response, expected_status=404)

    def test_full_customer_service_integration(
        self,
        customer_service_client: TestClient,
        sample_ticket_data: dict[str, Any],
    ) -> None:
        """Test the full customer service integration workflow.

        Steps:
            1. Create a ticket.
            2. Run triage.
            3. Generate resolution.
            4. Evaluate escalation.
            5. Analyze sentiment.
            6. Trigger proactive outreach.

        Args:
            customer_service_client: Test client for the Customer Service API.
            sample_ticket_data: Sample ticket creation payload.
        """
        customer_id = sample_ticket_data["customer_id"]

        # Step 1: Create ticket
        ticket_response = customer_service_client.post(
            "/api/v1/tickets", json=sample_ticket_data
        )
        ticket = assert_response_success(ticket_response, expected_status=201)
        ticket_id = ticket["ticket_id"]

        # Step 2: Triage
        triage_response = customer_service_client.post(
            f"/api/v1/tickets/{ticket_id}/triage"
        )
        triage = assert_response_success(triage_response)
        assert triage["category"] is not None

        # Step 3: Resolution
        resolution_response = customer_service_client.post(
            f"/api/v1/tickets/{ticket_id}/resolve"
        )
        resolution = assert_response_success(resolution_response)
        assert resolution["suggestion"] is not None

        # Step 4: Escalation
        escalation_response = customer_service_client.post(
            f"/api/v1/tickets/{ticket_id}/escalate"
        )
        escalation = assert_response_success(escalation_response)
        assert "should_escalate" in escalation

        # Step 5: Sentiment analysis
        sentiment_request: dict[str, Any] = {
            "text": sample_ticket_data["content"],
        }
        sentiment_response = customer_service_client.post(
            f"/api/v1/customers/{customer_id}/sentiment", json=sentiment_request
        )
        sentiment = assert_response_success(sentiment_response)
        assert sentiment["overall_sentiment"] is not None

        # Step 6: Proactive outreach
        outreach_request: dict[str, Any] = {
            "customer_data": {"customer_id": customer_id, "tier": "standard"},
        }
        outreach_response = customer_service_client.post(
            f"/api/v1/customers/{customer_id}/outreach", json=outreach_request
        )
        outreach = assert_response_success(outreach_response)
        assert "health_score" in outreach
