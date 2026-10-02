# Marketing Attribution

Standalone modularized agentic AI marketing attribution platform. Collects data from ad platforms and analytics tools, runs multi-touch attribution models, generates predictive insights, and delivers real-time dashboards.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬───────────┬──────────┬────────────┤
│   Data   │Attribution│ Predictive│ Reporting│  Real-time │
│Collection│  Engine  │ Analytics │          │ Dashboards │
├──────────┴──────────┴───────────┴──────────┴────────────┤
│              LangChain DeepAgents + LangGraph             │
├─────────────────────────────────────────────────────────┤
│  Google Ads  │  Meta Ads  │  Google Analytics  │  Redis  │
└─────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Data Collection** | Fetches campaign, ad group, and conversion data from Google Ads, Meta Ads, and Google Analytics |
| **Attribution Engine** | Runs multi-touch attribution models (first-touch, last-touch, linear, time-decay, data-driven) |
| **Predictive Analytics** | Forecasts ROAS, CPA, and conversion volume using ML models |
| **Reporting** | Generates scheduled and on-demand attribution reports |
| **Real-time Dashboards** | Streams live metrics and attribution results to WebSocket clients |

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

# Edit .env with your credentials

# Run the server

uvicorn attribution.main:app --reload --port 8000
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
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/attribution/run` | Run attribution analysis |
| `GET` | `/api/v1/attribution/models` | List available attribution models |
| `POST` | `/api/v1/reports/generate` | Generate attribution report |
| `GET` | `/api/v1/reports/{report_id}` | Get report by ID |
| `GET` | `/api/v1/dashboards/stream` | WebSocket stream for real-time metrics |
| `POST` | `/api/v1/agents/data-collection/collect` | Trigger data collection |
| `POST` | `/api/v1/agents/predictive/forecast` | Run predictive forecast |

## Configuration

All configuration is managed via environment variables (see `.env.example`) and `config/config.yaml`.

## Testing

```bash
pytest tests/ -v --cov=src/attribution
```

## License

MIT
