#!/usr/bin/env bash
# BYOC: LLM + MCP connector registry and gateway routes
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TOKEN="${GRC_CLAW_GATEWAY_TOKEN:-grc-test-token}"
BASE="${GRC_CLAW_BASE:-http://127.0.0.1:18791}"

export GRC_CLAW_CONNECTORS_JSON='{"version":1,"llm":[{"id":"mock","label":"Mock","kind":"openai_compatible","baseUrl":"http://127.0.0.1:9","apiKeyEnv":"OPENAI_API_KEY"}],"mcp":[{"id":"demo","label":"Demo MCP","transport":"http","url":"http://127.0.0.1:9/mcp","destructiveTools":["delete"]}]}'

echo "▶ BYOC unit tests"
npm run build
npm run test -w @grc-claw/connectors

echo "▶ BYOC gateway routes"
lsof -ti :18791 | xargs kill -9 2>/dev/null || true
sleep 1
GRC_CLAW_GATEWAY_TOKEN="$TOKEN" GRC_CLAW_CONNECTORS_JSON="$GRC_CLAW_CONNECTORS_JSON" node packages/gateway/dist/cli.js &
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

DENY=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/agent/invoke" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"byoc","tool":"mcp.demo.delete","args":{}}')
assert "agent: destructive mcp 403 without approval" '^403$' "$DENY"

echo ""
echo "BYOC connectors: $pass passed, $fail failed"
exit "$fail"
