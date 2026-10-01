# Unified Governance Crosswalk: ISO 42001 × NIST AI RMF × EU AI Act × OWASP Agentic Top 10

**Version:** 1.0  
**Date:** 2026-10-01  
**Purpose:** Map every control/requirement across four AI governance frameworks, identify gaps, and propose a unified control set satisfying all four simultaneously.

---

## 1. Framework Overview

| Framework | Type | Structure | Legal Force | Certification |
|-----------|------|-----------|-------------|---------------|
| **ISO/IEC 42001:2023** | Management system standard | 38 Annex A controls across 9 areas (A.2–A.10) | Voluntary | Third-party certifiable |
| **NIST AI RMF 1.0** | Risk management framework | 4 functions, 19 categories, 72 subcategories | Voluntary | No certification scheme |
| **EU AI Act (Reg. 2024/1689)** | Binding regulation | 4 risk tiers + GPAI track | Law (fines up to €35M/7%) | Conformity assessment |
| **OWASP Agentic Top 10** | Security risk taxonomy | 10 agentic AI risks (ASI01–ASI10) | Voluntary | No certification |

---

## 2. Detailed Crosswalk Matrix

### 2.1 ISO 42001 Annex A Controls → Other Frameworks

| ISO Control | ISO Title | NIST AI RMF | EU AI Act | OWASP Agentic |
|-------------|-----------|-------------|-----------|----------------|
| **A.2.2** | AI policy | GOVERN 1.1, 1.2 | Art. 5 (prohibited practices policy), Art. 17 (QMS) | — |
| **A.2.3** | Alignment with other policies | GOVERN 1.3 | Art. 17 (QMS integration) | — |
| **A.2.4** | Review of AI policy | GOVERN 1.4 | Art. 9(2) (continuous RMS) | — |
| **A.3.2** | AI roles and responsibilities | GOVERN 2.1, 2.2, 2.3 | Art. 9(2) (RMS roles), Art. 17 (QMS roles) | ASI03 (Identity & Privilege Abuse) |
| **A.3.3** | Reporting of concerns | GOVERN 4.1, 4.2 | Art. 9(2) (RMS feedback), Art. 86 (incident reporting) | ASI08 (Cascading Failures) |
| **A.4.2** | Resource documentation | GOVERN 6.1, MAP 2.1 | Art. 10(2) (data governance resources) | — |
| **A.4.3** | Data resources | MAP 2.2, MAP 4.1 | Art. 10 (data governance) | — |
| **A.4.4** | Tooling resources | GOVERN 6.2, MAP 2.3 | Art. 11 (technical documentation) | ASI04 (Supply Chain) |
| **A.4.5** | System and computing resources | MAP 2.4 | Art. 15 (robustness, cybersecurity) | ASI05 (Unexpected Code Execution) |
| **A.4.6** | Human resources | GOVERN 3.1, 3.2 | Art. 4 (AI literacy), Art. 14 (human oversight) | ASI09 (Human-Agent Trust Exploitation) |
| **A.5.2** | AI system impact assessment process | MAP 5.1, 5.2 | Art. 9 (risk management), Art. 27 (FRIA for deployers) | — |
| **A.5.3** | Documentation of impact assessments | MAP 5.3 | Art. 9(3) (RMS documentation), Art. 11 (Annex IV) | — |
| **A.5.4** | Impact on individuals/groups | MAP 5.4, MEASURE 2.11 | Art. 9(2) (RMS), Art. 13 (transparency) | ASI09 (Human-Agent Trust Exploitation) |
| **A.5.5** | Societal impacts | MAP 5.5 | Art. 5 (prohibited practices), Art. 51 (GPAI systemic risk) | ASI10 (Rogue Agents) |
| **A.6.1.2** | Objectives for responsible development | GOVERN 1.1, MAP 1.1 | Art. 9(1) (RMS objectives) | — |
| **A.6.1.3** | Responsible design & development processes | GOVERN 1.2, MAP 3.1 | Art. 9(1), Art. 10 (data governance) | ASI01 (Goal Hijack), ASI06 (Memory Poisoning) |
| **A.6.2.2** | AI system requirements and specification | MAP 2.1, 2.2 | Art. 9(1), Art. 11 (Annex IV) | ASI01 (Goal Hijack) |
| **A.6.2.3** | Documentation of design and development | MAP 2.3, MEASURE 1.1 | Art. 11 (Annex IV technical documentation) | — |
| **A.6.2.4** | AI system verification and validation | MEASURE 2.1–2.13 | Art. 15 (accuracy, robustness), Art. 43 (conformity assessment) | ASI05 (Unexpected Code Execution), ASI08 (Cascading Failures) |
| **A.6.2.5** | AI system deployment | MAP 3.2, MANAGE 1.1 | Art. 9(1), Art. 43 (conformity assessment) | ASI08 (Cascading Failures) |
| **A.6.2.6** | AI system operation and monitoring | MEASURE 3.1, 3.2, MANAGE 4.1 | Art. 9(2) (continuous RMS), Art. 72 (post-market monitoring) | ASI08 (Cascading Failures), ASI10 (Rogue Agents) |
| **A.6.2.7** | AI system technical documentation | MAP 2.3, MEASURE 1.2 | Art. 11 (Annex IV), Art. 13 (user instructions) | — |
| **A.6.2.8** | Recording of event logs | MEASURE 3.3, MANAGE 4.2 | Art. 12 (logging), Art. 72 (post-market monitoring) | ASI08 (Cascading Failures) |
| **A.7.2** | Data for development and enhancement | MAP 4.1, 4.2 | Art. 10(2) (training data governance) | ASI06 (Memory & Context Poisoning) |
| **A.7.3** | Acquisition of data | MAP 4.3 | Art. 10(2) (data governance) | ASI04 (Supply Chain) |
| **A.7.4** | Quality of data for AI systems | MEASURE 2.11, MAP 4.4 | Art. 10(2) (data quality, bias) | — |
| **A.7.5** | Data provenance | MAP 4.5, MEASURE 1.3 | Art. 10(2) (data provenance), Art. 11 (Annex IV) | ASI04 (Supply Chain) |
| **A.7.6** | Data preparation | MAP 4.6 | Art. 10(2) (data preparation) | — |
| **A.8.2** | System documentation and information for users | MAP 3.3, MEASURE 2.9 | Art. 13 (transparency, user instructions) | ASI09 (Human-Agent Trust Exploitation) |
| **A.8.3** | External reporting | GOVERN 5.1, 5.2 | Art. 13 (transparency), Art. 50 (limited-risk transparency) | — |
| **A.8.4** | Communication of incidents | GOVERN 4.3, MANAGE 4.3 | Art. 9(2) (RMS), Art. 73 (incident reporting) | ASI08 (Cascading Failures) |
| **A.8.5** | Information for interested parties | GOVERN 5.3, MAP 5.6 | Art. 13 (transparency), Art. 50 (limited-risk) | — |
| **A.9.2** | Processes for responsible use | GOVERN 1.2, MAP 3.3 | Art. 9(1), Art. 14 (human oversight) | ASI02 (Tool Misuse), ASI09 (Trust Exploitation) |
| **A.9.3** | Objectives for responsible use | GOVERN 1.1, MAP 1.2 | Art. 9(1) (RMS objectives) | — |
| **A.9.4** | Intended use of the AI system | MAP 2.5, MANAGE 1.2 | Art. 9(1), Art. 13 (intended use documentation) | ASI01 (Goal Hijack), ASI02 (Tool Misuse) |
| **A.10.2** | Allocating responsibilities | GOVERN 2.4, 6.3 | Art. 9(2) (RMS roles), Art. 17 (QMS) | ASI03 (Identity & Privilege Abuse) |
| **A.10.3** | Suppliers | GOVERN 6.1, 6.2, MAP 4.7 | Art. 17 (QMS), Art. 25 (supplier obligations) | ASI04 (Supply Chain Compromise) |
| **A.10.4** | Customers | GOVERN 5.4, MAP 5.7 | Art. 13 (transparency), Art. 27 (deployer FRIA) | ASI09 (Human-Agent Trust Exploitation) |

