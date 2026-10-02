# Agency Marketing

## Project Overview

Marketing platform for agencies to manage multiple clients, white-label reporting, and streamline client marketing operations.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `agency-marketing` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Multi-client dashboard and management
- White-label reporting and branding
- Client permission and access management
- Agency-specific workflow templates
- Bulk campaign management across clients
- Client billing and budget tracking
- Agency performance analytics and utilization
- Client portal with approval workflows

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/agency-marketing

# Using pip
pip install grc-claw-agency-marketing
```

### Basic Usage

```python
from grc_claw import AgencyMarketing

am = AgencyMarketing(
    agency_name="Digital Growth Agency",
    white_label=True,
    branding={{"logo": "agency_logo.png", "colors": ["#1a1a2e", "#16213e"]}}
)

client = am.add_client(
    company="Acme Corp",
    industry="ecommerce",
    monthly_budget=5000,
    contacts=["marketing@acme.com"]
)

campaign = am.create_client_campaign(
    client_id=client.id,
    name="Q1 Email Campaign",
    type="email",
    budget=2000,
    deliverables=["strategy", "design", "copy", "deployment"]
)

report = am.generate_white_label_report(
    client_id=client.id,
    period="January 2024",
    template="monthly_performance",
    branding=am.branding
)

am.submit_for_approval(
    client_id=client.id,
    items=[campaign.id, report.id],
    message="Please review and approve the Q1 campaign and January report."
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `AGENCY_PROFILE` | Agency profile configuration |
| `WHITE_LABEL_SETTINGS` | White-label branding settings |
| `CLIENT_PERMISSIONS` | Client permission templates |
| `BILLING_PROVIDER` | Billing provider integration |
| `WORKFLOW_TEMPLATES_DIR` | Agency workflow template directory |
| `REPORTING_BRANDING` | Report branding configuration |
| `UTILIZATION_TRACKING` | Team utilization tracking |

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
docker build -t grc-claw/agency-marketing .
docker run -p 3000:3000 --env-file .env grc-claw/agency-marketing
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agency-marketing
  labels:
    app: agency-marketing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: agency-marketing
  template:
    metadata:
      labels:
        app: agency-marketing
    spec:
      containers:
      - name: agency-marketing
        image: grc-claw/agency-marketing:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: agency-marketing
spec:
  selector:
    app: agency-marketing
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

- `POST /api/v1/clients - Add client`
- `GET /api/v1/clients/{id} - Get client details`
- `POST /api/v1/clients/{id}/campaigns - Create client campaign`
- `POST /api/v1/reports/white-label - Generate white-label report`
- `POST /api/v1/clients/{id}/approve - Submit for client approval`
- `GET /api/v1/agency/analytics - Get agency analytics`
- `POST /api/v1/billing/track - Track client billing`

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
from grc_claw import AgencyMarketing

am = AgencyMarketing(
    agency_name="Digital Growth Agency",
    white_label=True,
    branding={{"logo": "agency_logo.png", "colors": ["#1a1a2e", "#16213e"]}}
)

client = am.add_client(
    company="Acme Corp",
    industry="ecommerce",
    monthly_budget=5000,
    contacts=["marketing@acme.com"]
)

campaign = am.create_client_campaign(
    client_id=client.id,
    name="Q1 Email Campaign",
    type="email",
    budget=2000,
    deliverables=["strategy", "design", "copy", "deployment"]
)

report = am.generate_white_label_report(
    client_id=client.id,
    period="January 2024",
    template="monthly_performance",
    branding=am.branding
)

am.submit_for_approval(
    client_id=client.id,
    items=[campaign.id, report.id],
    message="Please review and approve the Q1 campaign and January report."
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
  "url": "https://your-app.com/webhooks/agency-marketing",
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
# HELP grc_claw_agency-marketing_requests_total Total requests
# TYPE grc_claw_agency-marketing_requests_total counter
grc_claw_agency-marketing_requests_total{method="POST",status="200"} 1234
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
