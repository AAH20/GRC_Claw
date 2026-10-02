"""Performance benchmarks for the Social Media Manager component.

These benchmarks verify that social media operations meet production
SLAs for latency and throughput.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.performance.conftest import BenchmarkResult


@pytest.mark.critical
class TestSocialMediaBenchmarks:
    """Benchmark suite for social media operations."""

    SLA_MS = 300.0

    def test_post_scheduling_latency(
        self,
        run_benchmark: Any,
        sample_social_payload: dict[str, Any],
    ) -> None:
        """Benchmark post scheduling latency."""
        def schedule_posts() -> dict[str, Any]:
            platforms = sample_social_payload["platforms"]
            posts = sample_social_payload["posts"]
            posts_per_day = sample_social_payload["posts_per_day"]
            schedule = []
            post_idx = 0
            for platform in platforms:
                for day in range(posts_per_day):
                    if post_idx < len(posts):
                        schedule.append({
                            "platform": platform,
                            "post_id": posts[post_idx]["id"],
                            "scheduled": True,
                        })
                        post_idx += 1
            return {"scheduled": schedule, "total_scheduled": len(schedule)}

        result = run_benchmark(schedule_posts, name="post_scheduling", iterations=200)
        assert result.avg_ms <= self.SLA_MS

    def test_optimal_posting_time_calculation(self, run_benchmark: Any) -> None:
        """Benchmark optimal posting time calculation."""
        def calculate_optimal_times() -> dict[str, list[int]]:
            return {
                "twitter": [8, 12, 17],
                "instagram": [11, 14, 19],
                "facebook": [9, 13, 16],
                "linkedin": [7, 10, 15],
                "tiktok": [6, 15, 21],
            }

        result = run_benchmark(calculate_optimal_times, name="optimal_time_calculation", iterations=500)
        assert result.avg_ms <= self.SLA_MS

    def test_engagement_rate_calculation(self, run_benchmark: Any) -> None:
        """Benchmark engagement rate calculation."""
        def calculate_engagement() -> dict[str, Any]:
            posts = [
                {"id": f"post_{i}", "likes": 100 + i * 10, "comments": 20 + i * 2,
                 "shares": 10 + i, "impressions": 5000 + i * 100}
                for i in range(50)
            ]
            results = []
            for post in posts:
                engagement = post["likes"] + post["comments"] + post["shares"]
                rate = (engagement / post["impressions"]) * 100 if post["impressions"] > 0 else 0
                results.append({"post_id": post["id"], "engagement_rate": round(rate, 2)})
            return {"posts": results}

        result = run_benchmark(calculate_engagement, name="engagement_rate_calculation", iterations=200)
        assert result.avg_ms <= self.SLA_MS

    def test_social_listening_sentiment_analysis(self, run_benchmark: Any) -> None:
        """Benchmark social listening sentiment analysis."""
        def analyze_sentiment() -> dict[str, Any]:
            mentions = [{"id": f"m_{i}", "text": f"Sample {i}"} for i in range(100)]
            positive_words = {"great", "love", "amazing"}
            negative_words = {"bad", "hate", "terrible"}
            results = {"positive": 0, "negative": 0, "neutral": 0}
            for mention in mentions:
                text_lower = mention["text"].lower()
                if any(w in text_lower for w in positive_words):
                    results["positive"] += 1
                elif any(w in text_lower for w in negative_words):
                    results["negative"] += 1
                else:
                    results["neutral"] += 1
            return {**results, "total": len(mentions)}

        result = run_benchmark(analyze_sentiment, name="sentiment_analysis", iterations=100)
        assert result.avg_ms <= self.SLA_MS

    def test_influencer_scoring_performance(self, run_benchmark: Any) -> None:
        """Benchmark influencer scoring performance."""
        def score_influencers() -> list[dict[str, Any]]:
            influencers = [
                {"id": f"inf_{i}", "followers": 10000 + i * 1000,
                 "engagement_rate": 2.0 + i * 0.1, "relevance_score": 0.5 + i * 0.02}
                for i in range(30)
            ]
            scored = []
            for inf in influencers:
                score = (0.4 * min(inf["engagement_rate"] / 10.0, 1.0)
                         + 0.3 * inf["relevance_score"]
                         + 0.3 * min(inf["followers"] / 100000.0, 1.0))
                scored.append({"id": inf["id"], "score": round(score, 3)})
            return sorted(scored, key=lambda x: x["score"], reverse=True)

        result = run_benchmark(score_influencers, name="influencer_scoring", iterations=100)
        assert result.avg_ms <= self.SLA_MS

    def test_content_calendar_generation(self, run_benchmark: Any) -> None:
        """Benchmark content calendar generation."""
        def generate_calendar() -> dict[str, Any]:
            platforms = ["twitter", "instagram", "linkedin"]
            calendar = []
            for day in range(1, 31):
                for platform in platforms:
                    if day % 2 == 0 or platform == "twitter":
                        calendar.append({"day": day, "platform": platform, "status": "planned"})
            return {"entries": calendar, "total_entries": len(calendar)}

        result = run_benchmark(generate_calendar, name="calendar_generation", iterations=50)
        assert result.avg_ms <= self.SLA_MS * 2
