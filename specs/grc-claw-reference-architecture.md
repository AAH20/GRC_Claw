# GRC_Claw Reference Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team

---

## 1. Architectural Principles

| Principle | Rationale |
|-----------|-----------|
| **PEP/PDP Separation** | Universal pattern across all analyzed platforms; enables independent scaling and policy distribution |
| **Deterministic Enforcement** | No LLM in the decision path — the governed system cannot influence its own governance |
| **Evidence-First Design** | Audit-ready from day one, not day-before-audit |
| **MCP-Native Integration** | Governance embedded in AI workflows via Model Context Protocol |
| **Cryptographic Integrity** | SHA-256 chain-hashed audit trail with RFC 3161 timestamps |
| **Multi-Framework Mapping** | Single control implementation satisfies multiple compliance frameworks |
| **Agent-as-Subject** | Agents are first-class governance subjects, not applications to be governed |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              GRC_Claw Reference Architecture                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                        GOVERNANCE CONTROL PLANE                               │  │
│  │                                                                               │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │  │
│  │  │   Compliance    │  │    Policy       │  │      Agent Identity         │  │  │
│  │  │   Mapping       │  │   Definition    │  │      & Registry             │  │  │
│  │  │   Layer         │  │   Layer         │  │      Layer                  │  │  │
│  │  │                 │  │                 │  │                             │  │  │
│  │  │ • Framework     │  │ • Cedar/Rego    │  │ • Agent Registry            │  │  │
│  │  │   Adapters     │  │   Policies      │  │ • Identity Lifecycle        │  │  │
│  │  │ • Crosswalk     │  │ • Versioning    │  │ • Capability Declarations   │  │  │
│  │  │   Engine       │  │ • Dependency    │  │ • Trust Scoring             │  │  │
│  │  │ • Gap Analysis │  │   Graph         │  │ • mTLS Identity             │  │  │
│  │  └────────┬────────┘  └────────┬────────┘  └─────────────┬───────────────┘  │  │
│  │           │                    │                         │                  │  │
│  │           └────────────────────┼─────────────────────────┘                  │  │
│  │                                │                                            │  │
│  │                                ▼                                            │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │  │
│  │  │                    POLICY DECISION POINT (PDP)                       │   │  │
│  │  │                                                                     │   │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │   │  │
│  │  │  │  OPA/Rego    │  │   Cedar      │  │   Decision Engine        │   │   │  │
│  │  │  │  Engine      │  │   Engine     │  │   (5-Way)                │   │   │  │
│  │  │  │              │  │              │  │                          │   │   │  │
│  │  │  │ • Rego rules │  │ • Cedar      │  │ • ALLOW                  │   │   │  │
│  │  │  │ • Data docs  │  │   policies   │  │ • ALLOW_WITH_REDACTION   │   │   │  │
│  │  │  │ • Built-ins  │  │ • Schema     │  │ • REQUIRE_APPROVAL       │   │   │  │
│  │  │  │              │  │   validation │  │ • DENY                   │   │   │  │
│  │  │  │              │  │              │  │ • QUARANTINE             │   │   │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────────┘   │   │  │
│  │  │                                                                     │   │  │
│  │  │  Decision: {verdict, policy_id, evidence_hash, context, timestamp}  │   │  │
│  │  └────────────────────────────────┬────────────────────────────────────┘   │  │
│  │                                   │                                        │  │
│  └───────────────────────────────────┼────────────────────────────────────────┘  │
│                                      │                                            │
│  ┌───────────────────────────────────┼────────────────────────────────────────┐  │
│  │                                   │                                        │  │
│  │  ┌────────────────────────────────▼────────────────────────────────────┐   │  │
│  │  │                    POLICY ENFORCEMENT POINT (PEP)                     │   │  │
│  │  │                                                                     │   │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │   │  │
│  │  │  │  MCP Gateway │  │  Sidecar     │  │   Kernel Enforcer        │   │   │  │
│  │  │  │  Proxy       │  │  Proxy       │  │   (eBPF/seccomp)         │   │   │  │
│  │  │  │              │  │              │  │                          │   │   │  │
│  │  │  │ • Tool call  │  │ • HTTP/gRPC  │  │ • File access            │   │   │  │
│  │  │  │   intercept  │  │   intercept  │  │ • Network control        │   │   │  │
│  │  │  │ • AuthN/AuthZ│  │ • AuthN/AuthZ│  │ • Process isolation      │   │   │  │
│  │  │  │ • Rate limit │  │ • Rate limit │  │ • Resource limits        │   │   │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────────┘   │   │  │
│  │  │                                                                     │   │  │
│  │  │  Enforcement: intercept → authenticate → authorize → execute/deny   │   │  │
│  │  └────────────────────────────────┬────────────────────────────────────┘   │  │
│  │                                   │                                        │  │
│  └───────────────────────────────────┼────────────────────────────────────────┘  │
│                                      │                                            │
│  ┌───────────────────────────────────┼────────────────────────────────────────┐  │
│  │                                   │                                        │  │
│  │  ┌────────────────────────────────▼────────────────────────────────────┐   │  │
│  │  │                    EVIDENCE COLLECTION LAYER                          │   │  │
│  │  │                                                                     │   │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │   │  │
│  │  │  │  Collectors  │  │  Normalizer  │  │   Evidence Store         │   │   │  │
│  │  │  │              │  │  (OSCAL)     │  │                          │   │   │  │
│  │  │  │ • API probes │  │              │  │ • WORM object storage   │   │   │  │
│  │  │  │ • Log stream │  │ • Parse      │  │ • Hash-chained audit    │   │   │  │
│  │  │  │ • File ingest│  │ • Map        │  │ • Chain of custody      │   │   │  │
│  │  │  │ • Agent scan │  │ • Enrich     │  │ • RFC 3161 timestamps   │   │   │  │
│  │  │  │ • Cloud conn │  │ • Hash       │  │ • Verification levels   │   │   │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────────┘   │   │  │
│  │  │                                                                     │   │  │
│  │  │  Evidence: OSCAL 1.1.0 assessment-results + GRC_Claw extensions    │   │  │
│  │  └────────────────────────────────┬────────────────────────────────────┘   │  │
│  │                                   │                                        │  │
│  └───────────────────────────────────┼────────────────────────────────────────┘  │
│                                      │                                            │
│  ┌───────────────────────────────────┼────────────────────────────────────────┐  │
│  │                                   │                                        │  │
│  │  ┌────────────────────────────────▼────────────────────────────────────┐   │  │
│  │  │                    OBSERVABILITY LAYER                                │   │  │
│  │  │                                                                     │   │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │   │  │
│  │  │  │  OpenTelemetry│  │ OpenInference│  │   Analytics Engine       │   │   │  │
│  │  │  │  Collector   │  │  (LLM Traces)│  │                          │   │   │  │
│  │  │  │              │  │              │  │ • Risk scoring           │   │   │  │
│  │  │  │ • Traces     │  │ • LLM spans  │  │ • Anomaly detection      │   │   │  │
│  │  │  │ • Metrics    │  │ • Token usage│  │ • Trend analysis         │   │   │  │
│  │  │  │ • Logs       │  │ • Prompt/resp│  │ • Drift detection        │   │   │  │
│  │  │  │ • Baggage    │  │ • Tool calls │  │ • Compliance posture     │   │   │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────────┘   │   │  │
│  │  │                                                                     │   │  │
│  │  │  Observability: OTel traces → OpenInference LLM spans → Analytics   │   │  │
│  │  └─────────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                             │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                         AGENT RUNTIME                                       │  │
│  │                                                                             │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │  │
│  │  │ Agent A  │  │ Agent B  │  │ Agent C  │  │ Agent D  │  │ Agent E  │     │  │
│  │  │(LangChain│  │(AutoGen) │  │(CrewAI)  │  │(Custom)  │  │(MCP Srv) │     │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │  │
│  │       │             │             │             │             │            │  │
│  │       └─────────────┴─────────────┴─────────────┴─────────────┘            │  │
│  │                                   │                                        │  │
│  │                    ┌──────────────▼──────────────┐                         │  │
│  │                    │      MCP Gateway             │                         │  │
│  │                    │  (PEP intercepts here)       │                         │  │
│  │                    └─────────────────────────────┘                         │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Specifications

### 3.1 Policy Definition Layer

**Purpose:** Author, version, and manage governance policies in declarative form.

**Technology:** Cedar (AWS) + Rego (OPA)

**Components:**

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| Policy Authoring API | FastAPI (Python) | CRUD for policies, versioning, lifecycle management |
| Cedar Policy Store | PostgreSQL + S3 | Store Cedar policies with full version history |
| Rego Policy Store | OPA Bundle Server | Distribute compiled Rego rules to PDP |
| Policy Dependency Graph | Neo4j / Apache AGE | Track inter-policy dependencies |
| Policy Compiler | Cedar→Rego translator | Compile Cedar policies to Rego for OPA evaluation |
| Dry-Run Engine | OPA `dry-run` | Simulate policy impact before activation |

**Policy Lifecycle States:**
```
draft → review → active → deprecated → archived
```

**Data Model:**
```yaml
Policy:
  id: UUID
  name: string
  description: string
  framework_tags: [string]  # [SOC2, ISO-27001, NIST-800-53, GDPR, HIPAA]
  cedar_policy: string      # Cedar source
  rego_policy: string       # Compiled Rego
  version: semver
  status: enum [draft, review, active, deprecated, archived]
  dependencies: [UUID]      # Other policy IDs
  created_by: string
  created_at: timestamp
  updated_at: timestamp
  effective_from: timestamp
  effective_until: timestamp
```

**Cedar Policy Example:**
```cedar
// Agent data access policy
permit(
  principal in Agent::"data-analyst",
  action == Action::"read",
  resource in DataClass::"public"
) when {
  resource.classification <= principal.clearance &&
  context.time.hour >= 6 && context.time.hour <= 22
};

// Deny access to PII without explicit approval
forbid(
  principal,
  action == Action::"read",
  resource in DataClass::"pii"
) unless {
  context.approval_ticket exists &&
  context.approval_ticket.status == "approved"
};
```

**Rego Policy Example (compiled from Cedar):**
```rego
package grc.agent.data_access

import future.keywords.if
import future.keywords.in

default allow := false

allow if {
    input.principal.clearance >= input.resource.classification
    input.action == "read"
    input.resource.classification <= 2
    time.now_ns() >= time.parse_rfc3339_ns("2026-10-01T06:00:00Z")
    time.now_ns() <= time.parse_rfc3339_ns("2026-10-01T22:00:00Z")
}

deny contains "pii_access_requires_approval" if {
    input.resource.classification == 4
    not input.context.approval_ticket
}

decision := {
    "verdict": "ALLOW",
    "policy_id": "pol-data-access-001",
    "evidence_hash": evidence_hash,
    "context": input.context,
    "timestamp": time.now_ns()
}
```

---

### 3.2 Policy Enforcement Layer (PEP/PDP)

**Purpose:** Enforce governance decisions at the point of agent action.

**Architecture:** Separated PEP (interception) and PDP (decision) for independent scaling.

#### 3.2.1 Policy Decision Point (PDP)

**Technology:** OPA (Open Policy Agent) + Cedar Engine

**Components:**

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| OPA Server | OPA 0.60+ | Evaluate Rego policies against input documents |
| Cedar Engine | Cedar Rust SDK | Evaluate Cedar policies natively |
| Decision Engine | Custom (Rust/Go) | 5-way decision logic |
| Policy Bundle Server | OPA Bundle API | Distribute policy bundles to PDP instances |
| Decision Cache | Redis | Cache frequent decisions (sub-ms lookup) |

**Decision Flow:**
```
Input Document (JSON)
    │
    ▼
┌─────────────────────────────────┐
│  PDP Evaluation Pipeline        │
│                                 │
│  1. Schema validation           │
│  2. Context enrichment           │
│  3. Cedar policy evaluation     │
│  4. Rego policy evaluation      │
│  5. Decision aggregation        │
│  6. Evidence hash computation   │
│  7. Decision certificate        │
└─────────────────────────────────┘
    │
    ▼
Decision Certificate (signed JSON)
```

**Decision Certificate:**
```json
{
  "decision-id": "uuid-v4",
  "verdict": "ALLOW | ALLOW_WITH_REDACTION | REQUIRE_APPROVAL | DENY | QUARANTINE",
  "policy-id": "pol-data-access-001",
  "policy-version": "1.2.0",
  "agent-id": "agent-42",
  "action": "read",
  "resource": "s3://data/public/dataset.csv",
  "context": {
    "time": "2026-10-01T14:30:00Z",
    "environment": "production",
    "approval_ticket": null
  },
  "evidence-hash": "sha256:abc123...",
  "timestamp": "2026-10-01T14:30:00.123Z",
  "ttl": 300,
  "signature": "ecdsa-p256:def456..."
}
```

#### 3.2.2 Policy Enforcement Point (PEP)

**Technology:** MCP Gateway Proxy + Sidecar Proxy + Kernel Enforcer

**Three Enforcement Modes:**

| Mode | Technology | Use Case | Latency |
|------|-----------|----------|---------|
| **MCP Gateway** | Python/TS MCP SDK | Tool-call interception via MCP protocol | < 10ms |
| **Sidecar Proxy** | Envoy + custom filter | HTTP/gRPC interception for service mesh | < 5ms |
| **Kernel Enforcer** | eBPF + seccomp | OS-level file/network/process control | < 1ms |

**PEP Decision Flow:**
```
Agent Action Request
    │
    ▼
┌─────────────────────────────────┐
│  PEP Interception               │
│                                 │
│  1. Extract action context      │
│  2. Authenticate agent (mTLS)   │
│  3. Build input document        │
│  4. Query PDP for decision      │
│  5. Apply decision              │
│  6. Log to evidence store       │
│  7. Return result to agent      │
└─────────────────────────────────┘
    │
    ├── ALLOW → Execute action
    ├── ALLOW_WITH_REDACTION → Execute with redaction
    ├── REQUIRE_APPROVAL → Queue for human review
    ├── DENY → Block action
    └── QUARANTINE → Isolate agent
```

**MCP Gateway Integration:**
```python
# MCP Gateway PEP implementation
from mcp.server import Server
from grc_claw.pep import EnforcementMiddleware

app = Server("grc-gateway")

@app.tool()
async def execute_tool(tool_name: str, arguments: dict) -> dict:
    # PEP intercepts every tool call
    decision = await pep.enforce(
        agent_id=context.agent_id,
        action=tool_name,
        resource=arguments.get("resource"),
        context=context
    )
    
    if decision.verdict == "ALLOW":
        return await execute_actual_tool(tool_name, arguments)
    elif decision.verdict == "ALLOW_WITH_REDACTION":
        redacted_args = apply_redaction(arguments, decision.redaction_rules)
        return await execute_actual_tool(tool_name, redacted_args)
    elif decision.verdict == "REQUIRE_APPROVAL":
        ticket = await create_approval_ticket(decision)
        return {"status": "pending_approval", "ticket_id": ticket.id}
    elif decision.verdict == "DENY":
        raise PolicyViolationError(decision.reason)
    elif decision.verdict == "QUARANTINE":
        await isolate_agent(context.agent_id)
        raise AgentQuarantinedError(decision.reason)
```

---

### 3.3 Evidence Collection Layer

**Purpose:** Collect, normalize, store, and verify compliance evidence.

**Technology:** OSCAL 1.1.0 + immudb + WORM storage

**Pipeline:**
```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Collectors │───▶│  Normalizer  │───▶│  Validator   │───▶│  Evidence    │
│             │    │  (OSCAL)     │    │  (Schema)    │    │  Store       │
│             │    │              │    │              │    │              │
│ • API probes│    │ • Parse      │    │ • Schema     │    │ • WORM       │
│ • Log stream│    │ • Map        │    │ • Completeness│   │ • Hash-chain │
│ • File ingest│   │ • Enrich     │    │ • Control ID │    │ • Custody    │
│ • Agent scan│    │ • Hash       │    │ • Hash verify│    │ • Timestamp  │
│ • Cloud conn│    │ • Timestamp  │    │ • Duplicate  │    │ • Verify     │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

**Evidence Types:**

| Type | Source | Collection Method |
|------|--------|-------------------|
| `artifact` | Config files, policy docs | File ingestion, API queries |
| `observation` | Runtime system state | Agent probes, API polling |
| `interview` | Human attestations | Manual upload with signature |
| `analysis` | Derived conclusions | Analytics engine output |
| `log` | Audit logs, event trails | SIEM integration, log streaming |

**Evidence Verification Levels:**

| Level | Name | Criteria |
|-------|------|----------|
| L0 | Unverified | Collected but not validated |
| L1 | Schema-valid | Passes OSCAL schema validation |
| L2 | Integrity-verified | Hash matches, chain of custody intact |
| L3 | Cross-validated | Corroborated by independent source |
| L4 | Attested | Signed by authorized human reviewer |

**Chain of Custody:**
```json
{
  "custody-event": {
    "event-id": "uuid-v4",
    "evidence-id": "uuid-v4",
    "action": "collected|verified|exported|accessed",
    "actor": "agent-42",
    "timestamp": "2026-10-01T14:30:00Z",
    "evidence-hash": "sha256:abc123...",
    "previous-event-hash": "sha256:def456...",
    "signature": "ecdsa-p256:ghi789..."
  }
}
```

---

### 3.4 Observability Integration

**Purpose:** Provide real-time visibility into agent behavior, policy enforcement, and compliance posture.

**Technology:** OpenTelemetry + OpenInference + Custom Analytics

**Three Pillars:**

| Pillar | Technology | Data Captured |
|--------|-----------|---------------|
| **Traces** | OpenTelemetry Collector | Agent action traces, policy evaluation traces, tool call spans |
| **Metrics** | Prometheus + Grafana | Enforcement latency, decision distribution, policy violation rates |
| **Logs** | Loki / Elastic | Audit logs, policy change events, agent lifecycle events |

**OpenInference Integration (LLM-Specific Observability):**

```python
from openinference.instrumentation import OpenInferenceTracer
from openinference.semconv.trace import SpanAttributes

# Trace LLM calls within agent actions
tracer = OpenInferenceTracer()

with tracer.start_as_current_span("agent_action") as span:
    span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "AGENT")
    span.set_attribute(SpanAttributes.INPUT_VALUE, user_prompt)
    span.set_attribute(SpanAttributes.OUTPUT_VALUE, agent_response)
    span.set_attribute("grc.agent_id", agent_id)
    span.set_attribute("grc.policy_id", policy_id)
    span.set_attribute("grc.decision", decision.verdict)
    span.set_attribute("grc.evidence_hash", decision.evidence_hash)
    
    # Tool call tracing
    for tool_call in agent_response.tool_calls:
        with tracer.start_as_current_span(f"tool_call:{tool_call.name}") as tool_span:
            tool_span.set_attribute("grc.tool_name", tool_call.name)
            tool_span.set_attribute("grc.tool_args", json.dumps(tool_call.arguments))
            tool_span.set_attribute("grc.tool_result", json.dumps(tool_call.result))
