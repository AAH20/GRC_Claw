# Pricing Optimizer

AI-powered pricing optimization for e-commerce platforms. Uses a multi-agent architecture to analyze market conditions, recommend optimal prices, run A/B tests, implement changes, and monitor performance.

## Architecture

```

┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Market  │ Pricing  │ Testing  │   Impl   │  Monitoring │
│   Intel  │  Engine  │  Agent   │  Agent   │    Agent    │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│              Integration Layer                            │
│         Shopify  │  WooCommerce  │  Stripe               │
└─────────────────────────────────────────────────────────┘

```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Market Intelligence** | Gathers competitor pricing, demand signals, and market trends |
| **Pricing Engine** | Computes optimal prices using elasticity models and constraints |
| **Testing** | Designs and runs A/B tests on pricing strategies |
| **Implementation** | Pushes approved price changes to e-commerce platforms |
| **Monitoring** | Tracks KPIs, detects anomalies, triggers re-optimization |

## Quick Start

### Local Development

```bash

# Create virtual environment

python -m venv .venv
source .venv/bin/activate

# Install dependencies

pip install -e ".[dev]"

# Copy environment template

cp config/.env.example .env

# Run the application

uvicorn pricing_optimizer.main:app --reload --port 8000

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
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/api/v1/products` | List products |
| `GET` | `/api/v1/products/{id}` | Get product details |
| `POST` | `/api/v1/pricing/optimize` | Run pricing optimization |
| `GET` | `/api/v1/pricing/recommendations` | Get current recommendations |
| `POST` | `/api/v1/pricing/apply` | Apply recommended prices |

## Configuration

See `config/config.yaml` for application settings and `config/.env.example` for environment variables.

## Testing

```bash

pytest tests/ -v --cov=pricing_optimizer

```

## CI/CD

GitHub Actions workflow at `.github/workflows/ci-cd.yml` runs linting, type checking, tests, and builds Docker image on every push.

## License

MIT
