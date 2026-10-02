"""Performance Analytics agent — aggregates metrics into insights."""

from __future__ import annotations

from statistics import mean
from typing import Any

from social_media_manager.agents.base import BaseAgent


class PerformanceAnalyticsAgent(BaseAgent):
    """Computes engagement metrics and generates recommendations."""

    name = "performance_analytics"
    description = "Aggregates performance metrics and produces insight reports"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Analyse post-level metrics and surface insights.

        Args:
            payload: Must contain ``posts`` (list of dicts with ``impressions``,
                ``likes``, ``comments``, ``shares``). Optional: ``platform``.

        Returns:
            Dictionary with ``totals``, ``averages``, ``engagement_rate`` and
            ``insights``.

        Raises:
            ValueError: If posts are missing or malformed.
        """
        posts = self._require(payload, "posts")
        if not isinstance(posts, list) or not posts:
            raise ValueError("'posts' must be a non-empty list")

        impressions = likes = comments = shares = 0
        per_post_rates: list[float] = []

        for idx, post in enumerate(posts):
            if not isinstance(post, dict):
                raise ValueError(f"posts[{idx}] must be an object")
            imp = self._num(post.get("impressions", 0), idx, "impressions")
            lk = self._num(post.get("likes", 0), idx, "likes")
            cm = self._num(post.get("comments", 0), idx, "comments")
            sh = self._num(post.get("shares", 0), idx, "shares")

            impressions += imp
            likes += lk
            comments += cm
            shares += sh
            if imp > 0:
                per_post_rates.append((lk + cm + sh) / imp * 100)

        interactions = likes + comments + shares
        engagement_rate = round(interactions / impressions * 100, 2) if impressions else 0.0
        n = len(posts)

        insights: list[str] = []
        if engagement_rate >= 5:
            insights.append("Engagement rate is strong (>=5%); consider scaling similar content.")
        elif engagement_rate < 1:
            insights.append("Engagement rate is below 1%; revisit creative and posting times.")
        if comments and shares and comments > shares * 3:
            insights.append("High comment-to-share ratio — content sparks discussion; add CTAs.")
        if not insights:
            insights.append("Performance is within expected ranges; continue monitoring.")

        return {
            "platform": str(payload.get("platform", "all")).lower(),
            "totals": {
                "posts": n,
                "impressions": impressions,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "interactions": interactions,
            },
            "averages": {
                "impressions_per_post": round(impressions / n, 2),
                "interactions_per_post": round(interactions / n, 2),
                "best_engagement_rate": round(max(per_post_rates), 2) if per_post_rates else 0.0,
                "avg_engagement_rate": round(mean(per_post_rates), 2) if per_post_rates else 0.0,
            },
            "engagement_rate": engagement_rate,
            "insights": insights,
        }

    @staticmethod
    def _num(value: Any, idx: int, field: str) -> int:
        """Validate and coerce a metric value to a non-negative int."""
        try:
            result = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"posts[{idx}].{field} must be numeric, got {value!r}") from exc
        if result < 0:
            raise ValueError(f"posts[{idx}].{field} cannot be negative")
        return result
