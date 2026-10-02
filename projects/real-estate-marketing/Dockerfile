# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --upgrade pip && \
    pip install fastapi uvicorn[standard] pydantic pydantic-settings httpx PyYAML python-dotenv structlog tenacity langchain langchain-core langchain-community langgraph openai anthropic sqlalchemy alembic redis celery jinja2 aiofiles

# Copy application code
COPY src/ src/

# Create non-root user
RUN useradd --create-home --shell /bin/sh appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "real_estate_marketing.main:app", "--host", "0.0.0.0", "--port", "8000"]
