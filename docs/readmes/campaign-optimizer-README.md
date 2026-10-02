# Campaign Optimizer

## Project Overview

AI-powered marketing campaign optimization engine that automatically adjusts bidding, targeting, and creative elements across advertising channels to maximize ROI.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `campaign-optimizer` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Real-time bid management across Google Ads, Meta Ads, and programmatic channels
- Automated A/B testing with multi-armed bandit algorithms
- Creative performance analysis with automated variant generation
- Budget pacing and reallocation based on performance signals
- Cross-channel attribution modeling and budget optimization
- Audience segment performance analysis and expansion recommendations
- Dayparting and geo-targeting optimization
- Automated pause rules for underperforming campaigns

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/campaign-optimizer

# Using pip
pip install grc-claw-campaign-optimizer
```

### Basic Usage

```python
from grc_claw import CampaignOptimizer

optimizer = CampaignOptimizer(
    platforms=["google_ads", "meta_ads"],
    attribution_model="data_driven",
    optimization_interval_minutes=15
)

results = optimizer.optimize_campaigns(
    campaign_ids=["camp_001", "camp_002"],
    objective="roas",
    target_roas=4.0
)

for rec in results.recommendations:
    print(f"{{rec.campaign_id}}: {{rec.action}} — {{rec.reason}}")
    optimizer.apply(rec)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `OPTIMIZATION_INTERVAL` | Minutes between optimization cycles (default: 15) |
| `MIN_CONVERSIONS_FOR_OPTIMIZATION` | Minimum data threshold before optimization (default: 10) |
| `BID_ADJUSTMENT_MAX_PCT` | Maximum single bid adjustment percentage (default: 20) |
| `ATTRIBUTION_MODEL` | Attribution model: first_click, last_click, linear, time_decay, data_driven |
| `API_KEYS` | Platform API credentials (Google Ads, Meta, etc.) |
| `BUDGET_REALLOCATION_THRESHOLD` | Performance gap threshold for budget shifts (default: 0.15) |

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
docker build -t grc-claw/campaign-optimizer .
docker run -p 3000:3000 --env-file .env grc-claw/campaign-optimizer
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: campaign-optimizer
  labels:
    app: campaign-optimizer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: campaign-optimizer
  template:
    metadata:
      labels:
        app: campaign-optimizer
    spec:
      containers:
      - name: campaign-optimizer
        image: grc-claw/campaign-optimizer:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: campaign-optimizer
spec:
  selector:
    app: campaign-optimizer
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

- `POST /api/v1/campaigns/optimize - Trigger optimization cycle`
- `GET /api/v1/campaigns/{id}/recommendations - Get optimization recommendations`
- `POST /api/v1/campaigns/{id}/apply - Apply recommended changes`
- `GET /api/v1/campaigns/{id}/performance - Get performance metrics`
- `POST /api/v1/experiments - Create A/B test experiment`
- `GET /api/v1/experiments/{id}/results - Get experiment results`

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
from grc_claw import CampaignOptimizer

optimizer = CampaignOptimizer(
    platforms=["google_ads", "meta_ads"],
    attribution_model="data_driven",
    optimization_interval_minutes=15
)

results = optimizer.optimize_campaigns(
    campaign_ids=["camp_001", "camp_002"],
    objective="roas",
    target_roas=4.0
)

for rec in results.recommendations:
    print(f"{{rec.campaign_id}}: {{rec.action}} — {{rec.reason}}")
    optimizer.apply(rec)
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
  "url": "https://your-app.com/webhooks/campaign-optimizer",
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
# HELP grc_claw_campaign-optimizer_requests_total Total requests
# TYPE grc_claw_campaign-optimizer_requests_total counter
grc_claw_campaign-optimizer_requests_total{method="POST",status="200"} 1234
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
