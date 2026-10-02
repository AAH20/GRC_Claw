"""Tests for the Journey Analytics agent and API."""
from __future__ import annotations

import pytest

from journey_orchestrator.agents.journey_analytics import (
    AnalyticsRequest,
    JourneyAnalytics,
)
from journey_orchestrator.models.analytics import MetricType


class TestJourneyAnalyticsAgent:
    """Tests for the Journey Analytics agent."""

    @pytest.fixture
    def agent(self) -> JourneyAnalytics:
        return JourneyAnalytics()

    @pytest.mark.asyncio
    async def test_analyze_success(self, agent: JourneyAnalytics) -> None:
        request = AnalyticsRequest(
            journey_id="journey_123",
            metrics=[MetricType.CONVERSION_RATE, MetricType.ENGAGEMENT_RATE],
            include_funnel=True,
            include_cohorts=True,
        )
        report = await agent.analyze(request)
        assert report.journey_id == "journey_123"
        assert report.performance.total_customers > 0
        assert 0.0 <= report.performance.conversion_rate <= 1.0
        assert 0.0 <= report.performance.engagement_rate <= 1.0
        assert report.funnel is not None
        assert len(report.funnel.stages) > 0
        assert len(report.cohorts) > 0
        assert len(report.insights) > 0

    @pytest.mark.asyncio
    async def test_analyze_empty_journey_id_raises(self, agent: JourneyAnalytics) -> None:
        request = AnalyticsRequest(journey_id="")
        with pytest.raises(ValueError, match="journey_id"):
            await agent.analyze(request)

    @pytest.mark.asyncio
    async def test_analyze_without_funnel(self, agent: JourneyAnalytics) -> None:
        request = AnalyticsRequest(
            journey_id="journey_123",
            include_funnel=False,
            include_cohorts=False,
        )
        report = await agent.analyze(request)
        assert report.funnel is None
        assert len(report.cohorts) == 0

    @pytest.mark.asyncio
    async def test_analyze_generates_insights(self, agent: JourneyAnalytics) -> None:
        request = AnalyticsRequest(
            journey_id="journey_123",
            include_funnel=True,
        )
        report = await agent.analyze(request)
        assert len(report.insights) > 0
        for insight in report.insights:
            assert insight.severity in ("info", "warning", "critical")
            assert 0.0 <= insight.confidence <= 1.0
            assert len(insight.message) > 0

    @pytest.mark.asyncio
    async def test_compare_journeys_success(self, agent: JourneyAnalytics) -> None:
        result = await agent.compare_journeys(
            journey_ids=["journey_1", "journey_2"],
            metric=MetricType.CONVERSION_RATE,
        )
        assert "metric" in result
        assert "journeys" in result
        assert result["metric"] == "conversion_rate"

    @pytest.mark.asyncio
    async def test_compare_journeys_single_id_raises(self, agent: JourneyAnalytics) -> None:
        with pytest.raises(ValueError, match="At least 2"):
            await agent.compare_journeys(journey_ids=["journey_1"])

    @pytest.mark.asyncio
    async def test_get_summary(self, agent: JourneyAnalytics) -> None:
        summary = await agent.get_summary()
        assert summary.total_journeys >= 0
        assert summary.active_journeys >= 0
        assert 0.0 <= summary.overall_conversion_rate <= 1.0
        assert summary.generated_at is not None

    @pytest.mark.asyncio
    async def test_analyze_with_custom_metrics(self, agent: JourneyAnalytics) -> None:
        request = AnalyticsRequest(
            journey_id="journey_123",
            metrics=[
                MetricType.CONVERSION_RATE,
                MetricType.ENGAGEMENT_RATE,
                MetricType.REVENUE_PER_CUSTOMER,
                MetricType.OPEN_RATE,
                MetricType.CLICK_RATE,
            ],
        )
        report = await agent.analyze(request)
        assert len(report.performance.metrics) == 5
        metric_types = {m.metric_type for m in report.performance.metrics}
        assert MetricType.CONVERSION_RATE in metric_types
        assert MetricType.ENGAGEMENT_RATE in metric_types
        assert MetricType.REVENUE_PER_CUSTOMER in metric_types


class TestJourneyAnalyticsAPI:
    """Tests for the Analytics API endpoints."""

    @pytest.fixture
    async def client(self):
        from httpx import AsyncClient, ASGITransport

        from journey_orchestrator.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_get_analytics_success(self, client) -> None:
        payload = {
            "journey_id": "journey_123",
            "metrics": ["conversion_rate", "engagement_rate"],
            "include_funnel": True,
        }
        response = await client.post("/api/v1/analytics", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["journey_id"] == "journey_123"
        assert "conversion_rate" in data
        assert "engagement_rate" in data
        assert "insights_count" in data

    @pytest.mark.asyncio
    async def test_get_analytics_empty_journey_id(self, client) -> None:
        payload = {"journey_id": ""}
        response = await client.post("/api/v1/analytics", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_analytics_invalid_metric(self, client) -> None:
        payload = {
            "journey_id": "journey_123",
            "metrics": ["invalid_metric"],
        }
        response = await client.post("/api/v1/analytics", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_analytics_summary(self, client) -> None:
        response = await client.get("/api/v1/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_journeys" in data
        assert "overall_conversion_rate" in data

    @pytest.mark.asyncio
    async def test_get_cached_analytics_not_found(self, client) -> None:
        response = await client.get("/api/v1/analytics/nonexistent_journey")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_cached_analytics_after_post(self, client) -> None:
        # First create analytics
        payload = {"journey_id": "journey_cached"}
        post_response = await client.post("/api/v1/analytics", json=payload)
        assert post_response.status_code == 200

        # Then retrieve cached
        get_response = await client.get("/api/v1/analytics/journey_cached")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["journey_id"] == "journey_cached"
