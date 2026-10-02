# Marketing Compliance Platform

AI-powered marketing compliance monitoring and enforcement platform built with LangChain DeepAgents.

## Overview

This platform provides automated compliance monitoring for marketing campaigns across multiple channels (Salesforce, Hubspot, Mailchimp). It uses a multi-agent architecture to detect violations, generate responses, and produce compliance reports.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Monitor  │  │  Detect  │  │ Respond  │  │ Report │ │
│  │  Agent   │  │  Agent   │  │  Agent   │  │ Agent  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │              │              │             │      │
│       └──────────────┴──────────────┴─────────────┘      │
│                          │                                │
│                   ┌──────┴──────┐                        │
│                   │ Orchestrator │                        │
│                   └──────┬──────┘                        │
│                          │                                │
│  ┌──────────┐  ┌─────────┴─────────┐  ┌──────────┐     │
│  │Analytics │  │   Integrations    │  │ Policies │     │
│  │  Agent   │  │ (SF/HS/Mailchimp) │  │   API    │     │
│  └──────────┘  └───────────────────┘  └──────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Monitor** | Continuously scans marketing content across integrated platforms |
| **Detect** | Identifies compliance violations using AI-powered analysis |
| **Respond** | Generates remediation responses and escalation workflows |
| **Report** | Produces compliance reports and audit trails |
| **Analytics** | Tracks compliance metrics and trends over time |
| **Orchestrator** | Coordinates agent workflows and manages task distribution |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)
- API keys for Salesforce, Hubspot, and/or Mailchimp

### Local Development

```bash

# Clone and navigate to the project

cd marketing-compliance

# Create virtual environment

python -m venv .venv
source .venv/bin/activate

# Install dependencies

pip install -e ".[dev]"

# Copy environment configuration

cp .env.example .env

# Edit .env with your API keys

# Run the server

uvicorn compliance.main:app --reload --port 8000
```

### Docker

```bash

# Build and run with Docker Compose

docker-compose up --build
```

### Kubernetes

```bash

# Deploy to Kubernetes

kubectl apply -f k8s/
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/policies` | GET/POST | List/create compliance policies |
| `/api/v1/policies/{id}` | GET/PUT/DELETE | Manage specific policy |
| `/api/v1/violations` | GET/POST | List/report violations |
| `/api/v1/violations/{id}` | GET/PUT | Manage specific violation |
| `/api/v1/violations/{id}/resolve` | POST | Resolve a violation |
| `/api/v1/monitor/scan` | POST | Trigger compliance scan |
| `/api/v1/reports/generate` | POST | Generate compliance report |

## Configuration

See `.env.example` for all available environment variables.

## Testing

```bash

# Run all tests

pytest

# Run with coverage

pytest --cov=src/compliance --cov-report=html

# Run specific test file

pytest tests/test_agents.py -v
```

## CI/CD

The project includes a GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that:
1. Runs linting and type checking
2. Executes the test suite
3. Builds and pushes Docker image
4. Deploys to Kubernetes

## License

MIT
