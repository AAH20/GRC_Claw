# Microsoft Agent Governance Toolkit — Deep-Dive & Hermes Agent Integration Guide

**For:** Ahmed Hassan (CISO/GRC) — GRC_Claw ISO 42001 Governance Chassis  
**Source:** github.com/microsoft/agent-governance-toolkit (6.2K stars, MIT, Public Preview v4.x)  
**OWASP Agentic Top 10:** Published Dec 9, 2025 by OWASP GenAI Security Project

---

## 1. Architecture Overview

AGT is a **runtime governance middleware** that sits between an agent framework and the actions agents take. It answers three questions: *Is this action allowed? Which agent did this? Can you prove what happened?*

### Core Principle

> Prompt-based safety has a **26.67% policy violation rate** in red-team testing. AGT's application-layer enforcement: **0.00%**. Actions the kernel denies are **structurally impossible**, not merely unlikely.

### Four-Layer Architecture

```
Agent ──► Policy Engine ──► Identity ──► Audit Log ──► Sandbox
         (YAML/OPA/Cedar)   (SPIFFE/DID/mTLS) (Merkle chain) (4 privilege rings)
              │                    │                │               │
              ├── Allowed ──► Tool executes ────────┘               │
              └── Denied  ──► GovernanceDenied                      │
                                                                   ▼
                                                          Execution environment
```

### Layer 1: Policy Engine (Agent Control Specification — ACS)

| Property | Contract |
|----------|----------|
| **Stateless** | No mutable state influences later verdicts; host supplies complete snapshot per call |
| **Deterministic** | Same manifest + snapshot + mode → same verdict every time |
| **Fail-closed** | Default deny; explicit allow required |
| **Sub-millisecond** | <0.1ms p99 for policy evaluation (Rust core) |

**Policy formats supported:** YAML (start here), OPA Rego (complex conditionals), Cedar (attribute-based access control). Mix formats in a single policy file.

**Eight intervention points:**
- `agent_startup` — evaluate session metadata before run
- `input` — evaluate external request ingress
- `pre_model_call` — evaluate messages, context, tool definitions before model call
- `pre_tool_call` — evaluate tool invocation before execution (primary enforcement point)
- `post_tool_call` — evaluate tool result after execution
- `output` — evaluate agent output before delivery
- `agent_shutdown` — evaluate session termination
- `inter_agent` — evaluate inter-agent messages

**Verdict types:** `allow`, `deny`, `warn`, `require_approval`, `transform` (redact/modify), `escalate`

### Layer 2: Zero-Trust Identity (Agent Mesh)

| Capability | Implementation |
|------------|----------------|
| Agent identity | Ed25519 keypair per agent |
| Workload identity | SPIFFE certificates |
| Cross-mesh trust | DID (Decentralized Identifier) verification |
| Transport security | mutual TLS (mTLS) for agent-to-agent communication |
| Trust scoring | Continuous behavioral score; demotion triggers privilege reduction |
| Action-level auth | Every action individually authenticated — no trusted sessions |

### Layer 3: Audit Trail (Tamper-Evident)

| Feature | Detail |
|---------|--------|
| Integrity | SHA-256 Merkle chain — any modification invalidates all subsequent hashes |
| Proof | O(log n) inclusion proofs for external auditors |
| Export | CloudEvents v1.0 JSON envelopes |
| Events | `tool_invocation`, `tool_blocked`, `policy_evaluation`, `policy_violation`, `rogue_detection`, `agent_invocation` |
| Verification | `verify_integrity()` for full chain; `get_proof(entry_id)` for single-entry proof |

### Layer 4: Execution Sandbox (Agent Runtime)

Four privilege rings modeled on OS protection rings:

| Ring | Level | Use Case |
|------|-------|----------|
| Ring 0 | Kernel | Governance operations only (policy eval, identity, audit) — no agent ever runs here |
| Ring 1 | System | Agent lifecycle management, inter-agent communication, framework adapters |
| Ring 2 | User | Default for normal agent tool calls |
| Ring 3 | Untrusted | Agents handling untrusted input, flagged by trust scoring — narrowest capabilities |

Additional runtime features: saga orchestration (multi-step rollback), termination control, execution plan validation, command denylist enforcement, kill switch.

### SRE Layer