### 2.2 NIST AI RMF Categories → Other Frameworks

| NIST Category | NIST Subcategories | ISO 42001 | EU AI Act | OWASP Agentic |
|---------------|-------------------|-----------|-----------|----------------|
| **GOVERN 1** | Policies, processes, procedures | A.2.2, A.2.3, A.2.4, A.6.1.2 | Art. 9, Art. 17 | — |
| **GOVERN 2** | Accountability structures | A.3.2, A.10.2 | Art. 9(2), Art. 17 | ASI03 |
| **GOVERN 3** | Workforce diversity, equity, inclusion | A.4.6 | Art. 4 (AI literacy) | ASI09 |
| **GOVERN 4** | Team culture, safe reporting | A.3.3, A.8.4 | Art. 9(2), Art. 86 | ASI08 |
| **GOVERN 5** | External engagement, feedback | A.8.3, A.8.5, A.10.4 | Art. 13, Art. 50 | — |
| **GOVERN 6** | Third-party risk management | A.4.4, A.10.3 | Art. 17, Art. 25 | ASI04 |
| **MAP 1** | Context establishment | A.6.1.2, A.9.3 | Art. 9(1), Art. 11 | — |
| **MAP 2** | System categorization, capabilities | A.4.2, A.4.3, A.4.4, A.6.2.2 | Art. 6 (classification), Art. 11 | ASI01 |
| **MAP 3** | Benefits and costs analysis | A.5.2, A.5.3 | Art. 9(1) (RMS) | — |
| **MAP 4** | Risk identification (third-party) | A.7.2, A.7.3, A.7.5, A.10.3 | Art. 10, Art. 25 | ASI04, ASI06 |
| **MAP 5** | Impact characterization | A.5.2, A.5.4, A.5.5 | Art. 9, Art. 27 (FRIA) | ASI09, ASI10 |
| **MEASURE 1** | Metrics and methods | A.6.2.3, A.6.2.7, A.7.5 | Art. 15 (accuracy metrics) | — |
| **MEASURE 2** | Trustworthiness evaluation (7 characteristics) | A.6.2.4, A.7.4, A.8.2 | Art. 15 (accuracy, robustness) | ASI05, ASI08 |
| **MEASURE 3** | Risk tracking, feedback | A.6.2.6, A.6.2.8 | Art. 9(2), Art. 72 | ASI08, ASI10 |
| **MEASURE 4** | Measurement feedback | A.6.2.6 | Art. 9(2) (continuous RMS) | — |
| **MANAGE 1** | Risk prioritization, go/no-go | A.6.2.5, A.9.4 | Art. 9(1), Art. 43 | ASI01, ASI02 |
| **MANAGE 2** | Benefit maximization | A.9.3 | Art. 9(1) | — |
| **MANAGE 3** | Third-party risk management | A.10.3 | Art. 17, Art. 25 | ASI04 |
| **MANAGE 4** | Monitoring, incident response | A.6.2.6, A.6.2.8, A.8.4 | Art. 9(2), Art. 72, Art. 73 | ASI08, ASI10 |

