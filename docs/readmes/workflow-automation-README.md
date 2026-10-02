# Workflow Automation

## Project Overview

Marketing workflow automation platform that connects tools, automates repetitive tasks, and orchestrates complex multi-step marketing processes.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `workflow-automation` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Visual workflow builder with drag-and-drop interface
- Pre-built integrations with 100+ marketing tools
- Conditional logic, branching, and loops
- Error handling, retries, and fallback actions
- Workflow templates for common marketing processes
- Real-time workflow monitoring and logging
- Webhook and API trigger support
- Workflow performance analytics and optimization

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/workflow-automation

# Using pip
pip install grc-claw-workflow-automation
```

### Basic Usage

```python
from grc_claw import WorkflowAutomation

wa = WorkflowAutomation()

workflow = wa.create_workflow(
    name="Lead Nurture Sequence",
    trigger={{"type": "crm_event", "event": "lead_created"}},
    steps=[
        {{"action": "enrich_lead", "service": "clearbit"}},
        {{"action": "condition", "if": "lead.score > 50", "then": "add_to_hot_list", "else": "add_to_nurture"}},
        {{"action": "send_email", "template": "welcome_series_1", "delay_minutes": 0}},
        {{"action": "wait", "delay_hours": 24}},
        {{"action": "send_email", "template": "welcome_series_2", "delay_minutes": 0}},
        {{"action": "update_crm", "field": "status", "value": "nurtured"}}
    ]
)

execution = wa.execute_workflow(
    workflow_id=workflow.id,
    input_data={{"lead_id": "lead_123", "email": "prospect@company.com"}}
)

logs = wa.get_logs(execution_id=execution.id)
for log in logs:
    print(f"[{{log.timestamp}}] {{log.step}}: {{log.status}} — {{log.message}}")
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `WORKFLOW_EXECUTION_INTERVAL` | Workflow check interval in seconds (default: 60) |
| `MAX_WORKFLOW_STEPS` | Maximum steps per workflow (default: 100) |
| `RETRY_POLICY` | Retry policy: max_attempts, backoff |
| `ERROR_NOTIFICATION_CHANNELS` | Error notification channels |
| `INTEGRATION_CREDENTIALS` | Integration credentials store |
| `WORKFLOW_TEMPLATES_DIR` | Workflow template directory |
| `LOG_RETENTION_DAYS` | Log retention period (default: 90) |

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
docker build -t grc-claw/workflow-automation .
docker run -p 3000:3000 --env-file .env grc-claw/workflow-automation
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workflow-automation
  labels:
    app: workflow-automation
spec:
  replicas: 2
  selector:
    matchLabels:
      app: workflow-automation
  template:
    metadata:
      labels:
        app: workflow-automation
    spec:
      containers:
      - name: workflow-automation
        image: grc-claw/workflow-automation:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: workflow-automation
spec:
  selector:
    app: workflow-automation
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

- `POST /api/v1/workflows - Create workflow`
- `GET /api/v1/workflows/{id} - Get workflow details`
- `POST /api/v1/workflows/{id}/execute - Execute workflow`
- `POST /api/v1/workflows/{id}/pause - Pause workflow`
- `POST /api/v1/workflows/{id}/resume - Resume workflow`
- `GET /api/v1/workflows/{id}/logs - Get execution logs`
- `GET /api/v1/workflows/{id}/analytics - Get workflow analytics`

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
from grc_claw import WorkflowAutomation

wa = WorkflowAutomation()

workflow = wa.create_workflow(
    name="Lead Nurture Sequence",
    trigger={{"type": "crm_event", "event": "lead_created"}},
    steps=[
        {{"action": "enrich_lead", "service": "clearbit"}},
        {{"action": "condition", "if": "lead.score > 50", "then": "add_to_hot_list", "else": "add_to_nurture"}},
        {{"action": "send_email", "template": "welcome_series_1", "delay_minutes": 0}},
        {{"action": "wait", "delay_hours": 24}},
        {{"action": "send_email", "template": "welcome_series_2", "delay_minutes": 0}},
        {{"action": "update_crm", "field": "status", "value": "nurtured"}}
    ]
)

execution = wa.execute_workflow(
    workflow_id=workflow.id,
    input_data={{"lead_id": "lead_123", "email": "prospect@company.com"}}
)

logs = wa.get_logs(execution_id=execution.id)
for log in logs:
    print(f"[{{log.timestamp}}] {{log.step}}: {{log.status}} — {{log.message}}")
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
  "url": "https://your-app.com/webhooks/workflow-automation",
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
# HELP grc_claw_workflow-automation_requests_total Total requests
# TYPE grc_claw_workflow-automation_requests_total counter
grc_claw_workflow-automation_requests_total{method="POST",status="200"} 1234
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
