# GRC_Claw Evidence Collection — Deep Implementation Specification

**Document ID:** GRC-EVD-002  
**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**Supersedes:** N/A  
**References:** GRC-EVD-001 (Compliance Evidence Specification), GRC-CMS-001 (Compliance Mapping Specification)

---

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Complete Evidence JSON Schema](#2-complete-evidence-json-schema)
3. [Evidence Deduplication Algorithm](#3-evidence-deduplication-algorithm)
4. [Evidence Freshness Scoring](#4-evidence-freshness-scoring)
5. [Evidence Conflict Resolution](#5-evidence-conflict-resolution)
6. [Evidence Retention Automation](#6-evidence-retention-automation)
7. [Evidence Package Generation for Auditors](#7-evidence-package-generation-for-auditors)
8. [Implementation Notes](#8-implementation-notes)
9. [Appendices](#9-appendices)

---

## 1. Purpose & Scope

### 1.1 Purpose

This specification deepens GRC-EVD-001 with concrete, implementable details for six critical evidence management capabilities. Where GRC-EVD-001 defines *what* the evidence pipeline does, this document defines *how* each component operates in production.

### 1.2 Scope

| In Scope | Out of Scope |
|----------|-------------|
| JSON Schema for evidence validation | Control implementation details |
| Deduplication algorithms and thresholds | Remediation workflows |
| Freshness scoring formulas and thresholds | Auditor identity management |
| Conflict detection and resolution logic | Legal interpretation of regulations |
| Retention automation procedures | Framework certification processes |
| Package generation and delivery | |

### 1.3 Relationship to Other Specifications

```
GRC-EVD-001 (Evidence Spec)     ← What the pipeline does
    │
    ├── GRC-EVD-002 (this doc)   ← How each component works
    │
    └── GRC-CMS-001 (Mapping Spec) ← How evidence maps to frameworks
```

---

## 2. Complete Evidence JSON Schema

### 2.1 Schema Overview

The evidence schema is defined in JSON Schema Draft 2020-12 and validates all evidence items entering the GRC_Claw evidence store. The schema is modular: a root schema references sub-schemas for evidence items, chain of custody, and assessment results.

### 2.2 Root Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grc-claw.ai/schemas/evidence/grc-evidence.schema.json",
  "title": "GRC_Claw Evidence Document",
  "description": "Root schema for GRC_Claw OSCAL-based compliance evidence",
  "type": "object",
  "required": ["grc-evidence"],
  "properties": {
    "grc-evidence": {
      "type": "object",
      "required": ["uuid", "metadata", "control-mapping", "evidence-items"],
      "properties": {
        "uuid": { "$ref": "#/$defs/uuid-v4" },
        "metadata": { "$ref": "#/$defs/metadata" },
        "control-mapping": { "$ref": "#/$defs/control-mapping" },
        "evidence-items": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/$defs/evidence-item" }
        },
        "assessment-results": { "$ref": "#/$defs/assessment-results" }
      },
      "additionalProperties": false
    }
  },
  "$defs": {
    "uuid-v4": {
      "type": "string",
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    },
    "iso-8601-timestamp": {
      "type": "string",
      "format": "date-time",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?(Z|[+-]\\d{2}:\\d{2})$"
    },
    "sha256-hex": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "mime-type": {
      "type": "string",
      "pattern": "^[a-z]+/[a-z0-9.+-]+$"
    },
    "metadata": {
      "type": "object",
      "required": ["title", "description", "version", "published", "last-modified", "oscal-version"],
      "properties": {
        "title": { "type": "string", "minLength": 1, "maxLength": 256 },
        "description": { "type": "string", "minLength": 1, "maxLength": 4096 },
        "version": { "type": "string", "pattern": "^\\d+\\.\\d+$" },
        "published": { "$ref": "#/$defs/iso-8601-timestamp" },
        "last-modified": { "$ref": "#/$defs/iso-8601-timestamp" },
        "oscal-version": { "type": "string", "const": "1.1.0" },
        "labels": {
          "type": "array",
          "items": { "type": "string" },
          "uniqueItems": true
        },
        "remarks": { "type": "string" }
      },
      "additionalProperties": false
    },
    "control-mapping": {
      "type": "object",
      "required": ["control-id", "framework", "control-title", "control-family"],
      "properties": {
        "control-id": {
          "type": "string",
          "description": "Unified control ID (e.g., UC-4.5) or framework-specific ID (e.g., AC-2)",
          "pattern": "^(UC-\\d+\\.\\d+|[A-Z]{2}-\\d+|[A-Z]+\\.\\d+\\.\\d+|Art\\.\\d+|§[\\d.]+[a-z]?(\\(\\w+\\))*)"
        },
        "framework": {
          "type": "string",
          "enum": [
            "NIST-800-53", "SOC2", "ISO-27001", "ISO-42001", "CIS-v8",
            "NIST-AI-RMF", "EU-AI-ACT", "HIPAA", "PCI-DSS", "GDPR",
            "GRC-CLAW-UNIFIED"
          ]
        },
        "control-title": { "type": "string", "minLength": 1 },
        "control-family": { "type": "string", "minLength": 1 },
        "control-baseline": {
          "type": "string",
          "enum": ["low", "moderate", "high"]
        },
        "enhancements": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "additionalProperties": false
    },
    "evidence-item": {
      "type": "object",
      "required": [
        "evidence-id", "type", "collected-by", "collected-at",
        "source-system", "source-location", "content", "context", "chain-of-custody"
      ],
      "properties": {
        "evidence-id": { "$ref": "#/$defs/uuid-v4" },
        "type": {
          "type": "string",
          "enum": ["artifact", "observation", "interview", "analysis", "log"]
        },
        "collected-by": {
          "type": "string",
          "description": "Agent ID, user ID, or system identity that collected this evidence",
          "minLength": 1
        },
        "collected-at": { "$ref": "#/$defs/iso-8601-timestamp" },
        "source-system": {
          "type": "string",
          "description": "Originating system identifier (e.g., 'aws-config', 'azure-policy', 'splunk')",
          "minLength": 1
        },
        "source-location": {
          "type": "string",
          "description": "URI, file path, or API endpoint where evidence was collected",
          "minLength": 1
        },
        "content": {
          "type": "object",
          "required": ["format", "data", "hash"],
          "properties": {
            "format": { "$ref": "#/$defs/mime-type" },
            "data": {
              "description": "Base64-encoded content or inline JSON string",
              "oneOf": [
                { "type": "string", "contentEncoding": "base64" },
                { "type": "object" },
                { "type": "string" }
              ]
            },
            "hash": {
              "type": "object",
              "required": ["algorithm", "value"],
              "properties": {
                "algorithm": { "type": "string", "const": "SHA-256" },
                "value": { "$ref": "#/$defs/sha256-hex" }
              },
              "additionalProperties": false
            },
            "size-bytes": { "type": "integer", "minimum": 0 },
            "encoding": { "type": "string", "enum": ["utf-8", "base64", "binary"] }
          },
          "additionalProperties": false
        },
        "context": {
          "type": "object",
          "required": ["environment", "resource-scope", "time-window"],
          "properties": {
            "environment": {
              "type": "string",
              "enum": ["prod", "staging", "dev", "sandbox", "dr"]
            },
            "resource-scope": {
              "type": "string",
              "description": "Resource identifier or scope expression (e.g., 'arn:aws:iam::123456789012:role/*')"
            },
            "time-window": {
              "type": "object",
              "required": ["start", "end"],
              "properties": {
                "start": { "$ref": "#/$defs/iso-8601-timestamp" },
                "end": { "$ref": "#/$defs/iso-8601-timestamp" }
              },
              "additionalProperties": false
            },
            "collection-method": {
              "type": "string",
              "enum": ["api-query", "agent-probe", "file-ingestion", "log-stream", "manual-upload"]
            },
            "authorization": {
              "type": "string",
              "description": "Authorization context (e.g., 'read-only', 'audit-role')"
            }
          },
          "additionalProperties": false
        },
        "chain-of-custody": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/$defs/custody-event" }
        },
        "verification-level": {
          "type": "string",
          "enum": ["L0", "L1", "L2", "L3", "L4"],
          "default": "L0"
        },
        "freshness-score": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "Computed freshness score (0.0 = stale, 1.0 = just collected)"
        },
        "expires-at": { "$ref": "#/$defs/iso-8601-timestamp" },
        "supersedes": {
          "type": "string",
          "description": "Evidence ID of the item this evidence supersedes",
          "$ref": "#/$defs/uuid-v4"
        },
        "tags": {
          "type": "array",
          "items": { "type": "string" },
          "uniqueItems": true
        },
        "pii-flags": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["phi", "pii", "financial", "credentials", "biometric"]
          },
          "uniqueItems": true
        }
      },
      "additionalProperties": false
    },
    "custody-event": {
      "type": "object",
      "required": ["action", "actor", "timestamp", "hash"],
      "properties": {
        "action": {
          "type": "string",
          "enum": ["collected", "transferred", "verified", "exported", "accessed", "modified", "deleted"]
        },
        "actor": { "type": "string", "minLength": 1 },
        "timestamp": { "$ref": "#/$defs/iso-8601-timestamp" },
        "hash": { "$ref": "#/$defs/sha256-hex" },
        "previous-event-hash": { "$ref": "#/$defs/sha256-hex" },
        "signature": {
          "type": "string",
          "description": "Base64-encoded ECDSA P-256 signature"
        },
        "notes": { "type": "string" }
      },
      "additionalProperties": false
    },
    "assessment-results": {
      "type": "object",
      "properties": {
        "observations": {
          "type": "array",
          "items": { "$ref": "#/$defs/observation" }
        },
        "findings": {
          "type": "array",
          "items": { "$ref": "#/$defs/finding" }
        },
        "risks": {
          "type": "array",
          "items": { "$ref": "#/$defs/risk" }
        }
      },
      "additionalProperties": false
    },
    "observation": {
      "type": "object",
      "required": ["observation-id", "title", "description", "collected-at", "evidence-refs"],
      "properties": {
        "observation-id": { "$ref": "#/$defs/uuid-v4" },
        "title": { "type": "string" },
        "description": { "type": "string" },
        "collected-at": { "$ref": "#/$defs/iso-8601-timestamp" },
        "evidence-refs": {
          "type": "array",
          "items": { "$ref": "#/$defs/uuid-v4" },
          "minItems": 1
        },
        "subjects": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["subject-id", "type"],
            "properties": {
              "subject-id": { "type": "string" },
              "type": { "type": "string" }
            }
          }
        }
      },
      "additionalProperties": false
    },
    "finding": {
      "type": "object",
      "required": ["finding-id", "title", "description", "severity", "evidence-refs"],
      "properties": {
        "finding-id": { "$ref": "#/$defs/uuid-v4" },
        "title": { "type": "string" },
        "description": { "type": "string" },
        "severity": { "type": "string", "enum": ["low", "medium", "high", "critical"] },
        "evidence-refs": {
          "type": "array",
          "items": { "$ref": "#/$defs/uuid-v4" }
        },
        "remediation": { "type": "string" },
        "status": { "type": "string", "enum": ["open", "mitigated", "accepted", "closed"] }
      },
      "additionalProperties": false
    },
    "risk": {
      "type": "object",
      "required": ["risk-id", "title", "description", "likelihood", "impact"],
      "properties": {
        "risk-id": { "$ref": "#/$defs/uuid-v4" },
        "title": { "type": "string" },
        "description": { "type": "string" },
        "likelihood": { "type": "string", "enum": ["low", "medium", "high"] },
        "impact": { "type": "string", "enum": ["low", "medium", "high"] },
        "evidence-refs": {
          "type": "array",
          "items": { "$ref": "#/$defs/uuid-v4" }
        }
      },
      "additionalProperties": false
    }
  }
}
```

### 2.3 Evidence Type-Specific Extensions

Each evidence type has additional required properties beyond the base `evidence-item`:

#### 2.3.1 Artifact Evidence

```json
{
  "type": "artifact",
  "properties": {
    "artifact-type": {
      "type": "string",
      "enum": ["config-file", "policy-document", "screenshot", "certificate", "report", "schema"]
    },
    "artifact-version": { "type": "string" },
    "artifact-author": { "type": "string" }
  },
  "required": ["artifact-type"]
}
```

#### 2.3.2 Observation Evidence

```json
{
  "type": "observation",
  "properties": {
    "observation-method": {
      "type": "string",
      "enum": ["agent-probe", "api-query", "log-analysis", "manual-inspection"]
    },
    "observation-target": { "type": "string" },
    "expected-value": {},
    "actual-value": {},
    "deviation": { "type": "string" }
  },
  "required": ["observation-method", "observation-target"]
}
```

#### 2.3.3 Interview Evidence

```json
{
  "type": "interview",
  "properties": {
    "interviewee": { "type": "string" },
    "interviewee-role": { "type": "string" },
    "interview-date": { "$ref": "#/$defs/iso-8601-timestamp" },
    "interview-method": { "type": "string", "enum": ["in-person", "video", "phone", "written"] },
    "attestation": {
      "type": "object",
      "required": ["signed", "signed-at"],
      "properties": {
        "signed": { "type": "boolean" },
        "signed-at": { "$ref": "#/$defs/iso-8601-timestamp" },
        "signature-hash": { "$ref": "#/$defs/sha256-hex" }
      }
    }
  },
  "required": ["interviewee", "interviewee-role", "attestation"]
}
```

#### 2.3.4 Analysis Evidence

```json
{
  "type": "analysis",
  "properties": {
    "analysis-method": {
      "type": "string",
      "enum": ["statistical", "rule-based", "ml-based", "hybrid", "manual"]
    },
    "input-evidence-refs": {
      "type": "array",
      "items": { "$ref": "#/$defs/uuid-v4" },
      "minItems": 2
    },
    "analysis-output": {},
    "confidence-score": { "type": "number", "minimum": 0.0, "maximum": 1.0 }
  },
  "required": ["analysis-method", "input-evidence-refs"]
}
```

#### 2.3.5 Log Evidence

```json
{
  "type": "log",
  "properties": {
    "log-source": {
      "type": "string",
      "enum": ["siem", "cloud-trail", "application-log", "system-log", "network-log", "database-audit"]
    },
    "log-format": {
      "type": "string",
      "enum": ["json", "csv", "syslog", "cef", "leef", "pcap"]
    },
    "event-count": { "type": "integer", "minimum": 0 },
    "event-types": {
      "type": "array",
      "items": { "type": "string" }
    },
    "filter-expression": { "type": "string" }
  },
  "required": ["log-source", "log-format"]
}
```

### 2.4 Schema Validation Pipeline

Evidence passes through three validation stages:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Structural     │───▶│  Semantic       │───▶│  Policy         │
│  Validation     │    │  Validation     │    │  Validation     │
│                 │    │                 │    │                 │
│ • JSON Schema   │    │ • Control ID    │    │ • PII handling  │
│ • Required      │    │   exists in     │    │ • Retention     │
│   fields        │    │   framework     │    │   period valid  │
│ • Type checks   │    │ • Time window   │    │ • Sufficient    │
│ • Format checks │    │   valid         │    │   verification  │
│ • UUID format   │    │ • Hash format   │    │   level         │
│ • Enum values   │    │ • Source system │    │ • Approved      │
│                 │    │   recognized    │    │   collectors     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Structural validation** uses the JSON Schema above. **Semantic validation** checks business rules (control IDs exist, timestamps are logical, source systems are registered). **Policy validation** enforces organizational policies (PII tagging, minimum verification levels, approved collector allowlist).

---

## 3. Evidence Deduplication Algorithm

### 3.1 Problem Statement

Evidence deduplication prevents redundant storage of identical or near-identical evidence while preserving legitimate updates and supersessions. The challenge is distinguishing true duplicates from evidence that is similar but represents a different point in time, different scope, or different context.

### 3.2 Duplicate Classification

| Class | Description | Action |
|-------|-------------|--------|
| **Exact duplicate** | Identical content hash, same control, same time window | Reject; link to existing |
| **Semantic duplicate** | Different hash but same semantic content (e.g., reformatted JSON) | Reject; link to existing |
| **Temporal duplicate** | Same content, overlapping time windows, different collection time | Reject; link to existing |
| **Supersession** | New evidence replaces older evidence for same control + scope | Accept; mark old as superseded |
| **Complementary** | Different content for same control (e.g., different time window) | Accept as new evidence |

### 3.3 Deduplication Key

Each evidence item has a **deduplication key** computed from its semantic identity:

```
dedup_key = SHA-256(
    control_id ||
    type ||
    source_system ||
    resource_scope ||
    time_window.start ||
    time_window.end ||
    content.format
)
```

The dedup key captures *what* the evidence is about, excluding *when* it was collected and *who* collected it. Two evidence items with the same dedup key are candidates for deduplication.

### 3.4 Deduplication Algorithm

```
function deduplicate(new_evidence, evidence_store):

    # Step 1: Compute dedup key
    new_key = compute_dedup_key(new_evidence)
    
    # Step 2: Look up candidates
    candidates = evidence_store.find_by_dedup_key(new_key)
    
    if candidates.is_empty():
        return ACCEPT  # No duplicates found
    
    # Step 3: Check for exact content match
    for candidate in candidates:
        if candidate.content.hash == new_evidence.content.hash:
            return REJECT_AS_DUPLICATE(candidate.evidence_id)
    
    # Step 4: Check for semantic similarity (near-duplicate detection)
    for candidate in candidates:
        similarity = compute_similarity(new_evidence, candidate)
        if similarity >= SEMANTIC_THRESHOLD (0.95):
            return REJECT_AS_DUPLICATE(candidate.evidence_id)
    
    # Step 5: Check for supersession
    for candidate in candidates:
        if is_supersession(new_evidence, candidate):
            mark_superseded(candidate, new_evidence)
            return ACCEPT_AS_SUPERSEDING
    
    # Step 6: Check for temporal overlap
    for candidate in candidates:
        if time_windows_overlap(new_evidence, candidate):
            # Same scope, overlapping time — likely a re-collection
            if new_evidence.collected_at > candidate.collected_at:
                mark_superseded(candidate, new_evidence)
                return ACCEPT_AS_SUPERSEDING
            else:
                return REJECT_AS_DUPLICATE(candidate.evidence_id)
    
    # Step 7: Complementary evidence (different time window, same control)
    return ACCEPT
```

### 3.5 Similarity Computation

For semantic duplicate detection, similarity is computed using a multi-factor approach:

```
similarity = w1 * content_similarity + w2 * metadata_similarity + w3 * context_similarity

Where:
  w1 = 0.60 (content is most important)
  w2 = 0.25 (metadata matters)
  w3 = 0.15 (context matters less)

content_similarity:
  - For text: Jaccard similarity on token sets, normalized to [0, 1]
  - For JSON: Structural similarity (same keys, similar values)
  - For binary: Perceptual hash comparison (pHash), threshold 0.95

metadata_similarity:
  - Title similarity: Levenshtein distance normalized
  - Description similarity: Cosine similarity on TF-IDF vectors

context_similarity:
  - Environment match: 1.0 if same, 0.0 if different
  - Resource scope match: 1.0 if same, 0.5 if overlapping, 0.0 if different
  - Time window overlap: Jaccard index of time intervals
```

### 3.6 Supersession Rules

New evidence supersedes existing evidence when ALL of the following are true:

1. Same `control_id` and `type`
2. Same `source_system` and `resource_scope`
3. New evidence's `collected-at` is later than existing evidence's `collected-at`
4. New evidence's verification level ≥ existing evidence's verification level
5. New evidence's time window overlaps or is contained within existing evidence's time window

When supersession occurs:
- Existing evidence is marked `status: "superseded"`
- Existing evidence's `superseded-by` field is set to the new evidence ID
- New evidence's `supersedes` field is set to the existing evidence ID
- Chain of custody is updated for both items
- Compliance posture is recalculated for affected controls

### 3.7 Deduplication Configuration

```yaml
deduplication:
  enabled: true
  semantic_threshold: 0.95
  temporal_overlap_threshold: 0.80  # 80% time window overlap = duplicate
  content_weights:
    content: 0.60
    metadata: 0.25
    context: 0.15
  supersession:
    enabled: true
    require_higher_verification: true
    max_supersession_chain: 10  # Prevent infinite chains
  exceptions:
    - control_id: "UC-4.5"  # V&V evidence — always keep all versions
      reason: "Regulatory requirement to retain all test versions"
    - type: "interview"  # Interviews are never deduplicated
      reason: "Each interview is a unique attestation"
```

---

## 4. Evidence Freshness Scoring

### 4.1 Problem Statement

Not all evidence ages equally. A firewall configuration snapshot from 30 days ago may be critically stale, while a signed policy document from 30 days ago may still be perfectly valid. Freshness scoring quantifies how current and reliable evidence is, enabling automated renewal prioritization and compliance posture accuracy.

### 4.2 Freshness Score Formula

The freshness score is a composite metric computed from four factors:

```
freshness_score = w_age * age_score + w_verification * verification_score 
                + w_collection * collection_score + w_criticality * criticality_score

Where:
  w_age = 0.35          (age is the strongest signal)
  w_verification = 0.25 (verification level matters)
  w_collection = 0.20   (collection frequency matters)
  w_criticality = 0.20  (control criticality amplifies staleness impact)
```

### 4.3 Age Score

```
age_score = max(0, 1 - (age_days / expiration_days))

Where:
  age_days = (now - collected_at) in days
  expiration_days = control's evidence expiration period

Special cases:
  - If age_days > expiration_days: age_score = 0.0
  - If evidence has been re-verified: age_score = min(1.0, age_score * 1.2)
    (re-verification gives a 20% boost, capped at 1.0)
```

### 4.4 Verification Score

```
verification_score = verification_level / 4.0

Where:
  L0 = 0.0
  L1 = 0.25
  L2 = 0.50
  L3 = 0.75
  L4 = 1.0
```

### 4.5 Collection Score

```
collection_score = 1.0 - (days_since_last_collection / collection_interval_days)

Where:
  collection_interval_days = control's collection schedule frequency
  days_since_last_collection = (now - last_collection_time) in days

Special cases:
  - If collection is automated: collection_score = min(1.0, collection_score * 1.1)
  - If collection is manual: collection_score = min(1.0, collection_score * 0.9)
```

### 4.6 Criticality Score

```
criticality_score = 1.0 - (criticality_weight * age_ratio)

Where:
  criticality_weight = 0.5 for Critical, 0.3 for High, 0.15 for Medium, 0.0 for Low
  age_ratio = min(1.0, age_days / expiration_days)

Interpretation:
  - Critical controls lose freshness faster (stale critical evidence is worse)
  - Low-criticality controls are more tolerant of age
```

### 4.7 Freshness Score Ranges and Actions

| Score Range | Label | Action |
|-------------|-------|--------|
| 0.90 – 1.00 | **Fresh** | No action needed |
| 0.70 – 0.89 | **Current** | Schedule next collection |
| 0.50 – 0.69 | **Aging** | Flag for renewal; notify control owner |
| 0.30 – 0.49 | **Stale** | Create renewal task; downgrade satisfaction |
| 0.00 – 0.29 | **Expired** | Mark as expired; escalate to control owner |

### 4.8 Freshness Score Computation Example

```
Evidence: Firewall configuration snapshot
Control: UC-7.1 (Network Security)
Collected: 2026-09-01T00:00:00Z
Now: 2026-10-01T00:00:00Z
Verification Level: L2
Collection Frequency: Daily (1 day)
Control Criticality: Critical
Expiration Period: 30 days

age_days = 30
expiration_days = 30
age_score = max(0, 1 - 30/30) = 0.0

verification_score = 2/4 = 0.50

days_since_last_collection = 30
collection_interval_days = 1
collection_score = 1.0 - 30/1 = -29 → clamped to 0.0

criticality_weight = 0.5 (Critical)
age_ratio = min(1.0, 30/30) = 1.0
criticality_score = 1.0 - (0.5 * 1.0) = 0.5

freshness_score = 0.35*0.0 + 0.25*0.50 + 0.20*0.0 + 0.20*0.5
                = 0.0 + 0.125 + 0.0 + 0.1
                = 0.225

Result: EXPIRED (0.00 – 0.29 range)
Action: Mark as expired; escalate to control owner
```

### 4.9 Freshness Score Storage

The freshness score is computed on read and stored as a cached field:

```json
{
  "evidence-id": "uuid-v4",
  "freshness-score": 0.225,
  "freshness-label": "expired",
  "freshness-computed-at": "2026-10-01T00:00:00Z",
  "freshness-factors": {
    "age-score": 0.0,
    "verification-score": 0.5,
    "collection-score": 0.0,
    "criticality-score": 0.5
  }
}
```

The score is recomputed:
- On every read (for real-time accuracy)
- Daily in batch (for reporting and trending)
- After any verification level change
- After any collection event for the same control

---

## 5. Evidence Conflict Resolution

### 5.1 Problem Statement

Conflicting evidence arises when two or more evidence items for the same control reach contradictory conclusions. For example, a vulnerability scan may report "no critical vulnerabilities" while a penetration test reports "critical vulnerability found." Without systematic conflict resolution, compliance posture becomes unreliable.

### 5.2 Conflict Types

| Conflict Type | Description | Example |
|---------------|-------------|---------|
| **Contradictory findings** | Two evidence items assert opposite conclusions | Scan says "compliant," pen test says "non-compliant" |
| **Version conflict** | Two evidence items represent different versions of the same artifact | Config file v1.2 vs v1.3 |
| **Source conflict** | Two sources report different values for the same metric | AWS Config says "encrypted," custom agent says "not encrypted" |
| **Temporal conflict** | Evidence from different time periods shows different states | Last month: compliant; this month: non-compliant |
| **Scope conflict** | Evidence covers different resource scopes | Prod evidence vs staging evidence |

### 5.3 Conflict Detection Algorithm

```
function detect_conflicts(evidence_set, new_evidence):

    conflicts = []
    
    for existing in evidence_set where existing.control_id == new_evidence.control_id:
        
        # Check 1: Contradictory findings
        if has_contradictory_findings(new_evidence, existing):
            conflicts.append({
                type: "CONTRADICTORY_FINDINGS",
                evidence_a: new_evidence.evidence_id,
                evidence_b: existing.evidence_id,
                description: "Evidence items reach contradictory conclusions"
            })
        
        # Check 2: Version conflict
        if is_different_version(new_evidence, existing):
            conflicts.append({
                type: "VERSION_CONFLICT",
                evidence_a: new_evidence.evidence_id,
                evidence_b: existing.evidence_id,
                description: "Different versions of the same artifact"
            })
        
        # Check 3: Source conflict
        if has_source_conflict(new_evidence, existing):
            conflicts.append({
                type: "SOURCE_CONFLICT",
                evidence_a: new_evidence.evidence_id,
                evidence_b: existing.evidence_id,
                description: "Different sources report different values"
            })
        
        # Check 4: Temporal conflict
        if has_temporal_conflict(new_evidence, existing):
            conflicts.append({
                type: "TEMPORAL_CONFLICT",
                evidence_a: new_evidence.evidence_id,
                evidence_b: existing.evidence_id,
                description: "Evidence from different time periods shows different states"
            })
    
    return conflicts
```

### 5.4 Contradictory Finding Detection

Two evidence items have contradictory findings when:

```
function has_contradictory_findings(evidence_a, evidence_b):

    # Extract findings from both evidence items
    findings_a = extract_findings(evidence_a)
    findings_b = extract_findings(evidence_b)
    
    for finding_a in findings_a:
        for finding_b in findings_b:
            # Same check, opposite result
            if finding_a.check_id == finding_b.check_id:
                if finding_a.result == "pass" and finding_b.result == "fail":
                    return true
                if finding_a.result == "fail" and finding_b.result == "pass":
                    return true
                if finding_a.result == "compliant" and finding_b.result == "non-compliant":
                    return true
                if finding_a.result == "non-compliant" and finding_b.result == "compliant":
                    return true
    
    # Check for contradictory observations
    observations_a = extract_observations(evidence_a)
    observations_b = extract_observations(evidence_b)
    
    for obs_a in observations_a:
        for obs_b in observations_b:
            if obs_a.metric == obs_b.metric:
                if values_contradict(obs_a.value, obs_b.value):
                    return true
    
    return false
```

### 5.5 Conflict Resolution Strategies

When a conflict is detected, the system applies resolution strategies in priority order:

#### Strategy 1: Recency (Default)

```
The most recent evidence wins.

resolution = evidence with latest collected_at timestamp

Rationale: Newer evidence reflects the current state of the system.
Applied when: Both evidence items have the same verification level.
```

#### Strategy 2: Verification Level

```
Higher verification level wins.

resolution = evidence with highest verification level (L4 > L3 > L2 > L1 > L0)

Rationale: Attested evidence (L4) is more reliable than unverified evidence (L0).
Applied when: Evidence items have different verification levels.
```

#### Strategy 3: Source Authority

```
Evidence from a more authoritative source wins.

Source authority ranking:
  1. Attested human review (L4)
  2. Independent third-party audit
  3. Automated agent probe (read-only)
  4. Cloud provider API
  5. Self-reported / manual upload
  6. Derived analysis

Rationale: Independent, read-only sources are more trustworthy than self-reported data.
Applied when: Evidence items have the same verification level but different sources.
```

#### Strategy 4: Consensus

```
When multiple evidence items agree and one disagrees, the majority wins.

resolution = conclusion supported by majority of evidence items

Rationale: Consensus reduces the impact of a single faulty collector.
Applied when: 3+ evidence items exist for the same control and check.
```

#### Strategy 5: Escalation

```
When no strategy produces a clear resolution, escalate to human review.

resolution = PENDING_HUMAN_REVIEW

Rationale: Some conflicts require human judgment to resolve.
Applied when: Strategies 1-4 produce conflicting results or evidence is ambiguous.
```

### 5.6 Conflict Resolution Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONFLICT DETECTED                             │
│  Evidence A (L2, 2026-09-15) vs Evidence B (L3, 2026-09-20)   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Same verification     │
              │  level?                │
              └────────┬───────┬───────┘
                   Yes │       │ No
                       ▼       ▼
            ┌──────────┐  ┌──────────────┐
            │ Strategy │  │ Strategy 2:  │
            │ 1:       │  │ Higher level │
            │ Recency  │  │ wins → B     │
            └────┬─────┘  └──────────────┘
                 │
                 ▼
            ┌──────────┐
            │ Same     │
            │ source   │
            │ authority?│
            └────┬─────┘
           Yes   │   No
                 ▼   ▼
            ┌──────────┐  ┌──────────────┐
            │ Strategy │  │ Strategy 3:  │
            │ 4:       │  │ Source       │
            │ Consensus│  │ authority    │
            └────┬─────┘  └──────────────┘
                 │
                 ▼
            ┌──────────┐
            │ Clear    │
            │ winner?  │
            └────┬─────┘
           Yes   │   No
                 ▼   ▼
            ┌──────────┐  ┌──────────────┐
            │ Apply    │  │ Strategy 5:  │
            │ resolution│  │ Escalate to  │
            └──────────┘  │ human review │
                          └──────────────┘
```

### 5.7 Conflict Record Schema

```json
{
  "conflict-id": "uuid-v4",
  "control-id": "UC-7.1",
  "conflict-type": "CONTRADICTORY_FINDINGS",
  "evidence-a": {
    "evidence-id": "uuid-v4",
    "collected-at": "2026-09-15T00:00:00Z",
    "verification-level": "L2",
    "source-system": "nessus-scan",
    "finding": "No critical vulnerabilities found"
  },
  "evidence-b": {
    "evidence-id": "uuid-v4",
    "collected-at": "2026-09-20T00:00:00Z",
    "verification-level": "L3",
    "source-system": "pentest-report",
    "finding": "Critical vulnerability CVE-2026-1234 found"
  },
  "detected-at": "2026-10-01T00:00:00Z",
  "resolution-strategy": "VERIFICATION_LEVEL",
  "resolution": "EVIDENCE_B_WINS",
  "resolution-rationale": "Evidence B has higher verification level (L3 > L2)",
  "resolved-at": "2026-10-01T00:00:00Z",
  "resolved-by": "system",
  "status": "RESOLVED"
}
```

### 5.8 Conflict Escalation

When conflicts are escalated to human review:

1. **Notification** sent to control owner and compliance team
2. **Evidence package** compiled with both evidence items and their full context
3. **Review deadline** set (default: 5 business days)
4. **Interim compliance posture** marked as `UNCERTAIN` for the affected control
5. **Resolution** recorded with reviewer identity, decision, and rationale
6. **Audit trail** updated with the full conflict history

---

## 6. Evidence Retention Automation

### 6.1 Problem Statement

Evidence retention is not just about deleting old data — it's about enforcing regulatory requirements, managing storage costs, maintaining legal hold obligations, and ensuring audit readiness. Manual retention management does not scale.

### 6.2 Retention Policy Engine

The retention policy engine automates the full evidence lifecycle from creation to destruction:

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ ACTIVE   │──▶│ ARCHIVE  │──▶│ REVIEW   │──▶│ DELETE   │──│ CERTIFY  │
│          │   │          │   │          │   │          │   │          │
│ Normal   │   │ Cold     │   │ Pending  │   │ Secure   │   │ Deletion │
│ access   │   │ storage  │   │ decision │   │ erase    │   │ proof    │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
  WORM storage  Object lock   Legal hold    Crypto-shred   Deletion
  + indexing    + no delete   + review      + overwrite    certificate
```

### 6.3 Retention Schedule

| Evidence Type | Active Period | Archive Period | Total Retention | Deletion Method |
|---------------|---------------|----------------|-----------------|-----------------|
| Security logs | 90 days | 6 years 3 months | 7 years | Crypto-shred |
| Configuration snapshots | 90 days | 2 years 3 months | 3 years | Crypto-shred |
| Access reviews | 90 days | 6 years 3 months | 7 years | Crypto-shred |
| Vulnerability scans | 90 days | 2 years 3 months | 3 years | Crypto-shred |
| Penetration test results | 365 days | 6 years | 7 years | Crypto-shred |
| Policy documents | 365 days | 2 years 3 months | 3 years | Crypto-shred |
| Manual attestations | 365 days | 2 years 3 months | 3 years | Crypto-shred |
| Audit logs | 90 days | 6 years 3 months | 7 years | Crypto-shred |
| Incident reports | 365 days | 6 years | 7 years | Crypto-shred |

### 6.4 Retention State Machine

```
                    ┌──────────────────────────────────────────┐
                    │                                          │
                    ▼                                          │
            ┌──────────────┐                                  │
            │   ACTIVE     │                                  │
            │              │                                  │
            │ • Full index │                                  │
            │ • Fast query │                                  │
            │ • WORM       │                                  │
            └──────┬───────┘                                  │
                   │                                          │
                   │ active_period expires                    │
                   ▼                                          │
            ┌──────────────┐                                  │
            │  ARCHIVING   │                                  │
            │              │                                  │
            │ • Move to    │                                  │
            │   cold store │                                  │
            │ • Update     │                                  │
            │   index      │                                  │
            └──────┬───────┘                                  │
                   │                                          │
                   │ archive complete                         │
                   ▼                                          │
            ┌──────────────┐                                  │
            │  ARCHIVED    │                                  │
            │              │                                  │
            │ • Cold store │                                  │
            │ • Object lock│                                  │
            │ • Slower     │                                  │
            │   access     │                                  │
            └──────┬───────┘                                  │
                   │                                          │
                   │ retention_period expires                 │
                   ▼                                          │
            ┌──────────────┐                                  │
            │   REVIEW     │                                  │
            │              │                                  │
            │ • Check      │                                  │
            │   legal hold │                                  │
            │ • Check      │                                  │
            │   audit      │                                  │
            │   window     │                                  │
            └──────┬───────┘                                  │
                   │                                          │
         ┌─────────┴─────────┐                                │
         │                   │                                │
         ▼                   ▼                                │
  ┌────────────┐    ┌──────────────┐                          │
  │ LEGAL_HOLD │    │  DELETING    │                          │
  │            │    │              │                          │
  │ • Retain   │    │ • Crypto-    │                          │
  │   until    │    │   shred     │                          │
  │   released │    │ • Overwrite │                          │
  │            │    │ • Verify    │                          │
  └────────────┘    └──────┬───────┘                          │
                           │                                  │
                           │ deletion complete               │
                           ▼                                  │
                    ┌──────────────┐                          │
                    │  CERTIFIED   │                          │
                    │              │                          │
                    │ • Deletion   │                          │
                    │   certificate│                          │
                    │ • Audit log  │                          │
                    │ • Proof for  │                          │
                    │   auditor    │                          │
                    └──────────────┘                          │
                                                              │
```

### 6.5 Legal Hold Mechanism

Legal holds override all retention policies and prevent deletion:

```json
{
  "legal-hold-id": "uuid-v4",
  "control-ids": ["UC-7.1", "UC-7.2"],
  "evidence-types": ["log", "observation"],
  "description": "Pending litigation — Case #2026-CV-1234",
  "issued-by": "legal@company.com",
  "issued-at": "2026-09-15T00:00:00Z",
  "expires-at": null,
  "status": "ACTIVE",
  "affected-evidence-count": 156
}
```

When a legal hold is active:
- Evidence matching the hold criteria is flagged `legal_hold: true`
- Deletion operations are blocked for held evidence
- The hold is reviewed quarterly by legal counsel
- When released, normal retention processing resumes

### 6.6 Automated Retention Workflow

```
Daily (02:00 UTC):
  1. Query evidence where active_period has expired
  2. Move to archive storage tier
  3. Update search index
  4. Log retention event

Weekly (Sunday 03:00 UTC):
  1. Query archived evidence where retention_period has expired
  2. Check for active legal holds
  3. If no hold: initiate deletion workflow
  4. If hold: flag for legal review
  5. Log retention event

Monthly (1st of month, 04:00 UTC):
  1. Generate retention compliance report
  2. Identify evidence approaching retention limits
  3. Notify control owners of upcoming expirations
  4. Review and release expired legal holds
  5. Log retention event

Quarterly:
  1. Full retention audit
  2. Verify deletion certificates
  3. Review retention policy effectiveness
  4. Update retention schedules per regulatory changes
```

### 6.7 Deletion Certificate

When evidence is deleted, a cryptographic certificate is generated as proof:

```json
{
  "deletion-certificate-id": "uuid-v4",
  "evidence-id": "uuid-v4",
  "evidence-hash": "sha256-hex",
  "deletion-method": "crypto-shred",
  "deletion-timestamp": "2026-10-01T00:00:00Z",
  "retention-policy": "security-logs-7yr",
  "retention-period-days": 2555,
  "actual-retention-days": 2555,
  "legal-hold-checked": true,
  "legal-hold-result": "none-active",
  "deletion-verified": true,
  "verification-hash": "sha256-hex",
  "certified-by": "system",
  "audit-trail-ref": "chain-of-custody-event-id"
}
```

### 6.8 Retention Monitoring Dashboard

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| Evidence count by state | Active / Archived / Review / Deleting | N/A |
| Storage utilization | Current / Capacity | > 80% |
| Upcoming expirations | Evidence expiring in 30 days | > 100 items |
| Legal holds active | Count and age of holds | > 90 days |
| Deletion certificate count | Certificates generated this period | N/A |
| Retention compliance rate | Evidence correctly retained / Total | < 99% |
| Orphaned evidence | Evidence without valid retention policy | > 0 |

---

## 7. Evidence Package Generation for Auditors

### 7.1 Problem Statement

Auditors need evidence packages that are complete, verifiable, and formatted for their specific framework and audit methodology. Manual package assembly is error-prone and does not scale. Automated package generation ensures consistency, completeness, and cryptographic verifiability.

### 7.2 Package Generation Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PACKAGE GENERATION PIPELINE                       │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐│
│  │ SELECT   │─▶│ ASSEMBLE │─▶│ RENDER   │─▶│ SIGN     │─▶│ DELIVER││
│  │          │  │          │  │          │  │          │  │        ││
│  │ • Filter │  │ • Gather │  │ • Format │  │ • ECDSA  │  │ • API ││
│  │   by     │  │   evidence│  │   per    │  │   sign   │  │ • Zip ││
│  │   control│  │ • Include│  │   frame- │  │ • RFC    │  │ • PDF ││
│  │ • Filter │  │   OSCAL  │  │   work   │  │   3161   │  │ • CSV ││
│  │   by date│  │ • Include│  │ • Include│  │   time-  │  │        ││
│  │ • Filter │  │   custody│  │   gap    │  │   stamp  │  │        ││
│  │   by type│  │ • Include│  │   analysis│ │ • Embed  │  │        ││
│  │ • Filter │  │   attach-│  │ • Include│  │   sigs   │  │        ││
│  │   by ver │  │   ments  │  │   README │  │          │  │        ││
│  │   level  │  │          │  │          │  │          │  │        ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 Package Content Selection

#### 7.3.1 Control Selection

```
function select_controls(package_request):

    controls = []
    
    if package_request.framework:
        # Select all controls with spokes to the target framework
        controls = framework_registry.get_controls(package_request.framework)
    
    if package_request.control_ids:
        # Specific controls requested
        controls = control_ids.map(id => control_registry.get(id))
    
    if package_request.control_category:
        # All controls in a category
        controls = control_registry.get_by_category(package_request.category)
    
    # Filter by risk tier if specified
    if package_request.min_risk_tier:
        controls = controls.filter(c => c.risk_tier >= package_request.min_risk_tier)
    
    return controls
```

#### 7.3.2 Evidence Selection

```
function select_evidence(controls, package_request):

    evidence_items = []
    
    for control in controls:
        # Get all evidence for this control
        control_evidence = evidence_store.find_by_control(control.id)
        
        # Filter by date range
        if package_request.date_range:
            control_evidence = control_evidence.filter(
                e => e.collected_at >= package_request.date_range.start
                     && e.collected_at <= package_request.date_range.end
            )
        
        # Filter by evidence type
        if package_request.evidence_types:
            control_evidence = control_evidence.filter(
                e => package_request.evidence_types.includes(e.type)
            )
        
        # Filter by verification level
        if package_request.min_verification_level:
            control_evidence = control_evidence.filter(
                e => verification_level_value(e.verification_level) 
                     >= verification_level_value(package_request.min_verification_level)
            )
        
        # Filter out superseded evidence
        control_evidence = control_evidence.filter(e => e.status != "superseded")
        
        # Filter out expired evidence (unless explicitly requested)
        if not package_request.include_expired:
            control_evidence = control_evidence.filter(e => e.freshness_score > 0.3)
        
        evidence_items.extend(control_evidence)
    
    return evidence_items
```

### 7.4 Package Rendering Formats

#### 7.4.1 JSON (OSCAL) Format

```json
{
  "package": {
    "package-id": "uuid-v4",
    "package-version": "1.0",
    "generated-at": "2026-10-01T00:00:00Z",
    "generated-by": "grc-evidence-engine-v2.1.0",
    "organization": "Example Corp",
    "assessment-period": {
      "start": "2026-07-01T00:00:00Z",
      "end": "2026-09-30T23:59:59Z"
    },
    "frameworks": ["ISO-42001", "NIST-AI-RMF"],
    "controls-assessed": 68,
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
      },
      "by-freshness": {
        "fresh": 80,
        "current": 50,
        "aging": 20,
        "stale": 4,
        "expired": 2
      }
    },
    "gap-analysis": {
      "total-gaps": 0,
      "gaps": []
    },
    "compliance-posture": {
      "ISO-42001": {
        "score": 0.98,
        "satisfied": 38,
        "partially-satisfied": 0,
        "not-satisfied": 0,
        "not-applicable": 0
      },
      "NIST-AI-RMF": {
        "score": 0.95,
        "satisfied": 18,
        "partially-satisfied": 1,
        "not-satisfied": 0,
        "not-applicable": 0
      }
    },
    "package-hash": {
      "algorithm": "SHA-256",
      "value": "sha256-hex"
    }
  }
}
```

#### 7.4.2 PDF Format

The PDF package includes:
1. **Cover page** — Organization, assessment period, frameworks, package ID
2. **Executive summary** — Compliance posture, key metrics, gap count
3. **Control-by-control detail** — For each control: status, evidence summary, verification level
4. **Evidence index** — Table of all evidence items with ID, type, date, verification level
5. **Gap analysis** — Any unsatisfied requirements with remediation plans
6. **Chain of custody summary** — Custody event counts and integrity verification
7. **Appendix** — Full evidence items (or reference to JSON package)

#### 7.4.3 CSV Format

```csv
evidence-id,control-id,framework,type,collected-at,verification-level,freshness-score,source-system,status,hash
uuid-1,UC-4.5,ISO-42001,test_report,2026-09-15T00:00:00Z,L2,0.85,grc-test-runner,active,abc123...
uuid-2,UC-4.5,NIST-AI-RMF,evaluation_record,2026-09-10T00:00:00Z,L3,0.72,ml-eval-engine,active,def456...
uuid-3,UC-7.1,ISO-42001,config_snapshot,2026-09-20T00:00:00Z,L2,0.91,aws-config,active,ghi789...
```

### 7.5 Package Signing and Timestamping

```
Step 1: Canonical serialization
  - Serialize package contents to canonical JSON (RFC 8785 JCS)
  - Deterministic: same input always produces same output

