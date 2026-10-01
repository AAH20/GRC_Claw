# GRC_Claw Unified Continuous Improvement Framework

## Synthesizing PDCA, NIST AI RMF, CMMI AIM, and Maturity Staging for Agentic AI Governance

---

## 1. Problem Statement

GRC_Claw's Wave 1 identified PDCA, NIST RMF, and maturity models as foundational frameworks. The gap: no unified operating model that connects governance theory to measurable, automated, agentic-AI-ready continuous improvement. This document proposes that unified framework.

---

## 2. Comparative Analysis of Source Frameworks

### 2.1 PDCA (Plan-Do-Check-Act)

| Dimension | Characteristic |
|-----------|---------------|
| **Origin** | Deming/Shewhart; embedded in ISO 42001 Clause 10 |
| **Loop Structure** | 4-phase iterative cycle |
| **CI Mechanism** | Clause 10.1 (continual improvement: suitability, adequacy, effectiveness) + Clause 10.2 (nonconformity & corrective action) |
| **Feedback Signals** | Monitoring results (9.1), internal audits (9.2), management reviews (9.3), incidents, corrective actions |
| **Automation Potential** | High — ISO 42001 explicitly requires evidence trails, not manual processes |
| **Agentic AI Fit** | Moderate — PDCA is human-centric; needs extension for autonomous loops |
| **Key Strength** | Universal, certifiable, audit-friendly |
| **Key Weakness** | No native metrics model; no maturity staging; no AI-specific guidance |

### 2.2 NIST AI RMF (Govern-Map-Measure-Manage)

| Dimension | Characteristic |
|-----------|---------------|
| **Origin** | NIST AI 100-1 (Jan 2023); voluntary, outcome-based |
| **Loop Structure** | 4 functions as continuous cycle; GOVERN is cross-cutting |
| **CI Mechanism** | GOVERN-5.2 (adjudicated feedback incorporation), MANAGE-4.2 (measurable continual improvement integrated into updates), MEASURE-4 (measurement efficacy feedback) |
| **Feedback Signals** | TEVV results, production monitoring, stakeholder engagement, incident feedback, drift detection |
| **Automation Potential** | High — MEASURE function is inherently automatable; MANAGE-4.2 requires release-gated improvement |
| **Agentic AI Fit** | High — explicitly addresses AI actors, emergent risk, third-party components |
| **Key Strength** | AI-specific, outcome-based, covers full lifecycle, addresses agentic risk |
| **Key Weakness** | No maturity levels; no prescriptive metrics; no certification path |

### 2.3 CMMI AIM (Artificial Intelligence Maturity)

| Dimension | Characteristic |
|-----------|---------------|
| **Origin** | CMMI Institute (Jul 2026); extends CMMI's proven appraisal method |
| **Loop Structure** | 8 domains (Data, Development, People, Safety, Security, etc.) × 5 maturity levels |
| **CI Mechanism** | Structured appraisals, crosswalks to ISO AI standards, performance analysis |
| **Feedback Signals** | Appraisal results, benchmark comparisons, domain-level gap analysis |
| **Automation Potential** | Moderate — appraisal-driven, not continuous; relies on periodic assessment |
| **Agentic AI Fit** | High — purpose-built for AI; covers all enterprise functions |
| **Key Strength** | Maturity staging, benchmarking, certified appraisal path, crosswalks |
| **Key Weakness** | New (2026); appraisal cadence is periodic not continuous; less operational than NIST |

### 2.4 Maturity Model Staging (CMMI Staged Representation)

| Level | Name | CI Characteristic |
|-------|------|-------------------|
| 0 | Incomplete | No CI mechanism; ad hoc |
| 1 | Initial | Reactive; hero-dependent; no repeatable process |
| 2 | Managed | Project-level process; planned, measured, controlled |
| 3 | Defined | Organization-wide standards; proactive; organizational assets |
| 4 | Quantitatively Managed | Data-driven; quantitative improvement objectives; predictable |
| 5 | Optimizing | Continuous improvement; incremental + innovative; causal analysis |

---

## 3. Gap Analysis: What Each Framework Lacks

