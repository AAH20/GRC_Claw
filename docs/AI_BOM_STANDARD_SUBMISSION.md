# AI Bill of Materials (AI-BOM) — Standard Submission Package

**Prepared by:** GRC_Claw / A2Z SOC  
**Contact:** https://a2zsoc.com/contact  
**Reference implementation:** `@grc-claw/observability` (SPDX/CycloneDX-aligned AI-BOM generator)  
**Status:** Draft for submission to NIST AI RMF WG, ISO/IEC JTC 1/SC 42 WG 42, CISA AI Security Initiative

---

## Executive Summary

This document packages GRC_Claw's AI-BOM format for submission to standards bodies as the reference implementation for AI supply chain transparency. The AI-BOM generator in `@grc-claw/observability` extracts models, tools, frameworks, and data sources from OpenTelemetry trace data and outputs SPDX 2.3 / CycloneDX 1.5-aligned documents.

As of June 2026, no published standard mandates an AI-BOM format. EU AI Act Art.11 and NIST AI RMF 1.0 require model documentation and transparency but do not specify a machine-readable format. This is the gap GRC_Claw fills — and the opportunity to become the reference implementation.

---

## 1. Problem Statement

### 1.1 Regulatory Requirements Without Format Standardization

| Regulation | Requirement | Current Gap |
|---|---|---|
| EU AI Act Art.11 | Technical documentation for high-risk AI systems | No machine-readable format specified |
| EU AI Act Art.53 | GPAI model transparency obligations | No standardized disclosure format |
| NIST AI RMF (MAP 1.1) | Document AI system components | No cross-vendor interoperable format |
| ISO/IEC 42001 A.7.1 | AI system resources and documentation | No toolchain-extractable format |
| CISA AI Security Guidance | Software supply chain transparency for AI | SBOM extended to AI not standardized |

### 1.2 Why Existing SBOMs are Insufficient

Software Bill of Materials (SPDX, CycloneDX) cover software components but lack semantics for:
- Model weights and training data lineage
- AI tool/plugin invocation chains
- LLM provider routing and version pinning
- Agent skill and MCP server dependencies
- Inference configuration (temperature, max_tokens, system prompt hash)
- Human oversight checkpoints
- Bias and fairness evaluation artifacts

---

## 2. GRC_Claw AI-BOM Schema

### 2.1 Root Document Structure

```json
{
  "aicom:version": "1.0",
  "aicom:generated": "2026-06-26T00:00:00Z",
  "aicom:generator": "@grc-claw/observability@1.0.0",
  "aicom:hash": "<SHA-256 of document>",
  
  "subject": {
    "name": "Customer Compliance Agent",
    "version": "2.1.0",
    "description": "Automated compliance monitoring agent",
    "type": "agentic_ai_system",
    "operator": "did:grc:node:<operator-node-id>",
    "deployedAt": "2026-01-15T00:00:00Z"
  },

  "models": [...],          // LLM components
  "tools": [...],           // Tools and MCP servers
  "frameworks": [...],      // GRC/AI governance frameworks
  "dataSources": [...],     // Training data and knowledge bases
  "humanOversight": [...],  // Oversight checkpoints
  "evaluations": [...]      // Safety/bias evaluations
}
```

### 2.2 Model Component

```json
{
  "id": "model-001",
  "name": "claude-sonnet-4-6",
  "provider": "Anthropic PBC",
  "providerDid": "did:web:anthropic.com",
  "version": "claude-sonnet-4-6",
  "type": "llm",
  "modality": ["text"],
  "contextWindow": 200000,
  "apiEndpoint": "https://api.anthropic.com/v1/messages",
  "policyUrl": "https://www.anthropic.com/usage-policy",
  "modelCardUrl": "https://www.anthropic.com/model-card",
  "licenseType": "proprietary_api",
  "dataResidency": ["US"],
  "euAiActClassification": "GPAI",
  "iso42001Scope": "operator_deployed",
  "riskRating": "medium",
  "firstSeenAt": "2026-01-15T00:00:00Z",
  "lastSeenAt": "2026-06-26T00:00:00Z",
  "invocationCount": 48291,
  "avgLatencyMs": 1840
}
```

### 2.3 Tool Component

```json
{
  "id": "tool-001",
  "name": "grc.list_controls",
  "category": "grc_query",
  "tier": "read",
  "provider": "GRC_Claw",
  "version": "1.0.0",
  "registeredAt": "2026-01-15T00:00:00Z",
  "allowlisted": true,
  "requiresApproval": false,
  "requiresIdempotencyKey": false,
  "invocationCount": 12847,
  "lastInvokedAt": "2026-06-26T00:00:00Z",
  "scopeHash": "<SHA-256 of tool definition>"
}
```

