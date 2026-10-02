# Social Media Manager

## Project Overview

Comprehensive social media management platform for scheduling, publishing, monitoring, and analyzing social media presence across all major networks.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `social-media-manager` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Multi-platform publishing (Twitter/X, LinkedIn, Facebook, Instagram, TikTok)
- Content calendar with visual scheduling and drag-and-drop
- Social listening and brand mention monitoring
- Engagement management with unified inbox
- Hashtag research and trending topic detection
- Competitor social media analysis
- Influencer identification and outreach management
- Social media analytics and reporting dashboards

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/social-media-manager

# Using pip
pip install grc-claw-social-media-manager
```

### Basic Usage

```python
from grc_claw import SocialMediaManager

smm = SocialMediaManager(
    platforms=["twitter", "linkedin", "instagram"],
    brand_voice="professional_engaging"
)

post = smm.schedule_post(
    content="Excited to announce our new product launch!",
    platforms=["twitter", "linkedin"],
    scheduled_time="2024-01-15T09:00:00Z",
    media=["product_launch.png"]
)

mentions = smm.get_mentions(
    keywords=["@YourBrand", "#YourProduct"],
    since="2024-01-01",
    sentiment="all"
)

for mention in mentions.positive:
    smm.reply(mention, template="thank_you_response")
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `PLATFORMS` | Enabled platforms: twitter,linkedin,facebook,instagram,tiktok |
| `POSTING_SCHEDULE` | Default posting schedule configuration |
| `SOCIAL_LISTENING_KEYWORDS` | Keywords to monitor for brand mentions |
| `AUTO_RESPONDER_ENABLED` | Enable automated responses (default: false) |
| `ANALYTICS_REFRESH_INTERVAL` | Analytics refresh in minutes (default: 60) |
| `API_CREDENTIALS` | Platform API keys and tokens |
| `CONTENT_APPROVAL_WORKFLOW` | Enable approval workflow (default: true) |

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
docker build -t grc-claw/social-media-manager .
docker run -p 3000:3000 --env-file .env grc-claw/social-media-manager
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: social-media-manager
  labels:
    app: social-media-manager
spec:
  replicas: 2
  selector:
    matchLabels:
      app: social-media-manager
  template:
    metadata:
      labels:
        app: social-media-manager
    spec:
      containers:
      - name: social-media-manager
        image: grc-claw/social-media-manager:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: social-media-manager
spec:
  selector:
    app: social-media-manager
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

- `POST /api/v1/posts/schedule - Schedule a post`
- `GET /api/v1/posts/calendar - Get content calendar`
- `POST /api/v1/posts/publish - Publish immediately`
- `GET /api/v1/mentions - Get brand mentions`
- `POST /api/v1/engagement/reply - Reply to a mention or comment`
- `GET /api/v1/analytics/{platform} - Get platform analytics`
- `GET /api/v1/competitors/{handle} - Get competitor analysis`

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
from grc_claw import SocialMediaManager

smm = SocialMediaManager(
    platforms=["twitter", "linkedin", "instagram"],
    brand_voice="professional_engaging"
)

post = smm.schedule_post(
    content="Excited to announce our new product launch!",
    platforms=["twitter", "linkedin"],
    scheduled_time="2024-01-15T09:00:00Z",
    media=["product_launch.png"]
)

mentions = smm.get_mentions(
    keywords=["@YourBrand", "#YourProduct"],
    since="2024-01-01",
    sentiment="all"
)

for mention in mentions.positive:
    smm.reply(mention, template="thank_you_response")
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
  "url": "https://your-app.com/webhooks/social-media-manager",
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
# HELP grc_claw_social-media-manager_requests_total Total requests
# TYPE grc_claw_social-media-manager_requests_total counter
grc_claw_social-media-manager_requests_total{method="POST",status="200"} 1234
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
