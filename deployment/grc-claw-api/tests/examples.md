# GRC_Claw API Examples

Complete request/response examples for all 54 endpoints.

**Base URL:** `http://localhost:8080`
**API Version:** 1.0.0
**Content-Type:** `application/json`

---

## Authentication

All endpoints (except `/health`, `/ready`, `/metrics`) require authentication via Bearer token:

```
Authorization: Bearer grc_test_your_api_key_here
```

---

## System

### GET /health

**Request:**
```bash
curl -X GET http://localhost:8080/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "api": { "status": "up" },
    "policy_engine": { "status": "up" },
    "evidence_store": { "status": "up" },
    "database": { "status": "up" },
    "cache": { "status": "up" }
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### GET /ready

**Request:**
```bash
curl -X GET http://localhost:8080/ready
```

**Response (200):**
```json
{
  "ready": true,
  "checks": {
    "database": { "status": "pass" },
    "policy_engine": { "status": "pass" },
    "evidence_store": { "status": "pass" }
  }
}
```

### GET /metrics

**Request:**
```bash
curl -X GET http://localhost:8080/metrics
```

**Response (200):**
```
grc_api_requests_total{method="GET",endpoint="/v1.0/agents",status="200"} 1523
grc_api_request_duration_seconds_bucket{method="GET",endpoint="/v1.0/agents",le="0.1"} 1200
grc_api_enforcement_decisions_total{verdict="ALLOW",policy_id="pol-001"} 14850
```

---

## Agents

### GET /v1.0/agents

**Request:**
```bash
curl -X GET "http://localhost:8080/v1.0/agents?limit=50&type=agent&framework=langchain" \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "agent-1",
      "name": "Data Analyst Agent",
      "type": "agent",
      "framework": "langchain",
      "owner": "team-data",
      "lifecycle_stage": "active",
      "risk_tier": "limited",
      "capabilities": [
        {
          "name": "read_data",
          "description": "Read data from approved sources",
          "permissions": ["data:read"],
          "resource_scope": "s3://grc-data/*"
        }
      ],
      "identity": null,
      "trust_score": {
        "value": 85,
        "grade": "B",
        "last_evaluated": "2025-01-15T10:00:00Z"
      },
      "policy_bindings": ["pol-001"],
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": "50",
    "has_next": true,
    "total": 125
  }
}
```

### POST /v1.0/agents

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/agents \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Agent",
    "type": "agent",
    "framework": "langchain",
    "owner": "team-ml",
    "risk_tier": "limited",
    "capabilities": [
      {
        "name": "analyze_data",
        "permissions": ["data:read", "data:analyze"]
      }
    ]
  }'
```

**Response (201):**
```json
{
  "id": "agent-2",
  "name": "New Agent",
  "type": "agent",
  "framework": "langchain",
  "owner": "team-ml",
  "lifecycle_stage": "proposed",
  "risk_tier": "limited",
  "capabilities": [
    {
      "name": "analyze_data",
      "permissions": ["data:read", "data:analyze"]
    }
  ],
  "identity": null,
  "trust_score": null,
  "policy_bindings": [],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### GET /v1.0/agents/{agent_id}

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/agents/agent-1 \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "id": "agent-1",
  "name": "Data Analyst Agent",
  "type": "agent",
  "framework": "langchain",
  "owner": "team-data",
  "lifecycle_stage": "active",
  "risk_tier": "limited",
  "capabilities": [],
  "identity": null,
  "trust_score": {
    "value": 85,
    "grade": "B",
    "last_evaluated": "2025-01-15T10:00:00Z"
  },
  "policy_bindings": ["pol-001"],
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### PUT /v1.0/agents/{agent_id}

**Request:**
```bash
curl -X PUT http://localhost:8080/v1.0/agents/agent-1 \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "lifecycle_stage": "active",
    "risk_tier": "high"
  }'
```

**Response (200):**
```json
{
  "id": "agent-1",
  "name": "Data Analyst Agent",
  "type": "agent",
  "framework": "langchain",
  "owner": "team-data",
  "lifecycle_stage": "active",
  "risk_tier": "high",
  "capabilities": [],
  "identity": null,
  "trust_score": null,
  "policy_bindings": [],
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

### POST /v1.0/agents/{agent_id}/trust-score

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/agents/agent-1/trust-score \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "value": 92,
    "grade": "A",
    "reason": "Quarterly evaluation - all checks passed"
  }'
