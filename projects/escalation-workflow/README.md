# Escalation Workflow Service

Agentic AI-powered escalation workflow management system with priority routing, SLA tracking, and resolution optimization.

## Features

- **Priority Router Agent**: AI-powered priority assessment and routing
- **SLA Tracker Agent**: Real-time SLA monitoring and breach detection
- **Resolution Optimizer Agent**: AI-optimized resolution strategies
- **Escalation Analyzer Agent**: Pattern detection and trend analysis
- **Auto Resolver Agent**: Automated resolution for eligible escalations

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn escalation_workflow.main:app --reload
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Kubernetes

```bash
# Deploy to Kubernetes cluster
kubectl apply -k k8s/
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |
| POST | `/escalations` | Create escalation |
| GET | `/escalations` | List escalations |
| GET | `/escalations/{id}` | Get escalation |
| PATCH | `/escalations/{id}` | Update escalation |
| DELETE | `/escalations/{id}` | Delete escalation |
| POST | `/escalations/{id}/route` | Route escalation |
| POST | `/escalations/{id}/analyze` | Analyze escalation |
| POST | `/escalations/{id}/auto-resolve` | Auto-resolve escalation |
| POST | `/escalations/bulk` | Bulk create escalations |
| GET | `/priorities` | List priorities |
| GET | `/priorities/{level}` | Get priority config |
| POST | `/priorities/assess` | Assess priority |
| POST | `/sla/track` | Track SLA |
| GET | `/sla` | List SLAs |
| GET | `/sla/{id}` | Get SLA |
| POST | `/sla/{id}/check` | Check SLA status |
| POST | `/sla/{id}/breach` | Record breach |
| POST | `/resolutions` | Create resolution |
| GET | `/resolutions` | List resolutions |
| GET | `/resolutions/{id}` | Get resolution |
| POST | `/resolutions/{id}/optimize` | Optimize resolution |
| POST | `/resolutions/{id}/approve` | Approve resolution |
| POST | `/resolutions/{id}/verify` | Verify resolution |

## Architecture

```
src/escalation_workflow/
├── agents/           # AI agent implementations
│   ├── base.py
│   ├── priority_router.py
│   ├── sla_tracker.py
│   ├── resolution_optimizer.py
│   ├── escalation_analyzer.py
│   └── auto_resolver.py
├── api/              # FastAPI route handlers
│   ├── health.py
│   ├── escalations.py
│   ├── priorities.py
│   ├── sla.py
│   └── resolutions.py
├── config/           # Application configuration
│   └── settings.py
├── integrations/     # External service integrations
│   ├── notifications.py
│   ├── slack.py
│   └── pagerduty.py
├── models/           # Pydantic data models
│   ├── escalation.py
│   ├── priority.py
│   ├── sla.py
│   ├── resolution.py
│   └── analysis.py
├── tests/            # Test suite
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_api.py
│   └── test_agents.py
└── main.py           # Application entry point
```

## License

MIT
