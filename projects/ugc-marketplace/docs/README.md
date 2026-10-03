# UGC Marketplace

Unified agentic AI platform for content marketplace operations. Consolidates 10 separate UGC marketplace projects into a single, standalone, modularized Python project.

## Features

- **Content Moderation** — Text, image, and video moderation with policy enforcement and appeal handling
- **Creator Monetization** — Revenue analytics, payout management, and subscription tracking
- **Content Discovery** — Semantic search, personalized recommendations, and trend detection
- **Rights Management** — Copyright infringement detection, license management, and takedown processing
- **Quality Scoring** — Readability, originality, engagement, and SEO scoring
- **Fraud Detection** — Anomaly detection, pattern matching, and risk scoring
- **Creator Analytics** — Audience analysis, content performance, and growth prediction
- **Licensing Engine** — License generation, negotiation, and compliance tracking
- **Community Curation** — Content ranking, quality filtering, and topic clustering
- **Content Marketplace** — Listing management, pricing optimization, and transaction processing

## Quick Start

### Docker (Recommended)

```bash
docker-compose up -d
```

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Start infrastructure
docker-compose up -d postgres redis

# Run the application
uvicorn ugc_marketplace.main:app --reload
```

### Kubernetes

```bash
kubectl apply -k k8s/overlays/development/
```

## Documentation

| Document | Description |
|----------|-------------|
| [API Reference](api-reference.md) | Complete API documentation with examples |
| [Architecture](architecture.md) | System architecture and design |
| [User Guide](user-guide.md) | User guide for all features |
| [Deployment Guide](deployment-guide.md) | Deployment instructions |
| [Development Guide](development-guide.md) | Development setup and workflow |

## API Endpoints

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI:** http://localhost:8000/openapi.json

## Project Structure

```
ugc-marketplace/
├── src/ugc_marketplace/       # Main application
│   ├── api/                   # API route handlers
│   ├── agents/                # AI agent implementations
│   ├── config/                # Configuration
│   ├── integrations/          # External service integrations
│   ├── models/                # Data models
│   └── tests/                 # Test suite
├── frontend/                  # Next.js frontend
├── docker/                    # Docker configuration
├── k8s/                       # Kubernetes manifests
├── monitoring/                # Monitoring configuration
├── database/                  # Database migrations
├── terraform/                 # Infrastructure as Code
├── pyproject.toml             # Python project config
├── Dockerfile                 # Container build
└── docker-compose.yml         # Local development
```

## Technology Stack

- **Backend:** FastAPI, Pydantic, SQLAlchemy, Redis, Kafka
- **Frontend:** Next.js, React, Tailwind CSS
- **AI/LLM:** LangChain, OpenAI, DeepAgents
- **Infrastructure:** Docker, Kubernetes, Prometheus
- **CI/CD:** GitHub Actions

## Configuration

All settings are configurable via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment (development/production) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka brokers |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `SECRET_KEY` | `change-me-in-production` | Application secret |

## Testing

```bash
pytest --cov=src/ugc_marketplace --cov-report=term-missing
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT
