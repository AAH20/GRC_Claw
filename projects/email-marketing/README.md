# Email Marketing

A standalone, modularized agentic AI email marketing platform built with LangChain DeepAgents and grc-marketing-core.

## Architecture

The system is composed of six specialized AI agents:

| Agent | Responsibility |
|-------|---------------|
| **Segmentation** | Audience segmentation based on behavior, demographics, and engagement |
| **Content Personalization** | Dynamic content generation tailored to individual recipients |
| **Send Time Optimization** | Optimal delivery timing per recipient using engagement history |
| **Subject Line Optimization** | A/B testing and optimization of subject lines for open rates |
| **List Hygiene** | Email list cleaning, validation, and deduplication |
| **Performance Analytics** | Campaign performance tracking, reporting, and insights |

## Integrations

- **SendGrid** — Transactional email delivery
- **Mailchimp** — Audience management and campaign orchestration
- **Klaviyo** — E-commerce focused email marketing automation

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional, for containerized deployment)
- API keys for SendGrid, Mailchimp, and/or Klaviyo

### Local Development

```bash
# Clone and navigate to the project
cd email-marketing

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
uvicorn email_marketing.main:app --reload --port 8000
```

### Docker

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
| `POST` | `/api/v1/campaigns` | Create a new campaign |
| `GET` | `/api/v1/campaigns/{id}` | Get campaign details |
| `POST` | `/api/v1/campaigns/{id}/send` | Send a campaign |
| `GET` | `/api/v1/segments` | List all segments |
| `POST` | `/api/v1/segments` | Create a new segment |
| `GET` | `/api/v1/segments/{id}` | Get segment details |
| `POST` | `/api/v1/segments/{id}/analyze` | Analyze segment performance |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (dev/staging/prod) | `dev` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `SENDGRID_API_KEY` | SendGrid API key | — |
| `MAILCHIMP_API_KEY` | Mailchimp API key | — |
| `MAILCHIMP_SERVER_PREFIX` | Mailchimp server prefix (e.g., `us1`) | — |
| `KLAVIYO_API_KEY` | Klaviyo API key | — |
| `OPENAI_API_KEY` | OpenAI API key for LLM agents | — |

## Project Structure

```
email-marketing/
├── src/email_marketing/
│   ├── agents/           # Six AI marketing agents
│   ├── api/              # FastAPI route handlers
│   ├── integrations/     # Third-party service clients
│   ├── config.py         # Application configuration
│   └── main.py           # FastAPI application entry point
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) automates:

1. **Lint** — Ruff linting and type checking with mypy
2. **Test** — Pytest with coverage reporting
3. **Build** — Docker image build and push to registry
4. **Deploy** — Kubernetes deployment on main branch merges

## License

MIT
