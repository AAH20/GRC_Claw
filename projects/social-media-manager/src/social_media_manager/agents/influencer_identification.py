"""Influencer Identification agent — discovers and scores brand partners."""

from __future__ import annotations

from typing import Any

from social_media_manager.agents.base import BaseAgent


class InfluencerIdentificationAgent(BaseAgent):
    """Scores candidate influencers for brand-fit and reach."""

    name = "influencer_identification"
    description = "Discovers and ranks influencers by relevance and reach"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Rank a list of candidate influencers.

        Args:
            payload: Must contain ``candidates`` (list of dicts with
                ``handle`` and ``followers``). Optional: ``niche``,
                ``min_followers``, ``top_n``.

        Returns:
            Dictionary with ``ranked`` (list, best first) and ``summary``.

        Raises:
            ValueError: If candidates are missing or malformed.
        """
        candidates = self._require(payload, "candidates")
        if not isinstance(candidates, list) or not candidates:
            raise ValueError("'candidates' must be a non-empty list")

        niche = str(payload.get("niche", "")).lower()
        min_followers = int(payload.get("min_followers", 0))
        top_n = int(payload.get("top_n", 10))

        scored: list[dict[str, Any]] = []
        for idx, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                raise ValueError(f"candidates[{idx}] must be an object")
            handle = str(candidate.get("handle", "")).strip()
            if not handle:
                raise ValueError(f"candidates[{idx}] is missing 'handle'")
            followers = self._as_int(candidate.get("followers", 0))
            engagement_rate = float(candidate.get("engagement_rate", 0.0))
            topics = [str(t).lower() for t in candidate.get("topics", [])]

            if followers < min_followers:
                continue

            score = self._score(followers, engagement_rate, topics, niche)
            scored.append(
                {
                    "handle": handle,
                    "followers": followers,
                    "engagement_rate": engagement_rate,
                    "topics": topics,
                    "score": score,
                    "tier": self._tier(followers),
                }
            )

        scored.sort(key=lambda c: c["score"], reverse=True)
        ranked = scored[:top_n]

        return {
            "ranked": ranked,
            "summary": {
                "candidates_evaluated": len(candidates),
                "candidates_qualified": len(scored),
                "returned": len(ranked),
                "niche": niche or None,
                "min_followers": min_followers,
            },
        }

    @staticmethod
    def _as_int(value: Any) -> int:
        """Coerce a value to a non-negative int, raising on bad input."""
        try:
            result = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid follower count: {value!r}") from exc
        if result < 0:
            raise ValueError("Follower count cannot be negative")
        return result

    @staticmethod
    def _score(
        followers: int, engagement_rate: float, topics: list[str], niche: str
    ) -> float:
        """Compute a weighted relevance score in ``[0, 100]``."""
        reach = min(followers / 1_000_000, 1.0) * 40
        engagement = min(engagement_rate / 10.0, 1.0) * 40
        relevance = 20.0 if niche and niche in topics else 5.0
        return round(reach + engagement + relevance, 2)

    @staticmethod
    def _tier(followers: int) -> str:
        """Classify an influencer into a conventional reach tier."""
        if followers >= 1_000_000:
            return "mega"
        if followers >= 100_000:
            return "macro"
        if followers >= 10_000:
            return "micro"
        return "nano"
