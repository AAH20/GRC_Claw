# GRC_Claw Component Design Specification

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**Parent Documents:** GRC_Claw Reference Architecture v1.0, GRC_Claw Deployment Specification v2.0

---

## 1. Component Interface Specifications

### 1.1 Interface Specification Methodology

Each component interface is specified using a consistent template:

| Field | Description |
|-------|-------------|
| **Interface ID** | Unique identifier (e.g., `IF-PDP-001`) |
| **Protocol** | gRPC, REST, MCP, Kafka, etc. |
| **Authentication** | mTLS, OAuth 2.1, SPIFFE SVID |
| **Authorization** | RBAC, ABAC, Cedar policy |
| **Request Schema** | JSON Schema / Protobuf |
| **Response Schema** | JSON Schema / Protobuf |
| **Error Model** | Standardized error envelope |
| **Rate Limit** | Requests per second per client |
| **SLA** | Latency target, availability target |
| **Idempotency** | At-least-once, exactly-once, at-most-once |

### 1.2 Standard Error Envelope

All GRC_Claw components return errors in a unified format:

```json
{
  "error": {
    "code": "GRC-4001",
    "message": "Policy evaluation failed: invalid principal",
    "type": "PolicyEvaluationError",
    "details": {
      "policy_id": "pol-data-access-001",
      "principal": "agent-42",
      "reason": "principal not found in registry"
    },
    "request_id": "req-uuid-v4",
    "timestamp": "2026-10-01T14:30:00.123Z",
    "trace_id": "trace-uuid-v4",
    "documentation": "https://docs.grc-claw.io/errors/GRC-4001"
  }
}
```

**Error Code Ranges:**

| Range | Category | Examples |
|-------|----------|----------|
| GRC-1xxx | Authentication | Invalid SVID, expired certificate, missing credentials |
| GRC-2xxx | Authorization | Policy denied, insufficient clearance, quarantine active |
| GRC-3xxx | Policy | Parse error, evaluation error, compilation failure |
| GRC-4xxx | Request | Validation error, malformed input, missing field |
| GRC-5xxx | Resource | Not found, already exists, quota exceeded |
| GRC-6xxx | System | Internal error, dependency unavailable, timeout |
| GRC-7xxx | Compliance | Framework mapping error, evidence gap, report failure |

### 1.3 Policy Definition Layer Interfaces

#### IF-POL-001: Policy Authoring API

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-POL-001 |
| **Protocol** | REST (HTTP/1.1 + HTTP/2) |
| **Base URL** | `https://policy-api.grc-claw.internal/v1` |
| **Authentication** | OAuth 2.1 (client credentials + mTLS) |
| **Authorization** | RBAC (roles: `policy-author`, `policy-reviewer`, `policy-admin`) |
| **Rate Limit** | 100 req/s per client |
| **Idempotency** | At-least-once (client-supplied idempotency key) |

**Endpoints:**

```
POST   /policies                      # Create new policy
GET    /policies                      # List policies (paginated)
GET    /policies/{id}                 # Get policy by ID
PUT    /policies/{id}                 # Update policy
DELETE /policies/{id}                 # Delete policy (soft)
POST   /policies/{id}/compile         # Compile Cedar → Rego
POST   /policies/{id}/dry-run         # Dry-run evaluation
POST   /policies/{id}/activate        # Transition to active
POST   /policies/{id}/deprecate       # Transition to deprecated
GET    /policies/{id}/versions        # List versions
GET    /policies/{id}/dependencies    # Get dependency graph
POST   /policies/search               # Full-text search
```

**Create Policy Request:**

```json
{
  "name": "agent-data-access-policy",
  "description": "Controls agent access to data classifications",
  "framework_tags": ["SOC2", "ISO-27001", "GDPR"],
  "cedar_policy": "permit(principal in Agent::\"data-analyst\", ...);",
  "metadata": {
    "owner": "security-team",
    "review_cycle": "quarterly",
    "risk_tier": "high"
  }
}
```

**Create Policy Response (201 Created):**

```json
{
  "id": "pol-uuid-v4",
  "name": "agent-data-access-policy",
  "version": "1.0.0",
  "status": "draft",
  "cedar_policy": "permit(principal in Agent::\"data-analyst\", ...);",
  "rego_policy": null,
  "compilation_status": "pending",
  "created_by": "user-42",
  "created_at": "2026-10-01T14:30:00Z",
  "effective_from": null,
  "effective_until": null,
  "_links": {
    "self": "/v1/policies/pol-uuid-v4",
    "compile": "/v1/policies/pol-uuid-v4/compile",
    "dry_run": "/v1/policies/pol-uuid-v4/dry-run",
    "versions": "/v1/policies/pol-uuid-v4/versions"
  }
}
```

#### IF-POL-002: Policy Compilation Interface

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-POL-002 |
| **Protocol** | Internal gRPC |
| **Service** | `grc.policy.CompilationService` |
| **Authentication** | mTLS (service account) |
| **Rate Limit** | 10 req/s per PDP instance |

**Protobuf Definition:**

```protobuf
syntax = "proto3";
package grc.policy.v1;

service CompilationService {
  rpc Compile(CompileRequest) returns (CompileResponse);
  rpc Validate(ValidateRequest) returns (ValidateResponse);
  rpc DryRun(DryRunRequest) returns (DryRunResponse);
}

message CompileRequest {
  string policy_id = 1;
  string cedar_source = 2;
  string target_engine = 3;  // "rego" | "cedar-native"
  map<string, string> options = 4;
}

message CompileResponse {
  string policy_id = 1;
  string compiled_output = 2;
  CompilationStatus status = 3;
  repeated Diagnostic diagnostics = 4;
  string evidence_hash = 5;
  int64 compilation_time_ms = 6;
}

message DryRunRequest {
  string policy_id = 1;
  repeated DryRunCase test_cases = 2;
}

message DryRunCase {
  string name = 1;
  string input_document = 2;  // JSON
  string expected_verdict = 3;
}

message DryRunResponse {
  string policy_id = 1;
  repeated DryRunResult results = 2;
  int32 passed = 3;
  int32 failed = 4;
  int32 total = 5;
}

enum CompilationStatus {
  COMPILATION_STATUS_UNSPECIFIED = 0;
  COMPILATION_STATUS_SUCCESS = 1;
  COMPILATION_STATUS_PARTIAL = 2;
  COMPILATION_STATUS_FAILURE = 3;
}

message Diagnostic {
  Severity severity = 1;
  string message = 2;
  int32 line = 3;
  int32 column = 4;
  string span = 5;
}

enum Severity {
  SEVERITY_UNSPECIFIED = 0;
  SEVERITY_INFO = 1;
  SEVERITY_WARNING = 2;
  SEVERITY_ERROR = 3;
}
```

### 1.4 Policy Decision Point (PDP) Interfaces

#### IF-PDP-001: Decision Evaluation API

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-PDP-001 |
| **Protocol** | gRPC (primary), REST (external) |
| **Service** | `grc.pdp.DecisionService` |
| **gRPC Port** | 9090 |
| **REST Port** | 8080 |
| **Authentication** | mTLS (SPIFFE SVID) |
| **Authorization** | Service-level RBAC |
| **Rate Limit** | 10,000 req/s per PEP instance |
| **SLA** | p99 < 50ms, availability 99.95% |
| **Idempotency** | At-least-once (decision-id deduplication) |

**Protobuf Definition:**

```protobuf
syntax = "proto3";
package grc.pdp.v1;

service DecisionService {
  rpc Evaluate(EvaluateRequest) returns (EvaluateResponse);
  rpc StreamEvaluate(stream EvaluateRequest) returns (stream EvaluateResponse);
  rpc BatchEvaluate(BatchEvaluateRequest) returns (BatchEvaluateResponse);
  rpc GetDecision(GetDecisionRequest) returns (GetDecisionResponse);
  rpc VerifyDecision(VerifyDecisionRequest) returns (VerifyDecisionResponse);
}

message EvaluateRequest {
  string request_id = 1;
  string agent_id = 2;
  string action = 3;
  string resource = 4;
  Context context = 5;
  repeated string policy_ids = 6;  // Optional: restrict to specific policies
  EvaluationMode mode = 7;
  int32 cache_ttl_seconds = 8;
}

message Context {
  string environment = 1;
  string tenant_id = 2;
  string session_id = 3;
  int64 timestamp = 4;
  map<string, string> attributes = 5;
  ApprovalTicket approval_ticket = 6;
  string ip_address = 7;
  string user_agent = 8;
}

message EvaluateResponse {
  string decision_id = 1;
  Verdict verdict = 2;
  string policy_id = 3;
  string policy_version = 4;
  string reason = 5;
  RedactionRule redaction_rules = 6;
  string evidence_hash = 7;
  int64 evaluation_time_ms = 8;
  int64 timestamp = 9;
  string signature = 10;
  repeated PolicyMatch matched_policies = 11;
  DecisionCertificate certificate = 12;
}

enum Verdict {
  VERDICT_UNSPECIFIED = 0;
  VERDICT_ALLOW = 1;
  VERDICT_ALLOW_WITH_REDACTION = 2;
  VERDICT_REQUIRE_APPROVAL = 3;
  VERDICT_DENY = 4;
  VERDICT_QUARANTINE = 5;
}

message RedactionRule {
  repeated string fields = 1;
  RedactionStrategy strategy = 2;
  string replacement = 3;
}

enum RedactionStrategy {
  REDACTION_STRATEGY_UNSPECIFIED = 0;
  REDACTION_STRATEGY_MASK = 1;
  REDACTION_STRATEGY_REMOVE = 2;
  REDACTION_STRATEGY_TOKENIZE = 3;
  REDACTION_STRATEGY_ENCRYPT = 4;
}

message DecisionCertificate {
  string certificate_id = 1;
  string decision_id = 2;
  string verdict = 3;
  string policy_id = 4;
  string policy_version = 5;
  string agent_id = 6;
  string action = 7;
  string resource = 8;
  string evidence_hash = 9;
  int64 issued_at = 10;
  int64 expires_at = 11;
  string issuer = 12;
  string signature = 13;
  string signing_algorithm = 14;
}

message BatchEvaluateRequest {
  repeated EvaluateRequest requests = 1;
  bool fail_fast = 2;
}

message BatchEvaluateResponse {
  repeated EvaluateResponse responses = 1;
  int32 succeeded = 2;
  int32 failed = 3;
}

enum EvaluationMode {
  EVALUATION_MODE_UNSPECIFIED = 0;
  EVALUATION_MODE_SYNC = 1;
  EVALUATION_MODE_ASYNC = 2;
  EVALUATION_MODE_CACHED = 3;
  EVALUATION_MODE_PRECOMPUTED = 4;
}

message PolicyMatch {
  string policy_id = 1;
  string policy_version = 2;
  Verdict verdict = 3;
  string reason = 4;
  int64 evaluation_time_ms = 5;
}

message ApprovalTicket {
  string ticket_id = 1;
  string status = 2;
  string approver = 3;
  int64 approved_at = 4;
  string approval_chain = 5;
}

message GetDecisionRequest {
  string decision_id = 1;
}

message GetDecisionResponse {
  DecisionCertificate certificate = 1;
  bool valid = 2;
  string revocation_reason = 3;
}

message VerifyDecisionRequest {
  string decision_id = 1;
  string signature = 2;
  string evidence_hash = 3;
}

message VerifyDecisionResponse {
  bool valid = 1;
  string reason = 2;
  int64 verified_at = 3;
}
```

#### IF-PDP-002: Policy Bundle Distribution

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-PDP-002 |
| **Protocol** | OPA Bundle API (HTTP/2) |
| **Authentication** | mTLS + bundle signing key |
| **Rate Limit** | 1 bundle fetch per 30s per PDP instance |

**Bundle Structure:**

```
bundle.tar.gz
├── .manifest
│   {
│     "revision": "20261001-143000",
│     "roots": ["grc/agent"],
│     "timestamp": 1727790600
│   }
├── grc/
│   ├── agent/
│   │   ├── data_access.rego
│   │   ├── pii_access.rego
│   │   └── network_access.rego
│   └── system/
│       ├── audit.rego
│       └── integrity.rego
└── data/
    └── context_enrichment.json
```

**Bundle Signing:**

```json
{
  "bundle_hash": "sha256:abc123...",
  "signed_at": "2026-10-01T14:30:00Z",
  "signed_by": "policy-compiler-01",
  "signature_algorithm": "ecdsa-p256",
  "signature": "base64-encoded-signature",
  "previous_bundle_hash": "sha256:def456..."
}
```

### 1.5 Policy Enforcement Point (PEP) Interfaces

#### IF-PEP-001: MCP Gateway Tool Interception

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-PEP-001 |
| **Protocol** | MCP (Model Context Protocol) over stdio/SSE |
| **Authentication** | mTLS (SPIFFE SVID) + MCP session token |
| **Authorization** | PDP decision per tool call |
| **Rate Limit** | 1000 tool calls/s per agent |
| **SLA** | p99 < 10ms overhead |

**MCP Tool Call Flow:**

```
Agent                    MCP Gateway (PEP)              PDP
  │                            │                          │
  │ 1. tools/call              │                          │
  │   (tool_name, args)        │                          │
  │───────────────────────────▶│                          │
  │                            │                          │
  │                            │ 2. Extract context       │
  │                            │    (agent_id, action,    │
  │                            │     resource, args)      │
  │                            │────┐                     │
  │                            │    │                     │
  │                            │◀───┘                     │
  │                            │                          │
  │                            │ 3. Evaluate              │
  │                            │─────────────────────────▶│
  │                            │                          │
  │                            │ 4. Decision              │
  │                            │◀─────────────────────────│
  │                            │                          │
  │                            │ 5. Apply decision        │
  │                            │────┐                     │
  │                            │    │                     │
  │                            │◀───┘                     │
  │                            │                          │
  │ 6. Tool result             │                          │
  │   (or error)               │                          │
  │◀───────────────────────────│                          │
  │                            │                          │
  │                            │ 7. Log evidence          │
  │                            │────┐                     │
  │                            │    │                     │
  │                            │◀───┘                     │
```

**MCP Gateway Configuration:**

```yaml
mcp_gateway:
  server:
    name: "grc-claw-pep-gateway"
    version: "1.0.0"
    transport: "sse"  # stdio | sse | http
    port: 8080
  
  enforcement:
    mode: "synchronous"  # synchronous | asynchronous | cached
    fail_policy: "closed"  # closed | open
    cache_ttl_seconds: 300
    max_concurrent_evaluations: 1000
  
  authentication:
    method: "mtls"
    spiffe_id_pattern: "spiffe://grc-claw.io/ns/{namespace}/sa/{service_account}"
    cert_ttl: "24h"
  
  rate_limiting:
    requests_per_second: 1000
    burst_size: 2000
    per_agent_limit: 100
  
  audit:
    log_all_decisions: true
    log_all_tool_calls: true
    evidence_level: "L2"
```

#### IF-PEP-002: Sidecar Proxy Interface

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-PEP-002 |
| **Protocol** | Envoy xDS (gRPC) + HTTP filter |
| **Authentication** | mTLS (Istio service mesh) |
| **Rate Limit** | Configured per-route |

**Envoy Filter Configuration:**

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: grc-pep-filter
  namespace: grc-claw-control-plane
spec:
  workloadSelector:
    labels:
      app: agent-service
  configPatches:
    - applyTo: HTTP_FILTER
      match:
        context: SIDECAR_INBOUND
        listener:
          filterChain:
            filter:
              name: envoy.filters.network.http_connection_manager
      patch:
        operation: INSERT_BEFORE
        value:
          name: grc.pep.filter
          typed_config:
            "@type": type.googleapis.com/grc.pep.v1.FilterConfig
            pdp_endpoint: "pdp-service.grc-claw-control-plane.svc:9090"
            timeout_ms: 50
            fail_closed: true
            cache:
              enabled: true
              ttl_seconds: 300
              max_entries: 10000
            enforcement_points:
              - path: "/api/v1/agents/*/actions"
                methods: ["POST"]
              - path: "/api/v1/agents/*/tools/*"
                methods: ["POST", "PUT", "DELETE"]
```

#### IF-PEP-003: Kernel Enforcer Interface

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-PEP-003 |
| **Protocol** | eBPF maps + netlink |
| **Authentication** | N/A (kernel-level) |
| **Authorization** | seccomp profiles + eBPF programs |

**eBPF Program Structure:**

```c
// grc_enforcer.bpf.c
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct grc_policy_key {
    u32 agent_id;
    u32 resource_id;
    u32 action_type;
};

