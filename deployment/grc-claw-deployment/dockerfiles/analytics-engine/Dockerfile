# Analytics Engine (ML/Stats) - Multi-stage build
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM gcr.io/distroless/python3-debian12 AS runtime
LABEL org.opencontainers.image.version="1.2.0" \
      org.opencontainers.image.revision="v1.2.0" \
      grc.component="analytics-engine" \
      grc.tier="analytics"
COPY --from=builder /install /usr/local
COPY --chown=nonroot:nonroot src/ /app/
WORKDIR /app
USER 65534:65534
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')"
ENTRYPOINT ["python", "-m", "grc_claw.analytics_engine"]
