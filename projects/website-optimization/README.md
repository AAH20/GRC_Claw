# Website Optimization

A modularized agentic AI platform for website optimization. Five specialized agents — A/B Testing, Personalization, SEO, Performance, and Analytics — work together to continuously improve website metrics.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI Application                │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│ A/B Test │ Personal │   SEO    │ Perform  │Analytics│
│  Agent   │  Agent   │  Agent   │  Agent   │  Agent  │
├──────────┴──────────┴──────────┴──────────┴─────────┤
│              Integration Layer                        │
│  Google Analytics │ Hotjar │ Optimizely             │
└─────────────────────────────────────────────────────┘
```

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

# Run the application
uvicorn website_optimization.main:app --reload --port 8000
```

### Docker

```bash
docker build -t website-optimization .
docker run -p 8000:8000 --env-file .env website-optimization
```

### Docker Compose

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
| POST | `/api/v1/experiments` | Create A/B test experiment |
| GET | `/api/v1/experiments/{id}` | Get experiment status |
| POST | `/api/v1/experiments/{id}/variant` | Assign variant to user |
| GET | `/api/v1/pages/{url}/recommendations` | Get page optimization recommendations |
| POST | `/api/v1/pages/{url}/personalize` | Get personalized content |
| GET | `/api/v1/pages/{url}/seo-audit` | Run SEO audit |
| GET | `/api/v1/pages/{url}/performance` | Get performance metrics |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:
- `APP_ENV`: Environment (development, staging, production)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `GA_MEASUREMENT_ID`: Google Analytics 4 Measurement ID
- `HOTJAR_SITE_ID`: Hotjar Site ID
- `OPTIMIZELY_SDK_KEY`: Optimizely SDK Key

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) runs on every push to `main`:

1. Lint and type-check
2. Run tests with coverage
3. Build Docker image
4. Push to container registry
5. Deploy to Kubernetes

## Project Structure

```
website-optimization/
├── .github/workflows/ci-cd.yml
├── config/
│   ├── config.yaml
│   └── .env.example
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── src/website_optimization/
│   ├── agents/
│   │   ├── ab_testing.py
│   │   ├── analytics.py
│   │   ├── performance.py
│   │   ├── personalization.py
│   │   └── seo.py
│   ├── api/
│   │   ├── experiments.py
│   │   └── pages.py
│   ├── integrations/
│   │   ├── google_analytics.py
│   │   ├── hotjar.py
│   │   └── optimizely.py
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_integrations.py
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## License

MIT