```

**Response (200):**
```json
{
  "id": "agent-1",
  "trust_score": {
    "value": 92,
    "grade": "A",
    "last_evaluated": "2025-01-15T11:00:00Z"
  },
  "updated_at": "2025-01-15T11:00:00Z"
}
```

### POST /v1.0/agents/{agent_id}/policy-bindings

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/agents/agent-1/policy-bindings \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_ids": ["pol-001", "pol-002", "pol-003"]
  }'
```

**Response (200):**
```json
{
  "id": "agent-1",
  "policy_bindings": ["pol-001", "pol-002", "pol-003"],
  "updated_at": "2025-01-15T11:00:00Z"
}
```

---

## Policies

### GET /v1.0/policies

**Request:**
```bash
curl -X GET "http://localhost:8080/v1.0/policies?status=active&category=safety" \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "pol-001",
      "policy_key": "DATA-ACCESS-001",
      "name": "Data Access Control",
      "description": "Controls access to sensitive data stores",
      "category": "safety",
      "status": "active",
      "version": "2.1.0",
      "framework_tags": ["NIST-800-53", "SOC2"],
      "effective_date": "2025-01-01T00:00:00Z",
      "expiry_date": null,
      "owner_id": "user-1",
      "agent_bindings": ["agent-1"],
      "cedar_policy": "permit(principal, action, resource) when { ... };",
      "rego_policy": "package grc.agent.pol-001\n...",
      "metadata": {},
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-10T00:00:00Z",
      "created_by": "user-1",
      "updated_by": "user-1"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_next": false,
    "total": 1
  }
}
```

### POST /v1.0/policies

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/policies \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_key": "ETHICS-001",
    "name": "AI Ethics Policy",
    "description": "Ensures ethical AI behavior",
    "category": "ethics",
    "framework_tags": ["ISO-42001"],
    "cedar_policy": "permit(principal, action, resource) when { principal.verified };"
  }'
```

**Response (201):**
```json
{
  "id": "pol-003",
  "policy_key": "ETHICS-001",
  "name": "AI Ethics Policy",
  "description": "Ensures ethical AI behavior",
  "category": "ethics",
  "status": "draft",
  "version": "1.0.0",
  "framework_tags": ["ISO-42001"],
  "effective_date": null,
  "expiry_date": null,
  "owner_id": "test-suite",
  "agent_bindings": [],
  "cedar_policy": "permit(principal, action, resource) when { principal.verified };",
  "rego_policy": null,
  "metadata": {},
  "created_at": "2025-01-15T11:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z",
  "created_by": "test-suite",
  "updated_by": "test-suite"
}
```

### GET /v1.0/policies/{policy_id}

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/policies/pol-001 \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "id": "pol-001",
  "policy_key": "DATA-ACCESS-001",
  "name": "Data Access Control",
  "category": "safety",
  "status": "active",
  "version": "2.1.0"
}
```

### PUT /v1.0/policies/{policy_id}

**Request:**
```bash
curl -X PUT http://localhost:8080/v1.0/policies/pol-001 \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Access Control v3",
    "description": "Updated description"
  }'
```

**Response (200):**
```json
{
  "id": "pol-001",
  "name": "Data Access Control v3",
  "version": "2.2.0",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

### DELETE /v1.0/policies/{policy_id}

**Request:**
```bash
curl -X DELETE "http://localhost:8080/v1.0/policies/pol-003?force=false" \
  -H "Authorization: Bearer grc_test_key"
```

**Response (204):**
```
No content
```

### POST /v1.0/policies/{policy_id}/compile

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/policies/pol-001/compile \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "policy_id": "pol-001",
  "compilation_status": "success",
  "rego_policy": "package grc.agent.pol-001\n\nimport future.keywords.if\nimport future.keywords.in\n\ndefault allow := false\n\nallow if {\n    # Compiled from Cedar policy\n    # Source: permit(principal, action, resource) when { ... };\n}",
  "warnings": [],
  "errors": [],
  "compiled_at": "2025-01-15T11:00:00Z"
}
```

### POST /v1.0/policies/{policy_id}/dry-run

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/policies/pol-001/dry-run \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "test_inputs": [
      {
        "principal": {"id": "agent-1", "type": "agent"},
        "action": "read",
        "resource": {"id": "data-1", "type": "data"},
        "context": {"environment": "production"}
      }
    ]
  }'
