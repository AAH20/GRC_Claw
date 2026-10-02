"""Audience Analyzer Agent using LangChain DeepAgents."""

from typing import Any
import structlog
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import tool

from creator_analytics.agents.base import BaseCreatorAgent
from creator_analytics.models.audience import Audience, AudienceDemographics, AudienceSegment

logger = structlog.get_logger(__name__)


@tool
def analyze_demographics(age_data: dict[str, float], gender_data: dict[str, float]) -> dict[str, Any]:
    """Analyze demographic data and identify patterns.

    Args:
        age_data: Age group distribution data.
        gender_data: Gender distribution data.

    Returns:
        Analysis results with key demographic insights.
    """
    insights = []
    dominant_age = max(age_data, key=age_data.get) if age_data else "unknown"
    dominant_gender = max(gender_data, key=gender_data.get) if gender_data else "unknown"

    insights.append(f"Dominant age group: {dominant_age}")
    insights.append(f"Dominant gender: {dominant_gender}")

    return {
        "dominant_age_group": dominant_age,
        "dominant_gender": dominant_gender,
        "insights": insights,
    }


@tool
def segment_audience(follower_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Segment audience based on behavior and demographics.

    Args:
        follower_data: List of follower data points.

    Returns:
        List of audience segments.
    """
    segments = []
    # Simple segmentation logic
    active = [f for f in follower_data if f.get("active", False)]
    inactive = [f for f in follower_data if not f.get("active", False)]

    if active:
        segments.append({
            "name": "Active Engaged",
            "size": len(active),
            "characteristics": ["high engagement", "regular interaction"],
        })
    if inactive:
        segments.append({
            "name": "Inactive",
            "size": len(inactive),
            "characteristics": ["low engagement", "need re-engagement"],
        })

    return segments


@tool
def identify_interests(content_tags: list[str], engagement_data: dict[str, float]) -> list[str]:
    """Identify top audience interests from content performance.

    Args:
        content_tags: List of content tags.
        engagement_data: Engagement data by tag.

    Returns:
        List of top interests.
    """
    sorted_tags = sorted(engagement_data.items(), key=lambda x: x[1], reverse=True)
    return [tag for tag, _ in sorted_tags[:5]]


class AudienceAnalyzerAgent(BaseCreatorAgent):
    """Agent for analyzing creator audience demographics, segments, and behavior."""

    def __init__(self, llm: BaseLanguageModel | None = None) -> None:
        """Initialize the Audience Analyzer Agent.

        Args:
            llm: Language model for agent reasoning.
        """
        super().__init__(llm=llm, name="audience_analyzer")

    def _get_instructions(self) -> str:
        """Get system instructions for the audience analyzer."""
        return (
            "You are an expert audience analyst for content creators. "
            "Analyze audience demographics, identify segments, and provide "
            "actionable insights about audience behavior and preferences. "
            "Focus on identifying growth opportunities and engagement patterns."
        )

    def _get_tools(self) -> list[Any]:
        """Get tools available to the audience analyzer."""
        return [analyze_demographics, segment_audience, identify_interests]

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run audience analysis.

        Args:
            input_data: Dictionary containing:
                - creator_id: Creator identifier
                - follower_data: Raw follower data
                - engagement_data: Engagement metrics
                - content_tags: Content tags for interest analysis

        Returns:
            Audience analysis results.
        """
        try:
            creator_id = input_data.get("creator_id", "")
            follower_data = input_data.get("follower_data", [])
            engagement_data = input_data.get("engagement_data", {})
            content_tags = input_data.get("content_tags", [])

            logger.info(f"Running audience analysis for creator {creator_id}")

            # Use the DeepAgent to process the analysis
            if self._agent:
                result = await self._agent.arun(
                    f"Analyze the audience for creator {creator_id}. "
                    f"Follower data: {follower_data}. "
                    f"Engagement data: {engagement_data}. "
                    f"Content tags: {content_tags}"
                )
            else:
                result = {"error": "Agent not initialized"}

            # Build structured response
            audience = Audience(
                creator_id=creator_id,
                total_followers=input_data.get("total_followers", 0),
                active_followers=input_data.get("active_followers", 0),
                demographics=AudienceDemographics(
                    age_distribution=input_data.get("age_distribution", {}),
                    gender_distribution=input_data.get("gender_distribution", {}),
                    top_countries=input_data.get("top_countries", {}),
                    top_cities=input_data.get("top_cities", {}),
                    languages=input_data.get("languages", {}),
                    interests=identify_interests(content_tags, engagement_data),
                ),
                segments=[],  # Populated from segment_audience tool
                growth_rate=input_data.get("growth_rate", 0.0),
                churn_rate=input_data.get("churn_rate", 0.0),
                peak_activity_hours=input_data.get("peak_activity_hours", []),
                insights=result.get("insights", []) if isinstance(result, dict) else [],
                recommendations=result.get("recommendations", []) if isinstance(result, dict) else [],
            )

            return audience.model_dump()

        except Exception as e:
            logger.error(f"Audience analysis failed: {e}")
            raise
