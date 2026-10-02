"""Engagement Analyzer Agent using LangChain DeepAgents."""

from datetime import datetime
from typing import Any

import structlog
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import tool

from creator_analytics.agents.base import BaseCreatorAgent
from creator_analytics.models.engagement import EngagementMetrics, EngagementReport, EngagementType

logger = structlog.get_logger(__name__)


@tool
def calculate_engagement_rate(
    total_interactions: int,
    total_followers: int,
    content_count: int,
) -> float:
    """Calculate overall engagement rate.

    Args:
        total_interactions: Total number of interactions.
        total_followers: Total follower count.
        content_count: Number of content pieces.

    Returns:
        Engagement rate as a decimal.
    """
    if total_followers == 0 or content_count == 0:
        return 0.0
    return total_interactions / (total_followers * content_count)


@tool
def analyze_engagement_by_type(
    interactions: dict[str, int],
) -> dict[str, Any]:
    """Analyze engagement breakdown by type.

    Args:
        interactions: Dictionary of interaction counts by type.

    Returns:
        Analysis with percentages and patterns.
    """
    total = sum(interactions.values())
    if total == 0:
        return {"total": 0, "breakdown": {}, "dominant_type": "none"}

    breakdown = {
        interaction_type: {
            "count": count,
            "percentage": (count / total) * 100,
        }
        for interaction_type, count in interactions.items()
    }

    dominant = max(interactions, key=interactions.get)

    return {
        "total": total,
        "breakdown": breakdown,
        "dominant_type": dominant,
    }


@tool
def calculate_loyalty_score(
    repeat_engagers: int,
    total_engagers: int,
    average_engagement_frequency: float,
) -> float:
    """Calculate audience loyalty score.

    Args:
        repeat_engagers: Number of users who engage repeatedly.
        total_engagers: Total number of engagers.
        average_engagement_frequency: Average engagements per user.

    Returns:
        Loyalty score from 0 to 100.
    """
    if total_engagers == 0:
        return 0.0

    repeat_rate = repeat_engagers / total_engagers
    frequency_score = min(average_engagement_frequency / 10, 1.0)

    return (repeat_rate * 0.6 + frequency_score * 0.4) * 100


@tool
def identify_peak_engagement_times(
    hourly_engagement: dict[int, int],
) -> list[dict[str, str]]:
    """Identify peak engagement time windows.

    Args:
        hourly_engagement: Engagement counts by hour.

    Returns:
        List of peak time windows.
    """
    if not hourly_engagement:
        return []

    sorted_hours = sorted(hourly_engagement.items(), key=lambda x: x[1], reverse=True)
    peak_hours = sorted_hours[:5]

    return [
        {
            "hour": str(hour),
            "engagement_count": str(count),
            "time_window": f"{hour:02d}:00-{(hour + 1) % 24:02d}:00",
        }
        for hour, count in peak_hours
    ]


@tool
def analyze_sentiment_distribution(
    sentiments: dict[str, int],
) -> dict[str, float]:
    """Analyze sentiment distribution.

    Args:
        sentiments: Sentiment counts (positive, negative, neutral).

    Returns:
        Sentiment distribution as percentages.
    """
    total = sum(sentiments.values())
    if total == 0:
        return {"positive": 0.0, "negative": 0.0, "neutral": 0.0}

    return {
        sentiment: (count / total) * 100
        for sentiment, count in sentiments.items()
    }


@tool
def calculate_community_health(
    engagement_rate: float,
    response_rate: float,
    sentiment_score: float,
    growth_rate: float,
) -> float:
    """Calculate overall community health score.

    Args:
        engagement_rate: Current engagement rate.
        response_rate: Creator response rate.
        sentiment_score: Average sentiment score.
        growth_rate: Community growth rate.

    Returns:
        Community health score from 0 to 100.
    """
    # Normalize sentiment from [-1, 1] to [0, 1]
    normalized_sentiment = (sentiment_score + 1) / 2

    score = (
        engagement_rate * 0.3
        + response_rate * 0.25
        + normalized_sentiment * 0.25
        + min(growth_rate, 1.0) * 0.2
    ) * 100

    return min(max(score, 0.0), 100.0)