```

**Response (200):**
```json
{
  "policy_id": "pol-001",
  "dry_run_results": [
    {
      "input_index": 0,
      "decision": "ALLOW",
      "matched_rules": ["allow_read_public"],
      "evaluation_time_ms": 2.0,
      "reason": null
    }
  ],
  "summary": {
    "total": 1,
    "allowed": 1,
    "denied": 0,
    "avg_evaluation_time_ms": 2.0
  }
}
```

### GET /v1.0/policies/{policy_id}/versions

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/policies/pol-001/versions \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
[
  {
    "version": "2.1.0",
    "status": "active",
    "change_summary": "Current version",
    "created_at": "2025-01-10T00:00:00Z",
    "created_by": "user-1"
  },
  {
    "version": "1.0.0",
    "status": "superseded",
    "change_summary": "Initial policy creation",
    "created_at": "2025-01-01T00:00:00Z",
    "created_by": "user-1"
  }
]
```

### GET /v1.0/policies/{policy_id}/dependencies

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/policies/pol-001/dependencies \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "policy_id": "pol-001",
  "dependencies": [],
  "dependents": []
}
```

---

## Evidence

### GET /v1.0/evidence

**Request:**
```bash
curl -X GET "http://localhost:8080/v1.0/evidence?evidence_type=artifact&environment=production" \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "data": [
    {
      "evidence_id": "evd-001",
      "policy_id": "pol-001",
      "assessment_id": "asm-001",
      "source": {
        "type": "automated_scan",
        "system": "config-auditor",
        "collection_method": "api"
      },
      "evidence_type": "artifact",
      "content": {
        "format": "json",
        "data": "{\"compliant\": true}",
        "hash": "sha256:abc123..."
      },
      "context": {
        "environment": "production",
        "region": "us-east-1",
        "timestamp": "2025-01-15T10:00:00Z",
        "metadata": {}
      },
      "validation": {
        "status": "verified",
        "validated_by": "user-1",
        "validated_at": "2025-01-15T10:30:00Z",
        "confidence_score": 0.95
      },
      "verification_level": "L2",
      "chain_of_custody": [
        {
          "action": "collected",
          "actor": "system",
          "timestamp": "2025-01-15T10:00:00Z",
          "hash": "sha256:abc123..."
        }
      ],
      "retention_class": "standard",
      "created_at": "2025-01-15T10:00:00Z",
      "expires_at": "2026-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_next": false,
    "total": 1
  }
}
```

### POST /v1.0/evidence

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/evidence \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "pol-001",
    "source": {
      "type": "automated_scan",
      "system": "test-suite",
      "collection_method": "api"
    },
    "evidence_type": "artifact",
    "content": {
      "format": "json",
      "data": "{\"test\": true}"
    },
    "context": {
      "environment": "test",
      "region": "us-east-1"
    },
    "control_mapping": {
      "control_id": "AC-2",
      "framework": "NIST-800-53",
      "control_title": "Account Management"
    }
  }'
```

**Response (201):**
```json
{
  "evidence_id": "evd-002",
  "policy_id": "pol-001",
  "source": {
    "type": "automated_scan",
    "system": "test-suite",
    "collection_method": "api"
  },
  "evidence_type": "artifact",
  "content": {
    "format": "json",
    "data": "{\"test\": true}",
    "hash": "sha256:def456..."
  },
  "context": {
    "environment": "test",
    "region": "us-east-1",
    "timestamp": "2025-01-15T11:00:00Z",
    "metadata": {}
  },
  "validation": {
    "status": "pending",
    "validated_by": null,
    "validated_at": null,
    "confidence_score": 0.0
  },
  "verification_level": "L0",
  "chain_of_custody": [
    {
      "action": "collected",
      "actor": "test-suite",
      "timestamp": "2025-01-15T11:00:00Z",
      "hash": "sha256:def456..."
    }
  ],
  "retention_class": "standard",
  "created_at": "2025-01-15T11:00:00Z",
  "expires_at": "2026-01-15T11:00:00Z"
}
```

### GET /v1.0/evidence/{evidence_id}

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/evidence/evd-001 \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "evidence_id": "evd-001",
  "policy_id": "pol-001",
  "evidence_type": "artifact",
  "verification_level": "L2",
  "validation": {
    "status": "verified",
    "confidence_score": 0.95
  }
}
```

### POST /v1.0/evidence/{evidence_id}/verify

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/evidence/evd-001/verify \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "evidence_id": "evd-001",
  "verification_result": {
    "status": "verified",
    "verification_level": "L2",
    "hash_match": true,
    "chain_of_custody_intact": true,
    "schema_valid": true,
    "control_mapping_valid": true,
    "verified_at": "2025-01-15T11:00:00Z",
    "verified_by": "test-suite"
  }
}
```