struct grc_policy_value {
    u8 verdict;
    u8 redaction_required;
    u64 expiry_ns;
    char reason[128];
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10000);
    __type(key, struct grc_policy_key);
    __type(value, struct grc_policy_value);
} grc_policy_map SEC(".maps");

SEC("lsm/file_open")
int BPF_PROGRM(grc_file_access, struct file *file, int mask)
{
    u32 agent_id = get_current_agent_id();
    u32 resource_id = get_file_resource_id(file);
    
    struct grc_policy_key key = {
        .agent_id = agent_id,
        .resource_id = resource_id,
        .action_type = GRC_ACTION_FILE_READ
    };
    
    struct grc_policy_value *policy = bpf_map_lookup_elem(&grc_policy_map, &key);
    if (!policy) {
        return -EPERM;  // Fail closed
    }
    
    if (policy->verdict == GRC_VERDICT_DENY) {
        return -EPERM;
    }
    
    if (policy->verdict == GRC_VERDICT_QUARANTINE) {
        bpf_send_signal(SIGKILL);
        return -EPERM;
    }
    
    return 0;
}

char _license[] SEC("license") = "GPL";
```

### 1.6 Evidence Collection Layer Interfaces

#### IF-EVD-001: Evidence Ingestion API

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-EVD-001 |
| **Protocol** | REST + Kafka (async) |
| **Base URL** | `https://evidence-api.grc-claw.internal/v1` |
| **Authentication** | mTLS + OAuth 2.1 |
| **Rate Limit** | 10,000 events/s |
| **SLA** | p99 < 5s end-to-end |

**Endpoints:**

```
POST   /evidence                      # Submit evidence
GET    /evidence/{id}                 # Retrieve evidence
POST   /evidence/batch                # Batch submit
POST   /evidence/{id}/verify          # Verify evidence integrity
GET    /evidence/{id}/chain-of-custody # Get custody chain
POST   /evidence/search               # Search evidence
GET    /evidence/health               # Collection health
```

**Submit Evidence Request:**

```json
{
  "evidence_id": "evd-uuid-v4",
  "type": "observation",
  "source": "agent-scanner-01",
  "control_id": "AC-2",
  "framework_mappings": ["nist_800_53", "soc2"],
  "content": {
    "format": "oscal-1.1.0",
    "data": { /* OSCAL assessment-results */ }
  },
  "metadata": {
    "collected_at": "2026-10-01T14:30:00Z",
    "collection_method": "api-probe",
    "environment": "production",
    "tenant_id": "tenant-acme"
  },
  "raw_evidence": {
    "format": "json",
    "data": { /* Original unprocessed data */ }
  }
}
```

**Submit Evidence Response (202 Accepted):**

```json
{
  "evidence_id": "evd-uuid-v4",
  "status": "received",
  "verification_level": "L0",
  "estimated_processing_time_ms": 2000,
  "queue_position": 42,
  "_links": {
    "self": "/v1/evidence/evd-uuid-v4",
    "status": "/v1/evidence/evd-uuid4/status"
  }
}
```

#### IF-EVD-002: Evidence Normalization Pipeline

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-EVD-002 |
| **Protocol** | Kafka consumer groups |
| **Topics** | `evidence.raw` → `evidence.normalized` → `evidence.validated` |
| **Authentication** | mTLS (Kafka SASL) |
| **Throughput** | 50,000 events/s per consumer group |

**Normalizer Configuration:**

```yaml
normalizer:
  input_topic: "evidence.raw"
  output_topic: "evidence.normalized"
  error_topic: "evidence.errors"
  consumer_group: "grc-normalizer"
  
  pipeline:
    - stage: "parse"
      config:
        formats: ["json", "xml", "yaml", "csv"]
        encoding: "utf-8"
    
    - stage: "map"
      config:
        target_schema: "oscal-1.1.0"
        mapping_rules: "/config/oscal-mapping.yaml"
    
    - stage: "enrich"
      config:
        add_timestamp: true
        add_source_metadata: true
        add_geolocation: false
        add_threat_intel: false
    
    - stage: "hash"
      config:
        algorithm: "sha256"
        include_metadata: true
    
    - stage: "timestamp"
      config:
        method: "rfc3161"
        timestamp_authority: "https://tsa.grc-claw.internal"
```

### 1.7 Agent Identity Layer Interfaces

#### IF-IDT-001: Agent Registration API

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-IDT-001 |
| **Protocol** | REST + GraphQL |
| **Base URL** | `https://identity-api.grc-claw.internal/v1` |
| **Authentication** | OAuth 2.1 (admin), mTLS (agent) |
| **Authorization** | RBAC (roles: `identity-admin`, `agent-registrar`) |

**Endpoints:**

```
POST   /agents                      # Register new agent
GET    /agents                      # List agents
GET    /agents/{id}                 # Get agent details
PUT    /agents/{id}                 # Update agent
DELETE /agents/{id}                 # Terminate agent
POST   /agents/{id}/suspend         # Suspend agent
POST   /agents/{id}/reinstate       # Reinstate agent
GET    /agents/{id}/trust-score     # Get trust score
GET    /agents/{id}/capabilities    # Get capabilities
POST   /agents/{id}/rotate-identity # Rotate SVID
```

**Register Agent Request:**

```json
{
  "name": "data-analyst-agent-01",
  "type": "agent",
  "framework": "langchain",
  "owner": "data-team",
  "risk_tier": "limited",
  "capabilities": [
    {
      "name": "read-data",
      "description": "Read data from approved sources",
      "permissions": ["data:read"],
      "resource_scope": "s3://data/public/*"
    },
    {
      "name": "query-database",
      "description": "Query analytics database",
      "permissions": ["db:read"],
      "resource_scope": "postgresql://analytics/readonly"
    }
  ],
  "metadata": {
    "version": "2.1.0",
    "deployment": "production",
    "team": "data-engineering"
  }
}
```

**Register Agent Response (201 Created):**

```json
{
  "agent_id": "agent-uuid-v4",
  "name": "data-analyst-agent-01",
  "lifecycle_stage": "proposed",
  "status": "pending_approval",
  "spiffe_id": "spiffe://grc-claw.io/ns/production/sa/agent-uuid-v4",
  "mtls_cert": null,
  "trust_score": {
    "value": 50,
    "grade": "C",
    "last_evaluated": null
  },
  "policy_bindings": [],
  "created_at": "2026-10-01T14:30:00Z",
  "_links": {
    "self": "/v1/agents/agent-uuid-v4",
    "approve": "/v1/agents/agent-uuid-v4/approve",
    "capabilities": "/v1/agents/agent-uuid-v4/capabilities"
  }
}
```

#### IF-IDT-002: SVID Issuance (SPIFFE/SPIRE)

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-IDT-002 |
| **Protocol** | SPIFFE Workload API (gRPC) |
| **Service** | `grpc.spiffe.io` |
| **Authentication** | mTLS (node attestation) |
| **Rate Limit** | 100 SVIDs/min per agent |

**SVID Structure:**

```json
{
  "spiffe_id": "spiffe://grc-claw.io/ns/production/sa/agent-uuid-v4",
  "x509_svid": {
    "cert_chain": ["base64-encoded-cert"],
    "private_key": "base64-encoded-key",
    "expires_at": "2026-10-02T14:30:00Z",
    "serial_number": "0a:0b:0c:0d",
    "subject": "CN=agent-uuid-v4,O=GRC_Claw,C=US",
    "uri_sans": ["spiffe://grc-claw.io/ns/production/sa/agent-uuid-v4"]
  },
  "jwt_svid": {
    "token": "eyJhbGciOi...",
    "expires_at": "2026-10-01T15:30:00Z",
    "audiences": ["grc-claw"]
  }
}
```

### 1.8 Compliance Mapping Layer Interfaces

#### IF-CMP-001: Crosswalk Engine API

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-CMP-001 |
| **Protocol** | REST + GraphQL |
| **Base URL** | `https://compliance-api.grc-claw.internal/v1` |
| **Authentication** | OAuth 2.1 |
| **Rate Limit** | 1000 req/s |

**Endpoints:**

```
GET    /frameworks                    # List supported frameworks
GET    /frameworks/{id}/controls      # List controls for framework
POST   /crosswalk/map                 # Map control to frameworks
GET    /crosswalk/{control_id}        # Get mappings for control
POST   /reports/generate             # Generate compliance report
GET    /reports/{id}                 # Get report
GET    /gaps                         # Get compliance gaps
POST   /gaps/analyze                 # Run gap analysis
```

**Generate Report Request:**

```json
{
  "framework": "soc2",
  "time_range": {
    "start": "2026-07-01T00:00:00Z",
    "end": "2026-10-01T00:00:00Z"
  },
  "controls": ["CC6.1", "CC6.2", "CC6.3"],
  "format": "oscal-1.1.0",
  "include_evidence": true,
  "include_gaps": true
}
```

**Generate Report Response (202 Accepted):**

```json
{
  "report_id": "rpt-uuid-v4",
  "status": "generating",
  "estimated_completion_time_ms": 300000,
  "_links": {
    "self": "/v1/reports/rpt-uuid-v4",
    "status": "/v1/reports/rpt-uuid-v4/status"
  }
}
```

### 1.9 Observability Interfaces

#### IF-OBS-001: OpenTelemetry Collector

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-OBS-001 |
| **Protocol** | OTLP (gRPC + HTTP) |
| **gRPC Port** | 4317 |
| **HTTP Port** | 4318 |
| **Authentication** | mTLS |
| **Rate Limit** | 100,000 spans/s |

**OTel Collector Configuration:**

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4337
        tls:
          cert_file: /certs/server.crt
          key_file: /certs/server.key
          client_ca_file: /certs/ca.crt
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  memory_limiter:
    limit_mib: 4000
    spike_limit_mib: 500
  resource:
    attributes:
      - key: grc.component
        from_attribute: service.name
        action: upsert
      - key: grc.environment
        value: production
        action: upsert
      - key: grc.tenant_id
        from_attribute: tenant.id
        action: upsert
  filter:
    error_mode: ignore
    traces:
      span:
        - attributes["grc.decision"] == "DENY"
        - attributes["grc.decision"] == "QUARANTINE"

exporters:
  jaeger:
    endpoint: jaeger-collector:14250
    tls:
      insecure: false
      cert_file: /certs/client.crt
      key_file: /certs/client.key
  prometheusremotewrite:
    endpoint: http://prometheus:9090/api/v1/write
  loki:
    endpoint: http://loki:3100/loki/api/v1/push

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [prometheusremotewrite]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [loki]
```

#### IF-OBS-002: Analytics Engine API

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-OBS-002 |
| **Protocol** | REST + gRPC |
| **Base URL** | `https://analytics-api.grc-claw.internal/v1` |
| **Authentication** | OAuth 2.1 |
| **Rate Limit** | 100 req/s |

**Endpoints:**

```
POST   /analytics/risk-score         # Calculate risk score
GET    /analytics/risk-score/{agent_id}  # Get agent risk score
POST   /analytics/anomaly-detect     # Detect anomalies
GET    /analytics/trends             # Get trend analysis
POST   /analytics/drift-detect       # Detect behavior drift
GET    /analytics/compliance-posture # Get compliance posture
```

### 1.10 Event Streaming Interfaces

#### IF-EVT-001: Kafka Event Bus

| Attribute | Value |
|-----------|-------|
| **Interface ID** | IF-EVT-001 |
| **Protocol** | Kafka protocol (SASL_SSL) |
| **Authentication** | SASL/SCRAM + mTLS |
| **Authorization** | ACL per topic |
| **Throughput** | 100,000 msg/s per partition |

**Event Envelope:**

```json
{
  "event_id": "evt-uuid-v4",
  "event_type": "grc.decision.made",
  "event_version": "1.0",
  "timestamp": "2026-10-01T14:30:00.123Z",
  "source": "pdp-service-01",
  "trace_id": "trace-uuid-v4",
  "span_id": "span-uuid-v4",
  "data": {
    "decision_id": "dec-uuid-v4",
    "agent_id": "agent-42",
    "action": "read",
    "resource": "s3://data/public/dataset.csv",
    "verdict": "ALLOW",
    "policy_id": "pol-data-access-001",
    "evidence_hash": "sha256:abc123..."
  },
  "metadata": {
    "environment": "production",
    "tenant_id": "tenant-acme",
    "region": "us-east-1"
  }
}
```

**Topic Catalog:**

| Topic | Partitions | Retention | RF | Schema |
|-------|-----------|-----------|----|--------|
| `grc.decisions` | 12 | 7 days | 3 | decision.avsc |
| `grc.evidence.collected` | 12 | 7 days | 3 | evidence.avsc |
| `grc.policy.changes` | 6 | 30 days | 3 | policy-change.avsc |
| `grc.agent.lifecycle` | 6 | 30 days | 3 | agent-lifecycle.avsc |
| `grc.compliance.updates` | 6 | 7 days | 3 | compliance-update.avsc |
| `grc.audit.events` | 12 | 90 days | 3 | audit-event.avsc |
| `grc.anomaly.alerts` | 6 | 7 days | 3 | anomaly-alert.avsc |
| `grc.identity.events` | 6 | 30 days | 3 | identity-event.avsc |

---

## 2. Data Flow Diagrams

