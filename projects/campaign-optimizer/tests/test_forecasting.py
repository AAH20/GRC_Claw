"""Tests for time-series forecasting agent."""
from __future__ import annotations

import math
from datetime import datetime, timedelta

import pytest

from campaign_agents.agents.forecaster import TimeSeriesForecaster
from campaign_agents.models.optimization import (
    ForecastConfig,
    ForecastGranularity,
    ForecastMethod,
    ForecastPoint,
    ForecastResult,
    TimeSeriesPoint,
)


# ─── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def basic_forecast_config() -> ForecastConfig:
    """Create a basic forecast configuration."""
    return ForecastConfig(
        method=ForecastMethod.EXPONENTIAL_SMOOTHING,
        granularity=ForecastGranularity.DAILY,
        horizon=7,
        confidence_level=0.95,
        smoothing_alpha=0.3,
        smoothing_beta=0.1,
    )


@pytest.fixture
def sample_time_series() -> list[TimeSeriesPoint]:
    """Create sample time-series data."""
    base_time = datetime(2024, 1, 1)
    points = []
    for i in range(30):
        # Simulate daily conversions with upward trend
        value = 10 + i * 0.5 + (i % 7) * 2  # Trend + weekly seasonality
        points.append(
            TimeSeriesPoint(
                timestamp=(base_time + timedelta(days=i)).isoformat(),
                value=float(value),
            )
        )
    return points


@pytest.fixture
def forecaster_with_data(basic_forecast_config: ForecastConfig, sample_time_series: list[TimeSeriesPoint]) -> TimeSeriesForecaster:
    """Create a forecaster with sample data loaded."""
    forecaster = TimeSeriesForecaster(basic_forecast_config)
    forecaster.add_data_points(sample_time_series)
    return forecaster


# ─── Initialization Tests ───────────────────────────────────────────


class TestForecasterInit:
    """Tests for forecaster initialization."""

    def test_init_with_exponential_smoothing(self, basic_forecast_config: ForecastConfig) -> None:
        """Test initialization with exponential smoothing."""
        forecaster = TimeSeriesForecaster(basic_forecast_config)
        assert forecaster.config.method == ForecastMethod.EXPONENTIAL_SMOOTHING
        assert forecaster.config.horizon == 7

    def test_init_with_moving_average(self) -> None:
        """Test initialization with moving average."""
        config = ForecastConfig(method=ForecastMethod.MOVING_AVERAGE, horizon=14)
        forecaster = TimeSeriesForecaster(config)
        assert forecaster.config.method == ForecastMethod.MOVING_AVERAGE
        assert forecaster.config.horizon == 14

    def test_init_with_linear_regression(self) -> None:
        """Test initialization with linear regression."""
        config = ForecastConfig(method=ForecastMethod.LINEAR_REGRESSION, horizon=30)
        forecaster = TimeSeriesForecaster(config)
        assert forecaster.config.method == ForecastMethod.LINEAR_REGRESSION

    def test_init_with_seasonal_decomposition(self) -> None:
        """Test initialization with seasonal decomposition."""
        config = ForecastConfig(
            method=ForecastMethod.SEASONAL_DECOMPOSITION,
            seasonality_period=7,
        )
        forecaster = TimeSeriesForecaster(config)
        assert forecaster.config.method == ForecastMethod.SEASONAL_DECOMPOSITION
        assert forecaster.config.seasonality_period == 7

    def test_init_invalid_horizon_raises(self) -> None:
        """Test that invalid horizon raises ValueError."""
        with pytest.raises(ValueError, match="Horizon must be at least 1"):
            ForecastConfig(method=ForecastMethod.MOVING_AVERAGE, horizon=0)

    def test_init_invalid_confidence_raises(self) -> None:
        """Test that invalid confidence level raises ValueError."""
        with pytest.raises(ValueError, match="Confidence level must be between 0 and 1"):
            ForecastConfig(confidence_level=1.5)

    def test_init_invalid_alpha_raises(self) -> None:
        """Test that invalid smoothing alpha raises ValueError."""
        with pytest.raises(ValueError, match="Smoothing alpha must be between 0 and 1"):
            ForecastConfig(smoothing_alpha=1.5)


