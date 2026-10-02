# Ecommerce Marketing

## Project Overview

Ecommerce marketing platform with tools for product promotion, cart abandonment recovery, and customer lifecycle marketing.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `ecommerce-marketing` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Product feed management and optimization
- Cart abandonment email and SMS recovery
- Customer lifecycle marketing automation
- Product recommendation widgets
- Discount and promotion management
- Customer review and UGC collection
- Ecommerce analytics and LTV tracking
- Integration with Shopify, WooCommerce, Magento

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/ecommerce-marketing

# Using pip
pip install grc-claw-ecommerce-marketing
```

### Basic Usage

```python
from grc_claw import EcommerceMarketing

ec = EcommerceMarketing(
    platform="shopify",
    abandoned_cart_delay_hours=1
)

ec.sync_products(
    store_url="https://mystore.myshopify.com",
    include_variants=True,
    update_frequency="hourly"
)

ec.trigger_cart_abandonment(
    cart_id="cart_123",
    customer_email="customer@example.com",
    items=[{{"product": "Widget Pro", "price": 49.99, "qty": 2}}],
    sequence=[
        {{"delay_hours": 1, "channel": "email", "template": "cart_reminder"}},
        {{"delay_hours": 24, "channel": "email", "template": "cart_discount", "discount": "10%"}},
        {{"delay_hours": 72, "channel": "sms", "template": "cart_urgency"}}
    ]
)

promo = ec.create_promotion(
    name="Spring Sale",
    type="percentage_discount",
    value=20,
    applicable_products="all",
    start_date="2024-03-01",
    end_date="2024-03-31",
    code="SPRING20"
)

ltv = ec.get_ltv_analytics(
    segment="repeat_customers",
    period="last_12_months"
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `ECOMMERCE_PLATFORM` | Ecommerce platform: shopify, woocommerce, magento |
| `ABANDONED_CART_DELAY_HOURS` | Cart abandonment trigger delay (default: 1) |
| `PRODUCT_FEED_SCHEDULE` | Product feed update schedule |
| `DISCOUNT_RULES` | Discount and promotion rules |
| `REVIEW_COLLECTION_ENABLED` | Enable review collection (default: true) |
| `LTV_SEGMENTATION` | LTV-based customer segmentation |

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
docker build -t grc-claw/ecommerce-marketing .
docker run -p 3000:3000 --env-file .env grc-claw/ecommerce-marketing
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-marketing
  labels:
    app: ecommerce-marketing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ecommerce-marketing
  template:
    metadata:
      labels:
        app: ecommerce-marketing
    spec:
      containers:
      - name: ecommerce-marketing
        image: grc-claw/ecommerce-marketing:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: ecommerce-marketing
spec:
  selector:
    app: ecommerce-marketing
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

- `POST /api/v1/products/sync - Sync product catalog`
- `POST /api/v1/cart-abandonment/trigger - Trigger cart recovery`
- `POST /api/v1/promotions - Create promotion`
- `POST /api/v1/recommendations - Get product recommendations`
- `POST /api/v1/reviews/collect - Collect product reviews`
- `GET /api/v1/analytics/ltv - Get customer LTV analytics`
- `POST /api/v1/lifecycle/automate - Create lifecycle automation`

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
from grc_claw import EcommerceMarketing

ec = EcommerceMarketing(
    platform="shopify",
    abandoned_cart_delay_hours=1
)

ec.sync_products(
    store_url="https://mystore.myshopify.com",
    include_variants=True,
    update_frequency="hourly"
)

ec.trigger_cart_abandonment(
    cart_id="cart_123",
    customer_email="customer@example.com",
    items=[{{"product": "Widget Pro", "price": 49.99, "qty": 2}}],
    sequence=[
        {{"delay_hours": 1, "channel": "email", "template": "cart_reminder"}},
        {{"delay_hours": 24, "channel": "email", "template": "cart_discount", "discount": "10%"}},
        {{"delay_hours": 72, "channel": "sms", "template": "cart_urgency"}}
    ]
)

promo = ec.create_promotion(
    name="Spring Sale",
    type="percentage_discount",
    value=20,
    applicable_products="all",
    start_date="2024-03-01",
    end_date="2024-03-31",
    code="SPRING20"
)

ltv = ec.get_ltv_analytics(
    segment="repeat_customers",
    period="last_12_months"
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
  "url": "https://your-app.com/webhooks/ecommerce-marketing",
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
# HELP grc_claw_ecommerce-marketing_requests_total Total requests
# TYPE grc_claw_ecommerce-marketing_requests_total counter
grc_claw_ecommerce-marketing_requests_total{method="POST",status="200"} 1234
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
