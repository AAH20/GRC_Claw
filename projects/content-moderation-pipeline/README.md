# Content Moderation Pipeline

Agentic AI content moderation pipeline with multi-modal analysis, policy enforcement, and appeal handling.

## Architecture

- **FastAPI** application with `create_app()` factory pattern
- **LangChain DeepAgents** for agent implementations
- **5 specialized agents**: Text, Image, Video, Policy Enforcement, Appeal Handler
- **Multi-modal analysis**: text, image, and video content moderation
- **Policy engine**: configurable rules with severity levels
- **Appeal system**: automated appeal review and escalation

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn content_moderation.main:create_app --factory --reload

# Docker
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/v1/moderate/text` | Moderate text content |
| POST | `/api/v1/moderate/image` | Moderate image content |
| POST | `/api/v1/moderate/video` | Moderate video content |
| POST | `/api/v1/moderate/batch` | Batch moderation |
| GET | `/api/v1/policies` | List policies |
| POST | `/api/v1/policies` | Create policy |
| GET | `/api/v1/policies/{id}` | Get policy |
| PUT | `/api/v1/policies/{id}` | Update policy |
| DELETE | `/api/v1/policies/{id}` | Delete policy |
| POST | `/api/v1/appeals` | Submit appeal |
| GET | `/api/v1/appeals/{id}` | Get appeal status |
| POST | `/api/v1/appeals/{id}/review` | Review appeal |

## Project Structure

```
src/content_moderation/
├── agents/           # LangChain agent implementations
├── api/              # FastAPI routes and dependencies
├── config/           # Settings and configuration
├── integrations/     # External service integrations
├── models/           # Pydantic schemas
└── tests/            # pytest test suite
```
