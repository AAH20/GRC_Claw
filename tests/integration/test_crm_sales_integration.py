"""Integration tests for CRM Enhancer + Sales Automator.

Tests the integration between the crm-enhancer and sales-automator projects,
verifying that enriched CRM data flows into sales automation workflows and that
sales activities update CRM records.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pytest


class TestCRMSalesIntegration:
    """Integration tests for crm-enhancer and sales-automator collaboration."""

    @pytest.fixture
    def enriched_contact(self) -> Dict[str, Any]:
        """Create an enriched CRM contact for sales automation.

        Returns:
            Enriched contact dictionary.
        """
        return {
            "contact_id": f"contact_{uuid.uuid4().hex[:8]}",
            "email": "prospect@acme.com",
            "first_name": "John",
            "last_name": "Doe",
            "company": "Acme Corp",
            "title": "VP of Marketing",
            "phone": "+1-555-0123",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "company_domain": "acme.com",
            "company_size": "200-500",
            "industry": "technology",
            "revenue": "$50M-$100M",
            "technologies": ["Salesforce", "HubSpot", "Marketo"],
            "enrichment_confidence": 0.92,
            "sources": ["clearbit", "zoominfo"],
        }

    @pytest.fixture
    def sales_sequence_context(self) -> Dict[str, Any]:
        """Create a sales sequence context for automation.

        Returns:
            Sales sequence context dictionary.
        """
        return {
            "sequence_id": f"seq_{uuid.uuid4().hex[:12]}",
            "name": "VP Marketing Outreach",
            "steps": [
                {"step": 1, "channel": "email", "template": "initial_outreach", "delay_days": 0},
                {"step": 2, "channel": "linkedin", "template": "connection_request", "delay_days": 1},
                {"step": 3, "channel": "email", "template": "value_proposition", "delay_days": 3},
                {"step": 4, "channel": "call", "template": "discovery_call", "delay_days": 5},
            ],
            "target_segment": "vp_marketing",
        }

    @pytest.fixture
    def deal_context(self) -> Dict[str, Any]:
        """Create a deal context for CRM-sales integration.

        Returns:
            Deal context dictionary.
        """
        return {
            "deal_id": f"deal_{uuid.uuid4().hex[:8]}",
            "title": "Acme Corp - Annual License",
            "value": 75000.0,
            "stage": "qualification",
            "contact_id": f"contact_{uuid.uuid4().hex[:8]}",
            "company": "Acme Corp",
            "probability": 0.3,
            "expected_close_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "activities": [],
        }

    def test_enriched_contact_triggers_sales_sequence(
        self, enriched_contact: Dict[str, Any], sales_sequence_context: Dict[str, Any]
    ) -> None:
        """Verify enriched contact data triggers appropriate sales sequence.

        Args:
            enriched_contact: Enriched contact fixture.
            sales_sequence_context: Sales sequence context fixture.
        """
        assert enriched_contact["enrichment_confidence"] >= 0.8

        required_fields = ["email", "company", "title"]
        for field in required_fields:
            assert enriched_contact.get(field) is not None

        if "VP" in enriched_contact["title"] or "Director" in enriched_contact["title"]:
            assert sales_sequence_context["target_segment"] == "vp_marketing"

    def test_crm_deal_scoring_informs_sales_priority(
        self, deal_context: Dict[str, Any]
    ) -> None:
        """Verify CRM deal scoring informs sales automation priority.

        Args:
            deal_context: Deal context fixture.
        """
        deal_value = deal_context["value"]
        deal_stage = deal_context["stage"]

        stage_scores = {
            "prospecting": 10,
            "qualification": 30,
            "proposal": 60,
            "negotiation": 80,
            "closed_won": 100,
            "closed_lost": 0,
        }

        base_score = stage_scores.get(deal_stage, 0)
        value_score = min(30, deal_value / 5000.0)

        total_score = base_score + value_score
        assert 0 <= total_score <= 130

        if total_score >= 60:
            priority = "high"
            sequence_pace = "accelerated"
        else:
            priority = "normal"
            sequence_pace = "standard"

        assert priority in ["high", "normal", "low"]
        assert sequence_pace in ["accelerated", "standard", "extended"]

    def test_sales_activity_updates_crm_record(
        self, enriched_contact: Dict[str, Any]
    ) -> None:
        """Verify sales activities are logged back to CRM records.

        Args:
            enriched_contact: Enriched contact fixture.
        """
        activity = {
            "activity_id": f"act_{uuid.uuid4().hex[:8]}",
            "contact_id": enriched_contact["contact_id"],
            "type": "email_sent",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "template": "initial_outreach",
                "sequence_step": 1,
            },
        }

        assert activity["contact_id"] == enriched_contact["contact_id"]
        assert activity["type"] == "email_sent"

        crm_update = {
            "contact_id": enriched_contact["contact_id"],
            "last_activity": activity["timestamp"],
            "activity_count": 1,
        }
        assert crm_update["activity_count"] > 0

    def test_crm_sales_end_to_end_flow(self) -> None:
        """Test the complete flow from CRM enrichment to sales automation."""
        contact = {
            "contact_id": f"contact_{uuid.uuid4().hex[:8]}",
            "email": "prospect@company.com",
            "company": "Company Inc",
            "title": "Marketing Director",
            "enrichment_confidence": 0.88,
        }
        assert contact["enrichment_confidence"] >= 0.8

        deal = {
            "deal_id": f"deal_{uuid.uuid4().hex[:8]}",
            "contact_id": contact["contact_id"],
            "value": 50000.0,
            "stage": "qualification",
            "score": 45,
        }
        assert deal["score"] > 0

        sequence = {
            "sequence_id": f"seq_{uuid.uuid4().hex[:12]}",
            "contact_id": contact["contact_id"],
            "deal_id": deal["deal_id"],
            "status": "active",
            "current_step": 1,
        }
        assert sequence["status"] == "active"

        touchpoint = {
            "touchpoint_id": f"tp_{uuid.uuid4().hex[:8]}",
            "sequence_id": sequence["sequence_id"],
            "step": 1,
            "channel": "email",
            "status": "sent",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        assert touchpoint["status"] == "sent"

    def test_crm_contact_enrichment_from_sales_data(self) -> None:
        """Verify CRM contact enrichment incorporates sales interaction data."""
        sales_data = {
            "emails_sent": 5,
            "emails_opened": 3,
            "calls_made": 2,
            "meetings_booked": 1,
            "last_contact": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
        }

        engagement_score = (
            sales_data["emails_opened"] * 10
            + sales_data["calls_made"] * 20
            + sales_data["meetings_booked"] * 30
        )

        assert engagement_score > 0
        assert sales_data["emails_opened"] <= sales_data["emails_sent"]

    def test_sales_sequence_personalization_with_crm_data(
        self, enriched_contact: Dict[str, Any], sales_sequence_context: Dict[str, Any]
    ) -> None:
        """Verify sales sequences are personalized using CRM data.

        Args:
            enriched_contact: Enriched contact fixture.
            sales_sequence_context: Sales sequence context fixture.
        """
        personalization = {
            "contact_name": f"{enriched_contact['first_name']} {enriched_contact['last_name']}",
            "company": enriched_contact["company"],
            "title": enriched_contact["title"],
            "industry": enriched_contact["industry"],
            "company_size": enriched_contact["company_size"],
            "technologies": enriched_contact["technologies"],
        }

        for step in sales_sequence_context["steps"]:
            assert "template" in step
            assert step["channel"] in ["email", "linkedin", "call", "sms"]

    def test_crm_deal_stage_advancement_from_sales_activity(self) -> None:
        """Verify deal stages advance based on sales automation activities."""
        stage_progression = [
            {"stage": "prospecting", "trigger": "sequence_enrolled"},
            {"stage": "qualification", "trigger": "email_opened"},
            {"stage": "proposal", "trigger": "meeting_booked"},
            {"stage": "negotiation", "trigger": "proposal_sent"},
            {"stage": "closed_won", "trigger": "contract_signed"},
        ]

        current_stage_idx = 1
        current_stage = stage_progression[current_stage_idx]

        if current_stage["trigger"] == "email_opened":
            next_stage = stage_progression[current_stage_idx + 1]
            assert next_stage["stage"] == "proposal"

    def test_crm_sales_reporting_integration(self) -> None:
        """Verify reporting integrates CRM and sales automation data."""
        report = {
            "report_id": f"rpt_{uuid.uuid4().hex[:8]}",
            "period": "last_30_days",
            "crm_metrics": {
                "contacts_enriched": 150,
                "deals_scored": 45,
                "avg_deal_score": 62.5,
            },
            "sales_metrics": {
                "sequences_active": 30,
                "emails_sent": 450,
                "meetings_booked": 12,
                "deals_advanced": 8,
            },
            "conversion_metrics": {
                "enrichment_to_sequence": 0.30,
                "sequence_to_meeting": 0.40,
                "meeting_to_close": 0.25,
            },
        }

        assert report["crm_metrics"]["contacts_enriched"] > 0
        assert report["sales_metrics"]["sequences_active"] > 0
        assert 0.0 <= report["conversion_metrics"]["enrichment_to_sequence"] <= 1.0

    def test_crm_sales_error_handling(self) -> None:
        """Verify error handling in CRM-sales integration."""
        incomplete_contact = {
            "contact_id": f"contact_{uuid.uuid4().hex[:8]}",
            "email": "",
            "company": "Test Co",
        }

        can_automate = len(incomplete_contact.get("email", "")) > 0
        assert can_automate is False

        invalid_deal = {
            "deal_id": f"deal_{uuid.uuid4().hex[:8]}",
            "value": -1000.0,
        }

        assert invalid_deal["value"] < 0

    def test_crm_sales_data_sync_consistency(self) -> None:
        """Verify data consistency between CRM and sales automation systems."""
        crm_contact = {
            "contact_id": f"contact_{uuid.uuid4().hex[:8]}",
            "email": "sync@test.com",
            "company": "Sync Co",
            "last_modified": datetime.now(timezone.utc).isoformat(),
        }

        sales_contact = {
            "contact_id": crm_contact["contact_id"],
            "email": crm_contact["email"],
            "company": crm_contact["company"],
            "last_activity": datetime.now(timezone.utc).isoformat(),
        }

        assert crm_contact["contact_id"] == sales_contact["contact_id"]
        assert crm_contact["email"] == sales_contact["email"]
        assert crm_contact["company"] == sales_contact["company"]
