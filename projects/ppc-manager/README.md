# PPC Manager

AI-powered Pay-Per-Click (PPC) campaign management platform that orchestrates intelligent agents across **Google Ads**, **Meta Ads**, **LinkedIn Ads**, and **TikTok Ads**.

## Architecture

The system is built around six specialized AI agents:

| Agent | Responsibility |
|-------|---------------|
| **Keyword Research** | Discovers, scores, and expands keyword opportunities |
| **Bid Management** | Optimizes CPC/CPM bids using performance signals |
| **Ad Creative** | Generates and iterates ad copy, headlines, and CTAs |
| **Landing Page Optimization** | Analyzes and recommends landing page improvements |
| **Budget Allocation** | Distributes budget across campaigns based on ROI |
| **Performance Analytics** | Aggregates metrics, detects anomalies, and reports |

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **AI Orchestration**: LangChain DeepAgents + LangGraph
- **Integrations**: Google Ads API, Meta Marketing API, LinkedIn Ads API, TikTok Marketing API
- **Observability**: Prometheus metrics, structlog structured logging
- **Deployment**: Docker, Kubernetes, GitHub Actions CI/CD

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- API credentials for each ad platform

### Local Development

```bash
# Clone and enter the project
cd ppc-manager

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp config/.env.example .env
# Edit .env with your API credentials

# Run the server
uvicorn ppc_manager.main:app --reload --port 8000
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
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/api/v1/campaigns` | List campaigns |
| `POST` | `/api/v1/campaigns` | Create campaign |
| `GET` | `/api/v1/campaigns/{id}` | Get campaign details |
| `PUT` | `/api/v1/campaigns/{id}` | Update campaign |
| `DELETE` | `/api/v1/campaigns/{id}` | Delete campaign |
| `GET` | `/api/v1/keywords` | List keywords |
| `POST` | `/api/v1/keywords/research` | Run keyword research |
| `POST` | `/api/v1/agents/{agent}/invoke` | Invoke an agent |

## Project Structure

```
ppc-manager/
├── src/ppc_manager/
│   ├── agents/           # AI agent implementations
│   ├── api/              # FastAPI route handlers
│   ├── integrations/     # Ad platform API clients
│   ├── main.py           # Application entry point
│   └── __init__.py
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Configuration

All configuration is managed via environment variables. See `config/.env.example` for the full list.

Key variables:

- `OPENAI_API_KEY` — LLM API key for agent reasoning
- `GOOGLE_ADS_DEVELOPER_TOKEN` — Google Ads API developer token
- `GOOGLE_ADS_CLIENT_ID` / `GOOGLE_ADS_CLIENT_SECRET` — OAuth2 credentials
- `META_ACCESS_TOKEN` — Meta Marketing API access token
- `LINKEDIN_ACCESS_TOKEN` — LinkedIn Ads API access token
- `TIKTOK_ACCESS_TOKEN` — TikTok Marketing API access token

## License

MIT
