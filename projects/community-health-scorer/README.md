# Community Health Scorer

AI-powered community health scoring service using LangChain DeepAgents. Analyzes engagement metrics, detects toxicity, predicts churn, and explains community health scores.

## Features

- **Engagement Metrics Agent** — Tracks DAU/MAU ratios, session duration, interaction depth
- **Toxicity Detector Agent** — Identifies toxic content and behavior patterns
- **Growth Analyzer Agent** — Analyzes member growth trends and retention
- **Churn Predictor Agent** — Predicts member churn risk using behavioral signals
- **Health Explainer Agent** — Generates human-readable explanations of health scores

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run locally
uvicorn community_health_scorer.main:create_app --factory --reload

# Run with Docker
docker-compose up --build

# Run tests
pytest
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| GET | `/ready` | Readiness probe |
| POST | `/api/v1/score` | Calculate overall health score |
| POST | `/api/v1/score/engagement` | Score engagement metrics |
| POST | `/api/v1/score/toxicity` | Score toxicity levels |
| POST | `/api/v1/score/growth` | Score growth metrics |
| POST | `/api/v1/score/churn` | Score churn risk |
| GET | `/api/v1/agents` | List available agents |
| GET | `/api/v1/agents/{agent_name}` | Get agent details |
| POST | `/api/v1/agents/{agent_name}/run` | Run a specific agent |
| GET | `/api/v1/metrics` | Prometheus metrics |
| GET | `/api/v1/analytics/summary` | Community analytics summary |

## Architecture

```
src/community_health_scorer/
├── main.py              # FastAPI app factory
├── config/              # Settings and configuration
├── models/              # Pydantic schemas
├── agents/              # LangChain DeepAgents
├── api/                 # FastAPI routes
├── integrations/        # External service clients
└── utils/               # Helper utilities
```

## License

MIT
