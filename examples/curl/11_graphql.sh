#!/bin/bash
# GRC_Claw cURL Examples - GraphQL
# ================================

BASE_URL="${GRC_BASE_URL:-https://api.grc-claw.io}"
API_KEY="${GRC_API_KEY:-grc_live_abc123...}"
TENANT_ID="${GRC_TENANT_ID:-org-acme}"

# --- GraphQL Query ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "query GetPolicies($limit: Int!) { policies(limit: $limit) { id name status version category } }",
       "variables": {"limit": 10}
     }' \
     "${BASE_URL}/v1.0/graphql" | jq .

# --- GraphQL Mutation ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "mutation CreatePolicy($input: PolicyInput!) { createPolicy(input: $input) { id name status } }",
       "variables": {"input": {"name": "New Policy", "category": "privacy"}}
     }' \
     "${BASE_URL}/v1.0/graphql" | jq .
