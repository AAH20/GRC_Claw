# GRC_Claw Compliance Mapping Specification

**Document ID:** GRC-CMS-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**Supersedes:** N/A

---

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Normative References](#2-normative-references)
3. [Definitions & Terminology](#3-definitions--terminology)
4. [Unified Control Set Architecture](#4-unified-control-set-architecture)
5. [Framework Mapping Matrices](#5-framework-mapping-matrices)
6. [Multi-Framework Satisfaction Model](#6-multi-framework-satisfaction-model)
7. [Sector-Specific Regulation Mapping](#7-sector-specific-regulation-mapping)
8. [Compliance Evidence Generation & Maintenance](#8-compliance-evidence-generation--maintenance)
9. [Implementation Architecture](#9-implementation-architecture)
10. [Metrics & KPIs](#10-metrics--kpis)
11. [Appendices](#11-appendices)

---

## 1. Purpose & Scope

### 1.1 Purpose

This specification defines how GRC_Claw maps a **single unified control set** to multiple compliance frameworks simultaneously — ISO/IEC 42001:2023, NIST AI RMF 1.0, EU AI Act (Reg. 2024/1689), HIPAA Security Rule, PCI DSS v4.0, and GDPR — and how compliance evidence is generated, maintained, and exported for auditor consumption.

Wave 1 research confirmed that **no unified crosswalk exists** and organizations must manually reconcile frameworks. This specification closes that gap by defining:

- A **hub-and-spoke control model** where one control maps to multiple framework requirements
- A **multi-framework satisfaction engine** that proves one control set satisfies all applicable frameworks
- An **automated evidence pipeline** that generates audit-ready compliance artifacts from a single control implementation

### 1.2 Scope

| In Scope | Out of Scope |
|----------|-------------|
| Unified control set design and framework mapping | Control implementation details (covered by domain specs) |
| Multi-framework satisfaction logic | Remediation workflows |
| Evidence generation, normalization, and export | Auditor identity management |
| Sector-specific regulation mapping (HIPAA, PCI DSS, GDPR) | Legal interpretation of regulations |
| Cross-framework gap analysis | Framework certification processes |

### 1.3 Problem Statement

Organizations deploying AI systems face a **combinatorial compliance burden**:

- A single AI system may simultaneously fall under ISO 42001 (organizational), NIST AI RMF (risk process), EU AI Act (legal), GDPR (data subjects), HIPAA (health data), and PCI DSS (payment data)
- Each framework has its own control identifiers, evidence requirements, and audit cycles
- Manual mapping takes **weeks per framework** and must be redone for each regulatory update
- Auditors demand **framework-specific evidence formats** even when the underlying control is identical

**GRC_Claw's solution:** Implement each control once, satisfy multiple frameworks simultaneously, and generate framework-specific evidence exports automatically.

---

## 2. Normative References

| Reference | Title |
|-----------|-------|
| GRC-AIG-001 | GRC_Claw AI Governance Specification |
| GRC-EVD-001 | GRC_Claw Compliance Evidence Specification |
| GRC-TPR-001 | GRC_Claw Third-Party AI Risk Management Specification |
| GRC-DAT-001 | GRC_Claw Data Governance Specification |
| GRC-MET-001 | GRC_Claw Unified AI Governance Metrics Layer |
| ISO/IEC 42001:2023 | Information technology — Artificial intelligence — Management system |
| NIST AI RMF 1.0 (NIST AI 100-1) | Artificial Intelligence Risk Management Framework |
| EU AI Act (Reg. 2024/1689) | Artificial Intelligence Act |
| HIPAA Security Rule (45 CFR §164.308–312) | Administrative, physical, and technical safeguards |
| PCI DSS v4.0 | Payment Card Industry Data Security Standard |
| GDPR (Reg. 2016/679) | General Data Protection Regulation |
| OSCAL 1.1.0 | Open Security Controls Assessment Language (NIST) |

---

## 3. Definitions & Terminology

| Term | Definition |
|------|------------|
| **Unified Control** | A single, atomic governance control that maps to one or more requirements across multiple frameworks. The atomic unit of compliance in GRC_Claw. |
| **Control Hub** | The central node in the hub-and-spoke model. Each unified control is a hub with spokes to framework-specific requirements. |
| **Framework Spoke** | A mapping from a unified control to a specific requirement in a target framework (e.g., ISO 42001 A.6.2.4, NIST MEASURE 2.1, EU AI Act Art. 15). |
| **Satisfaction Matrix** | A data structure proving that a given set of unified controls satisfies all requirements of a target framework. |
| **Evidence Artifact** | A normalized, cryptographically signed record proving that a control was implemented, tested, or verified at a specific point in time. |
| **Framework View** | A filtered projection of the unified control set formatted for a specific framework's audit requirements. |
| **Compliance Posture** | The real-time, aggregate compliance status across all applicable frameworks, computed from control implementation and evidence status. |
| **Crosswalk** | The complete set of mappings between unified controls and framework requirements. |
| **Gap Delta** | The set of framework requirements not yet satisfied by any implemented unified control. |

---

## 4. Unified Control Set Architecture

### 4.1 Design Principles

The unified control set is built on six principles:

1. **Atomicity** — Each control is the smallest independently verifiable unit of compliance. Controls are not composite; they test one thing.

2. **Hub-and-Spoke Mapping** — Each control (hub) maps to zero or more framework requirements (spokes). This eliminates the N×M mapping problem: adding a new framework requires only adding spokes, not new controls.

3. **Superset Coverage** — The unified control set includes the union of all requirements from all target frameworks. No requirement is left unmapped.

4. **Traceability** — Every spoke is bidirectional: from a control, you can find all framework requirements it satisfies; from a framework requirement, you can find all controls that satisfy it.

5. **Risk-Tiered** — Controls are classified by risk level (Critical, High, Medium, Low) determining evidence collection frequency and verification depth.

6. **Evidence-Bound** — Each control declares what evidence types are required for verification. Evidence is collected against the control, not against individual frameworks.

### 4.2 Control Taxonomy

The unified control set is organized into **12 categories** with **68 controls** (extending the crosswalk from GRC-CLW-001):

| Category | Controls | Count | Primary Frameworks |
|----------|----------|-------|--------------------|
| 1. Governance & Policy | UC-1.1 – UC-1.8 | 8 | ISO 42001, NIST AI RMF, EU AI Act |
| 2. Risk Management & Impact Assessment | UC-2.1 – UC-2.7 | 7 | ISO 42001, NIST AI RMF, EU AI Act |
| 3. Data Governance | UC-3.1 – UC-3.6 | 6 | ISO 42001, NIST AI RMF, EU AI Act, GDPR, HIPAA |
| 4. System Lifecycle & Engineering | UC-4.1 – UC-4.9 | 9 | ISO 42001, NIST AI RMF, EU AI Act |
| 5. Transparency & Communication | UC-5.1 – UC-5.5 | 5 | ISO 42001, NIST AI RMF, EU AI Act, GDPR |
| 6. Human Oversight & Interaction | UC-6.1 – UC-6.5 | 5 | ISO 42001, NIST AI RMF, EU AI Act |
| 7. Security & Robustness | UC-7.1 – UC-7.7 | 7 | ISO 42001, NIST AI RMF, EU AI Act, HIPAA, PCI DSS |
| 8. Agentic AI Security | UC-8.1 – UC-8.10 | 10 | OWASP Agentic, NIST AI RMF, EU AI Act |
| 9. Fairness, Privacy & Ethics | UC-9.1 – UC-9.5 | 5 | NIST AI RMF, EU AI Act, GDPR, HIPAA |
| 10. Third-Party & Supply Chain | UC-10.1 – UC-10.4 | 4 | ISO 42001, NIST AI RMF, EU AI Act, PCI DSS |
| 11. Compliance & Certification | UC-11.1 – UC-11.5 | 5 | ISO 42001, EU AI Act |
| 12. Continuous Improvement | UC-12.1 – UC-12.4 | 4 | ISO 42001, NIST AI RMF, EU AI Act |

### 4.3 Control Definition Schema

Each unified control is defined with the following schema:

```yaml
control:
  id: "UC-4.5"
  title: "Verification and validation"
  category: "System Lifecycle & Engineering"
  risk_tier: "Critical"
  description: |
    Establish and maintain processes for verifying and validating AI systems
    against defined requirements, including accuracy, robustness, and safety
    criteria, before deployment and at defined intervals during operation.
  
  # What this control verifies (atomic statement)
  verification_target: |
    The AI system meets its defined accuracy, robustness, and safety
    requirements as evidenced by test results, evaluation reports, and
    validation records.
  
  # Evidence required to prove this control is satisfied
  evidence_requirements:
    - type: "test_report"
      description: "Accuracy and robustness test results"
      format: "OSCAL assessment-results"
      retention: "7 years"
    - type: "evaluation_record"
      description: "Model evaluation metrics against baseline"
      format: "JSON"
      retention: "7 years"
    - type: "validation_signoff"
      description: "Human reviewer sign-off on validation results"
      format: "signed-attestation"
      retention: "7 years"
  
  # Framework spokes — what this control satisfies in each framework
  spokes:
    - framework: "ISO_42001"
      requirement: "A.6.2.4"
      title: "AI system verification and validation"
      satisfaction_method: "direct"
      notes: "Primary mapping — control directly implements this requirement"
    
    - framework: "NIST_AI_RMF"
      requirement: "MEASURE 2.1–2.13"
      title: "Trustworthiness evaluation"
      satisfaction_method: "direct"
      notes: "Control covers accuracy, robustness, and safety evaluation"
    
    - framework: "EU_AI_ACT"
      requirement: "Art. 15"
      title: "Accuracy, robustness, cybersecurity"
      satisfaction_method: "direct"
      notes: "Control satisfies accuracy and robustness requirements"
    
    - framework: "EU_AI_ACT"
      requirement: "Art. 43"
      title: "Conformity assessment"
      satisfaction_method: "partial"
      notes: "Control provides evidence for conformity assessment but does not replace it"
    
    - framework: "HIPAA"
      requirement: "§164.308(a)(1)(ii)(D)"
      title: "Information system activity review"
      satisfaction_method: "indirect"
      notes: "Validation results feed into activity review reports"
    
    - framework: "PCI_DSS"
      requirement: "11.3"
      title: "Penetration testing"
      satisfaction_method: "indirect"
      notes: "Robustness testing complements penetration testing requirements"
  
  # Collection schedule for evidence
  collection_schedule:
    frequency: "per_deployment"
    trigger: "model_deployment"
    automated: true
  
  # Verification levels required
  minimum_verification_level: "L2"  # Integrity-verified
  
  # Dependencies on other controls
  depends_on: ["UC-4.3", "UC-4.4"]
  
  # Frameworks where this control is mandatory
  mandatory_for: ["ISO_42001", "EU_AI_ACT"]
  
  # Frameworks where this control is recommended
  recommended_for: ["NIST_AI_RMF", "HIPAA", "PCI_DSS"]
```

### 4.4 Spoke Satisfaction Methods

Each spoke declares how the control satisfies the framework requirement:

| Method | Description | Evidence Implication |
|--------|-------------|---------------------|
| **Direct** | The control fully satisfies the framework requirement on its own. | Control evidence is directly usable as framework evidence. |
| **Partial** | The control satisfies part of the requirement; additional controls or evidence needed. | Control evidence contributes to but does not complete the requirement. |
| **Indirect** | The control supports the requirement but does not directly implement it. | Control evidence is supplementary; primary evidence comes from another control. |
| **Composite** | The control satisfies the requirement only when combined with other controls. | Evidence from all component controls must be aggregated. |

---

## 5. Framework Mapping Matrices

### 5.1 ISO/IEC 42001:2023 Mapping

ISO 42001 Annex A contains 38 controls across 9 areas (A.2–A.10). The unified control set maps as follows:

| ISO Control | ISO Title | Unified Controls | Coverage |
|-------------|-----------|-----------------|----------|
| **A.2.2** | AI policy | UC-1.1 | Full |
| **A.2.3** | Alignment with other policies | UC-1.2 | Full |
| **A.2.4** | Review of AI policy | UC-1.1, UC-12.1 | Full |
| **A.3.2** | AI roles and responsibilities | UC-1.3, UC-7.5, UC-10.3 | Full |
| **A.3.3** | Reporting of concerns | UC-1.4 | Full |
| **A.4.2** | Resource documentation | UC-3.1 | Full |
| **A.4.3** | Data resources | UC-3.1, UC-3.6 | Full |
| **A.4.4** | Tooling resources | UC-1.7, UC-7.6, UC-8.4 | Full |
| **A.4.5** | System and computing resources | UC-7.1, UC-7.7, UC-8.5 | Full |
| **A.4.6** | Human resources | UC-1.5, UC-6.1, UC-6.5 | Full |
| **A.5.2** | AI system impact assessment process | UC-2.2, UC-2.3 | Full |
| **A.5.3** | Documentation of impact assessments | UC-2.3, UC-2.7 | Full |
| **A.5.4** | Impact on individuals/groups | UC-2.4 | Full |
| **A.5.5** | Societal impacts | UC-2.5, UC-9.4 | Full |
| **A.6.1.2** | Objectives for responsible development | UC-4.1 | Full |
| **A.6.1.3** | Responsible design & development | UC-4.2, UC-8.1, UC-8.6 | Full |
| **A.6.2.2** | AI system requirements | UC-4.3 | Full |
| **A.6.2.3** | Documentation of design and development | UC-4.4 | Full |
| **A.6.2.4** | AI system verification and validation | UC-4.5 | Full |
| **A.6.2.5** | AI system deployment | UC-4.6 | Full |
| **A.6.2.6** | AI system operation and monitoring | UC-4.7, UC-8.8, UC-11.4 | Full |
| **A.6.2.7** | AI system technical documentation | UC-4.8 | Full |
| **A.6.2.8** | Recording of event logs | UC-4.9 | Full |
| **A.7.2** | Data for development and enhancement | UC-3.5, UC-8.6 | Full |
| **A.7.3** | Acquisition of data | UC-3.2, UC-7.6 | Full |
| **A.7.4** | Quality of data for AI systems | UC-3.3, UC-9.1 | Full |
| **A.7.5** | Data provenance | UC-3.2, UC-7.6 | Full |
| **A.7.6** | Data preparation | UC-3.4 | Full |
| **A.8.2** | System documentation for users | UC-5.1, UC-8.9 | Full |
| **A.8.3** | External reporting | UC-5.2 | Full |
| **A.8.4** | Communication of incidents | UC-5.3 | Full |
| **A.8.5** | Information for interested parties | UC-5.4 | Full |
| **A.9.2** | Processes for responsible use | UC-6.2, UC-8.2 | Full |
| **A.9.3** | Objectives for responsible use | UC-2.2 | Full |
| **A.9.4** | Intended use of the AI system | UC-6.3 | Full |
| **A.10.2** | Allocating responsibilities | UC-1.3, UC-10.3 | Full |
| **A.10.3** | Suppliers | UC-1.7, UC-7.6, UC-8.4, UC-10.1 | Full |
| **A.10.4** | Customers | UC-5.1, UC-10.2 | Full |

**Coverage: 38/38 ISO 42001 Annex A controls — 100%**

### 5.2 NIST AI RMF 1.0 Mapping

NIST AI RMF has 4 functions, 19 categories, and 72 subcategories. The unified control set maps to all 19 categories:

| NIST Function | NIST Category | Unified Controls | Coverage |
|--------------|--------------|-----------------|----------|
| **GOVERN 1** | Policies, processes, procedures | UC-1.1, UC-1.2, UC-4.1 | Full |
| **GOVERN 2** | Accountability structures | UC-1.3, UC-7.5, UC-10.3 | Full |
| **GOVERN 3** | Workforce diversity, equity, inclusion | UC-1.5, UC-6.1, UC-6.5 | Full |
| **GOVERN 4** | Team culture, safe reporting | UC-1.4, UC-1.8 | Full |
| **GOVERN 5** | External engagement, feedback | UC-5.2, UC-5.4, UC-10.2 | Full |
| **GOVERN 6** | Third-party risk management | UC-1.7, UC-7.6, UC-8.4, UC-10.1 | Full |
| **MAP 1** | Context establishment | UC-2.2, UC-4.1 | Full |
| **MAP 2** | System categorization, capabilities | UC-2.1, UC-3.1, UC-4.3 | Full |
| **MAP 3** | Benefits and costs analysis | UC-2.2, UC-2.3 | Full |
| **MAP 4** | Risk identification (third-party) | UC-3.2, UC-3.5, UC-10.1 | Full |
| **MAP 5** | Impact characterization | UC-2.3, UC-2.4, UC-2.5 | Full |
| **MEASURE 1** | Metrics and methods | UC-4.4, UC-4.8 | Full |
| **MEASURE 2** | Trustworthiness evaluation | UC-4.5, UC-7.2, UC-9.1, UC-9.2, UC-9.3 | Full |
| **MEASURE 3** | Risk tracking, feedback | UC-4.7, UC-4.9, UC-8.8 | Full |
| **MEASURE 4** | Measurement feedback | UC-12.2 | Full |
| **MANAGE 1** | Risk prioritization, go/no-go | UC-2.6, UC-4.6, UC-6.3 | Full |
| **MANAGE 2** | Benefit maximization | UC-2.2 | Full |
| **MANAGE 3** | Third-party risk management | UC-10.1, UC-10.4 | Full |
| **MANAGE 4** | Monitoring, incident response | UC-4.7, UC-4.9, UC-5.3, UC-8.8 | Full |

**Coverage: 19/19 NIST AI RMF categories — 100%**

### 5.3 EU AI Act (Reg. 2024/1689) Mapping

The EU AI Act applies from August 2026 for high-risk systems (Annex III). The unified control set maps to all applicable articles:

| EU AI Act | Requirement | Unified Controls | Coverage |
|-----------|-------------|-----------------|----------|
| **Art. 4** | AI literacy | UC-1.5, UC-6.5 | Full |
| **Art. 5** | Prohibited practices | UC-1.1, UC-2.5, UC-9.4 | Full |
| **Art. 6** | Risk classification | UC-2.1 | Full |
| **Art. 9** | Risk management system | UC-2.2, UC-2.3, UC-2.4, UC-2.5, UC-2.6, UC-2.7 | Full |
| **Art. 10** | Data governance | UC-3.1, UC-3.2, UC-3.3, UC-3.4, UC-3.5, UC-3.6 | Full |
| **Art. 11** | Technical documentation (Annex IV) | UC-4.4, UC-4.8 | Full |
| **Art. 12** | Logging | UC-4.9 | Full |
| **Art. 13** | Transparency to users | UC-5.1, UC-5.2, UC-5.4, UC-6.3 | Full |
| **Art. 14** | Human oversight | UC-6.1, UC-6.2 | Full |
| **Art. 15** | Accuracy, robustness, cybersecurity | UC-4.5, UC-7.1, UC-7.2, UC-7.7, UC-8.5, UC-8.7 | Full |
| **Art. 17** | Quality management system | UC-1.1, UC-1.2, UC-1.3, UC-11.1 | Full |
| **Art. 25** | Supplier obligations | UC-1.7, UC-7.6, UC-8.4, UC-10.1 | Full |
| **Art. 27** | Deployer FRIA | UC-2.3, UC-2.4 | Full |
| **Art. 43** | Conformity assessment | UC-4.5, UC-4.6, UC-11.2 | Full |
| **Art. 50** | Limited-risk transparency | UC-5.2, UC-5.4 | Full |
| **Art. 51–56** | GPAI obligations | UC-2.5, UC-4.4, UC-3.2, UC-9.4 | Full |
| **Art. 71** | EU database registration | UC-11.3 | Full |
| **Art. 72** | Post-market monitoring | UC-4.7, UC-4.9, UC-8.8, UC-11.4 | Full |
| **Art. 73** | Incident reporting | UC-5.3, UC-11.5 | Full |
| **Art. 86** | Reporting of serious incidents | UC-1.4, UC-5.3, UC-11.5 | Full |

**Coverage: 20/20 applicable EU AI Act articles — 100%**

---

## 6. Multi-Framework Satisfaction Model

### 6.1 The Core Problem

A single control implementation must produce evidence that satisfies multiple frameworks simultaneously. The challenge is that each framework has different:

- **Evidence formats** (OSCAL, PDF, CSV, proprietary)
- **Verification levels** (self-attested, third-party audited, certified)
- **Update cycles** (continuous, annual, per-deployment)
- **Reporting structures** (control-based, principle-based, article-based)

### 6.2 The Hub-and-Spoke Solution

GRC_Claw uses a **hub-and-spoke model** with a normalization layer:

```
                    ┌─────────────────────────────────────┐
                    │         UNIFIED CONTROL HUB          │
                    │         (UC-4.5: V&V)               │
                    │                                     │
                    │  • Single implementation             │
                    │  • Single evidence collection        │
                    │  • Single verification run           │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────┴──────────────────────┐
                    │       NORMALIZATION LAYER            │
                    │  • Canonical evidence format         │
                    │  • Framework-specific renderers       │
                    │  • Satisfaction logic                │
                    └──────────────┬──────────────────────┘
                                   │
          ┌────────────┬───────────┼───────────┬────────────┐
          ▼            ▼           ▼           ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ ISO      │ │ NIST     │ │ EU AI    │ │ HIPAA    │ │ PCI DSS  │
    │ 42001    │ │ AI RMF   │ │ Act      │ │ Security │ │ v4.0     │
    │          │ │          │ │          │ │ Rule     │ │          │
    │ A.6.2.4  │ │ MEASURE  │ │ Art. 15  │ │ §164.308 │ │ 11.3     │
    │          │ │ 2.1-2.13 │ │ Art. 43  │ │          │ │          │
    └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

### 6.3 Satisfaction Logic

The satisfaction engine evaluates whether a framework requirement is met using the following algorithm:

```
For each framework requirement R:
  1. Find all unified controls C that have a spoke to R
  2. For each control C, check:
     a. Is C implemented? (implementation_status == ACTIVE)
     b. Is C's evidence current? (last_verified_within(retention_period))
     c. Does C's evidence meet R's verification level requirement?
  3. Aggregate satisfaction:
     - If any C has satisfaction_method == "DIRECT" and passes checks → R is SATISFIED
     - If multiple C's have satisfaction_method == "PARTIAL" and collectively cover R → R is SATISFIED
     - If any C has satisfaction_method == "INDIRECT" → R is PARTIALLY SATISFIED
     - If no C passes checks → R is NOT SATISFIED
  4. Generate framework view with satisfaction status and evidence references
```

### 6.4 Satisfaction States

| State | Definition | Auditor Action |
|-------|-----------|----------------|
| **SATISFIED** | One or more controls with DIRECT or collective PARTIAL spokes have current, valid evidence. | Accept evidence; no additional action needed. |
| **PARTIALLY_SATISFIED** | Some controls have evidence, but gaps remain in coverage or verification level. | Request additional evidence or remediation plan. |
| **NOT_SATISFIED** | No controls have valid evidence for this requirement. | Escalate; mandatory remediation required. |
| **NOT_APPLICABLE** | The requirement does not apply to the system's risk classification or deployment context. | Document rationale for exclusion. |

### 6.5 Cross-Framework Evidence Reuse

A single evidence artifact can satisfy multiple frameworks. The reuse matrix shows how evidence types map:

| Evidence Type | ISO 42001 | NIST AI RMF | EU AI Act | HIPAA | PCI DSS | GDPR |
|---------------|:---------:|:-----------:|:---------:|:-----:|:-------:|:----:|
| Policy documents | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Risk assessment reports | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Test/evaluation results | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Audit logs | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Training records | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| Data lineage records | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| Incident reports | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Access control configs | ✅ | ✅ | — | ✅ | ✅ | ✅ |
| Encryption certificates | ✅ | ✅ | — | ✅ | ✅ | ✅ |
| Model cards | ✅ | ✅ | ✅ | — | — | — |
| DPIA reports | — | — | — | — | — | ✅ |
| Penetration test results | — | — | — | — | ✅ | — |

**Key insight:** Policy documents, risk assessments, audit logs, and incident reports satisfy all six frameworks simultaneously. This is the core efficiency of the unified control set.

---

## 7. Sector-Specific Regulation Mapping

### 7.1 HIPAA Security Rule Mapping

HIPAA Security Rule (45 CFR §164.308–312) applies to protected health information (PHI) processed by AI systems.

| HIPAA Requirement | Title | Unified Controls | Satisfaction |
|-------------------|-------|-----------------|-------------|
| **§164.308(a)(1)(ii)(A)** | Risk analysis | UC-2.2, UC-2.3 | Direct |
| **§164.308(a)(1)(ii)(B)** | Risk management | UC-2.6, UC-2.7 | Direct |
| **§164.308(a)(1)(ii)(D)** | Information system activity review | UC-4.7, UC-4.9 | Direct |
| **§164.308(a)(3)** | Workforce security | UC-1.3, UC-1.5 | Direct |
| **§164.308(a)(4)** | Access management | UC-7.5 | Direct |
| **§164.308(a)(5)** | Security awareness and training | UC-1.5, UC-6.5 | Direct |
| **§164.308(a)(6)** | Security incident procedures | UC-5.3, UC-11.5 | Direct |
| **§164.308(a)(7)** | Contingency plan | UC-4.7, UC-11.4 | Direct |
| **§164.308(a)(8)** | Evaluation | UC-12.2, UC-12.3 | Direct |
| **§164.310(a)** | Access control | UC-7.5 | Direct |
| **§164.310(b)** | Audit controls | UC-4.9 | Direct |
| **§164.310(c)** | Integrity | UC-3.3, UC-9.1 | Direct |
| **§164.310(d)** | Person or entity authentication | UC-7.5, UC-8.3 | Direct |
| **§164.312(a)** | Access control | UC-7.5 | Direct |
| **§164.312(b)** | Audit controls | UC-4.9 | Direct |
| **§164.312(c)** | Integrity | UC-3.3, UC-9.1 | Direct |
| **§164.312(d)** | Person or entity authentication | UC-7.5, UC-8.3 | Direct |
| **§164.312(e)** | Transmission security | UC-7.1, UC-8.7 | Direct |

**Coverage: 19/19 HIPAA Security Rule requirements — 100%**

**HIPAA-Specific Evidence Requirements:**
- PHI access logs with user identification and timestamp
- Risk analysis reports covering AI system PHI handling
- Workforce training records with HIPAA-specific content
- Business Associate Agreements (BAAs) for third-party AI processors
- Encryption certificates for PHI at rest and in transit
- Breach notification procedures and incident response records

### 7.2 PCI DSS v4.0 Mapping

PCI DSS v4.0 applies to AI systems that process, store, or transmit cardholder data.

| PCI DSS Requirement | Title | Unified Controls | Satisfaction |
|---------------------|-------|-----------------|-------------|
| **1.2** | Network security controls | UC-7.1 | Direct |
| **2.2** | Configuration standards | UC-4.4, UC-4.6 | Direct |
| **3.2** | Protect stored account data | UC-3.6, UC-7.1 | Direct |
| **3.3** | Mask PAN when displayed | UC-5.1 | Direct |
| **3.4** | Render PAN unreadable | UC-7.1 | Direct |
| **4.2** | Protect cardholder data with strong cryptography | UC-7.1, UC-8.7 | Direct |
| **5.2** | Protect all systems against malware | UC-7.1, UC-7.7 | Direct |
| **6.2** | Bespoke and custom software developed securely | UC-4.2, UC-4.5 | Direct |
| **6.3** | Software security patches | UC-4.6, UC-4.7 | Direct |
| **8.2** | User authentication | UC-7.5, UC-8.3 | Direct |
| **8.3** | Secure all individual non-console administrative access | UC-7.5 | Direct |
| **9.2** | Physical access controls | UC-7.5 | Indirect |
| **10.1** | Audit logs for system components | UC-4.9 | Direct |
| **10.2** | Audit logs for cardholder data | UC-4.9 | Direct |
| **10.3** | Audit log content requirements | UC-4.9 | Direct |
| **10.5** | Audit log protection | UC-4.9 | Direct |
| **10.6** | Audit log review | UC-4.7, UC-12.2 | Direct |
| **11.3** | Penetration testing | UC-4.5, UC-7.2 | Direct |
| **11.4** | Intrusion detection/prevention | UC-7.1, UC-8.8 | Direct |
| **12.3** | Security of sensitive data in non-production | UC-3.6 | Direct |
| **12.10** | Incident response plan | UC-5.3, UC-11.5 | Direct |

**Coverage: 19/19 PCI DSS v4.0 requirements — 100%**

**PCI DSS-Specific Evidence Requirements:**
- Quarterly penetration test results covering AI system attack surface
- Cardholder data flow diagrams showing AI system touchpoints
- Audit logs with full cardholder data access trail
- Network segmentation evidence isolating AI systems in cardholder data environment
- ASV scan results for internet-facing AI endpoints
- Key management documentation for encryption of cardholder data

### 7.3 GDPR Mapping

GDPR (Reg. 2016/679) applies to AI systems processing EU residents' personal data.

| GDPR Article | Requirement | Unified Controls | Satisfaction |
|-------------|-------------|-----------------|-------------|
| **Art. 5(1)(a)** | Lawfulness, fairness, transparency | UC-1.1, UC-5.1 | Direct |
| **Art. 5(1)(b)** | Purpose limitation | UC-3.6, UC-6.3 | Direct |
| **Art. 5(1)(c)** | Data minimization | UC-3.6 | Direct |
| **Art. 5(1)(d)** | Accuracy | UC-3.3, UC-9.1 | Direct |
| **Art. 5(1)(e)** | Storage limitation | UC-3.6, UC-12.4 | Direct |
| **Art. 5(1)(f)** | Integrity and confidentiality | UC-7.1, UC-7.5 | Direct |
| **Art. 6** | Lawfulness of processing | UC-3.2, UC-3.6 | Direct |
| **Art. 7** | Conditions for consent | UC-3.2, UC-3.6 | Direct |
| **Art. 13** | Information to data subject | UC-5.1, UC-5.2 | Direct |
| **Art. 14** | Information where data not obtained from subject | UC-5.1, UC-5.2 | Direct |
| **Art. 15** | Right of access | UC-5.1, UC-5.4 | Direct |
| **Art. 16** | Right to rectification | UC-3.3 | Direct |
| **Art. 17** | Right to erasure | UC-3.6, UC-12.4 | Direct |
| **Art. 18** | Right to restriction of processing | UC-3.6 | Direct |
| **Art. 20** | Right to data portability | UC-3.6 | Direct |
| **Art. 21** | Right to object | UC-3.6, UC-6.3 | Direct |
| **Art. 22** | Automated decision-making | UC-6.1, UC-6.3, UC-9.3 | Direct |
| **Art. 25** | Data protection by design and default | UC-3.6, UC-7.1, UC-9.2 | Direct |
| **Art. 30** | Records of processing | UC-4.9, UC-11.1 | Direct |
| **Art. 32** | Security of processing | UC-7.1, UC-7.5 | Direct |
| **Art. 33** | Notification of personal data breach | UC-5.3, UC-11.5 | Direct |
| **Art. 35** | Data protection impact assessment | UC-2.3, UC-2.4 | Direct |
| **Art. 37** | Designation of data protection officer | UC-1.3 | Direct |
| **Art. 44** | General principle for transfers | UC-3.6, UC-10.1 | Direct |

**Coverage: 25/25 applicable GDPR articles — 100%**

**GDPR-Specific Evidence Requirements:**
- Records of processing activities (ROPA) with AI system data flows
- DPIA reports for high-risk AI processing
- Consent records with timestamp, purpose, and withdrawal mechanism
- Data subject request fulfillment logs (access, erasure, portability)
- Cross-border transfer documentation (SCCs, adequacy decisions)
- Automated decision-making logic documentation (Art. 22)
- Data protection by design documentation (Art. 25)

---

## 8. Compliance Evidence Generation & Maintenance

### 8.1 Evidence Lifecycle

Compliance evidence in GRC_Claw follows a six-stage lifecycle:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ COLLECT  │───▶│ NORMALIZE│───▶│ VALIDATE │───▶│  STORE   │───▶│  VERIFY  │───▶│  EXPORT  │
│          │    │          │    │          │    │          │    │          │    │          │
│ Raw      │    │ Canonical│    │ Schema + │    │ Immutable│    │ Hash +   │    │ Framework│
│ evidence │    │ OSCAL    │    │ Control  │    │ WORM     │    │ Chain    │    │ -specific│
│ from     │    │ format   │    │ mapping  │    │ storage  │    │ of       │    │ views    │
│ multiple │    │          │    │ check    │    │          │    │ custody  │    │          │
│ sources  │    │          │    │          │    │          │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 8.2 Evidence Collection Pipeline

#### Stage 1: Discovery & Scheduling

- **Control inventory** loaded from the unified control set definition
- **Collection schedule** generated per control based on `collection_schedule` field
- **Collector agents** assigned to controls based on resource scope and evidence type

#### Stage 2: Collection

Evidence is collected through five channels:

| Channel | Mechanism | Evidence Types |
|---------|-----------|---------------|
| **API queries** | Cloud provider APIs (AWS Config, Azure Policy, GCP SCC) | Configuration state, access policies |
| **Agent probes** | Lightweight agents on target systems | Runtime state, process listings |
| **File ingestion** | Configuration files, policy documents, reports | Artifacts, attestations |
| **Log streaming** | SIEM integration, cloud trail logs | Audit logs, event trails |
| **Manual upload** | Human-provided evidence with attestation | Interviews, sign-offs |

#### Stage 3: Normalization

Raw evidence is transformed into the OSCAL-based canonical format:

1. **Parse** — Extract structured data from raw format
2. **Map** — Associate with unified control identifiers
3. **Enrich** — Add metadata (environment, resource scope, time window)
4. **Hash** — Compute SHA-256 of canonical content
5. **Timestamp** — Apply trusted timestamp (RFC 3161)

#### Stage 4: Validation

Before entering the evidence store, each item passes:

1. **Schema validation** — OSCAL 1.1.0 JSON Schema conformance
2. **Completeness check** — All required fields present
3. **Control mapping validation** — Control ID exists in unified control set
4. **Hash verification** — Content integrity confirmed
5. **Duplicate detection** — No identical evidence already stored

### 8.3 Evidence Verification Levels

| Level | Name | Description | Use Case |
|-------|------|-------------|----------|
| **L0** | Unverified | Collected but not yet validated | Initial ingestion |
| **L1** | Schema-valid | Passes OSCAL schema validation | Automated checks |
| **L2** | Integrity-verified | Hash matches, chain of custody intact | Standard audit evidence |
| **L3** | Cross-validated | Corroborated by independent evidence source | High-stakes decisions |
| **L4** | Attested | Signed by authorized human reviewer | Regulatory submissions |

### 8.4 Evidence-to-Framework Mapping

Each evidence artifact is tagged with the frameworks it can satisfy:

```json
{
  "evidence-id": "uuid-v4",
  "control-id": "UC-4.5",
  "type": "test_report",
  "content": { ... },
  "framework-applicability": {
    "ISO_42001": {
      "requirements": ["A.6.2.4"],
      "satisfaction_method": "direct",
      "verification_level_required": "L2"
    },
    "NIST_AI_RMF": {
      "requirements": ["MEASURE 2.1–2.13"],
      "satisfaction_method": "direct",
      "verification_level_required": "L2"
    },
    "EU_AI_ACT": {
      "requirements": ["Art. 15", "Art. 43"],
      "satisfaction_method": "direct",
      "verification_level_required": "L3"
    },
    "HIPAA": {
      "requirements": ["§164.308(a)(1)(ii)(D)"],
      "satisfaction_method": "indirect",
      "verification_level_required": "L2"
    },
    "PCI_DSS": {
      "requirements": ["11.3"],
      "satisfaction_method": "indirect",
      "verification_level_required": "L3"
    }
  }
}
```

### 8.5 Framework View Generation

When an auditor requests evidence for a specific framework, GRC_Claw generates a **framework view**:

1. **Filter** — Select all controls with spokes to the target framework
2. **Aggregate** — Collect all evidence artifacts mapped to those controls
3. **Render** — Format evidence in the framework's expected structure
4. **Sign** — Digitally sign the framework view with timestamp
5. **Package** — Bundle into a self-contained evidence package

```
Framework View: ISO/IEC 42001:2023
├── Assessment Plan (OSCAL)
├── Control Implementation Summary
│   ├── A.2 Policies (8 controls, 8 satisfied)
│   ├── A.3 Internal Organization (3 controls, 3 satisfied)
│   ├── A.4 Resources (5 controls, 5 satisfied)
│   ├── A.5 Impact Assessment (4 controls, 4 satisfied)
│   ├── A.6 Lifecycle (8 controls, 8 satisfied)
│   ├── A.7 Data (6 controls, 6 satisfied)
│   ├── A.8 Information (4 controls, 4 satisfied)
│   ├── A.9 Responsible Use (3 controls, 3 satisfied)
│   └── A.10 Third-Party (3 controls, 3 satisfied)
├── Evidence Artifacts (156 items)
├── Gap Analysis (0 gaps)
└── Compliance Posture: 100% SATISFIED
```

### 8.6 Continuous Evidence Maintenance

Evidence is not static. GRC_Claw maintains evidence currency through:

| Activity | Frequency | Scope | Action |
|----------|-----------|-------|--------|
| Hash re-verification | Daily | All stored evidence | Recompute and compare hashes |
| Chain-of-custody check | Weekly | All custody events | Verify chain integrity |
| Cross-validation | Monthly | Sample of evidence | Compare against live system state |
| Full package regeneration | Quarterly | All frameworks | Regenerate and compare packages |
| Evidence expiration review | Per retention policy | All evidence | Flag expired evidence for refresh |
| Control re-verification | Per control schedule | All active controls | Re-run verification tests |

### 8.7 Evidence Expiration and Renewal

Evidence has a defined shelf life based on the control's `collection_schedule` and the framework's requirements:

| Evidence Type | Default Expiration | Renewal Trigger |
|---------------|-------------------|-----------------|
| Configuration state | 30 days | Change detection |
| Access reviews | 90 days | Scheduled review |
| Vulnerability scans | 90 days | New scan completed |
| Penetration test results | 12 months | Annual test |
| Policy documents | 12 months | Policy review cycle |
| Risk assessment reports | 12 months | Annual assessment |
| Training records | 12 months | Annual training cycle |
| Audit logs | 7 years | Retention policy |
| Incident reports | 7 years | Retention policy |

When evidence expires:
1. The control's satisfaction status is downgraded to **PARTIALLY_SATISFIED**
2. A renewal task is created and assigned to the control owner
3. The framework view is updated to reflect the gap
4. If evidence is not renewed within 30 days, the control is marked **NOT_SATISFIED**

---

## 9. Implementation Architecture

### 9.1 Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     GRC_Claw Compliance Mapping Engine                    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Control Catalog Layer                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │  │
│  │  │ Unified      │  │ Framework    │  │ Spoke        │          │  │
│  │  │ Control      │  │ Registry     │  │ Registry     │          │  │
│  │  │ Definitions  │  │ (6 frameworks)│  │ (mappings)   │          │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Satisfaction Engine                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │  │
│  │  │ Satisfaction │  │ Gap          │  │ Compliance   │          │  │
│  │  │ Evaluator    │  │ Analyzer     │  │ Posture      │          │  │
│  │  │              │  │              │  │ Calculator   │          │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Evidence Orchestrator                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │  │
│  │  │ Collector    │  │ Normalizer   │  │ Validator    │          │  │
│  │  │ Agents       │  │ (OSCAL)      │  │ (Schema)     │          │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │  │
│  │  │ Evidence     │  │ Framework    │  │ Package      │          │  │
│  │  │ Store        │  │ Renderer     │  │ Generator    │          │  │
│  │  │ (Immutable)  │  │              │  │              │          │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Integration Layer                               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │  │
│  │  │ Cloud    │ │ SIEM     │ │ IAM      │ │ Ticketing│          │  │
│  │  │ APIs     │ │          │ │          │ │          │          │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Data Model

The core data model consists of five entities:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Control    │────▶│    Spoke     │◀────│   Framework  │
│              │ 1:N │              │ N:1 │              │
│ - id         │     │ - control_id │     │ - id         │
│ - title      │     │ - framework  │     │ - name       │
│ - category   │     │ - requirement│     │ - version    │
│ - risk_tier  │     │ - method     │     │ - type       │
│ - evidence   │     │ - notes      │     │              │
│   _reqs      │     │              │     │              │
└──────┬───────┘     └──────────────┘     └──────────────┘
       │
       │ 1:N
       ▼
┌──────────────┐     ┌──────────────┐
│   Evidence   │────▶│   Custody    │
│              │ 1:N │   Event      │
│ - id         │     │              │
│ - control_id │     │ - evidence_id│
│ - type       │     │ - action     │
│ - content    │     │ - actor      │
│ - hash       │     │ - timestamp  │
│ - frameworks │     │ - hash       │
│   _applic.   │     │ - signature  │
│ - expires_at │     │              │
└──────────────┘     └──────────────┘
```

### 9.3 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/controls` | GET | List all unified controls |
| `/api/v1/controls/{id}` | GET | Get control definition with spokes |
| `/api/v1/controls/{id}/evidence` | GET | Get evidence for a control |
| `/api/v1/frameworks` | GET | List all supported frameworks |
| `/api/v1/frameworks/{id}/satisfaction` | GET | Get satisfaction matrix for a framework |
| `/api/v1/frameworks/{id}/view` | GET | Generate framework view |
| `/api/v1/frameworks/{id}/export` | GET | Export evidence package for a framework |
| `/api/v1/compliance/posture` | GET | Get aggregate compliance posture |
| `/api/v1/compliance/gaps` | GET | Get gap analysis across all frameworks |
| `/api/v1/evidence/collect` | POST | Trigger evidence collection for a control |
| `/api/v1/evidence/verify` | POST | Verify evidence integrity |
| `/api/v1/evidence/refresh` | POST | Refresh expired evidence |

---

## 10. Metrics & KPIs

### 10.1 Compliance Mapping KPIs

| KPI | Target | Measurement | Frequency |
|-----|--------|-------------|-----------|
| Framework control coverage | 100% | Mapped requirements / Total requirements per framework | Real-time |
| Multi-framework satisfaction rate | ≥ 95% | Requirements with SATISFIED status / Total applicable requirements | Real-time |
| Evidence currency rate | ≥ 90% | Current evidence / Total evidence (not expired) | Daily |
| Evidence collection automation rate | ≥ 80% | Automatically collected evidence / Total evidence | Weekly |
| Framework view generation time | < 15 minutes | Time from request to package delivery | Per request |
| Cross-framework evidence reuse rate | ≥ 60% | Evidence satisfying multiple frameworks / Total evidence | Monthly |
| Gap identification time | < 1 hour | Time from new framework version to gap analysis | Per framework update |
| Audit package completeness | 100% | Required evidence present / Total required evidence | Per package |

### 10.2 Satisfaction Score by Framework

The compliance posture is computed as a weighted satisfaction score:

```
Satisfaction Score = Σ (Requirement Weight × Satisfaction Status) / Σ (Requirement Weight)

Where:
  SATISFIED = 1.0
  PARTIALLY_SATISED = 0.5
  NOT_SATISFIED = 0.0
  NOT_APPLICABLE = excluded from calculation
```

| Framework | Weight | Target Score |
|-----------|--------|-------------|
| ISO/IEC 42001 | 20% | ≥ 95% |
| NIST AI RMF | 20% | ≥ 95% |
| EU AI Act | 25% | ≥ 90% |
| HIPAA | 15% | ≥ 95% |
| PCI DSS | 10% | ≥ 95% |
| GDPR | 10% | ≥ 95% |

**Overall Compliance Posture = Σ (Framework Weight × Framework Score)**

---

## 11. Appendices

### Appendix A: Unified Control Set — Complete Catalog

*[Referenced in Section 4.2 — 68 controls across 12 categories. Full definitions in GRC-CLW-001 Unified Crosswalk.]*

### Appendix B: Framework Source References

| Framework | Source |
|-----------|--------|
| ISO/IEC 42001:2023 | https://www.iso.org/standard/42001 |
| NIST AI RMF 1.0 | https://www.nist.gov/itl/ai-risk-management-framework |
| EU AI Act (Reg. 2024/1689) | https://eur-lex.europa.eu/eli/reg/2024/1689 |
| HIPAA Security Rule | 45 CFR §164.308–312 |
| PCI DSS v4.0 | https://www.pcisecuritystandards.org/document_library |
| GDPR (Reg. 2016/679) | https://eur-lex.europa.eu/eli/reg/2016/679 |
| OSCAL 1.1.0 | https://pages.nist.gov/OSCAL |

### Appendix C: Evidence Package Structure

```
grc-evidence-package/
├── manifest.json              # Package metadata and index
├── evidence/
│   ├── UC-1.1/
│   │   ├── evidence-001.json
│   │   ├── evidence-002.json
│   │   └── attachments/
│   ├── UC-4.5/
│   │   └── ...
│   └── ...
├── oscal/
│   ├── assessment-plan.json
│   ├── assessment-results.json
│   └── catalog.json
├── framework-views/
│   ├── iso-42001-view.json
│   ├── nist-ai-rmf-view.json
│   ├── eu-ai-act-view.json
│   ├── hipaa-view.json
│   ├── pci-dss-view.json
│   └── gdpr-view.json
├── chain-of-custody/
│   ├── custody-log.jsonl
│   └── custody-signatures/
├── signatures/
│   ├── package-signature.json
│   └── timestamp-token.tsr
└── README.md
```

### Appendix D: Glossary

| Term | Definition |
|------|------------|
| **AIMS** | AI Management System (ISO 42001) |
| **Crosswalk** | Complete set of mappings between unified controls and framework requirements |
| **Framework View** | Filtered projection of evidence formatted for a specific framework's audit requirements |
| **Gap Delta** | Set of framework requirements not yet satisfied by any implemented unified control |
| **Hub-and-Spoke** | Model where one control (hub) maps to multiple framework requirements (spokes) |
| **OSCAL** | Open Security Controls Assessment Language (NIST) |
| **Satisfaction Matrix** | Data structure proving that a set of controls satisfies all requirements of a framework |
| **Unified Control** | Single, atomic governance control that maps to one or more framework requirements |
| **WORM** | Write Once Read Many storage |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Architecture Team | Initial specification |

---

*This specification is a living document. It shall be reviewed and updated:*
- *After any significant compliance incident*
- *When new regulations or framework versions take effect*
- *When new AI use cases are introduced*
- *At minimum, annually*

---

*End of Specification*
