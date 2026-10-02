"""Tests for Analytics & Attribution agents."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from analytics.agents.attribution_engine import (
    AttributionEngine,
    AttributionModel,
    AttributionResult,
    CustomerJourney,
    Touchpoint,
)
from analytics.agents.data_collection import (
    AmplitudeCollector,
    CollectionResult,
    DataSource,
    GoogleAnalyticsCollector,
    MixpanelCollector,
    RawEvent,
)
from analytics.agents.predictive_analytics import (
    ChurnPrediction,
    ChurnPredictionResult,
    ForecastPoint,
    ForecastResult,
    ModelType,
    PredictiveAnalyticsAgent,
)
from analytics.agents.realtime_dashboards import (
    ConnectionManager,
    DashboardSnapshot,
    MetricType,
    MetricValue,
    RealtimeDashboardsAgent,
)
from analytics.agents.reporting import (
    Report,
    ReportFormat,
    ReportType,
    ReportingAgent,
)


class TestAttributionEngine:
    """Tests for AttributionEngine."""

    @pytest.fixture
    def engine(self) -> AttributionEngine:
        return AttributionEngine()

    @pytest.fixture
    def sample_events(self) -> list[RawEvent]:
        base = datetime(2024, 1, 15, 10, 0, 0)
        return [
            RawEvent(
                event_id="e1",
                source=DataSource.GOOGLE_ANALYTICS,
                event_type="page_view",
                timestamp=base,
                user_id="u1",
                channel="organic",
            ),
            RawEvent(
                event_id="e2",
                source=DataSource.GOOGLE_ANALYTICS,
                event_type="click",
                timestamp=base + timedelta(hours=2),
                user_id="u1",
                channel="paid_search",
                campaign_id="cmp1",
            ),
            RawEvent(
                event_id="e3",
                source=DataSource.GOOGLE_ANALYTICS,
                event_type="purchase",
                timestamp=base + timedelta(hours=5),
                user_id="u1",
                channel="paid_search",
                revenue=150.0,
            ),
        ]

    def test_build_journeys(self, engine: AttributionEngine, sample_events: list[RawEvent]) -> None:
        journeys = engine.build_journeys(sample_events)
        assert len(journeys) == 1
        assert journeys[0].user_id == "u1"
        assert len(journeys[0].touchpoints) == 3
        assert journeys[0].converted is True
        assert journeys[0].conversion_value == 150.0

    def test_build_journeys_multiple_users(self, engine: AttributionEngine) -> None:
        base = datetime(2024, 1, 15)
        events = [
            RawEvent(
                event_id="e1",
                source=DataSource.GOOGLE_ANALYTICS,
                event_type="view",
                timestamp=base,
                user_id="u1",
                channel="email",
            ),
            RawEvent(
                event_id="e2",
                source=DataSource.GOOGLE_ANALYTICS,
                event_type="view",
                timestamp=base,
                user_id="u2",
                channel="social",
            ),
        ]
        journeys = engine.build_journeys(events)
        assert len(journeys) == 2

    def test_first_touch_attribution(self, engine: AttributionEngine) -> None:
        journey = CustomerJourney(
            user_id="u1",
            touchpoints=[
                Touchpoint("e1", "email", None, datetime(2024, 1, 1)),
                Touchpoint("e2", "paid_search", None, datetime(2024, 1, 2)),
                Touchpoint("e3", "social", None, datetime(2024, 1, 3)),
            ],
            conversion_value=100.0,
            converted=True,
        )
        results = engine.run_attribution([journey], AttributionModel.FIRST_TOUCH)
        assert len(results) == 1
        assert results[0].channel_attributions == {"email": 100.0}

    def test_last_touch_attribution(self, engine: AttributionEngine) -> None:
        journey = CustomerJourney(
            user_id="u1",
            touchpoints=[
                Touchpoint("e1", "email", None, datetime(2024, 1, 1)),
                Touchpoint("e2", "paid_search", None, datetime(2024, 1, 2)),
                Touchpoint("e3", "social", None, datetime(2024, 1, 3)),
            ],
            conversion_value=100.0,
            converted=True,
        )
        results = engine.run_attribution([journey], AttributionModel.LAST_TOUCH)
        assert len(results) == 1
        assert results[0].channel_attributions == {"social": 100.0}

    def test_linear_attribution(self, engine: AttributionEngine) -> None:
        journey = CustomerJourney(
            user_id="u1",
            touchpoints=[
                Touchpoint("e1", "email", None, datetime(2024, 1, 1)),
                Touchpoint("e2", "paid_search", None, datetime(2024, 1, 2)),
                Touchpoint("e3", "social", None, datetime(2024, 1, 3)),
            ],
            conversion_value=90.0,
            converted=True,
        )
        results = engine.run_attribution([journey], AttributionModel.LINEAR)
        assert len(results) == 1
        assert results[0].channel_attributions["email"] == pytest.approx(30.0)
        assert results[0].channel_attributions["paid_search"] == pytest.approx(30.0)
        assert results[0].channel_attributions["social"] == pytest.approx(30.0)

    def test_time_decay_attribution(self, engine: AttributionEngine) -> None:
        journey = CustomerJourney(
            user_id="u1",
            touchpoints=[
                Touchpoint("e1", "email", None, datetime(2024, 1, 1)),
                Touchpoint("e2", "paid_search", None, datetime(2024, 1, 3)),
            ],
            conversion_value=100.0,
            converted=True,
        )
        results = engine.run_attribution([journey], AttributionModel.TIME_DECAY)
        assert len(results) == 1
        # Later touchpoint should get more credit
        assert results[0].channel_attributions["paid_search"] > results[0].channel_attributions["email"]

    def test_data_driven_attribution(self, engine: AttributionEngine) -> None:
        journey = CustomerJourney(
            user_id="u1",
            touchpoints=[
                Touchpoint("e1", "email", None, datetime(2024, 1, 1)),
                Touchpoint("e2", "paid_search", None, datetime(2024, 1, 2)),
            ],
            conversion_value=100.0,
            converted=True,
        )
        results = engine.run_attribution([journey], AttributionModel.DATA_DRIVEN)
        assert len(results) == 1
        assert sum(results[0].channel_attributions.values()) == pytest.approx(100.0)

    def test_aggregate_results(self, engine: AttributionEngine) -> None:
        results = [
            AttributionResult(
                user_id="u1",
                model=AttributionModel.LINEAR,
                channel_attributions={"email": 50.0, "social": 50.0},
                total_revenue=100.0,
            ),
            AttributionResult(
                user_id="u2",
                model=AttributionModel.LINEAR,
                channel_attributions={"email": 30.0, "paid_search": 70.0},
                total_revenue=100.0,
            ),
        ]
        agg = engine.aggregate_results(results)
        assert agg.total_revenue == 200.0
        assert agg.journey_count == 2
        assert agg.converted_journeys == 2
        assert agg.channel_totals["email"] == 80.0
        assert agg.channel_totals["social"] == 50.0
        assert agg.channel_totals["paid_search"] == 70.0

    def test_compare_models(self, engine: AttributionEngine) -> None:
        journey = CustomerJourney(
            user_id="u1",
            touchpoints=[
                Touchpoint("e1", "email", None, datetime(2024, 1, 1)),
                Touchpoint("e2", "paid_search", None, datetime(2024, 1, 2)),
            ],
            conversion_value=100.0,
            converted=True,
        )
        comparison = engine.compare_models([journey])
        assert len(comparison) == len(AttributionModel)
        for model in AttributionModel:
            assert model.value in comparison


class TestDataCollection:
    """Tests for data collection agents."""

    @pytest.fixture
    def ga_collector(self) -> GoogleAnalyticsCollector:
        return GoogleAnalyticsCollector(property_id="12345", credentials_path="/tmp/creds.json")

    @pytest.fixture
    def mixpanel_collector(self) -> MixpanelCollector:
        return MixpanelCollector(project_id="proj1", api_secret="secret")

    @pytest.fixture
    def amplitude_collector(self) -> AmplitudeCollector:
        return AmplitudeCollector(api_key="key123")

    def test_ga_collector_init(self, ga_collector: GoogleAnalyticsCollector) -> None:
        assert ga_collector.source == DataSource.GOOGLE_ANALYTICS
        assert ga_collector.property_id == "12345"

    def test_mixpanel_collector_init(self, mixpanel_collector: MixpanelCollector) -> None:
        assert mixpanel_collector.source == DataSource.MIXPANEL
        assert mixpanel_collector.project_id == "proj1"

    def test_amplitude_collector_init(self, amplitude_collector: AmplitudeCollector) -> None:
        assert amplitude_collector.source == DataSource.AMPLITUDE
        assert amplitude_collector.api_key == "key123"

    @pytest.mark.asyncio
    async def test_ga_health_check_failure(self, ga_collector: GoogleAnalyticsCollector) -> None:
        result = await ga_collector.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_mixpanel_health_check_failure(
        self, mixpanel_collector: MixpanelCollector
    ) -> None:
        result = await mixpanel_collector.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_amplitude_health_check_failure(
        self, amplitude_collector: AmplitudeCollector
    ) -> None:
        result = await amplitude_collector.health_check()
        assert result is False


class TestPredictiveAnalytics:
    """Tests for PredictiveAnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> PredictiveAnalyticsAgent:
        return PredictiveAnalyticsAgent()

    @pytest.fixture
    def historical_data(self) -> list[dict]:
        return [
            {"date": f"2024-01-{i+1:02d}", "revenue": 1000 + i * 50}
            for i in range(30)
        ]

    def test_forecast_revenue(self, agent: PredictiveAnalyticsAgent, historical_data: list[dict]) -> None:
        result = agent.forecast_revenue(historical_data, horizon_days=7)
        assert isinstance(result, ForecastResult)
        assert result.forecast_horizon_days == 7
        assert len(result.points) == 7
        assert result.model_type == ModelType.GRADIENT_BOOSTING

    def test_forecast_revenue_empty_data(self, agent: PredictiveAnalyticsAgent) -> None:
        with pytest.raises(ValueError, match="Historical data cannot be empty"):
            agent.forecast_revenue([], horizon_days=7)

    def test_predict_churn(self, agent: PredictiveAnalyticsAgent) -> None:
        user_features = [
            {
                "user_id": "u1",
                "days_since_last_active": 5,
                "total_sessions": 50,
                "avg_session_duration": 120,
                "total_revenue": 500,
                "support_tickets": 1,
                "email_open_rate": 0.3,
            },
            {
                "user_id": "u2",
                "days_since_last_active": 60,
                "total_sessions": 5,
                "avg_session_duration": 30,
                "total_revenue": 50,
                "support_tickets": 5,
                "email_open_rate": 0.05,
            },
        ]
        result = agent.predict_churn(user_features)
        assert isinstance(result, ChurnPredictionResult)
        assert len(result.predictions) == 2
        assert all(0 <= p.churn_probability <= 1 for p in result.predictions)

    def test_predict_churn_empty_features(self, agent: PredictiveAnalyticsAgent) -> None:
        with pytest.raises(ValueError, match="User features cannot be empty"):
            agent.predict_churn([])