| Gap | PDCA | NIST AI RMF | CMMI AIM | Maturity Staging |
|-----|------|-------------|----------|------------------|
| Unified operating model | ✗ | ✗ | Partial | ✗ |
| Standardized CI KPIs | ✗ | Partial (MEASURE 1) | Partial | ✗ |
| Automated feedback loops | ✗ | Partial | ✗ | ✗ |
| Agentic AI considerations | ✗ | Partial | Partial | ✗ |
| Maturity progression path | ✗ | ✗ | ✓ | ✓ |
| Certifiable audit trail | ✓ | ✗ | ✓ | ✗ |
| AI-specific guidance | ✗ | ✓ | ✓ | ✗ |
| Continuous (not periodic) cadence | ✓ | ✓ | ✗ | ✗ |

---

## 4. Proposed Unified Framework: GRC_Claw CI Engine

### 4.1 Architecture Overview

The framework integrates all four source models into a single operating system:

```
┌─────────────────────────────────────────────────────────────┐
│                    GRC_Claw CI ENGINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   │
│  │ GOVERN  │──▶│   MAP   │──▶│ MEASURE │──▶│ MANAGE  │   │
│  │(Cross-  │   │(Context │   │(Metrics │   │(Action  │   │
│  │ cutting)│   │ & Risk) │   │ & Eval) │   │ & Resp) │   │
│  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   │
│       │             │             │             │         │
│       └─────────────┴──────┬──────┴─────────────┘         │
│                            │                                │
│                    ┌───────▼───────┐                        │
│                    │  PDCA LOOP    │                        │
│                    │  (ISO 42001   │                        │
│                    │   Clause 10)  │                        │
│                    └───────┬───────┘                        │
│                            │                                │
│              ┌─────────────┼─────────────┐                  │
│              │             │             │                  │
│        ┌─────▼─────┐ ┌────▼────┐ ┌─────▼─────┐            │
│        │ CI KPI    │ │Feedback │ │ Maturity  │            │
│        │ Dashboard │ │ Engine  │ │ Staging   │            │
│        │ (Automated)│ │(Automated)│ │(CMMI AIM) │            │
│        └───────────┘ └─────────┘ └───────────┘            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           AGENTIC AI LAYER                          │   │
│  │  • Guarded autonomy (human-on-the-loop)             │   │
│  │  • Self-healing feedback loops                      │   │
│  │  • Recursive self-improvement governance            │   │
│  │  • Closed-loop control with audit trails            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 The Unified CI Cycle

The framework operates as a nested loop system:

**Outer Loop (PDCA / ISO 42001 Clause 10):**
- **Plan**: Set CI objectives, define KPIs, establish thresholds, assign owners
- **Do**: Execute governance operations, collect evidence, run controls
- **Check**: Measure KPI performance, audit effectiveness, review maturity
- **Act**: Remediate nonconformities, update controls, advance maturity

**Inner Loop (NIST AI RMF Functions):**
- **GOVERN**: Maintain policies, accountability, culture, third-party oversight
- **MAP**: Update context, risk profiles, impact characterizations
- **MEASURE**: Run TEVV, monitor production, track drift, evaluate trustworthiness
- **MANAGE**: Prioritize risks, respond to incidents, update treatments

**Feedback Loop (Automated):**
- Signals → Triage → Adjudication → Change → Verification → Learning

### 4.3 Maturity Staging for GRC_Claw

Adapted from CMMI AIM's 5-level model, mapped to CI capabilities:

| Level | Name | GRC_Claw CI Capability | Evidence |
|-------|------|----------------------|----------|
| 0 | **Ad Hoc** | No formal CI; reactive incident response only | Incident tickets, no trend analysis |
| 1 | **Reactive** | Basic monitoring; PDCA applied incident-by-incident | KPI dashboards, corrective action logs |
| 2 | **Managed** | Defined CI process; regular PDCA cycles; KPI tracking | Documented SOPs, KPI trends, audit trails |
| 3 | **Defined** | Organization-wide CI standards; automated feedback loops; maturity appraisals | CMMI AIM appraisal, crosswalk evidence, automated workflows |
| 4 | **Quantitatively Managed** | Data-driven CI; predictive analytics; quantitative improvement objectives | Statistical process control, predictive models, benchmark comparisons |
| 5 | **Optimizing** | Self-healing governance; recursive improvement; innovation-driven CI | Autonomous remediation, self-optimizing controls, innovation metrics |

---

## 5. Standardized CI KPIs

### 5.1 KPI Taxonomy

Organized into 4 categories aligned with NIST AI RMF functions:

#### A. Governance KPIs (GOVERN)

| KPI | Definition | Target | Source |
|-----|-----------|--------|--------|
| AI Inventory Coverage | Discovered AI systems ÷ registered & owned | 100% | NIST MEASURE 2.4 |
| Policy Violation Rate | Policy violations per 1,000 users/month | <5 | ISO 42001 9.1 |
| Access Control Coverage | AI systems behind SSO/least-privilege ÷ total | >95% | NIST GOVERN 1 |
| Agent Identity Coverage | Agents with unique identity + named owner ÷ total | 100% | OWASP ASI03 |
| Over-Privilege Ratio | Agent's actual access ÷ approved access | <1.2 | NIST MAP 2-4 |
| Third-Party AI Risk Coverage | Assessed third-party AI components ÷ total | 100% | NIST GOVERN 6 |

#### B. Measurement KPIs (MEASURE)

| KPI | Definition | Target | Source |
|-----|-----------|--------|--------|
| Model Drift Index | PSI/KL divergence from baseline | <0.2 | NIST MEASURE 3 |
| Task Success Rate | Successful task completions ÷ total | >90% | NIST MEASURE 2 |
| Harmful Output Rate | Harmful/unsafe outputs ÷ total outputs | <0.1% | NIST MEASURE 2.6 |
| Human Override Rate | Human interventions ÷ total decisions | Trending down | NIST MANAGE 2 |
| Evaluation Coverage | Systems with current TEVV ÷ total in scope | 100% | NIST MEASURE 2 |
| Red-Team Finding Closure | Closed findings ÷ total findings | >95% in SLA | NIST MEASURE 2.7 |

#### C. Management KPIs (MANAGE)

| KPI | Definition | Target | Source |
|-----|-----------|--------|--------|
| Risk Treatment Coverage | Risks with recorded response ÷ total identified | 100% | NIST MANAGE 1.3 |
| Residual Risk Acceptance Currency | Acceptances reviewed within expiry ÷ total | 100% | NIST MANAGE 1.3 |
| Incident MTTR | Mean time to remediate AI incidents | <24h (critical) | NIST MANAGE 4 |
| Deactivation Readiness | Systems with tested deactivation path ÷ total | 100% | NIST MANAGE 2 |
| Post-Update Verification Rate | Updates with post-release verification ÷ total | 100% | NIST MANAGE 4.2 |

#### D. Improvement KPIs (PDCA / ISO 42001 Clause 10)

| KPI | Definition | Target | Source |
|-----|-----------|--------|--------|
| Corrective Action Closure Rate | Closed CAs ÷ total CAs | >90% in SLA | ISO 42001 10.2 |
| CA Effectiveness Rate | CAs verified effective ÷ total closed | >95% | ISO 42001 10.2 |
| Improvement Cycle Time | Signal-to-remediation median time | Trending down | ISO 42001 10.1 |
| Maturity Level Progression | Domains advancing level per year | ≥1 domain/year | CMMI AIM |
| Stakeholder Engagement Rate | Scheduled engagements completed ÷ planned | >90% | NIST MANAGE 4.2 |
| Feedback Loop Closure Rate | Feedback items with verified resolution ÷ total | >95% | NIST GOVERN 5.2 |

### 5.2 KPI Governance

Each KPI must have:
- **Owner**: Named role accountable for the metric
- **Data Source**: Automated collection point (not manual surveys)
- **Threshold/Trigger**: Defined breach level that initiates action
- **Review Cadence**: Minimum frequency of formal review
- **Action Playbook**: Predefined response when threshold is breached
- **Evidence Trail**: Auditable record of measurement and decisions

---

## 6. Automated Feedback Loop Mechanisms

### 6.1 The 8-Stage Self-Healing Loop

Adapted from agentic self-healing research and NIST AI RMF:

```
┌──────────────────────────────────────────────────────────────┐
│                  AUTOMATED FEEDBACK LOOP                      │
│                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ 1. DETECT│───▶│ 2. TRIAGE│───▶│3. DIAGNOSE│───▶│4. PLAN  │  │
│  │         │    │         │    │         │    │         │  │
│  │Monitoring│    │Deduplicate│   │Root cause│    │Select   │  │
│  │Alerts   │    │Classify  │    │analysis  │    │remediation│ │
│  │Anomalies│    │Prioritize│    │Pattern   │    │candidate │  │
│  └─────────┘    └─────────┘    │matching  │    └────┬────┘  │
│                                 └─────────┘         │       │
│                                                     ▼       │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │8. LEARN │◀───│7. VERIFY│◀───│6.REMEDIATE│◀───│5.APPROVE│  │
│  │         │    │         │    │         │    │         │  │
│  │Update   │    │Confirm  │    │Execute  │    │Policy   │  │
│  │knowledge│    │fix worked│   │action   │    │gate     │  │
│  │base     │    │         │    │         │    │Human?   │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Automation Patterns by Maturity Level

