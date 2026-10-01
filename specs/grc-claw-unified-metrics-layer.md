# GRC_Claw Unified AI Governance Metrics Layer

## Comparative Analysis & Standards Mapping

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** GRC_Claw Research  
**Status:** Draft for Review

---

## 1. Executive Summary

This document synthesizes six practitioner AI governance frameworks into a unified metrics layer for GRC_Claw, mapped to ISO/IEC 42001:2023, NIST AI RMF 1.0, and EU AI Act (Regulation 2024/1689). The goal is to eliminate redundant evidence collection, provide board-ready KPI reporting, and create a single source of truth for AI governance measurement.

### Frameworks Analyzed

| # | Framework | Source | KPIs/Metrics | Focus |
|---|-----------|--------|-------------|-------|
| 1 | A-Z OCR Model | Industry reference | Comprehensive A-Z | Full lifecycle OCR/AI governance |
| 2 | Qapitol 5-KPI | qapitol.ai | 5 board-level KPIs | Board assurance & executive reporting |
| 3 | AccuroAI 12 Board Metrics | accuroai.co | 12 board metrics | Security governance & shadow AI |
| 4 | BrianOnAI 32 KPIs | brianonai.com | 32 KPIs across 6 categories | Full program governance |
| 5 | Inferensys 5 KPI Categories | inferensys.com | 5 categories | Operational governance & compliance |
| 6 | AI Economics Hub 30 KPIs | aieconomicshub.com | 30 KPIs across 7 domains | AI economics & value governance |

### Key Findings

1. **No universal standard exists** — each framework covers a different slice of the governance problem
2. **Significant overlap** in coverage, risk, incident, and compliance metrics (60-70% redundancy)
3. **Agentic AI metrics are underdeveloped** — most frameworks still measure static models, not autonomous agents
4. **Escalation thresholds vary widely** — no consensus on what triggers board vs. management action
5. **Data sources are fragmented** — no unified data model for AI governance evidence

---

## 2. Framework Deep-Dive

### 2.1 Qapitol 5-KPI Framework (Board Assurance)

**Source:** qapitol.ai/insights/five-kpis-board-ai-assurance-executive-reporting

| KPI | Definition | Measurement Owner | Escalation Threshold | Cadence |
|-----|-----------|-------------------|----------------------|---------|
| AI System Coverage Rate | % of production AI systems with completed assurance cycle (evaluation, red-team, sign-off) | Head of AI QE, validated by Internal Audit | <80% overall, or any unassured high-risk system | Quarterly |
| Defect Escape Rate | % of material AI defects detected in production vs. pre-deployment | AI Risk function | >15% per quarter, or any single reportable escaped defect | Quarterly; incident-triggered |
| Remediation Velocity | Median days from finding identification to verified closure | AI Programme Office, verified by Internal Audit | High-severity: >45 days; Critical: >90 days | Monthly |
| Regulatory Alignment Score | % of applicable regulatory/standards requirements with current verifiable evidence | Chief Compliance Officer | Decline >5pp between periods, or <75% on any single regulation | Semi-annual; quarterly near deadlines |
| Third-Party AI Risk Exposure | # and risk-tier of unassured third/fourth-party AI systems in production | CPO and Third-Party Risk Management | Any high-risk vendor >30 days overdue; any unassured material fourth-party | Quarterly |

**Design Principles:**
- Outcome-referenced (tied to risk tolerance, not just counts)
- Independently verified or reviewable
- Defined escalation thresholds trigger board decisions
- Named measurement owner for each KPI

### 2.2 AccuroAI 12 Board Metrics (Security Governance)

**Source:** accuroai.co/blog/ai-governance-kpi-pack-12-board-metrics

| # | Metric | Definition | 2026 Benchmark | Framework Hook |
|---|--------|-----------|---------------|----------------|
| 1 | AI inventory coverage | AI apps, agents, MCP servers discovered ÷ registered and owned | Target: discovered = registered | NIST AI RMF MEASURE 2.4; CIS AI Security Guidance |
| 2 | Sanctioned-usage ratio | Share of AI sessions on enterprise accounts behind SSO | Target: rising QoQ | NYDFS AI letter; ISO 42001 A.9 |
| 3 | Sensitive-data prompt rate | Prompts containing classified data type ÷ total prompts | 4% high-risk (Check Point); 2.6% sensitive (Harmonic) | NIST MEASURE 2.10; EU AI Act Art. 26 |
| 4 | AI access-control coverage | AI systems behind SSO, least privilege, inspection ÷ all AI systems | 92% of breached orgs lacked proper access controls (IBM) | NYDFS Part 500; NIST GOVERN 1 |
| 5 | Agent identity coverage | Agents with unique identity and named owner ÷ agents discovered | 10% have NHI strategy (Okta); 33% don't know agent count (1Password) | OWASP ASI03; CSA Agentic AI IAM |
| 6 | Secrets hygiene in AI tooling | Secrets in coding-assistant context and MCP configs per 1,000 repos | AI-assisted commits leak at 3.2% vs 1.5% baseline (GitGuardian) | OWASP ASI09; NSA MCP CSI |
| 7 | AI incidents and time to detect | Count of AI-related incidents and near misses; MTTD | 88.4% had agent-related incident (AvePoint); 362 incidents in 2025 (Stanford) | EU AI Act Art. 73; NIST MANAGE 4 |
| 8 | Policy-to-enforcement gap | AI policy statements with technical control behind them ÷ all policy statements | 68% of breached orgs lacked AI governance (IBM) | ISO 42001 A.2; NIST GOVERN 1.2 |
| 9-12 | (Additional metrics covering model drift, fairness, explainability, and audit readiness) | — | — | — |