# ─── Data Management Tests ──────────────────────────────────────────


class TestDataManagement:
    """Tests for data management."""

    def test_add_single_data_point(self, basic_forecast_config: ForecastConfig) -> None:
        """Test adding a single data point."""
        forecaster = TimeSeriesForecaster(basic_forecast_config)
        point = TimeSeriesPoint(timestamp="2024-01-01T00:00:00", value=10.0)
        forecaster.add_data_point(point)
        assert len(forecaster.get_historical_data()) == 1

    def test_add_multiple_data_points(self, basic_forecast_config: ForecastConfig) -> None:
        """Test adding multiple data points."""
        forecaster = TimeSeriesForecaster(basic_forecast_config)
        points = [
            TimeSeriesPoint(timestamp="2024-01-01T00:00:00", value=10.0),
            TimeSeriesPoint(timestamp="2024-01-02T00:00:00", value=12.0),
            TimeSeriesPoint(timestamp="2024-01-03T00:00:00", value=11.0),
        ]
        forecaster.add_data_points(points)
        assert len(forecaster.get_historical_data()) == 3

    def test_data_points_sorted_by_timestamp(self, basic_forecast_config: ForecastConfig) -> None:
        """Test that data points are sorted by timestamp."""
        forecaster = TimeSeriesForecaster(basic_forecast_config)
        points = [
            TimeSeriesPoint(timestamp="2024-01-03T00:00:00", value=11.0),
            TimeSeriesPoint(timestamp="2024-01-01T00:00:00", value=10.0),
            TimeSeriesPoint(timestamp="2024-01-02T00:00:00", value=12.0),
        ]
        forecaster.add_data_points(points)
        data = forecaster.get_historical_data()
        assert data[0].timestamp == "2024-01-01T00:00:00"
        assert data[1].timestamp == "2024-01-02T00:00:00"
        assert data[2].timestamp == "2024-01-03T00:00:00"

    def test_clear_data(self, forecaster_with_data: TimeSeriesForecaster) -> None:
        """Test clearing all data."""
        forecaster_with_data.clear_data()
        assert len(forecaster_with_data.get_historical_data()) == 0
        assert len(forecaster_with_data.get_forecast_history()) == 0


# ─── Forecasting Method Tests ───────────────────────────────────────


class TestForecastingMethods:
    """Tests for different forecasting methods."""

    def test_exponential_smoothing_forecast(self, forecaster_with_data: TimeSeriesForecaster) -> None:
        """Test exponential smoothing forecast."""
        result = forecaster_with_data.forecast("campaign_123", "conversions")
        assert isinstance(result, ForecastResult)
        assert result.method == ForecastMethod.EXPONENTIAL_SMOOTHING
        assert len(result.forecast_points) == 7

    def test_moving_average_forecast(self, sample_time_series: list[TimeSeriesPoint]) -> None:
        """Test moving average forecast."""
        config = ForecastConfig(method=ForecastMethod.MOVING_AVERAGE, horizon=5)
        forecaster = TimeSeriesForecaster(config)
        forecaster.add_data_points(sample_time_series)
        result = forecaster.forecast("campaign_123", "conversions")
        assert result.method == ForecastMethod.MOVING_AVERAGE
        assert len(result.forecast_points) == 5

    def test_linear_regression_forecast(self, sample_time_series: list[TimeSeriesPoint]) -> None:
        """Test linear regression forecast."""
        config = ForecastConfig(method=ForecastMethod.LINEAR_REGRESSION, horizon=10)
        forecaster = TimeSeriesForecaster(config)
        forecaster.add_data_points(sample_time_series)
        result = forecaster.forecast("campaign_123", "conversions")
        assert result.method == ForecastMethod.LINEAR_REGRESSION
        assert len(result.forecast_points) == 10

    def test_seasonal_decomposition_forecast(self, sample_time_series: list[TimeSeriesPoint]) -> None:
        """Test seasonal decomposition forecast."""
        config = ForecastConfig(
            method=ForecastMethod.SEASONAL_DECOMPOSITION,
            seasonality_period=7,
            horizon=14,
        )
        forecaster = TimeSeriesForecaster(config)
        forecaster.add_data_points(sample_time_series)
        result = forecaster.forecast("campaign_123", "conversions")
        assert result.method == ForecastMethod.SEASONAL_DECOMPOSITION
        assert len(result.forecast_points) == 14

    def test_forecast_with_insufficient_data_raises(self, basic_forecast_config: ForecastConfig) -> None:
        """Test that forecasting with insufficient data raises ValueError."""
        forecaster = TimeSeriesForecaster(basic_forecast_config)
        forecaster.add_data_point(TimeSeriesPoint(timestamp="2024-01-01T00:00:00", value=10.0))
        with pytest.raises(ValueError, match="Need at least 3 data points"):
            forecaster.forecast("campaign_123", "conversions")


