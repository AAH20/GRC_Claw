# GRC_Claw Unified AI Governance Maturity Model (U-AIGMM)

## A Synthesis of Seven Leading Frameworks

**Version:** 1.0  
**Date:** October 2026  
**License:** Open Source (CC BY-SA 4.0)  
**Standards Alignment:** ISO/IEC 42001, NIST AI RMF 1.0, EU AI Act, NIST CSF 2.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Source Models Analyzed](#2-source-models-analyzed)
3. [Comparative Analysis](#3-comparative-analysis)
4. [Unified Model Architecture](#4-unified-model-architecture)
5. [Maturity Levels](#5-maturity-levels)
6. [Assessment Methodology](#6-assessment-methodology)
7. [Assessment Questionnaire](#7-assessment-questionnaire)
8. [Scoring Rubric](#8-scoring-rubric)
9. [Remediation Roadmap](#9-remediation-roadmap)
10. [Gap Analysis](#10-gap-analysis)
11. [Implementation Guide](#11-implementation-guide)
12. [Appendices](#12-appendices)

---

## 1. Executive Summary

The GRC_Claw Unified AI Governance Maturity Model (U-AIGMM) synthesizes seven leading AI governance maturity frameworks into a single, operational model purpose-built for agentic AI governance. It addresses a critical gap: existing models either focus narrowly on AI adoption (MITRE, Gartner), responsible AI practice (Microsoft), or application security (OWASP), leaving the governance of autonomous AI agents—their identity, behavior, tool access, and human oversight—underserved.

**Key innovations of U-AIGMM:**

- **Agentic-first design**: First model to center agent identity, runtime behavioral controls, and tool governance as core dimensions
- **Dual-stream assessment**: Combines MITRE's qualitative levels with OWASP's Create/Promote + Measure/Improve streams
- **Standards-native**: Every dimension maps to ISO/IEC 42001, NIST AI RMF, and EU AI Act clauses
- **Outcome-driven scoring**: Business outcome metrics (cost containment, risk reduction, efficiency, decision quality) linked to maturity levels
- **Modular architecture**: Organizations can assess all 12 domains or focus on specific areas

---

## 2. Source Models Analyzed

| Model | Year | Pillars/Domains | Levels | Focus | Assessment Method |
|-------|------|-----------------|--------|-------|-------------------|
| **MITRE AI MM** | 2023 | 6 pillars, 20 dimensions | 5 (Initial→Optimized) | Enterprise AI adoption readiness | Multiple-choice per dimension |
| **Microsoft RAI MM** | 2023 | 3 categories, 24 dimensions | 5 (Latent→Leading) | Responsible AI organizational maturity | Workshop-based, perception divergence |
| **Gartner AI MM** | 2024 | 7 pillars | 5 (Foundational→Transformational) | AI readiness and value realization | Online assessment, heat maps |
| **OWASP AIMA** | 2025 | 8 domains, 24 sub-practices | 3+ (Initial→Optimizing) | AI security and trustworthiness | Yes/no worksheets, SAMM scoring |
| **CMMI AIM** | 2026 | 8 domains, 31 PAs | 5 (CMMI standard) | AI capability and performance | Formal appraisal |
| **AAGMM** | 2026 | 12 governance domains | 5 (Ad-Hoc→Optimizing) | Agentic AI governance | Simulation-validated |
| **CSA AGMM** | 2026 | 7 dimensions | 5 (CMMI-based) | Agentic AI security governance | Operational assessment |

---

## 3. Comparative Analysis

### 3.1 Common Dimensions (Convergence Areas)

Across all seven models, the following dimensions consistently appear:

| Common Dimension | MITRE | MS RAI | Gartner | OWASP | CMMI AIM | AAGMM | CSA AGMM |
|---|---|---|---|---|---|---|---|
| **Governance & Strategy** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Ethics & Responsible AI** | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ |
| **Data Management** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Security & Privacy** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **People & Culture** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Risk Management** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Operations & Monitoring** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Technology & Architecture** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

### 3.2 Unique Contributions

| Model | Unique Contribution | U-AIGMM Incorporation |
|-------|--------------------|-----------------------|
| MITRE | CMMI lineage, cumulative level progression | Level architecture, assessment tool design |
| Microsoft RAI | Perception divergence (leader vs. team), sociotechnical approach | Multi-rater assessment, team-level dimensions |
| Gartner | Business value/ROI linkage, heat map visualization | Outcome metrics, gap visualization |
| OWASP AIMA | Dual-stream (Create/Promote + Measure/Improve), security lifecycle | Stream-based assessment, security depth |
| CMMI AIM | Formal appraisal rigor, crosswalks to standards | Standards mapping, appraisal methodology |
| AAGMM | Agent sprawl taxonomy, business outcome simulation | Agent-specific domains, outcome modeling |
| CSA AGMM | Agent identity governance, runtime behavioral controls, tool management | Agentic-first dimensions, runtime controls |

### 3.3 Maturity Level Comparison

| U-AIGMM Level | MITRE | MS RAI | Gartner | OWASP | CMMI AIM | AAGMM | CSA AGMM |
|---|---|---|---|---|---|---|---|
| **1 - Initial** | Initial | Latent | Foundational | Initial | Initial | Ad-Hoc | Ad-Hoc |
| **2 - Developing** | Adopted | Emerging | Emerging | Managed | Managed | Developing | Developing |
| **3 - Defined** | Defined | Developing | Operational | Defined | Defined | Defined | Defined |
| **4 - Managed** | Managed | Realizing | Scaled | Quant. Managed | Quant. Managed | Managed | Managed |
| **5 - Optimizing** | Optimized | Leading | Transformational | Optimizing | Optimizing | Optimizing | Optimizing |

### 3.4 Assessment Methodology Comparison

| Method | Models Using It | U-AIGMM Approach |
|--------|----------------|-------------------|
| Multiple-choice per dimension | MITRE | Primary method (adapted) |
| Yes/no worksheets | OWASP AIMA | Stream B (Measure & Improve) |
| Workshop-based perception | Microsoft RAI | Multi-rater option |
| Online self-assessment | Gartner | Digital platform |
| Formal appraisal | CMMI AIM | Enterprise tier |
| Simulation-based | AAGMM | Outcome validation |
| Evidence-based detailed | OWASP AIMA | Audit tier |

---

## 4. Unified Model Architecture

### 4.1 Structure Overview

The U-AIGMM is organized into **4 pillars**, **12 domains**, and **36 sub-dimensions**, assessed across **5 maturity levels** with **2 streams** per sub-dimension.

```
┌─────────────────────────────────────────────────────────────┐
│                    U-AIGMM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  PILLAR 1: GOVERNANCE & STRATEGY                              │
│  ├── Domain 1.1: AI Governance Framework                      │
│  ├── Domain 1.2: AI Strategy & Value Alignment                │
│  └── Domain 1.3: Risk & Compliance Management                 │
│                                                               │
│  PILLAR 2: RESPONSIBLE AI & ETHICS                            │
│  ├── Domain 2.1: Fairness, Transparency & Explainability      │
│  ├── Domain 2.2: Privacy & Data Protection                    │
│  └── Domain 2.3: Human Oversight & Accountability             │
│                                                               │
│  PILLAR 3: TECHNICAL FOUNDATION                               │
│  ├── Domain 3.1: Data Governance & Quality                    │
│  ├── Domain 3.2: Model & Platform Security                    │
│  ├── Domain 3.3: Agent Identity & Access Governance           │
│  └── Domain 3.4: Runtime Behavioral Controls                 │
│                                                               │
│  PILLAR 4: OPERATIONS & PERFORMANCE                           │
│  ├── Domain 4.1: Monitoring & Incident Response               │
│  ├── Domain 4.2: Workforce & Organizational Readiness         │
│  └── Domain 4.3: Continuous Improvement & Innovation          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Domain Definitions

#### PILLAR 1: GOVERNANCE & STRATEGY

**Domain 1.1: AI Governance Framework**
- Establishes the organizational structures, policies, decision rights, and accountability mechanisms for AI governance
- *Standards mapping*: ISO 42001 §5 (Leadership), §6 (Planning); NIST AI RMF GOVERN
- *Source models*: MITRE (Governance), MS RAI (Governance), Gartner (AI Governance), OWASP (Governance), CMMI AIM (all PAs), AAGMM (Governance), CSA AGMM (Governance)

**Domain 1.2: AI Strategy & Value Alignment**
- Connects AI adoption to business objectives, value realization, and investment prioritization
- *Standards mapping*: ISO 42001 §4 (Context), §6.1 (Risk assessment); NIST AI RMF MAP
- *Source models*: MITRE (AI Strategic Plan), Gartner (AI Strategy, Value), AAGMM (Business Outcome Orientation)

**Domain 1.3: Risk & Compliance Management**
- Identifies, assesses, and mitigates AI-specific risks; ensures regulatory compliance
- *Standards mapping*: ISO 42001 §6 (Risk treatment), §9 (Performance evaluation); NIST AI RMF MANAGE; EU AI Act
- *Source models*: MITRE (Risk), MS RAI (RAI Risks), Gartner (Risk), OWASP (Threat Assessment), CMMI AIM (Safety, Security), AAGMM (Risk Incident Rate), CSA AGMM (Compliance Posture)

#### PILLAR 2: RESPONSIBLE AI & ETHICS

**Domain 2.1: Fairness, Transparency & Explainability**
- Ensures AI systems are fair, transparent, and their decisions can be explained
- *Standards mapping*: ISO 42001 §6.1.2 (AI impact assessment); NIST AI RMF MEASURE; EU AI Act Art. 13
- *Source models*: MITRE (Transparency, Human-Centric), MS RAI (Transparency), OWASP (Fairness & Bias, Transparency), CMMI AIM (Safety), AAGMM (Decision Quality)

**Domain 2.2: Privacy & Data Protection**
- Protects personal data throughout the AI lifecycle; implements privacy by design
- *Standards mapping*: ISO 42001 §6.1.3 (Data protection); GDPR; NIST AI RMF MEASURE 2.7
- *Source models*: MITRE (Security & Privacy), MS RAI (AI Privacy), OWASP (Privacy), CMMI AIM (Security), CSA AGMM (Compliance)

**Domain 2.3: Human Oversight & Accountability**
- Establishes meaningful human oversight, approval gates, and clear accountability chains
- *Standards mapping*: ISO 42001 §6.1.4 (Human oversight); EU AI Act Art. 14; NIST AI RMF GOVERN 1.5
- *Source models*: MITRE (User Trust), MS RAI (Accountability), OWASP (Operational Management), AAGMM (Human Oversight), CSA AGMM (Human Oversight Mechanisms)

#### PILLAR 3: TECHNICAL FOUNDATION

**Domain 3.1: Data Governance & Quality**
- Ensures data used for training, validation, and operation is high-quality, properly governed, and traceable
- *Standards mapping*: ISO 42001 §6.1.3 (Data); NIST AI RMF MAP 2.1, MEASURE 2.2
- *Source models*: MITRE (AI Data Governance), Gartner (AI Data), OWASP (Data Management), CMMI AIM (Data), AAGMM (Data Governance)

**Domain 3.2: Model & Platform Security**
- Secures AI models, platforms, and infrastructure against threats including adversarial attacks, model theft, and supply chain risks
- *Standards mapping*: ISO 42001 §8 (Operational planning); NIST AI RMF MANAGE 2.4; NIST CSF 2.0
- *Source models*: MITRE (Security & Privacy), OWASP (Design, Implementation, Verification), CMMI AIM (Security), CSA AGMM (Security)

**Domain 3.3: Agent Identity & Access Governance**
- Governs agent identities, credentials, authentication, authorization, and lifecycle management
- *Standards mapping*: ISO 42001 §8.2 (Access control); NIST CSF 2.0 PR.AA; EU AI Act Art. 12
- *Source models*: AAGMM (Agent Identity Governance), CSA AGMM (Agent Identity Governance)
- *Unique to U-AIGMM*: No other model addresses agent-specific identity governance

**Domain 3.4: Runtime Behavioral Controls**
- Implements runtime monitoring, guardrails, anomaly detection, and behavioral constraints for AI agents
- *Standards mapping*: ISO 42001 §9 (Monitoring); NIST AI RMF MANAGE 2.5; NIST CSF 2.0 DE.AE
- *Source models*: AAGMM (Runtime Behavioral Controls), CSA AGMM (Runtime Behavioral Controls)
- *Unique to U-AIGMM*: First model to formalize runtime agent behavior governance

#### PILLAR 4: OPERATIONS & PERFORMANCE

**Domain 4.1: Monitoring & Incident Response**
- Detects, responds to, and recovers from AI-specific incidents including model drift, adversarial attacks, and agent misbehavior
- *Standards mapping*: ISO 42001 §10 (Improvement); NIST AI RMF MANAGE 2.6; NIST CSF 2.0 RS.RP
- *Source models*: MITRE (Solution Monitoring), OWASP (Operations), CMMI AIM (Services), AAGMM (Incident Response), CSA AGMM (Incident Response Readiness)

**Domain 4.2: Workforce & Organizational Readiness**
- Builds AI literacy, skills, culture, and organizational capacity for responsible AI adoption
- *Standards mapping*: ISO 42001 §7 (Support), §7.2 (Competence); NIST AI RMF GOVERN 1.3
- *Source models*: MITRE (Workforce Development, Culture), MS RAI (Leadership and Culture, Organizational Capacity), Gartner (People and Culture), CMMI AIM (People), CSA AGMM (Workforce Capability)

**Domain 4.3: Continuous Improvement & Innovation**
- Drives ongoing maturity improvement, innovation in governance practices, and adaptation to evolving threats
- *Standards mapping*: ISO 42001 §10 (Improvement); NIST AI RMF GOVERN 1.6
- *Source models*: MITRE (AI Innovation), Gartner (Ecosystems), AAGMM (Continuous Improvement), CSA AGMM (Innovation)

---

## 5. Maturity Levels

### Level 1: Initial (Ad-Hoc)

| Characteristic | Description |
|---|---|
| **Governance** | No formal AI governance structure; ad-hoc decision-making |
| **Strategy** | No AI strategy; isolated experimentation |
| **Risk** | Risks unidentified; no risk management process |
| **Ethics** | No ethical guidelines; reactive approach to issues |
| **Data** | Data quality unknown; no governance processes |
| **Security** | Basic IT security; no AI-specific controls |
| **Agents** | No agent inventory; shadow agents proliferate |
| **Monitoring** | No monitoring; incidents discovered externally |
| **People** | No AI training; skills gaps unaddressed |
| **Improvement** | No continuous improvement process |

### Level 2: Developing (Emerging)

| Characteristic | Description |
|---|---|
| **Governance** | AI governance charter drafted; roles informally assigned |
| **Strategy** | AI strategy aligned to business goals at department level |
| **Risk** | Risk register exists; qualitative risk assessment |
| **Ethics** | Ethical guidelines documented; awareness training begun |
| **Data** | Data quality processes defined for critical datasets |
| **Security** | AI-specific threat modeling begun; basic controls deployed |
| **Agents** | Agent inventory started; basic identity management |
| **Monitoring** | Basic logging; manual incident response |
| **People** | AI literacy programs launched; role-specific training |
| **Improvement** | Ad-hoc improvement initiatives |

### Level 3: Defined (Managed)

| Characteristic | Description |
|---|---|
| **Governance** | Formal AI governance body established; policies approved |
| **Strategy** | Enterprise AI strategy with value metrics and portfolio management |
| **Risk** | Quantitative risk assessment; risk treatment plans tracked |
| **Ethics** | Ethics review board operational; fairness metrics measured |
| **Data** | Enterprise data governance; lineage tracking; quality SLAs |
| **Security** | AI security controls integrated into SDLC; regular testing |
| **Agents** | Agent registry complete; identity lifecycle managed |
| **Monitoring** | Automated monitoring; defined incident response playbooks |
| **People** | Competency framework; cross-functional RAI teams |
| **Improvement** | Regular maturity assessments; improvement roadmap tracked |

### Level 4: Managed (Quantitatively Managed)

| Characteristic | Description |
|---|---|
| **Governance** | Governance integrated into enterprise GRC; board-level reporting |
| **Strategy** | AI value realization measured; portfolio optimized |
| **Risk** | Predictive risk modeling; automated risk monitoring |
| **Ethics** | Continuous fairness monitoring; explainability automated |
| **Data** | Data quality predictive; automated lineage and provenance |
| **Security** | AI red teaming; adversarial robustness testing; zero-trust agents |
| **Agents** | Dynamic credential management; behavioral baselines enforced |
| **Monitoring** | Real-time anomaly detection; automated response |
| **People** | AI champions network; culture metrics tracked |
| **Improvement** | Metrics-driven optimization; benchmarking against peers |

### Level 5: Optimizing (Leading)

| Characteristic | Description |
|---|---|
| **Governance** | Governance as competitive advantage; industry leadership |
| **Strategy** | AI-native business model; ecosystem orchestration |
| **Risk** | Predictive risk intelligence; self-healing systems |
| **Ethics** | Proactive ethical innovation; societal impact leadership |
| **Data** | Self-optimizing data pipelines; federated governance |
| **Security** | Autonomous threat response; predictive defense |
| **Agents** | Self-governing agents with verified autonomy |
| **Monitoring** | Predictive operations; cognitive incident management |
| **People** | AI-fluent organization; continuous learning culture |
| **Improvement** | Innovation-driven; contributions to standards and community |

---

## 6. Assessment Methodology

### 6.1 Assessment Tiers

| Tier | Method | Duration | Assurance Level | Cost |
|------|--------|----------|-----------------|------|
| **Tier 1: Self-Assessment** | Online questionnaire | 2-4 hours | Low | Free |
| **Tier 2: Facilitated Assessment** | Workshop + evidence review | 1-2 days | Medium | $ |
| **Tier 3: Formal Appraisal** | CMMI-style appraisal | 3-5 days | High | $$ |

### 6.2 Multi-Rater Approach

Inspired by Microsoft RAI MM, the U-AIGMM supports multi-rater assessment:

- **Leadership raters**: Score organizational-level dimensions (Pillar 1, 4.2)
- **Team raters**: Score practice-level dimensions (Pillar 2, 3)
- **Technical raters**: Score technical dimensions (Pillar 3)
- **Independent assessor**: Validates and reconciles scores

**Perception divergence** between rater groups is itself a maturity signal—large gaps indicate communication and alignment issues.

### 6.3 Dual-Stream Assessment

Each sub-dimension is assessed across two streams:

**Stream A: Create & Promote** (OWASP AIMA Stream A)
- Focuses on establishing policies, processes, and capabilities
- Questions: "Do you have X?" "Is X documented?" "Is X approved?"

**Stream B: Measure & Improve** (OWASP AIMA Stream B)
- Focuses on measuring effectiveness and continuous improvement
- Questions: "Do you measure X?" "What are your X metrics?" "How do you improve X?"

### 6.4 Assessment Process

```
Phase 1: Preparation (1 week)
├── Define assessment scope and tier
├── Identify raters and assign dimensions
├── Gather evidence artifacts
└── Schedule assessment sessions

Phase 2: Data Collection (1-2 weeks)
├── Complete online questionnaire (Tier 1+)
├── Conduct workshops (Tier 2+)
├── Gather evidence (Tier 2+)
└── Independent review (Tier 3)

Phase 3: Scoring & Analysis (3-5 days)
├── Calculate dimension scores
├── Identify perception divergences
├── Generate heat map
├── Benchmark against industry data
└── Identify top gaps

Phase 4: Reporting & Roadmap (1 week)
├── Generate assessment report
├── Prioritize remediation actions
├── Define target maturity levels
├── Create remediation roadmap
└── Present to leadership
```

---

## 7. Assessment Questionnaire

### 7.1 Pillar 1: Governance & Strategy

#### Domain 1.1: AI Governance Framework

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 1.1.1 | Does your organization have a documented AI governance policy? | No policy exists | Policy drafted but not approved | Policy approved and communicated | Policy integrated into enterprise GRC | Policy drives industry standards |
| 1.1.2 | Is there a designated AI governance body (council, committee)? | No body exists | Informal group of interested parties | Formal body with defined charter | Body with decision authority and board reporting | Body recognized as industry leader |
| 1.1.3 | Are AI governance roles and responsibilities clearly defined? | No defined roles | Roles informally assigned | RACI matrix published | Roles integrated into job descriptions | Roles drive organizational design |
| 1.1.4 | Is there an AI system registry/inventory? | No inventory | Partial inventory, manually maintained | Complete inventory with metadata | Real-time inventory with automated discovery | Self-maintaining inventory with predictive analytics |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 1.1.5 | How often is AI governance effectiveness reviewed? | Never | Annually | Quarterly | Monthly with metrics | Continuous with predictive indicators |
| 1.1.6 | What percentage of AI systems have documented governance coverage? | <25% | 25-50% | 50-75% | 75-95% | >95% with automated compliance |
| 1.1.7 | How are governance exceptions tracked and resolved? | Not tracked | Tracked in spreadsheet | Tracked in GRC tool | Automated workflow with SLA | Self-remediating with audit trail |

#### Domain 1.2: AI Strategy & Value Alignment

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 1.2.1 | Does your organization have a documented AI strategy? | No strategy | Strategy exists but not approved | Approved strategy aligned to business goals | Strategy with value metrics and KPIs | Strategy drives business model innovation |
| 1.2.2 | Is there an AI use-case portfolio management process? | No portfolio management | Informal prioritization | Structured portfolio with criteria | Portfolio optimized for value/risk | Dynamic portfolio with predictive value modeling |
| 1.2.3 | Are AI investments linked to measurable business outcomes? | No linkage | Qualitative linkage | Quantitative ROI tracking | Real-time value dashboards | Predictive value optimization |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 1.2.4 | What percentage of AI projects deliver measurable value? | <20% | 20-40% | 40-60% | 60-80% | >80% with predictive success modeling |
| 1.2.5 | How often is AI strategy reviewed and updated? | Never | Annually | Semi-annually | Quarterly | Continuous with environmental scanning |

#### Domain 1.3: Risk & Compliance Management

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 1.3.1 | Is there an AI risk management framework? | No framework | Framework based on existing risk framework | AI-specific framework with risk taxonomy | Framework integrated with enterprise risk | Framework recognized as best practice |
| 1.3.2 | Are AI systems classified by risk level? | No classification | Informal classification | Documented risk tiers | Automated risk classification | Dynamic risk classification with ML |
| 1.3.3 | Is there a process for AI regulatory compliance? | No process | Manual compliance checking | Automated compliance monitoring | Predictive compliance with regulatory intelligence | Regulatory leadership and contribution |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 1.3.4 | How many AI-related risk incidents occurred in the past year? | Unknown | >10 | 5-10 | 1-5 | 0 with predictive prevention |
| 1.3.5 | What is the average time to remediate AI compliance gaps? | N/A | >90 days | 30-90 days | 7-30 days | <7 days with automated remediation |

### 7.2 Pillar 2: Responsible AI & Ethics

#### Domain 2.1: Fairness, Transparency & Explainability

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 2.1.1 | Are there documented fairness guidelines for AI systems? | No guidelines | Guidelines drafted | Guidelines approved and implemented | Guidelines with automated enforcement | Guidelines drive industry standards |
| 2.1.2 | Is explainability required for AI decision systems? | Not required | Required for high-risk only | Required for all AI systems | Automated explainability for all decisions | Explainability as competitive advantage |
| 2.1.3 | Are AI systems tested for bias before deployment? | No testing | Ad-hoc testing | Systematic bias testing | Continuous bias monitoring | Predictive bias prevention |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 2.1.4 | What percentage of AI systems have documented fairness metrics? | <10% | 10-30% | 30-60% | 60-90% | >90% with real-time monitoring |
| 2.1.5 | How often are fairness metrics reviewed? | Never | Annually | Quarterly | Monthly | Continuous with automated alerting |

#### Domain 2.2: Privacy & Data Protection

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 2.2.1 | Is privacy by design implemented for AI systems? | Not implemented | Principles documented | Privacy impact assessments required | Privacy engineering integrated into SDLC | Privacy-preserving AI techniques standard |
| 2.2.2 | Is data minimization practiced for AI training and operation? | Not practiced | Policy exists | Enforced for new systems | Enforced for all systems with monitoring | Automated data minimization |
| 2.2.3 | Are Data Protection Impact Assessments (DPIAs) conducted for AI? | Not conducted | Conducted for high-risk only | Conducted for all AI systems | Automated DPIA with risk scoring | Predictive privacy risk modeling |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 2.2.4 | What percentage of AI systems have completed privacy assessments? | <25% | 25-50% | 50-75% | 75-95% | >95% with continuous validation |
| 2.2.5 | How many privacy incidents related to AI occurred in the past year? | Unknown | >5 | 2-5 | 1-2 | 0 with predictive prevention |

#### Domain 2.3: Human Oversight & Accountability

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 2.3.1 | Is human oversight required for high-impact AI decisions? | Not required | Policy exists | Oversight mechanisms implemented | Automated oversight with escalation | Adaptive oversight based on risk |
| 2.3.2 | Are there defined approval gates for AI agent actions? | No gates | Informal approval process | Defined gates for high-risk actions | Automated gates with audit trail | Intelligent gates with risk-adaptive thresholds |
| 2.3.3 | Is there clear accountability for AI system outcomes? | No accountability | Informal accountability | Documented accountability matrix | Accountability integrated into governance | Accountability as organizational value |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 2.3.4 | What percentage of high-impact AI decisions have human oversight? | <25% | 25-50% | 50-75% | 75-95% | >95% with meaningful oversight |
| 2.3.5 | How often is the effectiveness of human oversight reviewed? | Never | Annually | Quarterly | Monthly | Continuous with effectiveness metrics |

### 7.3 Pillar 3: Technical Foundation

#### Domain 3.1: Data Governance & Quality

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 3.1.1 | Is there a data governance framework for AI data? | No framework | Framework exists for non-AI data | AI-specific data governance framework | Framework with automated enforcement | Self-optimizing data governance |
| 3.1.2 | Is data lineage tracked for AI training and operation? | Not tracked | Tracked for critical datasets | Tracked for all AI data | Automated lineage with impact analysis | Predictive lineage with risk scoring |
| 3.1.3 | Are data quality metrics defined and monitored? | Not defined | Metrics defined for critical data | Metrics defined and monitored | Automated quality monitoring with alerting | Predictive quality management |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 3.1.4 | What percentage of AI training data has documented lineage? | <25% | 25-50% | 50-75% | 75-95% | >95% with automated verification |
| 3.1.5 | How often are data quality issues detected and remediated? | Never | Annually | Quarterly | Real-time | Predictive prevention |

#### Domain 3.2: Model & Platform Security

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 3.2.1 | Is AI-specific threat modeling conducted? | Not conducted | Conducted for high-risk systems | Conducted for all AI systems | Automated threat modeling | Predictive threat intelligence |
| 3.2.2 | Are AI models tested for adversarial robustness? | Not tested | Ad-hoc testing | Systematic adversarial testing | Continuous adversarial testing | Automated adversarial resilience |
| 3.2.3 | Is the AI supply chain secured? | Not secured | Vendor assessments | Supply chain risk management | Automated supply chain monitoring | Predictive supply chain security |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 3.2.4 | How many AI security incidents occurred in the past year? | Unknown | >10 | 5-10 | 1-5 | 0 with predictive prevention |
| 3.2.5 | What is the mean time to patch AI vulnerabilities? | N/A | >90 days | 30-90 days | 7-30 days | <7 days with automated patching |

#### Domain 3.3: Agent Identity & Access Governance

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 3.3.1 | Does each AI agent have a unique, attributable identity? | No unique identities | Some agents have identities | All agents have unique identities | Identities with cryptographic verification | Self-sovereign agent identities |
| 3.3.2 | Are agent credentials short-lived and task-scoped? | Long-lived static credentials | Credentials rotated periodically | Short-lived credentials | Task-scoped dynamic credentials | Self-expiring intent-bound credentials |
| 3.3.3 | Is there a complete agent inventory with ownership? | No inventory | Partial inventory | Complete inventory with owners | Real-time inventory with automated discovery | Self-maintaining inventory with predictive analytics |
| 3.3.4 | Are agent permissions scoped to least privilege? | No scoping | Informal scoping | Defined least privilege | Automated least privilege enforcement | Dynamic privilege adjustment based on context |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 3.3.5 | What percentage of agent actions are attributable to a specific identity? | <25% | 25-50% | 50-75% | 75-95% | >95% with cryptographic verification |
| 3.3.6 | How often are agent access reviews conducted? | Never | Annually | Quarterly | Monthly | Continuous with automated certification |
| 3.3.7 | How many unauthorized agent actions were detected in the past year? | Unknown | >10 | 5-10 | 1-5 | 0 with predictive prevention |

#### Domain 3.4: Runtime Behavioral Controls

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 3.4.1 | Are runtime behavioral guardrails implemented for agents? | No guardrails | Basic rate limiting | Defined guardrails for all agents | Automated guardrails with policy enforcement | Adaptive guardrails with ML-based detection |
| 3.4.2 | Is agent behavior monitored for anomalies? | Not monitored | Basic logging | Anomaly detection defined | Real-time anomaly detection | Predictive behavior analysis |
| 3.4.3 | Are there defined responses to agent misbehavior? | No defined responses | Informal response process | Documented response playbooks | Automated response with escalation | Self-healing response with learning |
| 3.4.4 | Are agent tool/API calls controlled and audited? | Not controlled | Basic access control | Tool allowlisting | Dynamic tool access with risk scoring | Intent-based tool governance |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 3.4.5 | What percentage of agent actions are governed by runtime controls? | <25% | 25-50% | 50-75% | 75-95% | >95% with adaptive controls |
| 3.4.6 | How quickly are anomalous agent behaviors detected? | N/A | >24 hours | 1-24 hours | 1-60 minutes | <1 minute with predictive detection |
| 3.4.7 | How often are runtime control policies reviewed and updated? | Never | Annually | Quarterly | Monthly | Continuous with automated optimization |

### 7.4 Pillar 4: Operations & Performance

#### Domain 4.1: Monitoring & Incident Response

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 4.1.1 | Is there an AI-specific incident response plan? | No plan | Plan based on general IR plan | AI-specific IR plan with playbooks | Plan with automated response | Plan with predictive response |
| 4.1.2 | Are AI systems monitored for model drift and degradation? | Not monitored | Manual monitoring | Automated drift detection | Predictive drift prevention | Self-mitigating drift management |
| 4.1.3 | Are AI incidents tracked and analyzed? | Not tracked | Tracked in spreadsheet | Tracked in incident management system | Automated trend analysis | Predictive incident prevention |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 4.1.4 | What is the mean time to detect AI incidents? | N/A | >7 days | 1-7 days | 1-24 hours | <1 hour with predictive detection |
| 4.1.5 | What is the mean time to recover from AI incidents? | N/A | >7 days | 1-7 days | 1-24 hours | <1 hour with automated recovery |

#### Domain 4.2: Workforce & Organizational Readiness

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 4.2.1 | Is there an AI literacy/training program? | No program | Ad-hoc training | Structured program for all roles | Role-specific competency framework | Continuous learning culture with AI fluency |
| 4.2.2 | Are there designated AI champions or RAI specialists? | No champions | Informal champions | Formal champion network | Champions with dedicated time and authority | Champions driving organizational transformation |
| 4.2.3 | Is AI governance included in employee onboarding? | Not included | Mentioned in onboarding | Formal AI governance module | Role-specific governance training | Personalized AI governance learning path |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 4.2.4 | What percentage of employees have completed AI literacy training? | <25% | 25-50% | 50-75% | 75-95% | >95% with continuous learning |
| 4.2.5 | How is AI competency assessed and tracked? | Not assessed | Self-assessment | Manager assessment | Formal competency certification | Continuous skills validation |

#### Domain 4.3: Continuous Improvement & Innovation

**Stream A: Create & Promote**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 4.3.1 | Is there a process for continuous improvement of AI governance? | No process | Ad-hoc improvements | Structured improvement process | Metrics-driven improvement program | Innovation-driven improvement culture |
| 4.3.2 | Are lessons learned from AI incidents systematically captured? | Not captured | Captured informally | Documented and shared | Integrated into training and processes | Predictive knowledge management |
| 4.3.3 | Does the organization contribute to AI governance standards/communities? | No contribution | Passive participation | Active participation | Leadership in standards bodies | Driving industry standards |

**Stream B: Measure & Improve**

| # | Question | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|---|
| 4.3.4 | How often is the AI governance maturity reassessed? | Never | Every 2-3 years | Annually | Semi-annually | Continuous with automated assessment |
| 4.3.5 | What percentage of improvement recommendations are implemented? | <25% | 25-50% | 50-75% | 75-95% | >95% with automated tracking |

---

## 8. Scoring Rubric

### 8.1 Scoring Methodology

Each question is scored 1-5 based on the selected maturity level. The scoring follows these rules:

**Dimension Score** = Average of all question scores in that dimension

**Domain Score** = Average of all dimension scores in that domain

**Pillar Score** = Average of all domain scores in that pillar

**Overall Maturity Score** = Average of all pillar scores

### 8.2 Stream Weighting

To balance the dual-stream approach:

- **Stream A (Create & Promote)**: 60% weight — emphasizes establishing capabilities
- **Stream B (Measure & Improve)**: 40% weight — emphasizes measurement and improvement

**Adjusted Dimension Score** = (Stream A Average × 0.6) + (Stream B Average × 0.4)

### 8.3 Maturity Level Thresholds

| Level | Score Range | Description |
|-------|-------------|-------------|
| **1 - Initial** | 1.0 - 1.8 | Ad-hoc, reactive practices |
| **2 - Developing** | 1.9 - 2.6 | Emerging practices, partial coverage |
| **3 - Defined** | 2.7 - 3.4 | Standardized, organization-wide practices |
| **4 - Managed** | 3.5 - 4.2 | Quantitatively managed, proactive practices |
| **5 - Optimizing** | 4.3 - 5.0 | Leading practices, continuous innovation |

### 8.4 Partial Credit System

Inspired by OWASP AIMA's "+" designation:

- If all questions at Level N are answered "Yes" but only some at Level N+1, the dimension is scored as **N+** (e.g., 2+)
- Partial credit = N + (fraction of Level N+1 criteria met × 0.5)
- Example: All Level 2 criteria met, 3 of 5 Level 3 criteria met → Score = 2.3

### 8.5 Perception Divergence Scoring

When multiple raters assess the same dimension:

- **Divergence** = |Rater A Score - Rater B Score|
- Divergence > 1.0 levels triggers a facilitated discussion
- Divergence > 2.0 levels indicates a significant alignment issue requiring executive attention

### 8.6 Business Outcome Metrics

Linked to AAGMM's outcome dimensions, the U-AIGMM tracks:

| Outcome Dimension | Metric | Level 1 | Level 3 | Level 5 |
|---|---|---|---|---|
| **Cost Containment** | Agent Sprawl Index | >0.8 | 0.3-0.5 | <0.1 |
| **Risk Reduction** | Risk Incident Rate (per 1K actions) | >10 | 2-5 | <0.5 |
| **Operational Efficiency** | Effective Task Completion Rate | <60% | 75-85% | >95% |
| **Decision Quality** | Delegation Safety Rate | <70% | 85-92% | >98% |

### 8.7 Heat Map Visualization

Results are visualized as a heat map:

```
                    L1    L2    L3    L4    L5
Pillar 1: Governance  [2.3] [3.1] [2.8] [1.9] [1.5]
Pillar 2: Responsible [1.8] [2.5] [2.2] [1.7] [1.3]
Pillar 3: Technical   [1.5] [2.1] [2.9] [2.3] [1.8]
Pillar 4: Operations  [2.0] [2.8] [3.2] [2.5] [2.1]

Color coding: Red (<2.0) | Yellow (2.0-2.9) | Light Green (3.0-3.9) | Green (4.0+)
```

---

## 9. Remediation Roadmap

### 9.1 Prioritization Framework

Remediation actions are prioritized using a **Risk-Value-Effort** matrix:

| Priority | Risk | Value | Effort | Timeline |
|----------|------|-------|--------|----------|
| **P1 - Critical** | High | High | Low | 0-3 months |
| **P2 - High** | High | High | Medium | 3-6 months |
| **P3 - Medium** | Medium | High | Medium | 6-12 months |
| **P4 - Low** | Low | Medium | High | 12-18 months |

### 9.2 Level 1 → Level 2 Remediation Roadmap

**Target**: Establish foundational governance and basic controls

| Domain | Action | Priority | Effort | Est. Duration |
|--------|--------|----------|--------|---------------|
| 1.1 | Draft and approve AI governance policy | P1 | Low | 4 weeks |
| 1.1 | Establish AI governance body | P1 | Low | 4 weeks |
| 1.1 | Create initial AI system inventory | P1 | Medium | 8 weeks |
| 1.2 | Develop AI strategy document | P1 | Medium | 6 weeks |
| 1.3 | Create AI risk register | P1 | Low | 4 weeks |
| 2.1 | Document fairness guidelines | P2 | Low | 4 weeks |
| 2.2 | Conduct privacy impact assessment for high-risk AI | P1 | Medium | 6 weeks |
| 2.3 | Define human oversight requirements | P1 | Low | 4 weeks |
| 3.1 | Define data quality metrics for critical datasets | P2 | Medium | 6 weeks |
| 3.2 | Conduct AI threat modeling for high-risk systems | P1 | Medium | 6 weeks |
| 3.3 | Create agent inventory and assign identities | P1 | Medium | 8 weeks |
| 3.4 | Implement basic runtime guardrails | P2 | Medium | 8 weeks |
| 4.1 | Develop AI incident response plan | P1 | Low | 4 weeks |
| 4.2 | Launch AI literacy training program | P2 | Medium | 8 weeks |
| 4.3 | Establish continuous improvement process | P3 | Low | 4 weeks |

### 9.3 Level 2 → Level 3 Remediation Roadmap

**Target**: Standardize practices across the organization

| Domain | Action | Priority | Effort | Est. Duration |
|--------|--------|----------|--------|---------------|
| 1.1 | Integrate governance into enterprise GRC | P2 | Medium | 12 weeks |
| 1.1 | Implement automated AI system discovery | P3 | High | 16 weeks |
| 1.2 | Implement AI portfolio management process | P2 | Medium | 12 weeks |
| 1.3 | Implement quantitative risk assessment | P2 | Medium | 12 weeks |
| 2.1 | Establish ethics review board | P2 | Medium | 8 weeks |
| 2.1 | Implement systematic bias testing | P2 | High | 16 weeks |
| 2.2 | Implement privacy by design in SDLC | P2 | High | 16 weeks |
| 2.3 | Implement automated approval gates | P3 | High | 16 weeks |
| 3.1 | Implement enterprise data lineage tracking | P3 | High | 20 weeks |
| 3.2 | Integrate AI security into SDLC | P2 | High | 16 weeks |
| 3.3 | Implement agent identity lifecycle management | P2 | High | 16 weeks |
| 3.4 | Implement real-time anomaly detection | P3 | High | 20 weeks |
| 4.1 | Implement automated monitoring and alerting | P2 | Medium | 12 weeks |
| 4.2 | Establish AI competency framework | P3 | Medium | 12 weeks |
| 4.3 | Implement metrics-driven improvement program | P3 | Medium | 12 weeks |

### 9.4 Level 3 → Level 4 Remediation Roadmap

**Target**: Achieve quantitative management and proactive practices

| Domain | Action | Priority | Effort | Est. Duration |
|--------|--------|----------|--------|---------------|
| 1.1 | Implement board-level AI governance reporting | P3 | Medium | 12 weeks |
| 1.2 | Implement real-time value dashboards | P3 | High | 16 weeks |
| 1.3 | Implement predictive risk modeling | P3 | High | 20 weeks |
| 2.1 | Implement continuous fairness monitoring | P3 | High | 16 weeks |
| 2.2 | Implement automated privacy compliance | P3 | High | 16 weeks |
| 2.3 | Implement adaptive human oversight | P4 | High | 20 weeks |
| 3.1 | Implement predictive data quality management | P4 | High | 20 weeks |
| 3.2 | Implement AI red teaming program | P3 | High | 16 weeks |
| 3.3 | Implement dynamic credential management | P3 | High | 16 weeks |
| 3.4 | Implement predictive behavior analysis | P4 | High | 20 weeks |
| 4.1 | Implement automated incident response | P3 | High | 16 weeks |
| 4.2 | Establish AI champions network | P3 | Medium | 12 weeks |
| 4.3 | Implement benchmarking against peers | P4 | Medium | 12 weeks |

### 9.5 Level 4 → Level 5 Remediation Roadmap

**Target**: Achieve optimization and industry leadership

| Domain | Action | Priority | Effort | Est. Duration |
|--------|--------|----------|--------|---------------|
| 1.1 | Establish governance as competitive advantage | P4 | High | 24 weeks |
| 1.2 | Implement AI-native business model innovation | P4 | High | 24 weeks |
| 1.3 | Implement self-healing risk management | P4 | High | 24 weeks |
| 2.1 | Implement proactive ethical innovation | P4 | High | 24 weeks |
| 2.2 | Implement privacy-preserving AI techniques | P4 | High | 24 weeks |
| 2.3 | Implement self-governing oversight | P4 | High | 24 weeks |
| 3.1 | Implement self-optimizing data pipelines | P4 | High | 24 weeks |
| 3.2 | Implement autonomous threat response | P4 | High | 24 weeks |
| 3.3 | Implement self-sovereign agent identities | P4 | High | 24 weeks |
| 3.4 | Implement self-governing agent behaviors | P4 | High | 24 weeks |
| 4.1 | Implement predictive operations | P4 | High | 24 weeks |
| 4.2 | Establish AI-fluent organizational culture | P4 | High | 24 weeks |
| 4.3 | Drive industry standards and community leadership | P4 | High | Ongoing |

### 9.6 Quick Wins (0-3 months)

These high-impact, low-effort actions can rapidly improve maturity:

1. **Draft AI governance policy** (Domain 1.1) — 2 weeks
2. **Establish AI governance body** (Domain 1.1) — 2 weeks
3. **Create AI system inventory** (Domain 1.1) — 4 weeks
4. **Create AI risk register** (Domain 1.3) — 2 weeks
5. **Define human oversight requirements** (Domain 2.3) — 2 weeks
6. **Create agent inventory** (Domain 3.3) — 4 weeks
7. **Develop AI incident response plan** (Domain 4.1) — 2 weeks
8. **Launch AI literacy training** (Domain 4.2) — 4 weeks

---

## 10. Gap Analysis

### 10.1 What Existing Models Miss

| Gap | Models Affected | U-AIGMM Solution |
|-----|-----------------|------------------|
| **Agent identity governance** | MITRE, MS RAI, Gartner, OWASP, CMMI AIM | Domain 3.3: Agent Identity & Access Governance |
| **Runtime behavioral controls** | MITRE, MS RAI, Gartner, OWASP, CMMI AIM | Domain 3.4: Runtime Behavioral Controls |
| **Agent sprawl management** | MITRE, MS RAI, Gartner, OWASP, CMMI AIM | Domain 3.3 + 4.1: Agent inventory + monitoring |
| **Tool/API governance for agents** | MITRE, MS RAI, Gartner, OWASP, CMMI AIM | Domain 3.4: Tool access controls |
| **Business outcome linkage** | MITRE, MS RAI, OWASP, CMMI AIM | Outcome metrics in scoring rubric |
| **Perception divergence** | MITRE, Gartner, OWASP, CMMI AIM, AAGMM, CSA AGMM | Multi-rater assessment methodology |
| **Dual-stream assessment** | MITRE, MS RAI, Gartner, CMMI AIM, AAGMM, CSA AGMM | Stream A + Stream B for each dimension |
| **Standards crosswalk** | MITRE, MS RAI, Gartner, OWASP, AAGMM | Every dimension maps to ISO/NIST/EU AI Act |
| **Simulation validation** | MITRE, MS RAI, Gartner, OWASP, CMMI AIM, CSA AGMM | Outcome metrics based on AAGMM simulation data |
| **Partial credit scoring** | MITRE, MS RAI, Gartner, CMMI AIM, AAGMM, CSA AGMM | "+" designation for partial level achievement |

### 10.2 Industry Maturity Distribution

Based on CSA/Google Cloud 2025 survey and AAGMM research:

| Level | % of Organizations | Characteristics |
|-------|-------------------|-----------------|
| **Level 1** | ~40% | Ad-hoc, no formal governance |
| **Level 2** | ~30% | Emerging practices, department-level |
| **Level 3** | ~20% | Defined, organization-wide practices |
| **Level 4** | ~8% | Managed, quantitative practices |
| **Level 5** | ~2% | Optimizing, industry-leading |

### 10.3 Common Maturity Gaps

| Gap | Prevalence | Impact | Priority |
|-----|-----------|--------|----------|
| No agent identity governance | ~77% | Critical | P1 |
| No runtime behavioral controls | ~84% | Critical | P1 |
| No AI risk register | ~60% | High | P1 |
| No human oversight mechanisms | ~55% | High | P1 |
| No AI literacy training | ~45% | Medium | P2 |
| No continuous improvement process | ~50% | Medium | P2 |
| No AI incident response plan | ~65% | High | P1 |
| No data lineage tracking | ~70% | High | P2 |

---

## 11. Implementation Guide

### 11.1 Getting Started

**Week 1-2: Preparation**
1. Secure executive sponsorship
2. Define assessment scope (enterprise-wide vs. department)
3. Select assessment tier (1, 2, or 3)
4. Identify raters and assign dimensions
5. Set up assessment platform/tools

**Week 3-4: Data Collection**
1. Distribute questionnaire to raters
2. Schedule workshops (Tier 2+)
3. Gather evidence artifacts
4. Conduct independent review (Tier 3)

**Week 5: Scoring & Analysis**
1. Calculate scores
2. Generate heat map
3. Identify top 10 gaps
4. Benchmark against industry data
5. Draft assessment report

**Week 6: Reporting & Roadmap**
1. Present findings to leadership
2. Prioritize remediation actions
3. Define target maturity levels
4. Create remediation roadmap
5. Establish review cadence

### 11.2 Tool Requirements

| Capability | Tier 1 | Tier 2 | Tier 3 |
|------------|--------|--------|--------|
| Online questionnaire | ✓ | ✓ | ✓ |
| Evidence repository | — | ✓ | ✓ |
| Scoring engine | ✓ | ✓ | ✓ |
| Heat map visualization | ✓ | ✓ | ✓ |
| Multi-rater support | — | ✓ | ✓ |
| Perception divergence analysis | — | ✓ | ✓ |
| Benchmarking | — | ✓ | ✓ |
| Roadmap generator | — | ✓ | ✓ |
| Standards crosswalk | — | — | ✓ |
| Audit trail | — | — | ✓ |

### 11.3 Integration with GRC_Claw

The U-AIGMM is designed to integrate with GRC_Claw's existing capabilities:

- **Risk Register**: AI risks feed into the enterprise risk register
- **Policy Management**: AI governance policies managed in GRC_Claw
- **Compliance Tracking**: AI compliance requirements tracked alongside other compliance
- **Incident Management**: AI incidents managed in GRC_Claw incident module
- **Reporting**: AI maturity reports generated from GRC_Claw dashboards
- **Workflow**: AI governance workflows automated through GRC_Claw

### 11.4 Review Cadence

| Activity | Frequency | Participants |
|----------|-----------|--------------|
| Self-assessment | Quarterly | All raters |
| Facilitated assessment | Semi-annually | Governance body + raters |
| Formal appraisal | Annually | Independent assessors |
| Maturity reassessment | Annually | All stakeholders |
| Roadmap review | Quarterly | Governance body |
| Executive reporting | Quarterly | Board/C-suite |

---

## 12. Appendices

### Appendix A: Standards Crosswalk

| U-AIGMM Domain | ISO/IEC 42001 | NIST AI RMF | EU AI Act | NIST CSF 2.0 |
|---|---|---|---|---|
| 1.1 AI Governance Framework | §5, §6 | GOVERN | Art. 9 | GV.OC |
| 1.2 AI Strategy & Value | §4, §6.1 | MAP | Art. 5 | GV.OC |
| 1.3 Risk & Compliance | §6, §9 | MANAGE | Art. 9, 15 | ID.RA, RS.RP |
| 2.1 Fairness & Transparency | §6.1.2 | MEASURE | Art. 13 | ID.AM |
| 2.2 Privacy & Data Protection | §6.1.3 | MEASURE 2.7 | Art. 10 | PR.DS |
| 2.3 Human Oversight | §6.1.4 | GOVERN 1.5 | Art. 14 | GV.HR |
| 3.1 Data Governance | §6.1.3 | MAP 2.1 | Art. 10 | ID.AM |
| 3.2 Model & Platform Security | §8 | MANAGE 2.4 | Art. 15 | PR.PS |
| 3.3 Agent Identity & Access | §8.2 | GOVERN 1.4 | Art. 12 | PR.AA |
| 3.4 Runtime Behavioral Controls | §9 | MANAGE 2.5 | Art. 15 | DE.AE, RS.AN |
| 4.1 Monitoring & Incident Response | §10 | MANAGE 2.6 | Art. 15 | RS.RP, RC.RP |
| 4.2 Workforce & Readiness | §7 | GOVERN 1.3 | Art. 4 | GV.HR |
| 4.3 Continuous Improvement | §10 | GOVERN 1.6 | Art. 9 | ID.IM |

### Appendix B: Glossary

| Term | Definition |
|------|-----------|
| **Agent Sprawl** | Uncontrolled proliferation of redundant, ungoverned AI agents |
| **Agent Identity** | Unique, attributable digital identity for an AI agent |
| **Runtime Behavioral Controls** | Mechanisms to detect, constrain, and respond to agent behavior during operation |
| **Perception Divergence** | Difference in maturity assessment between rater groups |
| **Dual-Stream Assessment** | Evaluation across both capability creation and measurement/improvement |
| **Maturity Level** | Hierarchical stage of organizational capability (1-5) |
| **Domain** | Area of governance focus (e.g., Data Governance) |
| **Sub-dimension** | Specific aspect within a domain (e.g., Data Lineage) |
| **Stream A** | Create & Promote — establishing policies and capabilities |
| **Stream B** | Measure & Improve — measuring effectiveness and improving |

### Appendix C: References

1. MITRE. (2023). *AI Maturity Model and Organizational Assessment Tool Guide*. MITRE Corporation.
2. Vorvoreanu, M., et al. (2023). *Responsible AI Maturity Model*. Microsoft Research.
3. Gartner. (2024). *AI Maturity Model*. Gartner Research.
4. OWASP. (2025). *AI Maturity Assessment (AIMA) v1.0*. OWASP Foundation.
5. CMMI Institute. (2026). *CMMI AIM: Artificial Intelligence Maturity*. CMMI Institute.
6. Acharya, V. (2026). *Agentic AI Governance Maturity Model (AAGMM)*. arXiv:2604.16338.
7. Cloud Security Alliance. (2026). *Agentic AI Governance Maturity Model (AGMM)*. CSA Labs.
8. Cloud Security Alliance & Google Cloud. (2025). *State of AI Security and Governance Survey Report*.
9. ISO/IEC. (2023). *ISO/IEC 42001:2023 — Information technology — Artificial intelligence — Management system*.
10. NIST. (2023). *AI Risk Management Framework (AI RMF 1.0)*.

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Research Team | Initial release |

---

*This document is licensed under CC BY-SA 4.0. You are free to share and adapt it with attribution.*
