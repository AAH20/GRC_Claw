# GRC_Claw Automation Engine: Deep-Dive Analysis & Open-Source Proposal

## Executive Summary

After analyzing 8 platforms (4 commercial, 4 open-source), the AI governance automation market reveals a clear pattern: **no single open-source tool covers the full lifecycle from discovery through runtime enforcement to audit evidence**. The gap is real and significant. This proposal outlines an open-source automation engine for GRC_Claw that fills this gap by combining the best patterns from commercial platforms with the extensibility of open-source.

---

## Part 1: Platform Comparison Matrix

### 1.1 Commercial Platforms

| Dimension | Credo AI | Holistic AI | IBM watsonx.governance | OneTrust |
|-----------|----------|-------------|------------------------|----------|
| **Core Pattern** | Knowledge Graph + Policy Packs | Guardian Agents (Sentinel + Operative) | Factsheets + Evaluation Studio | CORIE Intelligence Layer + AI Control Plane |
| **Discovery** | Shadow AI auto-discovery across cloud | 15+ read-only connectors (AWS, Azure, GitHub, Databricks) | Guardium AI Security integration | Trust Graph mapping |
| **Inventory** | AI Registry + Agent Registry with dependency graphs | Centralized AI Inventory with classification | AI use case inventory + governed agentic catalog | AI Program Center |
| **Risk Assessment** | Continuous contextual risk assessment | 40+ specialized tests (bias, safety, security, performance) | Automated risk scoring + evaluation studio | Template-driven risk tiering |
| **Policy Mapping** | Policy packs (EU AI Act, NIST, ISO 42001, OMB M-25) | Built-in frameworks (EU AI Act, NIST, ISO 42001, NYC LL 144) | Factsheets with compliance tracking | 50+ pre-mapped frameworks, 300+ jurisdictions |
| **Runtime Enforcement** | Policy engine with evidence recording | Guardian Agents (kill switches, blocking, remediation) | Guardrails for inputs/outputs | AI Control Plane (block, redact, route, escalate) |
| **Monitoring** | Real-time risk dashboards, drift detection | Sentinel Agents (continuous detection) | Runtime monitoring + anomaly detection | Continuous monitoring + alerts |
| **Evidence** | Automated evidence generation | Continuous audit trails | Factsheet history | Evidence Ledger (hash-chained) |
| **Agentic AI** | Agent Registry, GAIA assistant, multi-agent dependency graphs | Agent Graph, agentic red teaming, workflow tracing | Agentic catalog, experiment tracking | MCP governance, Guardian Agents |
| **Integrations** | 30+ (AWS, Azure, GCP, Databricks, Snowflake, ServiceNow, Jira, GitHub, MLflow) | 15+ (AWS, Azure, GCP, GitHub, GitLab, Databricks, MLflow, W&B, OpenAI, Anthropic) | AWS SageMaker, Azure, Guardium | 200+ (Bedrock, Azure AI Foundry, Vertex, Databricks, Jira, Snowflake, ServiceNow) |
| **Key Differentiator** | Proprietary knowledge graph fusing regulatory intelligence with business context | Only platform with autonomous enforcement agents (Sentinel + Operative) | Deep IBM ecosystem integration, model lifecycle management | Broadest GRC coverage, privacy + AI governance convergence |

### 1.2 Open-Source Platforms

