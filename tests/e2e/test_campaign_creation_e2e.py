"""E2E tests for the full Campaign Creation workflow.

Tests the complete lifecycle of a marketing campaign through the
Campaign Optimizer API: creation, retrieval, update, optimization,
status checks, and deletion.
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


class TestCampaignCreationE2E:
    """End-to-end test suite for campaign creation workflow."""

    def test_health_check(self, campaign_client: TestClient) -> None:
        """Verify the Campaign Optimizer service is healthy.

        Args:
            campaign_client: Test client for the Campaign Optimizer API.
        """
        assert_health_check(campaign_client)

    def test_create_campaign_full_workflow(
        self, campaign_client: TestClient, sample_campaign_data: dict[str, Any]
    ) -> None:
        """Test the complete campaign creation and management workflow.

        Steps:
            1. Create a new campaign.
            2. Verify the campaign was created with correct data.
            3. Retrieve the campaign by ID.
            4. Update the campaign status to active.
            5. Trigger optimization.
            6. Check campaign status.
            7. List all campaigns and verify ours is present.
            8. Delete the campaign.

        Args:
            campaign_client: Test client for the Campaign Optimizer API.
            sample_campaign_data: Sample campaign creation payload.
        """
        # Step 1: Create campaign
        create_response = campaign_client.post(
            "/api/v1/campaigns", json=sample_campaign_data
        )
        created = assert_response_success(create_response, expected_status=201)

        campaign_id = created["id"]
        assert campaign_id.startswith("camp_")
        assert created["name"] == sample_campaign_data["name"]
        assert created["status"] == "draft"
        assert created["total_budget"] == sample_campaign_data["total_budget"]
        assert created["daily_budget"] == sample_campaign_data["daily_budget"]
        assert len(created["goals"]) == 2
        assert "awareness" in created["goals"]
        assert "conversion" in created["goals"]

        # Step 2: Retrieve campaign by ID
        get_response = campaign_client.get(f"/api/v1/campaigns/{campaign_id}")
        retrieved = assert_response_success(get_response)
        assert retrieved["id"] == campaign_id
        assert retrieved["name"] == sample_campaign_data["name"]

        # Step 3: Update campaign status to active
        update_response = campaign_client.put(
            f"/api/v1/campaigns/{campaign_id}",
            json={"status": "active"},
        )
        updated = assert_response_success(update_response)
        assert updated["status"] == "active"
        assert updated["id"] == campaign_id

        # Step 4: Trigger optimization
        optimize_response = campaign_client.post(
            f"/api/v1/campaigns/{campaign_id}/optimize",
            json={"optimization_type": "full"},
        )
        optimization = assert_response_success(optimize_response)
        assert optimization["campaign_id"] == campaign_id
        assert optimization["status"] == "completed"
        assert "recommendations" in optimization
        assert len(optimization["recommendations"]) > 0

        # Step 5: Check campaign status
        status_response = campaign_client.get(
            f"/api/v1/campaigns/{campaign_id}/status"
        )
        status = assert_response_success(status_response)
        assert status["campaign_id"] == campaign_id
        assert status["status"] == "active"

        # Step 6: List campaigns and verify ours is present
        list_response = campaign_client.get("/api/v1/campaigns")
        campaign_list = assert_response_success(list_response)
        assert campaign_list["total"] >= 1
        campaign_ids = [c["id"] for c in campaign_list["campaigns"]]
        assert campaign_id in campaign_ids

        # Step 7: Delete campaign
        delete_response = campaign_client.delete(
            f"/api/v1/campaigns/{campaign_id}"
        )
        assert delete_response.status_code == 204

        # Step 8: Verify deletion
        get_after_delete = campaign_client.get(
            f"/api/v1/campaigns/{campaign_id}"
        )
        assert_response_error(get_after_delete, expected_status=404)

    def test_create_campaign_validation_error(
        self, campaign_client: TestClient
    ) -> None:
        """Test that campaign creation validates required fields.

        Args:
            campaign_client: Test client for the Campaign Optimizer API.
        """
        invalid_data: dict[str, Any] = {
            "name": "",
            "goals": [],
            "total_budget": -100,
            "channels": [],
            "duration_days": 0,
        }
        response = campaign_client.post("/api/v1/campaigns", json=invalid_data)
        assert_response_error(response, expected_status=422)

    def test_create_campaign_with_minimal_data(
        self, campaign_client: TestClient
    ) -> None:
        """Test campaign creation with minimal required fields.

        Args:
            campaign_client: Test client for the Campaign Optimizer API.
        """
        minimal_data: dict[str, Any] = {
            "name": f"Minimal Campaign {generate_unique_id()}",
            "goals": ["awareness"],
            "total_budget": 1000.0,
            "daily_budget": 100.0,
            "channels": ["email"],
            "duration_days": 7,
        }
        response = campaign_client.post("/api/v1/campaigns", json=minimal_data)
        created = assert_response_success(response, expected_status=201)
        assert created["name"] == minimal_data["name"]
        assert created["status"] == "draft"

        # Cleanup
        campaign_client.delete(f"/api/v1/campaigns/{created['id']}")

    def test_campaign_lifecycle_transitions(
        self, campaign_client: TestClient, sample_campaign_data: dict[str, Any]
    ) -> None:
        """Test all campaign status transitions.

        Args:
            campaign_client: Test client for the Campaign Optimizer API.
            sample_campaign_data: Sample campaign creation payload.
        """
        # Create
        create_response = campaign_client.post(
            "/api/v1/campaigns", json=sample_campaign_data
        )
        created = assert_response_success(create_response, expected_status=201)
        campaign_id = created["id"]
        assert created["status"] == "draft"

        # Draft -> Active
        response = campaign_client.put(
            f"/api/v1/campaigns/{campaign_id}", json={"status": "active"}
        )
        assert assert_response_success(response)["status"] == "active"

        # Active -> Paused
        response = campaign_client.put(
            f"/api/v1/campaigns/{campaign_id}", json={"status": "paused"}
        )
        assert assert_response_success(response)["status"] == "paused"

        # Paused -> Active
        response = campaign_client.put(
            f"/api/v1/campaigns/{campaign_id}", json={"status": "active"}
        )
        assert assert_response_success(response)["status"] == "active"

        # Active -> Completed
        response = campaign_client.put(
            f"/api/v1/campaigns/{campaign_id}", json={"status": "completed"}
        )
        assert assert_response_success(response)["status"] == "completed"

        # Cleanup
        campaign_client.delete(f"/api/v1/campaigns/{campaign_id}")

    def test_campaign_optimization_types(
        self, campaign_client: TestClient, sample_campaign_data: dict[str, Any]
    ) -> None:
        """Test different optimization types for a campaign.

        Args:
            campaign_client: Test client for the Campaign Optimizer API.
            sample_campaign_data: Sample campaign creation payload.
        """
        create_response = campaign_client.post(
            "/api/v1/campaigns", json=sample_campaign_data
        )
        created = assert_response_success(create_response, expected_status=201)
        campaign_id = created["id"]

        optimization_types = ["full", "bidding", "creative", "audience", "budget"]
        for opt_type in optimization_types:
            response = campaign_client.post(
                f"/api/v1/campaigns/{campaign_id}/optimize",
                json={"optimization_type": opt_type},
            )
            result = assert_response_success(response)
            assert result["campaign_id"] == campaign_id
            assert result["status"] == "completed"
            assert result["results"]["optimization_type"] == opt_type

        # Cleanup
        campaign_client.delete(f"/api/v1/campaigns/{campaign_id}")

    def test_campaign_list_pagination(
        self, campaign_client: TestClient, sample_campaign_data: dict[str, Any]
    ) -> None:
        """Test campaign listing with pagination.

        Args:
            campaign_client: Test client for the Campaign Optimizer API.
            sample_campaign_data: Sample campaign creation payload.
        """
        created_ids: list[str] = []
        for i in range(3):
            data = {**sample_campaign_data, "name": f"Pagination Test {i}"}
            response = campaign_client.post("/api/v1/campaigns", json=data)
            created = assert_response_success(response, expected_status=201)
            created_ids.append(created["id"])

        # Test pagination
        response = campaign_client.get("/api/v1/campaigns?page=1&page_size=2")
        page1 = assert_response_success(response)
        assert page1["page"] == 1
        assert page1["page_size"] == 2
        assert len(page1["campaigns"]) <= 2

        # Cleanup
        for cid in created_ids:
            campaign_client.delete(f"/api/v1/campaigns/{cid}")

    def test_campaign_not_found_error(self, campaign_client: TestClient) -> None:
        """Test that accessing a non-existent campaign returns 404.

        Args:
            campaign_client: Test client for the Campaign Optimizer API.
        """
        fake_id = "camp_nonexistent123"
        response = campaign_client.get(f"/api/v1/campaigns/{fake_id}")
        assert_response_error(response, expected_status=404)