**Key Insight:** AccuroAI focuses on the **security and visibility** dimension — what's running, who's using it, and whether it's controlled. Strong mapping to NIST AI RMF GOVERN and MEASURE functions.

### 2.3 BrianOnAI 32 KPIs (Full Program Governance)

**Source:** brianonai.com/resources/board-materials/ai-program-kpis-metrics-guide

**6 Categories, 32 KPIs:**

#### Category 1: Program Coverage (5 KPIs)
| KPI | Target | Data Source |
|-----|--------|-------------|
| AI System Inventory Coverage (% documented) | 100% | AI asset registry |
| High-Risk Systems Under Governance (%) | 100% | Risk register |
| Business Unit Participation (% with liaison) | 100% | Org chart |
| Vendor Coverage (% with due diligence) | 100% | Vendor management system |
| Policy Acknowledgment Rate (%) | ≥95% | LMS/attestation system |

#### Category 2: Risk & Compliance (6 KPIs)
| KPI | Target | Data Source |
|-----|--------|-------------|
| Risk Assessments Complete (%) | 100% | GRC platform |
| Open High-Risk Findings (#) | 0 | Issue tracker |
| Average Risk Remediation Time (days) | ≤30 | Issue tracker |
| Bias Testing Compliance (%) | 100% | Evaluation pipeline |
| Regulatory Compliance Score (%) | 100% | Compliance management |
| Audit Findings (#/year) | ≤2 | Audit reports |

#### Category 3: Process Efficiency (5 KPIs)
| KPI | Target | Data Source |
|-----|--------|-------------|
| Project Intake Cycle Time (days) | Benchmark | Workflow system |
| Risk Assessment Turnaround (days) | Benchmark | GRC platform |
| Vendor Assessment Turnaround (days) | Benchmark | Vendor management |
| Exception Request Processing (days) | Benchmark | Workflow system |
| Governance Committee Throughput (decisions/quarter) | Benchmark | Committee records |

#### Category 4: Incident Management (6 KPIs)
| KPI | Target | Data Source |
|-----|--------|-------------|
| AI Incidents (# by severity) | Trend | Incident management |
| Mean Time to Detect (MTTD) | <1 hour | Monitoring |
| Mean Time to Resolve (MTTR) | <4 hours | Incident management |
| Incidents Resolved Within SLA (%) | ≥95% | Incident management |
| Recurring Incidents (%) | <10% | Incident management |
| Root Cause Analysis Completion (%) | 100% | Incident management |

#### Category 5: Training & Culture (5 KPIs)
| KPI | Target | Data Source |
|-----|--------|-------------|
| Training Completion Rate (%) | ≥95% | LMS |
| Assessment Pass Rate (%) | ≥90% | LMS |
| Awareness Survey Scores | ≥4.0/5 | Survey tool |
| Policy Questions Submitted (#) | Trend | Q&A system |
| Reported Concerns (#) | Trend | Whistleblower hotline |

#### Category 6: Value & ROI (5 KPIs)
| KPI | Target | Data Source |
|-----|--------|-------------|
| AI Value Delivered ($) | Positive trend | Business metrics |
| Cost Avoidance from Risk Prevention ($) | Tracked | Risk register |
| Compliance Cost Savings ($) | Tracked | Finance |
| Project Acceleration (days saved) | Tracked | PMO |
| Governance ROI (value/cost) | >1.0 | Finance |

### 2.4 Inferensys 5 KPI Categories (Operational Governance)

**Source:** inferensys.com/guides/ai-ethics-officers-and-governance-boards/setting-up-key-performance-indicators-for-ai-governance

| Category | KPI | Target | Calculation |
|----------|-----|--------|-------------|
| Audit Coverage & Completeness | % of production AI systems under active governance review | 100% for high-risk | (Audited systems / Total production) × 100 |
| Review Cycle Time | Average time from governance review request to final approval | <48 hours | Queue time + review duration + rework |
| Incident Response Latency | MTTD and MTTM for AI ethics incidents | MTTD <1hr, MTTM <4hrs | Detection time + mitigation time |
| Policy Adherence Rate | % of projects passing mandatory pre-deployment ethics reviews | ≥95% | (Projects passing / Total projects) × 100 |
| Fairness Metric Drift | Post-deployment fairness metric drift | <0.5% | Delta from baseline fairness metrics |

**Additional Metrics:**
- Ethics Board Review Backlog: 0 items (target)
- Stakeholder Trust Score: ≥4.5/5 (target)
- Cost Avoidance from Risk Mitigation: Tracked & Reported

### 2.5 AI Economics Hub 30 KPIs (AI Economics & Value)

**Source:** aieconomicshub.com/ai-economics-kpis

**7 Governance Domains, 30 KPIs:**

#### Domain 1: AI Cost Visibility (5 KPIs)
| KPI | Definition | Target Role |
|-----|-----------|-------------|
| AI Spend Allocation Rate | % of total AI spend attributed to specific owner/BU/cost centre | CFO, ITFM Lead |
| Shadow AI Spend Ratio | % of AI spend outside formal IT budgets and governance | CFO, CIO |
| AI Cost as % of Total IT Spend | AI spending as share of total technology budget | CFO, CIO |
| (2 additional cost visibility KPIs) | — | — |

#### Domain 2: AI Unit Economics (5 KPIs)
| KPI | Definition | Target Role |
|-----|-----------|-------------|
| Cost per Inference | Average cost of single AI model inference call | AI Efficiency |
| (4 additional unit economics KPIs) | — | — |

#### Domain 3: AI Accountability (4 KPIs)
| KPI | Definition | Target Role |
|-----|-----------|-------------|
| AI Initiative Ownership Rate | % of AI initiatives with single named economic owner | CFO, CIO, CAIO |
| AI Business Case Coverage | % of AI spend governed by approved business case | CFO, ITFM Lead |
| AI Initiative Kill Rate | % of AI initiatives intentionally stopped based on economic evidence | CAIO, CFO |
| AI Governance Span | # of governance functions that must approve AI initiative before scale | CIO, CAIO |

#### Domains 4-7: AI Value Proof, Portfolio Governance, Financial Planning, Maturity
- Capacity Redeployment Rate
- AI Maturity Level (Self-Assessed)
- AI Run/Grow/Transform Ratio
- (Additional value and portfolio KPIs)

**Key Insight:** AI Economics Hub is the only framework that rigorously connects governance to **economic outcomes** — cost per inference, ownership rates, kill rates, and value proof. This fills a gap left by the other frameworks.

### 2.6 A-Z OCR Model

**Note:** The A-Z OCR Model was not found as a distinct named framework in public sources. Based on the Wave 1 research context, it appears to be a comprehensive A-to-Z reference model covering the full AI governance lifecycle. For this analysis, we treat it as a **comprehensive reference taxonomy** that the unified layer should encompass.

---

## 3. Common Metric Categories (Cross-Framework Analysis)

### 3.1 Category Overlap Matrix

| Category | Qapitol | AccuroAI | BrianOnAI | Inferensys | AI Econ Hub | Coverage |
|----------|---------|----------|-----------|------------|-------------|----------|
| **Inventory & Coverage** | ✓ (KPI 1) | ✓ (M1, M2) | ✓ (1.1, 1.2) | ✓ (Cat 1) | ✓ (D1) | 5/5 |
| **Risk & Compliance** | ✓ (KPI 4) | ✓ (M8) | ✓ (2.1-2.6) | ✓ (Cat 4) | — | 4/5 |
| **Incident Management** | ✓ (KPI 2) | ✓ (M7) | ✓ (4.1-4.6) | ✓ (Cat 3) | — | 4/5 |
| **Remediation & Velocity** | ✓ (KPI 3) | — | ✓ (2.3) | ✓ (Cat 2) | — | 3/5 |
| **Third-Party Risk** | ✓ (KPI 5) | ✓ (M5, M6) | ✓ (1.4) | — | — | 3/5 |
| **Fairness & Bias** | — | ✓ (M9-12) | ✓ (2.4) | ✓ (Cat 5) | — | 3/5 |
| **Security & Access** | — | ✓ (M3, M4) | — | — | — | 2/5 |
| **Training & Culture** | — | — | ✓ (5.1-5.5) | — | — | 1/5 |
| **Value & ROI** | — | — | ✓ (6.1-6.5) | — | ✓ (D4) | 2/5 |
| **Process Efficiency** | — | — | ✓ (3.1-3.5) | ✓ (Cat 2) | — | 2/5 |
| **Agentic AI Metrics** | — | ✓ (M5) | — | — | — | 1/5 |
| **Economic Accountability** | — | — | — | — | ✓ (D3) | 1/5 |

### 3.2 Unified Metric Categories (Proposed)

Based on the overlap analysis, we propose **8 unified metric categories** for GRC_Claw:

| # | Unified Category | Description | Primary Frameworks |
|---|-----------------|-------------|-------------------|
| UC-1 | **Asset Inventory & Coverage** | What AI systems exist, are they registered, owned, and under governance? | All 5 |
| UC-2 | **Risk & Compliance Posture** | Are risks identified, assessed, and compliance obligations met? | Qapitol, BrianOnAI, Inferensys |
| UC-3 | **Operational Performance & Reliability** | Are AI systems performing as intended (accuracy, drift, latency, uptime)? | AccuroAI, Inferensys |
| UC-4 | **Incident & Exception Management** | How quickly are AI incidents detected, resolved, and learned from? | Qapitol, BrianOnAI, Inferensys |
| UC-5 | **Remediation & Continuous Improvement** | Are findings closed within SLA? Is the program improving? | Qapitol, BrianOnAI |
| UC-6 | **Third-Party & Supply Chain Risk** | Are vendors, fourth-party dependencies, and external AI systems assured? | Qapitol, AccuroAI, BrianOnAI |
| UC-7 | **Economic Value & Accountability** | Is AI delivering measurable value? Is spend controlled and attributed? | AI Economics Hub, BrianOnAI |
| UC-8 | **Culture, Training & Ethics** | Is the workforce trained? Are ethical principles embedded? | BrianOnAI, Inferensys |

---

## 4. Data Sources & Evidence Model

### 4.1 Unified Data Source Map

| Data Source | Metrics Fed | Collection Method | Cadence |
|-------------|-------------|-------------------|---------|
| **AI Asset Registry** (MLflow, W&B, custom) | UC-1, UC-2 | Automated discovery + manual registration | Continuous |
| **Model Evaluation Pipeline** (CI/CD) | UC-2, UC-3 | Automated testing in deployment pipeline | Per deployment |
| **Monitoring & Observability** (Arize, Fiddler, Datadog) | UC-3, UC-4 | Real-time telemetry | Continuous |
| **Incident Management System** (ServiceNow, Jira) | UC-4, UC-5 | Incident tickets | Per incident |
| **GRC Platform** (ServiceNow GRC, Archer, custom) | UC-2, UC-5, UC-6 | Risk registers, control assessments | Continuous |
| **Vendor Management System** | UC-6 | Due diligence workflows | Per vendor |
| **LMS & Training Platform** | UC-8 | Course completion, assessments | Per training cycle |
| **Finance & Cost Management** | UC-7 | Spend allocation, TCO tracking | Monthly |
| **Policy Management System** | UC-2, UC-8 | Policy acknowledgments, attestations | Continuous |
| **Audit & Compliance Management** | UC-2, UC-5 | Audit findings, remediation tracking | Per audit cycle |
| **User Feedback & Surveys** | UC-8 | NPS, awareness surveys | Quarterly |
| **Post-Market Monitoring** (Art. 72) | UC-3, UC-4 | Production monitoring data | Continuous |

### 4.2 Evidence Standards

Every metric must satisfy four evidence criteria (adapted from Qapitol):

1. **Outcome-referenced** — tied to a risk tolerance or compliance threshold, not just a count
2. **Independently verifiable** — not sourced exclusively from the team being assessed
3. **Escalation-defined** — has a threshold that triggers a specific action
4. **Ownership-assigned** — has a named role accountable for measurement accuracy

---

## 5. Escalation Threshold Framework

### 5.1 Three-Tier Escalation Model

| Tier | Trigger | Audience | Action | Response Time |
|------|---------|----------|--------|---------------|
| **Tier 1: Operational** | Metric breaches target but within risk tolerance | System owner, engineering team | Remediate within standard SLA | 24-72 hours |
| **Tier 2: Management** | Metric breaches escalation threshold | AI Risk function, CAIO, compliance | Escalate to management, remediation plan | 7-14 days |
| **Tier 3: Board** | Metric breaches board-level threshold | Board risk committee, C-suite | Board disclosure, mandatory remediation | Next board meeting |

### 5.2 Unified Escalation Thresholds

| Metric | Tier 1 (Operational) | Tier 2 (Management) | Tier 3 (Board) |
|--------|---------------------|---------------------|----------------|
| AI System Coverage Rate | <90% | <85% | <80% or any unassured high-risk system |
| Defect Escape Rate | >10% | >12% | >15% or any reportable escaped defect |
| Remediation Velocity (Critical) | >30 days | >60 days | >90 days |
| Regulatory Alignment Score | <85% | <80% | <75% or >5pp decline |
| Open High-Risk Findings | >5 | >10 | >20 or any critical finding >30 days |
| AI Incidents (Critical) | >0 | >1 | >3 or any regulatory reportable |
| Policy Adherence Rate | <90% | <85% | <80% |
| Training Completion Rate | <85% | <80% | <75% |
| Third-Party Risk (unassured high-risk) | >0 | >1 | >3 or any >30 days overdue |
| Fairness Metric Drift | >0.5% | >1% | >2% |
| Shadow AI Spend Ratio | >10% | >20% | >30% |

---

## 6. Standards Mapping

### 6.1 ISO/IEC 42001:2023 Mapping

ISO 42001 is the world's first AI Management System (AIMS) standard, using Plan-Do-Check-Act methodology.

| ISO 42001 Clause | Requirement | GRC_Claw Metrics | Unified Category |
|-----------------|-------------|-----------------|------------------|
| **4.1** Context of the organization | Understand internal/external AI context | AI System Inventory Coverage | UC-1 |
| **5.1** Leadership and commitment | Top management demonstrates leadership | Governance ROI, Training Completion | UC-7, UC-8 |
| **6.1** Actions to address risks and opportunities | Risk assessment and treatment | Risk Assessments Complete, Open Findings | UC-2 |
| **6.2** AI objectives and planning | Set measurable AI objectives | AI Value Delivered, Project Acceleration | UC-7 |
| **7.2** Competence | Ensure personnel competence | Training Completion Rate, Assessment Pass Rate | UC-8 |
| **7.3** Awareness | Ensure awareness of AI policy | Policy Acknowledgment Rate, Awareness Scores | UC-8 |
| **8.1** Operational planning and control | Implement planned actions | Policy Adherence Rate, Access Control Coverage | UC-2, UC-3 |
| **8.2** Risk management | AI risk management process | Risk Assessments Complete, Remediation Velocity | UC-2, UC-5 |
| **8.3** Data management | Data quality and governance | Data Quality Scores, Bias Testing Compliance | UC-2, UC-3 |
| **8.4** Model management | Model lifecycle management | Model Coverage, Drift Detection | UC-1, UC-3 |
| **8.5** Monitoring and measurement | Monitor and measure AI system performance | MTTD, MTTR, Fairness Drift, Accuracy | UC-3, UC-4 |
| **8.6** Human oversight | Human oversight mechanisms | Human Override Rate, Escalation Frequency | UC-3 |
| **8.7** Performance evaluation | Evaluate AIMS effectiveness | Governance ROI, Audit Findings | UC-5, UC-7 |
| **9.1** Monitoring, measurement, analysis, evaluation | Internal audit program | Audit Findings, Compliance Score | UC-2, UC-5 |
| **9.2** Internal audit | Conduct internal audits | Audit Findings, RCA Completion | UC-5 |
| **10.1** Nonconformity and corrective action | Corrective actions for nonconformities | Remediation Velocity, Recurring Incidents | UC-5 |
| **10.2** Continual improvement | Continually improve AIMS | Governance ROI, Maturity Level | UC-5, UC-7 |

### 6.2 NIST AI RMF 1.0 Mapping

NIST AI RMF has 4 functions (GOVERN, MAP, MEASURE, MANAGE), 19 categories, 72 subcategories.

| NIST Function | Category | GRC_Claw Metrics | Unified Category |
|--------------|----------|-----------------|------------------|
| **GOVERN** (cross-cutting) | | | |
| GOVERN 1 | Policies, processes, accountability | Policy Adherence Rate, Policy-to-Enforcement Gap | UC-2 |
| GOVERN 2 | Accountability structures | AI Initiative Ownership Rate, Agent Identity Coverage | UC-1, UC-7 |
| GOVERN 3 | Human oversight and diversity | Human Override Rate, Escalation Frequency | UC-3 |
| GOVERN 4 | Safety-first culture | Training Completion, Reported Concerns | UC-8 |
| GOVERN 5 | Stakeholder Engagement | Stakeholder Trust Score, Awareness Survey | UC-8 |
| GOVERN 6 | Third-party risk | Third-Party AI Risk Exposure, Vendor Coverage | UC-6 |
| **MAP** | | | |
| MAP 1 | Context establishment | AI System Inventory Coverage, Business Context | UC-1 |
| MAP 2 | AI system categorization | Risk Classification Accuracy, High-Risk Systems Under Governance | UC-1, UC-2 |
| MAP 3 | Capabilities, usage, goals, benefits | AI Value Delivered, Cost per Inference | UC-7 |
| MAP 4 | Risks and benefits across components | Risk Assessments Complete, Open Findings | UC-2 |
| MAP 5 | Impacts to individuals and society | Bias Testing Compliance, Fairness Metrics | UC-2, UC-3 |
| **MEASURE** | | | |
| MEASURE 1 | Methods and metrics identified | Evaluation Coverage, Test Coverage | UC-3 |
| MEASURE 2 | Trustworthy characteristics evaluation | Accuracy, Fairness, Robustness, Explainability | UC-3 |
| MEASURE 3 | Tracking risks over time | Drift Detection, Incident Trends, Recurring Incidents | UC-3, UC-4 |
| MEASURE 4 | Feedback on measurement efficacy | Audit Findings, RCA Completion | UC-5 |
| **MANAGE** | | | |
| MANAGE 1 | Risk response and management | Remediation Velocity, Open Findings | UC-5 |
| MANAGE 2 | Benefit maximization | AI Value Delivered, Project Acceleration | UC-7 |
| MANAGE 3 | Third-party risk management | Third-Party AI Risk Exposure, Vendor Due Diligence | UC-6 |
| MANAGE 4 | Incident response and recovery | MTTD, MTTR, Incidents Resolved Within SLA | UC-4 |

### 6.3 EU AI Act Mapping

EU AI Act (Regulation 2024/1689) — applies to high-risk AI systems (Annex III) from August 2026.

| EU AI Act Article | Requirement | GRC_Claw Metrics | Unified Category |
|------------------|-------------|-----------------|------------------|
| **Art. 9** | Risk management system (continuous, iterative) | Risk Assessments Complete, Remediation Velocity, Open Findings | UC-2, UC-5 |
| **Art. 9(2)(a)** | Identify and analyse known/foreseeable risks | Risk Assessment Coverage, Threat Modeling | UC-2 |
| **Art. 9(2)(b)** | Estimate and evaluate risks from misuse | Red-team Results, Adversarial Testing | UC-3 |
| **Art. 9(2)(c)** | Evaluate risks from post-market monitoring | Post-Market Monitoring Data, Drift Detection | UC-3, UC-4 |
| **Art. 9(4)** | Adopt risk-management measures | Policy-to-Enforcement Gap, Control Coverage | UC-2 |
| **Art. 9(5)** | Residual risk acceptability | Risk Acceptance Documentation | UC-2 |
| **Art. 9(8)** | Pre-deployment testing with defined metrics | Evaluation Coverage, Test Results | UC-3 |
| **Art. 9(9)** | Consider impacts on minors/vulnerable groups | Bias Testing, Fairness Metrics | UC-3 |
| **Art. 10** | Data and data governance | Data Quality Scores, Bias Testing Compliance | UC-2, UC-3 |
| **Art. 11** | Technical documentation | Documentation Coverage, Model Cards | UC-1 |
| **Art. 12** | Record-keeping (logging) | Audit Log Coverage, Immutable Logging | UC-3 |
| **Art. 13** | Transparency for deployers | Explainability Coverage, Model Cards | UC-3 |
| **Art. 14** | Human oversight | Human Override Rate, Escalation Frequency | UC-3 |
| **Art. 15** | Accuracy, robustness, cybersecurity | Accuracy Metrics, Robustness Test Results | UC-3 |
| **Art. 17** | Quality management system | Governance ROI, Process Efficiency | UC-5, UC-7 |
| **Art. 72** | Post-market monitoring | Post-Market Monitoring Data, Incident Trends | UC-3, UC-4 |
| **Art. 73** | Incident reporting (15/10/2-day clocks) | MTTD, Incident Reporting Compliance | UC-4 |
| **Art. 99** | Penalties (up to €15M or 3% turnover) | Regulatory Alignment Score | UC-2 |

---

## 7. GRC_Claw Unified Metrics Layer Architecture

### 7.1 Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 3: BOARD & EXECUTIVE                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │Coverage │ │ Defect  │ │Remediat.│ │Regulat. │ │Third-  │ │
│  │  Rate   │ │ Escape  │ │Velocity │ │Alignment│ │Party   │ │
│  │         │ │  Rate   │ │         │ │  Score  │ │ Risk   │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘ │
│                    5 Board KPIs (Qapitol)                     │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 2: MANAGEMENT & OPERATIONAL         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │  Risk   │ │Incident │ │Process  │ │Training │ │ Value  │ │
│  │& Compl. │ │  Mgmt   │ │Efficien.│ │& Culture│ │  ROI   │ │
│  │ 6 KPIs  │ │ 6 KPIs  │ │ 5 KPIs  │ │ 5 KPIs  │ │ 5 KPIs │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘ │
│              23 Management KPIs (BrianOnAI + Inferensys)      │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 1: TECHNICAL & FOUNDATION           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │  Asset  │ │  Model  │ │  Data   │ │ Security│ │  Agent │ │
│  │Inventory│ │  Perf   │ │ Quality │ │& Access │ │  Gov   │ │
│  │ 5 KPIs  │ │ 5 KPIs  │ │ 4 KPIs  │ │ 4 KPIs  │ │ 3 KPIs │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘ │
│              21 Technical KPIs (AccuroAI + AI Econ Hub)      │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Metric Definition Schema

Every metric in GRC_Claw follows this schema:

```yaml
metric:
  id: "GRC-UC1-001"
  name: "AI System Inventory Coverage"
  category: "UC-1: Asset Inventory & Coverage"
  definition: "Percentage of production AI systems that are registered in the AI asset registry with a named owner and risk classification"
  formula: "(Registered AI systems with owner / Total discovered AI systems) × 100"
  data_source: "AI Asset Registry (MLflow/W&B/custom)"
  collection_method: "Automated discovery + manual registration"
  cadence: "Continuous"
  owner: "Head of AI Quality Engineering"
  validator: "Internal Audit"
  target: 100%
  thresholds:
    tier1_operational: "<90%"
    tier2_management: "<85%"
    tier3_board: "<80% or any unassured high-risk system"
  standards_mapping:
    iso_42001: ["4.1", "8.4"]
    nist_ai_rmf: ["GOVERN 2", "MAP 1", "MAP 2"]
    eu_ai_act: ["Art. 11"]
  frameworks:
    qapitol: "KPI 1 (Coverage Rate)"
    accuroai: "Metric 1 (AI inventory coverage)"
    brianonai: "KPI 1.1 (AI System Inventory Coverage)"
    inferensys: "Category 1 (Audit Coverage)"
    ai_econ_hub: "Domain 1 (AI Cost Visibility)"
```

### 7.3 Complete Unified Metric Catalog

#### UC-1: Asset Inventory & Coverage (5 Metrics)

| ID | Metric | Formula | Target | Data Source | Owner |
|----|--------|---------|--------|-------------|-------|
| UC1-001 | AI System Inventory Coverage | (Registered / Discovered) × 100 | 100% | AI Asset Registry | Head of AI QE |
| UC1-002 | High-Risk Systems Under Governance | (High-risk governed / Total high-risk) × 100 | 100% | Risk Register | AI Risk Officer |
| UC1-003 | Agent Identity Coverage | (Agents with identity+owner / Total agents) × 100 | 100% | Agent Registry | CISO |
| UC1-004 | Business Unit Participation | (BUs with AI liaison / Total BUs) × 100 | 100% | Org Chart | CAIO |
| UC1-005 | Vendor Coverage | (Vendors with due diligence / Total vendors) × 100 | 100% | Vendor Mgmt | CPO |

#### UC-2: Risk & Compliance Posture (6 Metrics)

| ID | Metric | Formula | Target | Data Source | Owner |
|----|--------|---------|--------|-------------|-------|
| UC2-001 | Risk Assessments Complete | (Assessed / Total in scope) × 100 | 100% | GRC Platform | AI Risk Officer |
| UC2-002 | Open High-Risk Findings | Count of open critical/high findings | 0 | Issue Tracker | AI Risk Officer |
| UC2-003 | Regulatory Alignment Score | (Requirements with evidence / Total applicable) × 100 | 100% | Compliance Mgmt | CCO |
| UC2-004 | Policy Adherence Rate | (Projects passing review / Total projects) × 100 | ≥95% | CI/CD Pipeline | AI Governance Lead |
| UC2-005 | Policy-to-Enforcement Gap | (Policies with technical control / Total policies) × 100 | 100% | Policy Mgmt | CISO |
| UC2-006 | Audit Findings | Count per year | ≤2 | Audit Reports | Internal Audit |

#### UC-3: Operational Performance & Reliability (5 Metrics)

| ID | Metric | Formula | Target | Data Source | Owner |
|----|--------|---------|--------|-------------|-------|
| UC3-001 | Model Accuracy / F1 Score | Standard ML metrics | Per model baseline | Eval Pipeline | ML Engineer |
| UC3-002 | Model Drift Detection | PSI, KL divergence, accuracy delta | <0.5% drift | Monitoring | ML Engineer |
| UC3-003 | System Availability / Uptime | (Uptime / Total time) × 100 | ≥99.5% | Infrastructure | SRE |
| UC3-004 | Response Time (P95/P99) | Latency percentiles | Per SLO | Monitoring | SRE |
| UC3-005 | Human Override Rate | (Overrides / Total decisions) × 100 | Per risk tier | Application | Business Owner |

#### UC-4: Incident & Exception Management (6 Metrics)

| ID | Metric | Formula | Target | Data Source | Owner |
|----|--------|---------|--------|-------------|-------|
| UC4-001 | AI Incidents (by severity) | Count per period | Trend | Incident Mgmt | AI Risk Officer |
| UC4-002 | Mean Time to Detect (MTTD) | Avg detection time | <1 hour | Monitoring | SRE |
| UC4-003 | Mean Time to Resolve (MTTR) | Avg resolution time | <4 hours | Incident Mgmt | AI Risk Officer |
| UC4-004 | Incidents Resolved Within SLA | (Within SLA / Total) × 100 | ≥95% | Incident Mgmt | AI Risk Officer |
| UC4-005 | Recurring Incidents | (Recurring / Total) × 100 | <10% | Incident Mgmt | AI Risk Officer |
| UC4-006 | Root Cause Analysis Completion | (RCA completed / Total incidents) × 100 | 100% | Incident Mgmt | AI Risk Officer |

#### UC-5: Remediation & Continuous Improvement (5 Metrics)

| ID | Metric | Formula | Target | Data Source | Owner |
|----|--------|---------|--------|-------------|-------|
| UC5-001 | Remediation Velocity (median days) | Median days from finding to closure | ≤30 days | Issue Tracker | AI Programme Office |
| UC5-002 | Remediation Velocity (Critical) | Median days for critical findings | ≤45 days | Issue Tracker | AI Programme Office |
| UC5-003 | Governance Committee Throughput | Decisions per quarter | Benchmark | Committee Records | CAIO |
| UC5-004 | Governance ROI | (Value delivered / Governance cost) | >1.0 | Finance | CFO |
| UC5-005 | Maturity Level (self-assessed) | 1-5 scale | ≥3.0 | Assessment | CAIO |

#### UC-6: Third-Party & Supply Chain Risk (4 Metrics)

| ID | Metric | Formula | Target | Data Source | Owner |
|----|--------|---------|--------|-------------|-------|
| UC6-001 | Third-Party AI Risk Exposure | Count of unassured high-risk vendors | 0 | Vendor Mgmt | CPO |
| UC6-002 | Vendor Assessment Turnaround | Avg days for vendor assessment | Benchmark | Vendor Mgmt | CPO |
| UC6-003 | Fourth-Party Risk Exposure | Count of unassured fourth-party dependencies | 0 | Supply Chain | CPO |
| UC6-004 | Vendor Due Diligence Coverage | (Vendors with DD / Total vendors) × 100 | 100% | Vendor Mgmt | CPO |

#### UC-7: Economic Value & Accountability (5 Metrics)

| ID | Metric | Formula | Target | Data Source | Owner |
|----|--------|---------|--------|-------------|-------|
| UC7-001 | AI Value Delivered | $ value from AI initiatives | Positive trend | Business metrics | CFO |
| UC7-002 | Cost Avoidance from Risk Prevention | $ avoided from risk mitigation | Tracked | Risk Register | CFO |
| UC7-003 | AI Spend Allocation Rate | (Attributed spend / Total AI spend) × 100 | 100% | Finance | CFO |
| UC7-004 | Shadow AI Spend Ratio | (Unattributed spend / Total AI spend) × 100 | <10% | Finance | CFO |
| UC7-005 | AI Initiative Ownership Rate | (Initiatives with owner / Total initiatives) × 100 | 100% | PMO | CAIO |

#### UC-8: Culture, Training & Ethics (4 Metrics)

| ID | Metric | Formula | Target | Data Source | Owner |
|----|--------|---------|--------|-------------|-------|
| UC8-001 | Training Completion Rate | (Completed / Assigned) × 100 | ≥95% | LMS | HR/CAIO |
| UC8-002 | Assessment Pass Rate | (Passed / Assessed) × 100 | ≥90% | LMS | HR/CAIO |
| UC8-003 | Awareness Survey Scores | Average score | ≥4.0/5 | Survey | CAIO |
| UC8-004 | Reported Concerns | Count per period | Trend | Hotline | Ethics Officer |

**Total: 40 unified metrics across 8 categories**

---

## 8. Agentic AI Metrics (Emerging)

### 8.1 Gap Analysis

Current frameworks are designed for **static models** producing single outputs. Agentic AI systems require fundamentally different measurement:

| Dimension | Static Model | Agentic AI |
|-----------|-------------|------------|
| Output | Single prediction | Multi-step action sequence |
| Autonomy | Human-in-the-loop | Autonomous with guardrails |
| Failure mode | Incorrect output | Runaway agent, tool abuse, prompt injection |
| Drift | Data/concept drift | Behavioral drift, permission escalation |
| Value | Accuracy-based | Task completion, intervention rate |

### 8.2 Proposed Agentic AI Metrics

| ID | Metric | Definition | Target | Data Source |
|----|--------|-----------|--------|-------------|
| AG-001 | Goal Accuracy | % of agent tasks completed successfully | ≥85% | Agent telemetry |
| AG-002 | Plan Adherence | % of agent actions within approved plan | ≥95% | Agent telemetry |
| AG-003 | Hallucination Rate | % of agent outputs with fabricated information | <1% | LLM-as-judge |
| AG-004 | Human Intervention Rate | % of tasks requiring human escalation | Declining trend | Agent telemetry |
| AG-005 | Escalation Frequency | Escalations per 1,000 tasks | <50 | Agent telemetry |
| AG-006 | Autonomous Resolution Rate | % tasks resolved without human intervention | ≥80% | Agent telemetry |
| AG-007 | Policy Violation Rate | % of agent actions violating policy | <0.5% | Policy engine |
| AG-008 | Permission Escalation Events | Count of unauthorized permission increases | 0 | Agent telemetry |
| AG-009 | Tool Abuse Incidents | Count of agent tool misuse events | 0 | Agent telemetry |
| AG-010 | Cost per Successful Task | $ cost per completed task | Declining trend | FinOps |
| AG-011 | Value Generated per Agent | $ value per agent per period | Positive trend | Business metrics |
| AG-012 | Agent Identity Coverage | % of agents with unique identity and owner | 100% | Agent registry |

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Months 1-3)
- [ ] Deploy AI Asset Registry with automated discovery
- [ ] Implement UC-1 (Asset Inventory) metrics
- [ ] Establish data source integrations (MLflow, ServiceNow, CI/CD)
- [ ] Define metric ownership and validation roles

### Phase 2: Core Governance (Months 4-6)
- [ ] Implement UC-2 (Risk & Compliance) metrics
- [ ] Implement UC-4 (Incident Management) metrics
- [ ] Implement UC-5 (Remediation) metrics
- [ ] Deploy three-tier escalation framework
- [ ] Map to ISO 42001 and NIST AI RMF

### Phase 3: Advanced (Months 7-9)
- [ ] Implement UC-3 (Operational Performance) metrics
- [ ] Implement UC-6 (Third-Party Risk) metrics
- [ ] Implement UC-7 (Economic Value) metrics
- [ ] Implement UC-8 (Culture & Training) metrics
- [ ] Map to EU AI Act

### Phase 4: Agentic AI (Months 10-12)
- [ ] Implement agentic AI metrics (AG-001 to AG-012)
- [ ] Deploy agent telemetry and monitoring
- [ ] Implement behavioral drift detection
- [ ] Full standards mapping and audit readiness

---

## 10. Key Recommendations

1. **Adopt the 8-category unified taxonomy** — eliminates 60-70% redundancy across frameworks
2. **Start with UC-1 (Asset Inventory)** — you cannot govern what you cannot see
3. **Implement three-tier escalation** — operational, management, board — with clear thresholds
4. **Map to all three standards simultaneously** — ISO 42001, NIST AI RMF, EU AI Act — to avoid redundant evidence collection
5. **Prioritize agentic AI metrics** — the industry gap is here; GRC_Claw can lead
6. **Automate evidence collection** — manual evidence assembly is the #1 audit failure point
7. **Assign named owners** — every metric must have a single accountable person
8. **Review cadence**: Board KPIs quarterly, management KPIs monthly, technical KPIs continuously

---

## Appendix A: Framework Source URLs

| Framework | URL |
|-----------|-----|
| Qapitol 5-KPI | https://qapitol.ai/insights/five-kpis-board-ai-assurance-executive-reporting |
| AccuroAI 12 Metrics | https://accuroai.co/blog/ai-governance-kpi-pack-12-board-metrics |
| BrianOnAI 32 KPIs | https://brianonai.com/resources/board-materials/ai-program-kpis-metrics-guide |
| Inferensys 5 KPI Categories | https://inferensys.com/guides/ai-ethics-officers-and-governance-boards/setting-up-key-performance-indicators-for-ai-governance |
| AI Economics Hub 30 KPIs | https://aieconomicshub.com/ai-economics-kpis |
| ISO/IEC 42001:2023 | https://www.iso.org/standard/42001 |
| NIST AI RMF 1.0 | https://www.nist.gov/itl/ai-risk-management-framework |
| EU AI Act | https://eur-lex.europa.eu/eli/reg/2024/1689 |

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| AIMS | AI Management System (ISO 42001) |
| CAIO | Chief AI Officer |
| CCO | Chief Compliance Officer |
| CISO | Chief Information Security Officer |
| CPO | Chief Procurement Officer |
| GRC | Governance, Risk, and Compliance |
| KPI | Key Performance Indicator |
| KRI | Key Risk Indicator |
| MTTD | Mean Time to Detect |
| MTTR | Mean Time to Resolve |
| NHI | Non-Human Identity |
| PSI | Population Stability Index |
| RCA | Root Cause Analysis |
| RMF | Risk Management Framework (NIST) |
| SLA | Service Level Agreement |
| SLO | Service Level Objective |
| TCO | Total Cost of Ownership |
| TEVV | Test, Evaluation, Validation, and Verification |

---

*End of document*