### 2.1 End-to-End Agent Action Flow (Detailed)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           END-TO-END AGENT ACTION FLOW                              │
│                                                                                     │
│  Agent          PEP Gateway       PDP           Evidence       Compliance    Identity │
│  ─────          ───────────       ───           ────────       ──────────    ─────── │
│                                                                                     │
│  1. Tool Call    ┌─────────┐                                                               │
│ ───────────────▶│ Extract │                                                               │
│                  │ Context │                                                               │
│                  └────┬────┘                                                               │
│                       │                                                                    │
│                  2. AuthN (mTLS + SVID)                                                   │
│                  ┌────┴────┐                                                               │
│                  │ Verify  │                                                               │
│                  │ SVID    │                                                               │
│                  └────┬────┘                                                               │
│                       │                                                                    │
│                  3. Build Input Document                                                   │
│                  ┌────┴────┐                                                               │
│                  │ Enrich  │                                                               │
│                  │ Context │                                                               │
│                  └────┬────┘                                                               │
│                       │                                                                    │
│                  4. Query PDP ──────────────────▶ ┌─────────────┐                         │
│                                                  │  Evaluate   │                         │
│                                                  │  Policies   │                         │
│                                                  │             │                         │
│                                                  │ ┌─────────┐ │                         │
│                                                  │ │ Schema  │ │                         │
│                                                  │ │ Validate│ │                         │
│                                                  │ └────┬────┘ │                         │
│                                                  │      │      │                         │
│                                                  │ ┌────▼────┐ │                         │
│                                                  │ │ Context │ │                         │
│                                                  │ │ Enrich  │ │                         │
│                                                  │ └────┬────┘ │                         │
│                                                  │      │      │                         │
│                                                  │ ┌────▼────┐ │                         │
│                                                  │ │ Cedar   │ │                         │
│                                                  │ │ Eval    │ │                         │
│                                                  │ └────┬────┘ │                         │
│                                                  │      │      │                         │
│                                                  │ ┌────▼────┐ │                         │
│                                                  │ │ Rego    │ │                         │
│                                                  │ │ Eval    │ │                         │
│                                                  │ └────┬────┘ │                         │
│                                                  │      │      │                         │
│                                                  │ ┌────▼────┐ │                         │
│                                                  │ │ Decision│ │                         │
│                                                  │ │ Aggregate│ │                         │
│                                                  │ └────┬────┘ │                         │
│                                                  │      │      │                         │
│                                                  │ ┌────▼────┐ │                         │
│                                                  │ │ Evidence│ │                         │
│                                                  │ │ Hash    │ │                         │
│                                                  │ └────┬────┘ │                         │
│                                                  │      │      │                         │
│                                                  │ ┌────▼────┐ │                         │
│                                                  │ │ Sign    │ │                         │
│                                                  │ │ Decision│ │                         │
│                                                  │ └────┬────┘ │                         │
│                                                  └─────┼──────┘                         │
│                                                        │                                    │
│                  5. Decision Certificate ◀─────────────┘                                    │
│                  ┌─────────────┐                                                               │
│                  │ Verify      │                                                               │
│                  │ Signature   │                                                               │
│                  └──────┬──────┘                                                               │
│                         │                                                                      │
│                  6. Apply Decision                                                           │
│                  ┌──────▼──────┐                                                               │
│                  │             │                                                               │
│                  │ ALLOW       │──────────────▶ Execute Tool Call                          │
│                  │ ALLOW_REDACT│──────────────▶ Execute with Redaction                     │
│                  │ REQUIRE_APPR│──────────────▶ Queue for Human Review                      │
│                  │ DENY        │──────────────▶ Return Policy Violation Error               │
│                  │ QUARANTINE  │──────────────▶ Isolate Agent                              │
│                  │             │                                                               │
│                  └──────┬──────┘                                                               │
│                         │                                                                      │
│                  7. Log Evidence ──────────────────▶ ┌─────────────┐                         │
│                                                      │  Normalize  │                         │
│                                                      │  (OSCAL)    │                         │
│                                                      └──────┬──────┘                         │
│                                                             │                                │
│                                                      ┌──────▼──────┐                         │
│                                                      │  Validate   │                         │
│                                                      │  (Schema)   │                         │
│                                                      └──────┬──────┘                         │
│                                                             │                                │
│                                                      ┌──────▼──────┐                         │
│                                                      │  Store      │                         │
│                                                      │  (WORM)     │                         │
│                                                      └──────┬──────┘                         │
│                                                             │                                │
│                                                      ┌──────▼──────┐                         │
│                                                      │  Hash Chain │                         │
│                                                      │  + Timestamp│                         │
│                                                      └──────┬──────┘                         │
│                                                             │                                │
│                  8. Map to Frameworks ◀─────────────────────┘                                │
│                  ┌─────────────┐                                                               │
│                  │ Crosswalk   │                                                               │
│                  │ Engine      │                                                               │
│                  └──────┬──────┘                                                               │
│                         │                                                                      │
│                  9. Update Compliance Posture                                                 │
│                  ┌──────▼──────┐                                                               │
│                  │ Recalculate │                                                               │
│                  │ Scores      │                                                               │
│                  └──────┬──────┘                                                               │
│                         │                                                                      │
│                  10. Emit Events ──────────────────▶ Kafka Topics                            │
│                  ┌──────▼──────┐                                                               │
│                  │ decisions   │                                                               │
│                  │ evidence    │                                                               │
│                  │ compliance  │                                                               │
│                  │ audit       │                                                               │
│                  └─────────────┘                                                               │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Policy Lifecycle Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           POLICY LIFECYCLE DATA FLOW                                  │
│                                                                                     │
│   Author    Compiler    Dry-Run    Reviewer    PDP       PEP       Agents            │
│   ──────    ────────    ───────    ────────    ───       ───       ──────            │
│                                                                                     │
│   ┌─────┐                                                                              │
│   │Draft│                                                                              │
│   └──┬──┘                                                                              │
│      │ 1. Write Cedar Policy                                                           │
│      │─────────────────────────────┐                                                   │
│      │                             ▼                                                   │
│      │                        ┌─────────┐                                              │
│      │                        │ Validate│                                              │
│      │                        │ Syntax  │                                              │
│      │                        └────┬────┘                                              │
│      │                             │                                                   │
│      │ 2. Submit for Review       │                                                   │
│      │─────────────────────────────┼─────────────────────────────┐                     │
│      │                             │                             ▼                     │
│      │                             │                        ┌─────────┐                │
│      │                             │                        │ Compile │                │
│      │                             │                        │ Cedar→  │                │
│      │                             │                        │ Rego    │                │
│      │                             │                        └────┬────┘                │
│      │                             │                             │                     │
│      │                             │ 3. Dry-Run Test Cases      │                     │
│      │                             │────────────────────────────▶│                     │
│      │                             │                             │                     │
│      │                             │ 4. Test Results            │                     │
│      │                             │◀────────────────────────────│                     │
│      │                             │                             │                     │
│      │                             │ 5. Review & Approve       │                     │
│      │                             │────────────────────────────▶│                     │
│      │                             │                             │                     │
│      │                             │                        ┌────▼────┐                │
│      │                             │                        │ Review  │                │
│      │                             │                        │ Decision│                │
│      │                             │                        └────┬────┘                │
│      │                             │                             │                     │
│      │                             │ 6. Approved                │                     │
│      │                             │◀────────────────────────────│                     │
│      │                             │                             │                     │
│      │                        ┌────▼────┐                        │                     │
│      │                        │ Active  │                        │                     │
│      │                        └────┬────┘                        │                     │
│      │                             │                             │                     │
│      │                             │ 7. Deploy Bundle           │                     │
│      │                             │────────────────────────────▶│                     │
│      │                             │                             │                     │
│      │                             │                        ┌────▼────┐                │
│      │                             │                        │ Update  │                │
│      │                             │                        │ Policies│                │
│      │                             │                        └────┬────┘                │
│      │                             │                             │                     │
│      │                             │ 8. Propagate to PEPs      │                     │
│      │                             │────────────────────────────▶│                     │
│      │                             │                             │                     │
│      │                             │                        ┌────▼────┐                │
│      │                             │                        │ Update  │                │
│      │                             │                        │ Cache   │                │
│      │                             │                        └────┬────┘                │
│      │                             │                             │                     │
│      │                             │ 9. Active Enforcement     │                     │
│      │                             │────────────────────────────▶│                     │
│      │                             │                             │                     │
│      │                             │                        ┌────▼────┐                │
│      │                             │                        │ Enforce │                │
│      │                             │                        │ Policy  │                │
│      │                             │                        └─────────┘                │
│      │                             │                                                   │
│      │ 10. Deprecate              │                                                   │
│      │─────────────────────────────│                                                   │
│      │                             │                                                   │
│      │                        ┌────▼────┐                                              │
│      │                        │Deprecatd│                                              │
│      │                        └────┬────┘                                              │
│      │                             │                                                   │
│      │                             │ 11. Grace Period (30d)                             │
│      │                             │────────────────────────────▶│                     │
│      │                             │                             │                     │
│      │ 12. Archive               │                             │                     │
│      │─────────────────────────────│                             │                     │
│      │                             │                             │                     │
│      │                        ┌────▼────┐                        │                     │
│      │                        │Archived │                        │                     │
│      │                        └─────────┘                        │                     │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Evidence Collection and Verification Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     EVIDENCE COLLECTION & VERIFICATION FLOW                          │
│                                                                                     │
│  Collectors    Normalizer    Validator    Evidence Store    Compliance    Auditor    │
│  ──────────    ──────────    ─────────    ──────────────    ──────────    ───────    │
│                                                                                     │
│  ┌──────────┐                                                                          │
│  │ Raw Data │                                                                          │
│  └────┬─────┘                                                                          │
│       │ 1. Collect                                                                     │
│       │─────────────────────────────┐                                                   │
│       │                             ▼                                                   │
│       │                        ┌──────────┐                                              │
│       │                        │  Parse   │                                              │
│       │                        │  + Map   │                                              │
│       │                        │  + Enrich│                                              │
│       │                        └────┬─────┘                                              │
│       │                             │                                                   │
│       │ 2. OSCAL JSON               │                                                   │
│       │─────────────────────────────┼─────────────────────────────┐                     │
│       │                             │                             ▼                     │
│       │                             │                        ┌──────────┐                │
│       │                             │                        │ Schema   │                │
│       │                             │                        │ Validate │                │
│       │                             │                        └────┬─────┘                │
│       │                             │                             │                     │
│       │                             │ 3. Validation Result       │                     │
│       │                             │◀────────────────────────────│                     │
│       │                             │                             │                     │
│       │                             │ 4. Compute Hash            │                     │
│       │                             │────────────────────────────▶│                     │
│       │                             │                             │                     │
│       │                             │ 5. Store + Hash Chain      │                     │
│       │                             │────────────────────────────▶│                     │
│       │                             │                             │                     │
│       │                             │                        ┌────▼─────┐                │
│       │                             │                        │  WORM    │                │
│       │                             │                        │  Store   │                │
│       │                             │                        │  + Chain │                │
│       │                             │                        │  + TSA   │                │
│       │                             │                        └────┬─────┘                │
│       │                             │                             │                     │
│       │                             │ 6. Evidence Stored (L2)    │                     │
│       │                             │◀────────────────────────────│                     │
│       │                             │                             │                     │
│       │                             │ 7. Cross-Validate          │                     │
│       │                             │────────────────────────────▶│                     │
│       │                             │                             │                     │
│       │                             │ 8. Corroborated (L3)       │                     │
│       │                             │◀────────────────────────────│                     │
│       │                             │                             │                     │
│       │                             │ 9. Map to Controls         │                     │
│       │                             │────────────────────────────▶│                     │
│       │                             │                             │                     │
│       │                             │                        ┌────▼─────┐                │
│       │                             │                        │Crosswalk │                │
│       │                             │                        │ Engine   │                │
│       │                             │                        └────┬─────┘                │
│       │                             │                             │                     │
│       │                             │ 10. Compliance Update     │                     │
│       │                             │◀────────────────────────────│                     │
│       │                             │                             │                     │
│       │                             │ 11. Generate Report       │                     │
│       │                             │────────────────────────────▶│                     │
│       │                             │                             │                     │
│       │                             │                        ┌────▼─────┐                │
│       │                             │                        │  Audit   │                │
│       │                             │                        │ Package  │                │
│       │                             │                        │(Signed + │                │
│       │                             │                        │Timestamp)│                │
│       │                             │                        └────┬─────┘                │
│       │                             │                             │                     │
│       │                             │ 12. Report Delivered      │                     │
│       │                             │◀────────────────────────────│                     │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Identity Lifecycle Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           IDENTITY LIFECYCLE DATA FLOW                               │
│                                                                                     │
│  Agent    Registry    SPIRE    Vault    PDP     PEP     Trust    Audit               │
│  ─────    ────────    ─────    ────    ───     ───     ─────    ─────               │
│                                                                                     │
│  1. Register Agent                                                               │
│ ─────────────────────────────┐                                                   │
│                              ▼                                                   │
│                         ┌─────────┐                                              │
│                         │ Proposed│                                              │
│                         └────┬────┘                                              │
│                              │                                                   │
│  2. Approve Agent            │                                                   │
│ ─────────────────────────────│                                                   │
│                              │                                                   │
│                         ┌────▼────┐                                              │
│                         │ Active  │                                              │
│                         └────┬────┘                                              │
│                              │                                                   │
│  3. Issue SVID               │                                                   │
│ ─────────────────────────────┼─────────────────────────────┐                     │
│                              │                             ▼                     │
│                              │                        ┌─────────┐                │
│                              │                        │  SPIRE  │                │
│                              │                        │  Issue  │                │
│                              │                        │  SVID   │                │
│                              │                        └────┬────┘                │
│                              │                             │                     │
│                              │ 4. Store Credentials      │                     │
│                              │────────────────────────────▶│                     │
│                              │                             │                     │
│                              │                        ┌────▼────┐                │
│                              │                        │  Vault  │                │
│                              │                        │  Store  │                │
│                              │                        │  mTLS   │                │
│                              │                        │  Creds  │                │
│                              │                        └────┬────┘                │
│                              │                             │                     │
│                              │ 5. Agent Boot             │                     │
│                              │────────────────────────────▶│                     │
│                              │                             │                     │
│                              │                        ┌────▼────┐                │
│                              │                        │  Agent  │                │
│                              │                        │  Boot   │                │
│                              │                        │  + SVID │                │
│                              │                        └────┬────┘                │
│                              │                             │                     │
│                              │ 6. Authenticate           │                     │
│                              │────────────────────────────▶│                     │
│                              │                             │                     │
│                              │                        ┌────▼────┐                │
│                              │                        │  PEP    │                │
│                              │                        │  Verify │                │
│                              │                        │  SVID   │                │
│                              │                        └────┬────┘                │
│                              │                             │                     │
│                              │ 7. Check Trust Score     │                     │
│                              │────────────────────────────▶│                     │
│                              │                             │                     │
│                              │                        ┌────▼────┐                │
│                              │                        │  Trust  │                │
│                              │                        │  Score  │                │
│                              │                        │  Check  │                │
│                              │                        └────┬────┘                │
│                              │                             │                     │
│                              │ 8. Enforce Policy        │                     │
│                              │────────────────────────────▶│                     │
│                              │                             │                     │
│                              │                        ┌────▼────┐                │
│                              │                        │  PDP    │                │
│                              │                        │  Eval   │                │
│                              │                        └────┬────┘                │
│                              │                             │                     │
│                              │ 9. Decision              │                     │
│                              │◀────────────────────────────│                     │
│                              │                             │                     │
│                              │ 10. Update Trust Score   │                     │
│                              │────────────────────────────▶│                     │
│                              │                             │                     │
│                              │                        ┌────▼────┐                │
│                              │                        │  Trust  │                │
│                              │                        │  Score  │                │
│                              │                        │  Update │                │
│                              │                        └────┬────┘                │
│                              │                             │                     │
│                              │ 11. Log Identity Event   │                     │
│                              │────────────────────────────▶│                     │
│                              │                             │                     │
│                              │                        ┌────▼────┐                │
│                              │                        │  Audit  │                │
│                              │                        │  Log    │                │
│                              │                        └─────────┘                │
│                                                                                     │
│  12. Suspend Agent                                                               │
│ ─────────────────────────────│                                                   │
│                              │                                                   │
│                         ┌────▼────┐                                              │
│                         │Suspended│                                              │
│                         └────┬────┘                                              │
│                              │                                                   │
│  13. Reinstate Agent         │                                                   │
│ ─────────────────────────────│                                                   │
│                              │                                                   │
│                         ┌────▼────┐                                              │
│                         │ Active  │                                              │
│                         └────┬────┘                                              │
│                              │                                                   │
│  14. Terminate Agent         │                                                   │
│ ─────────────────────────────│                                                   │
│                              │                                                   │
│                         ┌────▼────┐                                              │
│                         │Terminated                                              │
│                         └────┬────┘                                              │
│                              │                                                   │
│                              │ 15. Revoke SVID                                    │
│                              │────────────────────────────▶│                     │
│                              │                             │                     │
│                              │                        ┌────▼────┐                │
│                              │                        │  SPIRE  │                │
│                              │                        │  Revoke │                │
│                              │                        │  SVID   │                │
│                              │                        └─────────┘                │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.5 Cross-Component Data Flow Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                      CROSS-COMPONENT DATA FLOW MATRIX                                │
│                                                                                     │
│  Source → Destination    │ Data Flow                    │ Protocol    │ Frequency    │
│  ─────────────────────── │ ──────────────────────────── │ ─────────── │ ───────────  │
│                                                                                     │
│  Agent → PEP             │ Tool call request            │ MCP/gRPC    │ Per action   │
│  PEP → PDP               │ Evaluation request           │ gRPC        │ Per action   │
│  PDP → PEP               │ Decision certificate         │ gRPC        │ Per action   │
│  PEP → Evidence          │ Enforcement evidence         │ Kafka       │ Per action   │
│  PDP → Evidence          │ Decision evidence            │ Kafka       │ Per action   │
│  PDP → Identity           │ Agent context query          │ gRPC        │ Per action   │
│  PEP → Identity           │ SVID validation              │ gRPC        │ Per action   │
│  Evidence → Compliance   │ Verified evidence            │ Kafka       │ Continuous   │
│  Compliance → Analytics  │ Compliance posture           │ Kafka       │ Continuous   │
│  Analytics → Observability│ Risk scores, anomalies      │ OTLP        │ Continuous   │
│  All → Observability     │ Traces, metrics, logs        │ OTLP        │ Continuous   │
│  All → Audit (immudb)    │ Hash-chained audit events    │ Kafka       │ Continuous   │
│  Policy → PDP            │ Compiled policy bundles      │ OPA Bundle  │ On change    │
│  Policy → PEP            │ Policy cache invalidation    │ Kafka       │ On change    │
│  Identity → PDP          │ Agent registry updates       │ Kafka       │ On change    │
│  Identity → PEP          │ SVID rotation events         │ Kafka       │ On rotation  │
│  Compliance → Reporting  │ Compliance reports           │ REST        │ Scheduled    │
│  Evidence → Reporting    │ Evidence packages           │ REST        │ Scheduled    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Deployment Patterns

### 3.1 Pattern Catalog

| Pattern | Use Case | Components | Topology |
|---------|----------|------------|----------|
| **Single-Node** | Dev/test | All-in-one | 1 node |
| **HA Cluster** | Production | Full stack | 3+ nodes, 3 AZs |
| **Multi-Region** | DR | Full stack | 2+ regions |
| **Multi-Cloud** | Vendor independence | Full stack | 2+ clouds |
| **Edge** | Distributed enforcement | Lightweight PDP/PEP | Edge sites |
| **Serverless** | Bursty workloads | Evidence, reporting | Knative |
| **Cell-Based** | Multi-tenant isolation | Full stack per cell | Multiple cells |

