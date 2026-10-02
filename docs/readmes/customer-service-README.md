# Customer Service

## Project Overview

AI-powered customer service platform with intelligent ticketing, chatbot automation, sentiment analysis, and omnichannel support.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `customer-service` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- AI-powered ticket routing and prioritization
- Chatbot with natural language understanding for common queries
- Sentiment analysis and escalation triggers
- Omnichannel support (email, chat, social, phone)
- Knowledge base integration for instant answers
- Customer satisfaction (CSAT) and NPS surveying
- Agent assist with suggested responses and macros
- Service level agreement (SLA) monitoring and alerts

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/customer-service

# Using pip
pip install grc-claw-customer-service
```

### Basic Usage

```python
from grc_claw import CustomerService

cs = CustomerService(
    channels=["email", "chat", "social"],
    chatbot_enabled=True,
    knowledge_base="https://help.company.com"
)

ticket = cs.create_ticket(
    customer_email="user@example.com",
    subject="Cannot access account",
    body="I've been locked out of my account since yesterday.",
    channel="email"
)

print(f"Ticket: {{ticket.id}} | Priority: {{ticket.priority}} | Assigned: {{ticket.assignee}}")

response = cs.chatbot_message(
    session_id="sess_123",
    message="How do I reset my password?"
)

if response.confidence > 0.85:
    cs.send_chat_reply(session_id="sess_123", message=response.answer)
else:
    cs.escalate_to_human(session_id="sess_123", reason="low_confidence")
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `TICKET_ROUTING_MODEL` | Routing model type |
| `CHATBOT_ENABLED` | Enable chatbot (default: true) |
| `CHATBOT_CONFIDENCE_THRESHOLD` | Min confidence for auto-response (default: 0.85) |
| `SENTIMENT_ESCALATION_THRESHOLD` | Sentiment score for escalation (default: -0.5) |
| `SLA_POLICIES` | SLA policy definitions by priority |
| `KNOWLEDGE_BASE_URL` | Knowledge base endpoint |
| `CHANNELS` | Enabled channels: email, chat, social, phone |
| `CSAT_SURVEY_TRIGGER` | CSAT survey trigger: ticket_closed, periodic |

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
docker build -t grc-claw/customer-service .
docker run -p 3000:3000 --env-file .env grc-claw/customer-service
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: customer-service
  labels:
    app: customer-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: customer-service
  template:
    metadata:
      labels:
        app: customer-service
    spec:
      containers:
      - name: customer-service
        image: grc-claw/customer-service:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: customer-service
spec:
  selector:
    app: customer-service
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

- `POST /api/v1/tickets - Create support ticket`
- `GET /api/v1/tickets/{id} - Get ticket details`
- `POST /api/v1/tickets/{id}/reply - Reply to ticket`
- `POST /api/v1/chatbot/message - Send chatbot message`
- `GET /api/v1/sentiment/{ticket_id} - Get ticket sentiment`
- `POST /api/v1/surveys/csat - Send CSAT survey`
- `GET /api/v1/sla/status - Get SLA status`

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
from grc_claw import CustomerService

cs = CustomerService(
    channels=["email", "chat", "social"],
    chatbot_enabled=True,
    knowledge_base="https://help.company.com"
)

ticket = cs.create_ticket(
    customer_email="user@example.com",
    subject="Cannot access account",
    body="I've been locked out of my account since yesterday.",
    channel="email"
)

print(f"Ticket: {{ticket.id}} | Priority: {{ticket.priority}} | Assigned: {{ticket.assignee}}")

response = cs.chatbot_message(
    session_id="sess_123",
    message="How do I reset my password?"
)

if response.confidence > 0.85:
    cs.send_chat_reply(session_id="sess_123", message=response.answer)
else:
    cs.escalate_to_human(session_id="sess_123", reason="low_confidence")
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
  "url": "https://your-app.com/webhooks/customer-service",
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
# HELP grc_claw_customer-service_requests_total Total requests
# TYPE grc_claw_customer-service_requests_total counter
grc_claw_customer-service_requests_total{method="POST",status="200"} 1234
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
