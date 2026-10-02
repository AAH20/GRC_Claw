# SEO Optimizer

AI-powered SEO optimization platform built with a multi-agent architecture. Leverages LangChain DeepAgents to provide intelligent keyword research, content optimization, technical SEO auditing, link building recommendations, SEO monitoring, and performance analytics.

## Features

- **Keyword Research Agent** — Discovers high-value keywords using SEMrush and Ahrefs data
- **Content Optimization Agent** — Analyzes and optimizes content for target keywords
- **Technical SEO Agent** — Audits site health, crawlability, and performance issues
- **Link Building Agent** — Identifies backlink opportunities and manages outreach
- **SEO Monitoring Agent** — Tracks rankings, alerts on anomalies, and monitors competitors
- **Performance Analytics Agent** — Aggregates SEO metrics and generates actionable insights

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI Application                │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│ Keyword  │ Content  │ Technical│ Link     │ SEO     │
│ Research │ Optimize │ SEO      │ Building │ Monitor │
├──────────┴──────────┴──────────┴──────────┴─────────┤
│              Performance Analytics                   │
├─────────────────────────────────────────────────────┤
│  Google Search Console │ SEMrush │ Ahrefs │ Screaming Frog │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- API keys for Google Search Console, SEMrush, and Ahrefs

### Local Development

```bash
# Clone and navigate to the project
cd seo-optimizer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp config/.env.example .env
# Edit .env with your API keys

# Run the application
uvicorn seo_optimizer.main:app --reload --port 8000
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
| GET | `/health` | Health check |
| POST | `/api/v1/keywords/research` | Run keyword research |
| GET | `/api/v1/keywords/{task_id}` | Get keyword research results |
| POST | `/api/v1/content/optimize` | Optimize content |
| GET | `/api/v1/content/{task_id}` | Get content optimization results |
| GET | `/api/v1/monitoring/rankings` | Get ranking data |
| GET | `/api/v1/analytics/dashboard` | Get analytics dashboard |

## Configuration

All configuration is managed via environment variables. See `config/.env.example` for the full list.

Key settings:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | Yes |
| `GOOGLE_SEARCH_CONSOLE_CREDENTIALS` | GSC service account JSON | No |
| `SEMRUSH_API_KEY` | SEMrush API key | No |
| `AHREFS_API_KEY` | Ahrefs API key | No |
| `LOG_LEVEL` | Logging level (default: INFO) | No |
| `MAX_CONCURRENT_AGENTS` | Max parallel agents (default: 3) | No |

## Testing

```bash
pytest tests/ -v --cov=src/seo_optimizer
```

## CI/CD

The project includes a GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that:

1. Runs linting and type checking
2. Executes the test suite with coverage
3. Builds and pushes Docker image to GHCR
4. Deploys to Kubernetes on main branch merges

## Project Structure

```
seo-optimizer/
├── .github/workflows/ci-cd.yml
├── config/
│   ├── config.yaml
│   └── .env.example
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── src/seo_optimizer/
│   ├── __init__.py
│   ├── main.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── keyword_research.py
│   │   ├── content_optimization.py
│   │   ├── technical_seo.py
│   │   ├── link_building.py
│   │   ├── seo_monitoring.py
│   │   └── performance_analytics.py
│   ├── api/
│   │   ├── keywords.py
│   │   └── content.py
│   └── integrations/
│       ├── google_search_console.py
│       ├── semrush.py
│       └── ahrefs.py
├── tests/
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_integrations.py
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## License

MIT