| Maturity Level | Automation Pattern | Human Role |
|---------------|-------------------|------------|
| 0-1 | Manual detection, ticket-based response | Human-in-the-loop (full) |
| 2 | Automated alerting, dashboard monitoring | Human-in-the-loop (approval) |
| 3 | Automated triage, workflow routing, SLA tracking | Human-on-the-loop (oversight) |
| 4 | Predictive analytics, automated remediation for known patterns | Human-on-the-loop (exception) |
| 5 | Self-healing, recursive improvement, autonomous optimization | Human-on-the-loop (governance) |

### 6.3 Guarded Autonomy Model

For agentic AI systems, the framework adopts a **guarded autonomy** approach:

1. **Allowlist-based actions**: Agents can only execute actions from an explicit, version-controlled allowlist
2. **Risk-tiered approval**: Each action class carries a risk tier determining approval requirements
3. **Deterministic policy engine**: Layer 4 deterministic rules govern all agent actions
4. **Audit trail**: Every action logged to tamper-evident ledger
5. **Circuit breakers**: Kill-and-quarantine on invariant violation
6. **Compensating actions**: Rewind/rollback capability for irreversible operations

### 6.4 Feedback Loop Types

| Loop Type | Trigger | Response | Example |
|-----------|---------|----------|---------|
| **Threshold Breach** | KPI crosses defined threshold | Automated alert + playbook activation | Drift index > 0.2 |
| **Anomaly Detection** | Statistical deviation from baseline | Triage + investigation | Unusual tool call pattern |
| **Incident-Driven** | Production incident or harm | Full 8-stage loop | Harmful output detected |
| **Audit Finding** | Internal/external audit nonconformity | CAPA process (ISO 42001 10.2) | Missing documentation |
| **Stakeholder Feedback** | User report or engagement outcome | Adjudication workflow (GOVERN-5.2) | Bias complaint |
| **Regulatory Change** | New law or standard published | Impact assessment + gap analysis | EU AI Act update |
| **Maturity Appraisal** | Periodic CMMI AIM assessment | Improvement planning | Annual appraisal |