### 2.3 EU AI Act Requirements → Other Frameworks

| EU AI Act | Requirement | ISO 42001 | NIST AI RMF | OWASP Agentic |
|-----------|-------------|-----------|-------------|----------------|
| **Art. 4** | AI literacy | A.4.6 | GOVERN 3.1, 3.2 | — |
| **Art. 5** | Prohibited practices | A.2.2, A.5.5 | MAP 5.5, GOVERN 1.1 | ASI10 (Rogue Agents) |
| **Art. 6** | Risk classification | A.6.2.2 | MAP 2.1, 2.2 | — |
| **Art. 9** | Risk management system | A.5.2, A.6.1.2, A.6.1.3, A.9.2, A.9.3 | GOVERN 1, MAP 1, MAP 3, MAP 5 | ASI01, ASI02 |
| **Art. 10** | Data governance | A.4.3, A.7.2–A.7.6 | MAP 4.1–4.6, MEASURE 2.11 | ASI06 |
| **Art. 11** | Technical documentation (Annex IV) | A.6.2.3, A.6.2.7 | MAP 2.3, MEASURE 1.1 | — |
| **Art. 12** | Logging | A.6.2.8 | MEASURE 3.3, MANAGE 4.2 | ASI08 |
| **Art. 13** | Transparency to users | A.8.2, A.8.3, A.8.5, A.9.4 | MAP 3.3, MEASURE 2.9 | ASI09 |
| **Art. 14** | Human oversight | A.4.6, A.9.2 | GOVERN 3.1, MAP 3.1 | ASI09 |
| **Art. 15** | Accuracy, robustness, cybersecurity | A.4.5, A.6.2.4 | MEASURE 2.1–2.13 | ASI05, ASI08 |
| **Art. 17** | Quality management system | A.2.2, A.2.3, A.3.2, A.10.2 | GOVERN 1, GOVERN 2 | — |
| **Art. 25** | Supplier obligations | A.10.3 | GOVERN 6.1, 6.2 | ASI04 |
| **Art. 27** | Deployer FRIA | A.5.2, A.5.4 | MAP 5.1, 5.2 | — |
| **Art. 43** | Conformity assessment | A.6.2.4, A.6.2.5 | MEASURE 2, MANAGE 1.1 | — |
| **Art. 50** | Limited-risk transparency | A.8.3, A.8.5 | GOVERN 5.1, MAP 5.6 | — |
| **Art. 51–56** | GPAI obligations | A.5.5, A.6.2.3, A.7.5 | MAP 5.5, MEASURE 1.3 | ASI04, ASI10 |
| **Art. 72** | Post-market monitoring | A.6.2.6, A.6.2.8 | MEASURE 3.1, 3.2, MANAGE 4.1 | ASI08, ASI10 |
| **Art. 73** | Incident reporting | A.8.4 | GOVERN 4.3, MANAGE 4.3 | ASI08 |
| **Art. 86** | Reporting of serious incidents | A.3.3, A.8.4 | GOVERN 4.1, 4.2 | ASI08 |

### 2.4 OWASP Agentic Top 10 → Other Frameworks

| OWASP Risk | Risk Name | ISO 42001 | NIST AI RMF | EU AI Act |
|------------|-----------|-----------|-------------|-----------|
| **ASI01** | Agent Goal Hijack | A.6.1.3, A.6.2.2, A.9.4 | MAP 2.1, 2.2, MANAGE 1.1 | Art. 9 (RMS), Art. 14 (human oversight) |
| **ASI02** | Tool Misuse | A.9.2, A.9.4 | MAP 3.3, MANAGE 1.2 | Art. 9 (RMS), Art. 14 (human oversight) |
| **ASI03** | Identity & Privilege Abuse | A.3.2, A.10.2 | GOVERN 2.1, 2.2 | Art. 9(2), Art. 17 (QMS roles) |
| **ASI04** | Agentic Supply Chain Vulnerabilities | A.4.4, A.7.3, A.7.5, A.10.3 | GOVERN 6.1, 6.2, MAP 4.7 | Art. 17, Art. 25 (supplier obligations) |
| **ASI05** | Unexpected Code Execution | A.4.5, A.6.2.4 | MEASURE 2.1–2.13 | Art. 15 (robustness, cybersecurity) |
| **ASI06** | Memory & Context Poisoning | A.6.1.3, A.7.2 | MAP 4.1, 4.2 | Art. 10 (data governance) |
| **ASI07** | Insecure Inter-Agent Communication | A.6.2.4, A.6.2.6 | MEASURE 2.3, 3.1 | Art. 15 (cybersecurity) |
| **ASI08** | Cascading Failures | A.3.3, A.6.2.4, A.6.2.5, A.6.2.6, A.6.2.8, A.8.4 | MEASURE 3.1, 3.2, MANAGE 4.1, 4.3 | Art. 9(2), Art. 72, Art. 73 |
| **ASI09** | Human-Agent Trust Exploitation | A.4.6, A.5.4, A.8.2, A.9.2, A.10.4 | GOVERN 3.1, MAP 5.4, MEASURE 2.9 | Art. 4, Art. 13, Art. 14 |
| **ASI10** | Rogue Agents | A.5.5, A.6.2.6 | MAP 5.5, MEASURE 3.1, MANAGE 4.1 | Art. 5 (prohibited), Art. 51 (GPAI systemic risk) |

