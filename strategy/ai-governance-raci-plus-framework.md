# AI Governance RACI-Plus Framework
## Synthesizing Forrester, CTAIO, COMPEL, and ISO 42001 into a Unified Operating Model

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Proposed for GRC_Claw Wave 2

---

## 1. Executive Summary

This framework consolidates four major AI governance RACI references into a single, operational RACI-plus model. It addresses the Wave 1 gap: standardized role titles, competency frameworks, and authority calibration across Forrester (NIST AI RMF-aligned), CTAIO (6-role model), COMPEL (30-activity, 12-role matrix), and ISO 42001 Clause 5.3 (management system roles).

**Key innovations beyond standard RACI:**
- **Decision Rights** — explicit approve / block / accept / delegate authorities per role
- **Stop Authority** — named roles who can halt deployment, disable features, or trigger rollback
- **Escalation Thresholds** — measurable triggers that move accountability up the chain
- **Competency Framework** — required skills and knowledge per role
- **Authority Calibration** — budget, risk, and decision boundaries per role

---

## 2. Core Role Inventory (14 Roles)

Synthesized from all four frameworks. Each role has a standardized title, primary accountability, and framework mapping.

| # | Standardized Role | Primary Accountability | Forrester | CTAIO | COMPEL | ISO 42001 |
|---|---|---|---|---|---|---|
| 1 | **Chief AI Officer (CAIO)** | AI strategy, governance program, board reporting | ✓ | ✓ | ✓ | Top mgmt sponsor |
| 2 | **Chief Information Security Officer (CISO)** | AI security controls, model protection, incident response | ✓ | ✓ | ✓ | Information security |
| 3 | **Chief Risk Officer (CRO)** | AI risk appetite, enterprise risk register | ✓ | ✓ | ✓ | Risk management |
| 4 | **General Counsel (GC)** | Regulatory compliance, legal risk, contracts | ✓ | ✓ | ✓ | Legal/regulatory |
| 5 | **Data Protection Officer (DPO)** | Privacy conformance, DPIA, data subject rights | — | — | ✓ | Privacy |
| 6 | **AI Ethics Officer** | Fairness, transparency, bias audits, model cards | — | ✓ | — | — |
| 7 | **AI Governance Lead / CoE Lead** | Governance operations, policy, standards, training | ✓ | — | ✓ | AI governance lead |
| 8 | **Business Unit AI Owner** | Business outcome, residual risk acceptance per system | ✓ | ✓ | ✓ | Model/product owner |
| 9 | **ML / Data Engineering Lead** | Model building, data pipelines, MLOps, evaluation | ✓ | — | ✓ | Engineering lead |
| 10 | **Head of Compliance** | Regulatory mapping, attestations, external reporting | — | — | ✓ | — |
| 11 | **Head of Product** | User-facing AI experience, disclosures, trust UX | — | — | ✓ | — |
| 12 | **Internal Audit** | Independent assurance, control effectiveness | — | — | ✓ | Internal audit |
| 13 | **Board AI Committee** | Enterprise risk appetite, policy approval, oversight | ✓ | ✓ | ✓ | Top management |
| 14 | **AI Incident Manager** | AI incident triage, coordination, escalation | — | — | — | Incident manager |

### Role Consolidation Notes
- **Small organizations (< 20 AI systems):** One person may cover multiple functions, but accountability must be explicitly assigned and documented. Minimum: CAIO + CISO + GC coverage.
- **Regulated industries:** Split further — add sector-specific compliance officer, clinical safety officer (healthcare), or model risk validator (financial services).
- **CTAIO's "Business Unit AI Champions"** map to COMPEL's "Business Unit AI Owner" — the framework uses the latter as it implies accountability, not just advocacy.

---

## 3. Competency Framework by Role

Each role requires specific competencies across four dimensions: **Governance Knowledge**, **Technical Depth**, **Risk & Compliance**, and **Leadership & Communication**.

