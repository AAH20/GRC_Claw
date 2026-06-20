---
name: iso-42001-ai-management-engineering
description: Designs and implements ISO/IEC 42001 AI Management System (AIMS) architecture, controls, and evidence. Maps agentic platforms (OpenClaw, Cursor, OpenAI, Anthropic) to clauses with gap analysis. Use for ISO 42001 compliance, AI governance engineering, AIMS audits, or GRC_Claw control implementation.
---

# ISO/IEC 42001 — AI Management System Architecture & Engineering

ISO42001 comprehensive architecture and engineering with implementation while highlighting the top Companies Gaps such as Anthropic , OpenAI , Cursor and Open Source OpenClaw Projects.

## Priority

**Architecture first, implementation second.** Define AIMS scope, risk treatment, and control objectives before tooling. Align technical controls with `netsec-grc-architecture-engineering` (planes, gateway daemons) and **GRC_Claw** (OpenClaw for GRC, exec policy, evidence).

Production SOC context: **[a2zsoc.com](https://a2zsoc.com)** for tenant GRC + security events.

## GRC_Claw integration

| Artifact | Location |
|----------|----------|
| `@grc-claw/aims` | Vendor gaps, clause map, technical controls |
| `iso42001` framework pack | `@grc-claw/frameworks` |
| Gateway APIs | `GET /api/aims/vendor-gaps`, `GET /api/aims/technical-controls` |
| Docs | [docs/ISO_42001_AIMS.md](../../docs/ISO_42001_AIMS.md) |
| Tests | `npm run test:iso42001` |

```bash
curl -s http://127.0.0.1:18791/api/aims/vendor-gaps | jq .
curl -s http://127.0.0.1:18791/api/aims/technical-controls | jq .
npm run test:iso42001
```

## When to apply

- Designing or certifying an **AIMS** (AI Management System)
- Mapping agentic IDE / gateway products to ISO 42001 clauses
- Gap assessments vs **Anthropic, OpenAI, Cursor, OpenClaw**
- Implementing controls in GRC_Claw (`@grc-claw/agent-runtime`, gateway, evidence)
- AI impact assessments, lifecycle, monitoring, and supplier oversight

## Session workflow

```
- [ ] Define AIMS scope (systems, models, agents, data, geography)
- [ ] Stakeholder / regulator context (customers, EU AI Act overlap, sector)
- [ ] AI risk assessment (harm, likelihood, treat/mitigate/transfer/accept)
- [ ] Map clauses 4–10 + Annex A controls to architecture components
- [ ] Run vendor gap matrix (Anthropic, OpenAI, Cursor, OpenClaw)
- [ ] Produce control implementation plan + evidence owners
- [ ] Wire technical controls (gateway, exec policy, logging, human oversight)
- [ ] Validate with tests + audit evidence package
```

## AIMS reference architecture (planes)

| Plane | ISO 42001 theme | GRC_Claw / OpenClaw mapping |
|-------|-----------------|-----------------------------|
| **Governance** | Policy, roles, accountability (Clause 5) | AIMS policy docs, `frameworks` packs, RACI |
| **Control** | Operational planning, risk treatment (Clause 6, 8) | Gateway daemon, exec policy, change control |
| **Experience** | Communication, transparency (Clause 7) | User notices, model cards, incident comms |
| **Evidence** | Monitoring, measurement, audit (Clause 9, 10) | `@grc-claw/evidence`, immutable hashes, logs |
| **Data** | AI system lifecycle, data for AI (Annex A) | Ingest, training/ops data lineage, retention |

## Clause → implementation map (summary)

| Clause | Requirement | Default implementation anchor |
|--------|-------------|------------------------------|
| **4** | Context of organization | Scope doc, interested parties register |
| **5** | Leadership | AI policy, roles, management commitment |
| **6** | Planning | AI risk register, objectives, change planning |
| **7** | Support | Competence, awareness, documented info |
| **8** | Operation | Lifecycle controls, suppliers, agent operations |
| **9** | Performance evaluation | KPIs, internal audit, management review |
| **10** | Improvement | Nonconformity, corrective action |

Annex A control detail: [reference.md](reference.md#annex-a-control-themes).

## Top vendor gap highlights

Use as **review prompts**, not legal findings. Programmatic matrix: `@grc-claw/aims` and `GET /api/aims/vendor-gaps`. Full detail: [reference.md](reference.md#vendor-gap-matrix).

| Vendor / project | Strength | Typical gap theme for ISO 42001 |
|------------------|----------|--------------------------------|
| **Anthropic** | RSP, safety research, API policies | Enterprise AIMS evidence per tenant; integration assurance |
| **OpenAI** | Preparedness, usage policies | Human oversight for autonomous agents; destructive action gating |
| **Cursor** | IDE agent, MCP, skills | AIMS scope for local vs cloud; MCP supply-chain governance |
| **OpenClaw** (OSS) | Local gateway, pairing, skills | Operator-deployed AIMS boundary; prompt injection + tool abuse |

**GRC_Claw closes common gaps:** exec policy (allowlist → approval → sandbox), evidence hashing, gateway auth, canonical event lineage—see [examples.md](examples.md).

## Technical control patterns

| Control objective | Pattern | GRC_Claw component |
|-------------------|---------|-------------------|
| Human oversight | Approval tokens for destructive tools | `@grc-claw/agent-runtime` |
| Traceability | Audit log per tool invocation | `AgentSession.getAuditLog()` |
| Access control | Gateway token + WS `connect` | `@grc-claw/gateway` |
| Integrity of records | SHA-256 evidence lineage | `@grc-claw/evidence` |
| Monitoring AI incidents | Normalize alerts → controls | `@grc-claw/ingest` + a2zsoc.com |
| Supplier API hygiene | Scoped keys, no keys in repo | `npm run doctor` |

## Verification checklist

- [ ] SoA completed with owners and evidence IDs
- [ ] Risk register reviewed ≤ 12 months (or after major model/agent change)
- [ ] Destructive agent tools require human approval in production
- [ ] `npm run test:iso42001` and `npm run test:comprehensive` pass

## Additional resources

- [reference.md](reference.md) — Annex A themes + vendor gaps
- [examples.md](examples.md) — Templates and curl evidence
- [docs/ISO_42001_AIMS.md](../../docs/ISO_42001_AIMS.md)
- [docs/AGENTIC_AI_SECURITY.md](../../docs/AGENTIC_AI_SECURITY.md)
