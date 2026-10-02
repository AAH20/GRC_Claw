# Feedback Management

## Project Overview

Customer feedback management platform that collects, analyzes, and routes customer feedback to drive product and service improvements.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `feedback-management` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Multi-channel feedback collection (surveys, NPS, reviews, support tickets)
- Sentiment analysis and emotion detection
- Feedback categorization and tagging
- Automated feedback routing to relevant teams
- Customer effort score (CES) tracking
- Feedback trend analysis and alerting
- Closed-loop feedback follow-up automation
- Feedback-driven product insights dashboard

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/feedback-management

# Using pip
pip install grc-claw-feedback-management
```

### Basic Usage

```python
from grc_claw import FeedbackManagement

fm = FeedbackManagement(
    sources=["nps_survey", "support_tickets", "app_reviews"],
    closed_loop=True
)

feedback = fm.collect(
    source="nps_survey",
    user_id="user_123",
    score=9,
    comment="Love the new dashboard! Would be great to have dark mode."
)

analysis = fm.analyze(feedback.id)
print(f"Sentiment: {{analysis.sentiment}} | Emotion: {{analysis.emotion}}")
print(f"Category: {{analysis.category}} | Priority: {{analysis.priority}}")

fm.route(
    feedback_id=feedback.id,
    team="product",
    assignee="product_manager_1",
    due_date="2024-02-01"
)

trends = fm.get_trends(
    period="last_30_days",
    metrics=["nps", "sentiment", "category_breakdown"]
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `FEEDBACK_SOURCES` | Feedback collection sources |
| `SENTIMENT_MODEL` | Sentiment analysis model |
| `NPS_SURVEY_SCHEDULE` | NPS survey schedule (cron expression) |
| `FEEDBACK_CATEGORIES` | Feedback category definitions |
| `ROUTING_RULES` | Feedback routing rules by category |
| `CLOSED_LOOP_ENABLED` | Enable closed-loop follow-up (default: true) |
| `ALERT_THRESHOLDS` | Alert thresholds for feedback metrics |

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
docker build -t grc-claw/feedback-management .
docker run -p 3000:3000 --env-file .env grc-claw/feedback-management
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: feedback-management
  labels:
    app: feedback-management
spec:
  replicas: 2
  selector:
    matchLabels:
      app: feedback-management
  template:
    metadata:
      labels:
        app: feedback-management
    spec:
      containers:
      - name: feedback-management
        image: grc-claw/feedback-management:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: feedback-management
spec:
  selector:
    app: feedback-management
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

- `POST /api/v1/feedback/collect - Collect feedback`
- `GET /api/v1/feedback - List feedback`
- `POST /api/v1/feedback/{id}/analyze - Analyze feedback sentiment`
- `POST /api/v1/feedback/{id}/route - Route feedback to team`
- `POST /api/v1/feedback/{id}/follow-up - Trigger follow-up`
- `GET /api/v1/feedback/trends - Get feedback trends`
- `GET /api/v1/feedback/insights - Get product insights`

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
from grc_claw import FeedbackManagement

fm = FeedbackManagement(
    sources=["nps_survey", "support_tickets", "app_reviews"],
    closed_loop=True
)

feedback = fm.collect(
    source="nps_survey",
    user_id="user_123",
    score=9,
    comment="Love the new dashboard! Would be great to have dark mode."
)

analysis = fm.analyze(feedback.id)
print(f"Sentiment: {{analysis.sentiment}} | Emotion: {{analysis.emotion}}")
print(f"Category: {{analysis.category}} | Priority: {{analysis.priority}}")

fm.route(
    feedback_id=feedback.id,
    team="product",
    assignee="product_manager_1",
    due_date="2024-02-01"
)

trends = fm.get_trends(
    period="last_30_days",
    metrics=["nps", "sentiment", "category_breakdown"]
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
  "url": "https://your-app.com/webhooks/feedback-management",
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
# HELP grc_claw_feedback-management_requests_total Total requests
# TYPE grc_claw_feedback-management_requests_total counter
grc_claw_feedback-management_requests_total{method="POST",status="200"} 1234
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
