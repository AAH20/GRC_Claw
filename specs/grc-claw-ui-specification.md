# GRC_Claw User Interface Specification

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**Stakeholders:** CISO, GRC Analysts, Auditors, Platform Engineers, AI/ML Engineers

---

## 1. Purpose & Scope

This specification defines the user interface for GRC_Claw — the open-source, agent-native governance chassis. It addresses the industry gap where no standard UI patterns exist for AI governance dashboards, policy management, evidence review, or compliance mapping.

**In scope:** All user-facing interfaces for governance operations, including dashboards, policy management, evidence viewing, assessment workflows, compliance mapping, and alerting.

**Out of scope:** CLI interfaces, MCP protocol internals, API specifications, collector agent UIs.

---

## 2. Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Governance is for everyone** | CISOs, engineers, and auditors all need different views of the same data |
| **Evidence-first** | Every claim must be traceable to evidence — no "trust me" dashboards |
| **Deterministic clarity** | Governance decisions are deterministic; the UI must reflect that precision |
| **Progressive disclosure** | Summary → detail → raw evidence; never overwhelm, never hide |
| **Audit-ready by default** | Every view should be exportable for auditor consumption |
| **Agent-native** | AI agents are first-class citizens — their governance is as important as human governance |

---

## 3. User Roles & Permissions

### 3.1 Role Definitions

| Role | Description | Primary Use Case |
|------|-------------|------------------|
| **Executive** | CISO, CIO, VP Engineering, Board members | Strategic posture, risk trends, audit readiness |
| **GRC Analyst** | Compliance managers, risk analysts, GRC specialists | Day-to-day governance operations, evidence review, finding management |
| **Auditor** | Internal/external auditors, assessors | Evidence verification, control testing, attestation review |
| **Platform Engineer** | DevOps, SRE, infrastructure teams | Technical control status, agent registry, runtime enforcement |
| **AI/ML Engineer** | Data scientists, ML engineers, AI developers | Model/agent governance, risk assessment, policy compliance |
| **Policy Owner** | Legal, compliance leads, policy authors | Policy authoring, version management, approval workflows |
| **Approver** | Managers, team leads with approval authority | Approval workflows, exception grants, risk acceptance |
| **Read-Only** | Stakeholders, executives (view-only), auditors (limited) | Dashboard viewing, report access, posture review |

### 3.2 Permission Matrix

| Capability | Executive | GRC Analyst | Auditor | Platform Engineer | AI/ML Engineer | Policy Owner | Approver | Read-Only |
|------------|-----------|-------------|---------|-------------------|----------------|--------------|----------|-----------|
| View executive dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View operational dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View technical dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View evidence | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Upload evidence | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Verify evidence | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Attest evidence (L4) | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Manage policies | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Approve policies | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Run assessments | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manage findings | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Approve exceptions | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Configure alerts | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Manage agent registry | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Export evidence packages | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Manage users/roles | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| View audit trail | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Access API keys | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |

### 3.3 Data Scoping

- **Organization-scoped:** All users see data within their organization boundary
- **Framework-scoped:** Users can be limited to specific compliance frameworks (e.g., SOC 2 only)
- **Asset-scoped:** Users can be limited to specific AI assets, agents, or business units
- **Environment-scoped:** Users can be limited to specific environments (prod, staging, dev)

---

## 4. Dashboard Designs

### 4.1 Executive Dashboard

**Purpose:** Strategic governance posture for leadership — "Are we compliant? Are we ready for audit? What's our risk trend?"

**Target users:** Executive, Read-Only

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GRC_Claw Executive Dashboard                    [Org Selector] [Time Range] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Compliance  │  │   Risk       │  │   Audit      │  │   Agent      │   │
│  │  Score       │  │   Posture    │  │   Readiness  │  │   Coverage   │   │
│  │              │  │              │  │              │  │              │   │
│  │    87/100    │  │   Medium     │  │    92%       │  │   45/50      │   │
│  │   ▲ 3 pts    │  │   ▼ Low      │  │   Ready      │  │   90%        │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │  Compliance Score by Framework  │  │  Risk Trend (90 days)           │  │
│  │                                 │  │                                 │  │
│  │  SOC 2    ████████████░░  92%   │  │  High ───╲                      │  │
│  │  ISO 27001 ██████████░░░  85%   │  │  Med  ─────╲────╲               │  │
│  │  NIST AI  █████████░░░░  78%    │  │  Low  ──────────╲────           │  │
│  │  EU AI Act ████████░░░░░  71%    │  │                                 │  │
│  │  HIPAA    █████████████  95%    │  │  ──────────────────────         │  │
│  └─────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │  Top 5 Open Findings            │  │  Upcoming Audit Milestones      │  │
│  │                                 │  │                                 │  │
│  │  1. [HIGH] AC-2.1 Agent creds   │  │  • SOC 2 Type II — 45 days      │  │
│  │  2. [HIGH] AU-6.1 Log gap       │  │  • ISO 27001 surveillance — 90d │  │
│  │  3. [MED]  AU-9.4 Evidence gap  │  │  • EU AI Act report — 120 days  │  │
│  │  4. [MED]  AC-5.1 Segregation   │  │  • Internal audit — 30 days     │  │
│  │  5. [LOW]  AU-12.1 Log review   │  │                                 │  │
│  └─────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Agent Trust Score Distribution                                      │   │
│  │  A (90-100): 12 agents  ████████                                    │   │
│  │  B (80-89):  18 agents  ████████████                                │   │
│  │  C (70-79):  8 agents   ██████                                      │   │
│  │  D (60-69):  4 agents   ███                                         │   │
│  │  F (<60):     3 agents   ██                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Widget Specifications

| Widget | Data Source | Refresh | Drill-Down |
|--------|-------------|---------|------------|
| Compliance Score | Aggregated control status across all frameworks | Real-time | → Framework detail → Control detail |
| Risk Posture | Risk register summary (open risks by severity) | Real-time | → Risk register → Risk detail |
| Audit Readiness | Evidence completeness + verification levels | Hourly | → Evidence gaps by framework |
| Agent Coverage | Agents with active governance / total agents | Real-time | → Agent registry → Agent detail |
| Framework Scores | Per-framework compliance percentage | Real-time | → Compliance mapping viewer |
| Risk Trend | 90-day risk score time series | Daily | → Risk trend detail |
| Open Findings | Top findings by severity, age | Real-time | → Finding detail → Evidence |
| Audit Milestones | Upcoming audit dates and readiness | Daily | → Audit preparation checklist |
| Trust Distribution | Agent trust score histogram | Real-time | → Agent list filtered by grade |

#### Interactions

- **Time range selector:** 7d / 30d / 90d / 12m / custom
- **Framework filter:** Toggle frameworks on/off
- **Export:** PDF report generation for board distribution
- **Click-through:** Every widget drills down to operational detail

