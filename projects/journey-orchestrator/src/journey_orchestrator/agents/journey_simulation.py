"""Journey Simulation agent - Monte Carlo simulation for journey outcomes."""
from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Any

import structlog
from pydantic import BaseModel, Field

from journey_orchestrator.models.analytics import MetricType

logger = structlog.get_logger(__name__)


class SimulationRequest(BaseModel):
    """Request for Monte Carlo journey simulation."""

    journey_id: str = Field(..., description="The journey ID to simulate")
    num_simulations: int = Field(default=1000, ge=100, le=100000)
    num_customers: int = Field(default=1000, ge=10, le=1000000)
    target_metric: MetricType = Field(default=MetricType.CONVERSION_RATE)
    parameters: dict[str, float] = Field(
        default_factory=dict,
        description="Simulation parameters (conversion_prob, engagement_prob, etc.)",
    )
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99)
    random_seed: int | None = Field(default=None, description="Random seed for reproducibility")


class SimulationStatistics(BaseModel):
    """Statistical summary of simulation results."""

    mean: float = Field(..., ge=0.0)
    median: float = Field(..., ge=0.0)
    std_dev: float = Field(..., ge=0.0)
    min: float = Field(..., ge=0.0)
    max: float = Field(..., ge=0.0)
    percentile_5: float = Field(..., ge=0.0)
    percentile_95: float = Field(..., ge=0.0)
    confidence_interval_low: float = Field(..., ge=0.0)
    confidence_interval_high: float = Field(..., ge=0.0)


