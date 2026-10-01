# GRC_Claw — Expanded Technical Specification

**Version:** 1.1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Author:** Ahmed Hassan (CISO/GRC)  
**License:** Apache 2.0  
**Supersedes:** GRC_CLAW_TECHNICAL_SPEC.md v1.0.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Complete Entity-Relationship Diagram](#2-complete-entity-relationship-diagram)
3. [JSON Schema for Core Entities](#3-json-schema-for-core-entities)
4. [API Contract Tests](#4-api-contract-tests)
5. [Data Migration Strategy](#5-data-migration-strategy)
6. [Performance Benchmarks](#6-performance-benchmarks)
7. [Scalability Test Plan](#7-scalability-test-plan)
8. [Appendices](#8-appendices)

---

## 1. Executive Summary

This document expands the GRC_Claw Technical Specification v1.0.0 with detailed data models, API contracts, migration strategy, and performance/scalability test plans. It integrates content from both the base technical spec and the integration specification, providing a single authoritative reference for implementation.

### What's New in v1.1.0

| Section | Description |
|---------|-------------|
| ER Diagram | Complete crow's-foot notation with all entities, relationships, cardinalities, and constraints |
| JSON Schema | Draft 2020-12 JSON Schema for all 14 entities (5 core + 9 supporting) |
| API Contract Tests | 87 contract tests covering all REST endpoints with request/response validation |
| Data Migration | 5-phase migration strategy with rollback procedures and compatibility mapping |
| Performance Benchmarks | 12 benchmark suites with target SLAs, test data, and measurement methodology |
| Scalability Test Plan | 6 scalability test scenarios with load profiles, scaling triggers, and pass criteria |

---

## 2. Complete Entity-Relationship Diagram

### 2.1 Full ER Diagram (Crow's Foot Notation)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              GRC_Claw Entity-Relationship Diagram                                │
│                                                                                                 │
│  ┌──────────────┐         1:*         ┌──────────────┐         1:*         ┌──────────────┐     │
│  │  Framework   │─────────────────────│   Control    │─────────────────────│    Policy    │     │
│  │              │                     │              │                     │              │     │
│  │ framework_id │                     │ control_id   │                     │ policy_id    │     │
│  │ name         │                     │ title        │                     │ name         │     │
│  │ version      │                     │ description  │                     │ version      │     │
│  │ type         │                     │ family       │                     │ status       │     │
│  │ domains[]    │                     │ frameworks[] │                     │ category     │     │
│  │ crosswalks[] │                     │ impl.type    │                     │ rules[]      │     │
│  │ source_url   │                     │ parent_id    │                     │ scope{}      │     │
│  │ effective_dt │                     │ related[]    │                     │ fw_mappings[]│     │
│  └──────┬───────┘                     └──────┬───────┘                     └──────┬───────┘     │
│         │                                    │                                    │             │
│         │ 1:*                                │ 1:*                               │ 1:*         │
│         │                                    │                                    │             │
│         ▼                                    ▼                                    ▼             │
│  ┌──────────────┐                     ┌──────────────┐                     ┌──────────────┐     │
│  │  Framework   │                     │   Control    │                     │  PolicyRule  │     │
│  │  Domain      │                     │  Mapping     │                     │              │     │
│  │              │                     │              │                     │ rule_id      │     │
│  │ domain_id    │                     │ mapping_id   │                     │ policy_id FK │     │
│  │ framework_id │                     │ control_id   │                     │ name         │     │
│  │ name         │                     │ framework_id │                     │ description  │     │
│  │ controls[]   │                     │ fw_ctrl_id   │                     │ condition{}  │     │
│  └──────────────┘                     │ strength     │                     │ effect       │     │
│                                       └──────────────┘                     │ priority     │     │
│                                                                            │ approvers[]  │     │
│                                                                            │ limit_expr   │     │
│                                                                            └──────────────┘     │
│                                                                                                 │
│  ┌──────────────┐         1:*         ┌──────────────┐         1:*         ┌──────────────┐     │
│  │    Agent     │─────────────────────│ Enforcement  │─────────────────────│   Evidence   │     │
│  │              │                     │              │                     │              │     │
│  │ agent_id     │                     │ enforce_id   │                     │ evidence_id  │     │
│  │ name         │                     │ decision     │                     │ type         │     │
│  │ type         │                     │ agent_id FK  │                     │ title        │     │
│  │ status       │                     │ action{}     │                     │ content{}    │     │
│  │ identity{}   │                     │ policy_id FK │                     │ source{}     │     │
│  │ capabilities │                     │ rules_eval   │                     │ ctrl_map[]   │     │
│  │ trust_score  │                     │ eval_context │                     │ context{}    │     │
│  │ owner        │                     │ reason       │                     │ verif_level  │     │
│  │ team         │                     │ confidence   │                     │ verif_detail │     │
│  │ bu           │                     │ deterministic│                     │ custody[]    │     │
│  │ itil6c       │                     │ redaction{}  │                     │ oscal{}      │     │
│  │ registered   │                     │ escalation{} │                     │ retention    │     │
│  │ last_active  │                     │ quarantine{} │                     │ expires_at   │     │
│  └──────┬───────┘                     │ evidence_ids │                     └──────┬───────┘     │
│         │                             │ audit_trail  │                            │             │
│         │ 1:*                        │ latency_ms   │                            │ 1:*         │
│         │                             │ total_ms     │                            │             │
│         ▼                             └──────┬───────┘                            ▼             │
│  ┌──────────────┐                            │                     ┌──────────────┐            │
│  │  Agent       │                            │                     │  Evidence    │            │
│  │  Capability  │                            │                     │  Custody     │            │
│  │              │                            │                     │  Event       │            │
│  │ cap_id       │                            │                     │              │            │
│  │ agent_id FK  │                            │                     │ custody_id   │            │
│  │ name         │                            │                     │ evidence_id  │            │
│  │ description  │                            │                     │ action       │            │
│  │ risk_tier    │                            │                     │ actor        │            │
│  │ allowed_tools│                            │                     │ timestamp    │            │
│  │ allowed_res  │                            │                     │ ev_hash      │            │
│  │ max_autonomy │                            │                     │ prev_ev_hash │            │
│  └──────────────┘                            │                     │ signature    │            │
│                                              │                     └──────────────┘            │
│                                              │                                                 │
│  ┌──────────────┐         1:*         ┌──────▼─────────┐         1:*         ┌──────────────┐  │
│  │  Assessment  │─────────────────────│  Assessment    │─────────────────────│  Control     │  │
│  │              │                     │  Result        │                     │  Result      │  │
│  │ assess_id    │                     │                │                     │              │  │
│  │ type         │                     │ result_id      │                     │ ctrl_res_id  │  │
│  │ subject{}    │                     │ assess_id FK   │                     │ assess_id FK │  │
│  │ framework    │                     │ control_id     │                     │ control_id   │  │
│  │ ctrl_ids[]   │                     │ result         │                     │ result       │  │
│  │ period{}     │                     │ score          │                     │ score        │  │
│  │ status       │                     │ evidence_ids   │                     │ evidence_ids │  │
│  │ score        │                     │ findings[]     │                     │ findings[]   │  │
│  │ result       │                     │ tested_at      │                     │ tested_at    │  │
│  │ methodology  │                     │ tested_by      │                     │ tested_by    │  │
│  │ assessor     │                     │ notes          │                     │ notes        │  │
│  │ evidence_ids │                     └────────────────┘                     └──────────────┘  │
│  │ prev_assess  │                                                                        │
│  │ change_sum   │         1:*         ┌──────────────┐         1:*         ┌──────────────┐  │
│  └──────┬───────┘─────────────────────│   Finding    │─────────────────────│  Remediation │  │
│         │                             │              │                     │              │  │
│         │                             │ finding_id   │                     │ remed_id     │  │
│         │                             │ title        │                     │ finding_id   │  │
│         │                             │ description  │                     │ plan         │  │
│         │                             │ severity     │                     │ assigned_to  │  │
│         │                             │ status       │                     │ due_date     │  │
│         │                             │ source       │                     │ completed_at │  │
│         │                             │ ctrl_id FK   │                     │ verified_by  │  │
│         │                             │ policy_id FK │                     │ verif_evid   │  │
│         │                             │ agent_id FK  │                     └──────────────┘  │
│         │                             │ evidence_ids │                                        │
│         │                             │ remediation{}│         1:*         ┌──────────────┐  │
│         │                             │ identified_at │─────────────────────│   Risk       │  │
│         │                             │ resolved_at   │                     │              │  │
│         │                             │ sla_breach    │                     │ risk_id      │  │
│         │                             └──────────────┘                     │ title        │  │
│         │                                                                │ description  │  │
│         │                                                                │ category     │  │
│         │                                                                │ likelihood   │  │
│         │                                                                │ impact       │  │
│         │                                                                │ risk_score   │  │
│         │                                                                │ risk_tier    │  │
│         │                                                                │ airss{}      │  │
│         │                                                                │ treatment    │  │
│         │                                                                │ residual     │  │
│         │                                                                │ risk_owner   │  │
│         │                                                                │ review_date  │  │
│         │                                                                │ rel_ctrls[]  │  │
│         │                                                                │ rel_pols[]   │  │
│         │                                                                │ rel_agents[] │  │
│         │                                                                │ rel_findings[]│ │
│         │                                                                └──────┬───────┘  │
│         │                                                                       │ 1:*      │
│         │                                                                       ▼           │
│         │                                                                ┌──────────────┐  │
│         │                                                                │  Risk        │  │
│         │                                                                │  Treatment   │  │
│         │                                                                │  Record      │  │
│         │                                                                │              │  │
│         │                                                                │ treat_id     │  │
│         │                                                                │ risk_id FK   │  │
│         │                                                                │ treatment    │  │
│         │                                                                │ plan        │  │
│         │                                                                │ residual     │  │
│         │                                                                │ status       │  │
│         │                                                                └──────────────┘  │
│         │                                                                             │
│  ┌──────▼───────┐         1:*         ┌──────────────┐         1:*         ┌──────────────┐  │
│  │  Compliance  │─────────────────────│  Compliance  │─────────────────────│  Control     │  │
│  │  Posture     │                     │  Control     │                     │  Compliance  │  │
│  │              │                     │  Mapping     │                     │              │  │
│  │ compliance_id│                     │              │                     │ cc_id        │  │
│  │ org_id       │                     │ ccm_id       │                     │ compliance_id│  │
│  │ scope{}      │                     │ compliance_id│                     │ control_id   │  │
│  │ framework    │                     │ control_id   │                     │ status       │  │
│  │ status       │                     │ status       │                     │ evidence_ids │  │
│  │ score        │                     │ evidence_ids │                     │ assess_id FK │  │
│  │ trend        │                     │ assess_id FK │                     │ last_verified│  │
│  │ gaps{}       │                     │ last_verified│                     │ next_due     │  │
│  │ evid_summary │                     │ next_due     │                     │ gap_desc     │  │
│  │ report_ids[] │                     │ gap_desc     │                     │ remed_plan   │  │
│  │ computed_at  │                     │ remed_plan   │                     └──────────────┘  │
│  │ valid_until  │                     └──────────────┘                                        │
│  └──────────────┘                                                                        │
│                                                                             │
│  ┌──────────────┐         1:*         ┌──────────────┐         1:*         ┌──────────────┐  │
│  │  AuditTrail  │─────────────────────│  AuditTrail  │                     │  Decision    │  │
│  │              │                     │  Entity Ref  │                     │              │  │
│  │ audit_id     │                     │              │                     │ decision_id  │  │
│  │ event_type   │                     │ aref_id      │                     │ type         │  │
│  │ actor{}      │                     │ audit_id FK  │                     │ decision     │  │
│  │ action       │                     │ entity_type  │                     │ rationale    │  │
│  │ resource{}   │                     │ entity_id    │                     │ decided_by   │  │
│  │ context{}    │                     └──────────────┘                     │ decided_by_t │  │
│  │ before_state │                                                          │ decided_at   │  │
│  │ after_state  │         1:*         ┌──────────────┐                     │ context{}    │  │
│  │ timestamp    │─────────────────────│  AuditTrail  │                     │ rel_entities │  │
│  │ integ_hash  │                     │  Integrity   │                     │ approvals[]  │  │
│  │ prev_hash    │                     │  Check       │                     │ evidence_ids │  │
│  │ signature    │                     │              │                     │ status       │  │
│  │ merkle_root  │                     │ check_id     │                     │ expires_at   │  │
│  │ blockchain   │                     │ audit_id FK  │                     │ revoked_at   │  │
│  └──────────────┘                     │ check_type   │                     │ revoked_by   │  │
│                                       │ result       │                     │ revoke_reason│  │
│                                       │ checked_at   │                     └──────────────┘  │
│                                       │ details{}    │                                        │
│                                       └──────────────┘                                        │
│                                                                             │
│  ┌──────────────┐         1:*         ┌──────────────┐         1:*         ┌──────────────┐  │
│  │  Exception   │─────────────────────│  Exception   │                     │  Vendor      │  │
│  │              │                     │  Approval    │                     │              │  │
│  │ exception_id │                     │              │                     │ vendor_id    │  │
│  │ type         │                     │ appr_id      │                     │ name         │  │
│  │ title        │                     │ exception_id │                     │ type         │  │
│  │ description  │                     │ approver     │                     │ risk_tier    │  │
│  │ justification│                     │ decision     │                     │ composite    │  │
│  │ comp_ctrls[] │                     │ timestamp    │                     │ risk_dims{}  │  │
│  │ policy_id FK │                     │ comments     │                     │ status       │  │
│  │ ctrl_id FK   │                     └──────────────┘                     │ contract     │  │
│  │ agent_id FK  │                                                          │ fourth_party │  │
│  │ resource_scope│                                                         │ last_assess  │  │
│  │ requested_by │         1:*         ┌──────────────┐                     │ next_assess  │  │
│  │ requested_at │─────────────────────│  Exception   │                     │ metadata{}   │  │
│  │ approved_by  │                     │  Evidence    │                     └──────────────┘  │
│  │ approved_at  │                     │              │                                        │
│  │ approval_chain│                    │ ev_id        │                                        │
│  │ status       │                     │ exception_id │                                        │
│  │ effective_dt │                     │ evidence_id  │                                        │
│  │ expiration_dt│                     └──────────────┘                                        │
│  │ review_date  │                                                                        │
│  │ evidence_ids │                                                                        │
│  └──────────────┘                                                                        │
│                                                                             │
│  ┌──────────────┐         1:*         ┌──────────────┐                                        │
│  │  Enforcement │─────────────────────│  Enforcement │                                        │
│  │  Profile     │                     │  Hook        │                                        │
│  │              │                     │              │                                        │
│  │ profile_id   │                     │ hook_id      │                                        │
│  │ agent_id FK  │                     │ profile_id   │                                        │
│  │ name         │                     │ point        │                                        │
│  │ config{}     │                     │ callback     │                                        │
│  │ created_at   │                     │ priority     │                                        │
│  └──────────────┘                     └──────────────┘                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Relationship Summary

| Relationship | Cardinality | Type | Description |
|-------------|-------------|------|-------------|
| Framework → Control | 1:* | Composition | A framework contains many controls |
| Control → Policy | 1:* | Association | A control maps to many policies |
| Policy → PolicyRule | 1:* | Composition | A policy contains many rules |
| Agent → Enforcement | 1:* | Association | An agent has many enforcement decisions |
| Policy → Enforcement | 1:* | Association | A policy generates many enforcement decisions |
| Enforcement → Evidence | 1:* | Association | An enforcement decision produces many evidence items |
| Assessment → ControlResult | 1:* | Composition | An assessment has many control results |
| Assessment → Finding | 1:* | Association | An assessment produces many findings |
| Finding → Remediation | 1:1 | Association | A finding has one remediation plan |
| Risk → Finding | 1:* | Association | A risk links to many findings |
| Compliance → ControlCompliance | 1:* | Composition | A compliance posture has many control mappings |
| AuditTrail → AuditEntityRef | 1:* | Composition | An audit event references many entities |
| Agent → Capability | 1:* | Composition | An agent has many capabilities |
| Exception → ExceptionApproval | 1:* | Composition | An exception has many approval records |
| Exception → ExceptionEvidence | 1:* | Composition | An exception has many evidence items |
| EnforcementProfile → EnforcementHook | 1:* | Composition | A profile has many hooks |
| Framework → FrameworkDomain | 1:* | Composition | A framework has many domains |
| Control → ControlMapping | 1:* | Composition | A control has many framework mappings |
| Evidence → CustodyEvent | 1:* | Composition | An evidence has many custody events |
| Risk → RiskTreatment | 1:* | Association | A risk has many treatment records |
| Decision → Evidence | 1:* | Association | A decision references many evidence items |

### 2.3 Constraints and Business Rules

| Constraint | Type | Description |
|-----------|------|-------------|
| `UNIQUE(framework_id, version)` | Unique | One version per framework |
| `UNIQUE(control_id, framework_id)` | Unique | Control ID unique within framework |
| `UNIQUE(policy_id, version)` | Unique | One version per policy |
| `UNIQUE(agent_id, name)` | Unique | Agent name unique per org |
| `CHECK (score >= 0.0 AND score <= 1.0)` | Check | All scores normalized 0-1 |
| `CHECK (risk_score >= 0.0)` | Check | Risk score non-negative |
| `CHECK (effective_date < expiration_date)` | Check | Valid date ranges |
| `CHECK (trust_score >= 0.0 AND trust_score <= 1.0)` | Check | Trust score normalized |
| `FK enforcement.agent_id → agent.agent_id` | Foreign Key | Enforcement references valid agent |
| `FK enforcement.policy_id → policy.policy_id` | Foreign Key | Enforcement references valid policy |
| `FK evidence.policy_id → policy.policy_id` | Foreign Key | Evidence references valid policy |
| `FK assessment.subject_id → agent.agent_id` | Foreign Key | Assessment references valid subject |
| `FK compliance.org_id → organization.org_id` | Foreign Key | Multi-tenant isolation |
| `ON DELETE CASCADE` | Cascade | Child records deleted with parent |
| `ON DELETE SET NULL` | Set Null | Optional FK set to null on delete |

---

## 3. JSON Schema for Core Entities

### 3.1 Policy Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/policy.json",
  "title": "GRC_Claw Policy",
  "description": "A declarative governance rule that defines what is allowed, required, or prohibited",
  "type": "object",
  "required": ["policy_id", "name", "version", "status", "category", "rules", "policy_language", "scope", "owner", "created_at", "updated_at"],
  "properties": {
    "policy_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique policy identifier"
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 255,
      "description": "Human-readable policy name"
    },
    "description": {
      "type": "string",
      "maxLength": 4000
    },
    "version": {
      "type": "string",
      "pattern": "^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)(?:-((?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\\.(?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\\+([0-9a-zA-Z-]+(?:\\.[0-9a-zA-Z-]+)*))?$",
      "description": "Semantic version"
    },
    "status": {
      "type": "string",
      "enum": ["draft", "review", "active", "deprecated", "archived"]
    },
    "category": {
      "type": "string",
      "enum": ["data_handling", "agent_behavior", "model_governance", "access_control", "content_safety", "privacy", "custom"]
    },
    "rules": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/$defs/PolicyRule" }
    },
    "policy_language": {
      "type": "string",
      "enum": ["aigolang", "rego", "cedar", "yaml", "json"]
    },
    "compiled_rules": {
      "type": "object",
      "description": "Compiled enforcement rules"
    },
    "scope": { "$ref": "#/$defs/PolicyScope" },
    "framework_mappings": {
      "type": "array",
      "items": { "$ref": "#/$defs/FrameworkMapping" }
    },
    "effective_date": { "type": "string", "format": "date-time" },
    "expiration_date": { "type": "string", "format": "date-time" },
    "review_cycle": {
      "type": "string",
      "enum": ["continuous", "daily", "weekly", "monthly", "quarterly", "annual"]
    },
    "owner": { "type": "string", "format": "uuid" },
    "approvers": {
      "type": "array",
      "items": { "type": "string", "format": "uuid" }
    },
    "parent_policy_id": { "type": ["string", "null"], "format": "uuid" },
    "change_description": { "type": "string" },
    "tags": {
      "type": "array",
      "items": { "type": "string" }
    },
    "labels": {
      "type": "object",
      "additionalProperties": { "type": "string" }
    },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" },
    "created_by": { "type": "string", "format": "uuid" },
    "updated_by": { "type": "string", "format": "uuid" },
    "enforcement": { "$ref": "#/$defs/EnforcementConfig" }
  },
  "$defs": {
    "PolicyRule": {
      "type": "object",
      "required": ["rule_id", "name", "condition", "effect", "priority"],
      "properties": {
        "rule_id": { "type": "string", "format": "uuid" },
        "name": { "type": "string", "minLength": 1, "maxLength": 255 },
        "description": { "type": "string" },
        "condition": {
          "type": "object",
          "required": ["type", "expression"],
          "properties": {
            "type": { "type": "string", "enum": ["cedar", "rego", "aigolang", "json", "yaml"] },
            "expression": { "type": "string" },
            "query": { "type": "string" }
          }
        },
        "effect": {
          "type": "string",
          "enum": ["allow", "deny", "warn", "require_approval", "transform", "escalate", "throttle", "log"]
        },
        "priority": { "type": "integer", "minimum": 0, "maximum": 10000 },
        "approvers": {
          "type": "array",
          "items": { "type": "string" }
        },
        "limit_expression": { "type": "string" }
      }
    },
    "PolicyScope": {
      "type": "object",
      "properties": {
        "agents": { "type": "array", "items": { "type": "string" } },
        "models": { "type": "array", "items": { "type": "string" } },
        "resources": { "type": "array", "items": { "type": "string" } },
        "environments": {
          "type": "array",
          "items": { "type": "string", "enum": ["prod", "staging", "dev", "all"] }
        },
        "risk_tiers": {
          "type": "array",
          "items": { "type": "string", "enum": ["prohibited", "high", "limited", "minimal", "all"] }
        }
      }
    },
    "FrameworkMapping": {
      "type": "object",
      "required": ["framework", "control_ids", "mapping_strength"],
      "properties": {
        "framework": { "type": "string" },
        "control_ids": { "type": "array", "items": { "type": "string" } },
        "mapping_strength": { "type": "string", "enum": ["direct", "partial", "indirect"] }
      }
    },
    "EnforcementConfig": {
      "type": "object",
      "properties": {
        "mode": { "type": "string", "enum": ["enforce", "dry_run", "audit_only"] },
        "on_violation": { "type": "string", "enum": ["block", "redact", "escalate", "log", "quarantine"] },
        "fail_mode": { "type": "string", "enum": ["open", "closed"] },
        "escalation_target": { "type": "string" }
      }
    }
  }
}
```

### 3.2 Evidence Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/evidence.json",
  "title": "GRC_Claw Evidence",
  "description": "A cryptographically verifiable artifact that proves a control was satisfied",
  "type": "object",
  "required": ["evidence_id", "type", "title", "content", "source", "verification_level", "created_at"],
  "properties": {
    "evidence_id": { "type": "string", "format": "uuid" },
    "type": {
      "type": "string",
      "enum": ["artifact", "observation", "interview", "analysis", "log", "policy_evaluation", "assessment_result", "incident_record", "audit_event", "compliance_mapping", "risk_assessment"]
    },
    "title": { "type": "string", "minLength": 1, "maxLength": 500 },
    "description": { "type": "string" },
    "content": {
      "type": "object",
      "required": ["format", "data", "hash"],
      "properties": {
        "format": { "type": "string", "description": "MIME type" },
        "data": { "type": ["string", "object", "array"], "description": "Base64, inline, or URI reference" },
        "hash": {
          "type": "object",
          "required": ["algorithm", "value"],
          "properties": {
            "algorithm": { "type": "string", "enum": ["SHA-256", "SHA-384", "SHA-512"] },
            "value": { "type": "string", "pattern": "^[a-fA-F0-9]{64,128}$" }
          }
        }
      }
    },
    "source": {
      "type": "object",
      "required": ["system", "collected_at"],
      "properties": {
        "system": { "type": "string" },
        "location": { "type": "string" },
        "collector_id": { "type": "string" },
        "collector_version": { "type": "string" },
        "collected_at": { "type": "string", "format": "date-time" }
      }
    },
    "control_mappings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["control_id", "framework"],
        "properties": {
          "control_id": { "type": "string" },
          "framework": { "type": "string" },
          "control_title": { "type": "string" },
          "control_family": { "type": "string" }
        }
      }
    },
    "context": {
      "type": "object",
      "properties": {
        "environment": { "type": "string", "enum": ["prod", "staging", "dev"] },
        "resource_scope": { "type": "string" },
        "time_window": {
          "type": "object",
          "properties": {
            "start": { "type": "string", "format": "date-time" },
            "end": { "type": "string", "format": "date-time" }
          }
        },
        "agent_id": { "type": ["string", "null"], "format": "uuid" },
        "policy_id": { "type": ["string", "null"], "format": "uuid" },
        "input_hash": { "type": "string" },
        "output_hash": { "type": "string" },
        "trace_id": { "type": "string" }
      }
    },
    "verification_level": {
      "type": "string",
      "enum": ["L0", "L1", "L2", "L3", "L4"]
    },
    "verification_details": {
      "type": "object",
      "properties": {
        "schema_valid": { "type": "boolean" },
        "hash_verified": { "type": "boolean" },
        "chain_of_custody_intact": { "type": "boolean" },
        "cross_validated": { "type": "boolean" },
        "attested": { "type": "boolean" },
        "attested_by": { "type": "string" },
        "attested_at": { "type": "string", "format": "date-time" }
      }
    },
    "chain_of_custody": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["action", "actor", "timestamp", "evidence_hash", "previous_event_hash", "signature"],
        "properties": {
          "action": { "type": "string", "enum": ["collected", "transferred", "verified", "exported", "accessed"] },
          "actor": { "type": "string" },
          "timestamp": { "type": "string", "format": "date-time" },
          "evidence_hash": { "type": "string" },
          "previous_event_hash": { "type": "string" },
          "signature": { "type": "string" }
        }
      }
    },
    "oscal": {
      "type": "object",
      "properties": {
        "version": { "type": "string" },
        "assessment_plan_id": { "type": "string" },
        "assessment_result_id": { "type": "string" },
        "observation_id": { "type": "string" }
      }
    },
    "retention_class": {
      "type": "string",
      "enum": ["security_log", "config_snapshot", "access_review", "vuln_scan", "attestation", "custom"]
    },
    "retention_period": { "type": "string" },
    "expires_at": { "type": "string", "format": "date-time" },
    "compliance_tags": {
      "type": "array",
      "items": { "type": "string" }
    },
    "proof": {
      "type": "object",
      "properties": {
        "merkle_root": { "type": "string" },
        "merkle_path": { "type": "array", "items": { "type": "string" } },
        "signature": { "type": "string" }
      }
    },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" }
  }
}
```

### 3.3 Enforcement Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/enforcement.json",
  "title": "GRC_Claw Enforcement Decision",
  "description": "A runtime governance decision applied to an agent action or system event",
  "type": "object",
  "required": ["enforcement_id", "decision", "agent_id", "action", "policy_id", "decision_reason", "confidence_score", "deterministic", "requested_at", "decided_at"],
  "properties": {
    "enforcement_id": { "type": "string", "format": "uuid" },
    "decision": {
      "type": "string",
      "enum": ["ALLOW", "ALLOW_WITH_REDACTION", "REQUIRE_APPROVAL", "DENY", "QUARANTINE"]
    },
    "agent_id": { "type": "string", "format": "uuid" },
    "action": {
      "type": "object",
      "required": ["type", "resource"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["tool_call", "api_request", "data_access", "code_execution", "file_access", "network_access", "model_inference", "custom"]
        },
        "tool_name": { "type": "string" },
        "resource": { "type": "string" },
        "parameters": { "type": "object" }
      }
    },
    "policy_id": { "type": "string", "format": "uuid" },
    "policy_version": { "type": "string" },
    "rules_evaluated": { "type": "object" },
    "evaluation_context": { "type": "object" },
    "decision_reason": { "type": "string" },
    "confidence_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0
    },
    "deterministic": { "type": "boolean" },
    "redaction": {
      "type": ["object", "null"],
      "properties": {
        "fields_redacted": { "type": "array", "items": { "type": "string" } },
        "redaction_method": { "type": "string", "enum": ["mask", "tokenize", "remove", "replace"] },
        "original_hash": { "type": "string" }
      }
    },
    "escalation": {
      "type": ["object", "null"],
      "properties": {
        "escalation_id": { "type": "string", "format": "uuid" },
        "escalated_to": { "type": "string" },
        "escalation_reason": { "type": "string" },
        "status": { "type": "string", "enum": ["pending", "approved", "denied", "expired", "escalated"] },
        "resolved_at": { "type": "string", "format": "date-time" },
        "resolved_by": { "type": "string" }
      }
    },
    "quarantine": {
      "type": ["object", "null"],
      "properties": {
        "quarantine_id": { "type": "string", "format": "uuid" },
        "reason": { "type": "string" },
        "scope": { "type": "string", "enum": ["agent", "tool", "session", "resource"] },
        "initiated_at": { "type": "string", "format": "date-time" },
        "initiated_by": { "type": "string" },
        "status": { "type": "string", "enum": ["active", "lifted", "expired"] },
        "lift_conditions": { "type": "string" }
      }
    },
    "evidence_ids": {
      "type": "array",
      "items": { "type": "string", "format": "uuid" }
    },
    "audit_trail_id": { "type": "string", "format": "uuid" },
    "requested_at": { "type": "string", "format": "date-time" },
    "decided_at": { "type": "string", "format": "date-time" },
    "executed_at": { "type": "string", "format": "date-time" },
    "evaluation_latency_ms": { "type": "integer", "minimum": 0 },
    "total_latency_ms": { "type": "integer", "minimum": 0 }
  }
}
```

### 3.4 Assessment Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/assessment.json",
  "title": "GRC_Claw Assessment",
  "description": "An evaluation of compliance posture against a framework, control set, or policy",
  "type": "object",
  "required": ["assessment_id", "type", "subject", "status", "overall_score", "overall_result", "created_at"],
  "properties": {
    "assessment_id": { "type": "string", "format": "uuid" },
    "type": {
      "type": "string",
      "enum": ["control_assessment", "framework_assessment", "risk_assessment", "impact_assessment", "vendor_assessment", "agent_assessment"]
    },
    "subject": {
      "type": "object",
      "required": ["subject_type", "subject_id", "subject_name"],
      "properties": {
        "subject_type": { "type": "string", "enum": ["agent", "model", "system", "vendor", "process", "organization"] },
        "subject_id": { "type": "string" },
        "subject_name": { "type": "string" }
      }
    },
    "framework": { "type": "string" },
    "control_ids": { "type": "array", "items": { "type": "string" } },
    "assessment_period": {
      "type": "object",
      "properties": {
        "start": { "type": "string", "format": "date-time" },
        "end": { "type": "string", "format": "date-time" }
      }
    },
    "status": {
      "type": "string",
      "enum": ["not_started", "in_progress", "completed", "failed", "expired"]
    },
    "overall_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0
    },
    "overall_result": {
      "type": "string",
      "enum": ["compliant", "partially_compliant", "non_compliant", "not_assessed"]
    },
    "control_results": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["control_id", "result", "score", "tested_at"],
        "properties": {
          "control_id": { "type": "string" },
          "result": { "type": "string", "enum": ["pass", "fail", "partial", "not_applicable", "not_tested"] },
          "score": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
          "evidence_ids": { "type": "array", "items": { "type": "string" } },
          "findings": { "type": "array", "items": { "type": "string" } },
          "tested_at": { "type": "string", "format": "date-time" },
          "tested_by": { "type": "string" },
          "notes": { "type": "string" }
        }
      }
    },
    "risk_assessment": {
      "type": ["object", "null"],
      "properties": {
        "risks_identified": { "type": "integer" },
        "risks_mitigated": { "type": "integer" },
        "risks_accepted": { "type": "integer" },
        "residual_risk_score": { "type": "number" },
        "risk_acceptance_records": { "type": "object" }
      }
    },
    "methodology": { "type": "string" },
    "assessor": { "type": "string" },
    "assessor_type": { "type": "string", "enum": ["human", "automated", "hybrid"] },
    "evidence_ids": { "type": "array", "items": { "type": "string" } },
    "created_at": { "type": "string", "format": "date-time" },
    "started_at": { "type": "string", "format": "date-time" },
    "completed_at": { "type": "string", "format": "date-time" },
    "next_assessment_date": { "type": "string", "format": "date-time" },
    "valid_until": { "type": "string", "format": "date-time" },
    "previous_assessment_id": { "type": ["string", "null"], "format": "uuid" },
    "change_summary": { "type": "string" }
  }
}
```

### 3.5 Compliance Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/compliance.json",
  "title": "GRC_Claw Compliance Posture",
  "description": "A computed compliance posture mapping controls to frameworks with evidence status",
  "type": "object",
  "required": ["compliance_id", "organization_id", "scope", "framework", "overall_status", "compliance_score", "computed_at"],
  "properties": {
    "compliance_id": { "type": "string", "format": "uuid" },
    "organization_id": { "type": "string", "format": "uuid" },
    "scope": {
      "type": "object",
      "required": ["scope_type", "scope_id", "scope_name"],
      "properties": {
        "scope_type": { "type": "string", "enum": ["organization", "business_unit", "system", "agent", "custom"] },
        "scope_id": { "type": "string" },
        "scope_name": { "type": "string" }
      }
    },
    "framework": {
      "type": "object",
      "required": ["framework_id", "framework_version", "framework_name"],
      "properties": {
        "framework_id": { "type": "string" },
        "framework_version": { "type": "string" },
        "framework_name": { "type": "string" }
      }
    },
    "overall_status": {
      "type": "string",
      "enum": ["compliant", "partially_compliant", "non_compliant", "unknown"]
    },
    "compliance_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0
    },
    "trend": {
      "type": "string",
      "enum": ["improving", "stable", "declining", "unknown"]
    },
    "control_mappings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["control_id", "control_title", "status"],
        "properties": {
          "control_id": { "type": "string" },
          "control_title": { "type": "string" },
          "control_family": { "type": "string" },
          "status": { "type": "string", "enum": ["compliant", "partially_compliant", "non_compliant", "not_applicable"] },
          "evidence_ids": { "type": "array", "items": { "type": "string" } },
          "assessment_id": { "type": ["string", "null"], "format": "uuid" },
          "last_verified": { "type": "string", "format": "date-time" },
          "next_due": { "type": "string", "format": "date-time" },
          "gap_description": { "type": "string" },
          "remediation_plan_id": { "type": ["string", "null"] }
        }
      }
    },
    "gaps": {
      "type": "object",
      "properties": {
        "total_controls": { "type": "integer" },
        "compliant_controls": { "type": "integer" },
        "partial_controls": { "type": "integer" },
        "non_compliant_controls": { "type": "integer" },
        "not_applicable_controls": { "type": "integer" },
        "not_assessed_controls": { "type": "integer" },
        "coverage_percentage": { "type": "number" }
      }
    },
    "evidence_summary": {
      "type": "object",
      "properties": {
        "total_evidence_items": { "type": "integer" },
        "by_type": { "type": "object" },
        "by_verification_level": { "type": "object" },
        "oldest_evidence": { "type": "string", "format": "date-time" },
        "newest_evidence": { "type": "string", "format": "date-time" }
      }
    },
    "last_report_generated": { "type": "string", "format": "date-time" },
    "report_ids": { "type": "array", "items": { "type": "string" } },
    "computed_at": { "type": "string", "format": "date-time" },
    "valid_until": { "type": "string", "format": "date-time" }
  }
}
```

### 3.6 Supporting Entity Schemas

#### Agent Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/agent.json",
  "title": "GRC_Claw Agent",
  "type": "object",
  "required": ["agent_id", "name", "type", "status", "identity", "owner", "registered_at"],
  "properties": {
    "agent_id": { "type": "string", "format": "uuid" },
    "name": { "type": "string", "minLength": 1, "maxLength": 255 },
    "type": { "type": "string", "enum": ["autonomous", "semi_autonomous", "human_in_loop", "human_on_loop"] },
    "status": { "type": "string", "enum": ["proposed", "approved", "active", "deprecated", "terminated"] },
    "identity": {
      "type": "object",
      "required": ["unique_id"],
      "properties": {
        "unique_id": { "type": "string" },
        "attestation": { "type": "string" },
        "certificate": { "type": "string" },
        "trust_score": { "type": "number", "minimum": 0.0, "maximum": 1.0 }
      }
    },
    "capabilities": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "risk_tier"],
        "properties": {
          "name": { "type": "string" },
          "description": { "type": "string" },
          "risk_tier": { "type": "string", "enum": ["prohibited", "high", "limited", "minimal"] },
          "allowed_tools": { "type": "array", "items": { "type": "string" } },
          "allowed_resources": { "type": "array", "items": { "type": "string" } },
          "max_autonomy_level": { "type": "string", "enum": ["full", "guarded", "supervised", "manual"] }
        }
      }
    },
    "owner": { "type": "string", "format": "uuid" },
    "owning_team": { "type": "string" },
    "business_unit": { "type": "string" },
    "policy_ids": { "type": "array", "items": { "type": "string", "format": "uuid" } },
    "enforcement_profile": { "type": ["string", "null"], "format": "uuid" },
    "assessment_schedule": { "type": "string" },
    "itil_6c_classification": { "type": "string", "enum": ["creation", "curation", "clarification", "cognition", "communication", "coordination"] },
    "togaf_capability_map": { "type": "string" },
    "registered_at": { "type": "string", "format": "date-time" },
    "last_active_at": { "type": "string", "format": "date-time" },
    "deprecated_at": { "type": "string", "format": "date-time" },
    "termination_reason": { "type": "string" }
  }
}
```

