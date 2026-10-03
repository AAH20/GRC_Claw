# UGC Marketplace Development Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setting Up the Development Environment](#setting-up-the-development-environment)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Adding a New Agent](#adding-a-new-agent)
6. [Adding a New API Endpoint](#adding-a-new-api-endpoint)
7. [Testing](#testing)
8. [Code Style and Linting](#code-style-and-linting)
9. [Debugging](#debugging)
10. [Common Tasks](#common-tasks)

---

## Prerequisites

### Required Software

| Software | Version | Installation |
|----------|---------|-------------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) |
| Docker | 24.0+ | [docker.com](https://www.docker.com/) |
| Git | 2.40+ | [git-scm.com](https://git-scm.com/) |

### Recommended Tools

- **IDE:** VS Code with Python and TypeScript extensions
- **API Testing:** Postman or Insomnia
- **Database Client:** DBeaver or TablePlus
- **Container Tools:** Docker Desktop

---

## Setting Up the Development Environment

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ugc-marketplace.git
cd ugc-marketplace
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 4. Set Up Environment Variables

```bash
cp docker/.env.example .env
```

Edit `.env` with your local development values:

```env
APP_ENV=development
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ugc_marketplace
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-not-for-production
OPENAI_API_KEY=sk-your-openai-key
```

### 5. Start Infrastructure Services

```bash
docker-compose up -d postgres redis
```

### 6. Run Database Migrations

```bash
alembic upgrade head
```

### 7. Start the Development Server

```bash
uvicorn ugc_marketplace.main:app --reload
```

The API will be available at http://localhost:8000

### 8. Start the Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

---

## Project Structure

```
ugc-marketplace/
├── src/ugc_marketplace/
│   ├── api/                    # API route handlers (FastAPI routers)
│   │   ├── health.py           # Health check endpoints
│   │   ├── content_moderation/ # Content moderation routes
│   │   ├── creator_monetization/ # Creator monetization routes
│   │   ├── content_discovery/  # Content discovery routes
│   │   ├── rights_management/  # Rights management routes
│   │   ├── quality_scoring/    # Quality scoring routes
│   │   ├── fraud_detection/    # Fraud detection routes
│   │   ├── creator_analytics/  # Creator analytics routes
│   │   ├── licensing_engine/   # Licensing engine routes
│   │   ├── community_curation/ # Community curation routes
│   │   └── content_marketplace/ # Content marketplace routes
│   ├── agents/                 # AI agent implementations
│   │   ├── content_moderation/ # Text, image, video moderation agents
│   │   ├── creator_monetization/ # Revenue, payout, subscription agents
│   │   ├── content_discovery/  # Search, recommendation, trend agents
│   │   ├── rights_management/  # License, infringement, takedown agents
│   │   ├── quality_scoring/    # Readability, originality, SEO agents
│   │   ├── fraud_detection/    # Anomaly, pattern, risk agents
│   │   ├── creator_analytics/  # Audience, growth, revenue agents
│   │   ├── licensing_engine/   # License generation, negotiation agents
│   │   ├── community_curation/ # Ranking, filtering, clustering agents
│   │   └── content_marketplace/ # Listing, pricing, transaction agents
│   ├── config/                 # Application configuration
│   │   ├── __init__.py         # Settings class (Pydantic BaseSettings)
│   │   └── logging_config.py   # Structured logging configuration
│   ├── integrations/           # External service integrations
│   │   ├── content_moderation/ # Storage backends, webhooks
│   │   ├── creator_monetization/ # Stripe, PayPal, Patreon
│   │   ├── creator_analytics/  # YouTube, Twitter, Instagram, TikTok
│   │   ├── content_marketplace/ # Cache, notifications, payments
│   │   ├── fraud_detection/    # Database, Kafka, Redis
│   │   ├── quality_scoring/    # Cache, API clients
│   │   ├── rights_management/  # Storage, notifications
│   │   └── community_curation/ # Content fetcher
│   ├── models/                 # Pydantic data models
│   │   └── schemas.py          # Shared request/response schemas
│   ├── tests/                  # Test suite
│   │   ├── conftest.py         # Pytest fixtures
│   │   ├── test_agents/        # Agent unit tests
│   │   ├── test_api/           # API endpoint tests
│   │   ├── test_config/        # Configuration tests
│   │   └── test_integrations/  # Integration tests
│   ├── __init__.py             # Package initialization
│   └── main.py                 # Application entry point
├── frontend/                   # Next.js frontend application
│   ├── src/                    # Frontend source code
│   ├── package.json            # Node.js dependencies
│   └── next.config.js          # Next.js configuration
├── docker/                     # Docker configuration
│   ├── docker-compose.yml      # Local development compose
│   ├── docker-compose.prod.yml # Production overrides
│   ├── nginx.conf              # Nginx reverse proxy config
│   └── .env.example            # Environment variable template
├── k8s/                        # Kubernetes manifests
│   ├── base/                   # Base Kubernetes resources
│   └── overlays/               # Environment-specific overlays
│       ├── development/        # Development environment
│       └── production/         # Production environment
├── monitoring/                 # Monitoring configuration
│   └── prometheus.yml          # Prometheus alert rules
├── database/                   # Database migrations
│   └── versions/               # Alembic migration files
├── terraform/                  # Infrastructure as Code
├── pyproject.toml              # Python project configuration
├── Dockerfile                  # Container build definition
├── docker-compose.yml          # Root compose file
└── openapi.json                # OpenAPI specification
```

---

## Development Workflow

### Branching Strategy

```
main (production)
  ↑
develop (integration)
  ↑
feature/* (features)
  ↑
bugfix/* (bug fixes)
  ↑
hotfix/* (urgent fixes)
```

### Typical Development Flow

1. **Create a feature branch:**

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-new-feature
```

2. **Make changes and commit:**

```bash
# Make your changes
git add .
git commit -m "feat: add new moderation agent"
```

3. **Push and create PR:**

```bash
git push origin feature/my-new-feature
# Create pull request on GitHub
```

4. **After review, merge to develop**

5. **Release to production:**

```bash
git checkout main
git merge develop
git tag v1.1.0
git push origin main --tags
```

---

## Adding a New Agent

### Step 1: Create the Agent Module

Create a new file in the appropriate agent directory:

```python
# src/ugc_marketplace/agents/my_domain/my_agent.py
from __future__ import annotations

from typing import Any


class MyAgent:
    """Agent for performing specific tasks."""

    def __init__(self) -> None:
        """Initialize the agent."""
        pass

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process the input data.

        Args:
            data: Input data to process.

        Returns:
            Processing result.
        """
        # Implement your agent logic here
        return {"result": "success"}
```

### Step 2: Register the Agent

Update the agent's `__init__.py`:

```python
# src/ugc_marketplace/agents/my_domain/__init__.py
from ugc_marketplace.agents.my_domain.my_agent import MyAgent

__all__ = ["MyAgent"]
```

### Step 3: Add Tests

```python
# src/ugc_marketplace/tests/test_agents/test_my_agent.py
import pytest

from ugc_marketplace.agents.my_domain import MyAgent


@pytest.fixture
def agent() -> MyAgent:
    return MyAgent()


@pytest.mark.asyncio
async def test_process(agent: MyAgent) -> None:
    result = await agent.process({"key": "value"})
    assert result["result"] == "success"
```

---

## Adding a New API Endpoint

### Step 1: Create the Router

```python
# src/ugc_marketplace/api/my_domain/__init__.py
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/my-domain", tags=["my-domain"])


@router.get("/status")
async def get_status() -> dict[str, str]:
    """Get service status."""
    return {"status": "ok"}
```

### Step 2: Register the Router

Update `main.py`:

```python
from ugc_marketplace.api.my_domain import router as my_domain_router

# Add to the app setup
app.include_router(my_domain_router, prefix=api_prefix, tags=["MyDomain"])
```

### Step 3: Add Tests

```python
# src/ugc_marketplace/tests/test_api/test_my_domain.py
from fastapi.testclient import TestClient

from ugc_marketplace.main import app


def test_get_status() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/my-domain/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ugc_marketplace --cov-report=term-missing

# Run specific test file
pytest src/ugc_marketplace/tests/test_agents/test_content_moderation.py

# Run specific test
pytest src/ugc_marketplace/tests/test_agents/test_content_moderation.py::test_text_moderation

# Run with verbose output
pytest -v

# Run async tests
pytest --asyncio-mode=auto
```

### Test Structure

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

from ugc_marketplace.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create an async test client."""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

### Writing Good Tests

```python
import pytest
from fastapi.testclient import TestClient

from ugc_marketplace.main import app


class TestContentModeration:
    """Tests for content moderation endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(app)

    def test_moderate_text_success(self, client: TestClient) -> None:
        """Test successful text moderation."""
        response = client.post(
            "/api/v1/moderation/moderate/text",
            json={"content": "Hello world", "content_type": "text"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "text"
        assert "action" in data

    def test_moderate_text_invalid_content_type(self, client: TestClient) -> None:
        """Test moderation with invalid content type."""
        response = client.post(
            "/api/v1/moderation/moderate/text",
            json={"content": "Hello", "content_type": "invalid"},
        )
        assert response.status_code == 422
```

---

## Code Style and Linting

### Linting

The project uses **ruff** for linting and **mypy** for type checking:

```bash
# Run linter
ruff check src/

# Run linter with auto-fix
ruff check src/ --fix

# Run type checker
mypy src/

# Run all checks
ruff check src/ && mypy src/
```

### Code Style Rules

- **Line length:** 100 characters
- **Import order:** stdlib → third-party → local
- **Type annotations:** Required for all functions
- **Docstrings:** Required for all public classes and functions

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pre-commit install
```

Run manually:

```bash
pre-commit run --all-files
```

---

## Debugging

### Using VS Code

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["ugc_marketplace.main:app", "--reload", "--port", "8000"],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### Using pdb

```python
import pdb; pdb.set_trace()  # Add this where you want to break
```

### Logging

```python
from structlog import get_logger

logger = get_logger(__name__)

async def my_function():
    logger.info("Function called", extra={"key": "value"})
    logger.error("Error occurred", exc_info=True)
```

---

## Common Tasks

### Adding a New Integration

1. Create the integration module:

```python
# src/ugc_marketplace/integrations/my_domain/my_service.py
from __future__ import annotations

import httpx


class MyServiceClient:
    """Client for external service."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.api_key = api_key

    async def call_api(self, endpoint: str) -> dict:
        """Call the external API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            return response.json()
```

2. Register in the agent or API layer.

### Adding a New Database Model

1. Create the model:

```python
# src/ugc_marketplace/models/my_model.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from ugc_marketplace.models.base import Base


class MyModel(Base):
    __tablename__ = "my_table"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
```

2. Create migration:

```bash
alembic revision --autogenerate -m "add my_table"
alembic upgrade head
```

### Adding Configuration Options

Update `src/ugc_marketplace/config/__init__.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # New settings
    my_new_setting: str = "default_value"
    my_numeric_setting: int = 42
```

Access in code:

```python
from ugc_marketplace.config import get_settings

settings = get_settings()
print(settings.my_new_setting)
```

### Running Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current version
alembic current

# View history
alembic history
```
