"""Tests for Sales Forecaster agents."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from sales_forecaster.agents.action import ActionAgent
from sales_forecaster.agents.analysis import AnalysisAgent
from sales_forecaster.agents.data_collection import (
    DataCollectionAgent,
    DataSource,
    SalesRecord,
)
from sales_forecaster.agents.performance_analytics import PerformanceAnalyticsAgent
from sales_forecaster.agents.prediction import PredictionAgent
from sales_forecaster.core.models import ForecastPeriod, ForecastResult


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

    @pytest.mark.asyncio
    async def test_predict(self, agent: PredictionAgent, sample_records: list[SalesRecord]) -> None:
        result = await agent.predict(
            records=sample_records,
            horizon_days=14,
            period=ForecastPeriod.DAILY,
        )
        assert isinstance(result, ForecastResult)
        assert result.forecast_horizon_days == 14
        assert len(result.points) == 14

    @pytest.mark.asyncio
    async def test_predict_empty_data(self, agent: PredictionAgent) -> None:
        with pytest.raises((ValueError, Exception)):
            await agent.predict(
                records=[],
                horizon_days=14,
                period=ForecastPeriod.DAILY,
            )


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

    @pytest.mark.asyncio
    async def test_analyze(self, agent: AnalysisAgent, sample_records: list[SalesRecord]) -> None:
        result = await agent.analyze(sample_records)
        assert result is not None

    def test_detect_trend(self, agent: AnalysisAgent, sample_records: list[SalesRecord]) -> None:
        trend = agent._detect_trend(agent._prepare_dataframe(sample_records))
        assert isinstance(trend, str)

    def test_detect_seasonality(self, agent: AnalysisAgent, sample_records: list[SalesRecord]) -> None:
        result = agent._detect_seasonality(agent._prepare_dataframe(sample_records))
        assert isinstance(result, dict)

    def test_detect_anomalies(self, agent: AnalysisAgent, sample_records: list[SalesRecord]) -> None:
        anomalies = agent._detect_anomalies(agent._prepare_dataframe(sample_records))
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

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, agent: ActionAgent) -> None:
        forecast = ForecastResult(
            model_type="test",
            forecast_horizon_days=7,
            points=[],
            metrics={"mae": 50.0},
            created_at=datetime(2024, 1, 1),
        )
        analysis = agent._recommendations_from_forecast(forecast)
        assert isinstance(analysis, list)


class TestPerformanceAnalyticsAgent:
    """Tests for PerformanceAnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> PerformanceAnalyticsAgent:
        return PerformanceAnalyticsAgent()

    @pytest.mark.asyncio
    async def test_evaluate(self, agent: PerformanceAnalyticsAgent) -> None:
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
        result = await agent.evaluate(records)
        assert result is not None

    def test_calculate_kpis(self, agent: PerformanceAnalyticsAgent) -> None:
        records = [
            SalesRecord(
                id=f"s{i}",
                date=datetime(2024, 1, 1) + timedelta(days=i),
                amount=1000,
                product_id="p1",
                region="us-east",
            )
            for i in range(30)
        ]
        kpis = agent._calculate_kpis(records)
        assert isinstance(kpis, dict)