#### AuditTrail Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/audittrail.json",
  "title": "GRC_Claw Audit Trail Event",
  "type": "object",
  "required": ["audit_id", "event_type", "actor", "action", "resource", "timestamp", "integrity_hash", "previous_hash", "signature"],
  "properties": {
    "audit_id": { "type": "string", "format": "uuid" },
    "event_type": {
      "type": "string",
      "enum": ["policy_created", "policy_updated", "policy_activated", "enforcement_decision", "evidence_collected", "evidence_verified", "assessment_completed", "compliance_computed", "access_granted", "access_revoked", "agent_registered", "agent_terminated", "config_change", "incident_detected", "incident_resolved"]
    },
    "actor": {
      "type": "object",
      "required": ["type", "id"],
      "properties": {
        "type": { "type": "string", "enum": ["user", "agent", "system", "vendor"] },
        "id": { "type": "string" },
        "role": { "type": "string" },
        "auth_method": { "type": "string", "enum": ["oidc", "mtls", "api_key", "saml"] }
      }
    },
    "action": { "type": "string" },
    "resource": {
      "type": "object",
      "required": ["type", "id"],
      "properties": {
        "type": { "type": "string" },
        "id": { "type": "string" },
        "name": { "type": "string" }
      }
    },
    "context": { "type": "object" },
    "before_state": { "type": "object" },
    "after_state": { "type": "object" },
    "timestamp": { "type": "string", "format": "date-time" },
    "integrity_hash": { "type": "string", "pattern": "^[a-fA-F0-9]{64}$" },
    "previous_hash": { "type": "string", "pattern": "^[a-fA-F0-9]{64}$" },
    "signature": { "type": "string" },
    "merkle_root": { "type": "string" },
    "blockchain_anchor": { "type": "string" },
    "related_entity_ids": { "type": "object" }
  }
}
```

#### Risk Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/risk.json",
  "title": "GRC_Claw Risk",
  "type": "object",
  "required": ["risk_id", "title", "category", "likelihood", "impact", "risk_score", "risk_tier", "treatment"],
  "properties": {
    "risk_id": { "type": "string", "format": "uuid" },
    "title": { "type": "string", "minLength": 1 },
    "description": { "type": "string" },
    "category": { "type": "string", "enum": ["model", "data", "security", "compliance", "operational", "reputational"] },
    "likelihood": { "type": "string", "enum": ["rare", "unlikely", "possible", "likely", "almost_certain"] },
    "impact": { "type": "string", "enum": ["negligible", "minor", "moderate", "major", "catastrophic"] },
    "risk_score": { "type": "number", "minimum": 0.0 },
    "risk_tier": { "type": "string", "enum": ["low", "medium", "high", "critical"] },
    "airss": {
      "type": "object",
      "properties": {
        "adaptability": { "type": "number" },
        "integrity": { "type": "number" },
        "resilience": { "type": "number" },
        "scalability": { "type": "number" },
        "safety": { "type": "number" },
        "composite_score": { "type": "number" }
      }
    },
    "treatment": { "type": "string", "enum": ["avoid", "transfer", "mitigate", "accept"] },
    "treatment_plan": { "type": "string" },
    "residual_risk": { "type": "number" },
    "risk_owner": { "type": "string" },
    "review_date": { "type": "string", "format": "date-time" },
    "related_controls": { "type": "array", "items": { "type": "string" } },
    "related_policies": { "type": "array", "items": { "type": "string" } },
    "related_agents": { "type": "array", "items": { "type": "string" } },
    "related_findings": { "type": "array", "items": { "type": "string" } }
  }
}
```

