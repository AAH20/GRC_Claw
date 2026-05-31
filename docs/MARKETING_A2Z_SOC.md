# Marketing: GRC_Claw × A2Z SOC

Use this copy for GitHub README badges, landing pages, and conference one-pagers.

## Headline options

1. **GRC_Claw — Open GRC. Private SOC. Agent-safe by design.**
2. **The compliance engine for A2Z SOC — fork it, demo it, bridge your enterprise.**
3. **Agentic GRC without agentic risk — powered by A2Z SOC.**

## Elevator pitch (30 seconds)

GRC_Claw is an MIT-licensed, modular GRC control plane with a supervised gateway daemon and **agentic AI security** built in. Run it standalone for audits and framework packs, or connect it to **Private A2Z SOC** for live SIEM correlation, Saudi-enterprise scale, and Wazuh/Snort/Suricata visibility. Open source earns trust; A2Z SOC earns the production contract.

## Value pillars

### 1. Open source credibility

- Framework packs (ISO 27001, NIST CSF, SOC 2) in-repo
- Evidence hashing and lineage for auditors
- Community connectors welcome (Splunk, Jira, ServiceNow)

### 2. A2Z SOC production bridge

- `@grc-claw/a2z-connector` — private URL, API key, tenant scope
- Maps `security_events` to control impact
- Pushes control failures back into SOC workflows

### 3. Agentic AI security (hero feature)

- Not “AI slapped on GRC” — **mandatory** exec policy, sandbox, approvals
- Safe automation: auto-collect evidence, human-gate remediation
- Audit trail for every tool invocation

## Comparison table (sales)

| | Spreadsheet GRC | Generic GRC SaaS | GRC_Claw + A2Z SOC |
|--|-----------------|------------------|---------------------|
| Live SIEM tie-in | Manual | Add-on $$$ | Native connector |
| On-prem / KSA data residency | Yes | Rare | A2Z SOC deployment |
| OSS inspection | No | No | GRC_Claw MIT |
| Agent automation | No | Risky black box | Policy-gated runtime |
| IDS/IPS context | No | Limited | Wazuh, Snort, Suricata |

## Call to action blocks

**For developers:** Star GRC_Claw → `docker compose up` → read `docs/AGENTIC_AI_SECURITY.md`

**For enterprises:** Deploy Private A2Z SOC → enable `a2z-connector` → contact A2Z for tenant keys

**For auditors:** Export evidence packs with SHA-256 lineage — no agent write access without approval

## Badge suggestions (README)

```markdown
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![A2Z SOC](https://img.shields.io/badge/Pairs%20with-A2Z%20SOC-red)](docs/MARKETING_A2Z_SOC.md)
[![Agentic AI Security](https://img.shields.io/badge/Agentic%20AI-Secured-green)](docs/AGENTIC_AI_SECURITY.md)
```

## SEO keywords

open source GRC, agentic AI security, compliance automation, A2Z SOC, Wazuh GRC, continuous control monitoring, ISO 27001 evidence, Saudi cybersecurity framework, SOC 2 audit automation
