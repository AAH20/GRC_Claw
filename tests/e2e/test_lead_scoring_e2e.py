"""E2E tests for the full Lead Scoring workflow.

Tests the complete lifecycle of lead scoring through the
Lead Scorer API: scoring, batch scoring, qualification,
churn prediction, next best action, and insights.
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


class TestLeadScoringE2E:
    """End-to-end test suite for lead scoring workflow."""

    def test_health_check(self, lead_scorer_client: TestClient) -> None:
        """Verify the Lead Scorer service is healthy.

        Args:
            lead_scorer_client: Test client for the Lead Scorer API.
        """
        assert_health_check(lead_scorer_client)

    def test_score_lead_full_workflow(
        self, lead_scorer_client: TestClient, sample_lead_data: dict[str, Any]
    ) -> None:
        """Test the complete lead scoring workflow.

        Steps:
            1. Score a single lead.
            2. Verify score breakdown and grade.
            3. Batch score multiple leads.
            4. Verify batch results.

        Args:
            lead_scorer_client: Test client for the Lead Scorer API.
            sample_lead_data: Sample lead data payload.
        """
        lead_id = generate_unique_id("lead")

        # Step 1: Score a single lead
        score_request: dict[str, Any] = {
            "lead_id": lead_id,
            "company_name": sample_lead_data["company_name"],
            "domain": sample_lead_data["domain"],
            "industry": sample_lead_data["industry"],
            "company_size": sample_lead_data["company_size"],
            "location": sample_lead_data["location"],
            "firmographic_score": 75.0,
            "technographic_score": 80.0,
            "intent_score": 65.0,
            "engagement_score": 70.0,
            "timing_score": 85.0,
            "evidence_confidence": 0.8,
        }
        response = lead_scorer_client.post("/api/v1/leads/score", json=score_request)
        result = assert_response_success(response)

        assert result["lead_id"] == lead_id
        assert 0 <= result["total_score"] <= 100
        assert result["grade"] in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]
        assert len(result["breakdown"]) > 0
        assert result["confidence"] > 0
        assert "scoring_model" in result
        assert "rationale" in result

        # Verify breakdown structure
        for item in result["breakdown"]:
            assert "dimension" in item
            assert "score" in item
            assert "weight" in item
            assert "weighted_score" in item

        # Step 2: Batch score multiple leads
        batch_request: dict[str, Any] = {
            "leads": [
                {
                    "lead_id": generate_unique_id("lead"),
                    "company_name": f"Batch Lead {i}",
                    "domain": f"batch-lead-{i}.com",
                    "firmographic_score": 50.0 + i * 10,
                    "technographic_score": 60.0 + i * 5,
                    "intent_score": 70.0,
                    "engagement_score": 55.0,
                    "timing_score": 65.0,
                    "evidence_confidence": 0.7,
                }
                for i in range(3)
            ]
        }
        batch_response = lead_scorer_client.post(
            "/api/v1/leads/score/batch", json=batch_request
        )
        batch_result = assert_response_success(batch_response)

        assert batch_result["total_processed"] == 3
        assert batch_result["total_failed"] == 0
        assert len(batch_result["results"]) == 3

    def test_qualify_lead_full_workflow(
        self, lead_scorer_client: TestClient, sample_lead_data: dict[str, Any]
    ) -> None:
        """Test the complete lead qualification workflow.

        Steps:
            1. Qualify a lead using BANT framework.
            2. Verify qualification results.
            3. Qualify using MEDDIC framework.

        Args:
            lead_scorer_client: Test client for the Lead Scorer API.
            sample_lead_data: Sample lead data payload.
        """
        lead_id = generate_unique_id("lead")

        # Step 1: BANT qualification
        bant_request: dict[str, Any] = {
            "lead_id": lead_id,
            "company_name": sample_lead_data["company_name"],
            "framework": "BANT",
            "budget": "$50,000 - $100,000",
            "authority": "VP of Marketing",
            "need": "Marketing automation platform",
            "timeline": "Q1 2026",
            "metrics": "Increase conversion by 20%",
        }
        response = lead_scorer_client.post(
            f"/api/v1/leads/{lead_id}/qualify", json=bant_request
        )
        result = assert_response_success(response)

        assert result["lead_id"] == lead_id
        assert result["framework"] == "BANT"
        assert isinstance(result["qualified"], bool)
        assert 0 <= result["qualification_score"] <= 100
        assert "criteria" in result
        assert "next_steps" in result
        assert "risk_factors" in result
        assert "summary" in result

        # Step 2: MEDDIC qualification
        meddic_request: dict[str, Any] = {
            "lead_id": lead_id,
            "company_name": sample_lead_data["company_name"],
            "framework": "MEDDIC",
            "metrics": "Increase MQL to SQL conversion by 30%",
            "economic_buyer": "CFO",
            "decision_criteria": "ROI within 6 months",
            "decision_process": "Committee review",
            "identify_pain": "Manual lead scoring is slow",
            " champion": "VP of Sales",
        }
        response = lead_scorer_client.post(
            f"/api/v1/leads/{lead_id}/qualify", json=meddic_request
        )
        result = assert_response_success(response)
        assert result["framework"] == "MEDDIC"

    def test_churn_prediction_workflow(self, lead_scorer_client: TestClient) -> None:
        """Test the churn prediction workflow.

        Args:
            lead_scorer_client: Test client for the Lead Scorer API.
        """
        customer_id = generate_unique_id("cust")

        churn_request: dict[str, Any] = {
            "customer_id": customer_id,
            "company_name": "Test Customer Inc",
            "tenure_months": 24,
            "contract_value": 50000.0,
            "usage_trend": "declining",
            "support_tickets_90d": 5,
            "nps_score": 6.0,
            "engagement_score": 30.0,
            "last_login_days": 30,
            "feature_adoption_rate": 0.2,
            "stakeholder_changes": 2,
            "competitor_mentions": 3,
        }
        response = lead_scorer_client.post(
            "/api/v1/churn/predict", json=churn_request
        )
        result = assert_response_success(response)

        assert result["customer_id"] == customer_id
        assert 0 <= result["churn_probability"] <= 1
        assert result["risk_level"] in ["high", "medium", "low"]
        assert "risk_factors" in result
        assert "protective_factors" in result
        assert "recommended_actions" in result
        assert "confidence" in result

    def test_next_best_action_workflow(
        self, lead_scorer_client: TestClient, sample_lead_data: dict[str, Any]
    ) -> None:
        """Test the next best action workflow.

        Args:
            lead_scorer_client: Test client for the Lead Scorer API.
            sample_lead_data: Sample lead data payload.
        """
        lead_id = generate_unique_id("lead")

        nba_request: dict[str, Any] = {
            "lead_id": lead_id,
            "company_name": sample_lead_data["company_name"],
            "lead_score": 75.0,
            "grade": "B+",
            "qualified": True,
            "industry": "technology",
            "company_size": "50-200",
            "current_stage": "qualified",
            "last_interaction": "demo_completed",
            "preferred_channel": "email",
            "pain_points": ["manual processes", "lack of automation"],
            "interests": ["AI", "marketing automation"],
        }
        response = lead_scorer_client.post(
            "/api/v1/next-action", json=nba_request
        )
        result = assert_response_success(response)

        assert result["lead_id"] == lead_id
        assert "actions" in result
        assert len(result["actions"]) > 0
        assert "overall_strategy" in result
        assert "urgency" in result
        assert "summary" in result

    def test_insights_synthesis_workflow(
        self, lead_scorer_client: TestClient, sample_lead_data: dict[str, Any]
    ) -> None:
        """Test the insights synthesis workflow.

        Args:
            lead_scorer_client: Test client for the Lead Scorer API.
            sample_lead_data: Sample lead data payload.
        """
        lead_id = generate_unique_id("lead")

        insights_request: dict[str, Any] = {
            "lead_id": lead_id,
            "company_name": sample_lead_data["company_name"],
            "domain": sample_lead_data["domain"],
            "industry": "technology",
            "company_size": "50-200",
            "engagement_score": 70.0,
            "intent_score": 65.0,
            "notes": sample_lead_data["notes"],
        }
        response = lead_scorer_client.post(
            "/api/v1/insights", json=insights_request
        )
        result = assert_response_success(response)

        assert result["lead_id"] == lead_id
        assert "overall_assessment" in result
        assert "key_insights" in result
        assert "action_items" in result
        assert "opportunities" in result
        assert "risks" in result
        assert "recommended_approach" in result
        assert "confidence" in result

    def test_score_lead_validation_error(
        self, lead_scorer_client: TestClient
    ) -> None:
        """Test that lead scoring validates required fields.

        Args:
            lead_scorer_client: Test client for the Lead Scorer API.
        """
        invalid_request: dict[str, Any] = {
            "lead_id": "",
            "company_name": "",
            "domain": "",
            "firmographic_score": 150.0,
            "evidence_confidence": 2.0,
        }
        response = lead_scorer_client.post(
            "/api/v1/leads/score", json=invalid_request
        )
        assert_response_error(response, expected_status=422)

    def test_get_nonexistent_lead_score(
        self, lead_scorer_client: TestClient
    ) -> None:
        """Test that getting a non-existent lead score returns 404.

        Args:
            lead_scorer_client: Test client for the Lead Scorer API.
        """
        fake_id = "lead_nonexistent123"
        response = lead_scorer_client.get(f"/api/v1/leads/{fake_id}")
        assert_response_error(response, expected_status=404)