#### Finding Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/finding.json",
  "title": "GRC_Claw Finding",
  "type": "object",
  "required": ["finding_id", "title", "severity", "status", "source", "identified_at"],
  "properties": {
    "finding_id": { "type": "string", "format": "uuid" },
    "title": { "type": "string", "minLength": 1 },
    "description": { "type": "string" },
    "severity": { "type": "string", "enum": ["critical", "high", "medium", "low", "informational"] },
    "status": { "type": "string", "enum": ["open", "in_progress", "resolved", "accepted", "false_positive"] },
    "source": { "type": "string", "enum": ["assessment", "monitoring", "incident", "audit", "manual"] },
    "source_id": { "type": "string" },
    "control_id": { "type": "string" },
    "policy_id": { "type": "string" },
    "agent_id": { "type": ["string", "null"] },
    "evidence_ids": { "type": "array", "items": { "type": "string" } },
    "remediation": {
      "type": ["object", "null"],
      "properties": {
        "plan": { "type": "string" },
        "assigned_to": { "type": "string" },
        "due_date": { "type": "string", "format": "date-time" },
        "completed_at": { "type": "string", "format": "date-time" },
        "verified_by": { "type": "string" },
        "verification_evidence": { "type": "array", "items": { "type": "string" } }
      }
    },
    "identified_at": { "type": "string", "format": "date-time" },
    "resolved_at": { "type": "string", "format": "date-time" },
    "sla_breach": { "type": "boolean" }
  }
}
```

#### Decision Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/decision.json",
  "title": "GRC_Claw Decision",
  "type": "object",
  "required": ["decision_id", "type", "decision", "rationale", "decided_by", "decided_by_type", "decided_at", "status"],
  "properties": {
    "decision_id": { "type": "string", "format": "uuid" },
    "type": { "type": "string", "enum": ["enforcement", "approval", "exception", "risk_acceptance", "policy_change"] },
    "decision": { "type": "string" },
    "rationale": { "type": "string" },
    "decided_by": { "type": "string" },
    "decided_by_type": { "type": "string", "enum": ["human", "automated", "hybrid"] },
    "decided_at": { "type": "string", "format": "date-time" },
    "context": { "type": "object" },
    "related_entities": { "type": "object" },
    "approvals": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["approver", "decision", "timestamp"],
        "properties": {
          "approver": { "type": "string" },
          "decision": { "type": "string", "enum": ["approved", "denied", "abstained"] },
          "timestamp": { "type": "string", "format": "date-time" },
          "comments": { "type": "string" }
        }
      }
    },
    "evidence_ids": { "type": "array", "items": { "type": "string" } },
    "status": { "type": "string", "enum": ["pending", "approved", "denied", "expired", "revoked"] },
    "expires_at": { "type": "string", "format": "date-time" },
    "revoked_at": { "type": "string", "format": "date-time" },
    "revoked_by": { "type": "string" },
    "revocation_reason": { "type": "string" }
  }
}
```

