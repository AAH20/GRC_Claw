# Sales Automator

## Project Overview

Sales process automation platform that automates follow-ups, proposal generation, contract management, and sales administrative tasks.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `sales-automator` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Automated follow-up sequences and cadences
- AI-powered proposal and quote generation
- Contract generation and e-signature integration
- Sales task automation and to-do management
- Meeting scheduling and calendar integration
- Sales document management and templating
- Pipeline automation and stage progression rules
- Sales notifications and alert management

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/sales-automator

# Using pip
pip install grc-claw-sales-automator
```

### Basic Usage

```python
from grc_claw import SalesAutomator

sa = SalesAutomator(
    crm="salesforce",
    esignature="docusign",
    calendar="google"
)

sequence = sa.create_sequence(
    name="Post-Demo Follow-Up",
    steps=[
        {{"delay_hours": 0, "action": "send_email", "template": "demo_recap"}},
        {{"delay_hours": 24, "action": "send_email", "template": "case_study"}},
        {{"delay_hours": 72, "action": "call", "script": "follow_up_script"}},
        {{"delay_hours": 120, "action": "send_email", "template": "pricing"}}
    ]
)

proposal = sa.generate_proposal(
    deal_id="006xx000001abc",
    template="enterprise_proposal",
    line_items=deal.products,
    discount_approval_threshold=0.15
)

sa.send_for_signature(
    proposal_id=proposal.id,
    signers=["john@acme.com", "jane@acme.com"],
    reminder_interval_days=2
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `FOLLOW_UP_INTERVAL_HOURS` | Default follow-up interval (default: 48) |
| `PROPOSAL_TEMPLATE_DIR` | Proposal template directory |
| `ESIGNATURE_PROVIDER` | E-signature provider: docusign, hellosign |
| `CONTRACT_TEMPLATE_DIR` | Contract template directory |
| `CALENDAR_PROVIDER` | Calendar provider: google, outlook |
| `PIPELINE_STAGES` | Custom pipeline stage definitions |
| `NOTIFICATION_CHANNELS` | Notification channels: email, slack, sms |

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
docker build -t grc-claw/sales-automator .
docker run -p 3000:3000 --env-file .env grc-claw/sales-automator
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sales-automator
  labels:
    app: sales-automator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sales-automator
  template:
    metadata:
      labels:
        app: sales-automator
    spec:
      containers:
      - name: sales-automator
        image: grc-claw/sales-automator:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: sales-automator
spec:
  selector:
    app: sales-automator
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

- `POST /api/v1/sequences - Create follow-up sequence`
- `POST /api/v1/proposals/generate - Generate proposal`
- `POST /api/v1/contracts/generate - Generate contract`
- `POST /api/v1/tasks - Create sales task`
- `POST /api/v1/meetings/schedule - Schedule meeting`
- `GET /api/v1/pipeline - Get pipeline overview`
- `POST /api/v1/pipeline/{id}/advance - Advance deal stage`

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
from grc_claw import SalesAutomator

sa = SalesAutomator(
    crm="salesforce",
    esignature="docusign",
    calendar="google"
)

sequence = sa.create_sequence(
    name="Post-Demo Follow-Up",
    steps=[
        {{"delay_hours": 0, "action": "send_email", "template": "demo_recap"}},
        {{"delay_hours": 24, "action": "send_email", "template": "case_study"}},
        {{"delay_hours": 72, "action": "call", "script": "follow_up_script"}},
        {{"delay_hours": 120, "action": "send_email", "template": "pricing"}}
    ]
)

proposal = sa.generate_proposal(
    deal_id="006xx000001abc",
    template="enterprise_proposal",
    line_items=deal.products,
    discount_approval_threshold=0.15
)

sa.send_for_signature(
    proposal_id=proposal.id,
    signers=["john@acme.com", "jane@acme.com"],
    reminder_interval_days=2
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
  "url": "https://your-app.com/webhooks/sales-automator",
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
# HELP grc_claw_sales-automator_requests_total Total requests
# TYPE grc_claw_sales-automator_requests_total counter
grc_claw_sales-automator_requests_total{method="POST",status="200"} 1234
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