Step 2: Hash computation
  - Compute SHA-256 of canonical form
  - This hash represents the package content

Step 3: Digital signature
  - Sign the hash with ECDSA P-256 private key
  - Key stored in HSM (FIPS 140-2 Level 3)
  - Signature stored in signatures/package-signature.json

Step 4: Trusted timestamp
  - Submit hash to RFC 3161 Time Stamping Authority
  - Receive timestamp token (.tsr file)
  - Timestamp proves the package existed at a specific time

Step 5: Signature embedding
  - Embed signature and timestamp in package manifest
  - Include certificate chain for verification
```

### 7.6 Package Verification

Auditors can independently verify package integrity:

```
function verify_package(package):

    # Step 1: Recompute package hash
    canonical = canonicalize(package.contents)
    computed_hash = SHA-256(canonical)
    
    # Step 2: Verify signature
    signature = package.signatures.package-signature
    public_key = get_grc_claw_public_key()
    if not ecdsa_verify(computed_hash, signature, public_key):
        return INVALID_SIGNATURE
    
    # Step 3: Verify timestamp
    timestamp = package.signatures.timestamp-token
    if not rfc3161_verify(computed_hash, timestamp):
        return INVALID_TIMESTAMP
    
    # Step 4: Verify individual evidence hashes
    for item in package.evidence:
        if not verify_evidence_hash(item):
            return EVIDENCE_TAMPERED
    
    # Step 5: Verify chain of custody
    for item in package.evidence:
        if not verify_custody_chain(item):
            return CUSTODY_BROKEN
    
    return VALID