| Role | Governance Knowledge | Technical Depth | Risk & Compliance | Leadership |
|---|---|---|---|---|
| **CAIO** | Expert — NIST AI RMF, EU AI Act, ISO 42001, board governance | Working — ML lifecycle, architecture patterns | Expert — risk appetite, regulatory landscape | Expert — executive presence, board reporting |
| **CISO** | Working — AI governance frameworks | Expert — adversarial ML, model security, prompt injection | Expert — security regulations, incident response | Advanced — cross-functional coordination |
| **CRO** | Expert — enterprise risk management, AI risk taxonomy | Working — model risk, drift concepts | Expert — risk quantification, board reporting | Advanced — risk culture building |
| **GC** | Expert — AI regulation, liability, IP, contracts | Awareness — AI capabilities and limitations | Expert — regulatory interpretation, litigation | Advanced — executive communication |
| **DPO** | Expert — GDPR, privacy-by-design, DPIA | Working — data pipelines, model training data | Expert — data protection law, regulator liaison | Advanced — cross-functional privacy integration |
| **AI Ethics Officer** | Expert — fairness frameworks, ethics principles | Advanced — bias metrics, explainability, model cards | Advanced — human rights impact, sectoral ethics | Advanced — stakeholder engagement, training |
| **AI Governance Lead / CoE** | Expert — governance frameworks, policy design | Working — ML lifecycle, tooling | Advanced — compliance mapping, audit | Advanced — program management, enablement |
| **BU AI Owner** | Working — governance processes, risk acceptance | Working — system capabilities, limitations | Advanced — business risk, continuity | Advanced — business case, benefit realization |
| **ML / Data Eng Lead** | Working — governance requirements, documentation | Expert — model development, MLOps, evaluation | Working — security and privacy controls | Advanced — technical leadership |
| **Head of Compliance** | Expert — regulatory obligations, control mapping | Awareness — AI system types | Expert — attestations, external reporting | Advanced — regulatory relationships |
| **Head of Product** | Working — governance requirements, user trust | Working — AI UX patterns, limitations | Working — disclosure requirements, consent | Advanced — user advocacy, cross-functional |
| **Internal Audit** | Expert — audit standards, governance frameworks | Working — AI controls, data analytics | Expert — control evaluation, independence | Advanced — audit committee reporting |
| **Board AI Committee** | Expert — fiduciary duty, AI oversight | Awareness — AI capabilities and risks | Expert — risk appetite, regulatory landscape | Expert — governance oversight |
| **AI Incident Manager** | Working — incident response frameworks | Advanced — AI failure modes, forensics | Advanced — notification requirements, timelines | Expert — crisis coordination |

### Competency Levels
- **Awareness:** Can explain concepts and implications
- **Working:** Can apply knowledge to governance decisions
- **Advanced:** Can design controls, lead initiatives, mentor others
- **Expert:** Can shape organizational strategy, represent externally, testify to regulators

---

## 4. RACI-Plus Matrix: 30 Activities Across 6 Lifecycle Phases

### Phase 1: Calibrate (Strategy & Policy)

| # | Activity | R | A | C | I | Decision Rights | Stop Authority |
|---|---|---|---|---|---|---|---|
| 1 | AI strategy definition | CAIO, CoE | CAIO | CRO, GC, Comp, BU | Board, ML, Prod | CAIO approves strategy; Board may redirect | Board (strategic redirection) |
| 2 | AI policy approval | CoE | Board | CAIO, CRO, GC, DPO, Comp | CISO, IA, BU, ML, Prod | Board approves; CAIO may veto on feasibility grounds | Board (final authority) |
| 3 | AI ethics principles | CoE, Prod | CAIO | GC, DPO, BU, external stakeholders | Board, CISO, CRO, Comp, IA, ML | CAIO approves; Ethics Officer may block on rights grounds | AI Ethics Officer (rights-based veto) |
| 4 | Risk appetite statement | CRO | Board | CAIO, GC, Comp, BU | CoE, CISO, DPO, IA, ML, Prod | Board sets appetite; CRO recommends | Board (appetite change) |
| 5 | Use-case intake process | CoE | CAIO | CRO, GC, DPO, CISO, BU | Board, IA, Comp, ML, Prod | CAIO approves intake criteria | CAIO (intake suspension) |
| 6 | Board AI reporting cadence | CAIO, CoE | Board | CRO, IA, Comp | CISO, DPO, GC, BU, ML, Prod | Board sets cadence; CAIO proposes content | Board (reporting scope) |

