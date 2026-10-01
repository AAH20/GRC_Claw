#!/usr/bin/env bash
# GRC_Claw Deployment Validation Script
# Usage: bash scripts/validate-deployment.sh [port] [token]
set -euo pipefail

PORT="${1:-18791}"
TOKEN="${2:-grc-test-token}"
BASE="http://127.0.0.1:${PORT}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORT="${ROOT}/reports/deployment-validation-$(date +%Y%m%d_%H%M%S).json"

mkdir -p "$(dirname "$REPORT")"

pass=0
fail=0
warnings=0

assert() {
  local name="$1" pat="$2" hay="$3"
  if echo "$hay" | grep -qE "$pat"; then
    echo "  ✓ $name"
    pass=$((pass+1))
  else
    echo "  ✗ $name (expected: $pat)"
    fail=$((fail+1))
  fi
}

assert_http() {
  local name="$1" url="$2" expected_code="$3"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
  if [[ "$code" == "$expected_code" ]]; then
    echo "  ✓ $name (HTTP $code)"
    pass=$((pass+1))
  else
    echo "  ✗ $name (expected HTTP $expected_code, got $code)"
    fail=$((fail+1))
  fi
}

echo "═══════════════════════════════════════════════════════════"
echo " GRC_Claw Deployment Validation"
echo " Target: ${BASE}"
echo " Time:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── Phase 1: Container Health ───────────────────────────────────────────────
echo "▶ Phase 1: Container Health"

if command -v docker &>/dev/null; then
  containers=$(docker ps --filter "name=grc-claw" --format "{{.Names}}" 2>/dev/null || true)
  if [[ -n "$containers" ]]; then
    echo "  Running containers:"
    for c in $containers; do
      status=$(docker inspect --format='{{.State.Health.Status}}' "$c" 2>/dev/null || echo "unknown")
      echo "    → $c: $status"
      if [[ "$status" == "healthy" ]] || [[ "$status" == "unknown" ]]; then
        pass=$((pass+1))
      else
        echo "    ⚠ Container $c is not healthy ($status)"
        warnings=$((warnings+1))
      fi
    done
  else
    echo "  ⚠ No GRC_Claw containers found"
    warnings=$((warnings+1))
  fi
else
  echo "  ⚠ Docker not available — skipping container checks"
  warnings=$((warnings+1))
fi

echo ""

# ── Phase 2: Gateway Health ─────────────────────────────────────────────────
echo "▶ Phase 2: Gateway Health"

HEALTH=$(curl -sf "$BASE/health" 2>/dev/null || echo "")
assert "health endpoint" '"ok":true' "$HEALTH"
assert "agentic AI security" 'agentic_ai_security":true' "$HEALTH"
assert "A2Z SOC marketing" 'A2Z SOC' "$HEALTH"
assert "ISO 42001 AIMS" 'iso_42001_aims":true' "$HEALTH"

echo ""

# ── Phase 3: API Endpoints ──────────────────────────────────────────────────
echo "▶ Phase 3: API Endpoints"

FW=$(curl -sf "$BASE/api/frameworks" 2>/dev/null || echo "")
assert "framework packs" 'iso27001' "$FW"
assert "ISO 42001 framework" 'iso42001' "$FW"

AIMS=$(curl -sf "$BASE/api/aims/technical-controls" 2>/dev/null || echo "")
assert "technical controls" 'TC-01' "$AIMS"

GAPS=$(curl -sf "$BASE/api/aims/vendor-gaps?vendor=openai" 2>/dev/null || echo "")
assert "vendor gaps" '"vendor":"openai"' "$GAPS"

echo ""

# ── Phase 4: Auth & Policy ──────────────────────────────────────────────────
echo "▶ Phase 4: Auth & Policy Enforcement"

code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/ingest/normalize" \
  -H "X-GRC-Claw-Token: bad-token" \
  -H "Content-Type: application/json" \
  -d '{"source":"test","tenantId":1,"payload":{}}' 2>/dev/null || echo "000")
assert "auth reject (401)" '^401$' "$code"

A=$(curl -sf -X POST "$BASE/api/agent/invoke" \
  -H "X-GRC-Claw-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"val","tool":"grc.list_controls","args":{}}' 2>/dev/null || echo "")
assert "agent read allowed" '"allowed":true' "$A"

D=$(curl -s -o /tmp/grc-val-d.json -w "%{http_code}" -X POST "$BASE/api/agent/invoke" \
  -H "X-GRC-Claw-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"val","tool":"soar.run_playbook","args":{}}' 2>/dev/null || echo "000")
assert "destructive blocked (403)" '^403$' "$D"
assert "destructive needs approval" 'destructive_requires_approval' "$(cat /tmp/grc-val-d.json 2>/dev/null || echo "")"

echo ""

# ── Phase 5: A2Z SOC Bridge ─────────────────────────────────────────────────
echo "▶ Phase 5: A2Z SOC Bridge"

S=$(curl -sf -X POST "$BASE/api/a2z/sync" -H "X-GRC-Claw-Token: $TOKEN" 2>/dev/null || echo "")
assert "A2Z demo sync" '"processed":2' "$S"
assert "Suricata → controls" 'iso-a.8.16' "$S"

echo ""

# ── Phase 6: Ingest Pipeline ────────────────────────────────────────────────
echo "▶ Phase 6: Ingest Pipeline"

SURICATA='{"timestamp":"2026-05-31T12:00:00Z","event_type":"alert","src_ip":"10.1.1.1","dest_ip":"10.2.2.2","alert":{"signature_id":99,"signature":"ET TEST","severity":1}}'
NORM=$(curl -sf -X POST "$BASE/api/ingest/normalize" \
  -H "X-GRC-Claw-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"source\":\"suricata\",\"tenantId\":1,\"payload\":$SURICATA}" 2>/dev/null || echo "")
assert "Suricata normalize" '"sourceSystem":"suricata"' "$NORM"
assert "network.intrusion category" 'network.intrusion' "$NORM"
assert "ISO control mapping" 'iso-a.8.16' "$NORM"

echo ""

# ── Phase 7: Idempotency ────────────────────────────────────────────────────
echo "▶ Phase 7: Idempotency"

W1=$(curl -sf -X POST "$BASE/api/agent/invoke" \
  -H "X-GRC-Claw-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"val","tool":"evidence.attach","args":{},"idempotencyKey":"val-k1"}' 2>/dev/null || echo "")
assert "write with idempotency" '"allowed":true' "$W1"

W2=$(curl -sf -X POST "$BASE/api/agent/invoke" \
  -H "X-GRC-Claw-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"val","tool":"evidence.attach","args":{},"idempotencyKey":"val-k1"}' 2>/dev/null || echo "")
assert "idempotency dedupe" '"deduped":true' "$W2"

echo ""

# ── Summary ─────────────────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════"
echo " Validation Summary"
echo "  Passed:   $pass"
echo "  Failed:   $fail"
echo "  Warnings: $warnings"
echo "  Report:   $REPORT"
echo "═══════════════════════════════════════════════════════════"

# Write JSON report
cat > "$REPORT" <<ENDJSON
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "target": "${BASE}",
  "passed": $pass,
  "failed": $fail,
  "warnings": $warnings,
  "status": "$([[ $fail -eq 0 ]] && echo "PASS" || echo "FAIL")"
}
ENDJSON

if [[ $fail -gt 0 ]]; then
  echo "❌ Validation FAILED ($fail failures)"
  exit 1
fi

echo "✓ Validation PASSED"
