"""Analysis Agent - Performs sentiment analysis, topic extraction, and trend detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class Sentiment(StrEnum):
    """Sentiment classification."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class Topic(StrEnum):
    """Common topic categories for brand mentions."""

    PRODUCT = "product"
    SERVICE = "service"
    PRICING = "pricing"
    SUPPORT = "support"
    COMPETITION = "competition"
    GENERAL = "general"


@dataclass
class AnalysisResult:
    """Result of analyzing a brand mention."""

    mention_id: str
    sentiment: Sentiment
    sentiment_score: float
    topics: list[Topic]
    keywords: list[str]
    entities: list[str]
    urgency: int
    analyzed_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class AnalysisAgent:
    """Agent responsible for analyzing brand mentions."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.logger = logger.bind(agent="analysis")
        self._sentiment_threshold_positive = config.get("sentiment_threshold_positive", 0.6)
        self._sentiment_threshold_negative = config.get("sentiment_threshold_negative", -0.6)

    async def analyze(self, mention: Any) -> AnalysisResult:
        """Analyze a single brand mention."""
        self.logger.info("Analyzing mention", mention_id=getattr(mention, "id", "unknown"))

        sentiment, score = await self._analyze_sentiment(mention.content)
        topics = await self._extract_topics(mention.content)
        keywords = await self._extract_keywords(mention.content)
        entities = await self._extract_entities(mention.content)
        urgency = self._calculate_urgency(sentiment, score, topics)

        result = AnalysisResult(
            mention_id=mention.id,
            sentiment=sentiment,
            sentiment_score=score,
            topics=topics,
            keywords=keywords,
            entities=entities,
            urgency=urgency,
            analyzed_at=datetime.utcnow(),
        )

        self.logger.info(
            "Analysis complete",
            mention_id=mention.id,
            sentiment=sentiment.value,
            score=score,
        )
        return result

    async def analyze_batch(self, mentions: list[Any]) -> list[AnalysisResult]:
        """Analyze a batch of mentions."""
        self.logger.info("Starting batch analysis", count=len(mentions))
        results: list[AnalysisResult] = []
        for mention in mentions:
            try:
                result = await self.analyze(mention)
                results.append(result)
            except Exception as exc:
                self.logger.error(
                    "Failed to analyze mention",
                    mention_id=getattr(mention, "id", "unknown"),
                    error=str(exc),
                )
        self.logger.info("Batch analysis complete", analyzed=len(results))
        return results

    async def _analyze_sentiment(self, text: str) -> tuple[Sentiment, float]:
        """Analyze sentiment of text."""
        positive_words = {"great", "excellent", "amazing", "love", "best", "good", "happy"}
        negative_words = {"bad", "terrible", "awful", "hate", "worst", "poor", "angry"}

        text_lower = text.lower()
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)

        total = pos_count + neg_count
        if total == 0:
            return Sentiment.NEUTRAL, 0.0

        score = (pos_count - neg_count) / max(total, 1)

        if score >= self._sentiment_threshold_positive:
            return Sentiment.POSITIVE, score
        if score <= self._sentiment_threshold_negative:
            return Sentiment.NEGATIVE, score
        return Sentiment.MIXED, score

    async def _extract_topics(self, text: str) -> list[Topic]:
        """Extract topics from text."""
        topic_keywords = {
            Topic.PRODUCT: {"product", "feature", "app", "software", "tool"},
            Topic.SERVICE: {"service", "support", "help", "customer"},
            Topic.PRICING: {"price", "cost", "expensive", "cheap", "value", "subscription"},
            Topic.SUPPORT: {"support", "help", "issue", "bug", "problem", "fix"},
            Topic.COMPETITION: {"competitor", "alternative", "vs", "compared"},
        }

        text_lower = text.lower()
        detected: list[Topic] = []
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                detected.append(topic)

        return detected or [Topic.GENERAL]

    async def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text."""
        words = text.lower().split()
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been"}
        keywords = [w.strip(".,!?;:\"'") for w in words if w not in stop_words and len(w) > 3]
        return list(set(keywords))[:10]

    async def _extract_entities(self, text: str) -> list[str]:
        """Extract named entities from text."""
        return []

    def _calculate_urgency(
        self,
        sentiment: Sentiment,
        score: float,
        topics: list[Topic],
    ) -> int:
        """Calculate urgency level (1-5)."""
        urgency = 1

        if sentiment == Sentiment.NEGATIVE:
            urgency += 2
        if Topic.SUPPORT in topics:
            urgency += 1
        if abs(score) > 0.8:
            urgency += 1

        return min(urgency, 5)
