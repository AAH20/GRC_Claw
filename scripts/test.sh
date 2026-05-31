#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TOKEN="${GRC_CLAW_GATEWAY_TOKEN:-grc-test-token}"
BASE="${GRC_CLAW_BASE:-http://127.0.0.1:18791}"

echo "Building..."
npm run build

GW_PID=""
if ! curl -sf "$BASE/health" >/dev/null 2>&1; then
  echo "Starting gateway..."
  GRC_CLAW_GATEWAY_TOKEN="$TOKEN" A2Z_SOC_MODE=demo node packages/gateway/dist/cli.js &
  GW_PID=$!
  trap '[[ -n "$GW_PID" ]] && kill "$GW_PID" 2>/dev/null || true' EXIT
  sleep 2
fi

pass=0
fail=0
assert() {
  local name="$1" pat="$2" hay="$3"
  if echo "$hay" | grep -qE "$pat"; then echo "✓ $name"; pass=$((pass+1)); else echo "✗ $name (expected: $pat)"; fail=$((fail+1)); fi
}

echo "=== GRC_Claw tests @ $BASE ==="
H=$(curl -s "$BASE/health")
assert "health" '"ok":true' "$H"
assert "agentic AI security" 'agentic_ai_security":true' "$H"
assert "A2Z SOC marketing" 'A2Z SOC' "$H"

F=$(curl -s "$BASE/api/frameworks")
assert "framework packs" 'iso27001' "$F"
assert "ISO 42001 framework pack" 'iso42001' "$F"

S=$(curl -s -X POST "$BASE/api/a2z/sync" -H "X-GRC-Claw-Token: $TOKEN")
assert "A2Z demo sync (2 events)" '"processed":2' "$S"
assert "Suricata → controls" 'iso-a.8.16' "$S"

code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/a2z/sync" -H "X-GRC-Claw-Token: bad")
assert "auth reject 401" '^401$' "$code"

A=$(curl -s -X POST "$BASE/api/agent/invoke" -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"s","tool":"grc.list_controls","args":{}}')
assert "agent read allowed" '"allowed":true' "$A"

code=$(curl -s -o /tmp/grc-d.json -w "%{http_code}" -X POST "$BASE/api/agent/invoke" -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"s","tool":"soar.run_playbook","args":{}}')
assert "destructive HTTP 403" '^403$' "$code"
assert "destructive needs approval" 'destructive_requires_approval' "$(cat /tmp/grc-d.json)"

W2=$(curl -s -X POST "$BASE/api/agent/invoke" -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"s","tool":"evidence.attach","args":{},"idempotencyKey":"test-k1"}')
assert "write with idempotency" '"allowed":true' "$W2"

W3=$(curl -s -X POST "$BASE/api/agent/invoke" -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"s","tool":"evidence.attach","args":{},"idempotencyKey":"test-k1"}')
assert "idempotency dedupe" '"deduped":true' "$W3"

CONN=$(node --input-type=module -e "
import { A2ZSocConnector } from './packages/a2z-connector/dist/index.js';
const c = new A2ZSocConnector({ baseUrl: 'http://x', apiKey: 'k', tenantId: 1, mode: 'demo' });
const n = (await c.pullSecurityEvents(new Date().toISOString())).length;
process.stdout.write(n === 2 ? 'connector_ok' : 'connector_fail');
")
assert "connector package demo" 'connector_ok' "$CONN"

echo ""
echo "=== $pass passed, $fail failed ==="
exit "$fail"
