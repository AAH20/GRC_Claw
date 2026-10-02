"""Tests for predictive analytics agent."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from attribution.agents.data_collection import DataSource, RawDataPoint
from attribution.agents.predictive_analytics import (
    PredictiveAnalyticsAgent,
)


def _generate_data_points(n: int = 30) -> list[RawDataPoint]:
    """Generate sample data points for testing."""
    now = datetime.now(tz=timezone.utc)
    return [
        RawDataPoint(
            source=DataSource.GOOGLE_ADS,
            timestamp=now - timedelta(days=n - i),
            campaign_id=f"camp_{i % 3}",
            campaign_name=f"Campaign {i % 3}",
            spend=100.0 + i * 10,
            impressions=1000 + i * 100,
            clicks=50 + i * 5,
            conversions=5.0 + i * 0.5,
            revenue=500.0 + i * 50,
        )
        for i in range(n)
    ]


class TestPredictiveAnalyticsAgent:
    """Tests for PredictiveAnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> PredictiveAnalyticsAgent:
        return PredictiveAnalyticsAgent(forecast_horizon_days=7)

    @pytest.fixture
    def data_points(self) -> list[RawDataPoint]:
        return _generate_data_points(30)

    def test_train(self, agent: PredictiveAnalyticsAgent, data_points: list[RawDataPoint]) -> None:
        metrics = agent.train(data_points, target_metric="conversions")
        assert metrics.model_name == "GradientBoostingRegressor"
        assert metrics.mae >= 0
        assert metrics.rmse >= 0

    def test_train_insufficient_data(self, agent: PredictiveAnalyticsAgent) -> None:
        with pytest.raises(ValueError, match="At least 14 data points required"):
            agent.train(_generate_data_points(5))

    def test_forecast(self, agent: PredictiveAnalyticsAgent, data_points: list[RawDataPoint]) -> None:
        result = agent.forecast(data_points, target_metric="conversions")
        assert result.metric_name == "conversions"
        assert len(result.forecast_values) == 7
        assert len(result.confidence_intervals) == 7
        assert len(result.dates) == 7

    def test_detect_anomalies(self, agent: PredictiveAnalyticsAgent, data_points: list[RawDataPoint]) -> None:
        anomalies = agent.detect_anomalies(data_points)
        assert isinstance(anomalies, list)

    def test_detect_anomalies_insufficient_data(self, agent: PredictiveAnalyticsAgent) -> None:
        anomalies = agent.detect_anomalies(_generate_data_points(3))
        assert len(anomalies) == 0
