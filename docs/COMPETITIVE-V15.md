# Competitive Analysis — V15

## Market Position Map

```
                    Governance Depth
                         ▲
                         │
    OpenGRC ●            │           ● ServiceNow GRC
    (basic)              │           (expensive/slow)
                         │
                         │
    ─────────────────────┼────────────────────►
    Traditional          │           Agent-Native
                         │
    Drata ●              │           ● A2Z SOC
    (20 frameworks)      │           (89 packages, 375 crosswalks)
                         │
    Vanta ●              │
    (SOC 2 only)         │
```

---

## 1. vs Vanta

| Dimension | Vanta | A2Z SOC |
|-----------|-------|---------|
| Frameworks | SOC 2 primary | 20+ frameworks (SOC 2, ISO 27001, NIST CSF, HIPAA, GDPR, CCPA, PCI DSS, etc.) |
| SIEM/SOAR | None — integrates with third-party | Native SIEM ingest (Wazuh, Snort, Suricata, Elasticsearch) |
| Agent Governance | None | Agent policy firewall, evidence lineage, Claude/Cursor/OpenAI audit trails |
| Pricing | Per-employee, opaque | Published tiers, org-based |
| Audit Evidence | Manual upload | Automated evidence refresh, crosswalk matrix |
| Sovereign Mode | SaaS only | Local-first, Supabase + Ollama |

**A2Z SOC advantage:** Multi-framework coverage + native SIEM + agent governance. Vanta is SOC 2 automation — we are GRC + SOC + AI governance in one platform.

---

## 2. vs Drata

| Dimension | Drata | A2Z SOC |
|-----------|-------|---------|
| Frameworks | SOC 2, ISO 27001 (expanding) | 20+ frameworks, 375 crosswalk mappings |
| Marketplace | None | Agent + connector marketplace |
| Sovereign Deployment | SaaS only | Self-hosted + cloud hybrid |
| Evidence Automation | Good | Better — async refresh, crosswalk auto-generation |
| Pricing | Per-employee | Org-based, published |
| Agent Governance | None | Native — policy firewall, lineage, audit |

**A2Z SOC advantage:** Broader framework coverage, marketplace ecosystem, sovereign option, and agent governance. Drata is compliance automation — we are compliance + security operations + AI governance.

---

## 3. vs ServiceNow GRC

| Dimension | ServiceNow GRC | A2Z SOC |
|-----------|---------------|---------|
| Deployment | Enterprise SaaS, months to deploy | Open-core, minutes to deploy |
| Pricing | $150K+ annually, custom quotes | Published tiers, $0–$99/mo PLG |
| Learning Curve | Steep (ITIL-driven) | Thin routes, familiar patterns |
| Agent Governance | None | Native — policy firewall, evidence lineage |
| Extensibility | Plugin marketplace (closed) | Open-source packages, community |
| Speed to Value | 3–6 months | Day 1 |

**A2Z SOC advantage:** Speed, cost, and openness. ServiceNow is for Fortune 500 with ITSM budgets — we are for every org that needs GRC without the overhead.

---

## 4. vs Wiz / Prisma Cloud

| Dimension | Wiz / Prisma | A2Z SOC |
|-----------|-------------|---------|
| Core | CSPM — cloud posture | Posture + compliance + GRC evidence |
| Compliance | Limited (CIS benchmarks) | 20+ frameworks with crosswalk |
| Agent Governance | None | Native |
| GRC Evidence | Export to other tools | Built-in evidence vault + refresh |
| Multi-Cloud | AWS + Azure + GCP | Same + on-prem + hybrid |
| Pricing | Enterprise, opaque | Published, PLG available |

**A2Z SOC advantage:** CSPM is one module in a full GRC platform. Wiz tells you what's wrong — we tell you what to fix and prove it to auditors.

---

## 5. vs Splunk / CrowdStrike

| Dimension | Splunk / CrowdStrike | A2Z SOC |
|-----------|---------------------|---------|
| Core | SIEM — log analysis | SIEM + compliance crosswalk + audit evidence |
| Compliance | Limited (PCI, HIPAA templates) | 20+ frameworks with full crosswalk |
| Agent Governance | None | Native |
| Audit Evidence | Manual export | Automated evidence vault |
| Pricing | Per-GB / per-endpoint, expensive | Published, org-based |
| Open Source | Splunk free tier (limited) | Open-core, transparent |

**A2Z SOC advantage:** Splunk finds threats — we find threats AND prove compliance. Security + GRC convergence without stitching two tools together.

---

## 6. vs LangChain / CrewAI

| Dimension | LangChain / CrewAI | A2Z SOC |
|-----------|-------------------|---------|
| Core | Agent orchestration | Agent orchestration + governance |
| Policy Firewall | None | Per-agent allow/deny rules |
| Evidence Lineage | None | Audit trail for every agent action |
| Compliance | None | Agent actions mapped to GRC controls |
| Deployment | Python library | Full-stack platform |

**A2Z SOC advantage:** LangChain/CrewAI build agents — we build agents AND govern them. Agent governance is the missing layer for enterprise AI adoption.

---

## 7. vs OpenGRC

| Dimension | OpenGRC | A2Z SOC |
|-----------|---------|---------|
| Packages | Basic | 89 packages |
| Crosswalk | Manual | 375 automated mappings |
| Marketplace | None | Agent + connector marketplace |
| Evidence | Manual upload | Automated refresh + vault |
| Deployment | Self-hosted only | Self-hosted + cloud hybrid |
| Agent Governance | None | Native |

**A2Z SOC advantage:** OpenGRC is a basic open-source GRC — we are an open-core platform with automation, marketplace, and agent governance.

---

## 8. Monopoly Advantages

### Network Effects

Every new org onboarding adds to the crosswalk mapping database. More orgs → more evidence patterns → better recommendations for all orgs.

```
Org count ↑ → Evidence patterns ↑ → Crosswalk accuracy ↑ → Value ↑
```

### Switching Costs

- **Data lock-in:** Evidence vault, control history, audit trails — migrating is painful
- **Workflow lock-in:** Custom policies, dashboards, integrations become institutional knowledge
- **Compliance lock-in:** Auditors expect continuity — switching mid-audit is risky

### Data Moat

- 375 crosswalk mappings (growing) — no competitor has this granularity
- Evidence refresh patterns across industries — improves recommendations
- Agent governance audit trails — unique dataset for AI compliance

### Regulatory Tailwind

- **EU AI Act** → Agent governance mandatory by 2026
- **SEC Cyber Rules** → Continuous compliance monitoring
- **NIS2 Directive** → Supply chain security evidence
- **ISO 42001** → AI management system certification

Every new regulation expands our addressable market. Competitors must add governance features — we already have them.

---

## Summary: Why A2Z SOC Wins

| Dimension | A2Z SOC | Any Single Competitor |
|-----------|---------|----------------------|
| Frameworks | 20+ | 1–5 |
| SIEM + GRC | Unified | Separate tools |
| Agent Governance | Native | None |
| Sovereign Mode | Yes | No |
| Marketplace | Yes | No |
| Pricing | Published | Opaque |
| Speed to Value | Hours | Weeks–months |
| Open Core | Yes | No |

**We don't compete with any single tool — we replace the stack.**
