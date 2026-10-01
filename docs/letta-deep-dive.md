# Letta (formerly MemGPT) — Deep-Dive Analysis

> **For:** Ahmed Hassan — 330 concurrent agents, session management & resume
> **Repo:** [letta-ai/letta](https://github.com/letta-ai/letta) · ~24K stars · Apache-2.0
> **Current stable:** v0.16.8 (2026-05-14)

---

## 1. Architecture Overview — Stateful Agents with Memory

### Core Thesis

Letta is the production successor to the **MemGPT** research paper (Packer et al., UC Berkeley, arXiv:2310.08560, Oct 2023). The central idea: treat the LLM context window like **RAM** in an operating system, and give the agent tools to manage its own memory hierarchy — paging information in and out of context as needed.

The defining architectural bet: **agent state belongs in a database, not in your application code.** A Letta agent is a row (plus vector rows) in Postgres — its persona, editable memory blocks, message history, and attached tools — reachable through a REST API. You talk to an agent by ID; the server owns the loop, memory paging, and persistence.

### Three-Tier Memory Hierarchy

| Tier | OS Analog | Storage | Always in Context? | Read/Write | Capacity |
|------|----------|---------|-------------------|------------|----------|
| **Core Memory** (blocks) | RAM | Postgres / SQLite | Yes (prepended as XML) | `memory_replace`, `memory_insert` agent tools | Per-block char limit (default 100K in 0.16.6+) |
| **Archival Memory** | Disk | Vector DB (pgvector) | No (search on demand) | `archival_memory_search(query)`, `archival_memory_insert(text, tags)` | Unbounded |
| **Recall Memory** | Page cache | Postgres + index | No (rolled up by compactor) | `conversation_search(query)` | Unbounded; older messages compacted into summaries |

**Core memory blocks** are labeled (`persona`, `human`, plus custom labels like `policies`, `current_task`) and rendered as XML at the top of each prompt. Each block has a label, description (guides the agent's edit decisions), value (current content), and `read_only` flag. Blocks can be per-agent or **shared** — create once via `client.blocks.create(...)`, attach the same `block_id` to multiple agents for synchronized views (idiomatic for shared company policies).

**Archival memory** is agent-immutable from outside — the SDK can read but should not insert directly. The agent curates it. Each passage gets tagged at insert time; search returns semantically closest passages.

**Recall memory** is the conversation transcript itself. When the prompt approaches the context window, the compactor summarizes older messages into a system note, with raw messages still recoverable via `conversation_search`.

### Agent Loop

The agent runs in a heartbeat loop:
1. Assemble context (system prompt + core memory + message history + tool definitions)
2. Call LLM
3. LLM may call tools (including memory tools)
4. Execute tool calls, update state
5. Repeat until the agent yields

Because every step is persisted, an agent is **resumable and inspectable at any point**.

### Storage & Infrastructure

- **PostgreSQL** (primary production; pgvector for embeddings; 25-connection pool)
- **SQLite** (local development fallback)
- **Redis** (caching and session state)
- **Google Cloud Storage** (git-backed memory object storage)
- **Git-backed memory** (introduced late 2025): agent memory stored as version-controlled files, enabling memory versioning, diffing, and rollback

### Nine Agent Types

| Type | Purpose |
|------|---------|
| `memgpt_agent` | Original MemGPT full heartbeat loop with all memory tools |
| `memgpt_v2_agent` | Refreshed MemGPT-style with updated toolset |
| `letta_v1_agent` | Simplified loop without heartbeats |
| `react_agent` | Standard ReAct pattern without memory tools |
| `workflow_agent` | Auto-clearing message buffer — stateless conversations, stateful core memory |
| `split_thread_agent` | Separate threads for different conversation streams |
| `sleeptime_agent` | Background processing during idle periods |
| `voice_convo_agent` | Voice interaction optimized |
| `voice_sleeptime_agent` | Voice + background processing |

### Sleep-Time Agents

A sleep-time agent is a secondary agent that shares the memory blocks of a primary agent and runs in the background (every N steps, default 5, configurable via `sleeptime_agent_frequency`). It reads conversation history and rewrites the primary's blocks asynchronously — so the user-facing agent doesn't pay the latency cost of memory hygiene during its own turn. This addresses the original MemGPT design flaw (one agent juggles memory management AND conversation, slowing both).

### LLM Provider Support

OpenAI (incl. GPT-5.x families, Azure OpenAI), Anthropic (Claude 3.7 / 4.x families), Google Gemini, AWS Bedrock (Anthropic + Llama), Together, Groq, xAI Grok, DeepSeek, OpenRouter, Ollama, vLLM, LM Studio. Embedding providers: OpenAI, Anthropic (Voyage), Hugging Face, BGE local, Ollama embeddings. Model IDs are namespaced `provider/model` (e.g. `openai/gpt-5.3`, `anthropic/claude-opus-4-7`, `ollama/llama3.2`).

---

## 2. Key Features for Ahmed's Stack

### Persistent Memory Across Sessions

The core value proposition. An agent created once persists indefinitely:

```python
from letta_client import Letta

client = Letta(base_url="http://localhost:8283")

# Create once — agent survives process exit
agent = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "human", "value": "Name: Ahmed. Building multi-agent systems."},
        {"label": "persona", "value": "I am a systems architect assistant."},
    ],
)

# Next session, a fresh client hitting the same agent_id still knows Ahmed
resp = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "What do you know about me?"}],
)
```

### Identity & Persona

- **Persona block**: the agent's self-description, personality, and role — always in context
- **Human block**: facts about the user — always in context
- **Custom blocks**: developer-defined labeled sections (e.g., `policies`, `current_task`, `tech_stack`)
- Blocks are rendered as XML in the system prompt, giving the model structured self-knowledge

### Tool Use Across Sessions

Three tool sources, all called via the LLM's native tool-calling shape:

1. **Built-in agent tools**: `memory_replace`, `memory_insert`, `archival_memory_search`, `archival_memory_insert`, `conversation_search`, `send_message` (terminate-and-respond)
2. **Custom Python tools**: `client.tools.create(source_code="def my_tool(...): ...")` — runs in a sandbox per call (E2B if configured) with per-tool argument schema derived from the Python signature
3. **MCP servers**: attach any MCP server (stdio or SSE) via `POST /v1/mcp/servers` + `POST /v1/mcp/servers/{name}/tools/attach` — every MCP tool becomes a Letta tool

Tools persist with the agent — attach once, available every session.

### Multi-Agent Support

- **Shared memory blocks**: create a block once, attach to multiple agents
- **Agent-to-agent messaging**: any agent can call another agent as a tool
- **Groups**: supervisor (central coordinator delegates to specialists), round-robin (sequential distribution), dynamic (adaptive roles), sleep-time variants (v1–v4)
- **Conversations API** (January 2026): multiple agents share memory blocks, enabling parallel agent conversations with a user that maintain coherent shared understanding

### Skill Learning

December 2025: agents dynamically learn reusable skills from task trajectories, storing them in memory for application to future tasks. Benchmarks showed 21.1–36.8% improvement on Terminal Bench 2.0 with a 15.7% cost reduction.

### Agent Development Environment (ADE)

A web-based GUI for inspecting an agent's memory blocks, message trace, and tool calls — essential because a Letta agent's behavior is hard to reason about from code alone when state is in a database.

### Agent File (.af) Portability

Agents can be exported/imported as `.af` files, making them portable across hosts and servers.

---

## 3. Integration Guide — Agent Session Management

### Deployment Options

**Self-hosted server:**
```bash
pip install -U letta
letta server            # starts API server on http://localhost:8283
# or: docker run -p 8283:8283 letta/letta:latest
```

**Letta Cloud:** `https://api.letta.com` — managed, no infrastructure to operate.

### Session Lifecycle

```
Create Agent → Send Messages → Agent Self-Edits Memory → Resume Later
     ↑                                                    ↓
     └──────────── Same agent_id, same memory ─────────────┘
```

**Key concept:** You don't manage transcripts. You create an agent once, then send messages to it by ID. The server owns the conversation history, memory paging, and compaction.

### Python SDK Quickstart

```python
from letta_client import Letta

client = Letta(base_url="http://localhost:8283", token="...")

# 1. Create a stateful agent
agent = client.agents.create(
    model="anthropic/claude-sonnet-5",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "human", "value": "Name: Ahmed. Prefers terse answers."},
        {"label": "persona", "value": "Blunt technical partner. No filler."},
    ],
    tools=["web_search"],
)

# 2. Send messages — agent persists state
resp = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "Remember I deploy on Fridays."}],
)

# 3. Inspect / mutate memory directly from outside the agent loop
blocks = client.agents.blocks.list(agent_id=agent.id)
client.agents.blocks.modify(
    agent_id=agent.id,
    block_label="human",
    value="Name: Ahmed. Maintainer of 330-agent swarm. Prefers terse answers."
)

# 4. Resume in a new process — same agent_id, same memory
resp2 = client.agents.messages.create(
    agent_id=agent.id,
    messages=[{"role": "user", "content": "What do you know about me?"}],
)
```

### TypeScript SDK

```typescript
import Letta from "@letta-ai/letta-client";

const client = new Letta({ apiKey: process.env.LETTA_API_KEY });
const agent = await client.agents.create({ model: "openai/gpt-4.1" });
const response = await client.agents.messages.create(agent.id, { input: "Hello!" });
```

### REST API

All SDK methods map to REST endpoints:
- `POST /v1/agents/` — create agent
- `POST /v1/agents/{agent_id}/messages` — send message
- `GET /v1/agents/{agent_id}/blocks` — list memory blocks
- `PATCH /v1/agents/{agent_id}/blocks/{block_label}` — modify block
- `GET /v1/agents/` — list agents
- `DELETE /v1/agents/{agent_id}` — delete agent

### ACP Integration (Agent Client Protocol)

Connect Letta to any ACP-compatible client (Zed, JetBrains, etc.):

```json
{
  "agent_servers": {
    "Letta": {
      "type": "custom",
      "command": "npx",
      "args": ["-y", "@letta-ai/letta-acp"],
      "env": {
        "LETTA_ACP_BACKEND": "cloud-oauth",
        "LETTA_AGENT_ID": "agent-..."
      }
    }
  }
}
```

Each ACP session becomes a conversation on a Letta agent. Set `LETTA_AGENT_ID` to reuse an existing agent — and its memory — across clients and sessions.

### OpenAI-Compatible API

```bash
letta server --backend local --listen ws://127.0.0.1:4500 --openai-api
```

Then use any OpenAI-compatible client (Open WebUI, LibreChat, LobeChat):
- `GET /v1/models` — lists each Letta agent as a model
- `POST /v1/chat/completions` — sends requests to the selected agent
- `POST /v1/responses` — Responses API with streaming

### Letta Agent SDK (for application integrations)

```typescript
import { createAgentSDK } from "@letta-ai/letta-agent-sdk";

const client = createAgentSDK({ backend: "local" });
const agent = await client.createAgent({ model: "openai/gpt-4.1" });
const session = await client.createSession(agent.id);

await session.send("Hello!");
for await (const event of session.stream()) {
  console.log(event);
}

// Resume later
const resumed = await client.resumeSession(session.conversationId);
```

---

## 4. Configuration Examples

### Basic Agent with Core Memory

```python
from letta_client import Letta

client = Letta(base_url="http://localhost:8283")

agent = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "human",
            "value": "Name: Ahmed Hassan. Building 330-agent swarm for session management.",
            "description": "Information about the user — update as you learn more",
        },
        {
            "label": "persona",
            "value": "I am a systems architect assistant. I help design and debug multi-agent systems.",
            "description": "Agent's self-concept and role",
        },
        {
            "label": "tech_stack",
            "value": "Python, TypeScript, Postgres, Redis, Docker, Kubernetes.",
            "description": "User's technology stack and preferences",
            "read_only": False,
        },
    ],
)
```

### Multi-Agent with Shared Memory

```python
# Create a shared block once
shared_policies = client.blocks.create(
    label="company_policies",
    value="All agents must log actions. No destructive ops without approval.",
    description="Shared policies for all agents",
)

# Attach to multiple agents
agent1 = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "human", "value": "Name: Ahmed."},
        {"label": "persona", "value": "Research assistant."},
    ],
    block_ids=[shared_policies.id],
)

agent2 = client.agents.create(
    model="anthropic/claude-sonnet-5",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "human", "value": "Name: Ahmed."},
        {"label": "persona", "value": "Coding assistant."},
    ],
    block_ids=[shared_policies.id],  # Same shared block
)
```

### Custom Tool Registration

```python
# Register a Python function as a tool
tool = client.tools.create(
    source_code="""
def get_agent_status(agent_id: str) -> str:
    \"\"\"Get the current status of an agent by ID.\"\"\"
    # Your implementation here
    return f"Agent {agent_id}: running, 42 active sessions"
""",
    name="get_agent_status",
)

# Attach to agent
client.agents.tools.attach(agent_id=agent.id, tool_id=tool.id)
```

### MCP Server Integration

```python
# Attach an MCP server
client.mcp.servers.create(
    server_name="my_mcp_server",
    transport="sse",
    url="http://localhost:9000/sse",
)

# Attach specific tools from the server
client.mcp.tools.attach(
    server_name="my_mcp_server",
    tool_names=["search_docs", "create_ticket"],
    agent_id=agent.id,
)
```

### Sleep-Time Agent Configuration

```python
# Create a primary agent
primary = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "human", "value": "Name: Ahmed."},
        {"label": "persona", "value": "Primary assistant."},
    ],
)

# Create a sleep-time agent that shares memory and consolidates in background
sleeptime = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "human", "value": "Name: Ahmed."},
        {"label": "persona", "value": "Background memory consolidator."},
    ],
    agent_type="sleeptime_agent",
    sleeptime_agent_frequency=5,  # Run every 5 steps
)
```

### Docker Compose (Production)

```yaml
version: "3.8"
services:
  letta:
    image: letta/letta:latest
    ports:
      - "8283:8283"
    environment:
      - LETTA_PG_URI=postgresql://letta:letta@postgres:5432/letta
      - LETTA_OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=letta
      - POSTGRES_PASSWORD=letta
      - POSTGRES_DB=letta
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  pgdata:
```

---

## 5. Comparison with Mem0 and Other Memory Tools

### Architecture Philosophy

| Dimension | Letta (MemGPT) | Mem0 | Zep (Graphiti) |
|-----------|---------------|------|----------------|
| **Core model** | Stateful agent runtime; memory is part of the agent | Extract-and-store memory API (vector + optional graph) | Temporal knowledge graph |
| **Memory format** | Agent state blocks (XML in prompt) | Vector embeddings | Temporal knowledge graph nodes/edges |
| **Retrieval model** | Tier-based (core/archival) | Semantic similarity | Graph traversal + temporal |
| **Self-managing** | Yes (agent edits own memory) | No (developer-driven) | No (developer-driven) |
| **Temporal reasoning** | No | No | Yes (timestamps, expiry, supersession) |
| **Agent runtime included** | Yes (full agent server) | No (memory layer only) | No (memory layer only) |
| **Integration complexity** | High (full agent OS) | Low (CRUD API) | Medium-High (graph setup) |
| **Best for** | Long-running stateful agents | Drop-in memory API | Time-aware relational memory |

### When to Choose Which

**Choose Letta if:**
- You are building long-running, stateful agents from scratch
- You want the agent to manage its own memory (self-editing, tiered context)
- You need the agent to persist full conversation state between interactions
- You are building agents that run for hours/days and need to decide what to remember
- You need multi-agent coordination with shared memory

**Choose Mem0 if:**
- You have an existing agent (LangChain, CrewAI, custom) and want to add memory with minimal changes
- You need a simple API: store facts, retrieve relevant ones
- You do not need temporal reasoning or agent self-management
- You want the largest community and most integration examples
- Token cost is a primary concern (Mem0 is ~3x cheaper per turn)

**Choose Zep if:**
- Your agent needs to track how facts change over time
- You need relational knowledge (facts connected to other facts)
- You want to query historical state ("what did we know on date X?")
- You have the infrastructure budget for a graph database

### Cost Profile

| System | Write Latency (p50) | Token Cost per 1k Turns | Observability |
|--------|---------------------|------------------------|---------------|
| Letta | ~150–400ms (sync core update) | ~$2.80 (GPT-4.1, lots of meta-reasoning) | Great — agent tool calls visible |
| Mem0 | ~80–200ms (async) | ~$0.90 (GPT-4.1) | Limited — black-box extraction |
| Zep | ~300–800ms (graph extraction) | Not published | Graph traversal visible |

### Benchmark Landscape (Caution Advised)

All three projects publish contradictory benchmark claims on LOCOMO and LongMemEval. The honest read: **LOCOMO measures multi-session conversational recall and little else.** If your agent does support triage or codebase work, LOCOMO tells you almost nothing. Run your own evals on your own data before committing.

| System | LOCOMO | LongMemEval | Source |
|--------|--------|-------------|--------|
| Mem0 | 92.5 (own claim) / 68.5 (reprint) | 94.4 (own) / 49.0 (independent) | Vendor-run, unverified |
| Letta | 83.2 | Not published | Vendor-claimed |
| Zep | Claims lead over Mem0 | 63.8 (with GPT-4o) | Vendor-run |

---

## 6. Pitfalls and Best Practices

### Pitfalls

1. **Block-limit removal is silent (0.16.7)** — if you relied on per-block char limits to cap per-turn cost, you no longer get that bound. Blocks grow until either the context window or your model bills push back. Add your own pre-write length check on `block.value` before `memory_replace` calls.

2. **Context window default jumped 32K → 128K in 0.16.6** — self-hosters who built spend forecasts on 32K will see costs roughly 4× higher per turn under the new default for unknown models. Pin explicitly with `context_window=32000` if you want the old behavior.

3. **Per-block char default jumped 20K → 100K in 0.16.6** — same vintage as the context-window change. Stack-loaded prompts grow accordingly.

4. **Prompt injection reaches your memory** — because the agent writes untrusted conversational content into persistent memory that is replayed every turn, injected instructions can persist across sessions. Treat memory blocks as an attack surface, not just storage.

5. **Model choice leaks into behavior** — self-editing memory depends on reliable tool-calling. Weaker or heavily-quantized local models mis-format memory edits, corrupting core blocks. The abstraction assumes a competent function-calling model.

6. **Latency has a floor** — the memory-managed loop can issue several tool round-trips (search, edit, then answer) per user turn, each an LLM call. Interactive UX needs streaming and a fast model.

7. **Agent state accretes indefinitely** — there is no automatic TTL on archival or recall memory, so growth planning is on you.

8. **Self-hosting operational overhead** — you are running a stateful service, not calling a library. Backups, migrations, and the Postgres/pgvector instance are now your operational problem.

9. **Memory function design complexity** — if you don't first define the criteria for what information belongs in Core versus what should go to Archival, the agent starts storing things in the wrong layer. That design cost is paid upfront.

10. **Framework lock-in** — Letta is opinionated; sliding it under an existing framework (LangGraph, CrewAI) is more friction than picking Mem0 as a pure memory library. You adopt Letta's agent model wholesale or not at all.

### Best Practices

1. **Design your memory blocks upfront** — define what belongs in Core (always-in-context) vs. Archival (search-on-demand) before creating agents. Write clear `description` fields on each block to guide the agent's edit decisions.

2. **Use shared blocks for common knowledge** — create a block once via `client.blocks.create(...)`, attach to multiple agents. Idiomatic for shared company policies, tech stack, or domain knowledge.

3. **Pin your version** — the API surface (V1) is stable but no longer where new features land. Read release notes before upgrading.

4. **Set explicit context windows** — don't rely on defaults. Pin `context_window` to match your cost and latency budget.

5. **Use sleep-time agents for memory hygiene** — offload memory consolidation to a background agent so the user-facing agent doesn't pay the latency cost.

6. **Monitor token costs** — the self-editing loop consumes 1.5–3× the tokens of a stateless agent. Budget for it. Use the ADE to inspect what's being written to memory.

7. **Treat memory as an attack surface** — sanitize user input before it reaches memory blocks. A compromised tool that mutates a block can poison every subsequent session.

8. **Use the ADE for debugging** — the Agent Development Environment shows every tool call, every memory edit, every context swap. Invaluable for understanding why an agent behaves as it does.

9. **Start with Letta Cloud for prototypes** — get a feel for the memory model before committing to self-hosting. Migrate to self-hosting when you're ready to operate the infrastructure.

10. **Run your own evals** — vendor benchmark numbers contradict each other. Build a 50–100 item eval set from real transcripts with known-correct answers, then measure recall accuracy, tokens injected per turn, and p95 added latency.

11. **Serialize per-user memory writes** — if using Mem0 alongside Letta, be aware that bursty updates can produce double-writes. Serialize per-user.

12. **Plan for memory growth** — there is no automatic TTL. Implement your own archival pruning or compaction strategy for long-lived agents.

---

## Summary for Ahmed's 330-Agent Stack

**Letta is the right choice if:**
- You want each of the 330 agents to have persistent identity and memory across sessions
- You want agents to self-manage their own context (deciding what to remember, what to archive)
- You need multi-agent coordination with shared memory blocks
- You're building a platform, not just bolting memory onto an existing agent

**Letta is NOT the right choice if:**
- You already have an orchestration framework (LangGraph, CrewAI) and just need a memory layer → use **Mem0**
- You need temporal fact tracking (facts that change over time) → use **Zep**
- You want the simplest possible integration with minimal operational overhead → use **Mem0**

**Recommended architecture for 330 agents:**
- Use Letta as the agent runtime (one Letta server + Postgres)
- Create agents with well-designed memory blocks (persona, human, tech_stack, policies)
- Use shared blocks for cross-agent knowledge (company policies, domain knowledge)
- Attach MCP servers for tool access (one attachment, available across all sessions)
- Use sleep-time agents for background memory consolidation
- Use the ADE for debugging and monitoring
- Pin your Letta version and context window settings