---

### 4.2 Operational Dashboard

**Purpose:** Day-to-day governance operations — findings, evidence review, assessment tracking, alert management.

**Target users:** GRC Analyst, Platform Engineer, AI/ML Engineer

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GRC_Claw Operational Dashboard        [Search] [Filters ▼] [+ New Finding] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ALERTS & NOTIFICATIONS                    [Mark All Read] [Settings] │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │ 🔴 CRITICAL  Agent 'prod-customer-bot' trust score dropped to F  │ │   │
│  │  │ 🟠 HIGH      Evidence for AC-2.1 expired (3 agents affected)     │ │   │
│  │  │ 🟡 MEDIUM    New policy 'EU-AI-Act-v2' requires review           │ │   │
│  │  │ 🟢 LOW       Weekly evidence package generated successfully      │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────┐ │
│  │  OPEN FINDINGS               │  │  EVIDENCE STATUS                    │ │
│  │                              │  │                                      │ │
│  │  Critical:  3  [View →]     │  │  L0 Unverified:    12  [Review →]   │ │
│  │  High:      8  [View →]     │  │  L1 Schema-valid:  45               │ │
│  │  Medium:   15  [View →]     │  │  L2 Integrity:    120               │ │
│  │  Low:      22  [View →]     │  │  L3 Cross-val:     20               │ │
│  │                              │  │  L4 Attested:       6  [Attest →]   │ │
│  │  [+ Create Finding]          │  │                                      │ │
│  └──────────────────────────────┘  └──────────────────────────────────────┘ │
│                                                                             │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────┐ │
│  │  ACTIVE ASSESSMENTS          │  │  AGENT GOVERNANCE STATUS             │ │
│  │                              │  │                                      │ │
│  │  SOC 2 Type II    68% ████░  │  │  Governed:     42 agents             │ │
│  │  ISO 27001        45% ███░░  │  │  Ungoverned:    5 agents  [Review]  │ │
│  │  EU AI Act        30% ██░░░  │  │  Quarantined:   2 agents  [Review]  │ │
│  │  NIST AI RMF      80% █████  │  │  Pending:       1 agent              │ │
│  │                              │  │                                      │ │
│  │  [View All Assessments →]    │  │  [View Agent Registry →]             │ │
│  └──────────────────────────────┘  └──────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RECENT GOVERNANCE ACTIVITY                                          │   │
│  │  ┌──────────┬────────────┬──────────────┬──────────┬──────────────┐  │   │
│  │  │ Time     │ Actor      │ Action       │ Target   │ Outcome      │  │   │
│  │  ├──────────┼────────────┼──────────────┼──────────┼──────────────┤  │   │
│  │  │ 09:42    │ agent-sent │ Policy eval  │ prod-bot │ ALLOW        │  │   │
│  │  │ 09:38    │ analyst-jd │ Evidence upl │ AC-2.1   │ L2 verified  │  │   │
│  │  │ 09:15    │ system     │ Scan complete│ AU-6     │ 3 findings   │  │   │
│  │  │ 08:50    │ auditor-ex  │ Attestation  │ CC6.1    │ L4 attested  │  │   │
│  │  │ 08:30    │ agent-sent │ Tool call    │ prod-bot │ DENIED       │  │   │
│  │  └──────────┴────────────┴──────────────┴──────────┴──────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Widget Specifications

| Widget | Data Source | Refresh | Actions |
|--------|-------------|---------|---------|
| Alerts & Notifications | Alert engine, policy violations, trust score changes | Real-time | Acknowledge, dismiss, escalate, configure |
| Open Findings | Finding management system | Real-time | Create, assign, update status, link evidence |
| Evidence Status | Evidence store verification levels | Hourly | Review, verify, attest, export |
| Active Assessments | Assessment workflow engine | Real-time | View progress, add evidence, update status |
| Agent Governance Status | Agent registry + trust scoring | Real-time | View agent detail, quarantine, update policy |
| Recent Activity | Audit trail (Merkle-chained) | Real-time | View detail, verify integrity, export |

---

### 4.3 Technical Dashboard

**Purpose:** Deep technical view for engineers — agent registry, runtime enforcement, policy evaluation, control implementation status.

**Target users:** Platform Engineer, AI/ML Engineer

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GRC_Claw Technical Dashboard              [Env ▼] [Agent ▼] [Time Range ▼] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  AGENT REGISTRY                                                      │   │
│  │  ┌──────────────┬────────┬─────────┬──────────┬─────────┬─────────┐  │   │
│  │  │ Agent ID     │ Trust  │ Status  │ Policy   │ Last    │ Actions │  │   │
│  │  │              │ Score  │         │ Bundle   │ Eval    │         │  │   │
│  │  ├──────────────┼────────┼─────────┼──────────┼─────────┼─────────┤  │   │
│  │  │ prod-cs-bot  │ A (94) │ Active  │ v2.3.1   │ 2m ago  │ [View]  │  │   │
│  │  │ prod-sales   │ B (82) │ Active  │ v2.3.1   │ 5m ago  │ [View]  │  │   │
│  │  │ staging-ml   │ C (71) │ Active  │ v2.2.0   │ 1h ago  │ [View]  │  │   │
│  │  │ dev-experiment│ F (45) │ Quar.   │ v2.1.0   │ 3h ago  │ [View]  │  │   │
│  │  │ prod-finance │ A (97) │ Active  │ v2.3.1   │ 1m ago  │ [View]  │  │   │
│  │  └──────────────┴────────┴─────────┴──────────┴─────────┴─────────┘  │   │
│  │  [+ Register Agent]  [Bulk Import]  [Export]                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────┐ │
│  │  RUNTIME ENFORCEMENT         │  │  POLICY EVALUATION LOG              │ │
│  │                              │  │                                      │ │
│  │  Decisions (24h):            │  │  Recent evaluations:                 │ │
│  │  ALLOW:          1,247       │  │                                      │ │
│  │  DENY:              12       │  │  09:42 prod-cs-bot → ALLOW          │ │
│  │  REQUIRE_APPROVAL:   3       │  │    Policy: cs-bot-policy v2.3.1     │ │
│  │  QUARANTINE:         1       │  │    Rule: allow-read-tickets         │ │
│  │  TRANSFORM:           0       │  │                                      │ │
│  │                              │  │  09:38 prod-sales → DENY             │ │
│  │  [View Enforcement Detail →] │  │    Policy: sales-policy v2.3.1       │ │
│  │                              │  │    Rule: block-refund-over-500       │ │
│  └──────────────────────────────┘  │    Reason: amount > $500            │ │
│                                    │                                      │ │
│                                    │  [View Full Log →]                   │ │
│                                    └──────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CONTROL IMPLEMENTATION STATUS                                       │   │
│  │  ┌──────────────┬────────────┬──────────┬──────────┬──────────────┐  │   │
│  │  │ Control ID   │ Framework  │ Status   │ Evidence │ Last Check   │  │   │
│  │  ├──────────────┼────────────┼──────────┼──────────┼──────────────┤  │   │
│  │  │ AC-2.1       │ NIST 800-53│ ✅ Pass  │ 3 items  │ 2h ago       │  │   │
│  │  │ AU-6.1       │ NIST 800-53│ ⚠️ Gap   │ 1 item   │ 1d ago       │  │   │
│  │  │ CC6.1        │ SOC 2      │ ✅ Pass  │ 5 items  │ 4h ago       │  │   │
│  │  │ A.12.4       │ ISO 27001  │ ✅ Pass  │ 2 items  │ 6h ago       │  │   │
│  │  │ AU-9.4       │ NIST 800-53│ ❌ Fail  │ 0 items  │ 7d ago       │  │   │
│  │  └──────────────┴────────────┴──────────┴──────────┴──────────────┘  │   │
│  │  [View Control Detail]  [Run Assessment]  [Export]                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────┐ │
│  │  TRUST SCORE COMPONENTS      │  │  POLICY BUNDLE VERSIONS             │ │
│  │                              │  │                                      │ │
│  │  prod-cs-bot (A - 94):       │  │  v2.3.1: 38 agents  [Current]       │ │
│  │  Identity:     20/20 ████████ │  │  v2.3.0:  5 agents  [Deprecated]   │ │
│  │  Behavior:     18/20 ███████░ │  │  v2.2.0:  2 agents  [Deprecated]   │ │
│  │  Compliance:   19/20 ███████░ │  │                                      │ │
│  │  Attestation:  17/20 ██████░░ │  │  [View Policy Detail →]             │ │
│  │  Evidence:     20/20 ████████ │  │  [Create New Version →]             │ │
│  │                              │  │                                      │ │
│  │  [View Trust Detail →]       │  │                                      │ │
│  └──────────────────────────────┘  └──────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Widget Specifications

