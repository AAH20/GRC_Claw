# Rights Management Service

Agentic AI content rights management with license detection, usage tracking, and infringement detection.

## Quickstart

```bash
pip install -e ".[dev]"
uvicorn rights_management.main:app --reload
```

## API

- `POST /api/v1/licenses` — create a license
- `GET /api/v1/licenses` — list licenses
- `POST /api/v1/licenses/detect` — detect license for content
- `POST /api/v1/usage/record` — record content usage
- `GET /api/v1/usage/summary/{content_id}` — usage statistics
- `POST /api/v1/infringement/report` — file infringement report
- `POST /api/v1/infringement/detect` — automated infringement detection
- `POST /api/v1/validation` — validate usage against license
- `POST /api/v1/takedown/request` — submit takedown request
- `POST /api/v1/takedown/{id}/process` — process takedown request

## Architecture

- **Agents** — LangChain DeepAgents-based agents for license detection, usage tracking, infringement detection, rights validation, and takedown processing.
- **API** — FastAPI routers with Pydantic models.
- **Storage** — Pluggable in-memory backend (swap for persistent storage in production).
- **Integrations** — Notification service for event dispatch.

## Deployment

```bash
docker-compose up --build
# or
kubectl apply -f k8s/
```
