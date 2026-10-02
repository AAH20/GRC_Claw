# Agentic Customer Journey Orchestrator

A standalone, modularized multi-agent system for designing, personalizing, timing, and optimizing customer journeys across channels. Built with LangChain DeepAgents, governed by GRC_Claw, and powered by the shared `grc-marketing-core` library.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Journey  │ │Personal- │ │ Timing   │ │Experimen-│  │
│  │ Designer │ │ization   │ │Optimizer │ │tation    │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │             │             │             │        │
│  ┌────┴─────────────┴─────────────┴─────────────┴────┐  │
│  │           Cross-Channel Coordinator               │  │
│  └────────────────────┬──────────────────────────────┘  │
│                       │                                  │
│  ┌────────────────────┴──────────────────────────────┐  │
│  │              Critic Agent (Governance)             │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                                    │
    ┌────┴────┐                        ┌──────┴──────┐
    │  Redis  │                        │  PostgreSQL  │
    │ (Cache) │                        │  (Persistence)│
    └─────────┘                        └─────────────┘
```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Journey Designer** | Designs end-to-end customer journey maps with stages, transitions, and goals |
| **Personalization Engine** | Generates personalized content, offers, and recommendations per customer segment |
| **Timing Optimizer** | Determines optimal send times, frequency caps, and cadence per customer |
| **Experimentation** | Designs A/B tests, manages experiment lifecycle, and analyzes results |
| **Critic** | Validates journey quality, checks for compliance, and provides improvement feedback |
| **Cross-Channel Coordinator** | Orchestrates execution across email, SMS, push, web, and ad channels |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- Redis 7+
- PostgreSQL 15+

### Local Development

```bash
# Clone and navigate
cd ~/GRC_Claw/projects/journey-orchestrator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment configuration
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn api.main:app --reload --port 8000

# Or use the CLI entry point
journey-orchestrator
```

### Docker

```bash
# Build and start all services
docker-compose up --build

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/journeys` | Create a new customer journey |
| `GET` | `/api/v1/journeys/{journey_id}` | Get journey by ID |
| `PUT` | `/api/v1/journeys/{journey_id}` | Update journey |
| `DELETE` | `/api/v1/journeys/{journey_id}` | Delete journey |
| `POST` | `/api/v1/journeys/{journey_id}/execute` | Execute a journey |
| `GET` | `/api/v1/journeys/{journey_id}/status` | Get journey execution status |
| `POST` | `/api/v1/personalize` | Generate personalized content |
| `POST` | `/api/v1/optimize-timing` | Get optimal send time |
| `POST` | `/api/v1/experiments` | Create A/B test |
| `GET` | `/api/v1/experiments/{exp_id}/results` | Get experiment results |
| `GET` | `/health` | Health check |

## Configuration

All configuration is managed via environment variables (see `.env.example`) and `config.yaml`. The system uses Pydantic Settings for validation and type safety.

## Testing

```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with coverage
pytest --cov --cov-report=html
```

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) runs on every push to `main`:

1. Lint (Ruff) and type-check (mypy)
2. Unit tests with coverage
3. Integration tests
4. Build Docker image
5. Push to container registry
6. Deploy to Kubernetes (staging → production)

## Project Structure

```
journey-orchestrator/
├── agents/                  # Agent implementations
│   ├── base.py             # Base agent class
│   ├── journey_designer.py
│   ├── personalization_engine.py
│   ├── timing_optimizer.py
│   ├── experimentation.py
│   ├── critic.py
│   └── cross_channel_coordinator.py
├── api/                    # FastAPI application
│   ├── main.py            # App entry point
│   ├── routes/            # API route handlers
│   └── models/            # Pydantic request/response models
├── core/                   # Shared core library
│   ├── config.py          # Settings management
│   ├── logging.py         # Structured logging
│   └── exceptions.py      # Custom exceptions
├── tests/                  # Test suite
│   ├── unit/
│   └── integration/
├── k8s/                    # Kubernetes manifests
├── .github/workflows/      # CI/CD pipeline
├── config.yaml            # Application configuration
├── .env.example           # Environment template
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Revenue Target

$30-50K MRR within 75-90 days of build time.

## License

Proprietary — All rights reserved.
