# Account-Based Marketing (ABM) Platform

An AI-powered Account-Based Marketing platform built with LangChain DeepAgents and grc-marketing-core. Features 6 specialized agents for end-to-end ABM orchestration.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ Account  │  Intent  │ Buying   │ Content  │  Channel    │
│ Identif. │ Scoring  │Committee │Personal. │ Orchestrator│
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│              Performance Analytics Agent                  │
├─────────────────────────────────────────────────────────┤
│         Integrations: Salesforce / HubSpot / LinkedIn    │
└─────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Purpose |
|-------|---------|
| **Account Identification** | Discovers and scores target accounts using firmographic and technographic signals |
| **Intent Scoring** | Analyzes intent data to prioritize accounts showing buying signals |
| **Buying Committee Mapper** | Maps decision-makers and influencers within target accounts |
| **Content Personalization** | Generates personalized content for each account and persona |
| **Channel Orchestrator** | Coordinates multi-channel outreach (email, ads, social, web) |
| **Performance Analytics** | Tracks campaign performance, attribution, and ROI metrics |

## Quick Start

### Local Development

```bash

# Create virtual environment

python -m venv .venv
source .venv/bin/activate

# Install dependencies

pip install -e ".[dev]"

# Copy environment config

cp .env.example .env

# Run the application

uvicorn src.abm.main:app --reload --port 8000
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
| `GET` | `/accounts` | List target accounts |
| `POST` | `/accounts/identify` | Identify new target accounts |
| `GET` | `/accounts/{id}/intent` | Get intent score for account |
| `GET` | `/accounts/{id}/committee` | Get buying committee map |
| `POST` | `/campaigns` | Create ABM campaign |
| `GET` | `/campaigns/{id}` | Get campaign details |
| `GET` | `/campaigns/{id}/analytics` | Get campaign analytics |
| `POST` | `/campaigns/{id}/personalize` | Generate personalized content |
| `POST` | `/campaigns/{id}/orchestrate` | Trigger channel orchestration |

## Configuration

See `config/config.yaml` for application settings and `.env.example` for environment variables.

## Testing

```bash
pytest tests/ -v --cov=src/abm
```

## CI/CD

GitHub Actions workflow at `.github/workflows/ci-cd.yml` handles:
- Linting and type checking
- Unit and integration tests
- Docker image build and push
- Kubernetes deployment

## License

MIT