### Phase 2: Organize (Governance Infrastructure)

| # | Activity | R | A | C | I | Decision Rights | Stop Authority |
|---|---|---|---|---|---|---|---|
| 7 | Intake evaluation | CoE | CAIO | BU, DPO, GC, CISO | CRO, Comp, ML, Prod | CAIO approves/rejects; CoE recommends | CAIO (reject use case) |
| 8 | Risk classification | CoE | CRO | DPO, GC, CISO, BU | CAIO, IA, Comp, ML, Prod | CRO assigns tier; CAIO may override with documented rationale | CRO (tier assignment) |
| 9 | Gate 1 approval (concept) | CoE, BU | CAIO | CRO, DPO, GC, Comp | Board, CISO, IA, ML, Prod | CAIO approves concept; CRO may block on risk | CAIO + CRO (joint block) |
| 10 | Gate 2 approval (pre-build) | CoE, BU | CAIO | CISO, DPO, GC, ML, Comp | Board, CRO, IA, Prod | CAIO approves build start; CISO may block on security | CAIO + CISO (joint block) |

### Phase 3: Model (Data & Model Decisions)

| # | Activity | R | A | C | I | Decision Rights | Stop Authority |
|---|---|---|---|---|---|---|---|
| 11 | Dataset approval | ML | BU | DPO, CISO, CoE, GC | CAIO, CRO, IA, Comp, Prod | BU approves dataset; DPO may block on privacy | DPO (privacy block) |
| 12 | Data residency decisions | DPO | BU | CISO, GC, Comp, CoE | CAIO, CRO, IA, ML, Prod | DPO recommends; BU decides with DPO concurrence | DPO (residency veto) |
| 13 | Model selection | ML, CoE | BU | CISO, CAIO, Comp | CRO, DPO, GC, IA, Prod | BU selects model; CAIO may veto on governance | CAIO (governance veto) |
| 14 | Vendor model procurement | ML, CoE | BU | CISO, GC, DPO, Comp, CRO | CAIO, IA, Prod | BU approves vendor; GC approves contracts; CISO approves security | GC (contract block) + CISO (security block) |
| 15 | Model card approval | ML | BU | CoE, DPO, GC | CAIO, CISO, CRO, IA, Comp, Prod | BU approves model card; CoE may block on completeness | CoE (documentation block) |

### Phase 4: Produce (Deployment)

| # | Activity | R | A | C | I | Decision Rights | Stop Authority |
|---|---|---|---|---|---|---|---|
| 16 | Pre-deployment review | CoE, ML | CAIO | CISO, DPO, GC, BU, CRO, Comp | Board, IA, Prod | CAIO approves release; any C-role may block | CAIO + CISO + DPO + GC (any one may block) |
| 17 | Production release | ML, BU | BU | CoE, CISO, Prod | CAIO, CRO, DPO, GC, IA, Comp | BU releases; ML executes; Prod owns UX | BU (release abort) |
| 18 | Rollback decision | ML, BU | BU | CAIO, CISO, CoE, Prod | CRO, DPO, GC, IA, Comp, Board | BU triggers rollback; CAIO may require rollback | CAIO (mandatory rollback) |
| 19 | HITL threshold setting | BU, ML | BU | CoE, GC, Comp, Prod | CAIO, CISO, DPO, CRO, IA | BU sets thresholds; CoE may require adjustment | CoE (threshold adjustment) |

### Phase 5: Evaluate (Monitoring)

