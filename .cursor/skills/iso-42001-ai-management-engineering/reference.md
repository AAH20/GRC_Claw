# ISO/IEC 42001 Reference

Standard: **ISO/IEC 42001:2023** — Information technology — Artificial intelligence — Management system.

Programmatic data: `@grc-claw/aims` (`VENDOR_GAP_MATRIX`, `listClauseMap`, `listTechnicalControls`).

## Annex A control themes {#annex-a-control-themes}

| Theme | Annex A focus | Engineering artifacts |
|-------|---------------|------------------------|
| **A.2 Policies** | AI policy, alignment with org | `AIMS-AI-Policy.md`, board approval |
| **A.3 Internal organization** | Roles, responsibilities | RACI, AI system owner per product |
| **A.4 Resources** | Data, tools, compute | Asset inventory, capacity, GPU policy |
| **A.5 Lifecycle** | Development, deployment, retirement | SDLC gates, model version registry |
| **A.6 Data for AI** | Quality, provenance, bias | Data sheets, lineage, retention |
| **A.7 Information** | Transparency to users | Model cards, limitations, opt-out |
| **A.8 Use** | Intended use, misuse monitoring | Abuse monitoring, rate limits |
| **A.9 Third-party** | Suppliers, APIs | DPA, sub-processor list, API scopes |
| **A.10 Monitoring** | Performance, drift, incidents | SIEM rules, KPI dashboard |
| **A.11 Impact** | Impact assessment | AI impact assessment template |
| **A.12 Security** | Confidentiality, integrity, availability | Gateway, exec policy, encryption |
| **A.13 Privacy** | PII in prompts/logs | Redaction, retention, legal basis |
| **A.14 Safety** | Harm prevention | Red-team, kill switch, approvals |

GRC_Claw `iso42001` starter pack maps subset to `aims-a.*` control IDs.

## Vendor gap matrix {#vendor-gap-matrix}

See `packages/aims/src/vendor-gaps.ts` and `GET /api/aims/vendor-gaps`.

### Anthropic

| Area | Strength | Gap theme | Mitigation |
|------|----------|-----------|------------|
| Safety research | RSP, evaluations | Customer AIMS boundary | Gateway + contractual scope |
| API usage | Policies, limits | Tool chains invisible to customer | Gateway mediates tool calls |

### OpenAI

| Area | Strength | Gap theme | Mitigation |
|------|----------|-----------|------------|
| Policies | Preparedness | Autonomous loops | Exec policy + max calls |
| Tools | Function calling | Destructive composite actions | Tier + idempotency |

### Cursor

| Area | Strength | Gap theme | Mitigation |
|------|----------|-----------|------------|
| Product | IDE agents | Local vs cloud scope | SoA documentation |
| Extensibility | MCP, skills | MCP supply chain | Curated registry |

### OpenClaw

| Area | Strength | Gap theme | Mitigation |
|------|----------|-----------|------------|
| Architecture | Gateway, pairing | Deployer = accountable | `doctor`, hardening guide |
| Security | Public research | Localhost-trust defaults | Token auth, TLS |

## Overlap with other regimes

| Regime | Relationship to 42001 |
|--------|------------------------|
| **ISO 27001** | ISMS + AIMS; shared logging/access evidence |
| **NIST AI RMF** | Maps to Clause 6 and Annex A |
| **EU AI Act** | Conformity for high-risk AI; AIMS supports, does not replace |
| **SOC 2** | Trust criteria; AI as CC extensions |

## Connectivity matrix

| ID | Source | Destination | Purpose |
|----|--------|-------------|---------|
| A01 | Agent runtime | GRC_Claw gateway | Audited tool calls |
| A02 | Gateway | a2zsoc.com | Security + GRC events |
| A03 | Operators | Gateway :18791 | Management |
| A04 | LLM vendor API | Agent (via app) | Inference (scoped keys) |