### POST /v1.0/evidence/export

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/evidence/export \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "framework": "NIST-800-53",
    "time_range": {
      "from": "2025-01-01T00:00:00Z",
      "to": "2025-12-31T23:59:59Z"
    },
    "format": "json",
    "include_chain_of_custody": true
  }'
```

**Response (202):**
```json
{
  "package_id": "pkg-001",
  "status": "processing",
  "estimated_completion": "2025-01-15T11:05:00Z"
}
```

### GET /v1.0/evidence/export/{package_id}

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/evidence/export/pkg-001 \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "package_id": "pkg-001",
  "status": "completed",
  "download_url": "/v1.0/evidence/export/pkg-001/download",
  "expires_at": "2025-01-22T11:00:00Z",
  "package_hash": "sha256:ghi789...",
  "manifest": {
    "framework": "NIST-800-53",
    "controls_assessed": 42,
    "evidence_items": 156
  }
}
```

---

## Enforcement

### POST /v1.0/enforcement/decide

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/enforcement/decide \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-1",
    "action": "read",
    "resource": "s3://grc-data/dataset-1",
    "context": {"environment": "production"},
    "policy_ids": ["pol-001"],
    "include_evidence": true
  }'
```

**Response (200):**
```json
{
  "decision_id": "dec-001",
  "verdict": "ALLOW",
  "policy_id": "pol-001",
  "policy_version": "1.0.0",
  "agent_id": "agent-1",
  "action": "read",
  "resource": "s3://grc-data/dataset-1",
  "context": {"environment": "production"},
  "evidence_hash": "sha256:abc123...",
  "timestamp": "2025-01-15T11:00:00Z",
  "ttl": 300,
  "signature": "ecdsa-p256:def456...",
  "matched_rules": ["allow_read_public"],
  "evaluation_time_ms": 2.3,
  "reason": null
}
```

### POST /v1.0/enforcement/decide-batch

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/enforcement/decide-batch \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "decisions": [
      {
        "agent_id": "agent-1",
        "action": "read",
        "resource": "resource-1",
        "policy_ids": ["pol-001"]
      },
      {
        "agent_id": "agent-2",
        "action": "write",
        "resource": "resource-2",
        "policy_ids": ["pol-002"]
      }
    ]
  }'
```

**Response (200):**
```json
{
  "results": [
    {
      "decision_id": "dec-002",
      "verdict": "ALLOW",
      "policy_id": "pol-001",
      "evaluation_time_ms": 2.0,
      "reason": null
    },
    {
      "decision_id": "dec-003",
      "verdict": "ALLOW",
      "policy_id": "pol-002",
      "evaluation_time_ms": 2.0,
      "reason": null
    }
  ],
  "summary": {
    "total": 2,
    "allowed": 2,
    "denied": 0,
    "avg_evaluation_time_ms": 2.0
  }
}
```

### GET /v1.0/enforcement/decisions/{decision_id}

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/enforcement/decisions/dec-001 \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "decision_id": "dec-001",
  "verdict": "ALLOW",
  "policy_id": "pol-001",
  "agent_id": "agent-1",
  "action": "read",
  "resource": "s3://grc-data/dataset-1"
}
```

### GET /v1.0/enforcement/decisions

**Request:**
```bash
curl -X GET "http://localhost:8080/v1.0/enforcement/decisions?agent_id=agent-1&verdict=ALLOW" \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "data": [
    {
      "decision_id": "dec-001",
      "verdict": "ALLOW",
      "agent_id": "agent-1"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_next": false,
    "total": 1
  }
}
```

---

## Assessments

### GET /v1.0/assessments

**Request:**
```bash
curl -X GET "http://localhost:8080/v1.0/assessments?assessment_type=risk&status=planned" \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "data": [
    {
      "id": "asm-001",
      "assessment_key": "RISK-2025-001",
      "title": "Q1 2025 Risk Assessment",
      "description": "Quarterly risk assessment",
      "assessment_type": "risk",
      "target_id": "agent-1",
      "target_type": "agent",
      "status": "in_progress",
      "methodology": "NIST RMF",
      "score": 85.5,
      "risk_level": "medium",
      "started_at": "2025-01-10T00:00:00Z",
      "completed_at": null,
      "next_assessment_at": null,
      "lead_assessor": "assessor@company.com",
      "findings": [],
      "metadata": {},
      "created_at": "2025-01-05T00:00:00Z",
      "updated_at": "2025-01-10T00:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_next": false,
    "total": 1
  }
}
```

### POST /v1.0/assessments

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/assessments \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "assessment_key": "RISK-2025-002",
    "title": "Q2 2025 Risk Assessment",
    "assessment_type": "risk",
    "target_id": "agent-1",
    "target_type": "agent",
    "methodology": "NIST RMF",
    "lead_assessor": "assessor@company.com"
  }'
```