class SimulationResult(BaseModel):
    """Result of a Monte Carlo simulation."""

    journey_id: str
    num_simulations: int
    num_customers: int
    target_metric: str
    statistics: SimulationStatistics
    success_probability: float = Field(..., ge=0.0, le=1.0)
    expected_value: float = Field(..., ge=0.0)
    risk_of_underperformance: float = Field(..., ge=0.0, le=1.0)
    raw_results: list[float] = Field(default_factory=list)
    parameters_used: dict[str, float] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class JourneySimulation:
    """Agent that runs Monte Carlo simulations for journey outcomes.

    Simulates customer journey execution with probabilistic conversion,
    engagement, and revenue models to forecast performance and
    quantify uncertainty.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize the Journey Simulation agent.

        Args:
            llm_client: Optional LLM client for AI-powered simulation tuning.
        """
        self.llm_client = llm_client
        self.logger = logger.bind(agent="journey_simulation")

    async def simulate(self, request: SimulationRequest) -> SimulationResult:
        """Run a Monte Carlo simulation for a journey.

        Args:
            request: The simulation request.

        Returns:
            The simulation result with statistics and projections.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.journey_id.strip():
            raise ValueError("journey_id must not be empty")
        if request.num_simulations < 100:
            raise ValueError("num_simulations must be at least 100")
        if request.num_customers < 10:
            raise ValueError("num_customers must be at least 10")
        if not 0.8 <= request.confidence_level <= 0.99:
            raise ValueError("confidence_level must be between 0.8 and 0.99")

        self.logger.info(
            "Running Monte Carlo simulation",
            journey_id=request.journey_id,
            simulations=request.num_simulations,
            customers=request.num_customers,
        )

        # Set random seed for reproducibility
        if request.random_seed is not None:
            random.seed(request.random_seed)

        # Get simulation parameters
        params = self._get_simulation_parameters(request)

        # Run simulations
        results: list[float] = []
        for _ in range(request.num_simulations):
            outcome = self._run_single_simulation(request.num_customers, params)
            results.append(outcome)

        # Compute statistics
        stats = self._compute_statistics(results, request.confidence_level)

        # Compute success probability (probability of exceeding baseline)
        baseline = params.get("baseline_rate", 0.1)
        success_prob = sum(1 for r in results if r > baseline) / len(results)

        # Risk of underperformance (probability of being below target)
        target = params.get("target_rate", 0.15)
        risk = sum(1 for r in results if r < target) / len(results)

        result = SimulationResult(
            journey_id=request.journey_id,
            num_simulations=request.num_simulations,
            num_customers=request.num_customers,
            target_metric=request.target_metric.value,
            statistics=stats,
            success_probability=success_prob,
            expected_value=stats.mean,
            risk_of_underperformance=risk,
            raw_results=results,
            parameters_used=params,
        )

        self.logger.info(
            "Simulation complete",
            journey_id=request.journey_id,
            mean=stats.mean,
            success_probability=success_prob,
            risk=risk,
        )
        return result

    async def compare_scenarios(
        self,
        journey_id: str,
        scenarios: list[dict[str, float]],
        num_simulations: int = 1000,
        num_customers: int = 1000,
    ) -> dict[str, Any]:
        """Compare multiple journey scenarios via simulation.

        Args:
            journey_id: The journey ID.
            scenarios: List of parameter dictionaries for each scenario.
            num_simulations: Number of simulations per scenario.
            num_customers: Number of customers per simulation.

        Returns:
            A comparison of scenario results.

        Raises:
            ValueError: If fewer than 2 scenarios are provided.
        """
        if len(scenarios) < 2:
            raise ValueError("At least 2 scenarios are required for comparison")

        self.logger.info(
            "Comparing scenarios",
            journey_id=journey_id,
            scenarios=len(scenarios),
        )

        scenario_results: list[dict[str, Any]] = []
        for i, params in enumerate(scenarios):
            request = SimulationRequest(
                journey_id=journey_id,
                num_simulations=num_simulations,
                num_customers=num_customers,
                parameters=params,
            )
            result = await self.simulate(request)
            scenario_results.append(
                {
                    "scenario_index": i,
                    "parameters": params,
                    "expected_value": result.expected_value,
                    "success_probability": result.success_probability,
                    "risk": result.risk_of_underperformance,
                    "confidence_interval": [
                        result.statistics.confidence_interval_low,
                        result.statistics.confidence_interval_high,
                    ],
                }
            )

        # Find best scenario
        best = max(scenario_results, key=lambda s: s["expected_value"])

        return {
            "journey_id": journey_id,
            "scenarios": scenario_results,
            "best_scenario_index": best["scenario_index"],
            "best_expected_value": best["expected_value"],
        }

    def _get_simulation_parameters(self, request: SimulationRequest) -> dict[str, float]:
        """Get simulation parameters with defaults.

        Args:
            request: The simulation request.

        Returns:
            A dictionary of simulation parameters.
        """
        defaults = {
            "conversion_prob": 0.15,
            "engagement_prob": 0.45,
            "revenue_per_conversion": 50.0,
            "baseline_rate": 0.1,
            "target_rate": 0.15,
            "churn_prob": 0.05,
            "variance_factor": 0.2,
        }
        defaults.update(request.parameters)
        return defaults

    def _run_single_simulation(
        self,
        num_customers: int,
        params: dict[str, float],
    ) -> float:
        """Run a single simulation trial.

        Args:
            num_customers: Number of customers to simulate.
            params: Simulation parameters.

        Returns:
            The simulation outcome (e.g., conversion rate).
        """
        conversion_prob = params.get("conversion_prob", 0.15)
        variance = params.get("variance_factor", 0.2)

        # Add noise to conversion probability
        noisy_prob = conversion_prob * (1.0 + random.gauss(0, variance))
        noisy_prob = max(0.0, min(1.0, noisy_prob))

        # Simulate customer conversions
        conversions = sum(
            1 for _ in range(num_customers) if random.random() < noisy_prob
        )

        return conversions / num_customers if num_customers > 0 else 0.0

    def _compute_statistics(
        self,
        results: list[float],
        confidence_level: float,
    ) -> SimulationStatistics:
        """Compute statistical summary of simulation results.

        Args:
            results: List of simulation outcomes.
            confidence_level: Confidence level for intervals.

        Returns:
            The computed statistics.
        """
        sorted_results = sorted(results)
        n = len(sorted_results)

        mean = sum(sorted_results) / n
        median = sorted_results[n // 2] if n % 2 == 1 else (
            (sorted_results[n // 2 - 1] + sorted_results[n // 2]) / 2
        )
        variance = sum((x - mean) ** 2 for x in sorted_results) / n
        std_dev = variance**0.5

        # Percentiles
        p5_idx = int(n * 0.05)
        p95_idx = int(n * 0.95)
        percentile_5 = sorted_results[p5_idx]
        percentile_95 = sorted_results[p95_idx]

        # Confidence interval
        alpha = 1.0 - confidence_level
        ci_low_idx = int(n * (alpha / 2))
        ci_high_idx = int(n * (1.0 - alpha / 2))
        ci_low = sorted_results[ci_low_idx]
        ci_high = sorted_results[ci_high_idx]

        return SimulationStatistics(
            mean=mean,
            median=median,
            std_dev=std_dev,
            min=sorted_results[0],
            max=sorted_results[-1],
            percentile_5=percentile_5,
            percentile_95=percentile_95,
            confidence_interval_low=ci_low,
            confidence_interval_high=ci_high,
        )
