# GRC_Claw Unified Risk Assessment Framework

**Document ID:** GRC-RISK-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**Owner:** GRC_Claw Architecture Team  
**Status:** Draft for Review  
**Supersedes:** N/A

---

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Normative References](#2-normative-references)
3. [Risk Taxonomy](#3-risk-taxonomy)
4. [Risk Scoring Methodology](#4-risk-scoring-methodology)
5. [Risk Identification](#5-risk-identification)
6. [Risk Assessment](#6-risk-assessment)
7. [Risk Treatment Workflow](#7-risk-treatment-workflow)
8. [Risk Monitoring & Review](#8-risk-monitoring--review)
9. [Risk Reporting Format](#9-risk-reporting-format)
10. [Roles & Responsibilities](#10-roles--responsibilities)
11. [Compliance Mapping](#11-compliance-mapping)
12. [Appendices](#12-appendices)

---

## 1. Purpose & Scope

### 1.1 Purpose

This framework defines how GRC_Claw identifies, assesses, treats, and monitors risk across the full AI lifecycle. It unifies three foundational frameworks — **NIST AI RMF 1.0** (GOVERN-MAP-MEASURE-MANAGE), **ISO/IEC 42001:2023** (AI Management System), and **EU AI Act** (4-tier risk classification) — into a single, operational risk assessment methodology purpose-built for agentic AI governance.

### 1.2 Scope

| In Scope | Out of Scope |
|----------|-------------|
| First-party AI systems (models, agents, pipelines) | General enterprise IT risk (covered by GRC-VRM-001) |
| Third-party AI vendors and fourth-party dependencies | Physical security controls |
| Agentic AI systems (autonomous agents, multi-agent swarms) | Non-AI software risk |
| Data governance risks across the AI lifecycle | Financial/market risk |
| Model lifecycle risks (training → deployment → retirement) | |
| Cross-border and regulatory compliance risks | |

### 1.3 Design Principles

1. **Unified, not siloed** — One risk taxonomy, one scoring model, one register across all frameworks
2. **Agentic-aware** — Explicit coverage for autonomous agent risks (goal hijacking, tool misuse, cascading failures)
3. **Continuous, not point-in-time** — Risk is assessed continuously, not just at deployment gates
4. **Evidence-backed** — Every risk score links to verifiable evidence artifacts
5. **Deterministic** — Risk scoring uses deterministic rules, not LLM judgment
6. **Auditable** — Full chain of custody for every risk decision

---

## 2. Normative References

| Reference | Title | Role in This Framework |
|-----------|-------|----------------------|
| NIST AI RMF 1.0 (AI 100-1) | AI Risk Management Framework | Risk process structure (GOVERN-MAP-MEASURE-MANAGE) |
| NIST AI 600-1 | Generative AI Profile | GenAI-specific risk categories |
| ISO/IEC 42001:2023 | AI Management System | Management system structure, Annex A controls |
| ISO/IEC 23894:2023 | AI Risk Management | Risk treatment and monitoring guidance |
| EU AI Act (Reg. 2024/1689) | Artificial Intelligence Act | 4-tier risk classification, legal obligations |
| OWASP Agentic Top 10 (2025) | Agentic AI Security Risks | Agent-specific risk taxonomy |
| GRC-TPR-001 | Third-Party AI Risk Spec | Vendor risk dimensions and scoring |
| GRC-DAT-001 | Data Governance Spec | Data quality and provenance risk inputs |
| GRC-METRICS-001 | Unified Metrics Layer | KPI thresholds and escalation triggers |

---

## 3. Risk Taxonomy

### 3.1 Taxonomy Architecture

The GRC_Claw risk taxonomy is a **three-dimensional classification system**:

```
Dimension 1: Risk Domain (8 domains)
    └── Dimension 2: Risk Category (40 categories)
            └── Dimension 3: Risk Subcategory (120+ subcategories)
```

Each subcategory maps to source controls from NIST AI RMF, ISO 42001, EU AI Act, and OWASP Agentic Top 10.

### 3.2 Risk Domains (8 Domains)

| Domain | Code | Description | Primary Source |
|--------|------|-------------|---------------|
| **Governance & Policy** | GOV | Risks from inadequate AI governance structures, policies, and accountability | NIST GOVERN 1-6, ISO A.2-A.3 |
| **Data & Privacy** | DAT | Risks from training/inference data quality, provenance, privacy, and bias | NIST MAP 4, ISO A.7, EU Art. 10 |
| **Model & System** | MOD | Risks from model performance, robustness, accuracy, and lifecycle management | NIST MEASURE 2, ISO A.6, EU Art. 15 |
| **Security & Adversarial** | SEC | Risks from adversarial attacks, prompt injection, model extraction, and supply chain | OWASP ASI01-ASI10, EU Art. 15 |
| **Human & Societal** | HUM | Risks to individuals, groups, and society from AI decisions and interactions | NIST MAP 5, ISO A.5, EU Art. 5, 13, 14 |
| **Operational & Infrastructure** | OPS | Risks from deployment, monitoring, incident response, and business continuity | NIST MANAGE 4, ISO A.4, A.8 |
| **Third-Party & Supply Chain** | TPR | Risks from vendors, fourth-party dependencies, and AI supply chain | NIST GOVERN 6, ISO A.10, GRC-TPR-001 |
| **Compliance & Regulatory** | CMP | Risks from regulatory non-compliance, cross-border conflicts, and certification gaps | EU AI Act Art. 43, 71, 73; ISO A.11 |

### 3.3 Risk Categories (40 Categories)

#### Domain 1: Governance & Policy (GOV) — 5 Categories

| Code | Category | Description | Source Mapping |
|------|----------|-------------|----------------|
| GOV-01 | Policy Absence | Missing or outdated AI policies | NIST GOVERN 1.1, ISO A.2.2 |
| GOV-02 | Accountability Gap | Unclear AI ownership and responsibility | NIST GOVERN 2, ISO A.3.2 |
| GOV-03 | Reporting Failure | Inadequate incident/concern reporting mechanisms | NIST GOVERN 4, ISO A.3.3 |
| GOV-04 | Workforce Competence | Insufficient AI literacy and skills | NIST GOVERN 3, ISO A.4.6, EU Art. 4 |
| GOV-05 | Third-Party Governance | Inadequate vendor AI risk management | NIST GOVERN 6, ISO A.10.3 |

#### Domain 2: Data & Privacy (DAT) — 6 Categories

| Code | Category | Description | Source Mapping |
|------|----------|-------------|----------------|
| DAT-01 | Data Quality Deficiency | Incomplete, inaccurate, or inconsistent training data | NIST MEASURE 2.11, ISO A.7.4, EU Art. 10 |
| DAT-02 | Provenance Gap | Unverifiable data lineage and origin | NIST MAP 4.5, ISO A.7.5 |
| DAT-03 | Bias & Discrimination | Representational or historical bias in data | NIST MEASURE 2.11, ISO A.7.4, EU Art. 10(3) |
| DAT-04 | Privacy Violation | Unauthorized PII/PHI processing or exposure | NIST MEASURE 2.10, EU Art. 10, GDPR |
| DAT-05 | Data Poisoning | Adversarial contamination of training/inference data | OWASP ASI06, NIST MAP 4.1 |
| DAT-06 | Retention Non-Compliance | Data retained beyond policy or regulatory limits | ISO A.7.7, GDPR Art. 5(1)(e) |

#### Domain 3: Model & System (MOD) — 6 Categories

| Code | Category | Description | Source Mapping |
|------|----------|-------------|----------------|
| MOD-01 | Performance Degradation | Model accuracy/F1 below acceptable thresholds | NIST MEASURE 2.1, EU Art. 15 |
| MOD-02 | Model Drift | Data drift, concept drift, or label drift | NIST MEASURE 3.1, GRC-METRICS UC3-002 |
| MOD-03 | Robustness Failure | Model fails under distribution shift or edge cases | NIST MEASURE 2.2, EU Art. 15 |
| MOD-04 | Explainability Gap | Inability to explain model decisions | NIST MEASURE 2.9, EU Art. 13 |
| MOD-05 | Lifecycle Management | Inadequate versioning, documentation, or change control | ISO A.6.2.3, EU Art. 11 |
| MOD-06 | Hallucination | Model generates fabricated or false information | NIST AI 600-1, OWASP ASI01 |

#### Domain 4: Security & Adversarial (SEC) — 7 Categories

| Code | Category | Description | Source Mapping |
|------|----------|-------------|----------------|
| SEC-01 | Prompt Injection | Adversarial inputs manipulate model behavior | OWASP ASI01, NIST AI 600-1 |
| SEC-02 | Agent Goal Hijacking | Agent's objectives are subverted by external input | OWASP ASI01 |
| SEC-03 | Tool Misuse | Agent uses tools beyond authorized scope | OWASP ASI02 |
| SEC-04 | Identity & Privilege Abuse | Agent escalates privileges or impersonates | OWASP ASI03 |
| SEC-05 | Supply Chain Compromise | Compromised model, dataset, or MCP dependency | OWASP ASI04, ISO A.10.3 |
| SEC-06 | Unexpected Code Execution | Agent triggers unauthorized code execution | OWASP ASI05 |
| SEC-07 | Cascading Failure | Failure propagates across agent pipeline | OWASP ASI08 |

#### Domain 5: Human & Societal (HUM) — 5 Categories

| Code | Category | Description | Source Mapping |
|------|----------|-------------|----------------|
| HUM-01 | Individual Harm | AI decision negatively impacts an individual | NIST MAP 5.4, ISO A.5.4, EU Art. 9(2) |
| HUM-02 | Group Discrimination | AI system produces discriminatory outcomes for protected groups | NIST MEASURE 2.11, EU Art. 10 |
| HUM-03 | Human Oversight Failure | Inadequate human-in-the-loop controls | EU Art. 14, ISO A.9.2 |
| HUM-04 | Trust Exploitation | Agent manipulates human trust | OWASP ASI09 |
| HUM-05 | Societal Impact | Broad negative societal consequences | ISO A.5.5, NIST MAP 5.5, EU Art. 51 |

#### Domain 6: Operational & Infrastructure (OPS) — 5 Categories

| Code | Category | Description | Source Mapping |
|------|----------|-------------|----------------|
| OPS-01 | Monitoring Gap | Inadequate production monitoring and alerting | NIST MEASURE 3, ISO A.6.2.6 |
| OPS-02 | Incident Response | Slow or ineffective AI incident response | NIST MANAGE 4, ISO A.8.4, EU Art. 73 |
| OPS-03 | Availability Failure | AI system downtime or SLA breach | ISO A.4.5, GRC-TPR-001 |
| OPS-04 | Audit Trail Incompleteness | Missing or tampered audit logs | EU Art. 12, ISO A.6.2.8 |
| OPS-05 | Post-Market Monitoring | Inadequate post-deployment surveillance | EU Art. 72, NIST MEASURE 3.2 |

#### Domain 7: Third-Party & Supply Chain (TPR) — 4 Categories

| Code | Category | Description | Source Mapping |
|------|----------|-------------|----------------|
| TPR-01 | Vendor AI Risk | Third-party model/service introduces unacceptable risk | GRC-TPR-001 §4, ISO A.10.3 |
| TPR-02 | Fourth-Party Concentration | Over-reliance on single sub-contractor or provider | GRC-TPR-001 §7 |
| TPR-03 | Vendor Model Update | Silent model update changes behavior without notice | GRC-TPR-001 §5.3 |
| TPR-04 | Vendor Lock-in | Inability to exit vendor relationship | GRC-TPR-001 §8.2 |

#### Domain 8: Compliance & Regulatory (CMP) — 4 Categories

| Code | Category | Description | Source Mapping |
|------|----------|-------------|----------------|
| CMP-01 | Prohibited Practice | AI system violates EU AI Act Art. 5 prohibitions | EU Art. 5 |
| CMP-02 | Classification Error | AI system incorrectly risk-classified | EU Art. 6, NIST MAP 2 |
| CMP-03 | Conformity Assessment Gap | Missing or failed conformity assessment | EU Art. 43, ISO A.6.2.4 |
| CMP-04 | Cross-Border Conflict | Conflicting regulatory requirements across jurisdictions | GRC-INT-001 §3 |

### 3.4 Risk Subcategory Examples

Each category contains 2-5 subcategories. Example for SEC-01 (Prompt Injection):

| Subcode | Subcategory | Description |
|---------|-------------|-------------|
| SEC-01.1 | Direct Prompt Injection | User input directly manipulates system prompt |
| SEC-01.2 | Indirect Prompt Injection | Malicious content in retrieved context (RAG) |
| SEC-01.3 | Multi-Turn Injection | Attack requires multiple conversation turns |
| SEC-01.4 | Agent-to-Agent Injection | One agent injects another via inter-agent message |

Complete subcategory catalog maintained in GRC_Claw Risk Taxonomy Registry (Appendix A).

---

## 4. Risk Scoring Methodology

### 4.1 Multi-Dimensional Risk Score (MDRS)

GRC_Claw uses a **composite risk score** that evaluates each risk across five dimensions:

| Dimension | Weight | Description | Scale |
|-----------|--------|-------------|-------|
| **Likelihood (L)** | 25% | Probability of risk materializing | 1 (Rare) – 5 (Almost Certain) |
| **Impact (I)** | 30% | Severity of harm if risk materializes | 1 (Negligible) – 5 (Catastrophic) |
| **Detectability (D)** | 15% | Ease of detecting the risk before harm occurs | 1 (Easy) – 5 (Impossible) |
| **Velocity (V)** | 15% | Speed at which harm propagates | 1 (Slow) – 5 (Instant) |
| **Persistence (P)** | 15% | Duration of harm once risk materializes | 1 (Transient) – 5 (Permanent) |

### 4.2 Scoring Formula

```
MDRS = (L × 0.25) + (I × 0.30) + (D × 0.15) + (V × 0.15) + (P × 0.15)

Range: 1.00 (lowest risk) to 5.00 (highest risk)
```

### 4.3 Risk Tier Classification

| MDRS Range | Risk Tier | Color | Approval Authority | Review Frequency | Response SLA |
|------------|-----------|-------|--------------------|------------------|--------------|
| 1.00 – 1.49 | **Minimal** | 🟢 Green | System Owner | Annual | 30 days |
| 1.50 – 2.49 | **Low** | 🟢 Green | Business Unit Owner | Semi-annual | 14 days |
| 2.50 – 3.49 | **Medium** | 🟡 Amber | Department Head | Quarterly | 7 days |
| 3.50 – 4.49 | **High** | 🔴 Red | CISO / CTO | Monthly | 48 hours |
| 4.50 – 5.00 | **Critical** | 🔴 Red | Risk Committee | Continuous | 4 hours |

### 4.4 EU AI Act Risk Tier Mapping

For regulatory reporting, MDRS tiers map to EU AI Act classifications:

| MDRS Tier | EU AI Act Classification | Legal Obligations |
|-----------|-------------------------|-------------------|
| Minimal (1.0–1.49) | Minimal Risk | Transparency (Art. 50) if applicable |
| Low (1.5–2.49) | Limited Risk | Transparency obligations (Art. 50) |
| Medium (2.5–3.49) | High Risk (Annex III) | Full RMS, conformity assessment, registration |
| High (3.5–4.49) | High Risk (Annex III) | Full RMS + enhanced monitoring |
| Critical (4.5–5.0) | Prohibited (Art. 5) | Immediate cessation required |

### 4.5 Inherent vs. Residual Risk

| Risk Type | Definition | When Assessed |
|-----------|-----------|---------------|
| **Inherent Risk** | Risk before any controls are applied | During initial risk identification |
| **Residual Risk** | Risk remaining after controls are applied | After risk treatment implementation |
| **Control Effectiveness** | (Inherent − Residual) / Inherent × 100 | During control testing |

### 4.6 Risk Appetite Thresholds

Organizations define risk appetite per domain. Default GRC_Claw thresholds:

| Domain | Minimal | Low | Medium | High | Critical |
|--------|---------|-----|--------|------|----------|
| GOV | ≤1.49 | 1.5–2.49 | 2.5–3.49 | 3.5–4.49 | ≥4.50 |
| DAT | ≤1.49 | 1.5–2.49 | 2.5–3.49 | 3.5–4.49 | ≥4.50 |
| MOD | ≤1.49 | 1.5–2.49 | 2.5–3.49 | 3.5–4.49 | ≥4.50 |
| SEC | ≤1.49 | 1.5–2.49 | 2.5–3.49 | 3.5–4.49 | ≥4.50 |
| HUM | ≤1.49 | 1.5–2.49 | 2.5–3.49 | 3.5–4.49 | ≥4.50 |
| OPS | ≤1.49 | 1.5–2.49 | 2.5–3.49 | 3.5–4.49 | ≥4.50 |
| TPR | ≤1.49 | 1.5–2.49 | 2.5–3.49 | 3.5–4.49 | ≥4.50 |
| CMP | ≤1.49 | 1.5–2.49 | 2.5–3.49 | 3.5–4.49 | ≥4.50 |

**Risk Appetite Statement:** GRC_Claw's default risk appetite is **Medium** — the organization accepts risks up to MDRS 3.49 with appropriate mitigation. Risks at High or Critical tier require executive approval and active treatment plans.

---

## 5. Risk Identification

### 5.1 Identification Methods

GRC_Claw employs seven complementary risk identification methods:

| Method | Description | Frequency | Output |
|--------|-------------|-----------|--------|
| **Automated Discovery** | Scan code repos, cloud infra, network for AI assets | Continuous | Asset inventory with risk flags |
| **Threat Modeling** | Structured analysis of attack surfaces per AI system | Per system + on change | Threat model document |
| **Red Teaming** | Adversarial testing of AI systems | Per release + quarterly | Red team findings |
| **Stakeholder Reporting** | Concerns raised by employees, users, or partners | Continuous | Risk register entries |
| **Regulatory Monitoring** | Track new AI regulations and standards | Continuous | Compliance gap analysis |
| **Incident Analysis** | Post-incident root cause analysis | Per incident | Lessons learned → new risks |
| **Audit Findings** | Internal and external audit results | Per audit cycle | Audit findings → risk register |

### 5.2 Risk Identification Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                  RISK IDENTIFICATION PIPELINE                     │
│                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │ DISCOVER │──▶│ TRIAGE   │──▶│ CLASSIFY │──▶│ REGISTER │   │
│  │          │   │          │   │          │   │          │   │
│  │• Scan    │   │• Dedupl. │   │• Domain  │   │• Risk ID │   │
│  │• Detect  │   │• Priorit.│   │• Category│   │• MDRS    │   │
│  │• Report  │   │• Validate│   │• Source  │   │• Owner   │   │
│  │• Audit   │   │          │   │• Evidence│   │• Tier    │   │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   │
│                                                                   │
│  Triggers:                                                       │
│  • New AI system deployment    • Model retraining                │
│  • Vendor onboarding           • Regulatory change               │
│  • Incident occurrence         • Audit finding                   │
│  • Periodic review (scheduled) • Stakeholder report              │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Risk Register Entry Schema

Every identified risk is recorded in the GRC_Claw Risk Register:

```json
{
  "risk_id": "RISK-2026-0001",
  "risk_title": "Customer service agent may produce biased responses for loan applicants",
  "risk_description": "The customer support agent uses an LLM fine-tuned on historical customer interactions. Historical data contains demographic biases that may cause the agent to provide different quality of service based on customer demographics.",
  "risk_domain": "DAT",
  "risk_category": "DAT-03",
  "risk_subcategory": "DAT-03.2",
  "affected_assets": ["agent-customer-support-v2", "model-llama-3-8b-customer"],
  "affected_stakeholders": ["loan_applicants", "customer_service_team"],
  "inherent_score": {
    "likelihood": 4,
    "impact": 4,
    "detectability": 3,
    "velocity": 3,
    "persistence": 4,
    "mdrs": 3.65,
    "tier": "High"
  },
  "residual_score": null,
  "risk_owner": "data-science-lead@org.com",
  "risk_status": "identified",
  "identified_date": "2026-10-01",
  "identified_source": "automated_discovery",
  "evidence_refs": ["EVID-2026-0042", "EVID-2026-0043"],
  "framework_mapping": {
    "nist_ai_rmf": ["MEASURE 2.11", "MAP 5.4"],
    "iso_42001": ["A.7.4", "A.5.4"],
    "eu_ai_act": ["Art. 10(3)", "Art. 9(2)"],
    "owasp_agentic": []
  },
  "treatment_plan": null,
  "review_date": "2026-11-01",
  "audit_trail": []
}
```

---

## 6. Risk Assessment

### 6.1 Assessment Process

Risk assessment is a **four-phase process**:

#### Phase 1: Context Establishment
- Define the AI system's purpose, scope, and boundaries
- Identify all stakeholders (deployers, users, affected parties)
- Map applicable regulatory frameworks
- Document system capabilities and limitations

#### Phase 2: Risk Analysis
- Score each identified risk on 5 dimensions (L, I, D, V, P)
- Calculate MDRS and assign risk tier
- Identify risk interdependencies and cascading effects
- Assess existing control coverage

#### Phase 3: Risk Evaluation
- Compare MDRS against risk appetite thresholds
- Prioritize risks by tier and business impact
- Identify risks requiring immediate escalation
- Determine assessment confidence level

#### Phase 4: Assessment Documentation
- Generate assessment report with evidence links
- Record assessment in GRC_Claw Risk Register
- Map risks to compliance framework controls
- Set review date based on risk tier

### 6.2 Assessment Triggers

Risk assessment is triggered by:

| Trigger | Scope | Timeline |
|---------|-------|----------|
| New AI system onboarding | Full assessment | Before deployment |
| Model retraining/update | Targeted assessment | Before release |
| Vendor onboarding | Vendor risk assessment | Before contract execution |
| Regulatory change | Compliance gap analysis | Within 60 days of regulation |
| Incident occurrence | Incident-triggered assessment | Within 48 hours of incident |
| Scheduled review | Full re-assessment | Per risk tier frequency |
| Material change | Change-triggered assessment | Before change deployment |

### 6.3 Assessment Confidence Levels

| Level | Description | Data Quality | Action |
|-------|-------------|--------------|--------|
| **High** | Multiple evidence sources, validated | Complete and current | Proceed with treatment |
| **Medium** | Some evidence, partially validated | Minor gaps | Proceed with caveats |
| **Low** | Limited evidence, unvalidated | Significant gaps | Gather more data before treatment |
| **Unknown** | No evidence available | No data | Immediate data collection required |

### 6.4 Risk Interdependency Analysis

Risks are not independent. GRC_Claw models risk interdependencies using a directed graph:

```
Risk A (Prompt Injection) ──triggers──▶ Risk B (Agent Goal Hijacking)
                                              │
                                              ▼
                                       Risk C (Tool Misuse)
                                              │
                                              ▼
                                       Risk D (Data Exfiltration)
```

**Cascading Risk Score:** When Risk A materializes, the effective score of downstream risks B, C, D is increased by a propagation factor:

```
Effective MDRS = Base MDRS × (1 + 0.2 × Number of Active Upstream Risks)
```

Maximum effective MDRS is capped at 5.00.

---

## 7. Risk Treatment Workflow

### 7.1 Treatment Strategy Hierarchy

GRC_Claw applies risk treatment strategies in order of preference:

```
1. AVOID ─────── Do not deploy or use the AI system if risk is unacceptable
     │
2. TRANSFER ──── Shift risk through insurance, contracts, or indemnification
     │
3. MITIGATE ──── Implement controls to reduce likelihood or impact
     │
4. ACCEPT ────── Acknowledge residual risk with documented approval
```

### 7.2 Treatment Decision Matrix

| Risk Tier | Default Treatment | Escalation Required | Maximum Acceptance Period |
|-----------|-------------------|---------------------|--------------------------|
| Critical (4.5–5.0) | Avoid or Mitigate | Risk Committee | 30 days (with mitigation plan) |
| High (3.5–4.49) | Mitigate | CISO / CTO | 90 days |
| Medium (2.5–3.49) | Mitigate or Accept | Department Head | 180 days |
| Low (1.5–2.49) | Accept or Mitigate | Business Unit Owner | 12 months |
| Minimal (1.0–1.49) | Accept | System Owner | 12 months |

### 7.3 Mitigation Control Catalog

Each risk category maps to a set of standard mitigation controls:

#### GOV Controls

| Risk | Mitigation Control | Implementation |
|------|-------------------|----------------|
| GOV-01 | AI policy establishment | Policy engine with version control |
| GOV-02 | RACI matrix for AI roles | Role registry with accountability chains |
| GOV-03 | Whistleblower hotline | Anonymous reporting workflow |
| GOV-04 | AI literacy program | LMS integration with role-based curriculum |
| GOV-05 | Vendor risk assessment | VARQ workflow with CRS scoring |

#### DAT Controls

| Risk | Mitigation Control | Implementation |
|------|-------------------|----------------|
| DAT-01 | Data quality gates | 5-stage quality pipeline (G1–G5) |
| DAT-02 | Provenance tracking | Cryptographic lineage with hash chains |
| DAT-03 | Bias testing | Fairlearn/AIF360 integration in CI/CD |
| DAT-04 | PII detection | Presidio + custom NER at ingestion |
| DAT-05 | Data validation | Anomaly detection on training data |
| DAT-06 | Retention enforcement | Automated deletion with certificates |

#### MOD Controls

| Risk | Mitigation Control | Implementation |
|------|-------------------|----------------|
| MOD-01 | Performance monitoring | Real-time metrics with SLA alerts |
| MOD-02 | Drift detection | PSI/KL divergence monitoring |
| MOD-03 | Robustness testing | Adversarial test suite in CI/CD |
| MOD-04 | Explainability | SHAP/LIME integration with model cards |
| MOD-05 | Model versioning | Governance-aware model registry |
| MOD-06 | Hallucination detection | LLM-as-judge with ground truth validation |

#### SEC Controls

| Risk | Mitigation Control | Implementation |
|------|-------------------|----------------|
| SEC-01 | Input sanitization | Prompt injection filter pipeline |
| SEC-02 | Goal integrity monitoring | Agent objective verification |
| SEC-03 | Tool access controls | MCP tool permission scoping |
| SEC-04 | Identity management | Agent identity registry with attestation |
| SEC-05 | Supply chain verification | AI-SBOM with provenance checks |
| SEC-06 | Code execution sandboxing | Isolated execution environment |
| SEC-07 | Circuit breakers | Kill-and-quarantine on invariant violation |

#### HUM Controls

| Risk | Mitigation Control | Implementation |
|------|-------------------|----------------|
| HUM-01 | Impact assessment | FRIA workflow per EU Art. 27 |
| HUM-02 | Fairness monitoring | Continuous bias metrics on outputs |
| HUM-03 | Human oversight | Human-in-the-loop approval workflow |
| HUM-04 | Trust calibration | Output confidence scoring |
| HUM-05 | Societal impact review | Ethics board review process |

#### OPS Controls

| Risk | Mitigation Control | Implementation |
|------|-------------------|----------------|
| OPS-01 | Real-time monitoring | AI-Risk-Radar with sub-100ms latency |
| OPS-02 | Incident response | AI-IR-Playbooks with automated containment |
| OPS-03 | High availability | Multi-region deployment with failover |
| OPS-04 | Immutable audit trail | Hash-chained append-only log |
| OPS-05 | Post-market monitoring | Continuous production surveillance |

#### TPR Controls

| Risk | Mitigation Control | Implementation |
|------|-------------------|----------------|
| TPR-01 | Vendor due diligence | VARQ + CRS scoring per GRC-TPR-001 |
| TPR-02 | Fourth-party tracking | Fourth-party risk register (FPRS) |
| TPR-03 | Update notification | Contractual 30-day notification clause |
| TPR-04 | Exit planning | Data portability requirements |

#### CMP Controls

| Risk | Mitigation Control | Implementation |
|------|-------------------|----------------|
| CMP-01 | Prohibited practice screening | Automated Art. 5 compliance check |
| CMP-02 | Risk classification engine | EU AI Act tier triage automation |
| CMP-03 | Conformity assessment | Assessment workflow per Art. 43 |
| CMP-04 | Cross-border engine | GlobalAI-Compliance rules engine |

### 7.4 Treatment Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│                    RISK TREATMENT WORKFLOW                              │
│                                                                        │
│  ┌─────────────┐                                                      │
│  │ 1. ASSESS   │  Risk scored and tiered                               │
│  │    RISK     │  MDRS calculated                                      │
│  └──────┬──────┘                                                      │
│         │                                                              │
│         ▼                                                              │
│  ┌─────────────┐     ┌─────────────┐                                  │
│  │ 2. SELECT   │────▶│ AVOID?      │──Yes──▶ Decommission system      │
│  │  STRATEGY   │     └──────┬──────┘                                  │
│  │             │            │ No                                       │
│  │             │     ┌──────▼──────┐                                  │
│  │             │────▶│ TRANSFER?   │──Yes──▶ Insurance/contract        │
│  │             │     └──────┬──────┘                                  │
│  │             │            │ No                                       │
│  │             │     ┌──────▼──────┐                                  │
│  │             │────▶│ MITIGATE?   │──Yes──▶ Implement controls        │
│  │             │     └──────┬──────┘                                  │
│  │             │            │ No                                       │
│  │             │     ┌──────▼──────┐                                  │
│  │             │────▶│ ACCEPT      │──────▶ Document + approve         │
│  └─────────────┘     └─────────────┘                                  │
│         │                                                              │
│         ▼                                                              │
│  ┌─────────────┐                                                      │
│  │ 3. IMPLEMENT│  Controls deployed                                     │
│  │  CONTROLS   │  Evidence collected                                    │
│  └──────┬──────┘                                                      │
│         │                                                              │
│         ▼                                                              │
│  ┌─────────────┐                                                      │
│  │ 4. VERIFY   │  Control effectiveness tested                          │
│  │ EFFECTIVENESS│  Residual risk recalculated                           │
│  └──────┬──────┘                                                      │
│         │                                                              │
│         ▼                                                              │
│  ┌─────────────┐                                                      │
│  │ 5. DOCUMENT │  Treatment recorded in Risk Register                   │
│  │  & CLOSE    │  Evidence linked                                       │
│  └─────────────┘  Review date set                                      │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

### 7.5 Residual Risk Acceptance

When residual risk remains after mitigation:

1. **Document** residual risk in Risk Register with clear description
2. **Assess** whether residual risk is within risk appetite
3. **Approve** by designated authority based on risk tier
4. **Set review date** — maximum 12 months for acceptance
5. **Monitor** for changes that may alter the risk profile
6. **Escalate** immediately if residual risk increases

### 7.6 Risk Treatment Evidence Requirements

Every treatment action must produce:

| Evidence Type | Description | Storage |
|---------------|-------------|---------|
| Treatment Plan | Documented strategy, controls, timeline | Evidence Store |
| Control Implementation | Configuration, code, or policy artifact | Evidence Store |
| Effectiveness Test | Test results showing control works | Evidence Store |
| Approval Record | Signed approval from authority | Audit Trail |
| Residual Risk Assessment | Post-treatment risk score | Risk Register |

---

## 8. Risk Monitoring & Review

### 8.1 Continuous Monitoring Framework

GRC_Claw implements **four monitoring layers**:

| Layer | Scope | Frequency | Data Source |
|-------|-------|-----------|-------------|
| **L1: Signal Collection** | Raw metrics, logs, events | Real-time | Agent telemetry, audit logs, monitoring |
| **L2: Risk Scoring** | MDRS recalculation | On signal change | Risk engine |
| **L3: Threshold Alerting** | KPI breach detection | Real-time | Metrics engine |
| **L4: Trend Analysis** | Pattern and anomaly detection | Daily/Weekly | Analytics engine |

### 8.2 Monitoring Triggers

Risk monitoring is triggered by:

| Trigger | Description | Response |
|---------|-------------|----------|
| **Threshold Breach** | KPI crosses defined threshold | Automated alert + playbook activation |
| **Anomaly Detection** | Statistical deviation from baseline | Triage + investigation |
| **Incident Occurrence** | Production incident or harm | Full 8-stage response loop |
| **Audit Finding** | Internal/external audit nonconformity | CAPA process |
| **Regulatory Change** | New law or standard published | Impact assessment + gap analysis |
| **Material Change** | Model update, vendor change, new deployment | Re-assessment |
| **Scheduled Review** | Per risk tier frequency | Full re-assessment |

### 8.3 Key Risk Indicators (KRIs)

| KRI | Definition | Target | Alert Threshold | Source |
|-----|-----------|--------|-----------------|--------|
| Open Critical Risks | Count of risks at Critical tier | 0 | ≥1 | Risk Register |
| Open High Risks | Count of risks at High tier | 0 | ≥3 | Risk Register |
| Mean Risk Score | Average MDRS across all active risks | ≤2.5 | ≥3.0 | Risk Engine |
| Risk Treatment Overdue | Count of treatments past due date | 0 | ≥1 | Risk Register |
| Control Failure Rate | % of controls failing effectiveness test | <5% | ≥10% | Control Testing |
| Risk Assessment Currency | % of assessments within review period | 100% | <90% | Risk Register |
| Vendor Risk Exposure | Count of unassured high-risk vendors | 0 | ≥1 | Vendor Mgmt |
| Incident Recurrence | % of incidents that are recurring | <10% | ≥20% | Incident Mgmt |

### 8.4 Risk Review Cadence

| Review Type | Frequency | Scope | Output |
|-------------|-----------|-------|--------|
| **Continuous** | Real-time | Critical risks, KRIs | Automated alerts |
| **Operational** | Weekly | High and Medium risks | Status report |
| **Management** | Monthly | All active risks | Risk dashboard |
| **Executive** | Quarterly | Risk posture, trends, appetite | Board report |
| **Comprehensive** | Annually | Full risk register, framework | Annual risk report |

### 8.5 Risk Escalation Matrix

| Severity | Trigger | Response Time | Escalation Path |
|----------|---------|---------------|-----------------|
| P1 – Critical | Risk materializes with catastrophic impact | 15 minutes | CISO → CTO → Risk Committee |
| P2 – High | Risk tier escalates to High | 1 hour | Security Lead → Risk Owner |
| P3 – Medium | Risk tier escalates to Medium | 4 hours | GRC Analyst → Risk Owner |
| P4 – Low | Risk tier increases within Low | 24 hours | GRC Analyst |

---

## 9. Risk Reporting Format

### 9.1 Report Types

GRC_Claw generates **six standard risk reports**:

| Report | Audience | Frequency | Format |
|--------|----------|-----------|--------|
| **Risk Dashboard** | All stakeholders | Real-time | Web dashboard |
| **Risk Register Summary** | Risk owners, managers | Weekly | PDF + CSV |
| **Executive Risk Report** | C-suite, Board | Quarterly | PDF + interactive |
| **Regulatory Risk Report** | Regulators, auditors | On-demand | Evidence pack |
| **Incident Risk Report** | All stakeholders | Per incident | PDF + web |
| **Annual Risk Report** | Executive leadership, Board | Annually | PDF + presentation |

### 9.2 Risk Dashboard Structure

The real-time risk dashboard presents three views:

#### Executive View (One-Page Principle)

```
┌─────────────────────────────────────────────────────────────┐
│                    EXECUTIVE RISK DASHBOARD                   │
│                                                               │
│  Overall Risk Score: 2.85 (Medium)  │  Trend: ↓ 0.12       │
│                                                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │Critical │ │  High   │ │ Medium  │ │  Low    │           │
│  │   2     │ │   5     │ │   12    │ │   28    │           │
│  │   🔴    │ │   🔴    │ │   🟡    │ │   🟢    │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                               │
│  Top 5 Material Risks:                                        │
│  1. [SEC-02] Agent goal hijacking — MDRS 4.2 (High)          │
│  2. [DAT-03] Bias in loan model — MDRS 3.8 (High)            │
│  3. [TPR-01] Vendor concentration — MDRS 3.5 (High)          │
│  4. [MOD-02] Model drift detected — MDRS 3.2 (Medium)        │
│  5. [CMP-03] Conformity gap — MDRS 3.1 (Medium)             │
│                                                               │
│  Risk Posture by Domain:                                      │
│  GOV 2.1 │ DAT 3.2 │ MOD 2.8 │ SEC 3.5 │ HUM 2.9            │
│  OPS 2.4 │ TPR 3.1 │ CMP 2.6                                  │
│                                                               │
│  Decisions Required: 3  │  Overdue Treatments: 1             │
└─────────────────────────────────────────────────────────────┘
```

#### Program View (Management Detail)

- Risk breakdown by domain, category, and tier
- Risk treatment status and progress
- Control effectiveness scores
- Trend analysis (90-day rolling)
- Exception exposure
- Review currency

#### Operating View (Full Detail)

- Complete risk register with all fields
- Risk interdependency graph
- Evidence linkage
- Treatment plan details
- Audit trail
- Change history

### 9.3 Executive Risk Report Template

```markdown
# Executive AI Risk Report — [Period]

## 1. Risk Posture Summary
- Overall Risk Score: [MDRS] ([Tier])
- Trend: [↑/↓/↔] [delta] from previous period
- Risks by tier: Critical [N], High [N], Medium [N], Low [N], Minimal [N]
- Risks by domain: GOV [score], DAT [score], MOD [score], SEC [score], ...

## 2. Material Risks (Top 5)
For each: Risk ID, description, MDRS, tier, treatment status, target date

## 3. Risk Treatment Summary
- New risks identified: [N]
- Risks treated this period: [N]
- Risks escalated: [N]
- Risks closed: [N]
- Overdue treatments: [N]

## 4. Control Effectiveness
- Controls tested: [N]
- Controls passed: [N] ([%])
- Controls failed: [N] ([%])
- Mean time to remediate: [days]

## 5. Compliance Posture
- EU AI Act: [score] ([trend])
- NIST AI RMF: [score] ([trend])
- ISO 42001: [score] ([trend])

## 6. Key Risk Indicators
- [KRI-1]: [value] ([status])
- [KRI-2]: [value] ([status])
- ...

## 7. Decisions Required
1. [Decision 1: description, options, recommendation]
2. [Decision 2: description, options, recommendation]

## 8. Recommendations
1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]
```

### 9.4 Regulatory Risk Report (Evidence Pack)

For regulator submission, the risk report includes:

| Section | Content | EU AI Act Reference |
|---------|---------|-------------------|
| 1. System Identification | System ID, provider, deployer, classification | Art. 6, Art. 49 |
| 2. Risk Assessment | Methodology, identified risks, MDRS scores | Art. 9(2)(a) |
| 3. Risk Treatment | Mitigation measures, residual risk | Art. 9(4) |
| 4. Conformity Assessment | Assessment results, DoC | Art. 43 |
| 5. Post-Market Monitoring | Monitoring data, incident reports | Art. 72, Art. 73 |
| 6. Technical Documentation | Annex IV documentation | Art. 11 |
| 7. Change Log | Model/prompt/threshold changes | Art. 11(2) |

### 9.5 Risk Report Delivery

| Stakeholder | Report | Frequency | Channel |
|-------------|--------|-----------|---------|
| Board | Executive Risk Report | Quarterly | PDF + board portal |
| C-Suite | Executive Risk Report + Dashboard | Monthly | PDF + dashboard |
| Regulators | Regulatory Risk Report | On-demand | Evidence pack |
| Governance Committee | Program Risk Report | Monthly | PDF + dashboard |
| Risk Owners | Risk Register Summary | Weekly | Email + dashboard |
| All Stakers | Risk Dashboard | Real-time | Web dashboard |

---

## 10. Roles & Responsibilities

| Role | Risk Responsibility | Authority |
|------|-------------------|-----------|
| **Board** | Set risk appetite, approve Critical risk acceptance | Final authority on risk appetite |
| **Risk Committee** | Oversee risk framework, approve Critical/High acceptances | Approve Critical tier risks |
| **CISO** | Own security risk domain, approve High security risks | Approve High tier SEC risks |
| **CTO** | Own model/system risk domain, approve High model risks | Approve High tier MOD risks |
| **Chief AI Officer** | Own governance risk domain, approve High governance risks | Approve High tier GOV risks |
| **AI Risk Officer** | Maintain risk register, coordinate assessments, report posture | Escalate risks per matrix |
| **Data Science Lead** | Own data/model risk assessment, validate risk scores | Approve DAT/MOD risk assessments |
| **Security Lead** | Own security risk assessment, red team execution | Approve SEC risk assessments |
| **Compliance Officer** | Own compliance risk mapping, regulatory reporting | Approve CMP risk assessments |
| **Business Unit Owner** | Own operational risk for their AI systems | Accept Low tier risks |
| **System Owner** | Day-to-day risk monitoring for assigned systems | Accept Minimal tier risks |
| **GRC_Claw Analyst** | Maintain risk register, collect evidence, generate reports | No approval authority |

---

## 11. Compliance Mapping

### 11.1 NIST AI RMF Mapping

| NIST Function | Category | GRC_Claw Risk Process |
|---------------|----------|----------------------|
| GOVERN 1-6 | Policies, accountability, culture, third-party | Risk taxonomy (GOV domain), risk appetite |
| MAP 1-5 | Context, categorization, impact | Risk identification, context establishment |
| MEASURE 1-4 | Metrics, evaluation, tracking | Risk scoring (MDRS), KRI monitoring |
| MANAGE 1-4 | Risk response, incidents, monitoring | Risk treatment workflow, escalation |

### 11.2 ISO 42001 Mapping

| ISO Clause | Requirement | GRC_Claw Risk Process |
|------------|-------------|----------------------|
| 6.1 | Actions to address risks | Risk scoring methodology, treatment workflow |
| 6.2 | AI objectives | Risk appetite thresholds |
| 8.2 | Risk management | Full risk assessment process |
| 8.5 | Monitoring and measurement | Continuous monitoring framework |
| 9.1 | Performance evaluation | Risk review cadence, control effectiveness |
| 10.1 | Continual improvement | Risk treatment feedback loop |
| 10.2 | Corrective action | Risk escalation and remediation |

### 11.3 EU AI Act Mapping

| EU AI Act Article | Requirement | GRC_Claw Risk Process |
|-------------------|-------------|----------------------|
| Art. 5 | Prohibited practices | Risk category CMP-01, immediate cessation |
| Art. 6 | Risk classification | MDRS-to-EU-tier mapping (§4.4) |
| Art. 9 | Risk management system | Full risk assessment process |
| Art. 9(2) | Risk identification and analysis | Risk identification methods (§5.1) |
| Art. 9(4) | Risk treatment measures | Mitigation control catalog (§7.3) |
| Art. 9(5) | Residual risk acceptability | Residual risk acceptance (§7.5) |
| Art. 10 | Data governance | DAT domain risks, data quality gates |
| Art. 11 | Technical documentation | Risk assessment documentation |
| Art. 12 | Logging | OPS-04 audit trail risk |
| Art. 13 | Transparency | HUM-01, MOD-04 risks |
| Art. 14 | Human oversight | HUM-03 risk, human-in-the-loop controls |
| Art. 15 | Accuracy, robustness, cybersecurity | MOD-01, MOD-03, SEC domain risks |
| Art. 27 | FRIA | HUM-01 risk, impact assessment workflow |
| Art. 43 | Conformity assessment | CMP-03 risk, assessment workflow |
| Art. 72 | Post-market monitoring | OPS-05 risk, continuous monitoring |
| Art. 73 | Incident reporting | OPS-02 risk, incident response |

### 11.4 OWASP Agentic Top 10 Mapping

| OWASP Risk | GRC_Claw Category | Treatment Control |
|------------|-------------------|-------------------|
| ASI01: Goal Hijack | SEC-02 | Goal integrity monitoring |
| ASI02: Tool Misuse | SEC-03 | Tool access controls |
| ASI03: Identity Abuse | SEC-04 | Identity management |
| ASI04: Supply Chain | SEC-05 | Supply chain verification |
| ASI05: Code Execution | SEC-06 | Sandboxing |
| ASI06: Memory Poisoning | DAT-05 | Data validation |
| ASI07: Inter-Agent Comm | SEC-07 | Communication security |
| ASI08: Cascading Failures | SEC-07 | Circuit breakers |
| ASI09: Trust Exploitation | HUM-04 | Trust calibration |
| ASI10: Rogue Agents | SEC-02 | Goal integrity + containment |

---

## 12. Appendices

### Appendix A: Risk Taxonomy Registry

Complete risk subcategory catalog maintained as a versioned YAML document in the GRC_Claw repository:

```
grc-claw/
└── risk-taxonomy/
    ├── taxonomy.yaml              # Full 3-level taxonomy
    ├── category-controls.yaml     # Category-to-control mappings
    ├── scoring-rules.yaml         # MDRS scoring rules
    └── risk-appetite.yaml         # Risk appetite thresholds
```

### Appendix B: Risk Scoring Worksheets

#### B.1 Likelihood Scale

| Score | Label | Description | Frequency |
|-------|-------|-------------|-----------|
| 1 | Rare | May only occur in exceptional circumstances | <1% per year |
| 2 | Unlikely | Could occur but not expected | 1–10% per year |
| 3 | Possible | Might occur at some time | 10–50% per year |
| 4 | Likely | Will probably occur in most circumstances | 50–90% per year |
| 5 | Almost Certain | Expected to occur in most circumstances | >90% per year |

#### B.2 Impact Scale

| Score | Label | Description | Example |
|-------|-------|-------------|---------|
| 1 | Negligible | No discernible impact | Minor inconvenience |
| 2 | Minor | Small impact, easily recoverable | Service degradation <1 hour |
| 3 | Moderate | Significant impact, recoverable with effort | Service outage 1–24 hours |
| 4 | Major | Severe impact, difficult to recover | Data breach, regulatory fine |
| 5 | Catastrophic | Existential impact | Business cessation, criminal liability |

#### B.3 Detectability Scale

| Score | Label | Description |
|-------|-------|-------------|
| 1 | Easy | Risk is immediately visible and detectable |
| 2 | Moderate | Risk is detectable with standard monitoring |
| 3 | Difficult | Risk requires specialized detection capability |
| 4 | Very Difficult | Risk is hidden and requires active investigation |
| 5 | Impossible | Risk cannot be detected before harm occurs |

#### B.4 Velocity Scale

| Score | Label | Description |
|-------|-------|-------------|
| 1 | Slow | Harm propagates over weeks or months |
| 2 | Moderate | Harm propagates over days |
| 3 | Fast | Harm propagates over hours |
| 4 | Very Fast | Harm propagates over minutes |
| 5 | Instant | Harm is immediate upon trigger |

#### B.5 Persistence Scale

| Score | Label | Description |
|-------|-------|-------------|
| 1 | Transient | Harm resolves automatically within minutes |
| 2 | Short-term | Harm resolves within hours |
| 3 | Medium-term | Harm resolves within days |
| 4 | Long-term | Harm persists for weeks or months |
| 5 | Permanent | Harm is irreversible |

### Appendix C: Risk Treatment Plan Template

```markdown
# Risk Treatment Plan: [RISK-ID]

## Risk Summary
- **Risk ID:** [RISK-2026-XXX]
- **Title:** [risk title]
- **Current MDRS:** [score] ([tier])
- **Target MDRS:** [score] ([tier])
- **Target Date:** [date]

## Treatment Strategy
- **Selected Strategy:** [Avoid/Transfer/Mitigate/Accept]
- **Rationale:** [why this strategy]

## Mitigation Controls

| # | Control | Description | Owner | Status | Evidence |
|---|---------|-------------|-------|--------|----------|
| 1 | [control name] | [description] | [owner] | [planned/implemented/verified] | [evidence ID] |
| 2 | ... | ... | ... | ... | ... |

## Residual Risk Assessment
- **Expected Residual MDRS:** [score]
- **Residual Risk Tier:** [tier]
- **Within Risk Appetite:** [Yes/No]

## Approval
- **Risk Owner:** [name, date, signature]
- **Approver:** [name, role, date, signature]

## Review Schedule
- **Next Review Date:** [date]
- **Review Trigger:** [event or schedule]
```

### Appendix D: Risk Register Export Format

The risk register can be exported in the following formats:

| Format | Use Case | Schema |
|--------|----------|--------|
| JSON | System integration | Risk Register JSON Schema |
| CSV | Spreadsheet analysis | Flattened risk register |
| OSCAL | Regulatory submission | OSCAL assessment-results |
| PDF | Executive reporting | Formatted risk register |
| XLSX | Audit review | Multi-sheet workbook |

### Appendix E: Glossary

| Term | Definition |
|------|-----------|
| **MDRS** | Multi-Dimensional Risk Score — composite score across 5 dimensions |
| **KRI** | Key Risk Indicator — metric that signals increasing risk |
| **Inherent Risk** | Risk before controls are applied |
| **Residual Risk** | Risk remaining after controls are applied |
| **Risk Appetite** | Level of risk the organization is willing to accept |
| **Risk Tier** | Classification of risk severity based on MDRS |
| **Risk Register** | Central repository of all identified and assessed risks |
| **Risk Treatment** | Process of modifying risk through controls |
| **Cascading Risk** | Risk that propagates from one system/component to another |
| **FRIA** | Fundamental Rights Impact Assessment (EU AI Act Art. 27) |
| **RMS** | Risk Management System (EU AI Act Art. 9) |
| **TEVV** | Test, Evaluation, Validation, and Verification |
| **AI-SBOM** | AI Bill of Materials — inventory of AI components and dependencies |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Architecture Team | Initial framework |

---

*This framework is a living document. It shall be reviewed and updated:*
- *After any significant AI incident*
- *When new AI regulations take effect*
- *When new AI use cases are introduced*
- *At minimum, annually*

---

*End of Framework*