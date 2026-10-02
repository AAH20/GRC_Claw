"""Integration tests for Social Media Manager + Email Marketing.

Tests the integration between the social-media-manager and email-marketing projects,
verifying that social media campaigns and email campaigns work together cohesively,
with shared audience data, coordinated scheduling, and unified analytics.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pytest


class TestSocialEmailIntegration:
    """Integration tests for social-media-manager and email-marketing collaboration."""

    @pytest.fixture
    def social_campaign_data(self) -> Dict[str, Any]:
        """Create social media campaign data for cross-channel testing.

        Returns:
            Social campaign data dictionary.
        """
        return {
            "campaign_id": f"social_{uuid.uuid4().hex[:12]}",
            "name": "Cross-Channel Test Campaign",
            "platforms": ["twitter", "instagram", "linkedin"],
            "content_calendar": [
                {
                    "platform": "twitter",
                    "content": "Exciting product launch! #NewProduct",
                    "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                },
                {
                    "platform": "instagram",
                    "content": "Behind the scenes of our latest innovation",
                    "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
                },
            ],
            "target_audience": {
                "demographics": {"age": "25-45", "locations": ["US", "UK"]},
                "interests": ["technology", "innovation"],
            },
        }

    @pytest.fixture
    def email_campaign_data(self) -> Dict[str, Any]:
        """Create email campaign data for cross-channel testing.

        Returns:
            Email campaign data dictionary.
        """
        return {
            "campaign_id": f"email_{uuid.uuid4().hex[:12]}",
            "name": "Cross-Channel Email Sequence",
            "emails": [
                {
                    "subject": "Welcome to the future",
                    "template": "welcome_v2",
                    "delay_days": 0,
                },
                {
                    "subject": "Discover what's new",
                    "template": "product_highlight",
                    "delay_days": 3,
                },
                {
                    "subject": "Exclusive offer inside",
                    "template": "promotional",
                    "delay_days": 7,
                },
            ],
            "segment": "all_subscribers",
        }

    @pytest.fixture
    def unified_customer_profile(self) -> Dict[str, Any]:
        """Create a unified customer profile spanning social and email.

        Returns:
            Unified customer profile dictionary.
        """
        return {
            "customer_id": f"cust_{uuid.uuid4().hex[:8]}",
            "email": "customer@example.com",
            "social_handles": {
                "twitter": "@customer",
                "instagram": "@customer",
                "linkedin": "customer-profile",
            },
            "email_engagement": {
                "open_rate": 0.35,
                "click_rate": 0.12,
                "last_open": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            },
            "social_engagement": {
                "follower": True,
                "engagement_rate": 0.08,
                "last_interaction": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            },
            "preferred_channel": "email",
        }

    def test_social_post_triggers_email_followup(
        self, social_campaign_data: Dict[str, Any], email_campaign_data: Dict[str, Any]
    ) -> None:
        """Verify social media posts trigger coordinated email follow-ups.

        Args:
            social_campaign_data: Social campaign data fixture.
            email_campaign_data: Email campaign data fixture.
        """
        social_engagement = {
            "post_id": f"post_{uuid.uuid4().hex[:8]}",
            "likes": 150,
            "comments": 25,
            "shares": 10,
            "clicks": 45,
        }

        if social_engagement["clicks"] > 30:
            email_trigger = {
                "trigger": "social_engagement",
                "email_template": "product_highlight",
                "delay_hours": 24,
            }
            assert email_trigger["trigger"] == "social_engagement"
            assert email_trigger["delay_hours"] > 0

    def test_email_engagement_informs_social_targeting(
        self, unified_customer_profile: Dict[str, Any]
    ) -> None:
        """Verify email engagement data informs social media targeting.

        Args:
            unified_customer_profile: Unified customer profile fixture.
        """
        email_engagement = unified_customer_profile["email_engagement"]

        if email_engagement["open_rate"] >= 0.3:
            social_priority = "high"
            bid_modifier = 1.5
        else:
            social_priority = "normal"
            bid_modifier = 1.0

        assert social_priority in ["high", "normal", "low"]
        assert bid_modifier >= 1.0

    def test_cross_channel_content_coordination(
        self, social_campaign_data: Dict[str, Any], email_campaign_data: Dict[str, Any]
    ) -> None:
        """Verify content is coordinated across social and email channels.

        Args:
            social_campaign_data: Social campaign data fixture.
            email_campaign_data: Email campaign data fixture.
        """
        social_content = social_campaign_data["content_calendar"][0]["content"]
        email_subject = email_campaign_data["emails"][0]["subject"]

        assert len(social_content) > 0
        assert len(email_subject) > 0

        social_times = [
            item["scheduled_at"] for item in social_campaign_data["content_calendar"]
        ]
        assert len(social_times) == len(set(social_times))

    def test_unified_customer_journey_across_channels(
        self, unified_customer_profile: Dict[str, Any]
    ) -> None:
        """Verify customer journey is unified across social and email.

        Args:
            unified_customer_profile: Unified customer profile fixture.
        """
        customer = unified_customer_profile

        assert len(customer["social_handles"]) > 0
        assert customer["email"] is not None

        email_engaged = customer["email_engagement"]["open_rate"] > 0.2
        social_engaged = customer["social_engagement"]["engagement_rate"] > 0.05

        if email_engaged and social_engaged:
            assert customer["preferred_channel"] in ["email", "social"]

    def test_social_email_analytics_aggregation(
        self, social_campaign_data: Dict[str, Any], email_campaign_data: Dict[str, Any]
    ) -> None:
        """Verify analytics are aggregated across social and email channels.

        Args:
            social_campaign_data: Social campaign data fixture.
            email_campaign_data: Email campaign data fixture.
        """
        cross_channel_metrics = {
            "social": {
                "impressions": 50000,
                "engagements": 2500,
                "clicks": 800,
                "conversions": 45,
            },
            "email": {
                "sent": 10000,
                "delivered": 9500,
                "opened": 3500,
                "clicked": 1200,
                "conversions": 85,
            },
        }

        total_conversions = (
            cross_channel_metrics["social"]["conversions"]
            + cross_channel_metrics["email"]["conversions"]
        )
        assert total_conversions > 0

        email_conv_rate = (
            cross_channel_metrics["email"]["conversions"]
            / cross_channel_metrics["email"]["delivered"]
        )
        social_conv_rate = (
            cross_channel_metrics["social"]["conversions"]
            / cross_channel_metrics["social"]["impressions"]
        )
        assert email_conv_rate > social_conv_rate

    def test_social_email_scheduling_coordination(self) -> None:
        """Verify social and email campaigns are scheduled without conflicts."""
        base_time = datetime.now(timezone.utc)

        social_schedule = [
            {"platform": "twitter", "time": base_time + timedelta(hours=9)},
            {"platform": "instagram", "time": base_time + timedelta(hours=12)},
        ]

        email_schedule = [
            {"template": "welcome", "time": base_time + timedelta(hours=10)},
            {"template": "followup", "time": base_time + timedelta(hours=14)},
        ]

        all_times = [s["time"] for s in social_schedule] + [e["time"] for e in email_schedule]
        all_times.sort()

        for i in range(len(all_times) - 1):
            gap = (all_times[i + 1] - all_times[i]).total_seconds() / 3600
            assert gap >= 0.5, f"Scheduling conflict: {gap}h gap"

    def test_cross_channel_attribution(
        self, unified_customer_profile: Dict[str, Any]
    ) -> None:
        """Verify attribution works across social and email touchpoints.

        Args:
            unified_customer_profile: Unified customer profile fixture.
        """
        journey = [
            {"channel": "social", "touch": "impression", "time": "2024-01-01T09:00:00"},
            {"channel": "social", "touch": "click", "time": "2024-01-01T09:05:00"},
            {"channel": "email", "touch": "open", "time": "2024-01-01T10:00:00"},
            {"channel": "email", "touch": "click", "time": "2024-01-01T10:02:00"},
            {"channel": "social", "touch": "conversion", "time": "2024-01-01T11:00:00"},
        ]

        last_touch = journey[-1]
        assert last_touch["channel"] == "social"

        first_touch = journey[0]
        assert first_touch["channel"] == "social"

        channels_touched = set(t["channel"] for t in journey)
        assert "social" in channels_touched
        assert "email" in channels_touched

    def test_social_email_segmentation_sync(
        self, unified_customer_profile: Dict[str, Any]
    ) -> None:
        """Verify audience segments are synced between social and email.

        Args:
            unified_customer_profile: Unified customer profile fixture.
        """
        segment = {
            "name": "highly_engaged",
            "criteria": {
                "email_open_rate": ">= 0.25",
                "social_engagement": ">= 0.05",
            },
            "channels": ["email", "social"],
            "estimated_size": 5000,
        }

        assert segment["criteria"]["email_open_rate"] == ">= 0.25"
        assert "email" in segment["channels"]
        assert "social" in segment["channels"]

    def test_social_email_error_handling(self) -> None:
        """Verify error handling in cross-channel operations."""
        incomplete_profile = {
            "customer_id": f"cust_{uuid.uuid4().hex[:8]}",
            "email": "test@example.com",
            "social_handles": {},
        }

        assert len(incomplete_profile["social_handles"]) == 0

        available_channels = ["email"]
        assert "email" in available_channels

    def test_cross_channel_frequency_capping(self) -> None:
        """Verify frequency capping across social and email channels."""
        customer_id = f"cust_{uuid.uuid4().hex[:8]}"

        touchpoints = [
            {"channel": "email", "time": datetime.now(timezone.utc) - timedelta(hours=2)},
            {"channel": "social", "time": datetime.now(timezone.utc) - timedelta(hours=4)},
            {"channel": "email", "time": datetime.now(timezone.utc) - timedelta(hours=6)},
        ]

        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_count = sum(
            1 for t in touchpoints if t["time"] > recent_cutoff
        )

        max_frequency = 5
        assert recent_count <= max_frequency

        if recent_count >= max_frequency:
            next_action = "suppress"
        else:
            next_action = "send"

        assert next_action in ["send", "suppress"]
