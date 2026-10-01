#!/bin/bash
# GRC_Claw cURL Examples - Audit Trail
# =====================================

BASE_URL="${GRC_BASE_URL:-https://api.grc-claw.io}"
API_KEY="${GRC_API_KEY:-grc_live_abc123...}"
TENANT_ID="${GRC_TENANT_ID:-org-acme}"

# --- Query Audit Trail ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/audit?limit=100" | jq .

# --- Query with Filters ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/audit?event_type=policy.created&actor_id=user-123&limit=100" | jq .

# --- Verify Audit Chain ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "from_event_id": "evt-001",
       "to_event_id": "evt-100"
     }' \
     "${BASE_URL}/v1.0/audit/verify" | jq .
