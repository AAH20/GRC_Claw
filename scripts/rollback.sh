#!/usr/bin/env bash
# GRC_Claw Rollback Automation
# Usage: bash scripts/rollback.sh [registry] [current_tag]
set -euo pipefail

REGISTRY="${1:-ghcr.io/grc-claw}"
CURRENT_TAG="${2:-latest}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="${ROOT}/deploy/docker-compose.yml"
STATE_DIR="${ROOT}/.rollback"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$STATE_DIR"

echo "═══════════════════════════════════════════════════════════"
echo " GRC_Claw Rollback"
echo " Current tag: ${CURRENT_TAG}"
echo " Time:        $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── Step 1: Determine previous tag ──────────────────────────────────────────
echo "▶ Step 1: Finding previous stable tag..."

# Check for saved state from last deploy
PREVIOUS_TAG=""
if [[ -f "${STATE_DIR}/last_deploy" ]]; then
  PREVIOUS_TAG=$(cat "${STATE_DIR}/last_deploy")
  echo "  Found saved state: ${PREVIOUS_TAG}"
else
  # Try to find previous image by listing docker images
  echo "  No saved state — checking local images..."
  PREVIOUS_TAG=$(docker images --format "{{.Tag}}" "${REGISTRY}/gateway" 2>/dev/null | grep -v "$CURRENT_TAG" | grep -v "latest" | head -1 || true)
  if [[ -n "$PREVIOUS_TAG" ]]; then
    echo "  Found local image: ${PREVIOUS_TAG}"
  fi
fi

if [[ -z "$PREVIOUS_TAG" ]]; then
  echo "  ⚠ No previous tag found — cannot rollback automatically"
  echo "  Available tags:"
  docker images --format "    {{.Repository}}:{{.Tag}}" "${REGISTRY}/gateway" 2>/dev/null || echo "    (none)"
  echo ""
  echo "  Manual rollback: docker compose -f ${COMPOSE_FILE} down"
  echo "                   docker tag ${REGISTRY}/gateway:<previous> ${REGISTRY}/gateway:${CURRENT_TAG}"
  echo "                   docker compose -f ${COMPOSE_FILE} up -d"
  exit 1
fi

echo "  Rolling back to: ${PREVIOUS_TAG}"
echo ""

# ── Step 2: Save current state ──────────────────────────────────────────────
echo "▶ Step 2: Saving current state..."
echo "$CURRENT_TAG" > "${STATE_DIR}/rollback_source_${TIMESTAMP}"
echo "  Saved: ${STATE_DIR}/rollback_source_${TIMESTAMP}"
echo ""

# ── Step 3: Pull previous images ─────────────────────────────────────────────
echo "▶ Step 3: Ensuring previous images exist locally..."

SERVICES=(
  "gateway"
  "pdp-service"
  "pep-gateway"
  "policy-api"
  "agent-identity"
  "analytics-engine"
  "approval-workflow"
  "compliance-mapping"
  "discovery-engine"
  "evidence-collector"
  "otel-collector"
  "reporting-engine"
  "risk-assessment"
)

MISSING=0
for svc in "${SERVICES[@]}"; do
  if ! docker image inspect "${REGISTRY}/${svc}:${PREVIOUS_TAG}" &>/dev/null; then
    echo "  → Pulling ${svc}:${PREVIOUS_TAG}..."
    if ! docker pull "${REGISTRY}/${svc}:${PREVIOUS_TAG}" 2>/dev/null; then
      echo "    ⚠ Failed to pull ${svc}:${PREVIOUS_TAG}"
      MISSING=$((MISSING + 1))
    fi
  else
    echo "  ✓ ${svc}:${PREVIOUS_TAG} exists locally"
  fi
done

if [[ $MISSING -gt 0 ]]; then
  echo ""
  echo "  ⚠ ${MISSING} images missing — rollback may be incomplete"
  read -p "  Continue anyway? [y/N] " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "  Rollback cancelled"
    exit 1
  fi
fi

echo ""

# ── Step 4: Stop current stack ───────────────────────────────────────────────
echo "▶ Step 4: Stopping current stack..."
docker compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
echo "  Stack stopped"
echo ""

# ── Step 5: Tag previous as current ──────────────────────────────────────────
echo "▶ Step 5: Tagging previous images as ${CURRENT_TAG}..."
for svc in "${SERVICES[@]}"; do
  if docker image inspect "${REGISTRY}/${svc}:${PREVIOUS_TAG}" &>/dev/null; then
    docker tag "${REGISTRY}/${svc}:${PREVIOUS_TAG}" "${REGISTRY}/${svc}:${CURRENT_TAG}"
    echo "  ✓ ${svc}:${PREVIOUS_TAG} → ${CURRENT_TAG}"
  fi
done
echo ""

# ── Step 6: Start stack with previous images ─────────────────────────────────
echo "▶ Step 6: Starting stack with previous images..."
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
echo "  Stack started"
echo ""

# ── Step 7: Validate rollback ────────────────────────────────────────────────
echo "▶ Step 7: Validating rollback..."
sleep 3

GATEWAY_PORT=$(docker compose -f "$COMPOSE_FILE" port gateway 18791 2>/dev/null | grep -oE '[0-9]+$' || echo "18791")
TOKEN="${GRC_CLAW_GATEWAY_TOKEN:-demo-compose-token}"

HEALTH=$(curl -sf "http://127.0.0.1:${GATEWAY_PORT}/health" 2>/dev/null || echo "")
if echo "$HEALTH" | grep -q '"ok":true'; then
  echo "  ✓ Gateway healthy after rollback"
else
  echo "  ⚠ Gateway not healthy after rollback — manual intervention may be needed"
  echo "  Check: docker compose -f ${COMPOSE_FILE} logs"
fi

echo ""

# ── Step 8: Update state ─────────────────────────────────────────────────────
echo "$PREVIOUS_TAG" > "${STATE_DIR}/last_deploy"
echo "▶ Step 8: State updated — last_deploy = ${PREVIOUS_TAG}"
echo ""

echo "═══════════════════════════════════════════════════════════"
echo " Rollback Complete"
echo "  Rolled back to: ${PREVIOUS_TAG}"
echo "  Gateway:        http://127.0.0.1:${GATEWAY_PORT}"
echo "═══════════════════════════════════════════════════════════"
