# Pricing Optimizer

## Project Overview

Dynamic pricing optimization engine that uses market data, demand signals, and competitive intelligence to recommend optimal pricing strategies.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `pricing-optimizer` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Demand-based dynamic pricing recommendations
- Competitive price monitoring and analysis
- Price elasticity modeling and optimization
- A/B testing for pricing strategies
- Segment-based pricing and discount optimization
- Revenue and margin impact simulation
- Promotional pricing optimization
- Price change impact forecasting

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/pricing-optimizer

# Using pip
pip install grc-claw-pricing-optimizer
```

### Basic Usage

```python
from grc_claw import PricingOptimizer

po = PricingOptimizer(
    model="elasticity",
    objective="revenue",
    margin_floor=0.15
)

recommendation = po.recommend_price(
    product_id="prod_123",
    current_price=99.99,
    context={{"season": "holiday", "demand": "high", "inventory": "low"}}
)

print(f"Recommended: ${{recommendation.price}} (was ${{recommendation.current_price}})")
print(f"Expected Revenue Impact: {{recommendation.revenue_impact:+.1%}}")
print(f"Confidence: {{recommendation.confidence:.1%}}")

simulation = po.simulate(
    product_id="prod_123",
    price_points=[79.99, 89.99, 99.99, 109.99, 119.99],
    duration_days=30
)

competitor_prices = po.get_competitor_pricing(
    product_category="electronics",
    competitors=["amazon", "best_buy", "walmart"]
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `PRICING_MODEL` | Pricing model type: elasticity, conjoint, reinforcement_learning |
| `COMPETITOR_SOURCES` | Competitor price data sources |
| `PRICE_CHANGE_THRESHOLD` | Minimum price change to trigger review (default: 0.05) |
| `MARGIN_FLOOR` | Minimum acceptable margin (default: 0.15) |
| `OPTIMIZATION_OBJECTIVE` | Objective: revenue, margin, market_share |
| `PRICE_TEST_DURATION_DAYS` | A/B test duration (default: 14) |
| `DYNAMIC_PRICING_ENABLED` | Enable real-time dynamic pricing (default: false) |

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
docker build -t grc-claw/pricing-optimizer .
docker run -p 3000:3000 --env-file .env grc-claw/pricing-optimizer
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pricing-optimizer
  labels:
    app: pricing-optimizer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pricing-optimizer
  template:
    metadata:
      labels:
        app: pricing-optimizer
    spec:
      containers:
      - name: pricing-optimizer
        image: grc-claw/pricing-optimizer:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: pricing-optimizer
spec:
  selector:
    app: pricing-optimizer
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

- `POST /api/v1/pricing/recommend - Get pricing recommendation`
- `POST /api/v1/pricing/simulate - Simulate pricing scenario`
- `GET /api/v1/pricing/competitors - Get competitor pricing`
- `POST /api/v1/pricing/test - Create pricing A/B test`
- `GET /api/v1/pricing/elasticity/{product_id} - Get price elasticity`
- `POST /api/v1/pricing/optimize - Run pricing optimization`

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
from grc_claw import PricingOptimizer

po = PricingOptimizer(
    model="elasticity",
    objective="revenue",
    margin_floor=0.15
)

recommendation = po.recommend_price(
    product_id="prod_123",
    current_price=99.99,
    context={{"season": "holiday", "demand": "high", "inventory": "low"}}
)

print(f"Recommended: ${{recommendation.price}} (was ${{recommendation.current_price}})")
print(f"Expected Revenue Impact: {{recommendation.revenue_impact:+.1%}}")
print(f"Confidence: {{recommendation.confidence:.1%}}")

simulation = po.simulate(
    product_id="prod_123",
    price_points=[79.99, 89.99, 99.99, 109.99, 119.99],
    duration_days=30
)

competitor_prices = po.get_competitor_pricing(
    product_category="electronics",
    competitors=["amazon", "best_buy", "walmart"]
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
  "url": "https://your-app.com/webhooks/pricing-optimizer",
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
# HELP grc_claw_pricing-optimizer_requests_total Total requests
# TYPE grc_claw_pricing-optimizer_requests_total counter
grc_claw_pricing-optimizer_requests_total{method="POST",status="200"} 1234
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
