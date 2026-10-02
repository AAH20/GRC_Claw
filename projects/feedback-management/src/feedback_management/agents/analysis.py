"""Feedback Analysis Agent - performs sentiment analysis and topic extraction."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

from feedback_management.agents.collection import FeedbackItem

logger = structlog.get_logger(__name__)


class SentimentResult(BaseModel):
    """Result of sentiment analysis on a feedback item."""

    score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score from -1 to 1")
    label: str = Field(..., description="Sentiment label: positive, negative, or neutral")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the prediction")
    aspects: dict[str, float] = Field(
        default_factory=dict, description="Aspect-based sentiment scores"
    )


class TopicResult(BaseModel):
    """Extracted topic from feedback text."""

    name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    keywords: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Complete analysis result for a feedback item."""

    feedback_id: str
    sentiment: SentimentResult
    topics: list[TopicResult] = Field(default_factory=list)
    entities: list[dict[str, Any]] = Field(default_factory=list)
    urgency_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary: str = ""
    suggested_priority: str = Field(default="medium", description="low, medium, or high")
    language_detected: str = "en"
    analyzed_at: str = Field(default_factory=lambda: __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    ).isoformat())


class BatchAnalysisResult(BaseModel):
    """Result of analyzing a batch of feedback items."""

    total_items: int
    results: list[AnalysisResult]
    aggregate_sentiment: float = 0.0
    topic_distribution: dict[str, int] = Field(default_factory=dict)
    analyzed_at: str = Field(default_factory=lambda: __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    ).isoformat())