### 2.4 Human Oversight Checkpoint

```json
{
  "id": "oversight-001",
  "type": "approval_gate",
  "triggersOn": ["destructive", "write"],
  "approvalMethod": "approvalToken",
  "timeoutPolicy": "reject",
  "auditTrail": "action_ledger",
  "iso42001Control": "A.12.3",
  "euAiActArticle": "Art.14"
}
```

---

## 3. Submission Targets

### 3.1 NIST AI Risk Management Framework Working Group

**Contact:** aiframework@nist.gov  
**Submission type:** Comment on AI RMF Playbook, MAP 1.1 "Document AI system components"  
**Ask:** Reference GRC_Claw AI-BOM as example implementation in NIST AI RMF Playbook v1.1

**Submission text:**

> NIST AI RMF MAP 1.1 calls for organizations to document AI system components but does not specify a machine-readable format. We submit the GRC_Claw AI-BOM schema as a reference implementation that is:
> - Extractable automatically from OpenTelemetry trace data (no manual documentation burden)
> - Aligned with existing SPDX 2.3 and CycloneDX 1.5 structures
> - Mappable to EU AI Act Art.11 technical documentation requirements
> - Available as an MIT-licensed open-source implementation at github.com/AAH20/GRC_Claw
>
> We request that NIST AI RMF Playbook v1.1 reference this format in MAP 1.1 guidance materials.

### 3.2 ISO/IEC JTC 1/SC 42 WG 42 (ISO 42001 Working Group)

**Contact:** Through national body (ANSI for US, BSI for UK, DIN for Germany)  
**Submission type:** New Work Item Proposal (NWIP) for AI-BOM Technical Report  
**Ask:** Initiate ISO/IEC TR on AI Bill of Materials aligned with ISO 42001 A.7.1

**Proposal reference code:** ISO/IEC JTC 1/SC 42 N [XXXX]

### 3.3 CISA AI Security Initiative

**Contact:** https://www.cisa.gov/ai  
**Submission type:** Technical contribution to "Secure by Design" AI guidance  
**Ask:** Include AI-BOM as a recommended artifact in CISA AI Security Guidance for Critical Infrastructure

### 3.4 OWASP Foundation (Agentic AI Working Group)

**Contact:** https://owasp.org/www-project-top-10-for-large-language-model-applications/  
**Submission type:** Reference implementation for OWASP LLM Top 10 SC-10 (Supply Chain Vulnerability)  
**Ask:** Reference GRC_Claw AI-BOM as the mitigation artifact for supply chain transparency

---

## 4. Reference Implementation

The GRC_Claw AI-BOM generator is in `packages/observability/src/` and is:

- **Automatic:** Extracts AI-BOM from OpenTelemetry spans — zero manual work
- **Standards-aligned:** SPDX 2.3 DocumentNamespace + CycloneDX 1.5 component structure
- **Agent-executable:** `grc report --format ai-bom` generates a signed AI-BOM JSON document
- **Verifiable:** Content hash + DID-signed by GRC_Claw node for third-party verification

```bash
# Generate an AI-BOM for your deployment
grc report --format ai-bom --output ai-bom-$(date +%F).json

# Verify an AI-BOM
curl -X POST https://a2zsoc.com/api/aims-report/verify-bom \
  -H "Content-Type: application/json" \
  -d @ai-bom-2026-06-26.json
```

---

## 5. Competitive Positioning

| Standard body | Current AI-BOM guidance | GRC_Claw opportunity |
|---|---|---|
| NIST | "Document AI components" — no format | Reference implementation in Playbook v1.1 |
| ISO/IEC SC 42 | ISO 42001 A.7.1 — no machine-readable format | NWIP for AI-BOM Technical Report |
| CISA | General supply chain guidance | Secure by Design AI annex reference |
| OWASP | LLM-10 (Supply Chain) — no artifact spec | Mitigation reference implementation |
| EU AI Office | Art.11 tech docs — no format spec | GPAI code of practice annex |

**First-mover advantage:** The organization that publishes the first standards-body-endorsed AI-BOM format becomes the reference implementation that all tooling must support. GRC_Claw has the only working, OSS, trace-extraction-based AI-BOM generator as of June 2026.

---

*Prepared for external submission. Distribute freely. Contact a2zsoc.com for co-authorship on NWIP proposals.*
