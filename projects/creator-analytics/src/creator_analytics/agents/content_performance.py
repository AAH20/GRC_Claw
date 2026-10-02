"""Content Performance Agent using LangChain DeepAgents."""

from datetime import datetime
from typing import Any

import structlog
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import tool

from creator_analytics.agents.base import BaseCreatorAgent
from creator_analytics.models.content import ContentMetrics, ContentPerformance, ContentType

logger = structlog.get_logger(__name__)


@tool
def calculate_performance_score(metrics: dict[str, float]) -> float:
    """Calculate overall performance score from content metrics.

    Args:
        metrics: Dictionary of content metrics.

    Returns:
        Performance score from 0 to 100.
    """
    weights = {
        "engagement_rate": 0.3,
        "views": 0.2,
        "watch_time": 0.2,
        "sentiment": 0.15,
        "shares": 0.15,
    }

    score = 0.0
    for key, weight in weights.items():
        value = metrics.get(key, 0.0)
        if key == "views":
            # Normalize views (assume 100k is max)
            value = min(value / 100000, 1.0)
        elif key == "watch_time":
            # Normalize watch time (assume 1 hour is max)
            value = min(value / 3600, 1.0)
        score += value * weight * 100

    return min(max(score, 0.0), 100.0)


@tool
def compare_to_benchmarks(
    content_type: str,
    metrics: dict[str, float],
    benchmarks: dict[str, dict[str, float]],
) -> dict[str, float]:
    """Compare content metrics to industry benchmarks.

    Args:
        content_type: Type of content.
        metrics: Content metrics.
        benchmarks: Industry benchmarks by content type.

    Returns:
        Comparison results showing percentage above/below benchmark.
    """
    type_benchmarks = benchmarks.get(content_type, {})
    comparison = {}

    for metric, value in metrics.items():
        benchmark = type_benchmarks.get(metric, 0.0)
        if benchmark > 0:
            comparison[metric] = ((value - benchmark) / benchmark) * 100
        else:
            comparison[metric] = 0.0

    return comparison


@tool
def extract_topics(title: str, description: str) -> list[str]:
    """Extract topics from content title and description.

    Args:
        title: Content title.
        description: Content description.

    Returns:
        List of extracted topics.
    """
    # Simple topic extraction based on keywords
    text = f"{title} {description}".lower()
    common_topics = [
        "tutorial", "review", "vlog", "education", "entertainment",
        "gaming", "music", "fashion", "food", "travel", "fitness",
        "technology", "comedy", "news", "sports",
    ]
    found = [topic for topic in common_topics if topic in text]
    return found if found else ["general"]


@tool
def analyze_sentiment(text: str) -> float:
    """Analyze sentiment of content or comments.

    Args:
        text: Text to analyze.

    Returns:
        Sentiment score from -1 (negative) to 1 (positive).
    """
    positive_words = ["great", "amazing", "love", "excellent", "fantastic", "good", "best"]
    negative_words = ["bad", "terrible", "hate", "worst", "awful", "poor", "disappointing"]

    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    total = pos_count + neg_count
    if total == 0:
        return 0.0

    return (pos_count - neg_count) / total


class ContentPerformanceAgent(BaseCreatorAgent):
    """Agent for analyzing content performance and providing optimization insights."""

    def __init__(self, llm: BaseLanguageModel | None = None) -> None:
        """Initialize the Content Performance Agent.

        Args:
            llm: Language model for agent reasoning.
        """
        super().__init__(llm=llm, name="content_performance")

    def _get_instructions(self) -> str:
        """Get system instructions for the content performance agent."""
        return (
            "You are an expert content performance analyst. "
            "Analyze content metrics, compare to benchmarks, and provide "
            "actionable recommendations for improving content performance. "
            "Focus on identifying what content resonates with audiences."
        )

    def _get_tools(self) -> list[Any]:
        """Get tools available to the content performance agent."""
        return [
            calculate_performance_score,
            compare_to_benchmarks,
            extract_topics,
            analyze_sentiment,
        ]

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run content performance analysis.

        Args:
            input_data: Dictionary containing:
                - content_id: Content identifier
                - creator_id: Creator identifier
                - content_type: Type of content
                - title: Content title
                - description: Content description
                - metrics: Raw metrics data
                - benchmarks: Industry benchmarks

        Returns:
            Content performance analysis results.
        """
        try:
            content_id = input_data.get("content_id", "")
            creator_id = input_data.get("creator_id", "")
            content_type = input_data.get("content_type", "video")
            title = input_data.get("title", "")
            description = input_data.get("description", "")
            metrics_data = input_data.get("metrics", {})
            benchmarks = input_data.get("benchmarks", {})

            logger.info(f"Analyzing content performance for {content_id}")

            # Calculate performance score
            perf_score = calculate_performance_score.invoke({"metrics": metrics_data})

            # Compare to benchmarks
            benchmark_comparison = compare_to_benchmarks.invoke({"content_type": content_type, "metrics": metrics_data, "benchmarks": benchmarks})

            # Extract topics
            topics = extract_topics.invoke({"title": title, "description": description})

            # Analyze sentiment
            sentiment = analyze_sentiment.invoke({"text": f"{title} {description}"})

            # Build metrics
            metrics = ContentMetrics(
                views=int(metrics_data.get("views", 0)),
                likes=int(metrics_data.get("likes", 0)),
                comments=int(metrics_data.get("comments", 0)),
                shares=int(metrics_data.get("shares", 0)),
                saves=int(metrics_data.get("saves", 0)),
                click_throughs=int(metrics_data.get("click_throughs", 0)),
                watch_time_seconds=float(metrics_data.get("watch_time_seconds", 0)),
                average_watch_percentage=float(metrics_data.get("average_watch_percentage", 0)),
                engagement_rate=float(metrics_data.get("engagement_rate", 0)),
                sentiment_score=sentiment,
            )

            # Use DeepAgent for deeper analysis
            if self._agent:
                agent_result = await self._agent.arun(
                    f"Analyze content performance for {title}. "
                    f"Metrics: {metrics_data}. "
                    f"Benchmark comparison: {benchmark_comparison}. "
                    f"Provide insights and recommendations."
                )
                insights = (
                    agent_result.get("insights", []) if isinstance(agent_result, dict) else []
                )
                recommendations = (
                    agent_result.get("recommendations", [])
                    if isinstance(agent_result, dict)
                    else []
                )
            else:
                insights = []
                recommendations = []

            performance = ContentPerformance(
                content_id=content_id,
                creator_id=creator_id,
                content_type=ContentType(content_type),
                title=title,
                description=description,
                published_at=input_data.get("published_at") or datetime.utcnow(),
                metrics=metrics,
                tags=input_data.get("tags", []),
                topics=topics,
                performance_score=perf_score,
                benchmark_comparison=benchmark_comparison,
                insights=insights,
                recommendations=recommendations,
            )

            return performance.model_dump()

        except Exception as e:
            logger.error(f"Content performance analysis failed: {e}")
            raise
