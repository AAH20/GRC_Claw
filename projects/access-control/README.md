# Access Control Service

Agentic AI-powered access control service built with FastAPI and LangChain DeepAgents.

## Features

- **Permission Evaluation** — AI-driven permission assessment with contextual reasoning
- **Role Management** — Dynamic role creation, assignment, and lifecycle management
- **Access Auditing** — Comprehensive audit trail with anomaly detection
- **Policy Enforcement** — Real-time policy evaluation and enforcement
- **Access Recommendations** — ML-powered access recommendations

## Architecture

```
src/access_control/
├── agents/          # LangChain DeepAgents implementations
├── api/             # FastAPI routes and dependencies
├── config/          # Application configuration
├── integrations/    # LangChain and vector store integrations
├── models/          # Pydantic schemas
└── tests/           # Pytest test suite
```

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start development server
uvicorn access_control.main:create_app --factory --reload

# Docker
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/access/evaluate` | Evaluate access request |
| POST | `/api/v1/access/check` | Quick access check |
| GET | `/api/v1/roles` | List all roles |
| POST | `/api/v1/roles` | Create a new role |
| GET | `/api/v1/roles/{role_id}` | Get role details |
| PUT | `/api/v1/roles/{role_id}` | Update a role |
| DELETE | `/api/v1/roles/{role_id}` | Delete a role |
| GET | `/api/v1/audit` | List audit logs |
| POST | `/api/v1/audit` | Create audit entry |
| GET | `/api/v1/audit/{audit_id}` | Get audit details |
| POST | `/api/v1/policies/enforce` | Enforce a policy |
| GET | `/api/v1/recommendations` | Get access recommendations |
| POST | `/api/v1/recommendations` | Generate recommendations |

## License

MIT
