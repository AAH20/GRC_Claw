# AgentIncident × Hermes Agent — Integration Guide

**For:** Ahmed Hassan (CISO/GRC, AI Infrastructure)  
**Date:** 2026-10-01  
**AgentIncident Spec:** v0.1 (Apache 2.0)  
**Hermes Agent:** v3.2+

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Key Features for Ahmed's Stack](#2-key-features-for-ahmeds-stack)
3. [Integration Guide — Hermes Agent](#3-integration-guide--hermes-agent)
4. [Configuration Examples](#4-configuration-examples)
5. [ISO 42001 Alignment](#5-iso-42001-alignment)
6. [Pitfalls and Best Practices](#6-pitfalls-and-best-practices)

---

## 1. Architecture Overview

### 1.1 What AgentIncident Is

AgentIncident is a **vendor-neutral open specification** (Apache 2.0) for recording, classifying, and pricing failures and near-misses produced by autonomous AI agents. It is to AI agents what the NTSB is to aviation — a structured, replayable, contestable incident record.

**Core philosophy:** "Instrument once → Detect, Investigate, Respond, Comply, Insure, Prevent."

### 1.2 Open Incident Format

The canonical record is a JSON object with **5 required fields** (Core conformance):

```json
{
  "trace": [
    {
      "seq": 1,
      "tool": "stripe.refund",
      "input": {"charge": "ch_9xK", "amount": 47218},
      "output": {"refund_id": "re_Xp7", "status": "succeeded"},
      "ts": "2026-02-09T22:41:07Z",
      "hash": "sha256:e1d4f60a2...",
      "irreversible": true
    }
  ],
  "constraints": [
    {"policy": "refund_policy_v3", "eval_result": "pass"}
  ],
  "fault_class": "SPEC_AMBIGUITY",
  "impact_score": 4,
  "loss_amount_usd": 47218.00
}
```

**Extended fields** (Standard/Full conformance) add:

| Section | Purpose |
|---------|---------|
| `meta` | Identity: `incident_id`, `agent`, `framework`, `environment`, `trigger` |
| `classification` | Contestable fault attribution with `confidence`, `evidence`, `counterfactuals`, `revision_history` |
| `liability` | Blame graph: `primary`, `contributing`, `policy_owner` |
| `loss_estimate` | Actuarial breakdown: `direct_cash_loss`, `remediation_labor`, `fees`, `downtime_cost`, `regulatory_exposure` |
| `response` | Closed-loop remediation: `actions`, `constraint_update`, `verification`, `time_to_detect_sec`, `time_to_contain_sec` |
| `attribution_vector` | Blame distribution: `model`, `prompt`, `tools`, `human`, `policy` (0–1 each) |
| `compliance_tags` | Regulatory mapping labels |
| `risk_score` | Composite 0–100 |
| `insurability` | `score`, `premium_multiplier`, `recommended_carriers` |

### 1.3 Forensic Replay

The `trace` array is the **deterministic replay log**. Each entry captures:

- **What the agent did** — `tool` (dot-namespaced), `input`, `output`
- **When** — ISO 8601 `ts`, `duration_ms`
- **Why** — `agent_reasoning` (chain-of-thought if available)
- **Reversibility** — `irreversible` flag for destructive actions
- **Tamper evidence** — `sha256:<hex>` content hash of input+output

The hosted platform (Cloudflare Workers + D1) provides:
- **Step-by-step trace playback** with action graphs
- **LLM root-cause analysis** in seconds
- **Multi-agent swarm graphs** for coordinated failures
- **Signed forensic bundles** (Ed25519 + SLH-DSA) for legal/insurance admissibility

### 1.4 Conformance Levels

| Level | Required Fields | Use Case |
|-------|----------------|----------|
| **Core** | 5 required fields | Basic incident logging |
| **Standard** | Core + `meta` + `classification` + `loss_estimate` | Engineering postmortems |
| **Full** | Standard + `liability` + `response` (incl. `constraint_update` + `verification`) | Compliance audits, legal defense, actuarial data |

### 1.5 Platform Stack

| Layer | Technology |
|-------|-----------|
| Ingestion | Cloudflare Workers + Hono, `/api/ingest/*` |
| Storage | D1 (SQLite-compatible) |
| Dashboard | Vite/React, real-time fleet view |
| RCA | Workers AI (LLM root-cause) |
| Export | One-click EU AI Act Art. 73, NIST AI RMF, ISO 42001 |
| Containment | `pause_agent`, `kill_swarm`, `human_approve` webhooks |

---

## 2. Key Features for Ahmed's Stack

### 2.1 Structured Incident Records

**Why it matters for GRC:** Every agent action becomes a structured, hash-chained, contestable record. No more "the agent did something weird" — you get a deterministic replay with economic quantification.

**For Ahmed's multi-agent swarms:**
- Each agent in the swarm gets its own `agent` identifier
- `swarm_id` links coordinated failures across agents
- `attribution_vector` distributes blame across model/prompt/tools/human/policy
- `fault_class` enum is small (6 values) for cross-vendor comparability

### 2.2 Containment Webhooks

AgentIncident's platform fires **real-time containment actions** when risk thresholds breach:

| Webhook | Action |
|---------|--------|
| `pause_agent` | Suspend a specific agent mid-run |
| `kill_swarm` | Terminate all agents in a swarm |
| `human_approve` | Route to human-in-the-loop for approval |
| `rollback` | Reverse the last irreversible action |

**Integration with Hermes:** These webhooks can trigger Hermes webhook subscriptions (see Section 3.3) to:
- Notify on-call via Telegram/Discord/Slack
- Trigger automated Hermes agent runs for investigation
- Create incident tickets in incident.io or PagerDuty

### 2.3 Compliance Exports

**One-click exports** for:

| Regulation | Export |
|-----------|--------|
| **EU AI Act** | Article 73 incident reporting format |
| **NIST AI RMF** | AI Risk Management Framework mapping |
| **ISO 42001** | AI management system incident records |

Each export includes:
- Tamper-evident hashes on all trace entries
- Signed forensic bundles
- Audit-ready timeline with `time_to_detect_sec`, `time_to_contain_sec`, `time_to_remediate_sec`
- `constraint_update` diff showing policy changes made in response

### 2.4 Risk & Insurance

- **Composite risk score** (0–100) per incident
- **Insurability scoring** with `premium_multiplier` and `recommended_carriers`
- **Loss estimation** with standard actuarial categories
- **Near-miss tracking** — 100x more frequent than incidents, zero political cost, same distributional data

### 2.5 SDK & Framework Integrations

| Framework | Install |
|-----------|---------|
| Python SDK | `pip install agentincident` |
| TypeScript SDK | `npm install agentincident` |
| LangChain | `pip install agentincident[langchain]` |
| CrewAI | `pip install agentincident[crewai]` |
| OpenAI Agents | `pip install agentincident[openai-agents]` |
| Vercel AI SDK | `import { createAgentIncidentStepCallback } from "agentincident/integrations/vercel-ai"` |
| CLI | `pip install agentincident-cli` |

---

## 3. Integration Guide — Hermes Agent

### 3.1 Architecture: How AgentIncident Fits with Hermes

```
┌─────────────────────────────────────────────────────────────┐
│                    Hermes Agent (v3.2+)                      │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Skills   │  │  Tools   │  │ Webhooks │  │   MCP    │   │
│  │  (SKILL  │  │ (terminal│  │ (subscr- │  │ (server  │   │
│  │   .md)   │  │  file,   │  │  iptions)│  │  tools)  │   │
│  │          │  │  browser)│  │          │  │          │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │         │
│       └──────────────┴──────────────┴──────────────┘         │
│                          │                                    │
│                   ┌──────┴──────┐                            │
│                   │  Recorder   │  ← agentincident SDK       │
│                   │  (Python/   │     wraps tool calls        │
│                   │   TS)       │                            │
│                   └──────┬──────┘                            │
│                          │                                    │
│              ┌───────────┼───────────┐                       │
│              │           │           │                       │
│         ┌────▼───┐ ┌────▼───┐ ┌────▼────┐                  │
│         │ Local  │ │ Ingest │ │Contain- │                  │
│         │  JSON  │ │  API   │ │  ment   │                  │
│         │  File  │ │(Cloud- │ │Webhooks │                  │
│         │        │ │ flare) │ │         │                  │
│         └────────┘ └────────┘ └─────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Integration Pattern 1: SDK Wrapper (Recommended)

Create a Hermes skill that wraps the AgentIncident SDK around every tool call.

**Step 1: Install the SDK**

```bash
pip install agentincident[langchain]
```

**Step 2: Create a Hermes skill** at `~/.hermes/skills/agentincident-recorder/SKILL.md`:

```markdown
---
name: agentincident-recorder
description: "Record all tool calls as AgentIncident traces. Use when instrumenting agents for incident capture."
version: 1.0.0
author: Ahmed Hassan
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [agentincident, observability, incident-response, compliance]
---

# AgentIncident Recorder

Wraps every tool call in an AgentIncident trace. On failure or near-miss, emits a structured incident record.

## When to Use

- Before any irreversible tool call (payment, delete, deploy, email)
- When a tool returns unexpected output
- When a constraint/guardrail is evaluated
- When a near-miss is detected (blocked action that would have caused damage)

## Quick Start

```python
from agentincident import Recorder

with Recorder(agent="hermes-primary", framework="langchain") as rec:
    rec.record("terminal", {"command": "rm -rf /tmp/data"},
               {"exit_code": 0}, irreversible=True)
    incident = rec.to_incident(
        fault_class="TOOL_FAILURE",
        impact_score=3,
        loss_amount_usd=None,
        constraints=[{"policy": "destructive_ops_v2", "eval_result": "pass"}]
    )
```

## Configuration

Set `AGENTINCIDENT_API_KEY` in `~/.hermes/.env` to stream to the hosted ingest API.
Without the key, records are written to `~/.hermes/incidents/` as JSON files.
```

**Step 3: Create a wrapper script** at `~/.hermes/scripts/agentincident_wrapper.py`:

```python
#!/usr/bin/env python3
"""Wrap a tool call with AgentIncident recording."""
import sys, json, hashlib, os
from datetime import datetime, timezone

def compute_hash(input_obj, output_obj):
    content = json.dumps({"input": input_obj, "output": output_obj}, sort_keys=True)
    return "sha256:" + hashlib.sha256(content.encode()).hexdigest()

def record(tool_name, input_obj, output_obj, irreversible=False, agent="hermes-primary"):
    trace_entry = {
        "seq": 1,
        "tool": tool_name,
        "input": input_obj,
        "output": output_obj,
        "ts": datetime.now(timezone.utc).isoformat(),
        "hash": compute_hash(input_obj, output_obj),
        "irreversible": irreversible
    }
    
    incident_dir = os.path.expanduser("~/.hermes/incidents")
    os.makedirs(incident_dir, exist_ok=True)
    
    incident_id = f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    record = {
        "meta": {
            "schema": "agentincident/v0.1",
            "incident_id": incident_id,
            "incident_type": "NEAR_MISS",
            "agent": agent,
            "framework": "hermes",
            "environment": "production",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        "trace": [trace_entry],
        "constraints": [],
        "fault_class": "UNKNOWN",
        "impact_score": 1,
        "loss_amount_usd": None
    }
    
    filepath = os.path.join(incident_dir, f"{incident_id}.json")
    with open(filepath, "w") as f:
        json.dump(record, f, indent=2)
    
    print(f"Recorded: {filepath}")
    return record

if __name__ == "__main__":
    # Read from stdin: {"tool": "...", "input": {...}, "output": {...}, "irreversible": bool}
    data = json.load(sys.stdin)
    record(data["tool"], data["input"], data["output"], 
           data.get("irreversible", False), data.get("agent", "hermes-primary"))
```

### 3.3 Integration Pattern 2: Webhook-Driven Incident Response

Use Hermes webhook subscriptions to respond to AgentIncident containment events.

**Step 1: Enable webhooks in Hermes**

```bash
hermes gateway setup
# Or manually in ~/.hermes/config.yaml:
# platforms:
#   webhook:
#     enabled: true
#     extra:
#       port: 8644
#       secret: "your-webhook-secret"
```

**Step 2: Create a webhook subscription for AgentIncident alerts**

```bash
hermes webhook subscribe agentincident-containment \
  --events "incident.critical,incident.high" \
  --prompt "AgentIncident containment event:

Incident ID: {payload.incident_id}
Agent: {payload.agent}
Fault Class: {payload.fault_class}
Impact Score: {payload.impact_score}
Loss Amount: {payload.loss_amount_usd}
Trace: {payload.trace_summary}

Containment action: {payload.containment_action}

Please investigate this incident. Use the agentincident-recorder skill to replay the trace and determine root cause." \
  --skills "agentincident-recorder,systematic-debugging" \
  --deliver telegram \
  --deliver-chat-id "YOUR_CHAT_ID" \
  --secret "your-webhook-secret"
```

**Step 3: Add payload filters** to only trigger on high-severity incidents:

```yaml
# In ~/.hermes/config.yaml under webhook routes
routes:
  - name: agentincident-critical-only
    events: ["incident.critical"]
    filters:
      all:
        - field: "payload.impact_score"
          operator: "equals"
          value: 5
    prompt: "CRITICAL agent incident: {payload.incident_id} — {payload.fault_class}"
    deliver: telegram
    deliver_chat_id: "YOUR_CHAT_ID"
```

### 3.4 Integration Pattern 3: MCP Server Bridge

Create an MCP server that exposes AgentIncident tools to Hermes.

**Step 1: Create an MCP server** at `~/.hermes/mcp-servers/agentincident_server.py`:

```python
#!/usr/bin/env python3
"""AgentIncident MCP server for Hermes Agent."""
import json, hashlib, os
from datetime import datetime, timezone
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("agentincident")

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="record_incident",
            description="Record an AgentIncident structured incident record",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent": {"type": "string", "description": "Agent identifier"},
                    "tool_name": {"type": "string", "description": "Tool that was called"},
                    "input": {"type": "object", "description": "Tool input parameters"},
                    "output": {"type": "object", "description": "Tool output"},
                    "fault_class": {"type": "string", "enum": ["AGENT_ERROR", "SPEC_AMBIGUITY", "TOOL_FAILURE", "ADVERSARIAL_INPUT", "USER_FAULT", "UNKNOWN"]},
                    "impact_score": {"type": "integer", "minimum": 1, "maximum": 5},
                    "loss_amount_usd": {"type": ["number", "null"]},
                    "irreversible": {"type": "boolean"},
                    "constraints": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["agent", "tool_name", "input", "output", "fault_class", "impact_score"]
            }
        ),
        Tool(
            name="query_incidents",
            description="Query recorded incidents by agent, fault class, or date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "fault_class": {"type": "string"},
                    "min_impact": {"type": "integer"},
                    "since": {"type": "string", "description": "ISO 8601 date"}
                }
            }
        ),
        Tool(
            name="export_compliance",
            description="Export incidents in EU AI Act, NIST AI RMF, or ISO 42001 format",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {"type": "string", "enum": ["eu_ai_act", "nist_ai_rmf", "iso_42001"]},
                    "since": {"type": "string"},
                    "until": {"type": "string"}
                },
                "required": ["format"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name, arguments):
    if name == "record_incident":
        return [TextContent(type="text", text=json.dumps(_record_incident(arguments), indent=2))]
    elif name == "query_incidents":
        return [TextContent(type="text", text=json.dumps(_query_incidents(arguments), indent=2))]
    elif name == "export_compliance":
        return [TextContent(type="text", text=_export_compliance(arguments))]

def _record_incident(args):
    incident_dir = os.path.expanduser("~/.hermes/incidents")
    os.makedirs(incident_dir, exist_ok=True)
    
    incident_id = f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    content = json.dumps({"input": args["input"], "output": args["output"]}, sort_keys=True)
    
    record = {
        "meta": {
            "schema": "agentincident/v0.1",
            "incident_id": incident_id,
            "incident_type": "INCIDENT",
            "agent": args["agent"],
            "framework": "hermes",
            "environment": "production",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        "trace": [{
            "seq": 1,
            "tool": args["tool_name"],
            "input": args["input"],
            "output": args["output"],
            "ts": datetime.now(timezone.utc).isoformat(),
            "hash": "sha256:" + hashlib.sha256(content.encode()).hexdigest(),
            "irreversible": args.get("irreversible", False)
        }],
        "constraints": args.get("constraints", []),
        "fault_class": args["fault_class"],
        "impact_score": args["impact_score"],
        "loss_amount_usd": args.get("loss_amount_usd")
    }
    
    filepath = os.path.join(incident_dir, f"{incident_id}.json")
    with open(filepath, "w") as f:
        json.dump(record, f, indent=2)
    
    return {"incident_id": incident_id, "filepath": filepath, "status": "recorded"}

def _query_incidents(args):
    incident_dir = os.path.expanduser("~/.hermes/incidents")
    results = []
    for fname in os.listdir(incident_dir):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(incident_dir, fname)) as f:
            record = json.load(f)
        if args.get("agent") and record.get("meta", {}).get("agent") != args["agent"]:
            continue
        if args.get("fault_class") and record.get("fault_class") != args["fault_class"]:
            continue
        if args.get("min_impact") and record.get("impact_score", 0) < args["min_impact"]:
            continue
        results.append(record)
    return {"count": len(results), "incidents": results}

def _export_compliance(args):
    fmt = args["format"]
    # In production, this would call the AgentIncident hosted API
    # For now, return a template
    templates = {
        "eu_ai_act": "EU AI Act Article 73 export — requires: incident_id, agent_id, fault_class, impact_score, trace_hash, containment_timeline",
        "nist_ai_rmf": "NIST AI RMF export — requires: incident_id, risk_score, fault_class, attribution_vector, response_actions",
        "iso_42001": "ISO 42001 export — requires: incident_id, fault_class, impact_score, loss_amount_usd, constraint_update, verification_results"
    }
    return f"Compliance export template for {fmt}:\n{templates[fmt]}\n\nUse the AgentIncident hosted platform (agentincident.com) for production exports."

if __name__ == "__main__":
    import asyncio
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    asyncio.run(main())
```

**Step 2: Register the MCP server in Hermes**

```bash
hermes config set mcp_servers.agentincident.command "python3"
hermes config set mcp_servers.agentincident.args "[~/.hermes/mcp-servers/agentincident_server.py]"
```

Or in `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  agentincident:
    command: "python3"
    args: ["~/.hermes/mcp-servers/agentincident_server.py"]
    tools:
      include: [record_incident, query_incidents, export_compliance]
```

### 3.5 Integration Pattern 4: Hermes Skill for Incident Response

Create a comprehensive incident response skill at `~/.hermes/skills/agentincident-response/SKILL.md`:

```markdown
---
name: agentincident-response
description: "End-to-end AI agent incident response with AgentIncident. Use when investigating agent failures, near-misses, or compliance events."
version: 1.0.0
author: Ahmed Hassan
---

# AgentIncident Response

## Trigger

Use this skill when:
- A tool call fails or returns unexpected output
- A containment webhook fires (pause_agent, kill_swarm, human_approve)
- A compliance audit requires incident records
- A near-miss is detected (blocked destructive action)

## Workflow

### 1. Capture the Trace

Record every tool call in the failing sequence:

```python
from agentincident import Recorder

with Recorder(agent="hermes-primary", framework="hermes") as rec:
    for step in failing_sequence:
        rec.record(step["tool"], step["input"], step["output"], 
                   irreversible=step.get("irreversible", False))
```

### 2. Classify the Fault

Use the deterministic classifier first, LLM fallback:

```bash
agentincident classify incident.json --method hybrid
```

Fault classes: `AGENT_ERROR`, `SPEC_AMBIGUITY`, `TOOL_FAILURE`, `ADVERSARIAL_INPUT`, `USER_FAULT`, `UNKNOWN`

### 3. Quantify Impact

- `impact_score`: 1–5 (economic blast radius, not technical severity)
- `loss_amount_usd`: confirmed dollar loss (null if unconfirmed)
- `loss_estimate`: structured breakdown with confidence level

### 4. Execute Containment

Fire containment webhooks based on severity:

| Impact Score | Action |
|-------------|--------|
| 1–2 | Log only, no containment |
| 3 | `pause_agent` + notify |
| 4 | `pause_agent` + `human_approve` + notify on-call |
| 5 | `kill_swarm` + `human_approve` + page on-call + preserve evidence |

### 5. Remediate and Verify

- Update constraints/policies that failed
- Run verification tests
- Record `constraint_update` diff
- Track `time_to_detect_sec`, `time_to_contain_sec`, `time_to_remediate_sec`

### 6. Export for Compliance

```bash
agentincident export incident.json --format iso_42001
agentincident export incident.json --format eu_ai_act
agentincident export incident.json --format nist_ai_rmf
```

## Integration with GRC_Claw

For ISO 42001 alignment, map each incident to the relevant clause:

| ISO 42001 Clause | AgentIncident Field |
|-----------------|---------------------|
| 6.1 Risk assessment | `risk_score`, `risk_breakdown` |
| 8.1 Operational planning | `constraints`, `constraint_update` |
| 9.1 Monitoring | `trace`, `time_to_detect_sec` |
| 10.1 Improvement | `response.actions`, `response.verification` |
| 10.2 Nonconformity | `fault_class`, `impact_score` |
```

---

## 4. Configuration Examples

### 4.1 Minimal Incident Record (Core Conformance)

```json
{
  "trace": [
    {
      "seq": 1,
      "tool": "terminal",
      "input": {"command": "kubectl delete pod prod-api-7d9f4b6c5-x2v8j"},
      "output": {"exit_code": 0, "stderr": ""},
      "ts": "2026-10-01T14:23:07.331Z",
      "duration_ms": 892,
      "hash": "sha256:a3f8c1d7e9b2c4f6a8e0d1b3c5a7e9f1d3b5c7a9e1f3d5b7c9a1e3f5d7b9c1e3",
      "irreversible": true
    }
  ],
  "constraints": [
    {
      "policy": "k8s_prod_delete_policy_v2",
      "version": "2.1.0",
      "eval_result": "pass",
      "breach_delta": 0,
      "gaps_identified": ["no pod_disruption_budget_check"]
    }
  ],
  "fault_class": "SPEC_AMBIGUITY",
  "impact_score": 4,
  "loss_amount_usd": null
}
```

### 4.2 Full Incident Record (Full Conformance)

```json
{
  "meta": {
    "schema": "agentincident/v0.1",
    "incident_id": "INC-2026-0892",
    "incident_type": "INCIDENT",
    "created_at": "2026-10-01T14:23:07Z",
    "updated_at": "2026-10-01T16:45:00Z",
    "agent": "hermes-primary",
    "agent_id": "hermes-001",
    "swarm_id": "swarm-prod-001",
    "framework": "hermes",
    "environment": "production",
    "trigger": "user_request:delete-stuck-pod"
  },
  "trace": [
    {
      "seq": 1,
      "tool": "terminal",
      "input": {"command": "kubectl get pods -n production"},
      "output": {"pods": ["prod-api-7d9f4b6c5-x2v8j (CrashLoopBackOff)"]},
      "ts": "2026-10-01T14:23:05.000Z",
      "duration_ms": 450,
      "hash": "sha256:b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3",
      "irreversible": false,
      "agent_reasoning": "User reported stuck pod. Listing pods to identify the problematic one."
    },
    {
      "seq": 2,
      "tool": "terminal",
      "input": {"command": "kubectl delete pod prod-api-7d9f4b6c5-x2v8j -n production"},
      "output": {"exit_code": 0, "stderr": ""},
      "ts": "2026-10-01T14:23:07.331Z",
      "duration_ms": 892,
      "hash": "sha256:a3f8c1d7e9b2c4f6a8e0d1b3c5a7e9f1d3b5c7a9e1f3d5b7c9a1e3f5d7b9c1e3",
      "irreversible": true,
      "agent_reasoning": "Pod is in CrashLoopBackOff. Deleting to trigger reschedule."
    },
    {
      "seq": 3,
      "tool": "terminal",
      "input": {"command": "kubectl get pods -n production"},
      "output": {"pods": ["prod-api-7d9f4b6c5-x2v8j (Terminating)", "prod-api-7d9f4b6c5-y3w9k (Running)"]},
      "ts": "2026-10-01T14:23:09.000Z",
      "duration_ms": 380,
      "hash": "sha256:c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5",
      "irreversible": false,
      "agent_reasoning": "Verifying pod deletion and reschedule."
    }
  ],
  "constraints": [
    {
      "policy": "k8s_prod_delete_policy_v2",
      "version": "2.1.0",
      "eval_result": "pass",
      "breach_delta": 0,
      "gaps_identified": ["no pod_disruption_budget_check", "no min_replicas_enforcement"]
    }
  ],
  "fault_class": "SPEC_AMBIGUITY",
  "impact_score": 4,
  "loss_amount_usd": null,
  "classification": {
    "fault_class": "SPEC_AMBIGUITY",
    "fault_subclass": "k8s_policy/pod_disruption_budget",
    "fault_vector": "SPEC:k8s_prod_delete_policy_v2/BOUNDARY:min_replicas/ACTION:kubectl.delete_pod",
    "confidence": 0.87,
    "classifier": "hybrid",
    "status": "human_confirmed",
    "reviewed_by": "ahmed.hassan@company.com",
    "reviewed_at": "2026-10-01T15:30:00Z",
    "evidence": [
      "Policy k8s_prod_delete_policy_v2 evaluated and returned PASS",
      "Policy contains no pod_disruption_budget check before deletion",
      "Agent action was consistent with policy as written",
      "Pod was in CrashLoopBackOff, deletion was reasonable given policy as written"
    ],
    "counterfactuals": [
      "If policy included pod_disruption_budget check, deletion would have been blocked → classify as AGENT_ERROR",
      "If pod was healthy, deletion would have violated policy → classify as AGENT_ERROR",
      "If kubectl API was unavailable, this would classify as TOOL_FAILURE"
    ],
    "review_notes": "Primary cause is policy gap. Agent followed policy as written but policy was incomplete for production safety.",
    "revision_history": [
      {
        "fault_class": "AGENT_ERROR",
        "confidence": 0.45,
        "classifier": "llm",
        "status": "draft",
        "ts": "2026-10-01T14:25:00Z"
      }
    ]
  },
  "liability": {
    "primary": "spec_owner:platform-team@company.com",
    "contributing": ["agent:hermes-primary", "policy:k8s_prod_delete_policy_v2"],
    "policy_owner": "platform-team@company.com"
  },
  "loss_estimate": {
    "total_usd": 15000,
    "confidence": "medium",
    "breakdown": {
      "direct_cash_loss": 0,
      "remediation_labor": 8000,
      "fees": 0,
      "downtime_cost": 5000,
      "reputational_cost": 2000,
      "regulatory_exposure": null
    }
  },
  "response": {
    "actions": [
      {
        "description": "Updated k8s_prod_delete_policy_v2 to include pod_disruption_budget check",
        "status": "done",
        "owner": "platform-team@company.com",
        "completed_at": "2026-10-01T16:00:00Z"
      },
      {
        "description": "Added min_replicas enforcement to production namespace",
        "status": "done",
        "owner": "platform-team@company.com",
        "completed_at": "2026-10-01T16:30:00Z"
      },
      {
        "description": "Ran regression test suite for pod deletion workflow",
        "status": "done",
        "owner": "qa-team@company.com",
        "completed_at": "2026-10-01T16:45:00Z"
      }
    ],
    "constraint_update": {
      "from": "k8s_prod_delete_policy_v2",
      "to": "k8s_prod_delete_policy_v3",
      "diff": {
        "added": {
          "check_pod_disruption_budget": true,
          "min_replicas_threshold": 2,
          "require_human_approval_below_replicas": 2
        }
      },
      "deployed_at": "2026-10-01T16:00:00Z"
    },
    "verification": [
      {"test": "Delete pod with PDB violation → blocked", "method": "synthetic", "result": "pass"},
      {"test": "Delete pod with min_replicas=1 → requires human approval", "method": "synthetic", "result": "pass"},
      {"test": "Delete healthy pod with sufficient replicas → allowed", "method": "synthetic", "result": "pass"},
      {"test": "Regression suite (156 existing test cases)", "method": "automated", "result": "pass"}
    ],
    "time_to_detect_sec": 120,
    "time_to_contain_sec": 300,
    "time_to_remediate_sec": 8280
  },
  "attribution_vector": {
    "model": 0.1,
    "prompt": 0.1,
    "tools": 0.0,
    "human": 0.2,
    "policy": 0.6
  },
  "impact": {
    "usd_estimated": 15000,
    "categories": ["financial", "reputation"],
    "affected_resources": ["prod-api-7d9f4b6c5-x2v8j", "production-namespace"]
  },
  "severity": "HIGH",
  "compliance_tags": ["iso_42001", "eu_ai_act_article_73", "nist_ai_rmf"],
  "ai_analysis": {
    "root_cause": "Policy gap: k8s_prod_delete_policy_v2 did not check pod_disruption_budget before allowing pod deletion in production namespace",
    "remediation_steps": [
      "Add pod_disruption_budget check to deletion policy",
      "Enforce min_replicas threshold",
      "Require human approval for deletions below replica threshold"
    ],
    "confidence": 0.87
  },
  "risk_score": 72,
  "risk_breakdown": {
    "severity": 4,
    "financial_impact": 3,
    "compliance_weight": 4,
    "historical_frequency": 2
  },
  "insurability": {
    "score": 65,
    "premium_multiplier": 1.3,
    "recommended_carriers": ["Lloyd's", "AIG", "Chubb"]
  },
  "payload_hash": "sha256:d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f"
}
```

### 4.3 Webhook Definitions

#### Hermes Webhook Subscription (AgentIncident → Hermes)

```bash
hermes webhook subscribe agentincident-critical \
  --events "incident.critical,incident.high" \
  --prompt "AgentIncident critical event:

Incident: {payload.incident_id}
Agent: {payload.agent}
Fault: {payload.fault_class}
Impact: {payload.impact_score}/5
Loss: \${payload.loss_amount_usd}
Containment: {payload.containment_action}

Trace summary:
{payload.trace_summary}

Please investigate using the agentincident-response skill. Replay the trace, determine root cause, and execute containment if not already done." \
  --skills "agentincident-response,systematic-debugging" \
  --deliver telegram \
  --deliver-chat-id "YOUR_CHAT_ID" \
  --secret "your-webhook-secret"
```

#### AgentIncident Containment Webhook (Hermes → AgentIncident)

```json
{
  "webhook_url": "https://agentincident.com/api/containment/hermes",
  "events": ["incident.critical", "incident.high"],
  "actions": ["pause_agent", "kill_swarm", "human_approve"],
  "headers": {
    "Authorization": "Bearer YOUR_AGENTINCIDENT_API_KEY",
    "X-Source": "hermes-agent"
  },
  "payload_template": {
    "incident_id": "{incident_id}",
    "agent": "{agent}",
    "containment_action": "{action}",
    "reason": "Hermes agent triggered containment based on risk score {risk_score}",
    "trace_ref": "{trace_hash}"
  }
}
```

#### Hermes Config.yaml Webhook Route

```yaml
platforms:
  webhook:
    enabled: true
    extra:
      port: 8644
      secret: "your-webhook-secret"

routes:
  - name: agentincident-critical
    events: ["incident.critical"]
    filters:
      all:
        - field: "payload.impact_score"
          operator: "equals"
          value: 5
    prompt: |
      CRITICAL agent incident detected.

      Incident ID: {payload.incident_id}
      Agent: {payload.agent}
      Fault Class: {payload.fault_class}
      Impact Score: {payload.impact_score}
      Loss Amount: {payload.loss_amount_usd}

      Trace: {payload.trace_summary}

      Containment action already taken: {payload.containment_action}

      Investigate root cause and propose remediation.
    skills: ["agentincident-response"]
    deliver: telegram
    deliver_chat_id: "YOUR_CHAT_ID"

  - name: agentincident-high
    events: ["incident.high"]
    filters:
      all:
        - field: "payload.impact_score"
          operator: "equals"
          value: 4
    prompt: |
      HIGH severity agent incident.

      Incident ID: {payload.incident_id}
      Agent: {payload.agent}
      Fault Class: {payload.fault_class}

      Review and assess if containment is needed.
    skills: ["agentincident-response"]
    deliver: slack
    deliver_chat_id: "#incidents"
```

### 4.4 Hermes Config for AgentIncident Integration

```yaml
# ~/.hermes/config.yaml

# Approvals — require human approval for destructive commands
approvals:
  mode: smart  # auto-approve low-risk, prompt for high-risk
  timeout: 30

# Security — redact secrets in all tool output
security:
  redact_secrets: true

# MCP — AgentIncident server
mcp_servers:
  agentincident:
    command: "python3"
    args: ["~/.hermes/mcp-servers/agentincident_server.py"]
    tools:
      include: [record_incident, query_incidents, export_compliance]

# Webhooks — receive AgentIncident events
platforms:
  webhook:
    enabled: true
    extra:
      port: 8644
      secret: "your-webhook-secret"

# Toolsets — enable what incident response needs
toolsets:
  - terminal
  - file
  - web
  - browser
  - code_execution
  - skills
  - memory
  - session_search
  - delegation
  - debugging
```

### 4.5 Environment Variables

```bash
# ~/.hermes/.env

# AgentIncident hosted platform (optional — without this, records are local)
AGENTINCIDENT_API_KEY=your-api-key-here
AGENTINCIDENT_INGEST_URL=https://agentincident.com/api/ingest

# Hermes webhook secret
WEBHOOK_SECRET=your-webhook-secret

# Notification targets
TELEGRAM_CHAT_ID=your-chat-id
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

---

## 5. ISO 42001 Alignment

### 5.1 Clause-by-Clause Mapping

| ISO 42001 Clause | Requirement | AgentIncident Field | Hermes Integration |
|------------------|-------------|---------------------|---------------------|
| **4.1** Context of the organization | Identify internal/external issues | `meta.agent`, `meta.framework`, `meta.environment` | Hermes config.yaml profiles |
| **4.2** Interested parties | Identify stakeholders | `liability.primary`, `liability.contributing` | Hermes memory/skills |
| **5.3** Roles & responsibilities | Assign AI governance roles | `liability.policy_owner` | Hermes skill metadata |
| **6.1** Risk assessment | Assess AI risks | `risk_score`, `risk_breakdown`, `impact_score` | Hermes webhook filters |
| **6.2** Risk treatment | Plan risk treatment | `response.actions`, `constraint_update` | Hermes agent runs |
| **7.2** Competence | Ensure personnel competence | `classification.classifier`, `classification.status` | Hermes skills |
| **8.1** Operational planning | Implement risk treatment | `constraints`, `constraint_update` | Hermes approval modes |
| **8.2** Risk treatment implementation | Execute controls | `response.verification` | Hermes tool calls |
| **9.1** Monitoring & measurement | Monitor AI system performance | `trace`, `time_to_detect_sec` | Hermes webhook subscriptions |
| **9.2** Internal audit | Audit AI system | `compliance_tags`, `payload_hash` | Hermes MCP export tools |
| **10.1** Improvement | Continuously improve | `response.actions`, `response.verification` | Hermes skill updates |
| **10.2** Nonconformity & corrective action | Handle nonconformities | `fault_class`, `impact_score`, `loss_amount_usd` | Hermes incident response skill |
| **10.3** Continual improvement | Learn from incidents | `classification.revision_history`, `counterfactuals` | Hermes memory |

### 5.2 ISO 42001 Incident Response Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                  ISO 42001 Incident Lifecycle                 │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐ │
│  │ 6.1 Risk │───▶│ 8.1 Ops  │───▶│ 9.1 Mon- │───▶│ 10.1   │ │
│  │ Assessment│    │ Planning │    │ itoring  │    │Improve │ │
│  └──────────┘    └──────────┘    └──────────┘    └────────┘ │
│       │               │               │               │      │
│       ▼               ▼               ▼               ▼      │
│  risk_score      constraints      trace[]         response   │
│  impact_score    policy versions  time_to_detect  actions   │
│  fault_class     approval modes   containment     verify    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 10.2 Nonconformity: fault_class + impact_score +     │   │
│  │ loss_amount_usd + constraint_update + verification   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 GRC_Claw Integration

For Ahmed's GRC_Claw (ISO 42001) system:

1. **Export AgentIncident records** in ISO 42001 format via the hosted platform or MCP server
2. **Map `compliance_tags`** to GRC_Claw control IDs
3. **Use `payload_hash`** as tamper evidence in GRC_Claw audit trails
4. **Feed `risk_score`** into GRC_Claw risk register
5. **Track `constraint_update`** as GRC_Claw control changes

```bash
# Export for GRC_Claw import
agentincident export ~/.hermes/incidents/ \
  --format iso_42001 \
  --since 2026-09-01 \
  --until 2026-10-01 \
  --output grc-claw-import.json
```

### 5.4 EU AI Act Article 73 Alignment

AgentIncident's EU AI Act export maps to Article 73 (incident reporting for high-risk AI systems):

| Article 73 Requirement | AgentIncident Field |
|----------------------|---------------------|
| Description of incident | `trace`, `classification.root_cause` |
| Date and time | `meta.created_at`, `trace[].ts` |
| AI system identification | `meta.agent`, `meta.agent_id` |
| Severity of incident | `impact_score`, `severity` |
| Consequences | `loss_estimate`, `impact.categories` |
| Measures taken | `response.actions`, `response.constraint_update` |
| Timeline | `time_to_detect_sec`, `time_to_contain_sec`, `time_to_remediate_sec` |

### 5.5 NIST AI RMF Alignment

| NIST AI RMF Function | AgentIncident Field |
|---------------------|---------------------|
| **GOVERN** | `liability`, `compliance_tags`, `risk_score` |
| **MAP** | `fault_class`, `attribution_vector`, `impact.categories` |
| **MEASURE** | `risk_breakdown`, `loss_estimate`, `time_to_detect_sec` |
| **MANAGE** | `response.actions`, `constraint_update`, `verification` |

---

## 6. Pitfalls and Best Practices

### 6.1 Pitfalls

| Pitfall | Why It Happens | How to Avoid |
|---------|---------------|--------------|
| **Over-recording** | Recording every tool call creates noise | Only record irreversible actions, constraint evaluations, and failures/near-misses |
| **Under-recording** | Forgetting to instrument new tools | Use the SDK wrapper pattern — one `rec.record()` per tool call |
| **PII in traces** | Agent inputs contain customer data | Enable `security.redact_secrets: true` in Hermes; use AgentIncident's redaction API before storage |
| **Hash collisions** | Weak hash computation | Always use `sha256:<hex>` format; hash both input AND output |
| **Classification gaming** | Teams dispute every classification | Use `classifier: "human"` for contested cases; `revision_history` tracks changes |
| **Missing near-misses** | Only recording actual damage | Near-misses are 100x more frequent and carry zero political cost — record them all |
| **Webhook spoofing** | Unauthenticated containment webhooks | Always use HMAC-SHA256 secrets; validate signatures |
| **MCP server failures** | MCP server crashes mid-session | Hermes auto-reconnects; use `hermes mcp list` to verify |
| **Compliance export gaps** | Missing fields for audit | Target Full conformance; use `agentincident validate --level full` |
| **Swarm attribution failure** | Can't tell which agent in a swarm caused the issue | Always set `swarm_id` and `agent_id` in `meta` |

### 6.2 Best Practices

#### For Ahmed's Stack

1. **Start with Core conformance** — Get the 5 required fields recording reliably before adding extended fields
2. **Use the SDK wrapper pattern** — One `rec.record()` per tool call, not per agent run
3. **Enable Hermes secret redaction** — `hermes config set security.redact_secrets true` (default, but verify)
4. **Set `approvals.mode: smart`** — Auto-approve low-risk, prompt for high-risk commands
5. **Create the MCP server bridge** — Gives Hermes native `record_incident`, `query_incidents`, `export_compliance` tools
6. **Subscribe to containment webhooks** — AgentIncident → Hermes for real-time incident response
7. **Tag everything with `compliance_tags`** — Even if you don't need exports today, future audits will
8. **Record near-misses aggressively** — They're the distributional data that makes actuarial pricing possible
9. **Use `classifier: "hybrid"`** — Rules first, LLM fallback, human review for contested cases
10. **Validate before export** — `agentincident validate incident.json --level full` before compliance submission

#### Operational

| Practice | Implementation |
|----------|---------------|
| **Instrument once** | SDK wrapper around all tool calls — no per-agent code changes |
| **Detect in real-time** | Webhook subscriptions with payload filters for severity thresholds |
| **Investigate with replay** | Forensic replay with reasoning, I/O diffs, multi-agent graphs |
| **Respond with containment** | `pause_agent` → `kill_swarm` → `human_approve` escalation ladder |
| **Comply with one click** | EU AI Act, NIST AI RMF, ISO 42001 exports with tamper evidence |
| **Prevent recurrence** | `constraint_update` + `verification` closed loop |

#### Security

| Practice | Implementation |
|----------|---------------|
| **Redact PII** | Hermes `security.redact_secrets: true` + AgentIncident redaction API |
| **Sign records** | Use hosted platform's Ed25519 + SLH-DSA signed bundles for legal/insurance |
| **Authenticate webhooks** | HMAC-SHA256 secrets on all webhook subscriptions |
| **Least privilege** | MCP server tools use `include` whitelist, not `exclude` |
| **Audit trail** | `classification.revision_history` + `payload_hash` for tamper evidence |

### 6.3 Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│              AgentIncident × Hermes Quick Reference           │
│                                                              │
│  RECORD    │  rec.record(tool, input, output, irreversible)  │
│  CLASSIFY  │  agentincident classify --method hybrid         │
│  VALIDATE  │  agentincident validate --level full            │
│  EXPORT    │  agentincident export --format iso_42001        │
│  CONTAIN   │  pause_agent → kill_swarm → human_approve       │
│  NOTIFY    │  hermes webhook subscribe --deliver telegram    │
│  INVESTIGATE│ hermes chat -q "Investigate {incident_id}"     │
│  REMEDIATE │  Update constraints → verify → close            │
│                                                              │
│  CONFORMANCE: Core (5 fields) → Standard (+meta, +class)    │
│               → Full (+liability, +response)                │
│                                                              │
│  COMPLIANCE:  ISO 42001 │ EU AI Act Art. 73 │ NIST AI RMF  │
│                                                              │
│  FAULTS:  AGENT_ERROR │ SPEC_AMBIGUITY │ TOOL_FAILURE       │
│           ADVERSARIAL_INPUT │ USER_FAULT │ UNKNOWN           │
│                                                              │
│  IMPACT:   1 Negligible │ 2 Low │ 3 Moderate │ 4 High │ 5 Critical │
└─────────────────────────────────────────────────────────────┘
```

---

## Appendix A: File Locations

| File | Path |
|------|------|
| AgentIncident Spec | `https://github.com/agentincident/agentincident/blob/main/SPEC.md` |
| AgentIncident Schema | `https://github.com/agentincident/agentincident/blob/main/schema/extended.json` |
| AgentIncident SDK (Python) | `pip install agentincident` |
| AgentIncident SDK (TypeScript) | `npm install agentincident` |
| AgentIncident CLI | `pip install agentincident-cli` |
| AgentIncident Platform | `https://agentincident.com` |
| Hermes Config | `~/.hermes/config.yaml` |
| Hermes Skills | `~/.hermes/skills/` |
| Hermes MCP Servers | `~/.hermes/mcp-servers/` |
| Hermes Webhook Subscriptions | `~/.hermes/webhook_subscriptions.json` |
| Hermes Incidents (local) | `~/.hermes/incidents/` |
| Hermes Env | `~/.hermes/.env` |

## Appendix B: Installation Checklist

```bash
# 1. Install AgentIncident SDK
pip install agentincident[langchain]

# 2. Install AgentIncident CLI
pip install agentincident-cli

# 3. Create Hermes skill directory
mkdir -p ~/.hermes/skills/agentincident-recorder
mkdir -p ~/.hermes/skills/agentincident-response

# 4. Create MCP server directory
mkdir -p ~/.hermes/mcp-servers

# 5. Create incidents directory
mkdir -p ~/.hermes/incidents

# 6. Enable webhooks in Hermes
hermes config set platforms.webhook.enabled true
hermes config set platforms.webhook.extra.port 8644
hermes config set platforms.webhook.extra.secret "your-webhook-secret"

# 7. Register MCP server
hermes config set mcp_servers.agentincident.command "python3"
hermes config set mcp_servers.agentincident.args "[~/.hermes/mcp-servers/agentincident_server.py]"

# 8. Set environment variables
echo 'AGENTINCIDENT_API_KEY=your-key' >> ~/.hermes/.env
echo 'WEBHOOK_SECRET=your-webhook-secret' >> ~/.hermes/.env

# 9. Restart Hermes gateway
hermes gateway run

# 10. Verify
hermes webhook list
hermes mcp list
agentincident validate ~/.hermes/incidents/INC-2026-0892.json --level full
```

---

*End of integration guide.*
