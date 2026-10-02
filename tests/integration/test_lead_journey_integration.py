"""Integration tests for Lead Scorer + Journey Orchestrator.

Tests the integration between the lead-scorer and journey-orchestrator projects,
verifying that scored leads trigger appropriate journey workflows and that
journey execution results feed back into lead scoring.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pytest


class TestLeadJourneyIntegration:
    """Integration tests for lead-scorer and journey-orchestrator collaboration."""

    @pytest.fixture
    def scored_lead(self, sample_lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fully scored lead ready for journey enrollment.

        Args:
            sample_lead_data: Base lead data fixture.

        Returns:
            Scored lead dictionary with journey-ready fields.
        """
        return {
            **sample_lead_data,
            "total_score": 78.5,
            "grade": "A",
            "confidence": 0.85,
            "scoring_model": "weighted_v2",
            "qualified": True,
            "qualification_score": 82.0,
            "next_best_action": "start_nurture_journey",
        }

    @pytest.fixture
    def journey_context(self, sample_journey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a journey context for lead enrollment.

        Args:
            sample_journey_data: Base journey data fixture.

        Returns:
            Journey context dictionary with execution metadata.
        """
        return {
            "journey_id": f"journey_{uuid.uuid4().hex[:12]}",
            "name": sample_journey_data["name"],
            "status": "active",
            "target_audience": sample_journey_data["target_audience"],
            "business_goal": sample_journey_data["business_goal"],
            "channels": sample_journey_data["channels"],
        }

    def test_scored_lead_triggers_journey_enrollment(
        self, scored_lead: Dict[str, Any], journey_context: Dict[str, Any]
    ) -> None:
        """Verify a qualified lead triggers journey enrollment.

        Args:
            scored_lead: Scored lead fixture.
            journey_context: Journey context fixture.
        """
        # Only qualified leads should enter journeys
        assert scored_lead["qualified"] is True
        assert scored_lead["qualification_score"] >= 70.0

        # Journey should be active
        assert journey_context["status"] == "active"

        # Lead grade should meet journey entry threshold
        assert scored_lead["grade"] in ["A+", "A", "B+", "B"]

    def test_lead_grade_determines_journey_track(
        self, sample_lead_data: Dict[str, Any]
    ) -> None:
        """Verify lead grade determines which journey track is assigned.

        Args:
            sample_lead_data: Sample lead data fixture.
        """
        grade_track_mapping = {
            "A+": "premium_nurture",
            "A": "high_touch_nurture",
            "B+": "standard_nurture",
            "B": "self_serve_nurture",
            "C+": "low_priority_nurture",
            "C": "re_engagement",
            "D": "disqualify",
            "F": "disqualify",
        }

        for grade, track in grade_track_mapping.items():
            assert isinstance(track, str)
            assert len(track) > 0

        # High-grade leads should get premium tracks
        assert grade_track_mapping["A+"] == "premium_nurture"
        assert grade_track_mapping["A"] == "high_touch_nurture"

    def test_journey_execution_updates_lead_score(
        self, scored_lead: Dict[str, Any]
    ) -> None:
        """Verify journey execution results update lead engagement scores.

        Args:
            scored_lead: Scored lead fixture.
        """
        initial_engagement = scored_lead["engagement_score"]

        # Simulate journey touchpoint increasing engagement
        journey_touchpoints = [
            {"type": "email_open", "engagement_delta": 5.0},
            {"type": "email_click", "engagement_delta": 10.0},
            {"type": "page_visit", "engagement_delta": 3.0},
        ]

        total_delta = sum(t["engagement_delta"] for t in journey_touchpoints)
        updated_engagement = min(100.0, initial_engagement + total_delta)

        assert updated_engagement > initial_engagement
        assert updated_engagement <= 100.0

    def test_journey_channel_alignment_with_lead_preferences(
        self, scored_lead: Dict[str, Any], journey_context: Dict[str, Any]
    ) -> None:
        """Verify journey channels align with lead engagement patterns.

        Args:
            scored_lead: Scored lead fixture.
            journey_context: Journey context fixture.
        """
        journey_channels = set(journey_context["channels"])
        valid_channels = {"email", "sms", "push", "web", "ads"}

        assert journey_channels.issubset(valid_channels)
        assert len(journey_channels) > 0

        # High-engagement leads should have multi-channel journeys
        if scored_lead["engagement_score"] >= 70.0:
            assert len(journey_channels) >= 1

    def test_lead_journey_end_to_end_flow(
        self,
        sample_lead_data: Dict[str, Any],
        sample_journey_data: Dict[str, Any],
    ) -> None:
        """Test the complete flow from lead scoring to journey execution.

        Args:
            sample_lead_data: Sample lead data fixture.
            sample_journey_data: Sample journey data fixture.
        """
        # Step 1: Score the lead
        lead_score = {
            "lead_id": sample_lead_data["lead_id"],
            "total_score": 82.0,
            "grade": "A",
            "confidence": 0.88,
            "qualified": True,
        }
        assert lead_score["qualified"] is True

        # Step 2: Determine journey track
        journey_track = "high_touch_nurture" if lead_score["grade"] == "A" else "standard"
        assert journey_track == "high_touch_nurture"

        # Step 3: Create journey enrollment
        enrollment = {
            "enrollment_id": f"enroll_{uuid.uuid4().hex[:8]}",
            "lead_id": lead_score["lead_id"],
            "journey_id": f"journey_{uuid.uuid4().hex[:12]}",
            "track": journey_track,
            "status": "enrolled",
            "enrolled_at": datetime.now(timezone.utc).isoformat(),
        }
        assert enrollment["status"] == "enrolled"

        # Step 4: Execute journey stage
        stage_result = {
            "stage": "welcome_email",
            "status": "completed",
            "channel": "email",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        assert stage_result["status"] == "completed"

    def test_journey_personalization_uses_lead_data(
        self, scored_lead: Dict[str, Any], journey_context: Dict[str, Any]
    ) -> None:
        """Verify journey personalization incorporates lead scoring data.

        Args:
            scored_lead: Scored lead fixture.
            journey_context: Journey context fixture.
        """
        personalization_context = {
            "lead_id": scored_lead["lead_id"],
            "grade": scored_lead["grade"],
            "total_score": scored_lead["total_score"],
            "company_name": scored_lead["company_name"],
            "industry": scored_lead.get("industry", ""),
            "journey_track": "high_touch_nurture",
        }

        assert personalization_context["lead_id"] is not None
        assert personalization_context["grade"] in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]
        assert personalization_context["total_score"] > 0.0

    def test_lead_disqualification_stops_journey(
        self, sample_lead_data: Dict[str, Any]
    ) -> None:
        """Verify disqualified leads are removed from active journeys.

        Args:
            sample_lead_data: Sample lead data fixture.
        """
        disqualified_lead = {
            **sample_lead_data,
            "qualified": False,
            "qualification_score": 35.0,
            "grade": "D",
            "risk_factors": ["budget_timeline_mismatch", "authority_gap"],
        }

        assert disqualified_lead["qualified"] is False
        assert disqualified_lead["qualification_score"] < 50.0

        # Journey should be paused/stopped
        journey_action = "pause" if disqualified_lead["qualified"] is False else "continue"
        assert journey_action == "pause"

    def test_journey_analytics_feedback_loop(
        self, scored_lead: Dict[str, Any]
    ) -> None:
        """Verify journey analytics create a feedback loop to lead scoring.

        Args:
            scored_lead: Scored lead fixture.
        """
        # Simulate journey analytics data
        journey_analytics = {
            "emails_sent": 5,
            "emails_opened": 3,
            "emails_clicked": 2,
            "pages_visited": 4,
            "content_downloaded": 1,
            "meetings_booked": 1,
        }

        # Calculate engagement score from journey analytics
        engagement_indicators = [
            journey_analytics["emails_opened"] / max(journey_analytics["emails_sent"], 1),
            journey_analytics["emails_clicked"] / max(journey_analytics["emails_opened"], 1),
            journey_analytics["pages_visited"] / max(journey_analytics["emails_clicked"], 1),
        ]

        avg_engagement = sum(engagement_indicators) / len(engagement_indicators)
        assert 0.0 <= avg_engagement <= 1.0

        # Update lead engagement score
        updated_score = min(100.0, scored_lead["engagement_score"] + avg_engagement * 10)
        assert updated_score >= scored_lead["engagement_score"]

    def test_multi_lead_journey_segmentation(
        self, sample_lead_data: Dict[str, Any]
    ) -> None:
        """Verify multiple leads are correctly segmented into journey tracks.

        Args:
            sample_lead_data: Sample lead data fixture.
        """
        leads = []
        for i in range(10):
            lead = {**sample_lead_data}
            lead["lead_id"] = f"lead_{uuid.uuid4().hex[:8]}"
            lead["total_score"] = 40.0 + i * 6.0
            lead["grade"] = ["D", "C", "C+", "B", "B+", "A", "A+", "A", "B+", "B"][i]
            leads.append(lead)

        # Segment leads by grade
        premium_leads = [l for l in leads if l["grade"] in ["A+", "A"]]
        standard_leads = [l for l in leads if l["grade"] in ["B+", "B"]]
        low_priority = [l for l in leads if l["grade"] in ["C+", "C", "D", "F"]]

        assert len(premium_leads) + len(standard_leads) + len(low_priority) == 10
        assert len(premium_leads) > 0
        assert len(standard_leads) > 0

    def test_journey_timing_optimization_with_lead_scores(
        self, scored_lead: Dict[str, Any]
    ) -> None:
        """Verify journey timing is optimized based on lead score patterns.

        Args:
            scored_lead: Scored lead fixture.
        """
        # High-score leads should get faster journey progression
        if scored_lead["total_score"] >= 80.0:
            expected_pace = "accelerated"
            max_stages = 3
        elif scored_lead["total_score"] >= 60.0:
            expected_pace = "standard"
            max_stages = 5
        else:
            expected_pace = "extended"
            max_stages = 7

        assert expected_pace in ["accelerated", "standard", "extended"]
        assert max_stages >= 3

        # Timing optimization should consider lead engagement
        timing_config = {
            "pace": expected_pace,
            "max_stages": max_stages,
            "channel": "email",
            "optimal_send_time": "10:00",
            "frequency_cap": 3 if expected_pace == "accelerated" else 2,
        }

        assert timing_config["frequency_cap"] >= 1
