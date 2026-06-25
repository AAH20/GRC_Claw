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

## Action ledger and truthful execution

The gateway records an append-only, hash-chained action ledger at
`.grc_memory/action-ledger.ndjson` by default. Each agent or direct MCP call emits an intent,
policy decision, and result event. The ledger stores argument and output hashes plus key names,
not raw tool payloads. Read it through authenticated `GET /api/action-ledger`; the response also
verifies chain integrity.

Execution states are explicit: `recorded` means local evidence was stored, `executed` means a
connector accepted the request, and `verified` requires a target-system receipt. `simulated` and
`not_configured` are never presented as successful external execution.

## Agent assurance graph

Before an authenticated `POST /api/agent/invoke` is evaluated, the gateway records the action in
an in-memory assurance graph: a gateway-observed DID, tenant scope, tool tier, optional control
target, current risk assessment, and control blast radius. The invocation response includes this
`assurance` object, and authenticated `GET /api/assurance` returns aggregate graph and identity
statistics.

Gateway-observed DIDs are deliberately **provisional**: the gateway does not issue a credential
or claim an external identity. Set `GRC_CLAW_ASSURANCE_MAX_RISK` to a number from `0` to `100` to
make the pre-execution gate deny actions at or above that risk; leave it unset for observe-only
rollout. This is intended to be enabled gradually with a real credential issuance workflow.

## Assurance envelopes

Every completed gateway invocation now compiles its ledger intent, policy decision, final result,
identity context, and assurance assessment into a redacted `v1` assurance envelope. It carries
hashes, receipts, and identifiers—not raw arguments or outputs. In private A2Z SOC mode the
gateway posts the final envelope to `POST /api/grc/assurance` under the bridge tenant; in demo
mode the response truthfully reports `not_configured` for hosted persistence.

## Hardening checklist (operators)

- [ ] `GRC_CLAW_GATEWAY_TOKEN` from secret manager, not git
- [ ] Gateway bound to loopback or private VLAN
- [ ] `A2Z_SOC_API_KEY` scoped to ingest + GRC read, not user admin
- [ ] Docker sandbox image pinned by digest
- [ ] Approval workflow enabled for Tier Write/Destructive in production
- [ ] `GRC_CLAW_ASSURANCE_MAX_RISK` calibrated in a staging tenant before enforcement
- [ ] Weekly `npm run doctor` (config + token smoke test)

## Differentiator vs generic “AI GRC” bots

| Generic chatbot | GRC_Claw agent runtime |
|-----------------|------------------------|
| Browser plugin with full DOM | Gateway-mediated tools only |
| Optional guardrails | Mandatory exec policy |
| Cloud LLM by default | Pluggable; A2Z SOC private route |
| No SOC correlation | `a2z-connector` maps events → controls |

**Positioning for A2Z SOC:** *Your SOC detects; GRC_Claw explains compliance impact—with agents that cannot bypass your gateway.*
