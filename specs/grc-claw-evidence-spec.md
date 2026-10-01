# GRC_Claw Compliance Evidence Specification

**Version:** 1.1  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team

---

## 1. Purpose & Scope

This specification defines how GRC_Claw collects, stores, verifies, analyzes, and exports compliance evidence for auditor consumption. It establishes a unified, OSCAL-based evidence format that addresses the industry gap where no standardized evidence format exists and audit trail integrity is the exception rather than the norm. The specification covers the full evidence lifecycle from collection through analytics-driven decision support and export.

**In scope:** Evidence lifecycle from collection through export for all GRC_Claw compliance controls, including evidence quality scoring, completeness analysis, gap analysis, trend analysis, evidence-based decision support, and visualization/reporting.  
**Out of scope:** Control implementation details, remediation workflows, auditor identity management.

---

## 2. Evidence Format (OSCAL-Based)

### 2.1 Core Schema

All evidence conforms to the OSCAL 1.1.0 assessment-results and assessment-plans schemas, extended with GRC_Claw-specific metadata.

```json
{
  "grc-evidence": {
    "uuid": "uuid-v4",
    "metadata": {
      "title": "string",
      "description": "string",
      "version": "1.0",
      "published": "ISO-8601 timestamp",
      "last-modified": "ISO-8601 timestamp",
      "oscal-version": "1.1.0"
    },
    "control-mapping": {
      "control-id": "string (e.g., AC-2, AU-6, SI-4)",
      "framework": "string (e.g., NIST-800-53, SOC2, ISO-27001)",
      "control-title": "string",
      "control-family": "string"
    },
    "evidence-items": [
      {
        "evidence-id": "uuid-v4",
        "type": "artifact|observation|interview|analysis|log",
        "collected-by": "string (agent-id or user-id)",
        "collected-at": "ISO-8601 timestamp",
        "source-system": "string",
        "source-location": "string (URI or path)",
        "content": {
          "format": "string (mime-type)",
          "data": "base64-encoded or inline",
          "hash": {
            "algorithm": "SHA-256",
            "value": "hex-string"
          }
        },
        "context": {
          "environment": "string (prod, staging, dev)",
          "resource-scope": "string",
          "time-window": {
            "start": "ISO-8601 timestamp",
            "end": "ISO-8601 timestamp"
          }
        },
        "chain-of-custody": [
          {
            "action": "collected|transferred|verified|exported",
            "actor": "string",
            "timestamp": "ISO-8601 timestamp",
            "hash": "hex-string"
          }
        ]
      }
    ],
    "assessment-results": {
      "observations": [],
      "findings": [],
      "risks": []
    }
  }
}
```

### 2.2 Evidence Types

| Type | Description | Source |
|------|-------------|--------|
| `artifact` | Configuration files, policy documents, screenshots | File system, APIs |
| `observation` | Runtime system state, process listings | Agent probes |
| `interview` | Human attestations, sign-offs | Manual input |
| `analysis` | Derived conclusions from multiple evidence items | GRC_Claw analysis engine |
| `log` | Audit logs, event trails, change records | SIEM, cloud APIs |

### 2.3 Control Mapping

Every evidence item MUST map to at least one control identifier from a recognized framework:

- **NIST 800-53 Rev 5** — primary framework
- **SOC 2 Trust Services Criteria** — commercial compliance
- **ISO 27001:2022** — international standard
- **CIS Controls v8** — implementation benchmark

Mapping is stored in `control-mapping` and validated at collection time.

---

## 3. Evidence Collection Pipeline

### 3.1 Pipeline Architecture

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Collectors │───▶│  Normalizer  │───▶│  Validator   │───▶│  Evidence    │
│  (Agents)   │    │  (OSCAL)     │    │  (Schema)    │    │  Store       │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │                  │                   │                   │
       ▼                  ▼                   ▼                   ▼
  Raw evidence      Canonical format    Integrity check      Immutable
  (heterogeneous)   (OSCAL JSON)        (hash + schema)      storage