```

### 7.7 Package Delivery

| Channel | Format | Authentication | Use Case |
|---------|--------|----------------|----------|
| **API download** | JSON, CSV | OAuth 2.0 + mTLS | GRC tool integration |
| **Secure portal** | PDF, JSON | SSO + MFA | Auditor self-service |
| **Email** | PDF (encrypted) | PGP encryption | Small packages (< 10MB) |
| **Physical media** | Full package | Chain of custody | Air-gapped environments |
| **Blockchain anchor** | Hash only | N/A | Proof of existence |

### 7.8 Package Generation Triggers

```
┌─────────────────────────────────────────────────────────────┐
│                  PACKAGE GENERATION TRIGGERS                 │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  SCHEDULED  │  │  ON-DEMAND  │  │  EVENT      │         │
│  │             │  │             │  │  DRIVEN     │         │
│  │ • Monthly   │  │ • Auditor   │  │ • Post-     │         │
│  │ • Quarterly │  │   request   │  │   assessment│         │
│  │ • Annually  │  │ • Compliance│  │ • Post-     │         │
│  │             │  │   deadline  │  │   remediation│        │
│  │             │  │ • Internal  │  │ • Incident  │         │
│  │             │  │   audit     │  │   response  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  Priority: Scheduled = Normal, On-Demand = High,           │
│            Event = Urgent                                   │
│                                                             │
│  SLA:     Scheduled = 24h, On-Demand = 4h, Event = 1h      │
└─────────────────────────────────────────────────────────────┘
```

### 7.9 Package Generation Configuration

```yaml
package_generation:
  default_formats: ["json", "pdf"]
  signing:
    enabled: true
    algorithm: "ECDSA-P256"
    hsm-provider: "aws-cloudhsm"
    key-rotation-days: 90
  timestamping:
    enabled: true
    tsa-url: "https://tsa.grc-claw.ai"
    tsa-certificate: "/certs/tsa-ca.pem"
  delivery:
    api:
      enabled: true
      base-url: "https://api.grc-claw.ai/v1/packages"
      auth: "oauth2-mtls"
    portal:
      enabled: true
      url: "https://audit.grc-claw.ai"
      auth: "sso-mfa"
    email:
      enabled: false
      pgp-key: "/keys/audit-pgp.asc"
  retention:
    package_retention_days: 2555  # 7 years
    max_package_size_mb: 500
  performance:
    max_concurrent_generations: 5
    timeout_minutes: 30
    retry_attempts: 3
