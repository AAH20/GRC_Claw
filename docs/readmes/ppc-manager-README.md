# PPC Manager

## Project Overview

Pay-per-click advertising management platform for Google Ads, Microsoft Ads, and programmatic display with automated bidding and budget optimization.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `ppc-manager` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Cross-platform PPC management (Google, Microsoft, Meta, programmatic)
- Automated bidding strategies (Target CPA, Target ROAS, Maximize Conversions)
- Keyword research and expansion suggestions
- Negative keyword management and search term analysis
- Ad copy generation and A/B testing
- Landing page quality scoring and recommendations
- Budget pacing and dayparting automation
- Competitor auction insights and share of voice tracking

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/ppc-manager

# Using pip
pip install grc-claw-ppc-manager
```

### Basic Usage

```python
from grc_claw import PPCManager

ppc = PPCManager(
    platforms=["google_ads", "microsoft_ads"],
    default_strategy="target_roas",
    target_roas=4.0
)

campaign = ppc.create_campaign(
    name="Spring Sale 2024",
    type="search",
    budget_daily=500,
    keywords=["spring sale", "seasonal discount", "limited offer"],
    strategy="target_roas"
)

suggestions = ppc.keyword_research(
    seed_keywords=["digital marketing", "online advertising"],
    language="en",
    location="US"
)

ads = ppc.generate_ads(
    keywords=suggestions[:10],
    headlines_count=5,
    descriptions_count=3,
    tone="persuasive"
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `PLATFORMS` | Enabled platforms: google_ads, microsoft_ads, meta_ads |
| `DEFAULT_BIDDING_STRATEGY` | Default bidding strategy (default: target_roas) |
| `TARGET_ROAS` | Target return on ad spend (default: 4.0) |
| `TARGET_CPA` | Target cost per acquisition (default: 50) |
| `BUDGET_PACING_MODE` | Pacing mode: standard, accelerated |
| `API_CREDENTIALS` | Platform API credentials |
| `NEGATIVE_KEYWORD_LISTS` | Shared negative keyword lists |
| `QUALITY_SCORE_THRESHOLD` | Minimum quality score (default: 7) |

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
docker build -t grc-claw/ppc-manager .
docker run -p 3000:3000 --env-file .env grc-claw/ppc-manager
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ppc-manager
  labels:
    app: ppc-manager
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ppc-manager
  template:
    metadata:
      labels:
        app: ppc-manager
    spec:
      containers:
      - name: ppc-manager
        image: grc-claw/ppc-manager:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: ppc-manager
spec:
  selector:
    app: ppc-manager
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

- `POST /api/v1/campaigns - Create PPC campaign`
- `GET /api/v1/campaigns/{id}/performance - Get campaign performance`
- `POST /api/v1/keywords/research - Get keyword suggestions`
- `POST /api/v1/ads/generate - Generate ad copy`
- `POST /api/v1/bidding/adjust - Adjust bids`
- `GET /api/v1/auction-insights - Get auction insights`
- `POST /api/v1/negative-keywords - Add negative keywords`

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
from grc_claw import PPCManager

ppc = PPCManager(
    platforms=["google_ads", "microsoft_ads"],
    default_strategy="target_roas",
    target_roas=4.0
)

campaign = ppc.create_campaign(
    name="Spring Sale 2024",
    type="search",
    budget_daily=500,
    keywords=["spring sale", "seasonal discount", "limited offer"],
    strategy="target_roas"
)

suggestions = ppc.keyword_research(
    seed_keywords=["digital marketing", "online advertising"],
    language="en",
    location="US"
)

ads = ppc.generate_ads(
    keywords=suggestions[:10],
    headlines_count=5,
    descriptions_count=3,
    tone="persuasive"
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
  "url": "https://your-app.com/webhooks/ppc-manager",
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
# HELP grc_claw_ppc-manager_requests_total Total requests
# TYPE grc_claw_ppc-manager_requests_total counter
grc_claw_ppc-manager_requests_total{method="POST",status="200"} 1234
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
