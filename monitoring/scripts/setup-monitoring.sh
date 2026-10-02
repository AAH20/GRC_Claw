#!/usr/bin/env bash
# setup-monitoring.sh — Deploy the GRC Claw monitoring and observability stack.
# Starts Prometheus, Grafana, Alertmanager, Loki, Tempo, OTel Collector, and Promtail.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${STACK_DIR}/docker-compose.yml"
ENV_FILE="${STACK_DIR}/.env"

log()   { printf '\033[0;32m[setup]\033[0m %s\n' "$*"; }
warn()  { printf '\033[0;33m[setup]\033[0m %s\n' "$*" >&2; }
error() { printf '\033[0;31m[setup]\033[0m %s\n' "$*" >&2; exit 1; }

# ── Pre-flight checks ────────────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || error "Docker is not installed or not in PATH."
docker compose version >/dev/null 2>&1 || error "Docker Compose v2 is required."

# ── Environment ─────────────────────────────────────────────────────────────
if [[ -f "$ENV_FILE" ]]; then
  log "Loading environment from ${ENV_FILE}"
  set -a; # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
else
  warn "No .env file found at ${ENV_FILE}; using defaults."
fi

# ── Create required directories ─────────────────────────────────────────────
log "Creating data directories..."
mkdir -p \
  "${STACK_DIR}/data/prometheus" \
  "${STACK_DIR}/data/grafana" \
  "${STACK_DIR}/data/loki" \
  "${STACK_DIR}/data/tempo" \
  "${STACK_DIR}/data/alertmanager" \
  "${STACK_DIR}/data/otel-collector" \
  "${STACK_DIR}/data/promtail"

# ── Validate configs ────────────────────────────────────────────────────────
log "Validating Prometheus configuration..."
if command -v promtool >/dev/null 2>&1; then
  promtool check config "${STACK_DIR}/prometheus/prometheus.yml" \
    || error "Prometheus config validation failed."
  promtool check rules "${STACK_DIR}/prometheus/alert-rules.yml" \
    || error "Prometheus alert rules validation failed."
else
  warn "promtool not found; skipping Prometheus config validation."
fi

# ── Deploy stack ────────────────────────────────────────────────────────────
log "Starting monitoring stack..."
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

# ── Wait for services ───────────────────────────────────────────────────────
log "Waiting for services to become healthy..."
SERVICES=(
  "prometheus:9090/-/healthy"
  "grafana:3000/api/health"
  "alertmanager:9093/-/healthy"
  "loki:3100/ready"
  "tempo:3200/ready"
  "otel-collector:13133"
)

for svc in "${SERVICES[@]}"; do
  name="${svc%%:*}"
  endpoint="${svc##*:}"
  log "  Waiting for ${name}..."
  for i in $(seq 1 30); do
    if curl -sf "http://localhost:${endpoint}" >/dev/null 2>&1; then
      log "  ${name} is ready."
      break
    fi
    if [[ $i -eq 30 ]]; then
      warn "  ${name} did not become healthy in 30s; check logs with: docker compose -f ${COMPOSE_FILE} logs ${name}"
    fi
    sleep 1
  done
done

# ── Summary ─────────────────────────────────────────────────────────────────
log "Monitoring stack deployed successfully."
log ""
log "  Prometheus:    http://localhost:9090"
log "  Grafana:       http://localhost:3000  (admin/admin)"
log "  Alertmanager: http://localhost:9093"
log "  Loki:         http://localhost:3100"
log "  Tempo:        http://localhost:3200"
log "  OTel Collector: localhost:4317 (gRPC), localhost:4318 (HTTP)"
log ""
log "Dashboards are provisioned automatically from grafana/dashboards/."