#### Exception Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/exception.json",
  "title": "GRC_Claw Exception",
  "type": "object",
  "required": ["exception_id", "type", "title", "justification", "status"],
  "properties": {
    "exception_id": { "type": "string", "format": "uuid" },
    "type": { "type": "string", "enum": ["policy_exception", "risk_acceptance", "control_exception", "temporal_exception", "scope_exception"] },
    "title": { "type": "string", "minLength": 1 },
    "description": { "type": "string" },
    "justification": { "type": "string" },
    "compensating_controls": { "type": "array", "items": { "type": "string" } },
    "policy_id": { "type": ["string", "null"] },
    "control_id": { "type": ["string", "null"] },
    "agent_id": { "type": ["string", "null"] },
    "resource_scope": { "type": "string" },
    "requested_by": { "type": "string" },
    "requested_at": { "type": "string", "format": "date-time" },
    "approved_by": { "type": "string" },
    "approved_at": { "type": "string", "format": "date-time" },
    "approval_chain": { "type": "object" },
    "status": { "type": "string", "enum": ["pending", "approved", "denied", "expired", "revoked"] },
    "effective_date": { "type": "string", "format": "date-time" },
    "expiration_date": { "type": "string", "format": "date-time" },
    "review_date": { "type": "string", "format": "date-time" },
    "evidence_ids": { "type": "array", "items": { "type": "string" } }
  }
}
```

#### Vendor Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/vendor.json",
  "title": "GRC_Claw Vendor",
  "type": "object",
  "required": ["vendor_id", "name", "type", "risk_tier", "status"],
  "properties": {
    "vendor_id": { "type": "string", "format": "uuid" },
    "name": { "type": "string", "minLength": 1 },
    "type": { "type": "string", "enum": ["model_provider", "platform_provider", "data_provider", "service_provider", "subcontractor"] },
    "risk_tier": { "type": "string", "enum": ["low", "medium", "high", "critical"] },
    "composite_risk_score": { "type": "number", "minimum": 1.0, "maximum": 5.0 },
    "risk_dimensions": {
      "type": "object",
      "properties": {
        "model_risk": { "type": "number" },
        "data_risk": { "type": "number" },
        "security_risk": { "type": "number" },
        "compliance_risk": { "type": "number" },
        "operational_risk": { "type": "number" },
        "reputational_risk": { "type": "number" }
      }
    },
    "status": { "type": "string", "enum": ["procurement", "integration", "monitoring", "retirement", "retired"] },
    "contract_start": { "type": "string", "format": "date-time" },
    "contract_end": { "type": "string", "format": "date-time" },
    "fourth_party_ids": { "type": "array", "items": { "type": "string" } },
    "last_assessment_id": { "type": ["string", "null"] },
    "next_assessment_date": { "type": "string", "format": "date-time" },
    "metadata": { "type": "object" }
  }
}
```

#### Control Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/control.json",
  "title": "GRC_Claw Control",
  "type": "object",
  "required": ["control_id", "title", "family", "frameworks"],
  "properties": {
    "control_id": { "type": "string" },
    "title": { "type": "string", "minLength": 1 },
    "description": { "type": "string" },
    "family": { "type": "string" },
    "frameworks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["framework_id", "framework_control_id"],
        "properties": {
          "framework_id": { "type": "string" },
          "framework_control_id": { "type": "string" },
          "framework_title": { "type": "string" }
        }
      }
    },
    "implementation": {
      "type": "object",
      "properties": {
        "type": { "type": "string", "enum": ["automated", "manual", "hybrid"] },
        "policy_ids": { "type": "array", "items": { "type": "string" } },
        "evidence_requirements": { "type": "array", "items": { "type": "string" } },
        "test_procedure": { "type": "string" }
      }
    },
    "related_controls": { "type": "array", "items": { "type": "string" } },
    "parent_control": { "type": ["string", "null"] }
  }
}
```

#### Framework Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://grcclaw.local/schemas/framework.json",
  "title": "GRC_Claw Framework",
  "type": "object",
  "required": ["framework_id", "name", "version", "type"],
  "properties": {
    "framework_id": { "type": "string" },
    "name": { "type": "string", "minLength": 1 },
    "version": { "type": "string" },
    "type": { "type": "string", "enum": ["regulatory", "standards", "internal", "custom"] },
    "domains": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["domain_id", "name"],
        "properties": {
          "domain_id": { "type": "string" },
          "name": { "type": "string" },
          "controls": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "crosswalks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "target_framework": { "type": "string" },
          "target_control": { "type": "string" },
          "mapping_strength": { "type": "string", "enum": ["direct", "partial", "indirect"] }
        }
      }
    },
    "source_url": { "type": "string" },
    "effective_date": { "type": "string" },
    "review_cycle": { "type": "string" }
  }
}
```

---

## 4. API Contract Tests

### 4.1 Test Framework

All API contract tests use the following framework:

- **Tool:** pytest + httpx + jsonschema
- **Schema Validation:** jsonschema Draft 2020-12
- **Test Data:** Factory Boy with Faker
- **Coverage Target:** 100% of endpoints, ≥90% of response fields

### 4.2 Policy API Contract Tests

```python
# tests/contract/test_policy_api.py

import pytest
from httpx import AsyncClient
from jsonschema import validate

class TestPolicyAPI:
    """Contract tests for Policy REST API endpoints."""

    # POST /v1/policies
    async def test_create_policy_success(self, client: AsyncClient):
        """TC-POL-001: Create policy with valid payload returns 201."""
        payload = {
            "name": "test-policy",
            "version": "1.0.0",
            "status": "draft",
            "category": "data_handling",
            "rules": [{
                "name": "test-rule",
                "condition": {"type": "cedar", "expression": "principal.action == \"read\""},
                "effect": "allow",
                "priority": 100
            }],
            "policy_language": "cedar",
            "scope": {"agents": [], "environments": ["all"]},
            "owner": "user-123"
        }
        response = await client.post("/v1/policies", json=payload)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "test-policy"
        assert data["version"] == "1.0.0"
        assert data["status"] == "draft"
        assert "policy_id" in data

    async def test_create_policy_invalid_version(self, client: AsyncClient):
        """TC-POL-002: Create policy with invalid semver returns 400."""
        payload = {
            "name": "test-policy",
            "version": "not-semver",
            "status": "draft",
            "category": "data_handling",
            "rules": [],
            "policy_language": "cedar",
            "scope": {},
            "owner": "user-123"
        }
        response = await client.post("/v1/policies", json=payload)
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    async def test_create_policy_missing_required(self, client: AsyncClient):
        """TC-POL-003: Create policy missing required fields returns 400."""
        payload = {"name": "test-policy"}
        response = await client.post("/v1/policies", json=payload)
        assert response.status_code == 400

    async def test_create_policy_duplicate_version(self, client: AsyncClient):
        """TC-POL-004: Create policy with duplicate name+version returns 409."""
        payload = {
            "name": "test-policy",
            "version": "1.0.0",
            "status": "draft",
            "category": "data_handling",
            "rules": [{"name": "r1", "condition": {"type": "cedar", "expression": "true"}, "effect": "allow", "priority": 1}],
            "policy_language": "cedar",
            "scope": {},
            "owner": "user-123"
        }
        await client.post("/v1/policies", json=payload)
        response = await client.post("/v1/policies", json=payload)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "CONFLICT"

    # GET /v1/policies
    async def test_list_policies_success(self, client: AsyncClient):
        """TC-POL-005: List policies returns 200 with paginated data."""
        response = await client.get("/v1/policies")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "meta" in body
        assert "pagination" in body["meta"]
        assert "links" in body

    async def test_list_policies_with_filter(self, client: AsyncClient):
        """TC-POL-006: List policies with status filter returns filtered results."""
        response = await client.get("/v1/policies?status=active")
        assert response.status_code == 200
        for policy in response.json()["data"]:
            assert policy["status"] == "active"

    async def test_list_policies_pagination(self, client: AsyncClient):
        """TC-POL-007: List policies with cursor pagination works correctly."""
        response = await client.get("/v1/policies?limit=5")
        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) <= 5
        if body["meta"]["pagination"]["has_more"]:
            next_cursor = body["meta"]["pagination"]["cursor"]
            response2 = await client.get(f"/v1/policies?limit=5&cursor={next_cursor}")
            assert response2.status_code == 200

    # GET /v1/policies/{id}
    async def test_get_policy_success(self, client: AsyncClient):
        """TC-POL-008: Get policy by ID returns 200 with full policy."""
        # First create a policy
        create_resp = await client.post("/v1/policies", json={
            "name": "get-test", "version": "1.0.0", "status": "draft",
            "category": "data_handling",
            "rules": [{"name": "r1", "condition": {"type": "cedar", "expression": "true"}, "effect": "allow", "priority": 1}],
            "policy_language": "cedar", "scope": {}, "owner": "user-123"
        })
        policy_id = create_resp.json()["data"]["policy_id"]
        response = await client.get(f"/v1/policies/{policy_id}")
        assert response.status_code == 200
        assert response.json()["data"]["policy_id"] == policy_id

    async def test_get_policy_not_found(self, client: AsyncClient):
        """TC-POL-009: Get non-existent policy returns 404."""
        response = await client.get("/v1/policies/non-existent-id")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ENTITY_NOT_FOUND"

    # PUT /v1/policies/{id}
    async def test_update_policy_success(self, client: AsyncClient):
        """TC-POL-010: Update policy creates new version."""
        create_resp = await client.post("/v1/policies", json={
            "name": "update-test", "version": "1.0.0", "status": "draft",
            "category": "data_handling",
            "rules": [{"name": "r1", "condition": {"type": "cedar", "expression": "true"}, "effect": "allow", "priority": 1}],
            "policy_language": "cedar", "scope": {}, "owner": "user-123"
        })
        policy_id = create_resp.json()["data"]["policy_id"]
        response = await client.put(f"/v1/policies/{policy_id}", json={
            "version": "1.1.0",
            "change_description": "Updated rules"
        })
        assert response.status_code == 200
        assert response.json()["data"]["version"] == "1.1.0"

    # DELETE /v1/policies/{id}
    async def test_delete_policy_success(self, client: AsyncClient):
        """TC-POL-011: Delete (archive) policy returns 200."""
        create_resp = await client.post("/v1/policies", json={
            "name": "delete-test", "version": "1.0.0", "status": "draft",
            "category": "data_handling",
            "rules": [{"name": "r1", "condition": {"type": "cedar", "expression": "true"}, "effect": "allow", "priority": 1}],
            "policy_language": "cedar", "scope": {}, "owner": "user-123"
        })
        policy_id = create_resp.json()["data"]["policy_id"]
        response = await client.delete(f"/v1/policies/{policy_id}")
        assert response.status_code == 200
        # Verify it's archived
        get_resp = await client.get(f"/v1/policies/{policy_id}")
        assert get_resp.json()["data"]["status"] == "archived"

    # POST /v1/policies/{id}/validate
    async def test_validate_policy_success(self, client: AsyncClient):
        """TC-POL-012: Validate policy returns validation result."""
        create_resp = await client.post("/v1/policies", json={
            "name": "validate-test", "version": "1.0.0", "status": "draft",
            "category": "data_handling",
            "rules": [{"name": "r1", "condition": {"type": "cedar", "expression": "true"}, "effect": "allow", "priority": 1}],
            "policy_language": "cedar", "scope": {}, "owner": "user-123"
        })
        policy_id = create_resp.json()["data"]["policy_id"]
        response = await client.post(f"/v1/policies/{policy_id}/validate")
        assert response.status_code == 200
        assert response.json()["data"]["valid"] is True

    async def test_validate_policy_with_errors(self, client: AsyncClient):
        """TC-POL-013: Validate policy with syntax errors returns 422."""
        create_resp = await client.post("/v1/policies", json={
            "name": "invalid-test", "version": "1.0.0", "status": "draft",
            "category": "data_handling",
            "rules": [{"name": "r1", "condition": {"type": "cedar", "expression": "invalid syntax {{{"}, "effect": "allow", "priority": 1}],
            "policy_language": "cedar", "scope": {}, "owner": "user-123"
        })
        policy_id = create_resp.json()["data"]["policy_id"]
        response = await client.post(f"/v1/policies/{policy_id}/validate")
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "POLICY_COMPILATION_ERROR"

    # POST /v1/policies/{id}/activate
    async def test_activate_policy_success(self, client: AsyncClient):
        """TC-POL-014: Activate policy changes status to active."""
        create_resp = await client.post("/v1/policies", json={
            "name": "activate-test", "version": "1.0.0", "status": "draft",
            "category": "data_handling",
            "rules": [{"name": "r1", "condition": {"type": "cedar", "expression": "true"}, "effect": "allow", "priority": 1}],
            "policy_language": "cedar", "scope": {}, "owner": "user-123"
        })
        policy_id = create_resp.json()["data"]["policy_id"]
        response = await client.post(f"/v1/policies/{policy_id}/activate")
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "active"

    # POST /v1/policies/{id}/dry-run
    async def test_dry_run_policy(self, client: AsyncClient):
        """TC-POL-015: Dry-run policy returns simulation result."""
        create_resp = await client.post("/v1/policies", json={
            "name": "dryrun-test", "version": "1.0.0", "status": "active",
            "category": "data_handling",
            "rules": [{"name": "r1", "condition": {"type": "cedar", "expression": "principal.action == \"read\""}, "effect": "allow", "priority": 1}],
            "policy_language": "cedar", "scope": {}, "owner": "user-123"
        })
        policy_id = create_resp.json()["data"]["policy_id"]
        response = await client.post(f"/v1/policies/{policy_id}/dry-run", json={
            "actions": [{"action": "read", "resource": "test-resource"}]
        })
        assert response.status_code == 200
        assert "results" in response.json()["data"]
```

### 4.3 Evidence API Contract Tests