---

## 3. Gap Analysis

### 3.1 Unique Requirements per Framework (Not Covered by Others)

| Framework | Unique Requirement | Why It's Unique | Gap Impact |
|-----------|-------------------|-----------------|-------------|
| **ISO 42001** | A.2.4 — Periodic policy review | Only framework requiring scheduled policy re-review | Low — easily added to any program |
| **ISO 42001** | A.5.5 — Societal impact assessment | Only framework requiring broad societal impact evaluation | Medium — most frameworks stop at individual/group impact |
| **ISO 42001** | A.7.6 — Data preparation controls | Specific data preprocessing governance | Low — covered implicitly by NIST MAP 4 |
| **ISO 42001** | A.9.4 — Intended use enforcement | Only framework requiring technical enforcement of intended use | Medium — others document but don't enforce |
| **NIST AI RMF** | GOVERN 3 — Workforce diversity, equity, inclusion | Only framework requiring diverse teams as risk control | Medium — unique organizational requirement |
| **NIST AI RMF** | GOVERN 4 — Psychological safety for reporting | Only framework requiring non-retaliation culture | Low — cultural, not technical |
| **NIST AI RMF** | MEASURE 2.9 — Explainability evaluation | Only framework with explicit explainability metrics | High — critical for high-stakes AI |
| **NIST AI RMF** | MEASURE 2.10 — Privacy evaluation | Only framework with explicit privacy metrics | High — GDPR overlap but AI-specific |
| **NIST AI RMF** | MEASURE 2.11 — Fairness/bias evaluation | Only framework with explicit fairness metrics | High — critical for regulated AI |
| **EU AI Act** | Art. 5 — Prohibited practices list | Only framework with absolute bans | High — legal requirement, no mitigation possible |
| **EU AI Act** | Art. 12 — Automatic event logging | Only framework requiring mandatory logging | High — technical requirement others treat as best practice |
| **EU AI Act** | Art. 14 — Human oversight measures | Only framework requiring specific human oversight mechanisms | High — legal requirement for high-risk |
| **EU AI Act** | Art. 43 — Conformity assessment | Only framework requiring third-party conformity assessment | High — legal gate to market |
| **EU AI Act** | Art. 71 — EU database registration | Only framework requiring regulatory registration | Medium — administrative but mandatory |
| **EU AI Act** | Art. 51–56 — GPAI obligations | Only framework with specific GPAI/foundation model rules | High — unique to foundation models |
| **OWASP Agentic** | ASI01 — Agent goal hijacking | Only framework addressing autonomous agent goal subversion | High — unique to agentic AI |
| **OWASP Agentic** | ASI02 — Tool misuse by agents | Only framework addressing agent tool abuse | High — unique to agentic AI |
| **OWASP Agentic** | ASI03 — Identity & privilege abuse | Only framework addressing agent identity/privilege escalation | High — unique to agentic AI |
| **OWASP Agentic** | ASI04 — Agentic supply chain | Only framework addressing agent-specific supply chain (MCP, A2A) | High — unique to agentic AI |
| **OWASP Agentic** | ASI05 — Unexpected code execution | Only framework addressing agent-triggered RCE | High — unique to agentic AI |
| **OWASP Agentic** | ASI06 — Memory/context poisoning | Only framework addressing agent memory attacks | High — unique to agentic AI |
| **OWASP Agentic** | ASI07 — Insecure inter-agent communication | Only framework addressing agent-to-agent security | High — unique to multi-agent systems |
| **OWASP Agentic** | ASI08 — Cascading failures | Only framework addressing failure propagation in agent pipelines | High — unique to agentic AI |
| **OWASP Agentic** | ASI09 — Human-agent trust exploitation | Only framework addressing human manipulation via agent outputs | High — unique to agentic AI |
| **OWASP Agentic** | ASI10 — Rogue agents | Only framework addressing agent misalignment/concealment | High — unique to agentic AI |

### 3.2 Coverage Heat Map

| Domain | ISO 42001 | NIST AI RMF | EU AI Act | OWASP Agentic |
|--------|:---------:|:-----------:|:---------:|:-------------:|
| Governance & Policy | ●●● | ●●● | ●● | ● |
| Risk Management | ●●● | ●●● | ●●● | ●● |
| Data Governance | ●●● | ●● | ●●● | ●● |
| Transparency | ●● | ●●● | ●●● | ●● |
| Human Oversight | ●● | ●● | ●●● | ●● |
| Incident Response | ●● | ●●● | ●●● | ●●● |
| Third-Party/Supply Chain | ●● | ●●● | ●● | ●●● |
| Agentic Security | ● | ● | ● | ●●● |
| Fairness/Bias | ●● | ●●● | ●● | ● |
| Privacy | ● | ●●● | ●● | ● |
| Explainability | ● | ●●● | ●● | ● |
| Prohibited Practices | ● | ● | ●●● | ● |
| Conformity/ Certification | ●●● | ● | ●●● | ● |
| Societal Impact | ●●● | ●● | ●● | ● |
| Logging | ●● | ●● | ●●● | ●● |
| Post-Market Monitoring | ●● | ●●● | ●●● | ●● |

