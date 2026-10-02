"""Action Agent - generates actionable recommendations based on forecasts."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

import structlog

from sales_forecaster.core.exceptions import AnalysisError
from sales_forecaster.core.metrics import record_agent_error
from sales_forecaster.core.models import (
    ActionRecommendation,
    AnalysisResult,
    ForecastResult,
)

logger = structlog.get_logger(__name__)


class ActionAgent:
    """Agent responsible for generating actionable recommendations.

    Analyzes forecast results and analysis insights to produce prioritized,
    actionable recommendations for sales teams.
    """

    def __init__(
        self,
        max_recommendations: int = 10,
        priority_threshold: float = 0.7,
        auto_approve: bool = False,
    ) -> None:
        """Initialize the Action Agent.

        Args:
            max_recommendations: Maximum number of recommendations to generate.
            priority_threshold: Minimum confidence threshold for recommendations.
            auto_approve: Whether to auto-approve high-confidence recommendations.
        """
        self.max_recommendations = max_recommendations
        self.priority_threshold = priority_threshold
        self.auto_approve = auto_approve

    async def generate_recommendations(
        self,
        forecast: ForecastResult,
        analysis: AnalysisResult | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[ActionRecommendation]:
        """Generate actionable recommendations based on forecast and analysis.

        Args:
            forecast: The forecast result from the Prediction Agent.
            analysis: Optional analysis result from the Analysis Agent.
            context: Optional additional context (e.g., team capacity, budget).

        Returns:
            List of prioritized action recommendations.

        Raises:
            AnalysisError: If recommendation generation fails.
        """
        logger.info(
            "Generating recommendations",
            forecast_id=forecast.id,
            has_analysis=analysis is not None,
        )

        try:
            recommendations: list[ActionRecommendation] = []

            # Trend-based recommendations
            if analysis:
                recommendations.extend(
                    self._recommendations_from_trend(forecast, analysis)
                )

                # Anomaly-based recommendations
                recommendations.extend(
                    self._recommendations_from_anomalies(forecast, analysis)
                )

                # Seasonality-based recommendations
                if analysis.seasonality_detected:
                    recommendations.extend(
                        self._recommendations_from_seasonality(forecast, analysis)
                    )

            # Forecast-based recommendations
            recommendations.extend(
                self._recommendations_from_forecast(forecast, context)
            )

            # Sort by priority and confidence, then limit
            recommendations.sort(key=lambda r: (r.priority, -r.confidence))
            recommendations = recommendations[: self.max_recommendations]

            logger.info(
                "Recommendations generated",
                count=len(recommendations),
                forecast_id=forecast.id,
            )
            return recommendations

        except Exception as exc:
            record_agent_error("action")
            logger.error(
                "Recommendation generation failed",
                error=str(exc),
                exc_info=True,
            )
            raise AnalysisError(f"Failed to generate recommendations: {exc}") from exc

    def _recommendations_from_trend(
        self, forecast: ForecastResult, analysis: AnalysisResult
    ) -> list[ActionRecommendation]:
        """Generate recommendations based on trend analysis.

        Args:
            forecast: Forecast result.
            analysis: Analysis result.

        Returns:
            List of trend-based recommendations.
        """
        recommendations: list[ActionRecommendation] = []

        if analysis.trend == "decreasing":
            recommendations.append(
                ActionRecommendation(
                    id=str(uuid.uuid4()),
                    priority=1,
                    category="revenue",
                    title="Address declining sales trend",
                    description=(
                        "Sales trend is decreasing. Consider increasing marketing"
                        " spend, reviewing pricing strategy, or launching promotional"
                        " campaigns to reverse the decline."
                    ),
                    expected_impact=0.15,
                    confidence=0.85,
                    due_date=datetime.now() + timedelta(days=14),
                )
            )
        elif analysis.trend == "increasing":
            recommendations.append(
                ActionRecommendation(
                    id=str(uuid.uuid4()),
                    priority=2,
                    category="capacity",
                    title="Prepare for growth",
                    description=(
                        "Sales trend is increasing. Ensure inventory, staffing, and"
                        " operational capacity can handle the growth trajectory."
                    ),
                    expected_impact=0.10,
                    confidence=0.75,
                    due_date=datetime.now() + timedelta(days=30),
                )
            )

        return recommendations

    def _recommendations_from_anomalies(
        self, forecast: ForecastResult, analysis: AnalysisResult
    ) -> list[ActionRecommendation]:
        """Generate recommendations based on detected anomalies.

        Args:
            forecast: Forecast result.
            analysis: Analysis result.

        Returns:
            List of anomaly-based recommendations.
        """
        recommendations: list[ActionRecommendation] = []

        if analysis.anomalies:
            high_value_anomalies = [
                a for a in analysis.anomalies if a["z_score"] > 0
            ]
            if high_value_anomalies:
                recommendations.append(
                    ActionRecommendation(
                        id=str(uuid.uuid4()),
                        priority=2,
                        category="investigation",
                        title="Investigate high-value anomalies",
                        description=(
                            f"Found {len(high_value_anomalies)} periods with"
                            " unusually high sales. Investigate root causes to"
                            " identify replicable success factors."
                        ),
                        expected_impact=0.08,
                        confidence=0.70,
                        due_date=datetime.now() + timedelta(days=7),
                    )
                )

        return recommendations

    def _recommendations_from_seasonality(
        self, forecast: ForecastResult, analysis: AnalysisResult
    ) -> list[ActionRecommendation]:
        """Generate recommendations based on seasonality.

        Args:
            forecast: Forecast result.
            analysis: Analysis result.

        Returns:
            List of seasonality-based recommendations.
        """
        return [
            ActionRecommendation(
                id=str(uuid.uuid4()),
                priority=3,
                category="planning",
                title="Optimize for seasonal patterns",
                description=(
                    "Seasonal patterns detected. Adjust inventory, staffing, and"
                    " marketing spend to align with seasonal demand fluctuations."
                ),
                expected_impact=0.12,
                confidence=0.80,
                due_date=datetime.now() + timedelta(days=21),
            )
        ]

    def _recommendations_from_forecast(
        self,
        forecast: ForecastResult,
        context: dict[str, Any] | None,
    ) -> list[ActionRecommendation]:
        """Generate recommendations based on forecast values.

        Args:
            forecast: Forecast result.
            context: Additional context.

        Returns:
            List of forecast-based recommendations.
        """
        recommendations: list[ActionRecommendation] = []

        if not forecast.points:
            return recommendations

        # Check if forecast shows significant change
        first_quarter = forecast.points[: len(forecast.points) // 4]
        last_quarter = forecast.points[-(len(forecast.points) // 4) :]

        if first_quarter and last_quarter:
            first_avg = sum(p.value for p in first_quarter) / len(first_quarter)
            last_avg = sum(p.value for p in last_quarter) / len(last_quarter)

            if first_avg > 0 and (last_avg - first_avg) / first_avg > 0.2:
                recommendations.append(
                    ActionRecommendation(
                        id=str(uuid.uuid4()),
                        priority=1,
                        category="strategy",
                        title="Capitalize on forecasted growth",
                        description=(
                            "Forecast indicates significant growth ahead. Consider"
                            " expanding sales team, increasing inventory, or entering"
                            " new markets."
                        ),
                        expected_impact=0.20,
                        confidence=0.75,
                        due_date=datetime.now() + timedelta(days=14),
                    )
                )
            elif first_avg > 0 and (last_avg - first_avg) / first_avg < -0.2:
                recommendations.append(
                    ActionRecommendation(
                        id=str(uuid.uuid4()),
                        priority=1,
                        category="strategy",
                        title="Mitigate forecasted decline",
                        description=(
                            "Forecast indicates a significant decline. Review pipeline,"
                            " increase prospecting activities, and consider"
                            " promotional strategies."
                        ),
                        expected_impact=0.18,
                        confidence=0.72,
                        due_date=datetime.now() + timedelta(days=10),
                    )
                )

        return recommendations
