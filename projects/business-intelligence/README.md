# Business Intelligence

A modularized agentic AI business intelligence platform built with FastAPI, LangChain DeepAgents, and grc-marketing-core. Integrates with Tableau, Power BI, and Looker for enterprise-grade analytics.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│   Data   │ Analysis │   Viz    │ Reporting│  Predictive │
│Collection│  Agent   │  Agent   │  Agent   │  Analytics  │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│              Integrations Layer                          │
├──────────────┬──────────────────┬───────────────────────┤
│    Tableau   │    Power BI      │       Looker          │
└──────────────┴──────────────────┴───────────────────────┘
```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Data Collection** | Gathers data from APIs, databases, and file sources |
| **Analysis** | Performs statistical analysis, trend detection, and anomaly identification |
| **Visualization** | Generates charts, graphs, and interactive dashboards |
| **Reporting** | Produces formatted reports (PDF, HTML, Markdown) |
| **Predictive Analytics** | ML-based forecasting and predictive modeling |

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

# Run the application

uvicorn business_intelligence.main:app --reload --port 8000
```

### Docker

```bash

# Build and run with Docker Compose

docker-compose up --build
```

### Kubernetes

```bash

# Deploy to Kubernetes cluster

kubectl apply -f k8s/
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/reports` | POST | Generate a report |
| `/api/v1/reports/{report_id}` | GET | Retrieve a report |
| `/api/v1/dashboards` | POST | Create a dashboard |
| `/api/v1/dashboards/{dashboard_id}` | GET | Retrieve a dashboard |
| `/api/v1/agents/data-collection` | POST | Trigger data collection |
| `/api/v1/agents/analysis` | POST | Run analysis |
| `/api/v1/agents/visualization` | POST | Generate visualizations |
| `/api/v1/agents/predictive` | POST | Run predictive analytics |

## Configuration

All configuration is managed via environment variables. See `.env.example` for available options.

## CI/CD

GitHub Actions workflow at `.github/workflows/ci-cd.yml` handles:
- Linting and type checking
- Unit and integration tests
- Docker image build and push
- Kubernetes deployment

## License

MIT