- SLO monitoring with error budgets
- Circuit breakers (trip on repeated policy violations)
- Chaos testing for agent resilience
- Output validation (hallucination detection, data integrity)

### MCP Security Gateway

- Tool poisoning detection
- Schema drift monitoring
- Typosquatting detection
- Hidden instruction scanning

---

## 2. Key Features for Ahmed's Stack

### OWASP Agentic Top 10 Coverage

| ASI | Risk | Coverage | Primary AGT Control |
|-----|------|----------|---------------------|
| ASI01 | Agent Goal Hijack | ✅ Full | ACS input annotators, prompt-injection detection, audit |
| ASI02 | Tool Misuse | ✅ Full | Manifest tool catalog, `pre_tool_call`, sandbox controls |
| ASI03 | Identity & Privilege Abuse | ✅ Full | AgentMesh identity, capability checks, approval gates |
| ASI04 | Agentic Supply Chain | ⚠️ Partial | Policy YAML tool pinning; no SBOM generation |
| ASI05 | Unexpected Code Execution | ✅ Full | Sandbox providers, static reviewer (detects pickle/eval), tool policy |
| ASI06 | Memory & Context Poisoning | ⚠️ Partial | Audit hash-chain; no memory sandbox |
| ASI07 | Insecure Inter-Agent Comms | ✅ Full | AgentMesh trust-gate with DID verification, encrypted transport |
| ASI08 | Cascading Failures | ✅ Full | Circuit breakers, SLOs, rate limits, session budgets |
| ASI09 | Human-Agent Trust Exploitation | ⚠️ Partial | Audit trail, ReversibilityChecker; no UI-level guardrails |
| ASI10 | Rogue Agents | ✅ Full | AgentBehaviorMonitor, quarantine, kill switch |

**Summary: 7/10 Full, 3/10 Partial, 0 Gaps.**

### Deterministic Policy Engine

Unlike prompt-based safety (probabilistic), AGT intercepts every tool call in deterministic application code **before** the model's intent reaches the wire. The policy engine:

- Evaluates rules in priority order (higher priority checked first)
- Supports `allow`, `deny`, `require_approval`, `warn`, `throttle` effects
- Composes multi-tier policy hierarchies (org → platform → app)
- Conflict resolution: `deny_overrides` strategy
- Every decision recorded as trace attribute → audit trail

### Multi-Language SDKs

| Language | Package | Install |
|----------|---------|---------|
| Python | `agent-governance-toolkit[full]` | `pip install "agent-governance-toolkit[full]"` |
| TypeScript | `@microsoft/agent-governance-sdk` | `npm install @microsoft/agent-governance-sdk` |
| .NET | `Microsoft.AgentGovernance` | `dotnet add package Microsoft.AgentGovernance` |
| Rust | `agent-governance` | `cargo add agent-governance` |
| Go | `agent-governance-toolkit` | `go get github.com/microsoft/agent-governance-toolkit/agent-governance-golang` |

All five SDKs implement core governance (policy, identity, trust, audit). Python has the full stack.

### Framework Integrations

| Framework | Integration Type |
|-----------|-----------------|
| Microsoft Agent Framework | Native Middleware |
| Semantic Kernel | Native (.NET + Python) |
| AutoGen | Adapter |
| LangGraph / LangChain | Adapter |
| CrewAI | Adapter |
| OpenAI Agents SDK | Middleware |
| Claude Code | Governance plugin package |
| Google ADK | Adapter |
| LlamaIndex | Middleware |
| Haystack | Pipeline |
| PydanticAI | Function tool decorator |
| Dify | Plugin |
| GitHub Copilot CLI | Governance installer |

### CLI Tools (`agt`)

```bash
agt doctor                                        # check installation
agt verify                                        # OWASP compliance check
agt verify --evidence ./agt-evidence.json --strict  # fail CI on weak evidence
agt red-team scan ./prompts/ --min-grade B       # prompt injection audit
agt lint-policy policies/                          # validate policy files
```

### Compliance Mapping

| Standard | Coverage |
|----------|----------|
| OWASP Agentic AI Top 10 | All ASI risk categories mapped with deterministic controls |
| NIST AI RMF 1.0 | Full GOVERN, MAP, MEASURE, MANAGE alignment |
| EU AI Act | Compliance mapping with automated evidence |
| SOC 2 | Control mapping with audit trail export |
| AARM Extended | All R1–R9 requirements satisfied |
| ATF | All five elements mapped |

