"""Growth Predictor Agent using LangChain DeepAgents."""

from typing import Any

import structlog
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import tool

from creator_analytics.agents.base import BaseCreatorAgent
from creator_analytics.models.growth import GrowthPrediction, GrowthScenario

logger = structlog.get_logger(__name__)


@tool
def predict_follower_growth(
    current_followers: int,
    monthly_growth_rate: float,
    months: int,
) -> dict[str, int]:
    """Predict follower growth under different scenarios.

    Args:
        current_followers: Current follower count.
        monthly_growth_rate: Average monthly growth rate.
        months: Number of months to predict.

    Returns:
        Predicted followers for conservative, moderate, and aggressive scenarios.
    """
    conservative_rate = monthly_growth_rate * 0.5
    moderate_rate = monthly_growth_rate
    aggressive_rate = monthly_growth_rate * 1.5

    return {
        "conservative": int(current_followers * ((1 + conservative_rate) ** months)),
        "moderate": int(current_followers * ((1 + moderate_rate) ** months)),
        "aggressive": int(current_followers * ((1 + aggressive_rate) ** months)),
    }


@tool
def predict_revenue_growth(
    current_monthly_revenue: float,
    revenue_growth_rate: float,
    months: int,
) -> dict[str, float]:
    """Predict revenue growth under different scenarios.

    Args:
        current_monthly_revenue: Current monthly revenue.
        revenue_growth_rate: Average monthly revenue growth rate.
        months: Number of months to predict.

    Returns:
        Predicted monthly revenue for conservative, moderate, and aggressive scenarios.
    """
    conservative_rate = revenue_growth_rate * 0.5
    moderate_rate = revenue_growth_rate
    aggressive_rate = revenue_growth_rate * 1.5

    return {
        "conservative": current_monthly_revenue * ((1 + conservative_rate) ** months),
        "moderate": current_monthly_revenue * ((1 + moderate_rate) ** months),
        "aggressive": current_monthly_revenue * ((1 + aggressive_rate) ** months),
    }


@tool
def identify_growth_drivers(
    content_frequency: int,
    engagement_rate: float,
    collaboration_count: int,
    platform_diversity: int,
) -> list[str]:
    """Identify key growth drivers from creator activity.

    Args:
        content_frequency: Posts per week.
        engagement_rate: Current engagement rate.
        collaboration_count: Collaborations per month.
        platform_diversity: Number of active platforms.

    Returns:
        List of key growth drivers.
    """
    drivers = []

    if content_frequency >= 3:
        drivers.append("Consistent content schedule")
    if engagement_rate > 0.05:
        drivers.append("High audience engagement")
    if collaboration_count >= 2:
        drivers.append("Regular collaborations")
    if platform_diversity >= 3:
        drivers.append("Multi-platform presence")

    if not drivers:
        drivers.append("Room for improvement in content consistency")

    return drivers


@tool
def assess_risks(
    platform_dependency: float,
    content_saturation: float,
    audience_concentration: float,
) -> list[str]:
    """Assess potential risks to growth.

    Args:
        platform_dependency: Revenue dependency on single platform (0-1).
        content_saturation: Market saturation level (0-1).
        audience_concentration: Audience concentration risk (0-1).

    Returns:
        List of identified risk factors.
    """
    risks = []

    if platform_dependency > 0.7:
        risks.append("High dependency on single platform")
    if content_saturation > 0.6:
        risks.append("Market saturation in content niche")
    if audience_concentration > 0.5:
        risks.append("Audience concentration risk")

    if not risks:
        risks.append("No major risks identified")

    return risks


@tool
def calculate_confidence_score(
    data_quality: float,
    historical_accuracy: float,
    market_volatility: float,
) -> float:
    """Calculate confidence score for predictions.

    Args:
        data_quality: Quality of input data (0-1).
        historical_accuracy: Historical prediction accuracy (0-1).
        market_volatility: Market volatility factor (0-1).

    Returns:
        Confidence score from 0 to 1.
    """
    base_confidence = (data_quality + historical_accuracy) / 2
    volatility_penalty = market_volatility * 0.2
    return max(0.0, min(1.0, base_confidence - volatility_penalty))


