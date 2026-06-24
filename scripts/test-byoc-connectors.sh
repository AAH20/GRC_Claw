#!/usr/bin/env bash
# BYOC: LLM + MCP connector registry and gateway routes
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TOKEN="${GRC_CLAW_GATEWAY_TOKEN:-grc-test-token}"
BASE="${GRC_CLAW_BASE:-http://127.0.0.1:18791}"
LEDGER_PATH="$(mktemp)"
rm -f "$LEDGER_PATH"
MEMORY_DIR="$(mktemp -d)"

export GRC_CLAW_CONNECTORS_JSON='{"version":1,"llm":[{"id":"mock","label":"Mock","kind":"openai_compatible","baseUrl":"http://127.0.0.1:9","apiKeyEnv":"OPENAI_API_KEY"}],"mcp":[{"id":"demo","label":"Demo MCP","transport":"http","url":"http://127.0.0.1:9/mcp","destructiveTools":["delete"]}]}'

echo "▶ BYOC unit tests"
npm run build
npm run test -w @grc-claw/connectors

echo "▶ BYOC gateway routes"
lsof -ti :18791 | xargs kill -9 2>/dev/null || true
sleep 1
GRC_CLAW_GATEWAY_TOKEN="$TOKEN" GRC_CLAW_CONNECTORS_JSON="$GRC_CLAW_CONNECTORS_JSON" GRC_CLAW_ACTION_LEDGER_PATH="$LEDGER_PATH" GRC_CLAW_MEMORY_DIR="$MEMORY_DIR" node packages/gateway/dist/cli.js &
GW_PID=$!
trap '[[ -n "${GW_PID:-}" ]] && kill "$GW_PID" 2>/dev/null || true; rm -f "$LEDGER_PATH"; rmdir "$MEMORY_DIR" 2>/dev/null || true' EXIT
sleep 2

pass=0
fail=0
assert() {
  local name="$1" pat="$2" hay="$3"
  if echo "$hay" | grep -qE "$pat"; then echo "  ✓ $name"; pass=$((pass+1)); else echo "  ✗ $name"; fail=$((fail+1)); fi
}

HEALTH=$(curl -s "$BASE/health")
assert "health: byoc_connectors" '"byoc_connectors":true' "$HEALTH"
assert "health: llm_providers" '"llm_providers":1' "$HEALTH"

LIST=$(curl -s "$BASE/api/connectors")
assert "connectors list" '"byoc":true' "$LIST"
assert "connectors mock llm" '"id":"mock"' "$LIST"

# BYOC tool in allowlist (policy includes llm.mock.complete)
INV=$(curl -s -X POST "$BASE/api/agent/invoke" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"byoc","tool":"llm.mock.complete","args":{"prompt":"hi"}}')
assert "agent: llm tool allowed by policy" '"allowed":true' "$INV"

ATTACH=$(curl -s -X POST "$BASE/api/agent/invoke" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"agentId":"qa-agent","sessionId":"ledger","tool":"evidence.attach","idempotencyKey":"evidence-attach-1","args":{"tenantId":1,"controlId":"AC.1","uri":"test://evidence","content":"test-evidence"}}')
assert "agent: evidence receipt is recorded" '"executionState":"recorded"' "$ATTACH"
assert "agent: assurance binds a DID" '"agentDid":"did:grc:' "$ATTACH"
assert "agent: assurance calculates blast radius" '"blastRadius"' "$ATTACH"

ASSURANCE=$(curl -s "$BASE/api/assurance" -H "X-GRC-Claw-Token: $TOKEN")
assert "agent: assurance graph tracks actions" '"totalNodes":' "$ASSURANCE"

LEDGER=$(curl -s "$BASE/api/action-ledger?limit=10" -H "X-GRC-Claw-Token: $TOKEN")
assert "agent: ledger integrity" '"ok":true' "$LEDGER"
assert "agent: ledger records intent" '"kind":"intent"' "$LEDGER"

SCORE=$(curl -s -X POST "$BASE/api/agent/invoke" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"truth","tool":"grc.get_compliance_score","args":{"tenantId":1}}')
assert "agent: no fabricated compliance score" '"executionState":"not_configured"' "$SCORE"

DENY=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/agent/invoke" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"byoc","tool":"mcp.demo.delete","args":{}}')
assert "agent: destructive mcp 403 without approval" '^403$' "$DENY"

echo ""
echo "BYOC connectors: $pass passed, $fail failed"
exit "$fail"