| # | Activity | R | A | C | I | Decision Rights | Stop Authority |
|---|---|---|---|---|---|---|---|
| 20 | Performance threshold setting | ML, CoE | BU | CAIO, CRO, Prod | CISO, DPO, GC, IA, Comp | BU sets thresholds; CRO may require tightening | CRO (risk-based tightening) |
| 21 | Anomaly investigation | ML | BU | CoE, CISO, DPO, Prod | CAIO, CRO, GC, IA, Comp | BU investigates; ML executes; CISO may lead if security | CISO (security-led investigation) |
| 22 | Drift decision (retrain/retire) | ML, BU | BU | CoE, CAIO, Comp | CRO, CISO, DPO, GC, IA, Prod | BU decides retrain/retire; CAIO may require re-gate | CAIO (re-gate requirement) |
| 23 | Monitoring dashboard ownership | CoE, ML | CAIO | BU, CRO, IA | CISO, DPO, GC, Comp, Prod, Board | CAIO owns dashboard; CoE maintains | CAIO (dashboard access) |

### Phase 6: Learn (Incident, Audit & Improvement)

| # | Activity | R | A | C | I | Decision Rights | Stop Authority |
|---|---|---|---|---|---|---|---|
| 24 | Incident triage | ML, CISO | CAIO | BU, DPO, GC, CoE, Prod | CRO, IA, Comp, Board | CAIO leads triage; CISO leads security; ML provides technical | CAIO (incident declaration) |
| 25 | Customer communication | Prod, GC | BU | CAIO, DPO, Comp | CISO, CRO, IA, ML, Board | BU approves messaging; GC approves legal content | GC (legal content veto) |
| 26 | Regulatory notification | Comp, DPO | GC | CAIO, CRO, CISO, BU | IA, ML, Prod, Board | GC approves notification; DPO approves privacy-specific | GC (notification approval) |
| 27 | Internal audit | IA | Audit Committee | CAIO, CRO, Comp, CoE | CISO, DPO, GC, BU, ML, Prod | Audit Committee owns audit scope; IA executes | Audit Committee (audit scope) |
| 28 | Certification audit (ISO 42001) | CoE, Comp | CAIO | IA, CRO, CISO, DPO, GC, BU, ML | Board, Prod | CAIO certifies; IA supports; Comp maintains evidence | CAIO (certification decision) |
| 29 | Annual policy review | CoE | CAIO | All roles | Board | CAIO recommends; Board approves changes | Board (policy change approval) |
| 30 | Training record review | CoE | CAIO | HR, BU, IA, Comp | CISO, DPO, GC, CRO, ML, Prod | CAIO ensures compliance; CoE tracks completion | CAIO (training enforcement) |

---

## 5. Decision Rights Matrix

Explicit authority per role across decision types. This is the "plus" in RACI-plus.

| Decision Type | CAIO | CISO | CRO | GC | DPO | Ethics | CoE | BU Owner | ML Lead | Comp | Prod | IA | Board |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Approve new AI use case** | ✓ (Gate 1 & 2) | Consult | Consult | Consult | Consult | — | Recommend | Propose | — | — | — | — | Notify |
| **Block deployment** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (rights) | — | — | — | — | — | — | — |
| **Accept residual risk** | Program level | — | ✓ (enterprise) | — | — | — | — | ✓ (system) | — | — | — | — | ✓ (appetite) |
| **Approve vendor/model** | Veto | Security | — | Contract | Privacy | — | Recommend | ✓ | Technical | — | — | — | — |
| **Trigger rollback** | ✓ (mandatory) | ✓ (security) | — | — | — | — | — | ✓ (voluntary) | Execute | — | — | — | — |
| **Declare incident** | ✓ | ✓ (security) | — | — | ✓ (privacy) | — | — | — | — | — | — | — | Notify |
| **Regulatory notification** | Consult | Consult | Consult | ✓ | ✓ (privacy) | — | — | — | — | Prepare | — | — | Notify |
| **Policy exception** | Recommend | — | ✓ | ✓ | ✓ | ✓ | — | Request | — | — | — | — | ✓ (approve) |
| **Budget approval** | ≤$1M | — | — | — | — | — | — | ≤$500K | — | — | — | — | >$1M |
| **Kill/retire system** | ✓ | — | — | — | — | — | — | ✓ (recommend) | — | — | — | — | Notify |

**Legend:** ✓ = authority, — = no authority, Consult = must be consulted, Recommend = provides input, Prepare = prepares materials, Execute = implements decision, Notify = informed after decision, Veto = can block, Request = can request action.

