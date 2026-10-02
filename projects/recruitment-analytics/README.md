# Recruitment Analytics

Agentic AI-powered recruitment analytics platform with funnel analysis, source tracking, and predictive hiring.

## Features

- **Funnel Analysis**: Analyze recruitment funnel metrics, identify bottlenecks, and optimize conversion rates
- **Source Tracking**: Track recruitment source effectiveness, cost per hire, and quality scores
- **Predictive Hiring**: ML-powered candidate success predictions with confidence scoring
- **Diversity Analytics**: Monitor diversity metrics across the recruitment pipeline
- **Cost Analysis**: Track recruitment spend, cost per hire, and budget variance

## Architecture

- **Framework**: FastAPI with async support
- **AI**: LangChain DeepAgents for agent implementations
- **Data**: Pydantic v2 models with strict validation
- **Deployment**: Docker, Kubernetes with Helm/Kustomize

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
python -m recruitment_analytics.main
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Kubernetes

```bash
# Deploy to development
kubectl apply -k k8s/overlays/development

# Deploy to production
kubectl apply -k k8s/overlays/production
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/ready` | Readiness probe |
| GET | `/api/v1/live` | Liveness probe |
| POST | `/api/v1/funnel/analyze` | Analyze recruitment funnel |
| GET | `/api/v1/funnel/stages` | Get funnel stages |
| POST | `/api/v1/source/analyze` | Analyze recruitment sources |
| GET | `/api/v1/source/types` | Get source types |
| POST | `/api/v1/prediction/analyze` | Predict candidate success |
| GET | `/api/v1/prediction/outcomes` | Get prediction outcomes |
| POST | `/api/v1/diversity/analyze` | Analyze diversity metrics |
| GET | `/api/v1/diversity/dimensions` | Get diversity dimensions |
| POST | `/api/v1/cost/analyze` | Analyze recruitment costs |
| GET | `/api/v1/cost/categories` | Get cost categories |

## Project Structure

```
recruitment-analytics/
├── src/recruitment_analytics/
│   ├── agents/           # LangChain agent implementations
│   ├── api/              # FastAPI routes and middleware
│   ├── config/           # Application configuration
│   ├── integrations/     # External API clients
│   ├── models/           # Pydantic models
│   └── tests/            # Test suite
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## License

MIT
