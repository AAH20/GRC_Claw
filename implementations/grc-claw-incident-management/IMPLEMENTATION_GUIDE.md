# GRC_Claw AI Incident Management — Implementation Guide

**Reference:** GRC-AIM-001 v2.0  
**Version:** 1.0  
**Date:** 2026-10-01

---

## Table of Contents

1. [Overview](#1-overview)
2. [Incident Detection Pipeline (§12)](#2-incident-detection-pipeline)
3. [Incident Classification (§14)](#3-incident-classification)
4. [Incident Response Orchestration (§13)](#4-incident-response-orchestration)
5. [Incident Reporting (§6)](#5-incident-reporting)
6. [Post-Incident Learning (§15)](#6-post-incident-learning)
7. [Incident Trend Analysis (§16)](#7-incident-trend-analysis)
8. [Regulatory Reporting (§17)](#8-regulatory-reporting)
9. [Quick Start](#9-quick-start)
10. [Architecture Summary](#10-architecture-summary)

---

## 1. Overview

GRC_Claw's incident management framework covers the full AI incident lifecycle across **8 categories**, **44 subcategories**, **5 severity levels**, and a **6-phase response workflow**. This implementation provides working Python code for all 7 core capabilities.

### Taxonomy (§3)

| Code | Category | Subcategories | Min Severity |
|------|----------|---------------|-------------|
| DL | Data Leakage | DL-1 … DL-6 | S2 |
| HO | Harmful Output | HO-1 … HO-6 | S2 |
| WA | Wrong Action by Agent | WA-1 … WA-6 | S2 |
| HL | Hallucination | HL-1 … HL-6 | S3 |
| PI | Prompt Injection | PI-1 … PI-6 | S2 |
| MP | Model Poisoning | MP-1 … MP-6 | S1 |
| SC | Supply Chain | SC-1 … SC-5 | S3 |
| AM | Agent Misbehavior | AM-1 … AM-6 | S1 |

### Severity Levels (§4.1)

| Level | Name | Response Time | Escalation | Regulatory Notification |
|-------|------|---------------|------------|------------------------|
| S1 | Critical | 15 min | CISO → CTO → Risk Committee → Board | EU AI Act Art. 73: 24h |
| S2 | High | 1 hour | Security Lead → CISO → Risk Committee | EU AI Act Art. 73: 72h |
| S3 | Medium | 4 hours | GRC_Claw Analyst → Security Lead | Case-by-case |
| S4 | Low | 24 hours | GRC_Claw Analyst | Not required |
| S5 | Informational | 72 hours | GRC_Claw Analyst | Not required |

### Response Phases (§5.1)

```
Detect → Triage → Contain → Eradicate → Recover → Review
```

---

## 2. Incident Detection Pipeline

**Module:** `grc_incident_mgmt/detection.py`  
**Spec:** §12 — Automated Incident Detection Pipeline

### Architecture

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Ingest   │──▶│ Enrich   │──▶│ Detect   │──▶│ Correlate│──▶│ Alert    │
│          │   │          │   │          │   │          │   │ & Route  │
│ Multi-   │   │ Context  │   │ Multi-   │   │ Cross-   │   │ Severity │
│ source   │   │ & Norm   │   │ engine   │   │ signal   │   │ & Escalate│
│ streams  │   │          │   │          │   │ fusion   │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

### Stage 1: Data Ingestion (§12.2.1)

```python
from grc_incident_mgmt.detection import DetectionPipeline, SignalSource

pipeline = DetectionPipeline()

# Ingest from multiple sources
pipeline.ingestion.ingest(SignalSource.AI_RISK_RADAR, {
    "category": "PI", "subcategory_code": "PI-3",
    "confidence": 0.92, "text": "ignore previous instructions",
    "asset_id": "model-gpt4-001", "environment": "production",
})

# Batch ingestion
pipeline.ingestion.ingest_batch(SignalSource.POLICY_ENGINE, [
    {"category": "DL", "subcategory_code": "DL-1", "pii_detected": True},
    {"category": "HO", "subcategory_code": "HO-1", "toxicity_score": 0.85},
])
```

**Sources:** AI-Risk-Radar, Policy Engine, Model Inference Logs, Audit Trails, User Reports, External Feeds, Red Team Results, Infrastructure Metrics

### Stage 2: Data Enrichment (§12.2.2)

```python
# Register assets for context enrichment
pipeline.enrichment.register_asset("model-gpt4-001", {
    "type": "model", "criticality": "high", "version": "4.0.1",
})

# Add threat intelligence
pipeline.enrichment.update_threat_intel({
    "active_campaigns": ["APT-2026-AI"],
    "recent_cves": ["CVE-2026-12345"],
})
```

**Enrichment dimensions:** Asset Context, User Context, Historical Context, Threat Context (MITRE ATLAS), Temporal Context, Data Classification

### Stage 3: Detection Engines (§12.2.3)

```python
from grc_incident_mgmt.detection import (
    SignatureEngine, AnomalyEngine, MLClassifierEngine,
    BehavioralEngine, SemanticEngine, PolicyEngine,
)

# Signature Engine — pattern matching, regex, YARA rules
sig = SignatureEngine()
sig.add_pattern("PI-1", r"ignore\s+previous\s+instructions")

# Anomaly Engine — statistical baselines, z-score
anomaly = AnomalyEngine(z_threshold=3.0)
anomaly.set_baseline("api_call_rate", [100, 105, 98, 102, 110, 95, 103])

# ML Classifier — supervised models
ml = MLClassifierEngine()

# Behavioral Engine — sequence analysis
behavioral = BehavioralEngine()
behavioral.register_normal_sequence("agent-001", ["search", "summarize", "respond"])

# Semantic Engine — embedding similarity
semantic = SemanticEngine(similarity_threshold=0.3)

# Policy Engine — rule-based policy evaluation
policy = PolicyEngine()
policy.add_policy({
    "id": "POL-001", "name": "No PII in outputs",
    "condition": {"field": "pii_detected", "op": "eq", "value": True},
    "action": "alert", "severity": "S2", "category": "DL",
})

# Register all engines
for engine in [sig, anomaly, ml, behavioral, semantic, policy]:
    pipeline.register_engine(engine)
```

| Engine | Technique | Categories | Latency |
|--------|-----------|------------|---------|
| Signature | Pattern matching, regex, YARA | PI, MP, SC | <50ms |
| Anomaly | Statistical baselines, z-score | DL, WA, AM | <200ms |
| ML Classifier | Supervised models | HO, HL, DL | <100ms |
| Behavioral | Sequence analysis, Markov chains | AM, WA | <500ms |
| Semantic | Embedding similarity, drift detection | HL, PI | <300ms |
| Policy | Rule-based evaluation | All | Real-time |

### Stage 4: Signal Correlation (§12.2.4)

```python
# Default correlation rules (CORR-001 through CORR-005) are built-in:
#   CORR-001: Escalating Injection — ≥3 PI signals in 10 min → S2
#   CORR-002: Data Exfiltration Pattern — DL + API volume + off-hours → S1
#   CORR-003: Agent Cascade Failure — WA + error spike + resource exhaustion → S1
#   CORR-004: Model Degradation — HL increase + confidence drop + complaints → S3
#   CORR-005: Supply Chain Cascade — SC + multiple dependent systems → S2

# Add custom correlation rule
from grc_incident_mgmt.detection import CorrelationRule
from grc_incident_mgmt.taxonomy import Severity

pipeline.correlation.add_rule(CorrelationRule(
    rule_id="CORR-006", name="Custom Escalation",
    condition=lambda sigs: len(sigs) >= 5,
    action="escalate_s2", severity=Severity.S2_HIGH,
))
```

### Stage 5: Alerting & Routing (§12.2.5)

```python
# Process a signal through the full pipeline
alert = pipeline.process_signal(SignalSource.AI_RISK_RADAR, {
    "category": "PI", "subcategory_code": "PI-3",
    "confidence": 0.92, "text": "ignore previous instructions",
    "asset_id": "model-gpt4-001", "environment": "production",
})

if alert:
    print(f"Severity: {alert.severity.value}")
    print(f"Action: {alert.action}")
    print(f"Notifications: {alert.notifications}")
```

| Confidence | Severity | Action | Notification |
|------------|----------|--------|--------------|
| ≥0.95 | S1/S2 | Auto-classify, auto-contain, immediate alert | PagerDuty + SMS + Slack + Email |
| 0.80–0.94 | Any | Auto-classify, alert human for containment | Slack + Email |
| 0.60–0.79 | Any | Flag for human review, queue for triage | Slack (low priority) |
| <0.60 | — | Log for pattern analysis | Dashboard only |

---

## 3. Incident Classification

**Module:** `grc_incident_mgmt/classification.py`  
**Spec:** §14 — Incident Severity Auto-Classification

### Weighted Scoring Algorithm (§14.3)

```
Severity_Score = Σ(Factor_i × Weight_i × Normalized_Value_i)

Score ≥ 0.85 → S1 (Critical)
Score 0.70–0.84 → S2 (High)
Score 0.50–0.69 → S3 (Medium)
Score 0.30–0.49 → S4 (Low)
Score < 0.30 → S5 (Informational)
```

### Classification Factors (§14.2)

**Signal-Based Factors:**

| Factor | Weight | Description |
|--------|--------|-------------|
| Incident Category | 20% | Per-category base severity |
| Detection Confidence | 15% | Signal confidence score |
| Signal Velocity | 10% | Rate of signal generation |
| Signal Diversity | 10% | Number of distinct signals |
| Corroboration | 15% | Independent source confirmation |

**Asset-Based Factors:**

| Factor | Weight | Description |
|--------|--------|-------------|
| Asset Criticality | 15% | Business criticality |
| User Impact | 10% | Number of users affected |
| Data Sensitivity | 10% | Data classification level |
| Environment | 5% | Production > staging > development |

**Historical Factors:**

| Factor | Weight | Description |
|--------|--------|-------------|
| Similar Incidents | 10% | Severity of similar past incidents |
| Recurrence | 5% | Whether type has recurred |
| Trend | 5% | Whether frequency is increasing

### Usage

```python
from grc_incident_mgmt.classification import (
    SeverityClassificationEngine, RuleBasedClassifier, ClassificationFeedbackLoop,
)
from grc_incident_mgmt.models import DetectionSignal
from grc_incident_mgmt.taxonomy import IncidentCategory

engine = SeverityClassificationEngine()

signal = DetectionSignal(
    category=IncidentCategory.PROMPT_INJECTION,
    subcategory_code="PI-3",
    confidence=0.95,
    raw_data={
        "signal_velocity": 0.9, "signal_diversity": 0.8,
        "corroboration": 0.9, "asset_criticality": 0.95,
        "user_impact": 0.85, "data_sensitivity": 0.9,
    },
    environment="production",
)

result = engine.classify(signal)
print(f"Severity: {result.severity.value}")       # S1
print(f"Confidence: {result.confidence:.2f}")     # 0.96
print(f"Auto-apply: {result.auto_apply}")         # True
print(f"Explanation: {result.explanation}")
```

### Override Rules (§14.5)

```python
# Built-in overrides:
#   Regulatory Trigger     — PII breach >1,000 records → S2
#   Active Exploitation     — Confirmed active attack → S2
#   Physical Harm           — Physical harm caused/possible → S1
#   Critical Infrastructure — Affects critical infrastructure → S1
#   Mass Impact             — >10,000 users affected → S1
#   Media Attention         — Media attention → S2
#   Executive Involvement   — CISO/executive notified → S2
#   Cross-Border            — Multiple jurisdictions → S2
```

### Rule-Based Classification (§4.2)

```python
impact = RuleBasedClassifier.assess_impact(
    individuals_affected=500, records_affected=5000,
    financial_loss_usd=2_000_000, system_compromise="major",
)
severity = RuleBasedClassifier.classify(impact, "likely")
# → S2 (High)
```

### Feedback Loop (§14.7)

```python
feedback = ClassificationFeedbackLoop()
feedback.record_feedback("INC-001", Severity.S1_CRITICAL, Severity.S2_HIGH, "Analyst downgraded")
accuracy = feedback.get_accuracy()
# → {"exact_match": 0.0, "within_one_level": 1.0, "total": 1}
```

---

## 4. Incident Response Orchestration

**Module:** `grc_incident_mgmt/orchestration.py`  
**Spec:** §13 — Incident Response Orchestration with Runbooks

### Runbook Structure (§13.2)

```python
from grc_incident_mgmt.orchestration import (
    Runbook, RunbookTrigger, RunbookAction, ActionType, OnFailure, ExecutionMode,
)

runbook = Runbook(
    id="RB-PI-003", name="Jailbreak Response", version="1.0",
    trigger=RunbookTrigger(
        subcategory_code="PI-3", severity=["S1", "S2"],
    ),
    preconditions=["affected_asset_registered"],
    actions=[
        RunbookAction("1", "Block Jailbreak Patterns", ActionType.API_CALL,
                      "policy_engine", {"action": "block_patterns"}),
        RunbookAction("2", "Suspend Affected Model", ActionType.API_CALL,
                      "model_registry", {"action": "suspend"},
                      on_failure=OnFailure.ESCALATE),
        RunbookAction("3", "Preserve Evidence", ActionType.API_CALL,
                      "evidence_service", {"preserve_logs": True}),
    ],
    postconditions=["affected_model_suspended", "evidence_preserved"],
    execution_mode=ExecutionMode.FULLY_AUTOMATED,
)
```

### Default Runbook Library (§13.3)

```python
from grc_incident_mgmt.orchestration import create_default_runbooks

runbooks = create_default_runbooks()
# 15 runbooks covering all 8 categories:
#   RB-DL-001 … RB-DL-002  (Data Leakage)
#   RB-HO-001 … RB-HO-005  (Harmful Output)
#   RB-WA-001 … RB-WA-005  (Wrong Action)
#   RB-HL-001 … RB-HL-004  (Hallucination)
#   RB-PI-001 … RB-PI-005  (Prompt Injection)
#   RB-MP-001 … RB-MP-005  (Model Poisoning)
#   RB-SC-001 … RB-SC-005  (Supply Chain)
#   RB-AM-001 … RB-AM-006  (Agent Misbehavior)
```

### Execution

```python
from grc_incident_mgmt.orchestration import RunbookEngine, KillSwitch, OrchestrationStateMachine
from grc_incident_mgmt.models import Incident, IncidentStatus
from grc_incident_mgmt.taxonomy import IncidentCategory, Severity

engine = RunbookEngine()
for rb in create_default_runbooks():
    engine.register_runbook(rb)

incident = Incident(
    category=IncidentCategory.PROMPT_INJECTION,
    subcategory_code="PI-3",
    severity=Severity.S1_CRITICAL,
    confidence=0.95,
)

# Find and execute matching runbook
matches = engine.find_matching_runbooks(incident)
if matches:
    execution = engine.execute_runbook(matches[0].id, incident)
    print(f"Status: {execution.status}")
    print(f"Actions completed: {execution.actions_completed}")

# Kill switch (§5.4.2)
kill_switch = KillSwitch()
kill_switch.activate(incident, "Jailbreak detected", "automated_system")

# State machine (§13.6)
sm = OrchestrationStateMachine()
sm.transition(incident, IncidentStatus.TRIAGED)
sm.transition(incident, IncidentStatus.CONTAINED)
```

### Execution Modes (§13.4)

| Mode | Description | Use Case |
|------|-------------|----------|
| Fully Automated | No human intervention | S1, confidence ≥0.95, well-tested |
| Human-in-the-Loop | Pauses for approval | S2, irreversible actions, novel |
| Advisory | Generates recommendations | S3/S4, complex scenarios |
| Simulation | Sandbox execution | Testing, training, dry runs |

---

## 5. Incident Reporting

**Module:** `grc_incident_mgmt/reporting.py`  
**Spec:** §6 — Incident Reporting Format

### Report Structure (§6.1)

```python
from grc_incident_mgmt.reporting import IncidentReportGenerator

generator = IncidentReportGenerator()
report = generator.generate(incident)

# JSON format
json_report = generator.generate_json(incident)

# Executive summary (§6.2)
summary = generator.generate_executive_summary(incident)
# → {incident_id, date_time, category, severity, status, affected_systems, ...}
```

### EU AI Act Article 73 Reporting (§6.3)

```python
from grc_incident_mgmt.reporting import Article73Reporter

reporter = Article73Reporter()
assessment = reporter.assess_applicability(incident)
# → {"applicable": True, "criteria_met": [...], "deadline_timestamp": "..."}

notification = reporter.generate_notification(incident)
# → Full Article 73 notification content
```

### Report Formats

```python
from grc_incident_mgmt.reporting import ReportFormatter

# Markdown
md = ReportFormatter.to_markdown(report)

# CSV summary
csv = ReportFormatter.to_csv_summary([report1, report2, ...])
```

### Internal Reporting Cadence (§6.4)

```python
from grc_incident_mgmt.reporting import ReportingCadence

cadence = ReportingCadence()
cadence.schedule_incident_alert(incident, ["security-team", "ciso"])
cadence.schedule_status_update(incident, ["response-team"])
cadence.schedule_incident_summary(incident, ["all-stakeholders"])
cadence.schedule_post_incident_report(incident, ["management"])
```

---

## 6. Post-Incident Learning

**Module:** `grc_incident_mgmt/learning.py`  
**Spec:** §15 — Post-Incident Learning Loop

### Immediate Learning (§15.2)

```python
from grc_incident_mgmt.learning import ImmediateLearning

immediate = ImmediateLearning()

# Capture incident data within 24h of closure
data = immediate.capture_incident_data(incident)

# Detection gap analysis
gap = immediate.analyze_detection_gap(incident)
print(f"Detection gap: {gap.detection_gap_seconds}s")
print(f"Could detect earlier: {gap.could_detect_earlier}")

# Response effectiveness
effectiveness = immediate.analyze_response_effectiveness(incident)
print(f"SLA compliant: {effectiveness.sla_compliant}")
```

### Tactical Learning (§15.3)

```python
from grc_incident_mgmt.learning import TacticalLearning

tactical = TacticalLearning()

# Detection rule updates
tactical.create_detection_rule_update(
    "new_signature", "Add jailbreak pattern", incident.incident_id
)

# Runbook updates
tactical.create_runbook_update(
    "action_addition", "RB-PI-003", "Add input sanitization", incident.incident_id
)

# Monthly review
review = tactical.conduct_monthly_review(incidents)
```

### Strategic Learning (§15.4)

```python
from grc_incident_mgmt.learning import StrategicLearning

strategic = StrategicLearning()

# Control effectiveness assessment
assessment = strategic.assess_control_effectiveness("detective", incidents)

# Knowledge base
strategic.update_knowledge_base("incident_patterns", {
    "pattern": "jailbreak_via_adversarial_prompt",
    "category": "PI-3",
})

# Quarterly review
quarterly = strategic.conduct_quarterly_review(incidents)
```

### Recommendation Tracking (§7.6)

```python
from grc_incident_mgmt.learning import RecommendationTracker

tracker = RecommendationTracker()
tracker.add_recommendation(Recommendation(
    description="Implement continuous safety testing",
    priority="immediate", owner="Security Team", due_date="2026-10-08",
))
tracker.update_status(rec_id, "completed")
print(f"Implementation rate: {tracker.get_implementation_rate():.0%}")
```

### Knowledge Management (§7.7)

```python
from grc_incident_mgmt.learning import KnowledgeBase

kb = KnowledgeBase()
kb.add_incident_pattern({"pattern": "jailbreak_via_adversarial_prompt"})
kb.add_root_cause({"cause": "outdated_safety_classifier"})
kb.add_effective_response({"strategy": "immediate_model_suspension"})
kb.add_failed_response({"strategy": "output_filtering_only", "reason": "too slow"})
```

---

## 7. Incident Trend Analysis

**Module:** `grc_incident_mgmt/trends.py`  
**Spec:** §16 — Incident Trend Analysis and Prediction

### Temporal Trends (§16.3.1)

```python
from grc_incident_mgmt.trends import TemporalTrendAnalyzer

analyzer = TemporalTrendAnalyzer()
trend = analyzer.analyze(incidents, period="daily")
print(f"Direction: {trend.trend_direction}")
print(f"Seasonality: {trend.seasonality_detected}")
print(f"Change points: {trend.change_points}")
```

### Category Trends (§16.3.2)

```python
from grc_incident_mgmt.trends import CategoryTrendAnalyzer

cat_analyzer = CategoryTrendAnalyzer()
result = cat_analyzer.analyze(incidents)
print(f"Distribution: {result.category_distribution}")
print(f"Emerging: {result.emerging_categories}")
print(f"Growth rates: {result.growth_rates}")
```

### Severity Trends (§16.3.3)

```python
from grc_incident_mgmt.trends import SeverityTrendAnalyzer

sev_analyzer = SeverityTrendAnalyzer()
result = sev_analyzer.analyze(incidents)
print(f"Escalation: {result.escalation_trend}")
print(f"High severity ratio: {result.high_severity_ratio:.0%}")
```

### Asset Risk Scores (§16.5.1)

```python
from grc_incident_mgmt.trends import AssetTrendAnalyzer

asset_analyzer = AssetTrendAnalyzer()
risk = asset_analyzer.compute_risk_score(
    "model-001", "GPT-4 Production", incidents,
    threat_exposure=0.7, asset_criticality=0.9,
    control_maturity=0.6, change_velocity=0.8,
)
print(f"Risk score: {risk.risk_score:.1f} ({risk.risk_level})")
```

### Predictive Models (§16.4)

```python
from grc_incident_mgmt.trends import VolumePredictor, SeverityPredictor

# Volume prediction
predictor = VolumePredictor()
prediction = predictor.predict(incidents, horizon_days=30)
print(f"Predicted: {prediction.predicted_count} incidents")

# Severity prediction
sev_predictor = SeverityPredictor()
sev_prediction = sev_predictor.predict(incidents)
print(f"High severity probability: {sev_prediction.high_severity_probability:.0%}")
```

### Early Warning System (§16.6)

```python
from grc_incident_mgmt.trends import EarlyWarningSystem

ews = EarlyWarningSystem()
warnings = ews.check_indicators(incidents)
for w in warnings:
    action = ews.get_response_action(w.level)
    print(f"{w.indicator}: {w.level.value} → {action['action']} ({action['timeline']})")
```

### Organizational Risk Score (§16.5.2)

```python
from grc_incident_mgmt.trends import OrganizationalRiskScorer

scorer = OrganizationalRiskScorer()
org_risk = scorer.compute(
    asset_scores=[risk], incidents=incidents,
    detection_coverage=0.9, response_readiness=0.8, regulatory_compliance=1.0,
)
print(f"Organizational risk: {org_risk.overall_score:.1f} ({org_risk.risk_level})")
```

---

## 8. Regulatory Reporting

**Module:** `grc_incident_mgmt/regulatory.py`  
**Spec:** §17 — Regulatory Reporting Automation

### Supported Regulations (§17.2)

| Regulation | Jurisdiction | Trigger | Deadline |
|------------|-------------|---------|----------|
| EU AI Act Art. 73 | EU | Serious incident | 24h (S1), 72h (S2) |
| EU AI Act Art. 86 | EU | Serious incident (deployer) | 24h (S1), 72h (S2) |
| GDPR Art. 33 | EU/EEA | Personal data breach | 72 hours |
| GDPR Art. 34 | EU/EEA | High-risk data breach | Without undue delay |
| NIS2 Directive | EU | Significant incident | 24h / 72h |
| SEC Cybersecurity Rules | US | Material cyber incident | 4 business days |
| CIRCIA | US | Significant cyber incident | 72 hours |
| PIPEDA | Canada | Breach of security safeguards | As soon as feasible |
| APRA CPS 234 | Australia | Material info security incident | 72 hours |
| DORA | EU | Major ICT-related incident | 4h / 72h / 1 month |

### Applicability Assessment (§17.3)

```python
from grc_incident_mgmt.regulatory import ApplicabilityAssessmentEngine

assessor = ApplicabilityAssessmentEngine()
result = assessor.assess_all(incident)

for reg in result["applicable_regulations"]:
    print(f"{reg['regulation']}: deadline={reg['deadline']}")
    print(f"  Criteria: {reg['criteria_met']}")
    print(f"  Recipient: {reg['recipient']}")
```

### Report Generation (§17.4)

```python
from grc_incident_mgmt.regulatory import ReportGenerator

generator = ReportGenerator()
report = generator.generate("TPL-EU-AIA-73", incident)
print(f"Auto-populated: {len(report['auto_populated'])} fields")
print(f"Manual: {len(report['manual'])} fields")
print(f"Auto-population rate: {generator.get_auto_population_rate(report):.0%}")
```

### Deadline Management (§17.5)

```python
from grc_incident_mgmt.regulatory import DeadlineManager

dm = DeadlineManager()
dm.create_tracker("EU AI Act Art. 73", incident.incident_id, "2026-10-02T12:00:00+00:00", 24)

# Check deadlines and get escalation alerts
alerts = dm.check_deadlines()
for alert in alerts:
    print(f"{alert['regulation']}: {alert['elapsed_pct']:.0%} elapsed")
    print(f"  Action: {alert['action']}")
    print(f"  Recipients: {alert['recipients']}")
```

### Submission Tracking (§17.6)

```python
from grc_incident_mgmt.regulatory import SubmissionTracker

tracker = SubmissionTracker()
sub = tracker.create_submission("EU AI Act Art. 73", incident.incident_id, report)
tracker.update_status(sub.submission_id, "submitted")
```

### Compliance Dashboard (§17.8)

```python
from grc_incident_mgmt.regulatory import ComplianceDashboard

dashboard = ComplianceDashboard()
data = dashboard.get_dashboard()
print(f"Compliance rate: {data['compliance_rate']:.0%}")
print(f"Pending notifications: {data['pending_notifications']}")
```

---

## 9. Quick Start

```bash
# Run the end-to-end demo
cd /Users/ahmedhassan/grc-claw-incident-management
python3 demo.py
```

### Minimal Example

```python
from grc_incident_mgmt import IncidentCategory, Severity
from grc_incident_mgmt.detection import DetectionPipeline, SignalSource, SignatureEngine
from grc_incident_mgmt.classification import SeverityClassificationEngine
from grc_incident_mgmt.orchestration import RunbookEngine, create_default_runbooks
from grc_incident_mgmt.reporting import IncidentReportGenerator

# 1. Detect
pipeline = DetectionPipeline()
pipeline.register_engine(SignatureEngine())
alert = pipeline.process_signal(SignalSource.AI_RISK_RADAR, {
    "category": "PI", "subcategory_code": "PI-3",
    "confidence": 0.92, "text": "ignore previous instructions",
    "asset_id": "model-001", "environment": "production",
})

# 2. Classify
classifier = SeverityClassificationEngine()
result = classifier.classify(alert.signal)

# 3. Respond
engine = RunbookEngine()
for rb in create_default_runbooks():
    engine.register_runbook(rb)
matches = engine.find_matching_runbooks(incident)
if matches:
    engine.execute_runbook(matches[0].id, incident)

# 4. Report
generator = IncidentReportGenerator()
report = generator.generate(incident)
```

---

## 10. Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GRC_Claw Incident Management                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  ┌───────────┐ │
│  │Detection │→ │Classification│→ │ Orchestration │→ │ Reporting │ │
│  │Pipeline  │  │  Engine      │  │   Engine      │  │ Generator │ │
│  │(§12)     │  │  (§14)       │  │   (§13)       │  │ (§6)      │ │
│  └──────────┘  └──────────────┘  └───────────────┘  └───────────┘ │
│       │              │                  │                  │        │
│       ▼              ▼                  ▼                  ▼        │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  ┌───────────┐ │
│  │ Learning │  │    Trend     │  │  Regulatory   │  │Knowledge  │ │
│  │  Loop    │  │  Analysis    │  │  Reporting    │  │  Base     │ │
│  │ (§15)    │  │  (§16)       │  │   (§17)       │  │ (§7.7)    │ │
│  └──────────┘  └──────────────┘  └───────────────┘  └───────────┘ │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  Taxonomy: 8 categories × 44 subcategories × 5 severity levels       │
│  Response: 6-phase workflow (Detect→Triage→Contain→Eradicate→       │
│            Recover→Review)                                           │
│  Runbooks: 15 default runbooks covering all incident types          │
│  Regulations: 10 supported (EU AI Act, GDPR, NIS2, SEC, etc.)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

*End of Implementation Guide*