class EngagementAnalyzerAgent(BaseCreatorAgent):
    """Agent for analyzing creator engagement and community health."""

    def __init__(self, llm: BaseLanguageModel | None = None) -> None:
        """Initialize the Engagement Analyzer Agent.

        Args:
            llm: Language model for agent reasoning.
        """
        super().__init__(llm=llm, name="engagement_analyzer")

    def _get_instructions(self) -> str:
        """Get system instructions for the engagement analyzer agent."""
        return (
            "You are an expert community engagement analyst. "
            "Analyze engagement patterns, measure community health, "
            "and provide recommendations for building stronger "
            "audience relationships."
        )

    def _get_tools(self) -> list[Any]:
        """Get tools available to the engagement analyzer agent."""
        return [
            calculate_engagement_rate,
            analyze_engagement_by_type,
            calculate_loyalty_score,
            identify_peak_engagement_times,
            analyze_sentiment_distribution,
            calculate_community_health,
        ]

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run engagement analysis.

        Args:
            input_data: Dictionary containing:
                - creator_id: Creator identifier
                - report_period_start: Start of reporting period
                - report_period_end: End of reporting period
                - total_interactions: Total interactions
                - interactions_by_type: Interactions by type
                - total_followers: Total follower count
                - content_count: Number of content pieces
                - repeat_engagers: Repeat engagers count
                - average_engagement_frequency: Average engagement frequency
                - hourly_engagement: Engagement by hour
                - sentiments: Sentiment counts
                - response_rate: Creator response rate
                - growth_rate: Community growth rate

        Returns:
            Engagement report with analysis.
        """
        try:
            creator_id = input_data.get("creator_id", "")
            total_interactions = input_data.get("total_interactions", 0)
            interactions_by_type = input_data.get("interactions_by_type", {})
            total_followers = input_data.get("total_followers", 0)
            content_count = input_data.get("content_count", 0)

            logger.info(f"Analyzing engagement for creator {creator_id}")

            # Calculate engagement rate
            engagement_rate = calculate_engagement_rate.invoke({
                "total_interactions": total_interactions, "total_followers": total_followers, "content_count": content_count
            })

            # Analyze by type
            # Analyze by type (result used implicitly)
            analyze_engagement_by_type.invoke({"interactions": interactions_by_type})

            # Calculate loyalty score
            loyalty_score = calculate_loyalty_score.invoke({
                "repeat_engagers": input_data.get("repeat_engagers", 0),
                "total_engagers": input_data.get("total_engagers", 0),
                "average_engagement_frequency": input_data.get("average_engagement_frequency", 0.0),
            })

            # Identify peak times
            peak_times = identify_peak_engagement_times.invoke({
                "hourly_engagement": input_data.get("hourly_engagement", {})
            })

            # Analyze sentiment
            sentiment_dist = analyze_sentiment_distribution.invoke({
                "sentiments": input_data.get("sentiments", {})
            })

            # Calculate community health
            community_health = calculate_community_health.invoke({
                "engagement_rate": engagement_rate,
                "response_rate": input_data.get("response_rate", 0.0),
                "sentiment_score": input_data.get("sentiment_score", 0.0),
                "growth_rate": input_data.get("growth_rate", 0.0),
            })

            # Build metrics
            metrics = EngagementMetrics(
                total_interactions=total_interactions,
                interactions_by_type={
                    EngagementType(k): v for k, v in interactions_by_type.items()
                },
                engagement_rate=engagement_rate,
                response_rate=input_data.get("response_rate", 0.0),
                average_response_time_minutes=input_data.get("average_response_time_minutes", 0.0),
                sentiment_distribution=sentiment_dist,
                peak_engagement_times=peak_times,
            )

            # Use DeepAgent for deeper analysis
            if self._agent:
                agent_result = await self._agent.arun(
                    f"Analyze engagement for creator {creator_id}. "
                    f"Engagement rate: {engagement_rate}. "
                    f"Loyalty score: {loyalty_score}. "
                    f"Community health: {community_health}. "
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

            report = EngagementReport(
                creator_id=creator_id,
                report_period_start=input_data.get("report_period_start") or datetime.utcnow(),
                report_period_end=input_data.get("report_period_end") or datetime.utcnow(),
                metrics=metrics,
                top_engaging_content=input_data.get("top_engaging_content", []),
                audience_loyalty_score=loyalty_score,
                community_health_score=community_health,
                trending_topics=input_data.get("trending_topics", []),
                influencer_collaborations=input_data.get("influencer_collaborations", []),
                insights=insights,
                recommendations=recommendations,
            )

            return report.model_dump()

        except Exception as e:
            logger.error(f"Engagement analysis failed: {e}")
            raise
