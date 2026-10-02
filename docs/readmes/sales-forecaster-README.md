# Sales Forecaster

## Project Overview

AI-powered sales forecasting platform that predicts future revenue, pipeline value, and sales performance with confidence intervals.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `sales-forecaster` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Time-series forecasting with ARIMA, Prophet, and neural network models
- Pipeline-based forecasting with stage probability weighting
- Multi-scenario forecasting (optimistic, realistic, pessimistic)
- Seasonality and trend detection
- Forecast accuracy tracking and model improvement
- Territory and rep-level forecasting
- Product line revenue forecasting
- Forecast vs. actual variance analysis

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/sales-forecaster

# Using pip
pip install grc-claw-sales-forecaster
```

### Basic Usage

```python
from grc_claw import SalesForecaster

sf = SalesForecaster(
    model="ensemble",
    horizon_days=90,
    granularity="weekly"
)

forecast = sf.revenue_forecast(
    historical_data="sales_history.csv",
    include_seasonality=True,
    scenarios=["optimistic", "realistic", "pessimistic"]
)

for scenario in forecast.scenarios:
    print(f"{{scenario.name}}: ${{scenario.total_revenue:,.0f}} "
          f"(CI: ${{scenario.ci_low:,.0f}} - ${{scenario.ci_high:,.0f}})")

pipeline = sf.pipeline_forecast(
    pipeline_data="crm_pipeline",
    stage_probabilities={{"discovery": 0.2, "demo": 0.4, "proposal": 0.6, "negotiation": 0.8}}
)

print(f"Pipeline Value: ${{pipeline.weighted_value:,.0f}}")
print(f"Best Case: ${{pipeline.best_case:,.0f}}")
print(f"Worst Case: ${{pipeline.worst_case:,.0f}}")
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `FORECAST_MODEL` | Model type: arima, prophet, lstm, ensemble |
| `FORECAST_HORIZON_DAYS` | Forecast horizon in days (default: 90) |
| `CONFIDENCE_INTERVAL` | Confidence interval (default: 0.95) |
| `SEASONALITY_DETECTION` | Enable seasonality detection (default: true) |
| `PIPELINE_STAGES` | Pipeline stage definitions with probabilities |
| `FORECAST_GRANULARITY` | Forecast granularity: daily, weekly, monthly |
| `MODEL_RETRAIN_INTERVAL_DAYS` | Model retraining frequency (default: 7) |

### Environment File Example

```env
# .env
GRC_CLAW_API_KEY=your_api_key_here
GRC_CLAW_ENV=production
```

---

## Deployment

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

```bash
docker build -t grc-claw/sales-forecaster .
docker run -p 3000:3000 --env-file .env grc-claw/sales-forecaster
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sales-forecaster
  labels:
    app: sales-forecaster
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sales-forecaster
  template:
    metadata:
      labels:
        app: sales-forecaster
    spec:
      containers:
      - name: sales-forecaster
        image: grc-claw/sales-forecaster:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: sales-forecaster
spec:
  selector:
    app: sales-forecaster
  ports:
  - port: 80
    targetPort: 3000
```

### Serverless (AWS Lambda)

```bash
# Package and deploy
npm run build
serverless deploy --stage production
```

---

## API Reference

### Endpoints

- `POST /api/v1/forecast/revenue - Generate revenue forecast`
- `POST /api/v1/forecast/pipeline - Generate pipeline forecast`
- `GET /api/v1/forecast/{id} - Get forecast details`
- `GET /api/v1/forecast/accuracy - Get forecast accuracy metrics`
- `POST /api/v1/forecast/scenarios - Generate multi-scenario forecast`
- `GET /api/v1/forecast/variance - Get forecast vs. actual variance`

### Authentication

All API requests require a Bearer token:

```bash
curl -H "Authorization: Bearer $GRC_CLAW_API_KEY" \
     -H "Content-Type: application/json" \
     https://api.grc-claw.com/api/v1/...
```

### Rate Limits

| Tier | Requests/min | Burst |
|---|---|---|
| Free | 60 | 10 |
| Pro | 600 | 100 |
| Enterprise | 6000 | 1000 |

### Error Handling

All errors follow RFC 7807 (Problem Details):

```json
{
  "type": "https://api.grc-claw.com/errors/validation",
  "title": "Validation Error",
  "status": 400,
  "detail": "Invalid input parameters",
  "instance": "/api/v1/resource"
}
```

---

## Examples

### SDK Usage

```python
from grc_claw import SalesForecaster

sf = SalesForecaster(
    model="ensemble",
    horizon_days=90,
    granularity="weekly"
)

forecast = sf.revenue_forecast(
    historical_data="sales_history.csv",
    include_seasonality=True,
    scenarios=["optimistic", "realistic", "pessimistic"]
)

for scenario in forecast.scenarios:
    print(f"{{scenario.name}}: ${{scenario.total_revenue:,.0f}} "
          f"(CI: ${{scenario.ci_low:,.0f}} - ${{scenario.ci_high:,.0f}})")

pipeline = sf.pipeline_forecast(
    pipeline_data="crm_pipeline",
    stage_probabilities={{"discovery": 0.2, "demo": 0.4, "proposal": 0.6, "negotiation": 0.8}}
)

print(f"Pipeline Value: ${{pipeline.weighted_value:,.0f}}")
print(f"Best Case: ${{pipeline.best_case:,.0f}}")
print(f"Worst Case: ${{pipeline.worst_case:,.0f}}")
```

### cURL Examples

```bash
# Health check
curl https://api.grc-claw.com/api/v1/health

# Authenticate
curl -X POST https://api.grc-claw.com/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your_key"}'
```

### Webhook Integration

```json
{
  "url": "https://your-app.com/webhooks/sales-forecaster",
  "events": ["resource.created", "resource.updated", "resource.deleted"],
  "secret": "your_webhook_secret"
}
```

---

## Monitoring & Observability

### Health Checks

```bash
GET /api/v1/health
# Returns: {"status": "ok", "version": "1.0.0", "uptime": 3600}
```

### Metrics (Prometheus)

```
# HELP grc_claw_sales-forecaster_requests_total Total requests
# TYPE grc_claw_sales-forecaster_requests_total counter
grc_claw_sales-forecaster_requests_total{method="POST",status="200"} 1234
```

### Logging

Structured JSON logging to stdout:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "message": "Request completed",
  "duration_ms": 45,
  "status_code": 200
}
```

---

## Contributing

See [GRC Claw Contributing Guide](../../CONTRIBUTING.md).

---

## License

See [GRC Claw License](../../LICENSE).

---

## Support

- **Documentation**: [docs.grc-claw.com](https://docs.grc-claw.com)
- **Issues**: [GitHub Issues](https://github.com/grc-claw/grc-claw/issues)
- **Community**: [Discord](https://discord.gg/grc-claw)