**Response (201):**
```json
{
  "id": "asm-002",
  "assessment_key": "RISK-2025-002",
  "title": "Q2 2025 Risk Assessment",
  "assessment_type": "risk",
  "target_id": "agent-1",
  "target_type": "agent",
  "status": "planned",
  "methodology": "NIST RMF",
  "score": null,
  "risk_level": null,
  "lead_assessor": "assessor@company.com",
  "findings": [],
  "metadata": {},
  "created_at": "2025-01-15T11:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

### GET /v1.0/assessments/{assessment_id}

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/assessments/asm-001 \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "id": "asm-001",
  "assessment_key": "RISK-2025-001",
  "title": "Q1 2025 Risk Assessment",
  "status": "in_progress",
  "score": 85.5,
  "risk_level": "medium"
}
```

### PUT /v1.0/assessments/{assessment_id}

**Request:**
```bash
curl -X PUT http://localhost:8080/v1.0/assessments/asm-001 \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "score": 90.0,
    "risk_level": "low"
  }'
```

**Response (200):**
```json
{
  "id": "asm-001",
  "status": "completed",
  "score": 90.0,
  "risk_level": "low",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

### POST /v1.0/assessments/{assessment_id}/findings

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/assessments/asm-001/findings \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "finding_key": "FND-001",
    "title": "Excessive permissions",
    "description": "Agent has permissions beyond its role",
    "severity": "high",
    "category": "access_control",
    "policy_id": "pol-001",
    "evidence_ids": ["evd-001"],
    "remediation": "Review and reduce permissions",
    "due_date": "2025-03-15T00:00:00Z"
  }'
```

**Response (200):**
```json
{
  "id": "asm-001",
  "findings": [
    {
      "id": "fnd-001",
      "finding_key": "FND-001",
      "title": "Excessive permissions",
      "severity": "high",
      "status": "open",
      "remediation": "Review and reduce permissions"
    }
  ],
  "updated_at": "2025-01-15T11:00:00Z"
}
```

### POST /v1.0/assessments/{assessment_id}/report

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/assessments/asm-001/report \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "pdf",
    "include_evidence": true,
    "include_remediation": true
  }'
```

**Response (200):**
```json
{
  "report_id": "rpt-asm-001-1705316400",
  "status": "processing",
  "format": "pdf",
  "estimated_completion": "2025-01-15T11:00:00Z"
}
```

---

## Compliance

### GET /v1.0/compliance/frameworks

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/compliance/frameworks \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
[
  {
    "id": "fw-001",
    "framework_key": "NIST-800-53",
    "name": "NIST SP 800-53 Rev 5",
    "version": "5",
    "description": "Security and Privacy Controls for Information Systems",
    "authority": "NIST",
    "effective_date": "2020-09-23T00:00:00Z",
    "control_count": 1026
  },
  {
    "id": "fw-002",
    "framework_key": "SOC2",
    "name": "SOC 2 Trust Services Criteria",
    "version": "2017",
    "description": "Trust Services Criteria",
    "authority": "AICPA",
    "effective_date": "2017-04-01T00:00:00Z",
    "control_count": 64
  }
]
```

### GET /v1.0/compliance/frameworks/{framework_id}/controls

**Request:**
```bash
curl -X GET "http://localhost:8080/v1.0/compliance/frameworks/fw-001/controls?category=Access%20Control" \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
[
  {
    "id": "ctrl-001",
    "framework_id": "fw-001",
    "control_key": "AC-1",
    "title": "Policy and Procedures",
    "description": "Control 1",
    "category": "Access Control"
  }
]
```

### GET /v1.0/compliance/posture

**Request:**
```bash
curl -X GET "http://localhost:8080/v1.0/compliance/posture?framework=NIST-800-53" \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "framework": "NIST-800-53",
  "target_id": "all-production",
  "target_type": "organization",
  "controls_assessed": 1026,
  "controls_compliant": 856,
  "controls_non_compliant": 120,
  "controls_not_assessed": 50,
  "compliance_score": 83.4,
  "gaps": [],
  "trend": {
    "direction": "improving",
    "change": "+2.3%",
    "period": "30d"
  }
}
```

