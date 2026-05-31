#!/usr/bin/env bash
# ISO/IEC 42001 AIMS — unit + gateway API (iso-42001-ai-management-engineering)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TOKEN="${GRC_CLAW_GATEWAY_TOKEN:-grc-test-token}"
BASE="${GRC_CLAW_BASE:-http://127.0.0.1:18791}"

echo "▶ ISO 42001 AIMS: package unit tests"
npm run build
npm run test -w @grc-claw/aims

echo "▶ ISO 42001 AIMS: gateway endpoints"
lsof -ti :18791 | xargs kill -9 2>/dev/null || true
sleep 1
GRC_CLAW_GATEWAY_TOKEN="$TOKEN" A2Z_SOC_MODE=demo node packages/gateway/dist/cli.js &
GW_PID=$!
trap '[[ -n "${GW_PID:-}" ]] && kill "$GW_PID" 2>/dev/null || true' EXIT
sleep 2

pass=0
fail=0
assert() {
  local name="$1" pat="$2" hay="$3"
  if echo "$hay" | grep -qE "$pat"; then echo "  ✓ $name"; pass=$((pass+1)); else echo "  ✗ $name"; fail=$((fail+1)); fi
}

HEALTH=$(curl -s "$BASE/health")
assert "health: iso_42001_aims" '"iso_42001_aims":true' "$HEALTH"

GAPS=$(curl -s "$BASE/api/aims/vendor-gaps")
assert "vendor-gaps: anthropic" '"vendor":"anthropic"' "$GAPS"
assert "vendor-gaps: openclaw" '"vendor":"openclaw"' "$GAPS"

TC=$(curl -s "$BASE/api/aims/technical-controls")
assert "technical-controls: TC-01 oversight" 'TC-01' "$TC"
assert "technical-controls: agent-runtime" 'agent-runtime' "$TC"
assert "technical-controls: a2z-soc" 'a2z-soc' "$TC"

FW=$(curl -s "$BASE/api/frameworks")
assert "frameworks: iso42001 pack" '"code":"iso42001"' "$FW"

echo ""
echo "ISO 42001 AIMS: $pass passed, $fail failed"
exit "$fail"
