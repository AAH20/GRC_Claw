#!/bin/bash
# GRC_Claw cURL Examples - Agent Registry
# ========================================

BASE_URL="${GRC_BASE_URL:-https://api.grc-claw.io}"
API_KEY="${GRC_API_KEY:-grc_live_abc123...}"
TENANT_ID="${GRC_TENANT_ID:-org-acme}"

# --- List Agents ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/agents?limit=50" | jq .

# --- Register Agent ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Data Analyst Agent",
       "type": "agent",
       "framework": "langchain",
       "risk_tier": "limited",
       "owner": "data-team",
       "capabilities": [
         {"name": "read_data", "permissions": ["s3:GetObject"], "resource_scope": "s3://data/public/*"}
       ]
     }' \
     "${BASE_URL}/v1.0/agents" | jq .

# --- Get Agent ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/agents/agent-1" | jq .

# --- Update Agent ---
curl -s -X PUT \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "lifecycle_stage": "active",
       "risk_tier": "minimal"
     }' \
     "${BASE_URL}/v1.0/agents/agent-1" | jq .

# --- Update Trust Score ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "value": 85,
       "grade": "B",
       "reason": "Completed security review"
     }' \
     "${BASE_URL}/v1.0/agents/agent-1/trust-score" | jq .

# --- Bind Policies ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "policy_ids": ["pol-001", "pol-002"]
     }' \
     "${BASE_URL}/v1.0/agents/agent-1/policy-bindings" | jq .
