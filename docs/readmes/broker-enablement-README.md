# Broker Enablement

## Project Overview

Broker enablement platform that equips insurance and financial brokers with tools, content, and analytics to improve client engagement and sales.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `broker-enablement` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Broker portal with personalized client dashboards
- Product comparison tools and calculators
- Client communication templates and compliance-approved content
- Commission tracking and performance analytics
- Lead distribution and management for brokers
- Training and certification tracking
- Document management for applications and policies
- Client onboarding workflow automation

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/broker-enablement

# Using pip
pip install grc-claw-broker-enablement
```

### Basic Usage

```python
from grc_claw import BrokerEnablement

be = BrokerEnablement(
    portal_url="https://brokers.company.com",
    product_catalog="catalog.json",
    compliance_library="compliance/"
)

broker = be.register_broker(
    name="Jane Smith",
    email="jane@brokerage.com",
    license_number="BRK-12345",
    specialty="life_insurance"
)

lead = be.distribute_lead(
    client_info={{"name": "John Doe", "age": 35, "income": 80000}},
    product_interest="term_life",
    rules={{"round_robin": True, "specialty_match": True}}
)

comparison = be.compare_products(
    products=["term_20", "term_30", "whole_life"],
    client_profile={{"age": 35, "health": "excellent", "budget": 500}}
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `BROKER_PORTAL_URL` | Broker portal base URL |
| `PRODUCT_CATALOG` | Product catalog data source |
| `COMPLIANCE_CONTENT_LIBRARY` | Compliance-approved content library path |
| `COMMISSION_STRUCTURE` | Commission structure configuration |
| `LEAD_DISTRIBUTION_RULES` | Lead distribution rules configuration |
| `TRAINING_PLATFORM_URL` | Training platform integration URL |
| `DOCUMENT_TEMPLATES_DIR` | Document templates directory |

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
docker build -t grc-claw/broker-enablement .
docker run -p 3000:3000 --env-file .env grc-claw/broker-enablement
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broker-enablement
  labels:
    app: broker-enablement
spec:
  replicas: 2
  selector:
    matchLabels:
      app: broker-enablement
  template:
    metadata:
      labels:
        app: broker-enablement
    spec:
      containers:
      - name: broker-enablement
        image: grc-claw/broker-enablement:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: broker-enablement
spec:
  selector:
    app: broker-enablement
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

- `POST /api/v1/brokers - Register broker`
- `GET /api/v1/brokers/{id}/dashboard - Get broker dashboard`
- `POST /api/v1/leads/distribute - Distribute lead to broker`
- `POST /api/v1/commissions/calculate - Calculate commission`
- `GET /api/v1/products/compare - Compare products`
- `POST /api/v1/documents/generate - Generate document`
- `GET /api/v1/training/progress - Get training progress`

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
from grc_claw import BrokerEnablement

be = BrokerEnablement(
    portal_url="https://brokers.company.com",
    product_catalog="catalog.json",
    compliance_library="compliance/"
)

broker = be.register_broker(
    name="Jane Smith",
    email="jane@brokerage.com",
    license_number="BRK-12345",
    specialty="life_insurance"
)

lead = be.distribute_lead(
    client_info={{"name": "John Doe", "age": 35, "income": 80000}},
    product_interest="term_life",
    rules={{"round_robin": True, "specialty_match": True}}
)

comparison = be.compare_products(
    products=["term_20", "term_30", "whole_life"],
    client_profile={{"age": 35, "health": "excellent", "budget": 500}}
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
  "url": "https://your-app.com/webhooks/broker-enablement",
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
# HELP grc_claw_broker-enablement_requests_total Total requests
# TYPE grc_claw_broker-enablement_requests_total counter
grc_claw_broker-enablement_requests_total{method="POST",status="200"} 1234
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
