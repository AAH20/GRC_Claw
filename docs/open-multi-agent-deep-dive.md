# Open Multi-Agent (OMA) — Deep-Dive Analysis & Integration Guide

> **For:** Ahmed Hassan — Agent Task Decomposition with ApexGraphSwarm  
> **Repo:** [open-multi-agent/open-multi-agent](https://github.com/open-multi-agent/open-multi-agent) (6.9K stars, MIT)  
> **Package:** `@open-multi-agent/core` (v1.14.0)  
> **Launched:** 2026-04-01 · Maintained by YuanASI  

---

## 1. Architecture Overview

### Core Philosophy: Goal-First, Not Graph-First

OMA inverts the traditional orchestration model. Instead of hand-wiring a graph (LangGraph, Mastra), you describe **what you want** in plain English. A coordinator agent builds the task DAG at runtime.

```
┌─────────────────────────────────────────────────────────────┐
│  OpenMultiAgent (Orchestrator)                              │
│  createTeam() · runTeam() · runTasks() · runAgent()         │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │  Team                   │
          │  - AgentConfig[]        │
          │  - MessageBus           │
          │  - TaskQueue            │
          │  - SharedMemory         │
          └────────────┬────────────┘
                       │
     ┌─────────────────┴─────────────────┐
     │                                   │
┌────▼─────┐                    ┌────────▼────────┐
│ AgentPool │                    │ TaskQueue        │
│ Semaphore │                    │ dependency graph  │
│ runParallel()                 │ auto-unblock      │
└────┬─────┘                    │ cascade failure   │
     │                          └─────────────────┘
┌────▼──────────────────────────────────────────────┐
│  Agent                                            │
│  run() · prompt() · stream()                      │
│  └── LLMAdapter (Anthropic / OpenAI / Gemini / …) │
└───────────────────────────────────────────────────┘
```

### Three Execution Modes

| Mode | Method | When to Use |
|------|--------|-------------|
| **Single Agent** | `runAgent(agent, prompt)` | One agent, one task — no team needed |
| **Auto-Orchestrated** | `runTeam(team, goal)` | Goal in → coordinator plans DAG → parallel execution → synthesized result |
| **Explicit Pipeline** | `runTasks(team, tasks)` | You define the task graph and assignments manually |

### The Coordinator Pipeline (runTeam)

1. **Decompose** — Coordinator agent receives goal + agent roster → returns JSON task array with `dependsOn` edges and `assignee` fields
2. **Schedule** — Deterministic topological sort resolves dependencies; independent tasks dispatched immediately
3. **Execute** — AgentPool runs tasks in parallel (semaphore-bounded); outputs flow through SharedMemory
4. **Synthesize** — Second coordinator call writes the final answer from completed task outputs

The coordinator is **never consulted mid-run** — it plans once, then the deterministic scheduler takes over. The finished run is inspectable data.

### Key Architectural Properties

- **3 runtime dependencies** — `@anthropic-ai/sdk`, `openai`, `zod` (everything else is lazy-loaded opt-in)
- **In-process execution** — No subprocess overhead; deploys to serverless, Docker, CI/CD
- **Event-driven DAG dispatch** — Downstream tasks start the moment dependencies are satisfied, without waiting for unrelated ready tasks
- **Three-layer semaphore** — Agent pool, per-agent, and tool execution concurrency control
- **Default-deny tools** — Agents get only what they explicitly list; `bash` stays unsandboxed once granted

---

## 2. Key Features for Ahmed's Stack

### 2.1 Auto Task Decomposition

```typescript
// One call. No manual graph construction.
const result = await oma.runTeam(team, 'Build a REST API for a todo list')
// Coordinator planned the DAG at runtime — you never declared edges
```

The coordinator reasons about:
- Task boundaries and granularity
- Dependency edges (what must finish before what starts)
- Agent assignment (capability-match against system prompts)
- Parallelization opportunities

### 2.2 Auto-Parallelization of Independents

The TaskQueue resolves dependencies topologically. Tasks with no transitive dependency between them run concurrently:

```
task_start design-api
task_complete design-api
task_start implement-handlers    ┐
task_start scaffold-tests       ┘ independent → parallel
task_complete scaffold-tests
task_complete implement-handlers
task_start review-code          // unblocked after implementation
task_complete review-code
```

### 2.3 Model-Agnostic Mixed Teams

```typescript
const architect = { name: 'architect', model: 'claude-opus-4-7', provider: 'anthropic', ... }
const developer = { name: 'developer', model: 'gpt-5.4', provider: 'openai', ... }
const reviewer  = { name: 'reviewer',  model: 'llama3.2',   provider: 'ollama', baseURL: 'http://localhost:11434', ... }
```

10 built-in providers: Anthropic, OpenAI, Azure OpenAI, Bedrock, Gemini, Grok, DeepSeek, Doubao, Hunyuan, MiniMax, Qiniu, Copilot. Plus any OpenAI-compatible endpoint (Ollama, vLLM, LM Studio, OpenRouter, Groq).

### 2.4 Structured Output (Zod)

```typescript
const ClassifierOutput = z.object({
  category: z.enum(['billing', 'technical', 'shipping']),
  urgency: z.enum(['low', 'medium', 'high', 'critical']),
})
const classifier: AgentConfig = {
  name: 'classifier',
  outputSchema: ClassifierOutput,  // validated at runtime, auto-retry on failure
}
```

### 2.5 Durable Approvals & Checkpoint/Resume

```typescript
const result = await oma.runTeam(team, goal, {
  checkpoint: { store: new FileStore('./.oma/run.json') },
})
// Consequential tool calls (file writes, shell) suspend for human approval
// result.status?.code === 'suspended' until reviewer decides
// Resume after crash/restart with orchestrator.restore()
```

### 2.6 Observability

- `onProgress` events — token-by-token streaming on every adapter
- `onTrace` spans — OpenTelemetry-compatible
- Post-run HTML dashboard — renders executed task DAG, assignee, status, timing, token usage
- Automatic secret redaction in traces and dashboard payloads

### 2.7 MCP Tool Integration

```typescript
const mcpTools = await connectMCPTools({
  command: 'npx',
  args: ['-y', '@wonderwhy-er/desktop-commander@latest'],
})
const agent: AgentConfig = { name: 'file-agent', tools: [...mcpTools] }
```

### 2.8 Production Controls

| Concern | Knob |
|---------|------|
| Bound conversation | `maxTurns` + `contextStrategy` (sliding-window / summarize / compact) |
| Bound wall-clock | `timeoutMs` per agent |
| Cap tool output | `maxToolOutputChars` + `compressToolResults` |
| Recover from failure | `maxRetries`, `retryDelayMs`, `retryBackoff` |
| Survive crash | `checkpoint` + `orchestrator.restore()` |
| Bound spend | `maxTokenBudget` or `maxCostBudget` |
| Catch stuck agents | `loopDetection` with `onLoopDetected: 'terminate'` |
| Bound filesystem | `cwd` / `defaultCwd` (default `.agent-workspace`) |

---

## 3. Integration Guide: OMA + ApexGraphSwarm

### 3.1 Integration Patterns

Since ApexGraphSwarm is Ahmed's existing orchestration system, there are three integration patterns:

#### Pattern A: OMA as Runtime DAG Engine (Recommended)

Use OMA's `runTeam()` as the execution backend inside ApexGraphSwarm's task decomposition pipeline:

```typescript
// apex-graphswarm-integration.ts
import { OpenMultiAgent, type AgentConfig } from '@open-multi-agent/core'

export class OMAExecutionEngine {
  private oma: OpenMultiAgent

  constructor() {
    this.oma = new OpenMultiAgent({
      defaultProvider: 'anthropic',
      defaultModel: 'claude-sonnet-4-6',
      maxConcurrency: 3,
      maxTokenBudget: 100_000,
      onProgress: (event) => this.emitProgress(event),
    })
  }

  async executeGoal(goal: string, agents: AgentConfig[]) {
    const team = this.oma.createTeam('apex-team', {
      name: 'apex-team',
      agents,
      sharedMemory: true,
    })

    const result = await this.oma.runTeam(team, goal, {
      checkpoint: { store: new FileStore('./.oma/apex-run.json') },
    })

    return {
      success: result.success,
      tasks: result.tasks,
      output: result.agentResults.get('coordinator')?.output,
      tokenUsage: result.totalTokenUsage,
    }
  }

  private emitProgress(event: any) {
    // Bridge OMA progress events into ApexGraphSwarm's event system
    console.log(`[${event.type}] ${event.task ?? event.agent ?? ''}`)
  }
}
```

#### Pattern B: OMA Coordinator as ApexGraphSwarm Planner

Use OMA's coordinator for decomposition, then execute the resulting DAG in ApexGraphSwarm's own executor:

```typescript
// Use OMA only for planning (planOnly mode)
const plan = await oma.runTeam(team, goal, { planOnly: true })
// plan.tasks contains the DAG with dependencies and assignees
// Feed this DAG into ApexGraphSwarm's executor
await apexGraphSwarm.executeDAG(plan.tasks)
```

#### Pattern C: Hybrid — OMA for Dynamic Sub-Tasks

Use ApexGraphSwarm for the top-level pipeline, and invoke OMA `runTeam()` for complex sub-tasks that benefit from runtime decomposition:

```typescript
// Inside an ApexGraphSwarm task handler
async handleComplexSubTask(goal: string) {
  const engine = new OMAExecutionEngine()
  const agents = this.selectAgentsForGoal(goal)
  return await engine.executeGoal(goal, agents)
}
```

### 3.2 Express Backend Integration

```typescript
// server.ts
import express from 'express'
import { OpenMultiAgent, type AgentConfig } from '@open-multi-agent/core'

const app = express()
const oma = new OpenMultiAgent({
  defaultProvider: 'openai',
  defaultModel: 'gpt-5.4',
  maxTokenBudget: 50_000,
})

const team = oma.createTeam('support', {
  name: 'support',
  agents: [
    { name: 'classifier', model: 'claude-haiku-4-5', systemPrompt: 'Classify the ticket.' },
    { name: 'drafter', model: 'gpt-5.4', systemPrompt: 'Draft a reply.' },
    { name: 'qa-reviewer', model: 'claude-opus-5', systemPrompt: 'Review for tone.' },
  ],
  sharedMemory: true,
  maxConcurrency: 3,
})

app.post('/api/tickets/:id/handle', async (req, res) => {
  const result = await oma.runTeam(team, req.body.goal)
  res.json({
    success: result.success,
    output: result.agentResults.get('coordinator')?.output,
    tasks: result.tasks?.map(t => ({ title: t.title, status: t.status, assignee: t.assignee })),
    tokens: result.totalTokenUsage,
  })
})
```

### 3.3 Migration from @jackchen_me/open-multi-agent

The original package is deprecated. Migration is a one-line change:

```diff
- import { OpenMultiAgent } from '@jackchen_me/open-multi-agent'
+ import { OpenMultiAgent } from '@open-multi-agent/core'
```

---

## 4. Configuration Examples

### 4.1 Goal Definition Patterns

#### Simple Goal (skips coordinator)
```typescript
// Short, single-clause goals are treated as simple tasks
await oma.runAgent(agent, 'Reverse a string and save to /tmp/reverse.ts')
```

#### Complex Goal (triggers coordinator)
```typescript
// Multi-clause goals trigger full DAG decomposition
const goal = `
  Research the tradeoffs of TypeScript decorators, covering:
  - Stage-3 standard vs legacy experimental implementation
  - Runtime and bundle-size cost
  - Current framework support
  Then write a 500-word explainer for a team deciding whether to adopt them.
`
const result = await oma.runTeam(team, goal)
```

#### Goal with Structured Output
```typescript
const ResearchOutput = z.object({
  summary: z.string(),
  tradeoffs: z.array(z.object({
    approach: z.string(),
    pros: z.array(z.string()),
    cons: z.array(z.string()),
  })),
  recommendation: z.string(),
})

const analyst: AgentConfig = {
  name: 'analyst',
  outputSchema: ResearchOutput,
  systemPrompt: 'Compare evidence and identify tradeoffs. Respond ONLY with valid JSON.',
}
```

### 4.2 Team Configuration

```typescript
const team = oma.createTeam('api-team', {
  name: 'api-team',
  agents: [
    {
      name: 'architect',
      model: 'claude-sonnet-4-6',
      systemPrompt: 'Design clean API contracts and file structures.',
      tools: ['file_write'],
      maxTurns: 5,
      timeoutMs: 60_000,
    },
    {
      name: 'developer',
      model: 'claude-sonnet-4-6',
      systemPrompt: 'Implement runnable TypeScript from spec documents.',
      tools: ['bash', 'file_read', 'file_write', 'file_edit'],
      maxTurns: 10,
      timeoutMs: 120_000,
    },
    {
      name: 'reviewer',
      model: 'claude-sonnet-4-6',
      systemPrompt: 'Review code for correctness, security, and style.',
      tools: ['file_read', 'grep'],
      maxTurns: 5,
      timeoutMs: 60_000,
    },
  ],
  sharedMemory: true,
  maxConcurrency: 3,
})
```

### 4.3 Scheduling Strategies

```typescript
const orchestrator = new OpenMultiAgent({
  schedulingStrategy: 'composite',  // 'dependency-first' | 'round-robin' | 'least-busy' | 'capability-match' | 'composite'
  schedulingWeights: { fit: 0.7, load: 0.3 },
})
```

### 4.4 Durable Approval Workflow

```typescript
const oma = new OpenMultiAgent({
  defaultProvider: 'openai',
  defaultModel: 'gpt-5.4',
  onToolCall: ({ consequential }) => (consequential ? { action: 'suspend' } : { action: 'allow' }),
})

const result = await oma.runTeam(team, 'Find overdue invoices and draft the reminders.', {
  checkpoint: { store: new FileStore('./.oma/run.json') },
})

if (result.status?.code === 'suspended') {
  for (const approval of result.pendingApprovals) {
    // Show the user exactly what they're approving (hash-bound)
    console.log(approval.toolCall, approval.hash)
    // After human decision:
    // await oma.resolveApproval(approval.id, { action: 'approve' })
  }
}
```

### 4.5 Plan Replay (Deterministic)

```typescript
// First run: coordinator generates the plan
const firstRun = await oma.runTeam(team, goal)

// Later: replay the exact same plan without re-planning
const replayed = await oma.runTasks(team, firstRun.tasks, {
  checkpoint: { store: new FileStore('./.oma/replay.json') },
})
```

### 4.6 Fan-Out / MapReduce Pattern

```typescript
// For MapReduce-style fan-out without task dependencies
import { AgentPool } from '@open-multi-agent/core'

const pool = new AgentPool(agents, { maxConcurrency: 5 })
const results = await pool.runParallel(
  items.map(item => ({ prompt: `Process: ${item}` }))
)
```

---

## 5. Comparison with Other Orchestration Frameworks

| Feature | OMA | LangGraph JS | Mastra | CrewAI | Vercel AI SDK |
|---------|-----|-------------|--------|--------|---------------|
| **Language** | TypeScript-native | Python-first (TS port) | TypeScript-native | Python only | TypeScript-native |
| **Orchestration** | Goal-first (runtime DAG) | Graph-first (explicit nodes/edges) | Supervisor + hand-wired | Role-based Crews | Single agent loop |
| **Auto-decomposition** | ✅ Coordinator agent | ❌ Manual graph | ❌ Manual wiring | ⚠️ Crew roles | ❌ Manual |
| **Parallel execution** | ✅ Auto (independent tasks) | ✅ Manual (parallel branches) | ✅ Manual | ✅ Sequential/Hierarchical | ❌ Manual |
| **Durable execution** | ✅ Checkpoint + resume | ✅ Per-node checkpointing | ✅ Suspend/resume | ⚠️ Less documented | ❌ |
| **Human-in-the-loop** | ✅ Durable approvals | ✅ interrupt() | ✅ Suspend | ⚠️ Bolt-on | ❌ |
| **Model agnostic** | ✅ 10+ providers | ✅ Any | ✅ Any | ✅ Any | ✅ AI SDK providers |
| **MCP support** | ✅ connectMCPTools() | ⚠️ Via LangChain | ✅ | ⚠️ | ❌ |
| **Structured output** | ✅ Zod + auto-retry | ✅ Zod | ✅ | ⚠️ | ✅ |
| **Runtime deps** | 3 | Heavy (LangChain ecosystem) | Moderate | Heavy | Minimal |
| **Stars** | ~6.9K | ~33.9K | ~24.8K | ~52.8K | — |
| **Best for** | Goal-driven teams, TS backends | Production Python, durability | TS/Next.js products | Fast prototyping | Single-agent apps |

### When to Choose OMA

- **TypeScript/Node.js backend** — no Python sidecar needed
- **Goal-driven workflows** — you want to describe outcomes, not wire graphs
- **Mixed-model teams** — per-agent model assignment (Opus for planning, Haiku for classification, local for review)
- **Production controls** — durable approvals, checkpoint/resume, token budgets, loop detection
- **Lightweight footprint** — 3 runtime dependencies, in-process execution

### When to Choose Something Else

- **Python stack** → LangGraph (durable execution, time-travel debug)
- **Fixed production topology** → LangGraph JS (mature checkpointing)
- **Rapid prototyping** → CrewAI (role-based crews, fastest to working demo)
- **Next.js/Vercel ecosystem** → Mastra (suspend/resume, PII-redacted tracing)

---

## 6. Pitfalls and Best Practices

### Pitfalls

1. **Coordinator quality = DAG quality**  
   A weak coordinator model produces suboptimal DAGs — tasks that should run in parallel get sequenced, or redundant tasks duplicate work. Use a frontier model (Opus/S Sonnet) for the coordinator, even if workers use cheaper models.

2. **Non-deterministic plans**  
   The same goal can produce different DAGs across runs. If you need reproducibility, use `planOnly: true` to capture the plan, then replay it with `runTasks()`.

3. **In-process SharedMemory doesn't scale**  
   Default in-process KV store breaks under high concurrency or distributed deployments. Swap in Redis/Postgres by implementing `MemoryStore` for production.

4. **Node.js-only**  
   No language bindings. If your backend is Python/Go/Rust, you need a service boundary or JS runtime.

5. **bash tool is unsandboxed**  
   Once granted, `bash` executes with full filesystem access. Use `cwd` / `defaultCwd` to bound filesystem reach, and only grant `bash` to agents that need it.

6. **Two extra LLM calls per run**  
   Coordinator planning + synthesis add latency and token overhead. For simple tasks, use `runAgent()` directly to skip the coordinator.

7. **No explicit DAG validation**  
   There's no guarantee the generated DAG is optimal. Debugging planning decisions requires inspecting LLM reasoning chains, which can be opaque.

### Best Practices

1. **Start goal-first, drop to explicit graph when needed**  
   Use `runTeam()` for flexibility. When a path must be locked down, capture the plan and use `runTasks()` for deterministic replay.

2. **Use `planOnly: true` for debugging**  
   Preview the coordinator's task DAG without executing agents. Essential for understanding planning decisions.

3. **Set `revealCoordinator: true` for complex goals**  
   Inject team context (goal, roster, worker role) into every worker prompt. Keeps workers aligned and makes debugging easier.

4. **Bound everything**  
   ```typescript
   {
     maxTurns: 10,              // bound conversation
     timeoutMs: 120_000,        // bound wall-clock
     maxTokenBudget: 100_000,   // bound spend
     maxToolOutputChars: 10_000, // cap tool output
     loopDetection: true,        // catch stuck agents
     compressToolResults: true,  // reduce context bloat
   }
   ```

5. **Use per-agent model tiers**  
   Coordinator on Opus, workers on Sonnet, classification on Haiku, review on local model. 40-70% savings vs all-frontier baseline.

6. **Wire `onProgress` from day one**  
   Twenty lines of TypeScript turn token counts into dollar numbers per run. Without it, mixed-model teams silently regress.

7. **Grant tools deliberately**  
   Default-deny is a feature. An agent with no `tools` list gets none. Grant read/exec access on purpose, not by default.

8. **Use `checkpoint` for production runs**  
   Keeps the run and pending approvals durable. Essential for human-in-the-loop workflows that span hours or days.

9. **Set `maxDelegationDepth` (default: 3)**  
   Prevents infinite delegation chains. Cycle detection rejects targets already in the delegation chain.

10. **Redact secrets automatically**  
    Built-in — API keys, tokens, and Authorization headers stripped from traces, bash output, and dashboard payloads. On by default.

---

## Quick Start

```bash
npm install @open-multi-agent/core
export ANTHROPIC_API_KEY=sk-...
```

```typescript
import { OpenMultiAgent, type AgentConfig } from '@open-multi-agent/core'

const agents: AgentConfig[] = [
  { name: 'architect', model: 'claude-sonnet-4-6', systemPrompt: 'Design clean API contracts.', tools: ['file_write'] },
  { name: 'developer', model: 'claude-sonnet-4-6', systemPrompt: 'Implement runnable TypeScript.', tools: ['bash', 'file_read', 'file_write', 'file_edit'] },
  { name: 'reviewer', model: 'claude-sonnet-4-6', systemPrompt: 'Review correctness and security.', tools: ['file_read', 'grep'] },
]

const oma = new OpenMultiAgent({ defaultModel: 'claude-sonnet-4-6' })
const team = oma.createTeam('api-team', { name: 'api-team', agents, sharedMemory: true })
const result = await oma.runTeam(team, 'Create a REST API for a todo list in /tmp/todo-api/')

console.log(result.success, result.totalTokenUsage.output_tokens)
```

---

*Sources: [GitHub](https://github.com/open-multi-agent/open-multi-agent) · [Docs](https://open-multi-agent.com/docs) · [Blog](https://open-multi-agent.com/blog/goal-to-task-dag-coordinator) · [Production Checklist](https://open-multi-agent.com/guides/production-checklist)*
