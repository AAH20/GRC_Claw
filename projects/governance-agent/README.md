# Governance Agent

An AI governance and compliance agent for monitoring, auditing, and enforcing policies across agentic AI marketing systems. Built with LangChain DeepAgents and grc-marketing-core.

## Architecture

```
governance_agent/
├── agents/           # Governance AI agents
│   ├── audit.py       # Automated compliance auditing
│   ├── policy.py      # Policy enforcement & validation
│   ├── risk.py        # Risk assessment & mitigation
│   └── reporting.py   # Governance reporting
├── api/              # FastAPI route handlers
│   ├── audit.py
│   ├── policies.py
│   └── reports.py
├── integrations/     # External system connectors
│   ├── prometheus.py
│   └── elasticsearch.py
├── config/           # Configuration management
└── main.py           # Application entry point
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your settings

# Run the application
uvicorn governance_agent.main:app --reload --port 8000
```

## Docker

```bash
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/audit` | Run a governance audit |
| `GET` | `/api/v1/policies` | List all policies |
| `POST` | `/api/v1/policies` | Create a new policy |
| `GET` | `/api/v1/reports` | List governance reports |
| `POST` | `/api/v1/reports/generate` | Generate a governance report |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:
- `GOVERNANCE_ENV` — Runtime environment
- `PROMETHEUS_URL` — Prometheus metrics endpoint
- `ELASTICSEARCH_URL` — Elasticsearch connection

## Testing

```bash
pytest --cov=governance_agent --cov-report=html
```

## CI/CD

GitHub Actions workflow at `.github/workflows/ci-cd.yml` handles:

1. Linting (ruff) and type checking (mypy)
2. Unit and integration tests with coverage
3. Docker image build and push

## License

MIT
