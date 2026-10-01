#!/bin/bash
# GRC_Claw cURL Examples - Composed/Aggregated APIs
# ==================================================

BASE_URL="${GRC_BASE_URL:-https://api.grc-claw.io}"
API_KEY="${GRC_API_KEY:-grc_live_abc123...}"
TENANT_ID="${GRC_TENANT_ID:-org-acme}"

# --- Dashboard Overview ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/composed/dashboard" | jq .

# --- Agent 360 View ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/composed/agents/agent-1/360" | jq .

# --- Compliance Report ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/composed/compliance-report" | jq .

# --- Executive Summary ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/composed/executive-summary" | jq .