| Dimension | VerifyWise | Vigil | WhitePact | AIBOM-Guard |
|-----------|------------|-------|-----------|-------------|
| **License** | BSL 1.1 (source-available) | Apache 2.0 | MIT | MIT |
| **Core Pattern** | Full-lifecycle platform (register → assess → govern → monitor) | AI SOC with 13 specialized agents | Deterministic 5-way governance engine | CLI-based compliance triage |
| **Discovery** | Shadow AI detection, AI agent discovery | Agent discovery across enterprise | N/A (runtime only) | 220+ AI library signatures, repo scanning |
| **Inventory** | AI registry, model inventory, dataset registry | Agent inventory with identity attestation | N/A | AI-BOM (CycloneDX 1.6 + SPDX 3.0) |
| **Risk Assessment** | Risk management, LLM evaluations, bias audits | Live trust scoring, confidence thresholds | 6-dimension trust score (A-F grade) | EU AI Act tier triage (prohibited/high/limited/minimal) |
| **Policy Mapping** | 24+ frameworks (EU AI Act, ISO 42001, NIST, GDPR, SOC 2, HIPAA, etc.) | Compliance agent (NIST, ISO, PCI-DSS, HIPAA, GDPR, SOC 2) | NIST AI RMF, EU AI Act, ISO 42001 | EU AI Act, ISO 42001, NIST AI RMF (65 subcategories) |
| **Runtime Enforcement** | Policy manager, approval workflows, automations | Kernel-level enforcer (allow/deny/approve/contain) | 5-way decision (ALLOW/ALLOW_WITH_REDACTION/REQUIRE_APPROVAL/DENY/QUARANTINE) | N/A (documentation only) |
| **Monitoring** | Post-market monitoring, reporting | Continuous detection, 7,200+ detection rules | Drift monitoring, alerts | N/A |
| **Evidence** | Evidence center, audit trails, PDF/DOCX export | Audit-ready evidence packs, ledger-backed | Hash-chained EvidenceRecord | Annex IV technical documentation, HTML reports |
| **Agentic AI** | Agent Control module (v2.4) | Full agentic SOC (13 agents, MCP) | MCP server (30 tools, 20 resources) | MCP server (6 tools) |
| **Integrations** | 15+ plugins, MIT/IBM AI risk repository | 30+ MCP integrations, Bifrost LLM gateway | LangChain, LangGraph, Google ADK | GitHub, HuggingFace Hub |
| **Key Differentiator** | Most comprehensive open-source full-lifecycle platform | Only open-source agentic SOC with autonomous response | Only deterministic (non-LLM) governance decision engine | Only tool generating standards-compliant AI-BOMs |

---

## Part 2: Automation Patterns Identified

### Pattern 1: Policy-as-Code Translation
**Seen in:** Credo AI (policy packs), OneTrust (reasoning engine), WhitePact (deterministic rules), AIBOM-Guard (YAML knowledge bases)

The pattern: regulatory text → machine-readable rules → executable checks. Credo AI uses proprietary policy packs; WhitePact uses a deterministic first-match-wins policy engine; AIBOM-Guard uses editable YAML knowledge bases. The key insight is that **policy translation must be deterministic and auditable** — LLM-based classification alone is insufficient for enforcement decisions.

### Pattern 2: Five-Way Governance Decisions
**Seen in:** WhitePact (ALLOW / ALLOW_WITH_REDACTION / REQUIRE_APPROVAL / DENY / QUARANTINE)

Most platforms use binary allow/deny. WhitePact's five-way decision is more nuanced and maps better to real governance workflows where redaction, approval, and quarantine are distinct actions. This should be the standard for GRC_Claw.

### Pattern 3: Guardian Agent Architecture
**Seen in:** Holistic AI (Sentinel + Operative), Vigil (13 specialized agents), Credo AI (GAIA)

The pattern: specialized AI agents for different governance functions. Holistic AI separates detection (Sentinel) from enforcement (Operative). Vigil has 13 agents (Triage, Investigator, Compliance, etc.). This separation of concerns is critical — detection and enforcement should be independent.

### Pattern 4: MCP as Universal Integration Layer
**Seen in:** WhitePact, AIBOM-Guard, OneTrust, Vigil, IBM watsonx.governance

MCP (Model Context Protocol) is emerging as the standard integration layer for AI governance. WhitePact exposes 30 tools via MCP; AIBOM-Guard wraps its CLI as MCP tools; OneTrust has an MCP Gateway. This allows governance to be embedded directly into AI workflows without code changes.

### Pattern 5: Evidence-First Design
**Seen in:** All platforms, but most mature in OneTrust (Evidence Ledger) and WhitePact (hash-chained records)

Every platform emphasizes audit-ready evidence. OneTrust's Evidence Ledger captures what was considered, which policy applied, and what action was taken. WhitePact uses hash-chained EvidenceRecords with tamper detection. This is non-negotiable for GRC use cases.

### Pattern 6: Knowledge Graph for Context
**Seen in:** Credo AI (Governance Knowledge Graph), OneTrust (Trust Graph)

Both Credo AI and OneTrust use knowledge graphs to connect regulations, business context, and AI system configurations. This enables contextual governance — a model used in EU healthcare requires different controls than one in US financial services.

### Pattern 7: Deterministic Enforcement Outside the LLM
**Seen in:** WhitePact (no LLM in decision path), Vigil (kernel-level enforcer), Holistic AI (Guardian Agents)

