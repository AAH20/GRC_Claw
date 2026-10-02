# Quality Scoring Service

AI-powered content quality scoring service with multi-dimensional analysis using LangChain DeepAgents.

## Features

- **Multi-dimensional scoring**: Readability, Originality, Engagement, SEO
- **Improvement suggestions**: AI-generated actionable recommendations
- **Benchmark comparison**: Compare content against industry benchmarks
- **5 specialized agents**: Each dimension scored by a dedicated agent
- **Production-ready**: Docker, Kubernetes, CI/CD included

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn quality_scoring.main:create_app --factory --reload

# Or with Docker
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/v1/score` | Score content quality |
| POST | `/api/v1/score/readability` | Score readability only |
| POST | `/api/v1/score/originality` | Score originality only |
| POST | `/api/v1/score/engagement` | Score engagement only |
| POST | `/api/v1/score/seo` | Score SEO only |
| POST | `/api/v1/improvements` | Get improvement suggestions |
| POST | `/api/v1/benchmark` | Compare against benchmarks |
| POST | `/api/v1/batch/score` | Batch score multiple content |
| GET | `/api/v1/dimensions` | List scoring dimensions |
| GET | `/api/v1/benchmarks` | List available benchmarks |

## Architecture

```
src/quality_scoring/
├── main.py              # FastAPI app factory
├── config/              # Settings and configuration
├── models/              # Pydantic schemas
├── agents/              # LangChain DeepAgents
│   ├── base.py          # Base agent class
│   ├── readability.py   # ReadabilityScorerAgent
│   ├── originality.py   # OriginalityScorerAgent
│   ├── engagement.py    # EngagementScorerAgent
│   ├── seo.py           # SEOScorerAgent
│   └── improvement.py   # ImprovementSuggesterAgent
├── api/                 # FastAPI routes
├── integrations/        # External service clients
└── services/            # Business logic
```

## License

MIT
