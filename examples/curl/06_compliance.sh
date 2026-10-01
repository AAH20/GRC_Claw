#!/bin/bash
# GRC_Claw cURL Examples - Compliance Management
# ===============================================

BASE_URL="${GRC_BASE_URL:-https://api.grc-claw.io}"
API_KEY="${GRC_API_KEY:-grc_live_abc123...}"
TENANT_ID="${GRC_TENANT_ID:-org-acme}"

# --- List Frameworks ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/compliance/frameworks" | jq .

# --- List Controls ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/compliance/frameworks/fw-001/controls" | jq .

# --- Get Compliance Posture ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/compliance/posture?framework=NIST-800-53&target_id=org-acme&target_type=organization" | jq .

# --- Create Mapping ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "control_id": "ctrl-001",
       "mapping_type": "policy",
       "coverage": "full",
       "policy_id": "pol-001",
       "notes": "Policy fully covers this control"
     }' \
     "${BASE_URL}/v1.0/compliance/mappings" | jq .

# --- Crosswalk ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/compliance/crosswalk?control_id=ctrl-001&framework=NIST-800-53&target_framework=SOC2" | jq .

# --- Generate Compliance Report ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "framework": "NIST-800-53",
       "time_range": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-31T23:59:59Z"},
       "format": "json",
       "include_evidence": true,
       "include_gaps": true
     }' \
     "${BASE_URL}/v1.0/compliance/reports" | jq .
