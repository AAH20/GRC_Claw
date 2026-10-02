# Moderation Queue

AI-powered moderation queue management system with priority scoring, auto-moderation, and human review routing.

## Features

- **Priority Scoring**: AI-driven priority assessment for moderation items
- **Auto-Moderation**: Automated content moderation with configurable rules
- **Human Review Routing**: Intelligent routing of items to human reviewers
- **Queue Optimization**: Dynamic queue balancing and workload distribution
- **Escalation Management**: Automated escalation for high-priority or complex cases

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Application                    │
├─────────────────────────────────────────────────────────────┤
│  API Layer  │  Agents Layer  │  Integrations  │  Config     │
├─────────────────────────────────────────────────────────────┤
│  Routes     │  Priority      │  LangChain     │  Settings   │
│  Models     │  AutoMod       │  Notifications │  Logging    │
│  Dependencies│  HumanReview │  Redis         │  Metrics    │
│             │  QueueOpt      │  Database      │             │
│             │  Escalation    │                │             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run the application
uvicorn moderation_queue.main:app --reload
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run tests
docker-compose run api pytest
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -l app=moderation-queue
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/v1/items` | Create moderation item |
| GET | `/api/v1/items` | List moderation items |
| GET | `/api/v1/items/{item_id}` | Get item by ID |
| PATCH | `/api/v1/items/{item_id}` | Update item |
| DELETE | `/api/v1/items/{item_id}` | Delete item |
| POST | `/api/v1/queues` | Create queue |
| GET | `/api/v1/queues` | List queues |
| GET | `/api/v1/queues/{queue_id}` | Get queue by ID |
| POST | `/api/v1/agents/score` | Score item priority |
| POST | `/api/v1/agents/auto-moderate` | Auto-moderate item |
| POST | `/api/v1/agents/route` | Route to human review |
| POST | `/api/v1/agents/optimize` | Optimize queue |
| POST | `/api/v1/agents/escalate` | Escalate item |

## Configuration

Configuration is managed via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `DATABASE_URL` | `sqlite:///./moderation.db` | Database connection URL |
| `OPENAI_API_KEY` | - | OpenAI API key for LangChain |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENVIRONMENT` | `development` | Environment name |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=moderation_queue --cov-report=html

# Run specific test file
pytest src/moderation_queue/tests/test_agents.py
```

## Project Structure

```
moderation-queue/
├── src/moderation_queue/
│   ├── agents/           # AI agent implementations
│   ├── api/              # FastAPI routes and dependencies
│   ├── config/           # Configuration management
│   ├── integrations/     # External service integrations
│   ├── models/           # Pydantic data models
│   └── tests/            # Test suite
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## License

MIT