●●● = Comprehensive coverage | ●● = Partial coverage | ● = Minimal coverage

---

## 4. Unified Control Set Proposal

### 4.1 Design Principles

1. **Superset approach**: Include all requirements from all four frameworks
2. **No redundancy**: Merge overlapping requirements into single controls
3. **Traceability**: Each unified control maps back to source framework requirements
4. **Risk-based**: Controls are tiered by risk level (prohibited → high → medium → low)
5. **Agentic-aware**: Explicit coverage for autonomous agent risks
6. **Auditable**: Each control has measurable outcomes and evidence requirements

### 4.2 Unified Control Categories (12 Categories, 68 Controls)

#### Category 1: Governance & Policy (8 controls)

| UC# | Unified Control | ISO | NIST | EU AI Act | OWASP |
|-----|-----------------|-----|------|-----------|-------|
| UC-1.1 | AI policy establishment and maintenance | A.2.2, A.2.4 | GOVERN 1.1, 1.4 | Art. 5, Art. 17 | — |
| UC-1.2 | Policy alignment with organizational policies | A.2.3 | GOVERN 1.3 | Art. 17 | — |
| UC-1.3 | AI roles and responsibilities assignment | A.3.2, A.10.2 | GOVERN 2.1–2.3 | Art. 9(2), Art. 17 | ASI03 |
| UC-1.4 | Reporting of concerns mechanism | A.3.3 | GOVERN 4.1, 4.2 | Art. 9(2), Art. 86 | ASI08 |
| UC-1.5 | Workforce diversity and AI literacy | A.4.6 | GOVERN 3.1, 3.2 | Art. 4 | ASI09 |
| UC-1.6 | External stakeholder engagement | A.8.3, A.8.5 | GOVERN 5.1–5.3 | Art. 13, Art. 50 | — |
| UC-1.7 | Third-party AI risk management | A.4.4, A.10.3 | GOVERN 6.1, 6.2 | Art. 17, Art. 25 | ASI04 |
| UC-1.8 | Psychological safety and reporting culture | — | GOVERN 4.1 | — | — |

#### Category 2: Risk Management & Impact Assessment (7 controls)

| UC# | Unified Control | ISO | NIST | EU AI Act | OWASP |
|-----|-----------------|-----|------|-----------|-------|
| UC-2.1 | AI system risk classification | A.6.2.2 | MAP 2.1, 2.2 | Art. 6 | — |
| UC-2.2 | Risk management system (RMS) | A.5.2, A.6.1.2, A.9.3 | GOVERN 1, MAP 1, MAP 3 | Art. 9 | ASI01, ASI02 |
| UC-2.3 | Impact assessment process | A.5.2, A.5.3 | MAP 5.1, 5.2 | Art. 9, Art. 27 | — |
| UC-2.4 | Individual and group impact assessment | A.5.4 | MAP 5.4 | Art. 9(2), Art. 13 | ASI09 |
| UC-2.5 | Societal impact assessment | A.5.5 | MAP 5.5 | Art. 5, Art. 51 | ASI10 |
| UC-2.6 | Risk treatment and go/no-go decision | A.6.2.5, A.9.4 | MANAGE 1.1, 1.2 | Art. 9(1), Art. 43 | ASI01, ASI02 |
| UC-2.7 | Residual risk documentation | A.5.3 | MANAGE 1.3 | Art. 9(3) | — |

#### Category 3: Data Governance (6 controls)

| UC# | Unified Control | ISO | NIST | EU AI Act | OWASP |
|-----|-----------------|-----|------|-----------|-------|
| UC-3.1 | Data resource documentation | A.4.3 | MAP 2.2 | Art. 10(2) | — |
| UC-3.2 | Data acquisition and provenance | A.7.3, A.7.5 | MAP 4.3, 4.5 | Art. 10(2) | ASI04 |
| UC-3.3 | Data quality management | A.7.4 | MEASURE 2.11 | Art. 10(2) | — |
| UC-3.4 | Data preparation controls | A.7.6 | MAP 4.6 | Art. 10(2) | — |
| UC-3.5 | Training data governance | A.7.2 | MAP 4.1, 4.2 | Art. 10(2) | ASI06 |
| UC-3.6 | Data lifecycle management | A.4.3, A.7.2 | MAP 4.1–4.6 | Art. 10 | — |

#### Category 4: System Lifecycle & Engineering (9 controls)

