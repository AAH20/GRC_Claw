# GRC_Claw Metric Definition Document

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** GRC_Claw Research  
**Status:** Draft for Review  
**References:** grc-claw-unified-metrics-layer.md, grc-claw-reporting-engine-analysis.md

---

## Table of Contents

1. [Introduction & Scope](#1-introduction--scope)
2. [Metric Calculation Formulas](#2-metric-calculation-formulas)
3. [Data Collection Methods](#3-data-collection-methods)
4. [Measurement Frequency](#4-measurement-frequency)
5. [Threshold Definitions](#5-threshold-definitions)
6. [Escalation Procedures](#6-escalation-procedures)
7. [Metric Reporting & Visualization](#7-metric-reporting--visualization)
8. [Metric Quality Assurance](#8-metric-quality-assurance)
9. [Appendices](#9-appendices)

---

## 1. Introduction & Scope

This document defines the complete metric specification for GRC_Claw's AI governance measurement layer. It covers **40 unified metrics** across **8 categories**, plus **12 agentic AI metrics**, with explicit formulas, data sources, collection methods, measurement frequencies, thresholds, escalation procedures, reporting formats, and quality assurance protocols.

### 1.1 Metric Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 3: BOARD & EXECUTIVE                │
│  5 Board KPIs — Coverage, Defect Escape, Remediation,       │
│  Regulatory Alignment, Third-Party Risk                      │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 2: MANAGEMENT & OPERATIONAL         │
│  23 Management KPIs — Risk, Incidents, Process, Training,   │
│  Value & ROI                                                 │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 1: TECHNICAL & FOUNDATION           │
│  21 Technical KPIs — Inventory, Performance, Data Quality,  │
│  Security, Agent Governance                                  │
├─────────────────────────────────────────────────────────────┤
│                    AGENTIC AI METRICS (CROSS-CUTTING)        │
│  12 Agent Metrics — Goal Accuracy, Plan Adherence,           │
│  Hallucination, Intervention, Escalation, Policy, etc.      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Metric ID Convention

| Prefix | Category | Count |
|--------|----------|-------|
| UC1-xxx | Asset Inventory & Coverage | 5 |
| UC2-xxx | Risk & Compliance Posture | 6 |
| UC3-xxx | Operational Performance & Reliability | 5 |
| UC4-xxx | Incident & Exception Management | 6 |
| UC5-xxx | Remediation & Continuous Improvement | 5 |
| UC6-xxx | Third-Party & Supply Chain Risk | 4 |
| UC7-xxx | Economic Value & Accountability | 5 |
| UC8-xxx | Culture, Training & Ethics | 4 |
| AG-xxx | Agentic AI Metrics | 12 |

---

## 2. Metric Calculation Formulas

### 2.1 UC-1: Asset Inventory & Coverage

#### UC1-001: AI System Inventory Coverage
```
Formula: (Registered AI systems with named owner / Total discovered AI systems) × 100
Numerator: Count of AI systems in registry with non-null owner field
Denominator: Count of all AI systems discovered via automated scanning + manual registration
Unit: Percentage (%)
Target: 100%
```

#### UC1-002: High-Risk Systems Under Governance
```
Formula: (High-risk systems with active governance / Total high-risk systems) × 100
Numerator: Count of high-risk classified systems with completed risk assessment + assigned owner + active monitoring
Denominator: Count of all systems classified as high-risk per risk taxonomy
Unit: Percentage (%)
Target: 100%
```

#### UC1-003: Agent Identity Coverage
```
Formula: (Agents with unique identity + named owner / Total agents discovered) × 100
Numerator: Count of AI agents with unique NHI (Non-Human Identity) and assigned human owner
Denominator: Count of all autonomous agents discovered in environment
Unit: Percentage (%)
Target: 100%
```

#### UC1-004: Business Unit Participation
```
Formula: (BUs with designated AI liaison / Total business units) × 100
Numerator: Count of business units with an assigned AI governance liaison
Denominator: Count of all business units in organization
Unit: Percentage (%)
Target: 100%
```

#### UC1-005: Vendor Coverage
```
Formula: (Vendors with completed due diligence / Total AI vendors) × 100
Numerator: Count of third-party AI vendors with completed due diligence assessment
Denominator: Count of all third-party AI vendors in vendor management system
Unit: Percentage (%)
Target: 100%
```

### 2.2 UC-2: Risk & Compliance Posture

#### UC2-001: Risk Assessments Complete
```
Formula: (Systems with completed risk assessment / Total systems in scope) × 100
Numerator: Count of AI systems with risk assessment completed within last 12 months
Denominator: Count of all AI systems requiring risk assessment per scope rules
Unit: Percentage (%)
Target: 100%
```

#### UC2-002: Open High-Risk Findings
```
Formula: COUNT(findings WHERE severity IN ('critical','high') AND status = 'open')
Numerator: N/A (direct count)
Denominator: N/A
Unit: Count
Target: 0
```

#### UC2-003: Regulatory Alignment Score
```
Formula: (Applicable requirements with current verifiable evidence / Total applicable requirements) × 100
Numerator: Count of regulatory requirements with evidence dated within required freshness window
Denominator: Count of all regulatory requirements applicable to AI systems in scope
Unit: Percentage (%)
Target: 100%
```

#### UC2-004: Policy Adherence Rate
```
Formula: (Projects passing pre-deployment policy review / Total projects entering pipeline) × 100
Numerator: Count of AI projects that passed mandatory policy review gate
Denominator: Count of all AI projects that entered the deployment pipeline
Unit: Percentage (%)
Target: ≥95%
```

#### UC2-005: Policy-to-Enforcement Gap
```
Formula: (Policy statements with technical control implemented / Total policy statements) × 100
Numerator: Count of AI policy statements with at least one technical control mapped and verified
Denominator: Count of all AI policy statements in policy management system
Unit: Percentage (%)
Target: 100%
```

#### UC2-006: Audit Findings
```
Formula: COUNT(audit_findings WHERE audit_period = current_year)
Numerator: N/A (direct count)
Denominator: N/A
Unit: Count per year
Target: ≤2
```

### 2.3 UC-3: Operational Performance & Reliability

#### UC3-001: Model Accuracy / F1 Score
```
Formula: Standard ML metrics per model type
  - Classification: F1 = 2 × (Precision × Recall) / (Precision + Recall)
  - Regression: RMSE = √(Σ(predicted - actual)² / n)
  - Generation: BLEU/ROUGE per use case
Numerator: Per model evaluation results
Denominator: Per test dataset
Unit: Varies by model type
Target: Per model baseline (defined at deployment)
```

#### UC3-002: Model Drift Detection
```
Formula: PSI = Σ((actual% - expected%) × ln(actual% / expected%))
  - PSI < 0.1: No significant drift
  - 0.1 ≤ PSI < 0.25: Moderate drift
  - PSI ≥ 0.25: Significant drift
Also: KL divergence, accuracy delta from baseline
Numerator: Distribution comparison between training/reference and production
Denominator: Reference distribution
Unit: Index value
Target: <0.5% drift
```

#### UC3-003: System Availability / Uptime
```
Formula: (Total uptime / Total scheduled time) × 100
Numerator: Sum of time system was operational and accessible
Denominator: Total time in measurement period
Unit: Percentage (%)
Target: ≥99.5%
```

#### UC3-004: Response Time (P95/P99)
```
Formula: Percentile(response_times, 95) or Percentile(response_times, 99)
Numerator: N/A (statistical percentile)
Denominator: N/A
Unit: Milliseconds (ms)
Target: Per SLO definition
```

#### UC3-005: Human Override Rate
```
Formula: (Human overrides of AI decisions / Total AI decisions) × 100
Numerator: Count of AI decisions overridden by human operator
Denominator: Count of all AI decisions in period
Unit: Percentage (%)
Target: Per risk tier (defined per system)
```

### 2.4 UC-4: Incident & Exception Management

#### UC4-001: AI Incidents (by severity)
```
Formula: COUNT(incidents WHERE category = 'AI-related' AND period = measurement_period)
Grouped by severity: critical, high, medium, low
Numerator: N/A (direct count)
Denominator: N/A
Unit: Count per period
Target: Declining trend
```

#### UC4-002: Mean Time to Detect (MTTD)
```
Formula: AVG(detection_timestamp - occurrence_timestamp) for all incidents in period
Numerator: Sum of detection times
Denominator: Count of incidents
Unit: Hours
Target: <1 hour
```

#### UC4-003: Mean Time to Resolve (MTTR)
```
Formula: AVG(resolution_timestamp - detection_timestamp) for all resolved incidents in period
Numerator: Sum of resolution times
Denominator: Count of resolved incidents
Unit: Hours
Target: <4 hours
```

#### UC4-004: Incidents Resolved Within SLA
```
Formula: (Incidents resolved within SLA / Total incidents) × 100
Numerator: Count of incidents resolved within defined SLA window
Denominator: Count of all incidents in period
Unit: Percentage (%)
Target: ≥95%
```

#### UC4-005: Recurring Incidents
```
Formula: (Incidents with same root cause as prior incident / Total incidents) × 100
Numerator: Count of incidents linked to a previously identified root cause
Denominator: Count of all incidents in period
Unit: Percentage (%)
Target: <10%
```

#### UC4-006: Root Cause Analysis Completion
```
Formula: (Incidents with completed RCA / Total incidents) × 100
Numerator: Count of incidents with documented root cause analysis
Denominator: Count of all incidents in period
Unit: Percentage (%)
Target: 100%
```

### 2.5 UC-5: Remediation & Continuous Improvement

#### UC5-001: Remediation Velocity (Median Days)
```
Formula: MEDIAN(closure_date - identification_date) for all findings in period
Numerator: N/A (median calculation)
Denominator: N/A
Unit: Days
Target: ≤30 days
```

#### UC5-002: Remediation Velocity (Critical)
```
Formula: MEDIAN(closure_date - identification_date) WHERE severity = 'critical'
Numerator: N/A (median calculation)
Denominator: N/A
Unit: Days
Target: ≤45 days
```

#### UC5-003: Governance Committee Throughput
```
Formula: COUNT(decisions WHERE committee = 'AI Governance' AND quarter = current_quarter)
Numerator: N/A (direct count)
Denominator: N/A
Unit: Decisions per quarter
Target: Benchmark (established after 2 quarters of baseline)
```

#### UC5-004: Governance ROI
```
Formula: (Value delivered by AI initiatives / Cost of governance program) 
Numerator: Sum of quantified business value from AI initiatives
Denominator: Total cost of AI governance program (personnel + tools + processes)
Unit: Ratio
Target: >1.0
```

#### UC5-005: Maturity Level (Self-Assessed)
```
Formula: Average score across 5 maturity dimensions (1-5 scale)
  - Dimension 1: Strategy & Governance
  - Dimension 2: Risk Management
  - Dimension 3: Operational Excellence
  - Dimension 4: Culture & Training
  - Dimension 5: Value Delivery
Numerator: Sum of dimension scores
Denominator: 5
Unit: Scale (1-5)
Target: ≥3.0
```

### 2.6 UC-6: Third-Party & Supply Chain Risk

#### UC6-001: Third-Party AI Risk Exposure
```
Formula: COUNT(vendors WHERE risk_tier = 'high' AND assurance_status = 'unassured')
Numerator: N/A (direct count)
Denominator: N/A
Unit: Count
Target: 0
```

#### UC6-002: Vendor Assessment Turnaround
```
Formula: AVG(completion_date - initiation_date) for all vendor assessments in period
Numerator: Sum of assessment durations
Denominator: Count of vendor assessments
Unit: Days
Target: Benchmark (established after 2 quarters of baseline)
```

#### UC6-003: Fourth-Party Risk Exposure
```
Formula: COUNT(fourth_party_dependencies WHERE assurance_status = 'unassured')
Numerator: N/A (direct count)
Denominator: N/A
Unit: Count
Target: 0
```

#### UC6-004: Vendor Due Diligence Coverage
```
Formula: (Vendors with completed due diligence / Total vendors) × 100
Numerator: Count of vendors with completed due diligence
Denominator: Count of all vendors
Unit: Percentage (%)
Target: 100%
```

### 2.7 UC-7: Economic Value & Accountability

#### UC7-001: AI Value Delivered
```
Formula: SUM(business_value_attributed_to_AI_initiatives) in period
Numerator: N/A (direct sum)
Denominator: N/A
Unit: Currency ($)
Target: Positive trend
```

#### UC7-002: Cost Avoidance from Risk Prevention
```
Formula: SUM(estimated_cost_of_risks_mitigated) in period
Numerator: N/A (direct sum)
Denominator: N/A
Unit: Currency ($)
Target: Tracked and reported
```

#### UC7-003: AI Spend Allocation Rate
```
Formula: (AI spend attributed to owner/BU/cost centre / Total AI spend) × 100
Numerator: Sum of AI spend with attributed owner
Denominator: Sum of all AI spend
Unit: Percentage (%)
Target: 100%
```

#### UC7-004: Shadow AI Spend Ratio
```
Formula: (AI spend outside formal IT budgets / Total AI spend) × 100
Numerator: Sum of unattributed AI spend
Denominator: Sum of all AI spend
Unit: Percentage (%)
Target: <10%
```

#### UC7-005: AI Initiative Ownership Rate
```
Formula: (Initiatives with named economic owner / Total AI initiatives) × 100
Numerator: Count of AI initiatives with assigned economic owner
Denominator: Count of all AI initiatives
Unit: Percentage (%)
Target: 100%
```

### 2.8 UC-8: Culture, Training & Ethics

#### UC8-001: Training Completion Rate
```
Formula: (Employees completed training / Employees assigned training) × 100
Numerator: Count of employees who completed required AI training
Denominator: Count of employees assigned required AI training
Unit: Percentage (%)
Target: ≥95%
```

#### UC8-002: Assessment Pass Rate
```
Formula: (Employees passed assessment / Employees assessed) × 100
Numerator: Count of employees who passed AI competency assessment
Denominator: Count of employees who took AI competency assessment
Unit: Percentage (%)
Target: ≥90%
```

#### UC8-003: Awareness Survey Scores
```
Formula: AVG(survey_response_scores) across all respondents
Numerator: Sum of all survey response scores
Denominator: Count of survey responses
Unit: Scale (1-5)
Target: ≥4.0/5
```

#### UC8-004: Reported Concerns
```
Formula: COUNT(concerns_reported WHERE period = measurement_period)
Numerator: N/A (direct count)
Denominator: N/A
Unit: Count per period
Target: Trend (increasing indicates healthy reporting culture)
```

### 2.9 Agentic AI Metrics

#### AG-001: Goal Accuracy
```
Formula: (Agent tasks completed successfully / Total agent tasks attempted) × 100
Numerator: Count of agent tasks achieving defined success criteria
Denominator: Count of all agent tasks attempted
Unit: Percentage (%)
Target: ≥85%
```

#### AG-002: Plan Adherence
```
Formula: (Agent actions within approved plan / Total agent actions) × 100
Numerator: Count of agent actions that match approved plan steps
Denominator: Count of all agent actions
Unit: Percentage (%)
Target: ≥95%
```

#### AG-003: Hallucination Rate
```
Formula: (Agent outputs with fabricated information / Total agent outputs) × 100
Numerator: Count of outputs flagged by LLM-as-judge as containing fabricated information
Denominator: Count of all agent outputs evaluated
Unit: Percentage (%)
Target: <1%
```

#### AG-004: Human Intervention Rate
```
Formula: (Tasks requiring human escalation / Total agent tasks) × 100
Numerator: Count of tasks where human intervention was required
Denominator: Count of all agent tasks
Unit: Percentage (%)
Target: Declining trend
```

#### AG-005: Escalation Frequency
```
Formula: (Total escalations / Total tasks) × 1000
Numerator: Count of escalations to human operator
Denominator: Count of all agent tasks
Unit: Escalations per 1,000 tasks
Target: <50
```

#### AG-006: Autonomous Resolution Rate
```
Formula: (Tasks resolved without human intervention / Total agent tasks) × 100
Numerator: Count of tasks completed autonomously
Denominator: Count of all agent tasks
Unit: Percentage (%)
Target: ≥80%
```

#### AG-007: Policy Violation Rate
```
Formula: (Agent actions violating policy / Total agent actions) × 100
Numerator: Count of actions flagged by policy engine as violations
Denominator: Count of all agent actions
Unit: Percentage (%)
Target: <0.5%
```

#### AG-008: Permission Escalation Events
```
Formula: COUNT(events WHERE type = 'unauthorized_permission_increase')
Numerator: N/A (direct count)
Denominator: N/A
Unit: Count
Target: 0
```

#### AG-009: Tool Abuse Incidents
```
Formula: COUNT(incidents WHERE type = 'agent_tool_misuse')
Numerator: N/A (direct count)
Denominator: N/A
Unit: Count
Target: 0
```

#### AG-010: Cost per Successful Task
```
Formula: Total agent operational cost / Count of successfully completed tasks
Numerator: Sum of compute + API + infrastructure costs for agent operations
Denominator: Count of successfully completed tasks
Unit: Currency ($) per task
Target: Declining trend
```

#### AG-011: Value Generated per Agent
```
Formula: Total business value generated by agent / Count of active agents in period
Numerator: Sum of quantified business value attributed to agent actions
Denominator: Count of active agents
Unit: Currency ($) per agent per period
Target: Positive trend
```

#### AG-012: Agent Identity Coverage
```
Formula: (Agents with unique identity + named owner / Total agents) × 100
Numerator: Count of agents with unique NHI and assigned human owner
Denominator: Count of all agents
Unit: Percentage (%)
Target: 100%
```

---

## 3. Data Collection Methods

### 3.1 Data Source Inventory

| Data Source | Systems | Metrics Fed | Collection Method | Protocol |
|-------------|---------|-------------|-------------------|----------|
| AI Asset Registry | MLflow, W&B, custom | UC1-001, UC1-002, UC1-003, UC2-001 | Automated discovery + manual registration | REST API, scheduled sync |
| Model Evaluation Pipeline | CI/CD (GitHub Actions, Jenkins) | UC2-004, UC3-001, UC3-002 | Automated testing in deployment pipeline | Webhook, API |
| Monitoring & Observability | Arize, Fiddler, Datadog, Prometheus | UC3-002, UC3-003, UC3-004, UC4-002 | Real-time telemetry | Streaming, Prometheus remote write |
| Incident Management | ServiceNow, Jira | UC4-001, UC4-003, UC4-004, UC4-005, UC4-006 | Incident tickets | REST API, webhook |
| GRC Platform | ServiceNow GRC, Archer, custom | UC2-001, UC2-002, UC2-003, UC5-001, UC5-002 | Risk registers, control assessments | REST API, scheduled export |
| Vendor Management | Coupa, SAP Ariba, custom | UC1-005, UC6-001, UC6-002, UC6-003, UC6-004 | Due diligence workflows | REST API, manual entry |
| LMS & Training | Cornerstone, Workday, custom | UC8-001, UC8-002 | Course completion, assessments | REST API, SCORM |
| Finance & Cost | SAP, Oracle, custom | UC7-001, UC7-002, UC7-003, UC7-004, UC5-004 | Spend allocation, TCO tracking | REST API, scheduled export |
| Policy Management | Confluence, SharePoint, custom | UC2-004, UC2-005 | Policy acknowledgments, attestations | REST API, manual |
| Audit & Compliance | AuditBoard, Workiva | UC2-003, UC2-006, UC4-006 | Audit findings, remediation tracking | REST API |
| User Feedback | SurveyMonkey, Qualtrics | UC8-003, UC8-004 | NPS, awareness surveys | REST API, email |
| Post-Market Monitoring | Custom dashboards | UC3-002, UC4-001 | Production monitoring data | Streaming, API |
| Agent Telemetry | Custom agent framework | AG-001 through AG-012 | Agent action logs, outcome tracking | Streaming, event-driven |
| Policy Engine | OPA, custom | AG-007, AG-008 | Real-time policy evaluation | API call per action |

### 3.2 Collection Method Details

#### 3.2.1 Automated Discovery (UC-1)
- **Network scanning**: Discover AI endpoints, APIs, and services
- **Code repository scanning**: Identify AI/ML code, models, and configurations
- **Cloud resource scanning**: Discover AI/ML cloud resources (SageMaker, Vertex AI, Azure ML)
- **MCP server discovery**: Identify MCP servers and connected agents
- **Frequency**: Continuous with daily full scans

#### 3.2.2 Pipeline Integration (UC-2, UC3)
- **Pre-deployment gates**: Automated policy checks in CI/CD pipeline
- **Model evaluation**: Automated accuracy, fairness, robustness testing
- **Drift detection**: Continuous monitoring of input/output distributions
- **Frequency**: Per deployment + continuous monitoring

#### 3.2.3 Incident-Driven Collection (UC-4)
- **Incident creation**: Automatic ticket creation from monitoring alerts
- **Severity classification**: Automated based on impact and scope
- **SLA tracking**: Automatic timestamp capture at each stage
- **Frequency**: Per incident

#### 3.2.4 Survey-Based Collection (UC-8)
- **Training records**: LMS auto-completion tracking
- **Assessments**: Automated scoring and pass/fail determination
- **Surveys**: Quarterly pulse surveys with automated distribution
- **Frequency**: Per training cycle / quarterly

#### 3.2.5 Financial Data Collection (UC-7)
- **Cost allocation**: Automated tagging of AI spend by BU/cost centre
- **Shadow AI detection**: Analysis of unattributed cloud AI spend
- **Value tracking**: Business outcome attribution from project tracking
- **Frequency**: Monthly

#### 3.2.6 Agent Telemetry Collection (AG-001 to AG-012)
- **Action logging**: Every agent action logged with timestamp, input, output
- **Outcome tracking**: Success/failure classification per task
- **Intervention tracking**: Human escalation events with context
- **Policy evaluation**: Real-time policy engine evaluation per action
- **Frequency**: Real-time streaming

### 3.3 Data Quality Requirements

| Requirement | Standard | Verification |
|-------------|----------|--------------|
| Completeness | ≥95% of expected data points present | Automated completeness checks |
| Accuracy | ≥98% accuracy against source system | Sampling validation |
| Timeliness | Data latency ≤1 hour for operational metrics | Timestamp validation |
| Consistency | Cross-source reconciliation passes | Automated reconciliation |
| Validity | Data conforms to expected format/range | Schema validation |

---

## 4. Measurement Frequency

### 4.1 Frequency Matrix

| Metric ID | Metric Name | Frequency | Rationale |
|-----------|-------------|-----------|-----------|
| UC1-001 | AI System Inventory Coverage | Continuous | Asset changes are event-driven |
| UC1-002 | High-Risk Systems Under Governance | Weekly | Risk posture changes frequently |
| UC1-003 | Agent Identity Coverage | Continuous | Agent deployment is event-driven |
| UC1-004 | Business Unit Participation | Monthly | Org changes are monthly |
| UC1-005 | Vendor Coverage | Monthly | Vendor onboarding is continuous |
| UC2-001 | Risk Assessments Complete | Monthly | Assessment completion tracked monthly |
| UC2-002 | Open High-Risk Findings | Daily | Finding status changes frequently |
| UC2-003 | Regulatory Alignment Score | Semi-annual | Regulatory evidence is periodic |
| UC2-004 | Policy Adherence Rate | Per deployment | Pipeline gate is per-deployment |
| UC2-005 | Policy-to-Enforcement Gap | Quarterly | Policy changes are quarterly |
| UC2-006 | Audit Findings | Per audit cycle | Audit schedule driven |
| UC3-001 | Model Accuracy / F1 Score | Per deployment + continuous | Eval per deploy, drift continuous |
| UC3-002 | Model Drift Detection | Continuous | Real-time distribution monitoring |
| UC3-003 | System Availability / Uptime | Continuous | Infrastructure monitoring |
| UC3-004 | Response Time (P95/P99) | Continuous | Real-time latency monitoring |
| UC3-005 | Human Override Rate | Daily | Decision volume requires daily agg |
| UC4-001 | AI Incidents (by severity) | Per incident + daily summary | Event-driven with daily rollup |
| UC4-002 | Mean Time to Detect (MTTD) | Per incident + weekly summary | Event-driven with weekly rollup |
| UC4-003 | Mean Time to Resolve (MTTR) | Per incident + weekly summary | Event-driven with weekly rollup |
| UC4-004 | Incidents Resolved Within SLA | Weekly | SLA performance reviewed weekly |
| UC4-005 | Recurring Incidents | Monthly | Pattern detection requires monthly |
| UC4-006 | Root Cause Analysis Completion | Monthly | RCA completion tracked monthly |
| UC5-001 | Remediation Velocity (Median Days) | Monthly | Remediation tracked monthly |
| UC5-002 | Remediation Velocity (Critical) | Monthly | Critical remediation tracked monthly |
| UC5-003 | Governance Committee Throughput | Quarterly | Committee meets quarterly |
| UC5-004 | Governance ROI | Quarterly | Financial metrics are quarterly |
| UC5-005 | Maturity Level (Self-Assessed) | Semi-annual | Maturity assessed semi-annually |
| UC6-001 | Third-Party AI Risk Exposure | Monthly | Vendor risk reviewed monthly |
| UC6-002 | Vendor Assessment Turnaround | Monthly | Assessment turnaround monthly |
| UC6-003 | Fourth-Party Risk Exposure | Quarterly | Fourth-party reviewed quarterly |
| UC6-004 | Vendor Due Diligence Coverage | Monthly | DD completion tracked monthly |
| UC7-001 | AI Value Delivered | Quarterly | Value attribution is quarterly |
| UC7-002 | Cost Avoidance from Risk Prevention | Quarterly | Cost avoidance is quarterly |
| UC7-003 | AI Spend Allocation Rate | Monthly | Spend tracked monthly |
| UC7-004 | Shadow AI Spend Ratio | Monthly | Shadow spend tracked monthly |
| UC7-005 | AI Initiative Ownership Rate | Monthly | Ownership tracked monthly |
| UC8-001 | Training Completion Rate | Per training cycle + monthly | Training cycles vary |
| UC8-002 | Assessment Pass Rate | Per training cycle + monthly | Assessment cycles vary |
| UC8-003 | Awareness Survey Scores | Quarterly | Surveys conducted quarterly |
| UC8-004 | Reported Concerns | Monthly | Concerns tracked monthly |
| AG-001 | Goal Accuracy | Continuous | Agent telemetry is real-time |
| AG-002 | Plan Adherence | Continuous | Agent telemetry is real-time |
| AG-003 | Hallucination Rate | Daily | LLM-as-judge evaluation daily |
| AG-004 | Human Intervention Rate | Continuous | Agent telemetry is real-time |
| AG-005 | Escalation Frequency | Continuous | Agent telemetry is real-time |
| AG-006 | Autonomous Resolution Rate | Continuous | Agent telemetry is real-time |
| AG-007 | Policy Violation Rate | Continuous | Policy engine is real-time |
| AG-008 | Permission Escalation Events | Continuous | Agent telemetry is real-time |
| AG-009 | Tool Abuse Incidents | Continuous | Agent telemetry is real-time |
| AG-010 | Cost per Successful Task | Daily | Cost aggregation daily |
| AG-011 | Value Generated per Agent | Weekly | Value attribution weekly |
| AG-012 | Agent Identity Coverage | Continuous | Agent registry is real-time |

### 4.2 Frequency by Layer

| Layer | Frequency | Metrics |
|-------|-----------|---------|
| Board (Layer 3) | Quarterly | 5 Board KPIs |
| Management (Layer 2) | Monthly | 23 Management KPIs |
| Technical (Layer 1) | Continuous | 21 Technical KPIs |
| Agentic AI | Continuous | 12 Agent Metrics |

### 4.3 Event-Driven Triggers

Certain metrics are recalculated immediately upon specific events:

| Event | Metrics Recalculated |
|-------|---------------------|
| New AI system deployed | UC1-001, UC1-002, UC2-001 |
| New agent deployed | UC1-003, AG-012 |
| Incident declared | UC4-001, UC4-002, UC4-003 |
| Finding created/closed | UC2-002, UC5-001, UC5-002 |
| Vendor onboarded | UC1-005, UC6-001, UC6-004 |
| Training completed | UC8-001, UC8-002 |
| Policy updated | UC2-004, UC2-005 |
| Model retrained | UC3-001, UC3-002 |

---

## 5. Threshold Definitions

### 5.1 Threshold Structure

Each metric has three threshold levels corresponding to the three-tier escalation model:

| Level | Name | Description |
|-------|------|-------------|
| T1 | Operational | Target breach within risk tolerance |
| T2 | Management | Escalation threshold requiring management action |
| T3 | Board | Board-level threshold requiring board disclosure |

### 5.2 Threshold Matrix

| Metric ID | Metric | T1 (Operational) | T2 (Management) | T3 (Board) |
|-----------|--------|-------------------|-------------------|------------|
| UC1-001 | AI System Inventory Coverage | <90% | <85% | <80% or any unassured high-risk system |
| UC1-002 | High-Risk Systems Under Governance | <95% | <90% | <85% or any high-risk system without assessment |
| UC1-003 | Agent Identity Coverage | <90% | <85% | <80% or any agent without identity |
| UC1-004 | Business Unit Participation | <80% | <70% | <60% |
| UC1-005 | Vendor Coverage | <90% | <85% | <80% or any high-risk vendor unassured |
| UC2-001 | Risk Assessments Complete | <90% | <85% | <80% or any high-risk system without assessment |
| UC2-002 | Open High-Risk Findings | >5 | >10 | >20 or any critical finding >30 days |
| UC2-003 | Regulatory Alignment Score | <85% | <80% | <75% or >5pp decline |
| UC2-004 | Policy Adherence Rate | <90% | <85% | <80% |
| UC2-005 | Policy-to-Enforcement Gap | <90% | <85% | <80% |
| UC2-006 | Audit Findings | >3 | >5 | >8 or any critical finding |
| UC3-001 | Model Accuracy / F1 Score | <baseline - 5% | <baseline - 10% | <baseline - 15% |
| UC3-002 | Model Drift Detection | >0.5% | >1% | >2% |
| UC3-003 | System Availability / Uptime | <99.5% | <99.0% | <98.0% |
| UC3-004 | Response Time (P95/P99) | >SLO × 1.2 | >SLO × 1.5 | >SLO × 2.0 |
| UC3-005 | Human Override Rate | >target + 5% | >target + 10% | >target + 15% |
| UC4-001 | AI Incidents (Critical) | >0 | >1 | >3 or any regulatory reportable |
| UC4-002 | Mean Time to Detect (MTTD) | >30 min | >45 min | >1 hour |
| UC4-003 | Mean Time to Resolve (MTTR) | >2 hours | >3 hours | >4 hours |
| UC4-004 | Incidents Resolved Within SLA | <95% | <90% | <85% |
| UC4-005 | Recurring Incidents | >5% | >8% | >10% |
| UC4-006 | RCA Completion | <95% | <90% | <85% |
| UC5-001 | Remediation Velocity (Median) | >20 days | >25 days | >30 days |
| UC5-002 | Remediation Velocity (Critical) | >30 days | >45 days | >60 days |
| UC5-003 | Governance Committee Throughput | <benchmark - 20% | <benchmark - 40% | <benchmark - 60% |
| UC5-004 | Governance ROI | <1.2 | <1.0 | <0.8 |
| UC5-005 | Maturity Level | <2.5 | <2.0 | <1.5 |
| UC6-001 | Third-Party AI Risk Exposure | >0 | >1 | >3 or any >30 days overdue |
| UC6-002 | Vendor Assessment Turnaround | >benchmark + 20% | >benchmark + 50% | >benchmark + 100% |
| UC6-003 | Fourth-Party Risk Exposure | >0 | >2 | >5 |
| UC6-004 | Vendor Due Diligence Coverage | <95% | <90% | <85% |
| UC7-001 | AI Value Delivered | <80% of target | <60% of target | <40% of target |
| UC7-002 | Cost Avoidance | Tracked | Tracked | Tracked |
| UC7-003 | AI Spend Allocation Rate | <90% | <85% | <80% |
| UC7-004 | Shadow AI Spend Ratio | >10% | >20% | >30% |
| UC7-005 | AI Initiative Ownership Rate | <90% | <85% | <80% |
| UC8-001 | Training Completion Rate | <85% | <80% | <75% |
| UC8-002 | Assessment Pass Rate | <85% | <80% | <75% |
| UC8-003 | Awareness Survey Scores | <3.5/5 | <3.0/5 | <2.5/5 |
| UC8-004 | Reported Concerns | Tracked | Tracked | Tracked |
| AG-001 | Goal Accuracy | <80% | <75% | <70% |
| AG-002 | Plan Adherence | <90% | <85% | <80% |
| AG-003 | Hallucination Rate | >0.5% | >1% | >2% |
| AG-004 | Human Intervention Rate | >25% | >35% | >50% |
| AG-005 | Escalation Frequency | >30 | >50 | >100 |
| AG-006 | Autonomous Resolution Rate | <70% | <60% | <50% |
| AG-007 | Policy Violation Rate | >0.1% | >0.5% | >1% |
| AG-008 | Permission Escalation Events | >0 | >2 | >5 |
| AG-009 | Tool Abuse Incidents | >0 | >1 | >3 |
| AG-010 | Cost per Successful Task | >baseline + 20% | >baseline + 50% | >baseline + 100% |
| AG-011 | Value Generated per Agent | <80% of target | <60% of target | <40% of target |
| AG-012 | Agent Identity Coverage | <90% | <85% | <80% |

### 5.3 Threshold Change Management

- Thresholds are reviewed semi-annually by the AI Governance Committee
- Changes require CAIO approval and 30-day notice before taking effect
- Emergency threshold changes can be made by AI Risk Officer with 24-hour notice
- All threshold changes are logged in the metric registry with version history
- Threshold changes take effect after the notice period expires

---

## 6. Escalation Procedures

### 6.1 Three-Tier Escalation Model

```
┌─────────────────────────────────────────────────────────────┐
│                    TIER 3: BOARD                             │
│  Trigger: Metric breaches T3 threshold                       │
│  Audience: Board Risk Committee, C-Suite                     │
│  Action: Board disclosure, mandatory remediation plan        │
│  Response: Next board meeting                               │
├─────────────────────────────────────────────────────────────┤
│                    TIER 2: MANAGEMENT                        │
│  Trigger: Metric breaches T2 threshold                       │
│  Audience: AI Risk function, CAIO, Compliance                │
│  Action: Escalate to management, remediation plan required   │
│  Response: 7-14 days                                        │
├─────────────────────────────────────────────────────────────┤
│                    TIER 1: OPERATIONAL                       │
│  Trigger: Metric breaches T1 threshold                       │
│  Audience: System owner, engineering team                    │
│  Action: Remediate within standard SLA                       │
│  Response: 24-72 hours                                      │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Escalation Procedures by Tier

#### Tier 1: Operational Escalation

**Trigger**: Metric value crosses T1 threshold

**Procedure**:
1. Automated alert sent to system owner and engineering team
2. Alert includes: metric name, current value, threshold breached, trend
3. Owner acknowledges alert within 4 hours
4. Remediation plan documented within 24 hours
5. Remediation executed within 72 hours
6. Metric re-measured after remediation
7. If metric returns to within T1, close escalation
8. If metric remains at T1 or worsens to T2, escalate to Tier 2

**Responsible Parties**:
- Primary: System owner
- Support: Engineering team
- Oversight: AI Governance Lead

**Communication**:
- Channel: Slack/Teams alert + email
- Format: Standard alert template
- Documentation: Incident ticket or finding record

#### Tier 2: Management Escalation

**Trigger**: Metric value crosses T2 threshold OR Tier 1 escalation unresolved after 72 hours

**Procedure**:
1. Automated alert sent to AI Risk function, CAIO, and Compliance
2. Alert includes: metric name, current value, threshold, trend, Tier 1 actions taken
3. Management review meeting scheduled within 7 days
4. Remediation plan with resources and timeline documented
5. Progress tracked weekly until resolved
6. If metric returns to within T1, close escalation
7. If metric worsens to T3, escalate to Tier 3

**Responsible Parties**:
- Primary: AI Risk Officer
- Support: CAIO, Compliance, system owner
- Oversight: AI Governance Committee

**Communication**:
- Channel: Email + management dashboard flag
- Format: Management escalation report
- Documentation: Remediation plan in GRC platform

#### Tier 3: Board Escalation

**Trigger**: Metric value crosses T3 threshold OR Tier 2 escalation unresolved after 14 days

**Procedure**:
1. Automated alert sent to Board Risk Committee chair and C-Suite
2. Alert includes: metric name, current value, threshold, trend, all prior actions
3. Emergency board briefing scheduled within 48 hours
4. Board disclosure prepared for next board meeting
5. Mandatory remediation plan with board-approved resources
6. Monthly progress reports to board until resolved
7. External communication plan if regulatory reportable

**Responsible Parties**:
- Primary: CAIO
- Support: CCO, CISO, CPO, AI Risk Officer
- Oversight: Board Risk Committee

**Communication**:
- Channel: Secure board portal + executive briefing
- Format: Board disclosure document
- Documentation: Board minutes + remediation plan

### 6.3 Escalation Timelines

| Tier | Acknowledgment | Plan | Resolution Target | Board Disclosure |
|------|---------------|------|-------------------|------------------|
| T1 | 4 hours | 24 hours | 72 hours | N/A |
| T2 | 24 hours | 7 days | 14 days | Next board meeting |
| T3 | 48 hours | 48 hours | 30 days | Emergency briefing + next board meeting |

### 6.4 Special Escalation Triggers

Certain conditions trigger immediate escalation regardless of metric value:

| Condition | Automatic Tier | Rationale |
|-----------|---------------|-----------|
| Any critical AI incident | T3 | Potential regulatory/reportable event |
| Any regulatory inquiry | T3 | Regulatory scrutiny requires board visibility |
| Any data breach involving AI | T3 | Legal and reputational risk |
| Any model causing harm to individuals | T3 | EU AI Act Art. 73 requires reporting |
| Any agent unauthorized access | T2 | Security incident |
| Any vendor security breach | T2 | Supply chain risk |
| Any critical finding >30 days | T2 | Remediation failure |

### 6.5 Escalation Documentation

Every escalation must include:
1. Metric ID and name
2. Current value and threshold breached
3. Trend analysis (is it improving or worsening?)
4. Root cause analysis
5. Remediation plan with owner and timeline
6. Resource requirements
7. Risk if not remediated
8. Communication log

---

## 7. Metric Reporting & Visualization

### 7.1 Three-Layer Dashboard Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EXECUTIVE DASHBOARD                       │
│  Audience: Board, C-Suite                                   │
│  Content: Material signals, compliance score, top risks     │
│  Interaction: One-page principle, traffic-light, drill-down │
├─────────────────────────────────────────────────────────────┤
│                    PROGRAM DASHBOARD                         │
│  Audience: Governance leaders, Risk officers                │
│  Content: Risk tier breakdown, control status, exceptions   │
│  Interaction: Filtering, grouping, trend analysis           │
├─────────────────────────────────────────────────────────────┤
│                    OPERATING DASHBOARD                       │
│  Audience: Engineers, Compliance ops                        │
│  Content: Record-level detail, inventory, incidents         │
│  Interaction: Full search, evidence linkage, workflow       │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Report Templates

#### 7.2.1 Board Compliance Summary (Quarterly)

**Audience**: Board, C-Suite  
**Frequency**: Quarterly  
**Format**: PDF, interactive dashboard  
**Content**:
- Overall compliance score with trend
- Score by framework (EU AI Act, NIST AI RMF, ISO 42001)
- Top 5 material risks
- Decisions awaiting board attention
- Incident summary (open/closed)
- Key metrics with RAG status
- Trend analysis (90-day)

#### 7.2.2 Regulatory Evidence Pack (On-Demand)

**Audience**: Regulators, Auditors  
**Frequency**: On-demand  
**Format**: Structured bundle (PDF + structured data)  
**Content**:
- System identification and classification
- Technical documentation (Annex IV)
- Risk management records (Art. 9)
- Conformity assessment
- Logging and record-keeping evidence
- Post-market monitoring data
- Incident reports
- Registration details
- Change log

#### 7.2.3 Executive Risk Dashboard (Real-Time)

**Audience**: C-Suite  
**Frequency**: Real-time  
**Format**: Web dashboard  
**Content**:
- Risk posture summary
- Incident summary
- Resource needs
- Strategic alignment
- Key metrics with RAG status

#### 7.2.4 Program Status Report (Monthly)

**Audience**: Governance Committee  
**Frequency**: Monthly  
**Format**: PDF, web  
**Content**:
- Control status by family
- Exception exposure
- Review currency
- Monitoring coverage
- Decision speed metrics
- Remediation progress

#### 7.2.5 Operational Compliance View (Real-Time)

**Audience**: Engineers, Ops  
**Frequency**: Real-time  
**Format**: Web dashboard  
**Content**:
- System inventory with status
- Evidence freshness
- Open findings and remediation
- Incident register
- Change log
- Access review status

#### 7.2.6 Vendor Risk Assessment (Per-Vendor)

**Audience**: Procurement, Risk  
**Frequency**: Per-vendor  
**Format**: PDF, structured  
**Content**:
- Vendor risk tier
- Due diligence status
- Compliance posture
- Incident history
- Contract coverage

#### 7.2.7 Incident Report (Per-Incident)

**Audience**: All stakeholders  
**Frequency**: Per-incident  
**Format**: PDF, web  
**Content**:
- Incident timeline
- Root cause analysis
- Impact assessment
- Remediation actions
- Lessons learned

#### 7.2.8 Transparency Report (Annual)

**Audience**: Public  
**Frequency**: Annual  
**Format**: Web, PDF  
**Content**:
- AI governance commitments
- Incident disclosures
- Trust index
- Maturity level

### 7.3 Visualization Standards

#### 7.3.1 RAG Status Indicators

| Status | Color | Meaning |
|--------|-------|---------|
| Green | 🟢 | Within target, no action needed |
| Amber | 🟡 | Approaching threshold, monitoring required |
| Red | 🔴 | Threshold breached, action required |
| Gray | ⚪ | Insufficient data, measurement pending |

#### 7.3.2 Trend Indicators

| Indicator | Meaning |
|-----------|---------|
| ↑ | Improving (metric value increasing for positive metrics) |
| ↓ | Worsening (metric value decreasing for positive metrics) |
| → | Stable (no significant change) |
| ↗ | Slightly improving |
| ↘ | Slightly worsening |

#### 7.3.3 Chart Types by Metric Type

| Metric Type | Recommended Chart | Rationale |
|-------------|-------------------|-----------|
| Percentage | Gauge, progress bar | Clear target comparison |
| Count | Bar chart, trend line | Volume and trend visibility |
| Time (days/hours) | Trend line, box plot | Distribution and trend |
| Currency | Bar chart, trend line | Financial tracking |
| Ratio | Trend line, scatter plot | Relationship visibility |
| Scale (1-5) | Radar chart, bar chart | Multi-dimensional comparison |

### 7.4 Stakeholder Communication Matrix

| Stakeholder | Frequency | Format | Key Content |
|-------------|-----------|--------|-------------|
| Board | Quarterly | PDF, dashboard | Compliance score, material risks, decisions |
| C-Suite | Monthly | Dashboard, summary | Risk posture, incidents, resources |
| Regulators | On-demand | Evidence pack | Technical docs, conformity, risk records |
| Governance Committee | Monthly | Dashboard, PDF | Control status, exceptions, remediation |
| Engineering/Product | Real-time | Dashboard, alerts | Performance, drift, violations |
| Finance | Quarterly | PDF, dashboard | Spend, value, cost avoidance |
| Public | Annual | Web, PDF | Commitments, incidents, trust index |

### 7.5 Dashboard Design Principles

1. **Design for decisions, not display**: Every metric has an identified decision, owner, threshold, and response path
2. **Never publish a number without its denominator**: A percentage without complete scope can improve while unmanaged uses disappear
3. **Every threshold has an owner and response**: A crossed limit starts a named decision clock
4. **Use leading and lagging indicators**: Open findings, expired approvals (leading); audit findings, breaches (lagging)
5. **Event-driven escalation**: Incidents, approval bypasses, material changes should not wait for monthly presentation
6. **Protect against gaming**: Review exclusions, reclassification, owner changes, closed records without proof

---

## 8. Metric Quality Assurance

### 8.1 Evidence Standards

Every metric must satisfy four evidence criteria (adapted from Qapitol):

| Criterion | Definition | Verification Method |
|-----------|------------|---------------------|
| Outcome-referenced | Tied to a risk tolerance or compliance threshold, not just a count | Threshold review |
| Independently verifiable | Not sourced exclusively from the team being assessed | Cross-source validation |
| Escalation-defined | Has a threshold that triggers a specific action | Escalation procedure review |
| Ownership-assigned | Has a named role accountable for measurement accuracy | RACI review |

### 8.2 Data Quality Checks

#### 8.2.1 Automated Validation

| Check | Frequency | Action on Failure |
|-------|-----------|-------------------|
| Schema validation | Per data ingestion | Reject invalid records, alert data steward |
| Range validation | Per data ingestion | Flag out-of-range values for review |
| Completeness check | Daily | Alert owner if completeness <95% |
| Cross-source reconciliation | Daily | Flag discrepancies for investigation |
| Timeliness check | Hourly | Alert if data latency >1 hour |
| Duplicate detection | Daily | Merge duplicates, alert data steward |

#### 8.2.2 Manual Validation

| Check | Frequency | Responsible Party |
|-------|-----------|-------------------|
| Metric calculation audit | Quarterly | Internal Audit |
| Data source sampling | Monthly | AI Governance Lead |
| Threshold relevance review | Semi-annually | AI Governance Committee |
| Metric ownership review | Semi-annually | CAIO |
| Framework mapping review | Annually | Compliance |

### 8.3 Metric Governance

#### 8.3.1 Metric Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Define  │ →  │  Deploy  │ →  │  Measure │ →  │  Review  │
│          │    │          │    │          │    │          │
│ • Formula│    │ • Data   │    │ • Collect│    │ • Audit  │
│ • Source │    │   source │    │ • Calc   │    │ • Validate│
│ • Owner  │    │ • Pipeline│   │ • Report │    │ • Improve│
│ • Target │    │ • Dashboard│  │ • Alert  │    │ • Retire │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

#### 8.3.2 Metric Change Management

| Change Type | Approval Required | Notice Period |
|-------------|-------------------|---------------|
| New metric | AI Governance Committee | 30 days |
| Formula change | AI Risk Officer + CAIO | 30 days |
| Threshold change | AI Governance Committee | 30 days |
| Data source change | AI Risk Officer | 15 days |
| Owner change | CAIO | 15 days |
| Metric retirement | AI Governance Committee | 60 days |
| Emergency threshold change | AI Risk Officer | 24 hours |

#### 8.3.3 Metric Registry

All metrics are registered in a central metric registry with:

| Field | Description |
|-------|-------------|
| Metric ID | Unique identifier (e.g., UC1-001) |
| Name | Human-readable name |
| Category | UC-1 through UC-8, AG |
| Definition | Precise definition |
| Formula | Calculation formula |
| Data Source | Source system(s) |
| Collection Method | How data is collected |
| Frequency | Measurement frequency |
| Owner | Named accountable person |
| Validator | Independent validator |
| Target | Target value |
| Thresholds | T1, T2, T3 values |
| Standards Mapping | ISO, NIST, EU AI Act mappings |
| Framework Mapping | Source framework references |
| Version | Current version |
| Status | Active, deprecated, retired |
| Last Review | Date of last review |
| Next Review | Date of next review |

### 8.4 Metric Audit Program

#### 8.4.1 Internal Audit

| Audit Type | Frequency | Scope | Responsible |
|------------|-----------|-------|-------------|
| Metric calculation audit | Quarterly | Sample of 10 metrics | Internal Audit |
| Data source audit | Semi-annually | All data sources | Internal Audit |
| Threshold effectiveness | Annually | All thresholds | AI Governance Committee |
| Metric ownership | Annually | All metric owners | CAIO |
| Framework mapping | Annually | All mappings | Compliance |

#### 8.4.2 Audit Procedures

1. **Planning**: Define audit scope, criteria, and schedule
2. **Evidence Collection**: Gather metric calculations, data sources, and reports
3. **Testing**: Recalculate metrics from source data, verify accuracy
4. **Evaluation**: Compare results to reported values, identify discrepancies
5. **Reporting**: Document findings, recommendations, and action plans
6. **Follow-up**: Track remediation of audit findings

#### 8.4.3 Audit Findings Classification

| Severity | Definition | Response Time |
|----------|------------|---------------|
| Critical | Metric is fundamentally wrong or misleading | 24 hours |
| Major | Metric calculation error affecting decisions | 7 days |
| Minor | Metric presentation or documentation issue | 30 days |
| Observation | Improvement opportunity | Next review cycle |

### 8.5 Metric Quality Metrics

Meta-metrics to measure the quality of the metrics program itself:

| Metric | Formula | Target |
|--------|---------|--------|
| Metric completeness | (Metrics with complete data / Total metrics) × 100 | ≥95% |
| Metric accuracy | (Metrics passing audit / Metrics audited) × 100 | ≥98% |
| Metric timeliness | (Metrics reported on time / Total metrics) × 100 | ≥95% |
| Metric ownership coverage | (Metrics with named owner / Total metrics) × 100 | 100% |
| Metric threshold coverage | (Metrics with defined thresholds / Total metrics) × 100 | 100% |
| Metric documentation coverage | (Metrics with complete documentation / Total metrics) × 100 | 100% |
| Escalation response time | Avg time from threshold breach to acknowledgment | Per SLA |
| Audit finding closure rate | (Findings closed / Total findings) × 100 | ≥90% |

### 8.6 Continuous Improvement

#### 8.6.1 Improvement Cycle

1. **Monitor**: Track metric quality metrics monthly
2. **Identify**: Identify metrics with quality issues
3. **Analyze**: Root cause analysis of quality issues
4. **Improve**: Implement corrective actions
5. **Verify**: Validate improvement effectiveness
6. **Standardize**: Update procedures and documentation

#### 8.6.2 Improvement Triggers

| Trigger | Action |
|---------|--------|
| Metric accuracy <95% | Root cause analysis + corrective action |
| Metric completeness <90% | Data source investigation + fix |
| Audit finding rate >10% | Process review + training |
| Escalation response time >SLA | Process review + automation |
| Stakeholder feedback | Metric review + adjustment |

---

## 9. Appendices

### Appendix A: Metric ID Quick Reference

| ID | Metric | Category | Layer |
|----|--------|----------|-------|
| UC1-001 | AI System Inventory Coverage | Asset Inventory | Technical |
| UC1-002 | High-Risk Systems Under Governance | Asset Inventory | Technical |
| UC1-003 | Agent Identity Coverage | Asset Inventory | Technical |
| UC1-004 | Business Unit Participation | Asset Inventory | Technical |
| UC1-005 | Vendor Coverage | Asset Inventory | Technical |
| UC2-001 | Risk Assessments Complete | Risk & Compliance | Management |
| UC2-002 | Open High-Risk Findings | Risk & Compliance | Management |
| UC2-003 | Regulatory Alignment Score | Risk & Compliance | Board |
| UC2-004 | Policy Adherence Rate | Risk & Compliance | Management |
| UC2-005 | Policy-to-Enforcement Gap | Risk & Compliance | Management |
| UC2-006 | Audit Findings | Risk & Compliance | Management |
| UC3-001 | Model Accuracy / F1 Score | Operational Performance | Technical |
| UC3-002 | Model Drift Detection | Operational Performance | Technical |
| UC3-003 | System Availability / Uptime | Operational Performance | Technical |
| UC3-004 | Response Time (P95/P99) | Operational Performance | Technical |
| UC3-005 | Human Override Rate | Operational Performance | Technical |
| UC4-001 | AI Incidents (by severity) | Incident Management | Management |
| UC4-002 | Mean Time to Detect (MTTD) | Incident Management | Management |
| UC4-003 | Mean Time to Resolve (MTTR) | Incident Management | Management |
| UC4-004 | Incidents Resolved Within SLA | Incident Management | Management |
| UC4-005 | Recurring Incidents | Incident Management | Management |
| UC4-006 | Root Cause Analysis Completion | Incident Management | Management |
| UC5-001 | Remediation Velocity (Median Days) | Remediation | Management |
| UC5-002 | Remediation Velocity (Critical) | Remediation | Board |
| UC5-003 | Governance Committee Throughput | Remediation | Management |
| UC5-004 | Governance ROI | Remediation | Board |
| UC5-005 | Maturity Level (Self-Assessed) | Remediation | Management |
| UC6-001 | Third-Party AI Risk Exposure | Third-Party Risk | Board |
| UC6-002 | Vendor Assessment Turnaround | Third-Party Risk | Management |
| UC6-003 | Fourth-Party Risk Exposure | Third-Party Risk | Management |
| UC6-004 | Vendor Due Diligence Coverage | Third-Party Risk | Management |
| UC7-001 | AI Value Delivered | Economic Value | Board |
| UC7-002 | Cost Avoidance from Risk Prevention | Economic Value | Management |
| UC7-003 | AI Spend Allocation Rate | Economic Value | Management |
| UC7-004 | Shadow AI Spend Ratio | Economic Value | Management |
| UC7-005 | AI Initiative Ownership Rate | Economic Value | Management |
| UC8-001 | Training Completion Rate | Culture & Training | Management |
| UC8-002 | Assessment Pass Rate | Culture & Training | Management |
| UC8-003 | Awareness Survey Scores | Culture & Training | Management |
| UC8-004 | Reported Concerns | Culture & Training | Management |
| AG-001 | Goal Accuracy | Agentic AI | Cross-cutting |
| AG-002 | Plan Adherence | Agentic AI | Cross-cutting |
| AG-003 | Hallucination Rate | Agentic AI | Cross-cutting |
| AG-004 | Human Intervention Rate | Agentic AI | Cross-cutting |
| AG-005 | Escalation Frequency | Agentic AI | Cross-cutting |
| AG-006 | Autonomous Resolution Rate | Agentic AI | Cross-cutting |
| AG-007 | Policy Violation Rate | Agentic AI | Cross-cutting |
| AG-008 | Permission Escalation Events | Agentic AI | Cross-cutting |
| AG-009 | Tool Abuse Incidents | Agentic AI | Cross-cutting |
| AG-010 | Cost per Successful Task | Agentic AI | Cross-cutting |
| AG-011 | Value Generated per Agent | Agentic AI | Cross-cutting |
| AG-012 | Agent Identity Coverage | Agentic AI | Cross-cutting |

### Appendix B: Glossary

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

### Appendix C: Standards Mapping Summary

| Standard | Clauses/Articles Mapped | Metrics Mapped |
|----------|------------------------|----------------|
| ISO/IEC 42001:2023 | 4.1, 5.1, 6.1, 6.2, 7.2, 7.3, 8.1-8.7, 9.1, 9.2, 10.1, 10.2 | 25+ metrics |
| NIST AI RMF 1.0 | GOVERN 1-6, MAP 1-5, MEASURE 1-4, MANAGE 1-4 | 30+ metrics |
| EU AI Act | Art. 9, 10, 11, 12, 13, 14, 15, 17, 72, 73, 99 | 20+ metrics |

### Appendix D: Framework Source URLs

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

---

*End of document*
