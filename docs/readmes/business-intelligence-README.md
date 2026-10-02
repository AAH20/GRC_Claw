# Business Intelligence

## Project Overview

Marketing business intelligence platform that transforms raw marketing data into actionable insights, forecasts, and strategic recommendations.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `business-intelligence` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Automated insight discovery from marketing data
- Natural language query interface for data exploration
- Competitive intelligence monitoring and analysis
- Market trend detection and forecasting
- Automated executive summary generation
- Data storytelling with visual narratives
- Anomaly detection and root cause analysis
- Strategic recommendation engine

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/business-intelligence

# Using pip
pip install grc-claw-business-intelligence
```

### Basic Usage

```python
from grc_claw import BusinessIntelligence

bi = BusinessIntelligence(
    data_warehouse="snowflake://...",
    nl_query_model="gpt-4"
)

answer = bi.query("What was our ROAS by channel last quarter?")
print(answer.summary)
print(answer.visualization_url)

insights = bi.discover_insights(
    data_sources=["google_ads", "salesforce", "ga4"],
    focus_areas=["performance", "trends", "anomalies"]
)

for insight in insights:
    print(f"INSIGHT: {{insight.title}}: {{insight.description}}")
    print(f"   Impact: {{insight.estimated_value:,.0f}} | Confidence: {{insight.confidence:.1%}}")

summary = bi.generate_executive_summary(
    period="Q4_2024",
    include_forecast=True,
    include_recommendations=True
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `DATA_WAREHOUSE` | Data warehouse connection string |
| `NL_QUERY_MODEL` | NL query model type |
| `INSIGHT_DISCOVERY_INTERVAL` | Insight discovery frequency in hours (default: 24) |
| `COMPETITOR_SOURCES` | Competitor intelligence sources |
| `MARKET_DATA_PROVIDERS` | Market data provider APIs |
| `EXECUTIVE_SUMMARY_TEMPLATE` | Executive summary template |
| `ANOMALY_DETECTION_SENSITIVITY` | Anomaly detection sensitivity (default: 0.8) |

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
docker build -t grc-claw/business-intelligence .
docker run -p 3000:3000 --env-file .env grc-claw/business-intelligence
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: business-intelligence
  labels:
    app: business-intelligence
spec:
  replicas: 2
  selector:
    matchLabels:
      app: business-intelligence
  template:
    metadata:
      labels:
        app: business-intelligence
    spec:
      containers:
      - name: business-intelligence
        image: grc-claw/business-intelligence:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: business-intelligence
spec:
  selector:
    app: business-intelligence
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

- `POST /api/v1/query - Natural language data query`
- `POST /api/v1/insights/discover - Discover insights`
- `GET /api/v1/insights/{id} - Get insight details`
- `POST /api/v1/competitors/analyze - Analyze competitors`
- `POST /api/v1/forecasts - Generate market forecast`
- `POST /api/v1/summaries/executive - Generate executive summary`
- `GET /api/v1/anomalies - Get detected anomalies`

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
from grc_claw import BusinessIntelligence

bi = BusinessIntelligence(
    data_warehouse="snowflake://...",
    nl_query_model="gpt-4"
)

answer = bi.query("What was our ROAS by channel last quarter?")
print(answer.summary)
print(answer.visualization_url)

insights = bi.discover_insights(
    data_sources=["google_ads", "salesforce", "ga4"],
    focus_areas=["performance", "trends", "anomalies"]
)

for insight in insights:
    print(f"INSIGHT: {{insight.title}}: {{insight.description}}")
    print(f"   Impact: {{insight.estimated_value:,.0f}} | Confidence: {{insight.confidence:.1%}}")

summary = bi.generate_executive_summary(
    period="Q4_2024",
    include_forecast=True,
    include_recommendations=True
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
  "url": "https://your-app.com/webhooks/business-intelligence",
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
# HELP grc_claw_business-intelligence_requests_total Total requests
# TYPE grc_claw_business-intelligence_requests_total counter
grc_claw_business-intelligence_requests_total{method="POST",status="200"} 1234
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
