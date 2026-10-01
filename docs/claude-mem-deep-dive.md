# Deep-Dive Analysis: thedotmack/claude-mem (95K+ Stars)

> **For:** Ahmed Hassan — Agent context management for long-running tasks
> **Date:** 2026-10-01
> **Repo:** https://github.com/thedotmack/claude-mem

---

## 1. Architecture Overview

### What It Is

Claude-mem is a **hook-driven persistent memory plugin** that captures everything an AI coding agent does during sessions, compresses it with AI, and injects relevant context back into future sessions. It's not a standalone agent — it's a **harness plugin** that wraps around Claude Code, Codex, Gemini, Hermes, Copilot, OpenCode, and more.

### Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Plugin Hooks** | 7 lifecycle hooks (Setup, SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop, SessionEnd) | Observe agent behavior without modifying it |
| **Worker Service** | Express.js 5 on Bun ≥ 1.0 | Processes observations via Claude Agent SDK (or Gemini/OpenRouter) |
| **Database** | SQLite 3 + FTS5 (WAL mode) | Persistent storage at `~/.claude-mem/claude-mem.db` |
| **Vector Store** | Chroma (optional) | Semantic search with hybrid retrieval |
| **Search Tools** | 4 MCP tools + mem-search skill | Progressive disclosure search |
| **Viewer UI** | React + TypeScript | Real-time memory stream |

### Data Flow

```
Tool Execution → Hook (stdin) → SQLite → Worker Service → SDK Processor → SQLite → Next Session Hook
```

1. **Input**: Agent sends tool execution data via stdin to hooks
2. **Storage**: Hooks write observations to SQLite (observations table)
3. **Processing**: Worker service reads observations, processes via Claude Agent SDK
4. **Output**: AI-generated summaries written back to database (session_summaries table)
5. **Retrieval**: Next session's SessionStart hook reads summaries from database

### Database Schema (4 Core Tables)

```sql
-- Sessions: one per agent session
sdk_sessions (id, content_session_id, memory_session_id, project, platform_source, status, ...)

-- Observations: individual tool executions with hierarchical structure
observations (id, memory_session_id, project, type, title, subtitle, narrative, facts, concepts, files_read, files_modified, ...)

-- AI-generated session summaries (multiple per session)
session_summaries (id, memory_session_id, project, request, investigated, learned, completed, next_steps, notes, ...)

-- Raw user prompts with FTS5 search
user_prompts (id, memory_session_id, project, prompt_number, prompt_text, ...)
```

### Hook Lifecycle

| Hook | Timing | What It Does |
|------|--------|-------------|
| **Setup** | Before session | Sub-100ms version check, always exits 0 |
| **SessionStart** | Session start | Starts worker, injects context from previous sessions |
| **UserPromptSubmit** | Before processing | Creates session record, saves raw prompt for FTS5 |
| **PreToolUse (Read)** | Before file read | Intercepts file reads to save tokens via observation history |
| **PostToolUse** | After any tool | Captures observation (tool name, input, output) |
| **Stop** | When agent stops | Generates AI-powered session summary |
| **SessionEnd** | On exit | Marks session completed, graceful cleanup |

### Technology Stack

- **Language**: TypeScript (ES2022, ESNext modules)
- **Runtime**: Node.js 20+ and Bun ≥ 1.0
- **Database**: SQLite 3 with `bun:sqlite` driver
- **Vector Store**: Chroma (optional, for semantic search)
- **HTTP Server**: Express.js 5
- **Real-time**: Server-Sent Events (SSE)
- **AI SDK**: `@anthropic-ai/claude-agent-sdk` (or Gemini / OpenRouter)
- **Build**: esbuild (bundles TypeScript)
- **Process Manager**: Bun (auto-restart on failure)

---

## 2. Key Features for Ahmed's Stack

### 2.1 Persistent Memory Compression

Claude-mem's core value proposition: **context survives across sessions**. It automatically:

