# SaaS Marketing

## Project Overview

SaaS marketing platform with tools for product-led growth, trial conversion, onboarding, and expansion revenue.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `saas-marketing` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Product-led growth (PLG) analytics and optimization
- Free trial to paid conversion optimization
- In-app onboarding and feature adoption tracking
- Expansion revenue and upsell automation
- SaaS metrics tracking (MRR, ARR, NRR, CAC, LTV)
- Customer health scoring and churn prediction
- Self-serve and sales-assisted motion management
- Integration with Stripe, Chargebee, and product analytics

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/saas-marketing

# Using pip
pip install grc-claw-saas-marketing
```

### Basic Usage

```python
from grc_claw import SaaSMarketing

sm = SaaSMarketing(
    billing_provider="stripe",
    trial_days=14,
    plg_motion="hybrid"
)

trial = sm.start_trial(
    email="user@company.com",
    plan="pro_trial",
    features=["all_pro_features"],
    onboarding_flow="self_serve"
)

sm.optimize_onboarding(
    trial_id=trial.id,
    key_actions=["connect_integration", "invite_team", "create_first_project"],
    intervention_triggers={{"day_3_no_action": "send_tip_email", "day_7_no_action": "offer_demo"}}
)

health = sm.get_health_score(customer_id="cust_123")
print(f"Health: {{health.score}}/100 | Risk: {{health.churn_risk:.1%}}")
print(f"Expansion Opportunity: {{health.expansion_opportunity}}")

if health.expansion_opportunity:
    sm.trigger_expansion(
        customer_id="cust_123",
        trigger="usage_threshold",
        offer="upgrade_to_enterprise",
        channel="in_app"
    )

metrics = sm.get_saas_metrics(period="last_30_days")
print(f"MRR: ${{metrics.mrr:,.0f}} | NRR: {{metrics.nrr:.1%}} | CAC Payback: {{metrics.cac_payback_months}}mo")
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `BILLING_PROVIDER` | Billing provider: stripe, chargebee, recurly |
| `TRIAL_PERIOD_DAYS` | Free trial period (default: 14) |
| `PLG_MOTION` | Product-led growth motion: self_serve, sales_assisted, hybrid |
| `EXPANSION_TRIGGERS` | Expansion revenue trigger events |
| `HEALTH_SCORE_MODEL` | Customer health score model |
| `SAAS_METRICS_DASHBOARD` | SaaS metrics dashboard configuration |

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
docker build -t grc-claw/saas-marketing .
docker run -p 3000:3000 --env-file .env grc-claw/saas-marketing
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: saas-marketing
  labels:
    app: saas-marketing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: saas-marketing
  template:
    metadata:
      labels:
        app: saas-marketing
    spec:
      containers:
      - name: saas-marketing
        image: grc-claw/saas-marketing:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: saas-marketing
spec:
  selector:
    app: saas-marketing
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

- `POST /api/v1/trials/start - Start free trial`
- `POST /api/v1/trials/convert - Convert trial to paid`
- `POST /api/v1/onboarding/optimize - Optimize onboarding flow`
- `GET /api/v1/health/{customer_id} - Get customer health score`
- `POST /api/v1/expansion/trigger - Trigger expansion campaign`
- `GET /api/v1/metrics/saas - Get SaaS metrics`
- `POST /api/v1/churn/predict - Predict churn risk`

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
from grc_claw import SaaSMarketing

sm = SaaSMarketing(
    billing_provider="stripe",
    trial_days=14,
    plg_motion="hybrid"
)

trial = sm.start_trial(
    email="user@company.com",
    plan="pro_trial",
    features=["all_pro_features"],
    onboarding_flow="self_serve"
)

sm.optimize_onboarding(
    trial_id=trial.id,
    key_actions=["connect_integration", "invite_team", "create_first_project"],
    intervention_triggers={{"day_3_no_action": "send_tip_email", "day_7_no_action": "offer_demo"}}
)

health = sm.get_health_score(customer_id="cust_123")
print(f"Health: {{health.score}}/100 | Risk: {{health.churn_risk:.1%}}")
print(f"Expansion Opportunity: {{health.expansion_opportunity}}")

if health.expansion_opportunity:
    sm.trigger_expansion(
        customer_id="cust_123",
        trigger="usage_threshold",
        offer="upgrade_to_enterprise",
        channel="in_app"
    )

metrics = sm.get_saas_metrics(period="last_30_days")
print(f"MRR: ${{metrics.mrr:,.0f}} | NRR: {{metrics.nrr:.1%}} | CAC Payback: {{metrics.cac_payback_months}}mo")
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
  "url": "https://your-app.com/webhooks/saas-marketing",
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
# HELP grc_claw_saas-marketing_requests_total Total requests
# TYPE grc_claw_saas-marketing_requests_total counter
grc_claw_saas-marketing_requests_total{method="POST",status="200"} 1234
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