### 3.2 Single-Node Development Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                     Single Node (Docker Compose)              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Docker Network: grc-claw                 │   │
│  │                                                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │   │
│  │  │ Policy   │  │   PDP    │  │   PEP    │         │   │
│  │  │ API      │  │  (OPA)   │  │ Gateway  │         │   │
│  │  │ :8080    │  │ :8081    │  │ :8082    │         │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘         │   │
│  │       │              │              │                │   │
│  │  ┌────▼──────────────▼──────────────▼────┐          │   │
│  │  │         PostgreSQL :5432              │          │   │
│  │  │         Redis :6379                   │          │   │
│  │  │         Kafka :9092                   │          │   │
│  │  │         MinIO :9000                   │          │   │
│  │  └───────────────────────────────────────┘          │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**docker-compose.yml:**

```yaml
version: "3.9"
services:
  policy-api:
    image: ghcr.io/grc-claw/policy-api:v1.2.0
    ports: ["8080:8080"]
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/grc_claw
      - REDIS_URL=redis://redis:6379
      - KAFKA_BROKERS=kafka:9092
    depends_on: [postgres, redis, kafka]

  pdp-service:
    image: ghcr.io/grc-claw/pdp-service:v1.2.0
    ports: ["8081:8080", "9091:9090"]
    environment:
      - OPA_BUNDLE_SERVER=bundle-server:8080
      - REDIS_URL=redis://redis:6379
    depends_on: [bundle-server, redis]

  pep-gateway:
    image: ghcr.io/grc-claw/pep-gateway:v1.2.0
    ports: ["8082:8080"]
    environment:
      - PDP_ENDPOINT=pdp-service:9090
      - IDENTITY_ENDPOINT=identity-service:9090
    depends_on: [pdp-service, identity-service]

  postgres:
    image: postgres:16.4
    environment:
      POSTGRES_USER: grc
      POSTGRES_PASSWORD: grc
      POSTGRES_DB: grc_claw
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7.2
    command: redis-server --appendonly yes

  kafka:
    image: confluentinc/cp-kafka:7.5
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092

  minio:
    image: minio/minio:latest
    command: server /data
    environment:
      MINIO_ROOT_USER: grc
      MINIO_ROOT_PASSWORD: grcgrcgrc

volumes:
  pgdata:
```

### 3.3 HA Cluster Production Pattern

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     HA CLUSTER PRODUCTION PATTERN                                    │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                         Load Balancer (HAProxy/NLB)                         │   │
│  │                    Health checks, SSL termination                            │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌───────────────────────────────────┼───────────────────────────────────────────┐  │
│  │                                   │                                           │  │
│  │  ┌────────────────────────────────▼────────────────────────────────────────┐  │  │
│  │  │                      Ingress Controller (NGINX)                          │  │  │
│  │  │                    WAF, rate limiting, routing                            │  │  │
│  │  └────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                   │                                           │  │
│  │  ┌────────────────────────────────▼────────────────────────────────────────┐  │  │
│  │  │                      API Gateway (Kong)                                  │  │  │
│  │  │              AuthN, AuthZ, rate limiting, request transformation        │  │  │
│  │  └────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                   │                                           │  │
│  │  ┌────────────────────────────────▼────────────────────────────────────────┐  │  │
│  │  │                      Service Mesh (Istio)                                │  │  │
│  │  │              mTLS, traffic management, observability                     │  │  │
│  │  └────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                   │                                           │  │
│  │  ┌────────────────────────────────▼────────────────────────────────────────┐  │  │
│  │  │                      Microservices Layer                                 │  │  │
│  │  │                                                                         │  │  │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │  │  │
│  │  │  │ Policy API  │ │    PDP      │ │    PEP      │ │  Identity   │      │  │  │
│  │  │  │ 3 replicas  │ │ 3 replicas  │ │ 3 replicas  │ │ 3 replicas  │      │  │  │
│  │  │  │ HPA: 3-10   │ │ HPA: 3-20   │ │ HPA: 3-20   │ │ HPA: 3-10   │      │  │  │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │  │  │
│  │  │                                                                         │  │  │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │  │  │
│  │  │  │  Evidence   │ │ Compliance  │ │  Analytics  │ │  Reporting  │      │  │  │
│  │  │  │ 3 replicas  │ │ 2 replicas  │ │ 2 replicas  │ │ 2 replicas  │      │  │  │
│  │  │  │ HPA: 3-15   │ │ HPA: 2-8    │ │ HPA: 2-8    │ │ HPA: 2-5    │      │  │  │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │  │  │
│  │  │                                                                         │  │  │
│  │  └────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                   │                                           │  │
│  │  ┌────────────────────────────────▼────────────────────────────────────────┐  │  │
│  │  │                      Data Layer (StatefulSets)                           │  │  │
│  │  │                                                                         │  │  │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │  │  │
│  │  │  │ PostgreSQL  │ │    Redis    │ │    Kafka    │ │    MinIO    │      │  │  │
│  │  │  │ 3 nodes     │ │ 6 nodes     │ │ 3 brokers   │ │ 4 nodes     │      │  │  │
│  │  │  │ Patroni HA  │ │ Cluster mode │ │ RF=3, minISR│ │ Erasure code│      │  │  │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │  │  │
│  │  │                                                                         │  │  │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                       │  │  │
│  │  │  │    Neo4j    │ │   immudb    │ │    Vault    │                       │  │  │
│  │  │  │ 3 nodes     │ │ 3 nodes     │ │ 3 nodes     │                       │  │  │
│  │  │  │ Causal cluster│ │ HA cluster  │ │ Raft cluster│                       │  │  │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘                       │  │  │
│  │  │                                                                         │  │  │
│  │  └────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                             │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Multi-Region DR Pattern

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        MULTI-REGION DR PATTERN                                      │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                      Global Load Balancer (Route 53 / Cloudflare)            │   │
│  │                    Health checks, geo-routing, failover                      │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                    ┌─────────────────┼─────────────────┐                            │
│                    │                 │                 │                            │
│                    ▼                 │                 ▼                            │
│  ┌─────────────────────────────┐    │    ┌─────────────────────────────┐           │
│  │     PRIMARY REGION          │    │    │       DR REGION             │           │
│  │     (us-east-1)             │    │    │       (us-west-2)           │           │
│  │                             │    │    │                             │           │
│  │  ┌───────────────────────┐  │    │    │  ┌───────────────────────┐  │           │
│  │  │   EKS Cluster         │  │    │    │  │   EKS Cluster         │  │           │
│  │  │   (Active)            │  │    │    │  │   (Standby)           │  │           │
│  │  │                       │  │    │    │  │                       │  │           │
│  │  │  ┌─────┐ ┌─────┐     │  │    │    │  │  ┌─────┐ ┌─────┐     │  │           │
│  │  │  │ PDP │ │ PEP │     │  │    │    │  │  │ PDP │ │ PEP │     │  │           │
│  │  │  │ x3  │ │ x3  │     │  │    │    │  │  │ x0  │ │ x0  │     │  │           │
│  │  │  └─────┘ └─────┘     │  │    │    │  │  └─────┘ └─────┘     │  │           │
│  │  │                       │  │    │    │  │                       │  │           │
│  │  │  ┌─────┐ ┌─────┐     │  │    │    │  │  ┌─────┐ ┌─────┐     │  │           │
│  │  │  │Policy│ │Evid │     │  │    │    │  │  │Policy│ │Evid │     │  │           │
│  │  │  │ x3  │ │ x3  │     │  │    │    │  │  │ x0  │ │ x0  │     │  │           │
│  │  │  └─────┘ └─────┘     │  │    │    │  │  └─────┘ └─────┘     │  │           │
│  │  │                       │  │    │    │  │                       │  │           │
│  │  └───────────────────────┘  │    │    │  └───────────────────────┘  │           │
│  │                             │    │    │                             │           │
│  │  ┌───────────────────────┐  │    │    │  ┌───────────────────────┐  │           │
│  │  │   Data Layer          │  │    │    │  │   Data Layer          │  │           │
│  │  │                       │  │    │    │  │                       │  │           │
│  │  │  PostgreSQL (Primary) │  │    │    │  │  PostgreSQL (Replica) │  │           │
│  │  │  Redis (Primary)      │  │    │    │  │  Redis (Replica)      │  │           │
│  │  │  Kafka (Primary)      │  │    │    │  │  Kafka (Replica)      │  │           │
│  │  │  MinIO (Primary)      │  │    │    │  │  MinIO (Replica)      │  │           │
│  │  │  immudb (Primary)     │  │    │    │  │  immudb (Replica)     │  │           │
│  │  │  Vault (Primary)      │  │    │    │  │  Vault (Replica)      │  │           │
│  │  │                       │  │    │    │  │                       │  │           │
│  │  └───────────────────────┘  │    │    │  └───────────────────────┘  │           │
│  │                             │    │    │                             │           │
│  └─────────────────────────────┘    │    └─────────────────────────────┘           │
│                    │                 │                 │                            │
│                    │    Replication  │                 │                            │
│                    │    ────────────▶│                 │                            │
│                    │    PostgreSQL:  │                 │                            │
│                    │    Streaming    │                 │                            │
│                    │    (sync)        │                 │                            │
│                    │                 │                 │                            │
│                    │    Redis:       │                 │                            │
│                    │    Sentinel     │                 │                            │
│                    │    (async)       │                 │                            │
│                    │                 │                 │                            │
│                    │    Kafka:       │                 │                            │
│                    │    MirrorMaker2  │                 │                            │
│                    │    (async)       │                 │                            │
│                    │                 │                 │                            │
│                    │    MinIO:       │                 │                            │
│                    │    Bucket repl  │                 │                            │
│                    │    (async)       │                 │                            │
│                    │                 │                 │                            │
│                    │    immudb:      │                 │                            │
│                    │    Read replica │                 │                            │
│                    │    (async)       │                 │                            │
│                    │                 │                 │                            │
│                    │    Vault:       │                 │                            │
│                    │    Perf replica │                 │                            │
│                    │    (async)       │                 │                            │
│                    │                 │                 │                            │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.5 Cell-Based Multi-Tenant Pattern

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     CELL-BASED MULTI-TENANT PATTERN                                 │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                      Global Control Plane                                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │ Global      │  │ Global      │  │ Global      │  │ Global      │       │   │
│  │  │ Tenant      │  │ Policy      │  │ Analytics   │  │ Observability│       │   │
│  │  │ Registry    │  │ Template    │  │ Aggregator  │  │ Aggregator  │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                    ┌─────────────────┼─────────────────┐                            │
│                    │                 │                 │                            │
│                    ▼                 ▼                 ▼                            │
│  ┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────┐  │
│  │      Cell 1 (US)        │ │      Cell 2 (EU)        │ │      Cell 3 (APAC)  │  │
│  │                         │ │                         │ │                     │  │
│  │  ┌───────────────────┐  │ │  ┌───────────────────┐  │ │  ┌───────────────┐  │  │
│  │  │ Cell Control Plane│  │ │  │ Cell Control Plane│  │ │  │ Cell Control  │  │  │
│  │  │                   │  │ │  │                   │  │ │  │ Plane         │  │  │
│  │  │ ┌─────┐ ┌─────┐  │  │ │  │ ┌─────┐ ┌─────┐  │  │ │  │ ┌─────┐ ┌────┐│  │  │
│  │  │ │ PDP │ │ PEP │  │  │ │  │ │ PDP │ │ PEP │  │  │ │  │ │ PDP │ │PEP ││  │  │
│  │  │ │ x3  │ │ x3  │  │  │ │  │ │ x3  │ │ x3  │  │  │ │  │ │ x3  │ │ x3 ││  │  │
│  │  │ └─────┘ └─────┘  │  │ │  │ └─────┘ └─────┘  │  │ │  │ └─────┘ └────┘│  │  │
│  │  │                   │  │ │  │                   │  │ │  │               │  │  │
│  │  │ ┌─────┐ ┌─────┐  │  │ │  │ ┌─────┐ ┌─────┐  │  │ │  │ ┌─────┐ ┌────┐│  │  │
│  │  │ │Policy│ │Evid │  │  │ │  │ │Policy│ │Evid │  │  │ │  │ │Policy│ │Evid││  │  │
│  │  │ │ x3  │ │ x3  │  │  │ │  │ │ x3  │ │ x3  │  │  │ │  │ │ x3  │ │ x3 ││  │  │
│  │  │ └─────┘ └─────┘  │  │ │  │ └─────┘ └─────┘  │  │ │  │ └─────┘ └────┘│  │  │
│  │  └───────────────────┘  │ │  └───────────────────┘  │ │  └───────────────┘  │  │
│  │                         │ │                         │ │                     │  │
│  │  ┌───────────────────┐  │ │  ┌───────────────────┐  │ │  ┌───────────────┐  │  │
│  │  │ Cell Data Layer   │  │ │  │ Cell Data Layer   │  │ │  │ Cell Data     │  │  │
│  │  │                   │  │ │  │                   │  │ │  │ Layer         │  │  │
│  │  │ ┌─────┐ ┌─────┐  │  │ │  │ ┌─────┐ ┌─────┐  │  │ │  │ ┌─────┐ ┌────┐│  │  │
│  │  │ │Postgre│ │Redis │  │  │ │  │ │Postgre│ │Redis │  │  │ │  │ │Postgre│ │Redis││  │  │
│  │  │ │SQL  │ │     │  │  │ │  │ │SQL  │ │     │  │  │ │  │ │SQL  │ │    ││  │  │
│  │  │ └─────┘ └─────┘  │  │ │  │ └─────┘ └─────┘  │  │ │  │ └─────┘ └────┘│  │  │
│  │  │                   │  │ │  │                   │  │ │  │               │  │  │
│  │  │ ┌─────┐ ┌─────┐  │  │ │  │ ┌─────┐ ┌─────┐  │  │ │  │ ┌─────┐ ┌────┐│  │  │
│  │  │ │Kafka │ │MinIO │  │  │ │  │ │Kafka │ │MinIO │  │  │ │  │ │Kafka │ │MinIO││  │  │
│  │  │ └─────┘ └─────┘  │  │ │  │ └─────┘ └─────┘  │  │ │  │ └─────┘ └────┘│  │  │
│  │  │                   │  │ │  │                   │  │ │  │               │  │  │
│  │  │ ┌─────┐ ┌─────┐  │  │ │  │ ┌─────┐ ┌─────┐  │  │ │  │ ┌─────┐ ┌────┐│  │  │
│  │  │ │immudb│ │Vault │  │  │ │  │ │immudb│ │Vault │  │  │ │  │ │immudb│ │Vault││  │  │
│  │  │ └─────┘ └─────┘  │  │ │  │ └─────┘ └─────┘  │  │ │  │ └─────┘ └────┘│  │  │
│  │  └───────────────────┘  │ │  └───────────────────┘  │ │  └───────────────┘  │  │
│  │                         │ │                         │ │                     │  │
│  │  Tenant: acme, globex   │ │  Tenant: initech, umbra │ │  Tenant: sakura   │  │
│  │  Region: us-east-1      │ │  Region: eu-west-1      │ │  Region: ap-south-1│  │
│  │  Data residency: US     │ │  Data residency: EU     │ │  Data residency: APAC│ │
│  └─────────────────────────┘ └─────────────────────────┘ └─────────────────────┘  │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### 3.6 Edge Deployment Pattern

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        EDGE DEPLOYMENT PATTERN                                       │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                      Cloud Control Plane                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │ Policy      │  │ Global      │  │ Analytics   │  │ Global      │       │   │
│  │  │ Distribution│  │ Tenant      │  │ Aggregation │  │ Observability│       │   │
│  │  │ Service     │  │ Registry    │  │             │  │             │       │   │
│  │  └──────┬──────┘  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  │         │                                                                   │   │
│  │         │ Policy Sync (delta, 30s)                                           │   │
│  │         │ Evidence Upload (batch, 60s)                                       │   │
│  │         │ Heartbeat (10s)                                                    │   │
│  │         │                                                                   │   │
│  └─────────┼───────────────────────────────────────────────────────────────────┘   │
│            │                                                                       │
│  ┌─────────┼───────────────────────────────────────────────────────────────────┐   │
│  │         │                                                                   │   │
│  │         ▼                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                      Edge Site (K3s / MicroK8s)                      │   │   │
│  │  │                                                                     │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │   │
│  │  │  │ Edge PDP    │  │ Edge PEP    │  │ Local Cache │  │ Evidence   │ │   │   │
│  │  │  │ (Lightweight)│  │ (Local      │  │ (Redis      │  │ Buffer     │ │   │   │
│  │  │  │             │  │  Enforcement)│  │  Embedded)  │  │ (Local WAL)│ │   │   │
│  │  │  │ 100m CPU    │  │ 100m CPU    │  │ 50m CPU     │  │ 50m CPU    │ │   │   │
│  │  │  │ 128Mi RAM   │  │ 128Mi RAM   │  │ 64Mi RAM    │  │ 64Mi RAM   │ │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │   │
│  │  │                                                                     │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐                                │   │   │
│  │  │  │ Sync Agent  │  │ Edge Agent  │                                │   │   │
│  │  │  │ (Cloud ↔    │  │ (Local      │                                │   │   │
│  │  │  │  Edge)      │  │  Enforcement)│                                │   │   │
│  │  │  └─────────────┘  └─────────────┘                                │   │   │
│  │  │                                                                     │   │   │
│  │  └─────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

