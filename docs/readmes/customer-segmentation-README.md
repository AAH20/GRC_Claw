# Customer Segmentation

## Project Overview

Advanced customer segmentation platform using ML clustering and behavioral analysis to identify distinct customer groups for targeted marketing.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `customer-segmentation` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- RFM (Recency, Frequency, Monetary) analysis
- K-means and hierarchical clustering segmentation
- Behavioral segmentation based on product usage
- Demographic and firmographic segmentation
- Dynamic segment membership with real-time updates
- Segment overlap and migration analysis
- Lookalike audience generation from segments
- Segment performance comparison and analytics

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/customer-segmentation

# Using pip
pip install grc-claw-customer-segmentation
```

### Basic Usage

```python
from grc_claw import CustomerSegmentation

cs = CustomerSegmentation(
    model="kmeans",
    max_segments=8,
    dynamic=True
)

segments = cs.create_segments(
    data_source="crm_contacts",
    features=["recency", "frequency", "monetary", "tenure", "engagement_score"],
    min_cluster_size=50
)

for seg in segments:
    print(f"{{seg.name}}: {{seg.size}} customers | "
          f"Avg CLV: ${{seg.avg_clv:,.0f}} | "
          f"Churn Risk: {{seg.churn_risk:.1%}}")

lookalike = cs.generate_lookalike(
    source_segment="high_value_customers",
    ratio=5,
    platforms=["facebook", "google_ads"]
)

migration = cs.analyze_migration(
    period="last_90_days",
    segments=["new_customers", "active", "at_risk", "churned"]
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `SEGMENTATION_MODEL` | Model type: rfm, kmeans, hierarchical, dbscan |
| `MIN_CLUSTER_SIZE` | Minimum cluster size (default: 100) |
| `MAX_SEGMENTS` | Maximum number of segments (default: 10) |
| `RFM_WEIGHTS` | RFM component weights |
| `DYNAMIC_SEGMENTATION` | Enable real-time segment updates (default: true) |
| `LOOKALIKE_RATIO` | Lookalike audience ratio (default: 5) |
| `SEGMENT_REFRESH_INTERVAL_HOURS` | Segment refresh frequency (default: 24) |

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
docker build -t grc-claw/customer-segmentation .
docker run -p 3000:3000 --env-file .env grc-claw/customer-segmentation
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: customer-segmentation
  labels:
    app: customer-segmentation
spec:
  replicas: 2
  selector:
    matchLabels:
      app: customer-segmentation
  template:
    metadata:
      labels:
        app: customer-segmentation
    spec:
      containers:
      - name: customer-segmentation
        image: grc-claw/customer-segmentation:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: customer-segmentation
spec:
  selector:
    app: customer-segmentation
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

- `POST /api/v1/segments/create - Create customer segments`
- `GET /api/v1/segments - List all segments`
- `GET /api/v1/segments/{id} - Get segment details`
- `GET /api/v1/segments/{id}/members - Get segment members`
- `POST /api/v1/segments/{id}/lookalike - Generate lookalike audience`
- `GET /api/v1/segments/overlap - Analyze segment overlap`
- `POST /api/v1/segments/validate - Validate segment quality`

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
from grc_claw import CustomerSegmentation

cs = CustomerSegmentation(
    model="kmeans",
    max_segments=8,
    dynamic=True
)

segments = cs.create_segments(
    data_source="crm_contacts",
    features=["recency", "frequency", "monetary", "tenure", "engagement_score"],
    min_cluster_size=50
)

for seg in segments:
    print(f"{{seg.name}}: {{seg.size}} customers | "
          f"Avg CLV: ${{seg.avg_clv:,.0f}} | "
          f"Churn Risk: {{seg.churn_risk:.1%}}")

lookalike = cs.generate_lookalike(
    source_segment="high_value_customers",
    ratio=5,
    platforms=["facebook", "google_ads"]
)

migration = cs.analyze_migration(
    period="last_90_days",
    segments=["new_customers", "active", "at_risk", "churned"]
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
  "url": "https://your-app.com/webhooks/customer-segmentation",
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
# HELP grc_claw_customer-segmentation_requests_total Total requests
# TYPE grc_claw_customer-segmentation_requests_total counter
grc_claw_customer-segmentation_requests_total{method="POST",status="200"} 1234
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