---

## 6. Stop Authority

Stop authority is the power to halt a deployment, disable a feature, or trigger an immediate rollback. It must be explicit, documented, and exercisable.

### 6.1 Stop Authority by Role

| Role | Stop Scope | Trigger Conditions | Execution Mechanism | Time Limit |
|---|---|---|---|---|
| **CAIO** | Any AI system | Governance non-compliance, risk appetite breach, regulatory exposure | Direct order to BU Owner; can invoke emergency board session | Immediate |
| **CISO** | Any AI system with security risk | Active security incident, data breach, adversarial attack, unauthorized access | Technical kill switch; can block deployment gate | Immediate |
| **DPO** | Any AI system processing personal data | Unlawful processing, DPIA failure, data subject rights violation | Privacy block; can halt data flows | Immediate |
| **GC** | Any AI system with legal exposure | Regulatory violation, litigation hold, contract breach | Legal hold; can block customer-facing features | Immediate |
| **AI Ethics Officer** | Any AI system with rights impact | Discriminatory output, rights violation, unethical use case | Ethics block; can require human review | Before deployment only |
| **CRO** | Portfolio-level risk | Aggregated risk exceeds appetite, systemic failure pattern | Risk escalation; can require portfolio review | 24 hours |
| **BU AI Owner** | Own AI systems | Business risk, performance failure, continuity threat | Voluntary rollback; can halt own system | Immediate |
| **Board AI Committee** | Any AI system | Strategic risk, reputational threat, fiduciary concern | Board directive; can override CAIO | Next board session |

### 6.2 Stop Authority Protocol

1. **Declaration:** The stopping role declares the stop in writing (ticket, email, or incident record) with rationale.
2. **Notification:** All C-suite roles notified within 1 hour; Board notified within 24 hours for high-risk systems.
3. **Evidence Preservation:** System state, logs, and outputs preserved for investigation.
4. **Remediation:** Stopping role specifies conditions for resumption.
5. **Review:** Stop reviewed within 5 business days by CAIO + relevant C-roles; Board notified of outcome.
6. **Documentation:** Stop recorded in escalation log with trigger, decision, and resolution.

---

## 7. Escalation Thresholds

Measurable triggers that move accountability from the default role to a higher authority. These are not optional overlays — they are part of the RACI.

### 7.1 Risk-Based Escalation

| Trigger | Default A | Escalates To | Timing | Evidence Required |
|---|---|---|---|---|
| Risk tier = High (EU AI Act Art. 6) | BU AI Owner | CAIO + Board notification | At Gate 1 | Risk assessment, classification record |
| Risk tier = Prohibited (EU AI Act Art. 5) | CAIO | Board (go/no-go vote) | Before Gate 2 | Legal opinion, risk assessment |
| Risk tier = Unacceptable (internal) | CAIO | Board (go/no-go vote) | Before Gate 2 | Risk assessment, CRO recommendation |
| Special-category personal data (GDPR Art. 9) | BU AI Owner | DPO + BU (joint A) | At intake | DPIA, lawful basis determination |
| Regulated industry use (medical, credit, employment) | BU AI Owner | GC + BU (joint A) + regulator notification | At intake | Regulatory mapping, compliance assessment |
| Aggregated portfolio risk exceeds appetite | CRO | Board (appetite revision or rebalance) | Quarterly review | Portfolio risk report, trend analysis |

### 7.2 Incident-Based Escalation

| Trigger | Default A | Escalates To | Timing | Evidence Required |
|---|---|---|---|---|
| Customer harm from AI output | BU AI Owner | CAIO + GC (+ Board within 24h) | On triage | Incident record, customer impact assessment |
| Regulator inquiry or complaint | GC | CAIO + Board | On receipt | Legal assessment, regulator communication |
| Data breach involving AI system | CISO + DPO | CAIO + GC + Board | Within 1 hour | Breach assessment, DPIA reference |
| Model failure with safety implications | BU AI Owner | CAIO + CISO + CRO | On detection | Technical assessment, impact analysis |
| Vendor model deprecation or incident | BU AI Owner | CAIO + CISO + GC (joint triage) | On notification | Vendor notification, impact assessment |
| Adversarial attack on AI system | CISO | CAIO + GC | On detection | Security assessment, attack analysis |

