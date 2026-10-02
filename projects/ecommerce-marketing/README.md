# E-commerce Marketing Platform

AI-powered e-commerce marketing automation platform built with LangChain DeepAgents and grc-marketing-core.

## Features

- **Product Recommendations** — Personalized product suggestions using collaborative filtering and LLM-based ranking
- **Cart Abandonment Recovery** — Automated recovery workflows for abandoned carts
- **Email Marketing** — AI-generated email campaigns with A/B testing
- **Social Media** — Automated social media post generation and scheduling
- **Analytics** — Real-time campaign performance tracking and reporting

## Architecture

```
src/ecommerce_marketing/
├── agents/           # AI agent implementations
│   ├── product_recommendations.py
│   ├── cart_abandonment.py
│   ├── email.py
│   ├── social.py
│   └── analytics.py
├── api/              # FastAPI route handlers
│   ├── campaigns.py
│   └── products.py
├── integrations/     # E-commerce platform connectors
│   ├── shopify.py
│   ├── woocommerce.py
│   └── stripe.py
├── main.py           # FastAPI application entry point
└── config/           # Configuration management
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)
- API keys for OpenAI and your e-commerce platform

### Local Development

```bash
# Clone and navigate to the project
cd ecommerce-marketing

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp config/.env.example .env
# Edit .env with your API keys

# Run the application
uvicorn ecommerce_marketing.main:app --reload --port 8000
```

## Docker

```bash
docker build -t ecommerce-marketing .
docker run -p 8000:8000 --env-file .env ecommerce-marketing
```

### Docker Compose

```bash
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/v1/recommendations` | Get product recommendations |
| POST | `/api/v1/cart-abandonment` | Trigger cart abandonment recovery |
| POST | `/api/v1/email-campaign` | Create email campaign |
| POST | `/api/v1/social-post` | Generate social media post |
| GET | `/api/v1/analytics/campaign/{id}` | Get campaign analytics |
| GET | `/api/v1/products` | List products |
| POST | `/api/v1/campaigns` | Create campaign |

## Configuration

All configuration is managed via environment variables. See `config/.env.example` for the full list.

Key settings:

- `OPENAI_API_KEY` — OpenAI API key for LLM features
- `SHOPIFY_API_KEY` / `SHOPIFY_API_SECRET` — Shopify credentials
- `WOOCOMMERCE_API_KEY` / `WOOCOMMERCE_API_SECRET` — WooCommerce credentials
- `STRIPE_SECRET_KEY` — Stripe API key
- `LOG_LEVEL` — Logging level (default: INFO)
- `ENVIRONMENT` — Runtime environment (development/staging/production)

## Testing

```bash
pytest tests/ -v --cov=src/ecommerce_marketing
```

## CI/CD

The project includes a GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that:

1. Runs linting and type checking
2. Executes the test suite with coverage
3. Builds and pushes Docker image to GHCR
4. Deploys to Kubernetes on main branch merges

## Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## License

MIT
