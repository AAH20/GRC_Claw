"""Tests for Sales Forecaster agents."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from sales_forecaster.agents.action import ActionAgent, ActionRecommendation
from sales_forecaster.agents.analysis import AnalysisAgent, AnalysisResult
from sales_forecaster.agents.data_collection import (
    DataCollectionAgent,
    DataSource,
    SalesRecord,
)
from sales_forecaster.agents.performance_analytics import (
    PerformanceAnalyticsAgent,
    PerformanceMetrics,
)
from sales_forecaster.agents.prediction import PredictionAgent, ForecastResult
from sales_forecaster.core.models import ForecastPeriod, ForecastPoint


@pytest.fixture
def sample_sales_data() -> list[SalesRecord]:
    base = datetime(2024, 1, 1)
    return [
        SalesRecord(
            id=f"s{i}",
            date=base + timedelta(days=i),
            amount=1000 + i * 100,
            product_id="p1",
            region="us-east",
        )
        for i in range(30)
    ]


class TestPredictionAgent:
    """Tests for PredictionAgent."""

    @pytest.fixture
    def agent(self) -> PredictionAgent:
        return PredictionAgent()

    @pytest.fixture
    def sample_records(self) -> list[SalesRecord]:
        base = datetime(2024, 1, 1)
        return [
            SalesRecord(
                id=f"s{i}",
                date=base + timedelta(days=i),
                amount=1000 + i * 50,
                product_id="p1",
                region="us-east",
            )
            for i in range(60)
        ]

    def test_generate_forecast(self, agent: PredictionAgent, sample_records: list[SalesRecord]) -> None:
        result = agent.generate_forecast(sample_records, horizon_days=14)
        assert isinstance(result, ForecastResult)
        assert result.forecast_horizon_days == 14
        assert len(result.points) == 14

    def test_generate_forecast_empty_data(self, agent: PredictionAgent) -> None:
        with pytest.raises(ValueError):
            agent.generate_forecast([], horizon_days=14)

    def test_calculate_accuracy(self, agent: PredictionAgent, sample_records: list[SalesRecord]) -> None:
        forecast = agent.generate_forecast(sample_records, horizon_days=7)
        accuracy = agent.calculate_accuracy(sample_records, forecast)
        assert isinstance(accuracy, float)
        assert 0 <= accuracy <= 1.0


class TestAnalysisAgent:
    """Tests for AnalysisAgent."""

    @pytest.fixture
    def agent(self) -> AnalysisAgent:
        return AnalysisAgent()

    @pytest.fixture
    def sample_records(self) -> list[SalesRecord]:
        base = datetime(2024, 1, 1)
        return [
            SalesRecord(
                id=f"s{i}",
                date=base + timedelta(days=i),
                amount=1000 + i * 100,
                product_id="p1",
                region="us-east",
            )
            for i in range(30)
        ]

    def test_analyze_trends(self, agent: AnalysisAgent, sample_records: list[SalesRecord]) -> None:
        result = agent.analyze_trends(sample_records)
        assert isinstance(result, AnalysisResult)

    def test_detect_seasonality(self, agent: AnalysisAgent, sample_records: list[SalesRecord]) -> None:
        result = agent.detect_seasonality(sample_records)
        assert isinstance(result, dict)

    def test_detect_anomalies(self, agent: AnalysisAgent, sample_records: list[SalesRecord]) -> None:
        anomalies = agent.detect_anomalies(sample_records)
        assert isinstance(anomalies, list)


class TestDataCollectionAgent:
    """Tests for DataCollectionAgent."""

    @pytest.fixture
    def agent(self) -> DataCollectionAgent:
        return DataCollectionAgent()

    def test_init(self, agent: DataCollectionAgent) -> None:
        assert agent is not None

    @pytest.mark.asyncio
    async def test_collect_from_source(self, agent: DataCollectionAgent) -> None:
        records = await agent.collect_from_source(
            DataSource.SALESFORCE,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )
        assert isinstance(records, list)


class TestActionAgent:
    """Tests for ActionAgent."""

    @pytest.fixture
    def agent(self) -> ActionAgent:
        return ActionAgent()

    def test_generate_actions(self, agent: ActionAgent) -> None:
        forecast = ForecastResult(
            model_type="test",
            forecast_horizon_days=7,
            points=[
                ForecastPoint(
                    date=datetime(2024, 2, 1),
                    predicted_value=1000,
                    lower_bound=900,
                    upper_bound=1100,
                ),
            ],
            metrics={"mae": 50.0},
            created_at=datetime(2024, 1, 1),
        )
        actions = agent.generate_actions(forecast)
        assert isinstance(actions, list)


class TestPerformanceAnalyticsAgent:
    """Tests for PerformanceAnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> PerformanceAnalyticsAgent:
        return PerformanceAnalyticsAgent()

    def test_calculate_kpis(self, agent: PerformanceAnalyticsAgent) -> None:
        records = [
            SalesRecord(
                id=f"s{i}",
                date=datetime(2024, 1, 1) + timedelta(days=i),
                amount=1000 + i * 100,
                product_id="p1",
                region="us-east",
            )
            for i in range(30)
        ]
        kpis = agent.calculate_kpis(records)
        assert isinstance(kpis, PerformanceMetrics)

    def test_compare_periods(self, agent: PerformanceAnalyticsAgent) -> None:
        current = [
            SalesRecord(
                id=f"s{i}",
                date=datetime(2024, 1, 1) + timedelta(days=i),
                amount=1000,
                product_id="p1",
                region="us-east",
            )
            for i in range(30)
        ]
        previous = [
            SalesRecord(
                id=f"s{i}",
                date=datetime(2023, 1, 1) + timedelta(days=i),
                amount=900,
                product_id="p1",
                region="us-east",
            )
            for i in range(30)
        ]
        comparison = agent.compare_periods(current, previous)
        assert isinstance(comparison, dict)
