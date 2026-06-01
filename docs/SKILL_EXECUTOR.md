# Skill executor

GRC_Claw runs Cursor-style skills (markdown playbooks under `.cursor/skills/<id>/SKILL.md`) through a **gated executor** on the gateway — OpenClaw-style `claw.*` tools with mandatory exec policy.

## Architecture

```
Operator / Console
       │
       ▼
POST /api/skills/run  ──or──  POST /api/agent/invoke (claw.run_skill)
       │
       ▼
ExecPolicy (allowlist → approval → idempotency)
       │
       ▼
@grc-claw/skill-executor
  ├─ load SKILL.md body
  ├─ BYOC LLM loop (TOOL_CALL / FINAL_ANSWER protocol)
  └─ invoke grc.* / claw.* / mcp.* tools via gateway dispatch
```

Package: `packages/skill-executor/`

## Claw tools

| Tool | Tier | Description |
|------|------|-------------|
| `claw.list_skills` | read | Catalog of discovered skills |
| `claw.get_skill` | read | Metadata + optional full body (`skillId`, `includeBody`) |
| `claw.run_skill` | write | Run playbook for a task (`skillId`, `task`, `llmProviderId`, `maxSteps`) — requires `idempotencyKey` on `/api/agent/invoke` |

Inside a skill loop, only **read-tier** tools are allowed by default (`readOnlyTools: true`). Nested `claw.run_skill` is blocked.

## HTTP examples

```bash
export TOKEN=grc-test-token
export BASE=http://127.0.0.1:18791

# List skills
curl -s -H "X-GRC-Claw-Token: $TOKEN" -X POST "$BASE/api/agent/invoke" \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"demo","tool":"claw.list_skills","args":{}}' | jq .

# Run ISO 42001 skill (needs GEMINI_API_KEY / BYOC LLM)
curl -s -H "X-GRC-Claw-Token: $TOKEN" -X POST "$BASE/api/skills/run" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "demo",
    "skillId": "iso-42001-ai-management-engineering",
    "task": "List top Cursor vendor gaps in 3 bullets.",
    "llmProviderId": "gemini",
    "idempotencyKey": "run-iso-demo-1",
    "maxSteps": 6
  }' | jq .
```

## Discovery paths

1. `GRC_CLAW_SKILLS_DIRS` — comma-separated directories
2. Default: `<cwd>/.cursor/skills` and `<cwd>/../.cursor/skills` (GRC_Claw + parent A2Z workspace)

## LLM protocol

The executor prompts the model to emit either:

- `TOOL_CALL: {"tool":"grc.list_controls","args":{"tenantId":1}}`
- `FINAL_ANSWER: <markdown reply>`

Tool results are fed back until `FINAL_ANSWER` or `maxSteps` (default 8).

## Cursor IDE vs gateway

| Surface | Role |
|---------|------|
| **Cursor IDE** | Loads skills automatically for desktop agents |
| **GRC_Claw gateway** | Executes skills with audit log + exec policy for operators, cron, and console |

Both use the same `SKILL.md` files.