```python
# tests/contract/test_evidence_api.py

class TestEvidenceAPI:
    """Contract tests for Evidence REST API endpoints."""

    # POST /v1/evidence
    async def test_submit_evidence_success(self, client: AsyncClient):
        """TC-EVD-001: Submit evidence with valid payload returns 201."""
        payload = {
            "type": "policy_evaluation",
            "title": "Test evidence",
            "content": {
                "format": "application/json",
                "data": {"key": "value"},
                "hash": {"algorithm": "SHA-256", "value": "a" * 64}
            },
            "source": {"system": "test", "collected_at": "2026-10-01T00:00:00Z"},
            "verification_level": "L1"
        }
        response = await client.post("/v1/evidence", json=payload)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["type"] == "policy_evaluation"
        assert "evidence_id" in data

    async def test_submit_evidence_invalid_hash(self, client: AsyncClient):
        """TC-EVD-002: Submit evidence with invalid hash format returns 400."""
        payload = {
            "type": "log",
            "title": "Test",
            "content": {
                "format": "text/plain",
                "data": "test",
                "hash": {"algorithm": "SHA-256", "value": "invalid"}
            },
            "source": {"system": "test", "collected_at": "2026-10-01T00:00:00Z"},
            "verification_level": "L0"
        }
        response = await client.post("/v1/evidence", json=payload)
        assert response.status_code == 400

    # GET /v1/evidence
    async def test_list_evidence_success(self, client: AsyncClient):
        """TC-EVD-003: List evidence returns 200 with paginated data."""
        response = await client.get("/v1/evidence")
        assert response.status_code == 200
        assert "data" in response.json()
        assert "meta" in response.json()

    async def test_list_evidence_with_type_filter(self, client: AsyncClient):
        """TC-EVD-004: List evidence filtered by type."""
        response = await client.get("/v1/evidence?type=policy_evaluation")
        assert response.status_code == 200
        for ev in response.json()["data"]:
            assert ev["type"] == "policy_evaluation"

    # GET /v1/evidence/{id}
    async def test_get_evidence_success(self, client: AsyncClient):
        """TC-EVD-005: Get evidence by ID returns 200."""
        # Create first
        create_resp = await client.post("/v1/evidence", json={
            "type": "log", "title": "Test",
            "content": {"format": "text/plain", "data": "test", "hash": {"algorithm": "SHA-256", "value": "a" * 64}},
            "source": {"system": "test", "collected_at": "2026-10-01T00:00:00Z"},
            "verification_level": "L0"
        })
        ev_id = create_resp.json()["data"]["evidence_id"]
        response = await client.get(f"/v1/evidence/{ev_id}")
        assert response.status_code == 200
        assert response.json()["data"]["evidence_id"] == ev_id

    # POST /v1/evidence/{id}/verify
    async def test_verify_evidence_success(self, client: AsyncClient):
        """TC-EVD-006: Verify evidence returns verification result."""
        create_resp = await client.post("/v1/evidence", json={
            "type": "log", "title": "Test",
            "content": {"format": "text/plain", "data": "test", "hash": {"algorithm": "SHA-256", "value": "a" * 64}},
            "source": {"system": "test", "collected_at": "2026-10-01T00:00:00Z"},
            "verification_level": "L1"
        })
        ev_id = create_resp.json()["data"]["evidence_id"]
        response = await client.post(f"/v1/evidence/{ev_id}/verify")
        assert response.status_code == 200
        result = response.json()["data"]
        assert "schema_valid" in result
        assert "hash_verified" in result

    # GET /v1/evidence/{id}/chain-of-custody
    async def test_get_chain_of_custody(self, client: AsyncClient):
        """TC-EVD-007: Get chain of custody returns custody events."""
        create_resp = await client.post("/v1/evidence", json={
            "type": "log", "title": "Test",
            "content": {"format": "text/plain", "data": "test", "hash": {"algorithm": "SHA-256", "value": "a" * 64}},
            "source": {"system": "test", "collected_at": "2026-10-01T00:00:00Z"},
            "verification_level": "L1"
        })
        ev_id = create_resp.json()["data"]["evidence_id"]
        response = await client.get(f"/v1/evidence/{ev_id}/chain-of-custody")
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    # POST /v1/evidence/bulk
    async def test_bulk_submit_evidence(self, client: AsyncClient):
        """TC-EVD-008: Bulk submit evidence returns 201 with results."""
        payload = [
            {
                "type": "log", "title": f"Bulk test {i}",
                "content": {"format": "text/plain", "data": f"test-{i}", "hash": {"algorithm": "SHA-256", "value": "a" * 64}},
                "source": {"system": "test", "collected_at": "2026-10-01T00:00:00Z"},
                "verification_level": "L0"
            }
            for i in range(10)
        ]
        response = await client.post("/v1/evidence/bulk", json=payload)
        assert response.status_code == 201
        assert len(response.json()["data"]["results"]) == 10

    # GET /v1/evidence/search
    async def test_search_evidence(self, client: AsyncClient):
        """TC-EVD-009: Full-text search evidence returns results."""
        response = await client.get("/v1/evidence/search?query=test")
        assert response.status_code == 200
        assert "data" in response.json()
```

### 4.4 Enforcement API Contract Tests

```python
# tests/contract/test_enforcement_api.py

class TestEnforcementAPI:
    """Contract tests for Enforcement REST API endpoints."""

    # POST /v1/enforcements
    async def test_evaluate_action_allow(self, client: AsyncClient):
        """TC-ENF-001: Evaluate action that matches allow rule returns ALLOW."""
        # Create and activate policy first
        await client.post("/v1/policies", json={
            "name": "test-allow", "version": "1.0.0", "status": "active",
            "category": "data_handling",
            "rules": [{"name": "allow-read", "condition": {"type": "cedar", "expression": "principal.action == \"read\""}, "effect": "allow", "priority": 100}],
            "policy_language": "cedar", "scope": {"environments": ["all"]}, "owner": "user-123"
        })
        response = await client.post("/v1/enforcements", json={
            "agent_id": "agent-123",
            "action": {"type": "tool_call", "tool_name": "read", "resource": "test-resource", "parameters": {}},
            "policy_id": "test-policy-id"
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["decision"] in ["ALLOW", "DENY", "REQUIRE_APPROVAL", "ALLOW_WITH_REDACTION", "QUARANTINE"]
        assert "enforcement_id" in data
        assert "confidence_score" in data
        assert data["deterministic"] is True

    async def test_evaluate_action_deny(self, client: AsyncClient):
        """TC-ENF-002: Evaluate action that matches deny rule returns DENY."""
        response = await client.post("/v1/enforcements", json={
            "agent_id": "agent-123",
            "action": {"type": "tool_call", "tool_name": "export", "resource": "pii-data", "parameters": {}},
            "policy_id": "test-policy-id"
        })
        assert response.status_code == 200
        assert response.json()["data"]["decision"] == "DENY"

    async def test_evaluate_action_invalid_agent(self, client: AsyncClient):
        """TC-ENF-003: Evaluate action with non-existent agent returns 400."""
        response = await client.post("/v1/enforcements", json={
            "agent_id": "non-existent-agent",
            "action": {"type": "tool_call", "resource": "test", "parameters": {}},
            "policy_id": "test-policy-id"
        })
        assert response.status_code == 400

    # GET /v1/enforcements
    async def test_list_enforcements(self, client: AsyncClient):
        """TC-ENF-004: List enforcement decisions returns 200."""
        response = await client.get("/v1/enforcements")
        assert response.status_code == 200
        assert "data" in response.json()

    # GET /v1/enforcements/{id}
    async def test_get_enforcement(self, client: AsyncClient):
        """TC-ENF-005: Get enforcement by ID returns 200."""
        create_resp = await client.post("/v1/enforcements", json={
            "agent_id": "agent-123",
            "action": {"type": "tool_call", "resource": "test", "parameters": {}},
            "policy_id": "test-policy-id"
        })
        enf_id = create_resp.json()["data"]["enforcement_id"]
        response = await client.get(f"/v1/enforcements/{enf_id}")
        assert response.status_code == 200
        assert response.json()["data"]["enforcement_id"] == enf_id

    # POST /v1/enforcements/batch
    async def test_batch_evaluate(self, client: AsyncClient):
        """TC-ENF-006: Batch evaluate actions returns results for each."""
        payload = [
            {"agent_id": "agent-123", "action": {"type": "tool_call", "resource": f"res-{i}", "parameters": {}}, "policy_id": "test-policy-id"}
            for i in range(5)
        ]
        response = await client.post("/v1/enforcements/batch", json=payload)
        assert response.status_code == 200
        assert len(response.json()["data"]) == 5

    # GET /v1/enforcements/stats
    async def test_enforcement_stats(self, client: AsyncClient):
        """TC-ENF-007: Get enforcement statistics returns 200."""
        response = await client.get("/v1/enforcements/stats")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_decisions" in data
        assert "by_decision" in data

    # GET /v1/enforcements/violations
    async def test_list_violations(self, client: AsyncClient):
        """TC-ENF-008: List policy violations returns 200."""
        response = await client.get("/v1/enforcements/violations")
        assert response.status_code == 200
        assert "data" in response.json()
```

### 4.5 Assessment API Contract Tests

```python
# tests/contract/test_assessment_api.py

class TestAssessmentAPI:
    """Contract tests for Assessment REST API endpoints."""

    # POST /v1/assessments
    async def test_create_assessment(self, client: AsyncClient):
        """TC-ASM-001: Create assessment returns 201."""
        payload = {
            "type": "control_assessment",
            "subject": {"subject_type": "agent", "subject_id": "agent-123", "subject_name": "Test Agent"},
            "framework": "ISO-42001",
            "control_ids": ["6.1", "8.1"]
        }
        response = await client.post("/v1/assessments", json=payload)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["type"] == "control_assessment"
        assert data["status"] == "not_started"

    # GET /v1/assessments
    async def test_list_assessments(self, client: AsyncClient):
        """TC-ASM-002: List assessments returns 200."""
        response = await client.get("/v1/assessments")
        assert response.status_code == 200
        assert "data" in response.json()

    # GET /v1/assessments/{id}
    async def test_get_assessment(self, client: AsyncClient):
        """TC-ASM-003: Get assessment by ID returns 200."""
        create_resp = await client.post("/v1/assessments", json={
            "type": "control_assessment",
            "subject": {"subject_type": "agent", "subject_id": "agent-123", "subject_name": "Test"},
            "framework": "ISO-42001"
        })
        asm_id = create_resp.json()["data"]["assessment_id"]
        response = await client.get(f"/v1/assessments/{asm_id}")
        assert response.status_code == 200

    # POST /v1/assessments/{id}/start
    async def test_start_assessment(self, client: AsyncClient):
        """TC-ASM-004: Start assessment changes status to in_progress."""
        create_resp = await client.post("/v1/assessments", json={
            "type": "control_assessment",
            "subject": {"subject_type": "agent", "subject_id": "agent-123", "subject_name": "Test"},
            "framework": "ISO-42001"
        })
        asm_id = create_resp.json()["data"]["assessment_id"]
        response = await client.post(f"/v1/assessments/{asm_id}/start")
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "in_progress"

    # POST /v1/assessments/{id}/complete
    async def test_complete_assessment(self, client: AsyncClient):
        """TC-ASM-005: Complete assessment with results returns 200."""
        # Create and start
        create_resp = await client.post("/v1/assessments", json={
            "type": "control_assessment",
            "subject": {"subject_type": "agent", "subject_id": "agent-123", "subject_name": "Test"},
            "framework": "ISO-42001",
            "control_ids": ["6.1"]
        })
        asm_id = create_resp.json()["data"]["assessment_id"]
        await client.post(f"/v1/assessments/{asm_id}/start")
        response = await client.post(f"/v1/assessments/{asm_id}/complete", json={
            "control_results": [{"control_id": "6.1", "result": "pass", "score": 0.95, "tested_at": "2026-10-01T00:00:00Z"}],
            "overall_score": 0.95,
            "overall_result": "compliant"
        })
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "completed"

    # POST /v1/assessments/{id}/compare
    async def test_compare_assessments(self, client: AsyncClient):
        """TC-ASM-006: Compare two assessments returns diff."""
        # Create two assessments
        resp1 = await client.post("/v1/assessments", json={
            "type": "control_assessment",
            "subject": {"subject_type": "agent", "subject_id": "agent-123", "subject_name": "Test"},
            "framework": "ISO-42001"
        })
        resp2 = await client.post("/v1/assessments", json={
            "type": "control_assessment",
            "subject": {"subject_type": "agent", "subject_id": "agent-123", "subject_name": "Test"},
            "framework": "ISO-42001"
        })
        id1 = resp1.json()["data"]["assessment_id"]
        id2 = resp2.json()["data"]["assessment_id"]
        response = await client.post(f"/v1/assessments/{id1}/compare", json={"other_assessment_id": id2})
        assert response.status_code == 200
```

### 4.6 Compliance API Contract Tests

```python
# tests/contract/test_compliance_api.py

class TestComplianceAPI:
    """Contract tests for Compliance REST API endpoints."""

    # GET /v1/compliance
    async def test_list_compliance_postures(self, client: AsyncClient):
        """TC-CMP-001: List compliance postures returns 200."""
        response = await client.get("/v1/compliance")
        assert response.status_code == 200
        assert "data" in response.json()

    # GET /v1/compliance/{framework}
    async def test_get_compliance_by_framework(self, client: AsyncClient):
        """TC-CMP-002: Get compliance for specific framework returns 200."""
        response = await client.get("/v1/compliance/ISO-42001")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["framework"]["framework_id"] == "ISO-42001"

    # GET /v1/compliance/{framework}/score
    async def test_get_compliance_score(self, client: AsyncClient):
        """TC-CMP-003: Get compliance score returns 200."""
        response = await client.get("/v1/compliance/ISO-42001/score")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "score" in data
        assert 0 <= data["score"] <= 1

    # GET /v1/compliance/{framework}/gaps
    async def test_get_gap_analysis(self, client: AsyncClient):
        """TC-CMP-004: Get gap analysis returns 200."""
        response = await client.get("/v1/compliance/ISO-42001/gaps")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_controls" in data
        assert "coverage_percentage" in data

    # POST /v1/compliance/{framework}/compute
    async def test_trigger_compliance_computation(self, client: AsyncClient):
        """TC-CMP-005: Trigger compliance computation returns 200."""
        response = await client.post("/v1/compliance/ISO-42001/compute")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] in ["compliant", "partially_compliant", "non_compliant", "unknown"]

    # GET /v1/compliance/{framework}/trend
    async def test_get_compliance_trend(self, client: AsyncClient):
        """TC-CMP-006: Get compliance trend returns 200."""
        response = await client.get("/v1/compliance/ISO-42001/trend")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "trend" in data
        assert data["trend"] in ["improving", "stable", "declining", "unknown"]

    # GET /v1/compliance/{framework}/report
    async def test_generate_compliance_report(self, client: AsyncClient):
        """TC-CMP-007: Generate compliance report returns 200."""
        response = await client.get("/v1/compliance/ISO-42001/report")
        assert response.status_code == 200
```

### 4.7 Agent API Contract Tests

