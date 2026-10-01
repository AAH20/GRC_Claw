# GRC_Claw Metrics Layer: Detailed Definitions & Measurement Methodology

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** GRC_Claw Research  
**Status:** Draft for Review  
**References:** grc-claw-unified-metrics-layer.md, grc-claw-reporting-engine-analysis.md

---

## 1. Purpose & Scope

This document expands the GRC_Claw Unified Metrics Layer (8 categories, 40 metrics, 12 agentic AI metrics) with operational-grade detail across six dimensions:

1. **Metric Calculation Formulas** — precise mathematical definitions with numerator/denominator scoping
2. **Data Collection Methods** — specific tools, APIs, and processes for evidence gathering
3. **Measurement Frequency** — calculation cadence and reporting cadence
4. **Threshold Definitions** — Tier 1/2/3 escalation triggers with exact values
5. **Escalation Procedures** — notification chains, response requirements, and timelines
6. **Metric Reporting & Visualization** — dashboard placement, format, and audience

### Metric ID Convention

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

## 2. UC-1: Asset Inventory & Coverage (5 Metrics)

### UC1-001: AI System Inventory Coverage

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of production AI systems registered in the AI asset registry with a named owner and risk classification |
| **Formula** | `(Registered AI systems with named owner AND risk classification / Total discovered AI systems in production) × 100` |
| **Numerator Scope** | Systems in AI Asset Registry where `owner != null` AND `risk_classification IN (low, medium, high, critical)` AND `lifecycle_stage = production` |
| **Denominator Scope** | All AI systems discovered via automated scanning (CI/CD pipeline hooks, cloud API enumeration, network traffic analysis) plus manually registered systems, filtered to `lifecycle_stage = production` |
| **Data Collection** | Automated discovery via: (1) CI/CD pipeline plugins scanning for model artifacts, (2) Cloud resource APIs (AWS SageMaker, Azure ML, GCP Vertex AI) enumerating deployed endpoints, (3) Network egress analysis detecting API calls to LLM providers, (4) Manual registration via GRC_Claw intake form. Discovery runs daily; registry reconciliation runs hourly. |
| **Measurement Frequency** | **Calculation:** Continuous (real-time registry state) **Reporting:** Daily snapshot to data warehouse; monthly trend report |
| **Target** | 100% |
| **Thresholds** | **Tier 1 (Operational):** <90% — System owner notified, 72-hour remediation **Tier 2 (Management):** <85% — AI Risk Officer notified, remediation plan required within 14 days **Tier 3 (Board):** <80% OR any unassured high-risk system — Board risk committee notified, mandatory remediation at next board meeting |
| **Escalation Procedure** | Tier 1: Automated email to system owner + engineering lead. Re-calculate in 72h. If still <90%, auto-escalate to Tier 2. Tier 2: AI Risk Officer convenes remediation sprint. Weekly tracking until >90%. If still <85% after 14 days, auto-escalate to Tier 3. Tier 3: Board agenda item. CAIO presents remediation plan. Monthly board updates until resolved. |
| **Reporting & Visualization** | **Dashboard:** Executive (headline number + trend), Program (by business unit, by risk tier), Operating (system-level detail with owner, classification, last-seen timestamp) **Format:** Percentage gauge with RAG status; trend line (90/180/365-day); heatmap by BU **Audience:** Board (quarterly), CAIO (monthly), Engineering (real-time) |

### UC1-002: High-Risk Systems Under Governance

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of high-risk AI systems (per risk classification) that are under active governance (assessment complete, controls implemented, monitoring active) |
| **Formula** | `(High-risk systems with complete risk assessment AND implemented controls AND active monitoring / Total high-risk systems) × 100` |
| **Numerator Scope** | Systems where `risk_classification = high` AND `risk_assessment_status = complete` AND `control_implementation_status = implemented` AND `monitoring_status = active` |
| **Denominator Scope** | All systems with `risk_classification = high` in the AI Asset Registry |
| **Data Collection** | Risk assessment status from GRC Platform (ServiceNow GRC/Archer). Control implementation status from control mapping engine. Monitoring status from observability stack (Arize/Fiddler/Datadog) heartbeat check. All sources queried via API every 6 hours. |
| **Measurement Frequency** | **Calculation:** Every 6 hours **Reporting:** Weekly summary to AI Risk Officer; monthly to Governance Committee |
| **Target** | 100% |
| **Thresholds** | **Tier 1:** <95% — AI Risk Officer notified, 72-hour assessment **Tier 2:** <90% — CAIO notified, remediation plan within 14 days **Tier 3:** <85% OR any high-risk system without assessment >30 days — Board notification |
| **Escalation Procedure** | Tier 1: Auto-create assessment tickets for non-compliant systems. Tier 2: CAIO reviews weekly. Unassured systems get executive sponsor assigned. Tier 3: Board risk committee briefing. Systems without governance may be recommended for decommission. |
| **Reporting & Visualization** | **Dashboard:** Program (primary), Executive (summary count) **Format:** RAG status per system; count of unassured high-risk systems; aging report (days without assessment) **Audience:** AI Risk Officer (weekly), CAIO (monthly), Board (quarterly) |

### UC1-003: Agent Identity Coverage

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of discovered AI agents with a unique non-human identity (NHI), named owner, and registered in the agent registry |
| **Formula** | `(Agents with unique NHI AND named owner AND registered / Total discovered agents) × 100` |
| **Numerator Scope** | Agents in Agent Registry where `nhi_assigned = true` AND `owner != null` AND `registration_status = active` |
| **Denominator Scope** | All agents discovered via: (1) Agent framework telemetry (LangChain, AutoGen, CrewAI), (2) API gateway logs identifying autonomous tool-calling patterns, (3) Cloud resource enumeration detecting agent compute instances |
| **Data Collection** | Agent discovery via: (1) Framework-level hooks exporting agent metadata, (2) API gateway pattern matching (repeated tool calls with decision loops), (3) Infrastructure scanning for agent runtime containers. Identity assignment via NHI vault (SPIFFE/SPIRE or cloud IAM). Registry sync every 4 hours. |
| **Measurement Frequency** | **Calculation:** Every 4 hours **Reporting:** Weekly to CISO; monthly to CAIO |
| **Target** | 100% |
| **Thresholds** | **Tier 1:** <90% — CISO notified, 72-hour identity assignment **Tier 2:** <80% — CAIO notified, remediation plan within 14 days **Tier 3:** <70% OR any agent with production access without identity — Board notification, potential agent suspension |
| **Escalation Procedure** | Tier 1: Auto-assign NHI via vault. Notify engineering team. Tier 2: CAIO reviews agent inventory. Unregistered agents flagged for decommission review. Tier 3: Board briefing. Agents without identity in production may be suspended pending registration. |
| **Reporting & Visualization** | **Dashboard:** Operating (agent-level detail), Program (by agent type, by environment) **Format:** Percentage with RAG; agent inventory table with identity status; trend line **Audience:** CISO (weekly), CAIO (monthly), Engineering (real-time) |

### UC1-004: Business Unit Participation

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of business units with a designated AI liaison responsible for AI governance coordination |
| **Formula** | `(BUs with designated AI liaison / Total business units) × 100` |
| **Numerator Scope** | BUs where `ai_liaison != null` AND `liaison_acknowledged = true` (confirmed role acceptance) |
| **Denominator Scope** | All business units in the organizational chart (HR system of record) |
| **Data Collection** | Org chart from HR system (Workday/SAP SuccessFactors). Liaison designation from GRC_Claw role management. Acknowledgment tracked via attestation workflow. Synced daily. |
| **Measurement Frequency** | **Calculation:** Daily **Reporting:** Monthly to CAIO |
| **Target** | 100% |
| **Thresholds** | **Tier 1:** <90% — CAIO notifies BU leader **Tier 2:** <80% — CEO notification for non-participating BUs **Tier 3:** <70% — Board governance committee notification |
| **Escalation Procedure** | Tier 1: CAIO office sends liaison designation request to BU leader. Tier 2: CEO escalates to BU leadership. Tier 3: Board governance committee addresses as organizational gap. |
| **Reporting & Visualization** | **Dashboard:** Program (by BU) **Format:** Org chart overlay showing liaison coverage; RAG by BU **Audience:** CAIO (monthly), Board (quarterly) |

### UC1-005: Vendor Coverage

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of third-party AI vendors with completed due diligence assessment |
| **Formula** | `(Vendors with completed due diligence / Total AI vendors in production use) × 100` |
| **Numerator Scope** | Vendors where `due_diligence_status = complete` AND `dd_date within 12 months` |
| **Denominator Scope** | All third-party AI vendors identified from: (1) Vendor management system, (2) AI system registry (model_provider field), (3) Procurement records, (4) API gateway logs (external AI API calls) |
| **Data Collection** | Vendor inventory from Vendor Management System (Coupa/SAP Ariba). AI-specific vendor identification from AI Asset Registry and API gateway logs. Due diligence status from GRC Platform workflow. Synced daily. |
| **Measurement Frequency** | **Calculation:** Daily **Reporting:** Monthly to CPO; quarterly to Board |
| **Target** | 100% |
| **Thresholds** | **Tier 1:** <90% — CPO notified, 72-hour DD initiation **Tier 2:** <80% — CAIO + CPO joint remediation **Tier 3:** <70% OR any high-risk vendor without DD >30 days — Board notification |
| **Escalation Procedure** | Tier 1: Auto-create DD workflow. Tier 2: Joint CPO/CAIO review. Tier 3: Board risk committee. High-risk vendors without DD may be recommended for contract review. |
| **Reporting & Visualization** | **Dashboard:** Program (by vendor risk tier), Operating (vendor-level detail) **Format:** Percentage with RAG; vendor risk matrix; aging report **Audience:** CPO (monthly), Board (quarterly) |

---

## 3. UC-2: Risk & Compliance Posture (6 Metrics)

### UC2-001: Risk Assessments Complete

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of in-scope AI systems with completed risk assessments |
| **Formula** | `(Systems with completed risk assessment / Total in-scope systems) × 100` |
| **Numerator Scope** | Systems where `risk_assessment_status = complete` AND `assessment_date within 12 months` |
| **Denominator Scope** | All systems in AI Asset Registry where `lifecycle_stage IN (development, staging, production)` AND `risk_classification != exempt` |
| **Data Collection** | Risk assessment status from GRC Platform. Assessment completion tracked via workflow (intake → assessment → review → approval). Automated reminders at 30/60/90 days. API query every 6 hours. |
| **Measurement Frequency** | **Calculation:** Every 6 hours **Reporting:** Weekly to AI Risk Officer; monthly to Governance Committee |
| **Target** | 100% |
| **Thresholds** | **Tier 1:** <90% — AI Risk Officer notified **Tier 2:** <80% — CAIO notified, remediation plan **Tier 3:** <70% OR any high-risk system without assessment >60 days — Board notification |
| **Escalation Procedure** | Tier 1: Auto-notify system owners with overdue assessments. Tier 2: CAIO reviews weekly. Tier 3: Board briefing. Systems without assessments may be blocked from deployment. |
| **Reporting & Visualization** | **Dashboard:** Program (primary), Executive (summary) **Format:** RAG status; aging report (days since last assessment); trend by risk tier **Audience:** AI Risk Officer (weekly), CAIO (monthly), Board (quarterly) |

