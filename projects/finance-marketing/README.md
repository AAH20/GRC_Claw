# Finance Marketing

A standalone, modularized agentic AI marketing platform for financial services, built with LangChain DeepAgents and grc-marketing-core. Designed for FINRA/SEC compliance from the ground up.

## Architecture

```
finance_marketing/
├── agents/           # 5 specialized agents
│   ├── content.py     # Content generation & management
│   ├── compliance.py  # FINRA/SEC compliance checking
│   ├── campaigns.py   # Campaign orchestration
│   ├── analytics.py   # Performance analytics
│   └── reporting.py   # Regulatory reporting
├── api/              # FastAPI route handlers
│   ├── campaigns.py
│   └── content.py
├── integrations/     # Third-party connectors
│   ├── salesforce.py
│   ├── hubspot.py
│   └── mailchimp.py
├── config/           # Configuration
└── main.py           # Application entry point
```

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
# Edit .env with your credentials

# Run the application
uvicorn finance_marketing.main:app --reload --port 8000
```

## Docker

```bash
docker-compose up --build
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

## Agents

| Agent | Purpose |
|-------|---------|
| **Content** | Generates marketing copy, social posts, email campaigns with compliance-aware templates |
| **Compliance** | Validates content against FINRA/SEC rules, maintains audit trails |
| **Campaigns** | Orchestrates multi-channel campaign lifecycle |
| **Analytics** | Tracks campaign performance, ROI, engagement metrics |
| **Reporting** | Generates regulatory reports and performance dashboards |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/content/generate` | Generate marketing content |
| `POST` | `/api/v1/content/validate` | Validate content compliance |
| `POST` | `/api/v1/campaigns` | Create a campaign |
| `GET` | `/api/v1/campaigns/{id}` | Get campaign details |
| `POST` | `/api/v1/campaigns/{id}/launch` | Launch a campaign |
| `GET` | `/api/v1/campaigns/{id}/analytics` | Get campaign analytics |

## Compliance

This platform is designed for financial services marketing with:

- **FINRA Rule 2210** compliance checks (communications with the public)
- **SEC Marketing Rule** compliance (advertising by investment advisers)
- **Audit trails** for all content generation and approval workflows
- **Pre-approval workflows** for regulated content
- **Disclosure management** and required legal text injection

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (dev/staging/prod) | `dev` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `DATABASE_URL` | Database connection URL | — |
| `SALESFORCE_CLIENT_ID` | Salesforce OAuth client ID | — |
| `HUBSPOT_API_KEY` | HubSpot API key | — |
| `MAILCHIMP_API_KEY` | Mailchimp API key | — |

## Testing

```bash
pytest
```

## CI/CD

GitHub Actions workflow at `.github/workflows/ci-cd.yml` handles:

1. Linting (ruff) and type checking (mypy)
2. Unit and integration tests with coverage
3. Docker image build and push
4. Kubernetes deployment

## License

Proprietary. All rights reserved.
