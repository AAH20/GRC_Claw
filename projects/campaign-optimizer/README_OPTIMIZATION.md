# Campaign Optimization Guide

## Overview

The Campaign Optimizer provides three advanced optimization capabilities:

1. **Multi-Armed Bandit Optimization** — Adaptive traffic allocation using bandit algorithms
2. **Time-Series Forecasting** — Predict future campaign performance
3. **Creative A/B Testing** — Statistical testing for ad creative optimization

## Architecture

```
src/campaign_agents/
├── agents/
│   ├── optimizer.py          # Multi-armed bandit optimizer
│   ├── forecaster.py         # Time-series forecasting
│   └── creative_optimizer.py # A/B testing for creatives
├── api/
│   ├── optimization.py       # Bandit optimization endpoints
│   └── forecasting.py        # Forecasting endpoints
└── models/
    └── optimization.py       # Pydantic data models
```

## 1. Multi-Armed Bandit Optimization

### Supported Algorithms

| Algorithm | Description | Best For |
|-----------|-------------|----------|
| **UCB1** | Upper Confidence Bound | Balanced exploration/exploitation |
| **Epsilon-Greedy** | Random exploration with probability ε | Simple, fast exploration |
| **Thompson Sampling** | Bayesian approach | Best for conversion optimization |
| **Softmax** | Probability-based selection | Smooth allocation |

### Quick Start

```python
from campaign_agents.agents.optimizer import MultiArmedBanditOptimizer
from campaign_agents.models.optimization import BanditConfig, BanditAlgorithm

config = BanditConfig(
    algorithm=BanditAlgorithm.UCB1,
    arms=[
        {"arm_id": "creative_a", "name": "Creative A"},
        {"arm_id": "creative_b", "name": "Creative B"},
        {"arm_id": "creative_c", "name": "Creative C"},
    ],
    reward_metric="conversion_rate",
)

optimizer = MultiArmedBanditOptimizer(config)

# Run optimization round
result = optimizer.optimize("campaign_123")
print(f"Selected arm: {result.bandit_result.selected_arm}")

# Update with observed reward
optimizer.update_reward("creative_a", 0.05)  # 5% conversion rate
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bandit/optimize` | Run optimization cycle |
| POST | `/bandit/{campaign_id}/update` | Update arm reward |
| GET | `/bandit/{campaign_id}/status` | Get bandit status |
| POST | `/bandit/{campaign_id}/reset` | Reset optimizer |

### Configuration

```python
BanditConfig(
    algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
    epsilon=0.1,              # For epsilon-greedy
    exploration_factor=1.414,  # For UCB1
    temperature=1.0,          # For softmax
    min_pulls_before_exploit=10,
    reward_metric="conversion_rate",
)
```

## 2. Time-Series Forecasting

### Supported Methods

| Method | Description | Best For |
|--------|-------------|----------|
| **Exponential Smoothing** | Holt-Winters method | Trend + seasonality |
| **Moving Average** | Simple rolling average | Stable metrics |
| **Linear Regression** | Trend line fitting | Linear trends |
| **Seasonal Decomposition** | Trend + seasonal + residual | Strong seasonality |

### Quick Start

```python
from campaign_agents.agents.forecaster import TimeSeriesForecaster
from campaign_agents.models.optimization import ForecastConfig, ForecastMethod

config = ForecastConfig(
    method=ForecastMethod.EXPONENTIAL_SMOOTHING,
    granularity=ForecastGranularity.DAILY,
    horizon=7,
    confidence_level=0.95,
)

forecaster = TimeSeriesForecaster(config)

# Add historical data
for day in range(30):
    forecaster.add_data_point(
        TimeSeriesPoint(
            timestamp=f"2024-01-{day+1:02d}T00:00:00",
            value=100 + day * 2,
        )
    )

# Generate forecast
result = forecaster.forecast("campaign_123", "conversions")
print(f"Trend: {result.trend_direction}")
print(f"MAPE: {result.mape:.2f}%")
for point in result.forecast_points:
    print(f"{point.timestamp}: {point.value:.1f} [{point.lower_bound:.1f}, {point.upper_bound:.1f}]")
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/forecast` | Generate forecast |
| POST | `/forecast/{campaign_id}/data` | Add historical data |
| GET | `/forecast/{campaign_id}/history` | Get forecast history |
| DELETE | `/forecast/{campaign_id}/data` | Clear data |