class TestRealtimeDashboards:
    """Tests for RealtimeDashboardsAgent."""

    @pytest.fixture
    def agent(self) -> RealtimeDashboardsAgent:
        return RealtimeDashboardsAgent(refresh_interval_seconds=1.0)

    @pytest.fixture
    def connection_manager(self) -> ConnectionManager:
        return ConnectionManager()

    def test_connection_manager_init(self, connection_manager: ConnectionManager) -> None:
        assert connection_manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, connection_manager: ConnectionManager) -> None:
        class FakeWebSocket:
            def __init__(self) -> None:
                self.sent: list = []

            async def send_json(self, data: dict) -> None:
                self.sent.append(data)

        ws = FakeWebSocket()
        await connection_manager.connect(ws)
        assert connection_manager.connection_count == 1

        await connection_manager.disconnect(ws)
        assert connection_manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_broadcast(self, connection_manager: ConnectionManager) -> None:
        class FakeWebSocket:
            def __init__(self) -> None:
                self.sent: list = []

            async def send_json(self, data: dict) -> None:
                self.sent.append(data)

        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        await connection_manager.connect(ws1)
        await connection_manager.connect(ws2)

        await connection_manager.broadcast({"type": "test"})
        assert len(ws1.sent) == 1
        assert len(ws2.sent) == 1

    def test_get_current_snapshot(self, agent: RealtimeDashboardsAgent) -> None:
        snapshot = agent.get_current_snapshot()
        assert isinstance(snapshot, DashboardSnapshot)
        assert isinstance(snapshot.timestamp, datetime)

    def test_get_historical_metrics(self, agent: RealtimeDashboardsAgent) -> None:
        metrics = agent.get_historical_metrics()
        assert isinstance(metrics, list)


