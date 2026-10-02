"""E2E tests for the full Journey Execution workflow.

Tests the complete lifecycle of customer journey orchestration through the
Journey Orchestrator API: creation, execution, personalization,
timing optimization, and experimentation.
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


class TestJourneyExecutionE2E:
    """End-to-end test suite for journey execution workflow."""

    def test_health_check(self, journey_client: TestClient) -> None:
        """Verify the Journey Orchestrator service is healthy.

        Args:
            journey_client: Test client for the Journey Orchestrator API.
        """
        assert_health_check(journey_client)

    def test_create_journey_full_workflow(
        self, journey_client: TestClient, sample_journey_data: dict[str, Any]
    ) -> None:
        """Test the complete journey creation and execution workflow.

        Steps:
            1. Create a new journey.
            2. Verify the journey was created with correct data.
            3. Retrieve the journey by ID.
            4. Update the journey.
            5. Execute the journey.
            6. Check journey status.
            7. List all journeys.
            8. Delete the journey.

        Args:
            journey_client: Test client for the Journey Orchestrator API.
            sample_journey_data: Sample journey creation payload.
        """
        # Step 1: Create journey
        create_response = journey_client.post(
            "/api/v1/journeys", json=sample_journey_data
        )
        created = assert_response_success(create_response, expected_status=201)

        journey_id = created["id"]
        assert journey_id is not None
        assert created["name"] == sample_journey_data["name"]
        assert created["status"] == "draft"
        assert created["target_audience"] == sample_journey_data["target_audience"]
        assert created["business_goal"] == sample_journey_data["business_goal"]
        assert "email" in created["channels"]
        assert "push" in created["channels"]

        # Step 2: Retrieve journey by ID
        get_response = journey_client.get(f"/api/v1/journeys/{journey_id}")
        retrieved = assert_response_success(get_response)
        assert retrieved["id"] == journey_id
        assert retrieved["name"] == sample_journey_data["name"]

        # Step 3: Update journey
        update_response = journey_client.put(
            f"/api/v1/journeys/{journey_id}",
            json={"description": "Updated description for E2E test"},
        )
        updated = assert_response_success(update_response)
        assert updated["description"] == "Updated description for E2E test"

        # Step 4: Execute journey
        execute_response = journey_client.post(
            f"/api/v1/journeys/{journey_id}/execute",
            json={"customer_ids": ["cust_001", "cust_002"]},
        )
        execution = assert_response_success(execute_response)
        assert execution["journey_id"] == journey_id
        assert execution["status"].value == "active"
        assert execution["execution_id"] is not None

        # Step 5: Check journey status
        status_response = journey_client.get(
            f"/api/v1/journeys/{journey_id}/status"
        )
        status = assert_response_success(status_response)
        assert status["journey_id"] == journey_id
        assert status["status"].value == "active"

        # Step 6: List journeys
        list_response = journey_client.get("/api/v1/journeys")
        journey_list = assert_response_success(list_response)
        assert journey_list["total"] >= 1
        journey_ids = [j["id"] for j in journey_list["journeys"]]
        assert journey_id in journey_ids

        # Step 7: Delete journey
        delete_response = journey_client.delete(
            f"/api/v1/journeys/{journey_id}"
        )
        assert delete_response.status_code == 204

        # Step 8: Verify deletion
        get_after_delete = journey_client.get(
            f"/api/v1/journeys/{journey_id}"
        )
        assert_response_error(get_after_delete, expected_status=404)

    def test_journey_personalization_workflow(
        self, journey_client: TestClient
    ) -> None:
        """Test the journey personalization workflow.

        Args:
            journey_client: Test client for the Journey Orchestrator API.
        """
        customer_id = generate_unique_id("cust")

        personalize_request: dict[str, Any] = {
            "customer_id": customer_id,
            "customer_profile": {
                "name": "Test Customer",
                "tier": "enterprise",
                "industry": "technology",
                "company_size": "500+",
            },
            "channel": "email",
            "context": {"last_purchase": "2026-09-01", "preferences": ["ai", "automation"]},
        }
        response = journey_client.post(
            "/api/v1/personalize", json=personalize_request
        )
        result = assert_response_success(response)

        assert result["customer_id"] == customer_id
        assert "contents" in result
        assert "recommended_offers" in result
        assert "next_best_action" in result
        assert "confidence_score" in result

    def test_journey_timing_optimization_workflow(
        self, journey_client: TestClient
    ) -> None:
        """Test the journey timing optimization workflow.

        Args:
            journey_client: Test client for the Journey Orchestrator API.
        """
        customer_id = generate_unique_id("cust")

        timing_request: dict[str, Any] = {
            "customer_id": customer_id,
            "channels": ["email", "push", "sms"],
            "timezone": "America/New_York",
        }
        response = journey_client.post(
            "/api/v1/timing/optimize", json=timing_request
        )
        result = assert_response_success(response)

        assert result["customer_id"] == customer_id
        assert "channel_timings" in result
        assert "best_overall_time" in result
        assert "global_frequency_cap" in result

    def test_journey_experiment_workflow(
        self, journey_client: TestClient
    ) -> None:
        """Test the journey experimentation workflow.

        Args:
            journey_client: Test client for the Journey Orchestrator API.
        """
        # Create experiment
        experiment_request: dict[str, Any] = {
            "name": f"E2E Experiment {generate_unique_id()}",
            "hypothesis": "Personalized subject lines increase open rates by 15%",
            "experiment_type": "ab_test",
            "variants": [
                {"name": "control", "subject": "Check out our features"},
                {"name": "variant_a", "subject": "Your personalized recommendations"},
            ],
            "primary_metric": "open_rate",
            "secondary_metrics": ["click_rate", "conversion_rate"],
            "minimum_sample_size": 1000,
            "confidence_level": 0.95,
            "max_duration_days": 14,
        }
        response = journey_client.post(
            "/api/v1/experiments", json=experiment_request
        )
        result = assert_response_success(response, expected_status=201)

        assert result["name"] == experiment_request["name"]
        assert result["hypothesis"] == experiment_request["hypothesis"]
        assert result["status"] == "draft"
        assert len(result["variants"]) == 2

    def test_journey_creation_validation_error(
        self, journey_client: TestClient
    ) -> None:
        """Test that journey creation validates required fields.

        Args:
            journey_client: Test client for the Journey Orchestrator API.
        """
        invalid_data: dict[str, Any] = {
            "name": "",
            "target_audience": "",
            "business_goal": "",
        }
        response = journey_client.post("/api/v1/journeys", json=invalid_data)
        assert_response_error(response, expected_status=422)

    def test_journey_not_found_error(self, journey_client: TestClient) -> None:
        """Test that accessing a non-existent journey returns 404.

        Args:
            journey_client: Test client for the Journey Orchestrator API.
        """
        fake_id = "nonexistent-journey-id"
        response = journey_client.get(f"/api/v1/journeys/{fake_id}")
        assert_response_error(response, expected_status=404)

    def test_journey_execution_not_found(
        self, journey_client: TestClient
    ) -> None:
        """Test that executing a non-existent journey returns 404.

        Args:
            journey_client: Test client for the Journey Orchestrator API.
        """
        fake_id = "nonexistent-journey-id"
        response = journey_client.post(
            f"/api/v1/journeys/{fake_id}/execute"
        )
        assert_response_error(response, expected_status=404)

    def test_journey_lifecycle_transitions(
        self, journey_client: TestClient, sample_journey_data: dict[str, Any]
    ) -> None:
        """Test all journey status transitions.

        Args:
            journey_client: Test client for the Journey Orchestrator API.
            sample_journey_data: Sample journey creation payload.
        """
        # Create
        create_response = journey_client.post(
            "/api/v1/journeys", json=sample_journey_data
        )
        created = assert_response_success(create_response, expected_status=201)
        journey_id = created["id"]
        assert created["status"] == "draft"

        # Draft -> Active (via execute)
        execute_response = journey_client.post(
            f"/api/v1/journeys/{journey_id}/execute"
        )
        execution = assert_response_success(execute_response)
        assert execution["status"].value == "active"

        # Active -> Paused
        response = journey_client.put(
            f"/api/v1/journeys/{journey_id}", json={"status": "paused"}
        )
        assert assert_response_success(response)["status"].value == "paused"

        # Paused -> Active
        response = journey_client.put(
            f"/api/v1/journeys/{journey_id}", json={"status": "active"}
        )
        assert assert_response_success(response)["status"].value == "active"

        # Active -> Completed
        response = journey_client.put(
            f"/api/v1/journeys/{journey_id}", json={"status": "completed"}
        )
        assert assert_response_success(response)["status"].value == "completed"

        # Cleanup
        journey_client.delete(f"/api/v1/journeys/{journey_id}")
