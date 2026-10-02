# Real Estate Marketing Platform

AI-powered real estate marketing automation platform built with LangChain DeepAgents and FastAPI.

## Features

- **Listings Agent** — Automated property listing creation, optimization, and syndication
- **Lead Nurture Agent** — AI-driven lead scoring, segmentation, and personalized follow-up
- **Virtual Tours Agent** — Automated virtual tour generation and management
- **Analytics Agent** — Marketing performance tracking, attribution, and insights
- **Reporting Agent** — Automated report generation and distribution

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI Application                │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│ Listings │Lead Nurture│Virtual  │Analytics │Reporting│
│  Agent   │  Agent    │Tours    │  Agent   │  Agent  │
├──────────┴──────────┴──────────┴──────────┴─────────┤
│              Integration Layer                        │
├──────────┬──────────┬──────────┬─────────────────────┤
│  Zillow  │ Realtor  │Salesforce│  Other Platforms    │
└──────────┴──────────┴──────────┴─────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional)
- API keys for Zillow, Realtor.com, and Salesforce

### Local Development

```bash
# Clone and navigate to the project
cd real-estate-marketing

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys

# Run the application
uvicorn real_estate_marketing.main:app --reload --port 8000
```

## Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run the Dockerfile directly
docker build -t real-estate-marketing .
docker run -p 8000:8000 --env-file .env real-estate-marketing
```

## Kubernetes

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI documentation |
| POST | `/api/v1/properties` | Create a property listing |
| GET | `/api/v1/properties` | List all properties |
| GET | `/api/v1/properties/{id}` | Get property by ID |
| PUT | `/api/v1/properties/{id}` | Update property |
| DELETE | `/api/v1/properties/{id}` | Delete property |
| POST | `/api/v1/leads` | Create a lead |
| GET | `/api/v1/leads` | List all leads |
| GET | `/api/v1/leads/{id}` | Get lead by ID |
| POST | `/api/v1/leads/{id}/nurture` | Trigger lead nurture workflow |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

### Key Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `APP_ENV` | Environment (dev/staging/prod) | Yes |
| `OPENAI_API_KEY` | OpenAI API key for LLM operations | Yes |
| `ZILLOW_API_KEY` | Zillow API key | No |
| `REALTOR_API_KEY` | Realtor.com API key | No |
| `SALESFORCE_USERNAME` | Salesforce username | No |
| `SALESFORCE_PASSWORD` | Salesforce password | No |
| `SALESFORCE_SECURITY_TOKEN` | Salesforce security token | No |
| `DATABASE_URL` | Database connection string | Yes |
| `REDIS_URL` | Redis connection string | No |

## Project Structure

```
real-estate-marketing/
├── src/real_estate_marketing/
│   ├── agents/           # AI agent implementations
│   │   ├── listings.py
│   │   ├── lead_nurture.py
│   │   ├── virtual_tours.py
│   │   ├── analytics.py
│   │   └── reporting.py
│   ├── api/              # FastAPI route handlers
│   │   ├── properties.py
│   │   └── leads.py
│   ├── integrations/     # Third-party platform integrations
│   │   ├── zillow.py
│   │   ├── realtor.py
│   │   └── salesforce.py
│   ├── config.py         # Application configuration
│   ├── models.py         # Pydantic data models
│   └── main.py           # FastAPI application entry point
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=real_estate_marketing --cov-report=html

# Run specific test file
pytest tests/test_agents.py -v
```

## CI/CD

The project includes a GitHub Actions workflow that:
1. Runs linting and type checking
2. Executes the test suite
3. Builds and pushes Docker image
4. Deploys to Kubernetes (on main branch)

## License

MIT