The most robust pattern: governance decisions are made by deterministic systems outside the LLM's control. WhitePact explicitly states "no governance decision is LLM-based." Vigil enforces at the kernel level. This prevents the governed system from influencing its own governance.

---

## Part 3: GRC_Claw Automation Engine Proposal

### 3.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GRC_Claw Automation Engine                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Discovery  │→ │  Inventory  │→ │    Risk     │→ │   Policy    │        │
│  │   Engine    │  │   Graph     │  │ Assessment  │  │   Mapping   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                │                │                │                │
│         ▼                ▼                ▼                ▼                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Governance Knowledge Graph                         │   │
│  │  (Regulations × Business Context × AI Configurations × Controls)    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                │                │                │                │
│         ▼                ▼                ▼                ▼                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Runtime   │→ │ Continuous  │→ │    Audit    │  │   Agent     │        │
│  │ Enforcement │  │  Monitoring │  │  Evidence   │  │  Governance │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    MCP Gateway (Universal Integration)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Module Specifications

#### Module 1: Discovery Engine
**Purpose:** Automatically find all AI systems, models, agents, and pipelines across the enterprise.

**Design:**
- **Repository Scanner** (inspired by AIBOM-Guard): Scan code repos for 220+ AI library signatures, model files, API usage patterns
- **Cloud Connector** (inspired by Holistic AI): Read-only connectors for AWS, Azure, GCP, Databricks, Snowflake
- **Agent Detector** (inspired by Vigil): Detect registered and shadow AI agents across enterprise environments
- **MCP Registry** (inspired by agentic-community/mcp-gateway-registry): Discover MCP servers and tools
- **Output:** Raw discovery events → normalized AI asset records

**Key Design Decision:** Discovery must be read-only and non-intrusive. No agents to install, no code changes required.

#### Module 2: Inventory Graph
**Purpose:** Maintain a live, queryable inventory of all AI assets with dependency mapping.

**Design:**
- **Graph Database** (inspired by Credo AI Knowledge Graph, OneTrust Trust Graph): Nodes = AI assets (models, agents, datasets, APIs, vendors); Edges = dependencies, data flows, ownership
- **Asset Types:** Models, Agents, Datasets, Pipelines, Vendors, Endpoints
- **Metadata:** Owner, lifecycle stage, risk tier, business purpose, deployment status
- **Versioning:** Track changes over time with full lineage
- **API:** GraphQL for complex queries, REST for CRUD

**Key Design Decision:** Use a graph database (Neo4j or Apache AGE) rather than a relational database. AI systems have complex, multi-hop dependencies that are naturally expressed as graphs.

#### Module 3: Risk Assessment Engine
**Purpose:** Continuously assess risk across all AI assets using automated testing and scoring.

