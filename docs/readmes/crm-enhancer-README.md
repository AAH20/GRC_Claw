# CRM Enhancer

## Project Overview

CRM enhancement layer that adds AI-powered insights, automation, and data enrichment to existing CRM platforms.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `crm-enhancer` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- AI-powered contact and account insights
- Automated data enrichment and deduplication
- Next-best-action recommendations for sales reps
- Deal scoring and win probability prediction
- Activity capture and logging automation
- Custom field and object creation via API
- CRM health scoring and data quality reports
- Integration with Salesforce, HubSpot, Pipedrive, and Zoho

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/crm-enhancer

# Using pip
pip install grc-claw-crm-enhancer
```

### Basic Usage

```python
from grc_claw import CRMEnhancer

crm = CRMEnhancer(
    platform="salesforce",
    auto_enrich=True,
    auto_deduplicate=True
)

contact = crm.enrich_contact(
    email="john@acme.com",
    fields=["title", "company_size", "industry", "technologies"]
)

deal = crm.get_deal(
    deal_id="006xx000001abc",
    include_score=True,
    include_next_actions=True
)

print(f"Deal Score: {{deal.score}}/100 | Win Probability: {{deal.win_probability}}%")
for action in deal.next_best_actions:
    print(f"  -> {{action.description}} (impact: {{action.impact_score}})")

crm.log_activity(
    contact_id=contact.id,
    type="email",
    subject="Follow-up on proposal",
    outcome="positive_response"
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `CRM_PLATFORM` | Target CRM: salesforce, hubspot, pipedrive, zoho |
| `ENRICHMENT_SERVICES` | Data enrichment providers |
| `AUTO_LOG_ACTIVITIES` | Auto-log emails and calls (default: true) |
| `DEDUPLICATION_ENABLED` | Auto-deduplicate contacts (default: true) |
| `DEAL_SCORING_MODEL` | Deal scoring model type |
| `SYNC_INTERVAL_MINUTES` | Data sync frequency (default: 15) |
| `API_CREDENTIALS` | CRM API credentials |

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
docker build -t grc-claw/crm-enhancer .
docker run -p 3000:3000 --env-file .env grc-claw/crm-enhancer
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crm-enhancer
  labels:
    app: crm-enhancer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: crm-enhancer
  template:
    metadata:
      labels:
        app: crm-enhancer
    spec:
      containers:
      - name: crm-enhancer
        image: grc-claw/crm-enhancer:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: crm-enhancer
spec:
  selector:
    app: crm-enhancer
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

- `POST /api/v1/contacts/enrich - Enrich contact data`
- `POST /api/v1/contacts/deduplicate - Deduplicate contacts`
- `GET /api/v1/deals/{id}/score - Get deal score`
- `GET /api/v1/contacts/{id}/insights - Get contact insights`
- `POST /api/v1/activities/log - Log activity`
- `GET /api/v1/health - Get CRM health report`
- `POST /api/v1/automations - Create CRM automation`

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
from grc_claw import CRMEnhancer

crm = CRMEnhancer(
    platform="salesforce",
    auto_enrich=True,
    auto_deduplicate=True
)

contact = crm.enrich_contact(
    email="john@acme.com",
    fields=["title", "company_size", "industry", "technologies"]
)

deal = crm.get_deal(
    deal_id="006xx000001abc",
    include_score=True,
    include_next_actions=True
)

print(f"Deal Score: {{deal.score}}/100 | Win Probability: {{deal.win_probability}}%")
for action in deal.next_best_actions:
    print(f"  -> {{action.description}} (impact: {{action.impact_score}})")

crm.log_activity(
    contact_id=contact.id,
    type="email",
    subject="Follow-up on proposal",
    outcome="positive_response"
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
  "url": "https://your-app.com/webhooks/crm-enhancer",
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
# HELP grc_claw_crm-enhancer_requests_total Total requests
# TYPE grc_claw_crm-enhancer_requests_total counter
grc_claw_crm-enhancer_requests_total{method="POST",status="200"} 1234
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
