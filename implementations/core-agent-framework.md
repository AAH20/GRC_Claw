# Core Agent Framework Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Owner:** GRC_Claw Architecture Team  
**Status:** Implementation Ready  
**References:** [LangChain DeepAgents Research](../research/langchain-deepagents.md) · [Agentic GTM Research](../research/agentic-gtm.md) · [Agent Governance Spec](../specs/grc-claw-agent-governance-spec.md) · [Model Governance Spec](../specs/grc-claw-model-governance-spec.md) · [GRC_Claw Architecture](../ARCHITECTURE.md)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [LangChain DeepAgents Integration Patterns](#3-langchain-deepagents-integration-patterns)
4. [Agent Orchestration Layer](#4-agent-orchestration-layer)
5. [Multi-Agent Coordination Patterns](#5-multi-agent-coordination-patterns)
6. [Memory and State Management](#6-memory-and-state-management)
7. [Tool Integration Framework](#7-tool-integration-framework)
8. [Governance and Guardrails](#8-governance-and-guardrails)
9. [Model Routing and Cost Optimization](#9-model-routing-and-cost-optimization)
10. [GRC_Claw Governance Layer Integration](#10-grc_claw-governance-layer-integration)
11. [Scalability Patterns](#11-scalability-patterns)
12. [Monitoring and Observability](#12-monitoring-and-observability)
13. [Implementation Roadmap](#13-implementation-roadmap)
14. [Appendix: Code Patterns](#appendix-code-patterns)

---

## 1. Executive Summary

This document defines the **Core Agent Framework** — the foundational architecture for building agentic AI marketing systems using LangChain DeepAgents. The framework is designed to power autonomous marketing agents that can research, plan, execute, and optimize go-to-market operations while maintaining strict governance, observability, and cost efficiency.

### 1.1 Design Principles

| Principle | Description |
|-----------|-------------|
| **Harness over Runtime** | Build on DeepAgents' opinionated harness, not raw LangGraph |
| **Context Engineering First** | The central design problem is deciding what each agent sees |
| **Human-in-the-Loop by Default** | No client-facing action without human approval |
| **Governance as Code** | Every agent action is policy-checked, audited, and traceable |
| **Cost-Aware Routing** | Match task complexity to model capability |
| **Composable Middleware** | Extend behavior via middleware, not fork |
| **Zero-Trust Security** | No agent is trusted without verification |

### 1.2 Target Outcomes

| Metric | Target |
|--------|--------|
| Lead-to-qualified-opportunity conversion | +250% |
| Pipeline growth | 3x |
| Time saved per rep per month | 40 hours |
| Daily active usage among reps | 50% |
| AI cost of revenue | <20% |
| Agent workflow error rate | <5% |

---

## 2. Architecture Overview

### 2.1 Three-Layer Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MARKETING AGENT APPLICATIONS                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ SDR      │ │ AE       │ │ CSM      │ │ Partner  │ │ Analytics│ │
│  │ Agent    │ │ Agent    │ │ Agent    │ │ Manager  │ │ Agent    │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       │            │            │            │            │        │
│  ┌────┴────────────┴────────────┴────────────┴────────────┴────┐  │
│  │              ORCHESTRATION LAYER (Magentic)                   │  │
│  │  • Planner • Executor • Critic • Router • Handoff             │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
│                             │                                       │
│  ┌──────────────────────────┴───────────────────────────────────┐  │
│  │              DEEPAGENTS HARNESS LAYER                        │  │
│  │  • TodoListMiddleware • FilesystemMiddleware                  │  │
│  │  • SubAgentMiddleware • SummarizationMiddleware                │  │
│  │  • SkillsMiddleware • MemoryMiddleware • HITL Middleware      │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
│                             │                                       │
│  ┌──────────────────────────┴───────────────────────────────────┐  │
│  │              LANGGRAPH RUNTIME LAYER                         │  │
│  │  • Durable Execution • Checkpointing • Streaming • HITL       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              GRC_Claw GOVERNANCE LAYER                        │  │
│  │  • Agent Identity • Delegation • Policy Engine • Audit Trail  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GRC_Claw Gateway                              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐          │
│  │  Control     │  │  Agent Runtime   │  │  Evidence    │          │
│  │  Plane       │  │  (DeepAgents)    │  │  Plane       │          │
│  │              │  │                  │  │              │          │
│  │ - Auth       │  │ - Marketing      │  │ - Controls   │          │
│  │ - Routing    │  │   Agents         │  │ - Tests      │          │
│  │ - Jobs       │  │ - Compliance     │  │ - Artifacts  │          │
│  │ - Policy     │  │   Agents         │  │              │          │
│  └──────────────┘  └──────────────────┘  └──────────────┘          │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Core Agent Framework                             │   │
│  │                                                                │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │   │
│  │  │ Planner    │  │ Executor   │  │ Critic     │            │   │
│  │  │ (write_    │  │ (Tool      │  │ (Subagent  │            │   │
│  │  │  todos)    │  │  Loop)     │  │  Review)   │            │   │
│  │  └────────────┘  └────────────┘  └────────────┘            │   │
│  │                                                                │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │   │
│  │  │ Memory     │  │ Tool       │  │ Governance │            │   │
│  │  │ Manager    │  │ Registry   │  │ Enforcer   │            │   │
│  │  └────────────┘  └────────────┘  └────────────┘            │   │
│  │                                                                │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │   │
│  │  │ Model      │  │ Cost       │  │ Observ-    │            │   │
│  │  │ Router     │  │ Optimizer  │  │ ability    │            │   │
│  │  └────────────┘  └────────────┘  └────────────┘            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              GRC_Claw Integration Layer                        │   │
│  │  • query_compliance_graph  • query_siem_events                │   │
│  │  • push_compliance_alert  • calculate_blast_radius            │   │
│  │  • compile_regulation_ast • agent_identity_registry           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. LangChain DeepAgents Integration Patterns

### 3.1 DeepAgents Architecture

DeepAgents is an **opinionated agent harness** built on LangChain's `create_agent()` and the LangGraph runtime. It packages the components that long-running, complex agents need by default: planning, filesystem, sub-agents, context management, skills, and memory.

**Three-layer stack:**

| Layer | Role | Abstraction Level |
|-------|------|-------------------|
| **LangGraph** | Agent runtime (durable execution, checkpointing, streaming, HITL) | Lowest |
| **LangChain `create_agent`** | Minimal agent harness (tool-calling loop) | Medium |
| **DeepAgents `create_deep_agent`** | Opinionated harness with bundled best practices | Highest |

### 3.2 Core Components

#### 3.2.1 Planner (TodoListMiddleware)

- **Tool**: `write_todos` — a no-op planning tool that maintains a structured task list
- **Mechanism**: The agent writes and rewrites a to-do list as it works; the list is persisted in agent state
- **Status tracking**: Each task has `pending`, `in_progress`, or `completed` status
- **Purpose**: Context engineering strategy — keeps long-running agents on track by making the plan visible in context
- **Key insight**: The planning tool does NOT execute anything; it is purely a steering mechanism

#### 3.2.2 Executor (Tool Execution Loop)

- **Core loop**: LLM receives message history + system prompt + tools → responds or calls tools → tool results appended to state → loop continues
- **Driven by LangGraph**: Each turn is a graph step with full state persistence
- **Sandbox execution**: When using a sandbox backend, agents get an `execute` tool for shell commands
- **Interpreter**: Optional JavaScript runtime for tool composition, subagent orchestration, and structured data transformations

#### 3.2.3 Critic (Subagent Delegation)

- **Not a traditional "critic"**: DeepAgents does not have a separate critic agent in the classical sense
- **Subagent as critic**: The `task` tool spawns ephemeral subagents with isolated context windows
- **Compression**: Subagents return only compressed final results to the parent, keeping the main context clean
- **Isolation**: Each subagent gets a fresh context window — no cross-contamination
- **Async support**: Asynchronous subagents return a task ID immediately and run on remote servers

#### 3.2.4 Tools (Built-in + Custom)

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

### 3.3 Middleware Architecture

DeepAgents uses a **Middleware stack** that intercepts the agent loop at multiple points:

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

### 3.4 Construction & Execution Phases

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

### 3.5 Marketing Agent Template

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

## 4. Agent Orchestration Layer

### 4.1 Planner-Executor-Critic Pattern

The orchestration layer implements a **Planner-Executor-Critic** pattern that provides structured task decomposition, execution, and quality assurance.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                           │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   PLANNER    │───▶│  EXECUTOR    │───▶│   CRITIC     │      │
│  │              │    │              │    │              │      │
│  │ write_todos  │    │ Tool Loop    │    │ Subagent     │      │
│  │ Task Decomp  │    │ LLM + Tools  │    │ Review       │      │
│  │ Dependencies │    │ State Update │    │ Validation   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         ▲                                      │                  │
│         └──────────────────────────────────────┘                  │
│                    (Feedback Loop)                                │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Planner Component

**Responsibilities:**
- Decompose high-level marketing objectives into actionable tasks
- Establish task dependencies and execution order
- Set success criteria for each task
- Maintain the todo list as a steering mechanism

**Implementation:**

```python
PLANNER_SYSTEM_PROMPT = """
You are the planning agent for marketing operations.

Your responsibilities:
1. Decompose the marketing objective into specific, actionable tasks
2. Identify dependencies between tasks
3. Set clear success criteria for each task
4. Estimate resource requirements (tools, data, time)
5. Flag tasks that require human approval

Use write_todos to maintain the task list. Each task should be:
- Specific and measurable
- Bounded in scope
- Assigned to the appropriate executor
- Tagged with approval requirements

Task statuses: pending → in_progress → completed | failed | needs_approval
"""
```

**Planning Strategies:**

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Sequential** | Tasks execute in strict order | Lead ingestion → scoring → routing |
| **Parallel** | Independent tasks run concurrently | Multi-channel outreach |
| **Hierarchical** | Tasks decompose into subtasks | Complex campaign planning |
| **Adaptive** | Plan updates based on results | Dynamic market response |

### 4.3 Executor Component

**Responsibilities:**
- Execute individual tasks using the DeepAgents tool loop
- Manage tool invocation and result handling
- Handle errors and retries with backoff
- Report progress back to the planner

**Implementation:**

```python
EXECUTOR_SYSTEM_PROMPT = """
You are the execution agent for marketing operations.

Your responsibilities:
1. Execute the assigned task using available tools
2. Handle tool errors gracefully with retries
3. Validate results against success criteria
4. Report completion status and artifacts
5. Escalate to human when blocked

Execution rules:
- Always validate inputs before tool calls
- Use idempotency keys for all mutating operations
- Log all tool invocations for audit
- Respect rate limits and quotas
- Stop and escalate on repeated failures
"""
```

**Executor Configuration:**

```python
executor_config = {
    "max_retries": 3,
    "retry_backoff": "exponential",
    "timeout_seconds": 300,
    "max_tool_calls_per_task": 50,
    "enable_parallel_tools": True,
    "sandbox_backend": "e2b",  # or "modal", "daytona", "deno"
}
```

### 4.4 Critic Component

**Responsibilities:**
- Review executor outputs against success criteria
- Validate quality and compliance of agent actions
- Provide feedback for plan refinement
- Gate sensitive operations behind human approval

**Implementation:**

```python
CRITIC_SYSTEM_PROMPT = """
You are the quality assurance agent for marketing operations.

Your responsibilities:
1. Review executor outputs against task success criteria
2. Check compliance with brand voice, legal, and policy requirements
3. Validate data accuracy and completeness
4. Approve, reject, or request revision of outputs
5. Maintain quality metrics and trends

Review dimensions:
- Accuracy: Is the information correct and well-sourced?
- Completeness: Are all requirements addressed?
- Compliance: Does it meet policy and legal standards?
- Brand Voice: Does it match the organization's tone?
- Actionability: Can the output be used directly?
"""
```

**Critic Decision Framework:**

| Decision | Criteria | Action |
|----------|----------|--------|
| **Approve** | All criteria met | Mark task completed |
| **Revise** | Minor issues, fixable | Return to executor with feedback |
| **Reject** | Major issues, unsafe | Escalate to human |
| **Escalate** | Sensitive or ambiguous | Request human approval |

### 4.5 Orchestration Patterns

| Pattern | Description | Best For |
|---------|-------------|----------|
| **Subagents** | Ephemeral child agents with isolated context | Parallel research, context isolation |
| **Handoffs** | Transfer control between agents with shared context | Multi-hop conversations, user interaction |
| **Router** | Route tasks to specialized agents based on intent | Domain-specific dispatch |
| **Skills** | On-demand knowledge loaded progressively | Reusable workflows, domain knowledge |
| **Magentic** | Manager agent dynamically coordinates specialized agents | Complex, ambiguous tasks |

---

## 5. Multi-Agent Coordination Patterns

### 5.1 Marketing Agent Ecosystem

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT (Magentic)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ SDR      │  │ AE       │  │ CSM      │  │ Partner  │            │
│  │ Agent    │  │ Agent    │  │ Agent    │  │ Manager  │            │
│  │          │  │          │  │          │  │ Agent    │            │
│  │•Prospect │  │•Research │  │•Health   │  │•Enable   │            │
│  │•Enrich   │  │•Draft    │  │•QBR      │  │•Co-sell  │            │
│  │•Score    │  │•Coach    │  │•Expand   │  │•Track    │            │
│  │•Outreach │  │•Forecast │  │•Renew    │  │•Route    │            │
│  │•Book     │  │•Close    │  │•Churn    │  │          │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                          │
│  │ Inbound  │  │ Outbound │  │ Analytics│                          │
│  │ Agent    │  │ Agent    │  │ Agent    │                          │
│  │          │  │          │  │          │                          │
│  │•Voice    │  │•Sequence │  │•Attribution│                        │
│  │•Chat     │  │•Follow-up│  │•Forecast │                          │
│  │•Qualify  │  │•Multi-ch │  │•ROI      │                          │
│  │•Route    │  │•Personalize│ │•Dashboard│                          │
│  └──────────┘  └──────────┘  └──────────┘                          │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│              DATA LAYER (CRM + CDP + Enrichment)                      │
│    Salesforce / HubSpot / GHL + Clay + ZoomInfo +                   │
│    Data Cloud + Custom Postgres + Vector Store                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 SDR Agent Architecture

```
SDR Agent
├── Researcher Sub-Agent
│   ├── Firmographic enrichment (Clay, ZoomInfo)
│   ├── Technographic detection
│   ├── Intent signal monitoring
│   └── Contact discovery
├── Writer Sub-Agent
│   ├── Personalized email generation
│   ├── LinkedIn message drafting
│   ├── SMS/WhatsApp message creation
│   └── Follow-up sequence writing
├── Sequencer Sub-Agent
│   ├── Multi-channel delivery orchestration
│   ├── Timing optimization
│   ├── A/B testing
│   └── Reply handling and routing
└── Booker Sub-Agent
    ├── Calendar integration
    ├── Meeting qualification
    ├── AE routing and handoff
    └── CRM update
```

### 5.3 AE Agent Architecture

```
AE Agent
├── Research Sub-Agent
│   ├── Account intelligence brief
│   ├── Stakeholder mapping
│   ├── Competitive landscape
│   └── Deal history analysis
├── Coach Sub-Agent
│   ├── Real-time call support
│   ├── Objection handling suggestions
│   ├── Talk track recommendations
│   └── Deal strategy guidance
├── Writer Sub-Agent
│   ├── Proposal drafting
│   ├── Email sequencing
│   ├── Executive summary creation
│   └── CPQ suggestion
├── Forecaster Sub-Agent
│   ├── Deal health scoring
│   ├── Close probability
│   ├── Slippage risk detection
│   └── Forecast contribution
└── Closer Sub-Agent
    ├── Negotiation support
    ├── Contract review
    ├── Red flag identification
    └── Handoff to CSM
```

### 5.4 CSM Agent Architecture

```
CSM Agent
├── Health Sub-Agent
│   ├── Dynamic health scoring
│   ├── Usage pattern analysis
│   ├── Signal detection (adoption, engagement)
│   └── At-risk flagging
├── Onboarding Sub-Agent
│   ├── Personalized onboarding plans
│   ├── Milestone tracking
│   ├── Resource recommendation
│   └── Progress reporting
├── QBR Sub-Agent
│   ├── QBR deck generation
│   ├── ROI calculation
│   ├── Success metric tracking
│   └── Executive summary creation
├── Expansion Sub-Agent
│   ├── White space mapping
│   ├── Upsell/cross-sell identification
│   ├── Expansion opportunity scoring
│   └── Renewal risk assessment
└── Engagement Sub-Agent
    ├── Proactive outreach
    ├── Training recommendations
    ├── Community connection
    └── Feedback collection
```

### 5.5 Coordination Best Practices

1. **Single Response Principle**: Only one agent talks to the user per turn. The parent orchestrator delivers the final response; subagents are researchers, not responders.

2. **Subagent Role Declaration**: Every subagent must be told "You're a subagent. Do NOT reply to the user directly. Return findings to the parent agent."

3. **Parent Defines Orchestration Pattern**: The parent must have explicit instructions: invoke → wait → combine → respond.

4. **Human-in-the-Loop (HITL) Checkpoints**: Agents use approval-required tools that pause workflows for human review before execution. Critical for:
   - Pricing approvals above threshold
   - Compliance-sensitive communications
   - Deal stage changes with discount implications
   - Client-facing actions in broker channel

5. **Idempotency**: Every agent action carries idempotency keys. Retries are safe because actions are idempotent.

6. **Compensating Transactions**: When a quote is adjusted after new information arrives, the system reverses prior state before applying new state.

7. **Event-Driven Concurrency**: Platform event bus allows sub-tasks to proceed concurrently under explicit approvals.

---

## 6. Memory and State Management

### 6.1 Virtual Filesystem

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

### 6.2 Memory Types

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

### 6.3 Skills System

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

### 6.4 Context Management

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

### 6.5 State Persistence

- LangGraph checkpointing after every node
- Time-travel debugging
- Durable execution through failures
- Resume from where left off

### 6.6 Marketing Memory Schema

```python
# Memory structure for marketing agents
MEMORY_SCHEMA = {
    "/memories/": {
        "customer_profiles": "Persistent customer data and preferences",
        "interaction_history": "Past communications and outcomes",
        "brand_voice": "Tone, style, and messaging guidelines",
        "icp_criteria": "Ideal customer profile definitions",
        "competitor_intel": "Competitive landscape information",
        "campaign_learnings": "What worked and what didn't",
    },
    "/workspace/": {
        "current_campaigns": "Active campaign data",
        "draft_content": "Work-in-progress content",
        "research_notes": "Temporary research findings",
    },
    "/evidence/": {
        "compliance_approvals": "Approved actions and communications",
        "audit_trail": "Complete action history",
    }
}
```

---

## 7. Tool Integration Framework

### 7.1 Tool Types

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

### 7.2 Tool Schema Inference

DeepAgents infers tool schemas from:
- Function signature (parameters, types)
- Docstring (description, args)
- Pydantic models (validation)

No separate schema definition needed in most cases.

### 7.3 Tool Execution Model

- Tools execute in the agent's context
- Results appended to message history
- Large results automatically offloaded to filesystem
- HITL approval can gate sensitive operations via `interrupt_on`

### 7.4 Sandbox Backends

| Provider | Description |
|----------|-------------|
| Modal | Serverless sandbox |
| Daytona | Development environment |
| Deno | Secure JS/TS runtime |
| E2B | Cloud sandbox |
| Runloop | Cloud development environment |

### 7.5 Marketing Tool Registry

```python
MARKETING_TOOLS = {
    # CRM & Data
    "crm_lookup": {
        "description": "Look up customer or lead data from CRM",
        "category": "data",
        "hitl_required": False,
    },
    "query_database": {
        "description": "Query marketing analytics database",
        "category": "data",
        "hitl_required": False,
    },
    "enrich_account": {
        "description": "Enrich account data with firmographics and technographics",
        "category": "data",
        "hitl_required": False,
    },
    
    # Communication
    "send_email": {
        "description": "Send email to prospect or customer",
        "category": "communication",
        "hitl_required": True,
    },
    "send_linkedin": {
        "description": "Send LinkedIn message",
        "category": "communication",
        "hitl_required": True,
    },
    "schedule_meeting": {
        "description": "Schedule a meeting with prospect",
        "category": "communication",
        "hitl_required": True,
    },
    
    # Content
    "generate_content": {
        "description": "Generate marketing content (emails, posts, ads)",
        "category": "content",
        "hitl_required": False,
    },
    "edit_content": {
        "description": "Edit and refine marketing content",
        "category": "content",
        "hitl_required": False,
    },
    
    # Research
    "web_search": {
        "description": "Search the web for market and company information",
        "category": "research",
        "hitl_required": False,
    },
    "fetch_url": {
        "description": "Fetch and extract content from a URL",
        "category": "research",
        "hitl_required": False,
    },
    
    # Analytics
    "calculate_metrics": {
        "description": "Calculate campaign performance metrics",
        "category": "analytics",
        "hitl_required": False,
    },
    "generate_report": {
        "description": "Generate performance report",
        "category": "analytics",
        "hitl_required": False,
    },
}
```

### 7.6 Tool Bridge Pattern for GRC_Claw

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

---

## 8. Governance and Guardrails

### 8.1 Governance Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GOVERNANCE LAYER                                   │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Agent      │  │   Policy     │  │   Audit      │              │
│  │   Identity   │  │   Engine     │  │   Trail      │              │
│  │              │  │              │  │              │              │
│  │ - DID        │  │ - OPA/Rego   │  │ - Merkle     │              │
│  │ - SPIFFE     │  │ - SoD        │  │ - Tamper-    │              │
│  │ - Capability │  │ - Risk Score │  │   Evident    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Human-in-  │  │   Rate       │  │   Content    │              │
│  │   the-Loop   │  │   Limiting   │  │   Safety     │              │
│  │              │  │              │  │              │              │
│  │ - Approval   │  │ - Token      │  │ - PII        │              │
│  │   Gates      │  │   Budgets    │  │   Detection  │              │
│  │ - Escalation │  │ - Cost       │  │ - Compliance │              │
│  │   Paths      │  │   Controls   │  │   Check      │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 Agent Identity Model

Every agent has a verifiable identity document:

```json
{
  "$schema": "https://grc-claw.dev/schemas/agent-identity/v1",
  "id": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "name": "sdr-agent",
  "version": "2.1.0",
  "type": "autonomous",
  "framework": "langchain",
  "owner": {
    "type": "organization",
    "id": "did:grc:org:acme-corp",
    "name": "Acme Corp"
  },
  "deployment": {
    "environment": "production",
    "region": "us-east-1",
    "host": "agent-runner-01.acme.internal"
  },
  "credentials": {
    "public-key": "-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEA...\n-----END PUBLIC KEY-----",
    "key-type": "Ed25519",
    "certificate": "spiffe://acme.internal/agent/sdr-agent"
  },
  "metadata": {
    "created": "2026-09-15T10:30:00Z",
    "last-rotated": "2026-09-15T10:30:00Z",
    "description": "Handles outbound prospecting and lead qualification",
    "tags": ["outbound", "prospecting", "tier-1"]
  },
  "status": "active"
}
```

### 8.3 Delegation Chain

Delegations form chains that MUST be tracked and enforced:

```json
{
  "id": "del:8c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
  "delegator": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "delegate": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "scope": {
    "capabilities": ["read:leads", "write:outreach"],
    "resources": ["crm", "email-system"],
    "constraints": {
      "max-actions-per-session": 100,
      "allowed-operations": ["read", "write"],
      "denied-operations": ["delete", "export"],
      "max-cost-per-session": 50.00
    }
  },
  "expiry": "2026-10-01T12:00:00Z",
  "status": "active"
}
```

### 8.4 Policy Engine (OPA/Rego)

```rego
# Marketing agent policy
package grc.agent.marketing

import future.keywords.if
import future.keywords.in

# Default deny
default allow := false

# Allow read operations for active agents
allow if {
    input.agent.status == "active"
    input.action.category == "read"
    input.agent.capabilities[_] == input.action.required_capability
}

# Allow write operations with HITL
allow if {
    input.agent.status == "active"
    input.action.category == "write"
    input.action.hitl_approved == true
    input.agent.capabilities[_] == input.action.required_capability
    cost_within_budget
}

# Deny if cost exceeds budget
cost_within_budget if {
    input.action.estimated_cost + input.agent.session_cost < input.agent.max_cost_per_session
}

# Deny if agent is suspended
deny if {
    input.agent.status == "suspended"
}

# Deny if delegation expired
deny if {
    input.delegation.expiry < now_ns()
}
```

### 8.5 Human-in-the-Loop (HITL) Gates

```python
agent = create_deep_agent(
    tools=[send_email, delete_record, update_deal_stage],
    interrupt_on={
        "send_email": True,           # Require approval before sending
        "delete_record": True,        # Require approval before deletion
        "update_deal_stage": True,    # Require approval for stage changes
    },
)
```

**HITL Decision Points:**

| Action | Approval Required | Approver | Timeout |
|--------|-------------------|----------|---------|
| Send email to prospect | Yes | Sales Rep | 4 hours |
| Send LinkedIn message | Yes | Sales Rep | 4 hours |
| Schedule meeting | Yes | Sales Rep | 2 hours |
| Update deal stage | Yes | Sales Manager | 1 hour |
| Apply discount >10% | Yes | Sales Manager | 1 hour |
| Delete record | Yes | Admin | 24 hours |
| Export data | Yes | Compliance | 24 hours |

### 8.6 Content Safety

```python
CONTENT_SAFETY_RULES = {
    "pii_detection": {
        "enabled": True,
        "patterns": ["ssn", "credit_card", "email", "phone"],
        "action": "redact_and_flag",
    },
    "compliance_check": {
        "enabled": True,
        "frameworks": ["GDPR", "CCPA", "CAN-SPAM"],
        "action": "block_and_escalate",
    },
    "brand_voice": {
        "enabled": True,
        "check": "tone_and_style",
        "action": "revise",
    },
    "competitor_mentions": {
        "enabled": True,
        "check": "appropriate_use",
        "action": "flag_for_review",
    },
}
```

### 8.7 Rate Limiting and Cost Controls

```python
RATE_LIMITS = {
    "per_agent": {
        "max_requests_per_minute": 60,
        "max_tokens_per_minute": 100000,
        "max_cost_per_hour": 10.00,
        "max_cost_per_day": 50.00,
    },
    "per_workflow": {
        "max_concurrent_agents": 10,
        "max_total_cost": 500.00,
    },
    "per_tenant": {
        "max_requests_per_minute": 600,
        "max_cost_per_day": 500.00,
    },
}
```

---

## 9. Model Routing and Cost Optimization

### 9.1 Model Routing Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MODEL ROUTER                                      │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Task       │  │   Model      │  │   Cost       │              │
│  │   Classifier │  │   Registry   │  │   Optimizer  │              │
│  │              │  │              │  │              │              │
│  │ - Complexity│  │ - Claude     │  │ - Token      │              │
│  │ - Domain    │  │ - GPT-5      │  │   Budgets    │              │
│  │ - Urgency   │  │ - Gemini     │  │ - Caching    │              │
│  │ - Quality   │  │ - SLMs       │  │ - Batching   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Routing Decision Engine                          │   │
│  │  IF task.complexity == "high" AND quality == "critical"       │   │
│  │    THEN model = "claude-sonnet-5"                             │   │
│  │  ELSE IF task.type == "classification"                        │   │
│  │    THEN model = "gpt-4o-mini"                                 │   │
│  │  ELSE IF task.type == "extraction"                            │   │
│  │    THEN model = "gemini-flash"                                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Model Selection Matrix

| Task Type | Complexity | Recommended Model | Cost/1K Tokens | Use Case |
|-----------|------------|-------------------|----------------|----------|
| **Classification** | Low | gpt-4o-mini | $0.0001 | Lead scoring, intent detection |
| **Extraction** | Low | gemini-flash | $0.0001 | Data extraction, parsing |
| **Summarization** | Medium | gpt-4o | $0.0025 | Report generation, meeting notes |
| **Research** | Medium | claude-sonnet-5 | $0.0030 | Market research, competitive analysis |
| **Content Generation** | Medium | claude-sonnet-5 | $0.0030 | Email drafting, content creation |
| **Complex Reasoning** | High | claude-opus-5 | $0.0150 | Strategy, planning, analysis |
| **Code Generation** | High | claude-sonnet-5 | $0.0030 | Tool development, automation |

### 9.3 Cost Optimization Strategies

| Strategy | Description | Savings |
|----------|-------------|---------|
| **Prompt Caching** | Cache static prompt sections | 50-90% on cached tokens |
| **Context Offloading** | Write large results to filesystem | 30-50% on context tokens |
| **Model Downgrade** | Use SLMs for simple tasks | 60-80% on simple tasks |
| **Batching** | Batch similar API calls | 20-40% on API overhead |
| **Token Budgets** | Set per-agent token limits | Prevents cost overruns |
| **Semantic Caching** | Cache similar query results | 40-70% on repeated queries |

### 9.4 Token Budget Management

```python
TOKEN_BUDGETS = {
    "sdr_agent": {
        "daily_budget": 1000000,  # 1M tokens
        "per_task_budget": 50000,
        "per_subagent_budget": 20000,
        "alert_threshold": 0.8,  # Alert at 80% of budget
    },
    "ae_agent": {
        "daily_budget": 2000000,
        "per_task_budget": 100000,
        "per_subagent_budget": 50000,
        "alert_threshold": 0.8,
    },
    "csm_agent": {
        "daily_budget": 500000,
        "per_task_budget": 25000,
        "per_subagent_budget": 10000,
        "alert_threshold": 0.8,
    },
}
```

### 9.5 Cost Monitoring

```python
COST_METRICS = {
    "cost_per_qualified_meeting": "Total agentic workflow cost / meetings booked",
    "cost_per_opportunity": "Total agentic workflow cost / opportunities created",
    "cost_per_closed_deal": "Total agentic workflow cost / closed-won deals",
    "ai_cost_of_revenue": "Inference + compute cost / Revenue",
    "roai": "AI-attributed revenue / (Inference + compute overhead)",
    "token_efficiency": "Useful output tokens / Total input tokens",
}
```

---

## 10. GRC_Claw Governance Layer Integration

### 10.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GRC_Claw Gateway                                  │
│                                                                       │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐          │
│  │  Control     │  │  Agent Runtime   │  │  Evidence    │          │
│  │  Plane       │  │  (DeepAgents)    │  │  Plane       │          │
│  │              │  │                  │  │              │          │
│  │ - Auth       │  │ - Marketing      │  │ - Controls   │          │
│  │ - Routing    │  │   Agents         │  │ - Tests      │          │
│  │ - Jobs       │  │ - Compliance     │  │ - Artifacts  │          │
│  │ - Policy     │  │   Agents         │  │              │          │
│  └──────────────┘  └──────────────────┘  └──────────────┘          │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Core Agent Framework                             │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │   │
│  │  │ Planner    │  │ Executor   │  │ Critic     │            │   │
│  │  └────────────┘  └────────────┘  └────────────┘            │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │   │
│  │  │ Memory     │  │ Tool       │  │ Governance │            │   │
│  │  │ Manager    │  │ Registry   │  │ Enforcer   │            │   │
│  │  └────────────┘  └────────────┘  └────────────┘            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              GRC_Claw Integration Layer                        │   │
│  │  • query_compliance_graph  • query_siem_events                │   │
│  │  • push_compliance_alert  • calculate_blast_radius            │   │
│  │  • compile_regulation_ast • agent_identity_registry           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.2 GRC_Claw Tool Bridge

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

@tool
def compile_regulation_ast(regulation: str) -> dict:
    """Compile a regulation into an executable AST."""
    return grc_claw.regulation_compiler.compile(regulation)

@tool
def verify_agent_identity(agent_id: str) -> dict:
    """Verify an agent's identity and capabilities."""
    return grc_claw.agent_registry.verify(agent_id)

@tool
def check_delegation(delegation_id: str) -> dict:
    """Check if a delegation is valid and active."""
    return grc_claw.delegation_registry.check(delegation_id)
```

### 10.3 Compliance Research Agent

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

### 10.4 Evidence Analysis Agent

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

### 10.5 Policy Generation Agent

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

### 10.6 Memory Integration

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

### 10.7 HITL Integration

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

### 10.8 Integration Phases

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

## 11. Scalability Patterns

### 11.1 Auto-Scaling Architecture

GRC_Claw uses Kubernetes Horizontal Pod Autoscaler (HPA) and Vertical Pod Autoscaler (VPA) to dynamically adjust capacity based on demand.

**HPA Configuration for Agent Runtime:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: grc-agent-runtime-hpa
  namespace: grc-claw
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: grc-agent-runtime
  minReplicas: 2
  maxReplicas: 100
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: grc_agent_request_duration_seconds
        target:
          type: AverageValue
          averageValue: 15m  # 15ms p99 target
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 4
          periodSeconds: 60
        - type: Percent
          value: 100
          periodSeconds: 60
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
        - type: Percent
          value: 10
          periodSeconds: 120
      selectPolicy: Min
```

### 11.2 Multi-Agent Scaling Patterns

| Pattern | Description | Scaling Approach |
|---------|-------------|------------------|
| **Horizontal** | Add more agent instances | HPA based on queue depth |
| **Vertical** | Increase agent resources | VPA based on memory/CPU |
| **Sharding** | Partition by tenant/region | Database + cache sharding |
| **Queue-based** | Async task processing | Message queue + workers |
| **Event-driven** | React to events | Event bus + handlers |

### 11.3 Data Sharding

```python
# Shard agent state by tenant
class TenantShardManager:
    def __init__(self, shard_count: int = 16):
        self.shard_count = shard_count
    
    def get_shard(self, tenant_id: str) -> int:
        return hash(tenant_id) % self.shard_count
    
    def get_shard_for_agent(self, agent_id: str) -> int:
        tenant_id = self._get_tenant_for_agent(agent_id)
        return self.get_shard(tenant_id)
```

### 11.4 Cache Invalidation

```python
CACHE_INVALIDATION_RULES = {
    "agent_config": {
        "ttl": 300,  # 5 minutes
        "invalidate_on": ["config_update", "policy_change"],
    },
    "compliance_data": {
        "ttl": 3600,  # 1 hour
        "invalidate_on": ["control_update", "evidence_new"],
    },
    "model_registry": {
        "ttl": 86400,  # 24 hours
        "invalidate_on": ["model_update", "model_retired"],
    },
}
```

### 11.5 Multi-Tenancy

```python
MULTI_TENANCY_CONFIG = {
    "isolation_level": "tenant",  # tenant, agent, or session
    "data_separation": "schema",  # schema, database, or row
    "resource_quotas": {
        "max_agents_per_tenant": 100,
        "max_concurrent_sessions": 1000,
        "max_daily_cost": 500.00,
    },
    "tenant_routing": {
        "strategy": "header",  # header, subdomain, or path
        "header_name": "X-Tenant-ID",
    },
}
```

### 11.6 Load Balancing

```yaml
# Load balancer configuration
apiVersion: v1
kind: Service
metadata:
  name: grc-agent-runtime-lb
spec:
  type: LoadBalancer
  selector:
    app: grc-agent-runtime
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800  # 3 hours
```

### 11.7 Scalability Testing Framework

```python
SCALABILITY_TEST_CONFIG = {
    "load_tests": {
        "ramp_up": "0 to 1000 concurrent users in 5 minutes",
        "sustain": "1000 concurrent users for 30 minutes",
        "spike": "0 to 5000 users in 1 minute",
    },
    "metrics": {
        "p50_latency": "< 100ms",
        "p99_latency": "< 500ms",
        "error_rate": "< 0.1%",
        "throughput": "> 1000 req/s",
    },
    "agent_tests": {
        "max_concurrent_agents": 1000,
        "max_subagents_per_agent": 10,
        "max_tool_calls_per_session": 100,
    },
}
```

---

## 12. Monitoring and Observability

### 12.1 Observability Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                               │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   LangSmith  │  │   OpenTelemetry│  │   Custom     │              │
│  │              │  │              │  │   Metrics    │              │
│  │ - LLM Traces │  │ - Spans      │  │              │              │
│  │ - Token Usage│  │ - Metrics    │  │ - Cost/Task  │              │
│  │ - Cost Track │  │ - Logs       │  │ - Quality    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Prometheus │  │   Grafana    │  │   Alert      │              │
│  │              │  │              │  │   Manager    │              │
│  │ - Metrics    │  │ - Dashboards │  │              │              │
│  │ - Aggregation│  │ - Visualize  │  │ - Thresholds │              │
│  │ - Retention  │  │ - Explore    │  │ - Routing    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.2 LangSmith Integration

```python
# LangSmith configuration
LANGSMITH_CONFIG = {
    "api_key": os.environ.get("LANGSMITH_API_KEY"),
    "project": "grc-claw-marketing-agents",
    "tracing": True,
    "tracking": [
        "llm_calls",
        "tool_invocations",
        "agent_decisions",
        "token_usage",
        "cost_tracking",
    ],
}
```

### 12.3 Key Metrics

| Category | Metric | Description | Target |
|----------|--------|-------------|--------|
| **Performance** | p50_latency | Median response time | <100ms |
| | p99_latency | 99th percentile response time | <500ms |
| | throughput | Requests per second | >1000 |
| **Quality** | tool_f1 | Tool selection accuracy | >0.75 |
| | escalation_accuracy | Correct escalation rate | >90% |
| | task_completion_rate | Successful task completion | >95% |
| **Cost** | cost_per_task | Average cost per task | Decreasing |
| | token_efficiency | Useful output / total input | >0.3 |
| | roai | Return on AI investment | >10x |
| **Reliability** | error_rate | Failed requests / total | <0.1% |
| | availability | Uptime percentage | >99.9% |
| | recovery_time | Mean time to recovery | <5min |

### 12.4 Agent-Specific Metrics

```python
AGENT_METRICS = {
    "sdr_agent": {
        "connect_rate": "Successful connections / total attempts",
        "reply_rate": "Replies received / messages sent",
        "meetings_booked": "Meetings scheduled per day",
        "pipeline_created": "Pipeline value created per day",
        "cost_per_meeting": "Total cost / meetings booked",
    },
    "ae_agent": {
        "win_rate": "Deals won / total opportunities",
        "sales_cycle_length": "Days from opportunity to close",
        "quota_attainment": "Actual sales / quota",
        "forecast_accuracy": "Predicted vs actual revenue",
    },
    "csm_agent": {
        "nrr": "Net revenue retention",
        "grr": "Gross revenue retention",
        "health_score": "Average customer health score",
        "churn_rate": "Customers lost / total customers",
    },
}
```

### 12.5 Three-Tier Dashboard

| Tier | Audience | Cadence | Metrics |
|------|----------|---------|---------|
| **Board** | CRO, VP Sales, CFO | Monthly/Quarterly | ARR, NRR, CAC Payback, Burn Multiple, Pipeline Coverage |
| **Executive** | Sales Managers | Weekly | Pipeline created, win rate, sales cycle, quota attainment |
| **Operator** | SDRs, AEs, CSMs | Daily | Activity, pipeline, response, conversion, quality, AI ops |

### 12.6 Alerting Configuration

```python
ALERT_RULES = {
    "high_error_rate": {
        "condition": "error_rate > 0.05",
        "duration": "5m",
        "severity": "critical",
        "notification": ["pagerduty", "slack"],
    },
    "high_latency": {
        "condition": "p99_latency > 1000ms",
        "duration": "5m",
        "severity": "warning",
        "notification": ["slack"],
    },
    "cost_overrun": {
        "condition": "daily_cost > budget * 1.2",
        "duration": "1h",
        "severity": "warning",
        "notification": ["email", "slack"],
    },
    "agent_stuck": {
        "condition": "no_progress > 30m",
        "duration": "30m",
        "severity": "critical",
        "notification": ["pagerduty"],
    },
}
```

### 12.7 Audit Trail

Every agent action is logged with cryptographic integrity:

```python
AUDIT_LOG_SCHEMA = {
    "timestamp": "ISO 8601 timestamp",
    "agent_id": "DID of the acting agent",
    "action": "Action type (tool_call, decision, delegation)",
    "input": "Action input (hashed for PII)",
    "output": "Action output (hashed for PII)",
    "model": "Model used for decision",
    "tokens": "Token consumption",
    "cost": "Cost of action",
    "duration": "Execution time",
    "result": "success | failure | escalation",
    "hash": "SHA-256 hash of the log entry",
    "previous_hash": "Hash of the previous entry (Merkle chain)",
}
```

---

## 13. Implementation Roadmap

### 13.1 Phase 1: Foundation (Weeks 1-4)

- Set up GHL Unlimited with sub-accounts for 12 squads
- Deploy HubSpot for reporting and attribution
- Integrate Clay for enrichment
- Build basic n8n workflows for lead routing
- Establish baseline metrics (90 days pre-agentic data)

### 13.2 Phase 2: Core Agents (Weeks 5-8)

- Deploy SDR Agent (Researcher + Writer + Sequencer pattern)
- Deploy Inbound Agent (Voice AI + Conversation AI)
- Implement lead scoring and routing
- Build basic attribution tracking
- Train agents on ICP, messaging, and qualification criteria

### 13.3 Phase 3: Advanced Agents (Weeks 9-12)

- Deploy AE Agent (Research + Coach + Forecaster)
- Deploy CSM Agent (Health + Onboarding + Expansion)
- Deploy Partner Manager Agent
- Implement multi-touch attribution
- Build three-tier dashboard

### 13.4 Phase 4: Optimization (Weeks 13-16)

- Run holdout tests for incrementality measurement
- A/B test agent prompts and workflows
- Optimize cost per outcome
- Implement Shapley-value attribution
- Scale successful patterns across all 12 squads

### 13.5 Phase 5: Scale (Weeks 17-24)

- Deploy to all 330 agent slots
- Implement full governance and audit framework
- Build custom broker channel workflows
- Optimize unit economics
- Target: $30K MRR with <20% AI cost of revenue

---

## Appendix: Code Patterns

### A.1 Minimal Agent

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[my_tool],
    system_prompt="You are a research assistant.",
)
result = agent.invoke({"messages": [{"role": "user", "content": "Research topic"}]})
```

### A.2 Agent with Subagents

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

### A.3 Agent with HITL

```python
agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[send_email, delete_record],
    interrupt_on={"send_email": True, "delete_record": True},
)
```

### A.4 Agent with Persistent Memory

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

### A.5 Marketing Agent with Full Configuration

```python
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend, FilesystemBackend

# Define subagents
researcher = {
    "name": "researcher",
    "description": "Deep research on companies, markets, and prospects",
    "prompt": "You are a research subagent. Return structured findings with sources.",
    "tools": ["web_search", "fetch_url"],
}

writer = {
    "name": "writer",
    "description": "Drafts marketing content, emails, and campaigns",
    "prompt": "You are a content writer. Match brand voice and include CTAs.",
    "tools": ["write_file", "edit_file"],
}

analyst = {
    "name": "analyst",
    "description": "Analyzes campaign performance and customer data",
    "prompt": "You are a data analyst. Return insights with supporting data.",
    "tools": ["query_database", "execute"],
}

# Configure backend
backend = CompositeBackend(
    default=StateBackend(runtime),
    routes={
        "/memories/": StoreBackend(runtime),
        "/workspace/": StateBackend(runtime),
        "/evidence/": FilesystemBackend(root_dir="/marketing-evidence/"),
    },
)

# Create agent
agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[crm_lookup, send_email, schedule_meeting, generate_content],
    subagents=[researcher, writer, analyst],
    system_prompt="You are a GTM agent. Always research before outreach.",
    interrupt_on={
        "send_email": True,
        "schedule_meeting": True,
    },
    backend=backend,
    store=InMemoryStore(),
)
```

### A.6 GRC_Claw Integration Agent

```python
from deepagents import create_deep_agent
from langchain_core.tools import tool

@tool
def query_compliance_graph(control_id: str) -> dict:
    """Query the unified compliance graph for control details."""
    return grc_claw.compliance_graph.get_control(control_id)

@tool
def query_siem_events(filters: dict) -> list:
    """Query SIEM events with filters."""
    return grc_claw.a2z_connector.get_events(filters)

compliance_researcher = {
    "name": "compliance-researcher",
    "description": "Researches regulatory requirements and control mappings",
    "prompt": "You are a compliance research agent. Map findings to ISO 27001, SOC 2, NIST CSF.",
    "tools": ["web_search", "query_compliance_graph"],
}

agent = create_deep_agent(
    model="anthropic:claude-sonnet-5",
    tools=[query_compliance_graph, query_siem_events, search_regulations],
    subagents=[compliance_researcher],
    system_prompt="You are GRC_Claw's compliance research agent.",
    interrupt_on={"push_compliance_alert": True},
    backend=CompositeBackend(
        default=StateBackend(runtime),
        routes={
            "/memories/": StoreBackend(runtime),
            "/evidence/": FilesystemBackend(root_dir="/grc-evidence/"),
        },
    ),
)
```

---

*Document generated: 2026-10-01*  
*Sources: LangChain docs, GitHub langchain-ai/deepagents, LangChain blog, Applied AI benchmark, GRC_Claw research documents*