### POST /v1.0/compliance/mappings

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/compliance/mappings \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "control_id": "AC-2",
    "policy_id": "pol-001",
    "assessment_id": "asm-001",
    "mapping_type": "automated",
    "coverage": "full",
    "notes": "Mapped via automated scan"
  }'
```

**Response (201):**
```json
{
  "id": "map-001",
  "control_id": "AC-2",
  "policy_id": "pol-001",
  "assessment_id": "asm-001",
  "mapping_type": "automated",
  "coverage": "full",
  "notes": "Mapped via automated scan",
  "mapped_by": "test-suite",
  "mapped_at": "2025-01-15T11:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

### POST /v1.0/compliance/reports

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/compliance/reports \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "framework": "NIST-800-53",
    "time_range": {
      "from": "2025-01-01T00:00:00Z",
      "to": "2025-12-31T23:59:59Z"
    },
    "format": "json",
    "include_evidence": true,
    "include_gaps": true
  }'
```

**Response (200):**
```json
{
  "report_id": "rpt-1705316400",
  "status": "processing",
  "format": "json",
  "estimated_completion": "2025-01-15T11:00:00Z"
}
```

### GET /v1.0/compliance/crosswalk

**Request:**
```bash
curl -X GET "http://localhost:8080/v1.0/compliance/crosswalk?control_id=ctrl-001" \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "grc_control_id": "ctrl-001",
  "mappings": {
    "nist_800_53": ["AC-2", "AC-3", "AC-6"],
    "soc2": ["CC6.1", "CC6.2", "CC6.3"],
    "iso_27001": ["A.12.4", "A.12.5"],
    "iso_42001": ["A.6", "A.9"],
    "gdpr": ["Art.5", "Art.25"],
    "hipaa": ["164.308(a)(1)", "164.312(b)"],
    "pci_dss": ["10.1", "10.2", "10.3"],
    "cobit": ["DSS06", "APO12"],
    "nist_ai_rmf": ["Govern", "Map", "Measure"],
    "eu_ai_act": ["Annex III", "Art.9"]
  }
}
```

---

## Audit

### GET /v1.0/audit

**Request:**
```bash
curl -X GET "http://localhost:8080/v1.0/audit?event_type=policy.created&limit=100" \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "data": [
    {
      "event_id": "evt-001",
      "event_type": "policy.created",
      "actor": {
        "type": "user",
        "id": "user-1",
        "name": "Admin User"
      },
      "resource": {
        "type": "policy",
        "id": "pol-001",
        "name": "Data Access Control"
      },
      "timestamp": "2025-01-15T10:00:00Z",
      "details": {},
      "integrity_hash": "sha256:abc123...",
      "previous_event_hash": "sha256:0000..."
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_next": false,
    "total": 1
  }
}
```

### POST /v1.0/audit/verify

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/audit/verify \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "from_event_id": null,
    "to_event_id": null
  }'
```

**Response (200):**
```json
{
  "verification_status": "valid",
  "events_verified": 150,
  "chain_intact": true,
  "first_event_id": "evt-001",
  "last_event_id": "evt-150",
  "verified_at": "2025-01-15T11:00:00Z"
}
```

---

## Webhooks

### GET /v1.0/webhooks/subscriptions

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/webhooks/subscriptions \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "data": [
    {
      "subscription_id": "sub-001",
      "url": "https://example.com/webhook",
      "events": ["policy.created", "enforcement.decision_made"],
      "secret": "whsec_...",
      "description": "Policy and enforcement notifications",
      "active": true,
      "metadata": {},
      "created_at": "2025-01-15T10:00:00Z",
      "delivery_stats": {
        "total_deliveries": 42,
        "successful_deliveries": 40,
        "failed_deliveries": 2,
        "last_delivery_at": "2025-01-15T10:30:00Z"
      }
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_next": false,
    "total": 1
  }
}
```

### POST /v1.0/webhooks/subscriptions

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/webhooks/subscriptions \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/webhook",
    "events": ["policy.created", "enforcement.decision_made"],
    "secret": "whsec_my_secret_key_1234567890",
    "description": "Policy and enforcement notifications",
    "active": true
  }'
```

**Response (201):**
```json
{
  "subscription_id": "sub-002",
  "url": "https://example.com/webhook",
  "events": ["policy.created", "enforcement.decision_made"],
  "secret": "whsec_my_secret_key_1234567890",
  "description": "Policy and enforcement notifications",
  "active": true,
  "metadata": {},
  "created_at": "2025-01-15T11:00:00Z",
  "delivery_stats": {
    "total_deliveries": 0,
    "successful_deliveries": 0,
    "failed_deliveries": 0,
    "last_delivery_at": null
  }
}
```

