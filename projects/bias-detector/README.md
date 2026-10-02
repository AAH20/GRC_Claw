# Bias Detector

AI-powered bias detection for hiring decisions using agentic AI with demographic analysis, language bias detection, and fairness scoring.

## Features

- **Demographic Analyzer Agent** — Analyzes demographic representation and disparity metrics
- **Language Bias Detector Agent** — Detects biased language in job descriptions and feedback
- **Fairness Scorer Agent** — Computes fairness scores across multiple dimensions
- **Pattern Detector Agent** — Identifies patterns of bias across hiring decisions
- **Recommendation Agent** — Generates actionable recommendations for improvement

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn bias_detector.main:create_app --factory --reload

# Or with Docker
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/reports` | List all bias reports |
| POST | `/api/v1/reports` | Create a new bias report |
| GET | `/api/v1/reports/{report_id}` | Get a specific report |
| DELETE | `/api/v1/reports/{report_id}` | Delete a report |
| POST | `/api/v1/analyze/demographics` | Run demographic analysis |
| POST | `/api/v1/analyze/language` | Run language bias detection |
| POST | `/api/v1/analyze/fairness` | Run fairness scoring |
| POST | `/api/v1/analyze/patterns` | Run pattern detection |
| POST | `/api/v1/analyze/recommendations` | Get recommendations |
| POST | `/api/v1/analyze/full` | Run full analysis pipeline |
| GET | `/api/v1/metrics` | Prometheus metrics |
| GET | `/api/v1/config` | Current configuration |

## Architecture

```
src/bias_detector/
├── main.py              # FastAPI app factory
├── config/              # Settings and configuration
├── models/              # Pydantic schemas
├── agents/              # LangChain DeepAgents implementations
├── api/                 # FastAPI routes and dependencies
├── integrations/        # External service integrations
└── tests/               # Pytest test suite
```

## License

MIT