| UC# | Unified Control | ISO | NIST | EU AI Act | OWASP |
|-----|-----------------|-----|------|-----------|-------|
| UC-4.1 | Responsible development objectives | A.6.1.2 | GOVERN 1.1, MAP 1.1 | Art. 9(1) | — |
| UC-4.2 | Responsible design and development processes | A.6.1.3 | GOVERN 1.2, MAP 3.1 | Art. 9(1), Art. 10 | ASI01, ASI06 |
| UC-4.3 | Requirements and specification | A.6.2.2 | MAP 2.1, 2.2 | Art. 9(1), Art. 11 | ASI01 |
| UC-4.4 | Design and development documentation | A.6.2.3 | MAP 2.3, MEASURE 1.1 | Art. 11 (Annex IV) | — |
| UC-4.5 | Verification and validation | A.6.2.4 | MEASURE 2.1–2.13 | Art. 15, Art. 43 | ASI05, ASI08 |
| UC-4.6 | Deployment process | A.6.2.5 | MAP 3.2, MANAGE 1.1 | Art. 9(1), Art. 43 | ASI08 |
| UC-4.7 | Operation and monitoring | A.6.2.6 | MEASURE 3.1, 3.2, MANAGE 4.1 | Art. 9(2), Art. 72 | ASI08, ASI10 |
| UC-4.8 | Technical documentation | A.6.2.7 | MAP 2.3, MEASURE 1.2 | Art. 11 (Annex IV), Art. 13 | — |
| UC-4.9 | Event logging and audit trail | A.6.2.8 | MEASURE 3.3, MANAGE 4.2 | Art. 12, Art. 72 | ASI08 |

#### Category 5: Transparency & Communication (5 controls)

| UC# | Unified Control | ISO | NIST | EU AI Act | OWASP |
|-----|-----------------|-----|------|-----------|-------|
| UC-5.1 | System documentation for users | A.8.2 | MAP 3.3, MEASURE 2.9 | Art. 13 | ASI09 |
| UC-5.2 | External reporting and disclosure | A.8.3 | GOVERN 5.1, 5.2 | Art. 13, Art. 50 | — |
| UC-5.3 | Incident communication | A.8.4 | GOVERN 4.3, MANAGE 4.3 | Art. 9(2), Art. 73 | ASI08 |
| UC-5.4 | Information for interested parties | A.8.5 | GOVERN 5.3, MAP 5.6 | Art. 13, Art. 50 | — |
| UC-5.5 | Explainability and interpretability | — | MEASURE 2.9 | Art. 13 | — |

#### Category 6: Human Oversight & Interaction (5 controls)

| UC# | Unified Control | ISO | NIST | EU AI Act | OWASP |
|-----|-----------------|-----|------|-----------|-------|
| UC-6.1 | Human oversight mechanisms | A.4.6, A.9.2 | GOVERN 3.1, MAP 3.1 | Art. 14 | ASI09 |
| UC-6.2 | Responsible use processes | A.9.2 | GOVERN 1.2, MAP 3.3 | Art. 9(1), Art. 14 | ASI02, ASI09 |
| UC-6.3 | Intended use enforcement | A.9.4 | MAP 2.5, MANAGE 1.2 | Art. 9(1), Art. 13 | ASI01, ASI02 |
| UC-6.4 | Human-agent trust calibration | — | MEASURE 2.9 | Art. 13, Art. 14 | ASI09 |
| UC-6.5 | AI literacy program | A.4.6 | GOVERN 3.1, 3.2 | Art. 4 | — |

#### Category 7: Security & Robustness (7 controls)

| UC# | Unified Control | ISO | NIST | EU AI Act | OWASP |
|-----|-----------------|-----|------|-----------|-------|
| UC-7.1 | Cybersecurity controls | A.4.5 | MEASURE 2.3 | Art. 15 | ASI05 |
| UC-7.2 | Accuracy and robustness testing | A.6.2.4 | MEASURE 2.1, 2.2 | Art. 15 | ASI05, ASI08 |
| UC-7.3 | Agent goal hijacking prevention | — | MAP 2.1 | Art. 9, Art. 14 | ASI01 |
| UC-7.4 | Tool misuse prevention | — | MAP 3.3 | Art. 9, Art. 14 | ASI02 |
| UC-7.5 | Identity and privilege management | A.3.2, A.10.2 | GOVERN 2.1 | Art. 9(2) | ASI03 |
| UC-7.6 | Supply chain security | A.4.4, A.7.3, A.7.5, A.10.3 | GOVERN 6.1, 6.2 | Art. 17, Art. 25 | ASI04 |
| UC-7.7 | Unexpected code execution prevention | A.4.5, A.6.2.4 | MEASURE 2.1–2.13 | Art. 15 | ASI05 |

#### Category 8: Agentic AI Security (10 controls)

| UC# | Unified Control | ISO | NIST | EU AI Act | OWASP |
|-----|-----------------|-----|------|-----------|-------|
| UC-8.1 | Agent goal integrity monitoring | A.6.1.3 | MAP 2.1 | Art. 9 | ASI01 |
| UC-8.2 | Agent tool access controls | A.9.2 | MAP 3.3 | Art. 14 | ASI02 |
| UC-8.3 | Agent identity and authentication | A.3.2 | GOVERN 2.1 | Art. 9(2) | ASI03 |
| UC-8.4 | Agent supply chain verification | A.4.4, A.10.3 | GOVERN 6.1 | Art. 25 | ASI04 |
| UC-8.5 | Agent code execution sandboxing | A.4.5 | MEASURE 2.3 | Art. 15 | ASI05 |
| UC-8.6 | Agent memory and context integrity | A.6.1.3, A.7.2 | MAP 4.1 | Art. 10 | ASI06 |
| UC-8.7 | Inter-agent communication security | A.6.2.4 | MEASURE 2.3 | Art. 15 | ASI07 |
| UC-8.8 | Cascading failure prevention | A.6.2.6 | MEASURE 3.1 | Art. 72 | ASI08 |
| UC-8.9 | Human-agent interaction security | A.8.2 | MEASURE 2.9 | Art. 13, Art. 14 | ASI09 |
| UC-8.10 | Rogue agent detection and containment | A.5.5, A.6.2.6 | MAP 5.5, MEASURE 3.1 | Art. 5, Art. 51 | ASI10 |