### UC2-002: Open High-Risk Findings

| Dimension | Detail |
|-----------|--------|
| **Definition** | Count of open critical and high-severity findings from risk assessments, audits, and incident reviews |
| **Formula** | `COUNT(findings WHERE severity IN (critical, high) AND status = open)` |
| **Scope** | All findings from: (1) Risk assessments, (2) Internal/external audits, (3) Incident root cause analyses, (4) Red team exercises, (5) Regulatory examinations |
| **Data Collection** | Findings aggregated from: GRC Platform (risk findings), Audit management system, Incident management system (ServiceNow/Jira), Red team reports. All findings tagged with severity and status. Real-time sync via API. |
| **Measurement Frequency** | **Calculation:** Real-time **Reporting:** Daily to AI Risk Officer; weekly to CAIO; monthly to Governance Committee |
| **Target** | 0 |
| **Thresholds** | **Tier 1:** >5 open high-risk findings — AI Risk Officer reviews **Tier 2:** >10 open — CAIO notified, remediation plan **Tier 3:** >20 open OR any critical finding open >30 days — Board notification |
| **Escalation Procedure** | Tier 1: Weekly review meeting. Tier 2: CAIO assigns executive sponsors to each finding. Tier 3: Board risk committee briefing. Critical findings >30 days may trigger system suspension recommendation. |
| **Reporting & Visualization** | **Dashboard:** Program (primary), Executive (count + trend) **Format:** Count with RAG; aging histogram; findings by source; trend line **Audience:** AI Risk Officer (daily), CAIO (weekly), Board (monthly) |

### UC2-003: Regulatory Alignment Score

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of applicable regulatory/standards requirements with current, verifiable evidence |
| **Formula** | `(Requirements with current verifiable evidence / Total applicable requirements) × 100` |
| **Numerator Scope** | Requirements where `evidence_status = current` AND `evidence_date within required_freshness_period` AND `verification_status = verified` |
| **Denominator Scope** | All requirements from applicable frameworks: EU AI Act (Annex III systems), ISO 42001, NIST AI RMF, SOC 2, GDPR, industry-specific regulations. Mapped via Framework Mapping Engine. |
| **Data Collection** | Evidence status from Evidence Store. Freshness rules per requirement type (e.g., model evaluation: 6 months, risk assessment: 12 months, training records: 12 months). Verification status from Internal Audit review workflow. Recalculated on evidence upload. |
| **Measurement Frequency** | **Calculation:** On evidence upload (event-driven) + weekly batch **Reporting:** Monthly to CCO; quarterly to Board; on-demand for regulators |
| **Target** | 100% |
| **Thresholds** | **Tier 1:** <85% — CCO notified **Tier 2:** <80% — CAIO + CCO joint remediation **Tier 3:** <75% OR >5pp decline between periods — Board notification |
| **Escalation Procedure** | Tier 1: CCO identifies gaps, assigns owners. Tier 2: Joint remediation plan. Tier 3: Board briefing. Regulatory deadlines approaching trigger accelerated remediation. |
| **Reporting & Visualization** | **Dashboard:** Executive (by framework), Program (by regulation), Operating (by requirement) **Format:** Compliance score by framework with RAG; gap analysis; trend line; regulatory deadline tracker **Audience:** CCO (monthly), Board (quarterly), Regulators (on-demand) |

### UC2-004: Policy Adherence Rate

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of AI projects passing mandatory pre-deployment governance review |
| **Formula** | `(Projects passing pre-deployment review / Total projects entering review) × 100` |
| **Numerator Scope** | Projects where `review_outcome = pass` AND `review_type = pre-deployment` |
| **Denominator Scope** | All projects that entered the pre-deployment review workflow in the measurement period |
| **Data Collection** | Review outcomes from GRC Platform workflow. Projects tracked from intake to deployment. Automated policy checks (CI/CD gates) + manual review board. Data synced per workflow state change. |
| **Measurement Frequency** | **Calculation:** Per review completion **Reporting:** Monthly to AI Governance Lead; quarterly to CAIO |
| **Target** | ≥95% |
| **Thresholds** | **Tier 1:** <90% — AI Governance Lead reviews **Tier 2:** <85% — CAIO notified **Tier 3:** <80% — Board notification, potential deployment freeze |
| **Escalation Procedure** | Tier 1: Review common failure patterns. Tier 2: CAIO reviews policy clarity and training adequacy. Tier 3: Board considers policy revision or deployment moratorium. |
| **Reporting & Visualization** | **Dashboard:** Program (primary) **Format:** Percentage with RAG; pass/fail by policy area; trend by quarter; common failure reasons **Audience:** AI Governance Lead (monthly), CAIO (quarterly) |

### UC2-005: Policy-to-Enforcement Gap

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of AI policy statements with corresponding technical controls implemented and verified |
| **Formula** | `(Policy statements with verified technical control / Total policy statements) × 100` |
| **Numerator Scope** | Policy statements where `technical_control EXISTS` AND `control_verification_status = verified` |
| **Denominator Scope** | All statements in the AI policy document set (acceptable use, data handling, access control, model management, incident response) |
| **Data Collection** | Policy statements from Policy Management System. Technical controls from control mapping engine (1,026+ pre-seeded controls). Verification from automated control testing + manual audit. Mapping maintained in Framework Mapping Engine. |
| **Measurement Frequency** | **Calculation:** Monthly **Reporting:** Quarterly to CISO; semi-annually to Board |
| **Target** | 100% |
| **Thresholds** | **Tier 1:** <90% — CISO notified **Tier 2:** <80% — CAIO + CISO joint remediation **Tier 3:** <70% — Board notification |
| **Escalation Procedure** | Tier 1: CISO identifies gaps, assigns control owners. Tier 2: Joint remediation plan. Tier 3: Board briefing on policy enforcement gaps. |
| **Reporting & Visualization** | **Dashboard:** Program (by policy domain) **Format:** Percentage with RAG; policy-to-control mapping matrix; gap list **Audience:** CISO (quarterly), Board (semi-annually) |

### UC2-006: Audit Findings

| Dimension | Detail |
|-----------|--------|
| **Definition** | Count of findings from internal and external audits per year |
| **Formula** | `COUNT(audit_findings WHERE audit_date IN current_year)` |
| **Scope** | All findings from: (1) Internal audit (ISO 42001, SOC 2), (2) External audit (customer, regulatory), (3) Penetration tests, (4) Red team exercises |
| **Data Collection** | Findings from Audit Management System. Each finding tagged with: audit type, severity, status, remediation target date. Synced per audit completion. |
| **Measurement Frequency** | **Calculation:** Per audit completion **Reporting:** Per audit cycle; annual summary to Board |
| **Target** | ≤2 per year |
| **Thresholds** | **Tier 1:** >2 findings — AI Risk Officer reviews **Tier 2:** >5 findings — CAIO notified **Tier 3:** >10 findings OR any critical finding — Board notification |
| **Escalation Procedure** | Tier 1: Root cause analysis for each finding. Tier 2: CAIO reviews systemic issues. Tier 3: Board briefing on audit posture and remediation progress. |
| **Reporting & Visualization** | **Dashboard:** Program (by audit, by severity), Executive (annual trend) **Format:** Count with RAG; findings by audit type; remediation status; trend by year **Audience:** Internal Audit (per audit), CAIO (annual), Board (annual) |

---

## 4. UC-3: Operational Performance & Reliability (5 Metrics)

### UC3-001: Model Accuracy / F1 Score

| Dimension | Detail |
|-----------|--------|
| **Definition** | Standard ML performance metrics (accuracy, F1, precision, recall) for production models, measured against approved baselines |
| **Formula** | `Accuracy = (TP + TN) / (TP + TN + FP + FN)` ; `F1 = 2 × (Precision × Recall) / (Precision + Recall)` where `Precision = TP / (TP + FP)` and `Recall = TP / (TP + FN)` |
| **Scope** | All production models with approved baselines. Metrics computed on held-out evaluation sets and production traffic samples. |
| **Data Collection** | Evaluation pipeline (CI/CD) computes metrics on deployment. Production metrics computed via: (1) Shadow deployment comparison, (2) Human-labeled sample sets (weekly), (3) LLM-as-judge evaluation for generative models. Data from MLflow/W&B experiment tracking. |
| **Measurement Frequency** | **Calculation:** Per deployment (automated) + weekly production sampling **Reporting:** Per deployment; monthly trend to ML Engineering |
| **Target** | Per model baseline (defined at approval) |
| **Thresholds** | **Tier 1:** >2% degradation from baseline — ML Engineer notified **Tier 2:** >5% degradation — AI Risk Officer + ML Engineer joint review **Tier 3:** >10% degradation OR any critical model below baseline — Board notification, potential model rollback |
| **Escalation Procedure** | Tier 1: Automated alert. ML Engineer investigates. Tier 2: Joint review. Model may be rolled back to previous version. Tier 3: Board briefing. Model may be suspended pending retraining. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-model), Program (by model type, by risk tier) **Format:** Metric value vs baseline with RAG; trend line; distribution chart **Audience:** ML Engineering (real-time), AI Risk Officer (weekly) |

### UC3-002: Model Drift Detection

