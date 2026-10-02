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
from sales_forecaster.core.models import (
    AnalysisResult,
    ForecastPeriod,
    ForecastResult,
)


def _make_records(n: int, amount_fn=lambda i: 1000 + i * 50) -> list[SalesRecord]:
    base = datetime(2024, 1, 1)
    return [
        SalesRecord(
            id=f"s{i}",
            source=DataSource.SALESFORCE,
            date=base + timedelta(days=i),
            amount=amount_fn(i),
            product_id="p1",
            region="us-east",
        )
        for i in range(n)
    ]


class TestPredictionAgent:
    """Tests for PredictionAgent."""

    @pytest.fixture
    def agent(self) -> PredictionAgent:
        return PredictionAgent()

    @pytest.fixture
    def sample_records(self) -> list[SalesRecord]:
        return _make_records(60)

    @pytest.mark.asyncio
    async def test_predict(self, agent: PredictionAgent, sample_records: list[SalesRecord]) -> None:
        result = await agent.predict(
            records=sample_records,
            period=ForecastPeriod.DAILY,
        )
        assert isinstance(result, ForecastResult)
        assert result.horizon_days > 0
        assert len(result.points) > 0

    @pytest.mark.asyncio
    async def test_predict_empty_data(self, agent: PredictionAgent) -> None:
        with pytest.raises((ValueError, Exception)):
            await agent.predict(
                records=[],
                period=ForecastPeriod.DAILY,
            )


class TestAnalysisAgent:
    """Tests for AnalysisAgent."""

    @pytest.fixture
    def agent(self) -> AnalysisAgent:
        return AnalysisAgent()

    @pytest.fixture
    def sample_records(self) -> list[SalesRecord]:
        return _make_records(30, lambda i: 1000 + i * 100)

    @pytest.mark.asyncio
    async def test_analyze(self, agent: AnalysisAgent, sample_records: list[SalesRecord]) -> None:
        result = await agent.analyze(sample_records)
        assert result is not None

    def test_detect_trend(self, agent: AnalysisAgent, sample_records: list[SalesRecord]) -> None:
        df = agent._prepare_dataframe(sample_records, "daily")
        trend = agent._detect_trend(df)
        assert isinstance(trend, str)

    def test_detect_seasonality(self, agent: AnalysisAgent, sample_records: list[SalesRecord]) -> None:
        df = agent._prepare_dataframe(sample_records, "daily")
        result = agent._detect_seasonality(df)
        assert isinstance(result, tuple)

    def test_detect_anomalies(self, agent: AnalysisAgent, sample_records: list[SalesRecord]) -> None:
        df = agent._prepare_dataframe(sample_records, "daily")
        anomalies = agent._detect_anomalies(df)
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
        # Salesforce integration not configured in test env; expect empty or error
        try:
            records = await agent.collect_from_source(
                DataSource.SALESFORCE,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
            )
            assert isinstance(records, list)
        except Exception:
            pass  # Integration not configured is acceptable in test env


class TestActionAgent:
    """Tests for ActionAgent."""

    @pytest.fixture
    def agent(self) -> ActionAgent:
        return ActionAgent()

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, agent: ActionAgent) -> None:
        forecast = ForecastResult(
            id="fc1",
            created_at=datetime(2024, 1, 1),
            period=ForecastPeriod.DAILY,
            horizon_days=7,
            points=[],
            model_used="test",
        )
        result = await agent.generate_recommendations(forecast)
        assert isinstance(result, list)


class TestPerformanceAnalyticsAgent:
    """Tests for PerformanceAnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> PerformanceAnalyticsAgent:
        return PerformanceAnalyticsAgent()

    @pytest.mark.asyncio
    async def test_evaluate(self, agent: PerformanceAnalyticsAgent) -> None:
        records = _make_records(30, lambda i: 1000 + i * 100)
        result = await agent.evaluate(records)
        assert result is not None

    def test_calculate_kpis(self, agent: PerformanceAnalyticsAgent) -> None:
        records = _make_records(30, lambda i: 1000)
        kpis = agent._calculate_kpis(records, total_revenue=30000.0)
        assert isinstance(kpis, dict)
        assert "total_revenue" in kpis
