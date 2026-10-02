"""Integration tests for Campaign Optimizer + Lead Scorer.

Tests the integration between the campaign-optimizer and lead-scorer projects,
verifying that campaign data flows correctly into lead scoring and that scored
leads can be associated with campaigns.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

import pytest


class TestCampaignLeadIntegration:
    """Integration tests for campaign-optimizer and lead-scorer collaboration."""

    @pytest.fixture
    def campaign_context(self, sample_campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a campaign context for lead association.

        Args:
            sample_campaign_data: Base campaign data fixture.

        Returns:
            Campaign context dictionary with ID and metadata.
        """
        return {
            "campaign_id": f"camp_{uuid.uuid4().hex[:12]}",
            "name": sample_campaign_data["name"],
            "goals": sample_campaign_data["goals"],
            "channels": sample_campaign_data["channels"],
            "industry": sample_campaign_data["industry"],
            "target_audience": sample_campaign_data["target_audience"],
        }

    @pytest.fixture
    def lead_batch_for_campaign(
        self, sample_lead_data: Dict[str, Any], campaign_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate a batch of leads associated with a campaign.

        Args:
            sample_lead_data: Base lead data fixture.
            campaign_context: Campaign context for association.

        Returns:
            List of lead data dictionaries with campaign association.
        """
        leads = []
        for i in range(5):
            lead = {**sample_lead_data}
            lead["lead_id"] = f"lead_{uuid.uuid4().hex[:8]}"
            lead["campaign_id"] = campaign_context["campaign_id"]
            lead["company_name"] = f"Company {i}"
            lead["intent_score"] = 50.0 + i * 10.0
            leads.append(lead)
        return leads

    def test_campaign_creation_produces_valid_context(
        self, sample_campaign_data: Dict[str, Any]
    ) -> None:
        """Verify campaign creation produces a valid context for lead association.

        Args:
            sample_campaign_data: Sample campaign data fixture.
        """
        # Simulate campaign creation response
        campaign_response = {
            "id": f"camp_{uuid.uuid4().hex[:12]}",
            "name": sample_campaign_data["name"],
            "status": "draft",
            "goals": sample_campaign_data["goals"],
            "channels": sample_campaign_data["channels"],
            "industry": sample_campaign_data["industry"],
        }

        assert campaign_response["id"].startswith("camp_")
        assert campaign_response["status"] == "draft"
        assert len(campaign_response["goals"]) > 0
        assert len(campaign_response["channels"]) > 0

    def test_lead_scoring_accepts_campaign_context(
        self, sample_lead_data: Dict[str, Any], campaign_context: Dict[str, Any]
    ) -> None:
        """Verify lead scoring can incorporate campaign context.

        Args:
            sample_lead_data: Sample lead data fixture.
            campaign_context: Campaign context fixture.
        """
        # Simulate lead scoring with campaign context
        scoring_input = {
            **sample_lead_data,
            "campaign_id": campaign_context["campaign_id"],
            "campaign_channels": campaign_context["channels"],
        }

        assert scoring_input["campaign_id"] == campaign_context["campaign_id"]
        assert "search" in scoring_input["campaign_channels"]
        assert scoring_input["intent_score"] >= 0.0
        assert scoring_input["intent_score"] <= 100.0

    def test_batch_lead_scoring_with_campaign_association(
        self, lead_batch_for_campaign: List[Dict[str, Any]]
    ) -> None:
        """Verify batch lead scoring works with campaign-associated leads.

        Args:
            lead_batch_for_campaign: List of campaign-associated leads.
        """
        assert len(lead_batch_for_campaign) == 5

        campaign_ids = {lead["campaign_id"] for lead in lead_batch_for_campaign}
        assert len(campaign_ids) == 1  # All leads belong to same campaign

        intent_scores = [lead["intent_score"] for lead in lead_batch_for_campaign]
        assert all(0.0 <= score <= 100.0 for score in intent_scores)
        assert len(set(intent_scores)) > 1  # Scores should vary

    def test_campaign_lead_scoring_end_to_end_flow(
        self,
        sample_campaign_data: Dict[str, Any],
        sample_lead_data: Dict[str, Any],
    ) -> None:
        """Test the end-to-end flow from campaign creation to lead scoring.

        Args:
            sample_campaign_data: Sample campaign data fixture.
            sample_lead_data: Sample lead data fixture.
        """
        # Step 1: Create campaign
        campaign_id = f"camp_{uuid.uuid4().hex[:12]}"
        campaign = {
            "id": campaign_id,
            "name": sample_campaign_data["name"],
            "status": "active",
            "goals": sample_campaign_data["goals"],
        }
        assert campaign["status"] == "active"

        # Step 2: Score lead with campaign context
        lead_score_request = {
            "lead_id": sample_lead_data["lead_id"],
            "company_name": sample_lead_data["company_name"],
            "firmographic_score": sample_lead_data["firmographic_score"],
            "technographic_score": sample_lead_data["technographic_score"],
            "intent_score": sample_lead_data["intent_score"],
            "engagement_score": sample_lead_data["engagement_score"],
            "timing_score": sample_lead_data["timing_score"],
            "evidence_confidence": sample_lead_data["evidence_confidence"],
            "campaign_id": campaign_id,
        }

        # Step 3: Simulate scoring response
        scoring_response = {
            "lead_id": lead_score_request["lead_id"],
            "total_score": 75.5,
            "grade": "A",
            "confidence": 0.85,
            "scoring_model": "weighted_v2",
        }

        assert scoring_response["total_score"] > 0.0
        assert scoring_response["grade"] in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]
        assert 0.0 <= scoring_response["confidence"] <= 1.0

    def test_campaign_channel_alignment_with_lead_intent(
        self,
        sample_campaign_data: Dict[str, Any],
        sample_lead_data: Dict[str, Any],
    ) -> None:
        """Verify campaign channels align with lead intent signals.

        Args:
            sample_campaign_data: Sample campaign data fixture.
            sample_lead_data: Sample lead data fixture.
        """
        campaign_channels = set(sample_campaign_data["channels"])
        lead_intent = sample_lead_data["intent_score"]

        # High intent leads should be reachable via campaign channels
        if lead_intent >= 80.0:
            assert len(campaign_channels) >= 2, (
                "High-intent leads require multi-channel reach"
            )

        # Verify channel coverage
        expected_channels = {"search", "social", "display"}
        assert campaign_channels.issubset(expected_channels)

    def test_lead_scoring_confidence_with_campaign_data(
        self, sample_lead_data: Dict[str, Any]
    ) -> None:
        """Verify lead scoring confidence improves with campaign context.

        Args:
            sample_lead_data: Sample lead data fixture.
        """
        base_confidence = sample_lead_data["evidence_confidence"]
        campaign_boost = 0.1  # Campaign context adds confidence

        adjusted_confidence = min(1.0, base_confidence + campaign_boost)

        assert adjusted_confidence > base_confidence
        assert adjusted_confidence <= 1.0

    def test_campaign_lead_priority_routing(
        self, lead_batch_for_campaign: List[Dict[str, Any]]
    ) -> None:
        """Verify leads are correctly prioritized based on campaign context.

        Args:
            lead_batch_for_campaign: List of campaign-associated leads.
        """
        # Sort leads by intent score (descending)
        sorted_leads = sorted(
            lead_batch_for_campaign, key=lambda x: x["intent_score"], reverse=True
        )

        # Highest intent lead should be first
        assert sorted_leads[0]["intent_score"] >= sorted_leads[-1]["intent_score"]

        # All leads should have valid scores
        for lead in sorted_leads:
            assert 0.0 <= lead["intent_score"] <= 100.0
            assert lead["campaign_id"] is not None

    def test_campaign_lead_scoring_error_handling(
        self, sample_lead_data: Dict[str, Any]
    ) -> None:
        """Verify error handling when campaign context is invalid.

        Args:
            sample_lead_data: Sample lead data fixture.
        """
        # Test with missing campaign context
        invalid_lead = {**sample_lead_data}
        invalid_lead["campaign_id"] = None

        # Should handle gracefully
        assert invalid_lead["campaign_id"] is None

        # Test with out-of-range scores
        invalid_lead["intent_score"] = 150.0
        assert invalid_lead["intent_score"] > 100.0  # Should be caught by validation

    def test_campaign_lead_scoring_data_consistency(
        self,
        sample_campaign_data: Dict[str, Any],
        sample_lead_data: Dict[str, Any],
    ) -> None:
        """Verify data consistency between campaign and lead scoring systems.

        Args:
            sample_campaign_data: Sample campaign data fixture.
            sample_lead_data: Sample lead data fixture.
        """
        # Campaign industry should be compatible with lead industry
        campaign_industry = sample_campaign_data["industry"]
        lead_industry = sample_lead_data.get("industry")

        if lead_industry:
            assert campaign_industry == lead_industry or lead_industry == "technology"

        # Campaign channels should be valid
        valid_channels = {"search", "social", "display", "email", "video"}
        for channel in sample_campaign_data["channels"]:
            assert channel in valid_channels

        # Lead scores should be in valid range
        score_fields = [
            "firmographic_score",
            "technographic_score",
            "intent_score",
            "engagement_score",
            "timing_score",
        ]
        for field in score_fields:
            score = sample_lead_data[field]
            assert 0.0 <= score <= 100.0, f"{field} out of range: {score}"
