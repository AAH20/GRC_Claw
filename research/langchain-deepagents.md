# LangChain DeepAgents: Technical Architecture & Capabilities Analysis

> **Research Date**: 2026-10-01
> **Scope**: Architecture, orchestration, memory, tool integration, framework comparison, marketing applications, GRC_Claw integration patterns
> **Sources**: LangChain official docs, GitHub (langchain-ai/deepagents), LangChain blog, third-party benchmarks

---

## Table of Contents

1. [DeepAgents Architecture](#1-deepagents-architecture)
2. [Multi-Agent Orchestration Patterns](#2-multi-agent-orchestration-patterns)
3. [Memory & State Management](#3-memory--state-management)
4. [Tool Integration Framework](#4-tool-integration-framework)
5. [Framework Comparison: CrewAI, AutoGen, CAMEL](#5-framework-comparison)
6. [Marketing Automation Applications](#6-marketing-automation-applications)
7. [GRC_Claw Integration Patterns](#7-grc_claw-integration-patterns)
8. [Recommendations & Next Steps](#8-recommendations--next-steps)

---

## 1. DeepAgents Architecture

### 1.1 Overview

DeepAgents is an **opinionated agent harness** built on top of LangChain's `create_agent()` and the LangGraph runtime. It is not a new runtime — it packages the components that long-running, complex agents need by default: planning, filesystem, sub-agents, context management, skills, and memory.

**Three-layer stack:**

| Layer | Role | Abstraction Level |
|-------|------|-------------------|
| **LangGraph** | Agent runtime (durable execution, checkpointing, streaming, HITL) | Lowest |
| **LangChain `create_agent`** | Minimal agent harness (tool-calling loop) | Medium |
| **DeepAgents `create_deep_agent`** | Opinionated harness with bundled best practices | Highest |

### 1.2 Core Components

#### 1.2.1 Planner (TodoListMiddleware)

- **Tool**: `write_todos` — a no-op planning tool that maintains a structured task list
- **Mechanism**: The agent writes and rewrites a to-do list as it works; the list is persisted in agent state
- **Status tracking**: Each task has `pending`, `in_progress`, or `completed` status
- **Purpose**: Context engineering strategy — keeps long-running agents on track by making the plan visible in context
- **Key insight**: The planning tool does NOT execute anything; it is purely a steering mechanism

#### 1.2.2 Executor (Tool Execution Loop)

- **Core loop**: LLM receives message history + system prompt + tools → responds or calls tools → tool results appended to state → loop continues
- **Driven by LangGraph**: Each turn is a graph step with full state persistence
- **Sandbox execution**: When using a sandbox backend, agents get an `execute` tool for shell commands (tests, builds, git operations)
- **Interpreter**: Optional JavaScript runtime for tool composition, subagent orchestration, and structured data transformations

#### 1.2.3 Critic (Subagent Delegation)

- **Not a traditional "critic"**: DeepAgents does not have a separate critic agent in the classical sense
- **Subagent as critic**: The `task` tool spawns ephemeral subagents with isolated context windows
- **Compression**: Subagents return only compressed final results to the parent, keeping the main context clean
- **Isolation**: Each subagent gets a fresh context window — no cross-contamination
- **Async support**: Asynchronous subagents return a task ID immediately and run on remote servers

#### 1.2.4 Tools (Built-in + Custom)

**Built-in harness tools:**

| Tool | Purpose |
|------|---------|
| `write_todos` | Task planning and progress tracking |
| `ls` | List files in virtual filesystem |
| `read_file` | Read file contents |
| `write_file` | Create/overwrite files |
| `edit_file` | Exact string replacements in files |
| `glob` | Pattern-based file search |
| `grep` | Content search across files |
| `task` | Spawn subagents for isolated subtasks |
| `execute` | Run shell commands (sandbox backends only) |

**Custom tool integration:**
- Pass any callable, `@tool`-decorated function, or tool dict to `tools=` parameter
- Schema inferred from function signature and docstring
- MCP tools via `langchain-mcp-adapters`

### 1.3 Middleware Architecture

DeepAgents uses a **middleware stack** that intercepts the agent loop at multiple points:

```
Model Request → [Before Model] → LLM Call → [After Model] → Tool Execution → [Around Tools] → State Update
```

**Default middleware stack (attached by `create_deep_agent`):**

1. **TodoListMiddleware** — planning tool
2. **FilesystemMiddleware** — virtual filesystem tools + context offloading
3. **SubAgentMiddleware** — subagent spawning via `task` tool
4. **SummarizationMiddleware** — auto-summarization of long conversations
5. **SkillsMiddleware** — on-demand skill loading
6. **MemoryMiddleware** — AGENTS.md file loading
7. **HumanInTheLoopMiddleware** — approval gates for sensitive operations

**Middleware capabilities:**
- Add/remove tools from model requests
- Inject filesystem, memory, skills, subagent, or HITL instructions into system prompt
- Summarize/compact or offload message history as context grows
- Store typed values in graph state for later retrieval

### 1.4 Construction & Execution Phases

**Construction phase** (`create_deep_agent()`):
1. Resolves chat model and provider/harness profile
2. Resolves backend for filesystem, skills, memory, and execution
3. Assembles main-agent middleware stack
4. Builds default general-purpose subagent + caller-provided subagents
5. Composes system prompt (caller instructions + SDK defaults + profile text)
6. Calls LangChain's `create_agent()` to produce runnable agent graph

**Execution phase** (graph invocation):
- LangGraph drives the agent loop
- Model receives message history + system prompt + tools
- Tool results appended to state
- Loop continues until model produces final response
- Middleware modifies behavior at each step

---

## 2. Multi-Agent Orchestration Patterns

### 2.1 Subagent Patterns

**Synchronous subagents:**
- Block until completion
- Return single final report to parent
- Best for: sequential dependent tasks

**Asynchronous subagents:**
- Return task ID immediately
- Run on remote server
- Parent agent continues working
- Best for: parallel independent tasks

**Subagent configuration:**
```python
subagents = [
    {
        "name": "researcher",
        "description": "Pulls public web context on companies",
        "prompt": "You are a research subagent. Return 3 facts and 2 risks.",
        "tools": ["web_search"],
    },
    {
        "name": "analyst",
        "description": "Analyzes CRM data and product usage",
        "prompt": "You are a data analyst. Return structured insights.",
        "tools": ["query_database"],
    },
]
```

### 2.2 Orchestration Patterns

| Pattern | Description | Best For |
|---------|-------------|----------|
| **Subagents** | Ephemeral child agents with isolated context | Parallel research, context isolation |
| **Handoffs** | Transfer control between agents with shared context | Multi-hop conversations, user interaction |
| **Router** | Route tasks to specialized agents based on intent | Domain-specific dispatch |
| **Skills** | On-demand knowledge loaded progressively | Reusable workflows, domain knowledge |

### 2.3 Context Engineering

The central design principle: **deciding what information each agent sees**.

- **Subagents** excel at: distributed development, parallelization, multi-hop reasoning
- **Handoffs** excel at: multi-hop reasoning, direct user interaction
- **Skills** excel at: distributed development, multi-hop reasoning, user interaction
- **Router** excels at: parallelization

### 2.4 Streaming

DeepAgents adds `stream.subagents` so each delegated task gets its own handle with:
- Independent message streams
- Tool-call streams
- Nested subagent streams

---

## 3. Memory & State Management

### 3.1 Virtual Filesystem

The virtual filesystem is the primary memory mechanism. It is **pluggable** via backends:

| Backend | Persistence | Use Case |
|---------|-------------|----------|
| `StateBackend` | Ephemeral (in agent state) | Scratch work, single-session |
| `StoreBackend` | Persistent (LangGraph store) | Cross-thread memory |
| `FilesystemBackend` | Local disk | Development, persistent files |
| `CompositeBackend` | Mixed (routes by path) | Production hybrid |
| `LocalShellBackend` | Sandbox | Isolated execution |

**CompositeBackend routing example:**
```python
backend = CompositeBackend(
    default=StateBackend(runtime),
    routes={
        "/memories/": StoreBackend(runtime),  # Persistent across sessions
        "/workspace/": StateBackend(runtime),  # Ephemeral per session
    }
)
```

### 3.2 Memory Types

**Short-term memory:**
- Conversation history in agent state
- Tool results in context window
- Automatically summarized when context grows long

**Long-term memory:**
- AGENTS.md files (always loaded at startup)
- Persistent files in virtual filesystem (via StoreBackend)
- Stored in `~/.deepagents/<agent_name>/memories/`

**Memory-first protocol (Deep Agents Code):**
1. **Research**: Searches memory for relevant context before starting tasks
2. **Response**: Checks memory when uncertain during execution
3. **Learning**: Automatically saves new information for future sessions

### 3.3 Skills System

Skills are **on-demand domain knowledge** loaded progressively:

- Each skill is a directory with a `SKILL.md` file
- Agent reads SKILL.md frontmatter at startup
- Full skill content read only when a task needs it
- Supports scripts, templates, reference docs
- Follows the Agent Skills standard

**Skill sources:**
- `~/.claude/skills` (user skills)
- `.claude/skills` (project skills)
- Custom paths via `SkillsMiddleware`

### 3.4 Context Management

Four-layer context management:

1. **Skills**: On-demand domain knowledge loaded progressively
2. **Memory**: Persistent instructions loaded at startup from AGENTS.md
3. **Summarization & offloading**: Automatic compression of conversation history and large tool results
4. **Prompt caching**: Static prompt sections are cache-eligible (Anthropic, Bedrock)

**Context offloading:**
- Large tool results automatically written to filesystem
- Replaced with truncated preview + file reference
- Prevents context window saturation

**DeltaChannel checkpoint format:**
- Shrinks 200-turn coding session state from 5.27 GB to 129 MB
- Uses snapshots every ~50 Pregel steps to bound read depth

### 3.5 State Persistence

- LangGraph checkpointing after every node
- Time-travel debugging
- Durable execution through failures
- Resume from where left off

---

## 4. Tool Integration Framework

### 4.1 Tool Types

**Custom tools:**
```python
from langchain_core.tools import tool

@tool
def get_customer_data(customer_id: str) -> dict:
    """Retrieve customer data from CRM."""
    return crm.get_customer(customer_id)

agent = create_deep_agent(tools=[get_customer_data])
```

**MCP tools:**
```python
from langchain.mcp import MCPAdapter

mcp_tools = await MCPAdapter.connect("http://mcp-server/tools")
agent = create_deep_agent(tools=mcp_tools)
```

**LangChain tools:**
- Any `@tool`-decorated function
- `StructuredTool` instances
- Tool dicts with schema

### 4.2 Tool Schema Inference

DeepAgents infers tool schemas from:
- Function signature (parameters, types)
- Docstring (description, args)
- Pydantic models (validation)

No separate schema definition needed in most cases.

### 4.3 Tool Execution Model

- Tools execute in the agent's context
- Results appended to message history
- Large results automatically offloaded to filesystem
- HITL approval can gate sensitive operations via `interrupt_on`

### 4.4 Sandbox Backends

| Provider | Description |
|----------|-------------|
| Modal | Serverless sandbox |
| Daytona | Development environment |
| Deno | Secure JS/TS runtime |
| E2B | Cloud sandbox |
| Runloop | Cloud development environment |

---

## 5. Framework Comparison

### 5.1 Feature Matrix

| Dimension | DeepAgents | CrewAI | AutoGen | CAMEL |
|-----------|------------|--------|---------|-------|
| **Primary model** | Harness (opinionated) | Role-based crews | Conversational | Role-playing |
| **Abstraction level** | High | High | Medium | Medium |
| **Multi-agent** | Native (subagents) | Native (crews) | Native (group chat) | Native (workforce) |
| **Planning** | Built-in (write_todos) | Task-based | Emergent | Planner agent |
| **Filesystem** | Virtual (pluggable) | None | None | None |
| **Memory** | Persistent (AGENTS.md + store) | Short-term + RAG | Conversation state | State-based |
| **Context mgmt** | 4-layer (skills, memory, summarization, caching) | Limited | Limited | Limited |
| **HITL** | Built-in (interrupt_on) | Task human_input | Human proxy | Limited |
| **Observability** | LangSmith (excellent) | External tools | External tools | Limited |
| **Ecosystem** | 1000+ integrations | 50+ | 50+ | 40+ |
| **Model agnostic** | Yes (7+ providers) | Yes | Yes | Yes |
| **MCP support** | Yes (langchain-mcp-adapters) | Yes (crewai-tools) | Yes (autogen-ext-mcp) | Yes (native) |
| **Production readiness** | High | Medium | Medium (maintenance mode) | Medium |
| **Learning curve** | Medium | Low | Medium | Medium |
| **License** | MIT | MIT | MIT | Apache 2.0 |

### 5.2 Detailed Comparison

#### DeepAgents vs CrewAI

| Aspect | DeepAgents | CrewAI |
|--------|------------|--------|
| **Architecture** | Middleware stack on LangGraph | Role-based crews with process types |
| **State management** | LangGraph checkpointing + virtual FS | Task outputs passed sequentially |
| **Context management** | 4-layer with auto-summarization | Limited, manual |
| **Filesystem** | Virtual filesystem with pluggable backends | None built-in |
| **Subagents** | Ephemeral, isolated context | Role-based agents in crew |
| **Best for** | Long-running, complex multi-step tasks | Quick prototyping, content pipelines |
| **Time to production** | Medium | Fast (2-4 hours to first demo) |

#### DeepAgents vs AutoGen

| Aspect | DeepAgents | AutoGen |
|--------|------------|---------|
| **Architecture** | Harness with middleware | Conversational event-driven |
| **Communication** | Tool-based | Message-based (group chat) |
| **State** | LangGraph checkpointing | Conversation history |
| **HITL** | Built-in interrupt_on | HumanProxyAgent |
| **Status** | Active development | Maintenance mode (Oct 2025) |
| **Best for** | Production agents with observability | Research, conversational patterns |

#### DeepAgents vs CAMEL

| Aspect | DeepAgents | CAMEL |
|--------|------------|-------|
| **Architecture** | Harness with middleware | Workforce (Planner + Coordinator + Workers) |
| **Coordination** | Subagent spawning | Role-playing pairs |
| **Planning** | write_todos (no-op) | Planner agent (decomposes tasks) |
| **Memory** | Virtual filesystem + AGENTS.md | State-based |
| **Training** | Harness profiles (per-model tuning) | OWL (RL-trained planner) |
| **Best for** | General-purpose autonomous agents | Research, synthetic data generation |

### 5.3 Benchmark Results

From Applied AI Enterprise Agents Benchmark (2025):

| Framework | Tool F1 | Escalation Accuracy | Tokens Used | Cost/Request |
|-----------|---------|---------------------|-------------|--------------|
| LangGraph | 0.75 | 92% | 54,060 | $0.000089 |
| CrewAI | 0.65 | 75% | — | $0.000171 |
| AutoGen | 0.63 | 89% | — | — |
| Native | — | — | 28,529 | $0.000074 |

**Key insight**: Framework choice matters less than implementation quality. Bug fixes and prompt engineering yielded 45-66% improvements vs. 4% spread between frameworks.

### 5.4 When to Choose Each

**Choose DeepAgents when:**
- Long-horizon planning is needed (research, coding, multi-document synthesis)
- Subagents for context isolation without writing spawn-and-merge
- Multi-vendor model routing (Claude, GPT-5, Gemini)
- Anthropic prompt caching without learning breakpoint API
- Production observability via LangSmith

**Choose CrewAI when:**
- Workflow maps cleanly to business roles (Researcher → Writer → Editor)
- Fast prototyping with clean mental model
- Team is new to AI agents

**Choose AutoGen when:**
- Human-in-the-loop is a core requirement
- Research experiments where agent conversation is the output
- Microsoft/Azure environment

**Choose CAMEL when:**
- Role-playing coordination is needed
- Synthetic data generation
- Large-scale simulation (OASIS: up to 1M social agents)

---

## 6. Marketing Automation Applications

### 6.1 LangChain's GTM Agent Case Study

LangChain built an internal GTM (go-to-market) agent on DeepAgents that achieved:

| Metric | Result |
|--------|--------|
| Lead-to-qualified-opportunity conversion | **+250%** |
| Pipeline growth | **3x** |
| Time saved per rep per month | **40 hours** |
| Daily active usage among reps | **50%** |
| Weekly active usage among reps | **86%** |
| Monthly active users | **150+** |
| Weekly requests | **~10,000** |

**Architecture:**
```
New Salesforce lead → Agent checks support tickets & prior outreach
→ Researches prospect (Apollo, Exa, LinkedIn, BigQuery, Gong)
→ Generates personalized email draft with reasoning
→ Posts to Slack for rep approval
→ Rep edits → LLM diff extracts style observations → Stored in PostgreSQL
→ Future drafts load rep preferences automatically
```

**Key design patterns:**
- **Human-in-the-loop**: Nothing goes out without human approval
- **Learning mechanism**: Rep edits analyzed by LLM, style preferences stored
- **Memory compression**: Weekly cron jobs compress accumulated memory
- **Ambient + user-initiated**: 74% ambient, 26% user-initiated

### 6.2 Marketing Use Cases

#### 6.2.1 Lead Qualification & Enrichment
- **Trigger**: New lead in CRM
- **Agent workflow**: Research → Score → Enrich → Route
- **Tools**: CRM API, web search, LinkedIn, Clearbit, Apollo
- **HITL**: Approval before outreach

#### 6.2.2 Content Generation Pipeline
- **Pattern**: Parallel subagents for research, drafting, SEO review
- **Subagents**:
  - Researcher: Market analysis, competitor research
  - Writer: Draft generation
  - SEO Reviewer: Keyword optimization, meta tags
  - Editor: Quality check, brand voice

#### 6.2.3 Campaign Performance Analysis
- **Pattern**: Data aggregation → Analysis → Recommendations
- **Tools**: Google Analytics, ad platforms, CRM
- **Output**: Weekly performance reports with actionable insights

#### 6.2.4 Customer Support Triage
- **Pattern**: Classification → Routing → Response drafting
- **Tools**: Ticket system, knowledge base, CRM
- **HITL**: Escalation approval for sensitive issues

#### 6.2.5 Account-Based Marketing (ABM)
- **Pattern**: Account research → Personalization → Multi-channel orchestration
- **Subagents**:
  - Account Researcher: Company news, technographics, intent data
  - Content Personalizer: Tailored messaging per account
  - Channel Orchestrator: Email, LinkedIn, ads coordination

### 6.3 Marketing Agent Architecture Template

```python
from deepagents import create_deep_agent
from langchain_core.tools import tool

# Research subagent
researcher = {
    "name": "researcher",
    "description": "Deep research on companies, markets, and prospects",
    "prompt": "You are a research subagent. Return structured findings with sources.",
    "tools": ["web_search", "fetch_url"],
}

# Content subagent
writer = {
    "name": "writer",
    "description": "Drafts marketing content, emails, and campaigns",
    "prompt": "You are a content writer. Match brand voice and include CTAs.",
    "tools": ["write_file", "edit_file"],
}

# Analysis subagent
analyst = {
    "name": "analyst",
    "description": "Analyzes campaign performance and customer data",
    "prompt": "You are a data analyst. Return insights with supporting data.",
    "tools": ["query_database", "execute"],
}

agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[crm_lookup, send_email, schedule_meeting],
    subagents=[researcher, writer, analyst],
    system_prompt="You are a GTM agent. Always research before outreach.",
    interrupt_on={"send_email": True, "schedule_meeting": True},
    backend=CompositeBackend(
        default=StateBackend(runtime),
        routes={"/memories/": StoreBackend(runtime)},
    ),
)
```

---

## 7. GRC_Claw Integration Patterns

### 7.1 GRC_Claw Architecture Context

GRC_Claw is a GRC (Governance, Risk, Compliance) platform with three planes:

| Plane | Packages | Responsibility |
|-------|----------|----------------|
| **Control** | `gateway`, `agent-runtime` | Auth, routing, jobs, agent policy |
| **Evidence** | `evidence`, `frameworks` | Controls, tests, hashed artifacts |
| **Data** | `a2z-connector` | SIEM events, org/tenant sync |

**Key components:**
- **ComplianceSuperOrchestrator**: Continuous compliance loops
- **RegulationASTCompiler**: 6 frameworks → executable ASTs
- **NeuroSymbolicReasoner**: Z3 proofs + LLM reasoning
- **UnifiedComplianceGraph**: Real-time knowledge graph
- **AISupplyChainSovereignty**: Model provenance, TEE attestation, ZK proofs

### 7.2 Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GRC_Claw Gateway                          │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  Control     │  │  Agent Runtime   │  │  Evidence    │  │
│  │  Plane       │  │  (DeepAgents)    │  │  Plane       │  │
│  │              │  │                  │  │              │  │
│  │ - Auth       │  │ - Compliance     │  │ - Controls   │  │
│  │ - Routing    │  │   Agent          │  │ - Tests      │  │
│  │ - Jobs       │  │ - Research Agent │  │ - Artifacts  │  │
│  │ - Policy     │  │ - Evidence Agent │  │              │  │
│  └──────────────┘  └──────────────────┘  └──────────────┘  │
│                         │                                    │
│                    ┌────┴────┐                               │
│                    │  A2Z    │                               │
│                    │Connector│                               │
│                    └────┬────┘                               │
└─────────────────────────┼───────────────────────────────────┘
                          │
                    ┌─────┴─────┐
                    │  A2Z SOC  │
                    │  SIEM     │
                    └───────────┘
```

### 7.3 DeepAgents Integration Points

#### 7.3.1 Compliance Research Agent

**Purpose**: Automated compliance research across frameworks

```python
compliance_researcher = {
    "name": "compliance-researcher",
    "description": "Researches regulatory requirements and control mappings",
    "prompt": "You are a compliance research agent. Map findings to ISO 27001, SOC 2, NIST CSF.",
    "tools": ["web_search", "query_compliance_graph"],
}

agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[query_compliance_graph, search_regulations],
    subagents=[compliance_researcher],
    system_prompt="You are GRC_Claw's compliance research agent.",
    backend=CompositeBackend(
        default=StateBackend(runtime),
        routes={
            "/memories/": StoreBackend(runtime),
            "/evidence/": FilesystemBackend(root_dir="/grc-evidence/"),
        },
    ),
)
```

#### 7.3.2 Evidence Analysis Agent

**Purpose**: Analyze security events and map to compliance controls

```python
evidence_analyst = {
    "name": "evidence-analyst",
    "description": "Analyzes SIEM events and maps to compliance controls",
    "prompt": "You are a security evidence analyst. Correlate events with control failures.",
    "tools": ["query_siem", "query_compliance_graph", "calculate_blast_radius"],
}

agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[query_siem, query_compliance_graph],
    subagents=[evidence_analyst],
    interrupt_on={"push_compliance_alert": True},
)
```

#### 7.3.3 Policy Generation Agent

**Purpose**: Generate and update compliance policies

```python
policy_writer = {
    "name": "policy-writer",
    "description": "Drafts and updates compliance policies",
    "prompt": "You are a policy writer. Use clear, auditable language.",
    "tools": ["write_file", "edit_file", "read_file"],
}

agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[compile_regulation_ast, query_compliance_graph],
    subagents=[policy_writer],
    system_prompt="You are GRC_Claw's policy generation agent.",
)
```

### 7.4 Integration Patterns

#### 7.4.1 Tool Bridge Pattern

Expose GRC_Claw functions as DeepAgents tools:

```python
from langchain_core.tools import tool

@tool
def query_compliance_graph(control_id: str) -> dict:
    """Query the unified compliance graph for control details."""
    return grc_claw.compliance_graph.get_control(control_id)

@tool
def query_siem_events(filters: dict) -> list:
    """Query SIEM events with filters."""
    return grc_claw.a2z_connector.get_events(filters)

@tool
def push_compliance_alert(alert: dict) -> str:
    """Push a compliance alert to the A2Z SOC."""
    return grc_claw.a2z_connector.push_alert(alert)

@tool
def calculate_blast_radius(event_id: str) -> dict:
    """Calculate blast radius for a security event."""
    return grc_claw.compliance_orchestrator.calculate_blast_radius(event_id)
```

#### 7.4.2 Subagent Pattern

Use DeepAgents subagents for parallel compliance analysis:

```python
# Parallel framework analysis
iso_agent = create_deep_agent(
    tools=[query_iso_controls],
    system_prompt="Analyze from ISO 27001 perspective.",
)
soc2_agent = create_deep_agent(
    tools=[query_soc2_controls],
    system_prompt="Analyze from SOC 2 perspective.",
)
nist_agent = create_deep_agent(
    tools=[query_nist_controls],
    system_prompt="Analyze from NIST CSF perspective.",
)

# Main agent coordinates
main_agent = create_deep_agent(
    tools=[query_compliance_graph],
    subagents=[
        {"name": "iso", "agent": iso_agent},
        {"name": "soc2", "agent": soc2_agent},
        {"name": "nist", "agent": nist_agent},
    ],
)
```

#### 7.4.3 Memory Integration

Store compliance knowledge in virtual filesystem:

```python
backend = CompositeBackend(
    default=StateBackend(runtime),
    routes={
        "/memories/": StoreBackend(runtime),  # Cross-session compliance memory
        "/evidence/": FilesystemBackend(root_dir="/grc-evidence/"),  # Evidence artifacts
        "/policies/": FilesystemBackend(root_dir="/grc-policies/"),  # Policy documents
    }
)
```

#### 7.4.4 HITL Integration

Gate sensitive compliance operations:

```python
agent = create_deep_agent(
    tools=[push_compliance_alert, update_control_status, create_evidence],
    interrupt_on={
        "push_compliance_alert": True,      # Require approval before alerting
        "update_control_status": True,       # Require approval before status change
        "create_evidence": False,            # Auto-approve evidence creation
    },
)
```

### 7.5 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LangSmith (Observability)                 │
│  - Traces for every LLM call                                 │
│  - Tool invocation metrics                                   │
│  - Token usage tracking                                      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    GRC_Claw Gateway                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              DeepAgents Runtime                       │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │ Compliance │  │  Evidence  │  │   Policy   │     │   │
│  │  │  Agent     │  │  Agent     │  │   Agent    │     │   │
│  │  └────────────┘  └────────────┘  └────────────┘     │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │  Research  │  │  Analysis  │  │  Writing   │     │   │
│  │  │  Subagent  │  │  Subagent  │  │  Subagent  │     │   │
│  │  └────────────┘  └────────────┘  └────────────┘     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              GRC_Claw Tools                           │   │
│  │  - query_compliance_graph                              │   │
│  │  - query_siem_events                                  │   │
│  │  - push_compliance_alert                              │   │
│  │  - calculate_blast_radius                             │   │
│  │  - compile_regulation_ast                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────┴─────┐       ┌─────┴─────┐
              │  A2Z SOC  │       │  Evidence  │
              │  SIEM     │       │  Store     │
              └───────────┘       └───────────┘
```

### 7.6 Recommended Integration Phases

**Phase 1: Tool Bridge (Week 1-2)**
- Expose GRC_Claw functions as DeepAgents tools
- Implement `query_compliance_graph`, `query_siem_events`
- Test with single-agent compliance research

**Phase 2: Subagent Orchestration (Week 3-4)**
- Deploy compliance research subagent
- Implement parallel framework analysis
- Add HITL for sensitive operations

**Phase 3: Memory & Learning (Week 5-6)**
- Configure CompositeBackend with persistent memory
- Implement compliance knowledge accumulation
- Add evidence artifact storage

**Phase 4: Production Hardening (Week 7-8)**
- LangSmith observability integration
- LangGraph checkpointing configuration
- Load testing and optimization

---

## 8. Recommendations & Next Steps

### 8.1 For GRC_Claw

1. **Start with DeepAgents for compliance research agents** — the planning + filesystem + subagent pattern maps well to regulatory analysis
2. **Use the tool bridge pattern** to expose existing GRC_Claw functions without rewriting
3. **Leverage HITL** for compliance alerts and control status changes
4. **Deploy with LangSmith** for observability from day one
5. **Use CompositeBackend** to separate ephemeral session state from persistent compliance memory

### 8.2 For Marketing Automation

1. **Build a GTM agent** following LangChain's proven pattern: research → personalize → draft → approve
2. **Use parallel subagents** for content generation (research, writing, SEO review)
3. **Implement learning from feedback** — analyze rep edits to improve future drafts
4. **Deploy with human-in-the-loop** — no message goes out without approval
5. **Use memory compression** — weekly cron jobs to prevent context bloat

### 8.3 Key Takeaways

| Aspect | DeepAgents Advantage |
|--------|---------------------|
| **Planning** | Built-in write_todos keeps agents on track |
| **Context** | 4-layer management (skills, memory, summarization, caching) |
| **Isolation** | Subagents with fresh context windows |
| **Observability** | LangSmith integration out of the box |
| **Flexibility** | Model-agnostic, pluggable backends, extensible middleware |
| **Production** | LangGraph durability, checkpointing, streaming, HITL |

### 8.4 Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Token overhead (+47% vs native) | Use harness profiles, prompt caching, context offloading |
| Framework complexity | Start with defaults, customize incrementally |
| Model dependency | Use harness profiles for per-model tuning |
| Security (filesystem access) | Use sandbox backends, HITL approval, permission rules |

---

## Appendix A: DeepAgents v0.6+ Features

- **Harness profiles**: Named, versionable bundles of per-model overrides (prompts, tool descriptions, middleware)
- **Lightweight code interpreter**: JavaScript runtime for tool composition
- **v3 streaming event API**: Typed projections with front-end integrations
- **DeltaChannel checkpoint format**: 5.27 GB → 129 MB for 200-turn sessions
- **ContextHubBackend**: Versioned home for skills, policies, and memories via LangSmith Context Hub

## Appendix B: Key Code Patterns

### B.1 Minimal Agent
```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[my_tool],
    system_prompt="You are a research assistant.",
)
result = agent.invoke({"messages": [{"role": "user", "content": "Research topic"}]})
```

### B.2 Agent with Subagents
```python
agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[my_tool],
    subagents=[
        {"name": "researcher", "description": "Research subagent", "prompt": "...", "tools": ["web_search"]},
        {"name": "writer", "description": "Writing subagent", "prompt": "...", "tools": ["write_file"]},
    ],
)
```

### B.3 Agent with HITL
```python
agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[send_email, delete_record],
    interrupt_on={"send_email": True, "delete_record": True},
)
```

### B.4 Agent with Persistent Memory
```python
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

backend = CompositeBackend(
    default=StateBackend(runtime),
    routes={"/memories/": StoreBackend(runtime)},
)
agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[my_tool],
    backend=backend,
    store=InMemoryStore(),
)
```

---

*Document generated: 2026-10-01*
*Sources: LangChain docs, GitHub langchain-ai/deepagents, LangChain blog, Applied AI benchmark, third-party analyses*
