# Content Discovery Service

Agentic AI content discovery with semantic search, personalization, and trend detection.

## Architecture

- **FastAPI** web framework with `src/` layout
- **LangChain DeepAgents** for agent implementations
- **Pydantic v2** for request/response validation
- **Redis** for caching and user profiles
- **Vector Store** for semantic search

## Agents

| Agent | Purpose |
|-------|---------|
| `SemanticSearchAgent` | Vector similarity search with LLM re-ranking |
| `PersonalizationAgent` | User preference inference and content matching |
| `TrendDetectorAgent` | Temporal pattern analysis for trend detection |
| `RecommendationAgent` | Multi-strategy content recommendations |
| `SearchExplainerAgent` | Human-readable search result explanations |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |
| POST | `/api/v1/search` | Semantic search |
| POST | `/api/v1/search/explain` | Search with AI explanation |
| GET | `/api/v1/search/suggest` | Search suggestions |
| POST | `/api/v1/recommendations` | Get recommendations |
| GET | `/api/v1/recommendations/{user_id}` | User recommendations |
| POST | `/api/v1/trends` | Detect trends |
| GET | `/api/v1/trends` | Get current trends |
| GET | `/api/v1/users/{user_id}/profile` | User profile |
| POST | `/api/v1/users/{user_id}/history` | Add user history |
| GET | `/metrics` | Service metrics |

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run locally
uvicorn content_discovery.main:create_app --factory --reload

# Run with Docker
docker-compose up --build
```

## Development

```bash
# Linting
ruff check src/

# Type checking
mypy src/

# Run tests with coverage
pytest --cov=content_discovery --cov-report=term
```

## License

MIT
