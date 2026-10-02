#!/usr/bin/env bash
# teardown-monitoring.sh — Tear down the GRC Claw monitoring and observability stack.
# Stops all containers and optionally removes volumes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${STACK_DIR}/docker-compose.yml"

log()   { printf '\033[0;32m[teardown]\033[0m %s\n' "$*"; }
warn()  { printf '\033[0;33m[teardown]\033[0m %s\n' "$*" >&2; }
error() { printf '\033[0;31m[teardown]\033[0m %s\n" "$*" >&2; exit 1; }

# ── Parse arguments ─────────────────────────────────────────────────────────
REMOVE_VOLUMES=false
REMOVE_IMAGES=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --volumes|-v)
      REMOVE_VOLUMES=true
      shift
      ;;
    --images|-i)
      REMOVE_IMAGES=true
      shift
      ;;
    --all|-a)
      REMOVE_VOLUMES=true
      REMOVE_IMAGES=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  -v, --volumes    Remove data volumes (prometheus, loki, tempo, etc.)"
      echo "  -i, --images     Remove Docker images"
      echo "  -a, --all        Remove volumes and images"
      echo "  -h, --help       Show this help message"
      exit 0
      ;;
    *)
      error "Unknown option: $1. Use --help for usage."
      ;;
  esac
done

# ── Pre-flight checks ────────────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || error "Docker is not installed or not in PATH."
docker compose version >/dev/null 2>&1 || error "Docker Compose v2 is required."

# ── Stop containers ─────────────────────────────────────────────────────────
log "Stopping monitoring stack..."
if [[ "$REMOVE_VOLUMES" == true ]]; then
  log "Removing containers and volumes..."
  docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
elif [[ "$REMOVE_IMAGES" == true ]]; then
  log "Removing containers and images..."
  docker compose -f "$COMPOSE_FILE" down --rmi all --remove-orphans
else
  log "Removing containers (data volumes preserved)..."
  docker compose -f "$COMPOSE_FILE" down --remove-orphans
fi

# ── Clean up dangling resources ─────────────────────────────────────────────
if [[ "$REMOVE_IMAGES" == true ]]; then
  log "Cleaning up dangling images..."
  docker image prune -f >/dev/null 2>&1 || true
fi

# ── Summary ─────────────────────────────────────────────────────────────────
log "Monitoring stack torn down."
if [[ "$REMOVE_VOLUMES" == true ]]; then
  warn "All data volumes have been removed. Historical metrics and logs are gone."
else
  log "Data volumes are preserved. Run with --volumes to remove them."
fi
