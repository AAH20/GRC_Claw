# Customer Service AI Platform

A standalone, modularized agentic AI customer service platform built with LangChain DeepAgents and grc-marketing-core. Integrates with Zendesk, Intercom, and Salesforce Service Cloud.

## Architecture

```

┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Triage  │Resolution│Escalation│ Sentiment│  Customer   │
│  Agent   │  Agent   │  Agent   │ Analysis │  Success    │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│              grc-marketing-core (shared)                 │
├──────────┬──────────────────────┬───────────────────────┤
│ Zendesk  │      Intercom        │  Salesforce Service   │
│          │                      │       Cloud           │
└──────────┴──────────────────────┴───────────────────────┘

```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Triage** | Classifies incoming tickets by urgency, category, and intent |
| **Resolution** | Generates resolution suggestions and auto-replies |
| **Escalation** | Routes complex cases to human agents with context |
| **Sentiment Analysis** | Analyzes customer sentiment and satisfaction signals |
| **Customer Success** | Proactive outreach and retention risk detection |

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

# Edit .env with your API keys

# Run the application

uvicorn customer_service.main:app --reload --port 8000

```

## Docker

```bash

docker-compose up --build

```

### Kubernetes

```bash

kubectl apply -f k8s/

```

## Configuration

All configuration is managed via environment variables (see `.env.example`) and `config/config.yaml`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/tickets` | Create a new ticket |
| `GET` | `/api/v1/tickets/{ticket_id}` | Get ticket details |
| `POST` | `/api/v1/tickets/{ticket_id}/triage` | Run triage on a ticket |
| `POST` | `/api/v1/tickets/{ticket_id}/resolve` | Get resolution suggestions |
| `POST` | `/api/v1/tickets/{ticket_id}/escalate` | Escalate a ticket |
| `GET` | `/api/v1/customers/{customer_id}` | Get customer profile |
| `POST` | `/api/v1/customers/{customer_id}/sentiment` | Analyze customer sentiment |
| `POST` | `/api/v1/customers/{customer_id/outreach` | Trigger proactive outreach |

## Testing

```bash

pytest tests/ -v --cov=customer_service

```

## CI/CD

GitHub Actions workflow at `.github/workflows/ci-cd.yml` handles:

- Linting and type checking
- Unit and integration tests
- Docker image build and push
- Kubernetes deployment

## License

MIT
