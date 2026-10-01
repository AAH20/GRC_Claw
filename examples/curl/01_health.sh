#!/bin/bash
# GRC_Claw cURL Examples - System & Health
# =========================================

BASE_URL="${GRC_BASE_URL:-https://api.grc-claw.io}"
API_KEY="${GRC_API_KEY:-grc_live_abc123...}"
TENANT_ID="${GRC_TENANT_ID:-org-acme}"

# --- Health Check ---
curl -s "${BASE_URL}/health" | jq .

# --- Readiness Check ---
curl -s "${BASE_URL}/ready" | jq .

# --- Prometheus Metrics ---
curl -s -H "Authorization: Bearer ${API_KEY}" "${BASE_URL}/metrics"
