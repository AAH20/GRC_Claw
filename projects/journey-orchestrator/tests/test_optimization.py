"""Tests for the Journey Optimization agent and API."""
from __future__ import annotations

import pytest

from journey_orchestrator.agents.journey_optimization import (
    JourneyOptimization,
    OptimizationRequest,
)
from journey_orchestrator.models.analytics import MetricType


class TestJourneyOptimizationAgent:
    """Tests for the Journey Optimization agent."""

    @pytest.fixture
    def agent(self) -> JourneyOptimization:
        return JourneyOptimization()

    @pytest.mark.asyncio
    async def test_optimize_success(self, agent: JourneyOptimization) -> None:
        request = OptimizationRequest(
            journey_id="journey_123",
            target_metric=MetricType.CONVERSION_RATE,
            optimization_goal="maximize",
            max_suggestions=5,
        )
        result = await agent.optimize(request)
        assert result.journey_id == "journey_123"
        assert result.target_metric == "conversion_rate"
        assert result.current_value >= 0.0
        assert result.projected_value >= result.current_value
        assert result.improvement_potential >= 0.0
        assert len(result.suggestions) > 0
        assert len(result.suggestions) <= 5

    @pytest.mark.asyncio
    async def test_optimize_empty_journey_id_raises(self, agent: JourneyOptimization) -> None:
        request = OptimizationRequest(journey_id="")
        with pytest.raises(ValueError, match="journey_id"):
            await agent.optimize(request)

    @pytest.mark.asyncio
    async def test_optimize_invalid_goal_raises(self, agent: JourneyOptimization) -> None:
        request = OptimizationRequest(
            journey_id="journey_123",
            optimization_goal="invalid",
        )
        with pytest.raises(ValueError, match="optimization_goal"):
            await agent.optimize(request)

    @pytest.mark.asyncio
    async def test_optimize_auto_apply(self, agent: JourneyOptimization) -> None:
        request = OptimizationRequest(
            journey_id="journey_123",
            target_metric=MetricType.CONVERSION_RATE,
            auto_apply=True,
        )
        result = await agent.optimize(request)
        # Some suggestions should be auto-applied or require approval
        total = len(result.applied_changes) + len(result.requires_approval)
        assert total > 0

    @pytest.mark.asyncio
    async def test_optimize_suggestions_structure(self, agent: JourneyOptimization) -> None:
        request = OptimizationRequest(
            journey_id="journey_123",
            target_metric=MetricType.CONVERSION_RATE,
        )
        result = await agent.optimize(request)
        for suggestion in result.suggestions:
            assert suggestion.suggestion_id
            assert suggestion.category
            assert suggestion.title
            assert 0.0 <= suggestion.expected_impact <= 1.0
            assert 0.0 <= suggestion.confidence <= 1.0
            assert suggestion.effort in ("low", "medium", "high")
            assert suggestion.risk_level in ("low", "medium", "high")

    @pytest.mark.asyncio
    async def test_optimize_engagement_metric(self, agent: JourneyOptimization) -> None:
        request = OptimizationRequest(
            journey_id="journey_123",
            target_metric=MetricType.ENGAGEMENT_RATE,
        )
        result = await agent.optimize(request)
        assert result.target_metric == "engagement_rate"
        assert result.current_value >= 0.0

    @pytest.mark.asyncio
    async def test_optimize_revenue_metric(self, agent: JourneyOptimization) -> None:
        request = OptimizationRequest(
            journey_id="journey_123",
            target_metric=MetricType.REVENUE_PER_CUSTOMER,
        )
        result = await agent.optimize(request)
        assert result.target_metric == "revenue_per_customer"

    @pytest.mark.asyncio
    async def test_apply_optimization_success(self, agent: JourneyOptimization) -> None:
        result = await agent.apply_optimization(
            journey_id="journey_123",
            suggestion_id="suggestion_1",
        )
        assert result["journey_id"] == "journey_123"
        assert result["suggestion_id"] == "suggestion_1"
        assert result["status"] == "applied"

    @pytest.mark.asyncio
    async def test_apply_optimization_empty_journey_id_raises(
        self, agent: JourneyOptimization
    ) -> None:
        with pytest.raises(ValueError, match="journey_id"):
            await agent.apply_optimization(journey_id="", suggestion_id="s1")

    @pytest.mark.asyncio
    async def test_apply_optimization_empty_suggestion_id_raises(
        self, agent: JourneyOptimization
    ) -> None:
        with pytest.raises(ValueError, match="suggestion_id"):
            await agent.apply_optimization(journey_id="j1", suggestion_id="")

    @pytest.mark.asyncio
    async def test_optimize_max_suggestions_respected(self, agent: JourneyOptimization) -> None:
        request = OptimizationRequest(
            journey_id="journey_123",
            max_suggestions=3,
        )
        result = await agent.optimize(request)
        assert len(result.suggestions) <= 3


class TestJourneyOptimizationAPI:
    """Tests for the Optimization API endpoints."""

    @pytest.fixture
    async def client(self):
        from httpx import AsyncClient, ASGITransport

        from journey_orchestrator.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_optimize_journey_success(self, client) -> None:
        payload = {
            "journey_id": "journey_123",
            "target_metric": "conversion_rate",
            "optimization_goal": "maximize",
            "max_suggestions": 5,
        }
        response = await client.post("/api/v1/optimization", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["journey_id"] == "journey_123"
        assert data["target_metric"] == "conversion_rate"
        assert "current_value" in data
        assert "projected_value" in data
        assert "suggestions_count" in data

    @pytest.mark.asyncio
    async def test_optimize_journey_empty_id(self, client) -> None:
        payload = {"journey_id": ""}
        response = await client.post("/api/v1/optimization", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_optimize_journey_invalid_metric(self, client) -> None:
        payload = {
            "journey_id": "journey_123",
            "target_metric": "invalid_metric",
        }
        response = await client.post("/api/v1/optimization", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_apply_optimization_endpoint(self, client) -> None:
        payload = {
            "journey_id": "journey_123",
            "suggestion_id": "suggestion_1",
        }
        response = await client.post("/api/v1/optimization/apply", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "applied"

    @pytest.mark.asyncio
    async def test_apply_optimization_empty_id(self, client) -> None:
        payload = {"journey_id": "", "suggestion_id": "s1"}
        response = await client.post("/api/v1/optimization/apply", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_optimization_result_not_found(self, client) -> None:
        response = await client.get("/api/v1/optimization/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_optimization_result_after_post(self, client) -> None:
        # First create optimization
        payload = {"journey_id": "journey_opt_cached"}
        post_response = await client.post("/api/v1/optimization", json=payload)
        assert post_response.status_code == 200

        # Then retrieve
        get_response = await client.get("/api/v1/optimization/journey_opt_cached")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["journey_id"] == "journey_opt_cached"
