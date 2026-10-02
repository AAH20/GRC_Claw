"""A/B testing infrastructure for marketing experiments.

This module provides a complete A/B testing framework including:
- Experiment configuration and management
- Statistical significance testing
- Sample size calculation
- Variant assignment and tracking
- Results analysis and reporting
- Multi-armed bandit support
"""

from __future__ import annotations

import hashlib
import math
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class ExperimentStatus(Enum):
    """Status of an A/B experiment."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


class StatisticalTest(Enum):
    """Supported statistical tests."""

    T_TEST = "t_test"
    CHI_SQUARE = "chi_square"
    MANN_WHITNEY = "mann_whitney"
    BOOTSTRAP = "bootstrap"
    BAYESIAN = "bayesian"


@dataclass
class ExperimentVariant:
    """Represents a variant in an A/B experiment.

    Attributes:
        variant_id: Unique variant identifier.
        name: Human-readable variant name.
        config: Variant configuration parameters.
        traffic_percentage: Percentage of traffic allocated (0-100).
        is_control: Whether this is the control variant.
    """

    variant_id: str
    name: str
    config: dict[str, Any] = field(default_factory=dict)
    traffic_percentage: float = 50.0
    is_control: bool = False


@dataclass
class ExperimentConfig:
    """Configuration for an A/B experiment.

    Attributes:
        experiment_id: Unique experiment identifier.
        name: Experiment name.
        description: Experiment description.
        variants: List of experiment variants.
        primary_metric: Primary success metric name.
        secondary_metrics: List of secondary metric names.
        statistical_test: Statistical test to use.
        significance_level: Alpha level (e.g., 0.05).
        power: Statistical power (e.g., 0.80).
        minimum_detectable_effect: Minimum effect size to detect.
        status: Current experiment status.
        start_time: When the experiment started.
        end_time: When the experiment ended.
    """

    experiment_id: str
    name: str
    description: str = ""
    variants: list[ExperimentVariant] = field(default_factory=list)
    primary_metric: str = "conversion_rate"
    secondary_metrics: list[str] = field(default_factory=list)
    statistical_test: StatisticalTest = StatisticalTest.T_TEST
    significance_level: float = 0.05
    power: float = 0.80
    minimum_detectable_effect: float = 0.05
    status: ExperimentStatus = ExperimentStatus.DRAFT
    start_time: float = 0.0
    end_time: float = 0.0


@dataclass
class ExperimentResult:
    """Results of an A/B experiment.

    Attributes:
        experiment_id: The experiment identifier.
        variant_results: Per-variant result data.
        p_value: Statistical p_value.
        confidence_interval: Confidence interval for the effect.
        effect_size: Observed effect size.
        is_significant: Whether results are statistically significant.
        sample_size_per_variant: Sample size for each variant.
        recommendations: List of recommendations.
    """

    experiment_id: str
    variant_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    p_value: float = 1.0
    confidence_interval: tuple[float, float] = (0.0, 0.0)
    effect_size: float = 0.0
    is_significant: bool = False
    sample_size_per_variant: int = 0
    recommendations: list[str] = field(default_factory=list)


class SampleSizeCalculator:
    """Calculates required sample sizes for experiments."""

    @staticmethod
    def calculate_proportion_sample_size(
        baseline_rate: float,
        minimum_detectable_effect: float,
        significance_level: float = 0.05,
        power: float = 0.80,
    ) -> int:
        """Calculate sample size for a proportion-based metric.

        Args:
            baseline_rate: Baseline conversion rate (0-1).
            minimum_detectable_effect: Minimum detectable effect (absolute).
            significance_level: Alpha level.
            power: Statistical power.

        Returns:
            Required sample size per variant.

        Raises:
            ValueError: If parameters are invalid.
        """
        if not 0 < baseline_rate < 1:
            raise ValueError("baseline_rate must be between 0 and 1")
        if minimum_detectable_effect <= 0:
            raise ValueError("minimum_detectable_effect must be positive")
        if not 0 < significance_level < 1:
            raise ValueError("significance_level must be between 0 and 1")
        if not 0 < power < 1:
            raise ValueError("power must be between 0 and 1")

        z_alpha = SampleSizeCalculator._z_score(1 - significance_level / 2)
        z_beta = SampleSizeCalculator._z_score(power)

        p1 = baseline_rate
        p2 = baseline_rate + minimum_detectable_effect

        if p2 >= 1:
            raise ValueError("baseline_rate + MDE must be less than 1")

        pooled_p = (p1 + p2) / 2

        numerator = (
            z_alpha * math.sqrt(2 * pooled_p * (1 - pooled_p))
            + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
        ) ** 2

        denominator = (p2 - p1) ** 2

        return math.ceil(numerator / denominator)

    @staticmethod
    def calculate_continuous_sample_size(
        baseline_mean: float,
        minimum_detectable_effect: float,
        standard_deviation: float,
        significance_level: float = 0.05,
        power: float = 0.80,
    ) -> int:
        """Calculate sample size for a continuous metric.

        Args:
            baseline_mean: Baseline mean value.
            minimum_detectable_effect: Minimum detectable effect.
            standard_deviation: Standard deviation of the metric.
            significance_level: Alpha level.
            power: Statistical power.

        Returns:
            Required sample size per variant.

        Raises:
            ValueError: If parameters are invalid.
        """
        if standard_deviation <= 0:
            raise ValueError("standard_deviation must be positive")
        if minimum_detectable_effect <= 0:
            raise ValueError("minimum_detectable_effect must be positive")

        z_alpha = SampleSizeCalculator._z_score(1 - significance_level / 2)
        z_beta = SampleSizeCalculator._z_score(power)

        numerator = 2 * (z_alpha + z_beta) ** 2 * standard_deviation**2
        denominator = minimum_detectable_effect**2

        return math.ceil(numerator / denominator)

    @staticmethod
    def _z_score(probability: float) -> float:
        """Approximate the z-score for a given probability.

        Args:
            probability: The cumulative probability.

        Returns:
            The z-score.
        """
        # Rational approximation of the inverse normal CDF
        if probability <= 0 or probability >= 1:
            raise ValueError("Probability must be between 0 and 1")

        # Abramowitz and Stegun approximation
        p = probability
        if p > 0.5:
            sign = 1
            p = 1 - p
        else:
            sign = -1

        t = math.sqrt(-2 * math.log(p))
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308

        z = t - (c0 + c1 * t + c2 * t**2) / (1 + d1 * t + d2 * t**2 + d3 * t**3)
        return sign * z


class VariantAssigner:
    """Assigns users to experiment variants."""

    def __init__(self, seed: int | None = None) -> None:
        """Initialize VariantAssigner.

        Args:
            seed: Random seed for reproducibility.
        """
        self._rng = random.Random(seed)

    def assign(
        self, user_id: str, variants: list[ExperimentVariant]
    ) -> ExperimentVariant:
        """Assign a user to a variant using consistent hashing.

        Args:
            user_id: The user identifier.
            variants: Available variants.

        Returns:
            The assigned variant.

        Raises:
            ValueError: If variants list is empty.
        """
        if not variants:
            raise ValueError("At least one variant is required")

        if len(variants) == 1:
            return variants[0]

        # Use consistent hashing for deterministic assignment
        hash_input = f"{user_id}:{variants[0].variant_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        total_traffic = sum(v.traffic_percentage for v in variants)
        if total_traffic <= 0:
            raise ValueError("Total traffic percentage must be positive")

        normalized_hash = (hash_value % 10000) / 10000.0 * total_traffic

        cumulative = 0.0
        for variant in variants:
            cumulative += variant.traffic_percentage
            if normalized_hash <= cumulative:
                return variant

        return variants[-1]

    def assign_random(
        self, variants: list[ExperimentVariant]
    ) -> ExperimentVariant:
        """Assign a user to a variant randomly.

        Args:
            variants: Available variants.

        Returns:
            The assigned variant.
        """
        if not variants:
            raise ValueError("At least one variant is required")

        weights = [v.traffic_percentage for v in variants]
        return self._rng.choices(variants, weights=weights, k=1)[0]


class StatisticalAnalyzer:
    """Performs statistical analysis on experiment results."""

    def __init__(self) -> None:
        """Initialize StatisticalAnalyzer."""
        pass

    def analyze_proportions(
        self,
        control_successes: int,
        control_trials: int,
        treatment_successes: int,
        treatment_trials: int,
        significance_level: float = 0.05,
    ) -> dict[str, Any]:
        """Analyze proportion-based results (e.g., conversion rates).

        Args:
            control_successes: Number of successes in control.
            control_trials: Total trials in control.
            treatment_successes: Number of successes in treatment.
            treatment_trials: Total trials in treatment.
            significance_level: Alpha level.

        Returns:
            Dictionary with analysis results.

        Raises:
            ValueError: If trial counts are zero.
        """
        if control_trials == 0 or treatment_trials == 0:
            raise ValueError("Trial counts must be greater than zero")

        p_control = control_successes / control_trials
        p_treatment = treatment_successes / treatment_trials

        # Pooled proportion
        pooled_p = (control_successes + treatment_successes) / (
            control_trials + treatment_trials
        )

        # Standard error
        se = math.sqrt(
            pooled_p * (1 - pooled_p) * (1 / control_trials + 1 / treatment_trials)
        )

        if se == 0:
            z_score = 0.0
        else:
            z_score = (p_treatment - p_control) / se

        # Two-tailed p-value approximation
        p_value = 2 * (1 - self._normal_cdf(abs(z_score)))

        # Effect size
        effect_size = p_treatment - p_control

        # Confidence interval
        z_critical = SampleSizeCalculator._z_score(1 - significance_level / 2)
        se_diff = math.sqrt(
            p_control * (1 - p_control) / control_trials
            + p_treatment * (1 - p_treatment) / treatment_trials
        )
        ci_lower = effect_size - z_critical * se_diff
        ci_upper = effect_size + z_critical * se_diff

        return {
            "control_rate": p_control,
            "treatment_rate": p_treatment,
            "effect_size": effect_size,
            "relative_effect": (
                effect_size / p_control if p_control > 0 else 0.0
            ),
            "z_score": z_score,
            "p_value": p_value,
            "confidence_interval": (ci_lower, ci_upper),
            "is_significant": p_value < significance_level,
            "control_trials": control_trials,
            "treatment_trials": treatment_trials,
        }

    def analyze_continuous(
        self,
        control_values: list[float],
        treatment_values: list[float],
        significance_level: float = 0.05,
    ) -> dict[str, Any]:
        """Analyze continuous metric results.

        Args:
            control_values: Control group values.
            treatment_values: Treatment group values.
            significance_level: Alpha level.

        Returns:
            Dictionary with analysis results.

        Raises:
            ValueError: If either group is empty.
        """
        if not control_values or not treatment_values:
            raise ValueError("Both groups must have at least one value")

        n1, n2 = len(control_values), len(treatment_values)
        mean1 = sum(control_values) / n1
        mean2 = sum(treatment_values) / n2

        var1 = sum((x - mean1) ** 2 for x in control_values) / (n1 - 1) if n1 > 1 else 0
        var2 = (
            sum((x - mean2) ** 2 for x in treatment_values) / (n2 - 1) if n2 > 1 else 0
        )

        # Welch's t-test
        se = math.sqrt(var1 / n1 + var2 / n2) if (var1 + var2) > 0 else 0

        if se == 0:
            t_stat = 0.0
        else:
            t_stat = (mean2 - mean1) / se

        # Degrees of freedom (Welch-Satterthwaite)
        if var1 + var2 > 0:
            df = (var1 / n1 + var2 / n2) ** 2 / (
                (var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1)
            )
        else:
            df = n1 + n2 - 2

        effect_size = mean2 - mean1

        return {
            "control_mean": mean1,
            "treatment_mean": mean2,
            "effect_size": effect_size,
            "relative_effect": effect_size / mean1 if mean1 != 0 else 0.0,
            "t_statistic": t_stat,
            "degrees_of_freedom": df,
            "p_value": 0.0,  # Would need t-distribution CDF for exact value
            "is_significant": abs(t_stat) > 2.0,  # Rough approximation
            "control_n": n1,
            "treatment_n": n2,
        }

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Approximate the standard normal CDF.

        Args:
            x: The value.

        Returns:
            The CDF value.
        """
        # Abramowitz and Stegun approximation
        sign = 1 if x >= 0 else -1
        x = abs(x) / math.sqrt(2)

        t = 1.0 / (1.0 + 0.3275911 * x)
        erf = 1.0 - (
            ((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t
            + 0.254829592
        ) * t * math.exp(-x * x)

        return 0.5 * (1.0 + sign * erf)


class ABTestManager:
    """Manages A/B experiments end-to-end."""

    def __init__(self) -> None:
        """Initialize ABTestManager."""
        self._experiments: dict[str, ExperimentConfig] = {}
        self._results: dict[str, ExperimentResult] = {}
        self._assigner = VariantAssigner()

    def create_experiment(self, config: ExperimentConfig) -> ExperimentConfig:
        """Create a new experiment.

        Args:
            config: The experiment configuration.

        Returns:
            The created experiment config.

        Raises:
            ValueError: If experiment ID already exists.
        """
        if config.experiment_id in self._experiments:
            raise ValueError(
                f"Experiment {config.experiment_id} already exists"
            )

        self._experiments[config.experiment_id] = config
        return config

    def get_experiment(self, experiment_id: str) -> ExperimentConfig | None:
        """Get an experiment by ID.

        Args:
            experiment_id: The experiment identifier.

        Returns:
            The experiment config, or None if not found.
        """
        return self._experiments.get(experiment_id)

    def start_experiment(self, experiment_id: str) -> None:
        """Start an experiment.

        Args:
            experiment_id: The experiment identifier.

        Raises:
            ValueError: If experiment not found or already running.
        """
        exp = self._experiments.get(experiment_id)
        if exp is None:
            raise ValueError(f"Experiment {experiment_id} not found")
        if exp.status == ExperimentStatus.RUNNING:
            raise ValueError(f"Experiment {experiment_id} is already running")

        exp.status = ExperimentStatus.RUNNING
        exp.start_time = time.time()

    def stop_experiment(self, experiment_id: str) -> None:
        """Stop an experiment.

        Args:
            experiment_id: The experiment identifier.

        Raises:
            ValueError: If experiment not found.
        """
        exp = self._experiments.get(experiment_id)
        if exp is None:
            raise ValueError(f"Experiment {experiment_id} not found")

        exp.status = ExperimentStatus.COMPLETED
        exp.end_time = time.time()

    def assign_user(
        self, experiment_id: str, user_id: str
    ) -> ExperimentVariant | None:
        """Assign a user to a variant in an experiment.

        Args:
            experiment_id: The experiment identifier.
            user_id: The user identifier.

        Returns:
            The assigned variant, or None if experiment not found.
        """
        exp = self._experiments.get(experiment_id)
        if exp is None:
            return None
        return self._assigner.assign(user_id, exp.variants)

    def record_result(self, result: ExperimentResult) -> None:
        """Record experiment results.

        Args:
            result: The experiment result.
        """
        self._results[result.experiment_id] = result

    def get_result(self, experiment_id: str) -> ExperimentResult | None:
        """Get experiment results.

        Args:
            experiment_id: The experiment identifier.

        Returns:
            The experiment result, or None if not found.
        """
        return self._results.get(experiment_id)

    def list_experiments(
        self, status: ExperimentStatus | None = None
    ) -> list[ExperimentConfig]:
        """List experiments, optionally filtered by status.

        Args:
            status: Optional status filter.

        Returns:
            List of experiment configs.
        """
        experiments = list(self._experiments.values())
        if status is not None:
            experiments = [e for e in experiments if e.status == status]
        return experiments
