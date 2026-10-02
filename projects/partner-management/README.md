# Partner Management

A modularized agentic AI system for managing partner relationships, deals, communications, analytics, enablement, and compliance.

## Architecture

The system is built on **LangChain DeepAgents** and **grc-marketing-core**, exposing a FastAPI REST API with six specialized agents:

| Agent | Responsibility |
|-------|---------------|
| **Onboarding** | Partner registration, qualification, and activation workflows |
| **Deal Management** | Deal registration, tracking, forecasting, and approval |
| **Communication** | Multi-channel partner communications and notifications |
| **Analytics** | Partner performance metrics, reporting, and insights |
| **Enablement** | Training, certification, and resource management |
| **Compliance** | Policy enforcement, audit trails, and regulatory checks |

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Run the application
uvicorn partner_management.main:app --reload --port 8000
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
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/v1/partners` | Create a partner |
| GET | `/api/v1/partners` | List partners |
| GET | `/api/v1/partners/{id}` | Get partner by ID |
| PUT | `/api/v1/partners/{id}` | Update partner |
| DELETE | `/api/v1/partners/{id}` | Delete partner |
| POST | `/api/v1/deals` | Create a deal |
| GET | `/api/v1/deals` | List deals |
| GET | `/api/v1/deals/{id}` | Get deal by ID |
| PUT | `/api/v1/deals/{id}` | Update deal |
| DELETE | `/api/v1/deals/{id}` | Delete deal |

## Integrations

- **Salesforce** — CRM sync for partners and deals
- **HubSpot** — Marketing automation and lifecycle management
- **Impartner** — PRM platform integration

## Project Structure

```
partner-management/
├── src/partner_management/
│   ├── agents/           # Six specialized agents
│   ├── api/              # FastAPI route handlers
│   ├── integrations/     # External system connectors
│   ├── config.py         # Application configuration
│   └── main.py           # FastAPI application entry point
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## License

MIT
