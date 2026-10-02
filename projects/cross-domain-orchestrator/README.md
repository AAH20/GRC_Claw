# Cross-Domain Orchestrator

A production-grade FastAPI service that orchestrates agents across multiple domains.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Health  │ Workflows│  Domains │  Agents  │  Analytics  │
│  Router  │  Router  │  Router  │  Router  │   Router    │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│                    Agent Layer                           │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Domain  │ Workflow │  Result  │  Error   │  Analytics  │
│  Router  │Orchestr. │Aggregator│ Handler  │  Collector  │
│  Agent   │  Agent   │  Agent   │  Agent   │   Agent     │
└──────────┴──────────┴──────────┴──────────┴─────────────┘
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload

# Run with Docker
docker-compose up --build

# Run tests
pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness probe |
| POST | `/api/v1/workflows` | Create workflow |
| GET | `/api/v1/workflows` | List workflows |
| GET | `/api/v1/workflows/{id}` | Get workflow |
| POST | `/api/v1/workflows/{id}/execute` | Execute workflow |
| DELETE | `/api/v1/workflows/{id}` | Delete workflow |
| POST | `/api/v1/domains/route` | Route domain request |
| GET | `/api/v1/domains` | List domains |
| GET | `/api/v1/agents` | List agents |
| GET | `/api/v1/agents/{name}/status` | Agent status |
| POST | `/api/v1/analytics/collect` | Collect analytics |
| GET | `/api/v1/analytics/summary` | Analytics summary |
| GET | `/api/v1/analytics/cross-domain` | Cross-domain analytics |

## Agents

- **DomainRouterAgent**: Routes incoming requests to the appropriate domain
- **WorkflowOrchestratorAgent**: Manages workflow execution and step coordination
- **ResultAggregatorAgent**: Aggregates results from multiple workflow steps
- **ErrorHandlerAgent**: Handles and recovers from errors during execution
- **AnalyticsCollectorAgent**: Collects and reports cross-domain analytics

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Runtime environment |
| `DEBUG` | `true` | Debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
