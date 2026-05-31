# Agentic AI Security in GRC_Claw

GRC_Claw is marketed as **safe agentic GRC**: AI assists audits and control testing without becoming an unbounded insider threat.

## Threat model (assume breach)

| Threat | Example | Control |
|--------|---------|---------|
| Prompt injection | Malicious evidence text steers agent | Input sanitization; tool allowlists; no auto-execute on ingest |
| Tool abuse | Agent deletes logs or exfiltrates DB | Exec policy + approval + sandbox |
| Privilege escalation | Stolen gateway token | Short-lived tokens; pairing; rotate on leak |
| Cross-tenant bleed | Wrong `tenant_id` in job | Tenant guard on every facade call |
| Shadow AI | Analyst pastes keys into ChatGPT | On-prem / private LLM route via A2Z SOC policy |

## Three-phase exec policy

Implemented in `@grc-claw/agent-runtime`:

1. **Lexical allowlist** — `grc.query_controls`, `evidence.read`, not `shell.rm`
2. **Approval gate** — `evidence.write`, `soar.run_playbook`, `firewall.apply` need operator token
3. **Execution** — Docker sandbox default; host only with `execution: host` + paired device

## Tool tiers

| Tier | Examples | Policy |
|------|----------|--------|
| **Read** | List controls, fetch evidence metadata, query SOC events (read-only) | Auto-allow for paired agents |
| **Write** | Attach evidence, update control status | Idempotency key + audit log |
| **Destructive** | SOAR playbook, firewall change, bulk delete | Human approval + sandbox |

## Agent session rules

- Agents **never** hold A2Z SOC admin keys; gateway uses scoped integration key.
- Max tool calls per turn (default 12); timeout per call (30s).
- Full transcript + tool I/O appended to **audit stream** (gateway).
- LLM output is **untrusted** until validated against schema (Zod on tool args).

## Hardening checklist (operators)

- [ ] `GRC_CLAW_GATEWAY_TOKEN` from secret manager, not git
- [ ] Gateway bound to loopback or private VLAN
- [ ] `A2Z_SOC_API_KEY` scoped to ingest + GRC read, not user admin
- [ ] Docker sandbox image pinned by digest
- [ ] Approval workflow enabled for Tier Write/Destructive in production
- [ ] Weekly `npm run doctor` (config + token smoke test)

## Differentiator vs generic “AI GRC” bots

| Generic chatbot | GRC_Claw agent runtime |
|-----------------|------------------------|
| Browser plugin with full DOM | Gateway-mediated tools only |
| Optional guardrails | Mandatory exec policy |
| Cloud LLM by default | Pluggable; A2Z SOC private route |
| No SOC correlation | `a2z-connector` maps events → controls |

**Positioning for A2Z SOC:** *Your SOC detects; GRC_Claw explains compliance impact—with agents that cannot bypass your gateway.*
