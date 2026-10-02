# Market Research

Standalone modularized agentic AI market research platform built with LangChain DeepAgents, FastAPI, and grc-marketing-core.

## Architecture

The platform consists of 5 specialized agents orchestrated through a FastAPI application:

| Agent | Responsibility |
|-------|---------------|
| **Data Collection** | Gathers market data from Statista, IBISWorld, SEMrush, and other sources |
| **Analysis** | Performs competitive analysis, trend detection, and market sizing |
| **Reporting** | Generates structured reports with visualizations and insights |
| **Action** | Recommends actionable strategies based on analysis results |
| **Performance Analytics** | Tracks KPIs, campaign performance, and ROI metrics |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- API keys for research platforms (see `.env.example`)

### Local Development

```bash
# Clone and navigate
cd market-research

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
uvicorn market_research.main:app --reload --port 8000
```

### Docker

```bash
docker-compose up --build
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/research` | Start a new market research task |
| `GET` | `/api/v1/research/{task_id}` | Get research task status |
| `GET` | `/api/v1/reports/{report_id}` | Retrieve a generated report |
| `POST` | `/api/v1/reports` | Generate a report from research data |
| `GET` | `/api/v1/analytics/performance` | Get performance analytics |

## Project Structure

```
market-research/
├── src/market_research/
│   ├── agents/           # 5 specialized AI agents
│   ├── api/              # FastAPI route handlers
│   ├── integrations/     # Third-party platform connectors
│   ├── main.py           # Application entry point
│   └── __init__.py
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:
- `OPENAI_API_KEY` — Required for LLM-powered agents
- `STATISTA_API_KEY` — Statista data access
- `IBISWORLD_API_KEY` — IBISWorld industry reports
- `SEMRUSH_API_KEY` — SEMrush SEO/SEM data
- `LOG_LEVEL` — Logging verbosity (default: INFO)
- `MAX_CONCURRENT_AGENTS` — Agent concurrency limit (default: 3)

## Testing

```bash
pytest tests/ -v --cov=src/market_research
```

## License

MIT
