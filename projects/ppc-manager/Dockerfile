# syntax=docker/dockerfile:1

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --prefix=/install .

# Runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app

RUN groupadd -r ppc && useradd -r -g ppc ppc

COPY --from=builder /install /usr/local
COPY --chown=ppc:ppc src ./src
COPY --chown=ppc:ppc config ./config

USER ppc

EXPOSE 8000

ENV PYTHONPATH=/app/src \
    PORT=8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "ppc_manager.main:app", "--host", "0.0.0.0", "--port", "8000"]
