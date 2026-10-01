# GRC_Claw — Human Oversight Specification

**Document ID:** GRC-CLW-HO-001  
**Version:** 1.0  
**Classification:** Internal — AI Governance  
**Effective Date:** 2026-10-01  
**Owner:** GRC_Claw AI Governance Team  
**Review Cycle:** Quarterly (or upon material regulatory change)  
**Standards Alignment:** EU AI Act Art. 14, ISO/IEC 42001 A.6.2.8, NIST AI RMF GOVERN 3

---

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Regulatory & Standards Mapping](#2-regulatory--standards-mapping)
3. [Human Oversight Requirements](#3-human-oversight-requirements)
4. [Oversight Mechanisms](#4-oversight-mechanisms)
5. [Oversight Metrics](#5-oversight-metrics)
6. [Oversight Workflow](#6-oversight-workflow)
7. [Roles & Responsibilities](#7-roles--responsibilities)
8. [Implementation Roadmap](#8-implementation-roadmap)
9. [Appendices](#9-appendices)

---

## 1. Purpose & Scope

### 1.1 Purpose

This specification defines the human oversight framework for GRC_Claw's AI systems. It establishes the requirements, mechanisms, metrics, and workflows necessary to ensure meaningful human oversight of AI-driven decisions and agent actions. This addresses a critical gap identified in Wave 1 research: **no existing tool measures override rates, approval latency, or scalable human oversight effectiveness**.

### 1.2 Scope

| Dimension | Coverage |
|-----------|----------|
| **Systems** | All GRC_Claw AI modules — risk scoring, compliance mapping, policy enforcement, agent orchestration, reporting |
| **Decisions** | All AI-generated outputs that influence GRC decisions, regulatory filings, risk assessments, or compliance determinations |
| **Agents** | All autonomous AI agents that take actions (API calls, data modifications, notifications, workflow triggers) |
| **Personnel** | AI governance team, risk managers, compliance officers, business users, auditors |
| **Lifecycle** | Design, development, deployment, operation, monitoring, decommissioning |

### 1.3 Problem Statement

Wave 1 gap analysis revealed three critical deficiencies:

1. **Human oversight measurement is missing** — no tool measures whether oversight is meaningful, effective, or merely performative
2. **No override rate or approval latency tracking** — organizations cannot demonstrate to regulators that humans are actually in control
3. **Scalable human oversight is impractical** — reviewing every AI decision is infeasible; risk-based approaches are needed

This specification solves these problems by defining a **risk-tiered, measurable, and auditable** human oversight framework.

---

## 2. Regulatory & Standards Mapping

### 2.1 EU AI Act — Article 14 (Human Oversight)

| Art. 14 Requirement | GRC_Claw Implementation | Evidence |
|---------------------|------------------------|----------|
| **14(1)** — High-risk AI systems shall be designed and developed in such a way that they can be effectively overseen by natural persons during the period in which the AI system is in use | Human oversight controls embedded in all high-risk AI workflows; UI/UX designed for effective human interaction | Oversight UI screenshots, workflow documentation |
| **14(2)** — Oversight measures shall be built into the system in a way that allows for effective oversight | System-level oversight mechanisms (not just procedural); automated escalation triggers | System architecture docs, control inventory |
| **14(3)** — Oversight measures shall enable the individual to: | | |
| (a) Understand the capacities and limitations of the AI system | Model cards, confidence scores, explanation interfaces | Model registry, explanation UI |
| (b) Remain aware of the possible tendency of the AI system to over-rely or under-rely on human input | Overreliance detection, automation bias metrics | Overreliance KRI dashboard |
| (c) Correctly interpret the AI system's output | Explanation interfaces, confidence indicators, source citations | Explanation UI, citation verification |
| (d) Decide, in any particular situation, not to use the AI system or to override, reverse, or otherwise interrupt the output | Override mechanisms, kill switches, decision reversal workflows | Override logs, reversal audit trail |
| (e) Intervene on the operation of the AI system or interrupt the system through a "stop" button or a similar procedure | Emergency stop, circuit breaker, graceful degradation | Stop button logs, circuit breaker events |
| **14(4)** — The measures referred to in paragraph 3 shall be identified and documented in the technical documentation | Technical documentation includes oversight measure specifications | Technical documentation (Art. 11) |
| **14(5)** — For high-risk AI systems referred to in Annex III, point 1(a), the system shall be designed in a way that allows the user to override the decision and to take a different decision | Override capability for all Annex III high-risk decisions | Override workflow, decision reversal logs |

### 2.2 ISO/IEC 42001 — Clause A.6.2.8 (Human Oversight)

| ISO 42001 Requirement | GRC_Claw Implementation | Evidence |
|----------------------|------------------------|----------|
| **A.6.2.8.1** — The organization shall determine the need for human oversight of AI systems | Risk-based oversight classification; oversight requirements matrix per AI system | Oversight classification register |
| **A.6.2.8.2** — Where human oversight is required, the organization shall define: | | |
| (a) The roles and responsibilities of the human overseer | RACI matrix for oversight roles; role definitions | RACI chart, job descriptions |
| (b) The level of human oversight required | Risk-tiered oversight levels (L1-L4) | Oversight level assignment per system |
| (c) The information to be provided to the human overseer | Decision context package (inputs, confidence, alternatives, impact) | Decision context schema |
| (d) The actions available to the human overseer | Approve, reject, modify, escalate, override, stop | Oversight action inventory |
| (e) The criteria for escalation | Escalation triggers (risk score, confidence, anomaly, disagreement) | Escalation trigger configuration |
| **A.6.2.8.3** — The organization shall ensure that human oversight is effective and that the human overseer has the necessary competence, authority, and resources | Competence requirements, training, authority matrix, resource allocation | Training records, authority matrix |
| **A.6.2.8.4** — The organization shall monitor and measure the effectiveness of human oversight | Oversight effectiveness metrics (override rate, approval latency, escalation rate) | Oversight metrics dashboard |
| **A.6.2.8.5** — The organization shall improve human oversight based on monitoring results | Continuous improvement process for oversight | Improvement register, oversight review minutes |

### 2.3 NIST AI RMF — GOVERN 3 (Human Oversight)

| NIST AI RMF Category | GRC_Claw Implementation |
|----------------------|------------------------|
| GOVERN 3.1 — Human oversight is established and maintained | Oversight governance structure, policy, and procedures |
| GOVERN 3.2 — Human oversight is effective and meaningful | Effectiveness metrics, regular review, improvement cycle |
| GOVERN 3.3 — Human oversight is proportionate to risk | Risk-tiered oversight levels |
| GOVERN 3.4 — Human oversight is documented and auditable | Audit trail, oversight logs, evidence package |

### 2.4 Cross-Standard Alignment Matrix

| Oversight Element | EU AI Act Art. 14 | ISO 42001 A.6.2.8 | NIST AI RMF GOVERN 3 |
|--------------------|-------------------|---------------------|----------------------|
| Oversight requirement determination | 14(1) | A.6.2.8.1 | GOVERN 3.1 |
| Oversight mechanism design | 14(2), 14(3) | A.6.2.8.2 | GOVERN 3.1 |
| Override capability | 14(3)(d), 14(5) | A.6.2.8.2(d) | GOVERN 3.2 |
| Emergency stop | 14(3)(e) | A.6.2.8.2(d) | GOVERN 3.2 |
| Effectiveness monitoring | — | A.6.2.8.4 | GOVERN 3.2 |
| Competence & authority | — | A.6.2.8.3 | GOVERN 3.1 |
| Risk proportionality | 14(1) (high-risk focus) | A.6.2.8.1 | GOVERN 3.3 |
| Documentation & auditability | 14(4) | A.6.2.8.5 | GOVERN 3.4 |

---

## 3. Human Oversight Requirements

### 3.1 Oversight Classification

All GRC_Claw AI systems and agent actions are classified into one of four oversight levels based on risk:

| Level | Name | Description | Examples | Oversight Mechanism |
|-------|------|-------------|----------|---------------------|
| **L0** | No Oversight | Low-risk, fully automated decisions with no material impact | Data formatting, internal categorization, non-binding suggestions | Automated logging; periodic audit sampling |
| **L1** | Human-on-the-Loop | Low-to-moderate risk; human reviews outputs but is not required to act before execution | Risk scoring summaries, compliance gap reports, policy recommendations | Post-hoc review queue; batch approval; exception flagging |
| **L2** | Human-in-the-Loop | Moderate-to-high risk; human approval required before action execution | Regulatory filing recommendations, high-risk compliance determinations, significant risk assessments | Pre-execution approval gate; synchronous review; timeout escalation |
| **L3** | Human-in-Command | High-risk; human must initiate, direct, and confirm each action | Enforcement actions, data subject rights decisions, cross-border data transfers, model deployment | Human-initiated workflow; step-by-step confirmation; dual authorization |

### 3.2 Oversight Requirement Determination

The oversight level for each AI system or agent action is determined by:

```
Oversight Level = f(Decision Impact, Reversibility, Autonomy, Regulatory Classification)
```

| Factor | Weight | L0 Criteria | L1 Criteria | L2 Criteria | L3 Criteria |
|--------|--------|-------------|-------------|-------------|-------------|
| **Decision Impact** | 30% | No material impact | Minor operational impact | Significant business impact | Major legal/financial impact |
| **Reversibility** | 25% | Fully reversible | Reversible with effort | Partially reversible | Irreversible |
| **Autonomy** | 25% | No autonomous action | Suggests actions | Executes with approval | Executes autonomously |
| **Regulatory Classification** | 20% | Not regulated | Low-risk (Art. 50) | Limited-risk (Art. 50) | High-risk (Annex III) |

**Scoring:** Each factor scored 1-4. Weighted sum determines oversight level:
- 1.0-1.5 → L0
- 1.6-2.5 → L1
- 2.6-3.5 → L2
- 3.6-4.0 → L3

### 3.3 Mandatory Oversight Triggers

Regardless of classification, human oversight is **mandatory** when any of the following conditions are met:

| Trigger | Description | Oversight Level | Response Time |
|---------|-------------|-----------------|---------------|
| **T1: High Risk Score** | AI risk score exceeds threshold (configurable per system) | Minimum L2 | 1 hour |
| **T2: Low Confidence** | Model confidence below threshold (configurable per model) | Minimum L2 | 1 hour |
| **T3: Anomaly Detected** | Output deviates from expected distribution or pattern | Minimum L2 | 30 minutes |
| **T4: Regulatory Trigger** | Decision affects regulated activity or data subject rights | Minimum L2 | 1 hour |
| **T5: Override Request** | User or stakeholder requests human review | Minimum L2 | 30 minutes |
| **T6: Disagreement** | Multiple AI systems produce conflicting recommendations | Minimum L2 | 1 hour |
| **T7: Novel Situation** | Input pattern outside training distribution | Minimum L2 | 1 hour |
| **T8: Escalation** | Lower-level oversight cannot resolve the issue | Next level up | Per SLA |
| **T9: Emergency** | Potential for imminent harm or breach | L3 | Immediate |
| **T10: Audit/Regulatory** | Audit finding or regulatory inquiry | L3 | Immediate |

### 3.4 Oversight Exceptions

Exceptions to mandatory oversight requirements must be:

1. **Documented** — written justification for the exception
2. **Approved** — authorized by the AI Governance Board or designated authority
3. **Time-bound** — maximum 30 days, renewable with re-approval
4. **Compensating controls** — alternative risk mitigation measures in place
5. **Logged** — recorded in the oversight exception register
6. **Reviewed** — assessed at each review cycle

---

## 4. Oversight Mechanisms

### 4.1 Mechanism Overview

GRC_Claw implements three categories of oversight mechanisms, aligned with the spectrum of human control:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OVERSIGHT MECHANISM SPECTRUM                      │
│                                                                       │
│  Human-in-the-Loop ◄──────────► Human-on-the-Loop ◄──────► Human-in-Command  │
│  (HITL)                         (HOTL)                        (HIC)       │
│                                                                       │
│  • Pre-execution approval      • Post-hoc review              • Human-initiated  │
│  • Synchronous gate            • Batch approval               • Step-by-step    │
│  • Real-time interaction       • Exception flagging           • Dual authorization│
│  • Timeout escalation          • Sampling audit               • Continuous confirm│
│                                                                       │
│  High control ◄──────────────────────────────────────────► High autonomy │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Human-in-the-Loop (HITL) Mechanisms

| Mechanism | Description | Use Case | Implementation |
|-----------|-------------|----------|----------------|
| **Approval Gate** | Human must approve before action executes | L2 decisions; high-risk compliance determinations | Workflow engine blocks execution until approval received |
| **Synchronous Review** | Real-time human review of AI output before presentation | Risk assessments, regulatory recommendations | UI presents AI output with approve/reject/modify options |
| **Interactive Refinement** | Human iteratively refines AI output | Complex GRC analyses, policy drafting | Multi-turn conversation with human feedback loop |
| **Dual Authorization** | Two humans must approve | L3 decisions; irreversible actions | Workflow requires two independent approvals |
| **Timeout Escalation** | If human doesn't respond within SLA, escalates | Urgent decisions with oversight requirement | Escalation chain: primary → backup → manager → auto-defer |
| **Context Package** | Human receives full decision context | All HITL decisions | Structured package: inputs, confidence, alternatives, impact, citations |

### 4.3 Human-on-the-Loop (HOTL) Mechanisms

| Mechanism | Description | Use Case | Implementation |
|-----------|-------------|----------|----------------|
| **Review Queue** | Post-hoc review of AI decisions | L1 decisions; batch processing | Queue with priority scoring; SLA tracking |
| **Exception Flagging** | AI flags uncertain or anomalous decisions for review | Low confidence, anomalies, novel patterns | Automated flagging based on confidence/anomaly thresholds |
| **Sampling Audit** | Random sample of decisions reviewed | Quality assurance; oversight effectiveness | Configurable sampling rate (e.g., 5-20%) |
| **Dashboard Monitoring** | Real-time oversight dashboard | Continuous monitoring of AI behavior | Metrics dashboard with KRIs and alerts |
| **Periodic Review** | Scheduled review of AI system performance | Effectiveness assessment; drift detection | Weekly/monthly review cycles |
| **Override Capability** | Human can override any AI decision | All levels | Override button with reason capture and audit trail |

### 4.4 Human-in-Command (HIC) Mechanisms

| Mechanism | Description | Use Case | Implementation |
|-----------|-------------|----------|----------------|
| **Human-Initiated Workflow** | Human defines task, AI assists | L3 decisions; complex multi-step actions | Workflow starts from human request, not AI initiative |
| **Step-by-Step Confirmation** | Human confirms each step of agent action | Autonomous agent operations | Agent pauses at each step for human confirmation |
| **Kill Switch** | Immediate stop of all AI operations | Emergency; imminent harm | Global stop button; circuit breaker pattern |
| **Graceful Degradation** | System falls back to safe mode | System failure or compromise | Automatic fallback to rule-based or manual operation |
| **Authority Matrix** | Clear decision rights and escalation paths | All levels | RACI matrix with authority levels |
| **Circuit Breaker** | Automatic halt when thresholds breached | Anomaly detection; risk thresholds | Automated halt with human notification |

### 4.5 Mechanism Selection Matrix

| Oversight Level | Primary Mechanism | Secondary Mechanism | Emergency Mechanism |
|-----------------|-------------------|---------------------|---------------------|
| **L0** | Automated logging | Periodic audit sampling | Kill switch |
| **L1** | Review queue | Exception flagging | Override + kill switch |
| **L2** | Approval gate | Synchronous review | Timeout escalation + kill switch |
| **L3** | Human-initiated workflow | Step-by-step confirmation | Kill switch + graceful degradation |

### 4.6 Override Mechanisms

| Override Type | Description | Authority | Audit Requirement |
|---------------|-------------|-----------|-------------------|
| **Decision Override** | Human reverses or modifies AI decision | Assigned overseer | Full audit trail with reason |
| **Process Override** | Human bypasses standard workflow | Manager+ | Justification + approval |
| **Policy Override** | Human approves exception to policy | AI Governance Board | Exception register entry |
| **System Override** | Human disables AI system or component | CISO + AI Governance | Incident record + root cause |
| **Emergency Override** | Immediate stop of all AI operations | Any authorized user | Post-incident review within 24h |

---

## 5. Oversight Metrics

### 5.1 Metric Framework

GRC_Claw defines **12 core oversight metrics** organized into four categories:

```
┌─────────────────────────────────────────────────────────────┐
│                  OVERSIGHT METRICS FRAMEWORK                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  CATEGORY 1: OVERSIGHT COVERAGE                              │
│  ├── OV-001: Oversight Coverage Rate                         │
│  ├── OV-002: High-Risk Decision Oversight Rate               │
│  └── OV-003: Agent Action Oversight Rate                    │
│                                                               │
│  CATEGORY 2: OVERSIGHT EFFECTIVENESS                         │
│  ├── OV-004: Override Rate                                   │
│  ├── OV-005: Approval Latency                                │
│  ├── OV-006: Escalation Rate                                 │
│  └── OV-007: Overreliance Rate                               │
│                                                               │
│  CATEGORY 3: OVERSIGHT QUALITY                               │
│  ├── OV-008: Decision Reversal Rate                          │
│  ├── OV-009: Time to Detect Anomaly                          │
│  └── OV-010: Oversight Review Completion Rate                │
│                                                               │
│  CATEGORY 4: OVERSIGHT GOVERNANCE                            │
│  ├── OV-011: Oversight Training Compliance                    │
│  └── OV-012: Oversight Exception Rate                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Metric Definitions

#### OV-001: Oversight Coverage Rate

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of AI decisions and agent actions that have an assigned oversight level and mechanism |
| **Formula** | (Decisions with oversight / Total decisions) × 100 |
| **Target** | 100% |
| **Measurement Frequency** | Continuous |
| **Data Source** | Decision log, agent telemetry |
| **Owner** | AI Governance Lead |
| **Escalation Threshold** | <95% → Operational; <90% → Management; <85% → Board |
| **Standards Mapping** | ISO 42001 A.6.2.8.1; EU AI Act 14(1) |

#### OV-002: High-Risk Decision Oversight Rate

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of high-risk decisions (L2+) that received the required level of human oversight |
| **Formula** | (High-risk decisions with required oversight / Total high-risk decisions) × 100 |
| **Target** | 100% |
| **Measurement Frequency** | Real-time |
| **Data Source** | Approval workflow, decision log |
| **Owner** | AI Risk Officer |
| **Escalation Threshold** | <100% → Immediate operational alert; any miss → Management |
| **Standards Mapping** | EU AI Act 14(1), 14(5); ISO 42001 A.6.2.8.2 |

#### OV-003: Agent Action Oversight Rate

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of autonomous agent actions that were subject to appropriate oversight |
| **Formula** | (Agent actions with oversight / Total agent actions) × 100 |
| **Target** | 100% for L2+ actions; ≥95% for L1 actions |
| **Measurement Frequency** | Real-time |
| **Data Source** | Agent telemetry, action log |
| **Owner** | CISO |
| **Escalation Threshold** | <100% for L2+ → Immediate; <95% for L1 → Operational |
| **Standards Mapping** | ISO 42001 A.6.2.8.2; NIST AI RMF GOVERN 3.1 |

#### OV-004: Override Rate

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of AI decisions that were overridden by a human |
| **Formula** | (Overridden decisions / Total decisions presented for oversight) × 100 |
| **Target** | 2-15% (risk-tier dependent); investigate if outside range |
| **Measurement Frequency** | Daily |
| **Data Source** | Override log, decision audit trail |
| **Owner** | AI Governance Lead |
| **Escalation Threshold** | <1% → Potential overreliance; >20% → Potential underperformance; >30% → System review required |
| **Standards Mapping** | ISO 42001 A.6.2.8.4; NIST AI RMF GOVERN 3.2 |
| **Notes** | Override rate is a **key indicator of oversight effectiveness**. Very low rates may indicate automation bias (humans rubber-stamping). Very high rates may indicate poor AI performance or misaligned oversight thresholds. |

#### OV-005: Approval Latency

| Attribute | Value |
|-----------|-------|
| **Definition** | Average time from oversight request to human decision |
| **Formula** | Σ(Decision time - Request time) / Number of decisions |
| **Target** | L2: <1 hour; L3: <30 minutes |
| **Measurement Frequency** | Real-time |
| **Data Source** | Approval workflow timestamps |
| **Owner** | AI Governance Lead |
| **Escalation Threshold** | L2: >2 hours → Operational; >4 hours → Management. L3: >1 hour → Operational; >2 hours → Management |
| **Standards Mapping** | ISO 42001 A.6.2.8.4; EU AI Act 14(3) |
| **Notes** | Approval latency measures **responsiveness of the oversight system**. High latency may indicate insufficient staffing, unclear decision criteria, or oversight fatigue. |

#### OV-006: Escalation Rate

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of decisions that required escalation to a higher oversight level |
| **Formula** | (Escalated decisions / Total decisions) × 100 |
| **Target** | <10% for L1; <5% for L2; <2% for L3 |
| **Measurement Frequency** | Daily |
| **Data Source** | Escalation log, workflow engine |
| **Owner** | AI Risk Officer |
| **Escalation Threshold** | >15% → Operational review; >25% → Management review; >40% → System redesign |
| **Standards Mapping** | ISO 42001 A.6.2.8.2(e); NIST AI RMF GOVERN 3.2 |
| **Notes** | High escalation rate may indicate misaligned oversight thresholds, insufficient authority at lower levels, or increasing risk in AI outputs. |

#### OV-007: Overreliance Rate

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of decisions where the human approved the AI output without modification or meaningful review |
| **Formula** | (Unmodified approvals / Total approvals) × 100 |
| **Target** | <80% (investigate if consistently above) |
| **Measurement Frequency** | Weekly |
| **Data Source** | Approval log, time-on-task analytics |
| **Owner** | AI Governance Lead |
| **Escalation Threshold** | >90% → Automation bias investigation; >95% → Oversight redesign |
| **Standards Mapping** | EU AI Act 14(3)(b); ISO 42001 A.6.2.8.4 |
| **Notes** | Overreliance rate detects **automation bias** — the tendency to trust AI outputs without critical evaluation. Measured via time-on-task, modification rate, and decision patterns. |

#### OV-008: Decision Reversal Rate

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of AI decisions that were later reversed or modified after initial human approval |
| **Formula** | (Reversed decisions / Total approved decisions) × 100 |
| **Target** | <5% |
| **Measurement Frequency** | Weekly |
| **Data Source** | Decision audit trail, reversal log |
| **Owner** | AI Risk Officer |
| **Escalation Threshold** | >10% → Operational review; >20% → Management review |
| **Standards Mapping** | ISO 42001 A.6.2.8.4; NIST AI RMF GOVERN 3.2 |
| **Notes** | High reversal rate may indicate that initial oversight was inadequate or that conditions changed after approval. |

#### OV-009: Time to Detect Anomaly

| Attribute | Value |
|-----------|-------|
| **Definition** | Average time from anomalous AI behavior to detection by oversight mechanisms |
| **Formula** | Σ(Detection time - Anomaly occurrence time) / Number of anomalies |
| **Target** | <5 minutes for critical; <1 hour for high; <4 hours for medium |
| **Measurement Frequency** | Per anomaly |
| **Data Source** | Anomaly detection system, monitoring logs |
| **Owner** | CISO |
| **Escalation Threshold** | Critical: >15 min; High: >1 hour; Medium: >4 hours |
| **Standards Mapping** | ISO 42001 A.6.2.8.4; NIST AI RMF GOVERN 3.2 |

#### OV-010: Oversight Review Completion Rate

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of oversight reviews completed within SLA |
| **Formula** | (Reviews within SLA / Total reviews) × 100 |
| **Target** | ≥95% |
| **Measurement Frequency** | Daily |
| **Data Source** | Review queue, workflow engine |
| **Owner** | AI Governance Lead |
| **Escalation Threshold** | <90% → Operational; <80% → Management |
| **Standards Mapping** | ISO 42001 A.6.2.8.4 |

#### OV-011: Oversight Training Compliance

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of oversight personnel who have completed required training |
| **Formula** | (Trained personnel / Total oversight personnel) × 100 |
| **Target** | 100% |
| **Measurement Frequency** | Monthly |
| **Data Source** | LMS, training records |
| **Owner** | HR + AI Governance |
| **Escalation Threshold** | <100% → Immediate; <90% → Management |
| **Standards Mapping** | ISO 42001 A.6.2.8.3; EU AI Act 14(3) |

#### OV-012: Oversight Exception Rate

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of decisions processed under an oversight exception |
| **Formula** | (Decisions with exception / Total decisions) × 100 |
| **Target** | <1% |
| **Measurement Frequency** | Monthly |
| **Data Source** | Exception register |
| **Owner** | AI Governance Lead |
| **Escalation Threshold** | >5% → Operational review; >10% → Management review |
| **Standards Mapping** | ISO 42001 A.6.2.8.1 |

### 5.3 Metric Escalation Thresholds

| Metric | Tier 1 (Operational) | Tier 2 (Management) | Tier 3 (Board) |
|--------|---------------------|---------------------|----------------|
| OV-001 Oversight Coverage | <95% | <90% | <85% |
| OV-002 High-Risk Oversight | <100% | Any miss | Any regulatory reportable miss |
| OV-003 Agent Action Oversight | <100% (L2+) | <95% (L1) | Any unauthorized action |
| OV-004 Override Rate | <1% or >20% | >30% | >40% or pattern of overreliance |
| OV-005 Approval Latency | >2x target | >4x target | Regulatory deadline risk |
| OV-006 Escalation Rate | >15% | >25% | >40% |
| OV-007 Overreliance Rate | >90% | >95% | Pattern indicating systemic issue |
| OV-008 Decision Reversal Rate | >10% | >20% | >30% |
| OV-009 Time to Detect Anomaly | >2x target | >4x target | Any critical anomaly undetected >1h |
| OV-010 Review Completion | <90% | <80% | <70% |
| OV-011 Training Compliance | <100% | <90% | <80% |
| OV-012 Exception Rate | >5% | >10% | >20% |

### 5.4 Metric Data Model

```yaml
oversight_event:
  id: "OE-20261001-0001"
  timestamp: "2026-10-01T14:30:00Z"
  system_id: "GRC-RISK-001"
  decision_id: "DEC-20261001-0042"
  agent_id: "AGENT-COMPLIANCE-003"  # if applicable
  oversight_level: "L2"
  mechanism: "approval_gate"
  
  # Decision context
  decision_type: "compliance_determination"
  risk_score: 0.72
  confidence: 0.85
  impact: "high"
  reversibility: "partial"
  
  # Oversight details
  overseer_id: "user-12345"
  overseer_role: "compliance_officer"
  request_time: "2026-10-01T14:30:00Z"
  decision_time: "2026-10-01T14:45:00Z"
  decision: "approved"  # approved | rejected | modified | escalated | overridden
  decision_reason: "Reviewed against regulatory guidance; confirmed accurate"
  time_on_task_seconds: 900
  
  # Override details (if applicable)
  override: false
  override_reason: null
  original_recommendation: null
  
  # Escalation details (if applicable)
  escalated: false
  escalation_reason: null
  escalation_target: null
  
  # Audit
  audit_trail_id: "AT-20261001-0001"
  evidence_package_id: "EP-20261001-0001"
```

---

## 6. Oversight Workflow

### 6.1 Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     HUMAN OVERSIGHT WORKFLOW                             │
│                                                                           │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐ │
│  │ AI System │──▶│ Oversight│──▶│ Decision │──▶│ Human    │──▶│ Action │ │
│  │ Generates │   │ Level    │   │ Context  │   │ Review   │   │ Execute│ │
│  │ Output    │   │ Assigned │   │ Package  │   │ & Decide │   │ or Hold│ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └────────┘ │
│       │              │              │              │              │      │
│       ▼              ▼              ▼              ▼              ▼      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐ │
│  │ Risk     │   │ L0: Auto │   │ Inputs   │   │ Approve  │   │ Execute│ │
│  │ Score &  │   │ L1: Queue│   │ Confidence│   │ Reject   │   │ Log   │ │
│  │ Confidence│   │ L2: Gate │   │ Impact   │   │ Modify   │   │ Notify│ │
│  │ Anomaly  │   │ L3: HIC  │   │ Alternatives│ │ Escalate │   │ Audit │ │
│  │ Detection│   │          │   │ Citations│   │ Override │   │       │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └────────┘ │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐│
│  │                      FEEDBACK LOOP                                    ││
│  │  Override patterns → Model retraining → Oversight threshold tuning   ││
│  │  Escalation patterns → Authority adjustment → Training needs         ││
│  │  Reversal patterns → Decision criteria update → Process improvement  ││
│  └──────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Workflow by Oversight Level

#### L0: No Oversight Workflow

```
1. AI system generates output
2. System logs output with metadata
3. Automated quality checks run
4. Output delivered to user
5. Periodic audit sampling (configurable rate)
6. Metrics recorded (OV-001, OV-003)
```

#### L1: Human-on-the-Loop Workflow

```
1. AI system generates output
2. System assigns risk score and confidence
3. Output added to review queue (priority scored)
4. System checks for automatic triggers (T1-T10)
   ├── If trigger activated → escalate to L2
   └── If no trigger → continue
5. Human reviews output from queue
   ├── Approve → output delivered, logged
   ├── Modify → output modified, logged with reason
   ├── Reject → output discarded, logged with reason
   └── Escalate → move to L2 workflow
6. Metrics recorded (OV-004, OV-005, OV-007, OV-010)
7. Periodic sampling audit for quality assurance
```

#### L2: Human-in-the-Loop Workflow

```
1. AI system generates output
2. System creates decision context package
3. Approval gate blocks execution
4. Oversight request sent to assigned overseer
5. System starts approval latency timer
6. Human reviews decision context package
   ├── Approve → action executes, logged
   ├── Reject → action blocked, logged with reason
   ├── Modify → action modified, logged with reason
   ├── Override → human decision replaces AI, logged
   └── Escalate → move to L3 workflow
7. If no response within SLA:
   ├── Timeout escalation to backup overseer
   ├── If still no response → auto-defer or auto-reject (configurable)
8. Metrics recorded (OV-002, OV-004, OV-005, OV-006, OV-008)
9. Audit trail generated
```

#### L3: Human-in-Command Workflow

```
1. Human initiates workflow request
2. AI system prepares recommendation and context
3. Human reviews recommendation
4. Human defines action plan (with AI assistance)
5. For each step:
   a. AI prepares step details
   b. Human reviews and confirms
   c. Step executes
   d. Results logged
   e. Human confirms continuation
6. At any point, human can:
   ├── Modify the plan
   ├── Pause the workflow
   ├── Stop the workflow (kill switch)
   └── Escalate to higher authority
7. Dual authorization required for irreversible actions
8. Metrics recorded (OV-002, OV-003, OV-004, OV-005, OV-006)
9. Full audit trail with step-by-step evidence
```

### 6.3 Escalation Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ESCALATION WORKFLOW                            │
│                                                                   │
│  Level 1: Assigned Overseer                                      │
│  ├── Primary reviewer for the decision                           │
│  ├── SLA: L2 <1 hour, L3 <30 minutes                             │
│  └── If timeout → escalate to Level 2                            │
│                                                                   │
│  Level 2: Backup Overseer / Team Lead                            │
│  ├── Secondary reviewer or team lead                             │
│  ├── SLA: 2x Level 1 SLA                                         │
│  └── If timeout → escalate to Level 3                            │
│                                                                   │
│  Level 3: Manager / AI Risk Officer                              │
│  ├── Management-level decision authority                          │
│  ├── SLA: 4x Level 1 SLA                                         │
│  └── If timeout → escalate to Level 4                            │
│                                                                   │
│  Level 4: AI Governance Board / Emergency Response               │
│  ├── Governance board or emergency response team                 │
│  ├── SLA: Best effort                                            │
│  └── If unresolved → auto-defer or auto-reject (configurable)    │
│                                                                   │
│  Special: Regulatory Escalation                                   │
│  ├── If regulatory deadline risk → immediate management alert     │
│  ├── If data subject rights → DPO notification                    │
│  └── If serious incident → Art. 73 notification workflow         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 6.4 Override Workflow

```
1. Human initiates override
   ├── Decision override: select decision → click "Override"
   ├── Process override: select workflow → click "Bypass"
   ├── Policy override: select policy → click "Exception"
   └── Emergency override: click "Stop All" (kill switch)

2. System captures override context
   ├── Reason for override (required, structured)
   ├── Supporting evidence (optional)
   ├── Alternative decision (if applicable)
   └── Authorization level check

3. System validates override authority
   ├── Check user role and permissions
   ├── Check override type authorization
   └── If insufficient → escalate

4. System executes override
   ├── Log override with full context
   ├── Update decision record
   ├── Notify relevant stakeholders
   └── Trigger downstream actions

5. Post-override review
   ├── 24-hour review for emergency overrides
   ├── Weekly review for policy overrides
   ├── Monthly analysis of override patterns
   └── Feedback to model retraining pipeline
```

### 6.5 Emergency Stop Workflow

```
1. TRIGGER: Any authorized user activates emergency stop
   ├── UI: Global "Stop All" button
   ├── API: POST /api/v1/emergency-stop
   └── Automated: Circuit breaker threshold breached

2. IMMEDIATE ACTION (<1 second)
   ├── Halt all AI agent actions
   ├── Block all AI system outputs
   ├── Preserve system state for forensics
   └── Activate graceful degradation mode

3. NOTIFICATION (<5 seconds)
   ├── Alert all oversight personnel
   ├── Alert AI Governance Board
   ├── Alert CISO and CLO
   └── Log emergency stop event

4. ASSESSMENT (<15 minutes)
   ├── Determine scope of emergency
   ├── Assess potential harm
   ├── Identify root cause
   └── Decide: resume, degrade, or shutdown

5. RESOLUTION
   ├── Resume: Gradual restoration with enhanced monitoring
   ├── Degrade: Continue in safe mode with reduced AI capability
   └── Shutdown: Full system shutdown with manual fallback

6. POST-INCIDENT (<24 hours)
   ├── Root cause analysis
   ├── Impact assessment
   ├── Corrective actions
   └── Regulatory notification (if required)
```

---

## 7. Roles & Responsibilities

### 7.1 Oversight Governance Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    BOARD OF DIRECTORS                        │
│         • Oversight policy approval                          │
│         • Risk appetite for AI autonomy                      │
│         • Oversight effectiveness review                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              AI GOVERNANCE BOARD                             │
│  • Oversight level assignments                               │
│  • Override authority matrix                                 │
│  • Oversight exception approvals                             │
│  • Oversight effectiveness review                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              OVERSIGHT OPERATIONS                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ AI Risk      │  │ Compliance   │  │ CISO         │      │
│  │ Officer      │  │ Officer      │  │              │      │
│  │              │  │              │  │              │      │
│  │ • Risk-based │  │ • Regulatory │  │ • Agent      │      │
│  │   oversight  │  │   oversight  │  │   oversight  │      │
│  │ • Escalation │  │ • Audit      │  │ • Emergency  │      │
│  │   management │  │   readiness  │  │   response   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Business     │  │ Oversight    │  │ Internal     │      │
│  │ Owners       │  │ Personnel    │  │ Audit        │      │
│  │              │  │              │  │              │      │
│  │ • Decision   │  │ • Day-to-day │  │ • Oversight  │      │
│  │   oversight  │  │   review     │  │   audit      │      │
│  │ • Context    │  │ • Approvals  │  │ • Compliance │      │
│  │   provision  │  │ • Overrides  │  │   verification│     │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 RACI Matrix

| Activity | Board | AI Gov Board | AI Risk Officer | Compliance Officer | CISO | Business Owner | Oversight Personnel | Internal Audit |
|----------|-------|--------------|-----------------|-------------------|------|----------------|---------------------|----------------|
| Oversight policy | A | R | C | C | C | I | I | C |
| Oversight level assignment | I | A | R | C | C | C | I | I |
| Day-to-day oversight | I | I | I | I | I | A | R | I |
| Override decisions | I | I | C | C | C | A | R | I |
| Escalation management | I | A | R | C | C | I | I | I |
| Emergency stop | I | I | C | C | A | I | R | I |
| Oversight metrics review | I | A | R | C | C | I | I | C |
| Oversight effectiveness review | A | R | C | C | C | I | I | R |
| Exception approval | I | A | R | C | C | I | I | I |
| Training & competence | I | A | C | C | C | R | R | I |

*R = Responsible, A = Accountable, C = Consulted, I = Informed*

### 7.3 Competence Requirements

| Role | Required Competence | Training | Certification | Refresh |
|------|---------------------|----------|---------------|---------|
| **Oversight Personnel** | AI system understanding, domain expertise, regulatory awareness | 16 hours initial + 8 hours annual | AI Oversight Fundamentals | Annual |
| **AI Risk Officer** | Risk management, AI/ML knowledge, regulatory frameworks | 40 hours initial + 16 hours annual | ISO 42001 Lead Implementer, AI Risk Management | Annual |
| **Compliance Officer** | Regulatory expertise, AI governance, audit | 32 hours initial + 12 hours annual | AI Compliance Certification | Annual |
| **CISO** | Security, AI security, incident response | 40 hours initial + 16 hours annual | CISSP, AI Security Certification | Annual |
| **Business Owner** | Domain expertise, AI literacy, decision-making | 8 hours initial + 4 hours annual | AI Literacy for Executives | Bi-annual |

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Months 1-3)

| Week | Activity | Deliverable |
|------|----------|-------------|
| 1-2 | Oversight classification of all AI systems | Oversight classification register |
| 3-4 | Define oversight levels and mechanisms | Oversight level assignments |
| 5-6 | Implement L0 and L1 workflows | Review queue, logging, basic metrics |
| 7-8 | Deploy oversight metrics dashboard (OV-001 to OV-003) | Metrics dashboard v1 |
| 9-10 | Define escalation triggers and workflow | Escalation configuration |
| 11-12 | Train initial oversight personnel | Training records, competence matrix |

### Phase 2: Core Oversight (Months 4-6)

| Week | Activity | Deliverable |
|------|----------|-------------|
| 13-14 | Implement L2 approval gate workflow | Approval gate, context package |
| 15-16 | Deploy override mechanism | Override workflow, audit trail |
| 17-18 | Implement escalation workflow | Escalation chain, timeout handling |
| 19-20 | Deploy OV-004 to OV-008 metrics | Full metrics dashboard |
| 21-22 | Implement emergency stop | Kill switch, circuit breaker |
| 23-24 | Integration testing and refinement | Test report, refined workflows |

### Phase 3: Advanced Oversight (Months 7-9)

| Week | Activity | Deliverable |
|------|----------|-------------|
| 25-26 | Implement L3 human-in-command workflow | Step-by-step confirmation, dual authorization |
| 27-28 | Deploy overreliance detection | OV-007 metric, automation bias alerts |
| 29-30 | Implement decision reversal tracking | OV-008 metric, reversal analysis |
| 31-32 | Deploy OV-009 to OV-012 metrics | Complete metrics dashboard |
| 33-34 | Implement feedback loop to model retraining | Override pattern → retraining pipeline |
| 35-36 | Full system audit and compliance verification | Audit report, compliance certification |

### Phase 4: Optimization (Months 10-12)

| Week | Activity | Deliverable |
|------|----------|-------------|
| 37-38 | Oversight effectiveness analysis | Effectiveness report, improvement plan |
| 39-40 | Threshold tuning based on data | Optimized thresholds, reduced false positives |
| 41-42 | Advanced analytics and predictive oversight | Predictive models for oversight needs |
| 43-44 | Cross-system oversight optimization | Unified oversight dashboard |
| 45-46 | Regulatory compliance verification | EU AI Act Art. 14 compliance evidence |
| 47-48 | Continuous improvement process | Improvement register, next cycle plan |

---

## 9. Appendices

### Appendix A: Oversight Decision Context Schema

```json
{
  "decision_context": {
    "decision_id": "DEC-20261001-0042",
    "timestamp": "2026-10-01T14:30:00Z",
    "system": {
      "id": "GRC-RISK-001",
      "name": "Risk Scoring Engine",
      "version": "2.3.1",
      "oversight_level": "L2"
    },
    "input_summary": {
      "data_types": ["financial", "operational", "compliance"],
      "record_count": 15420,
      "time_range": "2026-07-01 to 2026-09-30"
    },
    "output_summary": {
      "risk_score": 0.72,
      "risk_category": "high",
      "confidence": 0.85,
      "recommendation": "Enhanced monitoring recommended",
      "key_factors": [
        {"factor": "regulatory_change", "weight": 0.3, "direction": "increases_risk"},
        {"factor": "control_gap", "weight": 0.4, "direction": "increases_risk"},
        {"factor": "incident_trend", "weight": 0.3, "direction": "increases_risk"}
      ]
    },
    "alternatives": [
      {"action": "standard_monitoring", "risk_score": 0.45, "confidence": 0.70},
      {"action": "reduced_monitoring", "risk_score": 0.20, "confidence": 0.60}
    ],
    "impact_assessment": {
      "decision_impact": "high",
      "reversibility": "partial",
      "affected_stakeholders": ["compliance_team", "risk_committee", "auditors"],
      "regulatory_implications": ["SOX", "GDPR"]
    },
    "citations": [
      {"source": "risk_model_v2.3", "reference": "https://internal/risk-model/2.3"},
      {"source": "regulatory_guidance", "reference": "SOX Section 404"}
    ],
    "anomaly_indicators": {
      "is_anomaly": false,
      "anomaly_score": 0.12,
      "novel_pattern": false
    }
  }
}
```

### Appendix B: Oversight Audit Trail Schema

```json
{
  "audit_trail": {
    "audit_id": "AT-20261001-0001",
    "decision_id": "DEC-20261001-0042",
    "events": [
      {
        "timestamp": "2026-10-01T14:30:00Z",
        "event": "decision_generated",
        "actor": "system",
        "details": "AI system generated risk assessment"
      },
      {
        "timestamp": "2026-10-01T14:30:01Z",
        "event": "oversight_level_assigned",
        "actor": "system",
        "details": "L2 assigned based on risk score 0.72"
      },
      {
        "timestamp": "2026-10-01T14:30:02Z",
        "event": "oversight_requested",
        "actor": "system",
        "details": "Approval requested from compliance_officer_001"
      },
      {
        "timestamp": "2026-10-01T14:45:00Z",
        "event": "oversight_decision",
        "actor": "user-12345",
        "details": {
          "decision": "approved",
          "time_on_task_seconds": 900,
          "modifications": false,
          "reason": "Reviewed against regulatory guidance"
        }
      },
      {
        "timestamp": "2026-10-01T14:45:01Z",
        "event": "action_executed",
        "actor": "system",
        "details": "Enhanced monitoring workflow initiated"
      }
    ],
    "integrity": {
      "hash": "sha256:abc123...",
      "previous_hash": "sha256:def456...",
      "chain_verified": true
    }
  }
}
```

### Appendix C: Glossary

| Term | Definition |
|------|-----------|
| **Human-in-the-Loop (HITL)** | Human approval required before AI action executes |
| **Human-on-the-Loop (HOTL)** | Human reviews AI outputs after execution; can override |
| **Human-in-Command (HIC)** | Human initiates, directs, and confirms each AI action |
| **Override** | Human reversal or modification of an AI decision |
| **Approval Latency** | Time from oversight request to human decision |
| **Escalation** | Transfer of decision to higher oversight level |
| **Overreliance** | Tendency to trust AI outputs without critical evaluation |
| **Automation Bias** | Human tendency to favor AI-generated information |
| **Circuit Breaker** | Automated halt mechanism when thresholds breached |
| **Graceful Degradation** | Fallback to safe mode with reduced AI capability |
| **Decision Context Package** | Structured information provided to human overseer |
| **Oversight Level** | Classification of required human oversight (L0-L3) |
| **Kill Switch** | Emergency stop mechanism for all AI operations |

### Appendix D: References

1. EU AI Act (Regulation 2024/1689) — Article 14: Human Oversight
2. ISO/IEC 42001:2023 — Clause A.6.2.8: Human Oversight
3. NIST AI Risk Management Framework 1.0 — GOVERN 3: Human Oversight
4. GRC_Claw Gap Analysis — Gap 2: Agentic AI Governance Standard
5. GRC_Claw U-AIGMM — Domain 2.3: Human Oversight & Accountability
6. GRC_Claw Legal & Regulatory Compliance Spec — Art. 14 Mapping
7. GRC_Claw Unified Metrics Layer — UC3-005, AG-004, AG-005
8. GRC_Claw Security Specification — LLM08: Excessive Agency

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw AI Governance Team | Initial release |

### Review & Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Document Owner | AI Governance Lead | ___________ | _______ |
| CLO | Chief Legal Officer | ___________ | _______ |
| CISO | Chief Information Security Officer | ___________ | _______ |
| AI Risk Officer | AI Risk Officer | ___________ | _______ |
| CEO | Chief Executive Officer | ___________ | _______ |

---

*End of Document*
