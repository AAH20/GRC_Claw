# SEO Optimizer

## Project Overview

Search engine optimization toolkit with automated auditing, keyword research, content optimization, and rank tracking.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `seo-optimizer` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Automated technical SEO audits (crawlability, speed, structured data)
- Keyword research with difficulty and opportunity scoring
- Content optimization with real-time SEO scoring
- Rank tracking with SERP feature monitoring
- Backlink analysis and link building opportunities
- Competitor SEO analysis and gap identification
- Schema markup generator and validator
- Core Web Vitals monitoring and optimization

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/seo-optimizer

# Using pip
pip install grc-claw-seo-optimizer
```

### Basic Usage

```python
from grc_claw import SEOOptimizer

seo = SEOOptimizer(
    site_url="https://example.com",
    search_console_key="gsc_credentials.json"
)

audit = seo.run_audit(
    crawl=True,
    technical=True,
    content=True,
    backlinks=True
)

print(f"Overall Score: {{audit.score}}/100")
for issue in audit.critical_issues:
    print(f"  {{issue.description}} — {{issue.fix_suggestion}}")

optimized = seo.optimize_content(
    content=blog_post_html,
    target_keyword="email marketing automation",
    secondary_keywords=["drip campaigns", "email sequences"]
)

ranks = seo.track_keywords(
    keywords=["email marketing", "marketing automation"],
    location="US",
    language="en"
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `CRAWL_INTERVAL_HOURS` | Site crawl frequency (default: 24) |
| `RANK_CHECK_INTERVAL` | Rank tracking frequency in hours (default: 24) |
| `KEYWORD_DATABASE` | Keyword database: google, bing, alexa |
| `SERP_FEATURES_TO_TRACK` | SERP features: featured_snippet, paa, local_pack |
| `CONTENT_SCORE_THRESHOLD` | Minimum content score (default: 80) |
| `TECHNICAL_AUDIT_RULES` | Path to custom audit rules configuration |
| `GOOGLE_SEARCH_CONSOLE_KEY` | Search Console API credentials |

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
docker build -t grc-claw/seo-optimizer .
docker run -p 3000:3000 --env-file .env grc-claw/seo-optimizer
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: seo-optimizer
  labels:
    app: seo-optimizer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: seo-optimizer
  template:
    metadata:
      labels:
        app: seo-optimizer
    spec:
      containers:
      - name: seo-optimizer
        image: grc-claw/seo-optimizer:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: seo-optimizer
spec:
  selector:
    app: seo-optimizer
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

- `POST /api/v1/audits - Run SEO audit`
- `GET /api/v1/audits/{id} - Get audit results`
- `POST /api/v1/keywords/research - Keyword research`
- `POST /api/v1/content/optimize - Optimize content for SEO`
- `GET /api/v1/ranks/{keyword} - Get keyword rankings`
- `POST /api/v1/backlinks/analyze - Analyze backlink profile`
- `GET /api/v1/competitors/{domain} - Competitor SEO analysis`

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
from grc_claw import SEOOptimizer

seo = SEOOptimizer(
    site_url="https://example.com",
    search_console_key="gsc_credentials.json"
)

audit = seo.run_audit(
    crawl=True,
    technical=True,
    content=True,
    backlinks=True
)

print(f"Overall Score: {{audit.score}}/100")
for issue in audit.critical_issues:
    print(f"  {{issue.description}} — {{issue.fix_suggestion}}")

optimized = seo.optimize_content(
    content=blog_post_html,
    target_keyword="email marketing automation",
    secondary_keywords=["drip campaigns", "email sequences"]
)

ranks = seo.track_keywords(
    keywords=["email marketing", "marketing automation"],
    location="US",
    language="en"
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
  "url": "https://your-app.com/webhooks/seo-optimizer",
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
# HELP grc_claw_seo-optimizer_requests_total Total requests
# TYPE grc_claw_seo-optimizer_requests_total counter
grc_claw_seo-optimizer_requests_total{method="POST",status="200"} 1234
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
