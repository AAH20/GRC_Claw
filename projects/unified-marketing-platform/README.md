# Unified Marketing Platform

A consolidated agentic AI marketing platform that unifies campaign management, content generation, analytics, and compliance across all marketing verticals. Built with LangChain DeepAgents, grc-marketing-core, and FastAPI.

## Architecture

```
unified_marketing_platform/
├── agents/           # Cross-vertical AI agents
│   ├── content.py     # Unified content generation
│   ├── campaigns.py   # Cross-channel campaign orchestration
│   ├── analytics.py   # Unified analytics & attribution
│   ├── compliance.py  # Multi-regulation compliance (HIPAA, FINRA, SEC)
│   └── reporting.py   # Consolidated reporting
├── api/              # FastAPI route handlers
│   ├── campaigns.py
│   ├── content.py
│   └── analytics.py
├── integrations/     # Third-party connectors
│   ├── salesforce.py
│   ├── hubspot.py
│   ├── mailchimp.py
│   └── stripe.py
├── config/           # Configuration management
└── main.py           # Application entry point
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- API keys for OpenAI and your marketing platforms

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
uvicorn unified_marketing_platform.main:app --reload --port 8000
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
| `POST` | `/api/v1/campaigns` | Create a campaign |
| `GET` | `/api/v1/campaigns` | List all campaigns |
| `GET` | `/api/v1/campaigns/{id}` | Get campaign details |
| `POST` | `/api/v1/content/generate` | Generate marketing content |
| `POST` | `/api/v1/content/validate` | Validate content compliance |
| `GET` | `/api/v1/analytics/dashboard` | Get unified analytics |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:
- `OPENAI_API_KEY` — OpenAI API key for LLM operations
- `APP_ENV` — Runtime environment (development/staging/production)
- `LOG_LEVEL` — Logging verbosity

## Testing

```bash
pytest --cov=unified_marketing_platform --cov-report=html
```

## CI/CD

GitHub Actions workflow at `.github/workflows/ci-cd.yml` handles:

1. Linting (ruff) and type checking (mypy)
2. Unit and integration tests with coverage
3. Docker image build and push
4. Kubernetes deployment

## License

MIT
