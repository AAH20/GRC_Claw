# Sales Forecaster

AI-powered sales forecasting platform using a multi-agent pipeline architecture. Collects data from CRM/ERP systems, analyzes trends, generates predictions, recommends actions, and tracks performance.

## Architecture

```

┌─────────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────────────┐
│  Data Collection │────▶│  Analysis    │────▶│  Prediction  │────▶│  Action      │────▶│  Performance       │
│  Agent           │     │  Agent       │     │  Agent       │     │  Agent       │     │  Analytics Agent   │
└─────────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └────────────────────┘
        │                       │                     │                     │                       │
        ▼                       ▼                     ▼                     ▼                       ▼
   Salesforce              Trend Analysis        Prophet/ML           Recommendations        KPI Tracking
   HubSpot                 Seasonality           Ensemble Models      Alerts                 Model Drift
   SAP                     Anomaly Detection     Confidence Intervals  Playbooks              Retraining Triggers

```

## Quick Start

### Local Development

```bash

# Clone and setup

git clone <repo-url>
cd sales-forecaster
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure

cp .env.example .env

# Edit .env with your credentials

# Run

uvicorn sales_forecaster.main:app --reload --port 8000

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
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/v1/forecasts` | Generate sales forecast |
| GET | `/api/v1/forecasts/{forecast_id}` | Get forecast by ID |
| GET | `/api/v1/forecasts` | List forecasts |
| POST | `/api/v1/pipeline/run` | Run full pipeline |
| GET | `/api/v1/pipeline/status/{run_id}` | Pipeline run status |
| GET | `/api/v1/analytics/performance` | Performance metrics |
| GET | `/api/v1/analytics/kpis` | KPI dashboard data |

## Configuration

All configuration is via environment variables or `config/config.yaml`. See `.env.example` for all available options.

## Project Structure

```

sales-forecaster/
├── src/sales_forecaster/
│   ├── agents/           # 5 AI agents
│   ├── api/              # FastAPI routes
│   ├── integrations/     # CRM/ERP connectors
│   ├── core/             # Shared utilities
│   └── main.py           # Application entry point
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
└── .github/workflows/    # CI/CD pipeline

```

## License

MIT
