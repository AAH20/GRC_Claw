# Content Generator

## Project Overview

AI-powered content generation engine that produces marketing copy, blog posts, social media content, and ad creatives at scale.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `content-generator` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- GPT-powered content generation for blogs, ads, emails, and social posts
- Brand voice customization and tone matching
- SEO-optimized content generation with keyword targeting
- Multi-language content generation and localization
- Content templates for common marketing formats
- Plagiarism checking and originality scoring
- Content performance prediction before publishing
- Batch content generation for campaigns

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/content-generator

# Using pip
pip install grc-claw-content-generator
```

### Basic Usage

```python
from grc_claw import ContentGenerator

gen = ContentGenerator(
    brand_voice="professional_friendly",
    model="gpt-4",
    seo_optimized=True
)

post = gen.blog_post(
    topic="10 Tips for Remote Team Productivity",
    keywords=["remote work", "productivity", "team management"],
    word_count=1500,
    tone="informative"
)

print(f"Title: {{post.title}}")
print(f"SEO Score: {{post.seo_score}}/100")

social_posts = gen.social_posts(
    source_content=post,
    platforms=["twitter", "linkedin", "facebook"],
    count=3
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `LLM_MODEL` | Language model for generation (default: gpt-4) |
| `BRAND_VOICE_PROFILE` | Path to brand voice configuration file |
| `MAX_TOKENS` | Maximum tokens per generation (default: 2000) |
| `TEMPERATURE` | Generation creativity 0.0-1.0 (default: 0.7) |
| `CONTENT_TEMPLATES_DIR` | Directory for content templates |
| `PLAGIARISM_CHECK_ENABLED` | Enable plagiarism detection (default: true) |
| `SUPPORTED_LANGUAGES` | Comma-separated list of supported languages |

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
docker build -t grc-claw/content-generator .
docker run -p 3000:3000 --env-file .env grc-claw/content-generator
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: content-generator
  labels:
    app: content-generator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: content-generator
  template:
    metadata:
      labels:
        app: content-generator
    spec:
      containers:
      - name: content-generator
        image: grc-claw/content-generator:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: content-generator
spec:
  selector:
    app: content-generator
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

- `POST /api/v1/content/generate - Generate content from prompt`
- `POST /api/v1/content/blog-post - Generate blog post`
- `POST /api/v1/content/social-post - Generate social media post`
- `POST /api/v1/content/ad-copy - Generate ad copy`
- `POST /api/v1/content/email - Generate email content`
- `GET /api/v1/content/{id}/score - Get content quality score`
- `POST /api/v1/content/batch - Batch generate content`

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
from grc_claw import ContentGenerator

gen = ContentGenerator(
    brand_voice="professional_friendly",
    model="gpt-4",
    seo_optimized=True
)

post = gen.blog_post(
    topic="10 Tips for Remote Team Productivity",
    keywords=["remote work", "productivity", "team management"],
    word_count=1500,
    tone="informative"
)

print(f"Title: {{post.title}}")
print(f"SEO Score: {{post.seo_score}}/100")

social_posts = gen.social_posts(
    source_content=post,
    platforms=["twitter", "linkedin", "facebook"],
    count=3
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
  "url": "https://your-app.com/webhooks/content-generator",
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
# HELP grc_claw_content-generator_requests_total Total requests
# TYPE grc_claw_content-generator_requests_total counter
grc_claw_content-generator_requests_total{method="POST",status="200"} 1234
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