### 7.3 Change-Based Escalation

| Trigger | Default A | Escalates To | Timing | Evidence Required |
|---|---|---|---|---|
| Material model change (new base model, new training data class, new region) | ML Lead | Re-trigger Gate 2 with CAIO as A | Before change | Change assessment, updated model card |
| Budget overrun >15% | BU AI Owner | CAIO + CFO | At budget review | Budget tracking, variance analysis |
| Gate review overdue >30 days | CoE | CAIO + Audit Committee | At 30-day mark | Gate tracking, remediation plan |
| Second consecutive gate failure | CoE | Executive Sponsor | At second failure | Gate records, remediation history |
| Certification nonconformity (ISO 42001 major) | CoE | CAIO + Audit Committee | Within audit cycle | Audit finding, corrective action plan |
| New AI system class (agentic, foundation model) | CAIO | Board (policy update) | At first deployment | Risk assessment, policy gap analysis |

### 7.4 Escalation Principles

1. **One accountable role at a time:** Escalation moves A to a new role; it does not create shared accountability at the same level.
2. **Documented trigger:** Every escalation must reference a specific, measurable trigger from this matrix.
3. **Time-bound:** Each escalation has a maximum time before the new A must engage.
4. **Reversible:** Escalation can be reversed when the trigger condition is resolved, with documentation.
5. **Non-punitive:** Escalation is a governance mechanism, not a blame assignment.

---

## 8. Authority Calibration

### 8.1 Budget Authority

| Role | Approval Limit | Delegation | Reporting |
|---|---|---|---|
| Board AI Committee | Unlimited (enterprise AI budget) | Delegates to CAIO | Board approval |
| CAIO | ≤$1M per system, ≤$5M per program | Delegates to BU AI Owner | Reports to Board |
| BU AI Owner | ≤$500K per system | Delegates to ML Lead (technical) | Reports to CAIO |
| CFO | >$1M per system | — | Reports to Board |
| ML Lead | Technical execution budget only | — | Reports to BU AI Owner |

### 8.2 Risk Acceptance Authority

| Risk Level | Acceptable By | Documentation | Review Frequency |
|---|---|---|---|
| Low | BU AI Owner | Risk register entry | Annual |
| Medium | CAIO | Risk register + treatment plan | Semi-annual |
| High | CAIO + CRO | Risk register + treatment plan + Board notification | Quarterly |
| Critical | Board | Board minute + risk assessment | Per incident |

### 8.3 Decision Latency Standards

| Decision Type | Maximum Latency | Escalation if Exceeded |
|---|---|---|
| Incident response | 1 hour | Auto-escalate to CAIO |
| Gate review (standard) | 5 business days | Escalate to CAIO |
| Gate review (high-risk) | 10 business days | Escalate to Board |
| Policy exception | 10 business days | Escalate to Board |
| Vendor approval | 15 business days | Escalate to CFO |
| Regulatory notification | Per regulation (typically 72 hours) | Auto-escalate to GC + Board |

---

## 9. Governance Forums

### 9.1 AI Governance Board

| Attribute | Specification |
|---|---|
| **Chair** | CAIO |
| **Members** | CISO, CRO, GC, DPO, AI Ethics Officer, rotating BU AI Owner |
| **Cadence** | Monthly (full board), quarterly (deep-dive metrics) |
| **Quorum** | 4 of 7 members for decisions |
| **Voting** | Majority for standard; unanimity for policy exceptions |
| **Emergency sessions** | CAIO or CISO may convene with 4-hour notice |
| **Documentation** | Written decisions with rationale, dissenting opinions, follow-up items |

### 9.2 AI Risk Review Board

| Attribute | Specification |
|---|---|
| **Chair** | CRO |
| **Members** | CAIO, CISO, DPO, GC, CoE Lead, relevant BU AI Owner |
| **Cadence** | Bi-weekly (risk review), ad-hoc (incident-driven) |
| **Scope** | Risk register review, exception decisions, incident escalation |
| **Escalation** | To Board AI Committee for risk appetite breaches |

