# Community Governance

A production-grade FastAPI application for managing community governance using agentic AI. Features rule enforcement, dispute resolution, policy management, governance analytics, and explainable governance decisions powered by LangChain DeepAgents.

## Features

- **Rule Enforcement Agent** — Automatically detects and enforces community rules
- **Dispute Resolution Agent** — Mediates and resolves community disputes
- **Policy Management Agent** — Creates, updates, and manages governance policies
- **Governance Analytics Agent** — Provides insights and metrics on governance health
- **Governance Explainer Agent** — Explains governance decisions in human-readable terms

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run the application
uvicorn community_governance.main:create_app --factory --reload
```

### Docker

```bash
docker build -t community-governance .
docker run -p 8000:8000 community-governance
```

### Docker Compose

```bash
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/v1/rules` | Create a new rule |
| GET | `/api/v1/rules` | List all rules |
| GET | `/api/v1/rules/{rule_id}` | Get a specific rule |
| PUT | `/api/v1/rules/{rule_id}` | Update a rule |
| DELETE | `/api/v1/rules/{rule_id}` | Delete a rule |
| POST | `/api/v1/rules/enforce` | Enforce rules on an action |
| POST | `/api/v1/disputes` | Create a dispute |
| GET | `/api/v1/disputes` | List all disputes |
| GET | `/api/v1/disputes/{dispute_id}` | Get a specific dispute |
| POST | `/api/v1/disputes/{dispute_id}/resolve` | Resolve a dispute |
| POST | `/api/v1/policies` | Create a policy |
| GET | `/api/v1/policies` | List all policies |
| GET | `/api/v1/policies/{policy_id}` | Get a specific policy |
| PUT | `/api/v1/policies/{policy_id}` | Update a policy |
| DELETE | `/api/v1/policies/{policy_id}` | Delete a policy |
| GET | `/api/v1/analytics` | Get governance analytics |
| GET | `/api/v1/analytics/summary` | Get governance summary |
| POST | `/api/v1/explain` | Explain a governance decision |

## Project Structure

```
community-governance/
├── src/community_governance/
│   ├── agents/           # Agent implementations
│   ├── api/              # FastAPI routes and dependencies
│   ├── config/           # Configuration management
│   ├── integrations/     # External service integrations
│   ├── models/           # Pydantic models
│   ├── exceptions.py     # Custom exceptions
│   └── main.py           # Application entry point
├── tests/                # Test suite
├── k8s/                  # Kubernetes manifests
└── .github/workflows/    # CI/CD pipelines
```

## Testing

```bash
pytest
```

## License

MIT