```

### 3.2 Collection Stages

#### Stage 1: Discovery & Scheduling

- **Control inventory** loaded from framework definitions
- **Collection schedule** generated per control (continuous, daily, weekly, event-triggered)
- **Collector agents** assigned to controls based on resource scope

#### Stage 2: Collection

Collectors gather evidence through:

1. **API queries** — cloud provider APIs (AWS Config, Azure Policy, GCP Security Command Center)
2. **Agent probes** — lightweight agents on target systems executing read-only queries
3. **File ingestion** — configuration files, policy documents, exported reports
4. **Log streaming** — SIEM integration, cloud trail logs
5. **Manual upload** — human-provided evidence with attestation

Each collection event produces a raw evidence record with:
- Source identifier and timestamp
- Collector identity and version
- Raw content (preserved byte-for-byte)
- Collection context (environment, scope, authorization)

#### Stage 3: Normalization

Raw evidence is transformed into the OSCAL-based format:

1. **Parse** — extract structured data from raw format
2. **Map** — associate with control identifiers
3. **Enrich** — add metadata (environment, resource scope, time window)
4. **Hash** — compute SHA-256 of canonical content
5. **Timestamp** — apply trusted timestamp (RFC 3161)

#### Stage 4: Validation

Before entering the evidence store, each item passes:

1. **Schema validation** — OSCAL 1.1.0 JSON Schema conformance
2. **Completeness check** — all required fields present
3. **Control mapping validation** — control ID exists in target framework
4. **Hash verification** — content integrity confirmed
5. **Duplicate detection** — no identical evidence already stored

### 3.3 Collection Schedule

| Evidence Class | Frequency | Trigger |
|----------------|-----------|---------|
| Configuration state | Continuous | Change detection |
| Access reviews | Daily | Scheduled |
| Vulnerability scans | Weekly | Scheduled |
| Log analysis | Continuous | Stream |
| Policy compliance | Daily | Scheduled |
| Penetration test results | Quarterly | Event |
| Manual attestations | As needed | Event |

---

## 4. Evidence Verification Mechanism

### 4.1 Integrity Verification

Every evidence item carries a cryptographic hash computed at collection time:

```
hash = SHA-256(canonical_json(content))
```

Verification recomputes the hash and compares against the stored value. Any mismatch triggers an integrity alert.

### 4.2 Chain of Custody

An append-only log tracks every interaction with evidence:

```json
{
  "custody-event": {
    "event-id": "uuid-v4",
    "evidence-id": "uuid-v4",
    "action": "collected|verified|exported|accessed",
    "actor": "string (agent or user identity)",
    "timestamp": "ISO-8601 timestamp",
    "evidence-hash": "hex-string",
    "previous-event-hash": "hex-string",
    "signature": "base64-encoded ECDSA signature"
  }
}
```

This creates a tamper-evident chain: each event references the previous event's hash, making any modification detectable.

### 4.3 Verification Levels

| Level | Name | Description |
|-------|------|-------------|
| L0 | Unverified | Collected but not yet validated |
| L1 | Schema-valid | Passes OSCAL schema validation |
| L2 | Integrity-verified | Hash matches, chain of custody intact |
| L3 | Cross-validated | Corroborated by independent evidence source |
| L4 | Attested | Signed by authorized human reviewer |

### 4.4 Automated Verification Checks

1. **Temporal consistency** — evidence timestamps within expected windows
2. **Source authenticity** — collector identity verified via mTLS or signed tokens
3. **Content plausibility** — values within expected ranges (e.g., no future dates)
4. **Cross-reference integrity** — referenced resources exist and are accessible
5. **Completeness** — all required evidence for a control is present

### 4.5 Continuous Re-verification

- **Daily:** Hash re-verification of all stored evidence
- **Weekly:** Chain-of-custody integrity check
- **Monthly:** Cross-validation against live system state
- **Quarterly:** Full evidence package regeneration and comparison

---

## 5. Evidence Package Export Format

### 5.1 Package Structure

Exported evidence packages are self-contained, signed archives:

```
grc-evidence-package/
├── manifest.json              # Package metadata and index
├── evidence/
│   ├── control-AU-6/
│   │   ├── evidence-001.json
│   │   ├── evidence-002.json
│   │   └── attachments/
│   │       ├── log-export.csv
│   │       └── screenshot.png
│   ├── control-AC-2/
│   │   └── ...
│   └── ...
├── oscal/
│   ├── assessment-plan.json
│   ├── assessment-results.json
│   └── catalog.json
├── chain-of-custody/
│   ├── custody-log.jsonl
│   └── custody-signatures/
│       └── ...
├── signatures/
│   ├── package-signature.json
│   └── timestamp-token.tsr
└── README.md                  # Human-readable package guide
```

### 5.2 Manifest Format

```json
{
  "manifest": {
    "package-id": "uuid-v4",
    "package-version": "1.0",
    "generated-at": "ISO-8601 timestamp",
    "generated-by": "string (system identity)",
    "organization": "string",
    "assessment-period": {
      "start": "ISO-8601 timestamp",
      "end": "ISO-8601 timestamp"
    },
    "frameworks": ["NIST-800-53", "SOC2"],
    "controls-assessed": 42,
    "evidence-items": 156,
    "evidence-summary": {
      "by-type": {
        "artifact": 45,
        "observation": 67,
        "interview": 12,
        "analysis": 20,
        "log": 12
      },
      "by-verification-level": {
        "L0": 0,
        "L1": 10,
        "L2": 120,
        "L3": 20,
        "L4": 6
      }
    },
    "package-hash": {
      "algorithm": "SHA-256",
      "value": "hex-string"
    }
  }
}
```

### 5.3 Export Formats

| Format | Use Case | Content |
|--------|----------|---------|
| **JSON (OSCAL)** | Machine consumption, GRC tool import | Full OSCAL assessment-results |
| **PDF** | Human review, auditor sign-off | Formatted report with evidence summaries |
| **CSV/Spreadsheet** | Data analysis, sampling | Tabular evidence index |
| **XML (OSCAL)** | Legacy system integration | OSCAL XML representation |

### 5.4 Package Signing

Each package is signed to ensure authenticity and integrity:

1. **Canonical serialization** — package contents serialized deterministically
2. **Hash computation** — SHA-256 of canonical form
3. **Digital signature** — ECDSA P-256 signature over hash
4. **Trusted timestamp** — RFC 3161 timestamp token from TSA
5. **Signature embedding** — signature and timestamp stored in `signatures/`

### 5.5 Export Triggers

- **Scheduled:** Monthly and quarterly automatic package generation
- **On-demand:** Auditor request or compliance deadline
- **Event-driven:** Post-assessment, post-remediation
- **Continuous:** Real-time evidence stream for continuous auditing

### 5.6 Auditor Access

Auditors receive:

1. **Read-only access** to the evidence store via authenticated API
2. **Package download** in preferred format
3. **Verification tools** to independently verify hashes and signatures
4. **Query interface** to search and filter evidence by control, date, type
5. **Attestation workflow** to sign off on reviewed evidence

---

## 6. Evidence Quality Scoring

### 6.1 Quality Score Model

Every evidence item receives a composite quality score (0–100) computed at collection time and updated on each verification event. The score drives prioritization in gap analysis, auditor attention, and automated remediation workflows.

```
Quality Score = Σ (Dimension Weight × Dimension Score) / Σ (Dimension Weight)
```

| Dimension | Weight | Description | Scoring Method |
|-----------|--------|-------------|----------------|
| **Verification Depth** | 25% | Highest verification level achieved | L0=0, L1=25, L2=50, L3=75, L4=100 |
| **Source Reliability** | 20% | Trustworthiness of the collecting source | Agent-automated=100, API-query=90, File-ingestion=70, Manual-upload=50 |
| **Content Richness** | 15% | Completeness of evidence metadata and content | % of optional fields populated × 100 |
| **Temporal Relevance** | 15% | Recency relative to control's collection schedule | 100 × (1 - age/expiration_window), floor at 0 |
| **Cross-Validation** | 15% | Corroboration by independent evidence sources | 0 (none), 50 (one corroborating source), 100 (≥2 sources) |
| **Chain-of-Custody Integrity** | 10% | Completeness and continuity of custody events | % of expected custody events present × 100 |

### 6.2 Quality Tiers

| Tier | Score Range | Label | Auditor Treatment |
|------|-------------|-------|-------------------|
| **Q1** | 90–100 | Excellent | Accept without additional review |
| **Q2** | 70–89 | Good | Standard review; spot-check |
| **Q3** | 50–69 | Adequate | Enhanced review; corroborating evidence recommended |
| **Q4** | 30–49 | Poor | Requires remediation before acceptance |
| **Q5** | 0–29 | Unacceptable | Reject; re-collect evidence |

### 6.3 Quality Score Persistence

Quality scores are stored as part of the evidence metadata and updated whenever:

- A new verification event occurs (hash re-verification, cross-validation, attestation)
- The evidence ages (temporal relevance decays)
- A new corroborating evidence item is linked
- Chain-of-custody events are appended

```json
{
  "quality-score": {
    "overall": 82,
    "tier": "Q2",
    "dimensions": {
      "verification-depth": 75,
      "source-reliability": 100,
      "content-richness": 90,
      "temporal-relevance": 65,
      "cross-validation": 50,
      "chain-of-custody": 100
    },
    "computed-at": "2026-10-01T00:00:00Z",
    "score-history": [
      { "date": "2026-09-01", "score": 78 },
      { "date": "2026-10-01", "score": 82 }
    ]
  }
}
```

### 6.4 Quality Score Weighting by Control Risk Tier

Quality score thresholds for acceptance vary by the control's risk classification:

| Control Risk Tier | Minimum Acceptable Tier | Minimum Score |
|-------------------|------------------------|---------------|
| Critical | Q1 | 90 |
| High | Q2 | 70 |
| Medium | Q2 | 70 |
| Low | Q3 | 50 |

Evidence below the minimum threshold for its control's risk tier is flagged for remediation and excluded from framework satisfaction calculations until corrected.

---

## 7. Evidence Completeness Analysis

### 7.1 Completeness Dimensions

Completeness analysis evaluates whether all required evidence for a control is present, current, and sufficient for each applicable framework requirement. Four dimensions are assessed:

| Dimension | Question Answered | Data Sources |
|-----------|-------------------|--------------|
| **Presence** | Is evidence collected for every required evidence type? | Control definition `evidence_requirements` vs. stored evidence |
| **Currency** | Is all evidence within its validity window? | Evidence timestamps vs. expiration policy |
| **Coverage** | Does evidence cover all framework requirements the control maps to? | Spoke mappings vs. evidence `framework-applicability` |
| **Depth** | Does evidence meet the minimum verification level for each framework? | Evidence verification level vs. framework requirement |

### 7.2 Completeness Score

```
Completeness Score = (Present Required Evidence / Total Required Evidence) × 100
```

A control is **complete** when all four dimensions score 100%. Partial scores indicate specific gaps that feed into the gap analysis engine (Section 8).

### 7.3 Completeness Check Algorithm

```
For each control C in the unified control set:
  1. Load C's evidence_requirements (list of required evidence types)
  2. For each required evidence type T:
     a. Query evidence store for items matching (C.id, T)
     b. If no items found → GAP: missing evidence type
     c. If items found but all expired → GAP: stale evidence
     d. If items found but verification level < minimum → GAP: insufficient verification
  3. For each framework requirement R mapped to C:
     a. Check if evidence items reference R in framework-applicability
     b. If not → GAP: framework coverage missing
  4. Compute completeness score and store as control metadata