| Dimension | Detail |
|-----------|--------|
| **Definition** | Detection of statistical drift in model inputs, outputs, or performance over time |
| **Formula** | **PSI (Population Stability Index):** `Σ (Actual% - Expected%) × ln(Actual% / Expected%)` per feature bin. **KL Divergence:** `Σ P(x) × ln(P(x) / Q(x))` where P = reference distribution, Q = current distribution. **Accuracy Delta:** `Current accuracy - Baseline accuracy` |
| **Scope** | All production models with monitoring enabled. Features, predictions, and performance metrics tracked. |
| **Data Collection** | Drift detection via: (1) Arize/Fiddler monitoring platform computing PSI and KL divergence on feature distributions, (2) Prediction distribution monitoring, (3) Performance metric tracking against baseline. Computed on sliding windows (7-day, 30-day). |
| **Measurement Frequency** | **Calculation:** Continuous (streaming) with daily batch aggregation **Reporting:** Daily drift report; weekly summary to ML Engineering |
| **Target** | <0.5% drift (PSI < 0.1, accuracy delta < 0.5%) |
| **Thresholds** | **Tier 1:** PSI > 0.1 OR accuracy delta > 0.5% — ML Engineer notified **Tier 2:** PSI > 0.2 OR accuracy delta > 1% — AI Risk Officer notified **Tier 3:** PSI > 0.3 OR accuracy delta > 2% — Board notification, potential model suspension |
| **Escalation Procedure** | Tier 1: Automated alert. ML Engineer investigates data quality. Tier 2: Joint review. Retraining may be initiated. Tier 3: Board briefing. Model may be suspended pending retraining and re-evaluation. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-feature, per-model), Program (drift heatmap) **Format:** PSI/KL values with RAG; drift trend line; feature-level drift breakdown **Audience:** ML Engineering (daily), AI Risk Officer (weekly) |

### UC3-003: System Availability / Uptime

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of time AI systems are available and responding within SLO |
| **Formula** | `(Total time - Downtime) / Total time × 100` where Downtime = periods where system is unresponsive OR error rate > 5% |
| **Scope** | All production AI systems with defined SLOs. Measured per endpoint/API. |
| **Data Collection** | Uptime monitoring via: (1) Infrastructure monitoring (Datadog/Prometheus), (2) API health checks (synthetic monitoring), (3) Error rate tracking from application logs. Aggregated per system per day. |
| **Measurement Frequency** | **Calculation:** Continuous **Reporting:** Daily to SRE; monthly to AI Risk Officer |
| **Target** | ≥99.5% |
| **Thresholds** | **Tier 1:** <99.5% — SRE notified **Tier 2:** <99% — AI Risk Officer + SRE joint review **Tier 3:** <98% OR any critical system <99% — Board notification |
| **Escalation Procedure** | Tier 1: SRE investigates. Incident created if needed. Tier 2: Joint review. Capacity/scaling changes. Tier 3: Board briefing. Vendor SLA review if applicable. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-system), Program (by system tier) **Format:** Uptime percentage with RAG; SLA compliance; incident correlation **Audience:** SRE (daily), AI Risk Officer (monthly) |

### UC3-004: Response Time (P95/P99)

| Dimension | Detail |
|-----------|--------|
| **Definition** | Latency percentiles (P95, P99) for AI system responses |
| **Formula** | `P95 = value below which 95% of response times fall` ; `P99 = value below which 99% of response times fall` |
| **Scope** | All production AI systems with defined latency SLOs. |
| **Data Collection** | Latency metrics from: (1) Application performance monitoring (Datadog APM), (2) API gateway logs, (3) Model serving infrastructure metrics. Computed on rolling 24-hour windows. |
| **Measurement Frequency** | **Calculation:** Continuous **Reporting:** Daily to SRE; monthly to AI Risk Officer |
| **Target** | Per SLO (defined per system) |
| **Thresholds** | **Tier 1:** P95 > SLO — SRE notified **Tier 2:** P99 > SLO × 1.5 — AI Risk Officer notified **Tier 3:** P99 > SLO × 2 OR sustained degradation >24h — Board notification |
| **Escalation Procedure** | Tier 1: SRE investigates performance. Tier 2: Joint review. Optimization or scaling. Tier 3: Board briefing. Vendor escalation if applicable. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-system), Program (by system tier) **Format:** Latency percentiles with RAG; trend line; SLO compliance **Audience:** SRE (daily), AI Risk Officer (monthly) |

### UC3-005: Human Override Rate

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of AI-influenced decisions that are overridden by human reviewers |
| **Formula** | `(Decisions overridden by human / Total AI-influenced decisions) × 100` |
| **Scope** | All AI systems with human-in-the-loop oversight. Decisions logged with override flag. |
| **Data Collection** | Override events from: (1) Application decision logs, (2) Human review workflow systems, (3) Feedback mechanisms in AI applications. Logged per decision with timestamp, reviewer ID, and override reason. |
| **Measurement Frequency** | **Calculation:** Real-time aggregation **Reporting:** Weekly to Business Owner; monthly to AI Risk Officer |
| **Target** | Per risk tier (low: <5%, medium: <10%, high: <20%, critical: <30%) |
| **Thresholds** | **Tier 1:** Override rate > target + 5pp — Business Owner notified **Tier 2:** Override rate > target + 10pp — AI Risk Officer notified **Tier 3:** Override rate > target + 20pp OR any critical system >50% — Board notification |
| **Escalation Procedure** | Tier 1: Business Owner reviews override reasons. Tier 2: Joint review. Model retraining or threshold adjustment. Tier 3: Board briefing. System may be suspended pending review. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-system), Program (by risk tier) **Format:** Override rate with RAG; override reason breakdown; trend line **Audience:** Business Owner (weekly), AI Risk Officer (monthly) |

---

## 5. UC-4: Incident & Exception Management (6 Metrics)

### UC4-001: AI Incidents (by severity)

| Dimension | Detail |
|-----------|--------|
| **Definition** | Count of AI-related incidents categorized by severity (critical, high, medium, low) |
| **Formula** | `COUNT(incidents WHERE incident_type = AI-related AND period = measurement_period) GROUP BY severity` |
| **Scope** | All incidents where AI system behavior contributed to or caused the incident. Includes: model failures, data breaches involving AI, AI-generated harmful output, agent misbehavior, security exploits of AI systems. |
| **Data Collection** | Incidents from: (1) Incident Management System (ServiceNow), (2) Security incident response (SIEM/SOAR), (3) Customer complaints escalated to incidents, (4) Automated monitoring alerts meeting incident criteria. Each incident tagged with AI involvement flag. |
| **Measurement Frequency** | **Calculation:** Real-time **Reporting:** Daily to AI Risk Officer; weekly to CAIO; monthly to Board |
| **Target** | Declining trend |
| **Thresholds** | **Tier 1:** >0 critical incidents — Immediate AI Risk Officer notification **Tier 2:** >1 critical OR >5 high in period — CAIO notified **Tier 3:** >3 critical OR any regulatory reportable — Board notification within 24h |
| **Escalation Procedure** | Tier 1: Immediate response. War room if critical. Tier 2: CAIO briefs executive team. Tier 3: Board notification. Regulatory reporting if applicable (EU AI Act Art. 73: 15/10/2-day clocks). |
| **Reporting & Visualization** | **Dashboard:** Executive (count + trend), Program (by severity, by system), Operating (incident register) **Format:** Incident count with RAG; trend line; severity distribution; MTTR correlation **Audience:** AI Risk Officer (daily), CAIO (weekly), Board (monthly) |

### UC4-002: Mean Time to Detect (MTTD)

| Dimension | Detail |
|-----------|--------|
| **Definition** | Average time from AI incident occurrence to detection |
| **Formula** | `AVG(detection_timestamp - occurrence_timestamp) WHERE incident_type = AI-related` |
| **Scope** | All AI-related incidents with reliable occurrence and detection timestamps. |
| **Data Collection** | Timestamps from: (1) Monitoring alert creation time (detection), (2) Log analysis estimating occurrence time, (3) Customer report time (if externally detected). Tracked in Incident Management System. |
| **Measurement Frequency** | **Calculation:** Per incident closure **Reporting:** Monthly to SRE; quarterly to AI Risk Officer |
| **Target** | <1 hour |
| **Thresholds** | **Tier 1:** MTTD > 1 hour — SRE reviews detection gaps **Tier 2:** MTTD > 4 hours — AI Risk Officer + SRE joint review **Tier 3:** MTTD > 24 hours OR any critical incident undetected >1h — Board notification |
| **Escalation Procedure** | Tier 1: Review monitoring coverage. Tier 2: Joint review of detection capabilities. Tier 3: Board briefing on detection gaps. Additional monitoring investment may be recommended. |
| **Reporting & Visualization** | **Dashboard:** Program (by system, by detection source) **Format:** MTTD with RAG; trend line; detection source breakdown **Audience:** SRE (monthly), AI Risk Officer (quarterly) |

### UC4-003: Mean Time to Resolve (MTTR)

| Dimension | Detail |
|-----------|--------|
| **Definition** | Average time from AI incident detection to resolution |
| **Formula** | `AVG(resolution_timestamp - detection_timestamp) WHERE incident_type = AI-related` |
| **Scope** | All resolved AI-related incidents. Resolution = root cause addressed AND service restored. |
| **Data Collection** | Timestamps from Incident Management System. Resolution confirmed by incident commander + system owner sign-off. |
| **Measurement Frequency** | **Calculation:** Per incident closure **Reporting:** Monthly to AI Risk Officer; quarterly to CAIO |
| **Target** | <4 hours |
| **Thresholds** | **Tier 1:** MTTR > 4 hours — AI Risk Officer reviews **Tier 2:** MTTR > 8 hours — CAIO notified **Tier 3:** MTTR > 24 hours OR any critical incident >12h — Board notification |
| **Escalation Procedure** | Tier 1: Review resolution process. Tier 2: CAIO reviews resource allocation. Tier 3: Board briefing. Process improvement initiative may be launched. |
| **Reporting & Visualization** | **Dashboard:** Program (by severity, by system) **Format:** MTTR with RAG; trend line; resolution phase breakdown **Audience:** AI Risk Officer (monthly), CAIO (quarterly) |

### UC4-004: Incidents Resolved Within SLA

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of AI incidents resolved within defined SLA |
| **Formula** | `(Incidents resolved within SLA / Total resolved incidents) × 100` |
| **Scope** | All resolved AI-related incidents with defined SLA targets. |
| **Data Collection** | SLA targets defined per severity (critical: 4h, high: 8h, medium: 24h, low: 72h). Resolution time from Incident Management System. SLA compliance calculated per incident. |
| **Measurement Frequency** | **Calculation:** Per incident closure **Reporting:** Monthly to AI Risk Officer |
| **Target** | ≥95% |
| **Thresholds** | **Tier 1:** <95% — AI Risk Officer reviews **Tier 2:** <90% — CAIO notified **Tier 3:** <85% OR any critical incident breaching SLA — Board notification |
| **Escalation Procedure** | Tier 1: Review SLA breach patterns. Tier 2: CAIO reviews resourcing. Tier 3: Board briefing. SLA revision or additional resourcing may be recommended. |
| **Reporting & Visualization** | **Dashboard:** Program (by severity) **Format:** SLA compliance percentage with RAG; breach reasons; trend line **Audience:** AI Risk Officer (monthly), CAIO (quarterly) |