```

**OTel Trace Flow:**
```
Agent Action
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  OpenTelemetry Trace                                        │
│                                                             │
│  Span: agent_action                                         │
│  ├── Span: policy_evaluation (PDP)                          │
│  │   ├── Span: cedar_evaluation                             │
│  │   └── Span: rego_evaluation                              │
│  ├── Span: enforcement_decision (PEP)                       │
│  ├── Span: tool_execution                                   │
│  │   ├── Span: llm_call (OpenInference)                     │
│  │   └── Span: tool_invocation                              │
│  └── Span: evidence_collection                              │
│      ├── Span: normalization                                │
│      └── Span: storage                                      │
│                                                             │
│  Baggage: agent_id, policy_id, decision, evidence_hash      │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
OTel Collector → Jaeger/Tempo (traces)
                → Prometheus (metrics)
                → Loki (logs)
                → Analytics Engine (risk scoring)
```

**Analytics Engine:**

| Capability | Description | Data Source |
|-----------|-------------|-------------|
| Risk Scoring | Composite risk score per agent/policy/org | OTel metrics + evidence store |
| Anomaly Detection | Statistical baselines for agent behavior | OTel traces + OpenInference spans |
| Drift Detection | Agent behavior changes over time | OTel metrics + historical baselines |
| Trend Analysis | Policy violation trends, compliance posture | Evidence store + analytics DB |
| Predictive Insights | Controls trending toward non-compliance | ML models on historical data |

---

### 3.5 Agent Identity Layer

**Purpose:** Register, authenticate, and govern autonomous AI agents.

**Technology:** SPIFFE/SPIRE + mTLS + Agent Registry

**Components:**

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| Agent Registry | PostgreSQL + GraphQL API | Store agent metadata, capabilities, lifecycle state |
| Identity Issuer | SPIFFE/SPIRE | Issue SVIDs (SPIFFE Verifiable Identity Documents) |
| Certificate Authority | HashiCorp Vault | mTLS certificate issuance and rotation |
| Capability Declarations | JSON Schema | Define what actions an agent can perform |
| Trust Scoring | Custom algorithm | Dynamic trust score based on behavior |

**Agent Lifecycle States:**
```
proposed → approved → active → deprecated → terminated
                              ↓
                         suspended
                              ↓
                         quarantined
