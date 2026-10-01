#!/bin/bash
# GRC_Claw cURL Examples - Evidence Management
# ============================================

BASE_URL="${GRC_BASE_URL:-https://api.grc-claw.io}"
API_KEY="${GRC_API_KEY:-grc_live_abc123...}"
TENANT_ID="${GRC_TENANT_ID:-org-acme}"

# --- Search Evidence ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/evidence?limit=50" | jq .

# --- Search Evidence with Filters ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/evidence?policy_id=pol-001&evidence_type=artifact&framework=NIST-800-53" | jq .

# --- Submit Evidence ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "source": {"type": "automated_scan", "system": "nessus", "collection_method": "api"},
       "evidence_type": "artifact",
       "content": {"format": "application/json", "data": "{\"scan_id\": \"scan-123\"}"},
       "policy_id": "pol-001",
       "assessment_id": "asm-001",
       "context": {"environment": "production", "region": "us-east-1"},
       "control_mapping": {"control_id": "AC-2", "framework": "NIST-800-53"}
     }' \
     "${BASE_URL}/v1.0/evidence" | jq .

# --- Get Evidence ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/evidence/evd-001" | jq .

# --- Verify Evidence ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/evidence/evd-001/verify" | jq .

# --- Export Evidence Package ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "framework": "NIST-800-53",
       "time_range": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-31T23:59:59Z"},
       "format": "json",
       "include_chain_of_custody": true
     }' \
     "${BASE_URL}/v1.0/evidence/export" | jq .

# --- Get Export Status ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/evidence/export/pkg-001" | jq .