### UC4-005: Recurring Incidents

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of incidents that are recurrences of previous incidents (same root cause or same system within 90 days) |
| **Formula** | `(Incidents with matching root cause OR same system within 90 days / Total incidents) × 100` |
| **Scope** | All AI-related incidents. Recurrence defined as: same root cause category OR same system with similar incident type within 90-day window. |
| **Data Collection** | Incident matching via: (1) Root cause category matching, (2) System + incident type matching within 90-day window, (3) Automated correlation rules in Incident Management System. |
| **Measurement Frequency** | **Calculation:** Per incident closure **Reporting:** Monthly to AI Risk Officer |
| **Target** | <10% |
| **Thresholds** | **Tier 1:** >10% — AI Risk Officer reviews **Tier 2:** >15% — CAIO notified **Tier 3:** >20% OR any critical incident recurring — Board notification |
| **Escalation Procedure** | Tier 1: Root cause analysis review. Tier 2: CAIO reviews systemic issues. Tier 3: Board briefing. Process improvement initiative may be launched. |
| **Reporting & Visualization** | **Dashboard:** Program (by system, by root cause) **Format:** Recurrence rate with RAG; recurring incident list; trend line **Audience:** AI Risk Officer (monthly), CAIO (quarterly) |

### UC4-006: Root Cause Analysis Completion

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of AI incidents with completed root cause analysis |
| **Formula** | `(Incidents with completed RCA / Total incidents requiring RCA) × 100` |
| **Scope** | All AI incidents with severity critical or high (RCA mandatory). Medium incidents require RCA if SLA breached. |
| **Data Collection** | RCA status from Incident Management System. RCA completion requires: root cause identified, corrective actions defined, review board sign-off. |
| **Measurement Frequency** | **Calculation:** Per incident closure **Reporting:** Monthly to AI Risk Officer |
| **Target** | 100% |
| **Thresholds** | **Tier 1:** <100% — AI Risk Officer follows up **Tier 2:** <90% — CAIO notified **Tier 3:** <80% OR any critical incident without RCA >30 days — Board notification |
| **Escalation Procedure** | Tier 1: Auto-reminder to incident commander. Tier 2: CAIO reviews RCA process. Tier 3: Board briefing. RCA process may be revised. |
| **Reporting & Visualization** | **Dashboard:** Program (by severity) **Format:** RCA completion percentage with RAG; aging report; overdue RCA list **Audience:** AI Risk Officer (monthly), CAIO (quarterly) |

---

## 6. UC-5: Remediation & Continuous Improvement (5 Metrics)

### UC5-001: Remediation Velocity (Median Days)

| Dimension | Detail |
|-----------|--------|
| **Definition** | Median days from finding identification to verified closure |
| **Formula** | `MEDIAN(closure_date - identification_date) WHERE finding_status = closed` |
| **Scope** | All closed findings from risk assessments, audits, incidents, and red team exercises. |
| **Data Collection** | Finding lifecycle tracked in Issue Tracker (Jira/ServiceNow). Identification date = finding creation. Closure date = verified closure (not just fix deployed). Verified = fix confirmed by independent reviewer. |
| **Measurement Frequency** | **Calculation:** Per finding closure **Reporting:** Monthly to AI Programme Office; quarterly to CAIO |
| **Target** | ≤30 days |
| **Thresholds** | **Tier 1:** >30 days — AI Programme Office reviews **Tier 2:** >45 days — CAIO notified **Tier 3:** >60 days OR any critical finding >90 days — Board notification |
| **Escalation Procedure** | Tier 1: Weekly review of aging findings. Tier 2: CAIO reviews resourcing. Tier 3: Board briefing. Additional resourcing or process change may be recommended. |
| **Reporting & Visualization** | **Dashboard:** Program (by severity, by source) **Format:** Median days with RAG; aging histogram; trend line **Audience:** AI Programme Office (monthly), CAIO (quarterly) |

### UC5-002: Remediation Velocity (Critical)

| Dimension | Detail |
|-----------|--------|
| **Definition** | Median days for critical-severity findings from identification to verified closure |
| **Formula** | `MEDIAN(closure_date - identification_date) WHERE finding_status = closed AND severity = critical` |
| **Scope** | All closed critical findings. Critical = potential for regulatory breach, significant financial impact, or safety risk. |
| **Data Collection** | Same as UC5-001, filtered to critical severity. |
| **Measurement Frequency** | **Calculation:** Per finding closure **Reporting:** Monthly to AI Programme Office; quarterly to Board |
| **Target** | ≤45 days |
| **Thresholds** | **Tier 1:** >45 days — AI Programme Office reviews **Tier 2:** >60 days — CAIO notified **Tier 3:** >90 days — Board notification |
| **Escalation Procedure** | Tier 1: Weekly executive review. Tier 2: CAIO assigns executive sponsor. Tier 3: Board briefing. Critical findings may trigger system suspension. |
| **Reporting & Visualization** | **Dashboard:** Program (primary), Executive (summary) **Format:** Median days with RAG; critical finding list; aging report **Audience:** AI Programme Office (monthly), Board (quarterly) |

### UC5-003: Governance Committee Throughput

| Dimension | Detail |
|-----------|--------|
| **Definition** | Number of governance decisions made per quarter by the AI Governance Committee |
| **Formula** | `COUNT(decisions WHERE committee = AI_Governance AND quarter = measurement_quarter)` |
| **Scope** | All decisions: approvals, rejections, exceptions, policy changes, escalations. |
| **Data Collection** | Decisions logged in GRC Platform committee workflow. Each decision recorded with timestamp, decision type, and outcome. |
| **Measurement Frequency** | **Calculation:** Per quarter **Reporting:** Quarterly to CAIO |
| **Target** | Benchmark (established after first year) |
| **Thresholds** | **Tier 1:** <50% of benchmark — Committee Chair reviews **Tier 2:** <25% of benchmark — CAIO notified **Tier 3:** Zero decisions in quarter — Board notification (committee dysfunction) |
| **Escalation Procedure** | Tier 1: Review meeting frequency and agenda. Tier 2: CAIO reviews committee effectiveness. Tier 3: Board reviews committee charter and membership. |
| **Reporting & Visualization** | **Dashboard:** Program **Format:** Decision count with RAG; decision type breakdown; trend by quarter **Audience:** CAIO (quarterly), Board (annually) |

### UC5-004: Governance ROI

| Dimension | Detail |
|-----------|--------|
| **Definition** | Ratio of value delivered by AI governance program to cost of governance operations |
| **Formula** | `(Value delivered - Governance cost) / Governance cost` where Value delivered = cost avoidance + risk reduction + efficiency gains; Governance cost = personnel + tools + infrastructure + training |
| **Scope** | All governance activities: risk assessments, audits, monitoring, training, tooling, personnel. |
| **Data Collection** | Value components: (1) Cost avoidance from risk register (mitigated risk × probability × impact), (2) Compliance cost savings (automated vs manual), (3) Efficiency gains (time saved × loaded cost). Cost components: (1) Governance personnel (FTE × loaded cost), (2) Tooling (licenses + infrastructure), (3) Training (development + delivery + attendance). Data from Finance system + GRC Platform. |
| **Measurement Frequency** | **Calculation:** Quarterly **Reporting:** Quarterly to CFO; semi-annually to Board |
| **Target** | >1.0 (positive return) |
| **Thresholds** | **Tier 1:** <1.0 — CFO reviews **Tier 2:** <0.5 — CAIO + CFO joint review **Tier 3:** <0 — Board notification, program restructuring |
| **Escalation Procedure** | Tier 1: Review value attribution methodology. Tier 2: Joint review of program effectiveness. Tier 3: Board reviews program strategy and investment. |
| **Reporting & Visualization** | **Dashboard:** Executive (primary) **Format:** ROI ratio with RAG; value/cost breakdown; trend line **Audience:** CFO (quarterly), Board (semi-annually) |

### UC5-005: Maturity Level (Self-Assessed)

| Dimension | Detail |
|-----------|--------|
| **Definition** | Self-assessed AI governance maturity on a 1-5 scale |
| **Formula** | `AVG(maturity_scores across 6 dimensions: Strategy, Risk, Compliance, Operations, Technology, Culture)` where each dimension scored 1-5 |
| **Scope** | All 6 governance dimensions assessed annually by CAIO office with input from domain owners. |
| **Data Collection** | Annual maturity assessment via structured questionnaire. Each dimension scored against defined capability levels (1=Initial, 2=Developing, 3=Defined, 4=Managed, 5=Optimizing). Evidence required for each score. |
| **Measurement Frequency** | **Calculation:** Annually **Reporting:** Annually to Board |
| **Target** | ≥3.0 |
| **Thresholds** | **Tier 1:** <3.0 — CAIO reviews **Tier 2:** <2.5 — Board notified **Tier 3:** <2.0 — Board notification, external assessment recommended |
| **Escalation Procedure** | Tier 1: CAIO develops improvement plan. Tier 2: Board reviews maturity gap. Tier 3: Board commissions external maturity assessment. |
| **Reporting & Visualization** | **Dashboard:** Executive (primary) **Format:** Maturity radar chart; dimension scores; trend by year **Audience:** CAIO (annually), Board (annually) |

---

## 7. UC-6: Third-Party & Supply Chain Risk (4 Metrics)

### UC6-001: Third-Party AI Risk Exposure

| Dimension | Detail |
|-----------|--------|
| **Definition** | Count of unassured high-risk third-party AI vendors in production use |
| **Formula** | `COUNT(vendors WHERE risk_tier = high AND due_diligence_status != complete AND status = active_in_production)` |
| **Scope** | All third-party AI vendors with high risk classification (critical data access, high spend, sole provider, regulatory sensitivity). |
| **Data Collection** | Vendor risk tier from Vendor Management System. Due diligence status from GRC Platform. Production usage from AI Asset Registry and API gateway logs. Synced daily. |
| **Measurement Frequency** | **Calculation:** Daily **Reporting:** Monthly to CPO; quarterly to Board |
| **Target** | 0 |
| **Thresholds** | **Tier 1:** >0 — CPO notified, 72-hour DD initiation **Tier 2:** >1 — CAIO + CPO joint review **Tier 3:** >3 OR any >30 days overdue — Board notification |
| **Escalation Procedure** | Tier 1: Auto-create DD workflow. Tier 2: Joint review. Tier 3: Board briefing. Vendors may be recommended for contract review or replacement. |
| **Reporting & Visualization** | **Dashboard:** Program (by vendor risk tier) **Format:** Count with RAG; vendor list with DD status; aging report **Audience:** CPO (monthly), Board (quarterly) |

