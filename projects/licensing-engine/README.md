# Licensing Engine

Agentic AI content licensing engine for GRC_Claw. Built with FastAPI, LangChain DeepAgents, and production-grade Python.

## Features

- **License Generation**: AI-powered license agreement generation
- **Terms Negotiation**: Automated negotiation between parties
- **Compliance Tracking**: Real-time compliance monitoring and reporting
- **Royalty Calculation**: Tier-based royalty computation
- **Contract Analysis**: AI-driven contract clause extraction and risk assessment

## Architecture

```
src/licensing_engine/
├── agents/          # LangChain DeepAgents implementations
│   ├── base.py      # Base agent class + all 5 agents
│   └── __init__.py
├── api/             # FastAPI routes
│   ├── routes/      # Endpoint modules (6 route files)
│   ├── router.py    # API router aggregation
│   └── __init__.py
├── config/          # Settings and configuration
│   ├── settings.py  # Pydantic Settings
│   └── __init__.py
├── integrations/    # External service clients
│   └── __init__.py  # LLM, Database, Cache clients
├── tests/           # Pytest test suite
│   ├── conftest.py
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_models.py
├── models.py        # Pydantic models
├── main.py          # FastAPI app factory
└── __init__.py
```

## Quick Start

### Local Development

```bash
cd ~/GRC_Claw/projects/licensing-engine
pip install -e ".[dev]"
uvicorn licensing_engine.main:app --reload
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
| GET | `/ready` | Readiness check |
| GET | `/live` | Liveness check |
| POST | `/licenses` | Create license |
| GET | `/licenses` | List licenses |
| GET | `/licenses/{id}` | Get license |
| PATCH | `/licenses/{id}` | Update license |
| DELETE | `/licenses/{id}` | Delete license |
| POST | `/licenses/{id}/activate` | Activate license |
| POST | `/licenses/{id}/revoke` | Revoke license |
| POST | `/negotiations` | Start negotiation |
| GET | `/negotiations/{id}` | Get negotiation |
| POST | `/negotiations/{id}/counter` | Submit counter proposal |
| POST | `/negotiations/{id}/accept` | Accept proposal |
| POST | `/negotiations/{id}/reject` | Reject proposal |
| POST | `/compliance/check` | Run compliance check |
| GET | `/compliance` | List compliance reports |
| GET | `/compliance/{id}` | Get compliance report |
| GET | `/compliance/license/{id}` | Get license compliance |
| POST | `/royalties/calculate` | Calculate royalties |
| GET | `/royalties/{id}` | Get calculation |
| GET | `/royalties/license/{id}` | Get license calculations |
| POST | `/contracts/analyze` | Analyze contract |
| GET | `/contracts/{id}` | Get analysis |

## Agents

1. **LicenseGeneratorAgent**: Generates license agreements from content metadata
2. **TermsNegotiatorAgent**: Negotiates terms between licensor and licensee
3. **ComplianceTrackerAgent**: Monitors and reports compliance status
4. **RoyaltyCalculatorAgent**: Computes royalty payments with tier support
5. **ContractAnalyzerAgent**: Analyzes contracts for clauses and risks

## Testing

```bash
pytest --cov=licensing_engine --cov-report=term
```

## CI/CD

GitHub Actions workflow at `.github/workflows/ci-cd.yml`:
- Lint (Ruff + MyPy)
- Test (pytest with coverage)
- Build (Docker image)
- Deploy (Kubernetes)
