# Video Marketing

## Project Overview

Video marketing platform for creating, hosting, optimizing, and analyzing video content across marketing channels.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `video-marketing` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Video creation and editing tools with templates
- Video hosting with customizable player
- Interactive video elements (CTAs, forms, chapters)
- Video SEO optimization and transcript generation
- Video analytics with engagement heatmaps
- Personalized video content at scale
- Video distribution to social and advertising platforms
- Video A/B testing and optimization

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/video-marketing

# Using pip
pip install grc-claw-video-marketing
```

### Basic Usage

```python
from grc_claw import VideoMarketing

vm = VideoMarketing(
    hosting_provider="wistia",
    personalization=True
)

video = vm.create_video(
    template="product_demo",
    title="Product Overview 2024",
    duration_seconds=120,
    brand_assets={{"logo": "logo.png", "colors": ["#FF6B35", "#004E89"]}}
)

vm.add_interactive_elements(
    video_id=video.id,
    elements=[
        {{"type": "cta", "time": 30, "text": "Start Free Trial", "url": "/signup"}},
        {{"type": "form", "time": 60, "fields": ["email"], "text": "Get the full guide"}},
        {{"type": "chapter", "time": 0, "title": "Introduction"}},
        {{"type": "chapter", "time": 30, "title": "Key Features"}}
    ]
)

personalized = vm.personalize(
    video_id=video.id,
    segment="enterprise_prospects",
    variables={{"company_name": "Acme Corp", "contact_name": "John"}}
)

analytics = vm.get_analytics(video_id=video.id)
print(f"Views: {{analytics.views}} | Avg Watch: {{analytics.avg_watch_time}}s")
print(f"Engagement Rate: {{analytics.engagement_rate:.1%}}")
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `VIDEO_HOSTING_PROVIDER` | Video hosting provider (wistia, brightcove, etc.) |
| `CREATION_TEMPLATES_DIR` | Video creation template directory |
| `TRANSCRIPTION_SERVICE` | Transcription service provider |
| `INTERACTIVE_ELEMENTS` | Enabled interactive elements |
| `DISTRIBUTION_CHANNELS` | Video distribution channels |
| `ANALYTICS_PROVIDER` | Video analytics provider |
| `PERSONALIZATION_ENABLED` | Enable video personalization (default: true) |

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
docker build -t grc-claw/video-marketing .
docker run -p 3000:3000 --env-file .env grc-claw/video-marketing
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-marketing
  labels:
    app: video-marketing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: video-marketing
  template:
    metadata:
      labels:
        app: video-marketing
    spec:
      containers:
      - name: video-marketing
        image: grc-claw/video-marketing:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: video-marketing
spec:
  selector:
    app: video-marketing
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

- `POST /api/v1/videos/create - Create video`
- `POST /api/v1/videos/{id}/upload - Upload video`
- `POST /api/v1/videos/{id}/publish - Publish video`
- `POST /api/v1/videos/{id}/personalize - Personalize video`
- `GET /api/v1/videos/{id}/analytics - Get video analytics`
- `POST /api/v1/videos/{id}/distribute - Distribute video`
- `POST /api/v1/videos/{id}/transcribe - Generate transcript`

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
from grc_claw import VideoMarketing

vm = VideoMarketing(
    hosting_provider="wistia",
    personalization=True
)

video = vm.create_video(
    template="product_demo",
    title="Product Overview 2024",
    duration_seconds=120,
    brand_assets={{"logo": "logo.png", "colors": ["#FF6B35", "#004E89"]}}
)

vm.add_interactive_elements(
    video_id=video.id,
    elements=[
        {{"type": "cta", "time": 30, "text": "Start Free Trial", "url": "/signup"}},
        {{"type": "form", "time": 60, "fields": ["email"], "text": "Get the full guide"}},
        {{"type": "chapter", "time": 0, "title": "Introduction"}},
        {{"type": "chapter", "time": 30, "title": "Key Features"}}
    ]
)

personalized = vm.personalize(
    video_id=video.id,
    segment="enterprise_prospects",
    variables={{"company_name": "Acme Corp", "contact_name": "John"}}
)

analytics = vm.get_analytics(video_id=video.id)
print(f"Views: {{analytics.views}} | Avg Watch: {{analytics.avg_watch_time}}s")
print(f"Engagement Rate: {{analytics.engagement_rate:.1%}}")
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
  "url": "https://your-app.com/webhooks/video-marketing",
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
# HELP grc_claw_video-marketing_requests_total Total requests
# TYPE grc_claw_video-marketing_requests_total counter
grc_claw_video-marketing_requests_total{method="POST",status="200"} 1234
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
