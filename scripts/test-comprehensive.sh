#!/usr/bin/env bash
# Comprehensive: ingest-oss-siem-ids-logs + netsec-grc-architecture + agentic AI
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TOKEN="${GRC_CLAW_GATEWAY_TOKEN:-grc-test-token}"
BASE="${GRC_CLAW_BASE:-http://127.0.0.1:18791}"

echo "═══════════════════════════════════════════════════════════"
echo " GRC_Claw Comprehensive Test Suite"
echo " Skills: ingest-oss-siem-ids-logs | netsec-grc-architecture | iso-42001-aims | cloud-security"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "▶ Phase 1: Unit tests (ingest, aims, agent, GRC, architecture)"
npm run build
npm run test -w @grc-claw/ingest
npm run test -w @grc-claw/aims
UNIT_EXIT=$?
echo ""

echo "▶ Phase 2: Gateway integration (daemon + A2Z bridge + ingest API)"
lsof -ti :18791 | xargs kill -9 2>/dev/null || true
sleep 1
echo "  Starting gateway (fresh build)..."
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

# --- ingest-oss-siem-ids-logs: live normalize endpoint ---
SURICATA='{"timestamp":"2026-05-31T12:00:00Z","event_type":"alert","src_ip":"10.1.1.1","dest_ip":"10.2.2.2","alert":{"signature_id":99,"signature":"ET TEST","severity":1}}'
NORM=$(curl -s -X POST "$BASE/api/ingest/normalize" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d "{\"source\":\"suricata\",\"tenantId\":1,\"payload\":$SURICATA}")
assert "ingest API: Suricata → canonical" '"sourceSystem":"suricata"' "$NORM"
assert "ingest API: network.intrusion" 'network.intrusion' "$NORM"
assert "ingest API: maps to ISO monitoring control" 'iso-a.8.16' "$NORM"

WAZUH='{"rule":{"id":5710,"level":12,"description":"SSH brute force"},"data":{"srcip":"203.0.113.5","dstip":"192.168.0.1"}}'
NW=$(curl -s -X POST "$BASE/api/ingest/normalize" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d "{\"source\":\"wazuh\",\"tenantId\":1,\"payload\":$WAZUH}")
assert "ingest API: Wazuh critical severity" '"severity":"critical"' "$NW"
assert "ingest API: Wazuh → access controls" 'iso-a.8.15' "$NW"

UFW_LINE='[UFW BLOCK] IN=eth0 OUT= MAC= SRC=198.18.0.1 DST=10.0.0.5 LEN=40 PROTO=TCP DPT=22'
UFW_BODY=$(node -e 'console.log(JSON.stringify({source:"ufw",tenantId:1,payload:process.argv[1]}))' "$UFW_LINE")
UFW_RES=$(curl -s -X POST "$BASE/api/ingest/normalize" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d "$UFW_BODY")
assert "ingest API: UFW firewall.block" 'firewall.block' "$UFW_RES"
assert "ingest API: UFW source IP" '198.18.0.1' "$UFW_RES"

# --- netsec-grc-architecture: gateway auth + idempotency ---
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/ingest/normalize" \
  -H "X-GRC-Claw-Token: bad" -H "Content-Type: application/json" \
  -d '{"source":"snort","tenantId":1,"payload":{}}')
assert "architecture: fail closed auth (401)" '^401$' "$code"

A=$(curl -s -X POST "$BASE/api/agent/invoke" -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"comp","tool":"soc.query_events","args":{}}')
assert "agentic AI: SOC read tool allowed" '"allowed":true' "$A"

D=$(curl -s -o /tmp/grc-comp-d.json -w "%{http_code}" -X POST "$BASE/api/agent/invoke" \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"sessionId":"comp","tool":"soar.run_playbook","args":{}}')
assert "agentic AI: SOAR destructive 403" '^403$' "$D"

S=$(curl -s -X POST "$BASE/api/a2z/sync" -H "X-GRC-Claw-Token: $TOKEN")
assert "A2Z SOC bridge: demo sync" '"processed":2' "$S"

HEALTH=$(curl -s "$BASE/health")
assert "ISO 42001: health iso_42001_aims" '"iso_42001_aims":true' "$HEALTH"
AIMS=$(curl -s "$BASE/api/aims/technical-controls")
assert "ISO 42001: technical-controls TC-01" 'TC-01' "$AIMS"
GAPS=$(curl -s "$BASE/api/aims/vendor-gaps?vendor=openai")
assert "ISO 42001: OpenAI vendor gaps" '"vendor":"openai"' "$GAPS"
FW=$(curl -s "$BASE/api/frameworks")
assert "ISO 42001: iso42001 framework pack" '"code":"iso42001"' "$FW"

echo ""
echo "▶ Phase 3: Cloud security (grc-claw-cloud-security-integration)"
CLOUD_EXIT=0
bash scripts/test-cloud-security.sh || CLOUD_EXIT=$?

echo ""
echo "═══════════════════════════════════════════════════════════"
if [[ $UNIT_EXIT -ne 0 ]]; then
  echo " Unit tests: FAILED"
  exit 1
fi
echo " Unit tests: PASSED"
echo " Integration (phase 2): $pass passed, $fail failed"
if [[ ${CLOUD_EXIT:-1} -ne 0 ]]; then
  echo " Cloud integration: FAILED"
  exit 1
fi
echo " Cloud integration: PASSED"
echo "═══════════════════════════════════════════════════════════"
exit "$fail"
