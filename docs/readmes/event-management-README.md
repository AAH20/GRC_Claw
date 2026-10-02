# Event Management

## Project Overview

Event management platform for planning, promoting, and executing marketing events including webinars, conferences, and trade shows.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `event-management` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Event planning and project management tools
- Event registration and ticketing system
- Event marketing and promotion automation
- Speaker and session management
- Virtual event platform integration
- Attendee engagement and networking tools
- Event analytics and ROI measurement
- Post-event follow-up automation

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/event-management

# Using pip
pip install grc-claw-event-management
```

### Basic Usage

```python
from grc_claw import EventManagement

em = EventManagement(
    registration_provider="eventbrite",
    virtual_platform="zoom"
)

event = em.create_event(
    name="Marketing Automation Summit 2024",
    type="conference",
    date="2024-03-15",
    location="Virtual",
    capacity=1000,
    ticket_tiers=[
        {{"name": "Early Bird", "price": 199, "quantity": 200}},
        {{"name": "Regular", "price": 299, "quantity": 500}},
        {{"name": "VIP", "price": 599, "quantity": 100}}
    ]
)

em.promote_event(
    event_id=event.id,
    channels=["email", "social", "paid_ads"],
    target_audience="marketing_professionals",
    budget=10000
)

registration = em.register(
    event_id=event.id,
    attendee={{"name": "Jane Doe", "email": "jane@company.com", "company": "Acme"}},
    ticket_tier="Early Bird"
)

analytics = em.get_analytics(event_id=event.id)
print(f"Registrations: {{analytics.registrations}} | Revenue: ${{analytics.revenue:,.0f}}")
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `EVENT_TYPES` | Supported event types: webinar, conference, trade_show, meetup |
| `REGISTRATION_PROVIDER` | Registration platform provider |
| `VIRTUAL_EVENT_PLATFORM` | Virtual event platform (zoom, hopin, etc.) |
| `MARKETING_AUTOMATION` | Event marketing automation settings |
| `TICKETING_PROVIDER` | Ticketing platform provider |
| `ANALYTICS_DASHBOARD` | Event analytics dashboard configuration |

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
docker build -t grc-claw/event-management .
docker run -p 3000:3000 --env-file .env grc-claw/event-management
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-management
  labels:
    app: event-management
spec:
  replicas: 2
  selector:
    matchLabels:
      app: event-management
  template:
    metadata:
      labels:
        app: event-management
    spec:
      containers:
      - name: event-management
        image: grc-claw/event-management:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: event-management
spec:
  selector:
    app: event-management
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

- `POST /api/v1/events - Create event`
- `GET /api/v1/events/{id} - Get event details`
- `POST /api/v1/events/{id}/register - Register attendee`
- `POST /api/v1/events/{id}/promote - Launch event promotion`
- `GET /api/v1/events/{id}/attendees - Get attendee list`
- `POST /api/v1/events/{id}/sessions - Add session`
- `GET /api/v1/events/{id}/analytics - Get event analytics`

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
from grc_claw import EventManagement

em = EventManagement(
    registration_provider="eventbrite",
    virtual_platform="zoom"
)

event = em.create_event(
    name="Marketing Automation Summit 2024",
    type="conference",
    date="2024-03-15",
    location="Virtual",
    capacity=1000,
    ticket_tiers=[
        {{"name": "Early Bird", "price": 199, "quantity": 200}},
        {{"name": "Regular", "price": 299, "quantity": 500}},
        {{"name": "VIP", "price": 599, "quantity": 100}}
    ]
)

em.promote_event(
    event_id=event.id,
    channels=["email", "social", "paid_ads"],
    target_audience="marketing_professionals",
    budget=10000
)

registration = em.register(
    event_id=event.id,
    attendee={{"name": "Jane Doe", "email": "jane@company.com", "company": "Acme"}},
    ticket_tier="Early Bird"
)

analytics = em.get_analytics(event_id=event.id)
print(f"Registrations: {{analytics.registrations}} | Revenue: ${{analytics.revenue:,.0f}}")
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
  "url": "https://your-app.com/webhooks/event-management",
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
# HELP grc_claw_event-management_requests_total Total requests
# TYPE grc_claw_event-management_requests_total counter
grc_claw_event-management_requests_total{method="POST",status="200"} 1234
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
