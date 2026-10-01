#!/bin/bash
# GRC_Claw cURL Examples - Enforcement Decisions
# ==============================================

BASE_URL="${GRC_BASE_URL:-https://api.grc-claw.io}"
API_KEY="${GRC_API_KEY:-grc_live_abc123...}"
TENANT_ID="${GRC_TENANT_ID:-org-acme}"

# --- Single Decision ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "agent_id": "agent-42",
       "action": "read",
       "resource": "s3://data/public/dataset.csv",
       "context": {"environment": "production"},
       "policy_ids": ["pol-001"],
       "include_evidence": true
     }' \
     "${BASE_URL}/v1.0/enforcement/decide" | jq .

# --- Batch Decision ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "decisions": [
         {"agent_id": "agent-1", "action": "read", "resource": "s3://bucket/file1.csv"},
         {"agent_id": "agent-2", "action": "write", "resource": "s3://bucket/file2.csv"}
       ]
     }' \
     "${BASE_URL}/v1.0/enforcement/decide-batch" | jq .

# --- Get Decision ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/enforcement/decisions/dec-001" | jq .

# --- List Decisions ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/enforcement/decisions?agent_id=agent-42&limit=50" | jq .
