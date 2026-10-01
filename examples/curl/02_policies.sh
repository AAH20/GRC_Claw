#!/bin/bash
# GRC_Claw cURL Examples - Policy Management
# ===========================================

BASE_URL="${GRC_BASE_URL:-https://api.grc-claw.io}"
API_KEY="${GRC_API_KEY:-grc_live_abc123...}"
TENANT_ID="${GRC_TENANT_ID:-org-acme}"

# --- List Policies ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/policies?limit=50" | jq .

# --- List Policies with Filters ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/policies?status=active&category=privacy&limit=50" | jq .

# --- Create Policy ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "policy_key": "AI-ETHICS-001",
       "name": "Data Access Control Policy",
       "category": "privacy",
       "description": "Controls access to sensitive data by AI agents",
       "framework_tags": ["NIST-800-53", "SOC2"],
       "cedar_policy": "permit(principal, action, resource) when { principal.role == \"analyst\" };"
     }' \
     "${BASE_URL}/v1.0/policies" | jq .

# --- Get Policy ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/policies/pol-001" | jq .

# --- Update Policy ---
curl -s -X PUT \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Data Access Control Policy v2",
       "description": "Updated with stricter controls"
     }' \
     "${BASE_URL}/v1.0/policies/pol-001" | jq .

# --- Delete Policy ---
curl -s -X DELETE \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/policies/pol-001?force=true" -w "\nHTTP Status: %{http_code}\n"

# --- Compile Policy ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/policies/pol-001/compile" | jq .

# --- Dry Run Policy ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "test_inputs": [
         {"principal": {"role": "analyst"}, "action": "read", "resource": {"classification": "public"}},
         {"principal": {"role": "intern"}, "action": "read", "resource": {"classification": "confidential"}}
       ]
     }' \
     "${BASE_URL}/v1.0/policies/pol-001/dry-run" | jq .

# --- Get Policy Versions ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/policies/pol-001/versions" | jq .

# --- Get Policy Dependencies ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/policies/pol-001/dependencies" | jq .
