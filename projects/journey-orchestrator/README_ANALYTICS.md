# Journey Orchestrator — Analytics Guide

## Overview

The Journey Orchestrator analytics module provides comprehensive performance measurement, optimization recommendations, and Monte Carlo simulation capabilities for customer journeys. This guide covers the architecture, API endpoints, agent usage, and best practices.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Journey Orchestrator                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Analytics   │  │ Optimization │  │  Simulation  │     │
│  │    Agent     │  │    Agent     │  │    Agent     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│  ┌──────┴─────────────────┴─────────────────┴───────┐     │
│  │              Models (Pydantic)                    │     │
│  │  JourneyMetric, JourneyPerformance, FunnelStage  │     │
│  │  CohortAnalysis, AnalyticsSummary                │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │              API Routes (FastAPI)                  │     │
│  │  /api/v1/analytics  /api/v1/optimization         │     │
│  └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Journey Analytics Agent

**Location:** `src/journey_orchestrator/agents/journey_analytics.py`

Computes performance metrics, funnel analysis, cohort tracking, and generates actionable insights.

#### Key Classes

| Class | Description |
|-------|-------------|
| `JourneyAnalytics` | Main agent class for computing analytics |
| `AnalyticsRequest` | Request model for analytics computation |
| `AnalyticsReport` | Complete analytics report with insights |
| `AnalyticsInsight` | Single actionable insight |

#### Usage

```python
from journey_orchestrator.agents.journey_analytics import (
    AnalyticsRequest, JourneyAnalytics
)
from journey_orchestrator.models.analytics import MetricType

agent = JourneyAnalytics()
request = AnalyticsRequest(
    journey_id="journey_123",
    metrics=[
        MetricType.CONVERSION_RATE,
        MetricType.ENGAGEMENT_RATE,
        MetricType.REVENUE_PER_CUSTOMER,
    ],
    include_funnel=True,
    include_cohorts=True,
)
report = await agent.analyze(request)

print(f"Conversion Rate: {report.performance.conversion_rate:.1%}")
print(f"Engagement Rate: {report.performance.engagement_rate:.1%}")
print(f"Revenue/Customer: ${report.performance.revenue_per_customer:.2f}")
print(f"Insights: {len(report.insights)}")
for insight in report.insights:
    print(f"  [{insight.severity}] {insight.message}")
```

#### Methods

| Method | Description |
|--------|-------------|
| `analyze(request)` | Compute full analytics report for a journey |
| `compare_journeys(ids, metric)` | Compare performance across journeys |
| `get_summary()` | Get aggregate summary across all journeys |

### 2. Journey Optimization Agent

**Location:** `src/journey_orchestrator/agents/journey_optimization.py`

Recommends and applies journey improvements based on analytics data.

#### Key Classes

| Class | Description |
|-------|-------------|
| `JourneyOptimization` | Main agent class for optimization |
| `OptimizationRequest` | Request model for optimization |
| `OptimizationSuggestion` | Single optimization suggestion |
| `OptimizationResult` | Complete optimization result |

#### Usage

```python
from journey_orchestrator.agents.journey_optimization import (
    JourneyOptimization, OptimizationRequest
)
from journey_orchestrator.models.analytics import MetricType

agent = JourneyOptimization()
request = OptimizationRequest(
    journey_id="journey_123",
    target_metric=MetricType.CONVERSION_RATE,
    optimization_goal="maximize",
    auto_apply=True,
    max_suggestions=5,
)
result = await agent.optimize(request)

print(f"Current: {result.current_value:.1%}")
print(f"Projected: {result.projected_value:.1%}")
print(f"Improvement: +{result.improvement_potential:.1%}")
for s in result.suggestions:
    print(f"  [{s.effort}/{s.risk_level}] {s.title} (+{s.expected_impact:.1%})")
```

#### Methods

