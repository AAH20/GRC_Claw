"""Experimentation agent - designs A/B tests and multi-armed bandit experiments."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ExperimentRequest(BaseModel):
    """Request for experiment design."""

    journey_id: str
    hypothesis: str
    variants: list[str] = Field(min_length=2, description="At least 2 variants required")
    success_metric: str
    minimum_sample_size: int = Field(default=1000, ge=100)
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99)


class ExperimentVariant(BaseModel):
    """A single experiment variant."""

    name: str
    traffic_allocation: float = Field(ge=0.0, le=1.0)
    description: str = ""


class ExperimentDesign(BaseModel):
    """Output of the Experimentation agent."""

    experiment_id: str
    journey_id: str
    hypothesis: str
    variants: list[ExperimentVariant]
    success_metric: str
    minimum_sample_size: int
    confidence_level: float
    estimated_duration_days: int
    status: str = "draft"


class ExperimentationAgent:
    """Agent that designs and manages experiments on journey variants.

    Creates A/B tests and multi-armed bandit experiments to optimize
    journey performance through data-driven iteration.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize the Experimentation Agent.

        Args:
            llm_client: Optional LLM client for AI-powered experiment design.
        """
        self.llm_client = llm_client
        self.logger = logger.bind(agent="experimentation")

    async def design_experiment(self, request: ExperimentRequest) -> ExperimentDesign:
        """Design an experiment for a journey.

        Args:
            request: The experiment design request.

        Returns:
            A complete experiment design.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.journey_id.strip():
            raise ValueError("journey_id must not be empty")
        if not request.hypothesis.strip():
            raise ValueError("hypothesis must not be empty")
        if len(request.variants) < 2:
            raise ValueError("At least 2 variants are required")
        if not request.success_metric.strip():
            raise ValueError("success_metric must not be empty")

        self.logger.info(
            "Designing experiment",
            journey_id=request.journey_id,
            variants=request.variants,
        )

        # Equal traffic allocation
        allocation = 1.0 / len(request.variants)
        variants = [
            ExperimentVariant(
                name=v,
                traffic_allocation=allocation,
                description=f"Variant {v}",
            )
            for v in request.variants
        ]

        design = ExperimentDesign(
            experiment_id=f"exp_{request.journey_id}_{len(request.variants)}",
            journey_id=request.journey_id,
            hypothesis=request.hypothesis,
            variants=variants,
            success_metric=request.success_metric,
            minimum_sample_size=request.minimum_sample_size,
            confidence_level=request.confidence_level,
            estimated_duration_days=max(7, request.minimum_sample_size // 100),
        )

        self.logger.info(
            "Experiment designed",
            experiment_id=design.experiment_id,
            variants=len(variants),
        )
        return design
