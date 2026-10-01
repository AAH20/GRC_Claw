#!/usr/bin/env bash
# GRC_Claw Image Scanner — Trivy + Grype vulnerability scanning
# Usage: bash scripts/scan-images.sh [registry] [tag]
set -euo pipefail

REGISTRY="${1:-ghcr.io/grc-claw}"
TAG="${2:-latest}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORT_DIR="${ROOT}/reports"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
FAIL_ON_CRITICAL="${FAIL_ON_CRITICAL:-true}"

mkdir -p "$REPORT_DIR"

# Images to scan
IMAGES=(
  "${REGISTRY}/gateway:${TAG}"
  "${REGISTRY}/pdp-service:${TAG}"
  "${REGISTRY}/pep-gateway:${TAG}"
  "${REGISTRY}/policy-api:${TAG}"
  "${REGISTRY}/agent-identity:${TAG}"
  "${REGISTRY}/analytics-engine:${TAG}"
  "${REGISTRY}/approval-workflow:${TAG}"
  "${REGISTRY}/compliance-mapping:${TAG}"
  "${REGISTRY}/discovery-engine:${TAG}"
  "${REGISTRY}/evidence-collector:${TAG}"
  "${REGISTRY}/otel-collector:${TAG}"
  "${REGISTRY}/reporting-engine:${TAG}"
  "${REGISTRY}/risk-assessment:${TAG}"
)

echo "═══════════════════════════════════════════════════════════"
echo " GRC_Claw Image Security Scan"
echo " Registry: ${REGISTRY}"
echo " Tag:      ${TAG}"
echo " Time:     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "═══════════════════════════════════════════════════════════"
echo ""

TOTAL_CRITICAL=0
TOTAL_HIGH=0
SCAN_FAILED=0

# ── Trivy Scan ──────────────────────────────────────────────────────────────
if command -v trivy &>/dev/null; then
  echo "▶ Running Trivy scan..."
  for img in "${IMAGES[@]}"; do
    name=$(echo "$img" | sed "s|${REGISTRY}/||; s|:${TAG}||")
    report="${REPORT_DIR}/trivy_${name}_${TIMESTAMP}.json"
    echo "  → Scanning ${name}..."
    if trivy image \
      --severity HIGH,CRITICAL \
      --format json \
      --output "$report" \
      --quiet \
      "$img" 2>/dev/null; then
      crit=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length' "$report" 2>/dev/null || echo 0)
      high=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="HIGH")] | length' "$report" 2>/dev/null || echo 0)
      TOTAL_CRITICAL=$((TOTAL_CRITICAL + crit))
      TOTAL_HIGH=$((TOTAL_HIGH + high))
      echo "    CRITICAL: ${crit}, HIGH: ${high}"
    else
      echo "    ⚠ Trivy scan failed for ${name}"
      SCAN_FAILED=$((SCAN_FAILED + 1))
    fi
  done
  echo "  Trivy complete: ${TOTAL_CRITICAL} critical, ${TOTAL_HIGH} high"
else
  echo "⚠ Trivy not installed — skipping"
  echo "  Install: brew install trivy"
fi

echo ""

# ── Grype Scan ──────────────────────────────────────────────────────────────
if command -v grype &>/dev/null; then
  echo "▶ Running Grype scan..."
  GRYPE_CRITICAL=0
  GRYPE_HIGH=0
  for img in "${IMAGES[@]}"; do
    name=$(echo "$img" | sed "s|${REGISTRY}/||; s|:${TAG}||")
    report="${REPORT_DIR}/grype_${name}_${TIMESTAMP}.json"
    echo "  → Scanning ${name}..."
    if grype "$img" -o json > "$report" 2>/dev/null; then
      crit=$(jq '[.matches[] | select(.vulnerability.severity=="Critical")] | length' "$report" 2>/dev/null || echo 0)
      high=$(jq '[.matches[] | select(.vulnerability.severity=="High")] | length' "$report" 2>/dev/null || echo 0)
      GRYPE_CRITICAL=$((GRYPE_CRITICAL + crit))
      GRYPE_HIGH=$((GRYPE_HIGH + high))
      echo "    Critical: ${crit}, High: ${high}"
    else
      echo "    ⚠ Grype scan failed for ${name}"
    fi
  done
  echo "  Grype complete: ${GRYPE_CRITICAL} critical, ${GRYPE_HIGH} high"
else
  echo "⚠ Grype not installed — skipping"
  echo "  Install: brew install grype"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo " Scan Summary"
echo "  Trivy: ${TOTAL_CRITICAL} critical, ${TOTAL_HIGH} high"
echo "  Reports: ${REPORT_DIR}"
echo "═══════════════════════════════════════════════════════════"

if [[ "$FAIL_ON_CRITICAL" == "true" ]] && [[ $TOTAL_CRITICAL -gt 0 ]]; then
  echo "❌ CRITICAL vulnerabilities found — failing build"
  exit 1
fi

if [[ $SCAN_FAILED -gt 0 ]]; then
  echo "⚠ ${SCAN_FAILED} scans failed"
  exit 1
fi

echo "✓ Image scan complete"