```python
# tests/contract/test_agent_api.py

class TestAgentAPI:
    """Contract tests for Agent REST API endpoints."""

    # POST /v1/agents
    async def test_register_agent(self, client: AsyncClient):
        """TC-AGT-001: Register agent returns 201."""
        payload = {
            "name": "test-agent",
            "type": "autonomous",
            "identity": {"unique_id": "did:grcclaw:org-123:agent-456"},
            "owner": "user-123"
        }
        response = await client.post("/v1/agents", json=payload)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "test-agent"
        assert data["status"] == "proposed"

    # GET /v1/agents
    async def test_list_agents(self, client: AsyncClient):
        """TC-AGT-002: List agents returns 200."""
        response = await client.get("/v1/agents")
        assert response.status_code == 200
        assert "data" in response.json()

    # GET /v1/agents/{id}
    async def test_get_agent(self, client: AsyncClient):
        """TC-AGT-003: Get agent by ID returns 200."""
        create_resp = await client.post("/v1/agents", json={
            "name": "get-test", "type": "autonomous",
            "identity": {"unique_id": "did:grcclaw:test"},
            "owner": "user-123"
        })
        agent_id = create_resp.json()["data"]["agent_id"]
        response = await client.get(f"/v1/agents/{agent_id}")
        assert response.status_code == 200

    # POST /v1/agents/{id}/attest
    async def test_attest_agent(self, client: AsyncClient):
        """TC-AGT-004: Attest agent identity returns 200."""
        create_resp = await client.post("/v1/agents", json={
            "name": "attest-test", "type": "autonomous",
            "identity": {"unique_id": "did:grcclaw:test"},
            "owner": "user-123"
        })
        agent_id = create_resp.json()["data"]["agent_id"]
        response = await client.post(f"/v1/agents/{agent_id}/attest", json={
            "attestation": "test-attestation-data"
        })
        assert response.status_code == 200

    # GET /v1/agents/{id}/trust-score
    async def test_get_trust_score(self, client: AsyncClient):
        """TC-AGT-005: Get agent trust score returns 200."""
        create_resp = await client.post("/v1/agents", json={
            "name": "trust-test", "type": "autonomous",
            "identity": {"unique_id": "did:grcclaw:test"},
            "owner": "user-123"
        })
        agent_id = create_resp.json()["data"]["agent_id"]
        response = await client.get(f"/v1/agents/{agent_id}/trust-score")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "trust_score" in data
        assert 0 <= data["trust_score"] <= 1

    # DELETE /v1/agents/{id}
    async def test_terminate_agent(self, client: AsyncClient):
        """TC-AGT-006: Terminate agent returns 200."""
        create_resp = await client.post("/v1/agents", json={
            "name": "terminate-test", "type": "autonomous",
            "identity": {"unique_id": "did:grcclaw:test"},
            "owner": "user-123"
        })
        agent_id = create_resp.json()["data"]["agent_id"]
        response = await client.delete(f"/v1/agents/{agent_id}")
        assert response.status_code == 200
```

### 4.8 Audit Trail API Contract Tests

```python
# tests/contract/test_audit_api.py

class TestAuditTrailAPI:
    """Contract tests for Audit Trail REST API endpoints."""

    # GET /v1/audit-trail
    async def test_query_audit_trail(self, client: AsyncClient):
        """TC-AUD-001: Query audit trail returns 200."""
        response = await client.get("/v1/audit-trail")
        assert response.status_code == 200
        assert "data" in response.json()

    # GET /v1/audit-trail/verify
    async def test_verify_audit_trail(self, client: AsyncClient):
        """TC-AUD-002: Verify audit trail integrity returns 200."""
        response = await client.post("/v1/audit-trail/verify", json={
            "start_time": "2026-10-01T00:00:00Z",
            "end_time": "2026-10-01T23:59:59Z"
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert "valid" in data
        assert "entries_checked" in data

    # GET /v1/audit-trail/merkle-root
    async def test_get_merkle_root(self, client: AsyncClient):
        """TC-AUD-003: Get current Merkle root returns 200."""
        response = await client.get("/v1/audit-trail/merkle-root")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "merkle_root" in data
        assert "timestamp" in data

    # POST /v1/audit-trail/export
    async def test_export_audit_trail(self, client: AsyncClient):
        """TC-AUD-004: Export audit trail returns 200."""
        response = await client.post("/v1/audit-trail/export", json={
            "start_time": "2026-10-01T00:00:00Z",
            "end_time": "2026-10-01T23:59:59Z",
            "format": "json"
        })
        assert response.status_code == 200
```

### 4.9 Error Handling Contract Tests

```python
# tests/contract/test_error_handling.py

class TestErrorHandling:
    """Contract tests for standard error responses."""

    async def test_unauthenticated_request(self, client: AsyncClient):
        """TC-ERR-001: Request without auth returns 401."""
        response = await client.get("/v1/policies", headers={"Authorization": ""})
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHENTICATED"

    async def test_forbidden_request(self, client: AsyncClient):
        """TC-ERR-002: Request with insufficient permissions returns 403."""
        # Use a token with limited permissions
        response = await client.get("/v1/policies", headers={"Authorization": "Bearer limited-token"})
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"

    async def test_rate_limited(self, client: AsyncClient):
        """TC-ERR-003: Rate limited request returns 429."""
        # Make many rapid requests
        for _ in range(100):
            await client.get("/v1/policies")
        response = await client.get("/v1/policies")
        # May or may not be rate limited depending on config
        if response.status_code == 429:
            assert response.json()["error"]["code"] == "RATE_LIMITED"

    async def test_not_found(self, client: AsyncClient):
        """TC-ERR-004: Non-existent endpoint returns 404."""
        response = await client.get("/v1/non-existent")
        assert response.status_code == 404

    async def test_internal_error_format(self, client: AsyncClient):
        """TC-ERR-005: Internal error returns standard format."""
        # This would need a mock to trigger internal error
        pass

    async def test_validation_error_format(self, client: AsyncClient):
        """TC-ERR-006: Validation error includes details."""
        response = await client.post("/v1/policies", json={"invalid": "data"})
        assert response.status_code == 400
        error = response.json()["error"]
        assert "code" in error
        assert "message" in error
        assert "details" in error
        assert "request_id" in error
        assert "timestamp" in error
```

### 4.10 Contract Test Summary

| Category | Test Count | Coverage |
|----------|-----------|----------|
| Policy API | 15 | CRUD, validate, activate, dry-run, error cases |
| Evidence API | 9 | Submit, list, get, verify, custody, bulk, search |
| Enforcement API | 8 | Evaluate, batch, stats, violations, error cases |
| Assessment API | 6 | Create, list, get, start, complete, compare |
| Compliance API | 7 | List, get, score, gaps, compute, trend, report |
| Agent API | 6 | Register, list, get, attest, trust-score, terminate |
| Audit Trail API | 4 | Query, verify, merkle-root, export |
| Error Handling | 6 | Auth, forbidden, rate limit, not found, formats |
| **Total** | **61** | **All REST endpoints** |

---

## 5. Data Migration Strategy

### 5.1 Migration Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Data Migration Strategy                               │
│                                                                         │
│  Phase 1: Assessment        Phase 2: Schema      Phase 3: Data         │
│  ┌──────────────┐          ┌──────────────┐     ┌──────────────┐      │
│  │ Inventory    │─────────▶│ Create new   │────▶│ Extract &    │      │
│  │ Analyze      │          │ schema       │     │ transform   │      │
│  │ Map          │          │ Set up       │     │ Validate    │      │
│  └──────────────┘          │ constraints  │     └──────┬───────┘      │
│                            └──────────────┘            │               │
│                                                        ▼               │
│  Phase 5: Cutover         Phase 4: Load         ┌──────────────┐      │
│  ┌──────────────┐          ┌──────────────┐     │ Load &       │      │
│  │ DNS switch   │◀─────────│ Verify &     │◀────│ Verify       │      │
│  │ Decommission │          │ reconcile    │     └──────────────┘      │
│  └──────────────┘          └──────────────┘                            │
│                                                                         │
│  Rollback: At any phase, restore from backup and re-run                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Phase 1: Assessment & Inventory (Week 1)

#### 5.2.1 Source System Inventory

| Source System | Data Type | Volume | Format | Location |
|--------------|-----------|--------|--------|----------|
| Legacy GRC DB | Policies, controls | ~500 records | PostgreSQL | on-prem |
| SIEM (Splunk) | Audit events | ~50M events | HEC | cloud |
| Spreadsheet | Compliance mappings | ~200 rows | Excel | file share |
| ServiceNow | Findings, risks | ~2000 records | REST API | cloud |
| Manual docs | Evidence | ~500 files | PDF/Word | SharePoint |

#### 5.2.2 Data Quality Assessment

```sql
-- Data quality checks
SELECT 
    'policies' as source,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE name IS NULL) as missing_name,
    COUNT(*) FILTER (WHERE version IS NULL) as missing_version,
    COUNT(*) FILTER (WHERE created_at IS NULL) as missing_created_at,
    COUNT(DISTINCT name) as unique_names
FROM legacy_policies;

-- Duplicate detection
SELECT name, version, COUNT(*) as cnt
FROM legacy_policies
GROUP BY name, version
HAVING COUNT(*) > 1;

-- Orphan detection
SELECT p.name
FROM legacy_policies p
LEFT JOIN legacy_controls c ON p.control_id = c.id
WHERE c.id IS NULL;
```

### 5.3 Phase 2: Schema Creation (Week 2)

#### 5.3.1 Target Schema DDL

```sql
-- Migration schema creation
CREATE SCHEMA IF NOT EXISTS grcclaw_migration;

-- Migration tracking table
CREATE TABLE grcclaw_migration.runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'running',
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_log TEXT
);

-- Migration mapping table
CREATE TABLE grcclaw_migration.entity_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system VARCHAR(100) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    target_entity_type VARCHAR(100) NOT NULL,
    target_entity_id UUID,
    migration_status VARCHAR(20) DEFAULT 'pending',
    migrated_at TIMESTAMPTZ,
    validation_status VARCHAR(20),
    error_message TEXT,
    UNIQUE(source_system, source_id, target_entity_type)
);

-- Create target tables (from Section 5.2 of base spec)
-- [DDL from base spec Section 5.2 goes here]

-- Add migration-specific columns
ALTER TABLE policies ADD COLUMN IF NOT EXISTS migration_source VARCHAR(100);
ALTER TABLE policies ADD COLUMN IF NOT EXISTS migration_source_id VARCHAR(255);
ALTER TABLE evidence ADD COLUMN IF NOT EXISTS migration_source VARCHAR(100);
ALTER TABLE evidence ADD COLUMN IF NOT EXISTS migration_source_id VARCHAR(255);
```

#### 5.3.2 Compatibility Mapping

| Legacy Concept | GRC_Claw Concept | Mapping Rule |
|---------------|-----------------|--------------|
| `policy_rule` | `PolicyRule` | Direct 1:1 |
| `control` | `Control` | Direct 1:1 |
| `control.framework` | `Framework` | Split JSON to normalized |
| `finding` | `Finding` | Direct 1:1 |
| `risk_register` | `Risk` | Direct 1:1 |
| `audit_log` | `AuditTrail` | Transform: add hash chain |
| `evidence_doc` | `Evidence` | Transform: add cryptographic proof |
| `compliance_matrix` | `Compliance` | Recompute from evidence |
| `agent_registry` | `Agent` | Direct 1:1 + add identity |
| `exception_request` | `Exception` | Direct 1:1 |
| `vendor_assessment` | `Assessment` | Transform: add scoring |

### 5.4 Phase 3: Data Extraction & Transformation (Week 3-4)

#### 5.4.1 ETL Pipeline

```python
# migration/etl_pipeline.py

class MigrationETL:
    """ETL pipeline for GRC_Claw data migration."""

    def __init__(self, source_config, target_config):
        self.source = SourceConnector(source_config)
        self.target = TargetConnector(target_config)
        self.transformer = DataTransformer()
        self.validator = DataValidator()

    async def extract_policies(self) -> list[dict]:
        """Extract policies from legacy system."""
        query = """
            SELECT p.*, array_agg(r.*) as rules
            FROM legacy_policies p
            LEFT JOIN legacy_policy_rules r ON p.id = r.policy_id
            GROUP BY p.id
        """
        return await self.source.execute(query)

    async def transform_policy(self, legacy_policy: dict) -> dict:
        """Transform legacy policy to GRC_Claw format."""
        return {
            "policy_id": str(uuid.uuid4()),
            "name": legacy_policy["name"],
            "version": self._normalize_version(legacy_policy["version"]),
            "status": self._map_status(legacy_policy["status"]),
            "category": self._map_category(legacy_policy["category"]),
            "rules": [self.transformer.transform_rule(r) for r in legacy_policy["rules"]],
            "policy_language": "cedar",
            "scope": self._extract_scope(legacy_policy),
            "owner": await self._resolve_owner(legacy_policy["owner_id"]),
            "created_at": legacy_policy["created_at"],
            "updated_at": legacy_policy["updated_at"],
            "migration_source": "legacy_grc",
            "migration_source_id": str(legacy_policy["id"])
        }

    async def transform_audit_event(self, legacy_event: dict) -> dict:
        """Transform legacy audit event with hash chain."""
        prev_hash = await self.target.get_last_audit_hash()
        event_data = json.dumps(legacy_event, sort_keys=True, default=str)
        integrity_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        return {
            "audit_id": str(uuid.uuid4()),
            "event_type": self._map_event_type(legacy_event["event_type"]),
            "actor": {
                "type": "system",
                "id": legacy_event["system_id"],
                "auth_method": "api_key"
            },
            "action": legacy_event["action"],
            "resource": {
                "type": legacy_event["resource_type"],
                "id": legacy_event["resource_id"],
                "name": legacy_event.get("resource_name", "")
            },
            "context": legacy_event.get("context", {}),
            "timestamp": legacy_event["timestamp"],
            "integrity_hash": integrity_hash,
            "previous_hash": prev_hash,
            "signature": await self._sign_event(integrity_hash),
            "migration_source": "siem_splunk",
            "migration_source_id": legacy_event["event_id"]
        }

    async def load_batch(self, entity_type: str, records: list[dict]) -> dict:
        """Load a batch of records into target."""
        results = {"success": 0, "failed": 0, "errors": []}
        
        for record in records:
            try:
                # Validate against JSON Schema
                self.validator.validate(entity_type, record)
                
                # Insert into target
                await self.target.insert(entity_type, record)
                
                # Update mapping
                await self.target.update_mapping(
                    record["migration_source"],
                    record["migration_source_id"],
                    entity_type,
                    record.get(f"{entity_type}_id") or record.get("policy_id") or record.get("audit_id"),
                    "migrated"
                )
                results["success"] += 1
                
            except ValidationError as e:
                results["failed"] += 1
                results["errors"].append({
                    "record": record.get("name", "unknown"),
                    "error": str(e)
                })
        
        return results
```

#### 5.4.2 Migration Scripts

