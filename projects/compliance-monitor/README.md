# Compliance Monitor

Agentic AI compliance monitoring system with policy tracking, violation detection, audit reporting, compliance scoring, and automated remediation.

## Architecture

- **FastAPI** application with `src/` layout
- **LangChain DeepAgents** for agent implementations
- **Pydantic v2** models for request/response validation
- **Docker** + **Kubernetes** deployment ready
- **GitHub Actions** CI/CD pipeline

## Agents

| Agent | Purpose |
|-------|---------|
| `PolicyTrackerAgent` | Tracks policy changes, versions, and effective dates |
| `ViolationDetectorAgent` | Detects compliance violations from events and logs |
| `AuditReporterAgent` | Generates audit reports with findings and evidence |
| `ComplianceScorerAgent` | Computes compliance scores per policy/domain |
| `RemediationAgent` | Recommends and executes remediation actions |

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run
uvicorn compliance_monitor.main:create_app --factory --reload

# Test
pytest

# Docker
docker compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/policies` | List policies |
| POST | `/api/v1/policies` | Create policy |
| GET | `/api/v1/policies/{id}` | Get policy |
| DELETE | `/api/v1/policies/{id}` | Delete policy |
| GET | `/api/v1/violations` | List violations |
| POST | `/api/v1/violations` | Report violation |
| GET | `/api/v1/violations/{id}` | Get violation |
| GET | `/api/v1/audits` | List audit reports |
| POST | `/api/v1/audits` | Generate audit report |
| GET | `/api/v1/audits/{id}` | Get audit report |
| GET | `/api/v1/scores` | List compliance scores |
| POST | `/api/v1/scores` | Compute compliance score |
| GET | `/api/v1/scores/{id}` | Get compliance score |
| POST | `/api/v1/remediate/{violation_id}` | Remediate violation |
| GET | `/api/v1/reports/compliance` | Full compliance report |

## Project Structure

```
src/compliance_monitor/
├── agents/          # LangChain DeepAgents
├── api/             # FastAPI routes & dependencies
├── config/          # Settings
├── integrations/    # Slack, email, storage
├── models/          # Pydantic schemas
└── tests/           # pytest suite
```
