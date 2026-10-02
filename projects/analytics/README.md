# Analytics & Attribution

A standalone, modularized agentic AI marketing analytics and attribution platform. It collects data from multiple sources (Google Analytics, Mixpanel, Amplitude), runs multi-touch attribution models, generates predictive forecasts, produces reports, and streams real-time dashboards.

## Architecture

```

┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬───────────┬──────────┬────────────┤
│  Data    │Attribution│ Predictive│ Reporting│ Real-time  │
│Collection│  Engine  │ Analytics │          │ Dashboards │
├──────────┴──────────┴───────────┴──────────┴────────────┤
│              Integration Layer                            │
│  ┌──────────────┬──────────────┬──────────────┐         │
│  │   Google     │   Mixpanel   │   Amplitude  │         │
│  │  Analytics   │              │              │         │
│  └──────────────┴──────────────┴──────────────┘         │
└─────────────────────────────────────────────────────────┘

```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Data Collection** | Fetches raw event and campaign data from GA, Mixpanel, Amplitude |
| **Attribution Engine** | Runs first-touch, last-touch, linear, time-decay, and data-driven attribution models |
| **Predictive Analytics** | Forecasts revenue, churn, and LTV using scikit-learn models |
| **Reporting** | Generates scheduled and on-demand marketing performance reports |
| **Real-time Dashboards** | Streams live metrics via WebSocket for dashboard consumption |

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

# Edit .env with your API keys

# Run the application

uvicorn analytics.main:app --reload --port 8000

```

## Docker

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
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/attribution/run` | Run attribution analysis |
| `GET` | `/api/v1/attribution/models` | List available attribution models |
| `POST` | `/api/v1/forecasting/revenue` | Generate revenue forecast |
| `POST` | `/api/v1/forecasting/churn` | Generate churn prediction |
| `GET` | `/api/v1/reports/{report_id}` | Retrieve a generated report |
| `POST` | `/api/v1/reports/generate` | Trigger report generation |
| `WS` | `/ws/dashboards` | Real-time dashboard WebSocket |

## Configuration

All configuration is managed via `config/config.yaml` and environment variables (see `.env.example`).

## Testing

```bash

pytest tests/ -v --cov=analytics --cov-report=term-missing

```

## CI/CD

GitHub Actions workflow at `.github/workflows/ci-cd.yml` runs linting, type checks, tests, builds the Docker image, and deploys to Kubernetes on pushes to `main`.

## License

MIT
