# Partner Management

## Project Overview

Partner relationship management (PRM) platform for managing channel partners, resellers, and strategic alliances.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `partner-management` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Partner portal with deal registration and tracking
- Partner tiering and certification management
- Co-marketing campaign management
- Partner enablement and training delivery
- Deal registration and protection
- Partner performance scoring and MDF management
- Revenue attribution and partner analytics
- Partner communication and collaboration tools

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/partner-management

# Using pip
pip install grc-claw-partner-management
```

### Basic Usage

```python
from grc_claw import PartnerManagement

pm = PartnerManagement(
    tiers=["registered", "certified", "premier", "strategic"],
    deal_protection_days=90
)

partner = pm.register_partner(
    company="Tech Solutions Inc",
    contact="Jane Smith",
    email="jane@techsolutions.com",
    type="reseller",
    region="North America"
)

deal = pm.register_deal(
    partner_id=partner.id,
    customer="Acme Corp",
    product="Enterprise Suite",
    value=100000,
    expected_close="2024-03-01"
)

pm.enroll_training(
    partner_id=partner.id,
    program="sales_certification",
    required_for_tier="certified"
)

mdf = pm.request_mdf(
    partner_id=partner.id,
    campaign="Q1 Webinar Series",
    amount=5000,
    justification="Expected 50 attendees, 10% conversion"
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `PARTNER_TIERS` | Partner tier definitions |
| `DEAL_REGISTRATION_RULES` | Deal registration rules |
| `CERTIFICATION_PROGRAMS` | Certification program definitions |
| `MDF_ALLOCATION_RULES` | Market development funds rules |
| `PARTNER_PORTAL_URL` | Partner portal URL |
| `CO_MARKETING_BUDGET` | Co-marketing budget allocation |
| `REVENUE_SHARE_STRUCTURE` | Revenue share structure |

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
docker build -t grc-claw/partner-management .
docker run -p 3000:3000 --env-file .env grc-claw/partner-management
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: partner-management
  labels:
    app: partner-management
spec:
  replicas: 2
  selector:
    matchLabels:
      app: partner-management
  template:
    metadata:
      labels:
        app: partner-management
    spec:
      containers:
      - name: partner-management
        image: grc-claw/partner-management:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: partner-management
spec:
  selector:
    app: partner-management
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

- `POST /api/v1/partners - Register partner`
- `GET /api/v1/partners/{id} - Get partner details`
- `POST /api/v1/partners/{id}/tier - Update partner tier`
- `POST /api/v1/deals/register - Register deal`
- `POST /api/v1/training/enroll - Enroll partner in training`
- `POST /api/v1/mdf/request - Request MDF`
- `GET /api/v1/partners/{id}/performance - Get partner performance`

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
from grc_claw import PartnerManagement

pm = PartnerManagement(
    tiers=["registered", "certified", "premier", "strategic"],
    deal_protection_days=90
)

partner = pm.register_partner(
    company="Tech Solutions Inc",
    contact="Jane Smith",
    email="jane@techsolutions.com",
    type="reseller",
    region="North America"
)

deal = pm.register_deal(
    partner_id=partner.id,
    customer="Acme Corp",
    product="Enterprise Suite",
    value=100000,
    expected_close="2024-03-01"
)

pm.enroll_training(
    partner_id=partner.id,
    program="sales_certification",
    required_for_tier="certified"
)

mdf = pm.request_mdf(
    partner_id=partner.id,
    campaign="Q1 Webinar Series",
    amount=5000,
    justification="Expected 50 attendees, 10% conversion"
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
  "url": "https://your-app.com/webhooks/partner-management",
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
# HELP grc_claw_partner-management_requests_total Total requests
# TYPE grc_claw_partner-management_requests_total counter
grc_claw_partner-management_requests_total{method="POST",status="200"} 1234
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