---

## 3. Integration Guide — Wrapping Hermes Agent with Governance Policies

### Architecture for Hermes

Hermes Agent has a first-class Python plugin system with synchronous `pre_tool_call` and `post_tool_call` hooks that cover **every** tool the agent runs — terminal, file, web, browser, vision, cron, custom skills. This makes it the cleanest integration surface among major coding agents.

```
Hermes Agent
    │
    ▼
pre_tool_call hook (Python callback, in-process)
    │
    ▼
AGT Policy Engine (ACS runtime)
    │
    ├── ALLOW → delegate to native Hermes tool handler
    ├── DENY  → return structured refusal with policy ID + reason
    └── REQUIRE_APPROVAL → block + prompt user to approve out-of-band
    │
    ▼
post_tool_call hook (observational — audit logging)
    │
    ▼
Merkle audit chain
```

### Option A: Direct AGT Integration (Python)

```python
# hermes_plugin.py — Hermes plugin that wraps tool calls with AGT governance
from agentmesh.governance import govern
from agent_control_specification import AgentControl, HostSession

# Load policy from YAML manifest
runtime = AgentControl.from_path("policies/hermes-governance.yaml")
session = HostSession(runtime, agent_id="hermes-agent", session_id="hermes-session-001")

def pre_tool_call(tool_name: str, arguments: dict, session_id: str) -> dict:
    """Hermes calls this before every tool dispatch."""
    try:
        result = session.evaluate_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            agent_id="hermes-agent"
        )
        if result.allowed:
            return {"action": "allow"}
        else:
            return {
                "action": "block",
                "message": f"[AGT] Denied by policy '{result.policy_id}': {result.reason}"
            }
    except Exception as e:
        # Fail-closed: block on any governance error
        return {
            "action": "block",
            "message": f"[AGT] Governance error: {str(e)}"
        }

def post_tool_call(tool_name: str, arguments: dict, result: dict, session_id: str) -> None:
    """Observational hook — log for audit."""
    session.log_tool_result(
        tool_name=tool_name,
        arguments=arguments,
        result=result,
        agent_id="hermes-agent"
    )
```

### Option B: IntentFrame Plugin (External Policy Runtime)

IntentFrame provides an external policy checkpoint that gates terminal, code, file, and cron tool calls before they run:

```bash
# Install
curl -fsSL https://github.com/intentframe/agent-integrations/raw/main/scripts/install-hermes-plugin.sh | bash

# Start enforcement stack
intentframe-integrations up hermes

# Configure governed tools
intentframe-integrations governance enable hermes terminal
intentframe-integrations governance enable hermes execute_code
intentframe-integrations governance enable hermes write_file
intentframe-integrations governance enable hermes patch
intentframe-integrations governance enable hermes cronjob

# Set policy
intentframe-integrations policy set hermes ~/.intentframe/integrations/hermes/policy.yaml
```

### Option C: Agentic Control Plane (ACP) Plugin

```bash
pip install hermes-acp
hermes plugins enable acp
hermes-acp login
```

ACP registers two hooks: `pre_tool_call` → POST `/govern/tool-use` (allow/deny/ask) and `post_tool_call` → POST `/govern/tool-output` (observational audit).

### Recommended Approach for GRC_Claw

**Use Option A (direct AGT) for production** because:
1. Deterministic enforcement in-process (no network dependency)
2. Full OWASP ASI coverage with `agt verify` compliance checking
3. Tamper-evident audit trail with Merkle chain
4. Policy-as-code with YAML — versionable, reviewable, auditable
5. Multi-tier policy composition (org → platform → app)

**Use Option B (IntentFrame) for defense-in-depth** — external judge outside the agent process.

---

## 4. Configuration Examples

### Basic Policy — Block Dangerous Operations

