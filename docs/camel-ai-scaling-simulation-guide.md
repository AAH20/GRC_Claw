# CAMEL-AI Deep-Dive: Multi-Agent Scaling Simulation for 330 Agent Slots

**Target:** Ahmed Hassan — Agent Scaling Simulation  
**Date:** 2026-10-01  
**Repository:** [camel-ai/camel](https://github.com/camel-ai/camel) (17.6K stars, Apache-2.0)  
**Companion:** [camel-ai/oasis](https://github.com/camel-ai/oasis) (5.1K stars)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Key Features for Ahmed's Stack](#2-key-features-for-ahmeds-stack)
3. [Integration Guide: Simulating 330 Agent Slots](#3-integration-guide-simulating-330-agent-slots)
4. [Configuration Examples](#4-configuration-examples)
5. [Using Results for Capacity Planning](#5-using-results-for-capacity-planning)
6. [Pitfalls and Best Practices](#6-pitfalls-and-best-practices)

---

## 1. Architecture Overview

### 1.1 What CAMEL-AI Is

CAMEL (Communicative Agents for "Mind" Exploration of Large Language Model Society) is the first open-source multi-agent framework purpose-built for **finding the scaling laws of agents**. Published at NeurIPS 2023 (arXiv:2303.17760), it has evolved from a two-agent role-playing prototype into a full-stack framework supporting up to **1 million concurrent agents** in simulation.

**Core insight:** When two LLM agents converse without constraints, they drift roles within 2-3 exchanges. CAMEL's solution — **inception prompting** — locks each agent's role via system prompts that cannot be overwritten mid-conversation. This is the foundation for all higher-level coordination.

### 1.2 Four Design Principles

| Principle | What It Means |
|---|---|
| **Evolvability** | Agents improve via RL or supervised learning from their own interactions |
| **Scalability** | Architecture supports millions of agents with efficient coordination |
| **Statefulness** | Context as explicit state transition, not accumulated chat history |
| **Code-as-Prompt** | Every line of code is legible as a prompt; agents can extend the system |

### 1.3 Core Abstractions (Layered Architecture)

```
┌─────────────────────────────────────────────────────┐
│                  OASIS (World Simulation)            │
│         1M agents · social networks · time engine    │
├─────────────────────────────────────────────────────┤
│              Workforce (N-Agent Orchestration)      │
│    Coordinator → Task Planner → Workers (parallel)   │
│    · Hierarchical decomposition · failure recovery   │
│    · Dynamic worker creation · HITL support          │
├─────────────────────────────────────────────────────┤
│           RolePlaying (2-Agent Coordination)         │
│    AI User ↔ AI Assistant · inception prompting         │
│    · task specification · critic-in-the-loop         │
├─────────────────────────────────────────────────────┤
│              ChatAgent (Atomic Reasoning Unit)       │
│    LLM backend · memory · tools · structured output  │
├─────────────────────────────────────────────────────┤
│              Model Layer (20+ backends)              │
│    OpenAI · Anthropic · Gemini · vLLM · Ollama · ... │
└─────────────────────────────────────────────────────┘
```

### 1.4 Key Components

| Module | Description |
|---|---|
| **Agents** | `ChatAgent` (primary), `CriticAgent`, `ToolAgent` — atomic reasoning units with memory, tool access, LLM backend |
| **Agent Societies** | `RolePlaying` (2-agent), `Workforce` (N-agent hierarchical), `BabyAGI` |
| **Interpreters** | Python, shell, Docker, browser — live code evaluation |
| **Memory** | `ChatHistoryMemory`, `VectorDBMemory` (Qdrant/pgvector), `LongtermAgentMemory` |
| **Storage** | JSON, key-value, vector storage backends |
| **Tools** | 100+ toolkits: Search, Code Execution, Browser, GitHub, Google Drive, SQL, MCP |
| **RAG Pipelines** | Chunking → retrieval → generation |
| **Synthetic Data** | Self-Instruct, CoT, Source2Synth with verifier loops |
| **World Simulation** | OASIS — million-agent social media simulation |
| **Benchmarks** | CRAB (cross-environment automation), GAIA, MMLU, etc. |

### 1.5 OASIS: The Million-Agent Simulation Engine

OASIS (Open Agent Social Interaction Simulations, NeurIPS 2024) is CAMEL's flagship scaling experiment. It simulates up to **1M LLM-powered agents** on Twitter-like and Reddit-like platforms.

**Five core components:**

1. **Environment Server** — Relational database (SQLite) of users, posts, comments, follows, action histories
2. **Recommendation System** — Dual algorithms: interest-based (TwHIN-BERT embeddings) and hot-score ranking
3. **Agent Module** — Each agent has memory, 23-action space, chain-of-thought reasoning
4. **Time Engine** — 24-dimensional hourly activity vector for probabilistic agent activation
5. **Scalable Inferencer** — Async message channels + GPU manager for distributed LLM inference

**Key finding:** Emergent phenomena (information cascades, opinion polarization, herd effects) only reliably appear **above ~10,000 agents**. Scale is a scientific requirement, not just a performance goal.

---

## 2. Key Features for Ahmed's Stack

### 2.1 Simulate Up to 1M Agents

| Capability | Detail |
|---|---|
| **Workforce** | N-agent hierarchical orchestration with coordinator, task planner, and parallel workers |
| **OASIS** | Purpose-built for million-agent social simulation with database-first design |
| **Agent Pool** | `SingleAgentWorker` uses `AgentPool` (default max 10) to reuse agent instances efficiently |
| **Async Execution** | `asyncio`-based; workers execute in parallel without manual thread management |
| **Nested Workforces** | `add_workforce()` nests one workforce inside another for hierarchical scaling |
| **Dynamic Workers** | New workers created at runtime when tasks fail repeatedly |

### 2.2 Emergent Behavior Study

| Feature | How CAMEL Enables It |
|---|---|
| **Role Diversity** | Each agent gets a unique system prompt; roles are locked via inception prompting |
| **Memory Systems** | `LongtermAgentMemory` combines chat history + vector DB for persistent agent state |
| **Tool Access** | Agents can be equipped with different toolkits (Search, Code, Browser) for behavioral diversity |
| **Action Space** | OASIS provides 23 distinct actions (post, comment, like, follow, mute, search, etc.) |
| **Network Topology** | Dynamic follow/mute graphs evolve during simulation |
| **Recommendation Effects** | Dual RecSys (interest-based + hot-score) shapes information flow |
| **Time Engine** | Probabilistic activation patterns simulate realistic daily rhythms |

### 2.3 Scaling Laws Research

CAMEL-AI's research program specifically investigates:
- **Agent count scaling** — How does performance change with N agents?
- **Agent diversity scaling** — Does role heterogeneity help or hurt?
- **Communication topology** — How does network structure affect outcomes?
- **Environment complexity** — How does task difficulty interact with agent count?

**Published findings:**
- Unconstrained agent pairs fail within 2-3 exchanges (role drift)
- Inception prompting prevents role drift but introduces rigidity
- Workforce coordinator can hallucinate task decomposition → cascading failures
- OASIS: Uncensored LLMs polarize harder than aligned counterparts; agents herd more aggressively than real humans

### 2.4 Synthetic Data Generation

CAMEL's data generation pipeline produced 25,000 domain-expert conversations used to train:
- Databricks MPT-30B-Chat
- Microsoft Phi
- Teknium OpenHermes

This is directly relevant for generating training data for Ahmed's agent models.

### 2.5 Model Flexibility

```python
# Switch backends without changing agent code
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

# OpenAI
model = ModelFactory.create(model_platform=ModelPlatformType.OPENAI, model_type=ModelType.GPT_4O_MINI)

# Anthropic
model = ModelFactory.create(model_platform=ModelPlatformType.ANTHROPIC, model_type=ModelType.CLAUDE_HAIKU_4_5)

# Local vLLM
model = ModelFactory.create(model_platform=ModelPlatformType.VLLM, model_type="qwen-2", url="http://localhost:8000/v1")

# Ollama
model = ModelFactory.create(model_platform=ModelPlatformType.OLLAMA, model_type="llama3", url="http://localhost:11434/v1")
```

---

## 3. Integration Guide: Simulating 330 Agent Slots

### 3.1 Architecture Decision: Workforce vs OASIS

| Criteria | Workforce | OASIS |
|---|---|---|
| **Best for** | Task-oriented multi-agent work | Social simulation / emergent behavior |
| **Agent count** | 10-1,000 practical | 100-1M |
| **Coordination** | Hierarchical (coordinator → workers) | Decentralized (agent graph) |
| **State** | Task DAG + shared memory | Relational database |
| **Use case for 330** | ✅ Task decomposition, parallel processing | ✅ Social dynamics, opinion formation |

**Recommendation:** Use **Workforce** for 330-agent task-oriented simulation. Use **OASIS** if studying social/information dynamics.

### 3.2 Workforce Architecture for 330 Agents

```
                    ┌──────────────────┐
                    │  Coordinator     │
                    │  (1 agent)       │
                    │  Routes subtasks │
                    └────────┬─────────┘
                             │
                    ┌────────┴─────────┐
                    │  Task Planner    │
                    │  (1 agent)       │
                    │  Decomposes task │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
     ┌──────┴──────┐  ┌─────┴──────┐  ┌─────┴──────┐
     │ Worker Pool │  │ Worker Pool│  │ Worker Pool│
     │  (110 agents)│  │ (110 agents)│  │ (108 agents)│
     │  Search     │  │  Code      │  │  Analysis  │
     └─────────────┘  └────────────┘  └────────────┘
```

**Total: 1 coordinator + 1 task planner + 328 workers = 330 agents**

### 3.3 Step-by-Step Implementation

#### Step 1: Install

```bash
pip install camel-ai[all]
# Or minimal: pip install camel-ai
# With specific toolkits: pip install 'camel-ai[web_tools,code_tools]'
```

#### Step 2: Create the 330-Agent Workforce

```python
import asyncio
from camel.societies.workforce import Workforce
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig
from camel.memories import (
    LongtermAgentMemory,
    ChatHistoryBlock,
    VectorDBBlock,
    ScoreBasedContextCreator,
)
from camel.utils import OpenAITokenCounter

# ─── Model Configuration ───────────────────────────────────
model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O_MINI,
    model_config_dict=ChatGPTConfig(temperature=0.2).as_dict(),
)

# ─── Memory Configuration ──────────────────────────────────
def create_memory():
    return LongtermAgentMemory(
        context_creator=ScoreBasedContextCreator(
            token_counter=OpenAITokenCounter(ModelType.GPT_4O_MINI),
            token_limit=2048,
        ),
        chat_history_block=ChatHistoryBlock(),
        vector_db_block=VectorDBBlock(),
    )

# ─── Worker Factory ────────────────────────────────────────
def create_worker(agent_id: int, role: str, tools: list = None):
    """Create a single worker agent with role-specific configuration."""
    sys_msg = (
        f"You are Agent-{agent_id}, a {role}. "
        f"Never flip roles. Complete your assigned task efficiently. "
        f"Output structured results when possible."
    )
    return ChatAgent(
        system_message=sys_msg,
        model=model,
        memory=create_memory(),
        message_window_size=10,
        tools=tools or [],
    )

# ─── Build the 330-Agent Workforce ─────────────────────────
workforce = Workforce(
    description="330-Agent Scaling Simulation Workforce",
    share_memory=False,  # Each worker has independent memory
    use_structured_output_handler=True,
    graceful_shutdown_timeout=30.0,
    task_timeout_seconds=600.0,
)

# Role distribution for 328 workers
ROLE_DISTRIBUTION = {
    "researcher": 82,      # Web search, information gathering
    "coder": 82,           # Code generation, execution
    "analyst": 82,         # Data analysis, reasoning
    "reviewer": 82,        # Quality review, critique
}

agent_id = 0
for role, count in ROLE_DISTRIBUTION.items():
    for _ in range(count):
        # Assign role-specific tools
        tools = []
        if role == "researcher":
            from camel.toolkits import SearchToolkit
            tools = [SearchToolkit().search_duckduckgo]
        elif role == "coder":
            from camel.toolkits import CodeExecutionToolkit
            tools = CodeExecutionToolkit(sandbox="docker").get_tools()
        elif role == "analyst":
            from camel.toolkits import MathToolkit, SearchToolkit
            tools = MathToolkit().get_tools() + [SearchToolkit().search_duckduckgo]
        elif role == "reviewer":
            from camel.toolkits import SearchToolkit
            tools = [SearchToolkit().search_duckduckgo]

        worker = create_worker(agent_id, role, tools)
        workforce.add_single_agent_worker(
            description=f"{role.capitalize()} Agent-{agent_id}",
            worker=worker,
            pool_max_size=10,
        )
        agent_id += 1

print(f"Workforce initialized with {agent_id} workers + 2 coordinators = {agent_id + 2} agents")
```

#### Step 3: Define the Simulation Task

```python
from camel.tasks import Task

# The task that will be decomposed and distributed
simulation_task = Task(
    content=(
        "Simulate a large-scale multi-agent system processing 10,000 "
        "independent research queries. Each query requires: "
        "(1) web research, (2) code implementation, "
        "(3) data analysis, and (4) quality review. "
        "Measure throughput, latency, token consumption, and "
        "result quality at 330-agent scale."
    ),
    id="scaling-sim-001",
)
```

#### Step 4: Run the Simulation

```python
async def run_simulation():
    # Process the task through the workforce
    result = await workforce.process_task(simulation_task)
    
    # Collect metrics
    print(f"Task completed: {result.id}")
    print(f"Result: {result.result}")
    print(f"Status: {result.status}")
    
    # Access individual task results
    for task in workforce.task_channel.tasks:
        print(f"  Task {task.id}: {task.status} -> {task.result}")

asyncio.run(run_simulation())
```

### 3.4 Alternative: OASIS for Social Simulation

If the goal is studying emergent social behavior rather than task completion:

```python
import asyncio
import oasis
from oasis import ActionType, LLMAction, ManualAction, generate_reddit_agent_graph

async def run_oasis_simulation():
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    
    available_actions = [
        ActionType.CREATE_POST,
        ActionType.CREATE_COMMENT,
        ActionType.LIKE_POST,
        ActionType.DISLIKE_POST,
        ActionType.FOLLOW,
        ActionType.MUTE,
        ActionType.SEARCH_POSTS,
        ActionType.TREND,
        ActionType.REFRESH,
        ActionType.DO_NOTHING,
    ]
    
    # Generate 330-agent graph
    agent_graph = await generate_reddit_agent_graph(
        profile_path="./data/reddit/user_data_36.json",
        model=model,
        available_actions=available_actions,
    )
    
    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.REDDIT,
        database_path="./data/simulation_330.db",
    )
    
    await env.reset()
    
    # Seed with manual actions
    seed_actions = {
        env.agent_graph.get_agent(0): ManualAction(
            action_type=ActionType.CREATE_POST,
            action_args={"content": "Scaling simulation: 330 agents"}
        ),
    }
    await env.step(seed_actions)
    
    # Run simulation steps
    for step in range(100):
        llm_actions = {agent: LLMAction() for _, agent in env.agent_graph.get_agents()}
        await env.step(llm_actions)
    
    await env.close()

asyncio.run(run_oasis_simulation())
```

---

## 4. Configuration Examples

### 4.1 Simulation Setup Config

```python
# config.py — Central configuration for 330-agent simulation

from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class SimulationConfig:
    # Agent counts
    total_agents: int = 330
    coordinator_agents: int = 2  # coordinator + task planner
    worker_agents: int = 328
    
    # Role distribution
    role_distribution: Dict[str, int] = field(default_factory=lambda: {
        "researcher": 82,
        "coder": 82,
        "analyst": 82,
        "reviewer": 82,
    })
    
    # Model configuration
    model_platform: str = "openai"
    model_type: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tokens: int = 4096
    
    # Memory configuration
    memory_type: str = "longterm"  # chat_history, vector_db, longterm
    message_window_size: int = 10
    vector_token_limit: int = 2048
    
    # Workforce configuration
    pool_max_size: int = 10
    task_timeout_seconds: int = 600
    graceful_shutdown_timeout: float = 30.0
    share_memory: bool = False
    use_structured_output_handler: bool = True
    
    # Failure handling
    max_retries: int = 3
    enabled_strategies: List[str] = field(default_factory=lambda: [
        "retry", "replan", "decompose", "reassign", "create_new_worker"
    ])
    halt_on_max_retries: bool = True
    
    # Simulation parameters
    num_simulation_steps: int = 100
    activation_probability: float = 0.1  # For OASIS-style time engine
    queries_per_step: int = 100
    
    # Cost tracking
    track_token_usage: bool = True
    track_latency: bool = True
    cost_budget_usd: Optional[float] = 100.0

# Usage
config = SimulationConfig()
```

### 4.2 Model Tier Configuration (Cost Optimization)

```python
# Use different models for different roles to optimize cost
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

# Coordinator: needs strong reasoning → use better model
coordinator_model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O,  # Stronger model for coordination
    model_config_dict={"temperature": 0.0, "max_tokens": 4096},
)

# Workers: high volume, simpler tasks → use cheaper model
worker_model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O_MINI,  # Cheaper for high-volume work
    model_config_dict={"temperature": 0.2, "max_tokens": 2048},
)

# Reviewer: needs critical thinking → mid-tier
reviewer_model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O_MINI,
    model_config_dict={"temperature": 0.1, "max_tokens": 2048},
)
```

### 4.3 Memory Configuration Patterns

```python
# Pattern 1: Chat History Only (cheapest, shortest context)
from camel.memories import ChatHistoryMemory, ScoreBasedContextCreator
from camel.utils import OpenAITokenCounter
from camel.types import ModelType

memory = ChatHistoryMemory(
    context_creator=ScoreBasedContextCreator(
        token_counter=OpenAITokenCounter(ModelType.GPT_4O_MINI),
        token_limit=2048,
    ),
    message_window_size=10,
)

# Pattern 2: Long-term Memory (chat history + vector DB)
from camel.memories import LongtermAgentMemory, ChatHistoryBlock, VectorDBBlock

memory = LongtermAgentMemory(
    context_creator=ScoreBasedContextCreator(
        token_counter=OpenAITokenCounter(ModelType.GPT_4O_MINI),
        token_limit=2048,
    ),
    chat_history_block=ChatHistoryBlock(),
    vector_db_block=VectorDBBlock(),  # Uses Qdrant by default
)

# Pattern 3: Shared Memory across workers (for collective learning)
workforce = Workforce(
    description="330-Agent Simulation with Shared Memory",
    share_memory=True,  # Workers share collected memory
)
```

### 4.4 Failure Recovery Configuration

```python
from camel.societies.workforce.utils import FailureHandlingConfig, RecoveryStrategy

failure_config = FailureHandlingConfig(
    max_retries=3,
    enabled_strategies=[
        RecoveryStrategy.RETRY,
        RecoveryStrategy.REPLAN,
        RecoveryStrategy.DECOMPOSE,
        RecoveryStrategy.REASSIGN,
        RecoveryStrategy.CREATE_NEW_WORKER,
    ],
    halt_on_max_retries=True,  # Stop entire workforce if task keeps failing
)
```

### 4.5 Human-in-the-Loop Configuration

```python
from camel.toolkits import HumanToolkit

human_toolkit = HumanToolkit()
human_tools = human_toolkit.get_tools()  # ask_human_via_console, send_message_to_user

coordinator = ChatAgent(
    system_message="You coordinate tasks. Ask a human for help when needed.",
    tools=human_tools,
    model=coordinator_model,
)

workforce = Workforce(
    description="330-Agent Simulation with HITL",
    coordinator_agent=coordinator,
)
```

---

## 5. Using Results for Capacity Planning

### 5.1 Metrics to Collect

```python
import time
from dataclasses import dataclass, field
from typing import List

@dataclass
class SimulationMetrics:
    # Throughput
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    tasks_per_second: float = 0.0
    
    # Latency
    avg_task_latency_seconds: float = 0.0
    p50_task_latency_seconds: float = 0.0
    p99_task_latency_seconds: float = 0.0
    
    # Token consumption
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    
    # Agent utilization
    agent_utilization: Dict[str, float] = field(default_factory=dict)
    # e.g., {"researcher": 0.85, "coder": 0.92, ...}
    
    # Failure analysis
    failure_counts: Dict[str, int] = field(default_factory=dict)
    # e.g., {"retry": 12, "replan": 3, "timeout": 1}
    
    # Scaling behavior
    # Key: how do metrics change as agent count increases?
    scaling_data: List[dict] = field(default_factory=list)
```

### 5.2 Scaling Law Measurement

```python
def measure_scaling_laws():
    """
    Run simulations at different agent counts and measure
    how throughput, latency, and quality scale.
    """
    agent_counts = [10, 50, 100, 150, 200, 250, 330, 500, 1000]
    results = []
    
    for n_agents in agent_counts:
        config = SimulationConfig(
            total_agents=n_agents,
            worker_agents=n_agents - 2,
        )
        
        metrics = run_simulation_with_config(config)
        
        results.append({
            "agent_count": n_agents,
            "throughput": metrics.tasks_per_second,
            "avg_latency": metrics.avg_task_latency_seconds,
            "total_cost": metrics.total_cost_usd,
            "failure_rate": metrics.total_tasks_failed / max(metrics.total_tasks_completed, 1),
            "agent_utilization": sum(metrics.agent_utilization.values()) / len(metrics.agent_utilization),
        })
    
    return results

# Analyze scaling behavior
def analyze_scaling(results):
    """
    Fit power law: performance = k * N^alpha
    where N = agent count, alpha = scaling exponent
    """
    import numpy as np
    
    counts = np.array([r["agent_count"] for r in results])
    throughput = np.array([r["throughput"] for r in results])
    
    # Log-log fit
    log_n = np.log(counts)
    log_t = np.log(throughput)
    
    # Linear regression in log space
    alpha, log_k = np.polyfit(log_n, log_t, 1)
    k = np.exp(log_k)
    
    print(f"Scaling law: throughput = {k:.4f} * N^{alpha:.4f}")
    print(f"Scaling exponent: {alpha:.4f}")
    print(f"  α > 1: superlinear (agents help each other)")
    print(f"  α = 1: linear (perfect scaling)")
    print(f"  α < 1: sublinear (coordination overhead dominates)")
    
    return k, alpha
```

### 5.3 Capacity Planning Framework

```python
def capacity_plan(simulation_results, target_throughput: float):
    """
    Given simulation results, determine:
    1. How many agents needed for target throughput
    2. Expected cost at that scale
    3. Bottleneck identification
    4. Recommended configuration
    """
    # Find minimum agent count for target throughput
    for result in simulation_results:
        if result["throughput"] >= target_throughput:
            recommended_agents = result["agent_count"]
            break
    else:
        recommended_agents = simulation_results[-1]["agent_count"]
        print(f"Warning: Target throughput not reached even at {recommended_agents} agents")
    
    # Cost projection
    cost_per_agent = simulation_results[-1]["total_cost"] / simulation_results[-1]["agent_count"]
    projected_cost = recommended_agents * cost_per_agent
    
    # Bottleneck analysis
    utilization = simulation_results[-1]["agent_utilization"]
    bottleneck_role = max(utilization, key=utilization.get)
    
    plan = {
        "recommended_agents": recommended_agents,
        "projected_monthly_cost": projected_cost * 30 * 24,  # Assuming continuous operation
        "bottleneck_role": bottleneck_role,
        "scaling_exponent": None,  # From analyze_scaling()
        "headroom_recommendation": f"Add 20% more {bottleneck_role} agents for safety",
    }
    
    return plan
```

### 5.4 Token Cost Estimation

Based on OASIS published data (100 agents, 1 step, activation=1.0):
- Input: 335,600 tokens
- Output: 16,750 tokens
- Total: ~352,350 tokens per step

For 330 agents:
```
Estimated tokens per step = 352,350 × (330/100) = 1,162,755 tokens
At GPT-4o-mini pricing ($0.15/1M input, $0.60/1M output):
  Input cost: 1,122,755 × $0.15/1M = $0.168
  Output cost: 40,000 × $0.60/1M = $0.024
  Total per step: ~$0.19
  100 steps: ~$19.30
  1,000 steps: ~$193
```

### 5.5 Key Capacity Planning Outputs

| Metric | How to Use |
|---|---|
| **Scaling exponent (α)** | Predict performance at untested agent counts |
| **Agent utilization** | Identify which role is the bottleneck |
| **Failure rate vs agent count** | Determine if more agents increase coordination failures |
| **Cost per task** | Budget forecasting and cost optimization |
| **Latency distribution** | SLA planning (p50, p99) |
| **Token consumption per agent** | API rate limit planning |

---

## 6. Pitfalls and Best Practices

### 6.1 Critical Pitfalls

| Pitfall | Why It Happens | Mitigation |
|---|---|---|
| **Coordinator hallucination** | Task planner decomposes incorrectly → all downstream work is wrong | Use `with_critic_in_the_loop=True`; add verifier agent; set `halt_on_max_retries=True` |
| **Role drift** | Agents forget their assigned role mid-conversation | Inception prompting (built into RolePlaying); explicit "Never flip roles!" in system prompts |
| **Infinite loops** | Agents keep talking without completing task | Set `chat_turn_limit`; use `CAMEL_TASK_DONE` termination keyword; set `task_timeout_seconds` |
| **Token explosion** | Each turn re-sends all prior context → quadratic cost growth | Use `message_window_size`; `prune_tool_calls_from_memory=True`; `summarize_threshold=50` |
| **Context window overflow** | Long conversations exceed model's context limit | Use `LongtermAgentMemory` with vector DB; set `token_limit` on agents |
| **API rate limiting** | 330 agents × multiple steps = thousands of API calls | Use `ModelManager` with `round_robin` scheduling; add retry logic; use local models (vLLM/Ollama) |
| **Memory bloat** | All agents storing full conversation history | Use `ChatHistoryMemory` with window; periodically call `agent.reset()` |
| **Cascading failures** | One failed subtask blocks dependent tasks | Use `FailureHandlingConfig` with `halt_on_max_retries=True`; design task DAG with loose coupling |
| **Cost overruns** | Unbounded agent loops consume tokens uncontrollably | Set `token_limit` per agent; use `cost_budget_usd` guardrail; monitor with callbacks |
| **OASIS cost surprise** | Million-agent simulation requires ~27 A100-equivalent GPUs | Start with 100 agents; use `activation_probability=0.1`; use cheaper models (GPT-4o-mini) |

### 6.2 Best Practices

#### Agent Design
1. **Scope toolkits per role** — Don't give every agent every tool. A SearchAgent doesn't need CodeExecutionToolkit. This reduces noise and latency.
2. **Use structured output** — Set `response_format` to Pydantic models for reliable parsing.
3. **Set explicit termination** — Always define a termination keyword (`CAMEL_TASK_DONE`) in system prompts.
4. **Limit message windows** — `message_window_size=10` prevents context explosion.

#### Workforce Configuration
5. **Start small, scale up** — Test with 10 agents, then 50, then 100, then 330. Measure at each step.
6. **Use `share_memory=True` cautiously** — Only when agents need collective learning. Increases token usage.
7. **Set `task_timeout_seconds`** — Prevents hung tasks from blocking the entire workforce.
8. **Enable structured output handler** — `use_structured_output_handler=True` for models without native JSON tool-calling.

#### Cost Management
9. **Use model tiering** — Coordinator gets GPT-4o, workers get GPT-4o-mini. 80% cost reduction with minimal quality loss.
10. **Track token usage per agent** — Use `OpenAITokenCounter` and log consumption by role.
11. **Set hard budget limits** — Kill switches at $X per simulation run.
12. **Use local models for high-volume workers** — vLLM or Ollama for worker agents; API models only for coordinator.

#### Simulation Design
13. **Measure before scaling** — Run 10-agent baseline first. Extrapolate before running 330.
14. **Use activation probability** — Not all 330 agents need to act every step. `activation_probability=0.1` means ~33 agents per step.
15. **Design for decomposability** — Google Research found multi-agent helps parallelizable tasks (+80.9%) but hurts sequential tasks (-39% to -70%). Ensure your task decomposes cleanly.
16. **Add observability early** — Use `WorkforceCallback` to log every task assignment, completion, and failure.

#### OASIS-Specific
17. **Use `generate_agents_100w` for large scale** — Returns list instead of AgentGraph for performance.
18. **Use `recsys_type="random"` for large scale** — Fastest recommendation algorithm.
19. **Batch database operations** — OASIS uses batch SQL insertions for million-agent scale.
20. **Plan GPU resources** — ~27 A100-equivalent GPUs for 1M agents at 3-minute steps.

### 6.3 Recommended Simulation Protocol for 330 Agents

```
Phase 1: Baseline (1 agent)
  └─ Measure single-agent throughput, latency, cost

Phase 2: Small team (10 agents)
  └─ Validate Workforce coordination overhead
  └─ Measure scaling exponent

Phase 3: Medium scale (50-100 agents)
  └─ Identify bottlenecks
  └─ Tune role distribution
  └─ Validate failure recovery

Phase 4: Target scale (330 agents)
  └─ Full simulation with all metrics
  └─ Multiple runs for statistical significance
  └─ Cost analysis and capacity planning

Phase 5: Stress test (500-1000 agents)
  └─ Find breaking point
  └─ Measure coordination overhead saturation
  └─ Determine maximum practical scale
```

### 6.4 Quick Reference: CAMEL API for 330-Agent Simulation

```python
# Essential imports
from camel.societies.workforce import Workforce
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig
from camel.memories import LongtermAgentMemory, ChatHistoryBlock, VectorDBBlock, ScoreBasedContextCreator
from camel.utils import OpenAITokenCounter
from camel.tasks import Task
from camel.toolkits import SearchToolkit, CodeExecutionToolkit, HumanToolkit

# Key classes
Workforce(
    description="...",
    coordinator_agent=...,      # Custom coordinator
    task_agent=...,            # Custom task planner
    new_worker_agent=...,      # Template for dynamic workers
    share_memory=False,        # Share memory across workers
    task_timeout_seconds=600,  # Per-task timeout
    graceful_shutdown_timeout=30.0,
    use_structured_output_handler=True,
)

workforce.add_single_agent_worker(description="...", worker=agent, pool_max_size=10)
workforce.add_role_playing_worker(description="...", assistant_role_name="...", user_role_name="...")
workforce.add_workforce(nested_workforce)  # Hierarchical nesting
workforce.process_task(task)  # Run the full pipeline
workforce.add_parallel_pipeline_tasks([...])  # Add parallel tasks
```

---

## Appendix A: OASIS Token Cost Reference

| Agents | Activation | Steps | Model | Input Tokens | Output Tokens | Est. Cost (Qwen) |
|---|---|---|---|---|---|---|
| 100 | 1.0 | 1 | QWEN_TURBO | 335,600 | 16,750 | ¥0.027 |
| 1,000 | 0.1 | 1 | QWEN_TURBO | — | — | ¥0.268 |
| 10,000 | 0.1 | 1 | QWEN_TURBO | — | — | ¥2.68 |
| 1,000 | 0.1 | 1 | QWEN_MAX | — | — | ¥7.72 |
| 10,000 | 0.1 | 1 | QWEN_MAX | — | — | ¥77.17 |

**For 330 agents (estimated):** ~1.16M input tokens, ~55K output tokens per step at full activation.

## Appendix B: Key Research Papers

1. **CAMEL (NeurIPS 2023):** arXiv:2303.17760 — Role-playing framework, inception prompting
2. **OASIS (NeurIPS 2024):** arXiv:2411.11581 — Million-agent social simulation
3. **CRAB (NeurIPS 2024):** arXiv:2410.18701 — Cross-environment agent benchmark
4. **OWL (NeurIPS 2025):** Optimized Workforce Learning for real-world task automation
5. **Scaling Environments for Agents (2025):** CAMEL-AI blog — RL environments for agent learning

## Appendix C: Repository Structure

```
camel-ai/camel/
├── camel/
│   ├── agents/           # ChatAgent, CriticAgent, ToolAgent
│   ├── societies/        # RolePlaying, Workforce, BabyAGI
│   │   └── workforce/    # Workforce, SingleAgentWorker, RolePlayingWorker
│   ├── models/           # ModelFactory, 20+ backends
│   ├── memories/         # ChatHistoryMemory, VectorDBMemory, LongtermAgentMemory
│   ├── toolkits/         # 100+ tools (Search, Code, Browser, etc.)
│   ├── tasks/            # Task data structures
│   ├── configs/          # ChatGPTConfig, OpenSourceConfig, etc.
│   ├── interpreters/     # Python, shell, Docker, browser
│   ├── storages/         # JSON, key-value, vector storage
│   └── utils/            # Token counters, logging, etc/
├── examples/             # Workforce, RolePlaying, OASIS examples
├── docs/                 # Documentation
└── tests/                # Test suite
```

---

*This guide was produced from research of CAMEL-AI's public documentation, GitHub repository, published papers, and community resources. All code examples are based on the camel-ai 0.2.x API. Verify against the latest documentation at docs.camel-ai.org before production deployment.*
