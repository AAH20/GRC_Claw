# Autonomous Campaign Optimization

> Multi-agent AI marketing platform for autonomous campaign strategy, optimization, and governance.

## Overview

Autonomous Campaign Optimization is a production-grade, multi-agent system that leverages LangChain DeepAgents and GRC_Claw governance to autonomously plan, execute, and optimize marketing campaigns. The system consists of six specialized agents working in concert:

| Agent | Responsibility |
|-------|---------------|
| **Strategy Agent** | High-level campaign planning, goal decomposition, budget allocation |
| **Research Agent** | Market research, competitor analysis, audience insights |
| **Creative Agent** | Ad copy generation, creative asset recommendations, A/B test variants |
| **Bidding Agent** | Real-time bid optimization, budget pacing, ROAS maximization |
| **Audience Agent** | Audience segmentation, targeting, lookalike expansion |
| **Critic Agent** | Quality assurance, performance evaluation, governance enforcement |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Gateway                       │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Strategy │  │ Research │  │ Creative │              │
│  │  Agent   │  │  Agent   │  │  Agent   │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │              │              │                    │
│  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐              │
│  │ Bidding  │  │ Audience │  │  Critic  │              │
│  │  Agent   │  │  Agent   │  │  Agent   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
├─────────────────────────────────────────────────────────┤
│              GRC_Claw Governance Layer                   │
├─────────────────────────────────────────────────────────┤
│         grc-marketing-core (Shared Library)              │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- Redis (for agent state management)
- PostgreSQL (for campaign data persistence)

### Local Development

```bash
# Clone and navigate
cd ~/GRC_Claw/projects/campaign-optimizer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys and settings

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn api.main:app --reload --port 8000

# Run tests
pytest
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

### Kubernetes Deployment

```bash
# Apply configurations
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# Check deployment status
kubectl get pods -n campaign-optimizer
kubectl get svc -n campaign-optimizer
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/campaigns` | Create a new campaign |
| `GET` | `/api/v1/campaigns` | List all campaigns |
| `GET` | `/api/v1/campaigns/{id}` | Get campaign details |
| `PUT` | `/api/v1/campaigns/{id}` | Update campaign |
| `DELETE` | `/api/v1/campaigns/{id}` | Delete campaign |
| `POST` | `/api/v1/campaigns/{id}/optimize` | Trigger optimization cycle |
| `GET` | `/api/v1/campaigns/{id}/status` | Get campaign status |
| `GET` | `/api/v1/agents/{agent_id}/status` | Get agent status |

## Configuration

All configuration is managed via environment variables (see `.env.example`) and `config.yaml`:

- **LLM Settings**: Model selection, temperature, token limits
- **Agent Settings**: Timeouts, retry policies, concurrency limits
- **Governance**: GRC_Claw policy enforcement, approval thresholds
- **Infrastructure**: Redis, PostgreSQL, API rate limiting

## Project Structure

```
campaign-optimizer/
├── agents/                 # Agent implementations
│   ├── base.py            # Base agent class
│   ├── strategy.py        # Strategy agent
│   ├── research.py        # Research agent
│   ├── creative.py        # Creative agent
│   ├── bidding.py         # Bidding agent
│   ├── audience.py        # Audience agent
│   └── critic.py          # Critic agent
├── api/                    # FastAPI application
│   ├── main.py            # Application entry point
│   ├── routes/            # API route handlers
│   └── models/            # Pydantic request/response models
├── core/                   # Shared core library
│   ├── config.py          # Configuration management
│   ├── logging.py         # Structured logging
│   └── exceptions.py      # Custom exceptions
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── k8s/                    # Kubernetes manifests
├── .github/workflows/      # CI/CD pipeline
├── config.yaml            # Application configuration
├── .env.example           # Environment variable template
├── Dockerfile             # Container image definition
├── docker-compose.yml     # Multi-service orchestration
└── pyproject.toml         # Project metadata & dependencies
```

## CI/CD

The project includes a GitHub Actions workflow that:

1. Runs linting (ruff) and type checking (mypy)
2. Executes unit and integration tests with coverage
3. Builds and pushes Docker images to a container registry
4. Deploys to Kubernetes on main branch merges

## Revenue Target

**$30-60K MRR** — Based on projected SaaS pricing tiers and customer acquisition targets over a 75-90 day build timeline.

## License

MIT