# ─── Forecast Result Tests ──────────────────────────────────────────


class TestForecastResults:
    """Tests for forecast result properties."""

    def test_forecast_points_have_confidence_intervals(self, forecaster_with_data: TimeSeriesForecaster) -> None:
        """Test that forecast points include confidence intervals."""
        result = forecaster_with_data.forecast("campaign_123", "conversions")
        for point in result.forecast_points:
            assert isinstance(point, ForecastPoint)
            assert point.lower_bound <= point.value <= point.upper_bound
            assert point.confidence == 0.95

    def test_forecast_timestamps_are_future(self, forecaster_with_data: TimeSeriesForecaster) -> None:
        """Test that forecast timestamps are in the future."""
        result = forecaster_with_data.forecast("campaign_123", "conversions")
        last_historical = datetime.fromisoformat(forecaster_with_data.get_historical_data()[-1].timestamp)
        for point in result.forecast_points:
            forecast_time = datetime.fromisoformat(point.timestamp)
            assert forecast_time > last_historical

    def test_forecast_values_are_non_negative(self, forecaster_with_data: TimeSeriesForecaster) -> None:
        """Test that forecast values are non-negative."""
        result = forecaster_with_data.forecast("campaign_123", "conversions")
        for point in result.forecast_points:
            assert point.value >= 0.0
            assert point.lower_bound >= 0.0

    def test_forecast_includes_metrics(self, forecaster_with_data: TimeSeriesForecaster) -> None:
        """Test that forecast includes accuracy metrics."""
        result = forecaster_with_data.forecast("campaign_123", "conversions")
        assert result.mape is not None or result.rmse is not None

    def test_forecast_detects_trend(self, forecaster_with_data: TimeSeriesForecaster) -> None:
        """Test that forecast detects trend direction."""
        result = forecaster_with_data.forecast("campaign_123", "conversions")
        assert result.trend_direction in ("increasing", "decreasing", "stable")

    def test_forecast_history_tracked(self, forecaster_with_data: TimeSeriesForecaster) -> None:
        """Test that forecast history is tracked."""
        assert len(forecaster_with_data.get_forecast_history()) == 0
        forecaster_with_data.forecast("campaign_123", "conversions")
        assert len(forecaster_with_data.get_forecast_history()) == 1
        forecaster_with_data.forecast("campaign_123", "conversions")
        assert len(forecaster_with_data.get_forecast_history()) == 2


# ─── Granularity Tests ──────────────────────────────────────────────


