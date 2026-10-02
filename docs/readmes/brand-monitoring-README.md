# Brand Monitoring

## Project Overview

Brand monitoring platform that tracks brand mentions, sentiment, and share of voice across online channels in real-time.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `brand-monitoring` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Real-time brand mention tracking across web and social
- Sentiment analysis and emotion detection
- Share of voice measurement vs. competitors
- Brand reputation scoring and trend analysis
- Crisis detection and alerting
- Influencer and advocate identification
- Brand mention geolocation tracking
- Competitive brand benchmarking

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/brand-monitoring

# Using pip
pip install grc-claw-brand-monitoring
```

### Basic Usage

```python
from grc_claw import BrandMonitoring

bm = BrandMonitoring(
    brand_keywords=["YourBrand", "@YourBrand", "#YourProduct"],
    sources=["web", "social", "news", "reviews"],
    crisis_threshold=-0.7
)

mentions = bm.get_mentions(
    since="2024-01-01",
    sentiment="all",
    limit=100
)

for mention in mentions:
    print(f"[{{mention.source}}] {{mention.sentiment}}: {{mention.text[:80]}}...")

sentiment = bm.get_sentiment(
    period="last_30_days",
    breakdown_by="source"
)

print(f"Overall: {{sentiment.overall:.2f}} | "
      f"Positive: {{sentiment.positive:.1%}} | "
      f"Negative: {{sentiment.negative:.1%}}")

sov = bm.get_share_of_voice(
    competitors=["CompetitorA", "CompetitorB"],
    period="last_30_days"
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `BRAND_KEYWORDS` | Brand keywords and variations to monitor |
| `MONITORING_SOURCES` | Sources: web, social, news, forums, reviews |
| `SENTIMENT_MODEL` | Sentiment analysis model |
| `ALERT_CHANNELS` | Alert channels: email, slack, sms |
| `CRISIS_DETECTION_THRESHOLD` | Crisis detection threshold (default: -0.7) |
| `SHARE_OF_VOICE_METRICS` | SOV metrics configuration |
| `COMPETITOR_BRANDS` | Competitor brands to track |

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
docker build -t grc-claw/brand-monitoring .
docker run -p 3000:3000 --env-file .env grc-claw/brand-monitoring
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: brand-monitoring
  labels:
    app: brand-monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: brand-monitoring
  template:
    metadata:
      labels:
        app: brand-monitoring
    spec:
      containers:
      - name: brand-monitoring
        image: grc-claw/brand-monitoring:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: brand-monitoring
spec:
  selector:
    app: brand-monitoring
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

- `GET /api/v1/mentions - Get brand mentions`
- `GET /api/v1/sentiment - Get sentiment analysis`
- `GET /api/v1/share-of-voice - Get share of voice`
- `GET /api/v1/reputation - Get brand reputation score`
- `POST /api/v1/alerts - Create monitoring alert`
- `GET /api/v1/influencers - Get brand influencers`
- `GET /api/v1/competitors/{brand} - Get competitor brand analysis`

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
from grc_claw import BrandMonitoring

bm = BrandMonitoring(
    brand_keywords=["YourBrand", "@YourBrand", "#YourProduct"],
    sources=["web", "social", "news", "reviews"],
    crisis_threshold=-0.7
)

mentions = bm.get_mentions(
    since="2024-01-01",
    sentiment="all",
    limit=100
)

for mention in mentions:
    print(f"[{{mention.source}}] {{mention.sentiment}}: {{mention.text[:80]}}...")

sentiment = bm.get_sentiment(
    period="last_30_days",
    breakdown_by="source"
)

print(f"Overall: {{sentiment.overall:.2f}} | "
      f"Positive: {{sentiment.positive:.1%}} | "
      f"Negative: {{sentiment.negative:.1%}}")

sov = bm.get_share_of_voice(
    competitors=["CompetitorA", "CompetitorB"],
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
  "url": "https://your-app.com/webhooks/brand-monitoring",
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
# HELP grc_claw_brand-monitoring_requests_total Total requests
# TYPE grc_claw_brand-monitoring_requests_total counter
grc_claw_brand-monitoring_requests_total{method="POST",status="200"} 1234
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
