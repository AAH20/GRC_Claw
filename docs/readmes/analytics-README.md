# Analytics

## Project Overview

Unified marketing analytics platform that aggregates data from all channels into cohesive dashboards, reports, and actionable insights.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `analytics` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Cross-channel data aggregation and unification
- Custom dashboard builder with drag-and-drop widgets
- Automated report generation and distribution
- Cohort analysis and retention metrics
- Funnel analysis with conversion path visualization
- Anomaly detection and alerting on key metrics
- Data export to BI tools (Tableau, Looker, Power BI)
- Real-time streaming analytics and monitoring

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/analytics

# Using pip
pip install grc-claw-analytics
```

### Basic Usage

```python
from grc_claw import Analytics

analytics = Analytics(
    data_sources=["google_analytics", "salesforce", "stripe", "hubspot"],
    streaming=True
)

dashboard = analytics.create_dashboard(
    name="Marketing Overview",
    widgets=[
        {{"type": "timeseries", "metric": "revenue", "group_by": "channel"}},
        {{"type": "funnel", "steps": ["visit", "signup", "activation", "purchase"]}},
        {{"type": "table", "metric": "roas", "dimensions": ["campaign", "ad_group"]}},
        {{"type": "number", "metric": "mrr", "comparison": "previous_period"}}
    ]
)

report = analytics.generate_report(
    template="monthly_marketing_report",
    date_range="last_30_days",
    recipients=["marketing@company.com", "ceo@company.com"],
    format="pdf"
)

analytics.create_alert(
    metric="daily_revenue",
    condition="below",
    threshold=5000,
    sensitivity=0.8,
    notify=["slack: #marketing-alerts"]
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `DATA_SOURCES` | Connected data sources (comma-separated) |
| `DASHBOARD_REFRESH_INTERVAL` | Dashboard refresh in minutes (default: 15) |
| `ANOMALY_DETECTION_SENSITIVITY` | Anomaly detection sensitivity 0.0-1.0 (default: 0.8) |
| `REPORT_SCHEDULE` | Automated report schedule (cron expression) |
| `RETENTION_DAYS` | Data retention period in days (default: 730) |
| `EXPORT_FORMATS` | Supported export formats: csv, json, pdf, xlsx |
| `STREAMING_ENABLED` | Enable real-time streaming (default: true) |

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
docker build -t grc-claw/analytics .
docker run -p 3000:3000 --env-file .env grc-claw/analytics
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics
  labels:
    app: analytics
spec:
  replicas: 2
  selector:
    matchLabels:
      app: analytics
  template:
    metadata:
      labels:
        app: analytics
    spec:
      containers:
      - name: analytics
        image: grc-claw/analytics:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: analytics
spec:
  selector:
    app: analytics
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

- `POST /api/v1/dashboards - Create dashboard`
- `GET /api/v1/dashboards/{id} - Get dashboard data`
- `POST /api/v1/reports/generate - Generate report`
- `POST /api/v1/funnels - Create funnel analysis`
- `POST /api/v1/cohorts - Create cohort analysis`
- `GET /api/v1/metrics/{name} - Get metric data`
- `POST /api/v1/alerts - Create metric alert`
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
from grc_claw import Analytics

analytics = Analytics(
    data_sources=["google_analytics", "salesforce", "stripe", "hubspot"],
    streaming=True
)

dashboard = analytics.create_dashboard(
    name="Marketing Overview",
    widgets=[
        {{"type": "timeseries", "metric": "revenue", "group_by": "channel"}},
        {{"type": "funnel", "steps": ["visit", "signup", "activation", "purchase"]}},
        {{"type": "table", "metric": "roas", "dimensions": ["campaign", "ad_group"]}},
        {{"type": "number", "metric": "mrr", "comparison": "previous_period"}}
    ]
)

report = analytics.generate_report(
    template="monthly_marketing_report",
    date_range="last_30_days",
    recipients=["marketing@company.com", "ceo@company.com"],
    format="pdf"
)

analytics.create_alert(
    metric="daily_revenue",
    condition="below",
    threshold=5000,
    sensitivity=0.8,
    notify=["slack: #marketing-alerts"]
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
  "url": "https://your-app.com/webhooks/analytics",
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
# HELP grc_claw_analytics_requests_total Total requests
# TYPE grc_claw_analytics_requests_total counter
grc_claw_analytics_requests_total{method="POST",status="200"} 1234
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
