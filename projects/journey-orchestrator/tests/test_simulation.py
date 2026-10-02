"""Tests for the Journey Simulation agent."""
from __future__ import annotations

import pytest

from journey_orchestrator.agents.journey_simulation import (
    JourneySimulation,
    SimulationRequest,
)
from journey_orchestrator.models.analytics import MetricType


class TestJourneySimulationAgent:
    """Tests for the Journey Simulation agent."""

    @pytest.fixture
    def agent(self) -> JourneySimulation:
        return JourneySimulation()

    @pytest.mark.asyncio
    async def test_simulate_success(self, agent: JourneySimulation) -> None:
        request = SimulationRequest(
            journey_id="journey_123",
            num_simulations=500,
            num_customers=1000,
            target_metric=MetricType.CONVERSION_RATE,
            random_seed=42,
        )
        result = await agent.simulate(request)
        assert result.journey_id == "journey_123"
        assert result.num_simulations == 500
        assert result.num_customers == 1000
        assert result.target_metric == "conversion_rate"
        assert result.statistics.mean >= 0.0
        assert result.statistics.median >= 0.0
        assert result.statistics.std_dev >= 0.0
        assert result.statistics.min >= 0.0
        assert result.statistics.max >= 0.0
        assert 0.0 <= result.success_probability <= 1.0
        assert 0.0 <= result.risk_of_underperformance <= 1.0
        assert len(result.raw_results) == 500

    @pytest.mark.asyncio
    async def test_simulate_reproducibility_with_seed(self, agent: JourneySimulation) -> None:
        request1 = SimulationRequest(
            journey_id="journey_123",
            num_simulations=200,
            num_customers=500,
            random_seed=42,
        )
        request2 = SimulationRequest(
            journey_id="journey_123",
            num_simulations=200,
            num_customers=500,
            random_seed=42,
        )
        result1 = await agent.simulate(request1)
        result2 = await agent.simulate(request2)
        assert result1.statistics.mean == result2.statistics.mean
        assert result1.raw_results == result2.raw_results

    @pytest.mark.asyncio
    async def test_simulate_empty_journey_id_raises(self, agent: JourneySimulation) -> None:
        request = SimulationRequest(journey_id="")
        with pytest.raises(ValueError, match="journey_id"):
            await agent.simulate(request)

    @pytest.mark.asyncio
    async def test_simulate_too_few_simulations_raises(self, agent: JourneySimulation) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SimulationRequest(
                journey_id="journey_123",
                num_simulations=50,
            )

    @pytest.mark.asyncio
    async def test_simulate_too_few_customers_raises(self, agent: JourneySimulation) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SimulationRequest(
                journey_id="journey_123",
                num_customers=5,
            )

    @pytest.mark.asyncio
    async def test_simulate_invalid_confidence_level_raises(
        self, agent: JourneySimulation
    ) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SimulationRequest(
                journey_id="journey_123",
                confidence_level=0.5,
            )

    @pytest.mark.asyncio
    async def test_simulate_with_custom_parameters(self, agent: JourneySimulation) -> None:
        request = SimulationRequest(
            journey_id="journey_123",
            num_simulations=300,
            num_customers=500,
            parameters={
                "conversion_prob": 0.25,
                "engagement_prob": 0.6,
                "variance_factor": 0.1,
            },
            random_seed=123,
        )
        result = await agent.simulate(request)
        assert result.parameters_used["conversion_prob"] == 0.25
        assert result.parameters_used["engagement_prob"] == 0.6
        assert result.parameters_used["variance_factor"] == 0.1

    @pytest.mark.asyncio
    async def test_simulate_statistics_consistency(self, agent: JourneySimulation) -> None:
        request = SimulationRequest(
            journey_id="journey_123",
            num_simulations=1000,
            num_customers=1000,
            random_seed=42,
        )
        result = await agent.simulate(request)
        stats = result.statistics
        assert stats.min <= stats.percentile_5 <= stats.median <= stats.percentile_95 <= stats.max
        assert stats.confidence_interval_low <= stats.confidence_interval_high
        assert stats.mean >= 0.0

    @pytest.mark.asyncio
    async def test_compare_scenarios_success(self, agent: JourneySimulation) -> None:
        scenarios = [
            {"conversion_prob": 0.10, "variance_factor": 0.1},
            {"conversion_prob": 0.20, "variance_factor": 0.15},
            {"conversion_prob": 0.15, "variance_factor": 0.2},
        ]
        result = await agent.compare_scenarios(
            journey_id="journey_123",
            scenarios=scenarios,
            num_simulations=200,
            num_customers=500,
        )
        assert result["journey_id"] == "journey_123"
        assert len(result["scenarios"]) == 3
        assert result["best_scenario_index"] is not None
        assert result["best_expected_value"] > 0.0

    @pytest.mark.asyncio
    async def test_compare_scenarios_single_scenario_raises(
        self, agent: JourneySimulation
    ) -> None:
        scenarios = [{"conversion_prob": 0.15}]
        with pytest.raises(ValueError, match="At least 2"):
            await agent.compare_scenarios(
                journey_id="journey_123",
                scenarios=scenarios,
            )

    @pytest.mark.asyncio
    async def test_simulate_engagement_metric(self, agent: JourneySimulation) -> None:
        request = SimulationRequest(
            journey_id="journey_123",
            num_simulations=200,
            num_customers=500,
            target_metric=MetricType.ENGAGEMENT_RATE,
            random_seed=42,
        )
        result = await agent.simulate(request)
        assert result.target_metric == "engagement_rate"

    @pytest.mark.asyncio
    async def test_simulate_large_scale(self, agent: JourneySimulation) -> None:
        request = SimulationRequest(
            journey_id="journey_123",
            num_simulations=10000,
            num_customers=10000,
            random_seed=42,
        )
        result = await agent.simulate(request)
        assert result.num_simulations == 10000
        assert len(result.raw_results) == 10000
        # With large samples, mean should be close to conversion_prob
        assert abs(result.statistics.mean - 0.15) < 0.02