- Captures tool usage observations (file reads, edits, searches)
- Generates semantic summaries at session end
- Injects context into new sessions via CLAUDE.md files
- Enables semantic search across project history

**For Ahmed's long-running tasks**: This means an agent working on a multi-day project doesn't lose context between sessions. The AI compresses what happened, and the next session picks up where the last left off.

### 2.2 ~10x Token Savings via 3-Layer Retrieval

The headline feature. Instead of fetching all historical data upfront (expensive), claude-mem uses **progressive disclosure**:

| Layer | Tool | Cost | What You Get |
|-------|------|------|-------------|
| **1. Search (Index)** | `search(query, type, limit)` | ~50-100 tokens/result | Compact table with IDs, titles, dates, types |
| **2. Timeline (Context)** | `timeline(anchor=ID, depth_before=3, depth_after=3)` | ~100-200 tokens/observation | Chronological view around a point |
| **3. Get Observations (Details)** | `get_observations(ids=[123, 456])` | ~500-1,000 tokens/observation | Full details (narrative, facts, files, concepts) |

**Traditional RAG approach**: Fetch 20 observations upfront = 10,000-20,000 tokens, ~10% relevant = 18,000 tokens wasted.

**3-Layer approach**: Search index (1,000) + Timeline context (500) + Fetch details (1,500) = **3,000 tokens, 100% relevant**.

### 2.3 Skill-Based Search (v5.4.0+)

The `mem-search` skill provides 10 search operations with progressive disclosure:
- Search observations, sessions, prompts (full-text FTS5)
- Filter by type, concept, file
- Get recent context, timeline, timeline by query
- API help documentation

**Token savings**: ~2,250 tokens per session vs MCP approach (skill frontmatter ~250 tokens loaded at session start, full instructions ~2,500 tokens loaded on-demand).

### 2.4 Hybrid Search (v5.0.0+)

Combines FTS5 full-text search with Chroma vector database for semantic search. This means you can query "authentication bug" and get results that semantically match even if they don't contain those exact words.

### 2.5 Web Viewer UI

Real-time memory stream at the worker URL. You can watch observations being captured and processed in real-time.

### 2.6 Cloud Sync

Backup memories to cmem.ai — no daemon required, the worker syncs on write.

### 2.7 File Read Gate

Intercepts file reads to save tokens using observation history. If the agent already read a file in a previous session, claude-mem can serve it from memory instead of re-reading.

---

## 3. Integration Guide: Using Claude-Mem Patterns with Hermes Agent

### 3.1 Direct Integration (Claude-Mem Supports Hermes)

Claude-mem explicitly lists Hermes as a supported agent. The installation is:

```bash
npx claude-mem install
```

This sets up:
- Plugin hooks in Hermes' hook system
- Worker service (Bun-managed)
- MCP server for search tools
- SQLite database at `~/.claude-mem/claude-mem.db`

### 3.2 Pattern Adaptation for Hermes Agent

Even without installing claude-mem directly, Ahmed can apply its patterns to Hermes:

#### Pattern 1: Progressive Disclosure in Hermes Skills

Create a Hermes skill that follows the 3-layer workflow:

```markdown
# Memory Search Skill

## 3-LAYER WORKFLOW (ALWAYS FOLLOW):
1. search(query) → Get index with IDs (~50-100 tokens/result)
2. timeline(anchor=ID) → Get context around interesting results
3. get_observations([IDs]) → Fetch full details ONLY for filtered IDs

NEVER fetch full details without filtering first. 10x token savings.
```

#### Pattern 2: Hook-Based Context Injection

Hermes supports project context files (`.hermes.md`, `AGENTS.md`, `CLAUDE.md`). You can create a hook that:

1. At session start: Query SQLite for recent observations, inject as index
2. At session end: Generate AI summary, store for next session

#### Pattern 3: MCP Server Integration