## 3. Creative A/B Testing

### Quick Start

```python
from campaign_agents.agents.creative_optimizer import CreativeOptimizer
from campaign_agents.models.optimization import ABTestConfig, CreativeVariant

config = ABTestConfig(
    test_id="creative_test_001",
    campaign_id="campaign_123",
    variants=[
        CreativeVariant(
            variant_id="control",
            name="Control",
            creative_type="image",
            content={"headline": "Buy Now"},
            impressions=10000,
            clicks=500,
            conversions=50,
            spend=1000.0,
        ),
        CreativeVariant(
            variant_id="treatment",
            name="Treatment",
            creative_type="video",
            content={"headline": "Watch Demo"},
            impressions=10000,
            clicks=800,
            conversions=90,
            spend=1200.0,
        ),
    ],
    primary_metric="ctr",
    min_sample_size=1000,
    confidence_level=0.95,
)

optimizer = CreativeOptimizer(config)

# Run optimization
result = optimizer.optimize("campaign_123")
print(f"Winner: {result.ab_test.winner_variant_id}")
print(f"Significant: {result.ab_test.is_significant}")
for insight in result.insights:
    print(f"  - {insight}")
```

### Statistical Testing

The creative optimizer uses chi-squared testing for statistical significance:

- **Primary metric**: CTR, conversion rate, or CPA
- **Confidence level**: 95% (configurable)
- **Minimum sample size**: 1000 impressions per variant
- **Auto winner selection**: Enabled by default

### Traffic Allocation

Traffic is allocated using Thompson Sampling:

```python
allocations = optimizer.get_variant_allocations()
# {"control": 0.35, "treatment": 0.65}
```

## Running Tests

```bash
# Run all optimization tests
pytest tests/test_optimization.py -v

# Run forecasting tests
pytest tests/test_forecasting.py -v

# Run creative optimizer tests
pytest tests/test_creative_optimizer.py -v

# Run with coverage
pytest tests/test_optimization.py tests/test_forecasting.py tests/test_creative_optimizer.py --cov=campaign_agents --cov-report=html
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "campaign_agents.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: campaign-optimizer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: campaign-optimizer
  template:
    metadata:
      labels:
        app: campaign-optimizer
    spec:
      containers:
      - name: optimizer
        image: campaign-optimizer:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

## Best Practices

### Bandit Optimization

1. **Start with UCB1** for balanced exploration/exploitation
2. **Use Thompson Sampling** for conversion rate optimization
3. **Set min_pulls_before_exploit** to 10-20 for new campaigns
4. **Monitor regret** to ensure algorithm is learning

### Forecasting

1. **Use at least 30 days** of historical data
2. **Enable seasonality detection** for weekly patterns
3. **Set confidence level** to 0.95 for production decisions
4. **Monitor MAPE** — aim for <20% for reliable forecasts

### Creative A/B Testing

1. **Run tests for at least 7 days** to account for day-of-week effects
2. **Use 1000+ impressions per variant** for statistical significance
3. **Test one variable at a time** (headline, image, or CTA)
4. **Auto-select winners** only after significance is reached

## Monitoring

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Bandit regret | Decreasing | >20% increase |
| Forecast MAPE | <20% | >30% |
| A/B test duration | 7-14 days | >21 days |
| Winner confidence | >95% | <90% |

### Logging

All agents use structured logging with `structlog`:

```python
import structlog
logger = structlog.get_logger(__name__)

logger.info(
    "Optimization completed",
    campaign_id=campaign_id,
    selected_arm=selected_arm,
    exploration=is_exploration,
)
```

## Troubleshooting

### Bandit Not Exploring

- Check `epsilon` value (should be >0)
- Verify `min_pulls_before_exploit` is not too high
- Ensure rewards are being updated correctly

### Forecast Accuracy Low

- Add more historical data (minimum 30 points)
- Check for data quality issues
- Try different forecasting method
- Verify seasonality period is correct

### A/B Test Not Significant

- Increase sample size (more impressions)
- Run test longer (at least 7 days)
- Check for external factors affecting results
- Verify traffic split is even

## License

MIT
