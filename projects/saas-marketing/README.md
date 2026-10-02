# SaaS Marketing

A modularized agentic AI marketing platform optimized for SaaS Product-Led Growth (PLG). Built with FastAPI, LangChain DeepAgents, and grc-marketing-core.

## Architecture

The platform consists of 5 specialized agents:

| Agent | Responsibility |
|-------|---------------|
| **Content** | Generates marketing copy, email sequences, and social content |
| **PQL Scoring** | Scores product-qualified leads based on behavioral signals |
| **Churn Prevention** | Identifies at-risk accounts and triggers retention workflows |
| **Analytics** | Aggregates metrics, funnels, and cohort analysis |
| **Reporting** | Produces executive dashboards and scheduled reports |

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
uvicorn saas_marketing.main:app --reload --port 8000
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
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/campaigns` | Create a marketing campaign |
| `GET` | `/api/v1/campaigns/{id}` | Get campaign details |
| `POST` | `/api/v1/users/{id}/score` | Score a user's PQL status |
| `GET` | `/api/v1/users/{id}/churn-risk` | Get churn risk assessment |
| `GET` | `/api/v1/analytics/funnel` | Get funnel metrics |
| `POST` | `/api/v1/reports/generate` | Generate a marketing report |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:

- `APP_ENV` — Environment (development, staging, production)
- `LOG_LEVEL` — Logging verbosity
- `SALESFORCE_API_KEY` — Salesforce integration
- `HUBSPOT_API_KEY` — HubSpot integration
- `STRIPE_SECRET_KEY` — Stripe integration

## Testing

```bash
pytest --cov=saas_marketing --cov-report=term-missing
```

## CI/CD

GitHub Actions workflow at `.github/workflows/ci-cd.yml` handles:

1. Linting (ruff)
2. Type checking (mypy)
3. Unit tests with coverage
4. Docker image build and push
5. Kubernetes deployment

## Project Structure

```
saas-marketing/
├── .github/workflows/ci-cd.yml
├── config/
│   ├── config.yaml
│   └── .env.example
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── src/saas_marketing/
│   ├── __init__.py
│   ├── main.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── analytics.py
│   │   ├── content.py
│   │   ├── churn_prevention.py
│   │   ├── pql_scoring.py
│   │   └── reporting.py
│   ├── api/
│   │   ├── campaigns.py
│   │   └── users.py
│   └── integrations/
│       ├── hubspot.py
│       ├── salesforce.py
│       └── stripe.py
├── tests/
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_integrations.py
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## License

MIT
