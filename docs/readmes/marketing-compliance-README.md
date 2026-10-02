# Marketing Compliance

## Project Overview

Marketing compliance management platform that ensures all marketing activities adhere to regulatory requirements and internal policies.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `marketing-compliance` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- GDPR, CCPA, and CAN-SPAM compliance checking
- Cookie consent management and tracking
- Marketing content compliance review workflow
- Data retention policy enforcement
- Privacy impact assessments for marketing activities
- Consent preference management
- Regulatory change monitoring and alerting
- Compliance audit trail and reporting

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/marketing-compliance

# Using pip
pip install grc-claw-marketing-compliance
```

### Basic Usage

```python
from grc_claw import MarketingCompliance

mc = MarketingCompliance(
    regulations=["gdpr", "ccpa", "can_spam"],
    cmp="onetrust"
)

review = mc.check_content(
    content=email_html,
    content_type="email",
    regulations=["gdpr", "can_spam"]
)

if not review.passed:
    for violation in review.violations:
        print(f"FAIL {{violation.rule}}: {{violation.description}}")
        print(f"   Fix: {{violation.suggestion}}")

mc.record_consent(
    user_id="user_123",
    purposes=["marketing_email", "analytics", "personalization"],
    status="granted",
    timestamp="2024-01-15T10:00:00Z",
    source="cookie_banner"
)

report = mc.generate_report(
    period="Q4_2024",
    regulations=["gdpr", "ccpa"],
    include_audit_trail=True
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `REGULATIONS` | Applicable regulations: gdpr, ccpa, can_spam, lgpd, pipeda |
| `CONSENT_MANAGEMENT_PROVIDER` | CMP provider |
| `DATA_RETENTION_POLICIES` | Data retention policy definitions |
| `COMPLIANCE_REVIEW_WORKFLOW` | Content review workflow configuration |
| `PRIVACY_IMPACT_ASSESSMENT_TEMPLATE` | PIA template path |
| `REGULATORY_MONITOR_SOURCES` | Regulatory news sources |
| `VIOLATION_ALERT_CHANNELS` | Alert channels for violations |

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
docker build -t grc-claw/marketing-compliance .
docker run -p 3000:3000 --env-file .env grc-claw/marketing-compliance
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: marketing-compliance
  labels:
    app: marketing-compliance
spec:
  replicas: 2
  selector:
    matchLabels:
      app: marketing-compliance
  template:
    metadata:
      labels:
        app: marketing-compliance
    spec:
      containers:
      - name: marketing-compliance
        image: grc-claw/marketing-compliance:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: marketing-compliance
spec:
  selector:
    app: marketing-compliance
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

- `POST /api/v1/compliance/check - Check content compliance`
- `POST /api/v1/consent/record - Record consent`
- `GET /api/v1/consent/{user_id} - Get consent status`
- `POST /api/v1/privacy/assessment - Create privacy impact assessment`
- `GET /api/v1/compliance/audit-trail - Get audit trail`
- `POST /api/v1/retention/enforce - Enforce data retention`
- `GET /api/v1/compliance/report - Generate compliance report`

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
from grc_claw import MarketingCompliance

mc = MarketingCompliance(
    regulations=["gdpr", "ccpa", "can_spam"],
    cmp="onetrust"
)

review = mc.check_content(
    content=email_html,
    content_type="email",
    regulations=["gdpr", "can_spam"]
)

if not review.passed:
    for violation in review.violations:
        print(f"FAIL {{violation.rule}}: {{violation.description}}")
        print(f"   Fix: {{violation.suggestion}}")

mc.record_consent(
    user_id="user_123",
    purposes=["marketing_email", "analytics", "personalization"],
    status="granted",
    timestamp="2024-01-15T10:00:00Z",
    source="cookie_banner"
)

report = mc.generate_report(
    period="Q4_2024",
    regulations=["gdpr", "ccpa"],
    include_audit_trail=True
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
  "url": "https://your-app.com/webhooks/marketing-compliance",
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
# HELP grc_claw_marketing-compliance_requests_total Total requests
# TYPE grc_claw_marketing-compliance_requests_total counter
grc_claw_marketing-compliance_requests_total{method="POST",status="200"} 1234
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
