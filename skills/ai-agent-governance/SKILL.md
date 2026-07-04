---
name: ai-agent-governance
description: Register an autonomous agent's identity, check a runtime policy decision before it acts, and log a hash-chained attestation of what it did. Backed by A2Z SOC's live Agent Registry, Policy Firewall, and Attestation Ledger.
homepage: https://github.com/AAH20/GRC_Claw
user-invocable: true
disable-model-invocation: false
---

# AI Agent Governance

Most agent frameworks let an autonomous agent act without any independent record of who it is, what it's allowed to do, or whether a specific action was checked against policy before it happened. This skill gives an agent (or the human operating it) three things, backed by real, live endpoints, not local state that disappears when the process exits:

1. A cryptographic identity for the agent, distinct from its API key or wallet.
2. A runtime policy check before a risky action, evaluated independently of the model making the decision.
3. A hash-chained, independently verifiable record of what the agent actually did.

## When to use this

Use this skill whenever an agent is about to take an action with real consequences, calling an external API that spends money, modifying infrastructure, sending an email or message on someone's behalf, or making a decision that should be auditable later. Do not use it for read-only, no-consequence actions like answering a question.

## 1. Register the agent (once, per agent)

```bash
curl -s -X POST https://a2zsoc.com/api/platform/agent-registry \
  -H 'Content-Type: application/json' \
  -d '{
    "action": "register",
    "orgId": "<your-org-id>",
    "agentName": "<descriptive-agent-name>",
    "agentType": "autonomous",
    "ownerEmail": "<your-email>",
    "scopeOfAuthority": ["<what this agent is allowed to affect>"],
    "allowedTools": ["<tool-1>", "<tool-2>"],
    "dataAccessLevel": "restricted",
    "riskTier": "limited"
  }'
```

This returns an `agent.id` (a DID-backed cryptographic identity) and `agent.trust_score`. Store the `agent.id` for the two calls below. Register once per distinct agent, not once per action.

## 2. Check policy before acting

Before the agent executes a consequential action, evaluate it against policy:

```bash
curl -s -X POST https://a2zsoc.com/api/platform/agent-firewall \
  -H 'Content-Type: application/json' \
  -d '{
    "action": "evaluate",
    "orgId": "<your-org-id>",
    "agentId": "<agent-id-from-step-1>",
    "requestedAction": "<the specific tool or action about to run>",
    "actionPayload": { "...": "whatever context makes the decision inspectable later" }
  }'
```

Response is `{ "decision": "allow" | "deny" | "require_approval", "reason": "..." }`. If `decision` is not `allow`, the agent must not proceed, escalate to a human or stop.

## 3. Log the attestation after acting

Once the action completes (or is blocked), write a hash-chained record of it:

```bash
curl -s -X POST https://a2zsoc.com/api/platform/agent-attestation \
  -H 'Content-Type: application/json' \
  -d '{
    "action": "record",
    "orgId": "<your-org-id>",
    "agentId": "<agent-id-from-step-1>",
    "actionType": "<short type, e.g. deploy | send_email | spend>",
    "actionSummary": "<one line, human-readable>",
    "actionPayload": { "...": "same context as the policy check" }
  }'
```

Each entry is chained to the previous one via SHA-256, so the sequence can be independently verified later with `{"action": "verify_chain", "agentId": "..."}` against the same endpoint, not just trusted on the agent's own say-so.

## Why this matters

An agent that can act without an independent identity, a policy check outside its own reasoning, and a tamper-evident log of what it did is a liability the moment it's trusted with anything real, spending money, touching infrastructure, or acting on someone's behalf. This skill is the minimum governance layer for that, three API calls, no local state to lose, and a ledger nobody, including the agent itself, can quietly rewrite after the fact.

Full platform: [a2zsoc.com](https://a2zsoc.com). Open-source engine underneath it: [github.com/AAH20/GRC_Claw](https://github.com/AAH20/GRC_Claw), MIT licensed.
