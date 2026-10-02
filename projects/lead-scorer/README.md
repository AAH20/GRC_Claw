# AI-Powered Lead Scoring & Qualification

> 7-agent system for automated lead intelligence, scoring, qualification, churn prediction, and next-best-action recommendations.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Gateway                       │
├─────────────────────────────────────────────────────────┤
│  Research → Evidence → Scoring → Qualification          │
│       ↓                                    ↓            │
│  Churn Prediction              Next-Best-Action         │
│       ↓                                    ↓            │
│              Insight Synthesis                          │
├─────────────────────────────────────────────────────────┤
│              GRC_Claw Governance Layer                   │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis  │  LangGraph  │  OpenTelemetry   │
└─────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Research** | Gathers firmographic, technographic, and intent data on leads |
| **Evidence** | Collects and validates supporting evidence for scoring signals |
| **Scoring** | Computes multi-dimensional lead scores (fit, intent, engagement) |
| **Qualification** | Applies BANT/MEDDIC criteria to qualify/disqualify leads |
| **Churn Prediction** | Predicts churn risk for existing customers |
| **Next-Best-Action** | Recommends optimal outreach actions per lead |
| **Insight Synthesis** | Aggregates all agent outputs into actionable insights |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API key

### Local Development

```bash
# Clone and enter
cd ~/GRC_Claw/projects/lead-scorer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Start the API
uvicorn api.main:app --reload --port 8000

# Run tests
pytest
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
# Deploy to cluster
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/leads/score` | Score a single lead |
| `POST` | `/api/v1/leads/score/batch` | Batch score multiple leads |
| `GET` | `/api/v1/leads/{lead_id}` | Get lead score and insights |
| `POST` | `/api/v1/leads/{lead_id}/qualify` | Run qualification |
| `POST` | `/api/v1/leads/{lead_id}/churn-predict` | Predict churn risk |
| `POST` | `/api/v1/leads/{lead_id}/next-action` | Get next best action |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/metrics` | Prometheus metrics |

## Configuration

All configuration is managed via environment variables (see `.env.example`) and `config.yaml`.

Key settings:

- `OPENAI_API_KEY` — Required for LLM-powered agents
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string for caching
- `LOG_LEVEL` — Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `SCORING_MODEL` — LLM model for scoring (default: `gpt-4o`)
- `ENABLE_GOVERNANCE` — Toggle GRC_Claw governance layer

## Project Structure

```
lead-scorer/
├── agents/               # 7 agent implementations
│   ├── base.py          # Base agent class
│   ├── research.py      # Research agent
│   ├── evidence.py      # Evidence agent
│   ├── scoring.py       # Scoring agent
│   ├── qualification.py # Qualification agent
│   ├── churn_prediction.py
│   ├── next_best_action.py
│   └── insight_synthesis.py
├── api/                  # FastAPI application
│   ├── main.py          # App factory
│   ├── routes/          # API route handlers
│   └── models/          # Pydantic request/response models
├── core/                 # Shared core library
│   ├── config.py        # Settings management
│   ├── database.py      # DB connection & session
│   ├── logging.py       # Structured logging
│   ├── governance.py    # GRC_Claw integration
│   └── cli.py           # CLI entry point
├── tests/                # Test suite
│   ├── unit/
│   └── integration/
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipeline
├── config.yaml           # App configuration
├── .env.example          # Environment template
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) runs on every push to `main`:

1. **Lint** — Ruff + mypy
2. **Test** — pytest with coverage
3. **Build** — Docker image build
4. **Deploy** — Push to registry + deploy to Kubernetes

## Revenue Target

$30-50K MRR via tiered SaaS pricing:

- **Starter**: $499/mo (1K leads/mo)
- **Growth**: $1,499/mo (10K leads/mo)
- **Enterprise**: Custom (unlimited + dedicated infra)

## License

MIT
