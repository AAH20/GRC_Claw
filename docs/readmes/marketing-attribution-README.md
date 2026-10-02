# Marketing Attribution

## Project Overview

Multi-touch attribution modeling platform that accurately assigns credit to marketing touchpoints across the customer journey.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `marketing-attribution` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Multi-touch attribution models (first-touch, last-touch, linear, time-decay, data-driven)
- Cross-channel touchpoint tracking and stitching
- Attribution model comparison and selection
- Incrementality testing and lift measurement
- Attribution-based budget optimization
- Customer journey path analysis
- Attribution data warehouse and ETL
- Attribution reporting and visualization

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/marketing-attribution

# Using pip
pip install grc-claw-marketing-attribution
```

### Basic Usage

```python
from grc_claw import MarketingAttribution

ma = MarketingAttribution(
    default_model="data_driven",
    lookback_days=90
)

results = ma.run_attribution(
    date_range="last_30_days",
    channels=["paid_search", "paid_social", "organic", "email", "display"],
    model="data_driven"
)

for channel, credit in results.channel_credit.items():
    print(f"{{channel}}: {{credit:.1%}} of total conversions")

comparison = ma.compare_models(
    models=["first_touch", "last_touch", "linear", "time_decay", "data_driven"],
    metric="roas"
)

best = comparison.best_model
print(f"Best model: {{best.name}} (accuracy: {{best.accuracy:.1%}})")

incrementality = ma.run_incrementality_test(
    channel="paid_social",
    test_group_size=10000,
    duration_days=30
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `ATTRIBUTION_MODEL` | Default model: first_touch, last_touch, linear, time_decay, data_driven |
| `LOOKBACK_WINDOW_DAYS` | Attribution lookback window (default: 90) |
| `TOUCHPOINT_SOURCES` | Touchpoint data sources |
| `INCREMENTALITY_TEST_ENABLED` | Enable incrementality testing (default: true) |
| `DATA_CLEAN_ROOM` | Data clean room configuration |
| `ATTRIBUTION_GRANULARITY` | Attribution granularity: campaign, ad_group, creative |
| `MODEL_COMPARISON_MODELS` | Models to compare |

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
docker build -t grc-claw/marketing-attribution .
docker run -p 3000:3000 --env-file .env grc-claw/marketing-attribution
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: marketing-attribution
  labels:
    app: marketing-attribution
spec:
  replicas: 2
  selector:
    matchLabels:
      app: marketing-attribution
  template:
    metadata:
      labels:
        app: marketing-attribution
    spec:
      containers:
      - name: marketing-attribution
        image: grc-claw/marketing-attribution:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: marketing-attribution
spec:
  selector:
    app: marketing-attribution
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

- `POST /api/v1/attribution/run - Run attribution analysis`
- `GET /api/v1/attribution/{id} - Get attribution results`
- `POST /api/v1/attribution/compare - Compare attribution models`
- `POST /api/v1/attribution/incrementality - Run incrementality test`
- `GET /api/v1/attribution/journeys/{customer_id} - Get customer journey`
- `POST /api/v1/attribution/optimize - Optimize budget based on attribution`

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
from grc_claw import MarketingAttribution

ma = MarketingAttribution(
    default_model="data_driven",
    lookback_days=90
)

results = ma.run_attribution(
    date_range="last_30_days",
    channels=["paid_search", "paid_social", "organic", "email", "display"],
    model="data_driven"
)

for channel, credit in results.channel_credit.items():
    print(f"{{channel}}: {{credit:.1%}} of total conversions")

comparison = ma.compare_models(
    models=["first_touch", "last_touch", "linear", "time_decay", "data_driven"],
    metric="roas"
)

best = comparison.best_model
print(f"Best model: {{best.name}} (accuracy: {{best.accuracy:.1%}})")

incrementality = ma.run_incrementality_test(
    channel="paid_social",
    test_group_size=10000,
    duration_days=30
)
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
  "url": "https://your-app.com/webhooks/marketing-attribution",
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
# HELP grc_claw_marketing-attribution_requests_total Total requests
# TYPE grc_claw_marketing-attribution_requests_total counter
grc_claw_marketing-attribution_requests_total{method="POST",status="200"} 1234
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
