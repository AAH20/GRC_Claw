"""Tests for the autonomous agents."""

from __future__ import annotations

import pytest

from social_media_manager.agents import (
    ContentCreationAgent,
    EngagementAgent,
    InfluencerIdentificationAgent,
    PerformanceAnalyticsAgent,
    SchedulingAgent,
    SocialListeningAgent,
)


class TestContentCreationAgent:
    """Content creation agent behaviour."""

    def test_generates_post_with_hashtags(self) -> None:
        agent = ContentCreationAgent()
        result = agent.invoke(
            {"topic": "new product launch", "platform": "twitter", "keywords": ["launch", "ai"]}
        )
        assert result.success
        assert result.data["platform"] == "twitter"
        assert "#Launch" in result.data["hashtags"]
        assert result.data["character_count"] <= result.data["character_limit"]

    def test_rejects_unsupported_platform(self) -> None:
        agent = ContentCreationAgent()
        result = agent.invoke({"topic": "hi", "platform": "myspace"})
        assert not result.success
        assert "Unsupported platform" in (result.error or "")

    def test_respects_character_limit(self) -> None:
        agent = ContentCreationAgent()
        result = agent.invoke({"topic": "x" * 500, "platform": "twitter"})
        assert result.success
        assert result.data["character_count"] <= 280

    def test_missing_topic_fails_gracefully(self) -> None:
        result = ContentCreationAgent().invoke({"platform": "twitter"})
        assert not result.success
        assert "topic" in (result.error or "")


class TestSchedulingAgent:
    """Scheduling agent behaviour."""

    def test_builds_schedule(self) -> None:
        agent = SchedulingAgent()
        result = agent.invoke(
            {"platforms": ["twitter", "linkedin"], "start_date": "2026-01-01T00:00:00Z"}
        )
        assert result.success
        assert len(result.data["schedule"]) == 2
        assert result.data["summary"]["total_slots"] == 2

    def test_invalid_date_fails(self) -> None:
        result = SchedulingAgent().invoke(
            {"platforms": ["twitter"], "start_date": "not-a-date"}
        )
        assert not result.success

    def test_rejects_empty_platforms(self) -> None:
        result = SchedulingAgent().invoke({"platforms": [], "start_date": "2026-01-01"})
        assert not result.success


class TestEngagementAgent:
    """Engagement agent behaviour."""

    def test_detects_complaint_and_escalates(self) -> None:
        result = EngagementAgent().invoke(
            {"message": "This is terrible, I want a refund!", "author": "Jane Doe"}
        )
        assert result.success
        assert result.data["intent"] == "complaint"
        assert result.data["escalate"] is True
        assert "Jane" in result.data["draft_reply"]

    def test_detects_praise(self) -> None:
        result = EngagementAgent().invoke({"message": "I love this, amazing work!"})
        assert result.success
        assert result.data["intent"] == "praise"
        assert result.data["sentiment"] == "positive"

    def test_empty_message_fails(self) -> None:
        assert not EngagementAgent().invoke({"message": "   "}).success


class TestSocialListeningAgent:
    """Social listening agent behaviour."""

    def test_aggregates_sentiment(self) -> None:
        mentions = [
            {"text": "I love this brand, amazing"},
            {"text": "terrible product, broken"},
            {"text": "it is fine"},
        ]
        result = SocialListeningAgent().invoke({"brand": "Acme", "mentions": mentions})
        assert result.success
        assert result.data["mention_count"] == 3
        assert result.data["sentiment_breakdown"]["positive"]["count"] == 1
        assert result.data["sentiment_breakdown"]["negative"]["count"] == 1

    def test_negative_alert(self) -> None:
        mentions = [{"text": "terrible awful worst"}] * 3
        result = SocialListeningAgent().invoke({"brand": "Acme", "mentions": mentions})
        assert result.data["alerts"]

    def test_malformed_mention_fails(self) -> None:
        assert not SocialListeningAgent().invoke(
            {"brand": "Acme", "mentions": ["not a dict"]}
        ).success


class TestInfluencerIdentificationAgent:
    """Influencer identification agent behaviour."""

    def test_ranks_by_score(self) -> None:
        candidates = [
            {"handle": "@small", "followers": 5000, "engagement_rate": 1.0},
            {
                "handle": "@big",
                "followers": 2_000_000,
                "engagement_rate": 9.0,
                "topics": ["fitness"],
            },
        ]
        result = InfluencerIdentificationAgent().invoke(
            {"candidates": candidates, "niche": "fitness"}
        )
        assert result.success
        assert result.data["ranked"][0]["handle"] == "@big"
        assert result.data["ranked"][0]["tier"] == "mega"

    def test_min_followers_filter(self) -> None:
        candidates = [{"handle": "@small", "followers": 100}]
        result = InfluencerIdentificationAgent().invoke(
            {"candidates": candidates, "min_followers": 1000}
        )
        assert result.data["summary"]["candidates_qualified"] == 0

    def test_empty_candidates_fails(self) -> None:
        assert not InfluencerIdentificationAgent().invoke({"candidates": []}).success


class TestPerformanceAnalyticsAgent:
    """Performance analytics agent behaviour."""

    def test_computes_totals_and_rate(self) -> None:
        posts = [
            {"impressions": 1000, "likes": 50, "comments": 10, "shares": 5},
            {"impressions": 500, "likes": 25, "comments": 5, "shares": 2},
        ]
        result = PerformanceAnalyticsAgent().invoke({"posts": posts})
        assert result.success
        assert result.data["totals"]["impressions"] == 1500
        assert result.data["totals"]["interactions"] == 97
        assert result.data["engagement_rate"] > 0

    def test_negative_metric_fails(self) -> None:
        result = PerformanceAnalyticsAgent().invoke(
            {"posts": [{"impressions": -5}]}
        )
        assert not result.success

    def test_empty_posts_fails(self) -> None:
        assert not PerformanceAnalyticsAgent().invoke({"posts": []}).success