class GrowthPredictorAgent(BaseCreatorAgent):
    """Agent for predicting creator growth trajectories."""

    def __init__(self, llm: BaseLanguageModel | None = None) -> None:
        """Initialize the Growth Predictor Agent.

        Args:
            llm: Language model for agent reasoning.
        """
        super().__init__(llm=llm, name="growth_predictor")

    def _get_instructions(self) -> str:
        """Get system instructions for the growth predictor agent."""
        return (
            "You are an expert growth strategist for content creators. "
            "Predict growth trajectories, identify key growth drivers, "
            "and assess risks. Provide actionable recommendations "
            "for sustainable growth."
        )

    def _get_tools(self) -> list[Any]:
        """Get tools available to the growth predictor agent."""
        return [
            predict_follower_growth,
            predict_revenue_growth,
            identify_growth_drivers,
            assess_risks,
            calculate_confidence_score,
        ]

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run growth prediction analysis.

        Args:
            input_data: Dictionary containing:
                - creator_id: Creator identifier
                - current_followers: Current follower count
                - current_monthly_revenue: Current monthly revenue
                - monthly_growth_rate: Average monthly growth rate
                - revenue_growth_rate: Average monthly revenue growth rate
                - prediction_period_months: Months to predict
                - content_frequency: Posts per week
                - engagement_rate: Current engagement rate
                - collaboration_count: Collaborations per month
                - platform_diversity: Number of active platforms

        Returns:
            Growth prediction with scenarios and recommendations.
        """
        try:
            creator_id = input_data.get("creator_id", "")
            current_followers = input_data.get("current_followers", 0)
            current_monthly_revenue = input_data.get("current_monthly_revenue", 0.0)
            monthly_growth_rate = input_data.get("monthly_growth_rate", 0.0)
            revenue_growth_rate = input_data.get("revenue_growth_rate", 0.0)
            months = input_data.get("prediction_period_months", 12)

            logger.info(f"Predicting growth for creator {creator_id}")

            # Predict follower growth
            predicted_followers = predict_follower_growth.invoke({
                "current_followers": current_followers, "monthly_growth_rate": monthly_growth_rate, "months": months
            })

            # Predict revenue growth
            predicted_revenue = predict_revenue_growth.invoke({
                "current_monthly_revenue": current_monthly_revenue, "revenue_growth_rate": revenue_growth_rate, "months": months
            })

            # Identify growth drivers
            drivers = identify_growth_drivers.invoke({
                "content_frequency": input_data.get("content_frequency", 0),
                "engagement_rate": input_data.get("engagement_rate", 0.0),
                "collaboration_count": input_data.get("collaboration_count", 0),
                "platform_diversity": input_data.get("platform_diversity", 1),
            })

            # Assess risks
            risks = assess_risks.invoke({
                "platform_dependency": input_data.get("platform_dependency", 0.5),
                "content_saturation": input_data.get("content_saturation", 0.3),
                "audience_concentration": input_data.get("audience_concentration", 0.3),
            })

            # Calculate confidence
            confidence = calculate_confidence_score.invoke({
                "data_quality": input_data.get("data_quality", 0.8),
                "historical_accuracy": input_data.get("historical_accuracy", 0.7),
                "market_volatility": input_data.get("market_volatility", 0.3),
            })

            # Generate milestones
            milestones = []
            for month in [3, 6, 9, 12]:
                if month <= months:
                    moderate_followers = int(
                        current_followers * ((1 + monthly_growth_rate) ** month)
                    )
                    milestones.append({
                        "month": str(month),
                        "follower_target": str(moderate_followers),
                        "milestone": f"Reach {moderate_followers} followers",
                    })

            # Use DeepAgent for deeper analysis
            if self._agent:
                agent_result = await self._agent.arun(
                    f"Predict growth for creator {creator_id}. "
                    f"Current followers: {current_followers}. "
                    f"Growth rate: {monthly_growth_rate}. "
                    f"Drivers: {drivers}. Risks: {risks}. "
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

            prediction = GrowthPrediction(
                creator_id=creator_id,
                prediction_period_months=months,
                current_followers=current_followers,
                predicted_followers={
                    GrowthScenario.CONSERVATIVE: predicted_followers["conservative"],
                    GrowthScenario.MODERATE: predicted_followers["moderate"],
                    GrowthScenario.AGGRESSIVE: predicted_followers["aggressive"],
                },
                current_monthly_revenue=current_monthly_revenue,
                predicted_monthly_revenue={
                    GrowthScenario.CONSERVATIVE: predicted_revenue["conservative"],
                    GrowthScenario.MODERATE: predicted_revenue["moderate"],
                    GrowthScenario.AGGRESSIVE: predicted_revenue["aggressive"],
                },
                growth_rate_predictions={
                    GrowthScenario.CONSERVATIVE: monthly_growth_rate * 0.5,
                    GrowthScenario.MODERATE: monthly_growth_rate,
                    GrowthScenario.AGGRESSIVE: monthly_growth_rate * 1.5,
                },
                key_growth_drivers=drivers,
                risk_factors=risks,
                milestones=milestones,
                confidence_score=confidence,
                insights=insights,
                recommendations=recommendations,
            )

            return prediction.model_dump()

        except Exception as e:
            logger.error(f"Growth prediction failed: {e}")
            raise