```

### 7.4 Completeness Status

| Status | Definition | Action |
|--------|-----------|--------|
| **COMPLETE** | All required evidence present, current, and sufficient | None |
| **PARTIAL** | Some required evidence missing, stale, or insufficient | Create remediation tasks for specific gaps |
| **INCOMPLETE** | Majority of required evidence missing | Escalate to control owner; block framework satisfaction |
| **NOT_ASSESSED** | Control has no evidence requirements defined | Flag for control definition review |

### 7.5 Completeness Reporting

Completeness is reported at three levels:

1. **Control-level** — Per-control completeness score and gap list
2. **Framework-level** — Aggregate completeness across all controls mapped to a framework
3. **Organization-level** — Portfolio-wide completeness across all active controls

---

## 8. Evidence Gap Analysis

### 8.1 Gap Types

Gap analysis identifies discrepancies between required evidence and available evidence across six categories:

| Gap Type | Description | Severity |
|----------|-------------|----------|
| **Missing Evidence** | No evidence collected for a required evidence type | Critical |
| **Expired Evidence** | Evidence exists but is past its validity window | High |
| **Insufficient Verification** | Evidence exists but verification level is below framework minimum | High |
| **Quality Deficit** | Evidence exists but quality score is below control risk tier threshold | Medium |
| **Coverage Gap** | Evidence exists for the control but does not map to all required framework requirements | Medium |
| **Stale Control Mapping** | Control definition has been updated but evidence reflects old control version | Low |

### 8.2 Gap Detection Engine

The gap detection engine runs continuously and on-demand:

```
Trigger: Scheduled (daily) or on-demand (pre-audit, framework update)