class TestReportingAgent:
    """Tests for ReportingAgent."""

    @pytest.fixture
    def agent(self) -> ReportingAgent:
        return ReportingAgent()

    @pytest.fixture
    def collection_results(self) -> list[CollectionResult]:
        return [
            CollectionResult(
                source=DataSource.GOOGLE_ANALYTICS,
                events=[
                    RawEvent(
                        event_id="e1",
                        source=DataSource.GOOGLE_ANALYTICS,
                        event_type="purchase",
                        timestamp=datetime(2024, 1, 15),
                        user_id="u1",
                        revenue=100.0,
                    ),
                ],
                collected_at=datetime(2024, 1, 15),
                total_count=1,
                success=True,
            ),
        ]

    def test_generate_performance_report(
        self, agent: ReportingAgent, collection_results: list[CollectionResult]
    ) -> None:
        report = agent.generate_performance_report(
            collection_results,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
        )
        assert isinstance(report, Report)
        assert report.report_type == ReportType.PERFORMANCE
        assert len(report.sections) >= 1

    def test_export_json(self, agent: ReportingAgent, collection_results: list[CollectionResult]) -> None:
        report = agent.generate_performance_report(
            collection_results,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
        )
        json_output = agent.export_report(report)
        assert isinstance(json_output, str)
        assert "report_id" in json_output

    def test_export_csv(self, agent: ReportingAgent, collection_results: list[CollectionResult]) -> None:
        report = agent.generate_performance_report(
            collection_results,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            format=ReportFormat.CSV,
        )
        csv_output = agent.export_report(report)
        assert isinstance(csv_output, str)
        assert "Report ID" in csv_output

    def test_get_report(self, agent: ReportingAgent, collection_results: list[CollectionResult]) -> None:
        report = agent.generate_performance_report(
            collection_results,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
        )
        retrieved = agent.get_report(report.report_id)
        assert retrieved is not None
        assert retrieved.report_id == report.report_id

    def test_list_reports(self, agent: ReportingAgent, collection_results: list[CollectionResult]) -> None:
        agent.generate_performance_report(
            collection_results,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
        )
        reports = agent.list_reports()
        assert len(reports) >= 1
