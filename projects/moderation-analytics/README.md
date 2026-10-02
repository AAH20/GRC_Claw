# Moderation Analytics

Agentic AI-powered moderation analytics service for GRC_Claw. Provides trend analysis, moderator performance metrics, policy effectiveness scoring, and predictive moderation insights.

## Architecture

- **FastAPI** application with `src/` layout
- **LangChain DeepAgents** for agent implementations
- **Pydantic v2** models for request/response validation
- **Prometheus** metrics integration
- **Structlog** structured logging

## Agents

| Agent | Purpose |
|-------|---------|
| `TrendAnalyzerAgent` | Analyzes moderation trends over time |
| `ModeratorPerformanceAgent` | Evaluates moderator accuracy, speed, and consistency |
| `PolicyEffectivenessAgent` | Measures policy impact and violation rates |
| `ModerationPredictorAgent` | Predicts future moderation workload and risk |
| `AnalyticsExplainerAgent` | Generates human-readable explanations of analytics |

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn moderation_analytics.main:create_app --factory --reload

# Or use the entry point
moderation-analytics
```

## Docker

```bash
docker build -t moderation-analytics .
docker run -p 8000:8000 moderation-analytics
```

## Docker Compose

```bash
docker-compose up -d
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/v1/analytics/summary` | Full analytics summary |
| GET | `/api/v1/trends` | Moderation trends |
| POST | `/api/v1/trends/analyze` | Analyze trends with AI |
| GET | `/api/v1/moderators` | List moderators |
| GET | `/api/v1/moderators/{id}/performance` | Moderator performance |
| POST | `/api/v1/moderators/evaluate` | Evaluate moderators with AI |
| GET | `/api/v1/policies` | List policies |
| GET | `/api/v1/policies/{id}/effectiveness` | Policy effectiveness |
| POST | `/api/v1/policies/assess` | Assess policies with AI |
| POST | `/api/v1/predictions` | Generate predictions |
| POST | `/api/v1/explain` | Explain analytics results |

## Kubernetes

```bash
kubectl apply -f k8s/
```

## CI/CD

GitHub Actions workflows for CI (lint, type check, test) and CD (build, push, deploy).
