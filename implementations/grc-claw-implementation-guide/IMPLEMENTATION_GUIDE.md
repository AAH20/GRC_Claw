# GRC_Claw — Implementation Guide

**Version:** 1.0.0
**Date:** 2026-10-01
**Status:** Complete
**License:** Apache 2.0

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Abstractions (Python)](#core-abstractions-python)
4. [Database Schema (SQL)](#database-schema-sql)
5. [API Endpoints (FastAPI)](#api-endpoints-fastapi)
6. [Event Schemas (CloudEvents)](#event-schema-cloudevents)
7. [Configuration (YAML)](#configuration-yaml)
8. [Testing (pytest)](#testing-pytest)
9. [Deployment (Docker Compose)](#deployment-docker-compose)
10. [Quick Start](#quick-start)

---

## Overview

GRC_Claw is an open-source, ISO 42001-native governance chassis for AI systems. This implementation guide provides complete, working code for all 5 core abstractions:

| Abstraction | File | Description |
|-------------|------|-------------|
| **Policy** | `src/grcclaw/models.py` | Declarative, version-controlled rule sets |
| **Evidence** | `src/grcclaw/models.py` | Cryptographically verifiable records |
| **Enforcement** | `src/grcclaw/enforcement.py` | Deterministic policy enforcement |
| **Assessment** | `src/grcclaw/assessment_engine.py` | Technical system evaluation |
| **Compliance** | `src/grcclaw/compliance_mapper.py` | Cross-framework control mapping |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GRC_Claw Server                           │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Policy  │  │ Evidence │  │Enforce-  │  │Assessment│  │
│  │  Engine  │  │Generator │  │  ment    │  │  Engine  │  │
│  │(Cedar/   │  │(OSCAL)   │  │  Engine  │  │(Fairness)│  │
│  │ Rego)    │  │          │  │          │  │          │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │              │        │
│  ┌────┴──────────────┴──────────────┴──────────────┴────┐  │
│  │              Core Abstraction Layer                    │  │
│  │  Policy │ Evidence │ Enforcement │ Assessment │ Compliance│
│  └────────────────────────┬───────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────┴───────────────────────────────┐  │
│  │              Integration Layer                          │  │
│  │  FastAPI │ CloudEvents │ Kafka │ MCP │ CI/CD Gates     │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Infrastructure Layer                       │  │
│  │  PostgreSQL │ Redis │ Kafka │ Prometheus │ Grafana     │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Abstractions (Python)

### File: `src/grcclaw/models.py`

All 5 core abstractions are implemented as Python dataclasses with full type hints:

```python
# 1. Policy — declarative governance rules
@dataclass
class Policy:
    name: str
    version: str
    rules: list[PolicyRule]
    scope: PolicyScope
    framework_mappings: list[FrameworkMapping]
    default_action: Action = Action.DENY
    on_timeout: Action = Action.DENY
    enforcement_strategy: EnforcementStrategy = EnforcementStrategy.DENY_OVERRIDES
    # ... lifecycle fields

# 2. Evidence — cryptographically verifiable records
@dataclass
class Evidence:
    evidence_id: str
    type: EvidenceType
    subject: EvidenceSubject
    decision: EvidenceDecision
    proof: Optional[EvidenceProof]  # Merkle root + Ed25519 signature
    compliance_tags: list[str]
    verification_level: VerificationLevel
    chain_of_custody: list[dict]

# 3. Enforcement — deterministic policy enforcement
@dataclass
class EnforcementResult:
    effect: Action
    reason: str
    policy_id: str
    rule_id: str
    evidence_id: str
    deterministic: bool = True
    evaluation_latency_ms: int = 0

# 4. Assessment — technical system evaluation
@dataclass
class Assessment:
    assessment_id: str
    system_id: str
    assessment_type: AssessmentType
    criteria: list[AssessmentCriterion]
    results: list[AssessmentResult]
    overall_score: float
    overall_result: ComplianceStatus

# 5. Compliance — cross-framework posture
@dataclass
class Compliance:
    organization_id: str
    framework: str
    overall_status: ComplianceStatus
    compliance_score: float
    control_mappings: list[ComplianceControlMapping]
    coverage_percentage: float
```

### File: `src/grcclaw/enforcement.py`

```python
class EnforcementEngine:
    """Deterministic enforcement engine with fail-closed defaults."""

    def enforce(
        self,
        action: AgentAction,
        context: EnforcementContext,
        policies: list[Policy],
    ) -> EnforcementResult:
        # 1. Sort policies by priority (descending)
        # 2. Evaluate each policy's rules
        # 3. Apply enforcement strategy (deny_overrides default)
        # 4. Generate evidence reference
        # 5. Return enforcement result
        ...

    def get_audit_trail(self, ...) -> list[Enforcement]:
        """Retrieve audit trail entries matching filter."""
        ...

    def get_stats(self) -> dict:
        """Get enforcement statistics."""
        ...
```

### File: `src/grcclaw/policy_engine.py`

```python
class CedarEngine(PolicyEngine):
    """Cedar-based policy engine (primary)."""
    def evaluate(self, principal, action, resource, context) -> PolicyDecision: ...
    def validate_policy(self, policy: Policy) -> ValidationResult: ...
    def compile_policy(self, policy: Policy) -> dict: ...

class RegoEngine(PolicyEngine):
    """OPA Rego-based policy engine (compatibility)."""
    def evaluate(self, principal, action, resource, context) -> PolicyDecision: ...
```

### File: `src/grcclaw/evidence_generator.py`

```python
class DefaultEvidenceGenerator(EvidenceGenerator):
    """Evidence generator with Merkle chain and Ed25519 signatures."""

    def generate(self, event_type, subject, decision, ...) -> Evidence: ...
    def to_oscal(self, evidence: Evidence) -> dict: ...
    def verify(self, evidence: Evidence) -> bool: ...
    def get_merkle_root(self) -> str: ...
```

### File: `src/grcclaw/assessment_engine.py`

```python
class DefaultAssessmentEngine(AssessmentEngine):
    """Assessment engine with pluggable test methods."""

    def run_assessment(self, system_id, assessment_type, config) -> Assessment: ...
    def compare_assessments(self, id1, id2) -> dict: ...
```

### File: `src/grcclaw/compliance_mapper.py`

```python
class DefaultComplianceMapper(ComplianceMapper):
    """Cross-framework compliance mapper."""

    def map_control(self, control_id, frameworks) -> ComplianceMapping: ...
    def compute_compliance(self, org_id, framework, evidence) -> Compliance: ...
    def generate_evidence_package(self, control_ids, framework) -> dict: ...
```

---

## Database Schema (SQL)

### File: `database/schema.sql`

Complete PostgreSQL schema with:

- **Core tables:** `policies`, `policy_rules`, `evidence`, `assessments`, `compliance_mappings`, `compliance_postures`, `enforcement_decisions`
- **Audit trail:** `audit_entries` with Merkle chain (SHA-256 hash chaining)
- **Supporting tables:** `agents`, `controls`, `frameworks`, `risks`, `findings`
- **Event store:** `event_store` for CQRS/Event Sourcing
- **Saga support:** `saga_instances`, `saga_step_history`
- **Views:** `v_compliance_summary`, `v_agent_governance`, `v_evidence_coverage`
- **Triggers:** Auto-update `updated_at` timestamps

```sql
-- Key indexes for performance
CREATE INDEX idx_evidence_type ON evidence(type);
CREATE INDEX idx_evidence_compliance_tags ON evidence USING GIN(compliance_tags);
CREATE INDEX idx_audit_timestamp ON audit_entries(timestamp);
CREATE INDEX idx_enforcement_agent ON enforcement_decisions(agent_id);
```

---

## API Endpoints (FastAPI)

### File: `src/grcclaw/api.py`

Complete REST API with 30+ endpoints:

| Category | Endpoints |
|----------|-----------|
| **Policies** | `POST/GET/PUT/DELETE /api/v1/policies`, `POST .../validate`, `POST .../deploy`, `POST .../compile` |
| **Evidence** | `POST/GET /api/v1/evidence`, `GET .../{id}/verify`, `GET .../oscal/{id}` |
| **Enforcement** | `POST /api/v1/enforcements`, `GET /api/v1/enforcements/stats` |
| **Assessment** | `POST/GET /api/v1/assessments`, `POST .../{id}/compare` |
| **Compliance** | `GET /api/v1/compliance/mappings`, `GET .../frameworks`, `POST .../evidence-package` |
| **Audit** | `GET /api/v1/audit`, `GET .../verify`, `GET .../merkle-root` |

Run with:
```bash
uvicorn grcclaw.api:app --host 0.0.0.0 --port 8080 --workers 4
```

---

## Event Schemas (CloudEvents)

### Directory: `events/`

15 CloudEvents v1.0 compliant event schemas with GRC_Claw extensions:

| Event File | Type |
|------------|------|
| `policy-evaluation.json` | `com.grcclaw.policy.evaluation` |
| `enforcement-decision.json` | `com.grcclaw.enforcement.decision` |
| `assessment-completed.json` | `com.grcclaw.assessment.completed` |
| `compliance-computed.json` | `com.grcclaw.compliance.computed` |
| `audit-event.json` | `com.grcclaw.audit.event` |
| `evidence-collected.json` | `com.grcclaw.evidence.collected` |
| `evidence-verified.json` | `com.grcclaw.evidence.verified` |
| `risk-detected.json` | `com.grcclaw.risk.detected` |
| `agent-registered.json` | `com.grcclaw.agent.registered` |
| `agent-terminated.json` | `com.grcclaw.agent.terminated` |
| `exception-created.json` | `com.grcclaw.exception.created` |
| `finding-created.json` | `com.grcclaw.finding.created` |
| `policy-activated.json` | `com.grcclaw.policy.activated` |
| `policy-violated.json` | `com.grcclaw.policy.violated` |
| `vendor-risk-changed.json` | `com.grcclaw.vendor.risk.changed` |
| `dead-letter.json` | `com.grcclaw.dead_letter` |

All events include the `grcclaw` extension with `tenant_id`, `environment`, `trace_id`, `compliance_frameworks`, and `risk_tier`.

---

## Configuration (YAML)

### Directory: `config/`

| File | Purpose |
|------|---------|
| `server.yaml` | Main server config (DB, Redis, Kafka, policy engine, circuit breakers, security) |
| `policy-example.yaml` | Example production policy (Cedar + Rego rules) |
| `compliance-mapping.yaml` | Cross-framework control mappings |
| `agent-config.yaml` | Per-agent governance settings |
| `cedar-schema.json` | Cedar policy schema |
| `policy-example.cedar` | Example Cedar policy |
| `policy-example.rego` | Example Rego policy |

---

## Testing (pytest)

### Directory: `tests/`

Two test files with 40+ test cases:

**`tests/test_core_abstractions.py`** — Unit tests for all 5 abstractions:
- `TestPolicy` — creation, serialization, hashing, rule sorting
- `TestEvidence` — creation, serialization, hashing
- `TestEnforcementEngine` — deny/allow/default, deny_overrides, audit trail, stats, latency
- `TestCedarEngine` — validation, CRUD, compilation
- `TestRegoEngine` — validation, CRUD
- `TestEvidenceGenerator` — generation, Merkle chain, OSCAL conversion, verification
- `TestAssessmentEngine` — fairness/robustness assessments, comparison
- `TestComplianceMapper` — control mapping, framework controls, evidence packages
- `TestEndToEnd` — full enforcement flow, assessment-to-compliance, policy lifecycle

**`tests/test_api.py`** — Integration tests for all API endpoints:
- Health checks, policy CRUD, enforcement, evidence, assessment, compliance, audit

Run with:
```bash
pytest tests/ -v --cov=src/grcclaw --cov-report=xml
```

---

## Deployment (Docker Compose)

### Directory: `deployment/`

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Full stack: API, PostgreSQL, Redis, Kafka, OPA, Prometheus, Grafana, Flink |
| `Dockerfile` | Python 3.11 slim-based container image |
| `kubernetes.yaml` | K8s deployment with RBAC, probes, service account |
| `prometheus.yml` | Prometheus scrape configuration |
| `ci-cd-gate.yml` | GitHub Actions compliance gate |

### Quick Start

```bash
# 1. Clone and navigate
cd grc-claw-implementation-guide

# 2. Set environment variables
export DB_PASSWORD=changeme
export GRAFANA_PASSWORD=changeme

# 3. Start the full stack
docker compose -f deployment/docker-compose.yml up -d

# 4. Run database migrations
docker compose exec postgres psql -U grcclaw -d grcclaw -f /docker-entrypoint-initdb.d/01-schema.sql

# 5. Verify health
curl http://localhost:8080/health

# 6. Run tests
pip install -r requirements.txt
pytest tests/ -v

# 7. View dashboard
open http://localhost:3000  # Grafana
```

### Service Ports

| Service | Port |
|---------|------|
| GRC_Claw API | 8080 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| Kafka | 9092 |
| OPA | 8181 |
| Prometheus | 9090 |
| Grafana | 3000 |
| Flink UI | 8081 |

---

## Key Design Decisions

1. **Fail-closed default:** All policies default to `deny`; enforcement engine defaults to `deny` on timeout
2. **Deny-overrides strategy:** Any deny rule wins over allow rules (configurable)
3. **Merkle chain audit:** Every enforcement decision is hash-chained for tamper evidence
4. **Ed25519 signatures:** All evidence is signed for cryptographic verification
5. **Cedar primary, Rego compatibility:** Cedar for new policies, Rego for existing OPA investments
6. **OSCAL 1.1 evidence:** All evidence convertible to NIST OSCAL format
7. **Multi-framework mapping:** Single control maps to ISO 42001, NIST AI RMF, EU AI Act, OWASP simultaneously
8. **CloudEvents v1.0:** All events follow CNCF CloudEvents specification with GRC_Claw extensions

---

*End of Implementation Guide*