| Widget | Data Source | Refresh | Actions |
|--------|-------------|---------|---------|
| Agent Registry | Agent registry + identity system | Real-time | Register, view detail, quarantine, update policy |
| Runtime Enforcement | Enforcement engine decision log | Real-time | View detail, override (with approval), export |
| Policy Evaluation Log | Policy engine evaluation records | Real-time | View detail, trace to evidence, export |
| Control Implementation | Control status + evidence mapping | Hourly | View detail, run assessment, add evidence |
| Trust Score Components | Trust scoring engine | Real-time | View component breakdown, history |
| Policy Bundle Versions | Policy version management | On change | View diff, rollback, create new version |

---

## 5. Policy Management Interface

### 5.1 Policy List View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Policy Management                              [+ New Policy] [Import]      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Search: [________________]  Framework: [All ▼]  Status: [All ▼]           │
│                                                                             │
│  ┌──────────────┬──────────────┬─────────┬──────────┬──────────┬─────────┐  │
│  │ Policy Name  │ Framework    │ Version │ Status   │ Owner    │ Actions │  │
│  ├──────────────┼──────────────┼─────────┼──────────┼──────────┼─────────┤  │
│  │ org-baseline │ All          │ v3.1.0  │ ✅ Active │ CISO     │ [Edit]  │  │
│  │ platform-sh  │ All          │ v2.3.1  │ ✅ Active │ Platform │ [Edit]  │  │
│  │ cs-bot-pol   │ SOC 2        │ v2.3.1  │ ✅ Active │ CS Team  │ [Edit]  │  │
│  │ sales-pol    │ SOC 2        │ v2.3.1  │ ✅ Active │ Sales    │ [Edit]  │  │
│  │ eu-ai-act    │ EU AI Act    │ v1.0.0  │ 📝 Draft │ Legal    │ [Edit]  │  │
│  │ hipaa-base   │ HIPAA        │ v2.0.0  │ ✅ Active │ Compliance│ [Edit] │  │
│  └──────────────┴──────────────┴─────────┴──────────┴──────────┴─────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Policy Editor

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Policy Editor: org-baseline v3.1.0                    [Save] [Validate]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Metadata ──────────────────────────────────────────────────────────┐   │
│  │  Name: [org-baseline          ]  Version: [3.1.0    ]              │   │
│  │  Framework: [All ▼]  Owner: [CISO ▼]  Status: [Active ▼]          │   │
│  │  Description: [Organization-wide non-negotiable controls        ]  │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Policy Rules (YAML) ───────────────────────────────────────────────┐   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │ apiVersion: governance.toolkit/v1                              │ │   │
│  │  │ name: org-baseline                                            │ │   │
│  │  │ default_action: deny                                          │ │   │
│  │  │ on_timeout: deny                                              │ │   │
│  │  │ rules:                                                        │ │   │
│  │  │   - name: block-pii-export                                   │ │   │
│  │  │     condition: "action.type == 'export' && data.contains_pii"│ │   │
│  │  │     action: deny                                              │ │   │
│  │  │     priority: 1000                                            │ │   │
│  │  │     description: "PII data must never leave the system"      │ │   │
│  │  │   - name: block-credential-access                            │ │   │
│  │  │     condition: "action.type == 'read' && resource.type ==    │ │   │
│  │  │                'credentials'"                                 │ │   │
│  │  │     action: deny                                              │ │   │
│  │  │     priority: 1000                                            │ │   │
│  │  │   - name: audit-everything                                   │ │   │
│  │  │     condition: "true"                                         │ │   │
│  │  │     action: log                                               │ │   │
│  │  │     priority: 0                                               │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  │  [+ Add Rule]  [Test Policy]  [View Evaluation Log]                │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Inheritance ──────────────────────────────────────────────────────┐   │
│  │  Inherits from: [None ▼]                                          │   │
│  │  Inherited by: platform-shared, cs-bot-policy, sales-policy       │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Version History ──────────────────────────────────────────────────┐   │
│  │  v3.1.0 (Current) — 2026-10-01 — Added audit-everything rule     │   │
│  │  v3.0.0 — 2026-09-15 — Added credential access blocking           │   │
│  │  v2.0.0 — 2026-08-01 — Initial org baseline                       │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Policy Test Console

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Policy Test Console: org-baseline v3.1.0                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Test Input (JSON):                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ {                                                                   │   │
│  │   "action": {                                                       │   │
│  │     "type": "export",                                               │   │
│  │     "data": { "contains_pii": true }                                │   │
│  │   },                                                                │   │
│  │   "agent_id": "prod-cs-bot",                                        │   │
│  │   "resource": { "type": "database" }                                │   │
│  │ }                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [Run Test]                                                                 │
│                                                                             │
│  Result:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Decision: DENY                                                     │   │
│  │  Matched Rule: block-pii-export (priority: 1000)                    │   │
│  │  Reason: "PII data must never leave the system"                     │   │
│  │  Evaluation Time: 0.08ms                                            │   │
│  │  Policy Version: v3.1.0                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Evidence Viewer

