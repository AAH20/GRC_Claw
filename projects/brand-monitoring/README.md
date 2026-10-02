# Brand Monitoring

AI-powered brand monitoring platform with a multi-agent architecture. Monitors social media, news, and online platforms for brand mentions, analyzes sentiment, generates responses, and produces actionable reports.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ Listening │ Analysis │ Response │ Reporting│  Performance │
│  Agent    │  Agent   │  Agent   │  Agent   │  Analytics   │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│              LangChain DeepAgents + LangGraph             │
├─────────────────────────────────────────────────────────┤
│  Twitter  │  Reddit  │  NewsAPI  │  PostgreSQL  │ Redis  │
└─────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Listening** | Collects brand mentions from Twitter, Reddit, and NewsAPI |
| **Analysis** | Performs sentiment analysis, topic extraction, and trend detection |
| **Response** | Generates response suggestions for negative mentions |
| **Reporting** | Compiles periodic reports with insights and recommendations |
| **Performance Analytics** | Tracks KPIs, agent performance, and ROI metrics |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- API keys for Twitter, Reddit, and NewsAPI

### Local Development

```bash
# Clone and navigate
cd brand-monitoring

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp config/.env.example .env
# Edit .env with your API keys

# Run the application
uvicorn brand_monitoring.main:app --reload --port 8000
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
| `GET` | `/metrics` | Prometheus metrics |
| `POST` | `/api/v1/mentions` | Submit a brand mention |
| `GET` | `/api/v1/mentions` | List mentions with filters |
| `GET` | `/api/v1/mentions/{id}` | Get mention by ID |
| `POST` | `/api/v1/reports` | Generate a report |
| `GET` | `/api/v1/reports` | List reports |
| `GET` | `/api/v1/reports/{id}` | Get report by ID |
| `POST` | `/api/v1/agents/{agent}/trigger` | Trigger an agent |

## Configuration

All configuration is managed via environment variables. See `config/.env.example` for the full list.

Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (dev/staging/prod) | `dev` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `OPENAI_API_KEY` | OpenAI API key for LLM calls | — |
| `TWITTER_BEARER_TOKEN` | Twitter API bearer token | — |
| `REDDIT_CLIENT_ID` | Reddit API client ID | — |
| `REDDIT_CLIENT_SECRET` | Reddit API client secret | — |
| `NEWSAPI_KEY` | NewsAPI key | — |
| `DATABASE_URL` | PostgreSQL connection string | — |
| `REDIS_URL` | Redis connection string | — |

## Testing

```bash
pytest
```

## CI/CD

The GitHub Actions workflow at `.github/workflows/ci-cd.yml` runs on every push to `main`:

1. Lint (ruff) and type-check (mypy)
2. Run tests with coverage
3. Build and push Docker image
4. Deploy to Kubernetes

## Project Structure

```
brand-monitoring/
├── .github/workflows/ci-cd.yml
├── config/
│   ├── config.yaml
│   └── .env.example
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── src/brand_monitoring/
│   ├── __init__.py
│   ├── main.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── listening.py
│   │   ├── analysis.py
│   │   ├── response.py
│   │   ├── reporting.py
│   │   └── performance_analytics.py
│   ├── api/
│   │   ├── mentions.py
│   │   └── reports.py
│   └── integrations/
│       ├── twitter.py
│       ├── reddit.py
│       └── newsapi.py
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
