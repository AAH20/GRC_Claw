# Workflow Automation

Standalone modularized agentic AI marketing workflow automation platform. Built with LangChain DeepAgents, grc-marketing-core, and integrates with n8n, Zapier, and Make.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                        │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Workflow │ Workflow │ Process  │Integration│  Performance   │
│ Discovery│Optimization│Automation│Automation │  Analytics     │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│              LangChain DeepAgents + grc-marketing-core        │
├─────────────────────────────────────────────────────────────┤
│         n8n  │  Zapier  │  Make  │  Prometheus Metrics       │
└─────────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Purpose |
|-------|---------|
| **Workflow Discovery** | Discovers and maps existing marketing workflows across tools |
| **Workflow Optimization** | Analyzes workflows for bottlenecks and suggests optimizations |
| **Process Automation** | Automates repetitive marketing processes end-to-end |
| **Integration Automation** | Manages connections between n8n, Zapier, Make, and internal tools |
| **Performance Analytics** | Tracks KPIs, generates reports, and provides insights |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- n8n / Zapier / Make accounts (for integrations)

### Local Development

```bash

# Clone and navigate

cd workflow-automation

# Create virtual environment

python -m venv .venv
source .venv/bin/activate

# Install dependencies

pip install -e ".[dev]"

# Copy environment config

cp .env.example .env

# Edit .env with your API keys

# Run the application

uvicorn workflow_automation.main:app --reload --port 8000
```

### Docker

```bash

# Build and run with Docker Compose

docker-compose up --build

# Or run the Dockerfile directly

docker build -t workflow-automation .
docker run -p 8000:8000 --env-file .env workflow-automation
```

### Kubernetes

```bash

# Deploy to Kubernetes

kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics |
| `POST` | `/api/v1/workflows/discover` | Discover workflows |
| `GET` | `/api/v1/workflows` | List all workflows |
| `GET` | `/api/v1/workflows/{id}` | Get workflow by ID |
| `POST` | `/api/v1/workflows/{id}/optimize` | Optimize a workflow |
| `POST` | `/api/v1/processes` | Create automated process |
| `GET` | `/api/v1/processes` | List processes |
| `POST` | `/api/v1/processes/{id}/execute` | Execute a process |
| `GET` | `/api/v1/integrations/{provider}/status` | Check integration status |
| `POST` | `/api/v1/integrations/{provider}/sync` | Sync with provider |
| `GET` | `/api/v1/analytics/report` | Get performance report |
| `POST` | `/api/v1/analytics/track` | Track a metric event |

## Configuration

All configuration is managed via environment variables. See `.env.example` for all available options.

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (dev/staging/prod) | `dev` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `N8N_BASE_URL` | n8n instance URL | `http://localhost:5678` |
| `N8N_API_KEY` | n8n API key | — |
| `ZAPIER_WEBHOOK_URL` | Zapier webhook URL | — |
| `MAKE_API_KEY` | Make API key | — |
| `MAKE_BASE_URL` | Make API base URL | `https://www.make.com` |
| `LANGCHAIN_API_KEY` | LangChain API key | — |
| `LANGCHAIN_PROJECT` | LangChain project name | `workflow-automation` |

## Project Structure

```
workflow-automation/
├── src/workflow_automation/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Settings management
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── workflow_discovery.py
│   │   ├── workflow_optimization.py
│   │   ├── process_automation.py
│   │   ├── integration_automation.py
│   │   └── performance_analytics.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── workflows.py
│   │   └── processes.py
│   └── integrations/
│       ├── __init__.py
│       ├── n8n.py
│       ├── zapier.py
│       └── make.py
├── tests/
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_integrations.py
├── config/
│   └── config.yaml
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── .github/workflows/
│   └── ci-cd.yml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── pyproject.toml
└── README.md
```

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) provides:

1. **Lint & Type Check** — Ruff + mypy
2. **Test** — pytest with coverage
3. **Build** — Docker image build
4. **Deploy** — Kubernetes deployment (on main branch)

## Testing

```bash

# Run all tests

pytest

# Run with coverage

pytest --cov=workflow_automation --cov-report=term-missing

# Run specific test file

pytest tests/test_agents.py -v
```

## License

MIT