### 6.1 Evidence List View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Evidence Viewer                                    [+ Upload] [Export]      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Search: [________________]  Control: [All ▼]  Type: [All ▼]               │
│  Verification: [All ▼]  Date: [Last 30 days ▼]                             │
│                                                                             │
│  ┌──────────────┬────────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ Evidence ID  │ Control    │ Type     │ Verif.   │ Collected│ Actions  │  │
│  ├──────────────┼────────────┼──────────┼──────────┼──────────┼──────────┤  │
│  │ ev-001       │ AC-2.1     │ artifact │ L4 ✅    │ 2h ago   │ [View]   │  │
│  │ ev-002       │ AU-6.1     │ log      │ L2 ✅    │ 4h ago   │ [View]   │  │
│  │ ev-003       │ CC6.1      │ observ.  │ L3 ✅    │ 6h ago   │ [View]   │  │
│  │ ev-004       │ AC-2.1     │ artifact │ L1 ⚠️    │ 1d ago   │ [View]   │  │
│  │ ev-005       │ AU-9.4     │ analysis │ L0 ❌    │ 2d ago   │ [View]   │  │
│  └──────────────┴────────────┴──────────┴──────────┴──────────┴──────────┘  │
│                                                                             │
│  Verification Legend:                                                       │
│  L0 Unverified | L1 Schema-valid | L2 Integrity-verified |                   │
│  L3 Cross-validated | L4 Attested                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Evidence Detail View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Evidence Detail: ev-001                                    [Verify] [Attest]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Metadata ──────────────────────────────────────────────────────────┐   │
│  │  Evidence ID:    ev-001                                             │   │
│  │  Control:        AC-2.1 (Account Management)                        │   │
│  │  Framework:      NIST 800-53 Rev 5                                  │   │
│  │  Type:           artifact                                           │   │
│  │  Verification:   L4 ✅ Attested                                     │   │
│  │  Collected by:   agent-sentinel-01                                  │   │
│  │  Collected at:   2026-10-01T09:30:00Z                              │   │
│  │  Source system:  AWS IAM                                            │   │
│  │  Environment:    production                                         │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Content ───────────────────────────────────────────────────────────┐   │
│  │  Format: application/json                                            │   │
│  │  Size: 2.4 KB                                                       │   │
│  │  SHA-256: a3f2b8c9d1e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6  │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ {                                                               ││   │
│  │  │   "agent_id": "prod-cs-bot",                                    ││   │
│  │  │   "iam_role": "cs-bot-role",                                    ││   │
│  │  │   "mfa_enabled": true,                                          ││   │
│  │  │   "last_access_review": "2026-09-15",                           ││   │
│  │  │   "permissions": ["read:tickets", "write:responses"],           ││   │
│  │  │   "credential_rotation_days": 30                                ││   │
│  │  │ }                                                               ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │  [View Raw]  [Download]  [Copy Hash]                                │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Chain of Custody ─────────────────────────────────────────────────┐   │
│  │  ┌──────────┬────────────┬──────────────┬──────────┬──────────────┐ │   │
│  │  │ Time     │ Action     │ Actor        │ Hash     │ Signature    │ │   │
│  │  ├──────────┼────────────┼──────────────┼──────────┼──────────────┤ │   │
│  │  │ 09:30:00 │ collected  │ agent-sent-01│ a3f2b8.. │ ✅ Valid     │ │   │
│  │  │ 09:31:00 │ verified   │ system       │ b7c9d1.. │ ✅ Valid     │ │   │
│  │  │ 09:45:00 │ attested   │ auditor-ext   │ e4f5a6.. │ ✅ Valid     │ │   │
│  │  └──────────┴────────────┴──────────────┴──────────┴──────────────┘ │   │
│  │  [Verify Chain Integrity]                                           │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Cross-References ─────────────────────────────────────────────────┐   │
│  │  Related Evidence:                                                  │   │
│  │  • ev-004 (AC-2.1, L1) — Previous configuration snapshot           │   │
│  │  • ev-012 (AC-2.2, L4) — Related access review evidence            │   │
│  │                                                                     │   │
│  │  Mapped Controls:                                                   │   │
│  │  • NIST 800-53: AC-2.1, AC-2.2, AC-2.3                             │   │
│  │  • SOC 2: CC6.1, CC6.2                                              │   │
│  │  • ISO 27001: A.9.1.2, A.9.2.1                                     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Evidence Package Export

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Export Evidence Package                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Assessment Period: [2026-07-01] to [2026-10-01]                           │
│  Frameworks: [✓] NIST 800-53  [✓] SOC 2  [ ] ISO 27001  [ ] EU AI Act     │
│                                                                             │
│  Controls: [All ▼]  Evidence Types: [All ▼]  Verification: [L2+ ▼]        │
│                                                                             │
│  Format:  (•) JSON (OSCAL)  ( ) PDF  ( ) CSV  ( ) XML                      │
│                                                                             │
│  Package Contents:                                                          │
│  ✓ Evidence items (156 items, 2.4 MB)                                      │
│  ✓ Chain of custody log                                                    │
│  ✓ Assessment plan (OSCAL)                                                 │
│  ✓ Assessment results (OSCAL)                                              │
│  ✓ Digital signatures + timestamp                                          │
│                                                                             │
│  Estimated size: 3.1 MB                                                     │
│                                                                             │
│  [Generate Package]  [Schedule Recurring Export]                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Assessment Workflow UI

