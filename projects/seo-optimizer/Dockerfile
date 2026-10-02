# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --prefix=/install .

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

RUN groupadd -r seooptimizer && useradd -r -g seooptimizer seooptimizer

COPY --from=builder /install /usr/local

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=seooptimizer:seooptimizer src ./src
COPY --chown=seooptimizer:seooptimizer config ./config

USER seooptimizer

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "seo_optimizer.main:app", "--host", "0.0.0.0", "--port", "8000"]
