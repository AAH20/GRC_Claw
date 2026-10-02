"""A/B Testing agent for managing and analyzing experiments."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ExperimentStatus(StrEnum):
    """Status of an A/B test experiment."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class Variant:
    """A variant in an A/B test.

    Attributes:
        name: Variant identifier (e.g., "control", "treatment").
        weight: Traffic allocation weight (0.0 to 1.0).
        content: Optional content override for this variant.
    """

    name: str
    weight: float = 0.5
    content: dict[str, Any] = field(default_factory=dict)


@dataclass
class Experiment:
    """An A/B test experiment.

    Attributes:
        id: Unique experiment identifier.
        name: Human-readable experiment name.
        page_url: Target page URL.
        variants: List of variants in the experiment.
        status: Current experiment status.
        confidence_level: Statistical confidence level (0.0 to 1.0).
        min_sample_size: Minimum sample size for significance.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        metadata: Additional experiment metadata.
    """

    id: str
    name: str
    page_url: str
    variants: list[Variant]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    confidence_level: float = 0.95
    min_sample_size: int = 100
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


class ABTestingAgent:
    """Agent for creating, managing, and analyzing A/B test experiments.

    This agent handles experiment lifecycle management, variant assignment,
    and statistical analysis of experiment results.
    """

    def __init__(self, default_confidence_level: float = 0.95, min_sample_size: int = 100) -> None:
        """Initialize the A/B Testing agent.

        Args:
            default_confidence_level: Default statistical confidence level.
            min_sample_size: Minimum sample size for statistical significance.
        """
        self._experiments: dict[str, Experiment] = {}
        self._default_confidence_level = default_confidence_level
        self._min_sample_size = min_sample_size
        logger.info(
            "ABTestingAgent initialized",
            confidence_level=default_confidence_level,
            min_sample_size=min_sample_size,
        )

    def create_experiment(
        self,
        name: str,
        page_url: str,
        variants: list[Variant],
        confidence_level: float | None = None,
        min_sample_size: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Experiment:
        """Create a new A/B test experiment.

        Args:
            name: Human-readable experiment name.
            page_url: Target page URL.
            variants: List of variants to test.
            confidence_level: Statistical confidence level (defaults to agent default).
            min_sample_size: Minimum sample size (defaults to agent default).
            metadata: Additional experiment metadata.

        Returns:
            The created experiment.

        Raises:
            ValueError: If variants list is empty or weights don't sum to 1.0.
        """
        if not variants:
            raise ValueError("At least one variant is required")

        total_weight = sum(v.weight for v in variants)
        if not 0.99 <= total_weight <= 1.01:
            raise ValueError(f"Variant weights must sum to 1.0, got {total_weight}")

        experiment_id = self._generate_id(name, page_url)
        experiment = Experiment(
            id=experiment_id,
            name=name,
            page_url=page_url,
            variants=variants,
            confidence_level=confidence_level or self._default_confidence_level,
            min_sample_size=min_sample_size or self._min_sample_size,
            metadata=metadata or {},
        )
        self._experiments[experiment_id] = experiment
        logger.info("Experiment created", experiment_id=experiment_id, name=name)
        return experiment

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        """Retrieve an experiment by ID.

        Args:
            experiment_id: The experiment identifier.

        Returns:
            The experiment if found, None otherwise.
        """
        return self._experiments.get(experiment_id)

    def start_experiment(self, experiment_id: str) -> Experiment:
        """Start a draft experiment.

        Args:
            experiment_id: The experiment identifier.

        Returns:
            The updated experiment.

        Raises:
            KeyError: If experiment not found.
            ValueError: If experiment is not in draft status.
        """
        experiment = self._get_experiment_or_raise(experiment_id)
        if experiment.status != ExperimentStatus.DRAFT:
            raise ValueError(f"Cannot start experiment in {experiment.status} status")
        experiment.status = ExperimentStatus.RUNNING
        experiment.updated_at = datetime.utcnow()
        logger.info("Experiment started", experiment_id=experiment_id)
        return experiment

    def pause_experiment(self, experiment_id: str) -> Experiment:
        """Pause a running experiment.

        Args:
            experiment_id: The experiment identifier.

        Returns:
            The updated experiment.

        Raises:
            KeyError: If experiment not found.
            ValueError: If experiment is not running.
        """
        experiment = self._get_experiment_or_raise(experiment_id)
        if experiment.status != ExperimentStatus.RUNNING:
            raise ValueError(f"Cannot pause experiment in {experiment.status} status")
        experiment.status = ExperimentStatus.PAUSED
        experiment.updated_at = datetime.utcnow()
        logger.info("Experiment paused", experiment_id=experiment_id)
        return experiment

    def complete_experiment(self, experiment_id: str) -> Experiment:
        """Mark an experiment as completed.

        Args:
            experiment_id: The experiment identifier.

        Returns:
            The updated experiment.

        Raises:
            KeyError: If experiment not found.
        """
        experiment = self._get_experiment_or_raise(experiment_id)
        experiment.status = ExperimentStatus.COMPLETED
        experiment.updated_at = datetime.utcnow()
        logger.info("Experiment completed", experiment_id=experiment_id)
        return experiment

    def assign_variant(self, experiment_id: str, user_id: str) -> Variant | None:
        """Assign a variant to a user using consistent hashing.

        Args:
            experiment_id: The experiment identifier.
            user_id: The user identifier.

        Returns:
            The assigned variant, or None if experiment not found or not running.
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return None

        hash_input = f"{experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        normalized = (hash_value % 10000) / 10000.0

        cumulative = 0.0
        for variant in experiment.variants:
            cumulative += variant.weight
            if normalized <= cumulative:
                logger.debug(
                    "Variant assigned",
                    experiment_id=experiment_id,
                    user_id=user_id,
                    variant=variant.name,
                )
                return variant

        return experiment.variants[-1]

    def get_experiment_results(self, experiment_id: str) -> dict[str, Any] | None:
        """Get statistical results for an experiment.

        Args:
            experiment_id: The experiment identifier.

        Returns:
            Results dictionary with conversion rates and statistical significance,
            or None if experiment not found.
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return None

        results: dict[str, Any] = {
            "experiment_id": experiment_id,
            "status": experiment.status.value,
            "variants": [],
            "is_significant": False,
        }

        for variant in experiment.variants:
            variant_result = {
                "name": variant.name,
                "participants": 0,
                "conversions": 0,
                "conversion_rate": 0.0,
            }
            results["variants"].append(variant_result)

        return results

    def list_experiments(
        self, page_url: str | None = None, status: ExperimentStatus | None = None
    ) -> list[Experiment]:
        """List experiments with optional filtering.

        Args:
            page_url: Filter by page URL.
            status: Filter by experiment status.

        Returns:
            List of matching experiments.
        """
        experiments = list(self._experiments.values())
        if page_url:
            experiments = [e for e in experiments if e.page_url == page_url]
        if status:
            experiments = [e for e in experiments if e.status == status]
        return experiments

    def _generate_id(self, name: str, page_url: str) -> str:
        """Generate a unique experiment ID.

        Args:
            name: Experiment name.
            page_url: Target page URL.

        Returns:
            Unique experiment identifier.
        """
        raw = f"{name}:{page_url}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _get_experiment_or_raise(self, experiment_id: str) -> Experiment:
        """Get an experiment or raise KeyError.

        Args:
            experiment_id: The experiment identifier.

        Returns:
            The experiment.

        Raises:
            KeyError: If experiment not found.
        """
        if experiment_id not in self._experiments:
            raise KeyError(f"Experiment {experiment_id} not found")
        return self._experiments[experiment_id]