```yaml
# policies/hermes-governance.yaml
apiVersion: governance.toolkit/v1
name: hermes-production-policy
description: "Production governance policy for Hermes Agent"
default_action: deny
on_timeout: deny  # fail-closed on governance engine timeout

rules:
  # Block destructive database operations
  - name: block-destructive-db
    condition: "action.type in ['drop', 'delete', 'truncate']"
    action: deny
    description: "Destructive operations require human approval"
    priority: 1000

  # Block credential access
  - name: block-credential-access
    condition: "action.type == 'read' and resource.type == 'credentials'"
    action: deny
    description: "Direct credential access is forbidden"
    priority: 1000

  # Block PII exfiltration
  - name: block-pii-export
    condition: "action.type == 'export' and data.contains_pii"
    action: deny
    description: "PII data must never leave the system"
    priority: 1000

  # Require approval for email sends
  - name: approve-email-sends
    condition: "action.type == 'send_email'"
    action: require_approval
    approvers: ["security-team"]
    priority: 500

  # Rate limit external API calls
  - name: rate-limit-api
    condition: "action.type == 'api_call'"
    action: throttle
    limit: "100/hour"
    priority: 500

  # Block external network requests without approval
  - name: block-external-network
    condition: "action.type == 'http_request' and target.is_external"
    action: require_approval
    approvers: ["platform-oncall"]
    priority: 800

  # Allow read-only operations
  - name: allow-read
    condition: "action.type == 'read'"
    action: allow
    priority: 100

  # Audit everything
  - name: audit-everything
    condition: "true"
    action: log
    priority: 0
```

### Multi-Tier Policy Composition (CISO → Platform → App)

```yaml
# policies/org-baseline.yaml — CISO non-negotiables
apiVersion: governance.toolkit/v1
name: org-baseline
description: "Organization-wide non-negotiable controls"
default_action: deny
rules:
  - name: block-pii-export
    condition: "action.type == 'export' and data.contains_pii"
    action: deny
    priority: 1000
  - name: block-credential-access
    condition: "action.type == 'read' and resource.type == 'credentials'"
    action: deny
    priority: 1000
  - name: audit-everything
    condition: "true"
    action: log
    priority: 0
```

```yaml
# policies/platform-shared.yaml — Platform team controls
apiVersion: governance.toolkit/v1
name: platform-shared
extends: org-baseline.yaml
description: "Platform-level controls for all agents"
default_action: deny
rules:
  - name: rate-limit-api
    condition: "action.type == 'api_call'"
    action: warn
    limit: "100/hour"
    priority: 500
  - name: block-external-network
    condition: "action.type == 'http_request' and target.is_external"
    action: require_approval
    approvers: ["platform-oncall"]
    priority: 800
```

```yaml
# policies/customer-service-agent.yaml — App-specific
apiVersion: governance.toolkit/v1
name: customer-service-agent
extends:
  - platform-shared.yaml
description: "Policy for customer service chatbot agent"
default_action: deny
rules:
  - name: allow-read-tickets
    condition: "action.type == 'read' and resource.type == 'ticket'"
    action: allow
    priority: 100
  - name: allow-send-response
    condition: "action.type == 'send_message' and target.type == 'customer'"
    action: allow
    priority: 100
  - name: block-refund-over-500
    condition: "action.type == 'refund' and amount.value > 500"
    action: require_approval
    approvers: ["cs-manager"]
    priority: 200
```

### ACS Manifest (Advanced — Full Lifecycle)

```yaml
# policies/acs-owasp-manifest.yaml
agent_control_specification_version: "0.3.1-beta"
metadata:
  name: hermes-owasp-governance
  description: "Full OWASP ASI coverage for Hermes Agent"

policies:
  input_safety:
    type: rego
    bundle: ./policy
    query: data.hermes.input.verdict

  tool_governance:
    type: rego
    bundle: ./policy
    query: data.hermes.tool.verdict

  output_filter:
    type: rego
    bundle: ./policy
    query: data.hermes.output.verdict

intervention_points:
  input:
    policy_target: "$.input.body"
    policy_target_kind: input_body
    policy:
      id: input_safety

  pre_tool_call:
    policy_target: "$.tool_call.args"
    policy_target_kind: tool_args
    tool_name_from: "$.tool_call.name"
    policy:
      id: tool_governance

  post_tool_call:
    policy_target: "$.tool_result"
    policy_target_kind: tool_result
    tool_name_from: "$.tool_call.name"
    policy:
      id: tool_governance

  output:
    policy_target: "$.output.body"
    policy_target_kind: output_body
    policy:
      id: output_filter

tools:
  terminal:
    type: Tool
    id: terminal
    clearance: internal
    security_labels: ["shell", "file_system"]
  write_file:
    type: Tool
    id: write_file
    clearance: internal
    security_labels: ["file_write"]
  web_search:
    type: Tool
    id: web_search
    clearance: external
    security_labels: ["network"]

approval:
  backend: webhook
  endpoint: https://grc-claw.internal/api/approvals
  timeout_seconds: 300
```

