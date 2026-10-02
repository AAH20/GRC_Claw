"""Optimization data models — Pydantic schemas for optimization, forecasting, and A/B testing."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ─── Optimization Models ─────────────────────────────────────────────


class OptimizationStrategy(StrEnum):
    """Optimization strategy types."""

    MULTI_ARMED_BANDIT = "multi_armed_bandit"
    BAYESIAN = "bayesian"
    GRID_SEARCH = "grid_search"
    GENETIC = "genetic"


class BanditAlgorithm(StrEnum):
    """Multi-armed bandit algorithm variants."""

    EPSILON_GREEDY = "epsilon_greedy"
    UCB1 = "ucb1"
    THOMPSON_SAMPLING = "thompson_sampling"
    SOFTMAX = "softmax"


class ArmConfig(BaseModel):
    """Configuration for a single bandit arm."""

    arm_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    initial_reward: float = Field(default=0.0)
    initial_pulls: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BanditConfig(BaseModel):
    """Configuration for multi-armed bandit optimization."""

    algorithm: BanditAlgorithm = Field(default=BanditAlgorithm.UCB1)
    epsilon: float = Field(default=0.1, ge=0.0, le=1.0)
    exploration_factor: float = Field(default=1.414, gt=0.0)
    temperature: float = Field(default=1.0, gt=0.0)
    arms: list[ArmConfig] = Field(..., min_length=2)
    reward_metric: str = Field(default="conversion_rate")
    min_pulls_before_exploit: int = Field(default=10, ge=0)


class BanditState(BaseModel):
    """Current state of a bandit arm."""

    arm_id: str
    pulls: int = Field(default=0, ge=0)
    total_reward: float = Field(default=0.0)
    mean_reward: float = Field(default=0.0)
    ucb_score: float = Field(default=0.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class BanditResult(BaseModel):
    """Result of a bandit optimization round."""

    selected_arm: str
    exploration: bool
    arm_states: list[BanditState]
    total_pulls: int
    total_reward: float
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class OptimizationRecommendation(BaseModel):
    """A single optimization recommendation."""

    recommendation_id: str
    category: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    current_value: float | None = None
    recommended_value: float | None = None
    expected_improvement: float = Field(default=0.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning: str = ""
    priority: int = Field(default=5, ge=1, le=10)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OptimizationResult(BaseModel):
    """Complete optimization result."""

    campaign_id: str
    strategy: OptimizationStrategy
    recommendations: list[OptimizationRecommendation]
    bandit_result: BanditResult | None = None
    metrics_before: dict[str, float] = Field(default_factory=dict)
    metrics_after: dict[str, float] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ─── Forecasting Models ──────────────────────────────────────────────


class ForecastGranularity(StrEnum):
    """Time granularity for forecasts."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ForecastMethod(StrEnum):
    """Forecasting method types."""

    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_REGRESSION = "linear_regression"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    ARIMA = "arima"


class TimeSeriesPoint(BaseModel):
    """A single time-series data point."""

    timestamp: str
    value: float = Field(..., ge=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ForecastConfig(BaseModel):
    """Configuration for time-series forecasting."""

    method: ForecastMethod = Field(default=ForecastMethod.EXPONENTIAL_SMOOTHING)
    granularity: ForecastGranularity = Field(default=ForecastGranularity.DAILY)
    horizon: int = Field(default=7, ge=1, le=365)
    seasonality_period: int | None = Field(default=None, ge=1)
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)
    smoothing_alpha: float = Field(default=0.3, ge=0.0, le=1.0)
    smoothing_beta: float = Field(default=0.1, ge=0.0, le=1.0)
    smoothing_gamma: float = Field(default=0.1, ge=0.0, le=1.0)


class ForecastPoint(BaseModel):
    """A single forecast data point."""

    timestamp: str
    value: float
    lower_bound: float
    upper_bound: float
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)


class ForecastResult(BaseModel):
    """Complete forecast result."""

    campaign_id: str
    metric: str
    method: ForecastMethod
    granularity: ForecastGranularity
    historical_points: int
    forecast_points: list[ForecastPoint]
    mape: float | None = None
    rmse: float | None = None
    trend_direction: str = Field(default="stable")
    seasonality_detected: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ─── Creative A/B Testing Models ─────────────────────────────────────


class CreativeVariant(BaseModel):
    """A creative variant for A/B testing."""

    variant_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    creative_type: str = Field(..., min_length=1)
    content: dict[str, Any] = Field(default_factory=dict)
    impressions: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    conversions: int = Field(default=0, ge=0)
    spend: float = Field(default=0.0, ge=0.0)
    weight: float = Field(default=1.0, gt=0.0)


class ABTestConfig(BaseModel):
    """Configuration for creative A/B testing."""

    test_id: str = Field(..., min_length=1, max_length=100)
    campaign_id: str = Field(..., min_length=1)
    variants: list[CreativeVariant] = Field(..., min_length=2)
    primary_metric: str = Field(default="ctr")
    secondary_metrics: list[str] = Field(default_factory=list)
    min_sample_size: int = Field(default=1000, ge=100)
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)
    max_duration_days: int = Field(default=14, ge=1, le=90)
    auto_winner_selection: bool = True


class ABTestResult(BaseModel):
    """Result of an A/B test."""

    test_id: str
    campaign_id: str
    winner_variant_id: str | None = None
    is_significant: bool = False
    p_value: float | None = None
    confidence_level: float = Field(default=0.95, ge=0.0, le=1.0)
    variant_results: list[dict[str, Any]] = Field(default_factory=list)
    recommendation: str = ""
    test_duration_days: int = 0
    total_impressions: int = 0
    total_conversions: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class CreativeOptimizationResult(BaseModel):
    """Complete creative optimization result."""

    campaign_id: str
    ab_test: ABTestResult
    winning_variants: list[str] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    next_test_recommendations: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
