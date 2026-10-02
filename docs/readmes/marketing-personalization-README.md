# Marketing Personalization

## Project Overview

Real-time marketing personalization engine that delivers individualized content, offers, and experiences across all touchpoints.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `marketing-personalization` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Real-time behavioral personalization
- Dynamic content blocks and recommendations
- Personalized product and content suggestions
- 1:1 email and web personalization
- AI-generated personalized copy variants
- Personalization rule engine with conditions
- Cross-device personalization consistency
- Personalization performance analytics and optimization

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/marketing-personalization

# Using pip
pip install grc-claw-marketing-personalization
```

### Basic Usage

```python
from grc_claw import MarketingPersonalization

mp = MarketingPersonalization(
    real_time=True,
    depth="individual",
    fallback_strategy="popular"
)

experience = mp.personalize_web(
    user_id="user_123",
    page="homepage",
    slots=["hero", "product_recommendations", "cta_banner"]
)

for slot, content in experience.slots.items():
    print(f"{{slot}}: {{content.variant_name}} (relevance: {{content.relevance_score:.2f}})")

email = mp.personalize_email(
    template="monthly_newsletter",
    user_id="user_123",
    dynamic_blocks=["hero_image", "product_picks", "headline", "cta_text"]
)

mp.create_rule(
    name="High-Value Customer Hero",
    condition="customer_lifetime_value > 10000",
    action="show_premium_hero",
    priority=10
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `PERSONALIZATION_ENGINE` | Personalization engine endpoint |
| `REAL_TIME_ENABLED` | Enable real-time personalization (default: true) |
| `PERSONALIZATION_DEPTH` | Depth: segment, individual, contextual |
| `CONTENT_VARIANTS_PER_SLOT` | Max variants per content slot (default: 5) |
| `ML_PERSONALIZATION_MODEL` | ML model for personalization |
| `FALLBACK_STRATEGY` | Fallback when no personalization match |
| `PERSONALIZATION_CACHE_TTL_SECONDS` | Cache TTL (default: 300) |

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
docker build -t grc-claw/marketing-personalization .
docker run -p 3000:3000 --env-file .env grc-claw/marketing-personalization
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: marketing-personalization
  labels:
    app: marketing-personalization
spec:
  replicas: 2
  selector:
    matchLabels:
      app: marketing-personalization
  template:
    metadata:
      labels:
        app: marketing-personalization
    spec:
      containers:
      - name: marketing-personalization
        image: grc-claw/marketing-personalization:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: marketing-personalization
spec:
  selector:
    app: marketing-personalization
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

- `POST /api/v1/personalize/content - Get personalized content`
- `POST /api/v1/personalize/email - Personalize email content`
- `POST /api/v1/personalize/web - Personalize web experience`
- `POST /api/v1/personalize/recommendations - Get personalized recommendations`
- `GET /api/v1/personalize/{user_id}/profile - Get personalization profile`
- `POST /api/v1/personalize/rules - Create personalization rule`
- `GET /api/v1/personalize/performance - Get personalization performance`

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
from grc_claw import MarketingPersonalization

mp = MarketingPersonalization(
    real_time=True,
    depth="individual",
    fallback_strategy="popular"
)

experience = mp.personalize_web(
    user_id="user_123",
    page="homepage",
    slots=["hero", "product_recommendations", "cta_banner"]
)

for slot, content in experience.slots.items():
    print(f"{{slot}}: {{content.variant_name}} (relevance: {{content.relevance_score:.2f}})")

email = mp.personalize_email(
    template="monthly_newsletter",
    user_id="user_123",
    dynamic_blocks=["hero_image", "product_picks", "headline", "cta_text"]
)

mp.create_rule(
    name="High-Value Customer Hero",
    condition="customer_lifetime_value > 10000",
    action="show_premium_hero",
    priority=10
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
  "url": "https://your-app.com/webhooks/marketing-personalization",
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
# HELP grc_claw_marketing-personalization_requests_total Total requests
# TYPE grc_claw_marketing-personalization_requests_total counter
grc_claw_marketing-personalization_requests_total{method="POST",status="200"} 1234
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