---

## 7. Agentic AI Considerations

### 7.1 Recursive Self-Improvement Governance

The framework addresses the unique challenge of AI systems that participate in their own improvement:

| Loop Closure Level | Description | GRC_Claw Approach |
|-------------------|-------------|-------------------|
| **Human-in-the-loop** | Human reviews each change | Default for high-risk decisions |
| **Human-on-the-loop** | Automated signal generation; human audits and gates | Standard for production agents |
| **Closed loop** | System generates, validates, applies own improvements | Restricted to low-risk, well-bounded domains with deterministic verification |

### 7.2 Agentic CI Patterns

1. **Self-Monitoring Agents**: Agents that monitor other agents' behavior for drift, permission escalation, and anomalous patterns
2. **Self-Remediation Agents**: Agents that can execute predefined remediation actions (rollback, reconfiguration) within guarded boundaries
3. **Self-Evaluation Agents**: Agents that run continuous evaluation suites against production traffic
4. **Self-Reporting Agents**: Agents that generate structured feedback reports for human review

### 7.3 Safety Constraints for Agentic CI

- **No self-modification of governance policies**: Agents cannot change their own governance rules
- **No self-approval of high-risk actions**: Risk tiers above threshold always require human approval
- **No unbounded self-improvement**: Improvement loops must have defined stopping conditions
- **Deterministic verification**: All self-improvements must be verifiable by deterministic tests before deployment
- **Tamper-evident logging**: All agent actions logged to append-only, cryptographically verifiable store

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Months 1-3)
- [ ] Establish CI governance structure (GOVERN)
- [ ] Define KPI taxonomy and baseline measurements
- [ ] Implement basic PDCA cycle with ISO 42001 Clause 10 alignment
- [ ] Deploy automated monitoring for Level 0-1 KPIs
- [ ] Create feedback intake and adjudication workflow

