#!/bin/bash
# GRC_Claw cURL Examples - Webhook Subscriptions
# ==============================================

BASE_URL="${GRC_BASE_URL:-https://api.grc-claw.io}"
API_KEY="${GRC_API_KEY:-grc_live_abc123...}"
TENANT_ID="${GRC_TENANT_ID:-org-acme}"

# --- List Subscriptions ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/webhooks/subscriptions" | jq .

# --- Create Subscription ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://example.com/webhooks/grc-claw",
       "events": ["policy.created", "policy.updated", "enforcement.decision"],
       "secret": "whsec_my_webhook_secret",
       "description": "Production webhook",
       "active": true
     }' \
     "${BASE_URL}/v1.0/webhooks/subscriptions" | jq .

# --- Get Subscription ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/webhooks/subscriptions/sub-001" | jq .

# --- Update Subscription ---
curl -s -X PUT \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "events": ["policy.created", "policy.updated", "enforcement.decision", "evidence.verified"]
     }' \
     "${BASE_URL}/v1.0/webhooks/subscriptions/sub-001" | jq .

# --- Test Subscription ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/webhooks/subscriptions/sub-001/test" | jq .

# --- Get Delivery History ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/webhooks/subscriptions/sub-001/deliveries" | jq .

# --- Delete Subscription ---
curl -s -X DELETE \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/webhooks/subscriptions/sub-001" -w "\nHTTP Status: %{http_code}\n"
