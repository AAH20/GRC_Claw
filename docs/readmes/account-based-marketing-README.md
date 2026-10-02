# Account-Based Marketing

## Project Overview

Account-based marketing (ABM) platform for identifying, targeting, and engaging high-value accounts with personalized multi-channel campaigns.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `account-based-marketing` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Ideal customer profile (ICP) definition and scoring
- Account identification and intent data integration
- Multi-channel account engagement orchestration
- Personalized content and messaging per account
- Account engagement scoring and staging
- Sales and marketing alignment dashboards
- Account-based advertising and retargeting
- ABM campaign ROI and pipeline impact measurement

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/account-based-marketing

# Using pip
pip install grc-claw-account-based-marketing
```

### Basic Usage

```python
from grc_claw import AccountBasedMarketing

abm = AccountBasedMarketing(
    icp={{"industry": "technology", "size": "500-5000", "revenue": "100M+"}},
    intent_sources=["bombora", "6sense"]
)

accounts = abm.identify_accounts(
    icp_criteria={{"industry": "fintech", "employees": "200-2000"}},
    intent_signals=["funding", "hiring", "technology_evaluation"],
    limit=100
)

scored = abm.score_accounts(accounts)
for account in scored.top(20):
    print(f"{{account.name}}: Score {{account.score}} | Intent: {{account.intent_level}}")

campaign = abm.engage(
    account_id=scored.top(1).id,
    channels=["email", "linkedin_ads", "direct_mail"],
    personalization="account_level",
    sales_alert_threshold=75
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `ICP_DEFINITION` | Ideal customer profile criteria |
| `INTENT_DATA_SOURCES` | Intent data providers (Bombora, 6sense, etc.) |
| `ACCOUNT_SCORING_MODEL` | Account scoring model |
| `ENGAGEMENT_CHANNELS` | Engagement channels: email, ads, direct_mail, sales |
| `PERSONALIZATION_DEPTH` | Personalization depth: account, contact, individual |
| `SALES_ALERT_THRESHOLD` | Engagement score threshold for sales alert (default: 75) |
| `ABM_BUDGET_ALLOCATION` | Budget allocation by account tier |

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
docker build -t grc-claw/account-based-marketing .
docker run -p 3000:3000 --env-file .env grc-claw/account-based-marketing
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: account-based-marketing
  labels:
    app: account-based-marketing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: account-based-marketing
  template:
    metadata:
      labels:
        app: account-based-marketing
    spec:
      containers:
      - name: account-based-marketing
        image: grc-claw/account-based-marketing:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: account-based-marketing
spec:
  selector:
    app: account-based-marketing
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

- `POST /api/v1/accounts/identify - Identify target accounts`
- `GET /api/v1/accounts/{id} - Get account details`
- `POST /api/v1/accounts/{id}/engage - Launch engagement campaign`
- `GET /api/v1/accounts/{id}/intent - Get account intent data`
- `POST /api/v1/accounts/score - Score accounts against ICP`
- `GET /api/v1/accounts/{id}/engagement - Get engagement metrics`
- `POST /api/v1/accounts/{id}/personalize - Generate personalized content`

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
from grc_claw import AccountBasedMarketing

abm = AccountBasedMarketing(
    icp={{"industry": "technology", "size": "500-5000", "revenue": "100M+"}},
    intent_sources=["bombora", "6sense"]
)

accounts = abm.identify_accounts(
    icp_criteria={{"industry": "fintech", "employees": "200-2000"}},
    intent_signals=["funding", "hiring", "technology_evaluation"],
    limit=100
)

scored = abm.score_accounts(accounts)
for account in scored.top(20):
    print(f"{{account.name}}: Score {{account.score}} | Intent: {{account.intent_level}}")

campaign = abm.engage(
    account_id=scored.top(1).id,
    channels=["email", "linkedin_ads", "direct_mail"],
    personalization="account_level",
    sales_alert_threshold=75
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
  "url": "https://your-app.com/webhooks/account-based-marketing",
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
# HELP grc_claw_account-based-marketing_requests_total Total requests
# TYPE grc_claw_account-based-marketing_requests_total counter
grc_claw_account-based-marketing_requests_total{method="POST",status="200"} 1234
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
