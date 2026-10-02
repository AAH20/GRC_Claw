# Community Curation

Agentic AI service for curating community content with content ranking, trend surfacing, and quality filtering.

## Architecture

- **FastAPI** application with `src/` layout
- **LangChain DeepAgents** for agent implementations
- **5 specialized agents**: ContentRanker, TrendSurfer, QualityFilter, TopicCluster, CurationExplainer

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run locally
uvicorn community_curation.main:create_app --factory --reload

# Run tests
pytest

# Docker
docker compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/curate` | Full curation pipeline |
| POST | `/rank` | Rank content |
| POST | `/trends` | Surface trends |
| POST | `/filter` | Quality filter |
| POST | `/cluster` | Topic clustering |
| POST | `/explain` | Explain curation |
| GET | `/agents` | List agents |
| GET | `/metrics` | Service metrics |
