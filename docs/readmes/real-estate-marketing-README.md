# Real Estate Marketing

## Project Overview

Real estate marketing platform for agents, brokers, and property managers to generate leads and manage client relationships.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `real-estate-marketing` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Property listing marketing and syndication
- Lead generation and nurturing for buyers/sellers
- Virtual tour and video marketing
- Neighborhood and market report automation
- Open house promotion and management
- Agent website and IDX integration
- Client relationship management for real estate
- Market analysis and CMA automation

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/real-estate-marketing

# Using pip
pip install grc-claw-real-estate-marketing
```

### Basic Usage

```python
from grc_claw import RealEstateMarketing

re_ = RealEstateMarketing(
    mls_provider="bright_mls",
    idx_provider="diverse_solutions"
)

listing = re_.create_listing(
    property_id="prop_123",
    address="123 Main St, Austin, TX",
    price=450000,
    beds=3, baths=2, sqft=2100,
    photos=["photo1.jpg", "photo2.jpg", "photo3.jpg"],
    agent="Jane Smith"
)

re_.syndicate_listing(
    listing_id=listing.id,
    platforms=["zillow", "realtor", "trulia", "redfin"]
)

tour = re_.create_virtual_tour(
    listing_id=listing.id,
    type="matterport",
    embed_url="https://my.matterport.com/show/?m=abc123"
)

re_.nurture_lead(
    lead_id="lead_456",
    type="buyer",
    criteria={{"price_range": "400000-500000", "location": "Austin"}},
    sequence=["market_update", "new_listing_alert", "home_buying_guide"]
)

cma = re_.generate_cma(
    property_id="prop_123",
    comparable_properties=5,
    report_format="pdf"
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `MLS_INTEGRATION` | MLS integration provider |
| `IDX_PROVIDER` | IDX website provider |
| `LEAD_SOURCES` | Lead source configuration |
| `VIRTUAL_TOUR_PROVIDER` | Virtual tour platform |
| `MARKET_REPORT_SCHEDULE` | Market report schedule |
| `AGENT_PORTAL_URL` | Agent portal URL |

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
docker build -t grc-claw/real-estate-marketing .
docker run -p 3000:3000 --env-file .env grc-claw/real-estate-marketing
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: real-estate-marketing
  labels:
    app: real-estate-marketing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: real-estate-marketing
  template:
    metadata:
      labels:
        app: real-estate-marketing
    spec:
      containers:
      - name: real-estate-marketing
        image: grc-claw/real-estate-marketing:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: real-estate-marketing
spec:
  selector:
    app: real-estate-marketing
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

- `POST /api/v1/listings - Create property listing`
- `POST /api/v1/listings/{id}/syndicate - Syndicate listing`
- `POST /api/v1/leads/nurture - Start lead nurture sequence`
- `POST /api/v1/tours/virtual - Create virtual tour`
- `POST /api/v1/open-houses - Schedule open house`
- `GET /api/v1/market-reports - Get market reports`
- `POST /api/v1/cma - Generate CMA report`

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
from grc_claw import RealEstateMarketing

re_ = RealEstateMarketing(
    mls_provider="bright_mls",
    idx_provider="diverse_solutions"
)

listing = re_.create_listing(
    property_id="prop_123",
    address="123 Main St, Austin, TX",
    price=450000,
    beds=3, baths=2, sqft=2100,
    photos=["photo1.jpg", "photo2.jpg", "photo3.jpg"],
    agent="Jane Smith"
)

re_.syndicate_listing(
    listing_id=listing.id,
    platforms=["zillow", "realtor", "trulia", "redfin"]
)

tour = re_.create_virtual_tour(
    listing_id=listing.id,
    type="matterport",
    embed_url="https://my.matterport.com/show/?m=abc123"
)

re_.nurture_lead(
    lead_id="lead_456",
    type="buyer",
    criteria={{"price_range": "400000-500000", "location": "Austin"}},
    sequence=["market_update", "new_listing_alert", "home_buying_guide"]
)

cma = re_.generate_cma(
    property_id="prop_123",
    comparable_properties=5,
    report_format="pdf"
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
  "url": "https://your-app.com/webhooks/real-estate-marketing",
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
# HELP grc_claw_real-estate-marketing_requests_total Total requests
# TYPE grc_claw_real-estate-marketing_requests_total counter
grc_claw_real-estate-marketing_requests_total{method="POST",status="200"} 1234
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