```

---

## 8. Implementation Notes

### 8.1 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| JSON Schema validation | jsonschema (Python) | 4.21+ |
| Canonical JSON | RFC 8785 JCS | — |
| Digital signatures | ECDSA P-256 (cryptography lib) | 42+ |
| Timestamping | RFC 3161 (rfc3161ng) | — |
| Object storage | AWS S3 (WORM) / MinIO | — |
| Search index | Elasticsearch | 8.x |
| Message queue | Apache Kafka | 3.7+ |
| Workflow engine | Temporal | 1.22+ |
| HSM | AWS CloudHSM (FIPS 140-2 L3) | — |

### 8.2 Performance Targets

| Operation | Target Latency | Throughput |
|-----------|---------------|------------|
| Evidence ingestion | < 500ms | 1000 items/sec |
| Schema validation | < 50ms | 10,000 items/sec |
| Deduplication check | < 100ms | 5000 items/sec |
| Freshness score computation | < 10ms | 100,000 items/sec |
| Conflict detection | < 200ms | 2000 items/sec |
| Package generation (100 items) | < 30s | 10 packages/min |
| Package generation (1000 items) | < 5min | 2 packages/min |
| Package verification | < 5s | 100 packages/min |

### 8.3 Scalability Considerations

- **Evidence store:** Sharded by control_id, partitioned by date
- **Index:** Elasticsearch with hot-warm-cold tiering
- **Package generation:** Async via Temporal workflows, horizontally scalable
- **Deduplication:** Bloom filter for fast negative checks, then exact comparison
- **Freshness scoring:** Computed on read, cached with TTL, batch-recomputed daily

### 8.4 Failure Handling

| Failure | Detection | Response |
|---------|-----------|----------|
| Schema validation failure | Immediate | Reject evidence, alert collector |
| Hash mismatch | On read | Quarantine evidence, integrity alert |
| Deduplication service down | Timeout | Queue for retry, accept with flag |
| Signing service down | Timeout | Queue package, retry with backoff |
| TSA unavailable | Timeout | Generate unsigned package, flag for re-signing |
| Storage write failure | Immediate | Retry 3x, then alert operations |

---

## 9. Appendices

### Appendix A: JSON Schema Validation Errors

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `SCHEMA-001` | Missing required field | Add required field |
| `SCHEMA-002` | Invalid UUID format | Use UUID v4 format |
| `SCHEMA-003` | Invalid ISO-8601 timestamp | Use `YYYY-MM-DDTHH:MM:SSZ` |
| `SCHEMA-004` | Invalid SHA-256 hash | Use 64-character lowercase hex |
| `SCHEMA-005` | Invalid MIME type | Use standard MIME type |
| `SCHEMA-006` | Invalid enum value | Use value from allowed set |
| `SCHEMA-007` | Invalid control ID format | Use UC-X.Y or framework-specific format |
| `SCHEMA-008` | Time window end before start | Correct time window |
| `SCHEMA-009` | Future timestamp | Use current or past timestamp |
| `SCHEMA-010` | Empty evidence items array | Include at least one evidence item |

### Appendix B: Freshness Score Factor Weights

| Factor | Weight | Rationale |
|--------|--------|-----------|
| Age | 0.35 | Strongest signal of evidence reliability |
| Verification level | 0.25 | Higher verification = more trustworthy |
| Collection frequency | 0.20 | Frequently collected evidence is more current |
| Control criticality | 0.20 | Critical controls need fresher evidence |

### Appendix C: Conflict Resolution Strategy Priority

| Priority | Strategy | When Applied |
|----------|----------|-------------|
| 1 | Verification level | Different verification levels |
| 2 | Recency | Same verification level, different timestamps |
| 3 | Source authority | Same verification level and timestamp |
| 4 | Consensus | 3+ evidence items, no clear winner |
| 5 | Escalation | All strategies inconclusive |

### Appendix D: Retention State Transitions

| From | To | Trigger | Automated |
|------|----|---------|-----------|
| ACTIVE | ARCHIVING | active_period expires | Yes |
| ARCHIVING | ARCHIVED | archive complete | Yes |
| ARCHIVED | REVIEW | retention_period expires | Yes |
| REVIEW | DELETING | No legal hold, no audit window | Yes |
| REVIEW | LEGAL_HOLD | Legal hold active | Yes |
| LEGAL_HOLD | REVIEW | Legal hold released | Yes |
| DELETING | CERTIFIED | Deletion verified | Yes |
| Any | LEGAL_HOLD | Legal hold issued | Yes |

### Appendix E: Package Generation Checklist

- [ ] Controls selected per framework and filters
- [ ] Evidence items gathered per control
- [ ] Superseded evidence excluded
- [ ] Expired evidence excluded (unless requested)
- [ ] OSCAL assessment-results generated
- [ ] Chain of custody included
- [ ] Gap analysis computed
- [ ] Compliance posture calculated
- [ ] Package hash computed
- [ ] Package signed (ECDSA P-256)
- [ ] Timestamp token obtained (RFC 3161)
- [ ] Signatures embedded
- [ ] README generated
- [ ] Formats rendered (JSON, PDF, CSV)
- [ ] Package verified
- [ ] Delivery confirmed
- [ ] Audit log updated

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Architecture Team | Initial deep implementation specification |

---

*This specification is a living document. It shall be reviewed and updated:*
- *After any significant compliance incident*
- *When new regulations or framework versions take effect*
- *When new AI use cases are introduced*
- *At minimum, annually*

---

*End of Specification*