```bash
#!/bin/bash
# migration/run_migration.sh

set -euo pipefail

PHASE=${1:-"all"}
LOG_FILE="migration/logs/migration_$(date +%Y%m%d_%H%M%S).log"

echo "Starting GRC_Claw migration - Phase: $PHASE" | tee -a "$LOG_FILE"

case $PHASE in
    "policies")
        echo "Migrating policies..." | tee -a "$LOG_FILE"
        python -m migration.cli migrate-policies \
            --source legacy_grc \
            --batch-size 100 \
            --validate \
            --log-file "$LOG_FILE"
        ;;
    "evidence")
        echo "Migrating evidence..." | tee -a "$LOG_FILE"
        python -m migration.cli migrate-evidence \
            --source sharepoint \
            --batch-size 50 \
            --validate \
            --log-file "$LOG_FILE"
        ;;
    "audit")
        echo "Migrating audit trail..." | tee -a "$LOG_FILE"
        python -m migration.cli migrate-audit \
            --source splunk \
            --batch-size 10000 \
            --validate \
            --log-file "$LOG_FILE"
        ;;
    "agents")
        echo "Migrating agents..." | tee -a "$LOG_FILE"
        python -m migration.cli migrate-agents \
            --source agent_registry \
            --batch-size 100 \
            --validate \
            --log-file "$LOG_FILE"
        ;;
    "all")
        $0 policies
        $0 agents
        $0 evidence
        $0 audit
        ;;
    *)
        echo "Unknown phase: $PHASE"
        exit 1
        ;;
esac

echo "Migration phase $PHASE completed" | tee -a "$LOG_FILE"
```

### 5.5 Phase 4: Data Loading & Verification (Week 5)

#### 5.5.1 Loading Order

```
1. Frameworks (no dependencies)
2. Controls (depends on Frameworks)
3. Policies (depends on Controls)
4. Agents (no dependencies)
5. Policy Rules (depends on Policies)
6. Evidence (depends on Policies, Agents)
7. Enforcement (depends on Policies, Agents, Evidence)
8. Assessments (depends on Controls, Agents)
9. Findings (depends on Assessments, Controls)
10. Risks (depends on Controls, Agents)
11. Compliance (depends on Evidence, Assessments, Controls)
12. Audit Trail (depends on all entities)
13. Exceptions (depends on Policies, Controls)
14. Vendors (no dependencies)
15. Decisions (depends on all entities)
```

#### 5.5.2 Verification Queries

```sql
-- Record count verification
SELECT 'policies' as entity, COUNT(*) as count FROM policies
UNION ALL
SELECT 'evidence', COUNT(*) FROM evidence
UNION ALL
SELECT 'agents', COUNT(*) FROM agents
UNION ALL
SELECT 'audit_trail', COUNT(*) FROM audit_entries
UNION ALL
SELECT 'assessments', COUNT(*) FROM assessments
UNION ALL
SELECT 'compliance', COUNT(*) FROM compliance_postures;

-- Referential integrity checks
SELECT 'orphaned evidence' as check_name, COUNT(*) as issues
FROM evidence e LEFT JOIN policies p ON e.policy_id = p.policy_id
WHERE e.policy_id IS NOT NULL AND p.policy_id IS NULL
UNION ALL
SELECT 'orphaned enforcement', COUNT(*)
FROM enforcements e LEFT JOIN agents a ON e.agent_id = a.agent_id
WHERE a.agent_id IS NULL
UNION ALL
SELECT 'orphaned assessment', COUNT(*)
FROM assessments a LEFT JOIN agents ag ON a.subject->>'subject_id' = ag.agent_id::text
WHERE a.subject->>'subject_type' = 'agent' AND ag.agent_id IS NULL;

-- Hash chain verification
WITH chain_check AS (
    SELECT 
        audit_id,
        integrity_hash,
        previous_hash,
        LAG(integrity_hash) OVER (ORDER BY sequence_number) as expected_prev_hash
    FROM audit_entries
    ORDER BY sequence_number
)
SELECT COUNT(*) as broken_links
FROM chain_check
WHERE previous_hash != expected_prev_hash
AND previous_hash != '0' * 64;  -- First entry has no previous

-- Score range validation
SELECT 'invalid scores' as check_name, COUNT(*) as issues
FROM assessments
WHERE overall_score < 0 OR overall_score > 1;

-- Date range validation
SELECT 'invalid dates' as check_name, COUNT(*) as issues
FROM policies
WHERE effective_date IS NOT NULL 
AND expiration_date IS NOT NULL 
AND effective_date >= expiration_date;
```

### 5.6 Phase 5: Cutover & Decommission (Week 6)

#### 5.6.1 Cutover Checklist

- [ ] All migration phases completed successfully
- [ ] Verification queries pass (0 issues)
- [ ] Performance benchmarks meet targets
- [ ] Rollback plan tested
- [ ] DNS records updated
- [ ] Load balancer reconfigured
- [ ] Monitoring alerts configured
- [ ] Team trained on new system
- [ ] Documentation updated
- [ ] Legacy system in read-only mode

#### 5.6.2 Rollback Procedure

```bash
#!/bin/bash
# migration/rollback.sh

echo "Initiating rollback..."

# 1. Stop writes to new system
kubectl scale deployment grc-claw --replicas=0

# 2. Restore DNS to legacy system
aws route53 change-resource-record-sets \
    --hosted-zone-id Z1234567890 \
    --change-batch file://dns-rollback.json

# 3. Verify legacy system is accessible
curl -f https://legacy-grc.internal/health || {
    echo "ERROR: Legacy system not accessible!"
    exit 1
}

# 4. Notify stakeholders
curl -X POST $SLACK_WEBHOOK_URL \
    -d '{"text": "GRC_Claw migration rolled back. Legacy system restored."}'

echo "Rollback completed."
```

### 5.7 Migration Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss during migration | Low | Critical | Full backup before each phase; verify counts |
| Schema incompatibility | Medium | High | Compatibility mapping; transformation layer |
| Performance degradation | Medium | High | Load testing; performance benchmarks |
| Extended downtime | Low | Critical | Blue-green deployment; instant rollback |
| Data corruption | Low | Critical | Validation at each phase; hash verification |
| Missing dependencies | Medium | Medium | Dependency graph; ordered loading |
| Team unfamiliarity | Medium | Medium | Training; documentation; runbooks |

---

## 6. Performance Benchmarks

### 6.1 Benchmark Environment

| Component | Specification |
|----------|--------------|
| **API Server** | 3x replicas, 4 vCPU, 8GB RAM each |
| **PostgreSQL** | 3-node HA, 8 vCPU, 32GB RAM, SSD |
| **Redis** | 3-node Sentinel, 2 vCPU, 4GB RAM |
| **Kafka** | 3 brokers, 4 vCPU, 8GB RAM |
| **Network** | 10Gbps internal, 1Gbps external |
| **Load Generator** | 5x instances, 8 vCPU, 16GB RAM each |
| **Monitoring** | Prometheus + Grafana |

### 6.2 Benchmark Suites

#### 6.2.1 Policy Evaluation Benchmark

| Metric | Target | Stretch | Measurement |
|--------|--------|---------|-------------|
| p50 latency | < 5ms | < 2ms | Histogram |
| p99 latency | < 50ms | < 20ms | Histogram |
| p99.9 latency | < 100ms | < 50ms | Histogram |
| Throughput | 50K req/s | 100K req/s | Counter |
| Error rate | < 0.01% | < 0.001% | Ratio |
| CPU utilization | < 60% | < 40% | Gauge |
| Memory utilization | < 70% | < 50% | Gauge |

**Test Data:**
- 10,000 policies with 10 rules each
- 1,000 agents with 5 capabilities each
- 100 frameworks with 50 controls each
- Mixed read/write: 90% reads, 10% writes

**Test Script:**
```python
# benchmarks/policy_evaluation.py

import asyncio
import time
from statistics import mean, percentile
from httpx import AsyncClient

async def benchmark_policy_evaluation():
    """Benchmark policy evaluation endpoint."""
    latencies = []
    errors = 0
    total_requests = 100_000
    
    async with AsyncClient(base_url="http://localhost:8080") as client:
        # Warmup
        for _ in range(1000):
            await client.post("/v1/enforcements", json={
                "agent_id": f"agent-{random.randint(1, 1000)}",
                "action": {"type": "tool_call", "resource": "test", "parameters": {}},
                "policy_id": f"policy-{random.randint(1, 10000)}"
            })
        
        # Benchmark
        start = time.monotonic()
        for i in range(total_requests):
            req_start = time.monotonic()
            try:
                response = await client.post("/v1/enforcements", json={
                    "agent_id": f"agent-{random.randint(1, 1000)}",
                    "action": {"type": "tool_call", "resource": f"res-{random.randint(1, 100)}", "parameters": {}},
                    "policy_id": f"policy-{random.randint(1, 10000)}"
                })
                if response.status_code != 200:
                    errors += 1
            except Exception:
                errors += 1
            latencies.append((time.monotonic() - req_start) * 1000)
        
        duration = time.monotonic() - start
    
    latencies.sort()
    results = {
        "total_requests": total_requests,
        "duration_seconds": duration,
        "throughput_rps": total_requests / duration,
        "error_rate": errors / total_requests,
        "p50_ms": percentile(latencies, 50),
        "p99_ms": percentile(latencies, 99),
        "p999_ms": percentile(latencies, 99.9),
        "mean_ms": mean(latencies),
        "min_ms": min(latencies),
        "max_ms": max(latencies)
    }
    return results
```

#### 6.2.2 Evidence Submission Benchmark

| Metric | Target | Stretch | Measurement |
|--------|--------|---------|-------------|
| p50 latency | < 20ms | < 10ms | Histogram |
| p99 latency | < 200ms | < 100ms | Histogram |
| Throughput | 5K req/s | 10K req/s | Counter |
| Bulk throughput | 50K items/min | 100K items/min | Counter |
| Verification latency | < 50ms | < 20ms | Histogram |

**Test Data:**
- Evidence sizes: 1KB, 10KB, 100KB, 1MB
- Mixed types: policy_evaluation, assessment_result, audit_event
- Verification: SHA-256 hash verification

#### 6.2.3 Audit Trail Write Benchmark

| Metric | Target | Stretch | Measurement |
|--------|--------|---------|-------------|
| p50 latency | < 5ms | < 2ms | Histogram |
| p99 latency | < 50ms | < 20ms | Histogram |
| Throughput | 100K events/s | 500K events/s | Counter |
| Hash chain verification | < 2s for 10K | < 1s for 10K | Timer |
| Merkle root computation | < 5s for 100K | < 2s for 100K | Timer |

#### 6.2.4 Compliance Computation Benchmark

| Metric | Target | Stretch | Measurement |
|--------|--------|---------|-------------|
| p50 latency | < 50ms | < 20ms | Histogram |
| p99 latency | < 500ms | < 200ms | Histogram |
| Throughput | 1K req/s | 5K req/s | Counter |
| Full recompute | < 30s | < 10s | Timer |

#### 6.2.5 Assessment Execution Benchmark

| Metric | Target | Stretch | Measurement |
|--------|--------|---------|-------------|
| Single assessment | < 5s | < 2s | Timer |
| Batch assessment (100) | < 60s | < 30s | Timer |
| Concurrent assessments | 10 | 50 | Gauge |
| Evidence generation | < 1s per item | < 0.5s | Timer |

#### 6.2.6 API CRUD Benchmarks

| Endpoint | p50 | p99 | Throughput |
|----------|-----|-----|------------|
| POST /v1/policies | < 50ms | < 200ms | 1K/s |
| GET /v1/policies | < 10ms | < 50ms | 10K/s |
| GET /v1/policies/{id} | < 5ms | < 20ms | 20K/s |
| PUT /v1/policies/{id} | < 100ms | < 500ms | 500/s |
| DELETE /v1/policies/{id} | < 50ms | < 200ms | 1K/s |
| POST /v1/evidence | < 50ms | < 200ms | 5K/s |
| GET /v1/evidence | < 10ms | < 50ms | 10K/s |
| POST /v1/enforcements | < 10ms | < 100ms | 50K/s |
| GET /v1/audit-trail | < 20ms | < 100ms | 5K/s |

#### 6.2.7 Database Benchmarks

| Operation | Target | Stretch |
|----------|--------|---------|
| Simple SELECT (PK) | < 1ms | < 0.5ms |
| Complex JOIN (5 tables) | < 10ms | < 5ms |
| JSONB query | < 5ms | < 2ms |
| Full-text search | < 50ms | < 20ms |
| INSERT | < 5ms | < 2ms |
| UPDATE | < 10ms | < 5ms |
| DELETE | < 5ms | < 2ms |
| Bulk INSERT (1000) | < 100ms | < 50ms |

#### 6.2.8 Cache Benchmarks

| Operation | Target | Stretch |
|----------|--------|---------|
| Cache hit | < 1ms | < 0.5ms |
| Cache miss | < 10ms | < 5ms |
| Cache invalidation | < 5ms | < 2ms |
| Hit ratio | > 95% | > 99% |

#### 6.2.9 Event Bus Benchmarks

| Operation | Target | Stretch |
|----------|--------|---------|
| Publish latency | < 5ms | < 2ms |
| End-to-end latency | < 100ms | < 50ms |
| Throughput | 100K msg/s | 500K msg/s |
| Consumer lag | < 1000 | < 100 |

#### 6.2.10 End-to-End Benchmarks

| Scenario | Target | Stretch |
|----------|--------|---------|
| Agent action → enforcement → evidence → audit | < 100ms | < 50ms |
| Policy update → cache invalidation → enforcement | < 1s | < 500ms |
| Evidence submission → compliance recompute | < 5s | < 2s |
| Assessment completion → finding generation → ticket | < 10s | < 5s |

### 6.3 Benchmark Execution Plan

```bash
#!/bin/bash
# benchmarks/run_all.sh

set -euo pipefail

RESULTS_DIR="benchmark_results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "Running GRC_Claw performance benchmarks..."
echo "Results: $RESULTS_DIR"

# 1. Policy Evaluation
echo "1/10: Policy Evaluation Benchmark"
python -m benchmarks.policy_evaluation --output "$RESULTS_DIR/policy_eval.json"

# 2. Evidence Submission
echo "2/10: Evidence Submission Benchmark"
python -m benchmarks.evidence_submission --output "$RESULTS_DIR/evidence_sub.json"

# 3. Audit Trail Write
echo "3/10: Audit Trail Write Benchmark"
python -m benchmarks.audit_write --output "$RESULTS_DIR/audit_write.json"

# 4. Compliance Computation
echo "4/10: Compliance Computation Benchmark"
python -m benchmarks.compliance_compute --output "$RESULTS_DIR/compliance_compute.json"

# 5. Assessment Execution
echo "5/10: Assessment Execution Benchmark"
python -m benchmarks.assessment_execution --output "$RESULTS_DIR/assessment_exec.json"

# 6. API CRUD
echo "6/10: API CRUD Benchmark"
python -m benchmarks.api_crud --output "$RESULTS_DIR/api_crud.json"

# 7. Database
echo "7/10: Database Benchmark"
python -m benchmarks.database --output "$RESULTS_DIR/database.json"

# 8. Cache
echo "8/10: Cache Benchmark"
python -m benchmarks.cache --output "$RESULTS_DIR/cache.json"

# 9. Event Bus
echo "9/10: Event Bus Benchmark"
python -m benchmarks.event_bus --output "$RESULTS_DIR/event_bus.json"

# 10. End-to-End
echo "10/10: End-to-End Benchmark"
python -m benchmarks.end_to_end --output "$RESULTS_DIR/end_to_end.json"

echo "All benchmarks completed. Results in $RESULTS_DIR"
```