### 7.1 Assessment List View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Assessments                                    [+ New Assessment]           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┬──────────────┬─────────┬──────────┬──────────┬─────────┐  │
│  │ Assessment   │ Framework    │ Progress│ Status   │ Due Date │ Actions │  │
│  ├──────────────┼──────────────┼─────────┼──────────┼──────────┼─────────┤  │
│  │ SOC 2 T-II   │ SOC 2        │ 68% ████│ Active   │ 45 days  │ [View]  │  │
│  │ ISO 27001    │ ISO 27001    │ 45% ███░│ Active   │ 90 days  │ [View]  │  │
│  │ EU AI Act    │ EU AI Act    │ 30% ██░░│ Active   │ 120 days │ [View]  │  │
│  │ NIST AI RMF  │ NIST AI RMF  │ 80% ████│ Active   │ 30 days  │ [View]  │  │
│  │ HIPAA 2025   │ HIPAA        │ 100% ███│ Complete  │ —        │ [View]  │  │
│  └──────────────┴──────────────┴─────────┴──────────┴──────────┴─────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Assessment Detail View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Assessment: SOC 2 Type II                              [Export] [Close]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Summary ───────────────────────────────────────────────────────────┐   │
│  │  Framework: SOC 2 Type II  |  Period: 2026-07-01 to 2026-10-01      │   │
│  │  Progress: 68% complete  |  Controls: 42/62 assessed                │   │
│  │  Evidence: 156 items  |  Findings: 8 open (2 critical, 3 high)     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Control Assessment Matrix ─────────────────────────────────────────┐   │
│  │  ┌──────────────┬────────────┬──────────┬──────────┬──────────────┐  │   │
│  │  │ Control ID   │ Control    │ Status   │ Evidence │ Last Review  │  │   │
│  │  ├──────────────┼────────────┼──────────┼──────────┼──────────────┤  │   │
│  │  │ CC6.1        │ Logical    │ ✅ Pass  │ 5 items  │ 2h ago       │  │   │
│  │  │ CC6.2        │ Access     │ ✅ Pass  │ 3 items  │ 4h ago       │  │   │
│  │  │ CC6.3        │ Access     │ ⚠️ Gap   │ 1 item   │ 1d ago       │  │   │
│  │  │ CC7.1        │ Monitoring │ ✅ Pass  │ 4 items  │ 6h ago       │  │   │
│  │  │ CC7.2        │ Monitoring │ ❌ Fail  │ 0 items  │ 7d ago       │  │   │
│  │  │ CC7.3        │ Monitoring │ 📝 Pend  │ 0 items  │ —            │  │   │
│  │  └──────────────┴────────────┴──────────┴──────────┴──────────────┘  │   │
│  │                                                                     │   │
│  │  Status: ✅ Pass | ⚠️ Gap | ❌ Fail | 📝 Pending                    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Findings ──────────────────────────────────────────────────────────┐   │
│  │  ┌──────────┬────────────┬──────────┬──────────┬──────────────────┐  │   │
│  │  │ Finding  │ Severity   │ Status   │ Owner    │ Due Date         │  │   │
│  │  ├──────────┼────────────┼──────────┼──────────┼──────────────────┤  │   │
│  │  │ F-001    │ Critical   │ Open     │ Platform │ 2026-10-08       │  │   │
│  │  │ F-002    │ High       │ Open     │ Security │ 2026-10-15       │  │   │
│  │  │ F-003    │ Medium     │ In Prog  │ CS Team  │ 2026-10-22       │  │   │
│  │  └──────────┴────────────┴──────────┴──────────┴──────────────────┘  │   │
│  │  [+ Add Finding]  [View All Findings →]                              │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Evidence Collection ───────────────────────────────────────────────┐   │
│  │  ┌──────────────┬────────────┬──────────┬──────────┬──────────────┐  │   │
│  │  │ Control      │ Required   │ Collected│ Verified │ Status       │  │   │
│  │  ├──────────────┼────────────┼──────────┼──────────┼──────────────┤  │   │
│  │  │ CC6.1        │ 3          │ 5        │ 5        │ ✅ Complete  │  │   │
│  │  │ CC6.2        │ 2          │ 3        │ 3        │ ✅ Complete  │  │   │
│  │  │ CC6.3        │ 2          │ 1        │ 1        │ ⚠️ Insuff.   │  │   │
│  │  │ CC7.2        │ 3          │ 0        │ 0        │ ❌ Missing   │  │   │
│  │  └──────────────┴────────────┴──────────┴──────────┴──────────────┘  │   │
│  │  [Request Evidence]  [Upload Evidence]  [Run Auto-Collection]       │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Finding Detail View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Finding: F-001                                            [Edit] [Close]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Finding Details ───────────────────────────────────────────────────┐   │
│  │  Title: Agent credential rotation non-compliant                      │   │
│  │  Severity: 🔴 Critical  |  Status: Open  |  Assigned: Platform Team │   │
│  │  Control: CC6.1 (Logical and Physical Access Controls)               │   │
│  │  Framework: SOC 2 Type II                                            │   │
│  │  Identified: 2026-09-15  |  Due: 2026-10-08                         │   │
│  │  Description:                                                        │   │
│  │  Agent 'prod-sales-bot' has not rotated credentials in 90 days.      │   │
│  │  Policy requires 30-day rotation. Evidence shows last rotation       │   │
│  │  was 2026-06-15 (108 days ago).                                     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Affected Assets ───────────────────────────────────────────────────┐   │
│  │  • prod-sales-bot (Agent) — Last rotation: 2026-06-15              │   │
│  │  • prod-cs-bot (Agent) — Last rotation: 2026-09-20 ✅              │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Evidence ──────────────────────────────────────────────────────────┐   │
│  │  • ev-001: IAM configuration snapshot (L4, attested)                 │   │
│  │  • ev-015: Credential rotation log (L2, verified)                   │   │
│  │  [View Evidence →]  [Add Evidence]                                  │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Remediation Plan ──────────────────────────────────────────────────┐   │
│  │  1. Rotate credentials for prod-sales-bot — Owner: Platform — Due: 10/02│
│  │  2. Update credential rotation policy to 30 days — Owner: Security — Due: 10/05│
│  │  3. Enable automatic rotation monitoring — Owner: Platform — Due: 10/08│
│  │  [+ Add Task]  [Update Status]                                       │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Activity Log ──────────────────────────────────────────────────────┐   │
│  │  2026-09-15 09:00 — Finding created by system (auto-detection)       │   │
│  │  2026-09-15 09:05 — Assigned to Platform Team by system              │   │
│  │  2026-09-16 14:30 — Status updated to "In Progress" by engineer-jd    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Compliance Mapping Viewer

