# Sales Automator

A standalone, modularized agentic AI sales automation platform built with LangChain DeepAgents and grc-marketing-core. It orchestrates six specialized agents — Prospecting, Outreach, Qualification, Demo Scheduling, Follow-up, and Sales Forecasting — and integrates with Salesforce, HubSpot, LinkedIn, and Google Calendar.

## Architecture

```

┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ Prospect │ Outreach │ Qualify  │ Schedule │  Forecast   │
│  Agent   │  Agent   │  Agent   │  Agent   │   Agent     │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│              Integration Layer                            │
│  Salesforce │ HubSpot │ LinkedIn │ Google Calendar       │
└─────────────────────────────────────────────────────────┘

```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- API keys for Salesforce, HubSpot, LinkedIn, Google Calendar, and OpenAI

### Local Development

```bash

# Clone and enter the project

cd sales-automator

# Create virtual environment

python -m venv .venv
source .venv/bin/activate

# Install dependencies

pip install -e ".[dev]"

# Configure environment

cp .env.example .env

# Edit .env with your API keys

# Run the application

uvicorn sales_automator.main:app --reload --port 8000

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
| POST | `/api/v1/prospects` | Create a prospect |
| GET | `/api/v1/prospects` | List prospects |
| GET | `/api/v1/prospects/{id}` | Get prospect by ID |
| POST | `/api/v1/sequences` | Create outreach sequence |
| GET | `/api/v1/sequences` | List sequences |
| POST | `/api/v1/sequences/{id}/enroll` | Enroll prospect in sequence |

## Agents

### Prospecting Agent

Discovers and scores potential leads using firmographic and technographic signals from LinkedIn and web sources.

### Outreach Agent

Generates personalized multi-channel outreach sequences (email, LinkedIn, calls) using LLM-powered content generation.

### Qualification Agent

Engages prospects in conversation, assesses BANT (Budget, Authority, Need, Timeline), and scores fit.

### Demo Scheduling Agent

Coordinates with Google Calendar to find mutually available time slots and books demos.

### Follow-up Agent

Manages post-demo and post-outreach follow-ups with contextual messaging and cadence management.

### Sales Forecasting Agent

Analyzes pipeline data from Salesforce and HubSpot to generate revenue forecasts and identify at-risk deals.

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:

- `OPENAI_API_KEY` — LLM provider key
- `SALESFORCE_CLIENT_ID` / `SALESFORCE_CLIENT_SECRET` — Salesforce OAuth
- `HUBSPOT_API_KEY` — HubSpot private app token
- `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` — LinkedIn OAuth
- `GOOGLE_CALENDAR_CREDENTIALS_PATH` — Service account JSON path

## Testing

```bash

pytest --cov=sales_automator --cov-report=term-missing

```

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) runs linting, type checking, and tests on every push, and builds/pushes a Docker image on merges to `main`.

## License

MIT
