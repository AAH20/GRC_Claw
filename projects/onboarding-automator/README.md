# Onboarding Automator

Agentic AI-powered employee onboarding automation service built with FastAPI and LangChain DeepAgents.

## Features

- **Task Generation**: Automatically generates personalized onboarding tasks based on role, department, and location
- **Document Collection**: Manages document submission, verification, and storage workflows
- **Progress Tracking**: Real-time progress monitoring with risk assessment and reporting
- **Compliance Checking**: Automated regulatory and policy compliance validation
- **Welcome Messages**: Personalized welcome communications across multiple channels

## Architecture

```
src/onboarding_automator/
├── agents/           # LangChain DeepAgents implementations
│   ├── __init__.py   # TaskGeneratorAgent, DocumentCollectorAgent, etc.
├── api/              # FastAPI route handlers
│   ├── routes/       # Endpoint modules
│   └── router.py     # API router aggregation
├── config/           # Application settings
├── integrations/     # External service integrations
├── models/           # Pydantic schemas
└── tests/            # pytest test suite
```

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the server
onboarding-automator
# or
uvicorn onboarding_automator.main:app --reload
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Kubernetes

```bash
# Deploy to K8s cluster
kubectl apply -f k8s/
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/ready` | Readiness probe |
| GET | `/api/v1/live` | Liveness probe |
| POST | `/api/v1/plans` | Create onboarding plan |
| GET | `/api/v1/plans` | List all plans |
| GET | `/api/v1/plans/{id}` | Get plan by ID |
| PATCH | `/api/v1/plans/{id}` | Update plan |
| DELETE | `/api/v1/plans/{id}` | Delete plan |
| POST | `/api/v1/plans/{id}/generate-tasks` | Generate tasks via agent |
| POST | `/api/v1/tasks` | Create task |
| GET | `/api/v1/tasks` | List tasks |
| GET | `/api/v1/tasks/{id}` | Get task by ID |
| PATCH | `/api/v1/tasks/{id}` | Update task |
| DELETE | `/api/v1/tasks/{id}` | Delete task |
| POST | `/api/v1/documents` | Register document |
| GET | `/api/v1/documents` | List documents |
| GET | `/api/v1/documents/{id}` | Get document by ID |
| PATCH | `/api/v1/documents/{id}` | Update document |
| DELETE | `/api/v1/documents/{id}` | Delete document |
| POST | `/api/v1/documents/{id}/verify` | Verify document |
| GET | `/api/v1/progress/{plan_id}` | Get progress |
| POST | `/api/v1/progress/{plan_id}` | Create progress record |
| PATCH | `/api/v1/progress/{plan_id}` | Update progress |
| POST | `/api/v1/progress/{plan_id}/recalculate` | Recalculate via agent |
| GET | `/api/v1/progress/{plan_id}/report` | Generate report |
| POST | `/api/v1/compliance` | Create compliance check |
| GET | `/api/v1/compliance` | List compliance checks |
| GET | `/api/v1/compliance/{id}` | Get check by ID |
| PATCH | `/api/v1/compliance/{id}` | Update check |
| DELETE | `/api/v1/compliance/{id}` | Delete check |
| POST | `/api/v1/compliance/{plan_id}/run-all` | Run all checks |
| POST | `/api/v1/welcome/generate` | Generate welcome message |
| POST | `/api/v1/welcome/send` | Send welcome message |
| GET | `/api/v1/welcome/{plan_id}` | List welcome messages |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=onboarding_automator --cov-report=term-missing
```

## CI/CD

The project includes a GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that:
1. Runs linting (Ruff) and type checking (MyPy)
2. Executes the test suite with coverage reporting
3. Builds and pushes Docker images to GHCR
4. Deploys to Kubernetes on main branch merges

## License

MIT