### Rego Policy Example (OWASP ASI01 — Goal Hijack Detection)

```rego
# policy/input.rego
package hermes.input

import future.keywords.if
import future.keywords.in

# Deny if prompt injection patterns detected
verdict := {"effect": "deny", "reason": "Prompt injection detected"} if {
    contains(lower(input.body), "ignore previous instructions")
}

verdict := {"effect": "deny", "reason": "Prompt injection detected"} if {
    contains(lower(input.body), "you are now")
}

verdict := {"effect": "deny", "reason": "Prompt injection detected"} if {
    contains(lower(input.body), "system prompt")
}

# Deny if goal hijack patterns detected
verdict := {"effect": "deny", "reason": "Goal hijack attempt detected"} if {
    contains(lower(input.body), "your new objective is")
}

verdict := {"effect": "deny", "reason": "Goal hijack attempt detected"} if {
    contains(lower(input.body), "forget your purpose")
}

# Default allow
verdict := {"effect": "allow"} if {
    not deny
}

deny := true if {
    contains(lower(input.body), "ignore previous instructions")
}

deny := true if {
    contains(lower(input.body), "you are now")
}
```

### Hermes Plugin Registration

```python
# hermes_agt_plugin.py
"""Hermes Agent plugin for AGT governance enforcement."""

from hermes_agent.plugins import register, PluginContext
from agent_control_specification import AgentControl, HostSession
from agentmesh.governance.audit import AuditLog
import json
import os

# Initialize governance runtime
POLICY_PATH = os.environ.get("AGT_POLICY_PATH", "policies/acs-owasp-manifest.yaml")
runtime = AgentControl.from_path(POLICY_PATH)
audit_log = AuditLog()

# Agent identity
AGENT_ID = os.environ.get("AGT_AGENT_ID", "hermes-agent")
SESSION_ID = os.environ.get("AGT_SESSION_ID", "hermes-session-001")

session = HostSession(runtime, agent_id=AGENT_ID, session_id=SESSION_ID)

@register
def pre_tool_call(ctx: PluginContext, tool_name: str, arguments: dict) -> dict:
    """Intercept every tool call before execution."""
    try:
        result = session.evaluate_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            agent_id=AGENT_ID
        )

        # Log the decision
        audit_log.log(
            event_type="policy_evaluation",
            agent_did=f"did:web:{AGENT_ID}",
            action="allow" if result.allowed else "deny",
            resource=tool_name,
            outcome="success" if result.allowed else "blocked",
            details={
                "policy_id": result.policy_id,
                "reason": result.reason,
                "tool_arguments": arguments
            }
        )

        if result.allowed:
            return {"action": "allow"}
        else:
            return {
                "action": "block",
                "message": f"[AGT] Denied by policy '{result.policy_id}': {result.reason}"
            }

    except Exception as e:
        # Fail-closed
        audit_log.log(
            event_type="policy_violation",
            agent_did=f"did:web:{AGENT_ID}",
            action="error",
            resource=tool_name,
            outcome="error",
            details={"error": str(e)}
        )
        return {
            "action": "block",
            "message": f"[AGT] Governance error (fail-closed): {str(e)}"
        }

@register
def post_tool_call(ctx: PluginContext, tool_name: str, arguments: dict, result: dict) -> None:
    """Observational hook — audit logging."""
    audit_log.log(
        event_type="tool_invocation",
        agent_did=f"did:web:{AGENT_ID}",
        action="complete",
        resource=tool_name,
        outcome="success",
        details={"tool_arguments": arguments, "result_summary": str(result)[:200]}
    )
```

---

## 5. ISO 42001 Alignment

### Clause-by-Clause Mapping

