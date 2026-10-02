# Influencer Marketing Platform

A standalone, modularized agentic AI platform for end-to-end influencer marketing campaign management. Built with LangChain DeepAgents, FastAPI, and modern Python.

## Architecture

The platform consists of 8 specialized agents orchestrated through a FastAPI application:

| Agent | Responsibility |
|-------|---------------|
| **Discovery** | Find and identify potential influencers across platforms |
| **Vetting** | Evaluate influencer quality, authenticity, and brand safety |
| **Outreach** | Manage initial contact and communication with influencers |
| **Negotiation** | Handle contract terms, pricing, and deliverable agreements |
| **Content** | Coordinate content creation, review, and approval workflows |
| **Performance** | Track campaign metrics, ROI, and engagement analytics |
| **Optimization** | Optimize campaign performance through data-driven adjustments |
| **Relationship Management** | Maintain long-term influencer relationships and retention |

## Project Structure

```
influencer-marketing/
├── src/influencer_marketing/
│   ├── agents/           # 8 specialized marketing agents
│   ├── api/              # FastAPI route handlers
│   ├── integrations/     # Social media platform connectors
│   ├── main.py           # Application entry point
│   └── __init__.py
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- API keys for supported social media platforms

### Local Development

```bash

# Clone and navigate to the project

cd influencer-marketing

# Create virtual environment

python -m venv .venv
source .venv/bin/activate

# Install dependencies

pip install -e ".[dev]"

# Copy and configure environment variables

cp .env.example .env

# Edit .env with your API keys

# Run the application

uvicorn influencer_marketing.main:app --reload --port 8000
```

### Docker

```bash

# Build and run with Docker Compose

docker-compose up --build
```

### Kubernetes

```bash

# Deploy to Kubernetes cluster

kubectl apply -f k8s/
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/influencers` | List influencers |
| POST | `/api/v1/influencers/discover` | Discover new influencers |
| GET | `/api/v1/campaigns` | List campaigns |
| POST | `/api/v1/campaigns` | Create new campaign |

## Configuration

All configuration is managed through environment variables. See `.env.example` for the full list of supported variables.

Key configuration areas:
- **LLM Settings**: Model selection, temperature, API keys
- **Platform Integrations**: Instagram, TikTok, YouTube API credentials
- **Agent Behavior**: Retry policies, timeouts, concurrency limits

## Testing

```bash

# Run all tests

pytest

# Run with coverage

pytest --cov=src/influencer_marketing --cov-report=html

# Run specific test file

pytest tests/test_agents.py -v
```

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) provides:
- Linting and type checking
- Unit and integration tests
- Docker image build and push
- Automated deployment to Kubernetes

## License

MIT
