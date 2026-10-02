# Fraud Detection

Agentic AI fraud detection system built with FastAPI and LangChain DeepAgents.

## Features

- **Pattern Detection** — Identifies known fraud patterns and signatures
- **Anomaly Detection** — Detects statistical outliers and behavioral anomalies
- **Risk Scoring** — Computes composite risk scores with explainable factors
- **Account Analysis** — Deep-dive account behavior profiling
- **Transaction Monitoring** — Real-time transaction stream monitoring

## Architecture

```
src/fraud_detection/
├── agents/          # LangChain DeepAgents implementations
├── api/             # FastAPI routes and dependencies
├── config/          # Settings and configuration
├── integrations/    # External service integrations
├── models/          # Pydantic schemas
└── tests/           # Pytest test suite
```

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn fraud_detection.main:create_app --factory --reload

# Or with Docker
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |
| POST | `//v1/analyze` | Analyze a transaction |
| POST | `//v1/analyze/batch` | Batch transaction analysis |
| GET | `/v1/reports/{report_id}` | Get fraud report |
| GET | `/v1/reports` | List fraud reports |
| POST | `//v1/patterns/detect` | Detect fraud patterns |
| POST | `//v1/anomalies/detect` | Detect anomalies |
| POST | `//v1/risk/score` | Score transaction risk |
| POST | `//v1/accounts/analyze` | Analyze account |
| POST | `//v1/monitor/start` | Start transaction monitoring |
| POST | `//v1/monitor/stop` | Stop transaction monitoring |
| GET | `/v1/agents/status` | Agent status overview |

## License

MIT
