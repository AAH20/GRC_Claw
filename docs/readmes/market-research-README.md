# Market Research

## Project Overview

AI-powered market research platform that automates survey creation, distribution, analysis, and insight generation.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `market-research` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- AI-assisted survey design and question generation
- Multi-channel survey distribution (email, social, web, SMS)
- Automated respondent recruitment and panel management
- Real-time survey analytics and cross-tabulation
- Sentiment and text analysis of open-ended responses
- Market sizing and TAM/SAM/SOM estimation
- Competitive analysis and benchmarking
- Research report generation with visualizations

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/market-research

# Using pip
pip install grc-claw-market-research
```

### Basic Usage

```python
from grc_claw import MarketResearch

mr = MarketResearch(
    survey_provider="qualtrics",
    panel_provider="dynata"
)

survey = mr.create_survey(
    title="Customer Satisfaction Survey 2024",
    questions=[
        {{"type": "nps", "text": "How likely are you to recommend us?"}},
        {{"type": "multiple_choice", "text": "What do you value most?", "options": ["Price", "Quality", "Service", "Innovation"]}},
        {{"type": "open_ended", "text": "What could we improve?"}}
    ],
    target_audience={{"industry": "technology", "company_size": "50-500"}}
)

mr.distribute(
    survey_id=survey.id,
    channels=["email", "in_app"],
    sample_size=500,
    incentive="$10_gift_card"
)

analysis = mr.analyze(survey_id=survey.id)
print(f"NPS: {{analysis.nps}} | Response Rate: {{analysis.response_rate:.1%}}")
print(f"Top Themes: {{analysis.open_ended_themes}}")

report = mr.generate_report(
    survey_id=survey.id,
    template="executive_summary",
    include_visualizations=True
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `SURVEY_PROVIDER` | Survey platform provider |
| `PANEL_PROVIDER` | Research panel provider |
| `DISTRIBUTION_CHANNELS` | Survey distribution channels |
| `ANALYSIS_MODEL` | Text analysis model |
| `MARKET_DATA_SOURCES` | Market data source APIs |
| `REPORT_TEMPLATE_DIR` | Report template directory |
| `MIN_RESPONDENTS` | Minimum respondents for statistical significance (default: 100) |

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
docker build -t grc-claw/market-research .
docker run -p 3000:3000 --env-file .env grc-claw/market-research
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: market-research
  labels:
    app: market-research
spec:
  replicas: 2
  selector:
    matchLabels:
      app: market-research
  template:
    metadata:
      labels:
        app: market-research
    spec:
      containers:
      - name: market-research
        image: grc-claw/market-research:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: market-research
spec:
  selector:
    app: market-research
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

- `POST /api/v1/surveys/create - Create survey`
- `POST /api/v1/surveys/{id}/distribute - Distribute survey`
- `GET /api/v1/surveys/{id}/responses - Get survey responses`
- `POST /api/v1/surveys/{id}/analyze - Analyze survey results`
- `POST /api/v1/market-size - Estimate market size`
- `POST /api/v1/competitive-analysis - Run competitive analysis`
- `POST /api/v1/reports/generate - Generate research report`

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
from grc_claw import MarketResearch

mr = MarketResearch(
    survey_provider="qualtrics",
    panel_provider="dynata"
)

survey = mr.create_survey(
    title="Customer Satisfaction Survey 2024",
    questions=[
        {{"type": "nps", "text": "How likely are you to recommend us?"}},
        {{"type": "multiple_choice", "text": "What do you value most?", "options": ["Price", "Quality", "Service", "Innovation"]}},
        {{"type": "open_ended", "text": "What could we improve?"}}
    ],
    target_audience={{"industry": "technology", "company_size": "50-500"}}
)

mr.distribute(
    survey_id=survey.id,
    channels=["email", "in_app"],
    sample_size=500,
    incentive="$10_gift_card"
)

analysis = mr.analyze(survey_id=survey.id)
print(f"NPS: {{analysis.nps}} | Response Rate: {{analysis.response_rate:.1%}}")
print(f"Top Themes: {{analysis.open_ended_themes}}")

report = mr.generate_report(
    survey_id=survey.id,
    template="executive_summary",
    include_visualizations=True
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
  "url": "https://your-app.com/webhooks/market-research",
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
# HELP grc_claw_market-research_requests_total Total requests
# TYPE grc_claw_market-research_requests_total counter
grc_claw_market-research_requests_total{method="POST",status="200"} 1234
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
