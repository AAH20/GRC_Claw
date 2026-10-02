# SMB Marketing

## Project Overview

Marketing automation platform designed specifically for small and medium-sized businesses with affordable, easy-to-use tools.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `smb-marketing` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- All-in-one marketing dashboard for SMBs
- Simplified email marketing with templates
- Social media scheduling and management
- Basic SEO and website optimization tools
- Local SEO and Google Business Profile management
- Reputation management and review monitoring
- Simple automation workflows
- SMB-specific reporting and ROI tracking

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/smb-marketing

# Using pip
pip install grc-claw-smb-marketing
```

### Basic Usage

```python
from grc_claw import SMBMarketing

smb = SMBMarketing(
    business_type="restaurant",
    location="Austin, TX",
    budget_monthly=500
)

campaign = smb.create_campaign(
    name="Weekend Special Promotion",
    type="email_social",
    audience="local_customers",
    offer="20% off weekend brunch",
    budget=200
)

smb.schedule_social(
    content="Weekend Brunch Special! 20% off this Saturday & Sunday.",
    platforms=["facebook", "instagram"],
    scheduled_time="2024-01-12T08:00:00"
)

seo = smb.get_local_seo()
print(f"Score: {{seo.score}}/100")
for rec in seo.recommendations:
    print(f"  -> {{rec}}")

reviews = smb.get_reviews(sources=["google", "yelp", "tripadvisor"])
for review in reviews.recent_negative:
    smb.respond_to_review(review, template="apology_discount")
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `SMB_TEMPLATES_DIR` | SMB template directory |
| `LOCAL_SEO_ENABLED` | Enable local SEO tools (default: true) |
| `REPUTATION_MONITORING` | Review monitoring configuration |
| `SIMPLICITY_MODE` | Simplified UI mode (default: true) |
| `BUDGET_TRACKING` | Marketing budget tracking configuration |
| `COMPETITOR_MONITORING` | Local competitor monitoring |

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
docker build -t grc-claw/smb-marketing .
docker run -p 3000:3000 --env-file .env grc-claw/smb-marketing
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: smb-marketing
  labels:
    app: smb-marketing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: smb-marketing
  template:
    metadata:
      labels:
        app: smb-marketing
    spec:
      containers:
      - name: smb-marketing
        image: grc-claw/smb-marketing:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: smb-marketing
spec:
  selector:
    app: smb-marketing
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

- `POST /api/v1/campaigns - Create campaign`
- `POST /api/v1/emails/send - Send email`
- `POST /api/v1/social/schedule - Schedule social post`
- `GET /api/v1/seo/local - Get local SEO recommendations`
- `GET /api/v1/reviews - Get reviews`
- `POST /api/v1/automations - Create simple automation`
- `GET /api/v1/reports - Get marketing report`

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
from grc_claw import SMBMarketing

smb = SMBMarketing(
    business_type="restaurant",
    location="Austin, TX",
    budget_monthly=500
)

campaign = smb.create_campaign(
    name="Weekend Special Promotion",
    type="email_social",
    audience="local_customers",
    offer="20% off weekend brunch",
    budget=200
)

smb.schedule_social(
    content="Weekend Brunch Special! 20% off this Saturday & Sunday.",
    platforms=["facebook", "instagram"],
    scheduled_time="2024-01-12T08:00:00"
)

seo = smb.get_local_seo()
print(f"Score: {{seo.score}}/100")
for rec in seo.recommendations:
    print(f"  -> {{rec}}")

reviews = smb.get_reviews(sources=["google", "yelp", "tripadvisor"])
for review in reviews.recent_negative:
    smb.respond_to_review(review, template="apology_discount")
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
  "url": "https://your-app.com/webhooks/smb-marketing",
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
# HELP grc_claw_smb-marketing_requests_total Total requests
# TYPE grc_claw_smb-marketing_requests_total counter
grc_claw_smb-marketing_requests_total{method="POST",status="200"} 1234
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
