# Autonomous Campaign Optimization Implementation Plan

## LangChain DeepAgents — Agentic AI Marketing Systems

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Ahmed Hassan  
**Stack:** LangChain DeepAgents, Python 3.11+, LangGraph, FastAPI, Redis, PostgreSQL

---

## Table of Contents

1. [Agent Architecture (Planner, Executor, Critic)](#1-agent-architecture)
2. [Campaign Management Agent](#2-campaign-management-agent)
3. [Budget Optimization Agent](#3-budget-optimization-agent)
4. [Creative Generation Agent](#4-creative-generation-agent)
5. [A/B Testing Agent](#5-ab-testing-agent)
6. [Performance Analytics Agent](#6-performance-analytics-agent)
7. [Real-Time Optimization Loops](#7-real-time-optimization-loops)
8. [Ad Platform Integration](#8-ad-platform-integration)
9. [Code Examples and Snippets](#9-code-examples-and-snippets)
10. [Testing Strategy](#10-testing-strategy)

---

## 1. Agent Architecture

### 1.1 High-Level Architecture

The system follows a **hierarchical multi-agent architecture** built on LangChain DeepAgents with LangGraph orchestration. Three core agent roles form the backbone:

```
┌─────────────────────────────────────────────────────────┐
│                    Orchestrator (LangGraph)              │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Planner  │→ │  Executor    │→ │     Critic        │  │
│  │  Agent   │  │   Agents     │  │     Agent         │  │
│  └──────────┘  └──────────────┘  └───────────────────┘  │
│       ↑               │                    │             │
│       └───────────────┴────────────────────┘             │
│                    Feedback Loop                          │
└─────────────────────────────────────────────────────────┘
         │                │                  │
    ┌────▼────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │ Campaign │     │  Budget   │     │  Creative │
    │  Agent   │     │  Agent    │     │  Agent    │
    └─────────┘     └───────────┘     └───────────┘
         │                │                  │
    ┌────▼────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │  A/B    │     │Performance│     │  Ad Platform│
    │ Testing │     │ Analytics │     │  Connectors │
    │  Agent  │     │  Agent    │     │             │
    └─────────┘     └───────────┘     └─────────────┘
```

### 1.2 Planner Agent

The Planner decomposes high-level marketing objectives into actionable sub-tasks, assigns them to specialized agents, and manages dependencies.

**Responsibilities:**
- Parse marketing goals (e.g., "Increase ROAS by 20% in Q4")
- Decompose into sub-tasks (budget reallocation, creative refresh, audience expansion)
- Build a DAG of task dependencies
- Assign tasks to specialized executor agents
- Set success criteria and constraints per task

**System Prompt:**
```python
PLANNER_SYSTEM_PROMPT = """
You are the Campaign Planning Agent. Your role is to decompose high-level marketing
objectives into concrete, executable sub-tasks.

For each objective, produce:
1. A list of sub-tasks with clear success criteria
2. Dependencies between tasks (DAG)
3. Priority ordering based on expected impact
4. Resource constraints (budget caps, time windows, platform limits)
5. Risk assessment for each sub-task

You coordinate with specialized agents:
- CampaignAgent: campaign lifecycle management
- BudgetAgent: budget allocation and pacing
- CreativeAgent: ad creative generation and iteration
- ABTestAgent: experiment design and analysis
- AnalyticsAgent: performance monitoring and reporting

Always include rollback plans for high-risk operations.
"""
```

**Implementation:**
```python
from langchain_deepagents import DeepAgent
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage

class PlannerState(TypedDict):
    objective: str
    sub_tasks: list[dict]
    task_dependencies: dict[str, list[str]]
    assignments: dict[str, str]  # task_id -> agent_name
    constraints: dict
    current_step: int
    messages: Annotated[Sequence[BaseMessage], "message_history"]

def create_planner_agent(llm):
    agent = DeepAgent(
        name="planner",
        llm=llm,
        system_prompt=PLANNER_SYSTEM_PROMPT,
        tools=[marketing_kpi_lookup, historical_performance_query],
        max_iterations=10,
    )
    return agent

def planner_node(state: PlannerState) -> PlannerState:
    agent = create_planner_agent(get_llm())
    result = agent.invoke({
        "input": state["objective"],
        "context": {
            "constraints": state["constraints"],
            "completed_tasks": state.get("completed_tasks", []),
        }
    })
    state["sub_tasks"] = result["sub_tasks"]
    state["task_dependencies"] = result["dependencies"]
    state["assignments"] = result["assignments"]
    return state
```

### 1.3 Executor Agents

Executors are specialized agents that perform the actual work. Each executor has domain-specific tools and a focused scope.

**Executor Types:**

| Executor | Tools | Output |
|----------|-------|--------|
| CampaignAgent | create_campaign, pause_campaign, update_targeting, archive_campaign | Campaign config changes |
| BudgetAgent | adjust_bid, reallocate_budget, set_pacing, forecast_spend | Budget allocation updates |
| CreativeAgent | generate_creative, score_creative, variant_creative | New creative assets |
| ABTestAgent | create_experiment, analyze_results, promote_variant | Experiment decisions |
| AnalyticsAgent | query_metrics, generate_report, detect_anomaly | Performance insights |

**Base Executor Pattern:**
```python
from abc import ABC, abstractmethod
from langchain_deepagents import DeepAgent

class BaseExecutorAgent(ABC):
    def __init__(self, name: str, llm, tools: list, system_prompt: str):
        self.agent = DeepAgent(
            name=name,
            llm=llm,
            system_prompt=system_prompt,
            tools=tools,
            max_iterations=15,
            verbose=True,
        )
        self.execution_log = []

    @abstractmethod
    def validate_preconditions(self, task: dict) -> bool:
        """Check if the task can be executed safely."""
        pass

    @abstractmethod
    def rollback(self, task: dict) -> bool:
        """Undo the task if critic rejects."""
        pass

    def execute(self, task: dict) -> dict:
        if not self.validate_preconditions(task):
            return {"status": "blocked", "reason": "preconditions_failed"}

        result = self.agent.invoke({
            "input": task["description"],
            "parameters": task.get("parameters", {}),
            "constraints": task.get("constraints", {}),
        })

        self.execution_log.append({
            "task_id": task["id"],
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return {
            "status": "completed",
            "task_id": task["id"],
            "output": result,
            "artifacts": result.get("artifacts", []),
        }
```

### 1.4 Critic Agent

The Critic evaluates executor outputs against success criteria, detects regressions, and decides whether to accept, retry, or rollback.

**Responsibilities:**
- Compare executor output against task success criteria
- Detect performance regressions (e.g., CPA increase after budget change)
- Validate constraint compliance (budget caps, brand safety)
- Decide: ACCEPT / RETRY / ROLLBACK / ESCALATE
- Provide feedback for retry attempts

**Implementation:**
```python
CRITIC_SYSTEM_PROMPT = """
You are the Campaign Critic Agent. You evaluate the outputs of executor agents
and decide whether changes should be accepted, retried, or rolled back.

Evaluation criteria:
1. Did the output meet the task's success criteria?
2. Are all constraints still satisfied?
3. Is there evidence of regression in related metrics?
4. Is the change reversible if it underperforms?

Decision options:
- ACCEPT: Output meets all criteria
- RETRY: Output is close but needs refinement (provide specific feedback)
- ROLLBACK: Output violates constraints or causes regression
- ESCALATE: Ambiguous case requiring human review

Always provide structured reasoning for your decision.
"""

class CriticAgent:
    def __init__(self, llm):
        self.agent = DeepAgent(
            name="critic",
            llm=llm,
            system_prompt=CRITIC_SYSTEM_PROMPT,
            tools=[
                query_realtime_metrics,
                check_constraint_compliance,
                compare_baseline_performance,
            ],
            max_iterations=5,
        )

    def evaluate(self, task: dict, output: dict, context: dict) -> dict:
        result = self.agent.invoke({
            "input": "Evaluate the following executor output",
            "task": task,
            "output": output,
            "context": context,
            "success_criteria": task.get("success_criteria", {}),
            "constraints": task.get("constraints", {}),
        })

        return {
            "decision": result["decision"],  # ACCEPT | RETRY | ROLLBACK | ESCALATE
            "confidence": result.get("confidence", 0.0),
            "reasoning": result["reasoning"],
            "feedback": result.get("feedback", ""),
            "suggested_modifications": result.get("modifications", {}),
        }
```

### 1.5 LangGraph Orchestration

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

def build_orchestration_graph():
    graph = StateGraph(OrchestrationState)

    # Nodes
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("critic", critic_node)
    graph.add_node("rollback", rollback_node)
    graph.add_node("human_review", human_review_node)

    # Edges
    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "critic")

    # Conditional edges from critic
    graph.add_conditional_edges("critic", lambda state: state["critic_decision"], {
        "ACCEPT": END,
        "RETRY": "executor",
        "ROLLBACK": "rollback",
        "ESCALATE": "human_review",
    })

    graph.add_edge("rollback", END)
    graph.add_edge("human_review", END)

    # Compile with checkpointer for fault tolerance
    checkpointer = PostgresSaver.from_conn_string(
        "postgresql://user:pass@localhost/campaign_db"
    )

    return graph.compile(checkpointer=checkpointer)
```

---

## 2. Campaign Management Agent

### 2.1 Overview

The Campaign Agent handles the full campaign lifecycle: creation, configuration, targeting, scheduling, pausing, and archiving across multiple ad platforms.

### 2.2 Tools

```python
from langchain_core.tools import tool
from typing import Optional

@tool
def create_campaign(
    name: str,
    objective: str,  # AWARENESS, CONSIDERATION, CONVERSION
    budget: float,
    budget_type: str,  # DAILY, LIFETIME
    start_date: str,
    end_date: Optional[str] = None,
    targeting: dict = None,
    platform: str = "google_ads",  # google_ads, meta, linkedin, tiktok
) -> dict:
    """Create a new ad campaign on the specified platform."""
    connector = get_platform_connector(platform)
    campaign = connector.create_campaign(
        name=name,
        objective=objective,
        budget=budget,
        budget_type=budget_type,
        start_date=start_date,
        end_date=end_date,
        targeting=targeting or {},
    )
    return {
        "campaign_id": campaign["id"],
        "status": "created",
        "platform": platform,
        "details": campaign,
    }

@tool
def update_campaign_targeting(
    campaign_id: str,
    platform: str,
    targeting_updates: dict,
) -> dict:
    """Update targeting criteria for an existing campaign."""
    connector = get_platform_connector(platform)
    result = connector.update_targeting(campaign_id, targeting_updates)
    return {"campaign_id": campaign_id, "updated_fields": list(targeting_updates.keys()), "status": "updated"}

@tool
def pause_campaign(campaign_id: str, platform: str, reason: str = "") -> dict:
    """Pause a running campaign."""
    connector = get_platform_connector(platform)
    connector.pause_campaign(campaign_id)
    return {"campaign_id": campaign_id, "status": "paused", "reason": reason}

@tool
def resume_campaign(campaign_id: str, platform: str) -> dict:
    """Resume a paused campaign."""
    connector = get_platform_connector(platform)
    connector.resume_campaign(campaign_id)
    return {"campaign_id": campaign_id, "status": "active"}

@tool
def archive_campaign(campaign_id: str, platform: str) -> dict:
    """Archive a campaign (soft delete, recoverable for 90 days)."""
    connector = get_platform_connector(platform)
    connector.archive_campaign(campaign_id)
    return {"campaign_id": campaign_id, "status": "archived"}

@tool
def get_campaign_status(campaign_id: str, platform: str) -> dict:
    """Get current status and key metrics for a campaign."""
    connector = get_platform_connector(platform)
    return connector.get_campaign_status(campaign_id)

@tool
def duplicate_campaign(
    source_campaign_id: str,
    platform: str,
    new_name: str,
    budget_adjustment: float = 1.0,
) -> dict:
    """Duplicate an existing campaign with optional budget adjustment."""
    connector = get_platform_connector(platform)
    source = connector.get_campaign(source_campaign_id)
    new_campaign = connector.create_campaign(
        name=new_name,
        objective=source["objective"],
        budget=source["budget"] * budget_adjustment,
        budget_type=source["budget_type"],
        start_date=source.get("start_date"),
        end_date=source.get("end_date"),
        targeting=source.get("targeting", {}),
    )
    return {"new_campaign_id": new_campaign["id"], "source_campaign_id": source_campaign_id}
```

### 2.3 Agent Implementation

```python
CAMPAIGN_AGENT_PROMPT = """
You are the Campaign Management Agent. You handle the full lifecycle of ad campaigns.

Capabilities:
- Create new campaigns with proper structure and naming conventions
- Update targeting, budgets, and schedules
- Pause/resume campaigns based on performance signals
- Duplicate successful campaigns for scaling
- Archive underperforming campaigns

Rules:
- Always confirm budget changes >20% with the planner
- Never delete campaigns; archive them instead
- Maintain naming convention: {brand}_{objective}_{audience}_{date}
- When creating campaigns, always set up UTM parameters
- Check for audience overlap before launching new campaigns
"""

class CampaignAgent(BaseExecutorAgent):
    def __init__(self, llm):
        super().__init__(
            name="campaign_agent",
            llm=llm,
            tools=[
                create_campaign,
                update_campaign_targeting,
                pause_campaign,
                resume_campaign,
                archive_campaign,
                get_campaign_status,
                duplicate_campaign,
                check_audience_overlap,
                validate_utm_parameters,
            ],
            system_prompt=CAMPAIGN_AGENT_PROMPT,
        )

    def validate_preconditions(self, task: dict) -> bool:
        """Ensure campaign operations are safe to execute."""
        if task["action"] == "create_campaign":
            # Check budget limits
            if task["parameters"]["budget"] > task["constraints"].get("max_budget", float("inf")):
                return False
            # Check for duplicate names
            if campaign_exists(task["parameters"]["name"]):
                return False
        return True

    def rollback(self, task: dict) -> bool:
        """Reverse campaign changes."""
        if task["action"] == "create_campaign":
            archive_campaign(task["output"]["campaign_id"], task["parameters"]["platform"])
        elif task["action"] == "pause_campaign":
            resume_campaign(task["parameters"]["campaign_id"], task["parameters"]["platform"])
        elif task["action"] == "update_campaign_targeting":
            # Restore previous targeting from audit log
            restore_targeting_from_audit(task["parameters"]["campaign_id"])
        return True
```

---

## 3. Budget Optimization Agent

### 3.1 Overview

The Budget Agent uses reinforcement learning-inspired heuristics and statistical forecasting to allocate budget across campaigns, ad groups, and time periods to maximize ROAS/CPA targets.

### 3.2 Core Algorithm

```python
import numpy as np
from scipy.optimize import minimize
from dataclasses import dataclass

@dataclass
class CampaignBudget:
    campaign_id: str
    current_budget: float
    current_roas: float
    current_cpa: float
    marginal_roas: float  # ROAS on the next dollar
    min_budget: float
    max_budget: float
    spend_velocity: float  # % of budget spent per day

class BudgetOptimizer:
    def __init__(self, total_budget: float, target_roas: float = 3.0):
        self.total_budget = total_budget
        self.target_roas = target_roas

    def optimize_allocation(
        self,
        campaigns: list[CampaignBudget],
        constraints: dict,
    ) -> dict[str, float]:
        """
        Optimize budget allocation using marginal ROAS equalization.

        The optimal allocation equalizes marginal ROAS across all campaigns
        (subject to min/max constraints).
        """
        n = len(campaigns)

        def objective(allocations):
            """Negative total return (we minimize)."""
            total_return = 0
            for i, camp in enumerate(campaigns):
                # Diminishing returns model: return = a * budget^b
                # where b < 1 captures diminishing returns
                b = 0.7 + 0.1 * (camp.marginal_roas / self.target_roas)
                total_return += camp.current_roas * allocations[i] ** b
            return -total_return

        def budget_constraint(allocations):
            return self.total_budget - sum(allocations)

        # Bounds: min_budget <= allocation <= max_budget
        bounds = [(c.min_budget, c.max_budget) for c in campaigns]

        # Initial guess: current allocations
        x0 = [c.current_budget for c in campaigns]

        # Constraints
        cons = [
            {"type": "eq", "fun": budget_constraint},
        ]

        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
        )

        if result.success:
            return {
                camp.campaign_id: round(result.x[i], 2)
                for i, camp in enumerate(campaigns)
            }
        else:
            # Fallback: proportional allocation based on ROAS
            return self._proportional_fallback(campaigns)

    def _proportional_fallback(self, campaigns: list[CampaignBudget]) -> dict[str, float]:
        """Fallback: allocate proportionally to ROAS performance."""
        total_roas = sum(c.current_roas for c in campaigns)
        return {
            c.campaign_id: round(self.total_budget * (c.current_roas / total_roas), 2)
            for c in campaigns
        }

    def compute_marginal_roas(self, campaign_id: str, platform: str) -> float:
        """
        Estimate marginal ROAS using recent spend/return data.
        Uses a sliding window regression on spend vs. revenue.
        """
        data = get_recent_performance(campaign_id, platform, days=14)
        if len(data) < 5:
            return 1.0  # Default for new campaigns

        spends = np.array([d["spend"] for d in data])
        revenues = np.array([d["revenue"] for d in data])

        # Log-linear model: log(revenue) = a + b * log(spend)
        # Marginal ROAS = d(revenue)/d(spend) = b * revenue / spend
        log_spends = np.log(spends + 1)
        log_revenues = np.log(revenues + 1)

        # Simple linear regression
        b, a = np.polyfit(log_spends, log_revenues, 1)

        # Marginal ROAS at current spend level
        current_spend = spends[-1]
        current_revenue = revenues[-1]
        marginal = b * current_revenue / (current_spend + 1)

        return max(0.1, marginal)  # Floor at 0.1
```

### 3.3 Budget Agent Implementation

```python
BUDGET_AGENT_PROMPT = """
You are the Budget Optimization Agent. You manage budget allocation across campaigns.

Your approach:
1. Analyze current performance (ROAS, CPA, spend velocity)
2. Compute marginal ROAS for each campaign
3. Reallocate budget toward higher marginal ROAS campaigns
4. Respect min/max budget constraints per campaign
5. Maintain total budget within the allocated envelope

Decision rules:
- Never reduce a campaign's budget by more than 30% in a single step
- Always maintain at least 10% of total budget as reserve for testing
- If a campaign's ROAS drops below 1.5x target for 3+ days, reduce budget
- If a campaign's ROAS exceeds 2x target for 5+ days, increase budget
- Consider day-of-week and hour-of-day performance patterns

Always provide a confidence score and expected impact for each change.
"""

class BudgetAgent(BaseExecutorAgent):
    def __init__(self, llm):
        super().__init__(
            name="budget_agent",
            llm=llm,
            tools=[
                adjust_campaign_budget,
                adjust_bid_strategy,
                set_budget_pacing,
                get_budget_utilization,
                forecast_spend,
                get_marginal_roas,
            ],
            system_prompt=BUDGET_AGENT_PROMPT,
        )
        self.optimizer = BudgetOptimizer(total_budget=0, target_roas=3.0)

    def optimize_portfolio(self, portfolio_data: dict) -> dict:
        """Run full portfolio budget optimization."""
        campaigns = [
            CampaignBudget(
                campaign_id=c["id"],
                current_budget=c["budget"],
                current_roas=c["roas"],
                current_cpa=c["cpa"],
                marginal_roas=self.optimizer.compute_marginal_roas(c["id"], c["platform"]),
                min_budget=c.get("min_budget", 10.0),
                max_budget=c.get("max_budget", c["budget"] * 2),
                spend_velocity=c.get("spend_velocity", 0.8),
            )
            for c in portfolio_data["campaigns"]
        ]

        self.optimizer.total_budget = portfolio_data["total_budget"]
        self.optimizer.target_roas = portfolio_data.get("target_roas", 3.0)

        new_allocation = self.optimizer.optimize_allocation(
            campaigns, portfolio_data.get("constraints", {})
        )

        # Compute changes
        changes = []
        for camp in campaigns:
            old = camp.current_budget
            new = new_allocation[camp.campaign_id]
            pct_change = (new - old) / old * 100 if old > 0 else 0
            changes.append({
                "campaign_id": camp.campaign_id,
                "old_budget": old,
                "new_budget": new,
                "change_pct": round(pct_change, 1),
                "expected_roas_improvement": self._estimate_improvement(camp, new),
            })

        return {
            "new_allocation": new_allocation,
            "changes": changes,
            "total_budget": self.optimizer.total_budget,
            "expected_portfolio_roas": self._estimate_portfolio_roas(campaigns, new_allocation),
        }

    def _estimate_improvement(self, camp: CampaignBudget, new_budget: float) -> float:
        """Estimate ROAS improvement from budget change."""
        if new_budget > camp.current_budget:
            # Diminishing returns on increase
            ratio = new_budget / camp.current_budget
            return camp.current_roas * (ratio ** -0.15)  # Slight decrease in ROAS
        else:
            # Cutting low-performing spend improves blended ROAS
            ratio = new_budget / camp.current_budget
            return camp.current_roas * (ratio ** -0.1)

    def _estimate_portfolio_roas(self, campaigns, allocation) -> float:
        """Estimate blended portfolio ROAS after reallocation."""
        total_revenue = 0
        total_spend = 0
        for camp in campaigns:
            b = 0.7 + 0.1 * (camp.marginal_roas / self.optimizer.target_roas)
            revenue = camp.current_roas * allocation[camp.campaign_id] ** b
            total_revenue += revenue
            total_spend += allocation[camp.campaign_id]
        return total_revenue / total_spend if total_spend > 0 else 0
```

### 3.4 Pacing Control

```python
class PacingController:
    """Controls spend pacing to avoid budget exhaustion too early or too late."""

    def __init__(self):
        self.pacing_profiles = {
            "even": lambda progress: 1.0,  # Linear spend
            "front_loaded": lambda progress: 1.5 - progress,  # More early
            "back_loaded": lambda progress: 0.5 + progress,  # More late
            "performance_based": None,  # Dynamic based on conversion rates
        }

    def compute_hourly_budget(
        self,
        daily_budget: float,
        day_progress: float,  # 0.0 to 1.0
        profile: str = "performance_based",
        hourly_performance: dict = None,
    ) -> float:
        """Compute the budget for the current hour."""
        if profile == "performance_based" and hourly_performance:
            # Allocate more budget to hours with higher conversion rates
            current_hour = datetime.now().hour
            hour_weight = hourly_performance.get(current_hour, 1.0)
            total_weight = sum(hour_performance.values())
            return daily_budget * (hour_weight / total_weight)

        pacing_fn = self.pacing_profiles.get(profile, self.pacing_profiles["even"])
        pace_multiplier = pacing_fn(day_progress)

        # Base hourly budget with pacing adjustment
        base_hourly = daily_budget / 24
        return base_hourly * pace_multiplier

    def should_throttle(self, campaign_id: str, current_spend: float, daily_budget: float) -> bool:
        """Determine if spending should be throttled."""
        now = datetime.now()
        day_progress = (now.hour * 60 + now.minute) / (24 * 60)
        expected_spend = daily_budget * day_progress

        # If spending > 120% of expected pace, throttle
        return current_spend > expected_spend * 1.2
```

---

## 4. Creative Generation Agent

### 4.1 Overview

The Creative Agent generates ad copy, headlines, descriptions, and visual concepts using LLMs, then scores and iterates based on predicted performance.

### 4.2 Creative Generation Pipeline

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class AdCreative(BaseModel):
    headline: str = Field(description="Ad headline, max 30 characters")
    description: str = Field(description="Ad description, max 90 characters")
    call_to_action: str = Field(description="CTA button text")
    primary_text: str = Field(description="Primary ad copy for social")
    hashtags: list[str] = Field(description="Relevant hashtags")
    target_audience: str = Field(description="Intended audience segment")
    predicted_ctr: float = Field(description="Predicted click-through rate")
    brand_alignment_score: float = Field(description="0-100 brand alignment score")

CREATIVE_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert digital marketer and copywriter.
Generate compelling ad creatives that:
1. Align with the brand voice: {brand_voice}
2. Target the audience: {target_audience}
3. Support the campaign objective: {objective}
4. Include a clear value proposition and call-to-action
5. Are platform-optimized for: {platform}
6. Follow character limits and best practices

Brand guidelines:
- Tone: {tone}
- Key messages: {key_messages}
- Things to avoid: {avoid_list}
- Mandatory inclusions: {mandatory}

Generate {num_variants} distinct creative variants.
"""),
    ("human", "Campaign context: {campaign_context}"),
])

class CreativeGenerator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm.with_structured_output(AdCreative)
        self.chain = CREATIVE_GENERATION_PROMPT | self.llm

    def generate_variants(
        self,
        campaign_context: dict,
        num_variants: int = 5,
    ) -> list[AdCreative]:
        """Generate multiple creative variants for A/B testing."""
        results = self.chain.batch([
            {
                "brand_voice": campaign_context["brand_voice"],
                "target_audience": campaign_context["target_audience"],
                "objective": campaign_context["objective"],
                "platform": campaign_context["platform"],
                "tone": campaign_context.get("tone", "professional"),
                "key_messages": campaign_context.get("key_messages", []),
                "avoid_list": campaign_context.get("avoid", []),
                "mandatory": campaign_context.get("mandatory", []),
                "num_variants": num_variants,
                "campaign_context": str(campaign_context),
            }
        ])
        return results

    def score_creative(self, creative: AdCreative, historical_data: list[dict]) -> dict:
        """
        Score a creative variant based on similarity to past top performers.
        Uses embedding similarity + heuristic rules.
        """
        scores = {
            "headline_length": self._score_headline_length(creative.headline),
            "cta_strength": self._score_cta(creative.call_to_action),
            "message_clarity": self._score_clarity(creative.primary_text),
            "audience_match": self._score_audience_match(creative, historical_data),
            "differentiation": self._score_differentiation(creative, historical_data),
        }

        # Weighted composite score
        weights = {
            "headline_length": 0.15,
            "cta_strength": 0.25,
            "message_clarity": 0.20,
            "audience_match": 0.25,
            "differentiation": 0.15,
        }

        composite = sum(scores[k] * weights[k] for k in scores)
        return {"composite_score": round(composite, 2), "component_scores": scores}

    def _score_headline_length(self, headline: str) -> float:
        """Score headline length (optimal: 20-30 chars)."""
        length = len(headline)
        if 20 <= length <= 30:
            return 1.0
        elif 15 <= length <= 35:
            return 0.8
        else:
            return 0.5

    def _score_cta(self, cta: str) -> float:
        """Score CTA strength based on action verbs and urgency."""
        strong_ctas = ["shop now", "get started", "try free", "learn more", "sign up", "buy now"]
        cta_lower = cta.lower()
        if any(s in cta_lower for s in strong_ctas):
            return 1.0
        return 0.6

    def _score_clarity(self, text: str) -> float:
        """Score message clarity using readability metrics."""
        # Simplified Flesch-Kincaid inspired scoring
        words = text.split()
        if not words:
            return 0.0
        avg_word_length = sum(len(w) for w in words) / len(words)
        # Prefer average word length 4-6 characters
        if 4 <= avg_word_length <= 6:
            return 1.0
        return 0.7

    def _score_audience_match(self, creative: AdCreative, historical_data: list[dict]) -> float:
        """Score how well the creative matches the target audience based on historical performance."""
        if not historical_data:
            return 0.5
        # Check if similar creatives performed well for this audience
        audience_performances = [
            h["ctr"] for h in historical_data
            if h.get("target_audience") == creative.target_audience
        ]
        if audience_performances:
            avg_ctr = sum(audience_performances) / len(audience_performances)
            return min(1.0, avg_ctr / 0.05)  # Normalize to 5% CTR
        return 0.5

    def _score_differentiation(self, creative: AdCreative, historical_data: list[dict]) -> float:
        """Score how different this creative is from existing ones (to avoid fatigue)."""
        if not historical_data:
            return 1.0
        # Simple Jaccard distance on headline words
        creative_words = set(creative.headline.lower().split())
        max_similarity = 0
        for h in historical_data:
            hist_words = set(h.get("headline", "").lower().split())
            if hist_words:
                jaccard = len(creative_words & hist_words) / len(creative_words | hist_words)
                max_similarity = max(max_similarity, jaccard)
        return 1.0 - max_similarity  # Higher is more different
```

### 4.3 Creative Agent Implementation

```python
CREATIVE_AGENT_PROMPT = """
You are the Creative Generation Agent. You create and iterate on ad creatives.

Your process:
1. Analyze campaign context and brand guidelines
2. Generate multiple creative variants
3. Score each variant using historical performance data
4. Select top performers for A/B testing
5. Iterate on winning creatives to prevent fatigue

Creative principles:
- Lead with the value proposition
- Use power words that drive action
- Create urgency without being pushy
- Match the platform's native style
- Respect brand voice and visual identity
- Test one variable at a time

Fatigue management:
- Rotate creatives every 7-14 days
- Maintain at least 3 active variants per ad set
- Monitor frequency metrics and refresh when frequency > 3
"""

class CreativeAgent(BaseExecutorAgent):
    def __init__(self, llm):
        super().__init__(
            name="creative_agent",
            llm=llm,
            tools=[
                generate_creative_variants,
                score_creative_variant,
                upload_creative_asset,
                check_creative_fatigue,
                get_brand_guidelines,
                get_top_performing_creatives,
            ],
            system_prompt=CREATIVE_AGENT_PROMPT,
        )
        self.generator = CreativeGenerator(llm)

    def generate_campaign_creatives(self, campaign_config: dict) -> dict:
        """Generate a full set of creatives for a campaign."""
        variants = self.generator.generate_variants(
            campaign_context=campaign_config,
            num_variants=campaign_config.get("num_variants", 5),
        )

        # Score all variants
        historical = get_top_performing_creatives(
            campaign_config.get("account_id"),
            platform=campaign_config["platform"],
            days=30,
        )

        scored = []
        for v in variants:
            score = self.generator.score_creative(v, historical)
            scored.append({
                "creative": v,
                "score": score["composite_score"],
                "component_scores": score["component_scores"],
            })

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)

        return {
            "variants": scored,
            "recommended_for_testing": [s["creative"] for s in scored[:3]],
            "recommended_for_production": scored[0]["creative"] if scored else None,
        }

    def refresh_fatigued_creatives(self, account_id: str, platform: str) -> dict:
        """Identify and refresh creatives showing fatigue."""
        fatigued = check_creative_fatigue(account_id, platform, frequency_threshold=3.0)

        refreshes = []
        for creative in fatigued:
            # Generate variations of the fatigued creative
            campaign_context = {
                "brand_voice": creative["brand_voice"],
                "target_audience": creative["target_audience"],
                "objective": creative["objective"],
                "platform": platform,
                "key_messages": creative["key_messages"],
            }
            new_variants = self.generator.generate_variants(campaign_context, num_variants=3)
            refreshes.append({
                "original_creative_id": creative["id"],
                "new_variants": new_variants,
                "fatigue_score": creative["frequency"],
            })

        return {"refreshed": refreshes, "total_fatigued": len(fatigued)}
```

---

## 5. A/B Testing Agent

### 5.1 Overview

The A/B Testing Agent designs experiments, monitors statistical significance, and makes promotion decisions. It uses Bayesian methods for more efficient testing than traditional frequentist approaches.

### 5.2 Bayesian A/B Testing Engine

```python
import numpy as np
from scipy import stats
from dataclasses import dataclass, field

@dataclass
class ExperimentVariant:
    name: str
    impressions: int = 0
    conversions: int = 0
    revenue: float = 0.0
    spend: float = 0.0

    @property
    def conversion_rate(self) -> float:
        return self.conversions / self.impressions if self.impressions > 0 else 0.0

    @property
    def roas(self) -> float:
        return self.revenue / self.spend if self.spend > 0 else 0.0

class BayesianABTest:
    """
    Bayesian A/B testing using Beta-Binomial conjugate prior.

    Advantages over frequentist:
    - Can stop early when one variant is clearly winning
    - Provides probability that A beats B (not just p-values)
    - Handles multiple variants naturally
    - More intuitive results for stakeholders
    """

    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0):
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.variants: dict[str, ExperimentVariant] = {}

    def add_variant(self, name: str):
        self.variants[name] = ExperimentVariant(name=name)

    def update(self, variant_name: str, impressions: int, conversions: int, revenue: float = 0, spend: float = 0):
        v = self.variants[variant_name]
        v.impressions += impressions
        v.conversions += conversions
        v.revenue += revenue
        v.spend += spend

    def probability_better_than(self, variant_a: str, variant_b: str, n_samples: int = 100000) -> float:
        """
        P(A > B) computed via Monte Carlo sampling from posterior distributions.
        """
        a = self.variants[variant_a]
        b = self.variants[variant_b]

        # Posterior: Beta(prior_alpha + conversions, prior_beta + failures)
        alpha_a = self.prior_alpha + a.conversions
        beta_a = self.prior_beta + (a.impressions - a.conversions)
        alpha_b = self.prior_alpha + b.conversions
        beta_b = self.prior_beta + (b.impressions - b.conversions)

        samples_a = np.random.beta(alpha_a, beta_a, n_samples)
        samples_b = np.random.beta(alpha_b, beta_b, n_samples)

        return float(np.mean(samples_a > samples_b))

    def expected_loss(self, variant_a: str, variant_b: str, n_samples: int = 100000) -> float:
        """
        Expected loss if we choose A over B.
        Loss = max(0, B_rate - A_rate) averaged over posterior.
        """
        a = self.variants[variant_a]
        b = self.variants[variant_b]

        alpha_a = self.prior_alpha + a.conversions
        beta_a = self.prior_beta + (a.impressions - a.conversions)
        alpha_b = self.prior_alpha + b.conversions
        beta_b = self.prior_beta + (b.impressions - b.conversions)

        samples_a = np.random.beta(alpha_a, beta_a, n_samples)
        samples_b = np.random.beta(alpha_b, beta_b, n_samples)

        loss = np.maximum(0, samples_b - samples_a)
        return float(np.mean(loss))

    def should_stop(self, control: str, treatment: str, threshold: float = 0.95, max_loss: float = 0.005) -> dict:
        """
        Determine if the experiment should stop.

        Stops when:
        1. P(treatment > control) > threshold (treatment wins), OR
        2. P(control > treatment) > threshold (control wins), OR
        3. Expected loss of choosing either < max_loss (practical equivalence)
        """
        p_treatment_wins = self.probability_better_than(treatment, control)
        p_control_wins = self.probability_better_than(control, treatment)

        if p_treatment_wins > threshold:
            return {
                "should_stop": True,
                "winner": treatment,
                "reason": f"P({treatment} > {control}) = {p_treatment_wins:.3f} > {threshold}",
                "confidence": p_treatment_wins,
            }
        elif p_control_wins > threshold:
            return {
                "should_stop": True,
                "winner": control,
                "reason": f"P({control} > {treatment}) = {p_control_wins:.3f} > {threshold}",
                "confidence": p_control_wins,
            }

        # Check practical equivalence
        loss_choose_treatment = self.expected_loss(treatment, control)
        loss_choose_control = self.expected_loss(control, treatment)

        if loss_choose_treatment < max_loss and loss_choose_control < max_loss:
            return {
                "should_stop": True,
                "winner": control,  # Default to control for equivalence
                "reason": f"Practical equivalence: expected loss < {max_loss}",
                "confidence": 1 - max(loss_choose_treatment, loss_choose_control),
            }

        return {
            "should_stop": False,
            "winner": None,
            "reason": "Insufficient evidence to conclude",
            "p_treatment_wins": p_treatment_wins,
            "p_control_wins": p_control_wins,
            "expected_loss_treatment": loss_choose_treatment,
            "expected_loss_control": loss_choose_control,
        }

    def get_summary(self) -> dict:
        """Get a summary of all variants with credible intervals."""
        summary = {}
        for name, v in self.variants.items():
            alpha = self.prior_alpha + v.conversions
            beta = self.prior_beta + (v.impressions - v.conversions)

            # 95% credible interval
            ci_low = stats.beta.ppf(0.025, alpha, beta)
            ci_high = stats.beta.ppf(0.975, alpha, beta)

            summary[name] = {
                "impressions": v.impressions,
                "conversions": v.conversions,
                "conversion_rate": v.conversion_rate,
                "credible_interval_95": [round(ci_low, 4), round(ci_high, 4)],
                "roas": round(v.roas, 2),
                "spend": round(v.spend, 2),
                "revenue": round(v.revenue, 2),
            }
        return summary
```

### 5.3 A/B Testing Agent Implementation

```python
AB_TEST_AGENT_PROMPT = """
You are the A/B Testing Agent. You design, monitor, and conclude experiments.

Experiment design principles:
1. Test one variable at a time (headline, image, CTA, audience, or bid strategy)
2. Ensure adequate sample size before concluding (use power analysis)
3. Run for at least 7 days to account for day-of-week effects
4. Use Bayesian methods for more efficient decision-making
5. Set clear success metrics before starting (primary and guardrail)

Decision framework:
- P(treatment > control) > 0.95: Promote treatment
- P(control > treatment) > 0.95: Keep control
- Expected loss < 0.5%: Either is fine, keep control (simplicity)
- Otherwise: Continue testing

Guardrail metrics (must not regress):
- CPA must not increase by >10%
- ROAS must not decrease by >5%
- Brand safety score must not decrease

Always document experiment learnings for future reference.
"""

class ABTestAgent(BaseExecutorAgent):
    def __init__(self, llm):
        super().__init__(
            name="ab_test_agent",
            llm=llm,
            tools=[
                create_experiment,
                get_experiment_results,
                promote_variant,
                allocate_traffic,
                check_sample_size,
                get_experiment_history,
            ],
            system_prompt=AB_TEST_AGENT_PROMPT,
        )

    def design_experiment(self, config: dict) -> dict:
        """Design a new A/B test with proper structure."""
        # Power analysis for sample size
        baseline_rate = config.get("baseline_conversion_rate", 0.02)
        mde = config.get("minimum_detectable_effect", 0.2)  # 20% relative lift
        alpha = config.get("alpha", 0.05)
        power = config.get("power", 0.8)

        required_sample = self._power_analysis(baseline_rate, mde, alpha, power)

        experiment = {
            "name": config["name"],
            "hypothesis": config["hypothesis"],
            "control_variant": config["control"],
            "treatment_variants": config["treatments"],
            "primary_metric": config.get("primary_metric", "conversion_rate"),
            "guardrail_metrics": config.get("guardrail_metrics", ["cpa", "roas"]),
            "required_sample_size": required_sample,
            "minimum_duration_days": 7,
            "traffic_split": config.get("traffic_split", [0.5, 0.5]),
            "status": "designed",
        }

        return experiment

    def _power_analysis(self, baseline_rate: float, mde: float, alpha: float, power: float) -> int:
        """Compute required sample size per variant using normal approximation."""
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)

        p1 = baseline_rate
        p2 = baseline_rate * (1 + mde)

        pooled_p = (p1 + p2) / 2

        n = (
            (z_alpha * np.sqrt(2 * pooled_p * (1 - pooled_p)) +
             z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
        ) / (p2 - p1) ** 2

        return int(np.ceil(n))

    def evaluate_experiment(self, experiment_id: str) -> dict:
        """Evaluate an active experiment and make a decision."""
        results = get_experiment_results(experiment_id)
        test = BayesianABTest()

        for variant_name, data in results["variants"].items():
            test.add_variant(variant_name)
            test.update(
                variant_name,
                impressions=data["impressions"],
                conversions=data["conversions"],
                revenue=data.get("revenue", 0),
                spend=data.get("spend", 0),
            )

        control = results["control_variant"]
        treatments = results["treatment_variants"]

        decisions = []
        for treatment in treatments:
            decision = test.should_stop(control, treatment)
            decisions.append({
                "treatment": treatment,
                **decision,
            })

        # Check guardrail metrics
        guardrails_ok = self._check_guardrails(results)

        return {
            "experiment_id": experiment_id,
            "summary": test.get_summary(),
            "decisions": decisions,
            "guardrails_passed": guardrails_ok,
            "recommendation": self._make_recommendation(decisions, guardrails_ok),
        }

    def _check_guardrails(self, results: dict) -> bool:
        """Check if guardrail metrics are within acceptable bounds."""
        control = results["variants"][results["control_variant"]]
        for treatment_name, treatment in results["variants"].items():
            if treatment_name == results["control_variant"]:
                continue

            # CPA guardrail: must not increase >10%
            if control["spend"] > 0 and control["conversions"] > 0:
                control_cpa = control["spend"] / control["conversions"]
                treatment_cpa = treatment["spend"] / treatment["conversions"] if treatment["conversions"] > 0 else float("inf")
                if treatment_cpa > control_cpa * 1.1:
                    return False

            # ROAS guardrail: must not decrease >5%
            if control["spend"] > 0 and treatment["spend"] > 0:
                control_roas = control["revenue"] / control["spend"]
                treatment_roas = treatment["revenue"] / treatment["spend"]
                if treatment_roas < control_roas * 0.95:
                    return False

        return True

    def _make_recommendation(self, decisions: list, guardrails_ok: bool) -> str:
        if not guardrails_ok:
            return "STOP: Guardrail metrics violated. Keep control variant."

        for d in decisions:
            if d["should_stop"] and d["winner"] != d.get("control", ""):
                return f"PROMOTE: {d['winner']} wins with {d['confidence']:.1%} confidence."

        return "CONTINUE: Insufficient evidence. Keep testing."
```

---

## 6. Performance Analytics Agent

### 6.1 Overview

The Analytics Agent monitors campaign performance in real-time, detects anomalies, generates reports, and provides actionable insights to other agents.

### 6.2 Metrics Pipeline

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import statistics

@dataclass
class MetricSnapshot:
    timestamp: datetime
    campaign_id: str
    impressions: int
    clicks: int
    conversions: int
    spend: float
    revenue: float

    @property
    def ctr(self) -> float:
        return self.clicks / self.impressions if self.impressions > 0 else 0.0

    @property
    def cpc(self) -> float:
        return self.spend / self.clicks if self.clicks > 0 else 0.0

    @property
    def cpa(self) -> float:
        return self.spend / self.conversions if self.conversions > 0 else 0.0

    @property
    def roas(self) -> float:
        return self.revenue / self.spend if self.spend > 0 else 0.0

    @property
    def conversion_rate(self) -> float:
        return self.conversions / self.clicks if self.clicks > 0 else 0.0

class MetricsAggregator:
    """Aggregates raw metrics into time-series windows."""

    def __init__(self, window_sizes: list[int] = None):
        self.window_sizes = window_sizes or [1, 7, 14, 30]  # days
        self.raw_data: dict[str, deque] = {}  # campaign_id -> deque of MetricSnapshot

    def add_snapshot(self, snapshot: MetricSnapshot):
        if snapshot.campaign_id not in self.raw_data:
            self.raw_data[snapshot.campaign_id] = deque(maxlen=10000)
        self.raw_data[snapshot.campaign_id].append(snapshot)

    def get_aggregated(self, campaign_id: str, days: int) -> dict:
        """Get aggregated metrics for a time window."""
        if campaign_id not in self.raw_data:
            return {}

        cutoff = datetime.utcnow() - timedelta(days=days)
        snapshots = [s for s in self.raw_data[campaign_id] if s.timestamp >= cutoff]

        if not snapshots:
            return {}

        total_impressions = sum(s.impressions for s in snapshots)
        total_clicks = sum(s.clicks for s in snapshots)
        total_conversions = sum(s.conversions for s in snapshots)
        total_spend = sum(s.spend for s in snapshots)
        total_revenue = sum(s.revenue for s in snapshots)

        return {
            "campaign_id": campaign_id,
            "period_days": days,
            "impressions": total_impressions,
            "clicks": total_clicks,
            "conversions": total_conversions,
            "spend": round(total_spend, 2),
            "revenue": round(total_revenue, 2),
            "ctr": round(total_clicks / total_impressions, 4) if total_impressions > 0 else 0,
            "cpc": round(total_spend / total_clicks, 2) if total_clicks > 0 else 0,
            "cpa": round(total_spend / total_conversions, 2) if total_conversions > 0 else 0,
            "roas": round(total_revenue / total_spend, 2) if total_spend > 0 else 0,
            "conversion_rate": round(total_conversions / total_clicks, 4) if total_clicks > 0 else 0,
        }

    def get_trend(self, campaign_id: str, metric: str, days: int = 14) -> list[dict]:
        """Get daily trend data for a specific metric."""
        if campaign_id not in self.raw_data:
            return []

        cutoff = datetime.utcnow() - timedelta(days=days)
        snapshots = [s for s in self.raw_data[campaign_id] if s.timestamp >= cutoff]

        # Group by day
        daily = {}
        for s in snapshots:
            day = s.timestamp.date().isoformat()
            if day not in daily:
                daily[day] = []
            daily[day].append(getattr(s, metric, 0))

        return [
            {"date": day, "value": round(statistics.mean(values), 4)}
            for day, values in sorted(daily.items())
        ]
```

### 6.3 Anomaly Detection

```python
class AnomalyDetector:
    """
    Detects performance anomalies using statistical methods.

    Uses a combination of:
    1. Z-score for sudden spikes/drops
    2. Moving average deviation for trend changes
    3. Seasonal decomposition for expected patterns
    """

    def __init__(self, z_threshold: float = 3.0, min_history: int = 7):
        self.z_threshold = z_threshold
        self.min_history = min_history

    def detect(self, campaign_id: str, metric: str, current_value: float, history: list[float]) -> dict:
        """
        Detect if the current value is anomalous given the history.

        Returns:
            {
                "is_anomaly": bool,
                "severity": "low" | "medium" | "high",
                "z_score": float,
                "expected_range": [low, high],
                "direction": "spike" | "drop" | "normal",
            }
        """
        if len(history) < self.min_history:
            return {"is_anomaly": False, "reason": "insufficient_history"}

        mean = statistics.mean(history)
        std = statistics.stdev(history) if len(history) > 1 else 0

        if std == 0:
            return {"is_anomaly": False, "reason": "no_variance"}

        z_score = (current_value - mean) / std

        is_anomaly = abs(z_score) > self.z_threshold

        if not is_anomaly:
            return {
                "is_anomaly": False,
                "z_score": round(z_score, 2),
                "expected_range": [
                    round(mean - self.z_threshold * std, 4),
                    round(mean + self.z_threshold * std, 4),
                ],
            }

        severity = "low"
        if abs(z_score) > self.z_threshold * 2:
            severity = "high"
        elif abs(z_score) > self.z_threshold * 1.5:
            severity = "medium"

        direction = "spike" if z_score > 0 else "drop"

        return {
            "is_anomaly": True,
            "severity": severity,
            "z_score": round(z_score, 2),
            "expected_range": [
                round(mean - self.z_threshold * std, 4),
                round(mean + self.z_threshold * std, 4),
            ],
            "direction": direction,
            "current_value": current_value,
            "historical_mean": round(mean, 4),
            "deviation_pct": round((current_value - mean) / mean * 100, 1) if mean != 0 else 0,
        }

    def detect_multivariate(self, campaign_id: str, current: MetricSnapshot, history: list[MetricSnapshot]) -> list[dict]:
        """Detect anomalies across multiple metrics simultaneously."""
        anomalies = []
        metrics_to_check = ["ctr", "cpc", "cpa", "roas", "conversion_rate"]

        for metric in metrics_to_check:
            current_value = getattr(current, metric, 0)
            hist_values = [getattr(h, metric, 0) for h in history]

            result = self.detect(campaign_id, metric, current_value, hist_values)
            if result["is_anomaly"]:
                result["metric"] = metric
                anomalies.append(result)

        return anomalies
```

### 6.4 Analytics Agent Implementation

```python
ANALYTICS_AGENT_PROMPT = """
You are the Performance Analytics Agent. You monitor, analyze, and report on campaign performance.

Your responsibilities:
1. Aggregate metrics across campaigns and time periods
2. Detect anomalies in performance (both positive and negative)
3. Generate actionable insights and recommendations
4. Create performance reports for stakeholders
5. Feed performance data to other agents for optimization

Analysis framework:
- Compare current performance to: yesterday, last week, last 30 days, and target
- Identify trends: improving, stable, declining
- Segment by: campaign, ad set, creative, audience, platform, time of day
- Compute efficiency metrics: ROAS, CPA, CTR, conversion rate
- Identify opportunities: scaling winners, fixing losers, testing new approaches

Report structure:
1. Executive summary (3-5 bullet points)
2. Key metrics dashboard
3. Anomalies and alerts
4. Recommendations with expected impact
5. Appendix with detailed data
"""

class AnalyticsAgent(BaseExecutorAgent):
    def __init__(self, llm):
        super().__init__(
            name="analytics_agent",
            llm=llm,
            tools=[
                query_campaign_metrics,
                get_anomaly_alerts,
                generate_performance_report,
                compare_to_benchmark,
                get_attribution_data,
                forecast_performance,
            ],
            system_prompt=ANALYTICS_AGENT_PROMPT,
        )
        self.aggregator = MetricsAggregator()
        self.anomaly_detector = AnomalyDetector()

    def analyze_portfolio(self, account_id: str, platform: str) -> dict:
        """Comprehensive portfolio analysis."""
        campaigns = get_active_campaigns(account_id, platform)

        analysis = {
            "account_id": account_id,
            "platform": platform,
            "timestamp": datetime.utcnow().isoformat(),
            "portfolio_summary": {},
            "campaign_analyses": [],
            "anomalies": [],
            "recommendations": [],
        }

        total_spend = 0
        total_revenue = 0
        total_conversions = 0

        for campaign in campaigns:
            # Get metrics for multiple time windows
            metrics_1d = self.aggregator.get_aggregated(campaign["id"], 1)
            metrics_7d = self.aggregator.get_aggregated(campaign["id"], 7)
            metrics_30d = self.aggregator.get_aggregated(campaign["id"], 30)

            total_spend += metrics_7d.get("spend", 0)
            total_revenue += metrics_7d.get("revenue", 0)
            total_conversions += metrics_7d.get("conversions", 0)

            # Detect anomalies
            if metrics_1d and metrics_7d:
                snapshot = MetricSnapshot(
                    timestamp=datetime.utcnow(),
                    campaign_id=campaign["id"],
                    **{k: metrics_1d.get(k, 0) for k in ["impressions", "clicks", "conversions", "spend", "revenue"]}
                )
                history = self._get_historical_snapshots(campaign["id"], days=14)
                anomalies = self.anomaly_detector.detect_multivariate(
                    campaign["id"], snapshot, history
                )
                analysis["anomalies"].extend(anomalies)

            # Campaign-level analysis
            campaign_analysis = {
                "campaign_id": campaign["id"],
                "name": campaign["name"],
                "status": campaign["status"],
                "metrics": {
                    "1d": metrics_1d,
                    "7d": metrics_7d,
                    "30d": metrics_30d,
                },
                "trend": self._compute_trend(metrics_1d, metrics_7d, metrics_30d),
                "health_score": self._compute_health_score(metrics_7d, metrics_30d),
            }
            analysis["campaign_analyses"].append(campaign_analysis)

        # Portfolio-level summary
        analysis["portfolio_summary"] = {
            "total_spend_7d": round(total_spend, 2),
            "total_revenue_7d": round(total_revenue, 2),
            "total_conversions_7d": total_conversions,
            "blended_roas": round(total_revenue / total_spend, 2) if total_spend > 0 else 0,
            "blended_cpa": round(total_spend / total_conversions, 2) if total_conversions > 0 else 0,
            "active_campaigns": len([c for c in campaigns if c["status"] == "active"]),
            "anomaly_count": len(analysis["anomalies"]),
        }

        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)

        return analysis

    def _compute_trend(self, m1d: dict, m7d: dict, m30d: dict) -> str:
        """Compute performance trend direction."""
        if not m1d or not m7d or not m30d:
            return "insufficient_data"

        roas_1d = m1d.get("roas", 0)
        roas_7d = m7d.get("roas", 0)
        roas_30d = m30d.get("roas", 0)

        if roas_1d > roas_7d * 1.1 and roas_7d > roas_30d * 1.05:
            return "improving"
        elif roas_1d < roas_7d * 0.9 and roas_7d < roas_30d * 0.95:
            return "declining"
        else:
            return "stable"

    def _compute_health_score(self, m7d: dict, m30d: dict) -> int:
        """Compute a 0-100 health score based on multiple factors."""
        score = 50  # Base

        # ROAS component (0-30 points)
        roas = m7d.get("roas", 0)
        if roas >= 4:
            score += 30
        elif roas >= 3:
            score += 25
        elif roas >= 2:
            score += 15
        elif roas >= 1:
            score += 5

        # Trend component (0-20 points)
        roas_30d = m30d.get("roas", 0)
        if roas > roas_30d * 1.1:
            score += 20
        elif roas > roas_30d:
            score += 10
        elif roas < roas_30d * 0.8:
            score -= 10

        # Efficiency component (0-20 points)
        cpa = m7d.get("cpa", 0)
        if cpa > 0 and cpa < 20:
            score += 20
        elif cpa < 50:
            score += 10
        elif cpa > 100:
            score -= 10

        # Scale component (0-10 points)
        spend = m7d.get("spend", 0)
        if spend > 1000:
            score += 10
        elif spend > 500:
            score += 5

        return max(0, min(100, score))

    def _generate_recommendations(self, analysis: dict) -> list[dict]:
        """Generate actionable recommendations from analysis."""
        recommendations = []

        for campaign in analysis["campaign_analyses"]:
            health = campaign["health_score"]
            trend = campaign["trend"]

            if health >= 80 and trend == "improving":
                recommendations.append({
                    "campaign_id": campaign["campaign_id"],
                    "action": "scale_budget",
                    "priority": "high",
                    "reason": f"Health score {health}/100 with improving trend",
                    "expected_impact": "+15-25% ROAS at 1.5x scale",
                })
            elif health <= 30 and trend == "declining":
                recommendations.append({
                    "campaign_id": campaign["campaign_id"],
                    "action": "pause_and_investigate",
                    "priority": "high",
                    "reason": f"Health score {health}/100 with declining trend",
                    "expected_impact": "Prevent further budget waste",
                })
            elif trend == "declining":
                recommendations.append({
                    "campaign_id": campaign["campaign_id"],
                    "action": "refresh_creative",
                    "priority": "medium",
                    "reason": "Performance declining, possible creative fatigue",
                    "expected_impact": "+10-20% CTR improvement",
                })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return recommendations

    def _get_historical_snapshots(self, campaign_id: str, days: int) -> list[MetricSnapshot]:
        """Retrieve historical metric snapshots for anomaly detection."""
        # In production, this would query a time-series database
        return []
```

---

## 7. Real-Time Optimization Loops

### 7.1 Architecture

Real-time optimization uses an event-driven architecture with streaming data from ad platforms, processed through a pipeline that triggers agent actions.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Ad Platform  │────▶│  Event Bus   │────▶│  Stream      │
│  Webhooks    │     │  (Redis/     │     │  Processor   │
│              │     │   Kafka)     │     │  (Flink/     │
└──────────────┘     └──────────────┘     │   Custom)    │
                                          └──────┬───────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────────┐
                    │                            │                            │
              ┌─────▼─────┐            ┌────────▼────────┐          ┌───────▼──────┐
              │ Budget    │            │  Anomaly        │          │  Creative    │
              │ Optimizer │            │  Detector       │          │  Fatigue     │
              │ Loop      │            │  Loop           │          │  Loop        │
              │ (15 min)  │            │  (5 min)        │          │  (1 hour)    │
              └───────────┘            └─────────────────┘          └──────────────┘
```

### 7.2 Event-Driven Optimization Loop

```python
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Callable
import redis.asyncio as redis

class OptimizationTrigger(Enum):
    METRIC_THRESHOLD = "metric_threshold"
    ANOMALY_DETECTED = "anomaly_detected"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    CREATIVE_FATIGUE = "creative_fatigue"
    BUDGET_PACING = "budget_pacing"

@dataclass
class OptimizationEvent:
    trigger: OptimizationTrigger
    campaign_id: str
    platform: str
    metric: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    context: dict

class RealTimeOptimizationLoop:
    """
    Main optimization loop that processes events and triggers agent actions.
    Runs multiple sub-loops at different frequencies.
    """

    def __init__(self, orchestrator, redis_url: str = "redis://localhost:6379"):
        self.orchestrator = orchestrator
        self.redis = redis.from_url(redis_url)
        self.running = False
        self.loops: dict[str, Callable] = {
            "budget_optimization": self._budget_loop,
            "anomaly_detection": self._anomaly_loop,
            "creative_refresh": self._creative_loop,
            "performance_monitoring": self._performance_loop,
        }

    async def start(self):
        """Start all optimization loops."""
        self.running = True
        tasks = [
            asyncio.create_task(self._run_loop("budget_optimization", interval_seconds=900)),   # 15 min
            asyncio.create_task(self._run_loop("anomaly_detection", interval_seconds=300)),    # 5 min
            asyncio.create_task(self._run_loop("creative_refresh", interval_seconds=3600)),    # 1 hour
            asyncio.create_task(self._run_loop("performance_monitoring", interval_seconds=60)), # 1 min
        ]
        await asyncio.gather(*tasks)

    async def _run_loop(self, name: str, interval_seconds: int):
        """Run a single optimization loop at the specified interval."""
        while self.running:
            try:
                await self.loops[name]()
            except Exception as e:
                logger.error(f"Loop {name} failed: {e}", exc_info=True)
                await self._alert_ops(f"Optimization loop {name} failed: {e}")
            await asyncio.sleep(interval_seconds)

    async def _budget_loop(self):
        """Budget optimization loop - runs every 15 minutes."""
        # Get all active campaigns
        campaigns = await self._get_active_campaigns()

        for campaign in campaigns:
            # Check pacing
            spend_data = await self._get_spend_data(campaign["id"], campaign["platform"])
            if self._is_pacing_off(spend_data):
                await self._emit_event(OptimizationEvent(
                    trigger=OptimizationTrigger.BUDGET_PACING,
                    campaign_id=campaign["id"],
                    platform=campaign["platform"],
                    metric="spend_pace",
                    current_value=spend_data["pace_ratio"],
                    threshold_value=1.2,
                    timestamp=datetime.utcnow(),
                    context=spend_data,
                ))

        # Run portfolio optimization
        portfolio = await self._get_portfolio_data()
        if self._should_reoptimize(portfolio):
            result = await self.orchestrator.invoke({
                "objective": "Optimize budget allocation across portfolio",
                "constraints": {"total_budget": portfolio["total_budget"]},
            })
            await self._apply_budget_changes(result)

    async def _anomaly_loop(self):
        """Anomaly detection loop - runs every 5 minutes."""
        campaigns = await self._get_active_campaigns()

        for campaign in campaigns:
            metrics = await self._get_recent_metrics(campaign["id"], campaign["platform"], minutes=30)
            history = await self._get_historical_metrics(campaign["id"], campaign["platform"], days=14)

            detector = AnomalyDetector(z_threshold=2.5)
            anomalies = detector.detect_multivariate(
                campaign["id"],
                MetricSnapshot(
                    timestamp=datetime.utcnow(),
                    campaign_id=campaign["id"],
                    **metrics,
                ),
                history,
            )

            for anomaly in anomalies:
                if anomaly["severity"] in ("medium", "high"):
                    await self._emit_event(OptimizationEvent(
                        trigger=OptimizationTrigger.ANOMALY_DETECTED,
                        campaign_id=campaign["id"],
                        platform=campaign["platform"],
                        metric=anomaly["metric"],
                        current_value=anomaly["current_value"],
                        threshold_value=anomaly["historical_mean"],
                        timestamp=datetime.utcnow(),
                        context=anomaly,
                    ))

    async def _creative_loop(self):
        """Creative refresh loop - runs every hour."""
        fatigued = await self._get_fatigued_creatives(frequency_threshold=3.0)

        for creative in fatigued:
            await self._emit_event(OptimizationEvent(
                trigger=OptimizationTrigger.CREATIVE_FATIGUE,
                campaign_id=creative["campaign_id"],
                platform=creative["platform"],
                metric="frequency",
                current_value=creative["frequency"],
                threshold_value=3.0,
                timestamp=datetime.utcnow(),
                context=creative,
            ))

    async def _performance_loop(self):
        """Performance monitoring loop - runs every minute."""
        # Quick health check on all active campaigns
        campaigns = await self._get_active_campaigns()

        for campaign in campaigns:
            metrics = await self._get_recent_metrics(campaign["id"], campaign["platform"], minutes=5)

            # Check for critical thresholds
            if metrics.get("cpa", 0) > campaign.get("cpa_target", 100) * 1.5:
                await self._emit_event(OptimizationEvent(
                    trigger=OptimizationTrigger.METRIC_THRESHOLD,
                    campaign_id=campaign["id"],
                    platform=campaign["platform"],
                    metric="cpa",
                    current_value=metrics["cpa"],
                    threshold_value=campaign["cpa_target"] * 1.5,
                    timestamp=datetime.utcnow(),
                    context={"campaign": campaign, "metrics": metrics},
                ))

    async def _emit_event(self, event: OptimizationEvent):
        """Publish an optimization event to the event bus."""
        await self.redis.publish(
            "optimization:events",
            json.dumps({
                "trigger": event.trigger.value,
                "campaign_id": event.campaign_id,
                "platform": event.platform,
                "metric": event.metric,
                "current_value": event.current_value,
                "threshold_value": event.threshold_value,
                "timestamp": event.timestamp.isoformat(),
                "context": event.context,
            }),
        )

    def _is_pacing_off(self, spend_data: dict) -> bool:
        """Check if campaign spend pacing is off."""
        return spend_data.get("pace_ratio", 1.0) > 1.2

    def _should_reoptimize(self, portfolio: dict) -> bool:
        """Determine if portfolio reoptimization is needed."""
        # Reoptimize if any campaign's ROAS deviates >20% from target
        for campaign in portfolio.get("campaigns", []):
            if campaign.get("roas", 0) > 0:
                deviation = abs(campaign["roas"] - portfolio.get("target_roas", 3.0)) / portfolio.get("target_roas", 3.0)
                if deviation > 0.2:
                    return True
        return False

    # Stub methods for data retrieval
    async def _get_active_campaigns(self) -> list[dict]: ...
    async def _get_spend_data(self, campaign_id: str, platform: str) -> dict: ...
    async def _get_recent_metrics(self, campaign_id: str, platform: str, minutes: int) -> dict: ...
    async def _get_historical_metrics(self, campaign_id: str, platform: str, days: int) -> list: ...
    async def _get_portfolio_data(self) -> dict: ...
    async def _get_fatigued_creatives(self, frequency_threshold: float) -> list[dict]: ...
    async def _apply_budget_changes(self, result: dict): ...
    async def _alert_ops(self, message: str): ...
```

### 7.3 Feedback Loop with LangGraph

```python
class OptimizationState(TypedDict):
    task: dict
    execution_result: dict
    critic_decision: str
    retry_count: int
    max_retries: int
    messages: Annotated[Sequence[BaseMessage], "message_history"]

def executor_node(state: OptimizationState) -> OptimizationState:
    """Execute the assigned task using the appropriate specialized agent."""
    task = state["task"]
    agent_name = task["assigned_agent"]

    agent = get_agent(agent_name)
    result = agent.execute(task)

    state["execution_result"] = result
    return state

def critic_node(state: OptimizationState) -> OptimizationState:
    """Evaluate the execution result."""
    critic = CriticAgent(get_llm())
    decision = critic.evaluate(
        task=state["task"],
        output=state["execution_result"],
        context={"retry_count": state["retry_count"]},
    )

    state["critic_decision"] = decision["decision"]
    state["critic_feedback"] = decision.get("feedback", "")
    return state

def should_retry(state: OptimizationState) -> str:
    """Determine next step based on critic decision."""
    if state["critic_decision"] == "ACCEPT":
        return "end"
    elif state["critic_decision"] == "RETRY" and state["retry_count"] < state["max_retries"]:
        return "retry"
    elif state["critic_decision"] == "ROLLBACK":
        return "rollback"
    else:
        return "escalate"

def build_optimization_graph():
    graph = StateGraph(OptimizationState)

    graph.add_node("executor", executor_node)
    graph.add_node("critic", critic_node)
    graph.add_node("rollback", rollback_node)
    graph.add_node("human_review", human_review_node)

    graph.set_entry_point("executor")
    graph.add_edge("executor", "critic")
    graph.add_conditional_edges("critic", should_retry, {
        "retry": "executor",
        "rollback": "rollback",
        "escalate": "human_review",
        "end": END,
    })
    graph.add_edge("rollback", END)
    graph.add_edge("human_review", END)

    return graph.compile()
```

---

## 8. Ad Platform Integration

### 8.1 Connector Architecture

```python
from abc import ABC, abstractmethod
from typing import Any
import hashlib
import hmac

class AdPlatformConnector(ABC):
    """Abstract base class for ad platform connectors."""

    @abstractmethod
    async def authenticate(self) -> str:
        """Obtain and return an access token."""
        pass

    @abstractmethod
    async def create_campaign(self, config: dict) -> dict:
        pass

    @abstractmethod
    async def update_campaign(self, campaign_id: str, updates: dict) -> dict:
        pass

    @abstractmethod
    async def get_campaign_metrics(self, campaign_id: str, date_range: tuple) -> dict:
        pass

    @abstractmethod
    async def update_budget(self, campaign_id: str, budget: float) -> dict:
        pass

    @abstractmethod
    async def update_bid(self, campaign_id: str, bid: float) -> dict:
        pass

    @abstractmethod
    async def pause_campaign(self, campaign_id: str) -> dict:
        pass

    @abstractmethod
    async def resume_campaign(self, campaign_id: str) -> dict:
        pass

    @abstractmethod
    async def get_campaigns(self, filters: dict = None) -> list[dict]:
        pass

    @abstractmethod
    async def upload_creative(self, campaign_id: str, creative: dict) -> dict:
        pass

    @abstractmethod
    async def create_experiment(self, config: dict) -> dict:
        pass

    @abstractmethod
    async def get_experiment_results(self, experiment_id: str) -> dict:
        pass
```

### 8.2 Google Ads Connector

```python
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

class GoogleAdsConnector(AdPlatformConnector):
    def __init__(self, developer_token: str, client_id: str, client_secret: str, refresh_token: str, login_customer_id: str = None):
        self.client = GoogleAdsClient.load_from_dict({
            "developer_token": developer_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "login_customer_id": login_customer_id,
            "use_proto_plus": True,
        })

    async def authenticate(self) -> str:
        # Google Ads uses OAuth2; the client handles token refresh
        return "authenticated"

    async def create_campaign(self, config: dict) -> dict:
        campaign_service = self.client.get_service("CampaignService")
        campaign_operation = self.client.get_type("CampaignOperation")

        campaign = campaign_operation.create
        campaign.name = config["name"]
        campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum.SEARCH

        # Set budget
        campaign_budget_service = self.client.get_service("CampaignBudgetService")
        budget_operation = self.client.get_type("CampaignBudgetOperation")
        budget = budget_operation.create
        budget.name = f"Budget for {config['name']}"
    .amount_micros = int(config["budget"] * 1_000_000)
        budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD

        # Create budget first
        budget_response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=config["customer_id"],
            operations=[budget_operation],
        )
        campaign_budget_resource = budget_response.results[0].resource_name

        campaign.campaign_budget = campaign_budget_resource

        # Set bidding
        if config.get("bidding_strategy") == "TARGET_ROAS":
            campaign.bidding_strategy_type = self.client.enums.BiddingStrategyTypeEnum.TARGET_ROAS
            campaign.target_roas.target_roas = config.get("target_roas", 3.0)
        elif config.get("bidding_strategy") == "MAXIMIZE_CONVERSIONS":
            campaign.bidding_strategy_type = self.client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS

        # Set status
        campaign.status = self.client.enums.CampaignStatusEnum.PAUSED  # Start paused for review

        response = campaign_service.mutate_campaigns(
            customer_id=config["customer_id"],
            operations=[campaign_operation],
        )

        return {
            "id": response.results[0].resource_name.split("/")[-1],
            "resource_name": response.results[0].resource_name,
            "status": "created",
        }

    async def get_campaign_metrics(self, campaign_id: str, date_range: tuple) -> dict:
        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date BETWEEN '{date_range[0]}' AND '{date_range[1]}'
        """

        response = ga_service.search_stream(
            customer_id=self.login_customer_id,
            query=query,
        )

        total_impressions = 0
        total_clicks = 0
        total_cost = 0
        total_conversions = 0
        total_conversion_value = 0

        for batch in response:
            for row in batch.results:
                total_impressions += row.metrics.impressions
                total_clicks += row.metrics.clicks
                total_cost += row.metrics.cost_micros / 1_000_000
                total_conversions += row.metrics.conversions
                total_conversion_value += row.metrics.conversions_value

        return {
            "campaign_id": campaign_id,
            "impressions": total_impressions,
            "clicks": total_clicks,
            "spend": round(total_cost, 2),
            "conversions": round(total_conversions, 2),
            "revenue": round(total_conversion_value, 2),
            "ctr": round(total_clicks / total_impressions, 4) if total_impressions > 0 else 0,
            "cpc": round(total_cost / total_clicks, 2) if total_clicks > 0 else 0,
            "cpa": round(total_cost / total_conversions, 2) if total_conversions > 0 else 0,
            "roas": round(total_conversion_value / total_cost, 2) if total_cost > 0 else 0,
        }

    async def update_budget(self, campaign_id: str, budget: float) -> dict:
        campaign_service = self.client.get_service("CampaignService")

        # First get the campaign to find the budget resource name
        ga_service = self.client.get_service("GoogleAdsService")
        query = f"SELECT campaign_budget FROM campaign WHERE campaign.id = {campaign_id}"
        response = ga_service.search(customer_id=self.login_customer_id, query=query)

        budget_resource = None
        for batch in response:
            for row in batch.results:
                budget_resource = row.campaign_budget.resource_name

        if not budget_resource:
            raise ValueError(f"Could not find budget for campaign {campaign_id}")

        # Update the budget
        campaign_budget_service = self.client.get_service("CampaignBudgetService")
        budget_operation = self.client.get_type("CampaignBudgetOperation")
        budget = budget_operation.update
        budget.resource_name = budget_resource
        budget.amount_micros = int(budget * 1_000_000)

        field_mask = self.client.get_type("FieldMask")
        field_mask.paths.append("amount_micros")
        budget_operation.update_mask.CopyFrom(field_mask)

        response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=self.login_customer_id,
            operations=[budget_operation],
        )

        return {"campaign_id": campaign_id, "new_budget": budget, "status": "updated"}

    async def pause_campaign(self, campaign_id: str) -> dict:
        campaign_service = self.client.get_service("CampaignService")
        campaign_operation = self.client.get_type("CampaignOperation")

        campaign = campaign_operation.update
        campaign.resource_name = f"customers/{self.login_customer_id}/campaigns/{campaign_id}"
        campaign.status = self.client.enums.CampaignStatusEnum.PAUSED

        field_mask = self.client.get_type("FieldMask")
        field_mask.paths.append("status")
        campaign_operation.update_mask.CopyFrom(field_mask)

        campaign_service.mutate_campaigns(
            customer_id=self.login_customer_id,
            operations=[campaign_operation],
        )

        return {"campaign_id": campaign_id, "status": "paused"}

    async def resume_campaign(self, campaign_id: str) -> dict:
        campaign_service = self.client.get_service("CampaignService")
        campaign_operation = self.client.get_type("CampaignOperation")

        campaign = campaign_operation.update
        campaign.resource_name = f"customers/{self.login_customer_id}/campaigns/{campaign_id}"
        campaign.status = self.client.enums.CampaignStatusEnum.ENABLED

        field_mask = self.client.get_type("FieldMask")
        field_mask.paths.append("status")
        campaign_operation.update_mask.CopyFrom(field_mask)

        campaign_service.mutate_campaigns(
            customer_id=self.login_customer_id,
            operations=[campaign_operation],
        )

        return {"campaign_id": campaign_id, "status": "active"}

    async def get_campaigns(self, filters: dict = None) -> list[dict]:
        ga_service = self.client.get_service("GoogleAdsService")
        query = """
            SELECT campaign.id, campaign.name, campaign.status,
                   campaign_budget.amount_micros, metrics.impressions,
                   metrics.clicks, metrics.cost_micros, metrics.conversions
            FROM campaign
            WHERE campaign.status != 'REMOVED'
        """
        response = ga_service.search(customer_id=self.login_customer_id, query=query)

        campaigns = []
        for batch in response:
            for row in batch.results:
                campaigns.append({
                    "id": row.campaign.id,
                    "name": row.campaign.name,
                    "status": row.campaign.status.name,
                    "budget": row.campaign_budget.amount_micros / 1_000_000,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "spend": row.metrics.cost_micros / 1_000_000,
                    "conversions": row.metrics.conversions,
                })
        return campaigns

    async def upload_creative(self, campaign_id: str, creative: dict) -> dict:
        # Implementation for uploading ad creatives via Google Ads API
        pass

    async def create_experiment(self, config: dict) -> dict:
        # Implementation for Google Ads experiments
        pass

    async def get_experiment_results(self, experiment_id: str) -> dict:
        # Implementation for getting experiment results
        pass
```

### 8.3 Meta Ads Connector

```python
import aiohttp

class MetaAdsConnector(AdPlatformConnector):
    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, access_token: str, ad_account_id: str):
        self.access_token = access_token
        self.ad_account_id = ad_account_id

    async def authenticate(self) -> str:
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/me?access_token={self.access_token}"
            async with session.get(url) as resp:
                data = await resp.json()
                return data.get("id", "")

    async def create_campaign(self, config: dict) -> dict:
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/act_{self.ad_account_id}/campaigns"
            params = {
                "name": config["name"],
                "objective": self._map_objective(config["objective"]),
                "status": "PAUSED",
                "special_ad_categories": [],
                "access_token": self.access_token,
            }

            async with session.post(url, params=params) as resp:
                data = await resp.json()
                return {"id": data["id"], "status": "created"}

    async def get_campaign_metrics(self, campaign_id: str, date_range: tuple) -> dict:
        async with aiohttp.ClientSession() as session:
            fields = "impressions,clicks,spend,actions,action_values"
            url = (
                f"{self.BASE_URL}/{campaign_id}/insights"
                f"?fields={fields}"
                f"&time_range={{'since': '{date_range[0]}', 'until': '{date_range[1]}'}}"
                f"&access_token={self.access_token}"
            )

            async with session.get(url) as resp:
                data = await resp.json()
                if not data.get("data"):
                    return {}

                metrics = data["data"][0]
                impressions = int(metrics.get("impressions", 0))
                clicks = int(metrics.get("clicks", 0))
                spend = float(metrics.get("spend", 0))

                conversions = 0
                revenue = 0.0
                for action in metrics.get("actions", []):
                    if action["action_type"] in ("purchase", "lead", "convert"):
                        conversions += int(action["value"])
                for value in metrics.get("action_values", []):
                    if value["action_type"] == "purchase":
                        revenue += float(value["value"])

                return {
                    "campaign_id": campaign_id,
                    "impressions": impressions,
                    "clicks": clicks,
                    "spend": round(spend, 2),
                    "conversions": conversions,
                    "revenue": round(revenue, 2),
                    "ctr": round(clicks / impressions, 4) if impressions > 0 else 0,
                    "cpc": round(spend / clicks, 2) if clicks > 0 else 0,
                    "cpa": round(spend / conversions, 2) if conversions > 0 else 0,
                    "roas": round(revenue / spend, 2) if spend > 0 else 0,
                }

    async def update_budget(self, campaign_id: str, budget: float) -> dict:
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/{campaign_id}"
            params = {
                "daily_budget": int(budget * 100),  # Meta uses cents
                "access_token": self.access_token,
            }
            async with session.post(url, params=params) as resp:
                data = await resp.json()
                return {"campaign_id": campaign_id, "new_budget": budget, "status": "updated"}

    async def pause_campaign(self, campaign_id: str) -> dict:
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/{campaign_id}"
            params = {"status": "PAUSED", "access_token": self.access_token}
            async with session.post(url, params=params) as resp:
                await resp.json()
                return {"campaign_id": campaign_id, "status": "paused"}

    async def resume_campaign(self, campaign_id: str) -> dict:
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/{campaign_id}"
            params = {"status": "ACTIVE", "access_token": self.access_token}
            async with session.post(url, params=params) as resp:
                await resp.json()
                return {"campaign_id": campaign_id, "status": "active"}

    async def get_campaigns(self, filters: dict = None) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            fields = "id,name,status,daily_budget,insights{impressions,clicks,spend}"
            url = (
                f"{self.BASE_URL}/act_{self.ad_account_id}/campaigns"
                f"?fields={fields}&access_token={self.access_token}"
            )
            async with session.get(url) as resp:
                data = await resp.json()
                return [
                    {
                        "id": c["id"],
                        "name": c["name"],
                        "status": c["status"],
                        "budget": int(c.get("daily_budget", 0)) / 100,
                    }
                    for c in data.get("data", [])
                ]

    async def upload_creative(self, campaign_id: str, creative: dict) -> dict:
        # Implementation for uploading creatives via Meta Marketing API
        pass

    async def create_experiment(self, config: dict) -> dict:
        # Implementation for Meta A/B testing
        pass

    async def get_experiment_results(self, experiment_id: str) -> dict:
        # Implementation for getting experiment results
        pass

    def _map_objective(self, objective: str) -> str:
        mapping = {
            "AWARENESS": "BRAND_AWARENESS",
            "CONSIDERATION": "ENGAGEMENT",
            "CONVERSION": "CONVERSIONS",
        }
        return mapping.get(objective, "CONVERSIONS")
```

### 8.4 Connector Registry

```python
class ConnectorRegistry:
    """Registry for managing ad platform connectors."""

    def __init__(self):
        self._connectors: dict[str, AdPlatformConnector] = {}

    def register(self, platform: str, connector: AdPlatformConnector):
        self._connectors[platform] = connector

    def get(self, platform: str) -> AdPlatformConnector:
        if platform not in self._connectors:
            raise ValueError(f"No connector registered for platform: {platform}")
        return self._connectors[platform]

    def list_platforms(self) -> list[str]:
        return list(self._connectors.keys())

# Initialize registry
registry = ConnectorRegistry()
registry.register("google_ads", GoogleAdsConnector(
    developer_token=os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
    client_id=os.environ["GOOGLE_ADS_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_ADS_CLIENT_SECRET"],
    refresh_token=os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
    login_customer_id=os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
))
registry.register("meta", MetaAdsConnector(
    access_token=os.environ["META_ACCESS_TOKEN"],
    ad_account_id=os.environ["META_AD_ACCOUNT_ID"],
))
```

---

## 9. Code Examples and Snippets

### 9.1 Full Agent Initialization

```python
from langchain_openai import ChatOpenAI
from langchain_deepagents import DeepAgent

def initialize_system():
    """Initialize the complete autonomous campaign optimization system."""

    # Shared LLM instance
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,  # Low temperature for deterministic decisions
        max_tokens=4096,
    )

    # Initialize agents
    planner = create_planner_agent(llm)
    campaign_agent = CampaignAgent(llm)
    budget_agent = BudgetAgent(llm)
    creative_agent = CreativeAgent(llm)
    ab_test_agent = ABTestAgent(llm)
    analytics_agent = AnalyticsAgent(llm)
    critic = CriticAgent(llm)

    # Build orchestration graph
    graph = build_orchestration_graph()

    # Initialize optimization loop
    loop = RealTimeOptimizationLoop(
        orchestrator=graph,
        redis_url="redis://localhost:6379",
    )

    return {
        "planner": planner,
        "agents": {
            "campaign": campaign_agent,
            "budget": budget_agent,
            "creative": creative_agent,
            "ab_test": ab_test_agent,
            "analytics": analytics_agent,
        },
        "critic": critic,
        "graph": graph,
        "loop": loop,
    }
```

### 9.2 Running an Optimization Cycle

```python
async def run_optimization_cycle(system: dict, objective: str):
    """Run a complete optimization cycle."""

    # 1. Planner decomposes the objective
    plan = await system["graph"].ainvoke({
        "objective": objective,
        "constraints": {
            "max_budget_change_pct": 30,
            "min_budget_per_campaign": 10,
            "max_experiments_concurrent": 5,
        },
    })

    # 2. Execute each sub-task
    results = []
    for task in plan["sub_tasks"]:
        agent = system["agents"][task["assigned_agent"]]
        result = await agent.execute(task)

        # 3. Critic evaluates
        decision = system["critic"].evaluate(task, result, plan["context"])

        results.append({
            "task": task,
            "result": result,
            "decision": decision,
        })

        # 4. Handle decision
        if decision["decision"] == "ROLLBACK":
            await agent.rollback(task)
        elif decision["decision"] == "ESCALATE":
            await notify_human(task, result, decision)

    return results
```

### 9.3 Configuration Management

```python
from pydantic import BaseModel, Field
from typing import Optional

class CampaignConfig(BaseModel):
    name: str
    objective: str
    total_budget: float = Field(gt=0)
    daily_budget: Optional[float] = Field(None, gt=0)
    start_date: str
    end_date: Optional[str] = None
    target_roas: float = Field(default=3.0, gt=0)
    target_cpa: Optional[float] = Field(None, gt=0)
    platforms: list[str] = Field(default=["google_ads"])
    targeting: dict = Field(default_factory=dict)
    creative_count: int = Field(default=5, ge=1, le=20)

class OptimizationConfig(BaseModel):
    # Budget optimization
    budget_rebalance_interval_minutes: int = 15
    max_budget_change_pct: float = 30.0
    min_budget_per_campaign: float = 10.0
    budget_reserve_pct: float = 10.0

    # Creative management
    creative_refresh_interval_hours: int = 1
    creative_fatigue_frequency_threshold: float = 3.0
    min_active_variants: int = 3

    # A/B testing
    ab_test_confidence_threshold: float = 0.95
    ab_test_max_expected_loss: float = 0.005
    ab_test_min_duration_days: int = 7
    ab_test_max_concurrent: int = 5

    # Anomaly detection
    anomaly_z_threshold: float = 3.0
    anomaly_check_interval_minutes: int = 5

    # Safety
    max_retries_per_task: int = 3
    human_escalation_threshold: float = 0.5  # Confidence below this triggers escalation
    enable_auto_rollback: bool = True
    require_human_approval_above: float = 1000.0  # Budget changes above this amount
```

### 9.4 Audit Logging

```python
import json
from datetime import datetime

class AuditLogger:
    """Comprehensive audit logging for all agent actions."""

    def __init__(self, db_connection):
        self.db = db_connection

    async def log_action(self, entry: dict):
        """Log an agent action with full context."""
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": entry.get("agent"),
            "action": entry.get("action"),
            "task_id": entry.get("task_id"),
            "input": json.dumps(entry.get("input", {})),
            "output": json.dumps(entry.get("output", {})),
            "decision": entry.get("decision"),
            "critic_feedback": entry.get("critic_feedback"),
            "rollback_performed": entry.get("rollback_performed", False),
            "execution_time_ms": entry.get("execution_time_ms"),
            "metadata": json.dumps(entry.get("metadata", {})),
        }

        await self.db.execute(
            """
            INSERT INTO agent_audit_log
            (timestamp, agent, action, task_id, input, output, decision,
             critic_feedback, rollback_performed, execution_time_ms, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            *record.values(),
        )

    async def get_audit_trail(self, task_id: str) -> list[dict]:
        """Get the full audit trail for a task."""
        rows = await self.db.fetch(
            "SELECT * FROM agent_audit_log WHERE task_id = $1 ORDER BY timestamp",
            task_id,
        )
        return [dict(row) for row in rows]
```

### 9.5 Human-in-the-Loop Interface

```python
from fastapi import FastAPI, WebSocket
from typing import Optional

app = FastAPI()

class HumanReviewQueue:
    """Queue for decisions that require human approval."""

    def __init__(self):
        self.pending: dict[str, dict] = {}
        self.websocket: Optional[WebSocket] = None

    async def submit_for_review(self, task: dict, output: dict, critic_decision: dict) -> dict:
        """Submit a decision for human review."""
        review_id = str(uuid.uuid4())
        self.pending[review_id] = {
            "task": task,
            "output": output,
            "critic_decision": critic_decision,
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "pending",
        }

        # Notify via WebSocket if connected
        if self.websocket:
            await self.websocket.send_json({
                "type": "review_requested",
                "review_id": review_id,
                "task": task,
                "critic_decision": critic_decision,
            })

        return {"review_id": review_id, "status": "pending"}

    async def resolve_review(self, review_id: str, decision: str, feedback: str = ""):
        """Resolve a pending review."""
        if review_id not in self.pending:
            raise ValueError(f"Review {review_id} not found")

        self.pending[review_id]["status"] = "resolved"
        self.pending[review_id]["human_decision"] = decision
        self.pending[review_id]["human_feedback"] = feedback
        self.pending[review_id]["resolved_at"] = datetime.utcnow().isoformat()

        return self.pending[review_id]

review_queue = HumanReviewQueue()

@app.websocket("/ws/review")
async def review_websocket(websocket: WebSocket):
    await websocket.accept()
    review_queue.websocket = websocket
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "resolve_review":
                result = await review_queue.resolve_review(
                    data["review_id"],
                    data["decision"],
                    data.get("feedback", ""),
                )
                await websocket.send_json({"type": "review_resolved", "result": result})
    except Exception:
        review_queue.websocket = None
```

---

## 10. Testing Strategy

### 10.1 Testing Pyramid

```
                    ┌─────────┐
                    │  E2E    │  (5 tests)
                    │  Tests  │
                   ┌┴─────────┴┐
                   │ Integration│  (20 tests)
                   │   Tests    │
                  ┌┴────────────┴┐
                  │   Unit Tests  │  (100+ tests)
                  │               │
                  └───────────────┘
```

### 10.2 Unit Tests

```python
# tests/test_budget_optimizer.py
import pytest
from unittest.mock import MagicMock

class TestBudgetOptimizer:
    def test_optimize_allocation_basic(self):
        optimizer = BudgetOptimizer(total_budget=1000, target_roas=3.0)
        campaigns = [
            CampaignBudget("camp_1", 500, 4.0, 25.0, 4.5, 50, 1000, 0.8),
            CampaignBudget("camp_2", 500, 2.0, 50.0, 1.8, 50, 1000, 0.9),
        ]

        result = optimizer.optimize_allocation(campaigns, {})

        assert sum(result.values()) == pytest.approx(1000, abs=1)
        # Higher ROAS campaign should get more budget
        assert result["camp_1"] > result["camp_2"]

    def test_optimize_allocation_respects_bounds(self):
        optimizer = BudgetOptimizer(total_budget=1000, target_roas=3.0)
        campaigns = [
            CampaignBudget("camp_1", 100, 4.0, 25.0, 4.5, 200, 1000, 0.8),
            CampaignBudget("camp_2", 100, 2.0, 50.0, 1.8, 200, 1000, 0.9),
        ]

        result = optimizer.optimize_allocation(campaigns, {})

        assert result["camp_1"] >= 200
        assert result["camp_2"] >= 200

    def test_marginal_roas_computation(self):
        optimizer = BudgetOptimizer(total_budget=1000, target_roas=3.0)
        # Mock data
        data = [
            {"spend": 100, "revenue": 400},
            {"spend": 200, "revenue": 750},
            {"spend": 300, "revenue": 1050},
        ]
        with patch("get_recent_performance", return_value=data):
            marginal = optimizer.compute_marginal_roas("camp_1", "google_ads")
            assert marginal > 0

# tests/test_ab_testing.py
class TestBayesianABTest:
    def test_probability_better_than_clear_winner(self):
        test = BayesianABTest()
        test.add_variant("control")
        test.add_variant("treatment")

        # Control: 100 impressions, 5 conversions (5%)
        test.update("control", 1000, 50)
        # Treatment: 1000 impressions, 80 conversions (8%)
        test.update("treatment", 1000, 80)

        p = test.probability_better_than("treatment", "control")
        assert p > 0.95

    def test_should_stop_when_significant(self):
        test = BayesianABTest()
        test.add_variant("control")
        test.add_variant("treatment")

        test.update("control", 10000, 200)  # 2% conversion
        test.update("treatment", 10000, 300)  # 3% conversion

        result = test.should_stop("control", "treatment")
        assert result["should_stop"] is True
        assert result["winner"] == "treatment"

    def test_should_not_stop_early(self):
        test = BayesianABTest()
        test.add_variant("control")
        test.add_variant("treatment")

        test.update("control", 100, 5)
        test.update("treatment", 100, 6)

        result = test.should_stop("control", "treatment")
        assert result["should_stop"] is False

    def test_practical_equivalence(self):
        test = BayesianABTest()
        test.add_variant("control")
        test.add_variant("treatment")

        # Very similar performance
        test.update("control", 10000, 200)  # 2.0%
        test.update("treatment", 10000, 202)  # 2.02%

        result = test.should_stop("control", "treatment", max_loss=0.005)
        assert result["should_stop"] is True
        assert "equivalence" in result["reason"].lower()

# tests/test_anomaly_detector.py
class TestAnomalyDetector:
    def test_detects_spike(self):
        detector = AnomalyDetector(z_threshold=2.0)
        history = [100, 102, 98, 101, 99, 100, 101, 98, 100, 102, 99, 100, 101, 99]
        result = detector.detect("camp_1", "ctr", 150, history)

        assert result["is_anomaly"] is True
        assert result["direction"] == "spike"

    def test_detects_drop(self):
        detector = AnomalyDetector(z_threshold=2.0)
        history = [100, 102, 98, 101, 99, 100, 101, 98, 100, 102, 99, 100, 101, 99]
        result = detector.detect("camp_1", "ctr", 50, history)

        assert result["is_anomaly"] is True
        assert result["direction"] == "drop"

    def test_no_anomaly_for_normal_variation(self):
        detector = AnomalyDetector(z_threshold=3.0)
        history = [100, 102, 98, 101, 99, 100, 101, 98, 100, 102, 99, 100, 101, 99]
        result = detector.detect("camp_1", "ctr", 100, history)

        assert result["is_anomaly"] is False

    def test_insufficient_history(self):
        detector = AnomalyDetector(min_history=7)
        result = detector.detect("camp_1", "ctr", 150, [100, 102, 98])

        assert result["is_anomaly"] is False
        assert result["reason"] == "insufficient_history"
```

### 10.3 Integration Tests

```python
# tests/integration/test_campaign_agent.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
class TestCampaignAgentIntegration:
    @pytest.fixture
    def mock_connector(self):
        connector = AsyncMock()
        connector.create_campaign.return_value = {"id": "camp_123", "status": "created"}
        connector.get_campaign_status.return_value = {"status": "active", "spend": 150.0}
        return connector

    async def test_create_campaign_end_to_end(self, mock_connector):
        with patch("get_platform_connector", return_value=mock_connector):
            agent = CampaignAgent(mock_llm)
            task = {
                "id": "task_1",
                "action": "create_campaign",
                "description": "Create a new search campaign",
                "parameters": {
                    "name": "Test_Campaign_US_20261001",
                    "objective": "CONVERSION",
                    "budget": 100.0,
                    "budget_type": "DAILY",
                    "start_date": "2026-10-01",
                    "platform": "google_ads",
                },
                "constraints": {"max_budget": 500.0},
            }

            result = await agent.execute(task)

            assert result["status"] == "completed"
            mock_connector.create_campaign.assert_called_once()

    async def test_pause_campaign_rollback(self, mock_connector):
        with patch("get_platform_connector", return_value=mock_connector):
            agent = CampaignAgent(mock_llm)
            task = {
                "id": "task_2",
                "action": "pause_campaign",
                "parameters": {"campaign_id": "camp_123", "platform": "google_ads"},
            }

            # Execute
            result = await agent.execute(task)
            assert result["status"] == "completed"

            # Rollback
            rollback_result = await agent.rollback(task)
            assert rollback_result is True
            mock_connector.resume_campaign.assert_called_once_with("camp_123")

# tests/integration/test_optimization_loop.py
@pytest.mark.asyncio
class TestOptimizationLoop:
    async def test_budget_loop_emits_pacing_event(self):
        loop = RealTimeOptimizationLoop(
            orchestrator=mock_orchestrator,
            redis_url="redis://localhost:6379",
        )

        with patch.object(loop, "_get_active_campaigns", return_value=[
            {"id": "camp_1", "platform": "google_ads", "budget": 100}
        ]):
            with patch.object(loop, "_get_spend_data", return_value={
                "pace_ratio": 1.5,  # 50% over pace
                "current_spend": 75,
                "expected_spend": 50,
            }):
                with patch.object(loop, "_emit_event") as mock_emit:
                    await loop._budget_loop()
                    mock_emit.assert_called()
                    event = mock_emit.call_args[0][0]
                    assert event.trigger == OptimizationTrigger.BUDGET_PACING
```

### 10.4 End-to-End Tests

```python
# tests/e2e/test_full_optimization_cycle.py
import pytest

@pytest.mark.e2e
class TestFullOptimizationCycle:
    """End-to-end tests that exercise the full agent pipeline."""

    @pytest.fixture
    async def system(self):
        """Initialize the full system with test configuration."""
        config = OptimizationConfig(
            budget_rebalance_interval_minutes=1,
            max_budget_change_pct=30,
            anomaly_z_threshold=2.5,
        )
        system = initialize_system()
        yield system
        await system["loop"].stop()

    async def test_budget_optimization_cycle(self, system):
        """Test a complete budget optimization cycle."""
        # Setup: create test campaigns
        campaign_data = {
            "campaigns": [
                {"id": "camp_1", "platform": "google_ads", "budget": 100, "roas": 4.0, "cpa": 25},
                {"id": "camp_2", "platform": "google_ads", "budget": 100, "roas": 2.0, "cpa": 50},
            ],
            "total_budget": 200,
            "target_roas": 3.0,
        }

        # Run optimization
        result = await run_optimization_cycle(system, "Optimize budget allocation")

        # Verify
        assert len(result) > 0
        for r in result:
            assert r["decision"]["decision"] in ("ACCEPT", "RETRY", "ROLLBACK", "ESCALATE")

    async def test_anomaly_triggers_investigation(self, system):
        """Test that an anomaly triggers the appropriate response."""
        # Inject anomalous data
        await inject_test_metrics("camp_1", {"cpa": 200, "roas": 0.5})

        # Run anomaly loop
        await system["loop"]._anomaly_loop()

        # Verify anomaly was detected and event emitted
        # (Would check event bus in real implementation)

    async def test_creative_refresh_on_fatigue(self, system):
        """Test that fatigued creatives trigger refresh."""
        # Setup fatigued creative
        await inject_fatigued_creative("camp_1", frequency=4.5)

        # Run creative loop
        await system["loop"]._creative_loop()

        # Verify refresh was triggered
```

### 10.5 Mock Ad Platform for Testing

```python
# tests/mocks/mock_ad_platform.py
class MockAdPlatformConnector(AdPlatformConnector):
    """In-memory mock ad platform for testing."""

    def __init__(self):
        self.campaigns: dict[str, dict] = {}
        self.creatives: dict[str, list[dict]] = {}
        self.experiments: dict[str, dict] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"mock_{self._counter}"

    async def create_campaign(self, config: dict) -> dict:
        campaign_id = self._next_id()
        self.campaigns[campaign_id] = {
            "id": campaign_id,
            "name": config["name"],
            "status": "PAUSED",
            "budget": config["budget"],
            "objective": config["objective"],
            "created_at": datetime.utcnow().isoformat(),
        }
        return {"id": campaign_id, "status": "created"}

    async def get_campaign_metrics(self, campaign_id: str, date_range: tuple) -> dict:
        # Return synthetic metrics
        import random
        impressions = random.randint(1000, 10000)
        ctr = random.uniform(0.01, 0.05)
        clicks = int(impressions * ctr)
        cpc = random.uniform(0.5, 3.0)
        spend = round(clicks * cpc, 2)
        conversion_rate = random.uniform(0.02, 0.1)
        conversions = int(clicks * conversion_rate)
        cpa = round(spend / conversions, 2) if conversions > 0 else 0
        roas = random.uniform(1.0, 5.0)
        revenue = round(spend * roas, 2)

        return {
            "campaign_id": campaign_id,
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "conversions": conversions,
            "revenue": revenue,
            "ctr": round(ctr, 4),
            "cpc": round(cpc, 2),
            "cpa": cpa,
            "roas": round(roas, 2),
            "conversion_rate": round(conversion_rate, 4),
        }

    async def update_budget(self, campaign_id: str, budget: float) -> dict:
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")
        self.campaigns[campaign_id]["budget"] = budget
        return {"campaign_id": campaign_id, "new_budget": budget, "status": "updated"}

    async def pause_campaign(self, campaign_id: str) -> dict:
        self.campaigns[campaign_id]["status"] = "PAUSED"
        return {"campaign_id": campaign_id, "status": "paused"}

    async def resume_campaign(self, campaign_id: str) -> dict:
        self.campaigns[campaign_id]["status"] = "ACTIVE"
        return {"campaign_id": campaign_id, "status": "active"}

    async def get_campaigns(self, filters: dict = None) -> list[dict]:
        return list(self.campaigns.values())

    async def upload_creative(self, campaign_id: str, creative: dict) -> dict:
        if campaign_id not in self.creatives:
            self.creatives[campaign_id] = []
        creative_id = self._next_id()
        self.creatives[campaign_id].append({"id": creative_id, **creative})
        return {"creative_id": creative_id, "status": "uploaded"}

    async def create_experiment(self, config: dict) -> dict:
        exp_id = self._next_id()
        self.experiments[exp_id] = {"id": exp_id, **config, "status": "running"}
        return {"experiment_id": exp_id, "status": "created"}

    async def get_experiment_results(self, experiment_id: str) -> dict:
        # Return synthetic experiment results
        return {
            "control_variant": "control",
            "treatment_variants": ["treatment"],
            "variants": {
                "control": {"impressions": 1000, "conversions": 30, "spend": 150, "revenue": 600},
                "treatment": {"impressions": 1000, "conversions": 40, "spend": 160, "revenue": 720},
            },
        }
```

### 10.6 Performance and Load Testing

```python
# tests/performance/test_optimization_throughput.py
import asyncio
import time

@pytest.mark.performance
class TestOptimizationPerformance:
    async def test_budget_optimization_throughput(self):
        """Test that budget optimization completes within SLA."""
        optimizer = BudgetOptimizer(total_budget=10000, target_roas=3.0)
        campaigns = [
            CampaignBudget(f"camp_{i}", 100, 2.0 + i * 0.1, 50, 2.0, 10, 1000, 0.8)
            for i in range(50)
        ]

        start = time.time()
        result = optimizer.optimize_allocation(campaigns, {})
        elapsed = time.time() - start

        assert elapsed < 1.0  # Must complete in under 1 second
        assert len(result) == 50

    async def test_concurrent_agent_execution(self):
        """Test that multiple agents can execute concurrently."""
        system = initialize_system()

        tasks = []
        for i in range(10):
            task = {
                "id": f"task_{i}",
                "action": "get_campaign_status",
                "parameters": {"campaign_id": f"camp_{i}", "platform": "google_ads"},
            }
            tasks.append(system["agents"]["campaign"].execute(task))

        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        assert len(results) == 10
        assert elapsed < 5.0  # All 10 should complete in under 5 seconds

    async def test_event_processing_latency(self):
        """Test that optimization events are processed within SLA."""
        loop = RealTimeOptimizationLoop(
            orchestrator=mock_orchestrator,
            redis_url="redis://localhost:6379",
        )

        event = OptimizationEvent(
            trigger=OptimizationTrigger.METRIC_THRESHOLD,
            campaign_id="camp_1",
            platform="google_ads",
            metric="cpa",
            current_value=200,
            threshold_value=150,
            timestamp=datetime.utcnow(),
            context={},
        )

        start = time.time()
        await loop._emit_event(event)
        elapsed = time.time() - start

        assert elapsed < 0.1  # Event emission should be near-instant
```

### 10.7 Test Configuration

```yaml
# tests/conftest.py
import pytest

def pytest_addoption(parser):
    parser.addoption("--e2e", action="store_true", help="run end-to-end tests")
    parser.addoption("--performance", action="store_true", help="run performance tests")

def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: mark test as end-to-end")
    config.addinivalue_line("markers", "performance: mark test as performance test")

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--e2e"):
        skip_e2e = pytest.mark.skip(reason="need --e2e option to run")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)
    if not config.getoption("--performance"):
        skip_perf = pytest.mark.skip(reason="need --performance option to run")
        for item in items:
            if "performance" in item.keywords:
                item.add_marker(skip_perf)
```

---

## Appendix A: Environment Setup

```bash
# requirements.txt
langchain>=0.3.0
langchain-deepagents>=0.1.0
langchain-openai>=0.2.0
langgraph>=0.2.0
google-ads>=22.0.0
aiohttp>=3.9.0
redis>=5.0.0
asyncpg>=0.29.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
numpy>=1.24.0
scipy>=1.11.0
pytest>=7.4.0
pytest-asyncio>=0.23.0
```

```bash
# .env
OPENAI_API_KEY=sk-...
GOOGLE_ADS_DEVELOPER_TOKEN=...
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_LOGIN_CUSTOMER_ID=...
META_ACCESS_TOKEN=...
META_AD_ACCOUNT_ID=...
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/campaign_db
```

## Appendix B: Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  API Server  │  │  API Server  │  │  API Server  │       │
│  │  (FastAPI)   │  │  (FastAPI)   │  │  (FastAPI)   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                  │               │
│  ┌──────▼─────────────────▼──────────────────▼───────┐       │
│  │              Redis (Event Bus + Cache)             │       │
│  └──────┬─────────────────▲──────────────────┬───────┘       │
│         │                 │                  │               │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐       │
│  │  Worker      │  │  Worker      │  │  Worker      │       │
│  │  (Celery/    │  │  (Celery/    │  │  (Celery/    │       │
│  │   RQ)        │  │   RQ)        │  │   RQ)        │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                  │               │
│  ┌──────▼─────────────────▼──────────────────▼───────┐       │
│  │              PostgreSQL (State + Audit)            │       │
│  └───────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

*End of Implementation Plan*
