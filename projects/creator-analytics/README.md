# Creator Analytics

Agentic AI platform for creator analytics with audience analysis, content performance, and revenue tracking.

## Features

- **Audience Analysis**: Demographic breakdown, segmentation, and behavior insights
- **Content Performance**: Metrics analysis, benchmarking, and optimization recommendations
- **Revenue Tracking**: Multi-stream revenue analysis and monetization opportunities
- **Growth Prediction**: AI-powered growth forecasting with multiple scenarios
- **Engagement Analysis**: Community health, loyalty scoring, and engagement patterns

## Tech Stack

- **Framework**: FastAPI with Pydantic v2
- **AI**: LangChain DeepAgents
- **Python**: 3.11+ with type hints
- **Testing**: pytest with async support
- **Deployment**: Docker, Kubernetes

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the application
uvicorn creator_analytics.main:app --reload
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Kubernetes

```bash
# Deploy to Kubernetes
kubectl apply -k k8s/overlays/production
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check |
| POST | `/api/v1/audience/analyze` | Analyze audience |
| GET | `/api/v1/audience/{creator_id}` | Get audience analysis |
| GET | `/api/v1/audience/{creator_id}/segments` | Get audience segments |
| POST | `/api/v1/content/analyze` | Analyze content performance |
| GET | `/api/v1/content/{content_id}` | Get content performance |
| GET | `/api/v1/content/creator/{creator_id}` | Get creator content |
| POST | `/api/v1/revenue/report` | Generate revenue report |
| GET | `/api/v1/revenue/{creator_id}` | Get revenue report |
| GET | `/api/v1/revenue/{creator_id}/breakdown` | Get revenue breakdown |
| POST | `/api/v1/growth/predict` | Predict growth |
| GET | `/api/v1/growth/{creator_id}` | Get growth prediction |
| GET | `/api/v1/growth/{creator_id}/scenarios` | Get growth scenarios |
| POST | `/api/v1/engagement/report` | Generate engagement report |
| GET | `/api/v1/engagement/{creator_id}` | Get engagement report |
| GET | `/api/v1/engagement/{creator_id}/metrics` | Get engagement metrics |

## Project Structure

```
creator-analytics/
├── src/creator_analytics/
│   ├── agents/           # LangChain DeepAgents implementations
│   ├── api/              # FastAPI routes
│   ├── config/           # Application configuration
│   ├── integrations/     # External platform integrations
│   ├── models/           # Pydantic data models
│   └── tests/            # Test suite
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## License

MIT