### GET /v1.0/webhooks/subscriptions/{subscription_id}

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/webhooks/subscriptions/sub-001 \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "subscription_id": "sub-001",
  "url": "https://example.com/webhook",
  "events": ["policy.created"],
  "active": true,
  "delivery_stats": {
    "total_deliveries": 42,
    "successful_deliveries": 40
  }
}
```

### PUT /v1.0/webhooks/subscriptions/{subscription_id}

**Request:**
```bash
curl -X PUT http://localhost:8080/v1.0/webhooks/subscriptions/sub-001 \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "active": false,
    "description": "Temporarily disabled"
  }'
```

**Response (200):**
```json
{
  "subscription_id": "sub-001",
  "active": false,
  "description": "Temporarily disabled"
}
```

### DELETE /v1.0/webhooks/subscriptions/{subscription_id}

**Request:**
```bash
curl -X DELETE http://localhost:8080/v1.0/webhooks/subscriptions/sub-002 \
  -H "Authorization: Bearer grc_test_key"
```

**Response (204):**
```
No content
```

### POST /v1.0/webhooks/subscriptions/{subscription_id}/test

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/webhooks/subscriptions/sub-001/test \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "subscription_id": "sub-001",
  "test_event_id": "evt-test-1705316400",
  "delivery_status": "delivered",
  "http_status": 200,
  "response_time_ms": 45.0,
  "delivered_at": "2025-01-15T11:00:00Z"
}
```

### GET /v1.0/webhooks/subscriptions/{subscription_id}/deliveries

**Request:**
```bash
curl -X GET "http://localhost:8080/v1.0/webhooks/subscriptions/sub-001/deliveries?status_filter=delivered" \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
[
  {
    "delivery_id": "del-001",
    "subscription_id": "sub-001",
    "event_id": "evt-test-1705316400",
    "event_type": "test",
    "status": "delivered",
    "http_status": 200,
    "response_time_ms": 45.0,
    "attempts": 1,
    "delivered_at": "2025-01-15T11:00:00Z",
    "next_retry_at": null
  }
]
```

---

## Composed

### GET /v1.0/composed/dashboard

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/composed/dashboard \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "compliance_summary": {
    "overall_score": 87.5,
    "frameworks": [
      {"name": "NIST-800-53", "score": 83.4, "status": "improving"},
      {"name": "SOC2", "score": 92.1, "status": "stable"},
      {"name": "ISO-42001", "score": 78.9, "status": "improving"}
    ],
    "trend": "improving",
    "change": "+2.3%"
  },
  "active_agents": {
    "total": 42,
    "by_risk_tier": {
      "minimal": 15,
      "limited": 20,
      "high": 5,
      "prohibited": 2
    },
    "avg_trust_score": 82.3
  },
  "recent_enforcements": {
    "total_24h": 15420,
    "allowed": 14850,
    "denied": 420,
    "require_approval": 150,
    "avg_evaluation_time_ms": 2.1
  },
  "open_findings": {
    "total": 23,
    "by_severity": {
      "critical": 2,
      "high": 8,
      "medium": 10,
      "low": 3
    },
    "overdue": 5
  },
  "risk_alerts": {
    "active": 7,
    "critical": 1,
    "high": 3,
    "medium": 3
  },
  "audit_stats": {
    "events_24h": 45230,
    "integrity_status": "valid",
    "last_verified": "2025-01-15T11:00:00Z"
  },
  "composed_at": "2025-01-15T11:00:00Z"
}
```

### GET /v1.0/composed/agents/{agent_id}/360

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/composed/agents/agent-1/360 \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "agent": {
    "id": "agent-1",
    "name": "Data Analyst Agent",
    "type": "agent",
    "framework": "langchain",
    "lifecycle_stage": "active",
    "risk_tier": "limited",
    "trust_score": {"value": 85, "grade": "B", "last_evaluated": "2025-01-15T10:00:00Z"}
  },
  "policies": [
    {"id": "pol-001", "name": "Data Access Control", "status": "active"},
    {"id": "pol-002", "name": "PII Handling", "status": "active"}
  ],
  "enforcements": {
    "total_24h": 150,
    "allowed": 140,
    "denied": 8,
    "require_approval": 2,
    "recent": []
  },
  "evidence": {
    "total_submitted": 45,
    "verified": 40,
    "pending": 5
  },
  "assessments": {
    "completed": 3,
    "in_progress": 1,
    "avg_score": 82.5
  },
  "compliance": {
    "NIST-800-53": 0.85,
    "SOC2": 0.92,
    "ISO-42001": 0.78
  },
  "risks": {
    "open": 2,
    "accepted": 1,
    "mitigated": 5
  },
  "audit_trail": {
    "events_7d": 320,
    "last_activity": "2025-01-15T10:00:00Z"
  }
}
```

