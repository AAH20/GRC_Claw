"""Moderation Predictor Agent implementation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate

from moderation_analytics.agents import BaseAgent
from moderation_analytics.models import ModerationPrediction


class ModerationPredictorAgent(BaseAgent[list[ModerationPrediction]]):
    """Agent that predicts future moderation metrics.

    Uses historical data and statistical methods to forecast
    workload, risk levels, and trend directions.
    """

    def __init__(self, llm: BaseLanguageModel | None = None) -> None:
        """Initialize the Moderation Predictor Agent.

        Args:
            llm: Optional pre-configured language model.
        """
        super().__init__(name="ModerationPredictor", llm=llm)
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert in predictive analytics for content moderation. "
                    "Use historical data to make accurate predictions about future "
                    "moderation workload and risk levels.",
                ),
                (
                    "human",
                    "Based on the following historical data, predict future moderation "
                    "metrics for {target_date}:\n\n{historical_data}",
                ),
            ]
        )

    async def run(
        self,
        historical_data: list[dict[str, Any]],
        target_date: datetime | None = None,
        prediction_types: list[str] | None = None,
        **kwargs: Any,
    ) -> list[ModerationPrediction]:
        """Generate predictions for future moderation metrics.

        Args:
            historical_data: Historical moderation data for prediction.
            target_date: Date to predict for. Defaults to 7 days from now.
            prediction_types: Types of predictions to generate. Defaults to all.
            **kwargs: Additional parameters.

        Returns:
            list[ModerationPrediction]: Generated predictions.

        Raises:
            ValueError: If historical_data is empty.
        """
        self._log_start(data_points=len(historical_data))

        if not historical_data:
            raise ValueError("Cannot predict with empty historical data")

        target = target_date or (datetime.utcnow() + timedelta(days=7))
        types = prediction_types or ["workload", "risk", "trend"]

        predictions: list[ModerationPrediction] = []

        if "workload" in types:
            predictions.append(self._predict_workload(historical_data, target))
        if "risk" in types:
            predictions.append(self._predict_risk(historical_data, target))
        if "trend" in types:
            predictions.append(self._predict_trend(historical_data, target))

        # Use LLM for enhanced predictions
        if self._settings.openai_api_key:
            try:
                await self._enhance_with_llm(predictions, historical_data, target)
            except Exception as e:
                self._log_error(e, fallback="using statistical predictions only")

        self._log_complete(predictions)
        return predictions

    def _predict_workload(
        self, data: list[dict[str, Any]], target: datetime
    ) -> ModerationPrediction:
        """Predict future moderation workload.

        Args:
            data: Historical data.
            target: Target prediction date.

        Returns:
            ModerationPrediction: Workload prediction.
        """
        volumes = [d.get("count", 0) for d in data]
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        # Simple linear projection
        predicted = avg_volume * 1.05  # 5% growth assumption
        margin = predicted * 0.15

        return ModerationPrediction(
            prediction_type="workload",
            target_date=target,
            predicted_value=round(predicted, 2),
            confidence_interval=(round(predicted - margin, 2), round(predicted + margin, 2)),
            confidence=0.75,
            factors=["historical average", "growth trend"],
        )

    def _predict_risk(self, data: list[dict[str, Any]], target: datetime) -> ModerationPrediction:
        """Predict future risk levels.

        Args:
            data: Historical data.
            target: Target prediction date.

        Returns:
            ModerationPrediction: Risk prediction.
        """
        severities = [d.get("avg_severity", 0.0) for d in data]
        avg_severity = sum(severities) / len(severities) if severities else 0.0

        return ModerationPrediction(
            prediction_type="risk",
            target_date=target,
            predicted_value=round(avg_severity, 4),
            confidence_interval=(round(avg_severity * 0.8, 4), round(avg_severity * 1.2, 4)),
            confidence=0.70,
            factors=["severity trend", "historical patterns"],
        )

    def _predict_trend(self, data: list[dict[str, Any]], target: datetime) -> ModerationPrediction:
        """Predict trend direction.

        Args:
            data: Historical data.
            target: Target prediction date.

        Returns:
            ModerationPrediction: Trend prediction.
        """
        if len(data) < 2:
            return ModerationPrediction(
                prediction_type="trend",
                target_date=target,
                predicted_value=0.0,
                confidence_interval=(0.0, 0.0),
                confidence=0.5,
                factors=["insufficient data"],
            )

        first_half = data[: len(data) // 2]
        second_half = data[len(data) // 2 :]
        first_avg = sum(d.get("count", 0) for d in first_half) / len(first_half)
        second_avg = sum(d.get("count", 0) for d in second_half) / len(second_half)
        trend_value = (second_avg - first_avg) / max(first_avg, 1)

        return ModerationPrediction(
            prediction_type="trend",
            target_date=target,
            predicted_value=round(trend_value, 4),
            confidence_interval=(round(trend_value * 0.5, 4), round(trend_value * 1.5, 4)),
            confidence=0.65,
            factors=["comparative analysis"],
        )

    async def _enhance_with_llm(
        self,
        predictions: list[ModerationPrediction],
        historical_data: list[dict[str, Any]],
        target: datetime,
    ) -> None:
        """Enhance predictions with LLM analysis.

        Args:
            predictions: Predictions to enhance in-place.
            historical_data: Historical data for context.
            target: Target prediction date.
        """
        # In production, use structured output to parse LLM response
        pass
