#!/bin/bash
# GRC_Claw cURL Examples - Assessment Management
# ===============================================

BASE_URL="${GRC_BASE_URL:-https://api.grc-claw.io}"
API_KEY="${GRC_API_KEY:-grc_live_abc123...}"
TENANT_ID="${GRC_TENANT_ID:-org-acme}"

# --- List Assessments ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/assessments?limit=50" | jq .

# --- Create Assessment ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "assessment_key": "RISK-2024-Q1",
       "title": "Q1 2024 Risk Assessment",
       "assessment_type": "risk",
       "target_id": "org-acme",
       "target_type": "organization",
       "description": "Quarterly risk assessment",
       "methodology": "NIST RMF",
       "lead_assessor": "security-team"
     }' \
     "${BASE_URL}/v1.0/assessments" | jq .

# --- Get Assessment ---
curl -s -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     "${BASE_URL}/v1.0/assessments/asm-001" | jq .

# --- Update Assessment ---
curl -s -X PUT \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "status": "in_progress",
       "score": 85.0,
       "risk_level": "medium"
     }' \
     "${BASE_URL}/v1.0/assessments/asm-001" | jq .

# --- Add Finding ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "finding_key": "FIND-001",
       "title": "Unrestricted data access",
       "severity": "high",
       "category": "access_control",
       "description": "Agent has access to confidential data",
       "policy_id": "pol-001",
       "evidence_ids": ["evd-001"],
       "remediation": "Implement RBAC",
       "due_date": "2024-02-15T00:00:00Z"
     }' \
     "${BASE_URL}/v1.0/assessments/asm-001/findings" | jq .

# --- Generate Report ---
curl -s -X POST \
     -H "Authorization: Bearer ${API_KEY}" \
     -H "X-Tenant-ID: ${TENANT_ID}" \
     -H "Content-Type: application/json" \
     -d '{
       "format": "pdf",
       "include_evidence": true,
       "include_remediation": true
     }' \
     "${BASE_URL}/v1.0/assessments/asm-001/report" | jq .