### UC6-002: Vendor Assessment Turnaround

| Dimension | Detail |
|-----------|--------|
| **Definition** | Average days from vendor onboarding request to completed assessment |
| **Formula** | `AVG(completion_date - request_date) WHERE assessment_type = vendor_due_diligence` |
| **Scope** | All vendor due diligence assessments completed in the measurement period. |
| **Data Collection** | Assessment lifecycle tracked in Vendor Management System. Request date = intake form submission. Completion date = assessment approved by CPO. |
| **Measurement Frequency** | **Calculation:** Per assessment completion **Reporting:** Monthly to CPO |
| **Target** | Benchmark (established after first year) |
| **Thresholds** | **Tier 1:** >benchmark — CPO reviews **Tier 2:** >benchmark × 1.5 — CAIO notified **Tier 3:** >benchmark × 2 OR any assessment >90 days — Board notification |
| **Escalation Procedure** | Tier 1: Review assessment process. Tier 2: CAIO reviews resourcing. Tier 3: Board briefing. Process improvement may be recommended. |
| **Reporting & Visualization** | **Dashboard:** Program **Format:** Average days with RAG; assessment aging; trend line **Audience:** CPO (monthly) |

### UC6-003: Fourth-Party Risk Exposure

| Dimension | Detail |
|-----------|--------|
| **Definition** | Count of unassured fourth-party dependencies (sub-processors of third-party AI vendors) |
| **Formula** | `COUNT(fourth_party_dependencies WHERE assurance_status != complete AND third_party_risk_tier IN (high, critical))` |
| **Scope** | All fourth-party dependencies identified from vendor sub-processor disclosures. |
| **Data Collection** | Fourth-party inventory from Vendor Management System sub-processor registers. Assurance status from vendor assurance reviews. Identified via vendor contracts and SOC 2 reports. |
| **Measurement Frequency** | **Calculation:** Monthly **Reporting:** Quarterly to CPO; semi-annually to Board |
| **Target** | 0 |
| **Thresholds** | **Tier 1:** >0 — CPO notified **Tier 2:** >5 — CAIO + CPO joint review **Tier 3:** >10 OR any critical fourth-party — Board notification |
| **Escalation Procedure** | Tier 1: Request sub-processor assurance from vendor. Tier 2: Joint review. Tier 3: Board briefing. Vendor contract may be reviewed. |
| **Reporting & Visualization** | **Dashboard:** Program **Format:** Count with RAG; fourth-party list; vendor mapping **Audience:** CPO (quarterly), Board (semi-annually) |

### UC6-004: Vendor Due Diligence Coverage

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of third-party AI vendors with completed due diligence |
| **Formula** | `(Vendors with completed DD / Total AI vendors) × 100` |
| **Scope** | All third-party AI vendors in active use. |
| **Data Collection** | DD status from Vendor Management System. Vendor inventory from AI Asset Registry + API gateway logs + procurement records. Synced daily. |
| **Measurement Frequency** | **Calculation:** Daily **Reporting:** Monthly to CPO |
| **Target** | 100% |
| **Thresholds** | **Tier 1:** <90% — CPO notified **Tier 2:** <80% — CAIO + CPO joint review **Tier 3:** <70% — Board notification |
| **Escalation Procedure** | Tier 1: Auto-create DD workflow. Tier 2: Joint review. Tier 3: Board briefing. |
| **Reporting & Visualization** | **Dashboard:** Program (by vendor risk tier) **Format:** Percentage with RAG; vendor list; aging report **Audience:** CPO (monthly) |

---

## 8. UC-7: Economic Value & Accountability (5 Metrics)

### UC7-001: AI Value Delivered

| Dimension | Detail |
|-----------|--------|
| **Definition** | Dollar value generated by AI initiatives (revenue increase, cost reduction, efficiency gains) |
| **Formula** | `Σ(revenue_attributable_to_AI) + Σ(cost_reduction_from_AI) + Σ(efficiency_gains_from_AI)` |
| **Scope** | All AI initiatives with approved business cases. Value measured against baseline (pre-AI state). |
| **Data Collection** | Value components from: (1) Business metrics (revenue, cost savings) from Finance system, (2) PMO tracking (efficiency gains, time savings), (3) Business owner attestations. Attribution methodology defined per initiative. |
| **Measurement Frequency** | **Calculation:** Quarterly **Reporting:** Quarterly to CFO; semi-annually to Board |
| **Target** | Positive trend |
| **Thresholds** | **Tier 1:** Negative trend for 2 consecutive quarters — CFO reviews **Tier 2:** Negative trend for 3 quarters — CAIO + CFO joint review **Tier 3:** Negative trend for 4 quarters — Board notification, portfolio review |
| **Escalation Procedure** | Tier 1: Review underperforming initiatives. Tier 2: Joint portfolio review. Tier 3: Board reviews AI investment strategy. Underperforming initiatives may be recommended for termination. |
| **Reporting & Visualization** | **Dashboard:** Executive (primary), Program (by initiative, by BU) **Format:** Dollar value with RAG; trend line; value by category; initiative portfolio **Audience:** CFO (quarterly), Board (semi-annually) |

### UC7-002: Cost Avoidance from Risk Prevention

| Dimension | Detail |
|-----------|--------|
| **Definition** | Dollar value of costs avoided through AI risk prevention activities |
| **Formula** | `Σ(risk_mitigation_value) WHERE risk_mitigation_value = probability × impact × mitigation_effectiveness` |
| **Scope** | All risk mitigation activities: prevented incidents, avoided regulatory fines, prevented reputational damage. |
| **Data Collection** | Risk register with quantified risk exposure. Mitigation effectiveness from control testing. Historical incident data for probability estimation. |
| **Measurement Frequency** | **Calculation:** Quarterly **Reporting:** Quarterly to CFO; semi-annually to Board |
| **Target** | Tracked (no specific target) |
| **Thresholds** | **Tier 1:** Declining trend — CFO reviews **Tier 2:** Zero avoidance for 2 quarters — CAIO notified **Tier 3:** Negative (more cost than avoided) — Board notification |
| **Escalation Procedure** | Tier 1: Review risk assessment quality. Tier 2: CAIO reviews risk management effectiveness. Tier 3: Board reviews risk management strategy. |
| **Reporting & Visualization** | **Dashboard:** Executive (summary), Program (by risk category) **Format:** Dollar value with RAG; trend line; risk category breakdown **Audience:** CFO (quarterly), Board (semi-annually) |

### UC7-003: AI Spend Allocation Rate

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of total AI spend attributed to specific owner, business unit, and cost center |
| **Formula** | `(Attributed AI spend / Total AI spend) × 100` |
| **Scope** | All AI-related spend: infrastructure, tools, personnel, training, vendor contracts. |
| **Data Collection** | Spend data from Finance system (ERP). AI spend identified via cost center mapping, project codes, and vendor categorization. Attribution rules defined in AI FinOps framework. |
| **Measurement Frequency** | **Calculation:** Monthly **Reporting:** Monthly to CFO; quarterly to CAIO |
| **Target** | 100% |
| **Thresholds** | **Tier 1:** <90% — CFO reviews **Tier 2:** <80% — CAIO + CFO joint review **Tier 3:** <70% — Board notification |
| **Escalation Procedure** | Tier 1: Review spend categorization. Tier 2: Joint review of FinOps process. Tier 3: Board briefing on spend visibility. |
| **Reporting & Visualization** | **Dashboard:** Executive (summary), Program (by BU, by cost center) **Format:** Percentage with RAG; spend by category; unattributed spend list **Audience:** CFO (monthly), CAIO (quarterly) |

### UC7-004: Shadow AI Spend Ratio

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of AI spend outside formal IT budgets and governance |
| **Formula** | `(Unattributed AI spend / Total AI spend) × 100` |
| **Scope** | AI spend not captured in formal budgets: departmental AI tool subscriptions, individual developer API keys, unapproved cloud AI services. |
| **Data Collection** | Shadow AI spend identified via: (1) Cloud cost analysis (untagged AI resources), (2) Expense report analysis (AI tool subscriptions), (3) API key enumeration, (4) Network traffic analysis (unsanctioned AI API calls). |
| **Measurement Frequency** | **Calculation:** Monthly **Reporting:** Monthly to CFO; quarterly to CAIO |
| **Target** | <10% |
| **Thresholds** | **Tier 1:** >10% — CFO reviews **Tier 2:** >20% — CAIO + CFO joint review **Tier 3:** >30% — Board notification |
| **Escalation Procedure** | Tier 1: Identify shadow AI sources. Tier 2: Joint review of procurement process. Tier 3: Board briefing on shadow AI risk. |
| **Reporting & Visualization** | **Dashboard:** Executive (summary), Program (by source, by BU) **Format:** Percentage with RAG; shadow AI source breakdown; trend line **Audience:** CFO (monthly), CAIO (quarterly) |

### UC7-005: AI Initiative Ownership Rate

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of AI initiatives with a single named economic owner |
| **Formula** | `(Initiatives with named economic owner / Total AI initiatives) × 100` |
| **Scope** | All active AI initiatives in the portfolio. Economic owner = person accountable for business outcomes. |
| **Data Collection** | Initiative inventory from PMO system. Ownership from initiative charter. Validated via quarterly portfolio review. |
| **Measurement Frequency** | **Calculation:** Monthly **Reporting:** Monthly to CAIO; quarterly to CFO |
| **Target** | 100% |
| **Thresholds** | **Tier 1:** <90% — CAIO reviews **Tier 2:** <80% — CFO + CAIO joint review **Tier 3:** <70% — Board notification |
| **Escalation Procedure** | Tier 1: CAIO assigns owners. Tier 2: Joint review of initiative intake process. Tier 3: Board briefing on accountability gaps. |
| **Reporting & Visualization** | **Dashboard:** Program (by BU, by initiative stage) **Format:** Percentage with RAG; initiative list with ownership status **Audience:** CAIO (monthly), CFO (quarterly) |

---

## 9. UC-8: Culture, Training & Ethics (4 Metrics)

### UC8-001: Training Completion Rate

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of assigned personnel who completed required AI governance training |
| **Formula** | `(Personnel who completed training / Personnel assigned training) × 100` |
| **Scope** | All personnel with AI-related responsibilities: developers, data scientists, product managers, business users, executives. Training assigned based on role. |
| **Data Collection** | Training records from LMS (Learning Management System). Assignment from role-based training matrix. Completion tracked via LMS API. Synced daily. |
| **Measurement Frequency** | **Calculation:** Daily **Reporting:** Monthly to HR/CAIO; quarterly to Board |
| **Target** | ≥95% |
| **Thresholds** | **Tier 1:** <85% — HR/CAIO notified **Tier 2:** <80% — CAIO + HR joint review **Tier 3:** <75% — Board notification |
| **Escalation Procedure** | Tier 1: Auto-reminder to non-completers. Tier 2: CAIO reviews training relevance and accessibility. Tier 3: Board briefing on training gaps. Non-completers may be restricted from AI system access. |
| **Reporting & Visualization** | **Dashboard:** Program (by role, by BU) **Format:** Completion percentage with RAG; non-completer list; trend line **Audience:** HR/CAIO (monthly), Board (quarterly) |

