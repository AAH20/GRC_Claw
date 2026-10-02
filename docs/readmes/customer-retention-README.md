# Customer Retention

## Project Overview

Customer retention platform that predicts churn risk, automates win-back campaigns, and optimizes customer lifetime value.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `customer-retention` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Churn prediction with ML models
- Customer health scoring and segmentation
- Automated win-back and save campaigns
- Loyalty program management and optimization
- Customer feedback loop and action management
- Renewal and upsell opportunity identification
- Customer lifetime value (CLV) prediction and optimization
- Retention campaign performance analytics

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/customer-retention

# Using pip
pip install grc-claw-customer-retention
```

### Basic Usage

```python
from grc_claw import CustomerRetention

cr = CustomerRetention(
    churn_model="gradient_boosting",
    health_score_weights={{"usage": 0.4, "support": 0.3, "billing": 0.2, "engagement": 0.1}}
)

risk = cr.predict_churn(
    customer_id="cust_123",
    include_factors=True
)

print(f"Churn Risk: {{risk.probability:.1%}}")
for factor in risk.top_factors:
    print(f"  {{factor.name}}: {{factor.impact:+.3f}}")

if risk.probability > 0.7:
    cr.trigger_win_back(
        customer_id="cust_123",
        offer="20%_discount_3months",
        channel="email",
        sequence="aggressive_save"
    )

health = cr.get_health_score(customer_id="cust_123")
print(f"Health: {{health.score}}/100 | Trend: {{health.trend}} | Segment: {{health.segment}}")
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `CHURN_MODEL` | Churn prediction model type |
| `HEALTH_SCORE_WEIGHTS` | Health score component weights |
| `CHURN_RISK_THRESHOLD` | Risk threshold for intervention (default: 0.7) |
| `WIN_BACK_SEQUENCE` | Win-back campaign sequence configuration |
| `LOYALTY_PROGRAM_RULES` | Loyalty program rules |
| `CLV_PREDICTION_MODEL` | CLV prediction model type |
| `RETENTION_BUDGET` | Retention campaign budget allocation |

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
docker build -t grc-claw/customer-retention .
docker run -p 3000:3000 --env-file .env grc-claw/customer-retention
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: customer-retention
  labels:
    app: customer-retention
spec:
  replicas: 2
  selector:
    matchLabels:
      app: customer-retention
  template:
    metadata:
      labels:
        app: customer-retention
    spec:
      containers:
      - name: customer-retention
        image: grc-claw/customer-retention:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: customer-retention
spec:
  selector:
    app: customer-retention
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

- `POST /api/v1/churn/predict - Predict churn risk`
- `GET /api/v1/customers/{id}/health - Get customer health score`
- `POST /api/v1/win-back - Trigger win-back campaign`
- `POST /api/v1/loyalty/enroll - Enroll customer in loyalty program`
- `GET /api/v1/clv/{customer_id} - Get predicted CLV`
- `POST /api/v1/feedback/collect - Collect customer feedback`
- `GET /api/v1/retention/metrics - Get retention metrics`

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
from grc_claw import CustomerRetention

cr = CustomerRetention(
    churn_model="gradient_boosting",
    health_score_weights={{"usage": 0.4, "support": 0.3, "billing": 0.2, "engagement": 0.1}}
)

risk = cr.predict_churn(
    customer_id="cust_123",
    include_factors=True
)

print(f"Churn Risk: {{risk.probability:.1%}}")
for factor in risk.top_factors:
    print(f"  {{factor.name}}: {{factor.impact:+.3f}}")

if risk.probability > 0.7:
    cr.trigger_win_back(
        customer_id="cust_123",
        offer="20%_discount_3months",
        channel="email",
        sequence="aggressive_save"
    )

health = cr.get_health_score(customer_id="cust_123")
print(f"Health: {{health.score}}/100 | Trend: {{health.trend}} | Segment: {{health.segment}}")
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
  "url": "https://your-app.com/webhooks/customer-retention",
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
# HELP grc_claw_customer-retention_requests_total Total requests
# TYPE grc_claw_customer-retention_requests_total counter
grc_claw_customer-retention_requests_total{method="POST",status="200"} 1234
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
