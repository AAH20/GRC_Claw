# Tier Management Service

Multi-tier gated community access management with agentic AI.

## Features

- **Tier Evaluation**: AI-powered evaluation of members against tier requirements
- **Upgrade Recommendations**: Intelligent tier upgrade suggestions
- **Access Control**: Policy-based access control for gated resources
- **Benefit Management**: Lifecycle management of tier benefits
- **Analytics**: Tier performance analytics and insights

## Architecture

- **Framework**: FastAPI with async support
- **AI**: LangChain DeepAgents for agent implementations
- **Python**: 3.11+ with full type hints
- **Testing**: pytest with async support

## Project Structure

```
src/tier_management/
├── agents/           # LangChain DeepAgents implementations
│   ├── access_controller.py
│   ├── benefit_manager.py
│   ├── tier_analytics.py
│   ├── tier_evaluator.py
│   └── upgrade_recommender.py
├── api/              # FastAPI routes
│   └── routes/
│       ├── access.py
│       ├── analytics.py
│       ├── benefits.py
│       ├── evaluation.py
│       ├── health.py
│       ├── tiers.py
│       └── upgrades.py
├── config/           # Application configuration
│   ├── logging_config.py
│   └── settings.py
├── integrations/     # External service clients
│   ├── cache.py
│   ├── database.py
│   └── llm.py
├── models/           # Pydantic schemas
│   └── schemas.py
├── exceptions.py     # Custom exceptions
└── main.py          # Application entry point
```

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn tier_management.main:app --reload
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /api/v1/tiers | List tiers |
| POST | /api/v1/tiers | Create tier |
| GET | /api/v1/tiers/{id} | Get tier |
| PUT | /api/v1/tiers/{id} | Update tier |
| DELETE | /api/v1/tiers/{id} | Delete tier |
| POST | /api/v1/evaluations | Create evaluation |
| GET | /api/v1/evaluations/{id} | Get evaluation |
| GET | /api/v1/evaluations/member/{id} | Member evaluations |
| POST | /api/v1/upgrades | Create upgrade request |
| GET | /api/v1/upgrades/{id} | Get upgrade request |
| POST | /api/v1/access/check | Check access |
| POST | /api/v1/access/policies | Create policy |
| POST | /api/v1/benefits | Create benefit |
| GET | /api/v1/benefits | List benefits |
| POST | /api/v1/analytics | Generate analytics |

## License

MIT
