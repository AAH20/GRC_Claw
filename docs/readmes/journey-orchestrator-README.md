# Journey Orchestrator

## Project Overview

Customer journey orchestration platform that designs, executes, and optimizes multi-channel customer journeys from awareness to advocacy.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `journey-orchestrator` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Visual journey builder with drag-and-drop interface
- Multi-channel journey execution (email, SMS, push, web, ads)
- Real-time journey branching based on customer behavior
- Journey analytics with funnel and drop-off analysis
- A/B testing for journey paths and content
- Journey templates for common use cases (onboarding, renewal, win-back)
- Integration with CRM and CDP for unified customer profiles
- Journey performance scoring and optimization suggestions

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/journey-orchestrator

# Using pip
pip install grc-claw-journey-orchestrator
```

### Basic Usage

```python
from grc_claw import JourneyOrchestrator

orch = JourneyOrchestrator()

journey = orch.create_journey(
    name="New Customer Onboarding",
    entry_trigger="signup_complete",
    steps=[
        {{"type": "email", "delay": 0, "template": "welcome"}},
        {{"type": "wait", "delay_hours": 24}},
        {{"type": "condition", "field": "email_opened", "if_true": "send_tip", "if_false": "send_reminder"}},
        {{"type": "email", "template": "getting_started_guide"}},
        {{"type": "wait", "delay_hours": 72}},
        {{"type": "condition", "field": "activation_complete", "if_true": "exit", "if_false": "escalate"}}
    ]
)

orch.activate(journey.id)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `JOURNEY_EXECUTION_INTERVAL` | Journey evaluation frequency in minutes (default: 5) |
| `MAX_JOURNEY_STEPS` | Maximum steps per journey (default: 50) |
| `CHANNEL_PRIORITY` | Channel fallback order: email,sms,push |
| `JOURNEY_TIMEOUT_HOURS` | Maximum journey duration (default: 720) |
| `TEMPLATE_LIBRARY_PATH` | Path to journey template library |
| `PERSONALIZATION_ENGINE` | Personalization engine endpoint URL |

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
docker build -t grc-claw/journey-orchestrator .
docker run -p 3000:3000 --env-file .env grc-claw/journey-orchestrator
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: journey-orchestrator
  labels:
    app: journey-orchestrator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: journey-orchestrator
  template:
    metadata:
      labels:
        app: journey-orchestrator
    spec:
      containers:
      - name: journey-orchestrator
        image: grc-claw/journey-orchestrator:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: journey-orchestrator
spec:
  selector:
    app: journey-orchestrator
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

- `POST /api/v1/journeys - Create a new journey`
- `GET /api/v1/journeys/{id} - Get journey details`
- `POST /api/v1/journeys/{id}/activate - Activate a journey`
- `POST /api/v1/journeys/{id}/deactivate - Deactivate a journey`
- `GET /api/v1/journeys/{id}/analytics - Get journey analytics`
- `POST /api/v1/journeys/{id}/test - Test journey with sample contacts`

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
from grc_claw import JourneyOrchestrator

orch = JourneyOrchestrator()

journey = orch.create_journey(
    name="New Customer Onboarding",
    entry_trigger="signup_complete",
    steps=[
        {{"type": "email", "delay": 0, "template": "welcome"}},
        {{"type": "wait", "delay_hours": 24}},
        {{"type": "condition", "field": "email_opened", "if_true": "send_tip", "if_false": "send_reminder"}},
        {{"type": "email", "template": "getting_started_guide"}},
        {{"type": "wait", "delay_hours": 72}},
        {{"type": "condition", "field": "activation_complete", "if_true": "exit", "if_false": "escalate"}}
    ]
)

orch.activate(journey.id)
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
  "url": "https://your-app.com/webhooks/journey-orchestrator",
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
# HELP grc_claw_journey-orchestrator_requests_total Total requests
# TYPE grc_claw_journey-orchestrator_requests_total counter
grc_claw_journey-orchestrator_requests_total{method="POST",status="200"} 1234
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