| ISO 42001 Clause | Requirement | AGT Evidence |
|-----------------|-------------|--------------|
| **4. Context** | Define AIMS scope, interested parties, AI system boundaries | Agent inventory via AgentMesh; policy manifests define scope per agent |
| **5. Leadership** | Top management assigns roles, AI policy, accountability | `agt verify` compliance reports; policy-as-code with named owners |
| **6. Planning** | AI risk assessment, impact assessment, risk treatment | OWASP ASI mapping; `agt red-team scan` for risk identification; policy rules as risk treatments |
| **7. Support** | Resources, competence, awareness, documented information | Policy documentation; audit trail as documented information; `agt lint-policy` for quality |
| **8. Operation** | Operational planning, risk treatment execution, impact assessment | Deterministic policy enforcement; `pre_tool_call` hooks; sandbox execution |
| **9. Performance Evaluation** | Monitoring, measurement, internal audit, management review | Merkle audit trail; `verify_integrity()`; `agt verify --evidence` for audit evidence; SLO monitoring |
| **10. Improvement** | Nonconformity, corrective action, continual improvement | `rogue_detection` events; policy violation tracking; `agt verify --strict` CI gate |

### Annex A Controls Mapping

| Control | Objective | AGT Coverage |
|---------|-----------|--------------|
| A.2 | Policies related to AI | Policy-as-code YAML; multi-tier composition; `agt lint-policy` |
| A.3 | Internal organization | AgentMesh identity; per-agent ownership; DID-based accountability |
| A.4 | Resources for AI systems | Agent inventory; tool catalog in manifest; MCP server registry |
| A.5 | Assessing impacts of AI systems | OWASP ASI mapping; `agt red-team scan`; ReversibilityChecker |
| A.6 | AI system lifecycle | Agent lifecycle management; `agent_startup`/`agent_shutdown` intervention points; kill switch |
| A.7 | Data for AI systems | IFC (Information Flow Control) label flow; egress policies; data clearance levels |
| A.8 | Information for interested parties | Audit trail export (CloudEvents); compliance reports; `agt verify --evidence` |
| A.9 | Use of AI systems | Deterministic policy enforcement; behavioral monitoring; AgentBehaviorMonitor |
| A.10 | Third-party and customer relationships | MCP Security Gateway; tool pinning; supply-chain trust scoring |

### ISO 42001 Certification Evidence from AGT

```bash
# Generate compliance evidence for audit
agt verify --evidence ./iso42001-evidence.json --strict

# Verify audit trail integrity (for Clause 9)
python -c "
from agentmesh.governance.audit import AuditLog
audit = AuditLog()
is_valid, error = audit.verify_integrity()
print(f'Audit trail valid: {is_valid}')
if not is_valid:
    print(f'Tampering detected: {error}')
"

# Export audit trail as CloudEvents (for Clause 9 external audit)
events = audit.export_cloudevents(start_time=one_hour_ae)
for event in events:
    print(json.dumps(event))
```

### GRC_Claw Integration Pattern

For Ahmed's ISO 42001 governance chassis:

1. **Policy Repository** — Store all AGT policy YAML files in version control (Git) with required reviews
2. **CI/CD Gate** — Run `agt verify --strict` and `agt lint-policy` in CI pipeline
3. **Audit Pipeline** — Export Merkle audit trail → SIEM → ISO 42001 Clause 9 evidence
4. **Risk Register** — Map OWASP ASI risks to ISO 42001 Clause 6 risk treatments
5. **Management Review** — Dashboard showing policy violations, trust scores, compliance posture
6. **Continuous Improvement** — `rogue_detection` events feed corrective action process (Clause 10)

---

## 6. Pitfalls and Best Practices

### Pitfalls