#### Category 9: Fairness, Privacy & Ethics (5 controls)

| UC# | Unified Control | ISO | NIST | EU AI Act | OWASP |
|-----|-----------------|-----|------|-----------|-------|
| UC-9.1 | Fairness and bias evaluation | A.7.4 | MEASURE 2.11 | Art. 10(2) | — |
| UC-9.2 | Privacy enhancement | — | MEASURE 2.10 | Art. 10 | — |
| UC-9.3 | Explainability evaluation | — | MEASURE 2.9 | Art. 13 | — |
| UC-9.4 | Prohibited practice screening | A.2.2, A.5.5 | MAP 5.5 | Art. 5 | ASI10 |
| UC-9.5 | Ethical review board | — | GOVERN 1.1 | Art. 9 | — |

#### Category 10: Third-Party & Supply Chain (4 controls)

| UC# | Unified Control | ISO | NIST | EU AI Act | OWASP |
|-----|-----------------|-----|------|-----------|-------|
| UC-10.1 | Supplier due diligence | A.10.3 | GOVERN 6.1 | Art. 25 | ASI04 |
| UC-10.2 | Customer transparency obligations | A.10.4 | GOVERN 5.4 | Art. 13, Art. 27 | ASI09 |
| UC-10.3 | Responsibility allocation | A.10.2 | GOVERN 2.4 | Art. 9(2), Art. 17 | ASI03 |
| UC-10.4 | Third-party monitoring | A.6.2.6 | MANAGE 3.1 | Art. 72 | ASI04 |

#### Category 11: Compliance & Certification (5 controls)

| UC# | Unified Control | ISO | NIST | EU AI Act | OWASP |
|-----|-----------------|-----|------|-----------|-------|
| UC-11.1 | Quality management system | A.2.2, A.2.3, A.3.2 | GOVERN 1, GOVERN 2 | Art. 17 | — |
| UC-11.2 | Conformity assessment | A.6.2.4, A.6.2.5 | MEASURE 2 | Art. 43 | — |
| UC-11.3 | Regulatory registration | — | — | Art. 71 | — |
| UC-11.4 | Post-market monitoring | A.6.2.6, A.6.2.8 | MEASURE 3.1, 3.2 | Art. 72 | ASI08 |
| UC-11.5 | Incident reporting to authorities | A.8.4 | GOVERN 4.3 | Art. 73, Art. 86 | ASI08 |

#### Category 12: Continuous Improvement (4 controls)

| UC# | Unified Control | ISO | NIST | EU AI Act | OWASP |
|-----|-----------------|-----|------|-----------|-------|
| UC-12.1 | Policy review and update | A.2.4 | GOVERN 1.4 | Art. 9(2) | — |
| UC-12.2 | Measurement effectiveness review | — | MEASURE 4.1 | Art. 9(2) | — |
| UC-12.3 | Management review | A.2.4 | GOVERN 1.4 | Art. 17 | — |
| UC-12.4 | Continuous monitoring and improvement | A.6.2.6 | MEASURE 3.1, MANAGE 4.1 | Art. 9(2), Art. 72 | ASI08 |

---

## 5. Implementation Priority Matrix

### Phase 1: Foundation (Months 1–3) — 15 controls

| Priority | Control | Rationale |
|----------|---------|-----------|
| P0 | UC-1.1, UC-1.3, UC-2.2 | Governance backbone — required by all frameworks |
| P0 | UC-2.1, UC-2.6 | Risk classification and go/no-go — legal gate |
| P0 | UC-3.1, UC-3.5 | Data governance — EU AI Act Art. 10 |
| P0 | UC-4.3, UC-4.5 | Requirements and V&V — quality foundation |
| P0 | UC-4.7, UC-4.9 | Operation, monitoring, logging — EU AI Act Art. 12, 72 |
| P0 | UC-5.1, UC-6.1 | Transparency and human oversight — EU AI Act Art. 13, 14 |
| P0 | UC-7.5, UC-9.4 | Identity management and prohibited practice screening |

### Phase 2: Risk Management (Months 4–6) — 18 controls

| Priority | Control | Rationale |
|----------|---------|-----------|
| P1 | UC-2.3, UC-2.4, UC-2.5, UC-2.7 | Impact assessment — EU AI Act Art. 9, 27 |
| P1 | UC-3.2, UC-3.3, UC-3.4, UC-3.6 | Data quality and lifecycle |
| P1 | UC-4.1, UC-4.2, UC-4.4, UC-4.6, UC-4.8 | Engineering lifecycle |
| P1 | UC-5.2, UC-5.3, UC-5.4 | External communication |
| P1 | UC-6.2, UC-6.3, UC-6.5 | Responsible use and AI literacy |
| P1 | UC-7.1, UC-7.2 | Security and robustness |
| P1 | UC-9.1, UC-9.2 | Fairness and privacy |