Add claude-mem's MCP server to Hermes config:

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  claude-mem:
    command: "node"
    args: ["~/.claude/plugins/marketplaces/thedotmack/plugin/scripts/mcp-server.cjs"]
    timeout: 120
```

This gives Hermes access to the 4 MCP search tools (`search`, `timeline`, `get_observations`, `important_workflow`).

#### Pattern 4: SQLite + FTS5 for Session Memory

Hermes already uses SQLite + FTS5 at `~/.hermes/state.db`. You can create a parallel observations database following claude-mem's schema:

```sql
CREATE TABLE IF NOT EXISTS observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  project TEXT NOT NULL,
  type TEXT NOT NULL,
  title TEXT,
  narrative TEXT,
  facts TEXT,
  concepts TEXT,
  files_read TEXT,
  files_modified TEXT,
  created_at TEXT NOT NULL,
  created_at_epoch INTEGER NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
  title, narrative, facts, concepts,
  content='observations',
  content_rowid='id'
);
```

### 3.3 Hermes Memory Architecture (Native)

Hermes already has a built-in memory system that shares some claude-mem concepts:

| Feature | Hermes Native | Claude-Mem Pattern |
|---------|--------------|-------------------|
| Memory storage | `~/.hermes/memories/MEMORY.md` | SQLite observations |
| User profile | `~/.hermes/memories/USER.md` | Session summaries |
| Session search | `session_search` tool | FTS5 search |
| Context engine | `context_engine` toolset (lcm) | 3-layer retrieval |
| Compression | `compression.enabled` | AI summarization |
| Memory providers | Mem0, Zep, Letta, etc. | Built-in + Chroma |

**Key insight**: Hermes' `memory` toolset is write-only (add/replace/remove). Memory is always in context via the system prompt. This is different from claude-mem's progressive disclosure approach where the agent fetches details on demand.

### 3.4 Recommended Hybrid Approach

For Ahmed's stack, the best approach combines both:

1. **Use Hermes native memory** for user preferences, identity, and durable facts (MEMORY.md, USER.md)
2. **Use claude-mem patterns** for session observations, tool execution history, and project-specific context
3. **Use MCP integration** to make claude-mem's search tools available in Hermes
4. **Use progressive disclosure** in custom skills to minimize token usage

---

## 4. Configuration Examples

### 4.1 Claude-Mem Settings

```json
// ~/.claude-mem/settings.json
{
  "CLAUDE_MEM_MODEL": "claude-haiku-4-5-20251001",
  "CLAUDE_MEM_PROVIDER": "claude",
  "CLAUDE_MEM_CONTEXT_OBSERVATIONS": 50,
  "CLAUDE_MEM_SESSION_START_INCLUDE_ALL_SOURCES": "false",
  "CLAUDE_MEM_DATA_DIR": "~/.claude-mem"
}
```

### 4.2 Hook Configuration (Claude Code / Hermes)

```json
{
  "hooks": {
    "Setup": [{
      "hooks": [{
        "type": "command",
        "command": "node ${CLAUDE_PLUGIN_ROOT}/scripts/version-check.js",
        "timeout": 60
      }]
    }],
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/context-hook.js",
        "timeout": 300
      }]
    }],
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/new-hook.js",
        "timeout": 60
      }]
    }],
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/save-hook.js",
        "timeout": 120
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/summary-hook.js",
        "timeout": 120
      }]
    }],
    "SessionEnd": [{
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/cleanup-hook.js",
        "timeout": 120
      }]
    }]
  }
}
```

### 4.3 Hermes MCP Integration

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  claude-mem:
    command: "node"
    args:
      - "~/.claude/plugins/marketplaces/thedotmack/plugin/scripts/mcp-server.cjs"
    timeout: 120
    connect_timeout: 60
```

### 4.4 Hermes Memory Configuration

```yaml
# ~/.hermes/config.yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  write_approval: false  # Set true for human confirmation on writes

compression:
  enabled: true
  threshold: 0.50
  target_ratio: 0.20

context:
  engine: lcm  # Layered Context Management
```