class AnalysisAgent:
    """Agent responsible for analyzing collected feedback.

    Performs sentiment analysis, topic extraction, entity recognition,
    and urgency scoring on feedback items using NLP models and LLMs.
    """

    def __init__(self, llm: Any = None, sentiment_model: Any = None) -> None:
        """Initialize the Analysis Agent.

        Args:
            llm: Language model for advanced analysis. If None, uses heuristic analysis.
            sentiment_model: Pre-trained sentiment classification model.
        """
        self.llm = llm
        self.sentiment_model = sentiment_model

    async def analyze(self, item: FeedbackItem) -> AnalysisResult:
        """Analyze a single feedback item.

        Args:
            item: The feedback item to analyze.

        Returns:
            AnalysisResult with sentiment, topics, entities, and urgency.
        """
        text = item.text.strip()

        sentiment = await self._analyze_sentiment(text)
        topics = await self._extract_topics(text)
        entities = await self._extract_entities(text)
        urgency_score = self._calculate_urgency(text, sentiment, item)
        summary = await self._generate_summary(text, sentiment, topics)
        suggested_priority = self._determine_priority(sentiment, urgency_score, item)

        logger.info(
            "Feedback analysis complete",
            feedback_id=item.id,
            sentiment=sentiment.label,
            priority=suggested_priority,
        )

        return AnalysisResult(
            feedback_id=item.id,
            sentiment=sentiment,
            topics=topics,
            entities=entities,
            urgency_score=urgency_score,
            summary=summary,
            suggested_priority=suggested_priority,
            language_detected=item.language,
        )

    async def analyze_batch(self, items: list[FeedbackItem]) -> BatchAnalysisResult:
        """Analyze a batch of feedback items.

        Args:
            items: List of feedback items to analyze.

        Returns:
            BatchAnalysisResult with individual and aggregate results.
        """
        import asyncio

        results = await asyncio.gather(*[self.analyze(item) for item in items])

        if results:
            aggregate_sentiment = sum(r.sentiment.score for r in results) / len(results)
        else:
            aggregate_sentiment = 0.0

        topic_dist: dict[str, int] = {}
        for r in results:
            for topic in r.topics:
                topic_dist[topic.name] = topic_dist.get(topic.name, 0) + 1

        logger.info(
            "Batch analysis complete",
            total_items=len(results),
            aggregate_sentiment=aggregate_sentiment,
        )

        return BatchAnalysisResult(
            total_items=len(results),
            results=list(results),
            aggregate_sentiment=aggregate_sentiment,
            topic_distribution=topic_dist,
        )

    async def _analyze_sentiment(self, text: str) -> SentimentResult:
        """Analyze sentiment of the given text.

        Args:
            text: The text to analyze.

        Returns:
            SentimentResult with score, label, confidence, and aspects.
        """
        if not text.strip():
            return SentimentResult(score=0.0, label="neutral", confidence=0.0)

        if self.sentiment_model:
            try:
                prediction = self.sentiment_model(text[:512])
                score = float(prediction.get("score", 0.0))
                label = prediction.get("label", "neutral").lower()
                confidence = float(prediction.get("confidence", 0.8))

                if label == "LABEL_0" or label == "negative":
                    normalized_label = "negative"
                    normalized_score = -score
                elif label == "LABEL_1" or label == "positive":
                    normalized_label = "positive"
                    normalized_score = score
                else:
                    normalized_label = "neutral"
                    normalized_score = 0.0

                return SentimentResult(
                    score=normalized_score,
                    label=normalized_label,
                    confidence=confidence,
                )
            except Exception as exc:
                logger.warning("Sentiment model failed, falling back to heuristic", error=str(exc))

        return self._heuristic_sentiment(text)

    def _heuristic_sentiment(self, text: str) -> SentimentResult:
        """Fallback heuristic sentiment analysis.

        Args:
            text: The text to analyze.

        Returns:
            SentimentResult based on keyword matching.
        """
        positive_words = {
            "great", "excellent", "amazing", "love", "fantastic",
            "wonderful", "good", "best", "happy", "satisfied",
        }
        negative_words = {
            "bad", "terrible", "awful", "hate", "worst", "poor",
            "disappointed", "horrible", "angry", "frustrated",
        }

        words = set(text.lower().split())
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        total = pos_count + neg_count

        if total == 0:
            return SentimentResult(score=0.0, label="neutral", confidence=0.5)

        score = (pos_count - neg_count) / max(total, 1)
        if score > 0.1:
            label = "positive"
        elif score < -0.1:
            label = "negative"
        else:
            label = "neutral"
            score = 0.0

        confidence = min(total / 5.0, 1.0) * 0.6 + 0.2

        return SentimentResult(score=score, label=label, confidence=confidence)

    async def _extract_topics(self, text: str) -> list[TopicResult]:
        """Extract topics from feedback text.

        Args:
            text: The text to extract topics from.

        Returns:
            List of TopicResult with topic names and confidence.
        """
        if not text.strip():
            return []

        topic_keywords = {
            "customer_service": ["service", "support", "help", "representative", "staff"],
            "product_quality": ["quality", "product", "item", "defective", "broken", "durability"],
            "pricing": ["price", "cost", "expensive", "cheap", "value", "money", "afford"],
            "delivery": ["delivery", "shipping", "arrived", "package", "tracking", "late"],
            "user_experience": [
                "experience", "easy", "difficult", "interface", "design", "usability",
            ],
            "bug_report": ["bug", "error", "crash", "broken", "not working", "glitch"],
            "feature_request": ["feature", "suggestion", "would like", "should have", "add"],
        }

        topics: list[TopicResult] = []

        for topic_name, keywords in topic_keywords.items():
            matching = [kw for kw in keywords if kw in text.lower()]
            if matching:
                confidence = min(len(matching) / max(len(keywords) * 0.3, 1.0), 1.0)
                topics.append(
                    TopicResult(
                        name=topic_name,
                        confidence=confidence,
                        keywords=matching,
                    )
                )

        topics.sort(key=lambda t: t.confidence, reverse=True)
        return topics[:5]

    async def _extract_entities(self, text: str) -> list[dict[str, Any]]:
        """Extract named entities from text.

        Args:
            text: The text to extract entities from.

        Returns:
            List of entity dictionaries with type, text, and position.
        """
        import re

        entities: list[dict[str, Any]] = []

        email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
        for match in email_pattern.finditer(text):
            entities.append({"type": "email", "text": match.group(), "start": match.start()})

        phone_pattern = re.compile(r"\+?[\d\s\-().]{7,20}")
        for match in phone_pattern.finditer(text):
            entities.append({
                "type": "phone", "text": match.group().strip(), "start": match.start(),
            })

        return entities

    def _calculate_urgency(
        self,
        text: str,
        sentiment: SentimentResult,
        item: FeedbackItem,
    ) -> float:
        """Calculate urgency score based on content, sentiment, and metadata.

        Args:
            text: The feedback text.
            sentiment: Sentiment analysis result.
            item: The original feedback item.

        Returns:
            Urgency score between 0.0 and 1.0.
        """
        score = 0.0

        urgent_keywords = {
            "urgent", "asap", "immediately", "emergency",
            "critical", "complaint", "refund", "cancel",
        }
        words = set(text.lower().lower().split())
        if words & urgent_keywords:
            score += 0.4

        if sentiment.score < -0.5:
            score += 0.3
        elif sentiment.score < -0.2:
            score += 0.15

        if item.rating is not None:
            if item.rating <= 2.0:
                score += 0.3
            elif item.rating <= 3.0:
                score += 0.1

        if item.customer_id:
            score += 0.05

        return min(score, 1.0)

    async def _generate_summary(self,
        text: str, sentiment: SentimentResult, topics: list[TopicResult]) -> str:
        """Generate a brief summary of the feedback.

        Args:
            text: The feedback text.
            sentiment: Sentiment analysis result.
            topics: Extracted topics.

        Returns:
            A brief summary string.
        """
        if len(text) <= 140:
            return text

        truncated = text[:140].rsplit(" ", 1)[0] + "..."

        if topics:
            topic_str = ", ".join(t.name.replace("_", " ") for t in topics[:2])
            return f"{sentiment.label.title()} feedback about {topic_str}. {truncated}"

        return f"{sentiment.label.title()} feedback. {truncated}"

    def _determine_priority(self,
        sentiment: SentimentResult, urgency: float, item: FeedbackItem) -> str:
        """Determine suggested priority based on multiple factors.

        Args:
            sentiment: Sentiment analysis result.
            urgency: Calculated urgency score.
            item: The original feedback item.

        Returns:
            Priority level: low, medium, or high.
        """
        if (
            urgency >= 0.6
            or sentiment.score < -0.6
            or (item.rating is not None and item.rating <= 1.0)
        ):
            return "high"
        if (
            urgency >= 0.3
            or sentiment.score < -0.2
            or (item.rating is not None and item.rating <= 3.0)
        ):
            return "medium"
        return "low"
