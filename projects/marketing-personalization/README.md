# Marketing Personalization Platform

AI-powered marketing personalization platform built with LangChain DeepAgents, featuring a multi-agent architecture for intelligent campaign management, audience segmentation, and performance optimization.

## Architecture

The platform uses 7 specialized agents orchestrated by a central orchestrator:

| Agent | Responsibility |
|-------|---------------|
| **Data Collection** | Gathers customer data from CRM and marketing platforms |
| **Analysis** | Analyzes customer behavior, trends, and patterns |
| **Personalization** | Generates personalized content and recommendations |
| **Optimization** | A/B testing, campaign optimization, and budget allocation |
| **Governance** | Compliance, data privacy, and approval workflows |
| **Performance Analytics** | Metrics tracking, reporting, and ROI analysis |
| **Orchestrator** | Coordinates agent workflows and manages state |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- Redis (for caching and state management)

### Local Development

```bash

# Clone and navigate to the project

cd marketing-personalization

# Create virtual environment

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies

pip install -e ".[dev]"

# Copy environment configuration

cp .env.example .env

# Edit .env with your API keys and configuration

# Run the server

uvicorn personalization.main:app --reload --port 8000
```

### Docker

```bash

# Build and run with Docker Compose

docker-compose up --build

# Or run the Dockerfile directly

docker build -t marketing-personalization .
docker run -p 8000:8000 --env-file .env marketing-personalization
```

### Kubernetes

```bash

# Deploy to Kubernetes

kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/v1/campaigns` | Create a new campaign |
| GET | `/api/v1/campaigns` | List all campaigns |
| GET | `/api/v1/campaigns/{id}` | Get campaign details |
| PUT | `/api/v1/campaigns/{id}` | Update a campaign |
| DELETE | `/api/v1/campaigns/{id}` | Delete a campaign |
| POST | `/api/v1/segments` | Create a customer segment |
| GET | `/api/v1/segments` | List all segments |
| GET | `/api/v1/segments/{id}` | Get segment details |
| POST | `/api/v1/orchestrate` | Run agent orchestration workflow |

## Integrations

- **Salesforce**: CRM data sync, lead management
- **HubSpot**: Marketing automation, contact management
- **Mailchimp**: Email campaigns, audience management

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:
- `APP_ENV`: Environment (development, staging, production)
- `REDIS_URL`: Redis connection string
- `SALESFORCE_*`: Salesforce API credentials
- `HUBSPOT_API_KEY`: HubSpot API key
- `MAILCHIMP_API_KEY`: Mailchimp API key

## Testing

```bash

# Run all tests

pytest

# Run with coverage

pytest --cov=src/personalization --cov-report=html

# Run specific test file

pytest tests/test_agents.py
```

## CI/CD

The project includes a GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that:
1. Runs linting and type checking
2. Executes the test suite with coverage
3. Builds and pushes Docker image
4. Deploys to Kubernetes (production only)

## Project Structure

```
marketing-personalization/
├── src/personalization/
│   ├── agents/           # Agent implementations
│   ├── api/              # FastAPI route handlers
│   ├── integrations/     # Third-party platform integrations
│   ├── main.py           # Application entry point
│   └── __init__.py
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## License

MIT
