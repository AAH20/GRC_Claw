"""E2E tests for the full Sales Pipeline workflow.

Tests the complete lifecycle of sales automation through the
Sales Automator API: prospect management, scoring, outreach sequences,
and enrollment.
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


class TestSalesPipelineE2E:
    """End-to-end test suite for sales pipeline workflow."""

    def test_health_check(self, sales_client: TestClient) -> None:
        """Verify the Sales Automator service is healthy.

        Args:
            sales_client: Test client for the Sales Automator API.
        """
        assert_health_check(sales_client)

    def test_prospect_management_full_workflow(
        self, sales_client: TestClient, sample_prospect_data: dict[str, Any]
    ) -> None:
        """Test the complete prospect management workflow.

        Steps:
            1. Create a new prospect.
            2. Verify the prospect was created with correct data.
            3. Retrieve the prospect by ID.
            4. Score the prospect.
            5. List all prospects.
            6. Verify our prospect is in the list.

        Args:
            sales_client: Test client for the Sales Automator API.
            sample_prospect_data: Sample prospect creation payload.
        """
        # Step 1: Create prospect
        create_response = sales_client.post(
            "/api/v1/prospects", json=sample_prospect_data
        )
        created = assert_response_success(create_response, expected_status=201)

        prospect_id = created["id"]
        assert prospect_id is not None
        assert created["name"] == sample_prospect_data["name"]
        assert created["company"] == sample_prospect_data["company"]
        assert created["title"] == sample_prospect_data["title"]
        assert created["email"] == sample_prospect_data["email"]
        assert created["source"] == "e2e_test"

        # Step 2: Retrieve prospect by ID
        get_response = sales_client.get(f"/api/v1/prospects/{prospect_id}")
        retrieved = assert_response_success(get_response)
        assert retrieved["id"] == prospect_id
        assert retrieved["name"] == sample_prospect_data["name"]

        # Step 3: Score prospect
        score_response = sales_client.post(
            f"/api/v1/prospects/{prospect_id}/score"
        )
        score = assert_response_success(score_response)
        assert isinstance(score, dict)
        assert len(score) > 0

        # Step 4: List prospects
        list_response = sales_client.get("/api/v1/prospects")
        prospect_list = assert_response_success(list_response)
        assert isinstance(prospect_list, list)
        prospect_ids = [p["id"] for p in prospect_list]
        assert prospect_id in prospect_ids

    def test_outreach_sequence_full_workflow(
        self, sales_client: TestClient, sample_prospect_data: dict[str, Any]
    ) -> None:
        """Test the complete outreach sequence workflow.

        Steps:
            1. Create a prospect.
            2. Create an outreach sequence.
            3. Verify the sequence was created.
            4. Enroll the prospect in the sequence.
            5. List sequences.
            6. Get sequence by ID.

        Args:
            sales_client: Test client for the Sales Automator API.
            sample_prospect_data: Sample prospect creation payload.
        """
        # Step 1: Create prospect
        prospect_response = sales_client.post(
            "/api/v1/prospects", json=sample_prospect_data
        )
        prospect = assert_response_success(prospect_response, expected_status=201)
        prospect_id = prospect["id"]

        # Step 2: Create sequence
        sequence_request: dict[str, Any] = {
            "name": f"E2E Sequence {generate_unique_id()}",
            "prospect_id": prospect_id,
            "steps": 5,
            "context": {
                "prospect_name": sample_prospect_data["name"],
                "company": sample_prospect_data["company"],
                "industry": sample_prospect_data["industry"],
            },
        }
        sequence_response = sales_client.post(
            "/api/v1/sequences", json=sequence_request
        )
        sequence = assert_response_success(sequence_response, expected_status=201)

        sequence_id = sequence["id"]
        assert sequence["name"] == sequence_request["name"]
        assert sequence["target_prospect_id"] == prospect_id
        assert len(sequence["steps"]) == 5
        assert sequence["status"] == "draft"

        # Step 3: Enroll prospect in sequence
        enroll_request: dict[str, Any] = {
            "prospect_id": prospect_id,
            "start_step": 1,
        }
        enroll_response = sales_client.post(
            f"/api/v1/sequences/{sequence_id}/enroll", json=enroll_request
        )
        enrollment = assert_response_success(enroll_response)
        assert enrollment["sequence_id"] == sequence_id
        assert enrollment["prospect_id"] == prospect_id
        assert enrollment["status"] == "enrolled"

        # Step 4: List sequences
        list_response = sales_client.get("/api/v1/sequences")
        sequences = assert_response_success(list_response)
        assert isinstance(sequences, list)
        sequence_ids = [s["id"] for s in sequences]
        assert sequence_id in sequence_ids

        # Step 5: Get sequence by ID
        get_response = sales_client.get(f"/api/v1/sequences/{sequence_id}")
        retrieved = assert_response_success(get_response)
        assert retrieved["id"] == sequence_id
        assert retrieved["name"] == sequence_request["name"]

    def test_prospect_scoring_workflow(
        self, sales_client: TestClient, sample_prospect_data: dict[str, Any]
    ) -> None:
        """Test the prospect scoring workflow.

        Args:
            sales_client: Test client for the Sales Automator API.
            sample_prospect_data: Sample prospect creation payload.
        """
        # Create prospect
        prospect_response = sales_client.post(
            "/api/v1/prospects", json=sample_prospect_data
        )
        prospect = assert_response_success(prospect_response, expected_status=201)
        prospect_id = prospect["id"]

        # Score prospect
        score_response = sales_client.post(
            f"/api/v1/prospects/{prospect_id}/score"
        )
        score = assert_response_success(score_response)

        assert isinstance(score, dict)
        assert len(score) > 0

    def test_prospect_creation_validation_error(
        self, sales_client: TestClient
    ) -> None:
        """Test that prospect creation validates required fields.

        Args:
            sales_client: Test client for the Sales Automator API.
        """
        invalid_data: dict[str, Any] = {
            "name": "",
            "company": "",
        }
        response = sales_client.post("/api/v1/prospects", json=invalid_data)
        assert_response_error(response, expected_status=422)

    def test_prospect_not_found_error(self, sales_client: TestClient) -> None:
        """Test that accessing a non-existent prospect returns 404.

        Args:
            sales_client: Test client for the Sales Automator API.
        """
        fake_id = "nonexistent-prospect-id"
        response = sales_client.get(f"/api/v1/prospects/{fake_id}")
        assert_response_error(response, expected_status=404)

    def test_sequence_not_found_error(self, sales_client: TestClient) -> None:
        """Test that accessing a non-existent sequence returns 404.

        Args:
            sales_client: Test client for the Sales Automator API.
        """
        fake_id = "nonexistent-sequence-id"
        response = sales_client.get(f"/api/v1/sequences/{fake_id}")
        assert_response_error(response, expected_status=404)

    def test_sequence_enrollment_not_found(
        self, sales_client: TestClient
    ) -> None:
        """Test that enrolling in a non-existent sequence returns 404.

        Args:
            sales_client: Test client for the Sales Automator API.
        """
        fake_id = "nonexistent-sequence-id"
        enroll_request: dict[str, Any] = {
            "prospect_id": "some-prospect",
            "start_step": 1,
        }
        response = sales_client.post(
            f"/api/v1/sequences/{fake_id}/enroll", json=enroll_request
        )
        assert_response_error(response, expected_status=404)

    def test_full_sales_pipeline_integration(
        self, sales_client: TestClient, sample_prospect_data: dict[str, Any]
    ) -> None:
        """Test the full sales pipeline from prospect creation to enrollment.

        Steps:
            1. Create a prospect.
            2. Score the prospect.
            3. Create an outreach sequence.
            4. Enroll the prospect.
            5. Verify the complete pipeline state.

        Args:
            sales_client: Test client for the Sales Automator API.
            sample_prospect_data: Sample prospect creation payload.
        """
        # Step 1: Create prospect
        prospect_response = sales_client.post(
            "/api/v1/prospects", json=sample_prospect_data
        )
        prospect = assert_response_success(prospect_response, expected_status=201)
        prospect_id = prospect["id"]

        # Step 2: Score prospect
        score_response = sales_client.post(
            f"/api/v1/prospects/{prospect_id}/score"
        )
        score = assert_response_success(score_response)
        assert isinstance(score, dict)

        # Step 3: Create sequence
        sequence_request: dict[str, Any] = {
            "name": f"Pipeline Sequence {generate_unique_id()}",
            "prospect_id": prospect_id,
            "steps": 3,
            "context": {"company": sample_prospect_data["company"]},
        }
        sequence_response = sales_client.post(
            "/api/v1/sequences", json=sequence_request
        )
        sequence = assert_response_success(sequence_response, expected_status=201)
        sequence_id = sequence["id"]

        # Step 4: Enroll prospect
        enroll_request: dict[str, Any] = {
            "prospect_id": prospect_id,
            "start_step": 1,
        }
        enroll_response = sales_client.post(
            f"/api/v1/sequences/{sequence_id}/enroll", json=enroll_request
        )
        enrollment = assert_response_success(enroll_response)
        assert enrollment["status"] == "enrolled"

        # Step 5: Verify pipeline state
        # Prospect exists
        prospect_get = sales_client.get(f"/api/v1/prospects/{prospect_id}")
        assert prospect_get.status_code == 200

        # Sequence exists
        sequence_get = sales_client.get(f"/api/v1/sequences/{sequence_id}")
        assert sequence_get.status_code == 200