```

**Agent Registration:**
```yaml
Agent:
  id: UUID
  name: string
  type: enum [model, agent, pipeline, endpoint]
  framework: enum [langchain, autogen, crewai, custom, mcp-server]
  owner: string
  lifecycle_stage: enum [proposed, approved, active, deprecated, terminated]
  risk_tier: enum [prohibited, high, limited, minimal]
  capabilities:
    - name: string
      description: string
      permissions: [string]
      resource_scope: string
  identity:
    spiffe_id: string
    mtls_cert: string
    cert_expiry: timestamp
  trust_score:
    value: 0-100
    grade: enum [A, B, C, D, F]
    last_evaluated: timestamp
  policy_bindings: [UUID]  # Policy IDs
  created_at: timestamp
  updated_at: timestamp
```

**Identity Verification Flow:**
```
Agent Boot
    │
    ▼
┌─────────────────────────────────┐
│  1. Agent presents SVID          │
│  2. PEP verifies mTLS cert      │
│  3. PEP queries Agent Registry  │
│  4. PEP validates capabilities  │
│  5. PEP checks trust score      │
│  6. PEP enforces policy         │
│  7. PEP logs identity event     │
└─────────────────────────────────┘
    │
    ▼
Agent Authorized (or Denied)
```

---

### 3.6 Compliance Mapping Layer

**Purpose:** Map policies and evidence to multiple compliance frameworks simultaneously.

**Technology:** Unified Control Taxonomy (UCT) + Crosswalk Engine

**Supported Frameworks:**

| Framework | Control Count | Source |
|-----------|--------------|--------|
| NIST 800-53 Rev 5 | 1,026+ | NIST SP 800-53B |
| SOC 2 Trust Services Criteria | 64+ | AICPA TSC |
| ISO 27001:2022 | 93+ | ISO/IEC 27001:2022 |
| ISO/IEC 42001:2023 | 38+ | ISO/IEC 42001:2023 Annex A |
| GDPR | 30+ | EU GDPR Articles 5-30 |
| HIPAA Security Rule | 50+ | 45 CFR 164.308-312 |
| PCI DSS v4.0 | 78+ | PCI SSC v4.0 |
| COBIT 2019 | 40+ | ISACA COBIT 2019 |
| NIST AI RMF | 68+ | NIST AI 100-1 |
| EU AI Act | 40+ | EU AI Act Annex III |

**Hub-and-Spoke Mapping Model:**
```
                    ┌─────────────────┐
                    │  GRC_Claw       │
                    │  Control        │
                    │  (Hub)          │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ NIST 800-53   │   │ SOC 2         │   │ ISO 27001     │