### 9.3 AI Ethics Committee

| Attribute | Specification |
|---|---|
| **Chair** | AI Ethics Officer |
| **Members** | GC, DPO, Head of Product, external stakeholder (rotating) |
| **Cadence** | Monthly |
| **Scope** | Ethics review, bias audit results, rights impact assessments |
| **Authority** | Can block deployment on rights grounds; escalates to Board for policy changes |

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Days 1-30)
- [ ] Name interim accountable owners for all 14 roles
- [ ] Draft RACI-plus matrix (this document, customized)
- [ ] Get top management sign-off on governance charter
- [ ] Publish roles and escalation paths in authoritative location
- [ ] Identify all AI systems in scope and map to lifecycle activities

### Phase 2: Operationalization (Days 31-60)
- [ ] Embed approvals into intake, change, and release workflows
- [ ] Stand up AI Governance Board with defined quorum
- [ ] Train key stakeholders on RACI-plus and escalation thresholds
- [ ] Configure tooling: ticketing workflows, CI/CD gates, model registry approvals
- [ ] Begin collecting operational proof: signed approvals, meeting minutes

### Phase 3: Maturation (Days 61-90)
- [ ] Convert interim owners to stable role assignments with backups
- [ ] Add maintenance triggers (org changes, new systems, vendor updates)
- [ ] Run tabletop incident exercise using defined escalation
- [ ] Perform internal control check: sample recent changes for correct sign-offs
- [ ] Establish metrics baseline: RACI coverage, escalation latency, gate throughput

### Phase 4: Optimization (Days 91-180)
- [ ] First annual RACI review with all named roles
- [ ] Refine escalation thresholds based on operational data
- [ ] Expand competency framework with role-specific training paths
- [ ] Integrate with ISO 42001 certification audit (if applicable)
- [ ] Benchmark against peer organizations

---

## 11. Metrics and KPIs

| Metric | Definition | Target | Measurement Frequency |
|---|---|---|---|
| RACI Coverage | % of in-scope AI activities with named R and A | 100% | Quarterly |
| Role Coverage | % of named roles with current signed acceptance | 100% | Quarterly |
| Escalation Latency | Median time from trigger to new A engaged | <24h (incidents), <5 days (risk) | Per escalation |
| Gate Throughput | AI systems passing each gate per quarter | Trend (rising = bottleneck) | Quarterly |
| Decision Traceability | % of gate decisions with documented C-input and A-sign-off | 100% | Quarterly |
| Tabletop Findings Closure | % of tabletop gaps closed within agreed timeframe | >90% | Per exercise |
| Training Compliance | % of named roles current on AI governance training | 100% | Quarterly |
| Audit Findings (Role Clarity) | Number of audit findings citing unclear roles | 0 | Per audit |
| Stop Authority Exercises | Number of times stop authority was exercised | Track (not zero) | Per incident |
| Policy Exception Rate | % of decisions requiring policy exception | <5% | Quarterly |

---

## 12. Framework Mapping

### 12.1 To NIST AI RMF

| NIST Function | RACI-Plus Coverage |
|---|---|
| **Govern** | Activities 1-10 (Calibrate, Organize) + Governance Forums |
| **Map** | Activities 7-8 (Intake, Risk Classification) + Activity 11-15 (Data & Model) |
| **Measure** | Activities 20-23 (Monitoring) + Activity 15 (Model Card) |
| **Manage** | Activities 16-19 (Deployment) + Activities 24-26 (Incident) + Activities 27-30 (Audit) |

### 12.2 To EU AI Act