class TestGranularity:
    """Tests for different time granularities."""

    def test_hourly_forecast(self, sample_time_series: list[TimeSeriesPoint]) -> None:
        """Test hourly granularity forecast."""
        config = ForecastConfig(
            method=ForecastMethod.MOVING_AVERAGE,
            granularity=ForecastGranularity.HOURLY,
            horizon=24,
        )
        forecaster = TimeSeriesForecaster(config)
        forecaster.add_data_points(sample_time_series)
        result = forecaster.forecast("campaign_123", "conversions")
        assert result.granularity == ForecastGranularity.HOURLY
        assert len(result.forecast_points) == 24

    def test_weekly_forecast(self, sample_time_series: list[TimeSeriesPoint]) -> None:
        """Test weekly granularity forecast."""
        config = ForecastConfig(
            method=ForecastMethod.MOVING_AVERAGE,
            granularity=ForecastGranularity.WEEKLY,
            horizon=4,
        )
        forecaster = TimeSeriesForecaster(config)
        forecaster.add_data_points(sample_time_series)
        result = forecaster.forecast("campaign_123", "conversions")
        assert result.granularity == ForecastGranularity.WEEKLY
        assert len(result.forecast_points) == 4

    def test_monthly_forecast(self, sample_time_series: list[TimeSeriesPoint]) -> None:
        """Test monthly granularity forecast."""
        config = ForecastConfig(
            method=ForecastMethod.MOVING_AVERAGE,
            granularity=ForecastGranularity.MONTHLY,
            horizon=3,
        )
        forecaster = TimeSeriesForecaster(config)
        forecaster.add_data_points(sample_time_series)
        result = forecaster.forecast("campaign_123", "conversions")
        assert result.granularity == ForecastGranularity.MONTHLY
        assert len(result.forecast_points) == 3


# ─── Edge Cases ─────────────────────────────────────────────────────


class TestEdgeCases:
    """Tests for edge cases."""

    def test_forecast_with_constant_values(self, basic_forecast_config: ForecastConfig) -> None:
        """Test forecasting with constant values."""
        forecaster = TimeSeriesForecaster(basic_forecast_config)
        base_time = datetime(2024, 1, 1)
        for i in range(10):
            forecaster.add_data_point(
                TimeSeriesPoint(
                    timestamp=(base_time + timedelta(days=i)).isoformat(),
                    value=10.0,
                )
            )
        result = forecaster.forecast("campaign_123", "conversions")
        assert result.trend_direction == "stable"

    def test_forecast_with_declining_trend(self, basic_forecast_config: ForecastConfig) -> None:
        """Test forecasting with declining trend."""
        forecaster = TimeSeriesForecaster(basic_forecast_config)
        base_time = datetime(2024, 1, 1)
        for i in range(10):
            forecaster.add_data_point(
                TimeSeriesPoint(
                    timestamp=(base_time + timedelta(days=i)).isoformat(),
                    value=float(20 - i),
                )
            )
        result = forecaster.forecast("campaign_123", "conversions")
        assert result.trend_direction == "decreasing"

    def test_forecast_with_increasing_trend(self, basic_forecast_config: ForecastConfig) -> None:
        """Test forecasting with increasing trend."""
        forecaster = TimeSeriesForecaster(basic_forecast_config)
        base_time = datetime(2024, 1, 1)
        for i in range(10):
            forecaster.add_data_point(
                TimeSeriesPoint(
                    timestamp=(base_time + timedelta(days=i)).isoformat(),
                    value=float(10 + i * 2),
                )
            )
        result = forecaster.forecast("campaign_123", "conversions")
        assert result.trend_direction == "increasing"

    def test_seasonality_detection(self, basic_forecast_config: ForecastConfig) -> None:
        """Test seasonality detection."""
        config = ForecastConfig(
            method=ForecastMethod.SEASONAL_DECOMPOSITION,
            seasonality_period=7,
        )
        forecaster = TimeSeriesForecaster(config)
        base_time = datetime(2024, 1, 1)
        # Create data with clear weekly seasonality
        for i in range(28):
            value = 10 + (i % 7) * 5
            forecaster.add_data_point(
                TimeSeriesPoint(
                    timestamp=(base_time + timedelta(days=i)).isoformat(),
                    value=float(value),
                )
            )
        result = forecaster.forecast("campaign_123", "conversions")
        assert result.seasonality_detected is True

    def test_mape_calculation(self, forecaster_with_data: TimeSeriesForecaster) -> None:
        """Test MAPE calculation."""
        result = forecaster_with_data.forecast("campaign_123", "conversions")
        if result.mape is not None:
            assert result.mape >= 0.0

    def test_rmse_calculation(self, forecaster_with_data: TimeSeriesForecaster) -> None:
        """Test RMSE calculation."""
        result = forecaster_with_data.forecast("campaign_123", "conversions")
        if result.rmse is not None:
            assert result.rmse >= 0.0