**Edge PDP Configuration:**

```yaml
edge_pdp:
  mode: "offline-first"
  sync:
    policy_interval: "30s"
    evidence_interval: "60s"
    heartbeat_interval: "10s"
    offline_tolerance: "24h"
  cache:
    max_policies: 1000
    max_decisions: 10000
    ttl_seconds: 300
  enforcement:
    fail_policy: "closed"
    local_evaluation: true
    max_offline_duration: "24h"
  resources:
    cpu: "100m"
    memory: "128Mi"
  security:
    tamper_detection: true
    secure_boot: true
    encryption: "AES-256"
```

---

## 4. Security Architecture

### 4.1 Defense-in-Depth Model

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        DEFENSE-IN-DEPTH SECURITY MODEL                                │
│                                                                                     │
│  Layer 7: Application Security                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Input validation (JSON Schema)                                            │   │
│  │  • Output encoding (prevent injection)                                      │   │
│  │  • Rate limiting (per agent, per tenant)                                     │   │
│  │  • Request signing (HMAC-SHA256)                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  Layer 6: API Security                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • OAuth 2.1 + OIDC authentication                                          │   │
│  │  • RBAC + ABAC authorization                                                │   │
│  │  • API gateway (Kong) with WAF                                              │   │
│  │  • Request/response transformation                                           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  Layer 5: Service-to-Service Security                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • mTLS (SPIFFE/SPIRE SVIDs)                                                │   │
│  │  • Service mesh (Istio) with mutual TLS                                     │   │
│  │  • Network policies (micro-segmentation)                                    │   │
│  │  • Authorization policies (Istio AuthorizationPolicy)                       │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  Layer 4: Data Security                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Encryption at rest (AES-256-GCM)                                         │   │
│  │  • Encryption in transit (TLS 1.3)                                          │   │
│  │  • Field-level encryption (PII, sensitive data)                             │   │
│  │  • Key management (HashiCorp Vault + HSM)                                   │   │
│  │  • WORM storage for evidence (immutability)                                 │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  Layer 3: Runtime Security                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Container isolation (gVisor/Kata Containers)                              │   │
│  │  • Seccomp profiles (syscall filtering)                                     │   │
│  │  • AppArmor/SELinux (mandatory access control)                               │   │
│  │  • eBPF programs (runtime threat detection)                                 │   │
│  │  • Read-only root filesystem                                                │   │
│  │  • Non-root container execution                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  Layer 2: Network Security                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • VPC isolation (private subnets)                                          │   │
│  │  • Security groups (least privilege)                                        │   │
│  │  • Network ACLs (defense in depth)                                           │   │
│  │  • DDoS protection (AWS Shield / Cloud Armor)                                │   │
│  │  • Egress filtering (Istio Egress Gateway)                                   │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  Layer 1: Infrastructure Security                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Hardware security modules (HSM)                                          │   │
│  │  • Secure boot (UEFI + TPM)                                                 │   │
│  │  • Disk encryption (LUKS)                                                   │   │
│  │  • Instance metadata protection (IMDSv2)                                    │   │
│  │  • Audit logging (immutable)                                                │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Trust Boundary Definitions

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           TRUST BOUNDARY DEFINITIONS                                 │
│                                                                                     │
│  Boundary 1: External ↔ API Gateway                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • TLS 1.3 termination                                                       │   │
│  │  • OAuth 2.1 + OIDC authentication                                          │   │
│  │  • WAF (OWASP Top 10 protection)                                             │   │
│  │  • DDoS protection                                                           │   │
│  │  • Rate limiting (per IP, per client)                                       │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Boundary 2: API Gateway ↔ Microservices                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • mTLS (Istio service mesh)                                                │   │
│  │  • Service account authentication                                           │   │
│  │  • Authorization policies (Istio AuthorizationPolicy)                       │   │
│  │  • Network policies (Kubernetes NetworkPolicy)                              │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Boundary 3: Microservices ↔ Data Layer                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • mTLS (service-to-service)                                                │   │
│  │  • Database authentication (PostgreSQL SCRAM-SHA-256)                       │   │
│  │  • Redis authentication (ACL + AUTH)                                        │   │
│  │  • Kafka authentication (SASL/SCRAM + mTLS)                                 │   │
│  │  • MinIO authentication (IAM + STS)                                         │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Boundary 4: Data Layer ↔ External Systems                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Outbound mTLS                                                             │   │
│  │  • Egress filtering (Istio Egress Gateway)                                   │   │
│  │  • API key management (Vault)                                                │   │
│  │  • Request signing (HMAC)                                                    │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Boundary 5: Agent ↔ PEP                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • mTLS (SPIFFE SVIDs)                                                       │   │
│  │  • Agent identity verification                                               │   │
│  │  • Capability validation                                                     │   │
│  │  • Trust score check                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Authentication and Authorization Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION & AUTHORIZATION FLOW                               │
│                                                                                     │
│  Agent    PEP    Identity    PDP    Policy Store    Evidence    Audit               │
│  ─────    ───    ────────    ───    ────────────    ────────    ─────               │
│                                                                                     │
│  1. Agent Boot + SVID                                                              │
│ ─────────────────────────────┐                                                      │
│                              ▼                                                      │
│                         ┌─────────┐                                                 │
│                         │  Agent  │                                                 │
│                         │  Boot   │                                                 │
│                         └────┬────┘                                                 │
│                              │                                                      │
│  2. Present SVID            │                                                      │
│ ─────────────────────────────┼──────────────────────────────▶│                      │
│                              │                              │                      │
│                              │                         ┌────▼────┐                 │
│                              │                         │  PEP    │                 │
│                              │                         │  Verify │                 │
│                              │                         │  SVID   │                 │
│                              │                         └────┬────┘                 │
│                              │                              │                      │
│  3. Validate SVID           │                              │                      │
│ ─────────────────────────────┼──────────────────────────────▶│                      │
│                              │                              │                      │
│                              │                         ┌────▼────┐                 │
│                              │                         │Identity │                 │
│                              │                         │ Service │                 │
│                              │                         │ Validate│                 │
│                              │                         └────┬────┘                 │
│                              │                              │                      │
│  4. Agent Context           │                              │                      │
│ ◀─────────────────────────────┼──────────────────────────────│                      │
│                              │                              │                      │
│  5. Check Trust Score       │                              │                      │
│ ─────────────────────────────┼──────────────────────────────▶│                      │
│                              │                              │                      │
│                              │                         ┌────▼────┐                 │
│                              │                         │  Trust  │                 │
│                              │                         │  Score  │                 │
│                              │                         │  Check  │                 │
│                              │                         └────┬────┘                 │
│                              │                              │                      │
│  6. Trust Score OK          │                              │                      │
│ ◀─────────────────────────────┼──────────────────────────────│                      │
│                              │                              │                      │
│  7. Tool Call Request       │                              │                      │
│ ─────────────────────────────┼──────────────────────────────▶│                      │
│                              │                              │                      │
│                              │                         ┌────▼────┐                 │
│                              │                         │  PEP    │                 │
│                              │                         │  Build  │                 │
│                              │                         │  Input  │                 │
│                              │                         │  Doc    │                 │
│                              │                         └────┬────┘                 │
│                              │                              │                      │
│  8. Evaluate Policy         │                              │                      │
│ ─────────────────────────────┼──────────────────────────────▶│                      │
│                              │                              │                      │
│                              │                         ┌────▼────┐                 │
│                              │                         │  PDP    │                 │
│                              │                         │  Eval   │                 │
│                              │                         │  Policy │                 │
│                              │                         └────┬────┘                 │
│                              │                              │                      │
│  9. Decision Certificate   │                              │                      │
│ ◀─────────────────────────────┼──────────────────────────────│                      │
│                              │                              │                      │
│  10. Apply Decision        │                              │                      │
│ ─────────────────────────────┼──────────────────────────────▶│                      │
│                              │                              │                      │
│                              │                         ┌────▼────┐                 │
│                              │                         │  PEP    │                 │
│                              │                         │  Apply  │                 │
│                              │                         │ Decision│                 │
│                              │                         └────┬────┘                 │
│                              │                              │                      │
│  11. Execute Tool Call     │                              │                      │
│ ─────────────────────────────┼──────────────────────────────▶│                      │
│                              │                              │                      │
│  12. Log Evidence          │                              │                      │
│ ─────────────────────────────┼──────────────────────────────▶│                      │
│                              │                              │                      │
│                              │                         ┌────▼────┐                 │
│                              │                         │Evidence │                 │
│                              │                         │ Store   │                 │
│                              │                         │ + Audit │                 │
│                              │                         └─────────┘                 │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Secret Management Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        SECRET MANAGEMENT ARCHITECTURE                                │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                         HashiCorp Vault Cluster                              │   │
│  │                                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                         Vault Secrets Engines                         │   │   │
│  │  │                                                                     │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │   │
│  │  │  │ KV v2       │  │ PKI         │  │ Database    │  │ Transit    │ │   │   │
│  │  │  │ (App        │  │ (mTLS certs)│  │ (Dynamic    │  │ (Encryption)│ │   │   │
│  │  │  │  secrets)   │  │             │  │  credentials)│  │            │ │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │   │
│  │  │                                                                     │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │   │   │
│  │  │  │ AWS/GCP     │  │ PKI         │  │ Kubernetes  │                │   │   │
│  │  │  │ (Cloud auth)│  │ (SSH certs) │  │ (K8s auth)  │                │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘                │   │   │
│  │  │                                                                     │   │   │
│  │  └─────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                         Vault Auth Methods                            │   │   │
│  │  │                                                                     │   │   │
│  │  │  • Kubernetes auth (service account tokens)                         │   │   │
│  │  │  • AppRole auth (service-to-service)                                │   │   │
│  │  │  • AWS IAM auth (cloud services)                                    │   │   │
│  │  │  • OIDC auth (human users via Dex/SSO)                              │   │   │
│  │  │                                                                     │   │   │
│  │  └─────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌───────────────────────────────────┼───────────────────────────────────────────┐  │
│  │                                   │                                           │  │
│  │  ┌────────────────────────────────▼────────────────────────────────────────┐  │  │
│  │  │                      External Secrets Operator                          │  │  │
│  │  │                                                                        │  │  │
│  │  │  • Syncs Vault secrets → Kubernetes Secrets                            │  │  │
│  │  │  • Automatic rotation on secret update                                 │  │  │
│  │  │  • Template-based secret generation                                    │  │  │
│  │  │                                                                        │  │  │
│  │  └────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                   │                                           │  │
│  │  ┌────────────────────────────────▼────────────────────────────────────────┐  │  │
│  │  │                      Vault Agent Sidecar                                │  │  │
│  │  │                                                                        │  │  │
│  │  │  • Auto-authentication via Kubernetes auth                             │  │  │
│  │  │  • Secret caching and renewal                                          │  │  │
│  │  │  • Template rendering (config files)                                   │  │  │
│  │  │                                                                        │  │  │
│  │  └────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                             │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

**Secret Rotation Schedule:**

| Secret Type | Storage | Rotation Frequency | Rotation Method | Impact |
|-------------|---------|-------------------|-----------------|--------|
| mTLS certificates | Vault PKI | 24 hours | cert-manager + Vault | Zero-downtime |
| API tokens | Vault KV v2 | 7 days | Vault dynamic secrets | Zero-downtime |
| Database credentials | Vault Database | 30 days | Vault database secrets engine | Rolling restart |
| Encryption keys (DEK) | Vault Transit | 90 days | Vault transit engine | Re-encryption |
| Signing keys | HSM | 1 year | Manual HSM operation | Scheduled maintenance |
| Vault tokens | Vault | 24 hours | Kubernetes auth | Zero-downtime |
| Kafka credentials | Vault KV v2 | 30 days | Vault + Kafka ACL | Rolling restart |
| Redis credentials | Vault KV v2 | 30 days | Vault + Redis ACL | Rolling restart |

### 4.5 Data Protection

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           DATA PROTECTION MODEL                                      │
│                                                                                     │
│  Data Classification:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  Level 5: Critical (Signing keys, root CA)                                 │   │
│  │  ├── Storage: HSM (FIPS 140-2 Level 3)                                     │   │
│  │  ├── Encryption: AES-256-GCM (HSM-backed)                                  │   │
│  │  ├── Access: Dual-control, break-glass procedure                           │   │
│  │  └── Audit: Real-time alerting, immutable logs                             │   │
│  │                                                                             │   │
│  │  Level 4: Highly Sensitive (PII, PHI, financial data)                       │   │
│  │  ├── Storage: Encrypted database (AES-256)                                 │   │
│  │  ├── Encryption: Field-level encryption (Vault Transit)                    │   │
│  │  ├── Access: ABAC + need-to-know                                           │   │
│  │  └── Audit: Full access logging, quarterly review                          │   │
│  │                                                                             │   │
│  │  Level 3: Sensitive (Compliance evidence, audit logs)                     │   │
│  │  ├── Storage: WORM object storage (MinIO)                                  │   │
│  │  ├── Encryption: SSE-S3 / SSE-KMS                                          │   │
│  │  ├── Access: RBAC + time-bound                                              │   │
│  │  └── Audit: Hash-chained, RFC 3161 timestamps                              │   │
│  │                                                                             │   │
│  │  Level 2: Internal (Policy definitions, agent metadata)                    │   │
│  │  ├── Storage: PostgreSQL (encrypted at rest)                               │   │
│  │  ├── Encryption: AES-256 (cloud KMS)                                       │   │
│  │  ├── Access: RBAC                                                           │   │
│  │  └── Audit: Standard audit logging                                         │   │
│  │                                                                             │   │
│  │  Level 1: Public (Documentation, open-source code)                         │   │
│  │  ├── Storage: Standard storage                                              │   │
│  │  ├── Encryption: TLS in transit                                             │   │
│  │  ├── Access: Public read                                                    │   │
│  │  └── Audit: Standard logging                                                │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Encryption Strategy:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  At Rest:                                                                   │   │
│  │  ├── Database: AES-256-GCM (cloud KMS / Vault Transit)                     │   │
│  │  ├── Object Storage: SSE-S3 / SSE-KMS                                       │   │
│  │  ├── Audit Store: WORM + hash chaining                                     │   │
│  │  └── Backups: AES-256 (pgBackRest encryption)                               │   │
│  │                                                                             │   │
│  │  In Transit:                                                                 │   │
│  │  ├── External: TLS 1.3 (mandatory)                                          │   │
│  │  ├── Internal: mTLS (Istio service mesh)                                    │   │
│  │  ├── Database: TLS 1.3 + certificate pinning                                │   │
│  │  └── Kafka: SASL_SSL + mTLS                                                 │   │
│  │                                                                             │   │
│  │  In Use:                                                                     │   │
│  │  ├── Memory: Encrypted swap, secure enclaves (SGX)                         │   │
│  │  ├── Processing: Field-level encryption for PII                             │   │
│  │  └── Keys: HSM-backed, never in plaintext                                   │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.6 Audit and Compliance Security

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        AUDIT & COMPLIANCE SECURITY                                   │
│                                                                                     │
│  Audit Event Lifecycle:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  1. Event Generated                                                         │   │
│  │     ├── All components emit audit events                                    │   │
│  │     ├── Events include: actor, action, resource, timestamp, context        │   │
│  │     └── Events signed with component identity                               │   │
│  │                                                                             │   │
│  │  2. Event Transmitted                                                       │   │
│  │     ├── Events sent to Kafka `audit.events` topic                           │   │
│  │     ├── Transmission encrypted with mTLS                                    │   │
│  │     └── Events include trace_id for correlation                            │   │
│  │                                                                             │   │
│  │  3. Event Validated                                                         │   │
│  │     ├── Schema validation (JSON Schema)                                     │   │
│  │     ├── Signature verification                                              │   │
│  │     └── Duplicate detection                                                 │   │
│  │                                                                             │   │
│  │  4. Event Stored                                                           │   │
│  │     ├── Stored in immudb (immutable)                                        │   │
│  │     ├── Hash-chained with previous event                                    │   │
│  │     ├── RFC 3161 timestamp                                                  │   │
│  │     └── WORM storage (MinIO)                                                │   │
│  │                                                                             │   │
│  │  5. Event Verified                                                          │   │
│  │     ├── Hash chain integrity check                                          │   │
│  │     ├── Signature verification                                              │   │
│  │     ├── Timestamp verification                                              │   │
│  │     └── Cross-reference with evidence store                                 │   │
│  │                                                                             │   │
│  │  6. Event Reported                                                          │   │
│  │     ├── Compliance reports generated                                        │   │
│  │     ├── Audit packages assembled                                            │   │
│  │     ├── Reports signed and timestamped                                      │   │
│  │     └── Reports distributed to auditors                                     │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Audit Event Schema:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  {                                                                          │   │
│  │    "event_id": "uuid-v4",                                                   │   │
│  │    "event_type": "grc.action.performed",                                    │   │
│  │    "event_version": "1.0",                                                  │   │
│  │    "timestamp": "2026-10-01T14:30:00.123Z",                               │   │
│  │    "actor": {                                                               │   │
│  │      "type": "agent | user | system",                                       │   │
│  │      "id": "agent-42",                                                      │   │
│  │      "spiffe_id": "spiffe://grc-claw.io/...",                              │   │
│  │      "ip_address": "10.0.1.42",                                             │   │
│  │      "user_agent": "grc-agent/2.1.0"                                        │   │
│  │    },                                                                       │   │
│  │    "action": {                                                              │   │
│  │      "type": "read | write | delete | execute | approve",                   │   │
│  │      "resource": "s3://data/public/dataset.csv",                            │   │
│  │      "result": "success | failure | denied",                                │   │
│  │      "policy_id": "pol-data-access-001",                                    │   │
│  │      "decision_id": "dec-uuid-v4"                                           │   │
│  │    },                                                                       │   │
│  │    "context": {                                                             │   │
│  │      "environment": "production",                                           │   │
│  │      "tenant_id": "tenant-acme",                                            │   │
│  │      "session_id": "sess-uuid-v4",                                          │   │
│  │      "trace_id": "trace-uuid-v4"                                            │   │
│  │    },                                                                       │   │
│  │    "evidence": {                                                            │   │
│  │      "evidence_id": "evd-uuid-v4",                                          │   │
│  │      "evidence_hash": "sha256:abc123...",                                   │   │
│  │      "verification_level": "L2"                                             │   │
│  │    },                                                                       │   │
│  │    "integrity": {                                                           │   │
│  │      "previous_event_hash": "sha256:def456...",                             │   │
│  │      "event_hash": "sha256:ghi789...",                                      │   │
│  │      "signature": "ecdsa-p256:jkl012...",                                  │   │
│  │      "timestamp_authority": "https://tsa.grc-claw.internal"                │   │
│  │    }                                                                        │   │
│  │  }                                                                          │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Performance Architecture