| Pitfall | Detail | Mitigation |
|---------|--------|------------|
| **Fail-open default** | If policy engine unreachable within timeout (default 50ms), action proceeds | Set `on_timeout: deny` in policy; monitor governance engine health |
| **Audit records attempts, not outcomes** | AGT logs what agent attempted and whether governance allowed it — not whether the action actually succeeded in the external world | Correlate with application-level logging; use post_tool_call for outcome verification |
| **Knowledge governance gap** | AGT governs actions, not the knowledge agents consume (documents, databases, embeddings retrieved during reasoning) | Use egress policies; implement DLP layer; restrict data sources per agent |
| **Credential persistence gap** | AGT governs what agents do with tools, not the credentials agents hold across tasks within a session | Implement credential vault with per-task scoping; use short-lived tokens |
| **Initialization bypass risk** | If governance middleware is incorrectly initialized, enforcement is bypassed | Health checks; `agt doctor`; fail-closed initialization; startup policy validation |
| **Performance in distributed deployments** | <0.1ms is policy engine only; full governance overhead includes network round-trip (1-10ms) and crypto verification | For multi-agent mesh: expect 5-50ms per governed interaction; use sidecar pattern |
| **No SBOM generation** | ASI04 supply chain coverage is partial — AGT does not generate SBOM for the governed system | Integrate with external SBOM tooling; use MCP server allowlist |
| **No memory sandbox** | ASI06 memory poisoning coverage is partial — audit hash-chain but no memory isolation | Implement memory provenance tracking; use RAG governance layer |
| **No UI-level guardrails** | ASI09 human-agent trust exploitation — audit trail exists but no UI-level approval interfaces | Build approval UI; use ReversibilityChecker for irreversible actions |
| **Public preview status** | May have breaking changes before GA | Pin versions; test upgrades in staging; monitor CHANGELOG |

### Best Practices

1. **Start with `govern()` + audit logging** — Most teams never need the full stack. Add layers as risk profile grows.

2. **Use deny-by-default** — `default_action: deny` with explicit allow rules. Fail-closed on timeout.

3. **Multi-tier policy composition** — CISO defines org baseline (non-negotiable), platform team adds shared controls, app teams add use-case rules. No team can weaken inherited rules.

4. **Run each agent in a separate container** — AGT enforces at application middleware layer, not OS kernel. Container isolation provides defense-in-depth.

5. **Version-control all policies** — Policy-as-code in Git with required reviews. `agt lint-policy` in CI.

6. **Verify audit trail integrity periodically** — Call `verify_integrity()` before exporting for auditors. Publish Merkle root hash for external verification.

7. **Use `agt verify --strict` in CI** — Fail builds on weak OWASP evidence. Generate compliance reports for audits.

8. **Implement kill switch** — SRE layer with emergency termination capability. Test quarterly.

9. **Monitor trust scores** — AgentMesh trust scoring continuously evaluates behavior. Demotion triggers automatic privilege reduction.

10. **Red-team continuously** — `agt red-team scan ./prompts/ --min-grade B` for prompt injection audit. Model-layer defenses are probabilistic by construction.

11. **Separate governance from agent process** — For high-risk deployments, use IntentFrame or ACP as external judge outside the agent process.

12. **Document policy decisions** — Every rule should have a `description` field explaining the risk it mitigates. This becomes ISO 42001 Clause 6 evidence.

### Security Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Deployment                       │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Model      │  │   AGT       │  │   External          │  │
│  │   Safety     │  │   Kernel    │  │   Audit             │  │
│  │   Layer      │  │   (Ring 0)  │  │   (Merkle root)     │  │
│  │   (Azure AI  │  │             │  │                     │  │
│  │   Content    │  │  Policy     │  │  SIEM / Cloud       │  │
│  │   Safety,    │  │  Identity   │  │  Events             │  │
│  │   Llama      │  │  Audit      │  │                     │  │
│  │   Guard)     │  │  Sandbox    │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Agent Container (Ring 2/3)                  │ │
│  │  Hermes Agent ──► AGT Middleware ──► Tools              │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

| Aspect | Finding |
|--------|---------|
| **Architecture** | 4-layer: Policy engine (ACS, Rust core, <0.1ms), Zero-trust identity (SPIFFE/DID/mTLS), Tamper-evident audit (Merkle chain), Execution sandbox (4 privilege rings) |
| **OWASP Coverage** | 7/10 Full, 3/10 Partial (ASI04 supply chain, ASI06 memory poisoning, ASI09 human-agent trust) |
| **Key Strength** | Deterministic enforcement — 0.00% violation rate vs 26.67% for prompt-based safety |
| **Hermes Integration** | Via `pre_tool_call` Python hook — universal coverage, synchronous, in-process |
| **ISO 42001 Alignment** | All clauses 4-10 mapped; Annex A controls A.2-A.10 covered; audit trail = Clause 9 evidence |
| **Maturity** | Public Preview v4.x — production-quality but may have breaking changes before GA |
| **Recommendation** | Adopt for GRC_Claw: policy-as-code + `agt verify` CI gate + Merkle audit trail for ISO 42001 certification evidence |
