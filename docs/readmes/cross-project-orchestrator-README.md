# Cross-Project Orchestrator

## Project Overview

Orchestration layer that coordinates all 42 GRC Claw marketing projects, managing dependencies, data flow, and unified reporting across the entire platform.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `cross-project-orchestrator` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Centralized project registry and dependency management
- Cross-project data flow and event bus
- Unified configuration and secrets management
- Cross-project analytics and reporting
- Project health monitoring and alerting
- Resource allocation and capacity planning
- Cross-project workflow orchestration
- Unified API gateway and authentication

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/cross-project-orchestrator

# Using pip
pip install grc-claw-cross-project-orchestrator
```

### Basic Usage

```python
from grc_claw import CrossProjectOrchestrator

cpo = CrossProjectOrchestrator(
    event_bus="kafka",
    secrets_manager="vault",
    api_gateway="https://api.grc-claw.com"
)

projects = cpo.list_projects()
for p in projects:
    print(f"{{p.name}}: {{p.status}} | Health: {{p.health_score}}/100")

cpo.publish_event(
    event_type="lead.converted",
    source="lead-scorer",
    targets=["crm-enhancer", "sales-automator", "analytics"],
    payload={{"lead_id": "lead_123", "score": 85, "grade": "hot"}}
)

workflow = cpo.create_cross_project_workflow(
    name="Lead-to-Cash",
    steps=[
        {{"project": "lead-scorer", "action": "score_lead"}},
        {{"project": "crm-enhancer", "action": "enrich_and_route"}},
        {{"project": "sales-automator", "action": "create_task"}},
        {{"project": "analytics", "action": "track_conversion"}}
    ]
)

analytics = cpo.get_unified_analytics(
    projects=["campaign-optimizer", "lead-scorer", "analytics"],
    metrics=["revenue", "conversions", "roas"],
    period="last_30_days"
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `PROJECT_REGISTRY` | Project registry configuration path |
| `EVENT_BUS_PROVIDER` | Event bus provider (kafka, rabbitmq, sqs) |
| `SECRETS_MANAGER` | Secrets manager (vault, aws_sm, azure_kv) |
| `API_GATEWAY_URL` | Unified API gateway URL |
| `MONITORING_DASHBOARD` | Monitoring dashboard configuration |
| `RESOURCE_LIMITS` | Resource limits per project |
| `CROSS_PROJECT_AUTH` | Cross-project authentication configuration |

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
docker build -t grc-claw/cross-project-orchestrator .
docker run -p 3000:3000 --env-file .env grc-claw/cross-project-orchestrator
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cross-project-orchestrator
  labels:
    app: cross-project-orchestrator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cross-project-orchestrator
  template:
    metadata:
      labels:
        app: cross-project-orchestrator
    spec:
      containers:
      - name: cross-project-orchestrator
        image: grc-claw/cross-project-orchestrator:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: cross-project-orchestrator
spec:
  selector:
    app: cross-project-orchestrator
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

- `GET /api/v1/projects - List all projects`
- `GET /api/v1/projects/{id} - Get project details`
- `POST /api/v1/projects/{id}/health - Get project health`
- `POST /api/v1/events/publish - Publish cross-project event`
- `GET /api/v1/analytics/unified - Get unified analytics`
- `POST /api/v1/workflows/cross-project - Create cross-project workflow`
- `GET /api/v1/config/{project_id} - Get project configuration`

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
from grc_claw import CrossProjectOrchestrator

cpo = CrossProjectOrchestrator(
    event_bus="kafka",
    secrets_manager="vault",
    api_gateway="https://api.grc-claw.com"
)

projects = cpo.list_projects()
for p in projects:
    print(f"{{p.name}}: {{p.status}} | Health: {{p.health_score}}/100")

cpo.publish_event(
    event_type="lead.converted",
    source="lead-scorer",
    targets=["crm-enhancer", "sales-automator", "analytics"],
    payload={{"lead_id": "lead_123", "score": 85, "grade": "hot"}}
)

workflow = cpo.create_cross_project_workflow(
    name="Lead-to-Cash",
    steps=[
        {{"project": "lead-scorer", "action": "score_lead"}},
        {{"project": "crm-enhancer", "action": "enrich_and_route"}},
        {{"project": "sales-automator", "action": "create_task"}},
        {{"project": "analytics", "action": "track_conversion"}}
    ]
)

analytics = cpo.get_unified_analytics(
    projects=["campaign-optimizer", "lead-scorer", "analytics"],
    metrics=["revenue", "conversions", "roas"],
    period="last_30_days"
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
  "url": "https://your-app.com/webhooks/cross-project-orchestrator",
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
# HELP grc_claw_cross-project-orchestrator_requests_total Total requests
# TYPE grc_claw_cross-project-orchestrator_requests_total counter
grc_claw_cross-project-orchestrator_requests_total{method="POST",status="200"} 1234
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
