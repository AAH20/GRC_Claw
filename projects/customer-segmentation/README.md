# Customer Segmentation Platform

AI-powered customer segmentation platform built with a multi-agent architecture. Uses LangChain DeepAgents to orchestrate intelligent customer data collection, analysis, segmentation, strategy formulation, and performance tracking.

## Architecture

```

┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                        │
├─────────────────────────────────────────────────────────────┤
│  API Layer          │  Agent Orchestration Layer              │
│  ├─ /segments       │  ├─ DataCollectorAgent                 │
│  ├─ /customers      │  ├─ AnalystAgent                       │
│  └─ /health         │  ├─ SegmentBuilderAgent                │
│                     │  ├─ StrategistAgent                    │
│                     │  ├─ ReviewerAgent                      │
│                     │  └─ PerformanceAnalyticsAgent          │
├─────────────────────────────────────────────────────────────┤
│  Integration Layer                                            │
│  ├─ Salesforce CRM  ├─ HubSpot CRM  ├─ Google Analytics      │
└─────────────────────────────────────────────────────────────┘

```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **DataCollector** | Gathers customer data from CRM and analytics platforms |
| **Analyst** | Performs RFM analysis, behavioral clustering, and trend detection |
| **SegmentBuilder** | Creates dynamic customer segments using ML clustering |
| **Strategist** | Generates marketing strategies and campaign recommendations per segment |
| **Reviewer** | Validates segment quality, checks for bias, ensures business rules compliance |
| **PerformanceAnalytics** | Tracks segment KPIs, conversion rates, and ROI metrics |

## Quick Start

### Local Development

```bash

# Create virtual environment

python -m venv .venv
source .venv/bin/activate

# Install dependencies

pip install -e ".[dev]"

# Copy environment configuration

cp .env.example .env

# Edit .env with your API keys

# Run the application

uvicorn customer_segmentation.main:app --reload --port 8000

```

## Docker

```bash

# Build and run with Docker Compose

docker-compose up --build

# Access the application
# API: http://localhost:8000
# Docs: http://localhost:8000/docs

```

## Kubernetes

```bash

# Deploy to Kubernetes cluster

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/segments` | List all customer segments |
| POST | `/segments` | Create a new segment |
| GET | `/segments/{segment_id}` | Get segment details |
| PUT | `/segments/{segment_id}` | Update a segment |
| DELETE | `/segments/{segment_id}` | Delete a segment |
| GET | `/customers` | List customers with optional segment filter |
| GET | `/customers/{customer_id}` | Get customer profile |
| POST | `/customers/enrich` | Enrich customer data from integrations |
| POST | `/segments/{segment_id}/analyze` | Run full analysis pipeline on a segment |
| GET | `/segments/{segment_id}/performance` | Get segment performance metrics |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for LLM-powered agents |
| `SALESFORCE_USERNAME` | Salesforce CRM username |
| `SALESFORCE_PASSWORD` | Salesforce CRM password |
| `SALESFORCE_SECURITY_TOKEN` | Salesforce security token |
| `HUBSPOT_API_KEY` | HubSpot API key |
| `GOOGLE_ANALYTICS_PROPERTY_ID` | GA4 property ID |

## Project Structure

```

customer-segmentation/
├── src/customer_segmentation/
│   ├── agents/               # AI agent implementations
│   │   ├── data_collector.py
│   │   ├── analyst.py
│   │   ├── segment_builder.py
│   │   ├── strategist.py
│   │   ├── reviewer.py
│   │   └── performance_analytics.py
│   ├── api/                  # FastAPI route handlers
│   │   ├── segments.py
│   │   └── customers.py
│   ├── integrations/         # External platform connectors
│   │   ├── salesforce.py
│   │   ├── hubspot.py
│   │   └── google_analytics.py
│   ├── config.py             # Application configuration
│   ├── models.py             # Pydantic data models
│   └── main.py               # FastAPI application entry point
├── tests/                    # Test suite
├── config/                   # Configuration files
├── k8s/                      # Kubernetes manifests
├── .github/workflows/        # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml

```

## Testing

```bash

# Run all tests

pytest

# Run with coverage

pytest --cov=customer_segmentation --cov-report=html

# Run specific test file

pytest tests/test_agents.py -v

```

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) automates:

1. **Lint & Type Check** — Ruff + mypy
2. **Test** — pytest with coverage reporting
3. **Build** — Docker image build and push to registry
4. **Deploy** — Kubernetes deployment on main branch merges

## License

MIT
