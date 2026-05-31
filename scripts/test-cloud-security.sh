#!/usr/bin/env bash
# Tests grc-claw-cloud-security-integration skill
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TOKEN="${GRC_CLAW_GATEWAY_TOKEN:-grc-test-token}"
BASE="${GRC_CLAW_BASE:-http://127.0.0.1:18791}"

echo "═══════════════════════════════════════════════════════════"
echo " GRC_Claw Cloud Security Integration Tests"
echo " Skill: grc-claw-cloud-security-integration"
echo "═══════════════════════════════════════════════════════════"

npm run build
npm run test -w @grc-claw/ingest

lsof -ti :18791 | xargs kill -9 2>/dev/null || true
sleep 1
GRC_CLAW_GATEWAY_TOKEN="$TOKEN" A2Z_SOC_MODE=demo node packages/gateway/dist/cli.js &
GW_PID=$!
trap 'kill "$GW_PID" 2>/dev/null || true' EXIT
sleep 2

pass=0
fail=0
assert() {
  local name="$1" pat="$2" hay="$3"
  if echo "$hay" | grep -qE "$pat"; then echo "  ✓ $name"; pass=$((pass+1)); else echo "  ✗ $name"; fail=$((fail+1)); fi
}

H=$(curl -s "$BASE/health")
assert "health: cloud_security_integration" 'cloud_security_integration":true' "$H"
assert "health lists azure_sentinel" 'azure_sentinel' "$H"

# AWS GuardDuty (EventBridge shape)
GD='{"detail":{"id":"gd-test-1","severity":7.2,"type":"UnauthorizedAccess:IAMUser"}}'
GD_RES=$(curl -s -X POST "$BASE/api/ingest/normalize" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d "{\"source\":\"aws_guardduty\",\"tenantId\":1,\"payload\":$GD}")
assert "AWS GuardDuty → aws_guardduty" '"sourceSystem":"aws_guardduty"' "$GD_RES"
assert "GuardDuty critical" '"severity":"critical"' "$GD_RES"
assert "identity.compromise → GRC controls" 'iso-a.5.16' "$GD_RES"

# Azure Sentinel
SENT='{"properties":{"severity":"High","title":"Suspicious sign-in"}}'
SENT_RES=$(curl -s -X POST "$BASE/api/ingest/normalize" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d "{\"source\":\"azure_sentinel\",\"tenantId\":1,\"payload\":$SENT}")
assert "Azure Sentinel" '"sourceSystem":"azure_sentinel"' "$SENT_RES"
assert "Sentinel auth.failure mapping" 'auth.failure' "$SENT_RES"

# GCP Chronicle
CHR='{"security_result":[{"severity":"HIGH","summary":"Suspicious egress"}],"principal":{"ip":["10.0.0.8"]}}'
CHR_RES=$(curl -s -X POST "$BASE/api/ingest/normalize" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d "{\"source\":\"gcp_chronicle\",\"tenantId\":1,\"payload\":$CHR}")
assert "GCP Chronicle" '"sourceSystem":"gcp_chronicle"' "$CHR_RES"

# SOAR: Sentinel playbook blocked without approval
code=$(curl -s -o /tmp/grc-sent-soar.json -w "%{http_code}" -X POST "$BASE/api/agent/invoke" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"cloud","tool":"sentinel.run_playbook","args":{"playbookId":"isolate-vm"}}')
assert "Sentinel SOAR destructive 403" '^403$' "$code"
assert "destructive_requires_approval" 'destructive_requires_approval' "$(cat /tmp/grc-sent-soar.json)"

# SOAR: read allowed
R=$(curl -s -X POST "$BASE/api/agent/invoke" -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"cloud","tool":"sentinel.get_incident","args":{"id":"1"}}')
assert "sentinel.get_incident read" '"allowed":true' "$R"

echo ""
echo "Integration: $pass passed, $fail failed"
exit "$fail"
