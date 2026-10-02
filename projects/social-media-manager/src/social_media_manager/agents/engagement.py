"""Engagement agent — drafts replies to comments, mentions and DMs."""

from __future__ import annotations

from typing import Any

from social_media_manager.agents.base import BaseAgent

POSITIVE_WORDS = {"love", "great", "awesome", "thanks", "amazing", "excellent"}
NEGATIVE_WORDS = {"hate", "bad", "terrible", "awful", "broken", "refund", "angry"}


class EngagementAgent(BaseAgent):
    """Classifies inbound messages and drafts appropriate responses."""

    name = "engagement"
    description = "Triages mentions/comments and drafts on-brand replies"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Analyse an inbound message and draft a response.

        Args:
            payload: Must contain ``message``. Optional: ``platform``,
                ``author``, ``brand_name``.

        Returns:
            Dictionary with ``intent``, ``sentiment``, ``priority``,
            ``draft_reply`` and ``escalate``.

        Raises:
            ValueError: If ``message`` is missing or empty.
        """
        message = str(self._require(payload, "message")).strip()
        platform = str(payload.get("platform", "twitter")).lower()
        author = str(payload.get("author", "there"))
        brand = str(payload.get("brand_name", "our team"))

        intent = self._classify_intent(message)
        sentiment, score = self._score_sentiment(message)
        priority = self._priority(intent, sentiment)
        escalate = intent in {"complaint", "support"} or sentiment == "negative"

        return {
            "platform": platform,
            "intent": intent,
            "sentiment": sentiment,
            "sentiment_score": score,
            "priority": priority,
            "escalate": escalate,
            "draft_reply": self._draft(intent, sentiment, author, brand),
        }

    @staticmethod
    def _classify_intent(message: str) -> str:
        """Classify the message intent using keyword heuristics."""
        text = message.lower()
        if any(w in text for w in ("?", "how do i", "help", "issue", "not working")):
            return "support"
        if any(w in text for w in ("refund", "angry", "terrible", "worst", "complaint")):
            return "complaint"
        if any(w in text for w in ("price", "buy", "purchase", "cost", "discount")):
            return "sales"
        if any(w in text for w in ("love", "great", "thanks", "amazing", "awesome")):
            return "praise"
        return "general"

    @staticmethod
    def _score_sentiment(message: str) -> tuple[str, float]:
        """Return a coarse sentiment label and a score in ``[-1, 1]``."""
        words = set(message.lower().split())
        pos = len(words & POSITIVE_WORDS)
        neg = len(words & NEGATIVE_WORDS)
        total = pos + neg
        if total == 0:
            return "neutral", 0.0
        score = (pos - neg) / total
        if score > 0.2:
            return "positive", round(score, 2)
        if score < -0.2:
            return "negative", round(score, 2)
        return "neutral", round(score, 2)

    @staticmethod
    def _priority(intent: str, sentiment: str) -> str:
        """Derive a triage priority from intent and sentiment."""
        if intent in {"complaint", "support"} or sentiment == "negative":
            return "high"
        if intent in {"sales", "praise"}:
            return "medium"
        return "low"

    @staticmethod
    def _draft(intent: str, sentiment: str, author: str, brand: str) -> str:
        """Draft an on-brand reply matching the detected intent."""
        first = author.split()[0] if author else "there"
        templates = {
            "support": f"Hi {first}, thanks for reaching out! We'd love to help — "
                       f"could you DM us your details so {brand} can look into it?",
            "complaint": f"Hi {first}, we're sorry to hear this. We take it seriously "
                         f"and want to make it right. Please DM us so we can help.",
            "sales": f"Thanks for your interest, {first}! We'll send you pricing details "
                     f"for {brand} right away.",
            "praise": f"Thank you so much, {first}! 🙌 Feedback like this makes our day.",
            "general": f"Thanks for engaging, {first}! We appreciate you being part of "
                       f"the {brand} community.",
        }
        reply = templates.get(intent, templates["general"])
        if sentiment == "negative" and intent not in {"complaint", "support"}:
            reply = f"Hi {first}, we hear you and want to help. Please DM us the details."
        return reply
