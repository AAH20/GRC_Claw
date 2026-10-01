# GRC_Claw Agent Governance Specification

**Version:** 1.1
**Date:** 2026-10-01
**Status:** Draft
**Owner:** GRC_Claw Architecture Team
**Supersedes:** —
**Related:** GRC_Claw Gap Analysis (Gap #2), GRC_Claw Evidence Spec, GRC_Claw Roadmap Phase 2, [GRC_Claw Model Governance Spec](./grc-claw-model-governance-spec.md)

---

## 1. Purpose & Scope

This specification defines the **Agent Governance Protocol (AGP)** — the open standard for governing autonomous AI agents within and across organizational boundaries. It addresses the critical gap identified in Wave 1 research: no universal protocol exists for multi-agent governance, agent identity is unsolved, and cross-organizational accountability is missing.

**In scope:**
- Agent identity model and lifecycle
- Agent lifecycle management (provisioning, performance, behavior, risk, compliance, retirement)
- Delegation chain tracking and enforcement
- Multi-agent trust framework
- Agent-to-agent authorization protocol
- Agent audit trail format

**Out of scope:**
- Model-level governance (bias, fairness, explainability) — covered by [GRC_Claw Model Governance Spec](./grc-claw-model-governance-spec.md)
- Human-to-agent interaction governance — covered by GRC_Claw's policy engine
- Infrastructure-level controls (network, compute) — covered by existing security frameworks

**Design principles:**
1. **Zero-trust by default** — no agent is trusted without verification
2. **Deterministic enforcement** — policy decisions are reproducible, not probabilistic
3. **Fail-closed** — any governance system failure results in denial, not allowance
4. **Tamper-evident audit** — every action is logged with cryptographic integrity
5. **Least privilege** — agents receive minimum capabilities for their task
6. **Composability** — governance primitives compose across frameworks and organizations

---

## 2. Core Abstractions

### 2.1 Agent Identity

An **Agent Identity** is a unique, verifiable identifier for an AI agent that persists across sessions, deployments, and interactions. It is the foundation for all governance decisions.

#### 2.1.1 Identity Document

```json
{
  "$schema": "https://grc-claw.dev/schemas/agent-identity/v1",
  "id": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "name": "customer-service-agent",
  "version": "2.1.0",
  "type": "autonomous|assisted|workflow",
  "framework": "langchain|autogen|crewai|custom",
  "owner": {
    "type": "organization|individual|agent",
    "id": "did:grc:org:acme-corp",
    "name": "Acme Corp"
  },
  "deployment": {
    "environment": "production|staging|development",
    "region": "us-east-1",
    "host": "agent-runner-01.acme.internal"
  },
  "credentials": {
    "public-key": "-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEA...\n-----END PUBLIC KEY-----",
    "key-type": "Ed25519",
    "certificate": "spiffe://acme.internal/agent/customer-service-agent"
  },
  "metadata": {
    "created": "2026-09-15T10:30:00Z",
    "last-rotated": "2026-09-15T10:30:00Z",
    "description": "Handles customer inquiries and ticket routing",
    "tags": ["customer-facing", "read-only", "tier-1"]
  },
  "status": "active|provisioning|suspended|retiring|decommissioned"
}
```

#### 2.1.2 Identity Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | DID string | Yes | Unique decentralized identifier |
| `name` | string | Yes | Human-readable name |
| `version` | semver | Yes | Agent version |
| `type` | enum | Yes | `autonomous`, `assisted`, or `workflow` |
| `framework` | string | Yes | Underlying agent framework |
| `owner` | object | Yes | Owning organization or individual |
| `deployment` | object | Yes | Deployment context |
| `credentials` | object | Yes | Cryptographic credentials |
| `metadata` | object | No | Additional metadata |
| `status` | enum | Yes | Lifecycle status |

#### 2.1.3 Identity Lifecycle

```
provisioning → active → suspended → retiring → decommissioned
                  ↑         │                            │
                  └─────────┘                            ▼
                                                    [terminal]
```

| State | Description | Allowed Operations |
|-------|-------------|-------------------|
| `provisioning` | Identity created, credentials not yet distributed | Key generation, metadata finalization |
| `active` | Fully operational | All operations |
| `suspended` | Temporarily halted | Read-only audit queries, identity verification |
| `retiring` | Being decommissioned | Drain in-flight tasks, no new operations |
| `decommissioned` | Permanently disabled | None (identity retained for audit) |

See Section 11 for detailed agent lifecycle management.

#### 2.1.4 Identity Registration Protocol

1. **Agent bootstrap** — agent generates Ed25519 keypair locally
2. **Registration request** — agent submits identity document to GRC_Claw registry
3. **Owner attestation** — owning organization signs the identity document
4. **Policy binding** — applicable policies are associated with the identity
5. **Credential issuance** — SPIFFE certificate and capability tokens issued
6. **Activation** — identity status set to `active`

#### 2.1.5 Key Rotation

- Keys MUST be rotated at least every 90 days
- Rotation creates a new credential entry while preserving the identity `id`
- Old credentials are retained for audit trail verification but marked as `superseded`
- Rotation is logged as an audit event

---

### 2.2 Delegation

A **Delegation** is a time-bounded, scope-limited transfer of authority from one agent (the *delegator*) to another (the *delegate*). Delegations form chains that MUST be tracked and enforced.

#### 2.2.1 Delegation Record

```json
{
  "$schema": "https://grc-claw.dev/schemas/delegation/v1",
  "id": "del:8c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
  "delegator": "did:grc:agent:7f3a9b2c-4d5e-6f7a8b9c-0d1e2f3a4b5c",
  "delegate": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "scope": {
    "capabilities": ["read:tickets", "write:responses"],
    "resources": ["ticket-system", "customer-db"],
    "constraints": {
      "max-actions-per-session": 100,
      "allowed-operations": ["read", "write"],
      "denied-operations": ["delete", "export"],
      "data-classification": ["public", "internal"]
    }
  },
  "validity": {
    "issued-at": "2026-10-01T09:00:00Z",
    "expires-at": "2026-10-01T17:00:00Z",
    "max-depth": 2
  },
  "parent-delegation": null,
  "status": "active",
  "signature": "base64-encoded-ed25519-signature"
}
```

#### 2.2.2 Delegation Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | UUID | Yes | Unique delegation identifier |
| `delegator` | DID | Yes | Delegating agent |
| `delegate` | DID | Yes | Receiving agent |
| `scope` | object | Yes | What is being delegated |
| `validity` | object | Yes | Time and depth bounds |
| `parent-delegation` | UUID/null | No | Parent delegation if chained |
| `status` | enum | Yes | `active`, `expired`, `revoked` |
| `signature` | string | Yes | Delegator's cryptographic signature |

#### 2.2.3 Delegation Chain Rules

1. **Depth limit** — maximum delegation depth is configurable (default: 3)
2. **Scope narrowing** — each delegation in a chain MUST be a subset of its parent's scope
3. **Time bounding** — child delegations expire no later than their parent
4. **Revocation propagation** — revoking a delegation automatically revokes all its children
5. **No self-delegation** — an agent cannot delegate to itself
6. **No cycles** — the delegation graph MUST be acyclic
7. **Attribution preservation** — the original delegator is always recorded in the chain

#### 2.2.4 Delegation Chain Validation

When an agent acts under a delegation, the governance engine validates:

```
1. Delegation exists and is active
2. Current time is within validity window
3. Delegation depth ≤ max-depth
4. Action is within scope (capabilities, resources, constraints)
5. Delegation chain is acyclic
6. No revocation in the chain
7. Delegator's signature is valid
```

#### 2.2.5 Revocation

```json
{
  "revocation": {
    "delegation-id": "del:8c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
    "revoked-by": "did:grc:agent:7f3a9b2c-4d5e-6f7a8b9c-0d1e2f3a4b5c",
    "reason": "task-complete",
    "revoked-at": "2026-10-01T15:30:00Z",
    "propagate-to-children": true
  }
}
```

Revocation is immediate and propagates synchronously through the delegation chain. All in-flight actions under the revoked delegation are terminated.

---

### 2.3 Capability

A **Capability** is a verifiable, scoped authorization that permits an agent to perform specific actions on specific resources. Capabilities are the unit of authorization in AGP.

#### 2.3.1 Capability Token

```json
{
  "$schema": "https://grc-claw.dev/schemas/capability/v1",
  "id": "cap:9d0e1f2a-3b4c-5d6e-7f8a-9b0c1d2e3f4a",
  "subject": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "issuer": "did:grc:agent:7f3a9b2c-4d5e-6f7a8b9c-0d1e2f3a4b5c",
  "capability": {
    "action": "read",
    "resource": "ticket-system",
    "resource-id": "ticket-12345",
    "conditions": {
      "classification": ["public", "internal"],
      "time-window": {
        "start": "2026-10-01T09:00:00Z",
        "end": "2026-10-01T17:00:00Z"
      },
      "rate-limit": "100/hour"
    }
  },
  "delegation": "del:8c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
  "issued-at": "2026-10-01T09:00:00Z",
  "expires-at": "2026-10-01T17:00:00Z",
  "status": "active",
  "signature": "base64-encoded-ed25519-signature"
}
```

#### 2.3.2 Capability Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | UUID | Yes | Unique capability identifier |
| `subject` | DID | Yes | Agent this capability is granted to |
| `issuer` | DID | Yes | Agent or system that issued this capability |
| `capability` | object | Yes | The actual authorization |
| `delegation` | UUID/null | No | Associated delegation (if delegated) |
| `issued-at` | timestamp | Yes | When the capability was issued |
| `expires-at` | timestamp | Yes | When the capability expires |
| `status` | enum | Yes | `active`, `expired`, `revoked` |
| `signature` | string | Yes | Issuer's cryptographic signature |

#### 2.3.3 Capability Hierarchy

```
Capability
├── Read
│   ├── read:metadata
│   ├── read:content
│   └── read:analytics
├── Write
│   ├── write:create
│   ├── write:update
│   └── write:append
├── Execute
│   ├── execute:tool
│   ├── execute:code
│   └── execute:workflow
├── Communicate
│   ├── communicate:send
│   ├── communicate:receive
│   └── communicate:broadcast
└── Admin
    ├── admin:configure
    ├── admin:delegate
    └── admin:revoke
```

#### 2.3.4 Capability States

```
issued → active → expired
           │
           ├── revoked
           └── suspended
```

#### 2.3.5 Capability Evaluation

When an agent attempts an action, the governance engine evaluates:

1. **Identity verification** — is the agent's identity valid and active?
2. **Capability matching** — does the agent hold a capability matching the action?
3. **Scope validation** — is the target resource within the capability's scope?
4. **Condition satisfaction** — are all conditions (time, rate limit, classification) met?
5. **Delegation validity** — if acting under delegation, is the delegation chain valid?
6. **Policy compliance** — does the action comply with all applicable policies?
7. **Trust threshold** — does the agent's trust level meet the action's requirement?

---

### 2.4 Trust

**Trust** is a dynamic, quantifiable measure of an agent's reliability based on its behavior history, compliance record, and operational context. Trust determines the level of autonomy and privilege an agent receives.

#### 2.4.1 Trust Score

```json
{
  "$schema": "https://grc-claw.dev/schemas/trust/v1",
  "subject": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "score": 0.87,
  "level": "high",
  "factors": {
    "behavioral": {
      "score": 0.90,
      "weight": 0.40,
      "signals": {
        "policy-violations-30d": 0,
        "anomalous-actions-30d": 1,
        "successful-completions-30d": 342,
        "failed-actions-30d": 3
      }
    },
    "compliance": {
      "score": 0.85,
      "weight": 0.30,
      "signals": {
        "audit-findings-30d": 0,
        "policy-drift-events": 0,
        "compliance-check-pass-rate": 0.98
      }
    },
    "operational": {
      "score": 0.82,
      "weight": 0.20,
      "signals": {
        "uptime-30d": 0.999,
        "error-rate-30d": 0.002,
        "latency-p99": 45
      }
    },
    "reputation": {
      "score": 0.88,
      "weight": 0.10,
      "signals": {
        "peer-endorsements": 12,
        "cross-org-interactions": 156,
        "incident-history": 0
      }
    }
  },
  "evaluated-at": "2026-10-01T12:00:00Z",
  "next-evaluation": "2026-10-01T18:00:00Z"
}
```

#### 2.4.2 Trust Levels

| Level | Score Range | Description | Privileges |
|-------|-------------|-------------|------------|
| `untrusted` | 0.00–0.20 | New or severely demoted agent | Read-only, no delegation, human approval required |
| `low` | 0.21–0.40 | Building trust, minor violations | Limited capabilities, no delegation |
| `medium` | 0.41–0.60 | Established agent, clean record | Standard capabilities, shallow delegation (depth 1) |
| `high` | 0.61–0.80 | Proven reliable agent | Extended capabilities, delegation up to depth 2 |
| `privileged` | 0.81–1.00 | Highly trusted, exemplary record | Full capabilities, delegation up to depth 3, admin operations |

#### 2.4.3 Trust Transitions

```
untrusted → low → medium → high → privileged
    ↑         │       │        │
    └─────────┴───────┴────────┘
         (demotion on violation)
```

**Promotion** requires:
- Minimum 30 days at current level
- No policy violations in the evaluation period
- Positive behavioral signals above threshold
- For `privileged`: minimum 90 days at `high` + peer endorsements

**Demotion** triggers:
- Any critical policy violation → immediate drop to `untrusted`
- 3+ minor violations in 30 days → drop one level
- Anomalous behavior detection → temporary suspension pending review
- Trust score below current level threshold for 2 consecutive evaluations

#### 2.4.4 Cross-Organizational Trust

When agents from different organizations interact:

1. **Trust anchoring** — each organization's root of trust is established via cross-signed certificates
2. **Trust translation** — trust levels are mapped between organizations using a common scale
3. **Trust verification** — the receiving organization can verify the delegating organization's trust attestation
4. **Trust isolation** — an agent's trust in one organization does not automatically transfer to another

```json
{
  "cross-org-trust": {
    "home-organization": "did:grc:org:acme-corp",
    "home-trust-level": "high",
    "guest-organization": "did:grc:org:partner-inc",
    "guest-trust-level": "medium",
    "trust-mapping": {
      "method": "bilateral-agreement",
      "mapping-rule": "conservative-minimum",
      "effective-trust": "medium"
    },
    "verified-at": "2026-10-01T12:00:00Z",
    "expires-at": "2026-10-08T12:00:00Z"
  }
}
```

---

## 3. Agent Identity Model

### 3.1 Identity Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Identity                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   DID         │  │  Credentials │  │  Metadata    │  │
│  │  (Identifier) │  │  (Keys/Certs)│  │  (Attributes)│  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                  │           │
│         └────────────┬────┘                  │           │
│                      ▼                       ▼           │
│              ┌──────────────┐        ┌──────────────┐   │
│              │  Verifiable  │        │   Policy     │   │
│              │  Credential  │        │   Binding    │   │
│              └──────────────┘        └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 DID Method

GRC_Claw uses the `did:grc` method for agent identities:

```
did:grc:agent:<uuid>
did:grc:org:<uuid>
did:grc:user:<uuid>
```

DID documents are resolvable via the GRC_Claw registry API:

```
GET /api/v1/identity/resolve/{did}
```

### 3.3 Identity Verification Flow

```
Agent                    GRC_Claw Registry              Policy Engine
  │                            │                            │
  │  1. Present identity       │                            │
  │ ─────────────────────────► │                            │
  │                            │                            │
  │  2. Verify DID document    │                            │
  │ ◄───────────────────────── │                            │
  │                            │                            │
  │  3. Challenge-response     │                            │
  │ ─────────────────────────► │                            │
  │                            │                            │
  │  4. Signed response        │                            │
  │ ◄───────────────────────── │                            │
  │                            │                            │
  │  5. Identity verified      │                            │
  │ ─────────────────────────► │                            │
  │                            │                            │
  │                            │  6. Check applicable       │
  │                            │      policies              │
  │                            │ ─────────────────────────► │
  │                            │                            │
  │                            │  7. Policy set              │
  │                            │ ◄───────────────────────── │
  │                            │                            │
  │  8. Session token issued   │                            │
  │ ◄───────────────────────── │                            │
```

### 3.4 Multi-Framework Identity

Agents built on different frameworks are unified under AGP through framework adapters:

| Framework | Adapter | Identity Mapping |
|-----------|---------|-----------------|
| LangChain | `grc-adapter-langchain` | Chain → Agent, Tools → Capabilities |
| AutoGen | `grc-adapter-autogen` | ConversableAgent → Agent, Functions → Capabilities |
| CrewAI | `grc-adapter-crewai` | Crew → Agent Group, Tasks → Delegations |
| OpenAI Agents | `grc-adapter-openai` | Assistant → Agent, Functions → Capabilities |
| Custom | `grc-adapter-webhook` | HTTP webhook → Identity events |

---

## 4. Delegation Chain Tracking

### 4.1 Delegation Chain Structure

```
Root Agent (A)
  │
  ├── delegates to B (scope: read:tickets, write:responses)
  │     │
  │     ├── delegates to C (scope: read:tickets) [depth 2]
  │     │     │
  │     │     └── delegates to D (scope: read:tickets) [depth 3]
  │     │
  │     └── delegates to E (scope: write:responses) [depth 2]
  │
  └── delegates to F (scope: read:analytics) [depth 1]
```

### 4.2 Delegation Chain Record

Each delegation chain is stored as a directed acyclic graph (DAG):

```json
{
  "$schema": "https://grc-claw.dev/schemas/delegation-chain/v1",
  "chain-id": "chain:0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  "root-delegation": "del:8c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
  "nodes": [
    {
      "agent": "did:grc:agent:7f3a9b2c-4d5e-6f7a8b9c-0d1e2f3a4b5c",
      "delegation": null,
      "depth": 0,
      "role": "root"
    },
    {
      "agent": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
      "delegation": "del:8c4d5e6f-7a8b-9c0d-1e2f3a4b5c6d7e8f",
      "depth": 1,
      "role": "delegate"
    },
    {
      "agent": "did:grc:agent:2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
      "delegation": "del:3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
      "depth": 2,
      "role": "sub-delegate"
    }
  ],
  "edges": [
    {
      "from": "did:grc:agent:7f3a9b2c-4d5e-6f7a8b9c-0d1e2f3a4b5c",
      "to": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
      "delegation": "del:8c4d5e6f-7a8b-9c0d-1e2f3a4b5c6d7e8f"
    },
    {
      "from": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
      "to": "did:grc:agent:2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
      "delegation": "del:3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f"
    }
  ],
  "max-depth": 2,
  "status": "active",
  "created-at": "2026-10-01T09:00:00Z"
}
```

### 4.3 Chain Enforcement Points

Delegation chains are enforced at three points:

1. **Delegation creation** — validate scope narrowing, depth limit, acyclicity
2. **Action execution** — validate the acting agent's delegation chain permits the action
3. **Audit logging** — record the full delegation chain for every action

### 4.4 Chain Visualization

```
┌─────────────────────────────────────────────────────────────┐
│ Delegation Chain: ticket-processing-workflow                 │
│                                                              │
│  [A: orchestrator-agent]  depth=0  trust=privileged         │
│       │                                                      │
│       ├──► [B: ticket-reader]  depth=1  trust=high          │
│       │      scope: read:tickets                             │
│       │      │                                               │
│       │      └──► [C: ticket-summarizer]  depth=2  trust=med│
│       │             scope: read:tickets                     │
│       │                                                      │
│       └──► [D: response-writer]  depth=1  trust=high        │
│              scope: write:responses                          │
│                                                              │
│  Status: active  |  Max depth: 2  |  Created: 2026-10-01    │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Multi-Agent Trust Framework

### 5.1 Trust Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Multi-Agent Trust Framework                  │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Behavioral  │  │  Compliance │  │ Operational │         │
│  │  Monitor     │  │  Tracker    │  │  Health     │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                   │
│                  ┌─────────────┐                            │
│                  │   Trust     │                            │
│                  │   Engine    │                            │
│                  └──────┬──────┘                            │
│                         │                                    │
│         ┌───────────────┼───────────────┐                   │
│         ▼               ▼               ▼                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Trust     │ │   Trust     │ │   Trust     │          │
│  │   Score     │ │   Level     │ │   Policy    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                              │
│  ┌─────────────────────────────────────────────┐            │
│  │         Cross-Org Trust Anchor              │            │
│  │  (Bilateral agreements, certificate          │            │
│  │   chains, trust translation)                │            │
│  └─────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Trust Evaluation Algorithm

The trust score is computed as a weighted composite:

```
trust_score = (behavioral × 0.40) + (compliance × 0.30) + (operational × 0.20) + (reputation × 0.10)
```

Each factor is normalized to [0, 1] and computed from rolling 30-day windows.

#### 5.2.1 Behavioral Score

```
behavioral = 1.0 - (violations × 0.3 + anomalies × 0.2 + failures × 0.1) / total_actions
```

Signals:
- Policy violations (weighted by severity)
- Anomalous actions (detected by baseline deviation)
- Failed action rate
- Successful completion rate

#### 5.2.2 Compliance Score

```
compliance = (passed_checks / total_checks) × (1 - audit_findings × 0.1)
```

Signals:
- Policy compliance check pass rate
- Audit findings count
- Policy drift events
- Evidence submission timeliness

#### 5.2.3 Operational Score

```
operational = uptime × (1 - error_rate) × (1 - latency_penalty)
```

Signals:
- Uptime percentage
- Error rate
- Latency p99 vs. SLO
- Resource utilization

#### 5.2.4 Reputation Score

```
reputation = (endorsements × 0.3 + successful_interactions × 0.5 + incident_free_days × 0.2) / normalization
```

Signals:
- Peer endorsements from other agents
- Successful cross-organizational interactions
- Days since last incident
- Community contributions (for open-source agents)

### 5.3 Trust Negotiation Protocol

When two agents from different trust domains interact:

```
Agent A (Org 1)                                    Agent B (Org 2)
    │                                                    │
    │  1. Hello, I am did:grc:agent:A, trust=high       │
    │ ─────────────────────────────────────────────────► │
    │                                                    │
    │  2. Verify A's trust attestation                   │
    │     (check Org 1's trust anchor)                  │
    │                                                    │
    │  3. Hello, I am did:grc:agent:B, trust=medium     │
    │ ◄───────────────────────────────────────────────── │
    │                                                    │
    │  4. Verify B's trust attestation                   │
    │     (check Org 2's trust anchor)                  │
    │                                                    │
    │  5. Establish session with effective trust =       │
    │     min(A.trust, B.trust) = medium                │
    │                                                    │
    │  6. All actions in this session are gated          │
    │     by medium-trust policies                       │
```

### 5.4 Trust Demotion Triggers

| Trigger | Severity | Action |
|---------|----------|--------|
| Critical policy violation | Critical | Immediate demotion to `untrusted` + suspension |
| 3+ minor violations in 30 days | Major | Demote one level |
| Anomalous behavior detected | Major | Temporary suspension pending review |
| Trust score below threshold for 2 evaluations | Minor | Demote one level |
| Cross-org trust anchor revoked | Critical | Immediate demotion to `untrusted` |
| Audit finding of severity ≥ high | Major | Demote one level + mandatory review |

### 5.5 Trust Promotion Requirements

| From → To | Min Days | Violations | Additional Requirements |
|-----------|----------|------------|------------------------|
| untrusted → low | 7 | 0 | Complete onboarding training |
| low → medium | 30 | 0 | Pass capability assessment |
| medium → high | 60 | 0 | Peer endorsement from 2 agents at `high`+ |
| high → privileged | 90 | 0 | 5 peer endorsements + cross-org validation |

---

## 6. Agent-to-Agent Authorization Protocol

### 6.1 Protocol Overview

The Agent-to-Agent Authorization Protocol (A2A-AP) governs how one agent requests and receives authorization to act on behalf of another agent or to access another agent's resources.

```
┌──────────┐                                    ┌──────────┐
│  Agent A │                                    │  Agent B │
│ (Requester)│                                  │ (Resource │
│           │                                    │  Owner)  │
└─────┬─────┘                                    └────┬─────┘
      │                                               │
      │  1. Authorization Request                     │
      │ ─────────────────────────────────────────────►│
      │     (capability, scope, justification)        │
      │                                               │
      │  2. Policy Evaluation                         │
      │     (B's policies + trust + context)          │
      │                                               │
      │  3. Authorization Decision                    │
      │ ◄─────────────────────────────────────────────│
      │     (grant | deny | require-approval)         │
      │                                               │
      │  4. Capability Token (if granted)             │
      │ ◄─────────────────────────────────────────────│
      │     (signed, scoped, time-bounded)             │
      │                                               │
      │  5. Action Execution                          │
      │     (under granted capability)                │
      │                                               │
      │  6. Audit Event                               │
      │ ─────────────────────────────────────────────►│
      │     (action, outcome, delegation chain)        │
```

### 6.2 Authorization Request

```json
{
  "$schema": "https://grc-claw.dev/schemas/authz-request/v1",
  "request-id": "req:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "requester": {
    "agent": "did:grc:agent:7f3a9b2c-4d5e-6f7a8b9c-0d1e2f3a4b5c",
    "trust-level": "high",
    "delegation-chain": "chain:0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"
  },
  "resource-owner": {
    "agent": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
    "trust-level": "medium"
  },
  "request": {
    "capability": "read",
    "resource": "customer-database",
    "resource-id": "customer-789",
    "justification": "Need to verify customer identity before processing refund",
    "constraints": {
      "max-records": 1,
      "fields": ["name", "email", "account-status"],
      "time-limit": "5m"
    }
  },
  "context": {
    "session-id": "sess:2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
    "workflow-id": "wf:3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
    "parent-action": "action:4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a"
  },
  "timestamp": "2026-10-01T10:15:00Z",
  "signature": "base64-encoded-ed25519-signature"
}
```

### 6.3 Authorization Decision

```json
{
  "$schema": "https://grc-claw.dev/schemas/authz-decision/v1",
  "request-id": "req:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "decision": "grant",
  "decision-reason": "Requester trust level sufficient; capability within policy scope",
  "granted-capability": {
    "id": "cap:9d0e1f2a-3b4c-5d6e-7f8a-9b0c1d2e3f4a",
    "action": "read",
    "resource": "customer-database",
    "resource-id": "customer-789",
    "conditions": {
      "fields": ["name", "email", "account-status"],
      "max-records": 1,
      "expires-at": "2026-10-01T10:20:00Z"
    }
  },
  "policy-references": ["pol:customer-data-access", "pol:refund-workflow"],
  "evaluated-at": "2026-10-01T10:15:01Z",
  "evaluator": "did:grc:system:policy-engine",
  "signature": "base64-encoded-ed25519-signature"
}
```

### 6.4 Decision Types

| Decision | Description | Next Step |
|----------|-------------|-----------|
| `grant` | Authorization approved | Issue capability token |
| `deny` | Authorization refused | Log denial, notify requester |
| `require-approval` | Human approval needed | Route to approval workflow |
| `transform` | Approved with modifications | Issue modified capability token |
| `escalate` | Beyond policy scope | Route to security team |

### 6.5 Authorization Evaluation Pipeline

```
Request ──► Identity Check ──► Trust Check ──► Policy Check ──► Scope Check ──► Decision
              │                  │                │               │
              ▼                  ▼                ▼               ▼
           DID valid?      Trust level      Policy allows    Scope within
           Status active?  sufficient?      this action?     delegation?
           Not revoked?    No sanctions?    No conflicts?    Resource allowed?
```

### 6.6 Consent and Approval Flow

For sensitive actions requiring human approval:

```
Agent A                    GRC_Claw                    Human Approver
  │                          │                              │
  │  1. AuthZ request        │                              │
  │ ───────────────────────► │                              │
  │                          │                              │
  │                          │  2. Route to approver        │
  │                          │ ───────────────────────────► │
  │                          │                              │
  │                          │  3. Approval decision        │
  │                          │ ◄─────────────────────────── │
  │                          │                              │
  │  4. Capability token     │                              │
  │ ◄─────────────────────── │                              │
  │     (if approved)        │                              │
```

### 6.7 Cross-Organizational Authorization

When agents from different organizations request authorization:

1. **Trust anchor verification** — verify the requester organization's trust anchor
2. **Policy intersection** — compute the intersection of both organizations' policies
3. **Conservative minimum** — apply the most restrictive policy from either organization
4. **Data residency check** — verify data does not cross jurisdictional boundaries
5. **Audit trail sharing** — both organizations receive audit records of the interaction

---

## 7. Agent Audit Trail Format

### 7.1 Audit Trail Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Agent Audit Trail                          │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Action   │  │  Policy  │  │  Trust   │  │  Identity │   │
│  │  Events   │  │  Events  │  │  Events  │  │  Events   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │         │
│       └──────────────┼──────────────┘              │         │
│                      ▼                             │         │
│              ┌──────────────┐                      │         │
│              │   Merkle     │◄─────────────────────┘         │
│              │   Chain      │                                │
│              └──────┬───────┘                                │
│                     │                                        │
│                     ▼                                        │
│              ┌──────────────┐                                │
│              │  Tamper-     │                                │
│              │  Evidence    │                                │
│              └──────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Audit Event Format

Every audit event conforms to the CloudEvents v1.0 specification with GRC_Claw extensions:

```json
{
  "$schema": "https://grc-claw.dev/schemas/audit-event/v1",
  "specversion": "1.0",
  "type": "dev.grc-claw.agent.action.executed",
  "source": "did:grc:agent:7f3a9b2c-4d5e-6f7a8b9c-0d1e2f3a4b5c",
  "id": "evt:5e6f7a8b-9c0d-1e2f-3a4b-5c6d7e8f9a0b",
  "time": "2026-10-01T10:15:05Z",
  "datacontenttype": "application/json",
  "data": {
    "event-type": "action-executed",
    "agent": {
      "id": "did:grc:agent:7f3a9b2c-4d5e-6f7a8b9c-0d1e2f3a4b5c",
      "name": "customer-service-agent",
      "trust-level": "high"
    },
    "action": {
      "type": "tool-call",
      "tool": "read-ticket",
      "arguments": {
        "ticket-id": "TKT-12345"
      },
      "outcome": "success",
      "result-summary": "Retrieved ticket details"
    },
    "authorization": {
      "capability-id": "cap:9d0e1f2a-3b4c-5d6e-7f8a-9b0c1d2e3f4a",
      "delegation-chain": "chain:0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
      "policy-references": ["pol:ticket-access"],
      "decision": "grant"
    },
    "context": {
      "session-id": "sess:2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
      "workflow-id": "wf:3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
      "parent-action": "action:4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a",
      "trace-id": "trace:6f7a8b9c-0d1e-2f3a-4b5c-6d7e8f9a0b1c"
    },
    "integrity": {
      "previous-hash": "sha256:abc123...",
      "event-hash": "sha256:def456...",
      "merkle-root": "sha256:ghi789..."
    }
  }
}
```

### 7.3 Event Types

| Category | Event Type | Description |
|----------|------------|-------------|
| **Action** | `action-executed` | Agent performed an action |
| | `action-blocked` | Action denied by policy |
| | `action-transformed` | Action modified by policy |
| | `action-escalated` | Action routed to human |
| **Policy** | `policy-evaluated` | Policy decision recorded |
| | `policy-violated` | Policy violation detected |
| | `policy-drift` | Agent behavior drifted from policy |
| **Trust** | `trust-scored` | Trust score updated |
| | `trust-promoted` | Agent promoted to higher trust level |
| | `trust-demoted` | Agent demoted to lower trust level |
| **Identity** | `identity-registered` | New agent identity created |
| | `identity-rotated` | Agent keys rotated |
| | `identity-revoked` | Agent identity revoked |
| **Delegation** | `delegation-created` | New delegation issued |
| | `delegation-revoked` | Delegation revoked |
| | `delegation-expired` | Delegation expired |
| **Authorization** | `authz-requested` | Authorization requested |
| | `authz-granted` | Authorization granted |
| | `authz-denied` | Authorization denied |
| | `authz-approval-required` | Human approval needed |

### 7.4 Integrity Guarantees

#### 7.4.1 Merkle Chain

Each audit event includes:
- `previous-hash` — SHA-256 of the previous event
- `event-hash` — SHA-256 of the current event's canonical form
- `merkle-root` — root of the Merkle tree for the current batch

Any modification to a past event invalidates all subsequent hashes, making tampering detectable.

#### 7.4.2 Verification

```bash
# Verify full chain integrity
grc-audit verify --chain-id chain:0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d

# Verify single event
grc-audit verify --event-id evt:5e6f7a8b-9c0d-1e2f-3a4b-5c6d7e8f9a0b

# Generate inclusion proof
grc-audit proof --event-id evt:5e6f7a8b-9c0d-1e2f-3a4b-5c6d7e8f9a0b
```

#### 7.4.3 Export Format

Audit trails are exported as CloudEvents v1.0 JSON envelopes, one event per line (JSONL):

```jsonl
{"specversion":"1.0","type":"dev.grc-claw.agent.action.executed","source":"did:grc:agent:...","id":"evt:...","time":"2026-10-01T10:15:05Z","datacontenttype":"application/json","data":{...}}
{"specversion":"1.0","type":"dev.grc-claw.policy.evaluated","source":"did:grc:agent:...","id":"evt:...","time":"2026-10-01T10:15:06Z","datacontenttype":"application/json","data":{...}}
```

### 7.5 Retention and Compliance

| Event Category | Retention | Compliance Driver |
|---------------|-----------|------------------|
| Action events | 7 years | SOC 2 CC7.2, ISO 27001 A.12.4 |
| Policy events | 7 years | SOC 2 CC7.3, ISO 27001 A.12.5 |
| Trust events | 3 years | Internal governance |
| Identity events | Life of identity + 7 years | SOC 2 CC6.1, ISO 27001 A.9 |
| Delegation events | Life of delegation + 3 years | Internal governance |
| Authorization events | 7 years | SOC 2 CC6.2, ISO 27001 A.9.4 |

### 7.6 Audit Trail Query API

```
GET /api/v1/audit/events?agent={did}&from={timestamp}&to={timestamp}
GET /api/v1/audit/events?type={event-type}&outcome={outcome}
GET /api/v1/audit/chain/{chain-id}/verify
GET /api/v1/audit/chain/{chain-id}/proof/{event-id}
GET /api/v1/audit/export?format={jsonl|cloudevents|csv}&from={timestamp}&to={timestamp}
```

---

## 8. Policy Integration

### 8.1 Policy-to-Enforcement Bridge

AGP policies are compiled into enforceable rules at the runtime boundary:

```
Policy YAML ──► Compiler ──► OPA/Rego ──► Enforcement Point
                  │
                  ▼
            Capability Tokens
            Trust Thresholds
            Delegation Rules
```

### 8.2 Policy Binding

Each agent identity is bound to a set of policies:

```json
{
  "policy-binding": {
    "agent": "did:grc:agent:7f3a9b2c-4d5e-6f7a8b9c-0d1e2f3a4b5c",
    "policies": [
      {
        "id": "pol:customer-data-access",
        "version": "2.1.0",
        "priority": 100,
        "effect": "allow"
      },
      {
        "id": "pol:pii-protection",
        "version": "1.0.0",
        "priority": 1000,
        "effect": "deny"
      }
    ],
    "default-effect": "deny",
    "conflict-resolution": "deny-overrides"
  }
}
```

### 8.3 Multi-Agent Coordination Policies

Policies can span multiple agents:

```yaml
apiVersion: grc-claw.dev/v1
kind: MultiAgentPolicy
name: data-isolation-policy
description: "Agent A cannot share customer data with Agent B"
spec:
  subjects:
    - did:grc:agent:7f3a9b2c-4d5e-6f7a8b9c-0d1e2f3a4b5c
    - did:grc:agent:1a2b3c4d-5e6f-7a8b9c-0d1e2f3a4b5c6d
  rule:
    action: "share-data"
    source: "did:grc:agent:7f3a9b2c-4d5e-6f7a8b9c-0d1e2f3a4b5c"
    target: "did:grc:agent:1a2b3c4d-5e6f-7a8b9c-0d1e2f3a4b5c6d"
    data-classification: "customer-pii"
    effect: deny
```

---

## 9. Reference Implementation Architecture

### 9.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     GRC_Claw Agent Governance                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Identity   │  │   Policy     │  │   Trust      │          │
│  │   Registry   │  │   Engine     │  │   Engine     │          │
│  │              │  │  (OPA/Rego)  │  │              │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └────────────────┬┴─────────────────┘                   │
│                          ▼                                      │
│                  ┌──────────────┐                               │
│                  │  Governance  │                               │
│                  │  Orchestrator│                               │
│                  └──────┬───────┘                               │
│                         │                                       │
│         ┌───────────────┼───────────────┐                      │
│         ▼               ▼               ▼                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │
│  │  Delegation  │ │  Capability  │ │   Audit      │          │
│  │  Tracker     │ │  Token Svc   │ │   Logger     │          │
│  │              │ │              │ │  (Merkle)    │          │
│  └──────────────┘ └──────────────┘ └──────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────┐              │
│  │              Framework Adapters               │              │
│  │  LangChain │ AutoGen │ CrewAI │ OpenAI │ ... │              │
│  └──────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Enforcement Points

AGP enforcement is injected at the agent framework boundary via adapters:

| Framework | Enforcement Point | Mechanism |
|-----------|-------------------|-----------|
| LangChain | `BaseTool` wrapper | Python decorator / middleware |
| AutoGen | `ConversableAgent.send()` | Method interception |
| CrewAI | `Task.execute()` | Task wrapper |
| OpenAI | `function_call` hook | API middleware |
| Custom | HTTP webhook | Sidecar proxy |

### 9.3 SDK Integration

```python
# Python SDK — @grc_govern decorator
from grc_claw import grc_govern, AgentIdentity, Capability

@grc_govern(
    identity=AgentIdentity.from_env(),
    capabilities=[Capability.READ_TICKETS,Capability.WRITE_RESPONSES],
    require_trust="medium"
)
def process_ticket(ticket_id: str, action: str) -> dict:
    """Process a customer ticket."""
    # Business logic here
    return {"status": "processed", "ticket_id": ticket_id}
```

```typescript
// TypeScript SDK — middleware
import { grc_govern } from '@grc-claw/sdk';

app.use(grc_govern({
  identity: AgentIdentity.fromEnv(),
  capabilities: ['read:tickets', 'write:responses'],
  trustThreshold: 'medium',
  audit: true
}));
```

---

## 10. Compliance Mapping

### 10.1 OWASP Agentic AI Top 10

| ASI | Risk | AGP Control |
|-----|------|-------------|
| ASI01 | Agent Goal Hijack | Policy engine input validation, prompt injection detection |
| ASI02 | Tool Misuse | Capability tokens, tool catalog enforcement |
| ASI03 | Identity & Privilege Abuse | Agent identity model, trust levels, capability hierarchy |
| ASI04 | Agentic Supply Chain | Framework adapter verification, tool pinning |
| ASI05 | Unexpected Code Execution | Sandbox enforcement, command denylist |
| ASI06 | Memory & Context Poisoning | Audit trail integrity, memory provenance tracking |
| ASI07 | Insecure Inter-Agent Comms | mTLS, DID verification, encrypted transport |
| ASI08 | Cascading Failures | Circuit breakers, rate limits, session budgets |
| ASI09 | Human-Agent Trust Exploitation | Approval workflows, reversibility checks |
| ASI10 | Rogue Agents | Trust demotion, quarantine, kill switch |

See Section 11.10 for detailed agent lifecycle compliance mappings.

### 10.2 NIST AI RMF 1.0

| Function | AGP Coverage |
|----------|-------------|
| GOVERN | Agent identity registry, policy binding, trust framework, agent lifecycle provisioning (Section 11.2) |
| MAP | Capability declarations, delegation scope, agent inventory, behavior profiling (Section 11.3.3) |
| MEASURE | Trust scoring, behavioral monitoring, audit trail, performance scoring (Section 11.3.2), compliance monitoring (Section 11.3.5) |
| MANAGE | Policy enforcement, incident response, trust demotion, agent suspension/retirement (Sections 11.4-11.6) |

### 10.3 ISO/IEC 42001

| Clause | AGP Coverage |
|--------|-------------|
| 4. Context | Agent inventory, deployment context, provisioning (Section 11.2) |
| 5. Leadership | Policy ownership, trust level assignment, risk tier classification (Section 11.3.4) |
| 6. Planning | Risk assessment via trust scoring, capability scoping, agent risk assessment (Section 11.3.4) |
| 7. Support | Agent onboarding, training requirements for trust promotion |
| 8. Operation | Runtime enforcement, delegation management, performance scoring (Section 11.3.2) |
| 9. Performance Evaluation | Audit trail, trust evaluation, compliance monitoring (Section 11.3.5), lifecycle metrics (Section 11.9) |
| 10. Improvement | Incident-driven policy updates, trust demotion triggers, lessons learned (Section 11.5.1 R-10) |

---

## 11. Agent Lifecycle Management

### 11.1 Lifecycle Overview

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ PROVISIONING │───►│   ACTIVE     │───►│  SUSPENDED   │───►│  RETIRING    │───►│ DECOMMISSION │
│              │    │              │    │              │    │              │    │              │
│ Bootstrap    │    │ Execute      │    │ Halt         │    │ Drain        │    │ Archive      │
│ Register     │    │ Monitor      │    │ Preserve     │    │ Revoke       │    │ Delete       │
│ Attest       │    │ Score        │    │ Audit        │    │ Notify       │    │ Certify      │
│ Activate     │    │ Profile      │    │ Review       │    │ Transfer     │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
      │                  │                  │                  │                  │
      ▼                  ▼                  ▼                  ▼                  ▼
   Gate 1            Gate 2             Gate 3             Gate 4             Gate 5
  (Identity         (Performance       (Risk             (Retirement        (Decommission
   Issued)           Baseline)          Threshold)         Decision)          Complete)
```

### 11.2 Stage 1: Provisioning

**Objective:** Create, register, and activate a new agent identity with full governance controls before the agent performs any actions.

#### 11.2.1 Provisioning Controls

| Control | Requirement | Verification |
|---------|-------------|--------------|
| **P-01: Agent Registration** | All agents must be registered in the Identity Registry before activation | Automated — unregistered agents cannot receive credentials |
| **P-02: Owner Attestation** | Owning organization must cryptographically sign the identity document | Registry validation — no unsigned identities accepted |
| **P-03: Risk Classification** | Agent must be classified into a risk tier (1-4) at registration | Risk assessment workflow — tier determines governance requirements |
| **P-04: Capability Declaration** | Agent must declare intended capabilities and resources at registration | Capability manifest — validated against policy |
| **P-05: Policy Binding** | Applicable policies must be bound to the identity before activation | Policy engine — no unbound policies allowed |
| **P-06: Framework Adapter** | Agent must use a verified framework adapter for its framework | Adapter registry — unverified adapters blocked |
| **P-07: Sandbox Configuration** | Agent must be assigned a sandbox environment with resource limits | Infrastructure policy — sandbox validated |
| **P-08: Kill Switch** | Agent must have a kill switch configured before activation | Kill switch test — result recorded |
| **P-09: Baseline Establishment** | Performance and behavior baselines must be established | Baseline metrics recorded — comparison thresholds set |
| **P-10: Audit Stream** | Agent must have an audit stream configured and verified | Audit log — test event recorded and verified |

#### 11.2.2 Provisioning Workflow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ BOOTSTRAP│───►│ REGISTER │───►│  ATTEST  │───►│  BIND    │───►│ ACTIVATE │
│          │    │          │    │          │    │          │    │          │
│ Generate │    │ Submit   │    │ Owner    │    │ Policy   │    │ Issue    │
│ Keypair  │    │ Identity │    │ Signs    │    │ Engine   │    │ Creds    │
│ Create   │    │ Document │    │ Document │    │ Binds    │    │ Set      │
│ DID      │    │          │    │          │    │ Policies │    │ Active   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

#### 11.2.3 Provisioning Automation

Provisioning is fully automated via the Agent Provisioning API:

```python
class AgentProvisioningService:
    """Automated agent provisioning with governance enforcement."""
    
    def provision_agent(self, request: ProvisioningRequest) -> AgentIdentity:
        """Provision a new agent with full governance controls."""
        # 1. Validate request completeness
        self._validate_request(request)
        
        # 2. Classify risk tier
        risk_tier = self.risk_engine.classify_new_agent(request)
        
        # 3. Create identity document
        identity = self.registry.create_identity(request, risk_tier)
        
        # 4. Owner attestation
        self.registry.attest_identity(identity.id, request.owner)
        
        # 5. Bind policies
        policies = self.policy_engine.resolve_policies(identity, risk_tier)
        self.policy_engine.bind_policies(identity.id, policies)
        
        # 6. Issue credentials
        credentials = self.credential_service.issue(identity, risk_tier)
        
        # 7. Configure sandbox
        self.sandbox_service.configure(identity, risk_tier)
        
        # 8. Test kill switch
        self.kill_switch_service.test(identity)
        
        # 9. Establish baselines
        self.baseline_service.establish(identity)
        
        # 10. Activate
        self.registry.activate(identity.id)
        
        # 11. Audit
        self.audit.log_provisioning(identity, risk_tier)
        
        return identity
```

#### 11.2.4 Provisioning Request Schema

```json
{
  "$schema": "https://grc-claw.dev/schemas/provisioning-request/v1",
  "request-id": "prov:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "agent-name": "customer-service-agent",
  "agent-type": "autonomous",
  "framework": "langchain",
  "owner": {
    "type": "organization",
    "id": "did:grc:org:acme-corp",
    "name": "Acme Corp"
  },
  "deployment": {
    "environment": "production",
    "region": "us-east-1",
    "host": "agent-runner-01.acme.internal"
  },
  "capability-manifest": {
    "intended-capabilities": ["read:tickets", "write:responses"],
    "intended-resources": ["ticket-system", "customer-db"],
    "max-actions-per-session": 100,
    "data-classification": ["public", "internal"]
  },
  "risk-assessment": {
    "intended-use": "Handle customer inquiries and ticket routing",
    "data-sensitivity": "internal",
    "decision-impact": "low",
    "autonomy-level": "medium"
  },
  "sandbox": {
    "cpu-limit": "2 cores",
    "memory-limit": "4GB",
    "network-policy": "restricted",
    "filesystem": "read-only"
  },
  "submitted-at": "2026-10-01T09:00:00Z",
  "signature": "base64-encoded-ed25519-signature"
}
```

**Exit Criteria (Gate 1 — Identity Issued):**
- Identity document is complete and signed by owner
- Risk tier is assigned
- Policies are bound
- Credentials are issued
- Sandbox is configured
- Kill switch is tested
- Baselines are established
- Agent status is `active`

### 11.3 Stage 2: Active Operations

**Objective:** Continuously monitor, score, and profile the agent's performance, behavior, and compliance during active operations.

#### 11.3.1 Active Operations Controls

| Control | Requirement | Verification |
|---------|-------------|--------------|
| **A-01: Performance Scoring** | Agent performance must be continuously scored against baselines | Automated scoring — alerts on threshold breach |
| **A-02: Behavior Profiling** | Agent behavior must be profiled and compared to baseline | Behavioral analytics — anomaly alerts |
| **A-03: Risk Monitoring** | Agent risk signals must be continuously monitored | Risk engine — real-time risk assessment |
| **A-04: Compliance Checking** | Agent must be continuously checked for policy compliance | Policy engine — real-time compliance evaluation |
| **A-05: Trust Evaluation** | Agent trust score must be continuously evaluated | Trust engine — rolling 30-day window |
| **A-06: Delegation Monitoring** | All delegations must be monitored for scope compliance | Delegation tracker — violation alerts |
| **A-07: Capability Usage** | Agent capability usage must be monitored for anomalies | Usage analytics — anomaly detection |
| **A-08: Incident Response** | Agent-related incidents must be detected and remediated | Incident tracking — root cause analysis |
| **A-09: Periodic Review** | Agent must undergo periodic review based on risk tier | Review schedule — automated triggers |
| **A-10: Re-scoring Triggers** | Conditions requiring re-scoring must be defined and monitored | Re-scoring policy — automated triggers |

#### 11.3.2 Agent Performance Scoring

Performance scoring evaluates an agent's operational effectiveness against established baselines and SLAs.

**Performance Score Formula:**

```
performance_score = (task_success × 0.30) + (efficiency × 0.25) + (quality × 0.25) + (reliability × 0.20)
```

Each factor is normalized to [0, 1] and computed from rolling 30-day windows.

| Factor | Weight | Signals | Data Sources |
|--------|--------|---------|--------------|
| **Task Success** | 0.30 | Completion rate, error rate, retry rate | Action audit trail |
| **Efficiency** | 0.25 | Actions per session, latency p50/p99, resource utilization | Runtime metrics |
| **Quality** | 0.25 | Output quality scores, user satisfaction, rework rate | Quality assessment pipeline |
| **Reliability** | 0.20 | Uptime, error rate, recovery time | Infrastructure monitoring |

**Performance Score Record:**

```json
{
  "$schema": "https://grc-claw.dev/schemas/performance-score/v1",
  "agent": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "score": 0.85,
  "grade": "B+",
  "factors": {
    "task-success": {
      "score": 0.90,
      "weight": 0.30,
      "signals": {
        "tasks-completed-30d": 1250,
        "tasks-failed-30d": 12,
        "completion-rate": 0.990,
        "retry-rate": 0.008
      }
    },
    "efficiency": {
      "score": 0.82,
      "weight": 0.25,
      "signals": {
        "avg-actions-per-session": 45,
        "latency-p50": 120,
        "latency-p99": 450,
        "cpu-utilization": 0.35,
        "memory-utilization": 0.42
      }
    },
    "quality": {
      "score": 0.88,
      "weight": 0.25,
      "signals": {
        "output-quality-score": 0.88,
        "user-satisfaction": 4.2,
        "rework-rate": 0.03
      }
    },
    "reliability": {
      "score": 0.78,
      "weight": 0.20,
      "signals": {
        "uptime-30d": 0.995,
        "error-rate-30d": 0.005,
        "mean-recovery-time": 45
      }
    }
  },
  "baseline-comparison": {
    "baseline-score": 0.80,
    "delta": 0.05,
    "trend": "improving"
  },
  "evaluated-at": "2026-10-01T12:00:00Z",
  "next-evaluation": "2026-10-08T12:00:00Z"
}
```

**Performance Grades:**

| Grade | Score Range | Description | Action |
|-------|-------------|-------------|--------|
| A+ | 0.95–1.00 | Exemplary performance | Consider for privilege expansion |
| A | 0.90–0.94 | Excellent performance | Maintain current configuration |
| B+ | 0.85–0.89 | Good performance | Monitor for improvement opportunities |
| B | 0.80–0.84 | Acceptable performance | Review for optimization |
| C | 0.70–0.79 | Below expectations | Mandatory review and improvement plan |
| D | 0.60–0.69 | Poor performance | Restricted operations, mandatory retraining |
| F | 0.00–0.59 | Unacceptable | Suspend operations, emergency review |

**Performance Review Frequency by Risk Tier:**

| Risk Tier | Performance Review | Behavior Profile | Risk Re-assessment | Compliance Review | Full Re-evaluation |
|-----------|-------------------|------------------|-------------------|-------------------|-------------------|
| Tier 1 (Minimal) | Quarterly | Monthly | Semi-annual | Annual | Annual |
| Tier 2 (Limited) | Monthly | Weekly | Quarterly | Semi-annual | Semi-annual |
| Tier 3 (Substantial) | Weekly | Daily | Monthly | Quarterly | Quarterly |
| Tier 4 (High) | Daily | Real-time | Weekly | Monthly | Monthly |

#### 11.3.3 Agent Behavior Profiling

Behavior profiling creates a dynamic behavioral fingerprint of an agent to detect anomalies, drift, and potential compromise.

**Behavior Profile Dimensions:**

| Dimension | Signals | Detection Method |
|-----------|---------|-----------------|
| **Action Patterns** | Action types, frequency, sequences | Markov chain analysis |
| **Resource Access** | Resources accessed, access patterns | Access graph analysis |
| **Temporal Patterns** | Time-of-day, day-of-week activity | Time-series analysis |
| **Delegation Patterns** | Delegation frequency, depth, scope | Graph analysis |
| **Communication Patterns** | Inter-agent communication frequency, targets | Network analysis |
| **Error Patterns** | Error types, frequency, recovery patterns | Error clustering |
| **Data Access Patterns** | Data types, volumes, classification levels | Data flow analysis |

**Behavior Profile Record:**

```json
{
  "$schema": "https://grc-claw.dev/schemas/behavior-profile/v1",
  "agent": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "profile-version": "2026-10-01T12:00:00Z",
  "baseline-established": "2026-09-15T10:30:00Z",
  "dimensions": {
    "action-patterns": {
      "common-actions": [
        {"action": "read:ticket", "frequency": 0.45, "confidence": 0.95},
        {"action": "write:response", "frequency": 0.30, "confidence": 0.92},
        {"action": "search:knowledge-base", "frequency": 0.15, "confidence": 0.88}
      ],
      "sequence-model": "markov-chain-v3",
      "anomaly-threshold": 2.5
    },
    "resource-access": {
      "common-resources": [
        {"resource": "ticket-system", "access-frequency": 0.60, "confidence": 0.95},
        {"resource": "customer-db", "access-frequency": 0.30, "confidence": 0.90}
      ],
      "access-graph": "resource-access-graph-v2",
      "anomaly-threshold": 2.0
    },
    "temporal-patterns": {
      "active-hours": {"start": "08:00", "end": "18:00", "timezone": "UTC"},
      "peak-activity": "10:00-12:00",
      "day-of-week-pattern": "weekday-heavy",
      "anomaly-threshold": 3.0
    },
    "delegation-patterns": {
      "avg-delegation-depth": 1.2,
      "max-delegation-depth": 2,
      "common-delegates": ["did:grc:agent:ticket-summarizer"],
      "anomaly-threshold": 2.5
    },
    "communication-patterns": {
      "peers": ["did:grc:agent:response-writer", "did:grc:agent:ticket-reader"],
      "avg-messages-per-session": 15,
      "anomaly-threshold": 2.0
    },
    "error-patterns": {
      "common-errors": [
        {"error": "timeout", "frequency": 0.02, "confidence": 0.95},
        {"error": "rate-limit", "frequency": 0.01, "confidence": 0.90}
      ],
      "error-clusters": ["timeout-cluster-v1"],
      "anomaly-threshold": 3.0
    },
    "data-access-patterns": {
      "common-data-types": ["ticket", "customer-profile"],
      "avg-records-per-session": 25,
      "classification-levels": ["public", "internal"],
      "anomaly-threshold": 2.5
    }
  },
  "drift-detection": {
    "method": "ks-test",
    "threshold": 0.05,
    "last-drift-check": "2026-10-01T12:00:00Z",
    "drift-detected": false
  }
}
```

**Anomaly Detection:**

```
┌─────────────────────────────────────────────────────────────┐
│              BEHAVIOR ANOMALY DETECTION                      │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Action   │  │ Resource │  │ Temporal │  │ Comm     │   │
│  │ Patterns │  │ Access   │  │ Patterns │  │ Patterns │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │         │
│       └──────────────┼──────────────┘              │         │
│                      ▼                             │         │
│              ┌──────────────┐                      │         │
│              │   Anomaly    │◄─────────────────────┘         │
│              │   Detector   │                                │
│              └──────┬───────┘                                │
│                     │                                        │
│         ┌───────────┼───────────┐                           │
│         ▼           ▼           ▼                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ Baseline │ │ Statistical│ │ ML Model │                    │
│  │ Deviation│ │ Tests     │ │ Ensemble │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
│                                                              │
│  Anomaly Score = weighted_deviation × confidence            │
│                                                              │
│  Score > threshold → Alert → Review → Action               │
└─────────────────────────────────────────────────────────────┘
```

**Anomaly Response:**

| Anomaly Score | Severity | Automated Action | Notification |
|---------------|----------|------------------|--------------|
| 1.0–2.0 | Low | Log and continue | None |
| 2.0–3.0 | Medium | Increase monitoring frequency | Agent Owner |
| 3.0–4.0 | High | Restrict capabilities, require approval for sensitive actions | Agent Owner, Risk Officer |
| 4.0+ | Critical | Suspend agent, trigger incident response | Agent Owner, Risk Officer, CAIO |

#### 11.3.4 Agent Risk Assessment

Agent risk assessment evaluates the potential for adverse consequences from agent errors, misuse, or failure.

**Agent Risk Dimensions:**

| Dimension | Assessment Questions | Scoring |
|-----------|---------------------|---------|
| **Intended Use** | Is the agent's purpose clearly defined and documented? | 1-5 |
| **Data Sensitivity** | What data does the agent process? What is its classification? | 1-5 |
| **Decision Impact** | What decisions does the agent influence? What is the blast radius? | 1-5 |
| **Autonomy Level** | How much human oversight is present? Can the agent act autonomously? | 1-5 |
| **Regulatory Exposure** | What regulations apply? What is the compliance risk? | 1-5 |
| **Security Posture** | What security controls are in place? What is the attack surface? | 1-5 |
| **Explainability** | Can the agent's decisions be explained to affected parties? | 1-5 |
| **Delegation Risk** | How deep are delegation chains? What is the scope breadth? | 1-5 |

**Agent Risk Score Calculation:**

```
Agent Risk Score = (IntendedUse × 0.15) + (DataSensitivity × 0.20) + (DecisionImpact × 0.20) + (AutonomyLevel × 0.15) + (RegulatoryExposure × 0.10) + (SecurityPosture × 0.10) + (Explainability × 0.05) + (DelegationRisk × 0.05)
```

**Agent Risk Tiers:**

| Tier | Score Range | Description | Governance Requirements |
|------|-------------|-------------|------------------------|
| **Tier 1 — Minimal** | 1.00–1.99 | No consequential impact on individuals or operations | Basic registration, standard logging, annual review |
| **Tier 2 — Limited** | 2.00–2.99 | Limited consequential impact, non-regulated data | Registration, data classification review, human review, semi-annual review |
| **Tier 3 — Substantial** | 3.00–3.99 | Substantial impact on individuals or decisions, or regulated data | Full risk assessment, DPIA, human oversight, bias testing, enhanced monitoring, quarterly review |
| **Tier 4 — High** | 4.00–5.00 | High impact on fundamental rights, safety, or significant decisions | Full conformity assessment, FRIA, continuous monitoring, board approval, kill switch, monthly review |

**Agent Risk Assessment Record:**

```json
{
  "$schema": "https://grc-claw.dev/schemas/agent-risk-assessment/v1",
  "assessment-id": "risk:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "agent": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "assessed-by": "risk-scoring-engine-v2.1",
  "assessed-at": "2026-10-01T12:00:00Z",
  "risk-tier": "2",
  "dimensions": {
    "intended-use": {"score": 2, "rationale": "Customer service agent with well-defined scope"},
    "data-sensitivity": {"score": 3, "rationale": "Processes internal customer data"},
    "decision-impact": {"score": 2, "rationale": "Low-impact routing decisions"},
    "autonomy-level": {"score": 3, "rationale": "Semi-autonomous with human escalation"},
    "regulatory-exposure": {"score": 2, "rationale": "GDPR applies, standard compliance"},
    "security-posture": {"score": 2, "rationale": "Standard security controls in place"},
    "explainability": {"score": 2, "rationale": "Rule-based decisions, explainable"},
    "delegation-risk": {"score": 2, "rationale": "Shallow delegation chains, narrow scope"}
  },
  "overall-score": 2.30,
  "risk-appetite-check": "WITHIN_APPETITE",
  "treatment-decisions": [
    {
      "risk-id": "risk:customer-data-exposure",
      "description": "Agent processes internal customer data",
      "treatment": "MITIGATE",
      "mitigation-measures": ["data masking", "access logging", "rate limiting"],
      "residual-risk": "LOW",
      "accepted-by": "risk-officer-001"
    }
  ],
  "review-date": "2027-01-01",
  "next-review-date": "2027-04-01"
}
```

**Risk Re-assessment Triggers:**

| Trigger | Scope | Timeline |
|---------|-------|----------|
| Agent registration | Full assessment | Before activation |
| Capability change | Targeted re-assessment | Before new capability activation |
| Delegation depth increase | Targeted re-assessment | Before delegation expansion |
| Performance degradation | Full re-assessment | Within 24 hours of alert |
| Anomaly detection | Targeted re-assessment | Within 48 hours of anomaly |
| Security incident | Full re-assessment | Within 48 hours of incident |
| Regulatory change | Compliance re-assessment | Within 60 days of regulation |
| Scheduled review | Full re-assessment | Per risk tier frequency |

#### 11.3.5 Agent Compliance Monitoring

Compliance monitoring continuously verifies that an agent's actions, configurations, and behaviors comply with all applicable policies, regulations, and governance requirements.

**Compliance Monitoring Dimensions:**

| Dimension | Monitored Signals | Detection Method |
|-----------|-------------------|-----------------|
| **Policy Compliance** | Policy violations, policy drift | Real-time policy evaluation |
| **Capability Compliance** | Capability scope violations, unauthorized actions | Capability token validation |
| **Delegation Compliance** | Delegation scope violations, expired delegations | Delegation chain validation |
| **Data Compliance** | Data classification violations, unauthorized data access | Data access monitoring |
| **Regulatory Compliance** | Regulatory requirement violations | Regulatory rule engine |
| **Audit Compliance** | Audit trail gaps, missing events | Audit integrity verification |
| **Configuration Compliance** | Configuration drift from approved baseline | Configuration comparison |

**Compliance Check Record:**

```json
{
  "$schema": "https://grc-claw.dev/schemas/compliance-check/v1",
  "check-id": "comp:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "agent": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "check-type": "continuous",
  "checked-at": "2026-10-01T12:00:00Z",
  "dimensions": {
    "policy-compliance": {
      "status": "compliant",
      "violations-30d": 0,
      "drift-events": 0,
      "last-violation": null
    },
    "capability-compliance": {
      "status": "compliant",
      "unauthorized-actions-30d": 0,
      "scope-violations": 0,
      "last-violation": null
    },
    "delegation-compliance": {
      "status": "compliant",
      "scope-violations": 0,
      "expired-delegations": 0,
      "last-violation": null
    },
    "data-compliance": {
      "status": "compliant",
      "classification-violations": 0,
      "unauthorized-access": 0,
      "last-violation": null
    },
    "regulatory-compliance": {
      "status": "compliant",
      "violations": 0,
      "pending-reports": 0,
      "last-violation": null
    },
    "audit-compliance": {
      "status": "compliant",
      "missing-events": 0,
      "integrity-verified": true,
      "last-check": "2026-10-01T12:00:00Z"
    },
    "configuration-compliance": {
      "status": "compliant",
      "drift-detected": false,
      "last-baseline": "2026-09-15T10:30:00Z"
    }
  },
  "overall-status": "compliant",
  "next-check": "2026-10-01T18:00:00Z"
}
```

**Compliance Violation Response:**

| Violation Severity | Automated Action | Notification | Resolution Timeline |
|-------------------|------------------|--------------|---------------------|
| Critical | Immediate suspension, kill switch armed | Agent Owner, Risk Officer, CAIO | 4 hours |
| High | Restrict capabilities, require approval | Agent Owner, Risk Officer | 24 hours |
| Medium | Log violation, increase monitoring | Agent Owner | 72 hours |
| Low | Log violation, include in next review | Agent Owner | Next review |

**Compliance Monitoring Dashboard:**

```
┌─────────────────────────────────────────────────────────────┐
│           AGENT COMPLIANCE DASHBOARD                          │
│                                                              │
│  Agent: customer-service-agent                               │
│  Risk Tier: 2 (Limited)  |  Trust Level: High               │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Overall Status: COMPLIANT                            │    │
│  │ Last Check: 2026-10-01 12:00:00Z                    │    │
│  │ Next Check: 2026-10-01 18:00:00Z                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Policy       │  │ Capability   │  │ Delegation   │     │
│  │ ✓ Compliant  │  │ ✓ Compliant  │  │ ✓ Compliant  │     │
│  │ 0 violations │  │ 0 violations │  │ 0 violations │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Data         │  │ Regulatory   │  │ Audit        │     │
│  │ ✓ Compliant  │  │ ✓ Compliant  │  │ ✓ Compliant  │     │
│  │ 0 violations │  │ 0 violations │  │ 0 violations │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Configuration: ✓ Compliant                           │    │
│  │ No drift detected from baseline                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Recent Violations: None                                     │
│  Open Findings: None                                         │
│  Pending Reviews: None                                       │
└─────────────────────────────────────────────────────────────┘
```

### 11.4 Stage 3: Suspension

**Objective:** Temporarily halt an agent's operations while preserving its state, audit trail, and configuration for review.

#### 11.4.1 Suspension Controls

| Control | Requirement | Verification |
|---------|-------------|--------------|
| **S-01: Suspension Decision** | Suspension must be formally decided and approved | Suspension workflow — approval recorded |
| **S-02: Immediate Halt** | All agent operations must be immediately halted | Kill switch — verified halt |
| **S-03: State Preservation** | Agent state must be preserved for review | State snapshot — integrity verified |
| **S-04: Delegation Suspension** | All active delegations must be suspended | Delegation tracker — all delegations suspended |
| **S-05: Capability Suspension** | All capabilities must be suspended | Capability service — all capabilities suspended |
| **S-06: Notification** | Stakeholders must be notified of suspension | Notification log — stakeholders informed |
| **S-07: Review Process** | Suspended agent must undergo formal review | Review workflow — review scheduled |
| **S-08: Reinstatement Criteria** | Criteria for reinstatement must be defined | Reinstatement policy — criteria documented |

#### 11.4.2 Suspension Record

```json
{
  "$schema": "https://grc-claw.dev/schemas/suspension/v1",
  "suspension-id": "susp:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "agent": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "reason": "anomalous-behavior-detected",
  "severity": "high",
  "suspended-by": "did:grc:system:risk-engine",
  "suspended-at": "2026-10-01T14:30:00Z",
  "state-snapshot": {
    "snapshot-id": "snap:2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
    "integrity-hash": "sha256:abc123...",
    "captured-at": "2026-10-01T14:30:00Z"
  },
  "delegations-suspended": 3,
  "capabilities-suspended": 5,
  "review-assigned-to": "risk-officer-001",
  "review-deadline": "2026-10-02T14:30:00Z",
  "reinstatement-criteria": [
    "Anomaly root cause identified and remediated",
    "Risk re-assessment completed",
    "Agent Owner approves reinstatement"
  ],
  "status": "active"
}
```

### 11.5 Stage 4: Retirement

**Objective:** Formally decommission an agent with proper archival, access revocation, and data disposition.

#### 11.5.1 Retirement Controls

| Control | Requirement | Verification |
|---------|-------------|--------------|
| **R-01: Retirement Decision** | Retirement must be formally decided and approved | Retirement workflow — approval recorded |
| **R-02: Stakeholder Notification** | All stakeholders must be notified of retirement | Notification log — stakeholders informed |
| **R-03: Access Revocation** | All access to the agent must be revoked | Access control — revocation verified |
| **R-04: Data Disposition** | Agent data and artifacts must be dispositioned per retention policy | Data Governance Board — disposition decision recorded |
| **R-05: Archival** | Agent artifacts must be archived with appropriate retention | Archive storage — retention policy applied |
| **R-06: Deletion Verification** | Deletion of agent artifacts must be verified and certified | Deletion certificate — cryptographic verification |
| **R-07: Registry Update** | Identity Registry must be updated with retirement status | Registry — retirement status updated |
| **R-08: Audit Record** | Retirement must be recorded in the audit trail | Audit log — retirement event with full context |
| **R-09: Dependency Check** | Downstream dependencies must be identified and notified | Lineage query — downstream consumers identified |
| **R-10: Lessons Learned** | Retirement must include lessons learned documentation | Lessons learned report — improvements identified |

#### 11.5.2 Retirement Workflow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ DECISION │───►│  DRAIN   │───►│  REVOKE  │───►│  ARCHIVE │───►│  DELETE  │
│          │    │          │    │          │    │          │    │          │
│ Approve  │    │ Stop new │    │ Revoke   │    │ Archive  │    │ Delete   │
│ Retirement│   │ tasks    │    │ all caps │    │ artifacts│    │ artifacts│
│          │    │ Complete │    │ Revoke   │    │ Preserve │    │ Verify   │
│          │    │ in-flight│    │ delegs   │    │ audit    │    │ deletion │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

#### 11.5.3 Retirement Record

```json
{
  "$schema": "https://grc-claw.dev/schemas/retirement/v1",
  "retirement-id": "ret:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "agent": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "reason": "replaced-by-newer-version",
  "decided-by": "agent-owner-001",
  "decided-at": "2026-10-01T15:00:00Z",
  "stakeholders-notified": ["agent-owner-001", "risk-officer-001", "compliance-001"],
  "access-revoked": {
    "capabilities-revoked": 5,
    "delegations-revoked": 3,
    "api-keys-revoked": 2,
    "revoked-at": "2026-10-01T15:30:00Z"
  },
  "data-disposition": {
    "training-data": "archived",
    "configuration": "archived",
    "audit-trail": "retained-7-years",
    "disposition-decision-by": "data-governance-board",
    "disposition-date": "2026-10-01T16:00:00Z"
  },
  "archival": {
    "archive-location": "s3://grc-claw-archives/agents/customer-service-agent/",
    "retention-period": "7-years",
    "archive-integrity-hash": "sha256:def456...",
    "archived-at": "2026-10-01T16:30:00Z"
  },
  "deletion": {
    "artifacts-deleted": ["sandbox-environment", "runtime-state", "temporary-data"],
    "deletion-certificate": "cert:7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
    "deleted-at": "2026-10-01T17:00:00Z"
  },
  "dependencies-identified": [
    {
      "dependent": "did:grc:agent:response-writer",
      "relationship": "peer",
      "notified-at": "2026-10-01T15:00:00Z"
    }
  ],
  "lessons-learned": {
    "report-id": "ll:2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
    "key-findings": ["Agent performed well", "No major incidents"],
    "improvements": ["Consider adding more granular capability controls"]
  },
  "status": "complete"
}
```

### 11.6 Stage 5: Decommissioning

**Objective:** Complete the decommissioning process with final verification, certification, and closure.

#### 11.6.1 Decommissioning Controls

| Control | Requirement | Verification |
|---------|-------------|--------------|
| **D-01: Final Verification** | All retirement controls must be verified complete | Verification checklist — all items verified |
| **D-02: Certificate of Decommissioning** | A formal certificate must be issued | Certificate — cryptographically signed |
| **D-03: Registry Closure** | Identity Registry entry must be marked as decommissioned | Registry — status updated |
| **D-04: Final Audit** | A final audit event must be recorded | Audit log — decommissioning event |
| **D-05: Stakeholder Confirmation** | All stakeholders must confirm decommissioning is complete | Confirmation log — all confirmations received |
| **D-06: Archive Verification** | Archived artifacts must be verified for integrity | Archive — integrity check passed |
| **D-07: Lessons Learned Review** | Lessons learned must be reviewed and incorporated | Review meeting — improvements tracked |

#### 11.6.2 Certificate of Decommissioning

```json
{
  "$schema": "https://grc-claw.dev/schemas/decommission-certificate/v1",
  "certificate-id": "cert:7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
  "agent": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "agent-name": "customer-service-agent",
  "decommissioned-at": "2026-10-01T17:00:00Z",
  "decommissioned-by": "agent-owner-001",
  "verification-results": {
    "access-revoked": true,
    "data-dispositioned": true,
    "artifacts-archived": true,
    "artifacts-deleted": true,
    "dependencies-notified": true,
    "lessons-learned-documented": true,
    "audit-trail-complete": true
  },
  "archive-location": "s3://grc-claw-archives/agents/customer-service-agent/",
  "archive-retention-until": "2033-10-01T17:00:00Z",
  "audit-trail-id": "chain:0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  "digital-signature": "base64-encoded-ed25519-signature"
}
```

### 11.7 Stage Transitions

All stage transitions must be explicitly approved and recorded in the audit trail.

```
PROVISIONING ──► ACTIVE        (Gate 1: Identity Issued)
ACTIVE        ──► SUSPENDED     (Gate 2: Risk Threshold or Anomaly)
ACTIVE        ──► RETIRING      (Gate 3: Retirement Decision)
SUSPENDED     ──► ACTIVE        (Reinstatement Approved)
SUSPENDED     ──► RETIRING      (Gate 3: Retirement Decision)
RETIRING      ──► DECOMMISSION  (Gate 4: Decommissioning Complete)
DECOMMISSION  ──► [Terminal]    (No further transitions)
```

**Emergency Transitions:**
- Any stage may transition directly to **RETIRING** in case of emergency (security incident, safety risk, regulatory violation)
- Emergency transitions require post-hoc approval within 24 hours
- Emergency transitions trigger automatic incident response

### 11.8 Agent Lifecycle API

```python
class AgentLifecycleManager:
    """Agent lifecycle management with governance enforcement."""
    
    # Provisioning
    def provision_agent(self, request: ProvisioningRequest) -> AgentIdentity: ...
    def get_provisioning_status(self, agent_id: str) -> ProvisioningStatus: ...
    
    # Active Operations
    def get_performance_score(self, agent_id: str) -> PerformanceScore: ...
    def get_behavior_profile(self, agent_id: str) -> BehaviorProfile: ...
    def get_risk_assessment(self, agent_id: str) -> RiskAssessment: ...
    def get_compliance_status(self, agent_id: str) -> ComplianceStatus: ...
    def trigger_re_assessment(self, agent_id: str, trigger: str) -> None: ...
    
    # Suspension
    def suspend_agent(self, agent_id: str, reason: str, severity: str) -> SuspensionRecord: ...
    def reinstate_agent(self, agent_id: str, approver: str) -> None: ...
    def get_suspension_status(self, agent_id: str) -> SuspensionStatus: ...
    
    # Retirement
    def initiate_retirement(self, agent_id: str, reason: str, approver: str) -> RetirementRecord: ...
    def complete_retirement(self, agent_id: str) -> None: ...
    def get_retirement_status(self, agent_id: str) -> RetirementStatus: ...
    
    # Decommissioning
    def verify_decommissioning(self, agent_id: str) -> VerificationResult: ...
    def issue_decommission_certificate(self, agent_id: str) -> DecommissionCertificate: ...
    def get_decommission_status(self, agent_id: str) -> DecommissionStatus: ...
    
    # Lifecycle Queries
    def get_lifecycle_history(self, agent_id: str) -> List[LifecycleEvent]: ...
    def get_agents_by_stage(self, stage: LifecycleStage) -> List[str]: ...
    def get_agents_by_risk_tier(self, tier: int) -> List[str]: ...
```

### 11.9 Agent Lifecycle Metrics

| KPI | Target | Measurement | Frequency |
|-----|--------|-------------|-----------|
| Agent registration rate | 100% | Registered agents / Total agents | Real-time |
| Provisioning time | ≤ 1 hour | Average time from request to active | Monthly |
| Performance score accuracy | ≥ 95% | Scores matching manual review / Total scores | Quarterly |
| Anomaly detection precision | ≥ 90% | True anomalies / Total anomalies flagged | Monthly |
| Anomaly detection recall | ≥ 85% | Detected anomalies / Total actual anomalies | Monthly |
| Risk assessment timeliness | 100% | Assessments completed on schedule / Total scheduled | Real-time |
| Compliance check pass rate | ≥ 99% | Passed checks / Total checks | Real-time |
| Suspension response time | ≤ 5 minutes | Average time from trigger to suspension | Monthly |
| Retirement compliance | 100% | Retired agents with complete audit trail / Total retired | Per retirement |
| Decommissioning verification | 100% | Verified decommissions / Total decommissions | Per decommission |
| Mean time to retirement decision | ≤ 30 days | Average time from retirement request to decision | Monthly |
| Agent lifecycle audit completeness | 100% | Agents with complete lifecycle records / Total agents | Real-time |

### 11.10 Agent Lifecycle Compliance Mapping

#### 11.10.1 OWASP Agentic AI Top 10 — Agent Lifecycle Controls

| ASI | Risk | Agent Lifecycle Control |
|-----|------|--------------------------|
| ASI01 | Agent Goal Hijack | Behavior profiling (Section 11.3.3), anomaly detection, kill switch (Section 11.2.1 P-08) |
| ASI02 | Tool Misuse | Capability usage monitoring (Section 11.3.1 A-07), compliance checking (Section 11.3.5) |
| ASI03 | Identity & Privilege Abuse | Agent risk assessment (Section 11.3.4), provisioning controls (Section 11.2.1), trust evaluation (Section 2.4) |
| ASI04 | Agentic Supply Chain | Framework adapter verification (Section 11.2.1 P-06), provisioning automation (Section 11.2.3) |
| ASI05 | Unexpected Code Execution | Sandbox configuration (Section 11.2.1 P-07), capability declaration (Section 11.2.1 P-04) |
| ASI06 | Memory & Context Poisoning | Audit trail integrity (Section 7.4), behavior profiling (Section 11.3.3) |
| ASI07 | Insecure Inter-Agent Comms | Communication pattern monitoring (Section 11.3.3), delegation compliance (Section 11.3.5) |
| ASI08 | Cascading Failures | Delegation monitoring (Section 11.3.1 A-06), suspension controls (Section 11.4.1) |
| ASI09 | Human-Agent Trust Exploitation | Compliance monitoring (Section 11.3.5), anomaly response (Section 11.3.3) |
| ASI10 | Rogue Agents | Kill switch (Section 11.2.1 P-08), suspension (Section 11.4), retirement (Section 11.5) |

#### 11.10.2 NIST AI RMF 1.0 — Agent Lifecycle Coverage

| Function | Agent Lifecycle Coverage |
|----------|--------------------------|
| GOVERN | Agent provisioning (Section 11.2), policy binding (Section 11.2.1 P-05), lifecycle metrics (Section 11.9) |
| MAP | Agent risk assessment (Section 11.3.4), capability declaration (Section 11.2.1 P-04), behavior profiling (Section 11.3.3) |
| MEASURE | Performance scoring (Section 11.3.2), compliance monitoring (Section 11.3.5), trust evaluation (Section 2.4) |
| MANAGE | Suspension (Section 11.4), retirement (Section 11.5), decommissioning (Section 11.6), incident response (Section 11.3.1 A-08) |

#### 11.10.3 ISO/IEC 42001 — Agent Lifecycle Coverage

| Clause | Agent Lifecycle Coverage |
|--------|--------------------------|
| 4. Context | Agent inventory, deployment context, provisioning (Section 11.2) |
| 5. Leadership | Policy ownership, trust level assignment, risk tier classification (Section 11.3.4) |
| 6. Planning | Risk assessment (Section 11.3.4), capability scoping (Section 11.2.1 P-04) |
| 7. Support | Agent onboarding, training requirements for trust promotion (Section 2.4.3) |
| 8. Operation | Runtime enforcement, delegation management, performance scoring (Section 11.3.2) |
| 9. Performance Evaluation | Audit trail (Section 7), trust evaluation (Section 2.4), compliance monitoring (Section 11.3.5), lifecycle metrics (Section 11.9) |
| 10. Improvement | Incident-driven policy updates, trust demotion triggers (Section 2.4.3), lessons learned (Section 11.5.1 R-10) |

---

## 12. Appendix A: JSON Schemas

All JSON schemas referenced in this specification are available at:
`https://grc-claw.dev/schemas/{schema-name}/v1`

| Schema | URL |
|--------|-----|
| Agent Identity | `/schemas/agent-identity/v1` |
| Delegation | `/schemas/delegation/v1` |
| Delegation Chain | `/schemas/delegation-chain/v1` |
| Capability | `/schemas/capability/v1` |
| Trust Score | `/schemas/trust/v1` |
| AuthZ Request | `/schemas/authz-request/v1` |
| AuthZ Decision | `/schemas/authz-decision/v1` |
| Audit Event | `/schemas/audit-event/v1` |
| Cross-Org Trust | `/schemas/cross-org-trust/v1` |
| Provisioning Request | `/schemas/provisioning-request/v1` |
| Performance Score | `/schemas/performance-score/v1` |
| Behavior Profile | `/schemas/behavior-profile/v1` |
| Agent Risk Assessment | `/schemas/agent-risk-assessment/v1` |
| Compliance Check | `/schemas/compliance-check/v1` |
| Suspension | `/schemas/suspension/v1` |
| Retirement | `/schemas/retirement/v1` |
| Decommission Certificate | `/schemas/decommission-certificate/v1` |

---

## 13. Appendix B: Glossary

| Term | Definition |
|------|------------|
| **AGP** | Agent Governance Protocol — this specification |
| **DID** | Decentralized Identifier — W3C standard for verifiable identities |
| **Capability** | A scoped, verifiable authorization to perform an action on a resource |
| **Delegation** | A time-bounded transfer of authority from one agent to another |
| **Trust Score** | A quantifiable measure of agent reliability (0.0–1.0) |
| **Trust Level** | A discrete classification of trust (untrusted → privileged) |
| **Merkle Chain** | A cryptographic hash chain ensuring audit trail integrity |
| **SPIFFE** | Secure Production Identity Framework for Everyone — workload identity standard |
| **OPA** | Open Policy Agent — CNCF policy engine |
| **Rego** | OPA's declarative policy language |
| **OWASP ASI** | OWASP Agentic Security Initiative — top 10 risks for agentic AI |
| **NIST AI RMF** | NIST AI Risk Management Framework |
| **ISO/IEC 42001** | International standard for AI management systems |
| **Agent Provisioning** | The automated process of creating, registering, and activating a new agent identity with full governance controls |
| **Agent Performance Score** | A quantifiable measure of an agent's operational effectiveness (0.0–1.0) based on task success, efficiency, quality, and reliability |
| **Agent Behavior Profile** | A dynamic behavioral fingerprint of an agent used to detect anomalies, drift, and potential compromise |
| **Agent Risk Tier** | A classification of an agent's potential for adverse consequences (1=Minimal to 4=High) |
| **Agent Compliance Status** | The continuous assessment of an agent's adherence to policies, regulations, and governance requirements |
| **Agent Suspension** | The temporary halt of an agent's operations while preserving its state, audit trail, and configuration for review |
| **Agent Retirement** | The formal decommissioning of an agent with proper archival, access revocation, and data disposition |
| **Agent Decommissioning** | The final verification, certification, and closure of an agent's lifecycle |
| **Kill Switch** | A mechanism for immediate deactivation of an agent in case of emergency, security incident, or governance violation |
| **Agent Lifecycle Stage** | The current phase of an agent's lifecycle: Provisioning, Active, Suspended, Retiring, or Decommission |

---

## 14. Appendix C: Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Architecture Team | Initial specification |
| 1.1 | 2026-10-01 | GRC_Claw Architecture Team | Added Agent Lifecycle Management (Section 11): provisioning, performance scoring, behavior profiling, risk assessment, compliance monitoring, suspension, retirement, and decommissioning |

---

*End of specification.*