│ AC-2 (Spoke)  │   │ CC6.1 (Spoke) │   │ A.12.4 (Spoke)│
└───────────────┘   └───────────────┘   └───────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ COBIT 2019    │   │ ISO 42001     │   │ GDPR          │
│ DSS06 (Spoke) │   │ A.6 (Spoke)   │   │ Art.5 (Spoke) │
└───────────────┘   └───────────────┘   └───────────────┘
```

**Crosswalk Engine:**
```python
class CrosswalkEngine:
    """Map a single control implementation to multiple frameworks."""
    
    def map_control(self, control_id: str) -> dict:
        """Return all framework mappings for a control."""
        return {
            "grc_control_id": control_id,
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
    
    def generate_compliance_report(self, framework: str, time_range: tuple) -> dict:
        """Generate a compliance report for a specific framework."""
        controls = self.get_controls_for_framework(framework)
        evidence = self.get_evidence_for_controls(controls, time_range)
        gaps = self.identify_gaps(controls, evidence)
        
        return {
            "framework": framework,
            "time_range": time_range,
            "controls_assessed": len(controls),
            "controls_compliant": len(controls) - len(gaps),
            "controls_non_compliant": len(gaps),
            "compliance_score": (len(controls) - len(gaps)) / len(controls) * 100,
            "gaps": gaps,
            "evidence_summary": self.summarize_evidence(evidence)
        }
```

---

## 4. Data Flow Diagrams

### 4.1 Agent Action Enforcement Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Agent   │     │   PEP    │     │   PDP    │     │ Evidence │     │Compliance│
│          │     │ (Gateway)│     │  (OPA)   │     │  Store   │     │  Mapping │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. Tool Call   │                │                │                │
     │───────────────▶│                │                │                │
     │                │                │                │                │
     │                │ 2. AuthN (mTLS)│                │                │
     │                │────┐           │                │                │
     │                │    │           │                │                │
     │                │◀───┘           │                │                │
     │                │                │                │                │
     │                │ 3. Build Input │                │                │
     │                │    Document    │                │                │
     │                │────┐           │                │                │
     │                │    │           │                │                │
     │                │◀───┘           │                │                │
     │                │                │                │                │
     │                │ 4. Query PDP   │                │                │
     │                │───────────────▶│                │                │
     │                │                │                │                │
     │                │                │ 5. Evaluate    │                │
     │                │                │    Policies    │                │
     │                │                │────┐           │                │
     │                │                │    │           │                │
     │                │                │◀───┘           │                │
     │                │                │                │                │
     │                │ 6. Decision    │                │                │
     │                │    Certificate │                │                │
     │                │◀───────────────│                │                │
     │                │                │                │                │
     │                │ 7. Execute or  │                │                │
     │                │    Deny        │                │                │
     │◀───────────────│                │                │                │
     │                │                │                │                │
     │                │ 8. Log Evidence│                │                │
     │                │────────────────────────────────▶                │
     │                │                │                │                │
     │                │                │                │ 9. Map to      │
     │                │                │                │    Frameworks  │
     │                │                │                │───────────────▶│
     │                │                │                │                │
     │                │                │                │ 10. Update     │
     │                │                │                │     Compliance │
     │                │                │                │     Posture    │
     │                │                │                │────┐           │
     │                │                │                │    │           │
     │                │                │                │◀───┘           │
     │                │                │                │                │
```

### 4.2 Evidence Collection Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│Collectors│     │Normalizer│     │Validator │     │ Evidence │     │  Audit   │
│          │     │ (OSCAL)  │     │ (Schema) │     │  Store   │     │ Package  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. Raw Evidence│                │                │                │
     │───────────────▶│                │                │                │
     │                │                │                │                │
     │                │ 2. Parse + Map │                │                │
     │                │    + Enrich    │                │                │
     │                │────┐           │                │                │
     │                │    │           │                │                │
     │                │◀───┘           │                │                │
     │                │                │                │                │
     │                │ 3. OSCAL JSON  │                │                │
     │                │───────────────▶│                │                │
     │                │                │                │                │
     │                │                │ 4. Schema +   │                │
     │                │                │    Hash +     │                │
     │                │                │    Control ID │                │
     │                │                │────┐           │                │
     │                │                │    │           │                │
     │                │                │◀───┘           │                │
     │                │                │                │                │
     │                │                │ 5. Validated   │                │
     │                │                │    Evidence    │                │
     │                │                │───────────────▶│                │
     │                │                │                │                │
     │                │                │                │ 6. Store +     │
     │                │                │                │    Hash Chain  │
     │                │                │                │────┐           │
     │                │                │                │    │           │
     │                │                │                │◀───┘           │
     │                │                │                │                │
     │                │                │                │ 7. Generate    │
     │                │                │                │    Audit       │
     │                │                │                │    Package     │
     │                │                │                │───────────────▶│
     │                │                │                │                │
     │                │                │                │ 8. Signed +    │
     │                │                │                │    Timestamped │
     │                │                │                │    Package     │
     │                │                │                │────┐           │
     │                │                │                │    │           │
     │                │                │                │◀───┘           │
     │                │                │                │                │
```

### 4.3 Policy Change Propagation Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Policy  │     │  Policy  │     │   PDP    │     │   PEP    │     │  Agent   │
│  Author  │     │ Compiler │     │  (OPA)   │     │ (Gateway)│     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. New Policy  │                │                │                │
     │    (Cedar)     │                │                │                │
     │───────────────▶│                │                │                │
     │                │                │                │                │
     │                │ 2. Compile to  │                │                │
     │                │    Rego        │                │                │
     │                │────┐           │                │                │
     │                │    │           │                │                │
     │                │◀───┘           │                │                │
     │                │                │                │                │
     │                │ 3. Validate +  │                │                │
     │                │    Dry-Run     │                │                │
     │                │────┐           │                │                │
     │                │    │           │                │                │
     │                │◀───┘           │                │                │
     │                │                │                │                │
     │                │ 4. Deploy      │                │                │
     │                │    Bundle      │                │                │
     │                │───────────────▶│                │                │
     │                │                │                │                │
     │                │                │ 5. Update      │                │
     │                │                │    Policies    │                │
     │                │                │────┐           │                │
     │                │                │    │           │                │
     │                │                │◀───┘           │                │
     │                │                │                │                │
     │                │                │ 6. Propagate   │                │
     │                │                │    to PEPs     │                │
     │                │                │───────────────▶│                │
     │                │                │                │                │
     │                │                │                │ 7. Update      │
     │                │                │                │    Local Cache │
     │                │                │                │────┐           │
     │                │                │                │    │           │
     │                │                │                │◀───┘           │
     │                │                │                │                │
     │                │                │                │ 8. Active      │
     │                │                │                │    Enforcement │
     │                │                │                │───────────────▶│
     │                │                │                │                │
```

---

## 5. Interaction Patterns

### 5.1 PEP-PDP Interaction

| Pattern | Description | When Used |
|---------|-------------|-----------|
| **Synchronous** | PEP calls PDP inline, waits for decision | Real-time tool calls (< 100ms) |
| **Asynchronous** | PEP publishes action event, PDP evaluates async | Batch analysis, non-critical actions |
| **Cached** | PEP caches PDP decisions with TTL | Repeated identical actions |
| **Pre-computed** | PDP pre-computes decisions for known actions | Scheduled actions, predictable patterns |

### 5.2 Evidence-Policy Interaction

| Pattern | Description | When Used |
|---------|-------------|-----------|
| **Inline** | Evidence collected during policy evaluation | Decision context, real-time validation |
| **Batch** | Evidence collected asynchronously | Historical analysis, trend detection |
| **Event-driven** | Evidence collected on specific events | Policy violations, threshold breaches |
| **Scheduled** | Evidence collected on a schedule | Compliance reporting, periodic audits |

### 5.3 Identity-Policy Interaction

| Pattern | Description | When Used |
|---------|-------------|-----------|
| **Binding** | Policies bound to specific agents | Agent-specific governance |
| **Inheritance** | Policies inherited from agent groups | Hierarchical governance |
| **Dynamic** | Policies applied based on runtime context | Context-aware governance |
| **Override** | Policies overridden by higher-priority policies | Emergency governance |

---

## 6. Technology Stack Summary

| Layer | Primary Technology | Secondary Technology |
|-------|-------------------|----------------------|
| Policy Definition | Cedar + Rego | OPA Bundle Server |
| Policy Decision | OPA + Cedar Engine | Redis (cache) |
| Policy Enforcement | MCP Gateway + Envoy | eBPF (kernel) |
| Evidence Collection | OSCAL 1.1.0 + immudb | WORM S3 |
| Observability | OpenTelemetry + OpenInference | Prometheus + Loki |
| Agent Identity | SPIFFE/SPIRE + Vault | PostgreSQL |
| Compliance Mapping | Custom UCT + Crosswalk | Neo4j (graph) |
| Analytics | Custom ML + Grafana | Snowflake |
| API | FastAPI (Python) | GraphQL |
| Event Streaming | Apache Kafka | NATS |
| Task Queue | Temporal | Celery |
| Deployment | Docker + Kubernetes | Helm |

---

## 7. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Ingress Controller                           │   │
│  │                    (NGINX / Traefik / Istio)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────┼─────────────────────────────────────┐  │
│  │                                 │                                     │  │
│  │  ┌──────────────────────────────▼──────────────────────────────────┐  │  │
│  │  │                     API Gateway (Kong / Envoy)                  │  │  │
│  │  │              AuthN, Rate Limiting, Routing                      │  │  │
│  │  └──────────────────────────────────────────────────────────────────┘  │  │
│  │                                 │                                     │  │
│  │  ┌──────────────────────────────┼──────────────────────────────────┐  │  │
│  │  │                              │                                  │  │  │
│  │  │  ┌─────────────────┐  ┌──────▼──────┐  ┌─────────────────────┐ │  │  │
│  │  │  │  Policy API     │  │  PDP Service │  │  PEP Gateway        │ │  │  │
│  │  │  │  (FastAPI)      │  │  (OPA)       │  │  (MCP Server)       │ │  │  │
│  │  │  │                 │  │              │  │                     │ │  │  │
│  │  │  │ • CRUD          │  │ • Rego eval  │  │ • Tool intercept    │ │  │  │
│  │  │  │ • Versioning    │  │ • Cedar eval  │  │ • AuthN/AuthZ       │ │  │  │
│  │  │  │ • Dependency    │  │ • Decision   │  │ • Rate limit        │ │  │  │
│  │  │  │   graph         │  │   engine     │  │ • Audit logging     │ │  │  │
│  │  │  └────────┬────────┘  └──────┬───────┘  └──────────┬──────────┘ │  │  │
│  │  │           │                │                      │            │  │  │
│  │  │           └────────────────┼──────────────────────┘            │  │  │
│  │  │                            │                                   │  │  │
│  │  │  ┌─────────────────────────▼─────────────────────────────────┐ │  │  │
│  │  │  │              Evidence Collection Service                  │ │  │  │
│  │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │  │  │
│  │  │  │  │Collector │  │Normalizer│  │Validator │  │  Store   │  │ │  │  │
│  │  │  │  │          │  │          │  │          │  │          │  │ │  │  │
│  │  │  │  │• API     │  │• Parse   │  │• Schema  │  │• WORM    │  │ │  │  │
│  │  │  │  │• Log     │  │• Map     │  │• Hash    │  │• Hash    │  │ │  │  │
│  │  │  │  │• File    │  │• Enrich  │  │• Control │  │• Custody │  │ │  │  │
│  │  │  │  │• Agent   │  │• Hash    │  │• Dup     │  │• Verify  │  │ │  │  │
│  │  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │ │  │  │
│  │  │  └──────────────────────────────────────────────────────────┘ │  │  │
│  │  │                                                               │  │  │
│  │  │  ┌──────────────────────────────────────────────────────────┐ │  │  │
│  │  │  │              Observability Stack                          │ │  │  │
│  │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │  │  │
│  │  │  │  │   OTel   │  │OpenInfer-│  │Analytics │  │  Grafana │  │ │  │  │
│  │  │  │  │Collector │  │  ence    │  │  Engine  │  │  + Loki  │  │ │  │  │
│  │  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │ │  │  │
│  │  │  └──────────────────────────────────────────────────────────┘ │  │  │
│  │  │                                                               │  │  │
│  │  │  ┌──────────────────────────────────────────────────────────┐ │  │  │
│  │  │  │              Agent Identity Service                      │ │  │  │
│  │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │  │  │
│  │  │  │  │  Agent   │  │  SPIFFE/ │  │  Trust   │  │  Policy  │  │ │  │  │
│  │  │  │  │ Registry │  │  SPIRE   │  │  Scoring │  │  Binding │  │ │  │  │
│  │  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │ │  │  │
│  │  │  └──────────────────────────────────────────────────────────┘ │  │  │
│  │  │                                                               │  │  │
│  │  │  ┌──────────────────────────────────────────────────────────┐ │  │  │
│  │  │  │              Compliance Mapping Service                  │ │  │  │
│  │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │  │  │
│  │  │  │  │Framework │  │Crosswalk │  │   Gap    │  │  Report  │  │ │  │  │
│  │  │  │  │ Adapters │  │  Engine  │  │ Analysis │  │ Generator│  │ │  │  │
│  │  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │ │  │  │
│  │  │  └──────────────────────────────────────────────────────────┘ │  │  │
│  │  │                                                               │  │  │
│  │  └───────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌───────────────────────────────────────────────────────────────┐  │  │
│  │  │                    Data Layer                                  │  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │  │  │
│  │  │  │PostgreSQL│  │  Redis   │  │  Kafka   │  │  MinIO   │       │  │  │
│  │  │  │(policies)│  │  (cache) │  │ (events) │  │  (WORM)  │       │  │  │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │  │  │
│  │  │  │  Neo4j   │  │  immudb  │  │  Tempo   │  │  Vault   │       │  │  │
│  │  │  │  (graph) │  │  (audit) │  │ (traces) │  │  (secrets)│      │  │  │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │  │  │
│  │  └───────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Security Architecture

### 8.1 Trust Boundaries

| Boundary | Protection Mechanism |
|----------|---------------------|
| Agent ↔ PEP | mTLS (SPIFFE SVIDs) |
| PEP ↔ PDP | mTLS + service account tokens |
| PDP ↔ Evidence Store | mTLS + RBAC |
| Evidence Store ↔ Audit | WORM + hash chaining |
| All components ↔ API Gateway | OAuth 2.1 + OIDC |

### 8.2 Secret Management

| Secret Type | Storage | Rotation |
|-------------|---------|----------|
| mTLS certificates | HashiCorp Vault | 24 hours |
| API tokens | HashiCorp Vault | 7 days |
| Encryption keys | HSM (AWS CloudHSM) | 90 days |
| Database credentials | HashiCorp Vault | 30 days |
| Signing keys | HSM | 1 year |

### 8.3 Audit Requirements

Every action in the system MUST produce an audit record:

| Action | Audit Record | Evidence Level |
|--------|-------------|----------------|
| Policy created/updated/deleted | Policy change event | L2 |
| Agent registered/modified/terminated | Agent lifecycle event | L2 |
| Enforcement decision made | Decision certificate | L2 |
| Evidence collected/modified/accessed | Custody event | L2 |
| Compliance report generated | Report generation event | L2 |
| Identity issued/rotated/revoked | Identity event | L2 |

---

## 9. Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| PDP evaluation latency (p99) | < 50ms | OPA evaluation time |
| PEP enforcement latency (p99) | < 100ms | End-to-end tool call |
| Evidence collection latency | < 5 seconds | Collector to store |
| Audit log verification (10K entries) | < 2 seconds | Hash chain verification |
| Policy compilation time | < 5 seconds | Cedar to Rego |
| Agent action throughput | 1M+ actions/day | Aggregate across agents |
| Evidence packaging time | < 15 minutes | Full audit package |
| System availability | 99.9% | Uptime SLA |

---

## 10. Failure Modes & Resilience

| Failure | Impact | Mitigation |
|---------|--------|------------|
| PDP unavailable | Cannot make decisions | PEP falls back to cached decisions or fail-closed |
| Evidence store unavailable | Cannot store evidence | PEP queues evidence locally, replays when available |
| Agent identity service unavailable | Cannot authenticate agents | PEP uses cached SVIDs with short TTL |
| Compliance mapping service unavailable | Cannot generate reports | Reports generated from cached mappings |
| PEP gateway unavailable | Agents cannot execute actions | Agents retry with exponential backoff |
| Policy compiler unavailable | Cannot deploy new policies | Existing policies continue to enforce |

---

## 11. Appendix A: Component Interaction Matrix

| Component | Policy Def | PDP | PEP | Evidence | Observability | Identity | Compliance |
|-----------|-----------|-----|-----|----------|--------------|----------|------------|
| **Policy Definition** | — | Compiles to | — | Stores policy versions | Traces policy changes | — | Maps to frameworks |
| **PDP** | Consumes | — | Serves decisions | Stores decision evidence | Traces evaluations | Validates agent identity | — |
| **PEP** | — | Queries | — | Stores enforcement evidence | Traces enforcement | Authenticates agents | — |
| **Evidence** | — | — | — | — | Stores audit logs | — | Maps to controls |
| **Observability** | — | — | — | — | — | — | — |
| **Identity** | — | — | — | Stores identity evidence | Traces identity events | — | — |
| **Compliance** | — | — | — | Consumes evidence | — | — | — |

---

## 12. Appendix B: Data Flow Summary

| Flow | Source | Destination | Data | Frequency |
|------|--------|-------------|------|-----------|
| Policy Definition | Policy Author | Policy Store | Cedar/Rego policies | On change |
| Policy Compilation | Policy Compiler | PDP | Compiled Rego bundles | On change |
| Decision Request | PEP | PDP | Action context (JSON) | Per agent action |
| Decision Response | PDP | PEP | Decision certificate | Per agent action |
| Evidence Collection | Collectors | Evidence Store | OSCAL evidence | Continuous |
| Evidence Verification | Evidence Store | Compliance | Verified evidence | Scheduled |
| Identity Verification | PEP | Identity Service | SVID + capabilities | Per agent action |
| Compliance Report | Compliance | Report Generator | Framework-specific reports | Scheduled |
| Observability | All components | OTel Collector | Traces, metrics, logs | Continuous |
| Audit Trail | All components | immudb | Hash-chained audit events | Continuous |

---

*End of reference architecture.*
