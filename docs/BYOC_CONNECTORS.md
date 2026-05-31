# Bring Your Own Connector (BYOC) — LLMs & MCP

GRC_Claw lets operators plug in **their own LLM providers** and **MCP servers** without forking the gateway. All BYOC traffic goes through the same **exec policy** as built-in GRC/SOAR tools (allowlist → approval → sandbox).

## Configuration

Set one of:

| Method | Example |
|--------|---------|
| File | `GRC_CLAW_CONNECTORS_CONFIG=./connectors.config.json` |
| Inline JSON | `GRC_CLAW_CONNECTORS_JSON='{"version":1,"llm":[...]}'` |

Copy [examples/connectors.config.example.json](../examples/connectors.config.example.json).

**Never put API keys in the JSON file.** Reference env vars via `apiKeyEnv`:

```json
{ "id": "openai", "apiKeyEnv": "OPENAI_API_KEY", "baseUrl": "https://api.openai.com", ... }
```

## LLM providers

Supported kinds:

| `kind` | Use for |
|--------|---------|
| `openai_compatible` | OpenAI, Azure OpenAI, Ollama, vLLM, LiteLLM |
| `anthropic_messages` | Anthropic API |

### Direct chat API

```bash
curl -s -X POST http://127.0.0.1:18791/api/connectors/llm/openai/chat \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Summarize SOC2 CC6.1"}]}'
```

### Agent tool name

`llm.<providerId>.complete` — evaluated as **read** tier (no destructive side effects on its own).

## MCP servers

HTTP JSON-RPC transport (`initialize` → `tools/list` → `tools/call`).

### List tools

```bash
curl -s http://127.0.0.1:18791/api/connectors/mcp/filesystem/tools \
  -H "X-GRC-Claw-Token: $TOKEN"
```

### Invoke via agent policy (recommended)

```bash
curl -s -X POST http://127.0.0.1:18791/api/agent/invoke \
  -H "X-GRC-Claw-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "sessionId": "byoc",
    "tool": "mcp.filesystem.search_controls",
    "args": { "query": "encryption" }
  }'
```

Gated tool pattern: **`mcp.<serverId>.<mcpToolName>`**

Mark dangerous MCP tools in config:

```json
"destructiveTools": ["run_playbook", "delete_file"]
```

Those require `approvalToken` like `soar.run_playbook`.

## Gateway API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/connectors` | Redacted registry summary |
| `POST` | `/api/connectors/reload` | Reload config from env/file |
| `POST` | `/api/connectors/llm/:id/chat` | Chat completion proxy |
| `GET` | `/api/connectors/mcp/:id/tools` | Discover MCP tools |
| `POST` | `/api/connectors/mcp/:id/call` | Call MCP tool (policy-checked) |

## ISO 42001 / supply chain

- Curate MCP servers in config (AIMS Annex A.9 supply-chain control).
- Use `npm run doctor` — reports missing `apiKeyEnv` values.
- Prefer localhost or TLS-terminated MCP proxies for production.

## Tests

```bash
npm run test -w @grc-claw/connectors
npm run test:byoc
```
