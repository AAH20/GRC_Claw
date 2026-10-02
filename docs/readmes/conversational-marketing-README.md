# Conversational Marketing

## Project Overview

Conversational marketing platform with AI chatbots, live chat, and messaging automation for real-time customer engagement.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `conversational-marketing` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- AI-powered chatbot with natural language understanding
- Live chat with agent routing and queue management
- WhatsApp, Messenger, and SMS messaging automation
- Conversational lead qualification and routing
- Chatbot analytics and conversation optimization
- Multilingual chatbot support
- Integration with CRM and marketing automation
- Conversational commerce and booking capabilities

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/conversational-marketing

# Using pip
pip install grc-claw-conversational-marketing
```

### Basic Usage

```python
from grc_claw import ConversationalMarketing

cm = ConversationalMarketing(
    chatbot_provider="dialogflow",
    channels=["web", "whatsapp", "messenger"]
)

response = cm.chatbot_message(
    session_id="sess_123",
    message="What's your pricing for the enterprise plan?"
)

print(f"Bot: {{response.message}}")
print(f"Confidence: {{response.confidence:.2f}}")

if response.confidence < 0.7:
    cm.transfer_to_agent(
        session_id="sess_123",
        agent_team="sales",
        context=response.context
    )

campaign = cm.send_messaging_campaign(
    channel="whatsapp",
    template="product_launch_announcement",
    audience="opted_in_contacts",
    personalization={{"name": "first_name"}}
)

analytics = cm.get_chatbot_analytics(
    period="last_30_days",
    metrics=["resolution_rate", "csat", "handoff_rate", "conversation_length"]
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `CHATBOT_PROVIDER` | Chatbot platform provider |
| `NLU_MODEL` | NLU model type |
| `LIVE_CHAT_PROVIDER` | Live chat provider |
| `MESSAGING_CHANNELS` | Enabled channels: whatsapp, messenger, sms, web |
| `AGENT_ROUTING_RULES` | Agent routing rules |
| `CHATBOT_FALLBACK` | Fallback action for unknown queries |
| `MULTILINGUAL_ENABLED` | Enable multilingual support (default: true) |

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
docker build -t grc-claw/conversational-marketing .
docker run -p 3000:3000 --env-file .env grc-claw/conversational-marketing
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: conversational-marketing
  labels:
    app: conversational-marketing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: conversational-marketing
  template:
    metadata:
      labels:
        app: conversational-marketing
    spec:
      containers:
      - name: conversational-marketing
        image: grc-claw/conversational-marketing:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: conversational-marketing
spec:
  selector:
    app: conversational-marketing
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

- `POST /api/v1/chatbot/message - Send chatbot message`
- `POST /api/v1/chatbot/train - Train chatbot with new data`
- `POST /api/v1/live-chat/start - Start live chat session`
- `POST /api/v1/live-chat/transfer - Transfer to agent`
- `POST /api/v1/messaging/send - Send messaging campaign`
- `GET /api/v1/conversations - Get conversation history`
- `GET /api/v1/chatbot/analytics - Get chatbot analytics`

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
from grc_claw import ConversationalMarketing

cm = ConversationalMarketing(
    chatbot_provider="dialogflow",
    channels=["web", "whatsapp", "messenger"]
)

response = cm.chatbot_message(
    session_id="sess_123",
    message="What's your pricing for the enterprise plan?"
)

print(f"Bot: {{response.message}}")
print(f"Confidence: {{response.confidence:.2f}}")

if response.confidence < 0.7:
    cm.transfer_to_agent(
        session_id="sess_123",
        agent_team="sales",
        context=response.context
    )

campaign = cm.send_messaging_campaign(
    channel="whatsapp",
    template="product_launch_announcement",
    audience="opted_in_contacts",
    personalization={{"name": "first_name"}}
)

analytics = cm.get_chatbot_analytics(
    period="last_30_days",
    metrics=["resolution_rate", "csat", "handoff_rate", "conversation_length"]
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
  "url": "https://your-app.com/webhooks/conversational-marketing",
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
# HELP grc_claw_conversational-marketing_requests_total Total requests
# TYPE grc_claw_conversational-marketing_requests_total counter
grc_claw_conversational-marketing_requests_total{method="POST",status="200"} 1234
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