### 5.1 Performance Targets and SLIs

| Component | Metric | Target | Measurement | Alert Threshold |
|-----------|--------|--------|-------------|-----------------|
| PDP | Evaluation latency (p50) | < 10ms | OPA evaluation time | > 15ms |
| PDP | Evaluation latency (p99) | < 50ms | OPA evaluation time | > 75ms |
| PDP | Evaluation latency (p99.9) | < 100ms | OPA evaluation time | > 150ms |
| PEP | Enforcement overhead (p99) | < 10ms | End-to-end minus PDP | > 15ms |
| PEP | End-to-end latency (p99) | < 100ms | Agent request to response | > 150ms |
| Evidence | Collection latency (p99) | < 5s | Collector to store | > 10s |
| Evidence | Verification latency (p99) | < 2s | Hash chain verification (10K) | > 5s |
| Policy | Compilation time | < 5s | Cedar to Rego | > 10s |
| Policy | Bundle distribution | < 30s | PDP to all PEPs | > 60s |
| Identity | SVID issuance (p99) | < 100ms | SPIRE to agent | > 200ms |
| Identity | Trust score update | < 1s | Event to score update | > 5s |
| API | Response time (p99) | < 200ms | API Gateway | > 500ms |
| API | Throughput | 10,000 req/s | Aggregate | N/A |
| System | Decision throughput | 1M+ actions/day | Aggregate | N/A |
| System | Availability | 99.9% | Uptime | < 99.5% |

### 5.2 Performance Optimization Strategies

#### 5.2.1 PDP Performance Optimization

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        PDP PERFORMANCE OPTIMIZATION                                  │
│                                                                                     │
│  1. Policy Compilation Caching                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Compile Cedar → Rego once, cache compiled output                          │   │
│  │  • Invalidate cache on policy version change                                  │   │
│  │  • Pre-compile policies during deployment                                     │   │
│  │  • Cache hit ratio target: > 95%                                              │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  2. Decision Caching (Redis)                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Cache frequent decisions with TTL                                          │   │
│  │  • Cache key: hash(agent_id + action + resource + context_hash)              │   │
│  │  • TTL: 300 seconds (configurable per policy)                                 │   │
│  │  • Cache invalidation on policy change                                         │   │
│  │  • Cache hit ratio target: > 80%                                              │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  3. Pre-computed Decisions                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Pre-compute decisions for known action patterns                            │   │
│  │  • Scheduled actions (e.g., daily reports)                                     │   │
│  │  • Predictable patterns (e.g., routine data access)                           │   │
│  │  • Store in Redis with longer TTL                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  4. Policy Evaluation Optimization                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Rego: Use `import future.keywords` for efficient evaluation                │   │
│  │  • Cedar: Use native Rust SDK for evaluation                                  │   │
│  │  • Policy ordering: Most restrictive first (fail fast)                         │   │
│  │  • Short-circuit evaluation: Stop on first DENY/QUARANTINE                    │   │
│  │  • Parallel evaluation: Evaluate independent policies concurrently            │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  5. Connection Pooling                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • gRPC connection pooling (HTTP/2 multiplexing)                              │   │
│  │  • Database connection pooling (PgBouncer)                                    │   │
│  │  • Redis connection pooling                                                   │   │
│  │  • Kafka connection pooling                                                   │   │
│  │  • Max connections: 1000 per PDP instance                                     │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  6. Horizontal Scaling                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Stateless PDP instances (no local state)                                  │   │
│  │  • HPA: 3-20 replicas based on CPU + latency                                  │   │
│  │  • Load balancing: gRPC client-side round-robin                              │   │
│  │  • Cache sharing: Redis cluster (all PDP instances share cache)              │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### 5.2.2 PEP Performance Optimization

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        PEP PERFORMANCE OPTIMIZATION                                  │
│                                                                                     │
│  1. Decision Caching                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Local LRU cache for frequent decisions                                     │   │
│  │  • Cache TTL: 300 seconds (configurable)                                      │   │
│  │  • Cache size: 10,000 entries per PEP instance                                 │   │
│  │  • Cache invalidation via Kafka `policy.changes` topic                        │   │
│  │  • Cache hit ratio target: > 85%                                              │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  2. Async Evidence Logging                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Evidence logging is non-blocking (fire-and-forget)                         │   │
│  │  • Local buffer (ring buffer) for evidence events                             │   │
│  │  • Batch flush to Kafka every 100ms or 1000 events                            │   │
│  │  • Overflow: Drop oldest events, alert on > 80% capacity                      │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  3. Connection Reuse                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Persistent gRPC connections to PDP                                         │   │
│  │  • HTTP/2 multiplexing for REST calls                                         │   │
│  │  • Connection pool: 100 connections per PEP instance                          │   │
│  │  • Keep-alive: 30 seconds                                                      │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  4. Rate Limiting                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Token bucket algorithm per agent                                           │   │
│  │  • Burst capacity: 2x sustained rate                                          │   │
│  │  • Rate limit: 100 tool calls/s per agent                                     │   │
│  │  • Global rate limit: 10,000 tool calls/s per PEP instance                    │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### 5.2.3 Evidence Collection Performance

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     EVIDENCE COLLECTION PERFORMANCE                                  │
│                                                                                     │
│  1. Batch Processing                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Collect evidence in batches (100-1000 items)                              │   │
│  │  • Batch size: Configurable per collector                                     │   │
│  │  • Batch timeout: 5 seconds                                                    │   │
│  │  • Throughput target: 50,000 events/s per collector                           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  2. Parallel Processing                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Multiple collector instances (HPA: 3-15 replicas)                          │   │
│  │  • Parallel normalization (worker pool: 10-50 workers)                        │   │
│  │  • Parallel validation (worker pool: 5-20 workers)                            │   │
│  │  • Partition-based parallelism (Kafka partitions)                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  3. Streaming Processing                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Kafka Streams for real-time evidence processing                            │   │
│  │  • Windowed aggregations (tumbling window: 1 minute)                          │   │
│  │  • Exactly-once processing semantics                                          │   │
│  │  • Backpressure handling (pause on overload)                                   │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  4. Storage Optimization                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • WORM storage: Sequential writes (optimized for append-only)                │   │
│  │  • Compression: LZ4 for evidence payloads                                     │   │
│  │  • Indexing: Control ID + timestamp + agent ID                                │   │
│  │  • Partitioning: Monthly partitions for audit trail                           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Caching Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           CACHING STRATEGY                                           │
│                                                                                     │
│  Cache Layer 1: In-Memory (PEP Local)                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Type: LRU cache (in-process)                                              │   │
│  │  • Size: 10,000 entries                                                       │   │
│  │  • TTL: 300 seconds                                                            │   │
│  │  • Content: Decision certificates                                             │   │
│  │  • Invalidation: Kafka `policy.changes` + TTL expiry                         │   │
│  │  • Hit ratio target: > 85%                                                    │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Cache Layer 2: Distributed (Redis Cluster)                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Type: Redis Cluster (6 nodes)                                              │   │
│  │  • Size: 10GB total                                                            │   │
│  │  • TTL: 300 seconds (configurable per key pattern)                            │   │
│  │  • Content: Decision certificates, policy bundles, agent context              │   │
│  │  • Invalidation: Pub/sub + TTL expiry                                         │   │
│  │  • Hit ratio target: > 80%                                                    │   │
│  │  • Eviction: allkeys-lru                                                       │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Cache Layer 3: CDN (Static Assets)                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Type: CloudFront / Cloud CDN                                               │   │
│  │  • Content: UI assets, API documentation                                      │   │
│  │  • TTL: 24 hours                                                               │   │
│  │  • Invalidation: Manual purge on deployment                                   │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Cache Key Patterns:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  Decision:    `dec:{agent_id}:{action}:{resource_hash}:{context_hash}`       │   │
│  │  Policy:      `pol:{policy_id}:{version}`                                     │   │
│  │  Agent:       `agent:{agent_id}`                                              │   │
│  │  Bundle:      `bundle:{policy_set}:{revision}`                                │   │
│  │  Trust Score: `trust:{agent_id}`                                               │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 Load Testing Strategy

| Test Type | Frequency | Tool | Scenario | Success Criteria |
|-----------|-----------|------|----------|-----------------|
| Load test | Weekly | k6 | 10K decisions/s sustained | p99 < 10ms, 0 errors |
| Stress test | Monthly | k6 | 25K decisions/s peak | Graceful degradation, no crashes |
| Soak test | Monthly | k6 | 10K decisions/s for 72h | No memory leaks, stable latency |
| Spike test | Monthly | k6 | 0 → 50K decisions/s in 10s | Recovery < 30s, no errors |
| Chaos test | Monthly | Litmus | Random component kills | Recovery < 5min, graceful degradation |
| Failover test | Quarterly | Manual | Zone/region failure | RTO < 4h, RPO < 5min |

**k6 Load Test Script:**

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const decisionLatency = new Trend('decision_latency');

export const options = {
  stages: [
    { duration: '2m', target: 1000 },   // Ramp up
    { duration: '5m', target: 10000 },  // Sustained load
    { duration: '2m', target: 25000 },  // Stress test
    { duration: '2m', target: 0 },      // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(99)<50'],     // p99 < 50ms
    http_req_failed: ['rate<0.001'],     // Error rate < 0.1%
    errors: ['rate<0.001'],
  },
};

export default function () {
  const payload = JSON.stringify({
    agent_id: `agent-${__VU}`,
    action: 'read',
    resource: 's3://data/public/dataset.csv',
    context: {
      environment: 'load-test',
      tenant_id: 'tenant-load-test',
    },
  });

  const res = http.post('http://pep-gateway:8080/v1/evaluate', payload, {
    headers: { 'Content-Type': 'application/json' },
  });

  const success = check(res, {
    'status is 200': (r) => r.status === 200,
    'verdict is present': (r) => r.json('verdict') !== undefined,
  });

  errorRate.add(!success);
  decisionLatency.add(res.timings.duration);

  sleep(0.001); // 1ms between requests
}
```

---

## 6. Observability Architecture

### 6.1 Three Pillars of Observability

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OBSERVABILITY ARCHITECTURE                              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        OpenTelemetry Collector                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │  Traces  │  │  Metrics │  │   Logs   │  │ Baggage  │           │   │
│  │  │  (OTLP)  │  │  (OTLP)  │  │  (OTLP)  │  │          │           │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │   │
│  │       │             │             │             │                  │   │
│  │       ▼             ▼             ▼             ▼                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │  Tempo   │  │Prometheus│  │  Loki    │  │Analytics │           │   │
│  │  │(traces)  │  │(metrics) │  │ (logs)   │  │  Engine  │           │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │   │
│  │       │             │             │             │                  │   │
│  │       └─────────────┴─────────────┴─────────────┘                  │   │
│  │                           │                                        │   │
│  │                           ▼                                        │   │
│  │                    ┌──────────┐                                    │   │
│  │                    │ Grafana  │                                    │   │
│  │                    │(unified) │                                    │   │
│  │                    └──────────┘                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     OpenInference (LLM Traces)                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │  LLM     │  │  Token   │  │  Prompt/ │  │  Tool    │           │   │
│  │  │  Spans   │  │  Usage   │  │  Response│  │  Calls   │           │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Metrics

#### 6.2.1 Key Prometheus Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `grc_decision_total` | Counter | `verdict`, `policy_id`, `agent_id` | Total decisions by verdict |
| `grc_decision_duration_seconds` | Histogram | `policy_id`, `agent_id` | Decision evaluation latency |
| `grc_enforcement_total` | Counter | `verdict`, `action`, `agent_id` | Total enforcement actions |
| `grc_enforcement_duration_seconds` | Histogram | `action`, `agent_id` | End-to-end enforcement latency |
| `grc_policy_evaluation_total` | Counter | `policy_id`, `engine` | Policy evaluations by engine |
| `grc_policy_evaluation_duration_seconds` | Histogram | `policy_id`, `engine` | Policy evaluation latency |
| `grc_evidence_collected_total` | Counter | `type`, `source`, `level` | Evidence items collected |
| `grc_evidence_verification_duration_seconds` | Histogram | `type`, `level` | Evidence verification latency |
| `grc_cache_hit_total` | Counter | `cache_level`, `resource_type` | Cache hits by level |
| `grc_cache_miss_total` | Counter | `cache_level`, `resource_type` | Cache misses by level |
| `grc_agent_trust_score` | Gauge | `agent_id`, `grade` | Current trust score |
| `grc_compliance_score` | Gauge | `framework`, `control_id` | Compliance score |
| `grc_kafka_consumer_lag` | Gauge | `topic`, `consumer_group` | Kafka consumer lag |
| `grc_grpc_request_total` | Counter | `service`, `method`, `status` | gRPC requests |
| `grc_grpc_request_duration_seconds` | Histogram | `service`, `method` | gRPC request latency |

#### 6.2.2 SLO Definitions

| Service | SLO | Error Budget | Measurement |
|---------|-----|-------------|-------------|
| PDP Service | 99.95% availability | 21.9 min/month | Uptime / total time |
| PEP Gateway | 99.95% availability | 21.9 min/month | Uptime / total time |
| Policy API | 99.9% availability | 43.8 min/month | Uptime / total time |
| Evidence Collection | 99.9% availability | 43.8 min/month | Successful writes / total writes |
| Overall Platform | 99.9% availability | 43.8 min/month | Weighted average |

### 6.3 Logging

#### 6.3.1 Log Levels and Destinations

| Log Type | Level | Destination | Retention | Format |
|----------|-------|-------------|-----------|--------|
| Application logs | INFO | Loki | 30 days | JSON |
| Audit logs | INFO | immudb | 7 years | JSON (hash-chained) |
| Access logs | INFO | Loki | 90 days | JSON |
| System logs | INFO | Loki | 30 days | JSON |
| Security logs | WARN | SIEM (Splunk/Elastic) | 7 years | CEF/JSON |
| Performance traces | DEBUG | Tempo | 14 days | OTLP |
| Error logs | ERROR | Loki + PagerDuty | 90 days | JSON |

#### 6.3.2 Structured Log Format

```json
{
  "timestamp": "2026-10-01T14:30:00.123Z",
  "level": "INFO",
  "service": "pdp-service",
  "version": "1.2.0",
  "trace_id": "abc123def456",
  "span_id": "span789",
  "agent_id": "agent-42",
  "policy_id": "pol-data-access-001",
  "decision_id": "uuid-v4",
  "verdict": "ALLOW",
  "action": "read",
  "resource": "s3://data/public/dataset.csv",
  "message": "Policy evaluation completed",
  "duration_ms": 12,
  "metadata": {
    "engine": "cedar",
    "cache_hit": false,
    "policy_version": "1.2.0"
  }
}
```

### 6.4 Distributed Tracing

#### 6.4.1 Trace Span Hierarchy

```
Span: agent_action (root)
├── Span: pep_interception
│   ├── Span: mtls_authentication
│   └── Span: input_document_building
├── Span: pdp_evaluation
│   ├── Span: schema_validation
│   ├── Span: context_enrichment
│   ├── Span: cedar_evaluation
│   │   ├── Span: policy_parsing
│   │   └── Span: policy_execution
│   ├── Span: rego_evaluation
│   │   ├── Span: policy_parsing
│   │   └── Span: policy_execution
│   ├── Span: decision_aggregation
│   └── Span: evidence_hash_computation
├── Span: enforcement_decision
│   ├── Span: decision_application
│   └── Span: redaction (if applicable)
├── Span: tool_execution
│   ├── Span: llm_call (OpenInference)
│   │   ├── Span: tokenization
│   │   ├── Span: model_invocation
│   │   └── Span: response_parsing
│   └── Span: tool_invocation
└── Span: evidence_collection
    ├── Span: normalization
    └── Span: storage