### GET /v1.0/composed/compliance-report

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/composed/compliance-report \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "frameworks": [
    {
      "id": "fw-001",
      "name": "NIST SP 800-53 Rev 5",
      "score": 83.4,
      "status": "partially_compliant",
      "controls_assessed": 1026,
      "controls_compliant": 856,
      "controls_non_compliant": 120,
      "controls_not_assessed": 50
    }
  ],
  "evidence_summary": {
    "total_items": 156,
    "by_type": {
      "artifact": 45,
      "observation": 67,
      "interview": 12,
      "analysis": 20,
      "log": 12
    },
    "by_verification_level": {
      "L0": 0,
      "L1": 10,
      "L2": 120,
      "L3": 20,
      "L4": 6
    }
  },
  "findings": {
    "total": 23,
    "open": 15,
    "in_progress": 5,
    "resolved": 3
  },
  "gaps": [
    {
      "control_id": "AC-2",
      "title": "Account Management",
      "severity": "high",
      "framework": "NIST-800-53"
    }
  ],
  "trends": [
    {
      "framework": "NIST-800-53",
      "direction": "improving",
      "change": "+2.3%",
      "period": "30d"
    }
  ],
  "generated_at": "2025-01-15T11:00:00Z"
}
```

### GET /v1.0/composed/executive-summary

**Request:**
```bash
curl -X GET http://localhost:8080/v1.0/composed/executive-summary \
  -H "Authorization: Bearer grc_test_key"
```

**Response (200):**
```json
{
  "overall_compliance_score": 0.87,
  "framework_scores": {
    "NIST-800-53": 0.83,
    "SOC2": 0.92,
    "ISO-42001": 0.79,
    "GDPR": 0.88
  },
  "risk_posture": {
    "open_risks": 12,
    "critical_risks": 1,
    "high_risks": 4,
    "medium_risks": 5,
    "low_risks": 2,
    "trend": "improving"
  },
  "agent_governance": {
    "total_agents": 42,
    "active_agents": 35,
    "high_risk_agents": 7,
    "avg_trust_score": 82.3,
    "agents_under_review": 3
  },
  "recent_activity": {
    "enforcements_24h": 15420,
    "evidence_collected_24h": 230,
    "policies_updated_7d": 5,
    "assessments_completed_30d": 12
  },
  "open_items": {
    "critical_findings": 2,
    "overdue_remediations": 5,
    "pending_approvals": 15,
    "expiring_evidence": 8
  },
  "generated_at": "2025-01-15T11:00:00Z"
}
```

---

## GraphQL

### POST /v1.0/graphql

**Request:**
```bash
curl -X POST http://localhost:8080/v1.0/graphql \
  -H "Authorization: Bearer grc_test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ agents { id name type riskTier } }"
  }'
```

**Response (200):**
```json
{
  "data": {
    "agents": [
      {
        "id": "agent-1",
        "name": "Data Analyst Agent",
        "type": "agent",
        "riskTier": "limited"
      }
    ]
  }
}
```

---

## Error Responses

All endpoints return consistent error format:

### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Missing or invalid Authorization header.",
  "code": "UNAUTHORIZED"
}
```

### 403 Forbidden
```json
{
  "error": "forbidden",
  "message": "Insufficient scope. Required: policies:write",
  "code": "INSUFFICIENT_SCOPE"
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Agent 'nonexistent-agent-99999' not found.",
  "code": "AGENT_NOT_FOUND"
}
```

### 409 Conflict
```json
{
  "error": "conflict",
  "message": "Agent with name 'Duplicate Agent' already registered.",
  "code": "AGENT_ALREADY_REGISTERED"
}
```

### 422 Validation Error
```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "code": "VALIDATION_ERROR",
  "details": [
    {
      "field": "name",
      "message": "field required"
    }
  ]
}
```

### 429 Rate Limited
```json
{
  "error": "rate_limited",
  "message": "Rate limit exceeded. Try again in 30 seconds.",
  "code": "RATE_LIMIT_EXCEEDED"
}
```