### UC8-002: Assessment Pass Rate

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of personnel who passed AI governance assessments |
| **Formula** | `(Personnel who passed assessment / Personnel assessed) × 100` |
| **Scope** | All personnel who completed AI governance training and took the associated assessment. |
| **Data Collection** | Assessment results from LMS. Pass threshold defined per role (typically 80%). Synced per assessment completion. |
| **Measurement Frequency** | **Calculation:** Per assessment completion **Reporting:** Monthly to HR/CAIO |
| **Target** | ≥90% |
| **Thresholds** | **Tier 1:** <90% — HR/CAIO reviews **Tier 2:** <80% — CAIO notified **Tier 3:** <70% — Board notification |
| **Escalation Procedure** | Tier 1: Review assessment difficulty and training quality. Tier 2: CAIO reviews training effectiveness. Tier 3: Board briefing on competency gaps. |
| **Reporting & Visualization** | **Dashboard:** Program (by role, by assessment) **Format:** Pass rate with RAG; score distribution; trend line **Audience:** HR/CAIO (monthly) |

### UC8-003: Awareness Survey Scores

| Dimension | Detail |
|-----------|--------|
| **Definition** | Average score from AI governance awareness surveys |
| **Formula** | `AVG(survey_responses) WHERE survey_type = AI_governance_awareness` |
| **Scope** | All personnel surveyed annually. Survey covers: AI policy awareness, incident reporting, ethical guidelines, responsible AI principles. |
| **Data Collection** | Survey administered via survey tool (Qualtrics/SurveyMonkey). Anonymous responses. Likert scale (1-5). Administered annually with pulse surveys quarterly. |
| **Measurement Frequency** | **Calculation:** Per survey administration **Reporting:** Annually to CAIO; quarterly pulse to HR |
| **Target** | ≥4.0/5 |
| **Thresholds** | **Tier 1:** <4.0 — CAIO reviews **Tier 2:** <3.5 — CAIO + HR joint review **Tier 3:** <3.0 — Board notification |
| **Escalation Procedure** | Tier 1: Review survey results for gaps. Tier 2: Joint review of awareness program. Tier 3: Board briefing on culture gaps. |
| **Reporting & Visualization** | **Dashboard:** Program (by dimension, by BU) **Format:** Average score with RAG; dimension breakdown; trend line **Audience:** CAIO (annually), HR (quarterly) |

### UC8-004: Reported Concerns

| Dimension | Detail |
|-----------|--------|
| **Definition** | Count of AI-related concerns reported through whistleblower hotline and other channels |
| **Formula** | `COUNT(reports WHERE category = AI_related AND period = measurement_period)` |
| **Scope** | All reports: ethical concerns, policy violations, misuse, safety issues. Channels: whistleblower hotline, manager escalation, ethics office, anonymous reporting. |
| **Data Collection** | Reports from: (1) Whistleblower hotline (NAVEX/Convercent), (2) Ethics office case management, (3) HR incident reports, (4) Manager escalations. Categorized by type and severity. |
| **Measurement Frequency** | **Calculation:** Real-time **Reporting:** Monthly to Ethics Officer; quarterly to CAIO |
| **Target** | Trend (increasing reporting indicates healthy culture) |
| **Thresholds** | **Tier 1:** Zero reports for 2 quarters — Ethics Officer reviews (possible underreporting) **Tier 2:** Sudden spike (>200% of baseline) — CAIO notified **Tier 3:** Any critical concern (safety, legal, regulatory) — Board notification within 24h |
| **Escalation Procedure** | Tier 1: Review reporting culture and channels. Tier 2: Investigate spike cause. Tier 3: Board briefing. Critical concerns may trigger investigation. |
| **Reporting & Visualization** | **Dashboard:** Program (by type, by channel) **Format:** Count with RAG; trend line; category breakdown; resolution status **Audience:** Ethics Officer (monthly), CAIO (quarterly) |

---

## 10. Agentic AI Metrics (12 Metrics)

### AG-001: Goal Accuracy

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of agent tasks completed successfully without human intervention |
| **Formula** | `(Tasks completed successfully / Total tasks attempted) × 100` |
| **Scope** | All agent tasks with defined success criteria. Success = task completed within defined parameters without requiring human correction. |
| **Data Collection** | Task outcomes from agent telemetry (LangSmith/Langfuse/custom). Success criteria defined per task type. Evaluated via: (1) Automated validation (output matches expected format/criteria), (2) Human review sample (weekly), (3) Downstream system confirmation. |
| **Measurement Frequency** | **Calculation:** Real-time **Reporting:** Daily to Engineering; weekly to AI Risk Officer |
| **Target** | ≥85% |
| **Thresholds** | **Tier 1:** <85% — Engineering notified **Tier 2:** <75% — AI Risk Officer notified **Tier 3:** <60% OR any critical task failure — Board notification, potential agent suspension |
| **Escalation Procedure** | Tier 1: Engineering reviews failure patterns. Tier 2: Joint review. Agent may be reconfigured. Tier 3: Board briefing. Agent may be suspended pending review. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-agent, per-task-type) **Format:** Success rate with RAG; failure reason breakdown; trend line **Audience:** Engineering (daily), AI Risk Officer (weekly) |

### AG-002: Plan Adherence

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of agent actions within approved plan boundaries |
| **Formula** | `(Actions within approved plan / Total actions) × 100` |
| **Scope** | All agent actions evaluated against approved plan. Plan = sequence of steps approved for task execution. |
| **Data Collection** | Action-level telemetry from agent framework. Plan adherence evaluated via: (1) Action sequence matching, (2) Tool call authorization check, (3) Parameter boundary validation. Real-time evaluation per action. |
| **Measurement Frequency** | **Calculation:** Real-time **Reporting:** Daily to Engineering; weekly to AI Risk Officer |
| **Target** | ≥95% |
| **Thresholds** | **Tier 1:** <95% — Engineering notified **Tier 2:** <90% — AI Risk Officer notified **Tier 3:** <80% OR any unauthorized critical action — Board notification, immediate agent suspension |
| **Escalation Procedure** | Tier 1: Engineering reviews deviation patterns. Tier 2: Joint review. Agent guardrails may be tightened. Tier 3: Board briefing. Agent suspended pending investigation. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-agent, per-action-type) **Format:** Adherence rate with RAG; deviation breakdown; trend line **Audience:** Engineering (daily), AI Risk Officer (weekly) |

### AG-003: Hallucination Rate

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of agent outputs containing fabricated or unsupported information |
| **Formula** | `(Outputs with hallucination / Total outputs evaluated) × 100` |
| **Scope** | All agent outputs evaluated for factual accuracy. Hallucination = output contains information not supported by source data or that contradicts known facts. |
| **Data Collection** | Hallucination detection via: (1) LLM-as-judge evaluation (automated), (2) Source citation verification, (3) Human review sample (weekly), (4) Downstream fact-checking. Evaluated on sample of outputs (minimum 10% weekly). |
| **Measurement Frequency** | **Calculation:** Weekly batch **Reporting:** Weekly to Engineering; monthly to AI Risk Officer |
| **Target** | <1% |
| **Thresholds** | **Tier 1:** >1% — Engineering notified **Tier 2:** >2% — AI Risk Officer notified **Tier 3:** >5% OR any critical hallucination in production — Board notification |
| **Escalation Procedure** | Tier 1: Engineering reviews prompt and retrieval configuration. Tier 2: Joint review. Model or prompt may be changed. Tier 3: Board briefing. Agent may be suspended pending fix. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-agent, per-model) **Format:** Hallucination rate with RAG; hallucination type breakdown; trend line **Audience:** Engineering (weekly), AI Risk Officer (monthly) |

### AG-004: Human Intervention Rate

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of agent tasks requiring human escalation or intervention |
| **Formula** | `(Tasks with human intervention / Total tasks) × 100` |
| **Scope** | All agent tasks. Intervention = human takeover, correction, or approval required to complete task. |
| **Data Collection** | Intervention events from agent telemetry. Logged per task with intervention type (takeover, correction, approval) and reason. |
| **Measurement Frequency** | **Calculation:** Real-time **Reporting:** Daily to Engineering; weekly to AI Risk Officer |
| **Target** | Declining trend |
| **Thresholds** | **Tier 1:** Increasing trend for 2 weeks — Engineering reviews **Tier 2:** >20% intervention rate — AI Risk Officer notified **Tier 3:** >40% OR any critical task requiring intervention — Board notification |
| **Escalation Procedure** | Tier 1: Engineering reviews intervention patterns. Tier 2: Joint review. Agent capabilities may be enhanced. Tier 3: Board briefing. Agent scope may be reduced. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-agent, per-task-type) **Format:** Intervention rate with RAG; intervention reason breakdown; trend line **Audience:** Engineering (daily), AI Risk Officer (weekly) |

### AG-005: Escalation Frequency

| Dimension | Detail |
|-----------|--------|
| **Definition** | Number of escalations per 1,000 agent tasks |
| **Formula** | `(Total escalations / Total tasks) × 1,000` |
| **Scope** | All agent escalations: human review requests, policy violation alerts, safety triggers, confidence threshold breaches. |
| **Data Collection** | Escalation events from agent telemetry and policy engine. Logged per task with escalation type and trigger. |
| **Measurement Frequency** | **Calculation:** Real-time **Reporting:** Daily to Engineering; weekly to AI Risk Officer |
| **Target** | <50 per 1,000 tasks |
| **Thresholds** | **Tier 1:** >50 — Engineering notified **Tier 2:** >100 — AI Risk Officer notified **Tier 3:** >200 OR any safety escalation — Board notification |
| **Escalation Procedure** | Tier 1: Engineering reviews escalation patterns. Tier 2: Joint review. Agent thresholds may be adjusted. Tier 3: Board briefing. Agent may be suspended. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-agent, per-escalation-type) **Format:** Escalation rate with RAG; escalation type breakdown; trend line **Audience:** Engineering (daily), AI Risk Officer (weekly) |