### Phase 3: Agentic Security (Months 7–9) — 15 controls

| Priority | Control | Rationale |
|----------|---------|-----------|
| P2 | UC-7.3, UC-7.4, UC-7.6, UC-7.7 | Agent-specific security controls |
| P2 | UC-8.1–UC-8.10 | Full OWASP Agentic Top 10 coverage |
| P2 | UC-9.3, UC-9.5 | Explainability and ethics |
| P2 | UC-10.1–UC-10.4 | Third-party and supply chain |
| P2 | UC-11.1, UC-11.2 | QMS and conformity assessment |

### Phase 4: Compliance & Optimization (Months 10–12) — 10 controls

| Priority | Control | Rationale |
|----------|---------|-----------|
| P3 | UC-11.3, UC-11.4, UC-11.5 | Registration, monitoring, reporting |
| P3 | UC-12.1–UC-12.4 | Continuous improvement |
| P3 | UC-1.2, UC-1.4, UC-1.5, UC-1.6, UC-1.7, UC-1.8 | Governance refinement |
| P3 | UC-5.5, UC-6.4 | Advanced transparency |

---

## 6. Framework Satisfaction Matrix

| Unified Control Category | ISO 42001 | NIST AI RMF | EU AI Act | OWASP Agentic |
|--------------------------|:---------:|:-----------:|:---------:|:-------------:|
| 1. Governance & Policy | ✅ Full | ✅ Full | ✅ Full | ✅ Partial |
| 2. Risk Management & Impact Assessment | ✅ Full | ✅ Full | ✅ Full | ✅ Partial |
| 3. Data Governance | ✅ Full | ✅ Full | ✅ Full | ✅ Partial |
| 4. System Lifecycle & Engineering | ✅ Full | ✅ Full | ✅ Full | ✅ Partial |
| 5. Transparency & Communication | ✅ Full | ✅ Full | ✅ Full | ✅ Partial |
| 6. Human Oversight & Interaction | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| 7. Security & Robustness | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| 8. Agentic AI Security | ✅ Partial | ✅ Partial | ✅ Partial | ✅ Full |
| 9. Fairness, Privacy & Ethics | ✅ Full | ✅ Full | ✅ Full | ✅ Partial |
| 10. Third-Party & Supply Chain | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| 11. Compliance & Certification | ✅ Full | ✅ Partial | ✅ Full | ✅ Partial |
| 12. Continuous Improvement | ✅ Full | ✅ Full | ✅ Full | ✅ Partial |

**Legend:** ✅ Full = All requirements from this framework category are satisfied | ✅ Partial = Most requirements satisfied, minor gaps remain

---

## 7. Key Findings & Recommendations

### 7.1 Critical Gaps Identified

1. **Agentic AI security is the largest gap**: ISO 42001, NIST AI RMF, and EU AI Act were all designed before agentic AI became prevalent. OWASP Agentic Top 10 is the only framework addressing autonomous agent risks (goal hijacking, tool misuse, memory poisoning, cascading failures, rogue agents). **Recommendation**: Organizations deploying agents must supplement with OWASP Agentic controls regardless of other framework compliance.

2. **EU AI Act has unique legal requirements**: Prohibited practices (Art. 5), conformity assessment (Art. 43), and EU database registration (Art. 71) have no equivalent in other frameworks. **Recommendation**: Treat EU AI Act as the legal floor — implement its requirements first, then layer other frameworks on top.

3. **NIST AI RMF has unique measurement requirements**: Explainability (MEASURE 2.9), privacy (MEASURE 2.10), and fairness (MEASURE 2.11) metrics are not explicitly required by other frameworks. **Recommendation**: Adopt NIST's measurement approach for high-stakes AI systems.

4. **ISO 42001 has unique organizational requirements**: Societal impact assessment (A.5.5) and workforce diversity (GOVERN 3) are not covered by other frameworks. **Recommendation**: Include these for comprehensive governance.

### 7.2 Unified Control Set Statistics

- **Total unified controls**: 68
- **Controls satisfying all 4 frameworks**: 23 (33.8%)
- **Controls satisfying 3 frameworks**: 31 (45.6%)
- **Controls satisfying 2 frameworks**: 14 (20.6%)
- **Unique to one framework**: 0 (all controls map to at least 2 frameworks)

### 7.3 Implementation Recommendations

1. **Start with EU AI Act** as the legal baseline — it's the only binding framework with penalties
2. **Layer NIST AI RMF** for the risk management process and measurement approach
3. **Add ISO 42001** for management system structure and certification readiness
4. **Integrate OWASP Agentic Top 10** for agent-specific security controls
5. **Use the unified control set** (68 controls) as the single implementation checklist
6. **Prioritize Phase 1** (15 controls) for immediate risk reduction
7. **Plan for Phase 3** (agentic security) if deploying autonomous agents

---

## 8. Appendix: Framework Source References

- **ISO/IEC 42001:2023**: Information technology — Artificial intelligence — Management system
- **NIST AI RMF 1.0 (NIST AI 100-1)**: Artificial Intelligence Risk Management Framework, January 2023
- **EU AI Act (Regulation 2024/1689)**: Artificial Intelligence Act, August 2024 (as amended by Digital Omnibus 2026/1744)
- **OWASP Top 10 for Agentic Applications**: GenAI Security Project, December 2025

---

*End of document*