### 8.1 Cross-Framework Mapping Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Compliance Mapping Viewer              [Framework ▼] [Control ▼] [Search]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  NIST 800-53 Control: AC-2.1 (Account Management)                   │   │
│  │  ┌──────────────┬────────────┬──────────┬──────────┬──────────────┐  │   │
│  │  │ Framework    │ Control    │ Status   │ Evidence │ Mapping      │  │   │
│  │  ├──────────────┼────────────┼──────────┼──────────┼──────────────┤  │   │
│  │  │ SOC 2        │ CC6.1      │ ✅ Pass  │ 5 items  │ Direct       │  │   │
│  │  │ ISO 27001    │ A.9.1.2    │ ✅ Pass  │ 3 items  │ Direct       │  │   │
│  │  │ HIPAA        │ 164.312(a) │ ✅ Pass  │ 2 items  │ Direct       │  │   │
│  │  │ EU AI Act    │ Art.9      │ ⚠️ Gap   │ 1 item   │ Partial      │  │   │
│  │  │ PCI DSS      │ 8.2        │ ✅ Pass  │ 4 items  │ Direct       │  │   │
│  │  │ CIS Controls │ 5.1        │ ✅ Pass  │ 2 items  │ Direct       │  │   │
│  │  └──────────────┴────────────┴──────────┴──────────┴──────────────┘  │   │
│  │                                                                     │   │
│  │  Mapping Type:                                                      │   │
│  │  • Direct — Same control objective across frameworks                 │   │
│  │  • Partial — Overlapping but not identical requirements              │   │
│  │  — No mapping exists                                                │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Coverage Summary ─────────────────────────────────────────────────┐   │
│  │  Framework        │ Controls │ Mapped │ Pass │ Gap │ Fail │ Score  │   │
│  │  ─────────────────┼──────────┼────────┼──────┼──────┼──────┼─────── │   │
│  │  NIST 800-53      │ 42      │ 42     │ 35   │ 5    │ 2    │ 83%    │   │
│  │  SOC 2            │ 62      │ 62     │ 42   │ 12   │ 8    │ 68%    │   │
│  │  ISO 27001        │ 33      │ 33     │ 15   │ 10   │ 8    │ 45%    │   │
│  │  EU AI Act        │ 28      │ 28     │ 8    │ 12   │ 8    │ 29%    │   │
│  │  HIPAA            │ 18      │ 18     │ 17   │ 1    │ 0    │ 94%    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [Export Mapping Report]  [View Unmapped Controls]  [Suggest Mappings]      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Control Detail with Cross-Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Control Detail: AC-2.1                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Control Definition ────────────────────────────────────────────────┐   │
│  │  Framework: NIST 800-53 Rev 5                                        │   │
│  │  Family: AC (Access Control)                                         │   │
│  │  Title: Account Management                                            │   │
│  │  Description: The organization manages information system accounts,  │   │
│  │  including establishing, activating, modifying, reviewing, disabling, │   │
│  │  and removing accounts.                                              │   │
│  │  Implementation Status: ✅ Implemented                                │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Cross-Framework Mappings ──────────────────────────────────────────┐   │
│  │  ┌──────────────┬────────────┬──────────┬──────────────────────────┐ │   │
│  │  │ Framework    │ Control    │ Type     │ Notes                    │ │   │
│  │  ├──────────────┼────────────┼──────────┼──────────────────────────┤ │   │
│  │  │ SOC 2        │ CC6.1      │ Direct   │ Logical access controls  │ │   │
│  │  │ ISO 27001    │ A.9.1.2    │ Direct   │ Access control policy    │ │   │
│  │  │ HIPAA        │ 164.312(a) │ Direct   │ Access control          │ │   │
│  │  │ EU AI Act    │ Art.9      │ Partial  │ Risk management         │ │   │
│  │  │ PCI DSS      │ 8.2        │ Direct   │ User identification     │ │   │
│  │  │ CIS Controls │ 5.1        │ Direct   │ Account management      │ │   │
│  │  └──────────────┴────────────┴──────────┴──────────────────────────┘ │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Evidence ──────────────────────────────────────────────────────────┐   │
│  │  ┌──────────────┬────────────┬──────────┬──────────┬──────────────┐  │   │
│  │  │ Evidence ID  │ Type       │ Verif.   │ Collected│ Source       │  │   │
│  │  ├──────────────┼────────────┼──────────┼──────────┼──────────────┤  │   │
│  │  │ ev-001       │ artifact   │ L4 ✅    │ 2h ago   │ AWS IAM      │  │   │
│  │  │ ev-004       │ artifact   │ L1 ⚠️    │ 1d ago   │ AWS IAM      │  │   │
│  │  │ ev-012       │ observ.    │ L3 ✅    │ 3h ago   │ Agent probe  │  │   │
│  │  └──────────────┴────────────┴──────────┴──────────┴──────────────┘  │   │
│  │  [View Evidence →]  [Upload Evidence]  [Request Collection]         │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Assessment History ────────────────────────────────────────────────┐   │
│  │  2026-10-01 — Automated assessment — ✅ Pass (3 evidence items)    │   │
│  │  2026-09-01 — Automated assessment — ✅ Pass (2 evidence items)    │   │
│  │  2026-08-01 — Manual assessment — ✅ Pass (auditor-ex attested)    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Alerting Interface

