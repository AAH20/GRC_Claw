# Cross-Project Orchestrator

Unified orchestration layer for multi-project agentic AI marketing systems. Provides centralized project discovery, dependency resolution, resource allocation, health monitoring, and cost optimization across all marketing AI projects.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Cross-Project Orchestrator              │
├─────────────┬─────────────┬─────────────┬───────────────┤
│  Project    │ Dependency  │  Resource   │    Health     │
│  Discovery  │ Resolution  │ Allocation  │  Monitoring   │
├─────────────┴─────────────┴─────────────┴───────────────┤
│              Cost Optimization Agent                     │
├─────────────────────────────────────────────────────────┤
│              FastAPI REST API Layer                       │
├─────────────────────────────────────────────────────────┤
│  Kubernetes  │  Terraform   │  Prometheus  │  Custom    │
└─────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Project Discovery** | Discovers and catalogs all AI marketing projects across the organization |
| **Dependency Resolution** | Maps inter-project dependencies and resolves version conflicts |
| **Resource Allocation** | Optimizes compute, storage, and API quota distribution |
| **Health Monitoring** | Tracks project health metrics, uptime, and SLA compliance |
| **Cost Optimization** | Analyzes spend patterns and recommends cost-saving measures |

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment configuration
cp .env.example .env

# Run the application
uvicorn cross_project_orchestrator.main:app --reload --port 8080
```

## Docker

```bash
docker build -t cross-project-orchestrator .
docker run -p 8080:8080 --env-file .env cross-project-orchestrator
```

### Docker Compose

```bash
docker-compose up -d
```

### Kubernetes

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/v1/projects` | List all projects |
| POST | `/api/v1/projects` | Register a new project |
| GET | `/api/v1/projects/{id}` | Get project details |
| GET | `/api/v1/dependencies` | List all dependencies |
| POST | `/api/v1/dependencies/resolve` | Resolve dependency graph |
| GET | `/api/v1/agents/{agent_id}/status` | Get agent status |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCHESTRATOR_ENV` | `development` | Runtime environment |
| `ORCHESTRATOR_PORT` | `8080` | API server port |
| `ORCHESTRATOR_LOG_LEVEL` | `INFO` | Logging level |
| `KUBERNETES_NAMESPACE` | `default` | K8s namespace |
| `PROMETHEUS_URL` | `http://localhost:9090` | Prometheus endpoint |
| `TERRAFORM_STATE_PATH` | `./tfstate` | Terraform state directory |

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) provides:

1. **Lint & Type Check** — Ruff + mypy
2. **Test** — pytest with coverage
3. **Build** — Docker image build and push
4. **Deploy** — Kubernetes deployment (staging/production)

## Project Structure

```
cross-project-orchestrator/
├── src/cross_project_orchestrator/
│   ├── agents/           # Agent implementations
│   ├── api/              # FastAPI route handlers
│   ├── integrations/     # External system integrations
│   ├── config.py         # Pydantic settings
│   └── main.py           # Application entry point
├── tests/                # Test suite
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipeline
├── config/               # Configuration files
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## License

MIT
