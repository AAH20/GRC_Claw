# Product Recommendations

Standalone modularized agentic AI product recommendations engine for e-commerce platforms.

## Architecture

The system is composed of six specialized agents orchestrated via LangChain DeepAgents:

| Agent | Responsibility |
|-------|---------------|
| **Data Collection** | Fetches product catalogs, customer behavior, and order history from integrated platforms |
| **Analysis** | Performs customer segmentation, trend detection, and purchase pattern analysis |
| **Recommendation** | Generates personalized product recommendations using collaborative + content-based filtering |
| **Cross-Sell** | Identifies complementary product opportunities and bundle suggestions |
| **Optimization** | A/B tests recommendation strategies and optimizes ranking algorithms |
| **Performance Analytics** | Tracks KPIs, generates reports, and provides actionable insights |

## Integrations

- **Shopify** — REST Admin API
- **WooCommerce** — REST API v3
- **Magento** — REST API

## Quick Start

### Local Development

```bash

# Create virtual environment

python -m venv .venv
source .venv/bin/activate

# Install dependencies

pip install -e ".[dev]"

# Copy and configure environment

cp .env.example .env

# Edit .env with your credentials

# Run the application

uvicorn product_recommendations.main:app --reload --port 8000

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
| `GET` | `/api/v1/products` | List products |
| `GET` | `/api/v1/products/{id}` | Get product by ID |
| `POST` | `/api/v1/recommendations` | Get personalized recommendations |
| `POST` | `/api/v1/recommendations/cross-sell` | Get cross-sell suggestions |
| `GET` | `/api/v1/analytics/performance` | Get performance metrics |

## Configuration

All configuration is managed via environment variables (see `.env.example`) and `config/config.yaml`.

## Testing

```bash

pytest --cov=product_recommendations --cov-report=term-missing

```

## CI/CD

GitHub Actions workflow at `.github/workflows/ci-cd.yml` handles:

- Linting and type checking
- Unit and integration tests with coverage
- Docker image build and push
- Kubernetes deployment

## License

MIT