**Design:**
- **Test Suite** (inspired by Holistic AI's 40+ tests): Bias, fairness, toxicity, hallucination, prompt injection, adversarial attacks, robustness, privacy, performance
- **Risk Scoring** (inspired by WhitePact's 6-dimension trust score): Multi-dimensional scoring (0-100) with A-F grade
- **EU AI Act Triage** (inspired by AIBOM-Guard): Automatic risk tier classification (prohibited/high/limited/minimal) with Annex III matching
- **Agentic Risk Library** (inspired by Credo AI): Purpose-built risks for tool misuse, scope drift, inter-agent risk
- **Continuous Evaluation:** Pre-deployment gates + post-deployment monitoring

**Key Design Decision:** Risk assessment must be multi-dimensional. A single risk score is insufficient — different stakeholders care about different risk dimensions.

#### Module 4: Policy Mapping Engine
**Purpose:** Translate regulatory requirements and internal policies into executable controls.

**Design:**
- **Policy Packs** (inspired by Credo AI): Pre-built regulatory mappings for EU AI Act, NIST AI RMF, ISO 42001, GDPR, SOC 2, HIPAA
- **YAML Knowledge Bases** (inspired by AIBOM-Guard): Editable, version-controlled policy definitions
- **Policy-to-Code Compiler** (inspired by WhitePact): Deterministic translation of policy text → executable rules
- **Crosswalk Engine** (inspired by aitrustcommons/governance-framework): Map controls across frameworks (implement once, get credit across multiple frameworks)
- **Custom Framework Support:** Allow organizations to define their own governance frameworks

**Key Design Decision:** Policy definitions must be in version-controlled YAML, not hardcoded. This allows auditors to review exactly what rules are being enforced and allows organizations to customize without forking code.

#### Module 5: Runtime Enforcement Engine
**Purpose:** Enforce governance decisions at the point of AI system operation.

**Design:**
- **Five-Way Decision Engine** (inspired by WhitePact): ALLOW / ALLOW_WITH_REDACTION / REQUIRE_APPROVAL / DENY / QUARANTINE
- **Deterministic Core** (inspired by WhitePact, Vigil): No LLM in the decision path — governance decisions are made by deterministic rules
- **MCP Gateway** (inspired by OneTrust, agentic-community): Intercept all AI tool calls through a governed gateway
- **Kernel-Level Enforcer** (inspired by Vigil): For agent-level enforcement (file, network, process, tool control)
- **Approval Workflow** (inspired by WhitePact): REQUIRE_APPROVAL decisions queue real approval requests with resolution API
- **Kill Switch** (inspired by Holistic AI): Emergency stop for any AI system

**Key Design Decision:** Enforcement must be deterministic and outside the LLM's control. The governed system must not be able to influence its own governance.

#### Module 6: Continuous Monitoring Engine
**Purpose:** Monitor AI systems in production for drift, violations, and emerging risks.

**Design:**
- **Sentinel Agents** (inspired by Holistic AI, Vigil): Specialized monitoring agents for different risk types
- **Drift Detection** (inspired by WhitePact, IBM): Track model behavior changes over time
- **Anomaly Detection** (inspired by Vigil): 7,200+ detection rules (Sigma, Splunk, Elastic, KQL)
- **Alert Routing** (inspired by Vigil): Confidence-based routing — auto-approve above threshold, human review below
- **Regulatory Change Monitor** (inspired by apifyforge/ai-model-governance-mcp): Track regulatory updates and map to affected assets

**Key Design Decision:** Monitoring should use a confidence threshold model. High-confidence violations auto-remediate; low-confidence ones route to humans. This prevents both alert fatigue and missed risks.

#### Module 7: Audit Evidence Engine
**Purpose:** Generate and maintain audit-ready evidence for all governance activities.

**Design:**
- **Evidence Ledger** (inspired by OneTrust): Hash-chained, tamper-evident record of all governance decisions
- **Evidence Packs** (inspired by Vigil): Pre-packaged evidence for specific audit scenarios
- **Report Generator** (inspired by VerifyWise, AIBOM-Guard): PDF, DOCX, HTML export
- **AI Trust Center** (inspired by VerifyWise): Public-facing governance posture dashboard
- **Chain of Custody** (inspired by WhitePact): Every evidence item has verifiable provenance

**Key Design Decision:** Evidence must be generated continuously, not assembled before an audit. The system should be "audit-ready from day one, not day-before-audit" (Holistic AI principle).

#### Module 8: Agent Governance Layer
**Purpose:** Govern autonomous AI agents with specialized governance agents.

**Design:**
- **Sentinel Agents** (inspired by Holistic AI, Vigil): Detection-focused — drift, bias, anomalies, compliance gaps
- **Operative Agents** (inspired by Holistic AI): Enforcement-focused — kill switches, blocking, remediation
- **Governance Assistant** (inspired by Credo AI's GAIA): AI-powered assistant for governance teams
- **Agent Identity & Attestation** (inspired by Vigil): Verify agent identity, runtime posture, policy bundle, trust level
- **Multi-Agent Governance** (inspired by Credo AI): Dependency graphs across multi-agent networks

**Key Design Decision:** Detection and enforcement agents must be separate. The agent that detects a violation should not be the same agent that enforces the remediation — this prevents conflicts of interest.

### 3.3 Integration Architecture

```
                    ┌─────────────────────┐
                    │   AI Agents / Apps   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    MCP Gateway       │
                    │  (Auth + Routing +   │
                    │   Audit + Policy)    │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
    ┌─────▼─────┐       ┌─────▼─────┐       ┌─────▼─────┐
    │  MCP       │       │  MCP       │       │  MCP       │
    │  Server A  │       │  Server B  │       │  Server C  │
    └───────────┘       └───────────┘       └───────────┘
```

**Integration Points:**
1. **MCP Gateway** — Single entry point for all AI tool calls, with OAuth 2.1, policy enforcement, and audit logging
2. **Cloud Connectors** — AWS, Azure, GCP, Databricks, Snowflake (read-only discovery)
3. **Code Repository Connectors** — GitHub, GitLab, Bitbucket (AI component scanning)
4. **MLOps Connectors** — MLflow, Weights & Biases, Kubeflow (model metadata)
5. **GRC Connectors** — ServiceNow, Archer, OneTrust (governance workflow integration)
6. **SIEM Connectors** — Splunk, Elastic, Sentinel (security event integration)
7. **Webhook/API** — Custom integrations via REST API and webhooks

### 3.4 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Graph Database** | Neo4j / Apache AGE | Native graph queries for dependency mapping |
| **Policy Engine** | Open Policy Agent (OPA) / Cedar | Declarative, auditable policy-as-code |
| **MCP Server** | Python MCP SDK / TypeScript MCP SDK | Official SDKs, active ecosystem |
| **Task Queue** | Celery / Temporal | Reliable async processing for governance workflows |
| **Event Streaming** | Apache Kafka / NATS | Real-time event processing for monitoring |
| **Evidence Store** | PostgreSQL + immudb | Relational data + immutable audit log |
| **Frontend** | React + D3.js | Interactive graph visualization |
| **API** | FastAPI (Python) | Async, OpenAPI-native, MCP-compatible |
| **Deployment** | Docker + Kubernetes | Cloud-agnostic, scalable |
| **Observability** | OpenTelemetry | Standard tracing for audit trails |

### 3.5 Data Model (Simplified)

```yaml
# AI Asset
AIAsset:
  id: string (UUID)
  type: enum [model, agent, dataset, pipeline, vendor, endpoint]
  name: string
  owner: string
  lifecycle_stage: enum [development, testing, staging, production, retired]
  risk_tier: enum [prohibited, high, limited, minimal]
  business_purpose: string
  deployment_status: enum [deployed, pending, blocked]
  metadata: jsonb
  created_at: timestamp
  updated_at: timestamp

# Governance Decision
GovernanceDecision:
  id: string (UUID)
  asset_id: string (FK → AIAsset)
  decision: enum [ALLOW, ALLOW_WITH_REDACTION, REQUIRE_APPROVAL, DENY, QUARANTINE]
  policy_id: string (FK → Policy)
  evidence_hash: string (SHA-256)
  context: jsonb
  timestamp: timestamp

# Policy
Policy:
  id: string (UUID)
  name: string
  framework: enum [EU_AI_ACT, NIST_AI_RMF, ISO_42001, GDPR, SOC2, HIPAA, CUSTOM]
  version: string
  rules: jsonb (YAML-defined)
  created_at: timestamp
  updated_at: timestamp

# Evidence Record
EvidenceRecord:
  id: string (UUID)
  asset_id: string (FK → AIAsset)
  decision_id: string (FK → GovernanceDecision)
  record_type: enum [assessment, enforcement, monitoring, audit]
  data: jsonb
  hash_chain: string (SHA-256 of previous record + this record)
  timestamp: timestamp
```

### 3.6 Workflow Designs

#### Workflow 1: New AI System Onboarding
```
1. Discovery Engine detects new AI system
2. Inventory Graph creates asset record
3. Risk Assessment Engine runs initial assessment
4. Policy Mapping Engine maps applicable frameworks
5. Governance team reviews and approves
6. Runtime Enforcement Engine activates monitoring
7. Continuous Monitoring begins
```

#### Workflow 2: Runtime Violation Response
```
1. Sentinel Agent detects policy violation
2. Risk score exceeds threshold
3. If confidence > 0.90: Operative Agent auto-remediates
4. If confidence < 0.85: Route to human reviewer
5. Governance Decision Engine records decision
6. Evidence Ledger captures full context
7. Alert sent to governance team
```

#### Workflow 3: Regulatory Change Response
```
1. Regulatory Change Monitor detects new regulation
2. Policy Mapping Engine identifies affected assets
3. Gap Analysis Engine assesses compliance impact
4. Governance team reviews gap report
5. Policy updates are version-controlled and deployed
6. Affected assets are re-assessed
7. Evidence Ledger records the change trail
```

#### Workflow 4: Audit Evidence Generation
```
1. Auditor requests evidence for specific framework
2. Evidence Engine queries Evidence Ledger
3. Report Generator compiles relevant records
4. Chain of custody is verified
5. Evidence pack is exported (PDF/HTML)
6. AI Trust Center updates public posture
```

### 3.7 Implementation Roadmap

#### Phase 1: Foundation (Months 1-3)
- [ ] Core data model and API
- [ ] Discovery Engine (repository scanning)
- [ ] Inventory Graph (basic)
- [ ] Policy Engine (OPA integration)
- [ ] MCP Gateway (basic)

#### Phase 2: Assessment (Months 4-6)
- [ ] Risk Assessment Engine
- [ ] Policy Mapping Engine (EU AI Act, NIST, ISO 42001)
- [ ] Evidence Ledger
- [ ] Reporting Module

#### Phase 3: Enforcement (Months 7-9)
- [ ] Runtime Enforcement Engine (5-way decisions)
- [ ] Approval Workflow
- [ ] Continuous Monitoring
- [ ] Alert Routing

#### Phase 4: Intelligence (Months 10-12)
- [ ] Sentinel/Operative Agent separation
- [ ] Governance Knowledge Graph
- [ ] Agent Governance Layer
- [ ] AI Trust Center

### 3.8 Key Differentiators from Existing Solutions

1. **Only open-source platform with deterministic runtime enforcement** — WhitePact has this but lacks discovery/inventory; GRC_Claw combines both
2. **Only platform with full lifecycle coverage** — VerifyWise is close but lacks runtime enforcement; GRC_Claw adds this
3. **Only platform with policy-to-code compiler** — Credo AI has policy packs but they're proprietary; GRC_Claw uses open YAML definitions
4. **Only platform with cross-framework control mapping** — Implement once, get credit across multiple frameworks
5. **Only platform with MCP-native architecture** — Governance is embedded in the AI workflow, not bolted on

---

## Part 4: Competitive Positioning

### GRC_Claw vs. Commercial Platforms

| Capability | GRC_Claw | Credo AI | Holistic AI | IBM watsonx | OneTrust |
|------------|----------|----------|-------------|-------------|----------|
| Open source | ✅ | ❌ | ❌ | ❌ | ❌ |
| Self-hosted | ✅ | ❌ | ❌ | ✅ | ❌ |
| Full lifecycle | ✅ | ✅ | ✅ | ✅ | ✅ |
| Runtime enforcement | ✅ | ✅ | ✅ | ✅ | ✅ |
| Deterministic decisions | ✅ | ❌ | ❌ | ❌ | ❌ |
| MCP-native | ✅ | ❌ | ❌ | ❌ | ✅ |
| Agentic governance | ✅ | ✅ | ✅ | ✅ | ✅ |
| No vendor lock-in | ✅ | ❌ | ❌ | ❌ | ❌ |
| Community-driven | ✅ | ❌ | ❌ | ❌ | ❌ |

### GRC_Claw vs. Open-Source Platforms

| Capability | GRC_Claw | VerifyWise | Vigil | WhitePact | AIBOM-Guard |
|------------|----------|------------|-------|-----------|-------------|
| Full lifecycle | ✅ | ✅ | ❌ | ❌ | ❌ |
| Runtime enforcement | ✅ | ❌ | ✅ | ✅ | ❌ |
| Discovery/Inventory | ✅ | ✅ | ✅ | ❌ | ✅ |
| AI-BOM generation | ✅ | ❌ | ❌ | ❌ | ✅ |
| Agentic SOC | ✅ | ❌ | ✅ | ❌ | ❌ |
| Policy-to-code | ✅ | ❌ | ❌ | ✅ | ❌ |
| Audit evidence | ✅ | ✅ | ✅ | ✅ | ✅ |
| MCP server | ✅ | ❌ | ✅ | ✅ | ✅ |

---

## Part 5: Recommendation

**Build GRC_Claw as an open-source automation engine** that combines:
- **AIBOM-Guard's** scanning and AI-BOM generation (discovery)
- **VerifyWise's** full-lifecycle workflow (inventory → assessment → governance → monitoring)
- **WhitePact's** deterministic 5-way enforcement (runtime)
- **Vigil's** agentic SOC pattern (Sentinel/Operative agents)
- **Credo AI's** knowledge graph (contextual governance)
- **OneTrust's** evidence ledger (audit-ready evidence)

The engine should be:
1. **MCP-native** — governance embedded in AI workflows via MCP
2. **Deterministic** — no LLM in the enforcement decision path
3. **Policy-as-code** — version-controlled YAML definitions
4. **Evidence-first** — continuous audit readiness
5. **Graph-based** — dependency mapping via graph database
6. **Agent-separated** — detection and enforcement by different agents

This fills the identified gap: **no existing open-source tool provides end-to-end automation from discovery through runtime enforcement to audit evidence**. GRC_Claw can become the standard open-source AI governance automation engine.
