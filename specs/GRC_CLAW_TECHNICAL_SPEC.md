# GRC_Claw — Technical Specification

**Version:** 1.0.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Author:** Ahmed Hassan (CISO/GRC)  
**License:** Apache 2.0  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Core Abstractions](#3-core-abstractions)
4. [Component Interfaces](#4-component-interfaces)
5. [Data Models](#5-data-models)
6. [API Specifications](#6-api-specifications)
7. [Policy Language Selection](#7-policy-language-selection)
8. [Evidence Format (OSCAL)](#8-evidence-format-oscal)
9. [Integration Patterns](#9-integration-patterns)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Security Architecture](#11-security-architecture)
12. [Compliance Mapping](#12-compliance-mapping)
13. [Implementation Roadmap](#13-implementation-roadmap)

---

## 1. Executive Summary

GRC_Claw is an open-source, ISO 42001-native governance chassis for AI systems. It unifies policy enforcement, evidence generation, compliance mapping, and audit trail management into a single platform that covers the full AI lifecycle — from pre-deployment assessment through runtime monitoring to audit documentation.

### Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Deterministic enforcement** | Prompt-based safety has 26.67% violation rate; application-layer enforcement achieves 0.00% |
| **Fail-closed default** | Deny-by-default with explicit allow; governance engine timeout → deny |
| **Policy-as-code** | All policies version-controlled in Git with required reviews |
| **Tamper-evident audit** | SHA-256 Merkle chain for every decision; O(log n) inclusion proofs |
| **Multi-framework mapping** | Single control maps to NIST AI RMF, EU AI Act, ISO 42001, OWASP simultaneously |
| **Agentic AI native** | Purpose-built for agent governance, not traditional ML models |
| **Evidence chain** | Cryptographic linkage from technical test results to regulatory obligations |

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Policy Engine | Cedar (primary) + Rego (compat) | Deterministic policy evaluation |
| Identity | SPIFFE/SPIRE + Ed25519 | Zero-trust agent identity |
| Audit | Merkle chain + CloudEvents v1.0 | Tamper-evident logging |
| Evidence | OSCAL 1.1 | Structured compliance evidence |
| API | MCP OAuth 2.1 + REST | Tool integration and external access |
| Sandbox | 4 privilege rings | Execution isolation |
| Storage | PostgreSQL + Redis | Policy store + hot cache |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GRC_Claw Governance Chassis                      │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   Policy      │  │  Evidence    │  │  Compliance  │  │  Audit     │ │
│  │   Engine      │  │  Generator   │  │  Mapper      │  │  Trail     │ │
│  │  (Cedar/Rego) │  │  (OSCAL)     │  │  (Multi-FW)  │  │  (Merkle)  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │                 │        │
│  ┌──────┴─────────────────┴─────────────────┴─────────────────┴──────┐ │
│  │                      Core Abstraction Layer                         │ │
│  │  Policy │ Evidence │ Enforcement │ Assessment │ ComplianceMapping  │ │
│  └────────────────────────────┬──────────────────────────────────────┘ │
│                               │                                         │
│  ┌────────────────────────────┴──────────────────────────────────────┐ │
│  │                      Integration Layer                             │ │
│  │  MCP Server │ REST API │ Webhooks │ SDK │ CI/CD Gates │ SIEM     │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                      Infrastructure Layer                          │ │
│  │  PostgreSQL │ Redis │ Kafka │ Object Storage │ HashiCorp Vault    │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Diagram

```
                    ┌─────────────────┐
                    │   AI Agent      │
                    │  (Hermes, etc.) │
                    └────────┬────────┘
                             │ pre_tool_call / post_tool_call
                             ▼
                    ┌─────────────────┐
                    │  GRC_Claw       │
                    │  Middleware     │
                    │  (Sidecar/     │
                    │   In-Process)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │  Policy    │  │  Identity  │  │  Audit     │
     │  Engine    │  │  (SPIFFE)  │  │  Logger    │
     │  (Cedar)   │  │            │  │  (Merkle)  │
     └─────┬──────┘  └────────────┘  └─────┬──────┘
           │                                │
           ▼                                ▼
     ┌────────────┐                 ┌────────────┐
     │  Policy    │                 │  CloudEvents│
     │  Store     │                 │  Export     │
     │  (Git+DB)  │                 │  (SIEM)     │
     └────────────┘                 └────────────┘
```

### 2.3 Data Flow

```
1. Agent initiates action
       │
       ▼
2. GRC_Claw intercepts (pre_tool_call hook)
       │
       ▼
3. Policy Engine evaluates (Cedar/Rego)
       │
       ├── ALLOW → action proceeds → post_tool_call audit
       ├── DENY  → action blocked → audit + alert
       ├── REQUIRE_APPROVAL → human gate → audit
       └── TRANSFORM → redact/modify → action proceeds → audit
       │
       ▼
4. Evidence generated (OSCAL format)
       │
       ▼
5. Compliance mapping updated (multi-framework)
       │
       ▼
6. Audit trail appended (Merkle chain)
       │
       ▼
7. CloudEvents exported (SIEM/dashboard)
```

---

## 3. Core Abstractions

### 3.1 Policy

A **Policy** is a declarative, version-controlled rule set that governs AI agent behavior. Policies are the primary enforcement mechanism and are evaluated deterministically by the policy engine.

```yaml
apiVersion: grcclaw/v1
kind: Policy
metadata:
  name: production-agent-policy
  version: "2.1.0"
  description: "Production governance policy for customer-facing agents"
  owner: platform-team@company.com
  labels:
    environment: production
    framework: iso-42001
    severity: high
spec:
  defaultAction: deny
  onTimeout: deny
  rules:
    - name: block-pii-export
      description: "PII data must never leave the system"
      condition:
        type: cedar
        expression: |
          principal.action == "export" &&
          resource.containsPii == true
      effect: deny
      priority: 1000

    - name: require-approval-for-refunds
      description: "Refunds over $500 require human approval"
      condition:
        type: cedar
        expression: |
          principal.action == "refund" &&
          context.amount > 500
      effect: require_approval
      approvers:
        - role: cs-manager
      priority: 500

    - name: allow-read-operations
      description: "Read-only operations are generally allowed"
      condition:
        type: cedar
        expression: |
          principal.action == "read"
      effect: allow
      priority: 100

    - name: rate-limit-external-api
      description: "External API calls limited to 100/hour"
      condition:
        type: rego
        query: data.grcclaw.rate_limit
      effect: throttle
      limit: "100/hour"
      priority: 500
```

**Policy Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `apiVersion` | string | API version (grcclaw/v1) |
| `kind` | string | Resource type (Policy) |
| `metadata.name` | string | Unique policy identifier |
| `metadata.version` | string | Semantic version |
| `metadata.owner` | string | Responsible team/person |
| `spec.defaultAction` | Action | Default decision when no rule matches |
| `spec.onTimeout` | Action | Decision when policy engine times out |
| `spec.rules[]` | Rule[] | Ordered rule set (evaluated by priority) |

**Rule Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Rule identifier |
| `description` | string | Human-readable purpose (ISO 42001 Clause 6 evidence) |
| `condition` | Condition | When this rule applies |
| `effect` | Action | What happens when condition matches |
| `priority` | integer | Evaluation order (higher = first) |
| `approvers[]` | string[] | Required for require_approval effect |
| `limit` | string | Rate limit expression |

**Actions:** `allow`, `deny`, `warn`, `require_approval`, `transform`, `escalate`, `throttle`, `log`

### 3.2 Evidence

**Evidence** is a structured, cryptographically verifiable record of a governance decision or assessment result. Evidence is the bridge between technical operations and regulatory compliance.

```json
{
  "evidence_id": "EVD-2026-001234",
  "schema_version": "grcclaw/evidence/v1",
  "timestamp": "2026-10-01T14:23:07.331Z",
  "type": "policy_evaluation",
  "subject": {
    "agent_id": "hermes-primary",
    "agent_did": "did:web:hermes-agent",
    "session_id": "sess-2026-1001-001",
    "action": "tool_call",
    "tool": "terminal",
    "resource": "production-database"
  },
  "policy": {
    "id": "production-agent-policy",
    "version": "2.1.0",
    "rule": "block-pii-export"
  },
  "decision": {
    "effect": "deny",
    "reason": "PII export attempted by agent",
    "confidence": 1.0
  },
  "context": {
    "input_hash": "sha256:abc123...",
    "output_hash": "sha256:def456...",
    "environment": "production",
    "trace_id": "trace-2026-1001-001"
  },
  "compliance_tags": [
    "iso-42001:6.1",
    "iso-42001:8.1",
    "nist-ai-rmf:MEASURE",
    "eu-ai-act:article-9"
  ],
  "proof": {
    "merkle_root": "sha256:789abc...",
    "merkle_path": ["sha256:def...", "sha256:ghi..."],
    "signature": "ed25519:sig..."
  }
}
```

**Evidence Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `evidence_id` | string | Unique evidence identifier |
| `schema_version` | string | Evidence schema version |
| `timestamp` | ISO 8601 | When the evidence was generated |
| `type` | string | Evidence category |
| `subject` | object | What/who the evidence is about |
| `policy` | object | Policy that was evaluated |
| `decision` | object | The governance decision |
| `context` | object | Additional context (hashes, trace refs) |
| `compliance_tags` | string[] | Framework control mappings |
| `proof` | object | Cryptographic proof (Merkle + signature) |

**Evidence Types:**

| Type | Description |
|------|-------------|
| `policy_evaluation` | Result of a policy engine evaluation |
| `assessment_result` | Result of a technical assessment (fairness, bias, etc.) |
| `incident_record` | AgentIncident structured incident |
| `audit_event` | General audit trail entry |
| `compliance_mapping` | Control-to-framework mapping |
| `risk_assessment` | Risk evaluation result |

### 3.3 Enforcement

**Enforcement** is the mechanism by which policy decisions are applied to agent actions. Enforcement is deterministic and happens at the application layer before the action reaches the wire.

```python
class EnforcementResult:
    """Result of an enforcement decision."""
    effect: Literal["allow", "deny", "warn", "require_approval", "transform", "escalate"]
    reason: str
    policy_id: str
    rule_id: str
    evidence_id: str
    transformed_input: Optional[dict] = None
    approval_ticket: Optional[str] = None
    metadata: dict = field(default_factory=dict)

class EnforcementEngine:
    """Deterministic enforcement engine."""
    
    def enforce(
        self,
        action: AgentAction,
        context: EnforcementContext,
        policies: list[Policy]
    ) -> EnforcementResult:
        """
        Evaluate policies against an agent action.
        
        Args:
            action: The action the agent wants to take
            context: Full context (agent identity, session, environment)
            policies: Applicable policies (filtered by scope)
            
        Returns:
            EnforcementResult with the decision and evidence
        """
        # 1. Sort policies by priority (descending)
        # 2. Evaluate each policy's rules
        # 3. First matching rule wins (deny_overrides strategy)
        # 4. Generate evidence for the decision
        # 5. Return enforcement result
        ...
```

**Enforcement Points:**

| Point | Timing | Purpose |
|-------|--------|---------|
| `agent_startup` | Before agent run | Validate session metadata |
| `input` | External request ingress | Validate incoming data |
| `pre_model_call` | Before LLM call | Validate messages, context, tool definitions |
| `pre_tool_call` | Before tool execution | **Primary enforcement point** |
| `post_tool_call` | After tool execution | Observational audit |
| `output` | Before delivery | Validate agent output |
| `agent_shutdown` | Session termination | Final audit |
| `inter_agent` | Inter-agent messages | Validate agent-to-agent comms |

**Enforcement Strategies:**

| Strategy | Behavior |
|----------|----------|
| `deny_overrides` | Any deny rule wins over allow rules (default) |
| `allow_overrides` | Any allow rule wins over deny rules |
| `first_match` | First matching rule wins |
| `priority_order` | Highest priority rule wins |

### 3.4 Assessment

**Assessment** is the process of evaluating AI systems against technical criteria (fairness, bias, robustness, explainability) and producing structured evidence.

```python
class Assessment:
    """A technical assessment of an AI system."""
    
    assessment_id: str
    system_id: str
    assessment_type: AssessmentType
    criteria: list[AssessmentCriterion]
    results: list[AssessmentResult]
    overall_score: float
    evidence: list[Evidence]
    timestamp: datetime
    assessor: str  # Who/what performed the assessment

class AssessmentType(Enum):
    FAIRNESS = "fairness"
    BIAS = "bias"
    ROBUSTNESS = "robustness"
    EXPLAINABILITY = "explainability"
    SECURITY = "security"
    LLM_EVALUATION = "llm_evaluation"
    RED_TEAM = "red_team"

class AssessmentCriterion:
    """A single assessment criterion."""
    criterion_id: str
    name: str
    description: str
    framework_mapping: dict[str, str]  # framework -> control_id
    test_method: str
    threshold: float
    weight: float

class AssessmentResult:
    """Result of a single criterion evaluation."""
    criterion_id: str
    score: float  # 0.0 to 1.0
    passed: bool
    details: dict
    evidence_refs: list[str]
    raw_output: Optional[str]
```

**Assessment Integration:**

```
┌─────────────────────────────────────────────────────────┐
│                   Assessment Pipeline                    │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Fairness │  │ Explain- │  │ Robust-  │  │ LLM    │ │
│  │ (Fair-   │  │ ability  │  │ ness     │  │ Eval   │ │
│  │  learn)  │  │ (SHAP)   │  │ (Prompt- │  │(Prompt-│ │
│  │          │  │          │  │  foo)    │  │  foo)  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │              │              │            │      │
│       └──────────────┴──────────────┴────────────┘      │
│                          │                               │
│                          ▼                               │
│                 ┌────────────────┐                       │
│                 │  Aggregator    │                       │
│                 │  (Weighted     │                       │
│                 │   scoring)     │                       │
│                 └────────┬───────┘                       │
│                          │                               │
│                          ▼                               │
│                 ┌────────────────┐                       │
│                 │  OSCAL Evidence│                       │
│                 │  Generator     │                       │
│                 └────────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

### 3.5 Compliance Mapping

**Compliance Mapping** is the cross-framework control mapping that allows a single technical control to satisfy multiple regulatory frameworks simultaneously.

```python
class ComplianceMapping:
    """Maps a single control to multiple frameworks."""
    
    mapping_id: str
    control_id: str  # GRC_Claw internal control ID
    control_name: str
    description: str
    framework_mappings: dict[str, FrameworkMapping]
    evidence_requirements: list[EvidenceRequirement]
    assessment_criteria: list[str]  # Links to AssessmentCriterion IDs

class FrameworkMapping:
    """Mapping to a specific framework."""
    framework: str  # "iso-42001", "nist-ai-rmf", "eu-ai-act", "owasp-llm"
    version: str
    control_ids: list[str]  # e.g., ["6.1", "8.1"] for ISO 42001
    section_refs: list[str]  # e.g., ["Annex A.5"]
    obligation_level: str  # "mandatory", "recommended", "informative"
```

**Mapping Example:**

```yaml
mapping_id: MAP-001
control_id: GRC-CTRL-001
control_name: "AI System Risk Assessment"
description: "Conduct and document risk assessment for AI systems before deployment"
framework_mappings:
  iso-42001:
    version: "2023"
    control_ids: ["6.1", "6.2"]
    section_refs: ["Annex A.5"]
    obligation_level: mandatory
  nist-ai-rmf:
    version: "1.0"
    control_ids: ["GOVERN-1", "MAP-1", "MAP-2"]
    section_refs: ["2.1", "3.1"]
    obligation_level: mandatory
  eu-ai-act:
    version: "2024"
    control_ids: ["Article 9", "Article 15"]
    section_refs: ["Title III, Chapter 2"]
    obligation_level: mandatory
  owasp-llm:
    version: "2025"
    control_ids: ["LLM01", "LLM02"]
    section_refs: ["Top 10 for LLM Applications"]
    obligation_level: recommended
evidence_requirements:
  - type: assessment_result
    criteria: [risk-assessment, impact-assessment]
    threshold: 0.8
  - type: policy_evaluation
    policy: risk-assessment-policy
  - type: audit_event
    retention: "7years"
```

---

## 4. Component Interfaces

### 4.1 Policy Engine Interface

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

class PolicyEngine(ABC):
    """Abstract policy engine interface."""
    
    @abstractmethod
    def evaluate(
        self,
        principal: Principal,
        action: Action,
        resource: Resource,
        context: dict
    ) -> PolicyDecision:
        """
        Evaluate policies against an action.
        
        Returns:
            PolicyDecision with effect, reason, and matched rule
        """
        ...
    
    @abstractmethod
    def validate_policy(self, policy: Policy) -> ValidationResult:
        """Validate a policy definition for syntax and semantics."""
        ...
    
    @abstractmethod
    def load_policies(self, source: PolicySource) -> list[Policy]:
        """Load policies from a source (Git, DB, file)."""
        ...
    
    @abstractmethod
    def get_policy(self, policy_id: str, version: Optional[str] = None) -> Policy:
        """Retrieve a specific policy by ID and optional version."""
        ...

class CedarEngine(PolicyEngine):
    """Cedar-based policy engine implementation."""
    # Uses cedar-policy Rust crate via FFI
    ...

class RegoEngine(PolicyEngine):
    """OPA Rego-based policy engine implementation."""
    # Uses OPA WASM or sidecar
    ...
```

### 4.2 Evidence Generator Interface

```python
class EvidenceGenerator(ABC):
    """Abstract evidence generator interface."""
    
    @abstractmethod
    def generate(
        self,
        event: GovernanceEvent,
        context: EvidenceContext
    ) -> Evidence:
        """
        Generate structured evidence for a governance event.
        
        Args:
            event: The governance event (policy eval, assessment, incident)
            context: Additional context for evidence generation
            
        Returns:
            Evidence object with cryptographic proof
        """
        ...
    
    @abstractmethod
    def to_oscal(self, evidence: Evidence) -> OSCALDocument:
        """Convert evidence to OSCAL format."""
        ...
    
    @abstractmethod
    def verify(self, evidence: Evidence) -> bool:
        """Verify the cryptographic proof of an evidence object."""
        ...
```

### 4.3 Enforcement Engine Interface

```python
class EnforcementEngine(ABC):
    """Abstract enforcement engine interface."""
    
    @abstractmethod
    def enforce(
        self,
        action: AgentAction,
        context: EnforcementContext
    ) -> EnforcementResult:
        """
        Enforce policies against an agent action.
        
        This is the primary entry point for governance enforcement.
        It evaluates all applicable policies and returns a decision.
        """
        ...
    
    @abstractmethod
    def register_hook(self, point: str, callback: Callable) -> None:
        """Register an enforcement hook at a specific intervention point."""
        ...
    
    @abstractmethod
    def get_audit_trail(
        self,
        filter: AuditFilter
    ) -> list[AuditEntry]:
        """Retrieve audit trail entries matching the filter."""
        ...
```

### 4.4 Assessment Engine Interface

```python
class AssessmentEngine(ABC):
    """Abstract assessment engine interface."""
    
    @abstractmethod
    def run_assessment(
        self,
        system_id: str,
        assessment_type: AssessmentType,
        config: AssessmentConfig
    ) -> Assessment:
        """
        Run a technical assessment on an AI system.
        
        Args:
            system_id: The AI system to assess
            assessment_type: Type of assessment to run
            config: Assessment configuration
            
        Returns:
            Assessment with results and evidence
        """
        ...
    
    @abstractmethod
    def get_assessment(self, assessment_id: str) -> Assessment:
        """Retrieve a completed assessment."""
        ...
    
    @abstractmethod
    def compare_assessments(
        self,
        assessment_id_1: str,
        assessment_id_2: str
    ) -> AssessmentComparison:
        """Compare two assessments (e.g., before/after policy change)."""
        ...
```

### 4.5 Compliance Mapper Interface

```python
class ComplianceMapper(ABC):
    """Abstract compliance mapper interface."""
    
    @abstractmethod
    def map_control(
        self,
        control_id: str,
        frameworks: Optional[list[str]] = None
    ) -> ComplianceMapping:
        """
        Get the compliance mapping for a control.
        
        Args:
            control_id: GRC_Claw internal control ID
            frameworks: Optional list of frameworks to filter by
            
        Returns:
            ComplianceMapping with framework-specific references
        """
        ...
    
    @abstractmethod
    def get_framework_controls(
        self,
        framework: str,
        version: Optional[str] = None
    ) -> list[Control]:
        """Get all controls for a specific framework."""
        ...
    
    @abstractmethod
    def generate_evidence_package(
        self,
        control_ids: list[str],
        framework: str
    ) -> EvidencePackage:
        """
        Generate an evidence package for a set of controls
        in a specific framework's format.
        """
        ...
```

---

## 5. Data Models

### 5.1 Entity-Relationship Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Policy     │     │   Evidence   │     │   Audit      │
│              │     │              │     │   Entry      │
│ id           │◄────│ policy_id    │     │              │
│ name         │     │ evidence_id  │     │ entry_id     │
│ version      │     │ type         │     │ timestamp    │
│ content      │     │ subject      │     │ event_type   │
│ owner        │     │ decision     │     │ actor        │
│ status       │     │ proof        │     │ resource     │
│ created_at   │     │ timestamp    │     │ outcome      │
│ updated_at   │     │              │     │ details      │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                            │ evidence_id
                            ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  Assessment  │     │  Compliance  │
                     │              │     │  Mapping     │
                     │ id           │     │              │
                     │ system_id    │     │ mapping_id   │
                     │ type         │     │ control_id   │
                     │ criteria[]   │     │ framework    │
                     │ results[]    │     │ control_ids  │
                     │ score        │     │ version      │
                     │ timestamp    │     │ obligation   │
                     └──────────────┘     └──────────────┘
```

### 5.2 Database Schema (PostgreSQL)

```sql
-- Policies table
CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    owner VARCHAR(255) NOT NULL,
    content JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    labels JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, version)
);

-- Policy rules table
CREATE TABLE policy_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    condition JSONB NOT NULL,
    effect VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 0,
    approvers JSONB DEFAULT '[]',
    limit_expression VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Evidence table
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id VARCHAR(255) UNIQUE NOT NULL,
    schema_version VARCHAR(50) NOT NULL,
    type VARCHAR(100) NOT NULL,
    subject JSONB NOT NULL,
    policy_id UUID REFERENCES policies(id),
    decision JSONB NOT NULL,
    context JSONB DEFAULT '{}',
    compliance_tags JSONB DEFAULT '[]',
    proof JSONB NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Assessments table
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id VARCHAR(255) UNIQUE NOT NULL,
    system_id VARCHAR(255) NOT NULL,
    assessment_type VARCHAR(100) NOT NULL,
    criteria JSONB NOT NULL,
    results JSONB NOT NULL,
    overall_score DECIMAL(5,4),
    assessor VARCHAR(255),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Compliance mappings table
CREATE TABLE compliance_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mapping_id VARCHAR(255) UNIQUE NOT NULL,
    control_id VARCHAR(255) NOT NULL,
    control_name VARCHAR(255) NOT NULL,
    description TEXT,
    framework_mappings JSONB NOT NULL,
    evidence_requirements JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit entries table (Merkle chain)
CREATE TABLE audit_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id VARCHAR(255) UNIQUE NOT NULL,
    sequence_number BIGINT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    actor VARCHAR(255),
    resource VARCHAR(255),
    outcome VARCHAR(100),
    details JSONB DEFAULT '{}',
    previous_hash VARCHAR(256) NOT NULL,
    entry_hash VARCHAR(256) NOT NULL,
    merkle_root VARCHAR(256),
    signature VARCHAR(512)
);

-- Indexes
CREATE INDEX idx_evidence_type ON evidence(type);
CREATE INDEX idx_evidence_timestamp ON evidence(timestamp);
CREATE INDEX idx_evidence_compliance_tags ON evidence USING GIN(compliance_tags);
CREATE INDEX idx_audit_timestamp ON audit_entries(timestamp);
CREATE INDEX idx_audit_event_type ON audit_entries(event_type);
CREATE INDEX idx_assessments_system ON assessments(system_id);
CREATE INDEX idx_assessments_type ON assessments(assessment_type);
```

### 5.3 Event Schema (CloudEvents v1.0)

```json
{
  "specversion": "1.0",
  "type": "com.grcclaw.policy.evaluation",
  "source": "/grcclaw/policy-engine",
  "id": "EVD-2026-001234",
  "time": "2026-10-01T14:23:07.331Z",
  "datacontenttype": "application/json",
  "data": {
    "evidence_id": "EVD-2026-001234",
    "policy_id": "production-agent-policy",
    "rule_id": "block-pii-export",
    "effect": "deny",
    "agent_id": "hermes-primary",
    "action": "export",
    "resource": "customer-data"
  }
}
```

---

## 6. API Specifications

### 6.1 REST API

#### Policy Management

```
POST   /api/v1/policies                    # Create policy
GET    /api/v1/policies                    # List policies
GET    /api/v1/policies/{id}               # Get policy
PUT    /api/v1/policies/{id}               # Update policy
DELETE /api/v1/policies/{id}               # Delete policy
POST   /api/v1/policies/{id}/validate      # Validate policy
POST   /api/v1/policies/{id}/deploy        # Deploy policy
```

#### Evidence Management

```
POST   /api/v1/evidence                    # Submit evidence
GET    /api/v1/evidence                    # Query evidence
GET    /api/v1/evidence/{id}               # Get evidence
GET    /api/v1/evidence/{id}/verify        # Verify evidence proof
GET    /api/v1/evidence/oscal/{id}         # Get OSCAL format
```

#### Assessment Management

```
POST   /api/v1/assessments                 # Run assessment
GET    /api/v1/assessments                 # List assessments
GET    /api/v1/assessments/{id}            # Get assessment
POST   /api/v1/assessments/{id}/compare    # Compare assessments
```

#### Compliance Mapping

```
GET    /api/v1/compliance/mappings        # List mappings
GET    /api/v1/compliance/mappings/{id}   # Get mapping
GET    /api/v1/compliance/frameworks       # List frameworks
GET    /api/v1/compliance/frameworks/{fw}/controls  # Get controls
POST   /api/v1/compliance/evidence-package # Generate evidence package
```

#### Audit Trail

```
GET    /api/v1/audit                       # Query audit trail
GET    /api/v1/audit/verify                # Verify Merkle chain
GET    /api/v1/audit/proof/{entry_id}      # Get inclusion proof
GET    /api/v1/audit/export                # Export audit trail
```

### 6.2 MCP (Model Context Protocol) Interface

GRC_Claw exposes an MCP server for AI agent integration:

```json
{
  "mcpServers": {
    "grc-claw": {
      "command": "python3",
      "args": ["-m", "grcclaw.mcp_server"],
      "env": {
        "GRC_CLAW_API_URL": "https://grc-claw.internal",
        "GRC_CLAW_API_KEY": "..."
      }
    }
  }
}
```

**MCP Tools:**

| Tool | Description |
|------|-------------|
| `evaluate_policy` | Evaluate a policy against an action |
| `get_evidence` | Retrieve evidence by ID |
| `run_assessment` | Run a technical assessment |
| `get_compliance_mapping` | Get compliance mapping for a control |
| `verify_audit_trail` | Verify the integrity of the audit trail |
| `generate_evidence_package` | Generate OSCAL evidence package |

**MCP Resources:**

| Resource | Description |
|----------|-------------|
| `grcclaw://policies` | List all policies |
| `grcclaw://evidence/{id}` | Get evidence by ID |
| `grcclaw://assessments/{id}` | Get assessment by ID |
| `grcclaw://compliance/{control_id}` | Get compliance mapping |

### 6.3 Webhook API

#### Inbound Webhooks (GRC_Claw → Subscribers)

```json
{
  "event_type": "policy.violation",
  "timestamp": "2026-10-01T14:23:07.331Z",
  "payload": {
    "evidence_id": "EVD-2026-001234",
    "policy_id": "production-agent-policy",
    "rule_id": "block-pii-export",
    "effect": "deny",
    "agent_id": "hermes-primary",
    "severity": "high"
  }
}
```

**Event Types:**

| Event | Description |
|-------|-------------|
| `policy.evaluation` | Policy was evaluated |
| `policy.violation` | Policy was violated |
| `policy.approval_required` | Human approval needed |
| `assessment.completed` | Assessment finished |
| `audit.integrity_warning` | Audit chain verification failed |
| `compliance.mapping_updated` | Compliance mapping changed |

#### Outbound Webhooks (External → GRC_Claw)

```json
{
  "event_type": "agent.action",
  "timestamp": "2026-10-01T14:23:07.331Z",
  "payload": {
    "agent_id": "hermes-primary",
    "action": "tool_call",
    "tool": "terminal",
    "arguments": {"command": "kubectl get pods"},
    "session_id": "sess-2026-1001-001"
  }
}
```

### 6.4 SDK Interface

#### Python SDK

```python
from grcclaw import GRCClaw, Policy, AgentAction

# Initialize client
grc = GRCClaw(api_url="https://grc-claw.internal", api_key="...")

# Evaluate a policy
result = grc.evaluate_policy(
    policy_id="production-agent-policy",
    action=AgentAction(
        agent_id="hermes-primary",
        action="export",
        resource="customer-data"
    )
)

if result.effect == "deny":
    print(f"Denied: {result.reason}")
    print(f"Evidence: {result.evidence_id}")

# Run an assessment
assessment = grc.run_assessment(
    system_id="customer-service-agent",
    assessment_type="fairness",
    config={"threshold": 0.8}
)

# Get compliance mapping
mapping = grc.get_compliance_mapping(
    control_id="GRC-CTRL-001",
    frameworks=["iso-42001", "nist-ai-rmf"]
)

# Generate evidence package
package = grc.generate_evidence_package(
    control_ids=["GRC-CTRL-001", "GRC-CTRL-002"],
    framework="iso-42001"
)
```

#### TypeScript SDK

```typescript
import { GRCClaw, Policy, AgentAction } from '@grcclaw/sdk';

const grc = new GRCClaw({
  apiUrl: 'https://grc-claw.internal',
  apiKey: '...'
});

const result = await grc.evaluatePolicy({
  policyId: 'production-agent-policy',
  action: {
    agentId: 'hermes-primary',
    action: 'export',
    resource: 'customer-data'
  }
});

if (result.effect === 'deny') {
  console.log(`Denied: ${result.reason}`);
  console.log(`Evidence: ${result.evidenceId}`);
}
```

---

## 7. Policy Language Selection

### 7.1 Cedar vs Rego Comparison

| Criteria | Cedar | Rego (OPA) |
|----------|-------|------------|
| **Type** | Purpose-built authorization language | General-purpose policy language |
| **Syntax** | Declarative, scoped to authorization | Datalog-like, general computation |
| **Formal verification** | ✅ Yes (Rust-based, formally verified) | ❌ No |
| **Performance** | <0.1ms p99 (Rust core) | 1-10ms p99 (WASM/Go) |
| **Learning curve** | Moderate (new syntax) | Moderate (Datalog concepts) |
| **Ecosystem** | Growing (AWS, Cedar-lang.org) | Mature (CNCF graduated, K8s standard) |
| **AI governance fit** | ✅ Excellent (ABAC, scoped policies) | ⚠️ Good (general purpose) |
| **Kubernetes integration** | ❌ No native integration | ✅ Native (admission control) |
| **WASM support** | ❌ No | ✅ Yes (edge deployment) |
| **Policy composition** | ✅ Hierarchical | ✅ Data-based composition |
| **Debugging** | ✅ Good error messages | ⚠️ Can be opaque |
| **Community** | Smaller but growing | Large, mature |

### 7.2 Recommendation: Cedar as Primary, Rego as Compatibility Layer

**Primary: Cedar**

Cedar is the recommended primary policy language for GRC_Claw because:

1. **Formal verification** — Cedar policies can be formally verified, which is critical for compliance evidence
2. **Purpose-built for authorization** — Cedar's ABAC model maps directly to AI governance needs (principal, action, resource, context)
3. **Performance** — Sub-millisecond evaluation is essential for real-time agent governance
4. **Type safety** — Cedar's schema-driven approach prevents many policy errors at compile time
5. **Growing adoption** — Cedar is gaining traction in the formal verification community

**Compatibility: Rego**

Rego is supported as a compatibility layer because:

1. **Existing investments** — Many organizations already have OPA/Rego policies
2. **Kubernetes integration** — Rego is the standard for K8s admission control
3. **Complex conditionals** — Rego's general computation is useful for complex policy logic
4. **WASM deployment** — Rego policies can compile to WASM for edge deployment

### 7.3 Cedar Policy Example

```cedar
// GRC_Claw Production Policy
// Blocks PII export, requires approval for high-value refunds

permit(
    principal,
    action == Action::"export",
    resource
) when {
    !resource.containsPii &&
    principal.clearance >= "internal"
};

forbid(
    principal,
    action == Action::"export",
    resource
) when {
    resource.containsPii
};

permit(
    principal,
    action == Action::"refund",
    resource
) when {
    context.amount <= 500 &&
    principal.role == "cs-agent"
};

// High-value refunds require approval
forbid(
    principal,
    action == Action::"refund",
    resource
) when {
    context.amount > 500 &&
    !context.approvalTicket.exists
};
```

### 7.4 Rego Policy Example

```rego
package grcclaw

import future.keywords.if
import future.keywords.in

# Default deny
default verdict := {"effect": "deny", "reason": "No matching allow rule"}

# Block PII export
verdict := {"effect": "deny", "reason": "PII export blocked"} if {
    input.action == "export"
    input.resource.containsPii == true
}

# Allow read operations
verdict := {"effect": "allow"} if {
    input.action == "read"
}

# Require approval for high-value refunds
verdict := {"effect": "require_approval", "reason": "Refund over $500"} if {
    input.action == "refund"
    input.context.amount > 500
    not input.context.approvalTicket
}

# Rate limiting
verdict := {"effect": "throttle", "reason": "Rate limit exceeded"} if {
    input.action == "api_call"
    count(input.agent.apiCalls) > 100
    time.now_ns() - input.agent.firstCallTime < 3600000000000
}
```

### 7.5 Policy Composition Strategy

```
┌─────────────────────────────────────────────────────────┐
│                  Policy Hierarchy                        │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Organization Baseline (CISO)                    │    │
│  │  - Block PII export                             │    │
│  │  - Block credential access                       │    │
│  │  - Audit everything                              │    │
│  │  [Cedar - non-negotiable]                       │    │
│  └────────────────────┬────────────────────────────┘    │
│                       │                                  │
│  ┌────────────────────▼────────────────────────────┐    │
│  │  Platform Shared (Platform Team)                │    │
│  │  - Rate limit external APIs                     │    │
│  │  - Require approval for external network         │    │
│  │  [Cedar - platform controls]                    │    │
│  └────────────────────┬────────────────────────────┘    │
│                       │                                  │
│  ┌────────────────────▼────────────────────────────┐    │
│  │  Application-Specific (App Team)                │    │
│  │  - Allow read tickets                           │    │
│  │  - Block refunds over $500                      │    │
│  │  [Cedar + Rego - use case rules]                │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Conflict Resolution: deny_overrides                      │
│  No team can weaken inherited rules                      │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Evidence Format (OSCAL)

### 8.1 Why OSCAL

NIST's Open Security Controls Assessment Language (OSCAL) is the standard for structured compliance evidence. GRC_Claw uses OSCAL 1.1 as its canonical evidence format because:

1. **NIST standard** — OSCAL is the NIST standard for compliance documentation
2. **Machine-readable** — Structured JSON/XML/YAML for automated processing
3. **Framework-agnostic** — Supports any compliance framework
4. **Audit-ready** — Directly usable in audits and assessments
5. **Tool ecosystem** — Supported by NIST, GSA, and major compliance tools

### 8.2 OSCAL Document Types

| OSCAL Document | GRC_Claw Use |
|----------------|--------------|
| `catalog` | Control catalog (ISO 42001, NIST AI RMF, EU AI Act) |
| `profile` | Framework profile (subset of controls) |
| `system-security-plan` | AI system security plan |
| `assessment-plan` | Assessment plan (what to test) |
| `assessment-results` | Assessment results (test outcomes) |
| `plan-of-action-and-milestones` | Remediation plan |

### 8.3 OSCAL Assessment Results Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<assessment-results xmlns="http://csrc.nist.gov/ns/oscal/1.1"
    uuid="assessment-results-2026-001">
    
    <metadata>
        <title>GRC_Claw Assessment Results</title>
        <last-modified>2026-10-01T14:23:07.331Z</last-modified>
        <version>1.0.0</version>
        <oscal-version>1.1</oscal-version>
    </metadata>
    
    <import-ap href="#assessment-plan-2026-001"/>
    
    <local-definitions>
        <components>
            <component uuid="comp-001" type="software">
                <title>Hermes Agent</title>
                <description>AI agent under governance</description>
            </component>
        </components>
    </local-definitions>
    
    <results>
        <result uuid="result-001" title="Fairness Assessment">
            <description>Fairness assessment for customer service agent</description>
            <start>2026-10-01T14:00:00Z</start>
            <end>2026-10-01T14:23:07Z</end>
            
            <reviewed-controls>
                <reviewed-control uuid="rc-001">
                    <control-id>iso-42001:6.1</control-id>
                    <control-id>iso-42001:8.1</control-id>
                    <control-id>nist-ai-rmf:MEASURE</control-id>
                </reviewed-control>
            </reviewed-controls>
            
            <observations>
                <observation uuid="obs-001">
                    <title>Demographic Parity</title>
                    <description>Demographic parity ratio across groups</description>
                    <methods>
                        <method>fairlearn.MetricFrame</method>
                    </methods>
                    <subjects>
                        <subject subject-uuid="comp-001"/>
                    </subjects>
                    <collected>2026-10-01T14:20:00Z</collected>
                    <evidence>
                        <evidence uuid="evd-001">
                            <title>Fairness Metric Results</title>
                            <description>Demographic parity ratio: 0.92 (threshold: 0.80)</description>
                            <props>
                                <prop name="score">0.92</prop>
                                <prop name="threshold">0.80</prop>
                                <prop name="passed">true</prop>
                            </props>
                        </evidence>
                    </evidence>
                </observation>
            </observations>
            
            <risks>
                <risk uuid="risk-001">
                    <title>Potential Bias in Refund Decisions</title>
                    <description>Refund approval rates vary by demographic group</description>
                    <likelihood>medium</likelihood>
                    <impact>medium</impact>
                    <status>
                        <state>open</state>
                    </status>
                </risk>
            </risks>
            
            <findings>
                <finding uuid="finding-001">
                    <title>Fairness Criteria Met</title>
                    <description>All fairness criteria met for customer service agent</description>
                    <target target-id="iso-42001:6.1">
                        <status>
                            <state>satisfied</state>
                        </status>
                    </target>
                </finding>
            </findings>
        </result>
    </results>
</assessment-results>
```

### 8.4 Evidence Generation Pipeline

```
┌─────────────────────────────────────────────────────────┐
│              Evidence Generation Pipeline                 │
│                                                          │
│  ┌──────────┐                                           │
│  │ Event    │  (policy eval, assessment, incident)      │
│  └────┬─────┘                                           │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────┐                                           │
│  │ Enrich   │  (add context, compliance tags, hashes)   │
│  └────┬─────┘                                           │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────┐                                           │
│  │ Sign     │  (Ed25519 signature)                      │
│  └────┬─────┘                                           │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────┐                                           │
│  │ Merkle   │  (add to Merkle chain)                    │
│  └────┬─────┘                                           │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────┐                                           │
│  │ OSCAL    │  (convert to OSCAL format)                │
│  └────┬─────┘                                           │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────┐                                           │
│  │ Export   │  (CloudEvents, SIEM, audit package)       │
│  └──────────┘                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 9. Integration Patterns

### 9.1 Agent Integration (In-Process)

```python
# hermes_plugin.py — In-process governance middleware
from grcclaw import GRCClaw, AgentAction, EnforcementContext

grc = GRCClaw.from_config()

def pre_tool_call(tool_name: str, arguments: dict, session_id: str) -> dict:
    """Intercept every tool call before execution."""
    action = AgentAction(
        agent_id="hermes-primary",
        action="tool_call",
        tool=tool_name,
        arguments=arguments,
        session_id=session_id
    )
    
    context = EnforcementContext(
        environment="production",
        trace_id=get_current_trace_id()
    )
    
    result = grc.enforce(action, context)
    
    if result.effect == "allow":
        return {"action": "allow"}
    elif result.effect == "deny":
        return {
            "action": "block",
            "message": f"[GRC_Claw] Denied by policy '{result.policy_id}': {result.reason}"
        }
    elif result.effect == "require_approval":
        return {
            "action": "require_approval",
            "approval_ticket": result.approval_ticket,
            "message": f"[GRC_Claw] Approval required: {result.reason}"
        }
    elif result.effect == "transform":
        return {
            "action": "allow",
            "transformed_input": result.transformed_input
        }
    else:
        # Fail-closed
        return {
            "action": "block",
            "message": f"[GRC_Claw] Unknown effect: {result.effect}"
        }

def post_tool_call(tool_name: str, arguments: dict, result: dict, session_id: str) -> None:
    """Observational hook — audit logging."""
    grc.log_audit_event(
        event_type="tool_invocation",
        agent_id="hermes-primary",
        tool=tool_name,
        arguments=arguments,
        result=result,
        session_id=session_id
    )
```

### 9.2 Agent Integration (Sidecar)

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Container                       │
│                                                          │
│  ┌──────────────┐         ┌──────────────┐              │
│  │  AI Agent    │◄───────►│  GRC_Claw    │              │
│  │  (Hermes)    │  HTTP   │  Sidecar     │              │
│  │              │         │  (Envoy/     │              │
│  │              │         │   custom)    │              │
│  └──────────────┘         └──────┬───────┘              │
│                                  │                       │
│                                  │ localhost:8080        │
│                                  ▼                       │
│                           ┌──────────────┐              │
│                           │  GRC_Claw    │              │
│                           │  Server      │              │
│                           │  (Policy     │              │
│                           │   Engine)    │              │
│                           └──────────────┘              │
└─────────────────────────────────────────────────────────┘
```

### 9.3 CI/CD Integration

```yaml
# .github/workflows/grc-claw-gate.yml
name: GRC_Claw Compliance Gate

on: [push, pull_request]

jobs:
  compliance-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Validate Policies
        run: |
          grcclaw lint-policy policies/
          grcclaw validate-policy policies/
      
      - name: Run Assessments
        run: |
          grcclaw assess --system customer-service-agent --type fairness
          grcclaw assess --system customer-service-agent --type robustness
      
      - name: Check Compliance
        run: |
          grcclaw verify-compliance \
            --framework iso-42001 \
            --controls 6.1,8.1,9.1 \
            --strict
      
      - name: Generate Evidence Package
        run: |
          grcclaw generate-evidence \
            --framework iso-42001 \
            --output evidence/iso-42001-evidence.oscal.json
      
      - name: Upload Evidence
        uses: actions/upload-artifact@v4
        with:
          name: compliance-evidence
          path: evidence/
```

### 9.4 MCP Server Integration

```python
# grcclaw_mcp_server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from grcclaw import GRCClaw

app = Server("grc-claw")
grc = GRCClaw.from_config()

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="evaluate_policy",
            description="Evaluate a policy against an action",
            inputSchema={
                "type": "object",
                "properties": {
                    "policy_id": {"type": "string"},
                    "action": {"type": "object"},
                    "context": {"type": "object"}
                },
                "required": ["policy_id", "action"]
            }
        ),
        Tool(
            name="get_evidence",
            description="Retrieve evidence by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "evidence_id": {"type": "string"}
                },
                "required": ["evidence_id"]
            }
        ),
        Tool(
            name="run_assessment",
            description="Run a technical assessment",
            inputSchema={
                "type": "object",
                "properties": {
                    "system_id": {"type": "string"},
                    "assessment_type": {"type": "string"},
                    "config": {"type": "object"}
                },
                "required": ["system_id", "assessment_type"]
            }
        ),
        Tool(
            name="get_compliance_mapping",
            description="Get compliance mapping for a control",
            inputSchema={
                "type": "object",
                "properties": {
                    "control_id": {"type": "string"},
                    "frameworks": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["control_id"]
            }
        ),
        Tool(
            name="verify_audit_trail",
            description="Verify the integrity of the audit trail",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name, arguments):
    if name == "evaluate_policy":
        result = grc.evaluate_policy(**arguments)
        return [TextContent(type="text", text=result.to_json())]
    elif name == "get_evidence":
        evidence = grc.get_evidence(**arguments)
        return [TextContent(type="text", text=evidence.to_json())]
    elif name == "run_assessment":
        assessment = grc.run_assessment(**arguments)
        return [TextContent(type="text", text=assessment.to_json())]
    elif name == "get_compliance_mapping":
        mapping = grc.get_compliance_mapping(**arguments)
        return [TextContent(type="text", text=mapping.to_json())]
    elif name == "verify_audit_trail":
        result = grc.verify_audit_trail(**arguments)
        return [TextContent(type="text", text=result.to_json())]

if __name__ == "__main__":
    import asyncio
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    asyncio.run(main())
```

### 9.5 SIEM Integration

```python
# Export audit trail to SIEM (Splunk, Elastic, etc.)
from grcclaw import GRCClaw
import json

grc = GRCClaw.from_config()

# Export as CloudEvents
events = grc.export_audit_trail(
    start_time="2026-10-01T00:00:00Z",
    end_time="2026-10-01T23:59:59Z",
    format="cloudevents"
)

# Send to SIEM
for event in events:
    siem_client.send(event)
```

### 9.6 AgentIncident Integration

```python
# Map AgentIncident records to GRC_Claw evidence
from grcclaw import GRCClaw, Evidence, EvidenceType

grc = GRCClaw.from_config()

def map_incident_to_evidence(incident: dict) -> Evidence:
    """Convert an AgentIncident record to GRC_Claw evidence."""
    return Evidence(
        type=EvidenceType.INCIDENT_RECORD,
        subject={
            "agent_id": incident["meta"]["agent"],
            "agent_did": f"did:web:{incident['meta']['agent']}",
            "session_id": incident["meta"].get("session_id"),
            "action": "incident",
            "resource": incident.get("resource", "unknown")
        },
        decision={
            "effect": "deny" if incident["impact_score"] >= 4 else "warn",
            "reason": incident["classification"]["root_cause"],
            "confidence": incident["classification"]["confidence"]
        },
        context={
            "incident_id": incident["meta"]["incident_id"],
            "fault_class": incident["fault_class"],
            "impact_score": incident["impact_score"],
            "loss_amount_usd": incident.get("loss_amount_usd"),
            "payload_hash": incident.get("payload_hash"),
            "trace_hash": incident["trace"][0]["hash"] if incident["trace"] else None
        },
        compliance_tags=incident.get("compliance_tags", [])
    )

# Import incidents
for incident in agentincident.get_incidents(since="2026-09-01"):
    evidence = map_incident_to_evidence(incident)
    grc.submit_evidence(evidence)
```

---

## 10. Deployment Architecture

### 10.1 Deployment Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **In-Process** | Library linked into agent | Single agent, low latency |
| **Sidecar** | Sidecar container in same pod | Kubernetes, service mesh |
| **Centralized** | Central GRC_Claw server | Multi-agent, multi-team |
| **Edge** | Lightweight WASM/Rego | Edge deployment, IoT |

### 10.2 Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grc-claw
  namespace: governance
spec:
  replicas: 3
  selector:
    matchLabels:
      app: grc-claw
  template:
    metadata:
      labels:
        app: grc-claw
    spec:
      serviceAccountName: grc-claw
      containers:
        - name: grc-claw
          image: grcclaw/server:v1.0.0
          ports:
            - containerPort: 8080
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: grc-claw-db
                  key: url
            - name: SPIFFE_ENDPOINT
              value: "unix:///run/spire/sockets/agent.sock"
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "2000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: grc-claw
  namespace: governance
spec:
  selector:
    app: grc-claw
  ports:
    - port: 8080
      targetPort: 8080
  type: ClusterIP
```

### 10.3 Edge Deployment

For edge deployments, GRC_Claw uses a lightweight WASM-based policy engine:

```
┌─────────────────────────────────────────────────────────┐
│                    Edge Node                             │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  AI Agent    │  │  GRC_Claw    │  │  Local       │  │
│  │  (Hermes)    │  │  WASM        │  │  Storage     │  │
│  │              │  │  Policy      │  │  (SQLite)    │  │
│  │              │  │  Engine      │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  Latency: <1ms | Power: 50-200W                         │
│  Use: F2T2EA, grid control, fraud detection             │
└─────────────────────────────────────────────────────────┘
```

---

## 11. Security Architecture

### 11.1 Zero-Trust Identity

```
┌─────────────────────────────────────────────────────────┐
│                  Zero-Trust Identity                     │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Agent       │  │  Workload    │  │  Cross-Mesh  │  │
│  │  Identity    │  │  Identity    │  │  Trust       │  │
│  │  (Ed25519)   │  │  (SPIFFE)    │  │  (DID)       │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  Every action individually authenticated                  │
│  No trusted sessions                                     │
│  Continuous behavioral scoring                           │
└─────────────────────────────────────────────────────────┘
```

### 11.2 Tamper-Evident Audit Trail

```
┌─────────────────────────────────────────────────────────┐
│                  Merkle Chain Audit Trail                 │
│                                                          │
│  Entry 1    Entry 2    Entry 3    Entry 4    Entry N    │
│  ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐     │
│  │ H1  │──►│ H2  │──►│ H3  │──►│ H4  │──►│ HN  │     │
│  └─────┘   └─────┘   └─────┘   └─────┘   └─────┘     │
│     │          │          │          │          │        │
│     └──────────┴──────────┴──────────┴──────────┘        │
│                        │                                 │
│                        ▼                                 │
│                 ┌─────────────┐                          │
│                 │ Merkle Root │                          │
│                 │ (Published) │                          │
│                 └─────────────┘                          │
│                                                          │
│  Any modification invalidates all subsequent hashes       │
│  O(log n) inclusion proofs for external auditors         │
└─────────────────────────────────────────────────────────┘
```

### 11.3 Encryption

| Layer | Algorithm | Purpose |
|-------|-----------|---------|
| Data at rest | AES-256-GCM | Database encryption |
| Data in transit | TLS 1.3 + mTLS | Service-to-service |
| Key exchange | CRYSTALS-Kyber | Post-quantum key exchange |
| Signatures | Ed25519 + CRYSTALS-Dilithium | Evidence signing |
| Hashing | SHA-256 | Merkle chain, content hashing |

---

## 12. Compliance Mapping

### 12.1 ISO 42001 Clause Mapping

| ISO 42001 Clause | GRC_Claw Component | Evidence Type |
|-----------------|-------------------|---------------|
| **4. Context** | Agent inventory, policy scope | `audit_event` |
| **5. Leadership** | Policy ownership, role assignment | `policy_evaluation` |
| **6. Planning** | Risk assessment, policy rules | `assessment_result` |
| **7. Support** | Policy documentation, training | `audit_event` |
| **8. Operation** | Enforcement, monitoring | `policy_evaluation` |
| **9. Performance Evaluation** | Audit trail, assessments | `assessment_result` |
| **10. Improvement** | Incident response, policy updates | `incident_record` |

### 12.2 NIST AI RMF Mapping

| NIST AI RMF Function | GRC_Claw Component | Evidence Type |
|---------------------|-------------------|---------------|
| **GOVERN** | Policy engine, RBAC | `policy_evaluation` |
| **MAP** | Risk assessment, agent inventory | `assessment_result` |
| **MEASURE** | Technical assessments, metrics | `assessment_result` |
| **MANAGE** | Incident response, remediation | `incident_record` |

### 12.3 EU AI Act Mapping

| EU AI Act Article | GRC_Claw Component | Evidence Type |
|------------------|-------------------|---------------|
| **Article 9** (Risk management) | Risk assessment | `assessment_result` |
| **Article 10** (Data governance) | Data policies | `policy_evaluation` |
| **Article 11** (Technical documentation) | Evidence package | `assessment_result` |
| **Article 12** (Record keeping) | Audit trail | `audit_event` |
| **Article 13** (Transparency) | Output policies | `policy_evaluation` |
| **Article 14** (Human oversight) | Approval workflows | `policy_evaluation` |
| **Article 15** (Accuracy, robustness) | Robustness assessment | `assessment_result` |
| **Article 73** (Incident reporting) | Incident records | `incident_record` |

### 12.4 OWASP LLM Top 10 Mapping

| OWASP LLM Risk | GRC_Claw Control | Evidence Type |
|---------------|-----------------|---------------|
| **LLM01** (Prompt Injection) | Input validation policies | `policy_evaluation` |
| **LLM02** (Insecure Output) | Output filtering policies | `policy_evaluation` |
| **LLM03** (Training Data Poisoning) | Data governance policies | `policy_evaluation` |
| **LLM04** (Model Denial of Service) | Rate limiting policies | `policy_evaluation` |
| **LLM05** (Supply Chain) | Tool pinning, SBOM | `audit_event` |
| **LLM06** (Sensitive Info Disclosure) | PII detection policies | `policy_evaluation` |
| **LLM07** (Insecure Plugin) | MCP security gateway | `policy_evaluation` |
| **LLM08** (Excessive Agency) | Scope limitation policies | `policy_evaluation` |
| **LLM09** (Overreliance) | Human oversight policies | `policy_evaluation` |
| **LLM10** (Model Theft) | Access control policies | `policy_evaluation` |

---

## 13. Implementation Roadmap

### Phase 1: Foundation (Months 1-3)

- [ ] Core abstractions (Policy, Evidence, Enforcement, Assessment, ComplianceMapping)
- [ ] Cedar policy engine integration
- [ ] Basic REST API
- [ ] PostgreSQL schema
- [ ] Audit trail with Merkle chain
- [ ] Python SDK

### Phase 2: Integration (Months 4-6)

- [ ] MCP server
- [ ] Rego compatibility layer
- [ ] OSCAL evidence generation
- [ ] CI/CD gate integration
- [ ] AgentIncident integration
- [ ] SIEM export

### Phase 3: Assessment (Months 7-9)

- [ ] Fairness assessment (Fairlearn integration)
- [ ] Explainability assessment (SHAP integration)
- [ ] Robustness assessment (Promptfoo integration)
- [ ] LLM evaluation (Promptfoo integration)
- [ ] Assessment aggregator
- [ ] Evidence package generator

### Phase 4: Scale (Months 10-12)

- [ ] Multi-agent governance
- [ ] Edge deployment (WASM)
- [ ] Advanced compliance mapping
- [ ] Dashboard and reporting
- [ ] Performance optimization
- [ ] Production hardening

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **ABAC** | Attribute-Based Access Control |
| **Cedar** | AWS's purpose-built authorization language |
| **CloudEvents** | CNCF specification for event data format |
| **DID** | Decentralized Identifier |
| **MCP** | Model Context Protocol |
| **OSCAL** | Open Security Controls Assessment Language (NIST) |
| **Rego** | OPA's policy language |
| **SPIFFE** | Secure Production Identity Framework for Everyone |
| **WASM** | WebAssembly |

## Appendix B: References

1. NIST SP 800-171 — Protecting CUI
2. ISO/IEC 42001:2023 — AI Management System
3. NIST AI RMF 1.0 — AI Risk Management Framework
4. EU AI Act — Regulation on Artificial Intelligence
5. OWASP Top 10 for LLM Applications 2025
6. Cedar Policy Language Specification
7. OPA Rego Documentation
8. OSCAL 1.1 Specification
9. CloudEvents v1.0 Specification
10. AgentIncident Specification v0.1

---

*End of Technical Specification*