### 9.1 Alert Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Alert Configuration                                    [+ New Alert Rule]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Alert Rules ───────────────────────────────────────────────────────┐   │
│  │  ┌──────────────┬────────────┬──────────┬──────────┬──────────────┐  │   │
│  │  │ Rule Name    │ Trigger    │ Severity │ Channel   │ Status       │  │   │
│  │  ├──────────────┼────────────┼──────────┼──────────┼──────────────┤  │   │
│  │  │ Trust drop   │ Score < 60 │ Critical │ Email+Slack│ ✅ Active   │  │   │
│  │  │ Evidence exp │ > 7 days   │ High     │ Email     │ ✅ Active   │  │   │
│  │  │ Policy viol  │ Any deny   │ Medium   │ Slack     │ ✅ Active   │  │   │
│  │  │ Audit ready  │ < 30 days  │ Low      │ Email     │ ✅ Active   │  │   │
│  │  │ Agent unreg  │ > 24h      │ High     │ Email+Slack│ ⏸ Paused  │  │   │
│  │  └──────────────┴────────────┴──────────┴──────────┴──────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Create Alert Rule ─────────────────────────────────────────────────┐   │
│  │  Rule Name: [Trust score drop alert          ]                      │   │
│  │                                                                     │   │
│  │  Trigger Conditions:                                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ Metric: [Agent Trust Score ▼]                                   ││   │
│  │  │ Condition: [Less than ▼]  Value: [60]                           ││   │
│  │  │ Scope: [All Agents ▼]  Duration: [Immediate ▼]                  ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │                                                                     │   │
│  │  Severity:  (•) Critical  ( ) High  ( ) Medium  ( ) Low             │   │
│  │                                                                     │   │
│  │  Notification Channels:                                             │   │
│  │  [✓] Email    [✓] Slack    [ ] PagerDuty    [ ] Webhook             │   │
│  │                                                                     │   │
│  │  Email Recipients: [security-team@company.com, ciso@company.com]    │   │
│  │  Slack Channel:    [#grc-alerts]                                    │   │
│  │                                                                     │   │
│  │  Throttling: [Max 1 alert per 15 minutes ▼]                         │   │
│  │                                                                     │   │
│  │  [Save Rule]  [Test Rule]  [Cancel]                                 │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Alert Feed

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Alert Feed                                    [Mark All Read] [Settings]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Active Alerts ─────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  🔴 CRITICAL — 2m ago                                               │   │
│  │  Agent 'prod-customer-bot' trust score dropped to F (45)            │   │
│  │  Trigger: Trust score < 60  |  Affected: 1 agent                    │   │
│  │  [View Agent]  [Acknowledge]  [Escalate]  [Create Finding]          │   │
│  │                                                                     │   │
│  │  🟠 HIGH — 15m ago                                                  │   │
│  │  Evidence for AC-2.1 expired (3 agents affected)                    │   │
│  │  Trigger: Evidence age > 7 days  |  Affected: 3 agents              │   │
│  │  [View Evidence]  [Acknowledge]  [Request Re-collection]            │   │
│  │                                                                     │   │
│  │  🟡 MEDIUM — 1h ago                                                 │   │
│  │  New policy 'EU-AI-Act-v2' requires review                          │   │
│  │  Trigger: Policy draft created  |  Affected: All agents             │   │
│  │  [View Policy]  [Acknowledge]  [Assign Reviewer]                    │   │
│  │                                                                     │   │
│  │  🟢 LOW — 3h ago                                                    │   │
│  │  Weekly evidence package generated successfully                      │   │
│  │  Trigger: Scheduled export  |  Affected: —                          │   │
│  │  [View Package]  [Acknowledge]                                      │   │
│  │                                                                     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Alert Statistics (24h) ────────────────────────────────────────────┐   │
│  │  Critical: 1  |  High: 3  |  Medium: 7  |  Low: 12  |  Total: 23    │   │
│  │  MTTR: 4.2 hours  |  Acknowledged: 18/23  |  Escalated: 2           │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.3 Alert Detail

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Alert Detail: Trust Score Drop                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Alert Summary ─────────────────────────────────────────────────────┐   │
│  │  Severity: 🔴 Critical  |  Status: Active  |  Triggered: 2m ago      │   │
│  │  Rule: Trust score drop alert  |  Channel: Email + Slack              │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Affected Agent ────────────────────────────────────────────────────┐   │
│  │  Agent: prod-customer-bot                                            │   │
│  │  Trust Score: 45 (F) — Previous: 82 (B) — Drop: 37 points            │   │
│  │  Status: Quarantined  |  Last Evaluation: 2m ago                     │   │
│  │                                                                     │   │
│  │  Trust Score Components:                                            │   │
│  │  Identity:     18/20  ████████████████████░  (-2)                   │   │
│  │  Behavior:      8/20  ████████░░░░░░░░░░░░  (-10) ⚠️               │   │
│  │  Compliance:   12/20  ████████████░░░░░░░░  (-7)  ⚠️               │   │
│  │  Attestation:   4/20  ████░░░░░░░░░░░░░░░░  (-13) ⚠️               │   │
│  │  Evidence:      3/20  ███░░░░░░░░░░░░░░░░░  (-5)  ⚠️               │   │
│  │                                                                     │   │
│  │  [View Agent Detail]  [View Trust History]  [Re-evaluate]           │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Trigger Context ───────────────────────────────────────────────────┐   │
│  │  Recent policy evaluations for this agent:                          │   │
│  │  • 09:42 — DENY: block-credential-access (credential read attempt)  │   │
│  │  • 09:38 — DENY: block-pii-export (PII export attempt)              │   │
│  │  • 09:15 — DENY: block-external-network (external API call)         │   │
│  │  • 08:50 — DENY: block-credential-access (credential read attempt)  │   │
│  │                                                                     │   │
│  │  Pattern: 4 policy violations in 1 hour — possible rogue behavior    │   │
│  │  [View Full Evaluation Log]  [View Audit Trail]                      │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Response Actions ──────────────────────────────────────────────────┐   │
│  │  [Acknowledge]  [Escalate to CISO]  [Create Finding]  [Quarantine]  │   │
│  │  [Run Diagnostic]  [View Similar Alerts]                            │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Activity Log ──────────────────────────────────────────────────────┐   │
│  │  09:42 — Alert triggered by system (trust score < 60)                │   │
│  │  09:42 — Email sent to security-team@company.com                     │   │
│  │  09:42 — Slack notification sent to #grc-alerts                      │   │
│  │  09:43 — Agent automatically quarantined by system                  │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Accessibility Requirements

### 10.1 WCAG 2.1 AA Compliance

| Requirement | Implementation |
|-------------|----------------|
| **Perceivable** | All information available in text format; color is not the sole indicator; contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text |
| **Operable** | All functionality available via keyboard; no keyboard traps; focus visible; skip navigation links |
| **Understandable** | Consistent navigation; error identification and suggestions; labels and instructions for inputs |
| **Robust** | Compatible with assistive technologies; valid HTML; ARIA labels where needed |

### 10.2 Specific Accessibility Features

| Feature | Specification |
|---------|--------------|
| **Color Independence** | All status indicators use icons + text labels, not color alone. Severity uses 🔴🟠🟡🟢 + text. Verification levels use ✅⚠️❌ + text. |
| **Keyboard Navigation** | All interactive elements reachable via Tab/Enter. Arrow keys for list navigation. Escape to close modals. |
| **Screen Reader Support** | ARIA labels on all interactive elements. Live regions for alerts and notifications. Table headers associated with data cells. |
| **Contrast** | Minimum 4.5:1 contrast ratio for all text. Dark mode support with equivalent contrast. |
| **Font Size** | Support browser zoom up to 200% without loss of functionality. Minimum 14px base font size. |
| **Motion** | Respect `prefers-reduced-motion` media query. No auto-playing animations. |
| **Forms** | All inputs have associated labels. Error messages describe the issue and suggest fixes. Required fields indicated with `*` and `aria-required`. |
| **Data Tables** | Sortable columns with `aria-sort`. Pagination with page size selector. Sticky headers for long tables. |
| **Charts** | All charts have text alternatives (data tables). Color-blind friendly palettes. Patterns in addition to colors for differentiation. |

### 10.3 Responsive Design

| Breakpoint | Target Devices | Layout Changes |
|------------|----------------|----------------|
| ≥ 1440px | Desktop | Full multi-column layout |
| 1024–1439px | Laptop | Condensed multi-column, collapsible sidebar |
| 768–1023px | Tablet | Single column, stacked widgets |
| < 768px | Mobile | Single column, hamburger navigation, swipeable cards |

### 10.4 Internationalization

- All text externalized for translation
- RTL language support (Arabic, Hebrew)
- Date/time formatting per locale
- Number formatting per locale

---

## 11. Navigation & Information Architecture

### 11.1 Primary Navigation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GRC_Claw    Dashboard  Policies  Evidence  Assessments  Compliance  Alerts │
│                                                                             │
│  [User Menu ▼]  [Settings]  [Help]  [🔔 3]                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Navigation Structure

```
GRC_Claw
├── Dashboard
│   ├── Executive
│   ├── Operational
│   └── Technical
├── Policies
│   ├── Policy List
│   ├── Policy Editor
│   ├── Policy Test Console
│   └── Version History
├── Evidence
│   ├── Evidence List
│   ├── Evidence Detail
│   ├── Upload Evidence
│   └── Export Package
├── Assessments
│   ├── Assessment List
│   ├── Assessment Detail
│   ├── Finding Detail
│   └── New Assessment
├── Compliance
│   ├── Mapping Matrix
│   ├── Control Detail
│   ├── Coverage Summary
│   └── Export Report
├── Alerts
│   ├── Alert Feed
│   ├── Alert Configuration
│   └── Alert Detail
├── Agents
│   ├── Agent Registry
│   ├── Agent Detail
│   ├── Trust Score Detail
│   └── Policy Bundle Management
├── Audit Trail
│   ├── Activity Log
│   ├── Chain of Custody
│   └── Integrity Verification
└── Settings
    ├── User Management
    ├── Role Configuration
    ├── Framework Management
    ├── Integration Settings
    └── Notification Preferences
```

---

## 12. Interaction Patterns

### 12.1 Common Patterns

| Pattern | Usage | Behavior |
|---------|-------|----------|
| **Progressive Disclosure** | All detail views | Summary → Detail → Raw data; never show everything at once |
| **Inline Editing** | Finding status, agent metadata | Click to edit, Enter to save, Escape to cancel |
| **Bulk Operations** | Evidence selection, agent management | Checkbox selection, bulk action bar appears |
| **Real-time Updates** | Alerts, trust scores, enforcement log | WebSocket push, visual indicator for new data |
| **Contextual Actions** | All list views | Hover reveals actions; always-available primary action |
| **Confirmation Dialogs** | Destructive actions | Require confirmation for delete, quarantine, policy rollback |
| **Toast Notifications** | Success/error feedback | Auto-dismiss after 5s, action link for undo where applicable |
| **Skeleton Loading** | Data fetching | Show skeleton UI while loading; never blank screen |

### 12.2 Error Handling

| Error Type | UI Behavior |
|------------|-------------|
| **Validation Error** | Inline error message below field, red border, focus on first error |
| **Network Error** | Toast notification with retry option, preserve form state |
| **Permission Denied** | Redirect to unauthorized page with explanation and contact link |
| **Not Found** | 404 page with search and navigation suggestions |
| **Server Error** | 500 page with error ID for support reference, retry button |

---

## 13. Performance Requirements

| Metric | Target |
|--------|--------|
| Initial page load | < 2 seconds |
| Time to interactive | < 3 seconds |
| Dashboard widget render | < 500ms per widget |
| Search/filter response | < 200ms |
| Evidence list (1000 items) | < 1 second |
| Report generation | < 10 seconds |
| Real-time alert delivery | < 1 second |
| WebSocket reconnection | < 3 seconds |

---

## 14. Security Requirements for UI

| Requirement | Implementation |
|-------------|----------------|
| **Authentication** | SSO/SAML integration, session timeout after 30 minutes idle |
| **Authorization** | Role-based UI rendering — hide/disable unauthorized actions |
| **CSRF Protection** | All state-changing requests include CSRF tokens |
| **XSS Prevention** | All user input sanitized, CSP headers, no inline scripts |
| **Audit Logging** | All UI actions logged with user identity, timestamp, and context |
| **Sensitive Data** | PII masked by default, reveal requires explicit action + audit log |
| **Session Security** | Secure cookies, HttpOnly, SameSite=Strict |

---

## 15. Appendix A: UI Component Library

### 15.1 Core Components

| Component | Description | Used In |
|-----------|-------------|---------|
| `StatusBadge` | Colored badge with icon + text | All status indicators |
| `SeverityIndicator` | 🔴🟠🟡🟢 with text label | Findings, alerts, risks |
| `VerificationLevel` | L0-L4 with progress indicator | Evidence items |
| `TrustScoreGauge` | Circular gauge with letter grade | Agent detail, executive dashboard |
| `ComplianceScoreBar` | Horizontal bar with percentage | Framework scores |
| `EvidenceTimeline` | Vertical timeline with custody events | Evidence detail |
| `ControlMatrix` | Grid with status icons | Assessment detail, compliance mapping |
| `AgentCard` | Card with trust score, status, actions | Agent registry |
| `PolicyEditor` | YAML editor with validation | Policy management |
| `FilterBar` | Search + dropdown filters | All list views |
| `DataTable` | Sortable, paginated table | All list views |
| `ChartWidget` | Line, bar, pie, histogram | Dashboards |
| `AlertToast` | Slide-in notification | Alert feed |
| `ModalDialog` | Centered overlay with backdrop | Confirmations, detail views |
| `DrawerPanel` | Slide-in panel from right | Detail views, quick actions |
| `TabBar` | Horizontal tab navigation | Detail views |
| `Breadcrumb` | Navigation path | All pages |
| `EmptyState` | Illustration + message + CTA | Empty lists, no results |
| `SkeletonLoader` | Placeholder animation | Loading states |

### 15.2 Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| `--color-success` | #22c55e | Pass, active, verified |
| `--color-warning` | #f59e0b | Gap, pending, L1 |
| `--color-danger` | #ef4444 | Fail, critical, L0 |
| `--color-info` | #3b82f6 | Information, links |
| `--color-neutral` | #6b7280 | Secondary text, borders |
| `--color-background` | #ffffff | Page background |
| `--color-surface` | #f9fafb | Card background |
| `--color-text-primary` | #111827 | Primary text |
| `--color-text-secondary` | #6b7280 | Secondary text |

### 15.3 Typography

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| H1 | 24px | 600 | 32px |
| H2 | 20px | 600 | 28px |
| H3 | 16px | 600 | 24px |
| Body | 14px | 400 | 20px |
| Small | 12px | 400 | 16px |
| Code | 13px | 400 (monospace) | 18px |

---

## 16. Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Agent** | An autonomous AI system governed by GRC_Claw |
| **Attestation** | Human sign-off on evidence (L4 verification) |
| **Chain of Custody** | Chronological record of evidence handling |
| **Control** | A specific security or compliance requirement from a framework |
| **Crosswalk** | Mapping between controls in different frameworks |
| **Evidence** | Data collected to demonstrate control implementation |
| **Finding** | A identified gap or non-compliance |
| **Framework** | A compliance standard (NIST 800-53, SOC 2, ISO 27001, etc.) |
| **MCP** | Model Context Protocol — agent interoperability standard |
| **OSCAL** | Open Security Controls Assessment Language (NIST) |
| **Policy Bundle** | A versioned set of governance rules applied to an agent |
| **Trust Score** | Dynamic behavioral score for an agent (0-100, A-F grade) |
| **Verification Level** | Evidence integrity level (L0-L4) |
| **WORM** | Write Once Read Many storage |

---

*End of specification.*