For each active control C:
  1. Run completeness analysis (Section 7)
  2. For each gap detected:
     a. Classify gap type
     b. Assign severity based on control risk tier and framework criticality
     c. Compute remediation priority score:
        Priority = Control Risk Weight × Framework Criticality × Gap Severity
     d. Create remediation task with:
        - Gap description
        - Required action (collect new evidence, re-verify, upgrade verification level)
        - Deadline (based on framework audit schedule)
        - Assigned owner (control owner or delegated collector)
  3. Aggregate gaps by framework, control category, and organization
  4. Generate gap report with trend comparison
```

### 8.3 Gap Priority Scoring

```
Gap Priority = (Control Risk Weight × 0.4) + (Framework Criticality × 0.3) + (Gap Severity × 0.3)
```

| Factor | Values | Weight |
|--------|--------|--------|
| Control Risk Weight | Critical=1.0, High=0.75, Medium=0.5, Low=0.25 | 40% |
| Framework Criticality | Regulatory=1.0, Contractual=0.75, Voluntary=0.5 | 30% |
| Gap Severity | Critical=1.0, High=0.75, Medium=0.5, Low=0.25 | 30% |

### 8.4 Gap Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ DETECTED │───▶│ TRIAGED  │───▶│ ASSIGNED │───▶│ REMEDIATED│───▶│ VERIFIED │
│          │    │          │    │          │    │          │    │          │
│ Auto-    │    │ Priority │    │ Owner +  │    │ Evidence │    │ Gap      │
│ detected │    │ scored   │    │ deadline │    │ collected│    │ closed   │
│ by engine│    │          │    │ set      │    │ or fixed │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
      │                                                               │
      │              ┌──────────┐                                     │
      └─────────────▶│ ESCALATED│◀────────────────────────────────────┘
                     │          │    (if not resolved by deadline)
                     │ Management│
                     │ notified  │
                     └──────────┘
```