| EU AI Act Requirement | RACI-Plus Coverage |
|---|---|
| Art. 9 (Risk management) | Activities 8, 16, 20-22 + Risk Acceptance Authority |
| Art. 10 (Data governance) | Activities 11-12 + DPO authority |
| Art. 11 (Technical documentation) | Activity 15 (Model Card) + CoE responsibility |
| Art. 12 (Record keeping) | Activity 23 (Dashboard) + Audit trail requirements |
| Art. 13 (Transparency) | Activity 19 (HITL) + Product responsibility |
| Art. 14 (Human oversight) | Activity 19 (HITL thresholds) + Stop Authority |
| Art. 15 (Accuracy, robustness, cybersecurity) | Activities 16, 20-21 + CISO authority |
| Art. 17 (Quality management system) | Activities 27-28 (Audit) + ISO 42001 alignment |
| Art. 26 (Deployer obligations) | BU AI Owner accountability + Escalation thresholds |

### 12.3 To ISO/IEC 42001

| ISO 42001 Clause | RACI-Plus Coverage |
|---|---|
| 5.1 (Leadership & commitment) | Board AI Committee + Top management sponsor |
| 5.2 (Policy) | Activity 2 (AI policy approval) |
| 5.3 (Roles, responsibilities, authorities) | Entire RACI-plus matrix + Decision Rights + Stop Authority |
| 6.1 (Risk assessment) | Activities 8, 16 + Risk Acceptance Authority |
| 7.1 (Resources) | Authority Calibration (budget) |
| 7.2 (Competence) | Competency Framework |
| 7.3 (Awareness) | Activity 30 (Training) + Communication requirements |
| 8.1 (Operational planning) | Activities 7-22 (lifecycle) |
| 8.2 (Risk treatment) | Risk Acceptance Authority + Escalation Thresholds |
| 9.1 (Monitoring, measurement, analysis) | Metrics and KPIs |
| 9.2 (Internal audit) | Activity 27 + Internal Audit role |
| 9.3 (Management review) | Activity 6 (Board reporting) + Governance Forums |
| 10.1 (Nonconformity & corrective action) | Escalation Thresholds + Stop Authority |

---

## 13. References

1. **Forrester** — "The AI Governance RACI Matrix" (RES181597, Oct 2024). NIST AI RMF-aligned RACI for cross-functional governance teams.
2. **CTAIO** — "AI Governance Roles: Who Owns What" (2026). 6-role model with 8 decision types and 3 governance models.
3. **COMPEL Framework** — "AI Governance RACI Matrix for Enterprises: Decision Rights Across 30 Activities and 12 Roles" (FlowRidge, 2026). 12-role, 30-activity matrix with escalation thresholds.
4. **ISO/IEC 42001:2023** — "Information technology — Artificial intelligence — Management system." Clause 5.3 (Roles, responsibilities, and authorities).
5. **NIST AI Risk Management Framework 1.0** (2023). GOVERN, MAP, MEASURE, MANAGE functions.
6. **EU AI Act (Regulation 2024/1689)**. Articles 5, 6, 9, 10-17, 26.
7. **Daydream** — "ISO 42001 Clause 5.3: Roles, responsibilities and authorities" (2026). RACI-plus implementation guidance.
8. **Drel.ai** — "Roles and responsibilities under ISO 42001" (2026). AI governance function and operational roles.
9. **Elevate Consult** — "ISO 42001 RACI Matrix: Assigning AIMS Accountability" (2026). Top management, AI Risk Owner, AIMS Program Owner.

---

## Appendix A: RACI-Plus Definitions

| Term | Definition |
|---|---|
| **Responsible (R)** | Does the work; executes the activity |
| **Accountable (A)** | Approves and is on the hook; one per activity |
| **Consulted (C)** | Input required before decision; two-way communication |
| **Informed (I)** | Notified after decision; one-way communication |
| **Decision Right** | Explicit authority to approve, block, accept, or delegate |
| **Stop Authority** | Power to halt deployment, disable features, or trigger rollback |
| **Escalation Threshold** | Measurable trigger that moves accountability to a higher authority |
| **Competency** | Required skills, knowledge, and capabilities for a role |
| **Authority Calibration** | Budget, risk, and decision boundaries per role |

## Appendix B: Document Control

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-10-01 | GRC_Claw Wave 2 | Initial synthesis of Forrester, CTAIO, COMPEL, ISO 42001 |

---

*This framework is a living document. Review annually and on trigger: new regulation, material incident, new AI system class, or reorganization affecting named roles.*
