# Healthcare Marketing

A HIPAA-compliant, modularized agentic AI marketing platform for healthcare organizations. Built with LangChain DeepAgents, grc-marketing-core, and FastAPI.

## Architecture

The platform consists of five specialized AI agents orchestrated through a FastAPI application:

| Agent | Responsibility |
|-------|---------------|
| **Content** | Generates healthcare marketing copy, blog posts, social media content, and email campaigns |
| **Compliance** | Validates all content against HIPAA regulations, healthcare advertising laws, and brand guidelines |
| **Campaigns** | Manages multi-channel campaign lifecycle, scheduling, and audience segmentation |
| **Analytics** | Tracks campaign performance, patient engagement metrics, and ROI analysis |
| **Reporting** | Produces compliance reports, performance dashboards, and executive summaries |

## Project Structure

```
healthcare-marketing/
├── src/healthcare_marketing/
│   ├── agents/           # AI agent implementations
│   │   ├── content.py
│   │   ├── compliance.py
│   │   ├── campaigns.py
│   │   ├── analytics.py
│   │   └── reporting.py
│   ├── api/              # FastAPI route handlers
│   │   ├── campaigns.py
│   │   └── content.py
│   ├── integrations/     # Third-party service connectors
│   │   ├── salesforce.py
│   │   ├── hubspot.py
│   │   └── mailchimp.py
│   ├── main.py           # FastAPI application entry point
│   └── __init__.py
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- Kubernetes cluster (for production deployment)

### Local Development

```bash
# Clone and navigate to the project
cd healthcare-marketing

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment configuration
cp config/.env.example .env
# Edit .env with your API keys and settings

# Run the application
uvicorn healthcare_marketing.main:app --reload --port 8000
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
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

## API Endpoints

### Content Generation
- `POST /api/v1/content/generate` — Generate marketing content
- `POST /api/v1/content/validate` — Validate content for compliance
- `GET /api/v1/content/{content_id}` — Retrieve generated content

### Campaign Management
- `POST /api/v1/campaigns` — Create a new campaign
- `GET /api/v1/campaigns` — List all campaigns
- `GET /api/v1/campaigns/{campaign_id}` — Get campaign details
- `PUT /api/v1/campaigns/{campaign_id}` — Update a campaign
- `DELETE /api/v1/campaigns/{campaign_id}` — Delete a campaign
- `POST /api/v1/campaigns/{campaign_id}/launch` — Launch a campaign
- `POST /api/v1/campaigns/{campaign_id}/pause` — Pause a campaign

### Health & Monitoring
- `GET /health` — Health check endpoint
- `GET /metrics` — Prometheus metrics

## HIPAA Compliance

This platform is designed with HIPAA compliance as a core principle:

- **PHI Encryption**: All PHI is encrypted at rest (AES-256) and in transit (TLS 1.3)
- **Access Controls**: Role-based access control (RBAC) with JWT authentication
- **Audit Logging**: Comprehensive audit trails for all data access and modifications
- **Data Minimization**: Only necessary data is collected and processed
- **BAA Support**: Business Associate Agreement (BAA) compatible architecture
- **Content Compliance**: Automated HIPAA content validation via the Compliance agent

## Configuration

All configuration is managed through environment variables. See `config/.env.example` for the full list of available settings.

Key configuration sections:
- `APP_*` — Application settings (host, port, debug mode)
- `LANGCHAIN_*` — LangChain/LangGraph configuration
- `SALESFORCE_*` — Salesforce integration credentials
- `HUBSPOT_*` — HubSpot integration credentials
- `MAILCHIMP_*` — Mailchimp integration credentials
- `ENCRYPTION_*` — Encryption key and settings
- `HIPAA_*` — HIPAA compliance settings

## CI/CD

The project includes a GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that:

1. Runs linting (ruff) and type checking (mypy)
2. Executes the test suite with coverage reporting
3. Builds and pushes Docker images to a container registry
4. Deploys to Kubernetes on main branch merges

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=healthcare_marketing --cov-report=html

# Run specific test file
pytest tests/test_agents.py -v
```

## License

Proprietary — All rights reserved.
