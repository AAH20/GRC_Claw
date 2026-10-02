# Product Recommendations

## Project Overview

AI-driven product recommendation engine that delivers personalized product suggestions across web, email, and sales channels.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `product-recommendations` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Collaborative filtering and content-based recommendation models
- Real-time personalization based on browsing behavior
- Cross-sell and upsell recommendation strategies
- Recommendation widgets for web and mobile
- Email product recommendation automation
- Sales rep recommendation insights
- A/B testing for recommendation strategies
- Recommendation performance analytics

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/product-recommendations

# Using pip
pip install grc-claw-product-recommendations
```

### Basic Usage

```python
from grc_claw import ProductRecommendations

rec = ProductRecommendations(
    model="hybrid",
    personalization=True,
    max_recommendations=8
)

recommendations = rec.get_recommendations(
    user_id="user_123",
    context="product_page",
    current_product="prod_456",
    limit=8
)

for r in recommendations:
    print(f"{{r.product_name}} — {{r.reason}} (score: {{r.confidence:.2f}})")

rec.track_event(
    user_id="user_123",
    event_type="product_view",
    product_id="prod_789",
    metadata={{"duration_seconds": 45, "scroll_depth": 0.8}}
)

cross_sell = rec.cross_sell(
    cart_items=["prod_001", "prod_002"],
    strategy="frequently_bought_together"
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `RECOMMENDATION_MODEL` | Model type: collaborative, content_based, hybrid |
| `PERSONALIZATION_ENABLED` | Enable real-time personalization (default: true) |
| `MAX_RECOMMENDATIONS` | Max recommendations per request (default: 10) |
| `MIN_CONFIDENCE_SCORE` | Minimum confidence threshold (default: 0.6) |
| `CATEGORICAL_FILTERS` | Product category filters |
| `EXCLUDED_PRODUCTS` | Products to exclude from recommendations |
| `MODEL_RETRAIN_INTERVAL_HOURS` | Model retraining frequency (default: 24) |

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
docker build -t grc-claw/product-recommendations .
docker run -p 3000:3000 --env-file .env grc-claw/product-recommendations
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: product-recommendations
  labels:
    app: product-recommendations
spec:
  replicas: 2
  selector:
    matchLabels:
      app: product-recommendations
  template:
    metadata:
      labels:
        app: product-recommendations
    spec:
      containers:
      - name: product-recommendations
        image: grc-claw/product-recommendations:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: product-recommendations
spec:
  selector:
    app: product-recommendations
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

- `POST /api/v1/recommendations - Get product recommendations`
- `POST /api/v1/recommendations/similar - Get similar products`
- `POST /api/v1/recommendations/cross-sell - Get cross-sell recommendations`
- `POST /api/v1/recommendations/upsell - Get upsell recommendations`
- `GET /api/v1/recommendations/{id}/performance - Get recommendation performance`
- `POST /api/v1/events/track - Track user interaction event`

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
from grc_claw import ProductRecommendations

rec = ProductRecommendations(
    model="hybrid",
    personalization=True,
    max_recommendations=8
)

recommendations = rec.get_recommendations(
    user_id="user_123",
    context="product_page",
    current_product="prod_456",
    limit=8
)

for r in recommendations:
    print(f"{{r.product_name}} — {{r.reason}} (score: {{r.confidence:.2f}})")

rec.track_event(
    user_id="user_123",
    event_type="product_view",
    product_id="prod_789",
    metadata={{"duration_seconds": 45, "scroll_depth": 0.8}}
)

cross_sell = rec.cross_sell(
    cart_items=["prod_001", "prod_002"],
    strategy="frequently_bought_together"
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
  "url": "https://your-app.com/webhooks/product-recommendations",
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
# HELP grc_claw_product-recommendations_requests_total Total requests
# TYPE grc_claw_product-recommendations_requests_total counter
grc_claw_product-recommendations_requests_total{method="POST",status="200"} 1234
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
