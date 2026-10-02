"""
Budget Forecasting for GRC_Claw.

Provides cost forecasting using multiple methods:
- Linear regression
- Moving average
- Exponential smoothing
- Seasonal decomposition
- Monte Carlo simulation
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass, field

from .models import (
    BudgetForecast,
    CostCategory,
    CostLineItem,
    ForecastMethod,
)


@dataclass
class ForecastConfig:
    """Configuration for budget forecasting."""

    method: ForecastMethod = ForecastMethod.LINEAR_REGRESSION
    forecast_periods: int = 12
    confidence_level: float = 0.95
    seasonality_period: int = 12
    smoothing_alpha: float = 0.3
    smoothing_beta: float = 0.1
    monte_carlo_simulations: int = 1000
    include_growth_rate: bool = True
    growth_rate: float = 0.02


@dataclass
class HistoricalCost:
    """Historical cost data point."""

    period: str = ""
    amount: float = 0.0
    category: CostCategory = CostCategory.OTHER
    metadata: dict = field(default_factory=dict)


@dataclass
class ForecastSummary:
    """Summary of budget forecasts."""

    method: ForecastMethod = ForecastMethod.LINEAR_REGRESSION
    forecast_periods: int = 0
    total_forecasted: float = 0.0
    avg_monthly: float = 0.0
    min_monthly: float = 0.0
    max_monthly: float = 0.0
    growth_rate: float = 0.0
    confidence_interval: float = 0.95
    forecasts: list[BudgetForecast] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)


class BudgetForecaster:
    """
    Forecasts future costs using multiple statistical methods.

    Supports:
    - Linear regression for trend-based forecasting
    - Moving average for stable cost patterns
    - Exponential smoothing for recent-trend emphasis
    - Seasonal decomposition for periodic patterns
    - Monte Carlo simulation for risk analysis
    """

    def __init__(self, config: ForecastConfig | None = None):
        self.config = config or ForecastConfig()
        self.historical_data: list[HistoricalCost] = []
        self.line_items: list[CostLineItem] = []
        self.forecasts: list[BudgetForecast] = []

    def add_historical_data(self, data: HistoricalCost) -> None:
        """Add a historical cost data point."""
        self.historical_data.append(data)

    def add_line_item(self, item: CostLineItem) -> None:
        """Add a cost line item."""
        self.line_items.append(item)

    def load_historical_costs(self, costs: list[HistoricalCost]) -> None:
        """Load multiple historical cost data points."""
        self.historical_data.extend(costs)

    def forecast(self, periods: int | None = None) -> list[BudgetForecast]:
        """
        Generate cost forecasts for future periods.

        Args:
            periods: Number of periods to forecast (overrides config).

        Returns:
            List of BudgetForecast objects.
        """
        n_periods = periods or self.config.forecast_periods

        if self.config.method == ForecastMethod.LINEAR_REGRESSION:
            self.forecasts = self._linear_regression_forecast(n_periods)
        elif self.config.method == ForecastMethod.MOVING_AVERAGE:
            self.forecasts = self._moving_average_forecast(n_periods)
        elif self.config.method == ForecastMethod.EXPONENTIAL_SMOOTHING:
            self.forecasts = self._exponential_smoothing_forecast(n_periods)
        elif self.config.method == ForecastMethod.SEASONAL_DECOMPOSITION:
            self.forecasts = self._seasonal_decomposition_forecast(n_periods)
        elif self.config.method == ForecastMethod.MONTE_CARLO:
            self.forecasts = self._monte_carlo_forecast(n_periods)
        else:
            self.forecasts = self._linear_regression_forecast(n_periods)

        return self.forecasts

    def _linear_regression_forecast(self, periods: int) -> list[BudgetForecast]:
        """Forecast using linear regression."""
        if len(self.historical_data) < 2:
            return self._naive_forecast(periods)

        costs = [h.amount for h in self.historical_data]
        n = len(costs)

        # Calculate linear regression coefficients
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(costs)

        numerator = sum((i - x_mean) * (costs[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean

        # Calculate standard error
        residuals = [costs[i] - (intercept + slope * i) for i in range(n)]
        mse = sum(r ** 2 for r in residuals) / max(1, n - 2)
        std_error = math.sqrt(mse)

        # Z-score for confidence interval
        z_score = 1.96 if self.config.confidence_level == 0.95 else 1.645

        forecasts = []
        for i in range(periods):
            x = n + i
            predicted = intercept + slope * x

            if self.config.include_growth_rate:
                predicted *= (1 + self.config.growth_rate) ** i

            margin = z_score * std_error * math.sqrt(1 + 1 / n + (x - x_mean) ** 2 / denominator) if denominator > 0 else z_score * std_error

            forecasts.append(
                BudgetForecast(
                    period=f"forecast_{i+1}",
                    method=ForecastMethod.LINEAR_REGRESSION,
                    forecasted_cost=round(predicted, 2),
                    lower_bound=round(max(0, predicted - margin), 2),
                    upper_bound=round(predicted + margin, 2),
                    confidence_interval=self.config.confidence_level,
                    growth_rate=slope / y_mean if y_mean > 0 else 0,
                    assumptions=[
                        f"Linear trend with slope {slope:.2f}",
                        f"Confidence level {self.config.confidence_level * 100:.0f}%",
                    ],
                )
            )

        return forecasts

    def _moving_average_forecast(self, periods: int) -> list[BudgetForecast]:
        """Forecast using moving average."""
        if not self.historical_data:
            return self._naive_forecast(periods)

        costs = [h.amount for h in self.historical_data]
        window = min(self.config.seasonality_period, len(costs))

        recent_avg = statistics.mean(costs[-window:])
        std_dev = statistics.stdev(costs[-window:]) if len(costs[-window:]) > 1 else 0

        z_score = 1.96 if self.config.confidence_level == 0.95 else 1.645
        margin = z_score * std_dev / math.sqrt(window) if window > 0 else 0

        forecasts = []
        for i in range(periods):
            predicted = recent_avg

            if self.config.include_growth_rate:
                predicted *= (1 + self.config.growth_rate) ** i

            forecasts.append(
                BudgetForecast(
                    period=f"forecast_{i+1}",
                    method=ForecastMethod.MOVING_AVERAGE,
                    forecasted_cost=round(predicted, 2),
                    lower_bound=round(max(0, predicted - margin), 2),
                    upper_bound=round(predicted + margin, 2),
                    confidence_interval=self.config.confidence_level,
                    growth_rate=0,
                    assumptions=[
                        f"Moving average over {window} periods",
                        f"Confidence level {self.config.confidence_level * 100:.0f}%",
                    ],
                )
            )

        return forecasts

    def _exponential_smoothing_forecast(self, periods: int) -> list[BudgetForecast]:
        """Forecast using Holt's exponential smoothing."""
        if len(self.historical_data) < 2:
            return self._naive_forecast(periods)

        costs = [h.amount for h in self.historical_data]
        alpha = self.config.smoothing_alpha
        beta = self.config.smoothing_beta

        # Initialize
        level = costs[0]
        trend = costs[1] - costs[0] if len(costs) > 1 else 0

        # Apply smoothing
        for i in range(1, len(costs)):
            prev_level = level
            level = alpha * costs[i] + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend

        # Calculate prediction interval
        residuals = []
        l, t = costs[0], costs[1] - costs[0] if len(costs) > 1 else 0
        for i in range(1, len(costs)):
            pred = l + t
            residuals.append(costs[i] - pred)
            prev_l = l
            l = alpha * costs[i] + (1 - alpha) * (l + t)
            t = beta * (l - prev_l) + (1 - beta) * t

        mse = sum(r ** 2 for r in residuals) / max(1, len(residuals))
        std_error = math.sqrt(mse)

        z_score = 1.96 if self.config.confidence_level == 0.95 else 1.645

        forecasts = []
        for i in range(periods):
            predicted = level + (i + 1) * trend

            if self.config.include_growth_rate:
                predicted *= (1 + self.config.growth_rate) ** i

            margin = z_score * std_error * math.sqrt(1 + (i + 1) * alpha ** 2)

            forecasts.append(
                BudgetForecast(
                    period=f"forecast_{i+1}",
                    method=ForecastMethod.EXPONENTIAL_SMOOTHING,
                    forecasted_cost=round(predicted, 2),
                    lower_bound=round(max(0, predicted - margin), 2),
                    upper_bound=round(predicted + margin, 2),
                    confidence_interval=self.config.confidence_level,
                    growth_rate=trend / level if level > 0 else 0,
                    assumptions=[
                        f"Exponential smoothing (alpha={alpha}, beta={beta})",
                        f"Confidence level {self.config.confidence_level * 100:.0f}%",
                    ],
                )
            )

        return forecasts

    def _seasonal_decomposition_forecast(self, periods: int) -> list[BudgetForecast]:
        """Forecast using seasonal decomposition."""
        if len(self.historical_data) < self.config.seasonality_period * 2:
            return self._linear_regression_forecast(periods)

        costs = [h.amount for h in self.historical_data]
        period = self.config.seasonality_period

        # Calculate seasonal indices
        seasonal_indices = []
        for i in range(period):
            values = [costs[j] for j in range(i, len(costs), period)]
            seasonal_indices.append(statistics.mean(values) if values else 1)

        overall_mean = statistics.mean(costs)
        seasonal_indices = [s / overall_mean for s in seasonal_indices]

        # Deseasonalize
        deseasonalized = [
            costs[i] / seasonal_indices[i % period]
            for i in range(len(costs))
        ]

        # Fit linear trend on deseasonalized data
        n = len(deseasonalized)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(deseasonalized)

        numerator = sum((i - x_mean) * (deseasonalized[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean

        # Forecast
        forecasts = []
        for i in range(periods):
            x = n + i
            trend_value = intercept + slope * x
            seasonal_factor = seasonal_indices[x % period]
            predicted = trend_value * seasonal_factor

            if self.config.include_growth_rate:
                predicted *= (1 + self.config.growth_rate) ** i

            # Approximate confidence interval
            std_dev = statistics.stdev(costs) if len(costs) > 1 else 0
            z_score = 1.96 if self.config.confidence_level == 0.95 else 1.645
            margin = z_score * std_dev

            forecasts.append(
                BudgetForecast(
                    period=f"forecast_{i+1}",
                    method=ForecastMethod.SEASONAL_DECOMPOSITION,
                    forecasted_cost=round(predicted, 2),
                    lower_bound=round(max(0, predicted - margin), 2),
                    upper_bound=round(predicted + margin, 2),
                    confidence_interval=self.config.confidence_level,
                    growth_rate=slope / y_mean if y_mean > 0 else 0,
                    seasonality_factor=round(seasonal_factor, 4),
                    assumptions=[
                        f"Seasonal period: {period}",
                        f"Confidence level {self.config.confidence_level * 100:.0f}%",
                    ],
                )
            )

        return forecasts

    def _monte_carlo_forecast(self, periods: int) -> list[BudgetForecast]:
        """Forecast using Monte Carlo simulation."""
        if len(self.historical_data) < 2:
            return self._naive_forecast(periods)

        costs = [h.amount for h in self.historical_data]
        mean = statistics.mean(costs)
        std_dev = statistics.stdev(costs) if len(costs) > 1 else 0

        # Calculate trend
        n = len(costs)
        x_mean = (n - 1) / 2
        numerator = sum((i - x_mean) * (costs[i] - mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0

        simulations = self.config.monte_carlo_simulations
        forecasts = []

        for i in range(periods):
            simulated_costs = []
            for _ in range(simulations):
                # Random walk with trend
                random_shock = random.gauss(0, std_dev)
                predicted = mean + slope * (n + i) + random_shock

                if self.config.include_growth_rate:
                    predicted *= (1 + self.config.growth_rate) ** i

                simulated_costs.append(max(0, predicted))

            simulated_costs.sort()
            forecasted = statistics.mean(simulated_costs)

            # Confidence interval from percentiles
            alpha = 1 - self.config.confidence_level
            lower_idx = int(simulations * alpha / 2)
            upper_idx = int(simulations * (1 - alpha / 2))

            forecasts.append(
                BudgetForecast(
                    period=f"forecast_{i+1}",
                    method=ForecastMethod.MONTE_CARLO,
                    forecasted_cost=round(forecasted, 2),
                    lower_bound=round(simulated_costs[lower_idx], 2),
                    upper_bound=round(simulated_costs[upper_idx], 2),
                    confidence_interval=self.config.confidence_level,
                    growth_rate=slope / mean if mean > 0 else 0,
                    assumptions=[
                        f"Monte Carlo with {simulations} simulations",
                        f"Confidence level {self.config.confidence_level * 100:.0f}%",
                    ],
                    risk_factors=[
                        "Market price volatility",
                        "Usage pattern changes",
                        "Unexpected incidents",
                    ],
                )
            )

        return forecasts

    def _naive_forecast(self, periods: int) -> list[BudgetForecast]:
        """Naive forecast using last known value."""
        if not self.historical_data:
            return []

        last_value = self.historical_data[-1].amount

        forecasts = []
        for i in range(periods):
            predicted = last_value

            if self.config.include_growth_rate:
                predicted *= (1 + self.config.growth_rate) ** i

            forecasts.append(
                BudgetForecast(
                    period=f"forecast_{i+1}",
                    method=self.config.method,
                    forecasted_cost=round(predicted, 2),
                    lower_bound=round(predicted * 0.9, 2),
                    upper_bound=round(predicted * 1.1, 2),
                    confidence_interval=self.config.confidence_level,
                    growth_rate=self.config.growth_rate,
                    assumptions=["Naive forecast (insufficient historical data)"],
                )
            )

        return forecasts

    def get_forecast_summary(self) -> ForecastSummary:
        """
        Get summary of budget forecasts.

        Returns:
            ForecastSummary with aggregated metrics.
        """
        if not self.forecasts:
            self.forecast()

        if not self.forecasts:
            return ForecastSummary()

        total = sum(f.forecasted_cost for f in self.forecasts)
        avg = total / len(self.forecasts)
        min_cost = min(f.forecasted_cost for f in self.forecasts)
        max_cost = max(f.forecasted_cost for f in self.forecasts)

        # Calculate overall growth rate
        if len(self.forecasts) >= 2 and self.forecasts[0].forecasted_cost > 0:
            growth = (
                (self.forecasts[-1].forecasted_cost / self.forecasts[0].forecasted_cost)
                ** (1 / len(self.forecasts))
                - 1
            )
        else:
            growth = 0

        # Collect risk factors
        risk_factors = set()
        for f in self.forecasts:
            risk_factors.update(f.risk_factors)

        # Collect assumptions
        assumptions = set()
        for f in self.forecasts:
            assumptions.update(f.assumptions)

        return ForecastSummary(
            method=self.config.method,
            forecast_periods=len(self.forecasts),
            total_forecasted=round(total, 2),
            avg_monthly=round(avg, 2),
            min_monthly=round(min_cost, 2),
            max_monthly=round(max_cost, 2),
            growth_rate=round(growth, 4),
            confidence_interval=self.config.confidence_level,
            forecasts=list(self.forecasts),
            risk_factors=list(risk_factors),
            assumptions=list(assumptions),
        )

    def compare_methods(self, periods: int = 12) -> dict[str, ForecastSummary]:
        """
        Compare forecasts from all available methods.

        Args:
            periods: Number of periods to forecast.

        Returns:
            Dictionary mapping method name to ForecastSummary.
        """
        results = {}
        original_method = self.config.method

        for method in ForecastMethod:
            self.config.method = method
            self.forecast(periods)
            results[method.value] = self.get_forecast_summary()

        # Restore original method
        self.config.method = original_method
        self.forecast(periods)

        return results

    def get_budget_recommendation(
        self,
        target_periods: int = 12,
        contingency_pct: float = 0.10,
    ) -> dict:
        """
        Get budget recommendation with contingency.

        Args:
            target_periods: Number of periods to budget for.
            contingency_pct: Contingency percentage (e.g. 0.10 = 10%).

        Returns:
            Dictionary with budget recommendation.
        """
        if not self.forecasts or len(self.forecasts) < target_periods:
            self.forecast(target_periods)

        base_budget = sum(f.forecasted_cost for f in self.forecasts[:target_periods])
        upper_bound = sum(f.upper_bound for f in self.forecasts[:target_periods])
        contingency = base_budget * contingency_pct

        return {
            "base_budget": round(base_budget, 2),
            "contingency": round(contingency, 2),
            "recommended_budget": round(base_budget + contingency, 2),
            "upper_bound": round(upper_bound, 2),
            "confidence_interval": self.config.confidence_level,
            "periods": target_periods,
            "method": self.config.method.value,
        }
