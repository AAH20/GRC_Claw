"""Social Listening agent — tracks mentions, sentiment and trends."""

from __future__ import annotations

from collections import Counter
from typing import Any

from social_media_manager.agents.base import BaseAgent

NEGATIVE = {"hate", "bad", "terrible", "awful", "worst", "broken", "scam"}
POSITIVE = {"love", "great", "amazing", "excellent", "best", "awesome", "perfect"}


class SocialListeningAgent(BaseAgent):
    """Aggregates brand mentions and surfaces trending topics."""

    name = "social_listening"
    description = "Monitors brand mentions, sentiment and emerging trends"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Analyse a batch of mentions for sentiment and trends.

        Args:
            payload: Must contain ``brand`` and ``mentions`` (list of dicts
                with a ``text`` field). Optional: ``top_n``.

        Returns:
            Dictionary with ``mention_count``, ``sentiment_breakdown``,
            ``trending_topics`` and ``alerts``.

        Raises:
            ValueError: If required fields are missing or malformed.
        """
        brand = str(self._require(payload, "brand")).strip()
        mentions = self._require(payload, "mentions")
        if not isinstance(mentions, list):
            raise ValueError("'mentions' must be a list of objects")

        top_n = int(payload.get("top_n", 5))
        counts: Counter[str] = Counter()
        keywords: Counter[str] = Counter()
        negative_samples: list[str] = []

        for idx, mention in enumerate(mentions):
            if not isinstance(mention, dict) or "text" not in mention:
                raise ValueError(f"mentions[{idx}] must be a dict with a 'text' field")
            text = str(mention["text"])
            label = self._sentiment(text)
            counts[label] += 1
            if label == "negative":
                negative_samples.append(text)
            for word in self._tokenize(text):
                if word not in {"the", "a", "and", "to", "of", "is", "in", "it"}:
                    keywords[word] += 1

        total = len(mentions) or 1
        breakdown = {
            label: {
                "count": counts.get(label, 0),
                "percentage": round(counts.get(label, 0) / total * 100, 2),
            }
            for label in ("positive", "neutral", "negative")
        }

        alerts: list[dict[str, Any]] = []
        if breakdown["negative"]["percentage"] >= 30:
            alerts.append(
                {
                    "level": "warning",
                    "message": "Negative sentiment exceeds 30% of mentions",
                    "sample": negative_samples[:3],
                }
            )

        return {
            "brand": brand,
            "mention_count": len(mentions),
            "sentiment_breakdown": breakdown,
            "trending_topics": [word for word, _ in keywords.most_common(top_n)],
            "alerts": alerts,
        }

    @staticmethod
    def _sentiment(text: str) -> str:
        """Return a coarse sentiment label for ``text``."""
        words = set(text.lower().split())
        pos, neg = len(words & POSITIVE), len(words & NEGATIVE)
        if pos > neg:
            return "positive"
        if neg > pos:
            return "negative"
        return "neutral"

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Lowercase and split text into alphanumeric tokens."""
        return ["".join(c for c in w.lower() if c.isalnum()) for w in text.split()]