### 4.5 Custom Skill for Progressive Disclosure

```markdown
---
name: mem-search
description: "Search project memory with progressive disclosure. Use when querying past work, decisions, or context."
---

# Memory Search

## 3-LAYER WORKFLOW (ALWAYS FOLLOW):

1. **search(query)** → Get compact index with IDs (~50-100 tokens/result)
2. **timeline(anchor=ID)** → Get context around interesting results
3. **get_observations([IDs])** → Fetch full details ONLY for filtered IDs

NEVER fetch full details without filtering first. 10x token savings.

## Available Operations

- `search_observations(query, type, limit)` - FTS5 full-text search
- `search_sessions(query, limit)` - Search session summaries
- `get_timeline(anchor_id, depth_before, depth_after)` - Chronological context
- `get_observation(id)` - Full observation details
- `get_recent(limit)` - Most recent observations

## Token Costs

| Operation | Tokens per Result |
|-----------|------------------|
| search (index) | 50-100 |
| timeline (per observation) | 100-200 |
| get_observation (full details) | 500-1,000 |
```

---

## 5. Comparison with Other Context Management Tools

### 5.1 Feature Matrix

| Feature | claude-mem | Mem0 | Zep/Graphiti | Letta | Hermes Native |
|---------|-----------|------|-------------|-------|---------------|
| **Stars** | 95K+ | 65K+ | 30.7K | 24.7K | — |
| **Shape** | Harness plugin | Memory layer/API | Memory layer/engine | Agent runtime | Built-in |
| **Works with** | Claude Code, Codex, Gemini, Hermes, Copilot, OpenCode | Any agent/framework | Any agent/framework | Agents built in Letta | Hermes only |
| **Memory model** | Session observations → AI compression → progressive disclosure | Extracted facts, scoped per user/agent/session | Temporal knowledge graph | Self-editing memory blocks | File-based (MEMORY.md, USER.md) |
| **Search** | FTS5 + Chroma (hybrid) | Vector + metadata filtering | Graph traversal | Tool-based recall | FTS5 (session_search) |
| **Token efficiency** | ~10x savings (3-layer) | ~90% savings (claimed) | Not specified | Not specified | N/A (always in context) |
| **Setup complexity** | Low (npx install) | Medium (API integration) | High (self-host Graphiti) | High (adopt runtime) | None (built-in) |
| **License** | Apache-2.0 | Apache-2.0 | Apache-2.0 | Apache-2.0 | MIT |

### 5.2 When to Use Which

| Situation | Best Tool |
|-----------|----------|
| You have a coding assistant you already run | **claude-mem** |
| You're building a product that needs memory as a feature | **Mem0** |
| Your memory questions involve time and relationships | **Zep/Graphiti** |
| You're designing an agent around memory | **Letta** |
| You want something working in 10 minutes | **claude-mem** |
| You want fine-grained control over what's remembered | **Hermes native + custom skill** |
| You need cross-IDE memory | **claude-mem** or **Recallium** |

### 5.3 Key Differentiators

**Claude-mem's unique advantages:**
- Zero-config: install and it just works
- Agent-agnostic: works with any hook-supporting agent
- Progressive disclosure: agent controls its own context consumption
- No API calls required: hooks observe from outside

**Mem0's advantages:**
- More mature API and ecosystem
- Better for production applications
- Hosted and self-managed options

**Zep's advantages:**
- Temporal knowledge graph: facts carry validity intervals
- Better for conversational AI
- Fact invalidation with history

**Letta's advantages:**
- Agent manages its own memory (self-editing)
- Most architecturally interesting
- Sleep-time compute for background consolidation

---

## 6. Pitfalls and Best Practices

### 6.1 Pitfalls

1. **Over-reliance on AI summaries**: If something important gets compressed away, there's no clean way to intervene. The summary is a lossy compression.