### 6.4 Benchmark Pass/Fail Criteria

| Benchmark | Pass Condition | Fail Condition |
|-----------|---------------|----------------|
| Policy Evaluation | p99 < 50ms AND throughput > 50K/s | p99 > 100ms OR throughput < 10K/s |
| Evidence Submission | p99 < 200ms AND throughput > 5K/s | p99 > 500ms OR throughput < 1K/s |
| Audit Trail Write | p99 < 50ms AND throughput > 100K/s | p99 > 100ms OR throughput < 50K/s |
| Compliance Computation | p99 < 500ms AND throughput > 1K/s | p99 > 1s OR throughput < 100/s |
| Assessment Execution | Single < 5s AND batch < 60s | Single > 10s OR batch > 120s |
| API CRUD | All p99 < 500ms | Any p99 > 1s |
| Database | All p99 < 50ms | Any p99 > 100ms |
| Cache | Hit ratio > 95% AND p99 < 5ms | Hit ratio < 90% OR p99 > 10ms |
| Event Bus | p99 < 100ms AND throughput > 100K/s | p99 > 500ms OR throughput < 50K/s |
| End-to-End | p99 < 100ms | p99 > 500ms |

---

## 7. Scalability Test Plan

### 7.1 Scalability Test Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Scalability Test Architecture                         │
│                                                                         │
│  ┌──────────────┐                                                       │
│  │  Load        │                                                       │
│  │  Generator   │──────┐                                                │
│  │  (5 nodes)   │      │                                                │
│  └──────────────┘      │                                                │
│                         ▼                                                │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    API Gateway (3 replicas)                   │      │
│  │              Rate Limiting + Load Balancing                   │      │
│  └───────────────────────────┬──────────────────────────────────┘      │
│                              │                                          │
│         ┌────────────────────┼────────────────────┐                    │
│         ▼                    ▼                    ▼                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │  Policy      │    │  Enforcement │    │  Evidence    │              │
│  │  Engine (3)  │    │  Engine (5)  │    │  Service (3) │              │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│         │                   │                   │                       │
│         └───────────────────┼───────────────────┘                      │
│                             ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    Data Layer                                 │      │
│  │  PostgreSQL (3)  │  Redis (3)  │  Kafka (3)  │  ES (3)     │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    Monitoring Stack                           │      │
│  │  Prometheus  │  Grafana  │  Jaeger  │  AlertManager         │      │
│  └──────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Scalability Test Scenarios

#### 7.2.1 Scenario 1: Horizontal Scaling — Policy Engine

**Objective:** Verify policy engine scales horizontally with increasing load.

| Parameter | Value |
|----------|-------|
| **Initial Load** | 1K req/s |
| **Target Load** | 50K req/s |
| **Scale Increment** | 1K req/s per 10 seconds |
| **Max Replicas** | 20 |
| **Scaling Trigger** | CPU > 60% OR p99 latency > 50ms |
| **Scale-down Trigger** | CPU < 30% AND p99 latency < 20ms for 5 min |

**Pass Criteria:**
- [ ] p99 latency remains < 100ms at all load levels
- [ ] No errors at any load level
- [ ] Auto-scaling triggers within 30 seconds
- [ ] Scale-down occurs within 5 minutes of load decrease
- [ ] All replicas receive traffic (no hotspots)

**Test Script:**
```python
# scalability/test_policy_scaling.py

import asyncio
import time
from kubernetes import client, config

async def test_policy_engine_scaling():
    """Test policy engine horizontal scaling."""
    config.load_kube_config()
    v1 = client.AppsV1Api()
    
    # Start with 3 replicas
    await set_replicas(v1, "policy-engine", 3)
    
    load_levels = [1000, 5000, 10000, 20000, 30000, 40000, 50000]
    
    for target_rps in load_levels:
        print(f"Testing at {target_rps} req/s...")
        
        # Ramp up load
        await ramp_load(target_rps, duration=60)
        
        # Wait for scaling
        await asyncio.sleep(30)
        
        # Measure
        metrics = await collect_metrics(duration=60)
        
        # Check pass criteria
        assert metrics["p99_latency_ms"] < 100, f"p99 too high: {metrics['p99_latency_ms']}ms"
        assert metrics["error_rate"] < 0.001, f"Error rate too high: {metrics['error_rate']}"
        assert metrics["replicas"] >= 3, f"Too few replicas: {metrics['replicas']}"
        
        print(f"  ✓ p99: {metrics['p99_latency_ms']:.1f}ms, "
              f"replicas: {metrics['replicas']}, "
              f"errors: {metrics['error_rate']:.4f}")
    
    print("Policy engine scaling test PASSED")
```

#### 7.2.2 Scenario 2: Database Scalability — Read Replicas

**Objective:** Verify read scaling with PostgreSQL read replicas.

| Parameter | Value |
|----------|-------|
| **Initial Replicas** | 1 primary + 2 read replicas |
| **Target Replicas** | 1 primary + 5 read replicas |
| **Read/Write Ratio** | 90/10 |
| **Data Volume** | 10M policies, 100M evidence items |
| **Scaling Trigger** | Read latency p99 > 20ms |

**Pass Criteria:**
- [ ] Read latency p99 < 20ms with 5 replicas
- [ ] Write latency p99 < 50ms (no degradation)
- [ ] Replication lag < 1 second
- [ ] Automatic failover < 30 seconds
- [ ] Connection pool saturation < 80%

#### 7.2.3 Scenario 3: Event Bus Scalability — Kafka Partitioning

**Objective:** Verify Kafka scales with partition count and consumer groups.

| Parameter | Value |
|----------|-------|
| **Initial Partitions** | 12 per topic |
| **Target Partitions** | 48 per topic |
| **Consumer Groups** | 3 (enforcement, evidence, audit) |
| **Message Rate** | 100K msg/s |
| **Message Size** | 1KB average |
| **Retention** | 7 days |

**Pass Criteria:**
- [ ] End-to-end latency p99 < 1 second
- [ ] No message loss (exactly-once semantics)
- [ ] Consumer lag < 1000 messages
- [ ] Rebalancing completes < 30 seconds
- [ ] Throughput scales linearly with partitions

#### 7.2.4 Scenario 4: Cache Scalability — Redis Cluster

**Objective:** Verify Redis cluster scales with shard count.

| Parameter | Value |
|----------|-------|
| **Initial Shards** | 3 |
| **Target Shards** | 6 |
| **Cache Hit Ratio Target** | > 95% |
| **Eviction Policy** | allkeys-lru |
| **Max Memory per Node** | 4GB |

**Pass Criteria:**
- [ ] Cache hit ratio > 95% at all load levels
- [ ] Memory utilization < 80% per node
- [ ] No evictions under normal load
- [ ] Failover < 10 seconds
- [ ] Cluster rebalancing < 60 seconds

#### 7.2.5 Scenario 5: Multi-Tenant Scalability

**Objective:** Verify system scales with tenant count and tenant isolation.

| Parameter | Value |
|----------|-------|
| **Initial Tenants** | 10 |
| **Target Tenants** | 1000 |
| **Policies per Tenant** | 100 |
| **Agents per Tenant** | 50 |
| **Evidence per Tenant** | 10K items/day |
| **Isolation Level** | Row-level security |

**Pass Criteria:**
- [ ] No cross-tenant data leakage
- [ ] Query performance degrades < 20% from 10 to 1000 tenants
- [ ] Tenant onboarding < 5 seconds
- [ ] Resource quotas enforced
- [ ] Per-tenant rate limiting works

#### 7.2.6 Scenario 6: Failure Recovery — Chaos Engineering

**Objective:** Verify system resilience under various failure conditions.

| Failure Scenario | Injection Method | Expected Behavior |
|-----------------|-----------------|-------------------|
| Pod termination | kubectl delete pod | Auto-restart < 30s |
| Node failure | kubectl drain node | Workload reschedule < 60s |
| Network partition | toxiproxy | Circuit breaker triggers |
| Database primary failure | kill primary | Failover < 30s |
| Redis node failure | kubectl delete pod | Sentinel failover < 10s |
| Kafka broker failure | kubectl delete pod | Rebalance < 30s |
| DNS failure | /etc/hosts modification | Cached DNS < 60s |
| Certificate expiry | Short-lived cert | Auto-rotation |
| Disk full | Fill disk | Alert + graceful degradation |
| Memory pressure | Memory limit | OOM kill + restart |

**Pass Criteria:**
- [ ] All failures detected within 10 seconds
- [ ] Auto-recovery completes within defined RTO
- [ ] No data loss (RPO = 0 for critical data)
- [ ] Alerts fired for all failure scenarios
- [ ] Circuit breakers prevent cascade failures

### 7.3 Scalability Test Execution Plan

```bash
#!/bin/bash
# scalability/run_scalability_tests.sh

set -euo pipefail

RESULTS_DIR="scalability_results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "Running GRC_Claw scalability tests..."
echo "Results: $RESULTS_DIR"

# Scenario 1: Policy Engine Scaling
echo "1/6: Policy Engine Horizontal Scaling"
python -m scalability.test_policy_scaling --output "$RESULTS_DIR/policy_scaling.json"

# Scenario 2: Database Read Replicas
echo "2/6: Database Read Replica Scaling"
python -m scalability.test_db_scaling --output "$RESULTS_DIR/db_scaling.json"

# Scenario 3: Event Bus Scaling
echo "3/6: Event Bus Partition Scaling"
python -m scalability.test_event_bus_scaling --output "$RESULTS_DIR/event_bus_scaling.json"

# Scenario 4: Cache Scaling
echo "4/6: Cache Cluster Scaling"
python -m scalability.test_cache_scaling --output "$RESULTS_DIR/cache_scaling.json"

# Scenario 5: Multi-Tenant Scaling
echo "5/6: Multi-Tenant Scaling"
python -m scalability.test_multi_tenant --output "$RESULTS_DIR/multi_tenant.json"

# Scenario 6: Chaos Engineering
echo "6/6: Chaos Engineering"
python -m scalability.test_chaos --output "$RESULTS_DIR/chaos.json"

echo "All scalability tests completed. Results in $RESULTS_DIR"
```

### 7.4 Scalability Targets Summary

| Metric | Current | 6-Month Target | 12-Month Target |
|--------|---------|----------------|-----------------|
| Enforcement decisions/sec | 10K | 50K | 100K |
| Evidence items/day | 1M | 10M | 100M |
| Audit events/sec | 100K | 500K | 1M |
| API requests/sec | 10K | 50K | 100K |
| Concurrent agents | 10K | 100K | 1M |
| Registered policies | 10K | 100K | 1M |
| Compliance frameworks | 20 | 50 | 100 |
| Evidence retention | 7 years | 10 years | 15 years |
| Audit trail retention | 7 years | 10 years | 15 years |
| Tenants | 10 | 100 | 1000 |
| Availability | 99.9% | 99.99% | 99.999% |

### 7.5 Scalability Bottleneck Analysis

| Component | Current Bottleneck | Scaling Strategy | Expected Improvement |
|----------|-------------------|-----------------|---------------------|
| Policy Engine | Single-threaded evaluation | Horizontal scaling + policy sharding | 10x |
| PostgreSQL | Write throughput | Partitioning + read replicas | 5x |
| Redis | Memory per node | Cluster mode + sharding | 3x |
| Kafka | Partition count | Increase partitions + consumer groups | 4x |
| Elasticsearch | Index sharding | Add nodes + increase shards | 3x |
| API Gateway | Connection limits | Horizontal scaling + connection pooling | 5x |
| Audit Trail | Hash chain computation | Batch Merkle tree + parallel signing | 2x |

---

## 8. Appendices

### Appendix A: JSON Schema Validation

All JSON Schemas in Section 3 conform to [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/schema). Validation is performed at:

1. **API Gateway:** Request validation before routing
2. **Service Layer:** Business rule validation
3. **Database Layer:** JSONB constraint validation

### Appendix B: API Versioning Strategy

| Version | Status | Base Path | Sunset Date |
|---------|--------|-----------|-------------|
| v1 | Current | `/v1/` | — |
| v1.1 | Beta | `/v1.1/` | — |
| v0 | Deprecated | `/v0/` | 2027-01-01 |

### Appendix C: Migration Compatibility Matrix

| Source Version | Target Version | Migration Path | Downtime |
|---------------|---------------|----------------|----------|
| v0.9 → v1.0 | Direct | Automated | < 1 hour |
| v1.0 → v1.1 | Direct | Automated | < 30 min |
| v1.1 → v2.0 | Via v1.1 | Manual | < 4 hours |
| Legacy → v1.0 | Via ETL | ETL Pipeline | < 1 day |

### Appendix D: Performance Tuning Guidelines

| Area | Tuning Parameter | Default | Optimal |
|------|-----------------|---------|---------|
| PostgreSQL | shared_buffers | 25% RAM | 25% RAM |
| PostgreSQL | work_mem | 4MB | 16MB |
| PostgreSQL | effective_cache_size | 50% RAM | 75% RAM |
| PostgreSQL | max_connections | 100 | 500 |
| Redis | maxmemory-policy | allkeys-lru | allkeys-lru |
| Redis | maxmemory | 4GB | 8GB |
| Kafka | num.partitions | 12 | 24 |
| Kafka | replication.factor | 3 | 3 |
| Kafka | min.insync.replicas | 2 | 2 |
| API | timeout | 30s | 10s |
| API | rate_limit | 10K/min | 50K/min |

### Appendix E: Monitoring Dashboard

| Dashboard | Metrics | Refresh |
|----------|---------|---------|
| Overview | Request rate, error rate, latency | 15s |
| Enforcement | Decisions/sec, by decision type, latency | 15s |
| Evidence | Items/sec, by type, verification status | 30s |
| Compliance | Score by framework, trend, gaps | 1min |
| Audit | Events/sec, chain integrity, Merkle root | 15s |
| Infrastructure | CPU, memory, disk, network | 15s |
| Database | Connections, queries/sec, replication lag | 15s |
| Cache | Hit ratio, evictions, memory | 15s |
| Events | Throughput, consumer lag, errors | 15s |

---

*End of Expanded Technical Specification*
</longcat_think>
