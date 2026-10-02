# Broker Enablement Platform

A standalone, multi-tenant AI-powered broker enablement platform built with FastAPI, LangChain DeepAgents, and grc-marketing-core.

## Architecture

The platform consists of 5 specialized AI agents:

| Agent | Responsibility |
|-------|---------------|
| **Partner Onboarding** | Automated partner registration, KYC verification, and account provisioning |
| **Partner Enablement** | Training content delivery, certification tracking, and resource management |
| **Commission Tracking** | Real-time commission calculation, payout processing, and dispute resolution |
| **Performance Analytics** | KPI dashboards, trend analysis, and predictive insights |
| **Multi-tenant Orchestration** | Tenant isolation, resource routing, and cross-tenant governance |

## Quick Start

### Local Development

```bash

# Create virtual environment

python -m venv .venv
source .venv/bin/activate

# Install dependencies

pip install -e ".[dev]"

# Copy environment template

cp .env.example .env

# Run the application

uvicorn broker_enablement.main:app --reload --port 8000

```

## Docker

```bash

docker-compose up --build

```

### Kubernetes

```bash

kubectl apply -f k8s/

```

## Project Structure

```

broker-enablement/
├── src/broker_enablement/
│   ├── agents/           # AI agent implementations
│   ├── api/              # FastAPI route handlers
│   ├── integrations/     # Third-party service clients
│   ├── main.py           # Application entry point
│   └── __init__.py
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml

```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/partners` | Register a new partner |
| GET | `/partners/{partner_id}` | Get partner details |
| POST | `/partners/{partner_id}/enable` | Start enablement workflow |
| GET | `/commissions/{partner_id}` | Get commission records |
| POST | `/commissions/calculate` | Calculate commission |
| GET | `/analytics/{partner_id}` | Get performance metrics |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

## License

MIT