| Method | Description |
|--------|-------------|
| `optimize(request)` | Generate optimization suggestions |
| `apply_optimization(journey_id, suggestion_id)` | Apply a specific suggestion |

### 3. Journey Simulation Agent

**Location:** `src/journey_orchestrator/agents/journey_simulation.py`

Runs Monte Carlo simulations to forecast journey outcomes and quantify uncertainty.

#### Key Classes

| Class | Description |
|-------|-------------|
| `JourneySimulation` | Main agent class for simulation |
| `SimulationRequest` | Request model for simulation |
| `SimulationStatistics` | Statistical summary of results |
| `SimulationResult` | Complete simulation result |

#### Usage

```python
from journey_orchestrator.agents.journey_simulation import (
    JourneySimulation, SimulationRequest
)
from journey_orchestrator.models.analytics import MetricType

agent = JourneySimulation()
request = SimulationRequest(
    journey_id="journey_123",
    num_simulations=10000,
    num_customers=5000,
    target_metric=MetricType.CONVERSION_RATE,
    parameters={
        "conversion_prob": 0.15,
        "variance_factor": 0.2,
    },
    random_seed=42,  # For reproducibility
)
result = await agent.simulate(request)

print(f"Expected Conversion: {result.expected_value:.1%}")
print(f"95% CI: [{result.statistics.confidence_interval_low:.1%}, "
      f"{result.statistics.confidence_interval_high:.1%}]")
print(f"Success Probability: {result.success_probability:.1%}")
print(f"Risk of Underperformance: {result.risk_of_underperformance:.1%}")
```

#### Methods

| Method | Description |
|--------|-------------|
| `simulate(request)` | Run Monte Carlo simulation |
| `compare_scenarios(journey_id, scenarios)` | Compare multiple scenarios |

## API Endpoints

### Analytics API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/analytics` | Compute analytics for a journey |
| `GET` | `/api/v1/analytics/summary` | Get aggregate summary |
| `GET` | `/api/v1/analytics/{journey_id}` | Get cached analytics |

#### Example: Compute Analytics

```bash
curl -X POST http://localhost:8000/api/v1/analytics \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "journey_123",
    "metrics": ["conversion_rate", "engagement_rate"],
    "include_funnel": true,
    "include_cohorts": false
  }'
```

**Response:**
```json
{
  "journey_id": "journey_123",
  "conversion_rate": 0.15,
  "engagement_rate": 0.45,
  "revenue_per_customer": 15.0,
  "total_customers": 1000,
  "converted_customers": 150,
  "insights_count": 3,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### Optimization API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/optimization` | Get optimization suggestions |
| `POST` | `/api/v1/optimization/apply` | Apply an optimization |
| `GET` | `/api/v1/optimization/{journey_id}` | Get cached result |

#### Example: Optimize Journey

```bash
curl -X POST http://localhost:8000/api/v1/optimization \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "journey_123",
    "target_metric": "conversion_rate",
    "optimization_goal": "maximize",
    "auto_apply": true,
    "max_suggestions": 5
  }'
```

**Response:**
```json
{
  "journey_id": "journey_123",
  "target_metric": "conversion_rate",
  "current_value": 0.15,
  "projected_value": 0.22,
  "improvement_potential": 0.07,
  "suggestions_count": 4,
  "applied_count": 2,
  "requires_approval_count": 2,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

#### Example: Apply Optimization

```bash
curl -X POST http://localhost:8000/api/v1/optimization/apply \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "journey_123",
    "suggestion_id": "journey_123_conv_1"
  }'
