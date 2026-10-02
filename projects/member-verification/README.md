# Member Verification Service

AI-powered community member verification service built with FastAPI and LangChain DeepAgents.

## Features

- **Identity Verification** — Verify member identity using multiple data points
- **Trust Scoring** — Calculate trust scores based on behavior and history
- **Fraud Prevention** — Detect and prevent fraudulent verification attempts
- **Document Checking** — Validate uploaded identity documents
- **Verification Explanation** — Explain verification decisions transparently

## Architecture

```
src/member_verification/
├── agents/           # LangChain DeepAgents implementations
├── api/              # FastAPI routes and dependencies
├── config/           # Application configuration
├── integrations/     # External service integrations
├── models/           # Pydantic schemas
└── main.py           # Application entry point
```

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn member_verification.main:create_app --factory --reload
```

## Docker

```bash
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |
| POST | `/verify` | Submit verification request |
| GET | `/verify/{request_id}` | Get verification result |
| POST | `/verify/batch` | Batch verification |
| GET | `/agents` | List available agents |
| GET | `/agents/{name}/status` | Agent status |
| POST | `/trust-score` | Calculate trust score |
| GET | `/trust-score/{member_id}` | Get trust score |
| POST | `/fraud-check` | Run fraud check |
| GET | `/fraud-report/{member_id}` | Get fraud report |
| POST | `/documents/verify` | Verify documents |
| GET | `/explanation/{request_id}` | Get explanation |
| GET | `/metrics` | Prometheus metrics |

## License

MIT
