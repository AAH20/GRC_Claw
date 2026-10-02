# Affiliate Marketing Platform

A modularized agentic AI affiliate marketing platform built with FastAPI, LangChain DeepAgents, and grc-marketing-core.

## Architecture

The platform consists of 5 specialized agents:

| Agent | Responsibility |
|-------|---------------|
| **Recruitment** | Discover and onboard new affiliate partners |
| **Tracking** | Monitor clicks, conversions, and attribution |
| **Optimization** | A/B testing, bid optimization, and campaign tuning |
| **Payout** | Commission calculation and payment processing |
| **Analytics** | Reporting, forecasting, and insights |

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Run locally
uvicorn affiliate_marketing.main:app --reload

# Run with Docker
docker-compose up --build
```

## Project Structure

```
affiliate-marketing/
├── src/affiliate_marketing/
│   ├── agents/           # 5 specialized agents
│   ├── api/              # REST API routers
│   ├── integrations/     # Affiliate network connectors
│   ├── core/             # Shared utilities
│   └── main.py           # FastAPI application
├── tests/
├── config/
├── k8s/
└── .github/workflows/
```

## API Endpoints

- `GET /health` — Health check
- `GET /partners` — List affiliate partners
- `GET /commissions` — Commission records
- `POST /agents/{agent}/invoke` — Invoke an agent

## License

MIT