```

## Data Models

### Metric Types

| Metric | Description |
|--------|-------------|
| `conversion_rate` | Percentage of customers who convert |
| `engagement_rate` | Percentage of customers who engage |
| `open_rate` | Email/push open rate |
| `click_rate` | Click-through rate |
| `revenue_per_customer` | Average revenue per customer |
| `churn_rate` | Customer churn rate |
| `retention_rate` | Customer retention rate |
| `custom` | Custom metric |

### Funnel Stages

The analytics agent computes a standard funnel:
1. **Entered** — Customers who entered the journey
2. **Engaged** — Customers who engaged with content
3. **Converted** — Customers who completed the target action

### Simulation Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `conversion_prob` | 0.15 | Base conversion probability |
| `engagement_prob` | 0.45 | Base engagement probability |
| `revenue_per_conversion` | 50.0 | Revenue per conversion |
| `baseline_rate` | 0.10 | Baseline for success comparison |
| `target_rate` | 0.15 | Target rate for risk calculation |
| `churn_prob` | 0.05 | Customer churn probability |
| `variance_factor` | 0.20 | Noise/variance in simulation |

## Best Practices

### Analytics

1. **Run analytics regularly** — Schedule daily/weekly analytics computation
2. **Use funnel analysis** — Always enable funnel analysis to identify dropoff points
3. **Track cohorts** — Enable cohort analysis for retention insights
4. **Review insights** — Prioritize critical and warning insights

### Optimization

1. **Start with low-effort suggestions** — Apply low-effort, low-risk changes first
2. **A/B test changes** — Use the experimentation agent to validate optimizations
3. **Monitor after applying** — Track metrics after applying changes
4. **Set constraints** — Use budget and timeline constraints to guide suggestions

### Simulation

1. **Use sufficient simulations** — At least 1000 simulations for stable results
2. **Set random seeds** — Use seeds for reproducible results
3. **Compare scenarios** — Use scenario comparison to evaluate options
4. **Consider confidence intervals** — Don't just look at means; check the spread

## Testing

Run the analytics tests:

```bash
# All analytics tests
pytest tests/test_analytics.py -v

# Specific test class
pytest tests/test_analytics.py::TestJourneyAnalyticsAgent -v

# With coverage
pytest tests/test_analytics.py --cov=journey_orchestrator.agents.journey_analytics
```

## Integration Example

```python
from journey_orchestrator.agents.journey_analytics import (
    AnalyticsRequest, JourneyAnalytics
)
from journey_orchestrator.agents.journey_optimization import (
    JourneyOptimization, OptimizationRequest
)
from journey_orchestrator.agents.journey_simulation import (
    JourneySimulation, SimulationRequest
)
from journey_orchestrator.models.analytics import MetricType

async def full_optimization_cycle(journey_id: str):
    # 1. Analyze current performance
    analytics = JourneyAnalytics()
    report = await analytics.analyze(AnalyticsRequest(
        journey_id=journey_id,
        include_funnel=True,
    ))
    print(f"Current conversion: {report.performance.conversion_rate:.1%}")

    # 2. Get optimization suggestions
    optimizer = JourneyOptimization()
    opt_result = await optimizer.optimize(OptimizationRequest(
        journey_id=journey_id,
        target_metric=MetricType.CONVERSION_RATE,
        auto_apply=True,
    ))
    print(f"Projected conversion: {opt_result.projected_value:.1%}")

    # 3. Simulate outcomes
    simulator = JourneySimulation()
    sim_result = await simulator.simulate(SimulationRequest(
        journey_id=journey_id,
        num_simulations=5000,
        num_customers=10000,
        random_seed=42,
    ))
    print(f"Expected conversion: {sim_result.expected_value:.1%}")
    print(f"95% CI: [{sim_result.statistics.confidence_interval_low:.1%}, "
          f"{sim_result.statistics.confidence_interval_high:.1%}]")

    return report, opt_result, sim_result
```

## Configuration

The analytics module uses the standard Journey Orchestrator configuration. No additional environment variables are required.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Low simulation accuracy | Increase `num_simulations` to 5000+ |
| Unreliable results | Set `random_seed` for reproducibility |
| Missing insights | Ensure funnel analysis is enabled |
| Optimization not improving | Check constraints; try different target metric |
| API returns 404 | Ensure analytics/optimization has been run first |
