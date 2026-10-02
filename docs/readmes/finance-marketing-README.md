# Finance Marketing

## Project Overview

Financial services marketing platform with compliance tools for banking, insurance, and investment marketing.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `finance-marketing` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Financial services marketing automation
- Regulatory compliance checking (FINRA, SEC, FCA)
- Customer onboarding and KYC workflow
- Financial content marketing and education
- Lead nurturing for financial products
- Customer segmentation by financial profile
- Campaign performance with compliance audit trail
- Integration with core banking and CRM systems

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/finance-marketing

# Using pip
pip install grc-claw-finance-marketing
```

### Basic Usage

```python
from grc_claw import FinanceMarketing

fm = FinanceMarketing(
    regulatory_framework="finra",
    compliance_review_required=True
)

campaign = fm.create_campaign(
    name="Retirement Planning Webinar",
    type="webinar",
    audience="high_net_worth_individuals",
    content="retirement_planning_guide"
)

compliance = fm.check_compliance(
    content_id=campaign.content_id,
    regulations=["finra", "sec"]
)

if not compliance.passed:
    for violation in compliance.violations:
        print(f"FAIL {{violation.rule}}: {{violation.description}}")

onboarding = fm.start_onboarding(
    customer_id="cust_123",
    product="investment_account",
    kyc_required=True,
    steps=["identity_verification", "risk_assessment", "account_funding"]
)

segments = fm.get_segments(
    criteria={{"min_assets": 100000, "risk_tolerance": "moderate"}}
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `REGULATORY_FRAMEWORK` | Regulatory framework: finra, sec, fca, mifid |
| `COMPLIANCE_REVIEW_REQUIRED` | Require compliance review (default: true) |
| `KYC_WORKFLOW` | KYC workflow configuration |
| `CONTENT_APPROVAL_CHAIN` | Content approval chain |
| `CUSTOMER_SEGMENTATION_RULES` | Financial segmentation rules |
| `AUDIT_TRAIL_RETENTION_YEARS` | Audit trail retention (default: 7) |

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
docker build -t grc-claw/finance-marketing .
docker run -p 3000:3000 --env-file .env grc-claw/finance-marketing
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finance-marketing
  labels:
    app: finance-marketing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: finance-marketing
  template:
    metadata:
      labels:
        app: finance-marketing
    spec:
      containers:
      - name: finance-marketing
        image: grc-claw/finance-marketing:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: finance-marketing
spec:
  selector:
    app: finance-marketing
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

- `POST /api/v1/campaigns - Create financial campaign`
- `POST /api/v1/compliance/check - Check regulatory compliance`
- `POST /api/v1/onboarding/start - Start customer onboarding`
- `POST /api/v1/content/submit - Submit content for approval`
- `GET /api/v1/segments - Get customer segments`
- `GET /api/v1/audit-trail - Get compliance audit trail`
- `GET /api/v1/analytics - Get marketing analytics`

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
from grc_claw import FinanceMarketing

fm = FinanceMarketing(
    regulatory_framework="finra",
    compliance_review_required=True
)

campaign = fm.create_campaign(
    name="Retirement Planning Webinar",
    type="webinar",
    audience="high_net_worth_individuals",
    content="retirement_planning_guide"
)

compliance = fm.check_compliance(
    content_id=campaign.content_id,
    regulations=["finra", "sec"]
)

if not compliance.passed:
    for violation in compliance.violations:
        print(f"FAIL {{violation.rule}}: {{violation.description}}")

onboarding = fm.start_onboarding(
    customer_id="cust_123",
    product="investment_account",
    kyc_required=True,
    steps=["identity_verification", "risk_assessment", "account_funding"]
)

segments = fm.get_segments(
    criteria={{"min_assets": 100000, "risk_tolerance": "moderate"}}
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
  "url": "https://your-app.com/webhooks/finance-marketing",
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
# HELP grc_claw_finance-marketing_requests_total Total requests
# TYPE grc_claw_finance-marketing_requests_total counter
grc_claw_finance-marketing_requests_total{method="POST",status="200"} 1234
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