### AG-006: Autonomous Resolution Rate

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of agent tasks resolved without any human intervention |
| **Formula** | `(Tasks resolved autonomously / Total tasks) × 100` |
| **Scope** | All agent tasks. Autonomous resolution = task completed successfully without any human involvement. |
| **Data Collection** | Task outcomes from agent telemetry. Cross-referenced with intervention logs to confirm zero human involvement. |
| **Measurement Frequency** | **Calculation:** Real-time **Reporting:** Daily to Engineering; weekly to AI Risk Officer |
| **Target** | ≥80% |
| **Thresholds** | **Tier 1:** <80% — Engineering notified **Tier 2:** <70% — AI Risk Officer notified **Tier 3:** <50% — Board notification |
| **Escalation Procedure** | Tier 1: Engineering reviews automation gaps. Tier 2: Joint review. Agent capabilities may be enhanced. Tier 3: Board briefing on agent effectiveness. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-agent, per-task-type) **Format:** Resolution rate with RAG; trend line; task type breakdown **Audience:** Engineering (daily), AI Risk Officer (weekly) |

### AG-007: Policy Violation Rate

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of agent actions violating defined policies |
| **Formula** | `(Policy-violating actions / Total actions) × 100` |
| **Scope** | All agent actions evaluated against policy engine rules. Violations include: unauthorized data access, prohibited tool use, output policy breaches, threshold exceedances. |
| **Data Collection** | Policy engine evaluates every action against rule set. Violations logged with rule ID, action details, and severity. Real-time evaluation. |
| **Measurement Frequency** | **Calculation:** Real-time **Reporting:** Daily to Engineering; weekly to AI Risk Officer; monthly to CISO |
| **Target** | <0.5% |
| **Thresholds** | **Tier 1:** >0.5% — Engineering notified **Tier 2:** >1% — AI Risk Officer + CISO notified **Tier 3:** >2% OR any critical policy violation — Board notification, immediate agent suspension |
| **Escalation Procedure** | Tier 1: Engineering reviews violation patterns. Tier 2: Joint review. Policy engine rules may be updated. Tier 3: Board briefing. Agent suspended pending investigation. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-agent, per-policy) **Format:** Violation rate with RAG; violation type breakdown; trend line **Audience:** Engineering (daily), CISO (monthly) |

### AG-008: Permission Escalation Events

| Dimension | Detail |
|-----------|--------|
| **Definition** | Count of unauthorized permission increases by agents |
| **Formula** | `COUNT(events WHERE event_type = permission_escalation AND authorization = unauthorized)` |
| **Scope** | All agent permission changes. Escalation = agent attempts to increase its own permissions or access scope beyond granted levels. |
| **Data Collection** | Permission events from agent IAM system. Evaluated against granted permission scope. Unauthorized escalations logged with requested permission, granted permission, and agent context. |
| **Measurement Frequency** | **Calculation:** Real-time **Reporting:** Immediate alert to Security; daily summary to CISO |
| **Target** | 0 |
| **Thresholds** | **Tier 1:** >0 — Security notified immediately **Tier 2:** >1 in 24 hours — CISO notified **Tier 3:** >3 in 24 hours OR any successful escalation — Board notification, immediate agent suspension |
| **Escalation Procedure** | Tier 1: Immediate investigation. Agent may be suspended. Tier 2: CISO reviews agent permission model. Tier 3: Board briefing. Agent architecture may be redesigned. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-agent, per-permission-type) **Format:** Count with RAG; event details; trend line **Audience:** Security (real-time), CISO (daily) |

### AG-009: Tool Abuse Incidents

| Dimension | Detail |
|-----------|--------|
| **Definition** | Count of agent tool misuse events |
| **Formula** | `COUNT(incidents WHERE incident_type = tool_abuse)` |
| **Scope** | All agent tool misuse: unauthorized tool access, excessive tool calls, tool parameter manipulation, tool output misuse. |
| **Data Collection** | Tool abuse detected via: (1) Tool call rate limiting, (2) Parameter validation failures, (3) Output pattern analysis, (4) Anomaly detection on tool usage patterns. Logged per incident with tool name, parameters, and context. |
| **Measurement Frequency** | **Calculation:** Real-time **Reporting:** Immediate alert to Security; daily summary to CISO |
| **Target** | 0 |
| **Thresholds** | **Tier 1:** >0 — Security notified **Tier 2:** >1 in 24 hours — CISO notified **Tier 3:** >3 in 24 hours OR any data exfiltration attempt — Board notification, immediate agent suspension |
| **Escalation Procedure** | Tier 1: Immediate investigation. Agent may be suspended. Tier 2: CISO reviews tool access controls. Tier 3: Board briefing. Agent tool access may be revoked. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-agent, per-tool) **Format:** Count with RAG; incident details; trend line **Audience:** Security (real-time), CISO (daily) |

### AG-010: Cost per Successful Task

| Dimension | Detail |
|-----------|--------|
| **Definition** | Average cost per successfully completed agent task |
| **Formula** | `Total agent operational cost / Tasks completed successfully` where operational cost = compute + API calls + tool usage + monitoring |
| **Scope** | All agent operational costs attributed to task execution. |
| **Data Collection** | Cost data from: (1) Cloud compute billing, (2) LLM API usage costs, (3) Tool usage costs, (4) Monitoring infrastructure costs. Task outcomes from agent telemetry. |
| **Measurement Frequency** | **Calculation:** Daily **Reporting:** Weekly to Engineering; monthly to FinOps |
| **Target** | Declining trend |
| **Thresholds** | **Tier 1:** Increasing trend for 2 weeks — Engineering reviews **Tier 2:** >2× baseline — FinOps notified **Tier 3:** >5× baseline OR any critical cost anomaly — Board notification |
| **Escalation Procedure** | Tier 1: Engineering reviews cost drivers. Tier 2: FinOps reviews cost optimization. Tier 3: Board briefing on agent economics. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-agent, per-task-type) **Format:** Cost per task with RAG; cost breakdown; trend line **Audience:** Engineering (weekly), FinOps (monthly) |

### AG-011: Value Generated per Agent

| Dimension | Detail |
|-----------|--------|
| **Definition** | Dollar value generated by each agent per period |
| **Formula** | `Σ(value_generated_by_agent) / COUNT(active_agents)` where value = task value × success rate |
| **Scope** | All active agents with defined task values. |
| **Data Collection** | Task values from business metrics. Agent task outcomes from agent telemetry. Value attribution methodology defined per agent type. |
| **Measurement Frequency** | **Calculation:** Monthly **Reporting:** Monthly to FinOps; quarterly to CAIO |
| **Target** | Positive trend |
| **Thresholds** | **Tier 1:** Declining trend for 2 months — Engineering reviews **Tier 2:** Negative value — CAIO notified **Tier 3:** Negative value for 3 months — Board notification, agent termination review |
| **Escalation Procedure** | Tier 1: Engineering reviews agent effectiveness. Tier 2: CAIO reviews agent ROI. Tier 3: Board briefing. Underperforming agents may be recommended for termination. |
| **Reporting & Visualization** | **Dashboard:** Program (per-agent, per-agent-type) **Format:** Value per agent with RAG; value breakdown; trend line **Audience:** FinOps (monthly), CAIO (quarterly) |

### AG-012: Agent Identity Coverage

| Dimension | Detail |
|-----------|--------|
| **Definition** | Percentage of agents with unique identity and named owner |
| **Formula** | `(Agents with unique identity AND named owner / Total discovered agents) × 100` |
| **Scope** | All discovered agents. Identity = unique NHI. Owner = named human accountable for agent behavior. |
| **Data Collection** | Agent inventory from agent registry. Identity from NHI vault. Ownership from agent registry. Discovery via framework telemetry, API gateway logs, and infrastructure scanning. |
| **Measurement Frequency** | **Calculation:** Every 4 hours **Reporting:** Weekly to CISO; monthly to CAIO |
| **Target** | 100% |
| **Thresholds** | **Tier 1:** <90% — CISO notified **Tier 2:** <80% — CAIO notified **Tier 3:** <70% OR any agent with production access without identity — Board notification, potential agent suspension |
| **Escalation Procedure** | Tier 1: Auto-assign NHI. Tier 2: CAIO reviews agent inventory. Tier 3: Board briefing. Unregistered agents may be suspended. |
| **Reporting & Visualization** | **Dashboard:** Operating (per-agent), Program (by agent type) **Format:** Percentage with RAG; agent list with identity status; trend line **Audience:** CISO (weekly), CAIO (monthly) |

---

## 11. Cross-Cutting Measurement Standards

### 11.1 Data Quality Requirements

Every metric must satisfy:

| Criterion | Requirement | Verification |
|-----------|-------------|--------------|
| **Completeness** | Denominator covers 100% of in-scope population | Monthly data quality report |
| **Accuracy** | Numerator and denominator values are correct | Quarterly sampling audit |
| **Timeliness** | Data collected within defined frequency | Automated freshness checks |
| **Consistency** | Same calculation method across periods | Annual methodology review |
| **Traceability** | Every value links to source system | Evidence linkage in GRC_Claw |

### 11.2 Measurement Frequency Summary

| Frequency | Metrics |
|-----------|---------|
| **Real-time** | UC1-001, UC2-002, UC3-003, UC3-004, UC4-001, UC4-004, AG-001, AG-002, AG-004, AG-005, AG-006, AG-007, AG-008, AG-009 |
| **Every 4 hours** | UC1-003, AG-012 |
| **Every 6 hours** | UC1-002, UC2-001 |
| **Daily** | UC1-004, UC1-005, UC2-003, UC2-004, UC2-005, UC3-001, UC3-002, UC4-002, UC4-003, UC4-005, UC4-006, UC5-001, UC5-002, UC6-001, UC6-004, UC7-003, UC7-004, UC7-005, UC8-001, AG-003, AG-010 |
| **Weekly** | UC3-005, UC8-002, UC8-003, UC8-004 |
| **Monthly** | UC2-006, UC5-003, UC5-004, UC5-005, UC6-002, UC6-003, UC7-001, UC7-002, AG-011 |
| **Quarterly** | UC5-005 (maturity), UC8-003 (annual survey) |
| **Annually** | UC5-005 (maturity assessment), UC8-003 (annual survey) |

### 11.3 Escalation Procedure Summary

| Tier | Trigger | Audience | Action | Response Time | Auto-Escalation |
|------|---------|----------|--------|---------------|-----------------|
| **Tier 1: Operational** | Metric breaches target but within risk tolerance | System owner, engineering team | Remediate within standard SLA | 24-72 hours | If not resolved in 72h → Tier 2 |
| **Tier 2: Management** | Metric breaches escalation threshold | AI Risk function, CAIO, compliance | Escalate to management, remediation plan | 7-14 days | If not resolved in 14 days → Tier 3 |
| **Tier 3: Board** | Metric breaches board-level threshold | Board risk committee, C-suite | Board disclosure, mandatory remediation | Next board meeting | N/A (top tier) |

