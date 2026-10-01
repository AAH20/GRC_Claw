"""
GRC_Claw Incident Management — Complete Implementation Guide
=============================================================

Reference: GRC-AIM-001 v2.0 — GRC_Claw AI Incident Management Specification

This guide provides a complete, working implementation of the GRC_Claw AI
incident management framework, covering all 7 core capabilities:

    1. Incident Detection Pipeline (§12)
    2. Incident Classification (§14)
    3. Incident Response Orchestration (§13)
    4. Incident Reporting (§6)
    5. Post-Incident Learning (§15)
    6. Incident Trend Analysis (§16)
    7. Regulatory Reporting (§17)

Quick Start
-----------

>>> from grc_incident_mgmt.detection import DetectionPipeline, SignalSource
>>> from grc_incident_mgmt.classification import SeverityClassificationEngine
>>> from grc_incident_mgmt.orchestration import RunbookEngine, create_default_runbooks
>>> from grc_incident_mgmt.reporting import IncidentReportGenerator
>>> from grc_incident_mgmt.regulatory import ApplicabilityAssessmentEngine

>>> # 1. Set up detection pipeline
>>> pipeline = DetectionPipeline()
>>> pipeline.register_engine(SignatureEngine())
>>> pipeline.register_engine(MLClassifierEngine())

>>> # 2. Process a signal
>>> alert = pipeline.process_signal(SignalSource.AI_RISK_RADAR, {
...     "category": "PI", "subcategory_code": "PI-3",
...     "confidence": 0.92, "text": "ignore previous instructions",
...     "asset_id": "model-001", "environment": "production"
... })

>>> # 3. Classify severity
>>> classifier = SeverityClassificationEngine()
>>> result = classifier.classify(alert.signal)
>>> print(f"Severity: {result.severity.value}, Confidence: {result.confidence:.2f}")

>>> # 4. Execute runbook
>>> engine = RunbookEngine()
>>> for rb in create_default_runbooks():
...     engine.register_runbook(rb)
>>> incident = Incident(category=IncidentCategory.PROMPT_INJECTION, ...)
>>> execution = engine.execute_runbook("RB-PI-003", incident)

>>> # 5. Generate report
>>> generator = IncidentReportGenerator()
>>> report = generator.generate(incident)

>>> # 6. Assess regulatory applicability
>>> assessor = ApplicabilityAssessmentEngine()
>>> assessment = assessor.assess_all(incident)

Package Structure
-----------------
grc_incident_mgmt/
├── __init__.py        — Package exports
├── taxonomy.py        — 8 categories, 44 subcategories, severity levels (§3)
├── models.py          — Core data models (§6.1)
├── detection.py       — 5-stage detection pipeline (§12)
├── classification.py  — Severity auto-classification (§14)
├── orchestration.py  — Runbook engine + state machine (§13)
├── reporting.py       — Report generation + formatting (§6)
├── learning.py        — Post-incident learning loop (§15)
├── trends.py          — Trend analysis + prediction (§16)
└── regulatory.py      — Regulatory reporting automation (§17)

Taxonomy Overview (§3)
-----------------------
8 Categories × 44 Subcategories:

    DL — Data Leakage        (DL-1 … DL-6)   Min Severity: S2
    HO — Harmful Output      (HO-1 … HO-6)   Min Severity: S2
    WA — Wrong Action        (WA-1 … WA-6)   Min Severity: S2
    HL — Hallucination       (HL-1 … HL-6)   Min Severity: S3
    PI — Prompt Injection    (PI-1 … PI-6)   Min Severity: S2
    MP — Model Poisoning     (MP-1 … MP-6)   Min Severity: S1
    SC — Supply Chain        (SC-1 … SC-5)   Min Severity: S3
    AM — Agent Misbehavior   (AM-1 … AM-6)   Min Severity: S1

Severity Levels (§4.1)
---------------------
    S1 — Critical    (15 min response, 24h regulatory notification)
    S2 — High        (1 hour response, 72h regulatory notification)
    S3 — Medium      (4 hour response, case-by-case regulatory)
    S4 — Low         (24 hour response, no regulatory notification)
    S5 — Informational (72 hour response, no regulatory notification)

Response Phases (§5.1)
---------------------
    Detect → Triage → Contain → Eradicate → Recover → Review
"""
