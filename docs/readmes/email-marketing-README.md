# Email Marketing

## Project Overview

Enterprise email marketing platform with advanced segmentation, automation, personalization, and deliverability optimization.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `email-marketing` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Drag-and-drop email builder with responsive templates
- Advanced segmentation with dynamic lists and behavioral triggers
- Marketing automation workflows (drip campaigns, nurture sequences)
- Subject line A/B testing with AI-powered optimization
- Deliverability monitoring and sender reputation management
- Email analytics with open, click, bounce, and conversion tracking
- List hygiene and bounce management
- GDPR and CAN-SPAM compliance tools

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/email-marketing

# Using pip
pip install grc-claw-email-marketing
```

### Basic Usage

```python
from grc_claw import EmailMarketing

em = EmailMarketing(
    provider="sendgrid",
    from_address="marketing@company.com",
    tracking_domain="links.company.com"
)

campaign = em.create_campaign(
    name="January Newsletter",
    subject="New Year, New Features!",
    template="monthly_newsletter_v2",
    segment="active_users_90d",
    personalize=True
)

em.schedule(
    campaign_id=campaign.id,
    send_at="2024-01-15T14:00:00Z",
    timezone="America/New_York"
)

em.create_automation(
    name="Welcome Series",
    trigger="new_signup",
    steps=[
        {{"delay": 0, "template": "welcome_immediate"}},
        {{"delay_hours": 24, "template": "getting_started"}},
        {{"delay_hours": 72, "template": "feature_highlight"}},
        {{"delay_hours": 168, "template": "social_proof"}}
    ]
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `SMTP_PROVIDER` | Email delivery provider (sendgrid, mailgun, ses) |
| `DEFAULT_FROM_ADDRESS` | Default sender email address |
| `REPLY_TO_ADDRESS` | Reply-to email address |
| `TRACKING_DOMAIN` | Custom tracking domain |
| `AUTOMATION_INTERVAL` | Automation check interval in minutes (default: 5) |
| `MAX_EMAILS_PER_HOUR` | Rate limit for sending (default: 10000) |
| `UNSUBSCRIBE_PAGE_URL` | Unsubscribe landing page URL |
| `COMPLIANCE_MODE` | Compliance mode: gdpr, can_spam, both |

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
docker build -t grc-claw/email-marketing .
docker run -p 3000:3000 --env-file .env grc-claw/email-marketing
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: email-marketing
  labels:
    app: email-marketing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: email-marketing
  template:
    metadata:
      labels:
        app: email-marketing
    spec:
      containers:
      - name: email-marketing
        image: grc-claw/email-marketing:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: email-marketing
spec:
  selector:
    app: email-marketing
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

- `POST /api/v1/campaigns - Create email campaign`
- `POST /api/v1/campaigns/{id}/send - Send campaign`
- `POST /api/v1/campaigns/{id}/schedule - Schedule campaign`
- `GET /api/v1/campaigns/{id}/stats - Get campaign statistics`
- `POST /api/v1/segments - Create segment`
- `POST /api/v1/automations - Create automation workflow`
- `GET /api/v1/templates - List email templates`
- `POST /api/v1/templates - Create email template`

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
from grc_claw import EmailMarketing

em = EmailMarketing(
    provider="sendgrid",
    from_address="marketing@company.com",
    tracking_domain="links.company.com"
)

campaign = em.create_campaign(
    name="January Newsletter",
    subject="New Year, New Features!",
    template="monthly_newsletter_v2",
    segment="active_users_90d",
    personalize=True
)

em.schedule(
    campaign_id=campaign.id,
    send_at="2024-01-15T14:00:00Z",
    timezone="America/New_York"
)

em.create_automation(
    name="Welcome Series",
    trigger="new_signup",
    steps=[
        {{"delay": 0, "template": "welcome_immediate"}},
        {{"delay_hours": 24, "template": "getting_started"}},
        {{"delay_hours": 72, "template": "feature_highlight"}},
        {{"delay_hours": 168, "template": "social_proof"}}
    ]
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
  "url": "https://your-app.com/webhooks/email-marketing",
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
# HELP grc_claw_email-marketing_requests_total Total requests
# TYPE grc_claw_email-marketing_requests_total counter
grc_claw_email-marketing_requests_total{method="POST",status="200"} 1234
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
