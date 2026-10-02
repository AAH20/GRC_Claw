# Feedback Management

A standalone, modularized agentic AI feedback management system built with LangChain DeepAgents and grc-marketing-core. Collects, analyzes, and responds to customer feedback across multiple survey and review platforms.

## Architecture

The system consists of 5 specialized agents:

| Agent | Responsibility |
|-------|---------------|
| **Collection** | Gathers feedback from SurveyMonkey, Typeform, Google Forms, and review platforms |
| **Analysis** | Performs sentiment analysis, topic extraction, and trend detection |
| **Response** | Generates personalized response drafts using LLM |
| **Action** | Triggers workflows (tickets, escalations, follow-ups) based on analysis |
| **Performance Analytics** | Tracks KPIs, generates reports, and provides insights |

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional)
- API keys for survey platforms (see `.env.example`)

### Local Development

```bash

# Clone and navigate

cd feedback-management

# Create virtual environment

python -m venv .venv
source .venv/bin/activate

# Install dependencies

pip install -e ".[dev]"

# Configure environment

cp .env.example .env

# Edit .env with your API keys

# Run the application

uvicorn feedback_management.main:app --reload --port 8000
```

### Docker

```bash

# Build and run with Docker Compose

docker-compose up --build

# Or build the image directly

docker build -t feedback-management:latest .
docker run -p 8000:8000 --env-file .env feedback-management:latest
```

### Kubernetes

```bash

# Apply manifests

kubectl apply -f k8s/

# Check status

kubectl get pods -l app=feedback-management
kubectl get svc feedback-management
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/feedback/collect` | Collect feedback from all sources |
| `GET` | `/api/v1/feedback` | List collected feedback |
| `POST` | `/api/v1/feedback/analyze` | Analyze feedback batch |
| `POST` | `/api/v1/feedback/respond` | Generate response drafts |
| `POST` | `/api/v1/feedback/action` | Trigger action workflows |
| `GET` | `/api/v1/analytics/performance` | Get performance metrics |
| `GET` | `/api/v1/surveys` | List available surveys |
| `POST` | `/api/v1/surveys/sync` | Sync survey responses |

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) provides:

1. **CI Pipeline**: Linting, type checking, and testing on every push/PR
2. **CD Pipeline**: Docker image build and push to registry on main branch
3. **Deployment**: Automated Kubernetes deployment

## Project Structure

```
feedback-management/
├── src/feedback_management/
│   ├── agents/           # 5 specialized agents
│   ├── api/              # FastAPI route handlers
│   ├── integrations/     # Survey platform connectors
│   ├── config/           # Configuration management
│   └── main.py           # Application entry point
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:

- `APP_ENV`: Environment (development/staging/production)
- `LOG_LEVEL`: Logging verbosity
- `SURVEYMONKEY_API_KEY`: SurveyMonkey API token
- `TYPEFORM_API_KEY`: Typeform API token
- `GOOGLE_FORMS_CREDENTIALS`: Path to Google service account JSON
- `OPENAI_API_KEY`: LLM API key for analysis and response generation

## License

MIT