```

#### 6.4.2 OpenTelemetry Collector Configuration

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: grc-claw-otel
  namespace: grc-claw-observability
spec:
  mode: deployment
  replicas: 2
  config: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
    
    processors:
      batch:
        timeout: 1s
        send_batch_size: 1024
      memory_limiter:
        limit_mib: 512
        spike_limit_mib: 128
      resource:
        attributes:
          - key: service.namespace
            value: grc-claw
            action: upsert
          - key: deployment.environment
            from_attribute: k8s.namespace.name
            action: insert
    
    exporters:
      otlp/tempo:
        endpoint: tempo:4317
        tls:
          insecure: true
      prometheusremotewrite:
        endpoint: http://prometheus:9090/api/v1/write
      loki:
        endpoint: http://loki:3100/loki/api/v1/push
    
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, batch, resource]
          exporters: [otlp/tempo]
        metrics:
          receivers: [otlp]
          processors: [memory_limiter, batch, resource]
          exporters: [prometheusremotewrite]
        logs:
          receivers: [otlp]
          processors: [memory_limiter, batch, resource]
          exporters: [loki]
```

### 6.5 Alerting

#### 6.5.1 Alert Severity Matrix

| Severity | Condition | Response Time | Escalation |
|----------|-----------|---------------|------------|
| P1 — Critical | Enforcement down, data loss risk, security breach | 5 minutes | Page on-call → Manager → Director |
| P2 — High | p99 latency > 50ms, error rate > 1%, replication lag > 30s | 15 minutes | Page on-call → Manager |
| P3 — Medium | p99 latency > 20ms, disk > 80%, backup failure | 1 hour | Slack alert → On-call |
| P4 — Low | Disk > 70%, certificate expiry < 30 days, minor config drift | 24 hours | Slack alert → Team |

#### 6.5.2 Key Alert Rules

```yaml
groups:
  - name: grc-claw-critical
    rules:
      - alert: EnforcementDown
        expr: up{job="pdp-service"} == 0
        for: 1m
        labels:
          severity: P1
        annotations:
          summary: "PDP service is down"
          description: "PDP service has been down for more than 1 minute"
      
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          / sum(rate(http_requests_total[5m])) > 0.01
        for: 5m
        labels:
          severity: P2
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 1% for 5 minutes"
      
      - alert: HighLatency
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 0.050
        for: 5m
        labels:
          severity: P2
        annotations:
          summary: "High latency detected"
          description: "p99 latency is above 50ms for 5 minutes"
      
      - alert: CacheHitRateLow
        expr: |
          sum(rate(grc_cache_hit_total[5m]))
          / (sum(rate(grc_cache_hit_total[5m])) + sum(rate(grc_cache_miss_total[5m]))) < 0.80
        for: 10m
        labels:
          severity: P3
        annotations:
          summary: "Cache hit rate is low"
          description: "Cache hit rate is below 80%"
      
      - alert: KafkaConsumerLagHigh
        expr: grc_kafka_consumer_lag > 10000
        for: 5m
        labels:
          severity: P2
        annotations:
          summary: "Kafka consumer lag is high"
          description: "Consumer lag is above 10K messages"
      
      - alert: CertificateExpiringSoon
        expr: cert_expiry_timestamp - time() < 30 * 24 * 3600
        for: 1h
        labels:
          severity: P4
        annotations:
          summary: "Certificate expiring soon"
          description: "Certificate expires in less than 30 days"
```

### 6.6 Dashboards

| Dashboard | Audience | Key Metrics |
|-----------|----------|-------------|
| Executive | C-Suite, Board | Compliance score, risk posture, incident count |
| Operations | SRE, Platform | Availability, latency, error rate, saturation |
| Enforcement | Governance team | Decision rate, decision distribution, policy violations |
| Evidence | Compliance, Audit | Evidence freshness, verification levels, coverage |
| Infrastructure | Platform | CPU, memory, disk, network, pod health |
| DR | SRE, DR team | Replication lag, backup status, failover readiness |

---

## 7. Failure Mode Analysis

### 7.1 Failure Mode Matrix

| Failure | Impact | Likelihood | Detection | Mitigation | Recovery |
|---------|--------|------------|-----------|------------|----------|
| **PDP unavailable** | Cannot make decisions | Medium | Health check + alerting | PEP falls back to cached decisions or fail-closed | Automatic: PEP uses cached decisions; PDP HPA scales up |
| **Evidence store unavailable** | Cannot store evidence | Low | Health check + alerting | PEP queues evidence locally, replays when available | Automatic: Evidence replay from local queue |
| **Agent identity service unavailable** | Cannot authenticate agents | Low | Health check + alerting | PEP uses cached SVIDs with short TTL | Automatic: PEP falls back to cached SVIDs |
| **Compliance mapping service unavailable** | Cannot generate reports | Low | Health check + alerting | Reports generated from cached mappings | Automatic: Serve stale reports with warning |
| **PEP gateway unavailable** | Agents cannot execute actions | Medium | Health check + alerting | Agents retry with exponential backoff | Automatic: K8s reschedules pod; Istio reroutes |
| **Policy compiler unavailable** | Cannot deploy new policies | Low | Health check + alerting | Existing policies continue to enforce | Manual: Retry compilation when service recovers |
| **Redis cache unavailable** | Increased PDP load | Medium | Health check + alerting | PDP evaluates without cache; increased latency | Automatic: Redis Sentinel failover |
| **PostgreSQL unavailable** | Cannot read/write policies | Low | Health check + alerting | Read from replicas; queue writes | Automatic: Patroni failover (< 30s) |
| **Kafka unavailable** | Event streaming disrupted | Low | Health check + alerting | Local buffering; retry with backoff | Automatic: Kafka partition reassignment |
| **Vault unavailable** | Cannot access secrets | Low | Health check + alerting | Cached secrets with TTL; fail-closed for new | Automatic: Vault HA failover |
| **SPIRE unavailable** | Cannot issue new SVIDs | Low | Health check + alerting | Existing SVIDs valid until expiry | Automatic: SPIRE HA failover |
| **MinIO unavailable** | Cannot store evidence | Low | Health check + alerting | Queue evidence locally; retry | Automatic: MinIO heal |
| **immudb unavailable** | Cannot write audit trail | Low | Health check + alerting | Buffer audit events; retry | Automatic: immudb HA failover |
| **Istio sidecar unavailable** | mTLS broken | Low | Health check + alerting | Application-level mTLS fallback | Automatic: Sidecar restart |
| **Node failure** | Pod disruption | Medium | Node monitoring | Pod rescheduled to healthy node | Automatic: K8s reschedules (< 2min) |
| **Zone failure** | Service degradation | Low | Multi-zone monitoring | Traffic routed to remaining zones | Automatic: Cross-zone failover (< 30s) |
| **Region failure** | Full outage | Very low | Health check + alerting | DR failover to secondary region | Manual: ArgoCD promotes DR (< 4h) |

### 7.2 Failure Scenarios and Recovery Procedures

#### 7.2.1 Scenario 1: Single Component Failure (Automatic)

```
1. Kubernetes detects failure (liveness probe fails)
2. Pod rescheduled to healthy node (< 2 minutes)
3. Istio reroutes traffic to healthy instances (< 5 seconds)
4. Alert fired to on-call engineer
5. Post-incident review scheduled
```

#### 7.2.2 Scenario 2: Zone Failure (Automatic)

```
1. Load balancer detects zone failure
2. Traffic routed to remaining zones (< 30 seconds)
3. HPA scales up replicas in remaining zones (< 5 minutes)
4. Patroni promotes PostgreSQL replica in healthy zone (< 30 seconds)
5. Redis Sentinel promotes replica (< 10 seconds)
6. Kafka reassigns partitions (< 2 minutes)
7. Alert fired to on-call engineer
```

#### 7.2.3 Scenario 3: Region Failure (Manual)

```
1. On-call engineer declares region failure
2. ArgoCD promotes DR cluster to production (< 15 minutes)
3. PostgreSQL replica promoted to primary (< 5 minutes)
4. Redis replica promoted (< 2 minutes)
5. Kafka MirrorMaker2 reversed (< 5 minutes)
6. MinIO bucket replication reversed (< 10 minutes)
7. Vault performance replica promoted (< 5 minutes)
8. DNS updated to DR region (< 5 minutes)
9. Microservices scaled up in DR region (< 15 minutes)
10. Total RTO: < 4 hours
```

### 7.3 Circuit Breaker Configuration

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: pdp-service-circuit-breaker
  namespace: grc-claw-control-plane
spec:
  host: pdp-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
```

### 7.4 Retry and Timeout Policies

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: pdp-service-retry
  namespace: grc-claw-control-plane
spec:
  hosts:
    - pdp-service
  http:
    - route:
        - destination:
            host: pdp-service
      retries:
        attempts: 3
        perTryTimeout: 2s
        retryOn: gateway-error,connect-failure,refused-stream
      timeout: 10s
```

### 7.5 Graceful Degradation Strategy

| Component | Degradation Mode | Trigger | User Impact |
|-----------|-----------------|---------|-------------|
| PDP | Fail-closed (deny all) | PDP unavailable | Agents blocked from actions |
| PDP | Fail-open (allow with audit) | PDP unavailable + emergency flag | Agents allowed, all actions audited |
| Evidence | Queue locally | Evidence store unavailable | Delayed evidence, no data loss |
| Analytics | Skip scoring | Analytics engine unavailable | No risk scoring, basic enforcement continues |
| Compliance | Serve cached reports | Compliance mapping unavailable | Stale reports with warning |
| Cache | Bypass cache | Redis unavailable | Increased PDP load, higher latency |
| Kafka | Local buffering | Kafka unavailable | Delayed event processing |

### 7.6 Data Integrity Protection

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DATA INTEGRITY MECHANISMS                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Hash-Chained Audit Trail (immudb)                                   │   │
│  │                                                                     │   │
│  │  Event 1 ──▶ SHA-256(Event 1) ──▶ Hash 1                           │   │
│  │  Event 2 ──▶ SHA-256(Event 2 + Hash 1) ──▶ Hash 2                  │   │
│  │  Event 3 ──▶ SHA-256(Event 3 + Hash 2) ──▶ Hash 3                  │   │
│  │  ...                                                                │   │
│  │                                                                     │   │
│  │  Verification: Recompute chain from Event 1 to N                   │   │
│  │  Tamper detection: Any change breaks the chain                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  WORM Storage (MinIO)                                                │   │
│  │                                                                     │   │
│  │  • Object lock: Compliance mode (retention period)                  │   │
│  │  • Versioning: Enabled                                              │   │
│  │  • Replication: Cross-region                                        │   │
│  │  • Encryption: SSE-S3                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Decision Certificate Signing                                        │   │
│  │                                                                     │   │
│  │  • ECDSA P-256 signature on every decision                          │   │
│  │  • HSM-backed signing keys                                           │   │
│  │  • Signature verification on audit                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.7 Chaos Engineering Tests

| Test | Frequency | Scope | Success Criteria |
|------|-----------|-------|------------------|
| Component failure | Weekly | Kill single pod | Recovery < 2 min, zero data loss |
| Zone failure | Monthly | Simulate zone loss | Recovery < 15 min, RPO < 5 min |
| Region failure | Quarterly | Full region failover | RTO < 4 hours, RPO < 30 min |
| Backup restore | Monthly | Restore to staging | Data integrity verified |
| Chaos engineering | Monthly | Random component kills | Graceful degradation |
| Network partition | Monthly | Istio fault injection | Circuit breaker engages |
| Cache poisoning | Quarterly | Inject invalid cache entries | Cache invalidation works |
| Certificate expiry | Quarterly | Short-lived cert rotation | Auto-rotation succeeds |

---

## 8. Scalability Architecture

### 8.1 Scalability Dimensions

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         SCALABILITY DIMENSIONS                                       │
│                                                                                     │
│  Dimension 1: Horizontal Scaling (Scale Out)                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Add more instances to handle increased load                               │   │
│  │  • Stateless components: PDP, PEP, Policy API, Evidence Collector           │   │
│  │  • Stateful components: PostgreSQL (read replicas), Redis (cluster mode)     │   │
│  │  • Auto-scaling: HPA (horizontal), VPA (vertical), Karpenter (nodes)         │   │
│  │  • Target: 10x scale increase without architecture change                    │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Dimension 2: Vertical Scaling (Scale Up)                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Increase resources per instance                                           │   │
│  │  • CPU: Up to 32 vCPU per instance                                            │   │
│  │  • Memory: Up to 128GB per instance                                           │   │
│  │  • Storage: Up to 2TB per volume                                              │   │
│  │  • Use case: Stateful components (PostgreSQL, Redis)                          │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Dimension 3: Functional Scaling (Decomposition)                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Decompose monolith into microservices                                      │   │
│  │  • Separate read/write paths                                                  │   │
│  │  • Separate hot/cold data paths                                               │   │
│  │  • Separate real-time/batch processing                                        │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Dimension 4: Geographic Scaling (Distribution)                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Multi-region deployment                                                    │   │
│  │  • Multi-cloud deployment                                                     │   │
│  │  • Edge deployment                                                            │   │
│  │  • Data residency compliance                                                  │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Dimension 5: Tenant Scaling (Multi-Tenancy)                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Cell-based isolation                                                       │   │
│  │  • Tenant-aware routing                                                       │   │
│  │  • Resource quotas per tenant                                                 │   │
│  │  • Custom policies per tenant                                                 │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Scaling Strategies by Component