### 8.5 Gap Report Format

```json
{
  "gap-report": {
    "report-id": "uuid-v4",
    "generated-at": "ISO-8601 timestamp",
    "assessment-period": { "start": "ISO-8601", "end": "ISO-8601" },
    "summary": {
      "total-gaps": 23,
      "by-type": {
        "missing-evidence": 5,
        "expired-evidence": 8,
        "insufficient-verification": 4,
        "quality-deficit": 3,
        "coverage-gap": 2,
        "stale-control-mapping": 1
      },
      "by-severity": { "critical": 3, "high": 10, "medium": 7, "low": 3 },
      "by-framework": { "ISO_42001": 8, "NIST_AI_RMF": 6, "EU_AI_ACT": 5, "HIPAA": 2, "PCI_DSS": 1, "GDPR": 1 }
    },
    "gaps": [
      {
        "gap-id": "uuid-v4",
        "control-id": "UC-4.5",
        "type": "missing-evidence",
        "severity": "critical",
        "description": "No test_report evidence collected for UC-4.5",
        "framework-impact": ["ISO_42001:A.6.2.4", "EU_AI_ACT:Art.15"],
        "remediation": {
          "action": "collect-evidence",
          "assigned-to": "control-owner-uuid",
          "deadline": "ISO-8601 timestamp",
          "priority-score": 0.92
        }
      }
    ],
    "trend": {
      "previous-period-gaps": 31,
      "change": -8,
      "change-percent": -25.8
    }
  }
}
```

---

## 9. Evidence Trend Analysis

### 9.1 Trend Metrics

Trend analysis tracks evidence health over time to identify systemic issues, collection failures, and improvement opportunities.

| Metric | Description | Computation |
|--------|-------------|-------------|
| **Evidence Volume Trend** | Rate of evidence collection over time | Count of evidence items per time bucket (daily/weekly/monthly) |
| **Quality Score Trend** | Average quality score over time | Mean quality score per time bucket |
| **Completeness Trend** | Control completeness over time | % of controls with COMPLETE status per time bucket |
| **Gap Closure Rate** | Speed of gap remediation | Gaps closed / gaps opened per time bucket |
| **Verification Level Distribution** | Mix of verification levels over time | Count per level (L0–L4) per time bucket |
| **Collection Channel Mix** | Distribution of collection channels | Count per channel (API, agent, file, log, manual) per time bucket |
| **Expiration Forecast** | Predicted evidence expirations | Count of evidence expiring in next 30/60/90 days |

### 9.2 Trend Detection

The trend analysis engine identifies patterns:

1. **Deterioration Detection** — Quality score or completeness declining for 3+ consecutive periods triggers an alert
2. **Collection Anomaly** — Evidence volume drops >30% from rolling average triggers investigation
3. **Verification Plateau** — Verification level distribution static for 2+ periods suggests process bottleneck
4. **Gap Accumulation** — Gap closure rate < gap creation rate indicates systemic remediation failure
5. **Expiration Cliff** — Cluster of evidence expiring within a short window creates audit risk

### 9.3 Trend Report

```json
{
  "trend-report": {
    "report-id": "uuid-v4",
    "period": { "start": "2026-07-01", "end": "2026-10-01" },
    "granularity": "monthly",
    "metrics": {
      "evidence-volume": {
        "current": 156,
        "previous": 142,
        "change": "+9.9%",
        "trend": "increasing"
      },
      "average-quality-score": {
        "current": 78,
        "previous": 74,
        "change": "+5.4%",
        "trend": "improving"
      },
      "control-completeness": {
        "current": 87,
        "previous": 82,
        "change": "+6.1%",
        "trend": "improving"
      },
      "gap-closure-rate": {
        "current": 0.72,
        "previous": 0.65,
        "change": "+10.8%",
        "trend": "improving"
      },
      "verification-distribution": {
        "L0": 0, "L1": 8, "L2": 118, "L3": 22, "L4": 8
      },
      "expiration-forecast": {
        "next-30-days": 12,
        "next-60-days": 28,
        "next-90-days": 45
      }
    },
    "alerts": [
      {
        "type": "expiration-cliff",
        "severity": "medium",
        "description": "12 evidence items for UC-4.5 expire within 30 days",
        "recommended-action": "Schedule re-collection before expiration"
      }
    ]
  }
}
```

### 9.4 Predictive Analytics

Using historical trend data, the system projects future evidence health:

- **Expiration Risk Forecast** — Predicts which controls will have gaps in the next 90 days based on current evidence age and collection schedules
- **Collection Capacity Planning** — Forecasts collector agent workload and identifies bottlenecks
- **Audit Readiness Projection** — Estimates time to reach target completeness levels given current gap closure rates

---

## 10. Evidence-Based Decision Support

### 10.1 Decision Framework

Evidence analytics feed a decision support layer that provides actionable recommendations to compliance officers, control owners, and auditors.

| Decision Context | Inputs | Output |
|-----------------|--------|--------|
| **Audit Preparation** | Gap report, completeness scores, quality tiers | Prioritized remediation list; risk-ranked control review order |
| **Resource Allocation** | Collection channel mix, gap distribution, expiration forecast | Collector agent deployment recommendations; staffing assignments |
| **Framework Prioritization** | Framework satisfaction scores, gap counts by framework, regulatory deadlines | Framework attention ranking; deadline risk assessment |
| **Control Risk Reassessment** | Evidence quality trends, verification level distribution, incident history | Recommended risk tier adjustments |
| **Remediation Planning** | Gap types, remediation history, control dependencies | Optimal remediation sequence; dependency-aware task scheduling |
| **Auditor Engagement** | Package completeness, quality scores, gap status | Readiness assessment; evidence package confidence rating |

### 10.2 Decision Rules Engine

Decision rules are declarative and configurable:

```yaml
- name: "critical-control-missing-evidence"
  condition: "control.risk_tier == 'CRITICAL' AND gap.type == 'MISSING_EVIDENCE'"
  action:
    type: "escalate"
    target: "compliance-officer"
    priority: "urgent"
    message: "Critical control {{control.id}} has missing evidence for {{gap.framework}}"

- name: "quality-deterioration-alert"
  condition: "quality_score.trend == 'declining' AND quality_score.current < 70"
  action:
    type: "create-task"
    target: "control-owner"
    task-type: "evidence-review"
    due: "P7D"

- name: "expiration-cliff-warning"
  condition: "expiration_forecast.next_30_days > 10"
  action:
    type: "schedule-collection"
    target: "collector-agent"
    scope: "affected-controls"
    window: "P14D"
```

### 10.3 Confidence Scoring for Decisions

Each decision recommendation carries a confidence score based on evidence quality:

```
Decision Confidence = (Evidence Quality Score × 0.4) + (Completeness Score × 0.3) + (Trend Consistency × 0.3)
```

| Confidence | Label | Recommendation |
|------------|-------|----------------|
| 80–100% | High | Act immediately; minimal additional review needed |
| 60–79% | Medium | Proceed with standard verification; spot-check recommended |
| 40–59% | Low | Gather additional evidence before deciding |
| 0–39% | Insufficient | Do not decide; escalate for manual review |