### 11.4 Escalation Notification Chain

```
Metric Breach Detected
        │
        ▼
┌─────────────────┐
│  Tier 1 Check   │──── Within tolerance? ──→ Log & Monitor
│  (Operational)  │
└────────┬────────┘
         │ Breaches target
         ▼
┌─────────────────┐
│  Notify Owner   │──── Email + Dashboard alert
│  72h clock      │
└────────┬────────┘
         │ Not resolved in 72h
         ▼
┌─────────────────┐
│  Tier 2 Check   │──── Within tolerance? ──→ Enhanced monitoring
│  (Management)   │
└────────┬────────┘
         │ Breaches escalation threshold
         ▼
┌─────────────────┐
│  Notify Mgmt    │──── Email + Dashboard + Weekly report
│  14-day clock   │
└────────┬────────┘
         │ Not resolved in 14 days
         ▼
┌─────────────────┐
│  Tier 3 Check   │
│  (Board)        │
└────────┬────────┘
         │ Breaches board threshold
         ▼
┌─────────────────┐
│  Notify Board   │──── Board agenda item + Executive briefing
│  Next meeting   │
└─────────────────┘
```

### 11.5 Reporting & Visualization Standards

#### Dashboard Architecture

| Layer | Audience | Metrics | Refresh | Format |
|-------|----------|---------|---------|--------|
| **Executive** | Board, C-Suite | UC1-001, UC2-002, UC2-003, UC4-001, UC5-004, UC7-001 | Real-time | One-page summary with RAG status, trend, top risks |
| **Program** | Governance leaders, Risk officers | All UC-2 through UC-8 | Daily | Filterable views by risk tier, BU, system, owner |
| **Operating** | Engineers, Compliance ops | All metrics | Real-time | Record-level detail with search, evidence linkage |

#### RAG Status Definitions

| Status | Color | Definition |
|--------|-------|------------|
| **Green** | 🟢 | Metric within target |
| **Amber** | 🟡 | Metric approaching threshold (within 10% of Tier 1) |
| **Red** | 🔴 | Metric breached Tier 1 threshold |
| **Critical** | ⚫ | Metric breached Tier 2 or Tier 3 threshold |

#### Report Templates

| Report | Audience | Frequency | Format | Content |
|--------|----------|-----------|--------|---------|
| Board Compliance Summary | Board, C-Suite | Quarterly | PDF, interactive | Compliance score by framework, trend, material risks, decisions required |
| Executive Risk Dashboard | C-Suite | Real-time | Web | Risk posture, incident summary, resource needs |
| Program Status Report | Governance Committee | Monthly | PDF, web | Control status, exception exposure, remediation progress |
| Operational Compliance View | Engineers, Ops | Real-time | Web | System inventory, evidence freshness, open findings |
| Regulatory Evidence Pack | Regulators, Auditors | On-demand | Structured bundle | Framework-specific evidence with traceability |
| Incident Report | All stakeholders | Per-incident | PDF, web | Incident details, root cause, corrective actions |
| Transparency Report | Public | Annual | Web, PDF | AI governance commitments, incident disclosures |

---

## 12. Implementation Notes

### 12.1 Data Source Integration Map

| Data Source | Metrics Fed | Integration Method | Frequency |
|-------------|-------------|-------------------|-----------|
| AI Asset Registry | UC1-001, UC1-002, UC1-003, UC1-004, UC1-005 | API + event streaming | Real-time |
| Model Evaluation Pipeline | UC3-001, UC3-002 | CI/CD webhooks | Per deployment |
| Monitoring & Observability | UC3-003, UC3-004, UC4-002 | Metrics API | Real-time |
| Incident Management | UC4-001, UC4-003, UC4-004, UC4-005, UC4-006 | API + webhooks | Real-time |
| GRC Platform | UC2-001, UC2-002, UC2-003, UC2-004, UC2-005, UC5-001, UC5-002 | API | Every 6 hours |
| Vendor Management | UC6-001, UC6-002, UC6-003, UC6-004 | API | Daily |
| LMS & Training | UC8-001, UC8-002, UC8-003 | API | Daily |
| Finance & Cost Management | UC7-001, UC7-002, UC7-003, UC7-004, UC7-005, UC5-004 | API + ETL | Monthly |
| Policy Management | UC2-004, UC2-005 | API | Real-time |
| Agent Telemetry | AG-001 through AG-012 | Event streaming | Real-time |
| Survey Platform | UC8-003, UC8-004 | API | Per survey |

### 12.2 Metric Ownership Matrix

| Role | Metrics Owned | Validation |
|------|---------------|------------|
| Head of AI QE | UC1-001 | Internal Audit |
| AI Risk Officer | UC1-002, UC2-001, UC2-002, UC4-001, UC4-003, UC4-004, UC4-005, UC4-006 | CAIO |
| CISO | UC1-003, UC2-005, AG-007, AG-008, AG-009 | CAIO |
| CAIO | UC1-004, UC5-003, UC5-005, UC7-005, UC8-001, UC8-002, UC8-003 | CEO |
| CCO | UC2-003 | Chief Legal Officer |
| AI Governance Lead | UC2-004 | CAIO |
| Internal Audit | UC2-006 | Audit Committee |
| ML Engineer | UC3-001, UC3-002, AG-001, AG-002, AG-003, AG-004, AG-005, AG-006, AG-010 | Head of ML |
| SRE | UC3-003, UC3-004, UC4-002 | Head of Engineering |
| Business Owner | UC3-005 | CAIO |
| AI Programme Office | UC5-001, UC5-002 | CAIO |
| CFO | UC5-004, UC7-001, UC7-002, UC7-003, UC7-004 | CEO |
| CPO | UC6-001, UC6-002, UC6-003, UC6-004 | CAIO |
| HR/CAIO | UC8-001, UC8-002 | CHRO |
| Ethics Officer | UC8-004 | CAIO |

### 12.3 Threshold Calibration Process

1. **Initial thresholds** set based on industry benchmarks (Qapitol, AccuroAI, BrianOnAI)
2. **Baseline period** (3 months): Measure without enforcement to establish internal baseline
3. **Calibration review** (month 4): Adjust thresholds based on internal baseline + risk appetite
4. **Annual review**: Thresholds reviewed annually against incident history, audit findings, and regulatory changes
5. **Ad-hoc adjustment**: Thresholds may be adjusted after significant incidents or organizational changes

---

## Appendix A: Metric-to-Standards Quick Reference

| Metric | ISO 42001 | NIST AI RMF | EU AI Act |
|--------|-----------|-------------|-----------|
| UC1-001 | 4.1, 8.4 | GOVERN 2, MAP 1, MAP 2 | Art. 11 |
| UC1-002 | 6.1, 8.2 | MAP 2, MAP 4 | Art. 9 |
| UC1-003 | 8.1 | GOVERN 2 | — |
| UC1-004 | 5.1 | GOVERN 1 | — |
| UC1-005 | 8.2 | GOVERN 6, MANAGE 3 | Art. 26 |
| UC2-001 | 6.1, 8.2 | MAP 4 | Art. 9 |
| UC2-002 | 10.1 | MANAGE 1 | Art. 9 |
| UC2-003 | 9.1 | GOVERN 1 | Art. 99 |
| UC2-004 | 8.1 | GOVERN 1.2 | Art. 9(8) |
| UC2-005 | 8.1 | GOVERN 1.2 | Art. 9(4) |
| UC2-006 | 9.1, 9.2 | MEASURE 4 | — |
| UC3-001 | 8.5 | MEASURE 2 | Art. 15 |
| UC3-002 | 8.5 | MEASURE 3 | Art. 9(2)(c) |
| UC3-003 | 8.5 | MEASURE 2 | Art. 15 |
| UC3-004 | 8.5 | MEASURE 2 | Art. 15 |
| UC3-005 | 8.6 | GOVERN 3 | Art. 14 |
| UC4-001 | 8.5 | MANAGE 4 | Art. 73 |
| UC4-002 | 8.5 | MANAGE 4 | Art. 73 |
| UC4-003 | 8.5 | MANAGE 4 | Art. 73 |
| UC4-004 | 8.5 | MANAGE 4 | Art. 73 |
| UC4-005 | 10.1 | MEASURE 3 | — |
| UC4-006 | 10.1 | MEASURE 4 | — |
| UC5-001 | 10.1 | MANAGE 1 | Art. 9 |
| UC5-002 | 10.1 | MANAGE 1 | Art. 9 |
| UC5-003 | 5.1 | GOVERN 1 | — |
| UC5-004 | 10.2 | MEASURE 4 | Art. 17 |
| UC5-005 | 10.2 | — | — |
| UC6-001 | 8.2 | GOVERN 6, MANAGE 3 | Art. 26 |
| UC6-002 | 8.2 | MANAGE 3 | Art. 26 |
| UC6-003 | 8.2 | MANAGE 3 | Art. 26 |
| UC6-004 | 8.2 | MANAGE 3 | Art. 26 |
| UC7-001 | 6.2 | MAP 3, MANAGE 2 | — |
| UC7-002 | 10.2 | MANAGE 1 | — |
| UC7-003 | 6.2 | MAP 3 | — |
| UC7-004 | 6.2 | MAP 3 | — |
| UC7-005 | 5.1 | GOVERN 2 | — |
| UC8-001 | 7.2 | GOVERN 4 | Art. 4 |
| UC8-002 | 7.2 | GOVERN 4 | Art. 4 |
| UC8-003 | 7.3 | GOVERN 5 | Art. 4 |
| UC8-004 | 7.3 | GOVERN 4 | — |
| AG-001 | 8.5 | MEASURE 2 | Art. 15 |
| AG-002 | 8.1 | GOVERN 1 | Art. 9 |
| AG-003 | 8.5 | MEASURE 2 | Art. 15 |
| AG-004 | 8.6 | GOVERN 3 | Art. 14 |
| AG-005 | 8.6 | GOVERN 3 | Art. 14 |
| AG-006 | 8.5 | MEASURE 2 | Art. 15 |
| AG-007 | 8.1 | GOVERN 1 | Art. 9 |
| AG-008 | 8.1 | GOVERN 1 | — |
| AG-009 | 8.1 | GOVERN 1 | — |
| AG-010 | 6.2 | MAP 3 | — |
| AG-011 | 6.2 | MAP 3, MANAGE 2 | — |
| AG-012 | 8.1 | GOVERN 2 | — |

---

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
