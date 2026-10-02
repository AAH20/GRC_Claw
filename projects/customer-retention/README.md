# Customer Retention

AI-powered customer retention platform built with LangChain DeepAgents and grc-marketing-core. Predicts churn risk, automates interventions, optimizes campaigns, and tracks performance across CRM systems.

## Architecture

```

┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬──────────┬────────────────────────┤
│ Prediction│Intervention│Optimization│Performance Analytics│
│  Agent    │  Agent    │  Agent    │      Agent            │
├──────────┴──────────┴──────────┴────────────────────────┤
│              CRM Integrations Layer                      │
│         Salesforce │ HubSpot │ Stripe                    │
└─────────────────────────────────────────────────────────┘

```

## Agents

| Agent | Purpose |
|-------|---------|
| **Prediction** | Churn risk scoring, customer health scoring, behavioral pattern analysis |
| **Intervention** | Automated retention campaigns, personalized outreach, win-back flows |
| **Optimization** | A/B testing, campaign performance optimization, budget allocation |
| **Performance Analytics** | Cohort analysis, retention metrics, ROI tracking, reporting |

## Quick Start

### Local Development

```bash

# Create virtual environment

python -m venv .venv
source .venv/bin/activate

# Install dependencies

pip install -e ".[dev]"

# Copy environment configuration

cp .env.example .env

# Edit .env with your credentials

# Run the application

uvicorn customer_retention.main:app --reload --port 8000

```

## Docker

```bash

docker-compose up --build

```

### Kubernetes

```bash

kubectl apply -f k8s/

```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/v1/customers` | List customers |
| GET | `/api/v1/customers/{id}` | Get customer by ID |
| POST | `/api/v1/customers` | Create customer |
| GET | `/api/v1/customers/{id}/churn-risk` | Get churn risk score |
| GET | `/api/v1/campaigns` | List campaigns |
| POST | `/api/v1/campaigns` | Create campaign |
| GET | `/api/v1/campaigns/{id}` | Get campaign by ID |
| POST | `/api/v1/campaigns/{id}/optimize` | Optimize campaign |
| GET | `/api/v1/analytics/retention` | Retention metrics |
| GET | `/api/v1/analytics/cohorts` | Cohort analysis |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

### Required Environment Variables

- `SALESFORCE_CLIENT_ID` / `SALESFORCE_CLIENT_SECRET` — Salesforce OAuth
- `HUBSPOT_API_KEY` — HubSpot API key
- `STRIPE_SECRET_KEY` — Stripe secret key
- `OPENAI_API_KEY` — OpenAI API key for LLM agents

## Testing

```bash

pytest tests/ -v --cov=src/customer_retention

```

## CI/CD

GitHub Actions workflow runs on every push to `main`:
1. Lint (ruff)
2. Type check (mypy)
3. Test (pytest with coverage)
4. Build Docker image
5. Push to container registry
6. Deploy to Kubernetes

## Project Structure

```

customer-retention/
├── .github/workflows/ci-cd.yml
├── config/
│   └── config.yaml
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── src/customer_retention/
│   ├── agents/
│   │   ├── prediction.py
│   │   ├── intervention.py
│   │   ├── optimization.py
│   │   └── performance_analytics.py
│   ├── api/
│   │   ├── customers.py
│   │   └── campaigns.py
│   ├── integrations/
│   │   ├── salesforce.py
│   │   ├── hubspot.py
│   │   └── stripe.py
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_integrations.py
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml

```

## License

MIT