2. **Claude Code-only origins**: While it now supports Hermes, Codex, Gemini, and Copilot, the project started Claude Code-only. Some features may be more polished for Claude Code.

3. **No fine-grained control**: You have limited control over what gets compressed away. The system decides what to remember.

4. **Opaque memory**: No dashboard or query interface in the base product (the web viewer helps but isn't a full query interface).

5. **Token cost of processing**: The worker service uses Claude Agent SDK (or Gemini/OpenRouter) to process observations, which incurs API costs.

6. **Database growth**: SQLite database grows unbounded. No built-in archival or cleanup mechanism.

7. **Single-user assumption**: Designed for single-user local deployment. No multi-user or team features.

8. **Bun dependency**: Requires Bun runtime, which may not be available in all environments.

9. **Hook timeout risks**: SessionStart hook has 300-second timeout. If npm install is needed, it could timeout.

10. **Context injection limits**: SessionStart injects a progressive disclosure index (~800 tokens), not full context. If the agent doesn't follow the 3-layer workflow, it may miss relevant context.

### 6.2 Best Practices

1. **Always follow the 3-layer workflow**: Search → Timeline → Get Observations. Never fetch full details without filtering first.

2. **Use small search limits**: Start with 3-5 results, increase if needed.

3. **Filter before fetching**: Use type, date, project filters to narrow results.

4. **Batch get_observations**: Always group multiple IDs in one call.

5. **Use timeline strategically**: Get context only when narrative matters.

6. **Monitor database size**: Periodically check `~/.claude-mem/claude-mem.db` size and archive old observations.

7. **Configure AI model wisely**: Use a cheaper model (e.g., claude-haiku) for observation processing to reduce costs.

8. **Set write_approval for sensitive data**: If working with sensitive data, set `write_approval: true` in Hermes memory config.

9. **Use .hermes.md for project rules**: Keep project-specific rules in `.hermes.md` for automatic injection, not in memory.

10. **Combine with Hermes native memory**: Use Hermes MEMORY.md for user preferences and identity, claude-mem for session observations and project context.

11. **Regularly review summaries**: Check the web viewer to ensure summaries are capturing important information.

12. **Backup your database**: The SQLite database is the single source of truth. Back it up regularly.

### 6.3 For Ahmed's Stack Specifically

Given Ahmed's existing Nerve context ledger and Hermes Agent setup:

1. **Don't replace Nerve**: Nerve provides decision-significant events and bounded context. Use claude-mem patterns for session-level observations.

2. **Adopt progressive disclosure**: Implement the 3-layer workflow in a custom Hermes skill for memory search.

3. **Use MCP integration**: Add claude-mem's MCP server to Hermes config for search tools.

4. **Leverage Hermes' built-in memory**: Use MEMORY.md for durable facts, USER.md for preferences, and session_search for past conversations.

5. **Consider Hermes memory providers**: If you need more than file-based memory, consider Mem0 or Zep as Hermes memory providers.

6. **Monitor token usage**: Use `/context` and `/usage` commands to track token consumption and optimize.

---

## Summary

Claude-mem is the most popular agent memory plugin (95K+ stars) for good reason: it's zero-config, agent-agnostic, and delivers ~10x token savings through its 3-layer progressive disclosure pattern. For Ahmed's stack, the key takeaways are:

1. **Install claude-mem directly** for Hermes support, or **adapt its patterns** (progressive disclosure, hook-based capture, SQLite+FTS5 storage) in custom Hermes skills.

2. **The 3-layer workflow** (search → timeline → get_observations) is the core innovation. Implement this pattern in any memory search skill.

3. **Combine with Hermes native memory**: Use MEMORY.md for durable facts, claude-mem for session observations, and MCP for search tools.

4. **Watch for pitfalls**: Database growth, AI summary lossiness, and Bun dependency are the main concerns.

5. **Consider alternatives** if you need more control (Mem0), temporal reasoning (Zep), or self-editing memory (Letta).