| Component | Scaling Strategy | Min | Max | Trigger | Cooldown | Bottleneck |
|-----------|-----------------|-----|-----|---------|----------|------------|
| PDP Service | HPA (CPU + latency) | 3 | 20 | CPU > 70% or p99 > 15ms | 60s up / 300s down | OPA evaluation |
| PEP Gateway | HPA (CPU + latency) | 3 | 20 | CPU > 70% or p99 > 20ms | 60s up / 300s down | PDP round-trip |
| Policy API | HPA (CPU) | 3 | 10 | CPU > 70% | 60s up / 300s down | Database writes |
| Evidence Collector | HPA (queue depth) | 3 | 15 | Queue > 10K | 60s up / 300s down | Kafka throughput |
| Analytics Engine | HPA (CPU) | 2 | 8 | CPU > 70% | 120s up / 600s down | ML model inference |
| PostgreSQL | VPA + read replicas | 3 | 5 | N/A (manual) | N/A | Disk I/O |
| Redis | HPA (CPU) | 6 | 12 | CPU > 70% | 120s up / 600s down | Memory |
| Kafka | Partition scaling | 3 | 6 | N/A (manual) | N/A | Disk I/O |
| MinIO | Node scaling | 4 | 16 | N/A (manual) | N/A | Network bandwidth |

### 8.3 Data Partitioning Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        DATA PARTITIONING STRATEGY                                    │
│                                                                                     │
│  1. Time-Based Partitioning                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Audit events: Monthly partitions                                          │   │
│  │  • Evidence: Quarterly partitions                                             │   │
│  │  • Metrics: Daily aggregation, monthly raw                                    │   │
│  │  • Retention: Hot (30d) → Warm (90d) → Cold (365d) → Archive (7y)            │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  2. Tenant-Based Partitioning                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Cell-based: Each cell serves a subset of tenants                         │   │
│  │  • Tenant ID: Used as partition key for audit events                         │   │
│  │  • Isolation: Complete data isolation between cells                           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  3. Hash-Based Partitioning                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Kafka: Partition by `hash(agent_id) % num_partitions`                      │   │
│  │  • Redis: Cluster slot = `hash(key) % 16384`                                  │   │
│  │  • MinIO: Bucket per tenant                                                   │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  4. Range-Based Partitioning                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • PostgreSQL: Range partition by `created_at` (monthly)                      │   │
│  │  • Neo4j: Shard by `tenant_id`                                                │   │
│  │  • immudb: Time-range based compaction                                        │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 8.4 Scaling Limits and Headroom

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        SCALING LIMITS AND HEADROOM                                   │
│                                                                                     │
│  Component          Current    Max      Headroom    Scaling Action                   │
│  ────────────────── ───────── ──────── ────────── ───────────────────────────────  │
│  PDP instances      3          20       6.7x        HPA (CPU + latency)              │
│  PEP instances      3          20       6.7x        HPA (CPU + latency)              │
│  Policy API         3          10       3.3x        HPA (CPU)                        │
│  Evidence Collector 3          15       5x          HPA (queue depth)                │
│  Analytics Engine   2          8        4x          HPA (CPU)                        │
│  PostgreSQL         3 nodes    5 nodes  1.7x        VPA + read replicas             │
│  Redis              6 nodes    12 nodes 2x          Cluster mode                    │
│  Kafka              3 brokers  6 brokers 2x          Partition scaling               │
│  MinIO              4 nodes    16 nodes 4x          Node scaling                    │
│  Neo4j              3 nodes    5 nodes  1.7x        Causal cluster                  │
│  immudb             3 nodes    5 nodes  1.7x        Read replica                    │
│  Vault              3 nodes    5 nodes  1.7x        Raft cluster                    │
│                                                                                     │
│  Throughput Limits:                                                                 │
│  ──────────────────                                                                 │
│  • PDP evaluation: 10,000 decisions/s per instance                                   │
│  • PEP enforcement: 5,000 tool calls/s per instance                                  │
│  • Evidence collection: 50,000 events/s per collector                                │
│  • Kafka throughput: 100,000 msg/s per partition                                      │
│  • PostgreSQL: 50,000 TPS per node                                                    │
│  • Redis: 100,000 ops/s per node                                                      │
│                                                                                     │
│  Storage Limits:                                                                    │
│  ────────────────                                                                   │
│  • PostgreSQL: 500GB per volume (expandable to 64TB)                                  │
│  • Redis: 10GB per node (expandable to 100GB)                                         │
│  • MinIO: Unlimited (erasure coded)                                                   │
│  • immudb: 100GB per node (expandable to 1TB)                                         │
│  • Kafka: 1TB per broker (expandable)                                                 │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 8.5 Growth Projections and Capacity Planning

| Metric | Current | 6 Months | 12 Months | 24 Months | Scaling Action |
|--------|---------|----------|-----------|-----------|----------------|
| Registered agents | 1,000 | 2,500 | 5,000 | 10,000 | HPA + cells |
| Decisions/second | 10,000 | 25,000 | 50,000 | 100,000 | HPA + partition |
| Evidence items/day | 10M | 25M | 50M | 100M | Collector scaling |
| Audit trail entries | 500M | 1.5B | 3B | 6B | Partition + tiering |
| Storage (audit trail) | 500 GB | 1.2 TB | 2.5 TB | 5 TB | Tiering + compression |
| PDP replicas | 3 | 6 | 12 | 24 | HPA |
| PEP replicas | 3 | 6 | 12 | 24 | HPA |
| Evidence collectors | 3 | 4 | 8 | 16 | HPA |
| PostgreSQL nodes | 3 | 3 | 5 | 5 | Read replicas |
| Redis nodes | 6 | 6 | 9 | 12 | Cluster mode |
| Kafka brokers | 3 | 3 | 4 | 6 | Partition scaling |
| MinIO nodes | 4 | 4 | 8 | 16 | Node scaling |

### 8.6 Auto-Scaling Configuration

```yaml
# PDP Service HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pdp-service-hpa
  namespace: grc-claw-control-plane
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pdp-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: grc_enforcement_decision_duration_seconds
        target:
          type: AverageValue
          averageValue: 15m
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
        - type: Pods
          value: 4
          periodSeconds: 60
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
        - type: Pods
          value: 2
          periodSeconds: 60
      selectPolicy: Min
---
# Evidence Collector HPA (custom metric)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: evidence-collector-hpa
  namespace: grc-claw-evidence
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: evidence-collector
  minReplicas: 3
  maxReplicas: 15
  metrics:
    - type: External
      external:
        metric:
          name: kafka_consumer_lag
          selector:
            matchLabels:
              topic: evidence.raw
        target:
          type: AverageValue
          averageValue: "10000"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
---
# Karpenter NodePool for compute scaling
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: grc-claw-compute
spec:
  template:
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["m6i.2xlarge", "m6i.4xlarge", "c6i.2xlarge", "c6i.4xlarge"]
        - key: topology.kubernetes.io/zone
          operator: In
          values: ["us-east-1a", "us-east-1b", "us-east-1c"]
      nodeClassRef:
        name: grc-claw-node-class
  limits:
    cpu: 1000
    memory: 4000Gi
  disruption:
    consolidationPolicy: WhenUnderutilized
    expireAfter: 720h
    budgets:
      - nodes: "10%"
```

### 8.7 Multi-Tenant Scaling Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     MULTI-TENANT SCALING ARCHITECTURE                                │
│                                                                                     │
│  Tenant Isolation Levels:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  Level 1: Shared Infrastructure (Small Tenants)                             │   │
│  │  ├── Shared PDP/PEP instances                                               │   │
│  │  ├── Tenant ID in request context                                           │   │
│  │  ├── Tenant-specific policies in shared policy store                         │   │
│  │  └── Resource quotas per tenant                                             │   │
│  │                                                                             │   │
│  │  Level 2: Dedicated Instances (Medium Tenants)                              │   │
│  │  ├── Dedicated PDP/PEP instances per tenant group                           │   │
│  │  ├── Shared data layer                                                      │   │
│  │  ├── Tenant-specific policy bundles                                          │   │
│  │  └── Network isolation via namespace                                        │   │
│  │                                                                             │   │
│  │  Level 3: Dedicated Cells (Large Tenants)                                   │   │
│  │  ├── Complete infrastructure per cell                                        │   │
│  │  ├── Dedicated data layer                                                   │   │
│  │  ├── Data residency compliance                                              │   │
│  │  └── Independent scaling                                                    │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Tenant Routing:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  Request → API Gateway → Tenant Router → Cell Selection                     │   │
│  │                                                                             │   │
│  │  Routing Criteria:                                                          │   │
│  │  • Tenant ID (from JWT token)                                               │   │
│  │  • Data residency requirements                                              │   │
│  │  • Tenant tier (enterprise, standard, basic)                                │   │
│  │  • Geographic proximity                                                     │   │
│  │  • Current cell capacity                                                    │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Resource Quotas:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  Tier        Agents    Decisions/s    Evidence/day    Storage/month         │   │
│  │  ──────────  ────────  ─────────────  ──────────────  ───────────────────  │   │
│  │  Basic       10        100            1M                10GB                 │   │
│  │  Standard    100       1,000          10M               100GB                │   │
│  │  Enterprise  1,000     10,000         100M              1TB                  │   │
│  │  Custom      Custom    Custom          Custom            Custom              │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 8.8 Scalability Testing and Validation

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     SCALABILITY TESTING AND VALIDATION                               │
│                                                                                     │
│  Test Scenarios:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  1. Linear Scaling Test                                                     │   │
│  │     • Double instances, verify throughput doubles                            │   │
│  │     • Measure latency at each scaling level                                  │   │
│  │     • Identify breaking point                                                │   │
│  │                                                                             │   │
│  │  2. Burst Scaling Test                                                      │   │
│  │     • Sudden 10x traffic spike                                                │   │
│  │     • Measure auto-scaling response time                                     │   │
│  │     • Verify no request drops                                                 │   │
│  │                                                                             │   │
│  │  3. Sustained Load Test                                                     │   │
│  │     • 72-hour sustained load at 80% capacity                                 │   │
│  │     • Monitor for memory leaks, connection leaks                             │   │
│  │     • Verify stable latency                                                  │   │
│  │                                                                             │   │
│  │  4. Failure Recovery Test                                                   │   │
│  │     • Kill 50% of instances during load                                      │   │
│  │     • Measure recovery time                                                  │   │
│  │     • Verify data integrity                                                  │   │
│  │                                                                             │   │
│  │  5. Multi-Tenant Isolation Test                                             │   │
│  │     • Load one tenant, verify others unaffected                             │   │
│  │     • Test tenant quota enforcement                                          │   │
│  │     • Verify data isolation                                                  │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  Success Criteria:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  • Linear scaling: Throughput increases linearly up to max replicas          │   │
│  │  • Latency: p99 remains < 100ms at all scaling levels                        │   │
│  │  • Availability: 99.9% during scaling events                                 │   │
│  │  • Recovery: < 5 minutes to full capacity after failure                      │   │
│  │  • Data integrity: Zero data loss during scaling events                      │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Appendix A: Component Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        COMPONENT DEPENDENCY GRAPH                                    │
│                                                                                     │
│                              ┌─────────────┐                                        │
│                              │   Agent     │                                        │
│                              │  Identity   │                                        │
│                              └──────┬──────┘                                        │
│                                     │                                               │
│                              ┌──────▼──────┐                                        │
│                              │     PEP     │                                        │
│                              │   Gateway   │                                        │
│                              └──┬───┬───┬──┘                                        │
│                                 │   │   │                                           │
│                    ┌────────────┘   │   └────────────┐                              │
│                    │                │                │                              │
│             ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐                        │
│             │     PDP     │  │  Evidence │  │   Policy    │                        │
│             │   Service   │  │  Store    │  │    API      │                        │
│             └──┬───┬───┬──┘  └─────┬─────┘  └──────┬──────┘                        │
│                │   │   │             │               │                               │
│    ┌───────────┘   │   └─────────────┘               │                               │
│    │               │                                 │                               │
│    │        ┌──────▼──────┐                   ┌──────▼──────┐                        │
│    │        │    Redis    │                   │ PostgreSQL  │                        │
│    │        │   (Cache)   │                   │  (Policies) │                        │
│    │        └─────────────┘                   └─────────────┘                        │
│    │                                                                             │
│    │        ┌─────────────┐                   ┌─────────────┐                        │
│    └───────▶│    Kafka    │                   │    Neo4j    │                        │
│             │  (Events)   │                   │   (Graph)   │                        │
│             └──────┬──────┘                   └─────────────┘                        │
│                    │                                                                │
│             ┌──────▼──────┐                   ┌─────────────┐                        │
│             │  Analytics  │                   │  Compliance │                        │
│             │   Engine    │                   │   Mapping   │                        │
│             └──────┬──────┘                   └──────┬──────┘                        │
│                    │                                  │                               │
│             ┌──────▼──────┐                   ┌──────▼──────┐                        │
│             │    OTel     │                   │  Reporting  │                        │
│             │  Collector  │                   │   Engine    │                        │
│             └─────────────┘                   └─────────────┘                        │
│                                                                                     │
│  Legend:                                                                             │
│  ───────                                                                             │
│  Solid line: Synchronous dependency (gRPC/REST)                                     │
│  Dashed line: Asynchronous dependency (Kafka)                                       │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Appendix B: Technology Stack Summary

| Layer | Component | Technology | Version | Purpose |
|-------|-----------|-----------|---------|---------|
| **Interface** | API Gateway | Kong | 3.5+ | AuthN, rate limiting, routing |
| **Interface** | Service Mesh | Istio | 1.20+ | mTLS, traffic management |
| **Interface** | Ingress | NGINX | 1.9+ | TLS termination, WAF |
| **Policy** | Policy Engine | OPA | 0.60+ | Rego evaluation |
| **Policy** | Policy Language | Cedar | 3.0+ | Cedar evaluation |
| **Policy** | Policy Store | PostgreSQL | 16+ | Policy persistence |
| **Policy** | Policy Graph | Neo4j | 5+ | Dependency tracking |
| **Decision** | Decision Cache | Redis | 7.2+ | Decision caching |
| **Enforcement** | MCP Gateway | Python/TS | 1.0+ | Tool call interception |
| **Enforcement** | Sidecar Proxy | Envoy | 1.28+ | HTTP/gRPC interception |
| **Enforcement** | Kernel Enforcer | eBPF | 5.10+ | OS-level control |
| **Evidence** | Normalizer | Python | 3.12+ | OSCAL normalization |
| **Evidence** | Store | MinIO | 2024+ | WORM object storage |
| **Evidence** | Audit Store | immudb | 1.9+ | Immutable audit trail |
| **Observability** | Traces | OpenTelemetry | 1.20+ | Distributed tracing |
| **Observability** | Metrics | Prometheus | 2.48+ | Metrics collection |
| **Observability** | Logs | Loki | 3.0+ | Log aggregation |
| **Observability** | Dashboards | Grafana | 10.2+ | Visualization |
| **Identity** | Identity Framework | SPIFFE/SPIRE | 1.8+ | SVID issuance |
| **Identity** | Secrets | HashiCorp Vault | 1.15+ | Secret management |
| **Compliance** | Crosswalk Engine | Python | 3.12+ | Framework mapping |
| **Compliance** | Report Generator | Python | 3.12+ | Report generation |
| **Analytics** | Analytics Engine | Python | 3.12+ | Risk scoring, ML |
| **Analytics** | ML Serving | SageMaker/Vertex | - | Model inference |
| **Event Streaming** | Message Queue | Kafka | 3.6+ | Event-driven architecture |
| **Task Queue** | Workflow | Temporal | 1.20+ | Approval workflows |
| **Container** | Runtime | containerd | 1.7+ | Container runtime |
| **Container** | Orchestration | Kubernetes | 1.28+ | Container orchestration |
| **Deployment** | GitOps | ArgoCD | 2.9+ | Git-based deployment |
| **Deployment** | Progressive Delivery | Argo Rollouts | 0.32+ | Canary/blue-green |
| **Deployment** | Serverless | Knative | 1.12+ | Scale-to-zero |
| **Deployment** | Helm | Helm | 3.13+ | Package management |
| **Security** | Image Signing | Cosign | 2.2+ | Supply chain security |
| **Security** | Vulnerability Scanning | Trivy | 0.47+ | Image scanning |
| **Security** | SBOM | Syft | 0.95+ | Software bill of materials |
| **Security** | Cert Management | cert-manager | 1.13+ | Certificate automation |
| **Security** | Secrets Sync | External Secrets | 0.9+ | Secret synchronization |
| **Cost** | Cost Management | Kubecost | 2.0+ | Cost optimization |
| **Scaling** | Node Autoscaling | Karpenter | 0.34+ | Node provisioning |
| **Chaos** | Chaos Engineering | Litmus | 3.0+ | Failure testing |
| **SLO** | SLO Monitoring | Sloth | 0.11+ | SLO tracking |

---

*End of Component Design Specification.* </longcat_think>