### Phase 2: Automation (Months 4-6)
- [ ] Implement automated feedback loops (8-stage model)
- [ ] Deploy KPI dashboards with threshold alerting
- [ ] Integrate with change management (MANAGE-4.2 release-gated improvement)
- [ ] Establish maturity baseline assessment (CMMI AIM Level 1-2)
- [ ] Implement corrective action tracking and effectiveness verification

### Phase 3: Intelligence (Months 7-9)
- [ ] Deploy predictive analytics for drift and anomaly detection
- [ ] Implement guarded autonomy for agentic systems
- [ ] Automate triage and routing for known issue patterns
- [ ] Advance to CMMI AIM Level 3 (Defined)
- [ ] Establish quantitative improvement objectives

### Phase 4: Optimization (Months 10-12)
- [ ] Implement self-healing for well-bounded, low-risk scenarios
- [ ] Deploy recursive self-improvement governance
- [ ] Advance to CMMI AIM Level 4 (Quantitatively Managed)
- [ ] Conduct first CMMI AIM appraisal
- [ ] Establish innovation-driven CI metrics

---

## 9. Framework Mapping: Source → Unified

| Unified Component | PDCA | NIST AI RMF | CMMI AIM | Maturity Staging |
|-------------------|------|-------------|----------|------------------|
| CI Governance Structure | Plan | GOVERN 1-2 | Data/People domains | Level 2+ |
| Context & Risk Assessment | Plan | MAP 1-5 | Safety/Security domains | Level 2+ |
| Metrics & Measurement | Check | MEASURE 1-4 | Development domain | Level 3+ |
| Risk Treatment & Response | Act | MANAGE 1-4 | All domains | Level 3+ |
| Corrective Action | Act | MANAGE 4.1 | All domains | Level 2+ |
| Continual Improvement | All phases | GOVERN 5.2, MANAGE 4.2 | All domains | Level 4+ |
| Maturity Appraisal | Check | — | Appraisal method | All levels |
| Automated Feedback | Do/Check | MEASURE 3-4 | — | Level 3+ |
| Agentic AI Governance | — | GOVERN 6, MAP 2-4 | Security domain | Level 3+ |
| Self-Healing | Act | MANAGE 1-2 | — | Level 4-5 |

---

## 10. Key Recommendations

1. **Adopt the nested loop architecture**: PDCA as the outer governance cycle, NIST AI RMF functions as the inner operational cycle, with automated feedback loops connecting them.

2. **Standardize on the 20-KPI dashboard**: Implement the KPI taxonomy in Section 5 as the single source of truth for CI measurement, with automated collection and threshold-based alerting.

3. **Implement guarded autonomy**: For agentic AI systems, adopt the human-on-the-loop model with deterministic policy enforcement, allowlist-based actions, and tamper-evident audit trails.

4. **Target CMMI AIM Level 3 within 12 months**: Use the maturity staging to drive prioritized improvement, with automated feedback loops as the primary mechanism for advancing from Level 2 to Level 3.

5. **Close the loop on every signal**: Every feedback item, whether from monitoring, incidents, audits, or stakeholders, must trace through the full 8-stage loop with verified resolution and learning capture.

6. **Automate the Check phase**: The highest ROI in CI automation is in the Check phase — automated KPI collection, threshold monitoring, and effectiveness verification.

7. **Govern recursive self-improvement**: Establish explicit boundaries for agentic AI self-improvement, with deterministic verification requirements and human oversight for any governance policy changes.

---

## 11. References

- NIST AI RMF 1.0 (AI 100-1, January 2023)
- NIST AI RMF Generative AI Profile (AI 600-1, July 2024)
- ISO/IEC 42001:2023 — AI Management System (Clause 10: Improvement)
- ISO/IEC 23894 — AI Risk Management
- CMMI AIM (CMMI Institute, July 2026)
- CMMI Staged Representation Maturity Levels 1-5
- Agentic Self-Healing Architecture (arXiv:2608.01955)
- Recursive Self-Improvement in AI (arXiv:2607.07663)
- CASE Framework for Enterprise Agentic AI (arXiv:2608.10153)
- AI Governance KPI Pack (AccuroAI, 2026)
- Enterprise AI Agent Governance Playbook (TechJack Solutions)

---

*Framework version 1.0 — GRC_Claw Continuous Improvement Engine*