### 10.4 Decision Audit Log

All automated decisions are logged with full context:

```json
{
  "decision-log": {
    "decision-id": "uuid-v4",
    "timestamp": "ISO-8601 timestamp",
    "rule-triggered": "critical-control-missing-evidence",
    "context": {
      "control-id": "UC-4.5",
      "gap-id": "uuid-v4",
      "evidence-quality-score": 45,
      "completeness-score": 60,
      "trend-consistency": 0.8
    },
    "decision": "escalate-to-compliance-officer",
    "confidence": 0.67,
    "confidence-label": "medium",
    "outcome": "pending",
    "decided-by": "system",
    "reviewed-by": null
  }
}
```

---

## 11. Evidence Visualization and Reporting

### 11.1 Dashboard Architecture

The evidence analytics dashboard provides real-time and historical views of evidence health across the organization.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GRC_Claw Evidence Analytics Dashboard                 │
├──────────────────┬──────────────────┬──────────────────┬────────────────┤
│  Compliance      │  Evidence Quality │  Gap Analysis    │  Trend         │
│  Posture         │  Distribution     │  Summary         │  Analysis      │
│                  │                  │                  │                │
│  • Framework     │  • Quality tier   │  • Open gaps by  │  • Volume      │
│    scores        │    breakdown      │    severity      │    over time   │
│  • Satisfaction  │  • Score by       │  • Gap closure   │  • Quality     │
│    matrix        │    control        │    rate          │    trend       │
│  • Risk heatmap  │  • Verification   │  • Expiration    │  • Completeness│
│                  │    level mix      │    forecast      │    trend       │
├──────────────────┴──────────────────┴──────────────────┴────────────────┤
│                        Control Detail Drill-Down                        │
│  • Evidence inventory  • Quality score history  • Gap timeline         │
│  • Chain of custody    • Verification events     • Remediation status  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Standard Reports

| Report | Frequency | Audience | Content |
|--------|-----------|----------|---------|
| **Executive Summary** | Weekly | CISO, Compliance Officer | Framework posture, critical gaps, risk trends |
| **Control Owner Report** | Daily | Control Owners | Assigned gaps, evidence quality, upcoming expirations |
| **Auditor Package** | Per audit | External Auditors | Complete evidence package with quality scores and gap analysis |
| **Gap Analysis Report** | Daily | Compliance Team | All open gaps, priority scores, remediation status |
| **Trend Analysis Report** | Monthly | Architecture Team | Metric trends, predictive forecasts, anomaly alerts |
| **Quality Assurance Report** | Weekly | QA Team | Quality score distribution, low-quality evidence, remediation tracking |

### 11.3 Visualization Types

| Visualization | Data | Purpose |
|---------------|------|---------|
| **Compliance Posture Gauge** | Framework satisfaction scores | At-a-glance compliance status |
| **Quality Score Histogram** | Quality score distribution | Identify quality outliers |
| **Gap Heatmap** | Gaps by control category × severity | Prioritize remediation efforts |
| **Trend Line Charts** | Metric values over time | Detect deterioration or improvement |
| **Verification Level Stacked Bar** | L0–L4 distribution by control category | Assess verification maturity |
| **Collection Channel Pie Chart** | Channel mix | Optimize collector deployment |
| **Expiration Timeline** | Evidence expiration dates | Plan renewal activities |
| **Control Completeness Matrix** | Controls × completeness status | Identify systematic gaps |
| **Framework Coverage Map** | Controls × frameworks satisfied | Cross-framework reuse analysis |

### 11.4 Report Export Formats

| Format | Use Case | Content |
|--------|----------|---------|
| **PDF** | Executive review, auditor distribution | Formatted report with charts and tables |
| **JSON** | System integration, API consumption | Structured data for downstream tools |
| **CSV/Excel** | Data analysis, pivot tables | Tabular data for spreadsheet analysis |
| **HTML** | Interactive dashboard | Embedded visualizations with drill-down |
| **OSCAL** | Regulatory submission | OSCAL assessment-results with analytics extensions |

### 11.5 Alert Integration

Evidence analytics alerts integrate with notification channels:

| Alert Type | Trigger | Channel | Recipient |
|------------|---------|---------|-----------|
| Critical gap detected | New critical-severity gap | Email + Slack + PagerDuty | Compliance Officer |
| Quality deterioration | Quality score drops below threshold | Email + Slack | Control Owner |
| Expiration warning | Evidence expires within 14 days | Email | Control Owner |
| Gap escalation | Gap not resolved by deadline | Email + Slack | Compliance Officer + Manager |
| Trend anomaly | Metric deviates >2σ from baseline | Email | Architecture Team |
| Audit readiness change | Completeness drops below audit threshold | Email + Slack | Audit Coordinator |

---

## 12. Storage & Retention

### 12.1 Storage Architecture

- **Primary store:** Immutable object storage (WORM-enabled) with versioning
- **Index:** Searchable metadata index for fast retrieval
- **Backup:** Encrypted, geographically distributed backups
- **Encryption:** AES-256-GCM at rest, TLS 1.3 in transit

### 12.2 Retention Policy

| Evidence Type | Retention Period | Rationale |
|---------------|-----------------|-----------|
| Security logs | 7 years | Regulatory requirement |
| Configuration snapshots | 3 years | Change tracking |
| Access reviews | 7 years | Audit requirement |
| Vulnerability scans | 3 years | Remediation tracking |
| Manual attestations | Duration of attestation + 3 years | Policy-dependent |

### 12.3 Immutability Guarantees

- Write-once-read-many (WORM) storage for all evidence
- Cryptographic chaining prevents undetected modification
- Access logging captures all read operations
- Regular integrity audits verify storage consistency

---

## 13. Security Considerations

1. **Collector authentication** — mTLS with short-lived certificates
2. **Authorization** — collectors scoped to specific controls and resources
3. **Encryption** — all evidence encrypted at rest and in transit
4. **Access control** — role-based access with principle of least privilege
5. **Audit logging** — all access and modification logged immutably
6. **Key management** — HSM-backed key storage with rotation
7. **PII handling** — evidence containing PII is tagged and access-restricted

---

## 14. Compliance Mapping

This specification supports:

- **SOC 2** — CC6.1, CC6.2, CC7.2, CC7.3
- **ISO 27001** — A.12.4, A.12.5, A.16.1, A.18.2
- **NIST 800-53** — AU-2, AU-3, AU-6, AU-9, AU-11, AU-12
- **PCI DSS** — 10.1, 10.2, 10.3, 10.5, 10.6
- **HIPAA** — 164.308(a)(1)(ii)(D), 164.312(b)

---

## 15. Appendix A: OSCAL Extension Points

GRC_Claw extends OSCAL with the following custom properties (prefixed `grc-`):

| Property | Location | Purpose |
|----------|----------|---------|
| `grc-collector-id` | evidence-item | Identifying the collecting agent |
| `grc-source-system` | evidence-item | Originating system identifier |
| `grc-verification-level` | evidence-item | Current verification level |
| `grc-chain-of-custody` | evidence-item | Custody event references |
| `grc-collection-schedule` | control-mapping | Collection frequency metadata |
| `grc-quality-score` | evidence-item | Composite quality score (0–100) with dimension breakdown |
| `grc-quality-tier` | evidence-item | Quality tier classification (Q1–Q5) |
| `grc-completeness-score` | control | Percentage of required evidence present and current |
| `grc-gap-status` | control | Current gap analysis status (COMPLETE, PARTIAL, INCOMPLETE) |
| `grc-trend-direction` | metric | Trend direction (improving, stable, declining) |
| `grc-decision-confidence` | decision | Confidence score for evidence-based decisions |

---

## 16. Appendix B: Glossary

| Term | Definition |
|------|------------|
| **OSCAL** | Open Security Controls Assessment Language (NIST) |
| **Chain of Custody** | Chronological record of evidence handling |
| **WORM** | Write Once Read Many storage |
| **TSA** | Time Stamping Authority (RFC 3161) |
| **mTLS** | Mutual TLS authentication |
| **GRC** | Governance, Risk, and Compliance |
| **Quality Score** | Composite 0–100 score reflecting evidence reliability across six weighted dimensions |
| **Quality Tier** | Classification of evidence quality (Q1–Q5) driving auditor treatment |
| **Completeness** | Measure of whether all required evidence is present, current, and sufficient |
| **Gap Delta** | Set of framework requirements not yet satisfied by valid evidence |
| **Gap Priority** | Weighted score combining control risk, framework criticality, and gap severity |
| **Trend Analysis** | Longitudinal analysis of evidence metrics to detect patterns and anomalies |
| **Decision Confidence** | Score reflecting the reliability of an evidence-based decision recommendation |

---

*End of specification.*
