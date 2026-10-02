# Website Optimization

## Project Overview

Website optimization platform for improving conversion rates through A/B testing, personalization, and user experience analysis.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `website-optimization` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- A/B and multivariate testing with statistical significance
- Heatmap and session recording integration
- Conversion rate optimization (CRO) recommendations
- Personalized landing page variants
- Form optimization and funnel analysis
- Page speed monitoring and optimization
- Mobile responsiveness testing
- User journey analysis and drop-off identification

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/website-optimization

# Using pip
pip install grc-claw-website-optimization
```

### Basic Usage

```python
from grc_claw import WebsiteOptimization

wo = WebsiteOptimization(
    testing_provider="optimizely",
    heatmap_provider="hotjar"
)

test = wo.create_test(
    name="Homepage CTA Test",
    page="/",
    variants=[
        {{"name": "control", "cta_text": "Get Started", "cta_color": "blue"}},
        {{"name": "variant_a", "cta_text": "Start Free Trial", "cta_color": "green"}},
        {{"name": "variant_b", "cta_text": "Try It Now", "cta_color": "orange"}}
    ],
    metric="cta_click_rate",
    min_sample_size=2000
)

results = wo.get_results(test.id)
print(f"Winner: {{results.winner}} | Lift: {{results.lift:.1%}} | Confidence: {{results.confidence:.1%}}")

recommendations = wo.get_recommendations(
    page="/pricing",
    focus_areas=["form", "cta", "social_proof"]
)

for rec in recommendations:
    print(f"  -> {{rec.area}}: {{rec.suggestion}} (expected lift: {{rec.expected_lift:.1%}})")
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `TESTING_PROVIDER` | A/B testing provider (optimizely, VWO, etc.) |
| `HEATMAP_PROVIDER` | Heatmap tool (hotjar, crazyegg, etc.) |
| `SIGNIFICANCE_THRESHOLD` | Statistical significance threshold (default: 0.95) |
| `MIN_SAMPLE_SIZE` | Minimum sample size per variant (default: 1000) |
| `PERSONALIZATION_RULES` | Personalization rule definitions |
| `PAGE_SPEED_BUDGET` | Page speed performance budget |
| `FUNNEL_DEFINITIONS` | Conversion funnel definitions |

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
docker build -t grc-claw/website-optimization .
docker run -p 3000:3000 --env-file .env grc-claw/website-optimization
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: website-optimization
  labels:
    app: website-optimization
spec:
  replicas: 2
  selector:
    matchLabels:
      app: website-optimization
  template:
    metadata:
      labels:
        app: website-optimization
    spec:
      containers:
      - name: website-optimization
        image: grc-claw/website-optimization:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: website-optimization
spec:
  selector:
    app: website-optimization
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

- `POST /api/v1/tests - Create A/B test`
- `GET /api/v1/tests/{id} - Get test results`
- `POST /api/v1/tests/{id}/winner - Declare winner`
- `POST /api/v1/personalization - Create personalization rule`
- `GET /api/v1/funnels/{id} - Get funnel analysis`
- `GET /api/v1/speed - Get page speed metrics`
- `POST /api/v1/recommendations - Get CRO recommendations`

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
from grc_claw import WebsiteOptimization

wo = WebsiteOptimization(
    testing_provider="optimizely",
    heatmap_provider="hotjar"
)

test = wo.create_test(
    name="Homepage CTA Test",
    page="/",
    variants=[
        {{"name": "control", "cta_text": "Get Started", "cta_color": "blue"}},
        {{"name": "variant_a", "cta_text": "Start Free Trial", "cta_color": "green"}},
        {{"name": "variant_b", "cta_text": "Try It Now", "cta_color": "orange"}}
    ],
    metric="cta_click_rate",
    min_sample_size=2000
)

results = wo.get_results(test.id)
print(f"Winner: {{results.winner}} | Lift: {{results.lift:.1%}} | Confidence: {{results.confidence:.1%}}")

recommendations = wo.get_recommendations(
    page="/pricing",
    focus_areas=["form", "cta", "social_proof"]
)

for rec in recommendations:
    print(f"  -> {{rec.area}}: {{rec.suggestion}} (expected lift: {{rec.expected_lift:.1%}})")
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
  "url": "https://your-app.com/webhooks/website-optimization",
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
# HELP grc_claw_website-optimization_requests_total Total requests
# TYPE grc_claw_website-optimization_requests_total counter
grc_claw_website-optimization_requests_total{method="POST",status="200"} 1234
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
