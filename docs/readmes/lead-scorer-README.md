# Lead Scorer

## Project Overview

Intelligent lead scoring engine that uses machine learning to rank and prioritize leads based on demographic, behavioral, and firmographic signals.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `lead-scorer` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- ML-based lead scoring with gradient boosting and neural network models
- Behavioral signal tracking (email opens, page views, content downloads)
- Firmographic enrichment and matching
- Dynamic scoring model retraining on conversion outcomes
- Lead grading with customizable scoring tiers
- Integration with CRM for real-time score updates
- Score decay over time for stale leads
- Custom scoring rules and weighted attributes

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/lead-scorer

# Using pip
pip install grc-claw-lead-scorer
```

### Basic Usage

```python
from grc_claw import LeadScorer

scorer = LeadScorer(
    model="gradient_boosting",
    crm_integration="salesforce",
    auto_sync=True
)

lead = scorer.score_lead(
    email="prospect@company.com",
    company="Acme Corp",
    behaviors=["pricing_page_view", "whitepaper_download", "webinar_attend"]
)

print(f"Score: {{lead.score}} | Grade: {{lead.grade}} | Priority: {{lead.priority}}")
scorer.sync_hot_leads(threshold=80, assign_to="sales_team_1")
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `SCORING_MODEL` | Model type: gradient_boosting, neural_network, logistic_regression |
| `SCORE_DECAY_DAYS` | Days before score decays (default: 30) |
| `RETRAIN_INTERVAL_HOURS` | Model retraining frequency (default: 168) |
| `MIN_LEADS_FOR_TRAINING` | Minimum labeled leads for model training (default: 500) |
| `SCORE_THRESHOLDS` | Grade thresholds: hot=80, warm=50, cold=20 |
| `ENRICHMENT_SERVICES` | Data enrichment providers (Clearbit, ZoomInfo, etc.) |

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
docker build -t grc-claw/lead-scorer .
docker run -p 3000:3000 --env-file .env grc-claw/lead-scorer
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lead-scorer
  labels:
    app: lead-scorer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lead-scorer
  template:
    metadata:
      labels:
        app: lead-scorer
    spec:
      containers:
      - name: lead-scorer
        image: grc-claw/lead-scorer:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: lead-scorer
spec:
  selector:
    app: lead-scorer
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

- `POST /api/v1/leads/score - Score a single lead`
- `POST /api/v1/leads/score-batch - Batch score multiple leads`
- `GET /api/v1/leads/{id}/score - Get current lead score`
- `GET /api/v1/leads/{id}/score-history - Get score history`
- `POST /api/v1/models/retrain - Trigger model retraining`
- `GET /api/v1/models/performance - Get model performance metrics`

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
from grc_claw import LeadScorer

scorer = LeadScorer(
    model="gradient_boosting",
    crm_integration="salesforce",
    auto_sync=True
)

lead = scorer.score_lead(
    email="prospect@company.com",
    company="Acme Corp",
    behaviors=["pricing_page_view", "whitepaper_download", "webinar_attend"]
)

print(f"Score: {{lead.score}} | Grade: {{lead.grade}} | Priority: {{lead.priority}}")
scorer.sync_hot_leads(threshold=80, assign_to="sales_team_1")
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
  "url": "https://your-app.com/webhooks/lead-scorer",
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
# HELP grc_claw_lead-scorer_requests_total Total requests
# TYPE grc_claw_lead-scorer_requests_total counter
grc_claw_lead-scorer_requests_total{method="POST",status="200"} 1234
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
